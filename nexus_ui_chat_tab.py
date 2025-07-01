#!/usr/bin/env python3
"""
NEXUS Chat Interface Tab - Real-time AI assistant with advanced features
"""

import asyncio
import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

import aiofiles
from PIL import Image
from prompt_toolkit import Application, HTML
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import WordCompleter, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.filters import Condition, has_focus
from prompt_toolkit.formatted_text import FormattedText, StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import (
    Container, HSplit, VSplit, Window, WindowAlign,
    ConditionalContainer, ScrollablePane, FloatContainer, Float
)
from prompt_toolkit.layout.controls import FormattedTextControl, BufferControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.processors import (
    Processor, Transformation, HighlightSearchProcessor,
    HighlightSelectionProcessor
)
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType
from prompt_toolkit.search import SearchState
from prompt_toolkit.styles import Style, merge_styles
from prompt_toolkit.widgets import (
    TextArea, Button, Label, Frame, Box,
    SearchToolbar, MenuContainer, MenuItem
)
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.styles import get_style_by_name
import markdown
from markdown.extensions import fenced_code, tables, toc

from nexus_voice_engine import VoiceEngine
from nexus_vision_processor import VisionProcessor
from nexus_code_intelligence import CodeIntelligence


class MessageType(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    CODE = "code"
    IMAGE = "image"
    ERROR = "error"


@dataclass
class ChatMessage:
    type: MessageType
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: datetime.now().isoformat())


class CommandSuggester(Completer):
    """Smart command suggestions based on context"""
    
    def __init__(self, code_intelligence: CodeIntelligence):
        self.code_intelligence = code_intelligence
        self.commands = {
            "/help": "Show available commands",
            "/clear": "Clear chat history",
            "/export": "Export conversation",
            "/voice": "Toggle voice input",
            "/paste": "Paste image/screenshot",
            "/code": "Insert code block",
            "/search": "Search conversation",
            "/settings": "Open chat settings",
            "/model": "Switch AI model",
            "/context": "Add context files"
        }
    
    def get_completions(self, document: Document, complete_event) -> List[Completion]:
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        
        if document.text.startswith('/'):
            # Command completions
            for cmd, desc in self.commands.items():
                if cmd.startswith(word_before_cursor):
                    yield Completion(
                        cmd[len(word_before_cursor):],
                        display_meta=desc
                    )
        else:
            # Context-aware code completions
            completions = self.code_intelligence.get_completions(
                document.text,
                document.cursor_position
            )
            for comp in completions:
                yield Completion(
                    comp['text'],
                    start_position=-len(word_before_cursor),
                    display_meta=comp.get('type', '')
                )


class MarkdownProcessor(Processor):
    """Process markdown in chat messages"""
    
    def __init__(self):
        self.md = markdown.Markdown(extensions=[
            'fenced_code',
            'tables',
            'toc',
            'nl2br',
            'sane_lists',
            'codehilite'
        ])
    
    def apply_transformation(self, transformation_input) -> Transformation:
        fragments = transformation_input.fragments
        result_fragments = []
        
        for style, text, *rest in fragments:
            if '```' in text:
                # Handle code blocks
                parts = text.split('```')
                for i, part in enumerate(parts):
                    if i % 2 == 0:
                        # Regular text
                        result_fragments.append((style, part, *rest))
                    else:
                        # Code block
                        lines = part.split('\n')
                        lang = lines[0] if lines else ''
                        code = '\n'.join(lines[1:]) if len(lines) > 1 else ''
                        
                        try:
                            lexer = get_lexer_by_name(lang) if lang else guess_lexer(code)
                            highlighted = self._highlight_code(code, lexer)
                            result_fragments.extend(highlighted)
                        except:
                            result_fragments.append(('class:code', code, *rest))
            else:
                # Process other markdown elements
                html = self.md.convert(text)
                styled_text = self._html_to_styled(html)
                result_fragments.extend(styled_text)
        
        return Transformation(result_fragments)
    
    def _highlight_code(self, code: str, lexer) -> StyleAndTextTuples:
        """Syntax highlight code"""
        from pygments import highlight
        from pygments.formatters import TerminalFormatter
        
        highlighted = highlight(code, lexer, TerminalFormatter())
        return [('class:code', highlighted)]
    
    def _html_to_styled(self, html: str) -> StyleAndTextTuples:
        """Convert HTML to styled text tuples"""
        # Simple HTML to styled text conversion
        result = []
        text = re.sub(r'<[^>]+>', '', html)  # Strip HTML tags for now
        
        # Apply basic styling based on markdown elements
        if text.startswith('#'):
            level = len(text.split()[0])
            result.append((f'class:heading{level}', text.lstrip('#').strip()))
        elif text.startswith('*') or text.startswith('-'):
            result.append(('class:list', text))
        elif text.startswith('>'):
            result.append(('class:quote', text.lstrip('>').strip()))
        else:
            result.append(('', text))
        
        return result


class ChatInterface:
    """Advanced chat interface with all features"""
    
    def __init__(self, parent_app=None):
        self.parent_app = parent_app
        self.messages: List[ChatMessage] = []
        self.history_index = -1
        self.voice_engine = VoiceEngine()
        self.vision_processor = VisionProcessor()
        self.code_intelligence = CodeIntelligence()
        self.voice_enabled = False
        self.current_model = "claude-3-opus"
        self.context_files: List[Path] = []
        
        # UI components
        self.input_buffer = Buffer(
            multiline=True,
            completer=CommandSuggester(self.code_intelligence)
        )
        self.search_toolbar = SearchToolbar()
        self.message_display = FormattedTextControl(
            text=self._format_messages,
            focusable=True,
            show_cursor=False
        )
        
        # Key bindings
        self.kb = KeyBindings()
        self._setup_key_bindings()
        
        # Styles
        self.style = Style.from_dict({
            'chat.user': '#00aa00 bold',
            'chat.assistant': '#0088ff',
            'chat.system': '#888888 italic',
            'chat.error': '#ff0000 bold',
            'chat.timestamp': '#666666',
            'chat.code': 'bg:#1e1e1e #cccccc',
            'chat.heading1': '#ffffff bold underline',
            'chat.heading2': '#ffffff bold',
            'chat.heading3': '#ffffff italic',
            'chat.list': '#cccccc',
            'chat.quote': '#888888 italic',
            'chat.link': '#0088ff underline',
            'chat.image': 'bg:#333333 #00ff00',
            'input.prompt': '#00aa00 bold',
            'status.bar': 'bg:#444444 #ffffff',
            'button': 'bg:#222222 #ffffff',
            'button.focused': 'bg:#444444 #ffffff bold',
        })
    
    def _setup_key_bindings(self):
        """Setup keyboard shortcuts"""
        
        @self.kb.add('c-c')
        def copy_selection(event):
            """Copy selected text"""
            # TODO: Implement clipboard support
            pass
        
        @self.kb.add('c-v')
        async def paste_content(event):
            """Paste text or image"""
            # Check clipboard for images
            if self.vision_processor.has_image_in_clipboard():
                await self._handle_image_paste()
            else:
                # Regular text paste
                event.app.current_buffer.paste_clipboard_data(
                    event.app.clipboard.get_data()
                )
        
        @self.kb.add('c-enter')
        async def send_message(event):
            """Send message"""
            await self._send_message()
        
        @self.kb.add('c-l')
        def clear_chat(event):
            """Clear chat history"""
            self.messages.clear()
            event.app.invalidate()
        
        @self.kb.add('c-e')
        async def export_chat(event):
            """Export conversation"""
            await self._export_conversation()
        
        @self.kb.add('c-r')
        def toggle_voice(event):
            """Toggle voice input"""
            self.voice_enabled = not self.voice_enabled
            if self.voice_enabled:
                asyncio.create_task(self._start_voice_input())
        
        @self.kb.add('up')
        def previous_history(event):
            """Navigate to previous message in history"""
            if self.history_index < len(self.messages) - 1:
                self.history_index += 1
                self._load_history_message()
        
        @self.kb.add('down')
        def next_history(event):
            """Navigate to next message in history"""
            if self.history_index > -1:
                self.history_index -= 1
                self._load_history_message()
        
        @self.kb.add('c-/')
        def show_commands(event):
            """Show available commands"""
            self._show_command_palette()
    
    def _format_messages(self) -> StyleAndTextTuples:
        """Format all messages for display"""
        result = []
        
        for msg in self.messages:
            # Timestamp
            result.append(('class:chat.timestamp', 
                         f"[{msg.timestamp.strftime('%H:%M:%S')}] "))
            
            # Message type indicator
            if msg.type == MessageType.USER:
                result.append(('class:chat.user', "You: "))
            elif msg.type == MessageType.ASSISTANT:
                result.append(('class:chat.assistant', "Assistant: "))
            elif msg.type == MessageType.SYSTEM:
                result.append(('class:chat.system', "System: "))
            elif msg.type == MessageType.ERROR:
                result.append(('class:chat.error', "Error: "))
            
            # Message content
            if msg.type == MessageType.CODE:
                # Format code block
                lang = msg.metadata.get('language', 'python')
                result.append(('class:chat.code', f"```{lang}\n"))
                result.append(('class:chat.code', msg.content))
                result.append(('class:chat.code', "\n```"))
            elif msg.type == MessageType.IMAGE:
                # Format image indicator
                result.append(('class:chat.image', 
                             f"[Image: {msg.metadata.get('filename', 'image.png')}]"))
                if 'description' in msg.metadata:
                    result.append(('', f"\n{msg.metadata['description']}"))
            else:
                # Process markdown
                processor = MarkdownProcessor()
                transformed = processor.apply_transformation(
                    type('Input', (), {'fragments': [('', msg.content)]})()
                )
                result.extend(transformed.fragments)
            
            result.append(('', '\n\n'))
        
        return result
    
    async def _send_message(self):
        """Send the current message"""
        text = self.input_buffer.text.strip()
        if not text:
            return
        
        # Check for commands
        if text.startswith('/'):
            await self._handle_command(text)
            self.input_buffer.reset()
            return
        
        # Add user message
        self.messages.append(ChatMessage(
            type=MessageType.USER,
            content=text
        ))
        
        # Clear input
        self.input_buffer.reset()
        
        # Get AI response
        response = await self._get_ai_response(text)
        self.messages.append(ChatMessage(
            type=MessageType.ASSISTANT,
            content=response
        ))
        
        # Voice output if enabled
        if self.voice_enabled:
            await self.voice_engine.speak(response)
        
        # Update display
        if self.parent_app:
            self.parent_app.invalidate()
    
    async def _handle_command(self, command: str):
        """Handle chat commands"""
        cmd = command.split()[0]
        args = command[len(cmd):].strip()
        
        if cmd == '/help':
            self.messages.append(ChatMessage(
                type=MessageType.SYSTEM,
                content=self._get_help_text()
            ))
        elif cmd == '/clear':
            self.messages.clear()
        elif cmd == '/export':
            await self._export_conversation()
        elif cmd == '/voice':
            self.voice_enabled = not self.voice_enabled
            status = "enabled" if self.voice_enabled else "disabled"
            self.messages.append(ChatMessage(
                type=MessageType.SYSTEM,
                content=f"Voice input {status}"
            ))
        elif cmd == '/paste':
            await self._handle_image_paste()
        elif cmd == '/code':
            await self._insert_code_block(args)
        elif cmd == '/search':
            self.search_toolbar.search_state.text = args
        elif cmd == '/model':
            await self._switch_model(args)
        elif cmd == '/context':
            await self._add_context_files(args)
        else:
            self.messages.append(ChatMessage(
                type=MessageType.ERROR,
                content=f"Unknown command: {cmd}"
            ))
    
    async def _get_ai_response(self, prompt: str) -> str:
        """Get response from AI assistant"""
        try:
            # Include context files
            context = ""
            for file in self.context_files:
                if file.exists():
                    async with aiofiles.open(file, 'r') as f:
                        content = await f.read()
                        context += f"\n\n--- {file.name} ---\n{content}"
            
            # Build full prompt
            full_prompt = prompt
            if context:
                full_prompt = f"Context files:{context}\n\nUser query: {prompt}"
            
            # Get response from AI
            # TODO: Integrate with actual AI API
            response = f"I understand your request about: {prompt}\n\n"
            response += "Here's my response with **markdown** support and `inline code`."
            
            return response
        except Exception as e:
            return f"Error getting AI response: {str(e)}"
    
    async def _handle_image_paste(self):
        """Handle image paste from clipboard"""
        try:
            image_data = await self.vision_processor.get_clipboard_image()
            if image_data:
                # Save image temporarily
                temp_file = tempfile.NamedTemporaryFile(
                    suffix='.png', delete=False
                )
                image_data.save(temp_file.name)
                
                # Analyze image
                description = await self.vision_processor.analyze_image(
                    temp_file.name
                )
                
                self.messages.append(ChatMessage(
                    type=MessageType.IMAGE,
                    content=temp_file.name,
                    metadata={
                        'filename': os.path.basename(temp_file.name),
                        'description': description
                    }
                ))
            else:
                self.messages.append(ChatMessage(
                    type=MessageType.ERROR,
                    content="No image found in clipboard"
                ))
        except Exception as e:
            self.messages.append(ChatMessage(
                type=MessageType.ERROR,
                content=f"Error pasting image: {str(e)}"
            ))
    
    async def _export_conversation(self):
        """Export conversation to file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"nexus_chat_{timestamp}.md"
            
            content = "# NEXUS Chat Export\n\n"
            content += f"Exported: {datetime.now().isoformat()}\n\n"
            
            for msg in self.messages:
                content += f"## {msg.type.value.title()} - {msg.timestamp.strftime('%H:%M:%S')}\n\n"
                content += msg.content + "\n\n"
            
            async with aiofiles.open(filename, 'w') as f:
                await f.write(content)
            
            self.messages.append(ChatMessage(
                type=MessageType.SYSTEM,
                content=f"Conversation exported to {filename}"
            ))
        except Exception as e:
            self.messages.append(ChatMessage(
                type=MessageType.ERROR,
                content=f"Error exporting conversation: {str(e)}"
            ))
    
    async def _start_voice_input(self):
        """Start voice input listening"""
        try:
            while self.voice_enabled:
                # Listen for voice input
                text = await self.voice_engine.listen()
                if text:
                    # Add to input buffer
                    self.input_buffer.text = text
                    # Auto-send if ends with period or question mark
                    if text.rstrip().endswith(('.', '?', '!')):
                        await self._send_message()
                
                await asyncio.sleep(0.1)
        except Exception as e:
            self.messages.append(ChatMessage(
                type=MessageType.ERROR,
                content=f"Voice input error: {str(e)}"
            ))
            self.voice_enabled = False
    
    def _load_history_message(self):
        """Load message from history"""
        if 0 <= self.history_index < len(self.messages):
            msg = self.messages[-(self.history_index + 1)]
            if msg.type == MessageType.USER:
                self.input_buffer.text = msg.content
    
    def _show_command_palette(self):
        """Show command palette"""
        # TODO: Implement floating command palette
        pass
    
    def _get_help_text(self) -> str:
        """Get help text for commands"""
        return """
# NEXUS Chat Commands

- `/help` - Show this help message
- `/clear` - Clear chat history
- `/export` - Export conversation to file
- `/voice` - Toggle voice input (Ctrl+R)
- `/paste` - Paste image from clipboard (Ctrl+V)
- `/code [language]` - Insert code block
- `/search [query]` - Search conversation
- `/model [name]` - Switch AI model
- `/context [files]` - Add context files

## Keyboard Shortcuts

- `Ctrl+Enter` - Send message
- `Ctrl+C` - Copy selected text
- `Ctrl+V` - Paste text/image
- `Ctrl+L` - Clear chat
- `Ctrl+E` - Export conversation
- `Ctrl+R` - Toggle voice input
- `Ctrl+/` - Show command palette
- `Up/Down` - Navigate message history
"""
    
    async def _switch_model(self, model_name: str):
        """Switch AI model"""
        available_models = [
            "claude-3-opus",
            "claude-3-sonnet", 
            "gpt-4",
            "gpt-3.5-turbo"
        ]
        
        if model_name in available_models:
            self.current_model = model_name
            self.messages.append(ChatMessage(
                type=MessageType.SYSTEM,
                content=f"Switched to model: {model_name}"
            ))
        else:
            self.messages.append(ChatMessage(
                type=MessageType.ERROR,
                content=f"Unknown model: {model_name}\nAvailable: {', '.join(available_models)}"
            ))
    
    async def _add_context_files(self, files_str: str):
        """Add context files"""
        files = files_str.split()
        added = []
        
        for file_path in files:
            path = Path(file_path)
            if path.exists():
                self.context_files.append(path)
                added.append(path.name)
            else:
                self.messages.append(ChatMessage(
                    type=MessageType.ERROR,
                    content=f"File not found: {file_path}"
                ))
        
        if added:
            self.messages.append(ChatMessage(
                type=MessageType.SYSTEM,
                content=f"Added context files: {', '.join(added)}"
            ))
    
    async def _insert_code_block(self, language: str):
        """Insert a code block"""
        if not language:
            language = "python"
        
        self.input_buffer.text = f"```{language}\n\n```"
        # Move cursor inside code block
        self.input_buffer.cursor_position = len(f"```{language}\n")
    
    def create_layout(self) -> Container:
        """Create the chat tab layout"""
        # Message display area
        message_window = Window(
            content=self.message_display,
            wrap_lines=True,
            style='class:chat.messages'
        )
        
        # Input area with prompt
        input_prompt = Window(
            FormattedTextControl(
                text=lambda: [
                    ('class:input.prompt', '>>> '),
                    ('class:input.prompt', '[Voice]' if self.voice_enabled else ''),
                ]
            ),
            width=10,
            dont_extend_width=True
        )
        
        input_field = Window(
            BufferControl(
                buffer=self.input_buffer,
                include_default_input_processors=True,
                preview_search=True,
                search_buffer=self.search_toolbar.search_state
            ),
            wrap_lines=True,
            height=Dimension(min=3, max=10)
        )
        
        # Status bar
        status_bar = Window(
            FormattedTextControl(
                text=lambda: [
                    ('class:status.bar', f' Model: {self.current_model} '),
                    ('class:status.bar', f' | Context: {len(self.context_files)} files '),
                    ('class:status.bar', f' | Messages: {len(self.messages)} '),
                    ('class:status.bar', f' | Voice: {"ON" if self.voice_enabled else "OFF"} '),
                ]
            ),
            height=1,
            style='class:status.bar'
        )
        
        # Quick action buttons
        buttons = VSplit([
            Button("Send", handler=lambda: asyncio.create_task(self._send_message())),
            Button("Clear", handler=lambda: self.messages.clear()),
            Button("Export", handler=lambda: asyncio.create_task(self._export_conversation())),
            Button("Voice", handler=lambda: setattr(self, 'voice_enabled', not self.voice_enabled)),
        ], padding=1)
        
        # Main layout
        return HSplit([
            # Message display
            Frame(
                ScrollablePane(message_window),
                title="NEXUS Chat"
            ),
            # Search toolbar
            ConditionalContainer(
                self.search_toolbar,
                filter=has_focus(self.search_toolbar.search_state)
            ),
            # Input area
            VSplit([
                input_prompt,
                input_field
            ]),
            # Buttons and status
            buttons,
            status_bar
        ])


def create_chat_tab(parent_app=None) -> Container:
    """Factory function to create chat tab"""
    chat = ChatInterface(parent_app)
    return chat.create_layout()