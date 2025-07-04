#!/usr/bin/env python3
"""
NEXUS 2.0 Autonomous Agent
Self-directed AI agent capable of working independently on tasks
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import re
import os
import subprocess
import ast
from pathlib import Path

class AgentCapability(Enum):
    """Capabilities that an agent can have"""
    CODE_ANALYSIS = "code_analysis"
    FILE_OPERATIONS = "file_operations"
    TERMINAL_EXECUTION = "terminal_execution"
    SEARCH = "search"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    LEARNING = "learning"

class TaskPriority(Enum):
    """Priority levels for tasks"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    BACKGROUND = 1

class TaskStatus(Enum):
    """Status of a task"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

@dataclass
class Task:
    """Represents a task for the agent"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    subtasks: List['Task'] = field(default_factory=list)
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentMemory:
    """Agent's memory system"""
    short_term: List[Dict[str, Any]] = field(default_factory=list)
    long_term: Dict[str, Any] = field(default_factory=dict)
    learned_patterns: List[Dict[str, Any]] = field(default_factory=list)
    file_knowledge: Dict[str, Dict] = field(default_factory=dict)
    command_history: List[str] = field(default_factory=list)
    
    def remember(self, key: str, value: Any, category: str = "general"):
        """Store information in long-term memory"""
        if category not in self.long_term:
            self.long_term[category] = {}
        self.long_term[category][key] = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "access_count": 0
        }
        
    def recall(self, key: str, category: str = "general") -> Optional[Any]:
        """Retrieve information from long-term memory"""
        if category in self.long_term and key in self.long_term[category]:
            self.long_term[category][key]["access_count"] += 1
            return self.long_term[category][key]["value"]
        return None
        
    def add_short_term(self, info: Dict[str, Any], max_items: int = 100):
        """Add to short-term memory with size limit"""
        self.short_term.append({
            **info,
            "timestamp": datetime.now().isoformat()
        })
        if len(self.short_term) > max_items:
            self.short_term = self.short_term[-max_items:]

class AutonomousMANUS:
    """
    The autonomous agent with self-directed capabilities
    MANUS = Multi-purpose Autonomous Nexus Understanding System
    """
    
    def __init__(self, agent_id: Optional[str] = None, name: Optional[str] = None):
        self.agent_id = agent_id or str(uuid.uuid4())[:8]
        self.name = name or f"MANUS-{self.agent_id}"
        self.capabilities: Set[AgentCapability] = set()
        self.memory = AgentMemory()
        self.task_queue: List[Task] = []
        self.current_task: Optional[Task] = None
        self.running = False
        self.decision_threshold = 0.7
        self.learning_rate = 0.1
        self.output_callback: Optional[Callable[[str], None]] = None
        
        # Initialize with default capabilities
        self._initialize_capabilities()
        
    def _initialize_capabilities(self):
        """Initialize agent with default capabilities"""
        self.capabilities = {
            AgentCapability.CODE_ANALYSIS,
            AgentCapability.FILE_OPERATIONS,
            AgentCapability.SEARCH,
            AgentCapability.LEARNING
        }
        
    def add_capability(self, capability: AgentCapability):
        """Add a new capability to the agent"""
        self.capabilities.add(capability)
        self.output(f"Acquired new capability: {capability.value}")
        
    def output(self, message: str, level: str = "INFO"):
        """Output a message (to UI or console)"""
        formatted_msg = f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {message}"
        
        if self.output_callback:
            self.output_callback(formatted_msg)
        else:
            print(f"[{self.name}] {formatted_msg}")
            
        # Also store in memory
        self.memory.add_short_term({
            "type": "output",
            "message": message,
            "level": level
        })
        
    async def think(self, context: str) -> str:
        """Agent's thinking process - analyze context and decide action"""
        self.output(f"Thinking about: {context[:100]}...")
        
        # Analyze context
        analysis = {
            "has_code": bool(re.search(r'(def |class |import |function |const |let |var )', context)),
            "has_error": bool(re.search(r'(error|exception|failed|traceback)', context, re.I)),
            "has_question": bool(re.search(r'(what|how|why|when|where|can you|could you|\?)', context, re.I)),
            "has_command": bool(re.search(r'(create|build|analyze|fix|refactor|test|run)', context, re.I)),
            "mentions_file": bool(re.search(r'(\.\w+|file|directory|folder)', context, re.I))
        }
        
        # Decide on action based on analysis
        if analysis["has_error"] and AgentCapability.DEBUGGING in self.capabilities:
            return "debug_error"
        elif analysis["has_code"] and AgentCapability.CODE_ANALYSIS in self.capabilities:
            return "analyze_code"
        elif analysis["has_command"]:
            return "execute_command"
        elif analysis["mentions_file"] and AgentCapability.FILE_OPERATIONS in self.capabilities:
            return "file_operation"
        elif analysis["has_question"]:
            return "answer_question"
        else:
            return "general_assistance"
            
    async def create_subtasks(self, task: Task) -> List[Task]:
        """Break down a task into subtasks"""
        subtasks = []
        
        # Analyze task description
        desc_lower = task.description.lower()
        
        # Code analysis task
        if "analyze" in desc_lower and "code" in desc_lower:
            subtasks.extend([
                Task(name="Parse code structure", description="Parse and understand code structure"),
                Task(name="Identify patterns", description="Identify design patterns and conventions"),
                Task(name="Find issues", description="Look for potential bugs or improvements"),
                Task(name="Generate report", description="Create analysis report")
            ])
            
        # File operation task
        elif any(word in desc_lower for word in ["create", "write", "save"]):
            subtasks.extend([
                Task(name="Validate path", description="Check if path is valid and accessible"),
                Task(name="Prepare content", description="Prepare file content"),
                Task(name="Write file", description="Write content to file"),
                Task(name="Verify", description="Verify file was created successfully")
            ])
            
        # Search task
        elif "search" in desc_lower or "find" in desc_lower:
            subtasks.extend([
                Task(name="Define search scope", description="Determine where to search"),
                Task(name="Execute search", description="Perform the search operation"),
                Task(name="Filter results", description="Filter and rank results"),
                Task(name="Format output", description="Format results for presentation")
            ])
            
        # Default subtasks
        else:
            subtasks.extend([
                Task(name="Understand request", description="Fully understand what is being asked"),
                Task(name="Plan approach", description="Plan how to accomplish the task"),
                Task(name="Execute", description="Execute the planned approach"),
                Task(name="Verify", description="Verify the result meets requirements")
            ])
            
        # Set subtask properties
        for subtask in subtasks:
            subtask.priority = task.priority
            subtask.metadata["parent_task"] = task.id
            
        return subtasks
        
    async def execute_task(self, task: Task) -> Any:
        """Execute a specific task"""
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        
        try:
            self.output(f"Starting task: {task.name}")
            
            # Think about the task
            action = await self.think(f"{task.name}: {task.description}")
            
            # Execute based on action
            if action == "analyze_code":
                result = await self._analyze_code(task)
            elif action == "debug_error":
                result = await self._debug_error(task)
            elif action == "file_operation":
                result = await self._file_operation(task)
            elif action == "execute_command":
                result = await self._execute_command(task)
            else:
                result = await self._general_assistance(task)
                
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            
            self.output(f"Completed task: {task.name}")
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self.output(f"Task failed: {task.name} - {e}", "ERROR")
            raise
            
    async def _analyze_code(self, task: Task) -> Dict[str, Any]:
        """Analyze code"""
        self.output("Analyzing code structure...")
        
        # Extract code from task description or metadata
        code = task.metadata.get("code", task.description)
        
        analysis = {
            "lines": len(code.split('\n')),
            "functions": len(re.findall(r'def \w+', code)),
            "classes": len(re.findall(r'class \w+', code)),
            "imports": len(re.findall(r'^import |^from ', code, re.MULTILINE)),
            "complexity": "medium",  # Simplified
            "suggestions": []
        }
        
        # Learn from this code
        self.memory.remember(f"code_analysis_{task.id}", analysis, "code_analysis")
        
        return analysis
        
    async def _debug_error(self, task: Task) -> Dict[str, Any]:
        """Debug an error"""
        self.output("Debugging error...")
        
        error_info = task.metadata.get("error", task.description)
        
        debug_result = {
            "error_type": "Unknown",
            "likely_cause": "To be determined",
            "suggestions": [
                "Check syntax",
                "Verify imports",
                "Check variable names"
            ]
        }
        
        return debug_result
        
    async def _file_operation(self, task: Task) -> Dict[str, Any]:
        """Perform file operation"""
        self.output("Performing file operation...")
        
        operation = task.metadata.get("operation", "read")
        filepath = task.metadata.get("filepath", "")
        
        result = {
            "operation": operation,
            "filepath": filepath,
            "success": True,
            "details": f"Simulated {operation} on {filepath}"
        }
        
        return result
        
    async def _execute_command(self, task: Task) -> Dict[str, Any]:
        """Execute a command"""
        self.output("Executing command...")
        
        # This is a simulation - in real implementation would execute safely
        command = task.metadata.get("command", task.description)
        
        result = {
            "command": command,
            "output": f"Simulated execution of: {command}",
            "exit_code": 0
        }
        
        # Remember command for learning
        self.memory.command_history.append(command)
        
        return result
        
    async def _general_assistance(self, task: Task) -> Dict[str, Any]:
        """Provide general assistance"""
        self.output("Providing assistance...")
        
        return {
            "response": f"Understood. Working on: {task.description}",
            "confidence": 0.8
        }
        
    def add_task(self, name: str, description: str, priority: TaskPriority = TaskPriority.MEDIUM) -> Task:
        """Add a new task to the queue"""
        task = Task(
            name=name,
            description=description,
            priority=priority
        )
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority.value, reverse=True)
        
        self.output(f"Added task: {name} (Priority: {priority.name})")
        return task
        
    async def run(self):
        """Main agent loop"""
        self.running = True
        self.output(f"Agent {self.name} starting...")
        
        while self.running:
            if self.task_queue and not self.current_task:
                # Get highest priority task
                self.current_task = self.task_queue.pop(0)
                
                # Create subtasks if needed
                if not self.current_task.subtasks:
                    self.current_task.subtasks = await self.create_subtasks(self.current_task)
                    
                # Execute subtasks
                for subtask in self.current_task.subtasks:
                    if not self.running:
                        break
                    await self.execute_task(subtask)
                    await asyncio.sleep(0.1)  # Small delay between subtasks
                    
                # Execute main task
                await self.execute_task(self.current_task)
                self.current_task = None
                
            await asyncio.sleep(0.5)  # Check for new tasks every 0.5 seconds
            
    def stop(self):
        """Stop the agent"""
        self.running = False
        self.output(f"Agent {self.name} stopping...")
        
    def learn_from_experience(self, experience: Dict[str, Any]):
        """Learn from an experience"""
        self.memory.learned_patterns.append({
            **experience,
            "timestamp": datetime.now().isoformat()
        })
        
        # Adjust decision threshold based on success/failure
        if experience.get("success", False):
            self.decision_threshold *= (1 - self.learning_rate)
        else:
            self.decision_threshold *= (1 + self.learning_rate)
            
        self.decision_threshold = max(0.5, min(0.9, self.decision_threshold))
        self.output(f"Learned from experience. Decision threshold: {self.decision_threshold:.2f}")
        
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "id": self.agent_id,
            "name": self.name,
            "running": self.running,
            "capabilities": [c.value for c in self.capabilities],
            "current_task": self.current_task.name if self.current_task else None,
            "queued_tasks": len(self.task_queue),
            "memory_items": len(self.memory.long_term),
            "learned_patterns": len(self.memory.learned_patterns),
            "decision_threshold": self.decision_threshold
        }

# Factory functions for creating specialized agents
def create_code_analyzer_agent(name: Optional[str] = None) -> AutonomousMANUS:
    """Create an agent specialized in code analysis"""
    agent = AutonomousMANUS(name=name or "CodeAnalyzer")
    agent.add_capability(AgentCapability.CODE_ANALYSIS)
    agent.add_capability(AgentCapability.DOCUMENTATION)
    agent.add_capability(AgentCapability.REFACTORING)
    return agent

def create_debugger_agent(name: Optional[str] = None) -> AutonomousMANUS:
    """Create an agent specialized in debugging"""
    agent = AutonomousMANUS(name=name or "Debugger")
    agent.add_capability(AgentCapability.DEBUGGING)
    agent.add_capability(AgentCapability.TESTING)
    agent.add_capability(AgentCapability.CODE_ANALYSIS)
    return agent

def create_file_manager_agent(name: Optional[str] = None) -> AutonomousMANUS:
    """Create an agent specialized in file operations"""
    agent = AutonomousMANUS(name=name or "FileManager")
    agent.add_capability(AgentCapability.FILE_OPERATIONS)
    agent.add_capability(AgentCapability.SEARCH)
    return agent

def create_terminal_agent(name: Optional[str] = None) -> AutonomousMANUS:
    """Create an agent specialized in terminal operations"""
    agent = AutonomousMANUS(name=name or "Terminal")
    agent.add_capability(AgentCapability.TERMINAL_EXECUTION)
    agent.add_capability(AgentCapability.FILE_OPERATIONS)
    return agent

# Demo function
async def demo_autonomous_agent():
    """Demonstrate autonomous agent capabilities"""
    # Create an agent
    agent = AutonomousMANUS(name="DemoAgent")
    
    # Add some tasks
    agent.add_task("Analyze code", "Analyze the nexus_core.py file for improvements", TaskPriority.HIGH)
    agent.add_task("Search TODO", "Search for TODO comments in the codebase", TaskPriority.MEDIUM)
    agent.add_task("Create report", "Create a summary report of findings", TaskPriority.LOW)
    
    # Run agent for a short time
    agent_task = asyncio.create_task(agent.run())
    
    # Let it work for 5 seconds
    await asyncio.sleep(5)
    
    # Stop agent
    agent.stop()
    await agent_task
    
    # Show status
    status = agent.get_status()
    print(f"\nAgent Status: {json.dumps(status, indent=2)}")

if __name__ == "__main__":
    asyncio.run(demo_autonomous_agent())