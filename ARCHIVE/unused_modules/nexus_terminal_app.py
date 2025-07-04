#!/usr/bin/env python3
"""
NEXUS Terminal Application
Main terminal interface with all features integrated
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import json
import time

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static, Input, TextLog, DataTable, ProgressBar
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.reactive import reactive
from textual.binding import Binding
from textual import events
from textual.widget import Widget

from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

logger = logging.getLogger(__name__)


class StatusBar(Static):
    """Status bar showing service health"""
    
    def __init__(self, startup_manager, **kwargs):
        super().__init__(**kwargs)
        self.startup_manager = startup_manager
        self.update_timer = None
        
    def on_mount(self):
        """Start status updates when mounted"""
        self.update_timer = self.set_interval(2.0, self.update_status)
        self.update_status()
        
    def update_status(self):
        """Update status display"""
        if not self.startup_manager:
            self.update("No services")
            return
            
        status = self.startup_manager.get_status_summary()
        
        # Build status text
        healthy = status["healthy_count"]
        total = status["total_count"]
        unhealthy = status["unhealthy_count"]
        
        if unhealthy > 0:
            health_icon = "⚠️"
            health_color = "yellow"
        elif healthy == total:
            health_icon = "✅"
            health_color = "green"
        else:
            health_icon = "🔄"
            health_color = "blue"
            
        status_text = f"{health_icon} Services: {healthy}/{total} healthy"
        
        self.update(f"[{health_color}]{status_text}[/{health_color}]")


class MainScreen(Screen):
    """Main application screen"""
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("ctrl+p", "show_projects", "Projects"),
        Binding("ctrl+d", "show_dev", "Development"),
        Binding("ctrl+t", "show_chat", "Chat"),
        Binding("ctrl+g", "show_design", "Design"),
        Binding("ctrl+y", "show_deploy", "Deploy"),
        Binding("ctrl+m", "show_monitor", "Monitor"),
        Binding("f1", "help", "Help"),
    ]
    
    def __init__(self, config: Dict[str, Any], startup_manager, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.startup_manager = startup_manager
        self.current_tab = "projects"
        
    def compose(self) -> ComposeResult:
        """Create UI layout"""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            # Tab bar
            with Horizontal(id="tab-bar"):
                yield Button("Projects [P]", id="tab-projects", classes="tab active")
                yield Button("Dev [D]", id="tab-dev", classes="tab")
                yield Button("Chat [T]", id="tab-chat", classes="tab")
                yield Button("Design [G]", id="tab-design", classes="tab")
                yield Button("Deploy [Y]", id="tab-deploy", classes="tab")
                yield Button("Monitor [M]", id="tab-monitor", classes="tab")
            
            # Content area
            with Container(id="content-area"):
                # Projects tab (default)
                with Container(id="projects-content", classes="tab-content active"):
                    yield Static("# 📁 Projects\n\nSelect or create a project to get started.", 
                               classes="markdown")
                    
                    with Horizontal(classes="button-row"):
                        yield Button("New Project", id="new-project", variant="primary")
                        yield Button("Open Project", id="open-project")
                        yield Button("Recent Projects", id="recent-projects")
                    
                    yield DataTable(id="projects-table", show_header=True)
                
                # Dev tab
                with Container(id="dev-content", classes="tab-content"):
                    yield Static("# 💻 Development\n\nCode editor and tools", classes="markdown")
                    yield TextLog(id="code-editor", wrap=False, markup=True)
                
                # Chat tab
                with Container(id="chat-content", classes="tab-content"):
                    yield Static("# 💬 AI Chat\n\nChat with NEXUS AI", classes="markdown")
                    yield TextLog(id="chat-log", wrap=True, markup=True)
                    yield Input(placeholder="Type your message...", id="chat-input")
                
                # Design tab
                with Container(id="design-content", classes="tab-content"):
                    yield Static("# 🎨 Design\n\nUI/UX design tools", classes="markdown")
                    yield Static("Design canvas will appear here", classes="placeholder")
                
                # Deploy tab
                with Container(id="deploy-content", classes="tab-content"):
                    yield Static("# 🚀 Deployment\n\nDeploy your applications", classes="markdown")
                    
                    with Horizontal(classes="button-row"):
                        yield Button("Deploy to Cloud", id="deploy-cloud", variant="success")
                        yield Button("Build Docker", id="build-docker")
                        yield Button("Configure CI/CD", id="configure-cicd")
                
                # Monitor tab
                with Container(id="monitor-content", classes="tab-content"):
                    yield Static("# 📊 Monitoring\n\nSystem and application monitoring", classes="markdown")
                    yield DataTable(id="services-table", show_header=True)
                    yield ProgressBar(id="cpu-usage", total=100)
                    yield ProgressBar(id="memory-usage", total=100)
        
        # Status bar
        yield StatusBar(self.startup_manager, id="status-bar")
        yield Footer()
    
    def on_mount(self):
        """Initialize when mounted"""
        # Initialize projects table
        projects_table = self.query_one("#projects-table", DataTable)
        projects_table.add_column("Name", width=30)
        projects_table.add_column("Type", width=15)
        projects_table.add_column("Status", width=15)
        projects_table.add_column("Modified", width=20)
        
        # Initialize services table
        services_table = self.query_one("#services-table", DataTable)
        services_table.add_column("Service", width=20)
        services_table.add_column("Status", width=15)
        services_table.add_column("Uptime", width=15)
        services_table.add_column("Health", width=10)
        
        # Load initial data
        self.load_projects()
        self.update_services()
        
        # Start update timers
        self.set_interval(5.0, self.update_services)
        self.set_interval(1.0, self.update_system_usage)
        
    def load_projects(self):
        """Load project list"""
        projects_table = self.query_one("#projects-table", DataTable)
        
        # Clear existing rows
        projects_table.clear()
        
        # Add sample projects (would load from disk in production)
        sample_projects = [
            ("My Web App", "React", "Active", "2 hours ago"),
            ("API Server", "Python", "Active", "1 day ago"),
            ("Mobile App", "Flutter", "Inactive", "3 days ago"),
        ]
        
        for project in sample_projects:
            projects_table.add_row(*project)
    
    def update_services(self):
        """Update services monitoring table"""
        if not self.startup_manager:
            return
            
        services_table = self.query_one("#services-table", DataTable)
        services_table.clear()
        
        status = self.startup_manager.get_status_summary()
        
        for name, info in status["services"].items():
            status_text = info["status"]
            
            # Format status with color
            if status_text == "healthy":
                status_display = "[green]● Healthy[/green]"
            elif status_text == "unhealthy":
                status_display = "[red]● Unhealthy[/red]"
            elif status_text == "starting":
                status_display = "[yellow]● Starting[/yellow]"
            else:
                status_display = f"[dim]● {status_text.title()}[/dim]"
            
            # Format uptime
            uptime = info.get("uptime", 0)
            if uptime > 0:
                hours = int(uptime // 3600)
                minutes = int((uptime % 3600) // 60)
                uptime_str = f"{hours}h {minutes}m"
            else:
                uptime_str = "N/A"
            
            # Health indicator
            health = "✅" if status_text == "healthy" else "❌"
            
            services_table.add_row(name.replace("_", " ").title(), status_display, uptime_str, health)
    
    def update_system_usage(self):
        """Update system usage bars"""
        try:
            import psutil
            
            # CPU usage
            cpu_bar = self.query_one("#cpu-usage", ProgressBar)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_bar.update(progress=cpu_percent)
            
            # Memory usage
            mem_bar = self.query_one("#memory-usage", ProgressBar)
            mem_percent = psutil.virtual_memory().percent
            mem_bar.update(progress=mem_percent)
            
        except Exception as e:
            logger.error(f"Error updating system usage: {e}")
    
    def switch_tab(self, tab_name: str):
        """Switch to a different tab"""
        # Update tab buttons
        for button in self.query(".tab"):
            button.remove_class("active")
        
        tab_button = self.query_one(f"#tab-{tab_name}", Button)
        tab_button.add_class("active")
        
        # Update content
        for content in self.query(".tab-content"):
            content.remove_class("active")
        
        content_area = self.query_one(f"#{tab_name}-content", Container)
        content_area.add_class("active")
        
        self.current_tab = tab_name
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        button_id = event.button.id
        
        # Tab switching
        if button_id and button_id.startswith("tab-"):
            tab_name = button_id.replace("tab-", "")
            self.switch_tab(tab_name)
        
        # Project actions
        elif button_id == "new-project":
            # Would show new project dialog
            self.notify("New project dialog would appear here")
        
        elif button_id == "open-project":
            # Would show file picker
            self.notify("File picker would appear here")
        
        # Deploy actions
        elif button_id == "deploy-cloud":
            self.notify("Cloud deployment wizard would start here")
        
        elif button_id == "build-docker":
            self.notify("Docker build process would start here")
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submissions"""
        if event.input.id == "chat-input":
            message = event.value
            if message.strip():
                # Add to chat log
                chat_log = self.query_one("#chat-log", TextLog)
                chat_log.write(f"[bold cyan]You:[/bold cyan] {message}")
                
                # Clear input
                event.input.value = ""
                
                # Simulate AI response (would call actual AI in production)
                await asyncio.sleep(0.5)
                chat_log.write("[bold green]NEXUS:[/bold green] I understand your request. How can I help you build that?")
    
    # Keyboard shortcuts
    async def action_show_projects(self) -> None:
        self.switch_tab("projects")
    
    async def action_show_dev(self) -> None:
        self.switch_tab("dev")
    
    async def action_show_chat(self) -> None:
        self.switch_tab("chat")
    
    async def action_show_design(self) -> None:
        self.switch_tab("design")
    
    async def action_show_deploy(self) -> None:
        self.switch_tab("deploy")
    
    async def action_show_monitor(self) -> None:
        self.switch_tab("monitor")
    
    async def action_help(self) -> None:
        """Show help screen"""
        self.notify("Help documentation would appear here")


class NexusTerminalApp(App):
    """Main NEXUS Terminal Application"""
    
    CSS = """
    #main-container {
        height: 100%;
    }
    
    #tab-bar {
        height: 3;
        background: $boost;
        padding: 0 1;
    }
    
    .tab {
        margin: 0 1;
        min-width: 12;
    }
    
    .tab.active {
        background: $accent;
    }
    
    #content-area {
        height: 100%;
        padding: 1;
    }
    
    .tab-content {
        display: none;
        height: 100%;
    }
    
    .tab-content.active {
        display: block;
    }
    
    .markdown {
        margin-bottom: 1;
    }
    
    .button-row {
        height: 3;
        margin: 1 0;
    }
    
    .placeholder {
        height: 100%;
        align: center middle;
        text-style: dim;
    }
    
    #status-bar {
        dock: bottom;
        height: 1;
        background: $boost;
        padding: 0 1;
    }
    
    #projects-table {
        height: 100%;
        margin-top: 1;
    }
    
    #services-table {
        height: 50%;
    }
    
    #chat-log {
        height: 80%;
        border: solid $primary;
        margin-bottom: 1;
    }
    
    #code-editor {
        height: 100%;
        border: solid $primary;
    }
    
    ProgressBar {
        margin: 1 0;
    }
    """
    
    def __init__(self, config: Dict[str, Any], startup_manager, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.startup_manager = startup_manager
        self.title = "NEXUS - AI Development Environment"
        
    def on_mount(self):
        """Initialize app when mounted"""
        self.push_screen(MainScreen(self.config, self.startup_manager))
    
    async def run_async(self):
        """Run the app asynchronously"""
        await self.run_async()
    
    async def shutdown(self):
        """Cleanup on shutdown"""
        # Any cleanup needed
        pass