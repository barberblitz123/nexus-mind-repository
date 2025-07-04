#!/usr/bin/env python3
"""
NEXUS 2.0 Stage Manager
Manages multiple autonomous agents, each in their own window
Inspired by macOS Stage Manager but for AI agents
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json

class AgentState(Enum):
    """States an agent can be in"""
    IDLE = "idle"
    WORKING = "working"
    THINKING = "thinking"
    COMMUNICATING = "communicating"
    PAUSED = "paused"
    ERROR = "error"

@dataclass
class AgentWindow:
    """Represents a single agent window in the stage"""
    id: str
    name: str
    agent_type: str
    state: AgentState
    position: Dict[str, int]  # x, y coordinates
    size: Dict[str, int]      # width, height
    z_index: int              # stacking order
    created_at: datetime
    last_active: datetime
    current_task: Optional[str] = None
    memory_context: Dict[str, Any] = None
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "agent_type": self.agent_type,
            "state": self.state.value,
            "position": self.position,
            "size": self.size,
            "z_index": self.z_index,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "current_task": self.current_task,
            "memory_context": self.memory_context
        }

class StageManager:
    """Manages multiple agent windows like macOS Stage Manager"""
    
    def __init__(self, max_active_agents: int = 4):
        self.max_active_agents = max_active_agents
        self.agent_windows: Dict[str, AgentWindow] = {}
        self.active_stage: List[str] = []  # IDs of agents in active stage
        self.side_stage: List[str] = []    # IDs of agents in side stage
        self.minimized_agents: List[str] = []  # IDs of minimized agents
        self.focus_agent_id: Optional[str] = None
        self.stage_groups: Dict[str, List[str]] = {}  # Named groups of agents
        
    def create_agent_window(self, name: str, agent_type: str, 
                          position: Optional[Dict[str, int]] = None,
                          size: Optional[Dict[str, int]] = None) -> AgentWindow:
        """Create a new agent window"""
        agent_id = str(uuid.uuid4())
        
        # Default position and size
        if position is None:
            position = self._calculate_next_position()
        if size is None:
            size = {"width": 800, "height": 600}
            
        window = AgentWindow(
            id=agent_id,
            name=name,
            agent_type=agent_type,
            state=AgentState.IDLE,
            position=position,
            size=size,
            z_index=len(self.agent_windows),
            created_at=datetime.now(),
            last_active=datetime.now(),
            memory_context={}
        )
        
        self.agent_windows[agent_id] = window
        self._add_to_stage(agent_id)
        
        return window
        
    def _calculate_next_position(self) -> Dict[str, int]:
        """Calculate position for new window"""
        # Cascade windows
        offset = len(self.agent_windows) * 30
        return {"x": 100 + offset, "y": 100 + offset}
        
    def _add_to_stage(self, agent_id: str):
        """Add agent to appropriate stage"""
        if len(self.active_stage) < self.max_active_agents:
            self.active_stage.append(agent_id)
            if self.focus_agent_id is None:
                self.focus_agent_id = agent_id
        else:
            self.side_stage.append(agent_id)
            
    def switch_to_agent(self, agent_id: str):
        """Switch focus to a specific agent"""
        if agent_id not in self.agent_windows:
            return
            
        # Update last active time
        self.agent_windows[agent_id].last_active = datetime.now()
        
        # Move to active stage if not there
        if agent_id in self.side_stage:
            self.side_stage.remove(agent_id)
            # Move least recently used agent to side stage
            if len(self.active_stage) >= self.max_active_agents:
                lru_agent = self._get_least_recently_used()
                if lru_agent:
                    self.active_stage.remove(lru_agent)
                    self.side_stage.append(lru_agent)
            self.active_stage.append(agent_id)
            
        # Update focus
        self.focus_agent_id = agent_id
        self._update_z_indices()
        
    def _get_least_recently_used(self) -> Optional[str]:
        """Get the least recently used agent in active stage"""
        if not self.active_stage:
            return None
            
        lru_agent = None
        oldest_time = datetime.now()
        
        for agent_id in self.active_stage:
            if agent_id != self.focus_agent_id:
                agent = self.agent_windows[agent_id]
                if agent.last_active < oldest_time:
                    oldest_time = agent.last_active
                    lru_agent = agent_id
                    
        return lru_agent
        
    def _update_z_indices(self):
        """Update z-index for proper stacking"""
        z_index = 0
        
        # Minimized agents at bottom
        for agent_id in self.minimized_agents:
            self.agent_windows[agent_id].z_index = z_index
            z_index += 1
            
        # Side stage agents
        for agent_id in self.side_stage:
            self.agent_windows[agent_id].z_index = z_index
            z_index += 1
            
        # Active stage agents
        for agent_id in self.active_stage:
            if agent_id != self.focus_agent_id:
                self.agent_windows[agent_id].z_index = z_index
                z_index += 1
                
        # Focused agent on top
        if self.focus_agent_id:
            self.agent_windows[self.focus_agent_id].z_index = z_index
            
    def minimize_agent(self, agent_id: str):
        """Minimize an agent window"""
        if agent_id not in self.agent_windows:
            return
            
        # Remove from active stages
        if agent_id in self.active_stage:
            self.active_stage.remove(agent_id)
        if agent_id in self.side_stage:
            self.side_stage.remove(agent_id)
            
        # Add to minimized
        if agent_id not in self.minimized_agents:
            self.minimized_agents.append(agent_id)
            
        # Update focus if needed
        if self.focus_agent_id == agent_id:
            self.focus_agent_id = self.active_stage[0] if self.active_stage else None
            
        self._update_z_indices()
        
    def create_stage_group(self, group_name: str, agent_ids: List[str]):
        """Create a named group of agents that work together"""
        self.stage_groups[group_name] = agent_ids
        
    def activate_stage_group(self, group_name: str):
        """Activate all agents in a group"""
        if group_name not in self.stage_groups:
            return
            
        # Clear current active stage
        for agent_id in self.active_stage[:]:
            self.side_stage.append(agent_id)
        self.active_stage.clear()
        
        # Activate group agents
        for agent_id in self.stage_groups[group_name]:
            if agent_id in self.agent_windows:
                if len(self.active_stage) < self.max_active_agents:
                    self.active_stage.append(agent_id)
                else:
                    self.side_stage.append(agent_id)
                    
        # Set focus to first agent in group
        if self.active_stage:
            self.focus_agent_id = self.active_stage[0]
            
        self._update_z_indices()
        
    def get_stage_layout(self) -> Dict[str, Any]:
        """Get current stage layout for rendering"""
        return {
            "active_stage": [
                self.agent_windows[id].to_dict() 
                for id in self.active_stage
            ],
            "side_stage": [
                self.agent_windows[id].to_dict() 
                for id in self.side_stage
            ],
            "minimized": [
                self.agent_windows[id].to_dict() 
                for id in self.minimized_agents
            ],
            "focus_agent_id": self.focus_agent_id,
            "stage_groups": self.stage_groups
        }
        
    def arrange_cascade(self):
        """Arrange active windows in cascade layout"""
        x_offset = 100
        y_offset = 100
        
        for i, agent_id in enumerate(self.active_stage):
            window = self.agent_windows[agent_id]
            window.position = {
                "x": x_offset + (i * 30),
                "y": y_offset + (i * 30)
            }
            
    def arrange_grid(self, columns: int = 2):
        """Arrange active windows in grid layout"""
        window_width = 800
        window_height = 600
        gap = 20
        
        for i, agent_id in enumerate(self.active_stage):
            row = i // columns
            col = i % columns
            
            window = self.agent_windows[agent_id]
            window.position = {
                "x": 100 + (col * (window_width + gap)),
                "y": 100 + (row * (window_height + gap))
            }
            window.size = {"width": window_width, "height": window_height}
            
    def save_stage_session(self, filename: str):
        """Save current stage configuration"""
        session_data = {
            "timestamp": datetime.now().isoformat(),
            "agent_windows": {
                id: window.to_dict() 
                for id, window in self.agent_windows.items()
            },
            "active_stage": self.active_stage,
            "side_stage": self.side_stage,
            "minimized_agents": self.minimized_agents,
            "focus_agent_id": self.focus_agent_id,
            "stage_groups": self.stage_groups
        }
        
        with open(filename, 'w') as f:
            json.dump(session_data, f, indent=2)
            
    def load_stage_session(self, filename: str):
        """Load a saved stage configuration"""
        with open(filename, 'r') as f:
            session_data = json.load(f)
            
        # Restore windows
        self.agent_windows.clear()
        for id, window_data in session_data["agent_windows"].items():
            window = AgentWindow(
                id=window_data["id"],
                name=window_data["name"],
                agent_type=window_data["agent_type"],
                state=AgentState(window_data["state"]),
                position=window_data["position"],
                size=window_data["size"],
                z_index=window_data["z_index"],
                created_at=datetime.fromisoformat(window_data["created_at"]),
                last_active=datetime.fromisoformat(window_data["last_active"]),
                current_task=window_data.get("current_task"),
                memory_context=window_data.get("memory_context", {})
            )
            self.agent_windows[id] = window
            
        # Restore stage configuration
        self.active_stage = session_data["active_stage"]
        self.side_stage = session_data["side_stage"]
        self.minimized_agents = session_data["minimized_agents"]
        self.focus_agent_id = session_data["focus_agent_id"]
        self.stage_groups = session_data["stage_groups"]

# Example agent types that can be managed
AGENT_TYPES = {
    "developer": "Development Agent",
    "researcher": "Research Agent",
    "designer": "Design Agent",
    "tester": "Testing Agent",
    "documenter": "Documentation Agent",
    "reviewer": "Code Review Agent",
    "deployer": "Deployment Agent",
    "monitor": "Monitoring Agent"
}

if __name__ == "__main__":
    # Example usage
    stage = StageManager(max_active_agents=4)
    
    # Create some agents
    dev_agent = stage.create_agent_window("Dev Agent 1", "developer")
    research_agent = stage.create_agent_window("Research Agent", "researcher")
    design_agent = stage.create_agent_window("UI Designer", "designer")
    test_agent = stage.create_agent_window("Test Runner", "tester")
    doc_agent = stage.create_agent_window("Doc Writer", "documenter")
    
    # Create a stage group
    stage.create_stage_group("frontend_team", [dev_agent.id, design_agent.id, test_agent.id])
    
    # Arrange in grid
    stage.arrange_grid(columns=2)
    
    # Get current layout
    layout = stage.get_stage_layout()
    print(json.dumps(layout, indent=2))