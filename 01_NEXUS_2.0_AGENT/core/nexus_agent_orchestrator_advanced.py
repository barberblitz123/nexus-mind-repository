#!/usr/bin/env python3
"""
NEXUS 2.0 Advanced Agent Orchestrator
Manages multiple autonomous agents working together with advanced coordination
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import networkx as nx
from collections import defaultdict

from nexus_autonomous_agent import (
    AutonomousMANUS, Task, TaskPriority, TaskStatus, 
    AgentCapability, create_code_analyzer_agent,
    create_debugger_agent, create_file_manager_agent,
    create_terminal_agent
)
from nexus_stage_manager import StageManager, AgentType
from nexus_desktop_manager import DesktopManager

class CoordinationStrategy(Enum):
    """Strategies for coordinating agents"""
    PARALLEL = "parallel"          # All agents work independently
    SEQUENTIAL = "sequential"      # Agents work one after another
    COLLABORATIVE = "collaborative" # Agents share information and coordinate
    HIERARCHICAL = "hierarchical"  # Master-worker pattern
    CONSENSUS = "consensus"        # Agents vote on decisions
    SWARM = "swarm"               # Emergent behavior from simple rules

class MessageType(Enum):
    """Types of messages agents can exchange"""
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    QUERY = "query"
    SHARE_KNOWLEDGE = "share_knowledge"
    TASK_ASSIGNMENT = "task_assignment"
    STATUS_UPDATE = "status_update"
    HELP_REQUEST = "help_request"

@dataclass
class AgentMessage:
    """Message exchanged between agents"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    sender_id: str = ""
    recipient_id: Optional[str] = None  # None means broadcast
    message_type: MessageType = MessageType.BROADCAST
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    requires_response: bool = False
    priority: int = 1

@dataclass
class SharedKnowledge:
    """Knowledge shared among agents"""
    discoveries: Dict[str, Any] = field(default_factory=dict)
    file_mappings: Dict[str, List[str]] = field(default_factory=dict)  # file -> [agent_ids]
    task_history: List[Dict[str, Any]] = field(default_factory=list)
    error_patterns: List[Dict[str, Any]] = field(default_factory=list)
    success_patterns: List[Dict[str, Any]] = field(default_factory=list)
    agent_specializations: Dict[str, Set[str]] = field(default_factory=dict)

class AgentOrchestrator:
    """Advanced orchestrator for managing multiple autonomous agents"""
    
    def __init__(self, max_agents: int = 10):
        self.orchestrator_id = str(uuid.uuid4())[:8]
        self.agents: Dict[str, AutonomousMANUS] = {}
        self.max_agents = max_agents
        self.stage_manager = StageManager()
        self.desktop_manager = DesktopManager()
        self.shared_knowledge = SharedKnowledge()
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.task_graph = nx.DiGraph()
        self.coordination_strategy = CoordinationStrategy.COLLABORATIVE
        self.running = False
        self.agent_tasks: Dict[str, asyncio.Task] = {}
        
        # Performance metrics
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "messages_exchanged": 0,
            "avg_task_time": 0,
            "agent_utilization": {}
        }
        
        # Initialize subsystems
        self._initialize_subsystems()
        
    def _initialize_subsystems(self):
        """Initialize orchestrator subsystems"""
        # Create chat interface
        self.desktop_manager.create_chat_interface()
        
        # Add system message
        self.desktop_manager.add_chat_message(
            "Orchestrator",
            f"NEXUS Agent Orchestrator initialized (ID: {self.orchestrator_id})",
            "system"
        )
        
    def create_agent(self, name: str, agent_type: str = "general") -> AutonomousMANUS:
        """Create a new agent with specific type"""
        if len(self.agents) >= self.max_agents:
            raise ValueError(f"Maximum number of agents ({self.max_agents}) reached")
            
        # Create specialized agent based on type
        if agent_type == "code_analyzer":
            agent = create_code_analyzer_agent(name)
        elif agent_type == "debugger":
            agent = create_debugger_agent(name)
        elif agent_type == "file_manager":
            agent = create_file_manager_agent(name)
        elif agent_type == "terminal":
            agent = create_terminal_agent(name)
        else:
            agent = AutonomousMANUS(name=name)
            
        # Set output callback to route through orchestrator
        agent.output_callback = lambda msg: self._handle_agent_output(agent.agent_id, msg)
        
        # Register agent
        self.agents[agent.agent_id] = agent
        
        # Create visual representation in Stage Manager
        agent_type_enum = {
            "code_analyzer": AgentType.CODE_ANALYZER,
            "debugger": AgentType.DEBUG_ASSISTANT,
            "file_manager": AgentType.FILE_MANAGER,
            "terminal": AgentType.TERMINAL_RUNNER
        }.get(agent_type, AgentType.SEARCH_AGENT)
        
        self.stage_manager.create_agent_window(name, agent_type_enum)
        
        # Initialize metrics
        self.metrics["agent_utilization"][agent.agent_id] = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "uptime": 0,
            "efficiency": 1.0
        }
        
        # Announce creation
        self.desktop_manager.add_chat_message(
            "Orchestrator",
            f"Created agent: {name} ({agent_type}) with ID {agent.agent_id}",
            "system"
        )
        
        return agent
        
    def remove_agent(self, agent_id: str):
        """Remove an agent from the orchestrator"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.stop()
            
            # Cancel agent task if running
            if agent_id in self.agent_tasks:
                self.agent_tasks[agent_id].cancel()
                del self.agent_tasks[agent_id]
                
            del self.agents[agent_id]
            self.stage_manager.remove_agent(agent_id)
            
            self.desktop_manager.add_chat_message(
                "Orchestrator",
                f"Removed agent: {agent.name}",
                "system"
            )
            
    def _handle_agent_output(self, agent_id: str, message: str):
        """Handle output from an agent"""
        # Route to Stage Manager window
        agent_window = self.stage_manager.get_agent(agent_id)
        if agent_window:
            agent_window.update_output(message)
            
        # Also add to chat if important
        if any(keyword in message.lower() for keyword in ["error", "completed", "failed", "found"]):
            agent = self.agents.get(agent_id)
            if agent:
                self.desktop_manager.add_chat_message(agent.name, message, "agent")
                
    async def send_message(self, message: AgentMessage):
        """Send a message to agent(s)"""
        await self.message_queue.put(message)
        self.metrics["messages_exchanged"] += 1
        
    async def broadcast_to_agents(self, content: Dict[str, Any], message_type: MessageType = MessageType.BROADCAST):
        """Broadcast a message to all agents"""
        message = AgentMessage(
            sender_id=self.orchestrator_id,
            message_type=message_type,
            content=content
        )
        await self.send_message(message)
        
    async def assign_task_to_agent(self, agent_id: str, task: Task):
        """Assign a task to a specific agent"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.task_queue.append(task)
            
            # Send task assignment message
            message = AgentMessage(
                sender_id=self.orchestrator_id,
                recipient_id=agent_id,
                message_type=MessageType.TASK_ASSIGNMENT,
                content={"task": task.__dict__}
            )
            await self.send_message(message)
            
    async def distribute_task(self, task: Task) -> List[str]:
        """Distribute a task among agents based on capabilities"""
        assigned_agents = []
        
        # Analyze task requirements
        required_capabilities = self._analyze_task_requirements(task)
        
        # Find suitable agents
        for agent_id, agent in self.agents.items():
            agent_capabilities = agent.capabilities
            if any(cap in agent_capabilities for cap in required_capabilities):
                await self.assign_task_to_agent(agent_id, task)
                assigned_agents.append(agent_id)
                
                # Update task graph
                self.task_graph.add_node(task.id, task=task, assigned_to=agent_id)
                
        if not assigned_agents and self.agents:
            # No specialized agent found, assign to least busy
            least_busy = min(self.agents.items(), key=lambda x: len(x[1].task_queue))
            await self.assign_task_to_agent(least_busy[0], task)
            assigned_agents.append(least_busy[0])
            
        return assigned_agents
        
    def _analyze_task_requirements(self, task: Task) -> Set[AgentCapability]:
        """Analyze what capabilities a task requires"""
        requirements = set()
        desc_lower = task.description.lower()
        
        # Map keywords to capabilities
        capability_keywords = {
            AgentCapability.CODE_ANALYSIS: ["analyze", "review", "understand", "ast", "parse"],
            AgentCapability.DEBUGGING: ["debug", "error", "fix", "bug", "traceback"],
            AgentCapability.FILE_OPERATIONS: ["file", "create", "write", "read", "save"],
            AgentCapability.TERMINAL_EXECUTION: ["run", "execute", "command", "terminal", "shell"],
            AgentCapability.SEARCH: ["search", "find", "locate", "grep", "query"],
            AgentCapability.TESTING: ["test", "unittest", "pytest", "coverage"],
            AgentCapability.DOCUMENTATION: ["document", "docs", "readme", "comment"],
            AgentCapability.REFACTORING: ["refactor", "restructure", "optimize", "improve"]
        }
        
        for capability, keywords in capability_keywords.items():
            if any(keyword in desc_lower for keyword in keywords):
                requirements.add(capability)
                
        return requirements or {AgentCapability.CODE_ANALYSIS}  # Default
        
    async def coordinate_agents(self):
        """Main coordination loop"""
        while self.running:
            # Process messages
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=0.1)
                await self._process_message(message)
            except asyncio.TimeoutError:
                pass
                
            # Check agent health
            for agent_id, agent in list(self.agents.items()):
                if not agent.running and agent_id in self.agent_tasks:
                    # Restart stopped agent
                    self.agent_tasks[agent_id] = asyncio.create_task(agent.run())
                    
            # Update metrics
            self._update_metrics()
            
            await asyncio.sleep(0.1)
            
    async def _process_message(self, message: AgentMessage):
        """Process a message"""
        if message.recipient_id:
            # Direct message
            if message.recipient_id in self.agents:
                await self._deliver_to_agent(message.recipient_id, message)
        else:
            # Broadcast
            for agent_id in self.agents:
                if agent_id != message.sender_id:
                    await self._deliver_to_agent(agent_id, message)
                    
    async def _deliver_to_agent(self, agent_id: str, message: AgentMessage):
        """Deliver a message to an agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return
            
        # Handle different message types
        if message.message_type == MessageType.SHARE_KNOWLEDGE:
            # Update agent's memory with shared knowledge
            knowledge = message.content.get("knowledge", {})
            for key, value in knowledge.items():
                agent.memory.remember(key, value, "shared")
                
        elif message.message_type == MessageType.HELP_REQUEST:
            # Agent needs help with a task
            help_task = message.content.get("task")
            if help_task and self._can_agent_help(agent, help_task):
                agent.add_task(f"Help with: {help_task}", f"Assist {message.sender_id} with {help_task}")
                
    def _can_agent_help(self, agent: AutonomousMANUS, task_description: str) -> bool:
        """Check if an agent can help with a task"""
        required_caps = self._analyze_task_requirements(
            Task(description=task_description)
        )
        return bool(required_caps.intersection(agent.capabilities))
        
    def _update_metrics(self):
        """Update performance metrics"""
        total_completed = 0
        total_failed = 0
        
        for agent_id, agent in self.agents.items():
            agent_metrics = self.metrics["agent_utilization"][agent_id]
            
            # Count completed/failed tasks
            completed = sum(1 for t in agent.memory.short_term 
                          if t.get("type") == "output" and "Completed task" in t.get("message", ""))
            failed = sum(1 for t in agent.memory.short_term 
                       if t.get("type") == "output" and "Task failed" in t.get("message", ""))
                       
            agent_metrics["tasks_completed"] = completed
            agent_metrics["tasks_failed"] = failed
            
            total_completed += completed
            total_failed += failed
            
        self.metrics["tasks_completed"] = total_completed
        self.metrics["tasks_failed"] = total_failed
        
    async def execute_complex_task(self, description: str, priority: TaskPriority = TaskPriority.MEDIUM):
        """Execute a complex task that may require multiple agents"""
        # Create main task
        main_task = Task(
            name=f"Complex: {description[:30]}",
            description=description,
            priority=priority
        )
        
        self.desktop_manager.add_chat_message(
            "User",
            description,
            "user"
        )
        
        # Determine coordination strategy based on task
        if "parallel" in description.lower():
            self.coordination_strategy = CoordinationStrategy.PARALLEL
        elif "sequential" in description.lower():
            self.coordination_strategy = CoordinationStrategy.SEQUENTIAL
            
        # Break down into subtasks
        subtasks = await self._decompose_complex_task(main_task)
        
        # Distribute subtasks
        if self.coordination_strategy == CoordinationStrategy.PARALLEL:
            # Assign all subtasks at once
            for subtask in subtasks:
                await self.distribute_task(subtask)
                
        elif self.coordination_strategy == CoordinationStrategy.SEQUENTIAL:
            # Assign subtasks one by one
            for subtask in subtasks:
                assigned = await self.distribute_task(subtask)
                if assigned:
                    # Wait for completion before next
                    await self._wait_for_task_completion(subtask.id)
                    
        elif self.coordination_strategy == CoordinationStrategy.COLLABORATIVE:
            # Share task with all agents for collaborative solving
            await self.broadcast_to_agents({
                "task": main_task.__dict__,
                "subtasks": [t.__dict__ for t in subtasks]
            }, MessageType.TASK_ASSIGNMENT)
            
        return main_task
        
    async def _decompose_complex_task(self, task: Task) -> List[Task]:
        """Decompose a complex task into subtasks"""
        subtasks = []
        desc_lower = task.description.lower()
        
        # Pattern matching for common complex tasks
        if "analyze" in desc_lower and "optimize" in desc_lower:
            subtasks.extend([
                Task(name="Initial Analysis", description="Analyze current state", priority=task.priority),
                Task(name="Identify Issues", description="Find performance bottlenecks", priority=task.priority),
                Task(name="Generate Solutions", description="Propose optimizations", priority=task.priority),
                Task(name="Implement Changes", description="Apply optimizations", priority=task.priority),
                Task(name="Verify Results", description="Test and measure improvements", priority=task.priority)
            ])
            
        elif "refactor" in desc_lower:
            subtasks.extend([
                Task(name="Code Analysis", description="Understand current code structure", priority=task.priority),
                Task(name="Identify Patterns", description="Find refactoring opportunities", priority=task.priority),
                Task(name="Plan Refactoring", description="Design new structure", priority=task.priority),
                Task(name="Execute Refactoring", description="Implement changes", priority=task.priority),
                Task(name="Test Changes", description="Ensure functionality preserved", priority=task.priority)
            ])
            
        else:
            # Generic decomposition
            subtasks.extend([
                Task(name="Understand", description=f"Understand: {task.description}", priority=task.priority),
                Task(name="Plan", description="Create execution plan", priority=task.priority),
                Task(name="Execute", description="Execute the plan", priority=task.priority),
                Task(name="Verify", description="Verify results", priority=task.priority)
            ])
            
        # Link subtasks in graph
        for i, subtask in enumerate(subtasks):
            self.task_graph.add_node(subtask.id, task=subtask, parent=task.id)
            if i > 0:
                self.task_graph.add_edge(subtasks[i-1].id, subtask.id)
                
        return subtasks
        
    async def _wait_for_task_completion(self, task_id: str, timeout: int = 60):
        """Wait for a task to complete"""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout:
            # Check if task is completed in any agent
            for agent in self.agents.values():
                for task in agent.memory.short_term:
                    if (task.get("type") == "output" and 
                        f"Completed task" in task.get("message", "") and
                        task_id in task.get("message", "")):
                        return True
                        
            await asyncio.sleep(0.5)
            
        return False
        
    async def start(self):
        """Start the orchestrator and all agents"""
        self.running = True
        
        # Start all agents
        for agent_id, agent in self.agents.items():
            self.agent_tasks[agent_id] = asyncio.create_task(agent.run())
            
        # Start coordination loop
        coordination_task = asyncio.create_task(self.coordinate_agents())
        
        self.desktop_manager.add_chat_message(
            "Orchestrator",
            f"Started with {len(self.agents)} agents",
            "system"
        )
        
        return coordination_task
        
    def stop(self):
        """Stop the orchestrator and all agents"""
        self.running = False
        
        # Stop all agents
        for agent in self.agents.values():
            agent.stop()
            
        self.desktop_manager.add_chat_message(
            "Orchestrator",
            "Shutting down all agents",
            "system"
        )
        
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        agent_statuses = {}
        for agent_id, agent in self.agents.items():
            agent_statuses[agent_id] = agent.get_status()
            
        return {
            "orchestrator_id": self.orchestrator_id,
            "running": self.running,
            "num_agents": len(self.agents),
            "coordination_strategy": self.coordination_strategy.value,
            "metrics": self.metrics,
            "agents": agent_statuses,
            "task_graph_size": len(self.task_graph.nodes),
            "shared_knowledge_items": len(self.shared_knowledge.discoveries)
        }

# Helper functions for common orchestration patterns
async def create_analysis_team(orchestrator: AgentOrchestrator) -> List[str]:
    """Create a team of agents for code analysis"""
    agents = []
    
    # Create specialized agents
    analyzer = orchestrator.create_agent("Senior Analyst", "code_analyzer")
    debugger = orchestrator.create_agent("Bug Hunter", "debugger")
    documenter = orchestrator.create_agent("Doc Writer", "file_manager")
    
    agents.extend([analyzer.agent_id, debugger.agent_id, documenter.agent_id])
    
    # Share knowledge between them
    await orchestrator.broadcast_to_agents({
        "team": "analysis",
        "members": agents
    }, MessageType.SHARE_KNOWLEDGE)
    
    return agents

async def create_development_team(orchestrator: AgentOrchestrator) -> List[str]:
    """Create a team of agents for development tasks"""
    agents = []
    
    # Create specialized agents
    architect = orchestrator.create_agent("Architect", "code_analyzer")
    developer = orchestrator.create_agent("Developer", "file_manager")
    tester = orchestrator.create_agent("Tester", "terminal")
    reviewer = orchestrator.create_agent("Reviewer", "code_analyzer")
    
    agents.extend([
        architect.agent_id, developer.agent_id, 
        tester.agent_id, reviewer.agent_id
    ])
    
    return agents

# Demo function
async def demo_orchestrator():
    """Demonstrate orchestrator capabilities"""
    orchestrator = AgentOrchestrator(max_agents=5)
    
    # Create a diverse team
    print("Creating agent team...")
    await create_analysis_team(orchestrator)
    
    # Start orchestrator
    orchestration_task = await orchestrator.start()
    
    # Execute a complex task
    print("\nExecuting complex task...")
    await orchestrator.execute_complex_task(
        "Analyze the NEXUS codebase and create a comprehensive report with optimization suggestions",
        TaskPriority.HIGH
    )
    
    # Let it run for a bit
    await asyncio.sleep(10)
    
    # Get status
    status = orchestrator.get_status()
    print(f"\nOrchestrator Status:")
    print(json.dumps(status, indent=2))
    
    # Stop
    orchestrator.stop()
    await orchestration_task

if __name__ == "__main__":
    asyncio.run(demo_orchestrator())