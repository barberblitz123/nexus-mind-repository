#!/usr/bin/env python3
"""
NEXUS Voice Commands - Natural language command processing with context awareness
"""

import asyncio
import re
import json
import time
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path
import sqlite3
import threading
from collections import deque, defaultdict
import difflib
import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np
from fuzzywuzzy import fuzz, process
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CommandCategory(Enum):
    """Command categories"""
    SYSTEM = "system"
    FILE = "file"
    CODE = "code"
    SEARCH = "search"
    NAVIGATION = "navigation"
    PROJECT = "project"
    DEBUG = "debug"
    CHAT = "chat"
    SETTINGS = "settings"
    HELP = "help"


class CommandPriority(Enum):
    """Command execution priority"""
    CRITICAL = 1  # System commands
    HIGH = 2      # User-initiated commands
    NORMAL = 3    # Regular commands
    LOW = 4       # Background tasks


class ConfirmationLevel(Enum):
    """Confirmation requirements"""
    NONE = "none"
    OPTIONAL = "optional"
    REQUIRED = "required"
    DANGEROUS = "dangerous"  # Always require explicit confirmation


@dataclass
class CommandContext:
    """Context for command execution"""
    user_id: str
    session_id: str
    timestamp: float
    previous_commands: List[str] = field(default_factory=list)
    current_directory: Optional[str] = None
    active_project: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    noise_level: float = 0.0
    confidence_threshold: float = 0.7


@dataclass
class Command:
    """Represents a voice command"""
    name: str
    pattern: str
    category: CommandCategory
    handler: Callable
    aliases: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    description: str = ""
    confirmation: ConfirmationLevel = ConfirmationLevel.NONE
    priority: CommandPriority = CommandPriority.NORMAL
    shortcuts: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    
    
@dataclass
class CommandResult:
    """Result of command execution"""
    success: bool
    response: str
    data: Optional[Any] = None
    follow_up: Optional[str] = None
    speak_response: bool = True
    show_visual: bool = False
    
    
class IntentClassifier:
    """Classify user intent using NLP"""
    
    def __init__(self):
        try:
            # Load NLP model
            self.nlp = spacy.load("en_core_web_sm")
            
            # Load intent classification model
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli"
            )
            
            self.intent_labels = [
                "create_file", "open_file", "edit_code", "search_code",
                "run_command", "debug_code", "ask_question", "change_settings",
                "navigate", "get_help", "project_management", "system_control"
            ]
            
        except Exception as e:
            logger.warning(f"Could not load NLP models: {e}")
            self.nlp = None
            self.classifier = None
            
    def classify(self, text: str) -> Tuple[str, float]:
        """Classify intent from text"""
        if not self.classifier:
            return "unknown", 0.0
            
        try:
            result = self.classifier(text, self.intent_labels)
            intent = result['labels'][0]
            confidence = result['scores'][0]
            return intent, confidence
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return "unknown", 0.0
            
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text"""
        if not self.nlp:
            return {}
            
        doc = self.nlp(text)
        entities = defaultdict(list)
        
        for ent in doc.ents:
            entities[ent.label_].append(ent.text)
            
        # Extract custom entities
        # File paths
        file_pattern = r'[\w\-/\\]+\.\w+'
        files = re.findall(file_pattern, text)
        if files:
            entities['FILE'].extend(files)
            
        # Function/class names
        code_pattern = r'\b[A-Z][a-zA-Z0-9_]*\b|\b[a-z][a-zA-Z0-9_]*\('
        code_items = re.findall(code_pattern, text)
        if code_items:
            entities['CODE'].extend(code_items)
            
        return dict(entities)


class CommandParser:
    """Parse natural language into commands"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.command_patterns = self._compile_patterns()
        
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for common commands"""
        patterns = {
            'create_file': re.compile(
                r'(?:create|make|new)\s+(?:a\s+)?(?:file|document)\s+(?:called\s+|named\s+)?(.+)',
                re.IGNORECASE
            ),
            'open_file': re.compile(
                r'(?:open|show|display|go to)\s+(?:file\s+)?(.+)',
                re.IGNORECASE
            ),
            'search': re.compile(
                r'(?:search|find|look for)\s+(.+?)(?:\s+in\s+(.+))?',
                re.IGNORECASE
            ),
            'run_command': re.compile(
                r'(?:run|execute|do)\s+(?:command\s+)?(.+)',
                re.IGNORECASE
            ),
            'git_command': re.compile(
                r'(?:git\s+)?(?:commit|push|pull|add|status|checkout|branch)',
                re.IGNORECASE
            )
        }
        return patterns
        
    def parse(self, text: str, context: CommandContext) -> Tuple[Optional[str], Dict[str, Any]]:
        """Parse text into command and parameters"""
        # Clean text
        text = text.strip()
        
        # Check for exact matches first
        for pattern_name, pattern in self.command_patterns.items():
            match = pattern.match(text)
            if match:
                params = {'groups': match.groups()}
                return pattern_name, params
                
        # Use intent classification
        intent, confidence = self.intent_classifier.classify(text)
        
        if confidence < context.confidence_threshold:
            return None, {}
            
        # Extract entities
        entities = self.intent_classifier.extract_entities(text)
        
        params = {
            'intent': intent,
            'confidence': confidence,
            'entities': entities,
            'raw_text': text
        }
        
        return intent, params


class ConversationManager:
    """Manage multi-turn conversations"""
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.conversations = {}
        self.active_topics = {}
        
    def add_turn(self, session_id: str, role: str, text: str):
        """Add a conversation turn"""
        if session_id not in self.conversations:
            self.conversations[session_id] = deque(maxlen=self.max_history)
            
        turn = {
            'role': role,
            'text': text,
            'timestamp': time.time()
        }
        
        self.conversations[session_id].append(turn)
        
        # Update active topic
        self._update_topic(session_id, text)
        
    def get_context(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation context"""
        if session_id not in self.conversations:
            return []
            
        return list(self.conversations[session_id])
        
    def resolve_reference(self, session_id: str, reference: str) -> Optional[str]:
        """Resolve contextual references like 'it', 'that file', etc."""
        context = self.get_context(session_id)
        
        if not context:
            return None
            
        # Look for recent mentions
        for turn in reversed(context):
            if turn['role'] == 'user':
                # Check for file references
                files = re.findall(r'[\w\-/\\]+\.\w+', turn['text'])
                if files and reference in ['it', 'that', 'the file', 'that file']:
                    return files[-1]
                    
                # Check for code references
                if reference in ['that function', 'the function', 'it']:
                    functions = re.findall(r'\b\w+\s*\(', turn['text'])
                    if functions:
                        return functions[-1].rstrip('(')
                        
        return None
        
    def _update_topic(self, session_id: str, text: str):
        """Update the active conversation topic"""
        # Simple topic extraction - in production, use more sophisticated methods
        keywords = ['file', 'function', 'class', 'project', 'debug', 'error']
        
        for keyword in keywords:
            if keyword in text.lower():
                self.active_topics[session_id] = keyword
                break


class CommandHistory:
    """Track and learn from command history"""
    
    def __init__(self, db_path: str = "voice_commands.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                command TEXT,
                parameters TEXT,
                success BOOLEAN,
                timestamp REAL,
                confidence REAL,
                noise_level REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS command_shortcuts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shortcut TEXT UNIQUE,
                full_command TEXT,
                usage_count INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
        
    def add_command(self, session_id: str, command: str, parameters: Dict[str, Any],
                   success: bool, confidence: float, noise_level: float):
        """Add command to history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO command_history 
            (session_id, command, parameters, success, timestamp, confidence, noise_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, command, json.dumps(parameters), success,
            time.time(), confidence, noise_level
        ))
        
        conn.commit()
        conn.close()
        
    def get_frequent_commands(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most frequently used commands"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT command, COUNT(*) as count
            FROM command_history
            WHERE success = 1
            GROUP BY command
            ORDER BY count DESC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
        
    def suggest_command(self, partial: str) -> List[str]:
        """Suggest commands based on partial input"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT command
            FROM command_history
            WHERE command LIKE ? AND success = 1
            ORDER BY timestamp DESC
            LIMIT 5
        """, (f"{partial}%",))
        
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return results


class NexusVoiceCommands:
    """Main voice command processor"""
    
    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self.parser = CommandParser()
        self.conversation_manager = ConversationManager()
        self.history = CommandHistory()
        
        # Command shortcuts
        self.shortcuts = {}
        
        # Confirmation state
        self.pending_confirmations = {}
        
        # Background noise handling
        self.noise_threshold = 0.3
        self.noise_handlers = {
            'low': self._handle_low_noise,
            'medium': self._handle_medium_noise,
            'high': self._handle_high_noise
        }
        
        # Register default commands
        self._register_default_commands()
        
    def _register_default_commands(self):
        """Register built-in commands"""
        # File commands
        self.register_command(Command(
            name="create_file",
            pattern=r"create (?:a )?file (?:called |named )?(.+)",
            category=CommandCategory.FILE,
            handler=self._handle_create_file,
            aliases=["make file", "new file"],
            parameters=["filename"],
            description="Create a new file",
            confirmation=ConfirmationLevel.OPTIONAL,
            examples=["create file main.py", "make a file called index.html"]
        ))
        
        # Code commands
        self.register_command(Command(
            name="search_code",
            pattern=r"(?:search|find) (.+?)(?: in (.+))?",
            category=CommandCategory.SEARCH,
            handler=self._handle_search_code,
            aliases=["look for", "find"],
            parameters=["query", "scope"],
            description="Search for code",
            examples=["search function getData", "find TODO in current file"]
        ))
        
        # System commands
        self.register_command(Command(
            name="run_command",
            pattern=r"(?:run|execute) (.+)",
            category=CommandCategory.SYSTEM,
            handler=self._handle_run_command,
            parameters=["command"],
            description="Run a system command",
            confirmation=ConfirmationLevel.REQUIRED,
            priority=CommandPriority.HIGH,
            examples=["run npm install", "execute python test.py"]
        ))
        
        # Git commands
        self.register_command(Command(
            name="git_status",
            pattern=r"(?:git )?status",
            category=CommandCategory.PROJECT,
            handler=self._handle_git_status,
            aliases=["what changed", "show changes"],
            description="Show git status",
            shortcuts=["gs", "status"]
        ))
        
        # Help commands
        self.register_command(Command(
            name="help",
            pattern=r"help(?: with (.+))?",
            category=CommandCategory.HELP,
            handler=self._handle_help,
            parameters=["topic"],
            description="Get help",
            examples=["help", "help with file commands"]
        ))
        
    def register_command(self, command: Command):
        """Register a new command"""
        self.commands[command.name] = command
        
        # Register aliases
        for alias in command.aliases:
            self.commands[alias] = command
            
        # Register shortcuts
        for shortcut in command.shortcuts:
            self.shortcuts[shortcut] = command.name
            
        logger.info(f"Registered command: {command.name}")
        
    async def process_command(self, text: str, context: CommandContext) -> CommandResult:
        """Process a voice command"""
        # Add to conversation history
        self.conversation_manager.add_turn(
            context.session_id, 'user', text
        )
        
        # Handle noise
        if context.noise_level > self.noise_threshold:
            return await self._handle_noisy_command(text, context)
            
        # Check for shortcuts
        if text.lower() in self.shortcuts:
            command_name = self.shortcuts[text.lower()]
            command = self.commands[command_name]
            return await self._execute_command(command, {}, context)
            
        # Check for pending confirmations
        if context.session_id in self.pending_confirmations:
            return await self._handle_confirmation(text, context)
            
        # Parse command
        command_type, params = self.parser.parse(text, context)
        
        if not command_type:
            # Try fuzzy matching
            command = self._fuzzy_match_command(text)
            if command:
                return await self._execute_command(command, params, context)
            else:
                return CommandResult(
                    success=False,
                    response="I didn't understand that command. Can you rephrase?",
                    follow_up="Try saying 'help' to see available commands."
                )
                
        # Find and execute command
        if command_type in self.commands:
            command = self.commands[command_type]
            return await self._execute_command(command, params, context)
        else:
            # Handle by intent
            return await self._handle_by_intent(command_type, params, context)
            
    async def _execute_command(self, command: Command, params: Dict[str, Any],
                             context: CommandContext) -> CommandResult:
        """Execute a command"""
        # Check confirmation requirement
        if command.confirmation in [ConfirmationLevel.REQUIRED, ConfirmationLevel.DANGEROUS]:
            return await self._request_confirmation(command, params, context)
            
        try:
            # Execute command handler
            result = await command.handler(params, context)
            
            # Record in history
            self.history.add_command(
                context.session_id,
                command.name,
                params,
                result.success,
                params.get('confidence', 1.0),
                context.noise_level
            )
            
            # Add response to conversation
            self.conversation_manager.add_turn(
                context.session_id, 'assistant', result.response
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return CommandResult(
                success=False,
                response=f"Error executing command: {str(e)}"
            )
            
    async def _request_confirmation(self, command: Command, params: Dict[str, Any],
                                  context: CommandContext) -> CommandResult:
        """Request confirmation for a command"""
        confirmation_key = f"{context.session_id}:{command.name}"
        
        self.pending_confirmations[confirmation_key] = {
            'command': command,
            'params': params,
            'timestamp': time.time()
        }
        
        danger_warning = ""
        if command.confirmation == ConfirmationLevel.DANGEROUS:
            danger_warning = " This is a potentially dangerous operation."
            
        return CommandResult(
            success=True,
            response=f"Are you sure you want to {command.description}?{danger_warning} Say 'yes' to confirm or 'no' to cancel.",
            speak_response=True
        )
        
    async def _handle_confirmation(self, text: str, context: CommandContext) -> CommandResult:
        """Handle confirmation response"""
        confirmation_key = list(self.pending_confirmations.keys())[0]
        confirmation = self.pending_confirmations[confirmation_key]
        
        if text.lower() in ['yes', 'confirm', 'ok', 'sure', 'go ahead']:
            # Execute confirmed command
            del self.pending_confirmations[confirmation_key]
            return await self._execute_command(
                confirmation['command'],
                confirmation['params'],
                context
            )
        else:
            # Cancel command
            del self.pending_confirmations[confirmation_key]
            return CommandResult(
                success=True,
                response="Command cancelled.",
                speak_response=True
            )
            
    async def _handle_noisy_command(self, text: str, context: CommandContext) -> CommandResult:
        """Handle commands in noisy environment"""
        noise_level = 'high' if context.noise_level > 0.7 else 'medium'
        handler = self.noise_handlers.get(noise_level, self._handle_medium_noise)
        
        return await handler(text, context)
        
    async def _handle_low_noise(self, text: str, context: CommandContext) -> CommandResult:
        """Handle low noise - process normally"""
        return await self.process_command(text, context)
        
    async def _handle_medium_noise(self, text: str, context: CommandContext) -> CommandResult:
        """Handle medium noise - request confirmation"""
        return CommandResult(
            success=True,
            response=f"I heard '{text}'. Is that correct?",
            speak_response=True
        )
        
    async def _handle_high_noise(self, text: str, context: CommandContext) -> CommandResult:
        """Handle high noise - use alternative input"""
        return CommandResult(
            success=False,
            response="It's too noisy. Please type the command or wait for quieter conditions.",
            show_visual=True
        )
        
    def _fuzzy_match_command(self, text: str) -> Optional[Command]:
        """Find best matching command using fuzzy matching"""
        command_names = list(self.commands.keys())
        
        # Get best match
        match = process.extractOne(text.lower(), command_names, scorer=fuzz.ratio)
        
        if match and match[1] > 70:  # 70% similarity threshold
            return self.commands[match[0]]
            
        return None
        
    async def _handle_by_intent(self, intent: str, params: Dict[str, Any],
                              context: CommandContext) -> CommandResult:
        """Handle command by intent classification"""
        intent_handlers = {
            'create_file': self._handle_create_file,
            'open_file': self._handle_open_file,
            'search_code': self._handle_search_code,
            'ask_question': self._handle_chat,
            'debug_code': self._handle_debug
        }
        
        handler = intent_handlers.get(intent)
        if handler:
            return await handler(params, context)
        else:
            return CommandResult(
                success=False,
                response=f"I understand you want to {intent.replace('_', ' ')}, but I'm not sure how to do that yet."
            )
            
    # Command handlers
    async def _handle_create_file(self, params: Dict[str, Any], 
                                context: CommandContext) -> CommandResult:
        """Handle file creation"""
        entities = params.get('entities', {})
        files = entities.get('FILE', [])
        
        if not files and 'groups' in params:
            files = params['groups']
            
        if not files:
            return CommandResult(
                success=False,
                response="What should I call the file?",
                follow_up="Please specify a filename with extension"
            )
            
        filename = files[0] if isinstance(files, list) else files
        
        # Simulate file creation
        return CommandResult(
            success=True,
            response=f"Created file '{filename}'",
            data={'filename': filename}
        )
        
    async def _handle_open_file(self, params: Dict[str, Any],
                              context: CommandContext) -> CommandResult:
        """Handle file opening"""
        # Implementation
        return CommandResult(
            success=True,
            response="Opening file..."
        )
        
    async def _handle_search_code(self, params: Dict[str, Any],
                                context: CommandContext) -> CommandResult:
        """Handle code search"""
        query = params.get('raw_text', '')
        
        return CommandResult(
            success=True,
            response=f"Searching for '{query}'...",
            show_visual=True
        )
        
    async def _handle_run_command(self, params: Dict[str, Any],
                                context: CommandContext) -> CommandResult:
        """Handle system command execution"""
        command = params.get('groups', [None])[0]
        
        if not command:
            return CommandResult(
                success=False,
                response="What command should I run?"
            )
            
        return CommandResult(
            success=True,
            response=f"Running command: {command}",
            data={'command': command}
        )
        
    async def _handle_git_status(self, params: Dict[str, Any],
                               context: CommandContext) -> CommandResult:
        """Handle git status"""
        return CommandResult(
            success=True,
            response="Checking git status...",
            show_visual=True
        )
        
    async def _handle_help(self, params: Dict[str, Any],
                         context: CommandContext) -> CommandResult:
        """Handle help request"""
        topic = params.get('groups', [None])[0]
        
        if topic:
            # Topic-specific help
            relevant_commands = [
                cmd for cmd in self.commands.values()
                if topic.lower() in cmd.category.value.lower()
            ]
        else:
            # General help
            relevant_commands = list(self.commands.values())[:10]
            
        help_text = "Available commands:\n"
        for cmd in relevant_commands:
            help_text += f"- {cmd.name}: {cmd.description}\n"
            if cmd.examples:
                help_text += f"  Example: {cmd.examples[0]}\n"
                
        return CommandResult(
            success=True,
            response=help_text,
            show_visual=True
        )
        
    async def _handle_chat(self, params: Dict[str, Any],
                         context: CommandContext) -> CommandResult:
        """Handle conversational queries"""
        return CommandResult(
            success=True,
            response="I'm here to help. What would you like to know?"
        )
        
    async def _handle_debug(self, params: Dict[str, Any],
                          context: CommandContext) -> CommandResult:
        """Handle debug requests"""
        return CommandResult(
            success=True,
            response="Starting debugger...",
            show_visual=True
        )
        
    def learn_shortcut(self, shortcut: str, full_command: str):
        """Learn a new command shortcut"""
        self.shortcuts[shortcut.lower()] = full_command
        
        # Save to database
        conn = sqlite3.connect(self.history.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO command_shortcuts (shortcut, full_command, usage_count)
            VALUES (?, ?, COALESCE((SELECT usage_count FROM command_shortcuts WHERE shortcut = ?), 0))
        """, (shortcut, full_command, shortcut))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Learned shortcut: '{shortcut}' -> '{full_command}'")
        
    def get_command_suggestions(self, context: CommandContext) -> List[str]:
        """Get contextual command suggestions"""
        suggestions = []
        
        # Based on current directory
        if context.current_directory:
            if any(f.endswith('.py') for f in Path(context.current_directory).glob('*')):
                suggestions.extend(["run python tests", "search TODO"])
                
        # Based on recent commands
        recent_commands = self.history.get_frequent_commands(5)
        suggestions.extend([cmd[0] for cmd in recent_commands])
        
        # Based on conversation context
        topic = self.conversation_manager.active_topics.get(context.session_id)
        if topic == 'debug':
            suggestions.extend(["set breakpoint", "show variables", "continue"])
            
        return suggestions[:5]  # Limit suggestions


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Initialize command processor
        processor = NexusVoiceCommands()
        
        # Create context
        context = CommandContext(
            user_id="user123",
            session_id="session456",
            timestamp=time.time(),
            current_directory="/home/user/project"
        )
        
        # Test commands
        test_commands = [
            "create a file called main.py",
            "search for TODO comments",
            "run npm install",
            "git status",
            "help with file commands"
        ]
        
        for cmd in test_commands:
            print(f"\nCommand: {cmd}")
            result = await processor.process_command(cmd, context)
            print(f"Response: {result.response}")
            print(f"Success: {result.success}")
            
        # Test conversation context
        print("\n--- Testing conversation context ---")
        
        await processor.process_command("open config.json", context)
        result = await processor.process_command("search for port in it", context)
        print(f"Context-aware response: {result.response}")
        
        # Test shortcuts
        processor.learn_shortcut("gs", "git status")
        result = await processor.process_command("gs", context)
        print(f"Shortcut response: {result.response}")
        
        # Get suggestions
        suggestions = processor.get_command_suggestions(context)
        print(f"\nSuggestions: {suggestions}")
        
    # Run example
    asyncio.run(main())