#!/usr/bin/env python3
"""
NEXUS 2.0 Stage Manager
Manages multiple autonomous agent windows in a visual grid layout
"""

from textual.app import App, ComposeResult
from textual.widgets import Static, Label, Header, Footer, Log
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.binding import Binding
from textual.reactive import reactive
from textual.css.query import NoMatches
from rich.panel import Panel
from rich.console import Console
from rich.layout import Layout
from rich.text import Text
from rich.table import Table
from datetime import datetime
from typing import Dict, List, Optional, Set
import asyncio
from enum import Enum
import uuid

class AgentType(Enum):
    """Types of agents available in the system"""
    CODE_ANALYZER = "Code Analyzer"
    FILE_MANAGER = "File Manager"
    TERMINAL_RUNNER = "Terminal Runner"
    DOC_GENERATOR = "Documentation Generator"
    TEST_RUNNER = "Test Runner"
    DEBUG_ASSISTANT = "Debug Assistant"
    SEARCH_AGENT = "Search Agent"
    REFACTOR_AGENT = "Refactoring Agent"

class AgentState(Enum):
    """States an agent can be in"""
    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    ERROR = "error"
    WAITING = "waiting"

class AgentWindow(Static):
    """Individual agent window in the Stage Manager"""
    
    def __init__(self, agent_id: str, name: str, agent_type: AgentType, **kwargs):
        super().__init__(**kwargs)
        self.agent_id = agent_id
        self.name = name
        self.agent_type = agent_type
        self.state = AgentState.IDLE
        self.output_lines = []
        self.task_queue = []
        self.current_task = None
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
    def compose(self) -> ComposeResult:
        """Compose the agent window UI"""
        yield Label(f"🤖 {self.name}", id=f"agent-header-{self.agent_id}")
        yield Log(id=f"agent-output-{self.agent_id}")
        
    def update_output(self, content: str):
        """Update the agent's output display"""
        self.last_activity = datetime.now()
        self.output_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] {content}")
        
        # Keep only last 100 lines
        if len(self.output_lines) > 100:
            self.output_lines = self.output_lines[-100:]
            
        # Update the Log content
        try:
            output_log = self.query_one(f"#agent-output-{self.agent_id}", Log)
            output_log.clear()
            for line in self.output_lines:
                output_log.write(line)
        except NoMatches:
            pass
            
    def set_state(self, state: AgentState):
        """Update the agent's state"""
        self.state = state
        self.update_output(f"State changed to: {state.value}")
        self.refresh()
        
    def add_task(self, task: str):
        """Add a task to the agent's queue"""
        self.task_queue.append(task)
        self.update_output(f"Task added: {task}")
        
    async def process_task(self, task: str):
        """Process a single task"""
        self.current_task = task
        self.set_state(AgentState.WORKING)
        self.update_output(f"Processing: {task}")
        
        # Simulate work
        await asyncio.sleep(2)
        
        self.set_state(AgentState.COMPLETED)
        self.update_output(f"Completed: {task}")
        self.current_task = None

class StageManager:
    """Manages multiple agent windows in a grid layout"""
    
    def __init__(self):
        self.agents: Dict[str, AgentWindow] = {}
        self.active_agent_id: Optional[str] = None
        self.grid_columns = 2
        self.max_agents = 8
        
    def create_agent_window(self, name: str, agent_type: AgentType) -> AgentWindow:
        """Create a new agent window"""
        if len(self.agents) >= self.max_agents:
            raise ValueError(f"Maximum number of agents ({self.max_agents}) reached")
            
        agent_id = str(uuid.uuid4())[:8]
        agent = AgentWindow(
            agent_id=agent_id,
            name=name,
            agent_type=agent_type,
            id=f"agent-{agent_id}"
        )
        
        self.agents[agent_id] = agent
        
        # Set as active if it's the first agent
        if not self.active_agent_id:
            self.active_agent_id = agent_id
            
        return agent
        
    def remove_agent(self, agent_id: str):
        """Remove an agent window"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            
            # Update active agent if needed
            if self.active_agent_id == agent_id:
                self.active_agent_id = list(self.agents.keys())[0] if self.agents else None
                
    def get_agent(self, agent_id: str) -> Optional[AgentWindow]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)
        
    def get_active_agent(self) -> Optional[AgentWindow]:
        """Get the currently active agent"""
        if self.active_agent_id:
            return self.agents.get(self.active_agent_id)
        return None
        
    def switch_to_agent(self, agent_id: str):
        """Switch focus to a specific agent"""
        if agent_id in self.agents:
            self.active_agent_id = agent_id
            
    def arrange_grid(self, columns: int = 2):
        """Arrange agents in a grid layout"""
        self.grid_columns = columns
        
    def get_agents_by_type(self, agent_type: AgentType) -> List[AgentWindow]:
        """Get all agents of a specific type"""
        return [agent for agent in self.agents.values() if agent.agent_type == agent_type]
        
    def get_agents_by_state(self, state: AgentState) -> List[AgentWindow]:
        """Get all agents in a specific state"""
        return [agent for agent in self.agents.values() if agent.state == state]
        
    def broadcast_message(self, message: str, agent_types: Optional[Set[AgentType]] = None):
        """Send a message to multiple agents"""
        targets = self.agents.values()
        if agent_types:
            targets = [a for a in targets if a.agent_type in agent_types]
            
        for agent in targets:
            agent.update_output(f"[Broadcast] {message}")
            
    def get_status_summary(self) -> Dict:
        """Get a summary of all agents' status"""
        summary = {
            "total_agents": len(self.agents),
            "by_state": {},
            "by_type": {},
            "active_agent": self.active_agent_id
        }
        
        # Count by state
        for state in AgentState:
            count = len(self.get_agents_by_state(state))
            if count > 0:
                summary["by_state"][state.value] = count
                
        # Count by type
        for agent_type in AgentType:
            count = len(self.get_agents_by_type(agent_type))
            if count > 0:
                summary["by_type"][agent_type.value] = count
                
        return summary

class StageManagerWidget(Container):
    """Textual widget for the Stage Manager"""
    
    def __init__(self, stage_manager: StageManager, **kwargs):
        super().__init__(**kwargs)
        self.stage_manager = stage_manager
        
    def compose(self) -> ComposeResult:
        """Compose the stage manager UI"""
        # Create grid layout for agents
        with Horizontal(id="agent-grid"):
            for agent_id, agent in self.stage_manager.agents.items():
                yield agent
                
    def update_layout(self):
        """Update the grid layout when agents change"""
        # This would be called when agents are added/removed
        self.refresh()
        
    async def handle_agent_task(self, agent_id: str, task: str):
        """Handle a task for a specific agent"""
        agent = self.stage_manager.get_agent(agent_id)
        if agent:
            await agent.process_task(task)

# Example usage functions
def create_code_analyzer(stage_manager: StageManager, target_file: str) -> AgentWindow:
    """Create a code analyzer agent"""
    agent = stage_manager.create_agent_window(
        name=f"Analyzer: {target_file}",
        agent_type=AgentType.CODE_ANALYZER
    )
    agent.add_task(f"Analyze {target_file}")
    return agent

def create_terminal_runner(stage_manager: StageManager, command: str) -> AgentWindow:
    """Create a terminal runner agent"""
    agent = stage_manager.create_agent_window(
        name=f"Terminal: {command[:20]}...",
        agent_type=AgentType.TERMINAL_RUNNER
    )
    agent.add_task(f"Run command: {command}")
    return agent

def create_search_agent(stage_manager: StageManager, search_query: str) -> AgentWindow:
    """Create a search agent"""
    agent = stage_manager.create_agent_window(
        name=f"Search: {search_query[:20]}...",
        agent_type=AgentType.SEARCH_AGENT
    )
    agent.add_task(f"Search for: {search_query}")
    return agent

# Demo function to show capabilities
async def demo_stage_manager():
    """Demonstrate Stage Manager capabilities"""
    sm = StageManager()
    
    # Create various agents
    analyzer = create_code_analyzer(sm, "nexus_core.py")
    runner = create_terminal_runner(sm, "python test.py")
    searcher = create_search_agent(sm, "TODO comments")
    
    # Simulate some work
    await analyzer.process_task("Analyze nexus_core.py")
    await runner.process_task("Run python test.py")
    await searcher.process_task("Search for TODO comments")
    
    # Get status
    status = sm.get_status_summary()
    print(f"Stage Manager Status: {status}")
    
if __name__ == "__main__":
    # Run demo
    asyncio.run(demo_stage_manager())