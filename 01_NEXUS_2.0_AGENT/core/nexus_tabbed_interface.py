#!/usr/bin/env python3
"""
NEXUS 2.0 Tabbed Interface
Each tab shows a different part of the application
Clean, focused views instead of everything crammed together
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane, Static, Input, Label, Button, DataTable, Log
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual import on
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
from datetime import datetime
import asyncio

from nexus_stage_manager import StageManager, AgentState
from nexus_desktop_manager import DesktopManager, PreviewType
from nexus_debug_tab import DebugTab, DebugViewer, DebugCommands, integrate_logger_with_components, DEBUG_TAB_CSS
from nexus_logger import get_logger

class StageManagerTab(TabPane):
    """Tab 1: Stage Manager - Shows all agent windows"""
    
    def __init__(self, stage_manager: StageManager):
        super().__init__("Stage Manager", id="tab-stage")
        self.stage_manager = stage_manager
        
    def compose(self) -> ComposeResult:
        """Create the stage manager view"""
        with Vertical():
            yield Label("🎭 Agent Windows", classes="tab-header")
            
            with Horizontal(classes="stage-layout"):
                # Active Stage
                with Vertical(classes="active-stage-panel"):
                    yield Label("Active Agents (Focus)", classes="section-header")
                    yield ScrollableContainer(id="active-agents")
                    
                # Side Stage
                with Vertical(classes="side-stage-panel"):
                    yield Label("Background Agents", classes="section-header")
                    yield ScrollableContainer(id="side-agents")
                    
            # Controls
            with Horizontal(classes="stage-controls"):
                yield Button("New Agent", id="new-agent", variant="primary")
                yield Button("Arrange Grid", id="arrange-grid")
                yield Button("Arrange Cascade", id="arrange-cascade")
                yield Button("Close Agent", id="close-agent", variant="error")

class ChatTab(TabPane):
    """Tab 2: Chat Interface - Communication with agents"""
    
    def __init__(self, desktop_manager: DesktopManager):
        super().__init__("Chat", id="tab-chat")
        self.desktop_manager = desktop_manager
        
    def compose(self) -> ComposeResult:
        """Create the chat view"""
        with Vertical():
            yield Label("💬 Agent Communication", classes="tab-header")
            
            # Chat display
            yield Log(id="chat-log", classes="chat-display", auto_scroll=True)
            
            # Input area
            with Horizontal(classes="chat-input-area"):
                yield Input(
                    placeholder="Type a command or message...",
                    id="chat-input",
                    classes="chat-input"
                )
                yield Button("Send", id="send-button", variant="primary")

class PreviewTab(TabPane):
    """Tab 3: Preview - Shows code, output, and results"""
    
    def __init__(self, desktop_manager: DesktopManager):
        super().__init__("Preview", id="tab-preview")
        self.desktop_manager = desktop_manager
        
    def compose(self) -> ComposeResult:
        """Create the preview view"""
        with Vertical():
            yield Label("👁️ Preview & Output", classes="tab-header")
            
            # Preview selector
            with Horizontal(classes="preview-selector"):
                yield Label("Active Preview:", classes="preview-label")
                yield Button("Code", id="preview-code", variant="primary")
                yield Button("Output", id="preview-output")
                yield Button("Logs", id="preview-logs")
                yield Button("Data", id="preview-data")
                
            # Preview content
            yield ScrollableContainer(
                Static("Select a preview type above", id="preview-content"),
                id="preview-container",
                classes="preview-display"
            )

class TerminalTab(TabPane):
    """Tab 4: Terminal - Direct terminal access"""
    
    def compose(self) -> ComposeResult:
        """Create the terminal view"""
        with Vertical():
            yield Label("🖥️ Terminal", classes="tab-header")
            
            # Terminal output
            yield Log(id="terminal-output", classes="terminal-display", auto_scroll=True)
            
            # Terminal input
            yield Input(
                placeholder="$ Enter command...",
                id="terminal-input",
                classes="terminal-input"
            )

class StatusTab(TabPane):
    """Tab 5: Status - System status and monitoring"""
    
    def __init__(self, stage_manager: StageManager):
        super().__init__("Status", id="tab-status")
        self.stage_manager = stage_manager
        
    def compose(self) -> ComposeResult:
        """Create the status view"""
        with Vertical():
            yield Label("📊 System Status", classes="tab-header")
            
            # Agent status table
            yield Label("Agent Status:", classes="section-header")
            agent_table = DataTable(id="agent-status-table")
            agent_table.add_columns("Agent", "Type", "State", "Task", "Duration")
            yield agent_table
            
            # System metrics
            yield Label("System Metrics:", classes="section-header")
            yield Static(id="system-metrics", classes="metrics-display")
            
            # Recent activity log
            yield Label("Recent Activity:", classes="section-header")
            yield Log(id="activity-log", classes="activity-display")

class NEXUSTabbedInterface(App):
    """Main application with tabbed interface"""
    
    CSS = """
    /* Tab styling */
    TabbedContent {
        background: $surface;
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
        color: $secondary;
        margin: 1 0;
    }
    
    /* Stage Manager styling */
    .stage-layout {
        height: 80%;
    }
    
    .active-stage-panel {
        width: 70%;
        border: solid $primary;
        margin-right: 1;
    }
    
    .side-stage-panel {
        width: 30%;
        border: solid $secondary;
    }
    
    .stage-controls {
        margin-top: 1;
        height: 3;
    }
    
    /* Chat styling */
    .chat-display {
        height: 80%;
        border: solid $primary;
    }
    
    .chat-input-area {
        height: 3;
        margin-top: 1;
    }
    
    .chat-input {
        width: 85%;
    }
    
    /* Preview styling */
    .preview-selector {
        height: 3;
        margin-bottom: 1;
    }
    
    .preview-display {
        height: 85%;
        border: solid $primary;
    }
    
    /* Terminal styling */
    .terminal-display {
        height: 85%;
        border: solid $success;
        background: $surface-darken-2;
    }
    
    .terminal-input {
        background: $surface-darken-1;
    }
    
    /* Status styling */
    #agent-status-table {
        height: 40%;
        margin-bottom: 1;
    }
    
    .metrics-display {
        height: 20%;
        border: solid $secondary;
        padding: 1;
    }
    
    .activity-display {
        height: 30%;
        border: solid $secondary;
    }
    
    /* Button styling */
    Button {
        margin: 0 1;
    }
    """
    
    # Add the debug tab CSS
    CSS += DEBUG_TAB_CSS
    
    BINDINGS = [
        ("ctrl+1", "switch_tab('tab-stage')", "Stage Manager"),
        ("ctrl+2", "switch_tab('tab-chat')", "Chat"),
        ("ctrl+3", "switch_tab('tab-preview')", "Preview"),
        ("ctrl+4", "switch_tab('tab-terminal')", "Terminal"),
        ("ctrl+5", "switch_tab('tab-status')", "Status"),
        ("ctrl+6", "switch_tab('tab-debug')", "Debug"),
        ("ctrl+n", "new_agent", "New Agent"),
        ("ctrl+w", "close_agent", "Close Agent"),
        ("ctrl+q", "quit", "Quit"),
    ]
    
    def __init__(self):
        super().__init__()
        self.stage_manager = StageManager(max_active_agents=4)
        self.desktop_manager = DesktopManager(stage_manager=self.stage_manager)
        
        # Initialize logger
        self.logger = get_logger()
        self.logger.log_system_event("NEXUS 2.0 Tabbed Interface Started", {
            "version": "2.0",
            "interface": "tabbed"
        })
        
        # Initialize debug components
        self.debug_tab = None  # Will be set in compose
        self.debug_viewer = None
        self.debug_commands = DebugCommands(self)
        
        self.setup_demo_agents()
        
    def setup_demo_agents(self):
        """Create some demo agents"""
        self.stage_manager.create_agent_window("Code Analyzer", "analyzer")
        self.stage_manager.create_agent_window("API Builder", "developer")
        self.stage_manager.create_agent_window("Test Runner", "tester")
        
    def compose(self) -> ComposeResult:
        """Create the UI"""
        yield Header(show_clock=True)
        
        with TabbedContent(initial="tab-stage"):
            yield StageManagerTab(self.stage_manager)
            yield ChatTab(self.desktop_manager)
            yield PreviewTab(self.desktop_manager)
            yield TerminalTab()
            yield StatusTab(self.stage_manager)
            
            # Add the debug tab
            self.debug_tab = DebugTab()
            yield self.debug_tab
            
        yield Footer()
        
    def on_mount(self):
        """Initialize when app starts"""
        self.title = "NEXUS 2.0 - Tabbed Interface"
        self.sub_title = "Each tab shows a focused view"
        
        # Initialize debug viewer
        self.debug_viewer = DebugViewer(self.debug_tab)
        
        # Integrate logger with all components
        integrate_logger_with_components(self)
        
        # Start periodic updates
        self.set_interval(1.0, self.update_displays)
        
        # Add welcome message
        chat_log = self.query_one("#chat-log", Log)
        chat_log.write_line("🚀 Welcome to NEXUS 2.0 Tabbed Interface!")
        chat_log.write_line("Use Ctrl+1 through Ctrl+6 to switch tabs")
        chat_log.write_line("Type commands in the chat to create agents")
        chat_log.write_line("Press Ctrl+6 to view debug logs and system monitoring")
        
    def update_displays(self):
        """Update all displays periodically"""
        # Update stage manager display
        self.update_stage_display()
        
        # Update status display
        self.update_status_display()
        
        # Update debug display
        if self.debug_viewer:
            self.debug_viewer.update_activity_table()
            self.debug_viewer.update_error_list()
        
    def update_stage_display(self):
        """Update the stage manager display"""
        try:
            active_container = self.query_one("#active-agents", ScrollableContainer)
            active_container.remove_children()
            
            # Show active agents
            for agent_id in self.stage_manager.active_stage:
                agent = self.stage_manager.agent_windows[agent_id]
                agent_panel = Panel(
                    f"Type: {agent.agent_type}\n"
                    f"State: {agent.state.value}\n"
                    f"Task: {agent.current_task or 'Idle'}",
                    title=agent.name,
                    border_style="green" if agent_id == self.stage_manager.focus_agent_id else "blue"
                )
                active_container.mount(Static(agent_panel))
                
            # Show side stage agents
            side_container = self.query_one("#side-agents", ScrollableContainer)
            side_container.remove_children()
            
            for agent_id in self.stage_manager.side_stage:
                agent = self.stage_manager.agent_windows[agent_id]
                agent_panel = Panel(
                    f"Type: {agent.agent_type}\n"
                    f"State: {agent.state.value}",
                    title=agent.name,
                    border_style="dim"
                )
                side_container.mount(Static(agent_panel))
                
        except Exception:
            pass  # Ignore errors during updates
            
    def update_status_display(self):
        """Update the status display"""
        try:
            # Update agent status table
            table = self.query_one("#agent-status-table", DataTable)
            table.clear()
            
            for agent_id, agent in self.stage_manager.agent_windows.items():
                duration = (datetime.now() - agent.created_at).total_seconds()
                table.add_row(
                    agent.name,
                    agent.agent_type,
                    agent.state.value,
                    agent.current_task or "None",
                    f"{duration:.0f}s"
                )
                
            # Update system metrics
            metrics = self.query_one("#system-metrics", Static)
            metrics.update(
                f"Active Agents: {len(self.stage_manager.active_stage)}\n"
                f"Background Agents: {len(self.stage_manager.side_stage)}\n"
                f"Total Agents: {len(self.stage_manager.agent_windows)}\n"
                f"Focus: {self.stage_manager.agent_windows[self.stage_manager.focus_agent_id].name if self.stage_manager.focus_agent_id else 'None'}"
            )
            
        except Exception:
            pass
            
    @on(Input.Submitted, "#chat-input")
    def handle_chat_input(self, event: Input.Submitted):
        """Handle chat input"""
        if event.value.strip():
            # Add to chat
            chat_log = self.query_one("#chat-log", Log)
            chat_log.write_line(f"You: {event.value}")
            
            # Process command
            self.process_command(event.value)
            
            # Clear input
            event.input.value = ""
            
    @on(Input.Submitted, "#terminal-input")
    def handle_terminal_input(self, event: Input.Submitted):
        """Handle terminal input"""
        if event.value.strip():
            # Log terminal command
            self.logger.log_command(event.value, "terminal")
            
            # Add to terminal output
            terminal_output = self.query_one("#terminal-output", Log)
            terminal_output.write_line(f"$ {event.value}")
            terminal_output.write_line("Terminal execution not yet implemented")
            
            # Clear input
            event.input.value = ""
            
    def process_command(self, command: str):
        """Process user commands"""
        chat_log = self.query_one("#chat-log", Log)
        
        # Log the command
        self.logger.log_command(command, "user")
        
        # Simple command parsing
        cmd_lower = command.lower()
        
        if "create" in cmd_lower or "build" in cmd_lower or "analyze" in cmd_lower:
            # Create a new agent
            agent_type = "developer" if "build" in cmd_lower else "analyzer"
            name = f"{agent_type.title()} - {command[:20]}"
            
            window = self.stage_manager.create_agent_window(name, agent_type)
            window.current_task = command
            window.state = AgentState.WORKING
            
            chat_log.write_line(f"✅ Created {name}")
            chat_log.write_line(f"{name}: Starting work on '{command}'")
            
            # Log agent creation
            self.logger.log_agent_activity(window.id, "Started task", {"task": command})
            
            # Update displays
            self.update_displays()
            
            # Update debug log
            if self.debug_viewer:
                self.debug_viewer.update_log_stream(f"Created agent '{name}' for task: {command}", "INFO")
            
    @on(Button.Pressed, "#new-agent")
    def handle_new_agent(self):
        """Create a new agent"""
        # Switch to chat tab
        self.action_switch_tab("tab-chat")
        
        # Focus chat input
        chat_input = self.query_one("#chat-input", Input)
        chat_input.focus()
        
    def action_switch_tab(self, tab_id: str):
        """Switch to a specific tab"""
        tabbed_content = self.query_one(TabbedContent)
        tabbed_content.active = tab_id
        
    def action_new_agent(self):
        """Keyboard shortcut for new agent"""
        self.handle_new_agent()
        
    def action_close_agent(self):
        """Close the focused agent"""
        if self.stage_manager.focus_agent_id:
            self.stage_manager.minimize_agent(self.stage_manager.focus_agent_id)
            self.update_displays()
            
    # Debug tab event handlers
    @on(Button.Pressed, "#clear-logs")
    def handle_clear_logs(self):
        """Clear the debug log display"""
        debug_log = self.query_one("#debug-log", Log)
        debug_log.clear()
        self.logger.info("Debug log cleared")
        
    @on(Button.Pressed, "#pause-logs")
    def handle_pause_logs(self, event: Button.Pressed):
        """Pause/resume log updates"""
        self.debug_tab.log_paused = not self.debug_tab.log_paused
        event.button.label = "Resume" if self.debug_tab.log_paused else "Pause"
        self.logger.info(f"Log updates {'paused' if self.debug_tab.log_paused else 'resumed'}")
        
    @on(Button.Pressed, "#save-logs")
    def handle_save_logs(self):
        """Save current session logs"""
        self.logger.save_session_log()
        if self.debug_viewer:
            self.debug_viewer.update_log_stream(f"Session logs saved to {self.logger.log_dir}", "INFO")
            
    @on(Input.Submitted, "#debug-command-input")
    def handle_debug_command(self, event: Input.Submitted):
        """Handle debug command input"""
        if event.value.strip():
            result = self.debug_commands.process_command(event.value)
            
            # Show result in debug log
            if self.debug_viewer:
                self.debug_viewer.update_log_stream(f"Debug Command: {event.value}", "DEBUG")
                self.debug_viewer.update_log_stream(f"Result: {result}", "INFO")
                
            # Clear input
            event.input.value = ""
            
    @on(Button.Pressed, "#execute-debug")
    def handle_execute_debug(self):
        """Execute debug command from button"""
        debug_input = self.query_one("#debug-command-input", Input)
        if debug_input.value.strip():
            # Trigger the input submitted event
            debug_input.action_submit()

def main():
    """Launch the tabbed interface"""
    app = NEXUSTabbedInterface()
    app.run()

if __name__ == "__main__":
    main()