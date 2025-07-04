#!/usr/bin/env python3
"""
NEXUS 2.0 Integrated Workspace
Combines Stage Manager (agent windows) + Desktop Manager (chat/preview)
with the Terminal UI for a complete autonomous agent development environment
"""

import asyncio
import sys
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

# Fix imports for Textual compatibility
try:
    from textual import on
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.widgets import Button, Header, Footer, Static, Input, Label, Tree, TabbedContent, TabPane
    from textual.widget import Widget
    from textual.reactive import reactive
    from textual.css.query import NoMatches
except ImportError:
    print("Installing required dependencies...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "textual", "rich"])
    from textual import on
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.widgets import Button, Header, Footer, Static, Input, Label, Tree, TabbedContent, TabPane
    from textual.widget import Widget
    from textual.reactive import reactive

from rich.syntax import Syntax
from rich.text import Text
from rich.panel import Panel
from rich.table import Table

# Import our managers
from nexus_stage_manager import StageManager, AgentWindow, AgentState, AGENT_TYPES
from nexus_desktop_manager import DesktopManager, PreviewPane, PreviewType, ChatMessage
from nexus_autonomous_agent import AutonomousMANUS

class AgentWindowWidget(Widget):
    """Widget representing an agent window in the stage"""
    
    def __init__(self, agent_window: AgentWindow, is_focused: bool = False):
        super().__init__()
        self.agent_window = agent_window
        self.is_focused = is_focused
        
    def compose(self) -> ComposeResult:
        """Create the agent window display"""
        # Window frame with agent info
        frame_style = "bold green" if self.is_focused else "dim"
        
        content = f"""
[{frame_style}]╔══ {self.agent_window.name} ══╗[/{frame_style}]
Type: {self.agent_window.agent_type}
State: {self.agent_window.state.value}
Task: {self.agent_window.current_task or 'Idle'}
[{frame_style}]╚{'═' * (len(self.agent_window.name) + 6)}╝[/{frame_style}]
        """
        
        yield Static(content, classes="agent-window")

class StageView(Widget):
    """Widget showing the stage manager with agent windows"""
    
    def __init__(self, stage_manager: StageManager):
        super().__init__()
        self.stage_manager = stage_manager
        
    def compose(self) -> ComposeResult:
        """Create the stage view"""
        with Horizontal(classes="stage-container"):
            # Active stage
            with Vertical(classes="active-stage"):
                yield Label("Active Agents", classes="stage-label")
                with ScrollableContainer(classes="agent-list"):
                    for agent_id in self.stage_manager.active_stage:
                        agent = self.stage_manager.agent_windows[agent_id]
                        is_focused = agent_id == self.stage_manager.focus_agent_id
                        yield AgentWindowWidget(agent, is_focused)
                        
            # Side stage
            with Vertical(classes="side-stage"):
                yield Label("Side Stage", classes="stage-label")
                with ScrollableContainer(classes="agent-list"):
                    for agent_id in self.stage_manager.side_stage:
                        agent = self.stage_manager.agent_windows[agent_id]
                        yield AgentWindowWidget(agent, False)

class ChatView(Widget):
    """Widget for the chat interface"""
    
    def __init__(self, desktop_manager: DesktopManager):
        super().__init__()
        self.desktop_manager = desktop_manager
        
    def compose(self) -> ComposeResult:
        """Create the chat view"""
        with Vertical(classes="chat-container"):
            yield Label("Chat", classes="chat-label")
            yield ScrollableContainer(id="chat-messages", classes="chat-messages")
            yield Input(placeholder="Type a message...", id="chat-input", classes="chat-input")
            
    def on_mount(self):
        """Load chat history when mounted"""
        self.refresh_chat()
        
    def refresh_chat(self):
        """Refresh the chat display"""
        container = self.query_one("#chat-messages", ScrollableContainer)
        container.remove_children()
        
        for msg in self.desktop_manager.chat_history[-50:]:  # Last 50 messages
            style = "bold cyan" if msg.sender == "user" else "yellow"
            text = f"[{style}]{msg.sender}:[/{style}] {msg.content}"
            container.mount(Static(text, classes="chat-message"))
            
    @on(Input.Submitted, "#chat-input")
    def send_message(self, event: Input.Submitted):
        """Handle sending a chat message"""
        if event.value.strip():
            self.desktop_manager.add_chat_message("user", event.value)
            event.input.value = ""
            self.refresh_chat()

class PreviewView(Widget):
    """Widget for the preview panes"""
    
    def __init__(self, desktop_manager: DesktopManager):
        super().__init__()
        self.desktop_manager = desktop_manager
        
    def compose(self) -> ComposeResult:
        """Create the preview view"""
        with TabbedContent(classes="preview-tabs"):
            # Create tabs for each preview pane
            for pane_id, pane in self.desktop_manager.preview_panes.items():
                with TabPane(pane.title, id=f"preview-{pane_id}"):
                    yield self._create_preview_content(pane)
                    
    def _create_preview_content(self, pane: PreviewPane) -> Widget:
        """Create content widget based on preview type"""
        if pane.preview_type == PreviewType.CODE:
            # Syntax highlighted code
            if pane.content:
                syntax = Syntax(pane.content, "python", theme="monokai")
                return Static(syntax)
            return Static("No code to preview")
            
        elif pane.preview_type == PreviewType.TERMINAL:
            return Static(pane.content or "Terminal output will appear here...")
            
        elif pane.preview_type == PreviewType.MARKDOWN:
            # Could use rich.markdown here
            return Static(pane.content or "Markdown preview")
            
        else:
            return Static(f"{pane.preview_type.value} preview")

class NEXUSIntegratedWorkspace(App):
    """Main integrated workspace application"""
    
    CSS = """
    .stage-container {
        height: 40%;
        border: solid green;
    }
    
    .active-stage {
        width: 70%;
        border-right: solid dim;
    }
    
    .side-stage {
        width: 30%;
    }
    
    .agent-window {
        margin: 1;
        height: auto;
    }
    
    .chat-container {
        width: 30%;
        border: solid blue;
    }
    
    .chat-messages {
        height: 80%;
        border: solid dim;
    }
    
    .chat-input {
        dock: bottom;
        height: 3;
    }
    
    .preview-tabs {
        width: 70%;
        border: solid yellow;
    }
    
    .command-bar {
        dock: bottom;
        height: 3;
        background: $surface;
        border-top: solid $primary;
    }
    
    .status-bar {
        dock: bottom;
        height: 1;
        background: $surface-darken-2;
    }
    """
    
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+n", "new_agent", "New Agent"),
        ("ctrl+tab", "next_agent", "Next Agent"),
        ("ctrl+shift+tab", "prev_agent", "Previous Agent"),
        ("ctrl+p", "command_palette", "Command Palette"),
        ("ctrl+s", "save_workspace", "Save Workspace"),
        ("ctrl+o", "load_workspace", "Load Workspace"),
        ("f1", "help", "Help"),
    ]
    
    def __init__(self):
        super().__init__()
        self.stage_manager = StageManager(max_active_agents=4)
        self.desktop_manager = DesktopManager(stage_manager=self.stage_manager)
        self.setup_default_agents()
        
    def setup_default_agents(self):
        """Create some default agents"""
        # Create a development team
        self.dev_agent = self.stage_manager.create_agent_window("Dev Agent", "developer")
        self.research_agent = self.stage_manager.create_agent_window("Research Agent", "researcher")
        self.design_agent = self.stage_manager.create_agent_window("Design Agent", "designer")
        
        # Create default preview panes
        self.desktop_manager.create_preview_pane("main.py", PreviewType.CODE)
        self.desktop_manager.create_preview_pane("Terminal", PreviewType.TERMINAL)
        
        # Add welcome message
        self.desktop_manager.add_chat_message(
            "system",
            "Welcome to NEXUS 2.0 Integrated Workspace! Type 'help' for commands."
        )
        
    def compose(self) -> ComposeResult:
        """Create the UI layout"""
        yield Header(show_clock=True)
        
        # Main content area
        with Container(classes="main-content"):
            # Top: Stage Manager
            yield StageView(self.stage_manager)
            
            # Bottom: Desktop Manager (Chat + Preview)
            with Horizontal(classes="desktop-area"):
                yield ChatView(self.desktop_manager)
                yield PreviewView(self.desktop_manager)
                
        # Command bar
        yield Input(
            placeholder="Enter command (Ctrl+P for palette)...",
            id="command-bar",
            classes="command-bar"
        )
        
        # Status bar
        yield Static(
            "NEXUS 2.0 | Agents: 3 Active | Ready",
            id="status-bar",
            classes="status-bar"
        )
        
        yield Footer()
        
    @on(Input.Submitted, "#command-bar")
    def execute_command(self, event: Input.Submitted):
        """Execute a command from the command bar"""
        if event.value.strip():
            result = self.desktop_manager.execute_command(event.value)
            
            # Show result in chat
            if "error" in result:
                self.desktop_manager.add_chat_message("system", f"❌ {result['error']}")
            else:
                self.desktop_manager.add_chat_message("system", f"✅ Command executed")
                
            # Clear command bar
            event.input.value = ""
            
            # Refresh views
            self.refresh()
            
    def action_new_agent(self):
        """Create a new agent"""
        # In a real implementation, show a dialog
        agent = self.stage_manager.create_agent_window(
            f"Agent {len(self.stage_manager.agent_windows) + 1}",
            "developer"
        )
        self.desktop_manager.add_chat_message(
            "system",
            f"Created new agent: {agent.name}"
        )
        self.refresh()
        
    def action_next_agent(self):
        """Switch to next agent"""
        agents = self.stage_manager.active_stage
        if agents and self.stage_manager.focus_agent_id:
            current_idx = agents.index(self.stage_manager.focus_agent_id)
            next_idx = (current_idx + 1) % len(agents)
            self.stage_manager.switch_to_agent(agents[next_idx])
            self.refresh()
            
    def action_prev_agent(self):
        """Switch to previous agent"""
        agents = self.stage_manager.active_stage
        if agents and self.stage_manager.focus_agent_id:
            current_idx = agents.index(self.stage_manager.focus_agent_id)
            prev_idx = (current_idx - 1) % len(agents)
            self.stage_manager.switch_to_agent(agents[prev_idx])
            self.refresh()
            
    def action_command_palette(self):
        """Show command palette"""
        # Focus the command bar
        self.query_one("#command-bar", Input).focus()
        
    def action_save_workspace(self):
        """Save current workspace"""
        filename = f"workspace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.desktop_manager.save_workspace(filename)
        self.stage_manager.save_stage_session(f"stage_{filename}")
        self.desktop_manager.add_chat_message(
            "system",
            f"Workspace saved to {filename}"
        )
        
    def action_load_workspace(self):
        """Load a workspace"""
        # In a real implementation, show a file picker
        self.desktop_manager.add_chat_message(
            "system",
            "Load workspace: Not implemented in demo"
        )
        
    def action_help(self):
        """Show help"""
        help_text = """
NEXUS 2.0 Commands:
- agent create <type> <name>: Create new agent
- agent list: List all agents
- agent focus <id>: Focus on agent
- preview open <type> <title>: Open preview pane
- preview close <id>: Close preview pane
- chat send <message>: Send chat message
- workspace save <file>: Save workspace
- layout grid/cascade: Arrange agents

Keyboard Shortcuts:
- Ctrl+N: New agent
- Ctrl+Tab: Next agent
- Ctrl+P: Command palette
- Ctrl+S: Save workspace
        """
        self.desktop_manager.add_chat_message("system", help_text)
        
    def on_mount(self):
        """Called when app starts"""
        self.title = "NEXUS 2.0 - Integrated Autonomous Agent Workspace"
        self.sub_title = "Stage Manager + Desktop Manager + Terminal UI"

def main():
    """Launch the integrated workspace"""
    print("""
    ╔═══════════════════════════════════════════════════╗
    ║      NEXUS 2.0 INTEGRATED WORKSPACE               ║
    ║  Stage Manager + Desktop Manager + Terminal UI    ║
    ║                                                   ║
    ║  • Multiple autonomous agents in windows          ║
    ║  • Chat interface for communication               ║
    ║  • Preview panes for code/output                  ║
    ║  • Full terminal-based development environment    ║
    ╚═══════════════════════════════════════════════════╝
    """)
    
    app = NEXUSIntegratedWorkspace()
    app.run()

if __name__ == "__main__":
    main()