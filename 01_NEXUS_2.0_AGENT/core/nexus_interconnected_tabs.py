#!/usr/bin/env python3
"""
NEXUS 2.0 Interconnected Tabbed Interface
All tabs are connected and communicate with each other
Changes in one tab immediately affect others
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane, Static, Input, Label, Button, DataTable, Log, TextArea
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual import on, events
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
from datetime import datetime
import asyncio
import uuid
from typing import Dict, Optional

# Import our core components
from nexus_stage_manager import StageManager, AgentState, AgentWindow
from nexus_desktop_manager import DesktopManager, PreviewType, ChatMessage
from nexus_task_orchestrator import TaskOrchestrator

class InterconnectedWorkspace:
    """Central workspace that connects all components"""
    
    def __init__(self):
        self.stage_manager = StageManager(max_active_agents=4)
        self.desktop_manager = DesktopManager(stage_manager=self.stage_manager)
        self.task_orchestrator = TaskOrchestrator(self.stage_manager, self.desktop_manager)
        
        # Shared state that all tabs can access
        self.current_preview_content = ""
        self.current_preview_type = PreviewType.CODE
        self.terminal_output = []
        self.active_task = None
        
        # Event callbacks for inter-tab communication
        self.on_agent_created = []
        self.on_chat_message = []
        self.on_preview_update = []
        self.on_terminal_command = []
        self.on_agent_state_change = []
        
    def create_agent_from_chat(self, message: str) -> Optional[AgentWindow]:
        """Create an agent from a chat message"""
        # Parse the message to determine agent type
        agent_type = self._determine_agent_type(message)
        name = f"{agent_type.title()} - {message[:20]}"
        
        # Create agent in stage manager
        window = self.stage_manager.create_agent_window(name, agent_type)
        window.current_task = message
        window.state = AgentState.WORKING
        
        # Add chat response
        self.desktop_manager.add_chat_message(
            window.id,
            f"Starting work on: {message}"
        )
        
        # Create preview pane
        preview = self.desktop_manager.create_preview_pane(
            f"Output: {name}",
            PreviewType.CODE
        )
        
        # Trigger callbacks
        for callback in self.on_agent_created:
            callback(window)
            
        # Simulate agent work
        asyncio.create_task(self._simulate_agent_work(window, preview.id))
        
        return window
        
    def _determine_agent_type(self, message: str) -> str:
        """Determine agent type from message"""
        msg_lower = message.lower()
        if any(word in msg_lower for word in ["analyze", "review", "check"]):
            return "analyzer"
        elif any(word in msg_lower for word in ["build", "create", "implement"]):
            return "developer"
        elif any(word in msg_lower for word in ["test", "verify"]):
            return "tester"
        elif any(word in msg_lower for word in ["document", "write"]):
            return "documenter"
        else:
            return "general"
            
    async def _simulate_agent_work(self, window: AgentWindow, preview_id: str):
        """Simulate agent doing work"""
        # Update to thinking state
        window.state = AgentState.THINKING
        self._notify_agent_state_change(window)
        await asyncio.sleep(1)
        
        # Start working
        window.state = AgentState.WORKING
        self._notify_agent_state_change(window)
        
        # Generate some output
        if "analyze" in window.current_task.lower():
            output = """# Code Analysis Results
            
Found 3 issues:
1. Missing error handling in main()
2. Unused imports: sys, os
3. Function 'process_data' is too complex

Recommendations:
- Add try/except blocks
- Remove unused imports
- Refactor complex function"""
        elif "build" in window.current_task.lower():
            output = """# Generated Code

from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/api/status')
def status():
    return jsonify({"status": "running"})

if __name__ == '__main__':
    app.run(debug=True)"""
        else:
            output = f"Working on: {window.current_task}\nProgress: 50%\nEstimated time: 2 minutes"
            
        # Update preview
        self.desktop_manager.update_preview_content(preview_id, output)
        self.current_preview_content = output
        for callback in self.on_preview_update:
            callback(output, self.current_preview_type)
            
        await asyncio.sleep(2)
        
        # Complete
        window.state = AgentState.IDLE
        window.current_task = "Completed"
        self._notify_agent_state_change(window)
        
        # Add completion message
        self.desktop_manager.add_chat_message(
            window.id,
            f"✅ Task completed successfully!"
        )
        
    def _notify_agent_state_change(self, window: AgentWindow):
        """Notify all listeners of agent state change"""
        for callback in self.on_agent_state_change:
            callback(window)
            
    def execute_terminal_command(self, command: str):
        """Execute a terminal command and update all tabs"""
        # Add to terminal output
        self.terminal_output.append(f"$ {command}")
        
        # Simulate command execution
        if command.startswith("python"):
            output = "Running Python script...\n* Server started on http://localhost:5000"
        elif command.startswith("curl"):
            output = '{"status": "success", "data": []}'
        elif command == "ls":
            output = "api.py  test_api.py  requirements.txt  README.md"
        else:
            output = f"Command executed: {command}"
            
        self.terminal_output.append(output)
        
        # Notify listeners
        for callback in self.on_terminal_command:
            callback(command, output)

# Now create the interconnected tabs

class StageManagerTab(TabPane):
    """Tab 1: Stage Manager - Connected to workspace"""
    
    def __init__(self, workspace: InterconnectedWorkspace):
        super().__init__("Stage Manager", id="tab-stage")
        self.workspace = workspace
        self.workspace.on_agent_created.append(self.refresh_display)
        self.workspace.on_agent_state_change.append(self.refresh_display)
        
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("🎭 Agent Windows", classes="tab-header")
            
            with Horizontal(classes="stage-layout"):
                with Vertical(classes="active-stage-panel"):
                    yield Label("Active Agents", classes="section-header")
                    yield ScrollableContainer(id="active-agents")
                    
                with Vertical(classes="side-stage-panel"):
                    yield Label("Background", classes="section-header")
                    yield ScrollableContainer(id="side-agents")
                    
            with Horizontal(classes="stage-controls"):
                yield Button("Switch to Chat", id="go-to-chat", variant="primary")
                yield Button("Arrange Grid", id="arrange-grid")
                yield Button("Focus Next", id="focus-next")
                
    def on_mount(self):
        """Initial display update"""
        self.refresh_display(None)
        
    def refresh_display(self, agent=None):
        """Refresh the stage display when agents change"""
        # Update active agents
        active_container = self.query_one("#active-agents", ScrollableContainer)
        active_container.remove_children()
        
        for agent_id in self.workspace.stage_manager.active_stage:
            agent = self.workspace.stage_manager.agent_windows[agent_id]
            panel = Panel(
                f"Type: {agent.agent_type}\n"
                f"State: {agent.state.value}\n"
                f"Task: {agent.current_task or 'Idle'}",
                title=agent.name,
                border_style="green" if agent_id == self.workspace.stage_manager.focus_agent_id else "blue"
            )
            active_container.mount(Static(panel))
            
        # Update side stage
        side_container = self.query_one("#side-agents", ScrollableContainer)
        side_container.remove_children()
        
        for agent_id in self.workspace.stage_manager.side_stage:
            agent = self.workspace.stage_manager.agent_windows[agent_id]
            panel = Panel(
                f"{agent.agent_type}\n{agent.state.value}",
                title=agent.name,
                border_style="dim"
            )
            side_container.mount(Static(panel))
            
    @on(Button.Pressed, "#go-to-chat")
    def switch_to_chat(self):
        """Switch to chat tab"""
        self.app.action_switch_tab("tab-chat")
        
    @on(Button.Pressed, "#focus-next")
    def focus_next_agent(self):
        """Focus next agent"""
        agents = self.workspace.stage_manager.active_stage
        if agents and self.workspace.stage_manager.focus_agent_id:
            current_idx = agents.index(self.workspace.stage_manager.focus_agent_id)
            next_idx = (current_idx + 1) % len(agents)
            self.workspace.stage_manager.switch_to_agent(agents[next_idx])
            self.refresh_display(None)

class ChatTab(TabPane):
    """Tab 2: Chat - Connected to workspace"""
    
    def __init__(self, workspace: InterconnectedWorkspace):
        super().__init__("Chat", id="tab-chat")
        self.workspace = workspace
        
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("💬 Agent Communication", classes="tab-header")
            yield Log(id="chat-log", classes="chat-display", auto_scroll=True)
            
            with Horizontal(classes="chat-input-area"):
                yield Input(
                    placeholder="Type a command to create agents...",
                    id="chat-input",
                    classes="chat-input"
                )
                yield Button("Send", id="send-button", variant="primary")
                
    def on_mount(self):
        """Initialize chat"""
        chat_log = self.query_one("#chat-log", Log)
        chat_log.write_line("🚀 Welcome to NEXUS 2.0!")
        chat_log.write_line("Type commands like: 'analyze my code', 'build an API', 'test the system'")
        
        # Connect to workspace events
        self.workspace.desktop_manager.register_message_handler("system", self.add_system_message)
        
    def add_system_message(self, message):
        """Add system message to chat"""
        chat_log = self.query_one("#chat-log", Log)
        chat_log.write_line(f"System: {message.content}")
        
    @on(Input.Submitted, "#chat-input")
    def handle_chat_input(self, event: Input.Submitted):
        """Handle chat input - creates agents"""
        if event.value.strip():
            chat_log = self.query_one("#chat-log", Log)
            chat_log.write_line(f"You: {event.value}")
            
            # Create agent from message
            agent = self.workspace.create_agent_from_chat(event.value)
            
            if agent:
                chat_log.write_line(f"✅ Created {agent.name}")
                chat_log.write_line(f"{agent.name}: Starting work...")
                
                # Switch to stage manager to see the new agent
                self.app.action_switch_tab("tab-stage")
                
            event.input.value = ""
            
    @on(Button.Pressed, "#send-button")
    def send_button_pressed(self):
        """Send button clicked"""
        chat_input = self.query_one("#chat-input", Input)
        if chat_input.value:
            # Trigger the input submitted event
            chat_input.action_submit()

class PreviewTab(TabPane):
    """Tab 3: Preview - Connected to workspace"""
    
    def __init__(self, workspace: InterconnectedWorkspace):
        super().__init__("Preview", id="tab-preview")
        self.workspace = workspace
        self.workspace.on_preview_update.append(self.update_preview)
        
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("👁️ Preview & Output", classes="tab-header")
            
            with Horizontal(classes="preview-selector"):
                yield Button("Refresh", id="refresh-preview", variant="primary")
                yield Label(id="preview-type", classes="preview-label")
                
            yield TextArea(
                id="preview-content",
                language="python",
                theme="monokai",
                read_only=True,
                classes="preview-display"
            )
            
    def on_mount(self):
        """Initialize preview"""
        self.update_preview(self.workspace.current_preview_content, self.workspace.current_preview_type)
        
    def update_preview(self, content: str, preview_type: PreviewType):
        """Update preview content"""
        textarea = self.query_one("#preview-content", TextArea)
        textarea.text = content or "No preview content yet. Create an agent to see output."
        
        type_label = self.query_one("#preview-type", Label)
        type_label.update(f"Type: {preview_type.value if preview_type else 'None'}")
        
    @on(Button.Pressed, "#refresh-preview")
    def refresh_preview(self):
        """Refresh preview from workspace"""
        if self.workspace.desktop_manager.preview_panes:
            # Get the first preview pane
            pane = next(iter(self.workspace.desktop_manager.preview_panes.values()))
            self.update_preview(pane.content or "", pane.preview_type)

class TerminalTab(TabPane):
    """Tab 4: Terminal - Connected to workspace"""
    
    def __init__(self, workspace: InterconnectedWorkspace):
        super().__init__("Terminal", id="tab-terminal")
        self.workspace = workspace
        self.workspace.on_terminal_command.append(self.add_terminal_output)
        
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("🖥️ Terminal", classes="tab-header")
            yield Log(id="terminal-output", classes="terminal-display", auto_scroll=True)
            yield Input(
                placeholder="$ Enter command...",
                id="terminal-input",
                classes="terminal-input"
            )
            
    def add_terminal_output(self, command: str, output: str):
        """Add output to terminal"""
        term_log = self.query_one("#terminal-output", Log)
        term_log.write_line(f"$ {command}")
        term_log.write_line(output)
        
    @on(Input.Submitted, "#terminal-input")
    def handle_terminal_command(self, event: Input.Submitted):
        """Handle terminal command"""
        if event.value.strip():
            self.workspace.execute_terminal_command(event.value)
            event.input.value = ""

class StatusTab(TabPane):
    """Tab 5: Status - Connected to workspace"""
    
    def __init__(self, workspace: InterconnectedWorkspace):
        super().__init__("Status", id="tab-status")
        self.workspace = workspace
        self.workspace.on_agent_state_change.append(lambda x: self.update_status())
        
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("📊 System Status", classes="tab-header")
            yield Static(id="status-overview", classes="status-display")
            yield Label("Recent Activity:", classes="section-header")
            yield Log(id="activity-log", classes="activity-display")
            
    def on_mount(self):
        """Initialize status"""
        self.update_status()
        
    def update_status(self):
        """Update status display"""
        overview = self.query_one("#status-overview", Static)
        
        # Count agents by state
        agents = self.workspace.stage_manager.agent_windows.values()
        working = sum(1 for a in agents if a.state == AgentState.WORKING)
        thinking = sum(1 for a in agents if a.state == AgentState.THINKING)
        idle = sum(1 for a in agents if a.state == AgentState.IDLE)
        
        overview.update(
            f"Total Agents: {len(agents)}\n"
            f"Working: {working}\n"
            f"Thinking: {thinking}\n"
            f"Idle: {idle}\n"
            f"Active Stage: {len(self.workspace.stage_manager.active_stage)}\n"
            f"Chat Messages: {len(self.workspace.desktop_manager.chat_history)}"
        )
        
        # Add to activity log
        if agents:
            activity = self.query_one("#activity-log", Log)
            latest = max(agents, key=lambda a: a.last_active)
            activity.write_line(f"{datetime.now().strftime('%H:%M:%S')} - {latest.name}: {latest.state.value}")

class NEXUSInterconnectedTabs(App):
    """Main app with fully interconnected tabs"""
    
    CSS = """
    TabbedContent {
        height: 100%;
    }
    
    TabPane {
        padding: 1;
    }
    
    .tab-header {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    .section-header {
        text-style: bold;
        margin: 1 0;
    }
    
    .stage-layout {
        height: 75%;
    }
    
    .active-stage-panel {
        width: 65%;
        border: solid $primary;
        margin-right: 1;
    }
    
    .side-stage-panel {
        width: 35%;
        border: solid dim;
    }
    
    .chat-display {
        height: 75%;
        border: solid $primary;
    }
    
    .chat-input-area {
        height: 3;
        margin-top: 1;
    }
    
    .chat-input {
        width: 80%;
    }
    
    .preview-display {
        height: 80%;
        border: solid $primary;
    }
    
    .terminal-display {
        height: 80%;
        border: solid green;
        background: black;
    }
    
    .terminal-input {
        background: $surface-darken-2;
    }
    
    .status-display {
        height: 40%;
        border: solid $secondary;
        padding: 1;
    }
    
    .activity-display {
        height: 40%;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        ("ctrl+1", "switch_tab('tab-stage')", "Stage"),
        ("ctrl+2", "switch_tab('tab-chat')", "Chat"),
        ("ctrl+3", "switch_tab('tab-preview')", "Preview"),
        ("ctrl+4", "switch_tab('tab-terminal')", "Terminal"),
        ("ctrl+5", "switch_tab('tab-status')", "Status"),
        ("ctrl+q", "quit", "Quit"),
    ]
    
    def __init__(self):
        super().__init__()
        self.workspace = InterconnectedWorkspace()
        
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with TabbedContent(initial="tab-chat"):
            yield StageManagerTab(self.workspace)
            yield ChatTab(self.workspace)
            yield PreviewTab(self.workspace)
            yield TerminalTab(self.workspace)
            yield StatusTab(self.workspace)
            
        yield Footer()
        
    def on_mount(self):
        self.title = "NEXUS 2.0 - Fully Interconnected"
        self.sub_title = "All tabs communicate with each other"
        
        # Update displays periodically
        self.set_interval(0.5, self.update_all_tabs)
        
    def update_all_tabs(self):
        """Periodic update for all tabs"""
        # Each tab updates itself based on workspace state
        pass
        
    def action_switch_tab(self, tab_id: str):
        """Switch to specific tab"""
        content = self.query_one(TabbedContent)
        content.active = tab_id

def main():
    """Launch the interconnected tabbed interface"""
    app = NEXUSInterconnectedTabs()
    app.run()

if __name__ == "__main__":
    main()