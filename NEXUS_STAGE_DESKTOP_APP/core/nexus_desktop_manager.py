#!/usr/bin/env python3
"""
NEXUS 2.0 Desktop Manager
Chat and preview window for the working environment
Integrates with Stage Manager to provide a unified workspace
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import os

class PreviewType(Enum):
    """Types of content that can be previewed"""
    CODE = "code"
    MARKDOWN = "markdown"
    IMAGE = "image"
    TERMINAL = "terminal"
    BROWSER = "browser"
    DATA = "data"
    LOGS = "logs"
    CHAT = "chat"

@dataclass
class ChatMessage:
    """Represents a message in the chat"""
    id: str
    sender: str  # agent_id or "user"
    content: str
    timestamp: datetime
    message_type: str = "text"  # text, code, image, file
    metadata: Dict[str, Any] = None
    
    def to_dict(self):
        return {
            "id": self.id,
            "sender": self.sender,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "message_type": self.message_type,
            "metadata": self.metadata or {}
        }

@dataclass
class PreviewPane:
    """Represents a preview pane in the desktop"""
    id: str
    title: str
    preview_type: PreviewType
    content: Any
    position: Dict[str, int]  # x, y, width, height in desktop
    is_active: bool = True
    metadata: Dict[str, Any] = None
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "preview_type": self.preview_type.value,
            "position": self.position,
            "is_active": self.is_active,
            "metadata": self.metadata or {}
        }

class DesktopManager:
    """Manages the desktop environment with chat and preview capabilities"""
    
    def __init__(self, stage_manager=None):
        self.stage_manager = stage_manager
        self.chat_history: List[ChatMessage] = []
        self.preview_panes: Dict[str, PreviewPane] = {}
        self.active_preview_id: Optional[str] = None
        self.desktop_layout = {
            "chat": {"x": 0, "y": 0, "width": 400, "height": "100%"},
            "preview": {"x": 400, "y": 0, "width": "calc(100% - 400px)", "height": "100%"}
        }
        self.message_handlers: Dict[str, Callable] = {}
        self.preview_handlers: Dict[PreviewType, Callable] = {}
        self.command_history: List[str] = []
        self.workspace_context = {}
        
    def add_chat_message(self, sender: str, content: str, 
                        message_type: str = "text", 
                        metadata: Optional[Dict[str, Any]] = None) -> ChatMessage:
        """Add a message to the chat"""
        import uuid
        
        message = ChatMessage(
            id=str(uuid.uuid4()),
            sender=sender,
            content=content,
            timestamp=datetime.now(),
            message_type=message_type,
            metadata=metadata or {}
        )
        
        self.chat_history.append(message)
        
        # Trigger any registered handlers
        if sender in self.message_handlers:
            self.message_handlers[sender](message)
            
        return message
        
    def create_preview_pane(self, title: str, preview_type: PreviewType,
                          content: Any = None, 
                          position: Optional[Dict[str, int]] = None) -> PreviewPane:
        """Create a new preview pane"""
        import uuid
        
        pane_id = str(uuid.uuid4())
        
        if position is None:
            position = self._calculate_preview_position()
            
        pane = PreviewPane(
            id=pane_id,
            title=title,
            preview_type=preview_type,
            content=content,
            position=position,
            metadata={}
        )
        
        self.preview_panes[pane_id] = pane
        
        # Set as active if it's the first pane
        if self.active_preview_id is None:
            self.active_preview_id = pane_id
            
        return pane
        
    def _calculate_preview_position(self) -> Dict[str, int]:
        """Calculate position for new preview pane"""
        # Stack panes or tile them
        num_panes = len(self.preview_panes)
        if num_panes == 0:
            return {"x": 0, "y": 0, "width": "100%", "height": "100%"}
        elif num_panes == 1:
            # Split horizontally
            return {"x": 0, "y": "50%", "width": "100%", "height": "50%"}
        else:
            # Tile in grid
            col = num_panes % 2
            row = num_panes // 2
            return {
                "x": f"{col * 50}%",
                "y": f"{row * 50}%",
                "width": "50%",
                "height": "50%"
            }
            
    def update_preview_content(self, pane_id: str, content: Any):
        """Update the content of a preview pane"""
        if pane_id in self.preview_panes:
            self.preview_panes[pane_id].content = content
            
            # Trigger preview handler if registered
            pane = self.preview_panes[pane_id]
            if pane.preview_type in self.preview_handlers:
                self.preview_handlers[pane.preview_type](pane)
                
    def switch_preview_pane(self, pane_id: str):
        """Switch to a different preview pane"""
        if pane_id in self.preview_panes:
            self.active_preview_id = pane_id
            
    def close_preview_pane(self, pane_id: str):
        """Close a preview pane"""
        if pane_id in self.preview_panes:
            del self.preview_panes[pane_id]
            
            # Update active pane if needed
            if self.active_preview_id == pane_id:
                self.active_preview_id = next(iter(self.preview_panes), None)
                
    def register_message_handler(self, sender: str, handler: Callable):
        """Register a handler for messages from a specific sender"""
        self.message_handlers[sender] = handler
        
    def register_preview_handler(self, preview_type: PreviewType, handler: Callable):
        """Register a handler for a specific preview type"""
        self.preview_handlers[preview_type] = handler
        
    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a command in the desktop environment"""
        self.command_history.append(command)
        
        # Parse command
        parts = command.split()
        if not parts:
            return {"error": "Empty command"}
            
        cmd = parts[0].lower()
        args = parts[1:]
        
        # Built-in commands
        if cmd == "preview":
            return self._handle_preview_command(args)
        elif cmd == "chat":
            return self._handle_chat_command(args)
        elif cmd == "agent":
            return self._handle_agent_command(args)
        elif cmd == "layout":
            return self._handle_layout_command(args)
        elif cmd == "workspace":
            return self._handle_workspace_command(args)
        else:
            return {"error": f"Unknown command: {cmd}"}
            
    def _handle_preview_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle preview-related commands"""
        if not args:
            return {"error": "Preview command requires subcommand"}
            
        subcmd = args[0]
        
        if subcmd == "open":
            if len(args) < 3:
                return {"error": "Usage: preview open <type> <title>"}
            preview_type = PreviewType(args[1])
            title = " ".join(args[2:])
            pane = self.create_preview_pane(title, preview_type)
            return {"success": True, "pane_id": pane.id}
            
        elif subcmd == "close":
            if len(args) < 2:
                return {"error": "Usage: preview close <pane_id>"}
            self.close_preview_pane(args[1])
            return {"success": True}
            
        elif subcmd == "list":
            return {
                "panes": [pane.to_dict() for pane in self.preview_panes.values()]
            }
            
        return {"error": f"Unknown preview subcommand: {subcmd}"}
        
    def _handle_chat_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle chat-related commands"""
        if not args:
            return {"error": "Chat command requires subcommand"}
            
        subcmd = args[0]
        
        if subcmd == "send":
            if len(args) < 2:
                return {"error": "Usage: chat send <message>"}
            message = " ".join(args[1:])
            msg = self.add_chat_message("user", message)
            return {"success": True, "message_id": msg.id}
            
        elif subcmd == "history":
            limit = int(args[1]) if len(args) > 1 else 50
            messages = self.chat_history[-limit:]
            return {
                "messages": [msg.to_dict() for msg in messages]
            }
            
        elif subcmd == "clear":
            self.chat_history.clear()
            return {"success": True}
            
        return {"error": f"Unknown chat subcommand: {subcmd}"}
        
    def _handle_agent_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle agent-related commands via stage manager"""
        if not self.stage_manager:
            return {"error": "No stage manager connected"}
            
        if not args:
            return {"error": "Agent command requires subcommand"}
            
        subcmd = args[0]
        
        if subcmd == "list":
            layout = self.stage_manager.get_stage_layout()
            return {"agents": layout}
            
        elif subcmd == "focus":
            if len(args) < 2:
                return {"error": "Usage: agent focus <agent_id>"}
            self.stage_manager.switch_to_agent(args[1])
            return {"success": True}
            
        elif subcmd == "create":
            if len(args) < 3:
                return {"error": "Usage: agent create <type> <name>"}
            agent_type = args[1]
            name = " ".join(args[2:])
            window = self.stage_manager.create_agent_window(name, agent_type)
            return {"success": True, "agent_id": window.id}
            
        return {"error": f"Unknown agent subcommand: {subcmd}"}
        
    def _handle_layout_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle layout commands"""
        if not args:
            return {"layout": self.desktop_layout}
            
        subcmd = args[0]
        
        if subcmd == "set":
            if len(args) < 3:
                return {"error": "Usage: layout set <component> <settings>"}
            # Parse and update layout
            return {"success": True}
            
        elif subcmd == "reset":
            self.desktop_layout = {
                "chat": {"x": 0, "y": 0, "width": 400, "height": "100%"},
                "preview": {"x": 400, "y": 0, "width": "calc(100% - 400px)", "height": "100%"}
            }
            return {"success": True}
            
        return {"error": f"Unknown layout subcommand: {subcmd}"}
        
    def _handle_workspace_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle workspace commands"""
        if not args:
            return {"workspace": self.workspace_context}
            
        subcmd = args[0]
        
        if subcmd == "save":
            if len(args) < 2:
                return {"error": "Usage: workspace save <filename>"}
            self.save_workspace(args[1])
            return {"success": True}
            
        elif subcmd == "load":
            if len(args) < 2:
                return {"error": "Usage: workspace load <filename>"}
            self.load_workspace(args[1])
            return {"success": True}
            
        elif subcmd == "set":
            if len(args) < 3:
                return {"error": "Usage: workspace set <key> <value>"}
            key = args[1]
            value = " ".join(args[2:])
            self.workspace_context[key] = value
            return {"success": True}
            
        return {"error": f"Unknown workspace subcommand: {subcmd}"}
        
    def get_desktop_state(self) -> Dict[str, Any]:
        """Get current desktop state"""
        return {
            "layout": self.desktop_layout,
            "chat": {
                "message_count": len(self.chat_history),
                "recent_messages": [
                    msg.to_dict() for msg in self.chat_history[-10:]
                ]
            },
            "preview": {
                "active_pane_id": self.active_preview_id,
                "panes": [pane.to_dict() for pane in self.preview_panes.values()]
            },
            "workspace": self.workspace_context,
            "stage_manager_connected": self.stage_manager is not None
        }
        
    def save_workspace(self, filename: str):
        """Save current workspace configuration"""
        workspace_data = {
            "timestamp": datetime.now().isoformat(),
            "desktop_layout": self.desktop_layout,
            "chat_history": [msg.to_dict() for msg in self.chat_history],
            "preview_panes": {
                id: pane.to_dict() for id, pane in self.preview_panes.items()
            },
            "active_preview_id": self.active_preview_id,
            "workspace_context": self.workspace_context,
            "command_history": self.command_history[-100:]  # Last 100 commands
        }
        
        # Include stage manager state if connected
        if self.stage_manager:
            workspace_data["stage_layout"] = self.stage_manager.get_stage_layout()
            
        with open(filename, 'w') as f:
            json.dump(workspace_data, f, indent=2)
            
    def load_workspace(self, filename: str):
        """Load a saved workspace configuration"""
        if not os.path.exists(filename):
            return
            
        with open(filename, 'r') as f:
            workspace_data = json.load(f)
            
        # Restore desktop layout
        self.desktop_layout = workspace_data.get("desktop_layout", self.desktop_layout)
        
        # Restore chat history
        self.chat_history.clear()
        for msg_data in workspace_data.get("chat_history", []):
            msg = ChatMessage(
                id=msg_data["id"],
                sender=msg_data["sender"],
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                message_type=msg_data.get("message_type", "text"),
                metadata=msg_data.get("metadata", {})
            )
            self.chat_history.append(msg)
            
        # Restore preview panes
        self.preview_panes.clear()
        for pane_id, pane_data in workspace_data.get("preview_panes", {}).items():
            pane = PreviewPane(
                id=pane_data["id"],
                title=pane_data["title"],
                preview_type=PreviewType(pane_data["preview_type"]),
                content=None,  # Content not persisted
                position=pane_data["position"],
                is_active=pane_data.get("is_active", True),
                metadata=pane_data.get("metadata", {})
            )
            self.preview_panes[pane_id] = pane
            
        self.active_preview_id = workspace_data.get("active_preview_id")
        self.workspace_context = workspace_data.get("workspace_context", {})
        self.command_history = workspace_data.get("command_history", [])

# Integration with Stage Manager
def create_integrated_workspace(max_agents: int = 4) -> tuple:
    """Create an integrated workspace with both managers"""
    from nexus_stage_manager import StageManager
    
    stage_manager = StageManager(max_active_agents=max_agents)
    desktop_manager = DesktopManager(stage_manager=stage_manager)
    
    # Set up default preview handlers
    def code_preview_handler(pane: PreviewPane):
        # Syntax highlight code
        pass
        
    def terminal_preview_handler(pane: PreviewPane):
        # Handle terminal output
        pass
        
    desktop_manager.register_preview_handler(PreviewType.CODE, code_preview_handler)
    desktop_manager.register_preview_handler(PreviewType.TERMINAL, terminal_preview_handler)
    
    return stage_manager, desktop_manager

if __name__ == "__main__":
    # Example usage
    stage_mgr, desktop_mgr = create_integrated_workspace()
    
    # Create some agents
    dev_agent = stage_mgr.create_agent_window("Developer", "developer")
    research_agent = stage_mgr.create_agent_window("Researcher", "researcher")
    
    # Add chat messages
    desktop_mgr.add_chat_message("user", "Create a Python web scraper")
    desktop_mgr.add_chat_message(dev_agent.id, "I'll create a web scraper for you.")
    
    # Create preview panes
    code_pane = desktop_mgr.create_preview_pane("scraper.py", PreviewType.CODE)
    terminal_pane = desktop_mgr.create_preview_pane("Terminal Output", PreviewType.TERMINAL)
    
    # Get desktop state
    state = desktop_mgr.get_desktop_state()
    print(json.dumps(state, indent=2))