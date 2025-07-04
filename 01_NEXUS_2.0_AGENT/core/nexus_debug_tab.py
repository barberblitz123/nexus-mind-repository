#!/usr/bin/env python3
"""
NEXUS 2.0 Debug Tab
Real-time debugging and log viewing interface
"""

from textual.widgets import TabPane, Label, Log, Select, Button, Input, DataTable, Static
from textual.containers import Horizontal, Vertical, Container, ScrollableContainer
from textual.app import ComposeResult
from textual import on
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
from datetime import datetime
import json
from typing import Optional

from nexus_logger import get_logger, LogLevel

class DebugTab(TabPane):
    """Tab 6: Debug - Real-time logging and debugging"""
    
    def __init__(self):
        super().__init__("Debug", id="tab-debug")
        self.logger = get_logger()
        self.current_filter = "ALL"
        self.log_paused = False
        
    def compose(self) -> ComposeResult:
        """Create the debug view"""
        with Vertical():
            yield Label("🐛 Debug Console", classes="tab-header")
            
            # Controls
            with Horizontal(classes="debug-controls"):
                yield Select(
                    [(level.name, level.name) for level in LogLevel],
                    prompt="Log Level",
                    id="log-level-select",
                    value="INFO"
                )
                yield Select(
                    [("ALL", "All Components")] + 
                    [(comp, comp) for comp in ["StageManager", "DesktopManager", "TaskOrchestrator", "Agent"]],
                    prompt="Component Filter",
                    id="component-filter",
                    value="ALL"
                )
                yield Button("Clear", id="clear-logs", variant="warning")
                yield Button("Pause", id="pause-logs", variant="primary")
                yield Button("Save Logs", id="save-logs", variant="success")
                
            # Main debug area with three panels
            with Horizontal(classes="debug-panels"):
                # Live log stream
                with Vertical(classes="log-stream-panel"):
                    yield Label("📜 Live Log Stream", classes="section-header")
                    yield Log(id="debug-log", auto_scroll=True, wrap=True)
                    
                # Activity monitor
                with Vertical(classes="activity-panel"):
                    yield Label("📊 Activity Monitor", classes="section-header")
                    activity_table = DataTable(id="activity-table")
                    activity_table.add_columns("Time", "Type", "Details")
                    yield activity_table
                    
                # Error tracker
                with Vertical(classes="error-panel"):
                    yield Label("❌ Error Tracker", classes="section-header")
                    yield ScrollableContainer(id="error-list")
                    
            # Command tester
            with Horizontal(classes="debug-command"):
                yield Label("Test Command:", classes="command-label")
                yield Input(
                    placeholder="Enter debug command...",
                    id="debug-command-input"
                )
                yield Button("Execute", id="execute-debug", variant="primary")

class DebugViewer:
    """Utility class for viewing debug information"""
    
    def __init__(self, debug_tab: DebugTab):
        self.tab = debug_tab
        self.logger = get_logger()
        
    def update_log_stream(self, message: str, level: str = "INFO"):
        """Update the live log stream"""
        if self.tab.log_paused:
            return
            
        log_widget = self.tab.query_one("#debug-log", Log)
        
        # Color code by level
        colors = {
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red on yellow"
        }
        
        color = colors.get(level, "white")
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        formatted_msg = Text()
        formatted_msg.append(f"[{timestamp}] ", style="dim")
        formatted_msg.append(f"{level:<8} ", style=color)
        formatted_msg.append(message)
        
        log_widget.write(formatted_msg)
        
    def update_activity_table(self):
        """Update the activity monitor table"""
        table = self.tab.query_one("#activity-table", DataTable)
        table.clear()
        
        # Get recent activities
        activities = self.logger.get_recent_activity(20)
        
        for activity in activities:
            time = datetime.fromisoformat(activity["timestamp"]).strftime("%H:%M:%S")
            
            if activity.get("type") == "command":
                type_str = "Command"
                details = activity.get("command", "")
            elif activity.get("type") == "system_event":
                type_str = "System"
                details = activity.get("event", "")
            elif activity.get("agent_id"):
                type_str = f"Agent[{activity['agent_id'][:8]}]"
                details = activity.get("activity", "")
            else:
                type_str = activity.get("component", "Unknown")
                details = activity.get("activity", "")
                
            table.add_row(time, type_str, details[:40])
            
    def update_error_list(self):
        """Update the error tracker"""
        container = self.tab.query_one("#error-list", ScrollableContainer)
        container.remove_children()
        
        # Get error log
        errors = self.logger.error_log[-10:]  # Last 10 errors
        
        if not errors:
            container.mount(Static("No errors logged 🎉", classes="no-errors"))
            return
            
        for error in reversed(errors):
            time = datetime.fromisoformat(error["timestamp"]).strftime("%H:%M:%S")
            
            error_panel = Panel(
                f"Type: {error['type']}\n"
                f"Message: {error['message']}\n"
                f"Context: {error['context']}",
                title=f"Error at {time}",
                border_style="red"
            )
            
            container.mount(Static(error_panel))

def integrate_logger_with_components(app):
    """Integrate the logger with all NEXUS components"""
    logger = get_logger()
    
    # Log system startup
    logger.log_system_event("NEXUS 2.0 Started", {
        "version": "2.0",
        "interface": "tabbed",
        "components": ["stage_manager", "desktop_manager", "task_orchestrator"]
    })
    
    # Wrap Stage Manager methods
    original_create_agent = app.stage_manager.create_agent_window
    def logged_create_agent(name, agent_type, **kwargs):
        logger.log_system_event("Creating agent", {"name": name, "type": agent_type})
        result = original_create_agent(name, agent_type, **kwargs)
        logger.log_agent_activity(result.id, "Agent created", {"name": name, "type": agent_type})
        return result
    app.stage_manager.create_agent_window = logged_create_agent
    
    # Wrap Desktop Manager methods
    original_add_message = app.desktop_manager.add_chat_message
    def logged_add_message(sender, content, **kwargs):
        logger.log_command(content, sender) if sender == "user" else None
        result = original_add_message(sender, content, **kwargs)
        return result
    app.desktop_manager.add_chat_message = logged_add_message
    
    # Add error handling wrapper
    def wrap_with_error_logging(func, context):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.log_error(e, context)
                raise
        return wrapper
    
    # Apply error logging to key methods
    for method_name in ["switch_to_agent", "minimize_agent", "arrange_grid"]:
        if hasattr(app.stage_manager, method_name):
            original = getattr(app.stage_manager, method_name)
            setattr(app.stage_manager, method_name, 
                   wrap_with_error_logging(original, f"StageManager.{method_name}"))

class DebugCommands:
    """Debug command processor"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger()
        self.commands = {
            "log": self.cmd_log,
            "agent": self.cmd_agent_info,
            "error": self.cmd_test_error,
            "memory": self.cmd_memory_info,
            "save": self.cmd_save_logs,
            "clear": self.cmd_clear_logs,
            "level": self.cmd_set_log_level,
            "help": self.cmd_help
        }
        
    def process_command(self, command: str) -> str:
        """Process a debug command"""
        parts = command.strip().split()
        if not parts:
            return "No command entered"
            
        cmd = parts[0].lower()
        args = parts[1:]
        
        if cmd in self.commands:
            return self.commands[cmd](args)
        else:
            return f"Unknown command: {cmd}. Type 'help' for available commands."
            
    def cmd_log(self, args) -> str:
        """Log a test message at specified level"""
        if len(args) < 2:
            return "Usage: log <level> <message>"
            
        level = args[0].upper()
        message = " ".join(args[1:])
        
        if level == "DEBUG":
            self.logger.debug(message)
        elif level == "INFO":
            self.logger.info(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "ERROR":
            self.logger.error(message)
        elif level == "CRITICAL":
            self.logger.critical(message)
        else:
            return f"Invalid level: {level}"
            
        return f"Logged {level}: {message}"
        
    def cmd_agent_info(self, args) -> str:
        """Get info about agents"""
        agents = self.app.stage_manager.agent_windows
        
        if not agents:
            return "No agents active"
            
        info = ["Active Agents:"]
        for agent_id, agent in agents.items():
            info.append(f"  {agent.name} ({agent.agent_type})")
            info.append(f"    ID: {agent_id[:8]}")
            info.append(f"    State: {agent.state.value}")
            info.append(f"    Task: {agent.current_task or 'None'}")
            
        return "\n".join(info)
        
    def cmd_test_error(self, args) -> str:
        """Generate a test error"""
        try:
            # Intentionally cause an error
            1 / 0
        except Exception as e:
            self.logger.log_error(e, "Test error command")
            return "Test error logged"
            
    def cmd_memory_info(self, args) -> str:
        """Show memory usage info"""
        import psutil
        process = psutil.Process()
        
        info = [
            "Memory Usage:",
            f"  RSS: {process.memory_info().rss / 1024 / 1024:.2f} MB",
            f"  VMS: {process.memory_info().vms / 1024 / 1024:.2f} MB",
            f"  CPU: {process.cpu_percent()}%",
            f"  Threads: {process.num_threads()}"
        ]
        
        return "\n".join(info)
        
    def cmd_save_logs(self, args) -> str:
        """Save current session logs"""
        self.logger.save_session_log()
        return f"Logs saved to {self.logger.log_dir}"
        
    def cmd_clear_logs(self, args) -> str:
        """Clear log display"""
        return "Use the Clear button to clear logs"
        
    def cmd_set_log_level(self, args) -> str:
        """Set logging level"""
        if not args:
            return "Usage: level <DEBUG|INFO|WARNING|ERROR|CRITICAL>"
            
        level = args[0].upper()
        try:
            import logging
            self.logger.logger.setLevel(getattr(logging, level))
            return f"Log level set to {level}"
        except:
            return f"Invalid level: {level}"
            
    def cmd_help(self, args) -> str:
        """Show available commands"""
        help_text = [
            "Debug Commands:",
            "  log <level> <message> - Log a test message",
            "  agent - Show agent information",
            "  error - Generate a test error",
            "  memory - Show memory usage",
            "  save - Save session logs",
            "  clear - Clear log display",
            "  level <level> - Set log level",
            "  help - Show this help"
        ]
        
        return "\n".join(help_text)

# CSS for debug tab styling
DEBUG_TAB_CSS = """
/* Debug tab styling */
.debug-controls {
    height: 3;
    margin-bottom: 1;
}

.debug-panels {
    height: 75%;
}

.log-stream-panel {
    width: 50%;
    border: solid $primary;
    margin-right: 1;
}

.activity-panel {
    width: 25%;
    border: solid $secondary;
    margin-right: 1;
}

.error-panel {
    width: 25%;
    border: solid $error;
}

#debug-log {
    height: 90%;
    padding: 1;
}

#activity-table {
    height: 90%;
}

#error-list {
    height: 90%;
    padding: 1;
}

.debug-command {
    height: 3;
    margin-top: 1;
}

.command-label {
    width: 10;
    margin-right: 1;
}

#debug-command-input {
    width: 70%;
}

.no-errors {
    text-align: center;
    color: $success;
    margin-top: 2;
}
"""