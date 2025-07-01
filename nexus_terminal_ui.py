#!/usr/bin/env python3
"""
NEXUS Terminal UI Framework
A modular, feature-rich terminal UI for the NEXUS system.
"""

import asyncio
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import sys

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.align import Align
from rich.box import ROUNDED
from rich import print as rprint

# For keyboard input handling
try:
    import keyboard
except ImportError:
    keyboard = None
    
from pynput import keyboard as pynput_keyboard


class TabType(Enum):
    """Available tab types in NEXUS UI"""
    PROJECT = "Project"
    CHAT = "Chat"
    DEVELOPMENT = "Development"
    DESIGN = "Design"
    DEPLOY = "Deploy"
    MONITOR = "Monitor"


@dataclass
class UITheme:
    """Theme configuration for the UI"""
    primary: str = "bright_cyan"
    secondary: str = "bright_magenta"
    accent: str = "bright_yellow"
    success: str = "bright_green"
    error: str = "bright_red"
    warning: str = "yellow"
    info: str = "bright_blue"
    background: str = "black"
    text: str = "white"
    border: str = "dim white"
    selected: str = "reverse"


class Tab:
    """Base class for UI tabs"""
    
    def __init__(self, name: str, tab_type: TabType):
        self.name = name
        self.tab_type = tab_type
        self.content = Panel("", title=name, border_style="dim")
        self.is_active = False
        
    def render(self) -> Panel:
        """Render the tab content"""
        return self.content
        
    def update(self, content: Any) -> None:
        """Update tab content"""
        self.content = Panel(content, title=self.name, border_style="bright_cyan" if self.is_active else "dim")
        
    def on_activate(self) -> None:
        """Called when tab becomes active"""
        self.is_active = True
        
    def on_deactivate(self) -> None:
        """Called when tab becomes inactive"""
        self.is_active = False
        
    def handle_input(self, key: str) -> bool:
        """Handle keyboard input. Return True if handled."""
        return False


class ProjectTab(Tab):
    """Project management tab"""
    
    def __init__(self):
        super().__init__("Project", TabType.PROJECT)
        self.projects = []
        self.selected_index = 0
        
    def render(self) -> Panel:
        table = Table(title="Projects", box=ROUNDED, expand=True)
        table.add_column("ID", style="dim", width=6)
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Last Modified", style="yellow")
        
        # Example projects
        example_projects = [
            ("001", "NEXUS Core", "Active", "2 hours ago"),
            ("002", "Mobile App", "In Progress", "1 day ago"),
            ("003", "Web Dashboard", "Planning", "3 days ago"),
        ]
        
        for i, (proj_id, name, status, modified) in enumerate(example_projects):
            style = "reverse" if i == self.selected_index and self.is_active else ""
            table.add_row(proj_id, name, status, modified, style=style)
            
        self.update(table)
        return super().render()
        
    def handle_input(self, key: str) -> bool:
        if key == "up" and self.selected_index > 0:
            self.selected_index -= 1
            return True
        elif key == "down" and self.selected_index < 2:
            self.selected_index += 1
            return True
        return False


class ChatTab(Tab):
    """AI chat interface tab"""
    
    def __init__(self):
        super().__init__("Chat", TabType.CHAT)
        self.messages = []
        self.input_buffer = ""
        
    def render(self) -> Panel:
        chat_content = ""
        
        # Example chat messages
        example_messages = [
            ("User", "Help me create a new React component", "cyan"),
            ("NEXUS", "I'll help you create a React component. What type of component do you need?", "green"),
            ("User", "A dashboard widget showing real-time data", "cyan"),
            ("NEXUS", "Creating a real-time dashboard widget...", "green"),
        ]
        
        for sender, message, color in example_messages:
            chat_content += f"[{color}]{sender}:[/{color}] {message}\n"
            
        chat_content += f"\n[dim]> {self.input_buffer}[/dim]"
        
        self.update(Text.from_markup(chat_content))
        return super().render()


class DevelopmentTab(Tab):
    """Code development tab"""
    
    def __init__(self):
        super().__init__("Development", TabType.DEVELOPMENT)
        
    def render(self) -> Panel:
        dev_layout = Layout()
        dev_layout.split_column(
            Layout(Panel("File Explorer\n\n📁 nexus-core/\n  📄 main.py\n  📄 config.json\n📁 tests/", 
                        title="Files", border_style="dim"), name="files"),
            Layout(Panel("```python\n# NEXUS Core Module\n\nclass NexusCore:\n    def __init__(self):\n        self.initialized = True\n        \n    def process(self, data):\n        # AI processing logic\n        return data\n```", 
                        title="Editor", border_style="dim"), name="editor")
        )
        dev_layout["files"].ratio = 1
        dev_layout["editor"].ratio = 3
        
        self.update(dev_layout)
        return super().render()


class DesignTab(Tab):
    """UI/UX design tab"""
    
    def __init__(self):
        super().__init__("Design", TabType.DESIGN)
        
    def render(self) -> Panel:
        design_content = """
🎨 Design System

Colors:
  Primary: #00D9FF (Cyan)
  Secondary: #FF00FF (Magenta)
  Accent: #FFD700 (Gold)
  
Components:
  • Button
  • Card
  • Input
  • Modal
  • Navigation
  
Current Design: Dashboard Widget
Status: In Review
        """
        self.update(Text(design_content.strip()))
        return super().render()


class DeployTab(Tab):
    """Deployment management tab"""
    
    def __init__(self):
        super().__init__("Deploy", TabType.DEPLOY)
        
    def render(self) -> Panel:
        deploy_table = Table(title="Deployments", box=ROUNDED)
        deploy_table.add_column("Environment", style="cyan")
        deploy_table.add_column("Version", style="yellow")
        deploy_table.add_column("Status", style="green")
        deploy_table.add_column("Health", style="blue")
        
        deploy_table.add_row("Production", "v2.1.0", "Active", "✓ Healthy")
        deploy_table.add_row("Staging", "v2.2.0-beta", "Testing", "✓ Healthy")
        deploy_table.add_row("Development", "v2.2.0-dev", "Building", "⟳ Deploying")
        
        self.update(deploy_table)
        return super().render()


class MonitorTab(Tab):
    """System monitoring tab"""
    
    def __init__(self):
        super().__init__("Monitor", TabType.MONITOR)
        
    def render(self) -> Panel:
        monitor_content = """
📊 System Metrics

CPU Usage: ████████░░ 78%
Memory:    ██████░░░░ 62%
Disk:      █████░░░░░ 45%
Network:   ███░░░░░░░ 23%

🔄 Active Processes: 42
⚡ Requests/sec: 1,247
📥 Queue Length: 18
⏱️  Avg Response: 127ms

[green]✓ All systems operational[/green]
        """
        self.update(Text(monitor_content.strip()))
        return super().render()


class TabManager:
    """Manages tab lifecycle and switching"""
    
    def __init__(self):
        self.tabs: Dict[TabType, Tab] = {}
        self.active_tab: Optional[TabType] = None
        self.tab_order: List[TabType] = list(TabType)
        
    def register_tab(self, tab: Tab) -> None:
        """Register a new tab"""
        self.tabs[tab.tab_type] = tab
        
    def switch_to(self, tab_type: TabType) -> None:
        """Switch to a specific tab"""
        if self.active_tab:
            self.tabs[self.active_tab].on_deactivate()
            
        self.active_tab = tab_type
        self.tabs[tab_type].on_activate()
        
    def next_tab(self) -> None:
        """Switch to next tab"""
        if not self.active_tab:
            self.switch_to(self.tab_order[0])
            return
            
        current_index = self.tab_order.index(self.active_tab)
        next_index = (current_index + 1) % len(self.tab_order)
        self.switch_to(self.tab_order[next_index])
        
    def previous_tab(self) -> None:
        """Switch to previous tab"""
        if not self.active_tab:
            self.switch_to(self.tab_order[-1])
            return
            
        current_index = self.tab_order.index(self.active_tab)
        prev_index = (current_index - 1) % len(self.tab_order)
        self.switch_to(self.tab_order[prev_index])
        
    def get_active_tab(self) -> Optional[Tab]:
        """Get the currently active tab"""
        return self.tabs.get(self.active_tab) if self.active_tab else None


class EventSystem:
    """Simple event system for UI components"""
    
    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = {}
        
    def on(self, event: str, callback: Callable) -> None:
        """Register an event listener"""
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(callback)
        
    def emit(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all listeners"""
        if event in self.listeners:
            for callback in self.listeners[event]:
                callback(*args, **kwargs)


class CommandPalette:
    """Command palette for quick actions"""
    
    def __init__(self):
        self.commands = {
            "switch_project": "Switch to Project tab",
            "switch_chat": "Switch to Chat tab",
            "switch_dev": "Switch to Development tab",
            "switch_design": "Switch to Design tab",
            "switch_deploy": "Switch to Deploy tab",
            "switch_monitor": "Switch to Monitor tab",
            "reload": "Reload current tab",
            "quit": "Exit NEXUS UI",
        }
        self.visible = False
        self.selected_index = 0
        self.filter = ""
        
    def toggle(self) -> None:
        """Toggle command palette visibility"""
        self.visible = not self.visible
        if not self.visible:
            self.filter = ""
            self.selected_index = 0
            
    def get_filtered_commands(self) -> List[tuple]:
        """Get commands matching the current filter"""
        if not self.filter:
            return list(self.commands.items())
        return [(k, v) for k, v in self.commands.items() 
                if self.filter.lower() in k.lower() or self.filter.lower() in v.lower()]
        
    def render(self) -> Optional[Panel]:
        """Render the command palette"""
        if not self.visible:
            return None
            
        filtered = self.get_filtered_commands()
        
        content = f"[dim]Type to filter commands...[/dim]\n\n"
        content += f"Filter: {self.filter}_\n\n"
        
        for i, (cmd, desc) in enumerate(filtered):
            if i == self.selected_index:
                content += f"[reverse]▶ {cmd}: {desc}[/reverse]\n"
            else:
                content += f"  {cmd}: {desc}\n"
                
        return Panel(
            Text.from_markup(content),
            title="Command Palette (Esc to close)",
            border_style="bright_yellow",
            width=60,
            height=min(len(filtered) + 5, 20)
        )


class NexusTerminalUI:
    """Main NEXUS Terminal UI class"""
    
    def __init__(self, theme: Optional[UITheme] = None):
        self.console = Console()
        self.theme = theme or UITheme()
        self.tab_manager = TabManager()
        self.event_system = EventSystem()
        self.command_palette = CommandPalette()
        self.layout = Layout()
        self.running = False
        self.keyboard_listener = None
        
        # Initialize tabs
        self._init_tabs()
        
        # Setup layout
        self._setup_layout()
        
        # Setup event handlers
        self._setup_events()
        
    def _init_tabs(self) -> None:
        """Initialize all tabs"""
        self.tab_manager.register_tab(ProjectTab())
        self.tab_manager.register_tab(ChatTab())
        self.tab_manager.register_tab(DevelopmentTab())
        self.tab_manager.register_tab(DesignTab())
        self.tab_manager.register_tab(DeployTab())
        self.tab_manager.register_tab(MonitorTab())
        
        # Set default active tab
        self.tab_manager.switch_to(TabType.PROJECT)
        
    def _setup_layout(self) -> None:
        """Setup the main layout structure"""
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="tabs", size=3),
            Layout(name="main", ratio=1),
            Layout(name="status", size=1)
        )
        
    def _setup_events(self) -> None:
        """Setup event handlers"""
        self.event_system.on("tab_switch", self._on_tab_switch)
        self.event_system.on("command_execute", self._on_command_execute)
        
    def _on_tab_switch(self, tab_type: TabType) -> None:
        """Handle tab switch events"""
        self.tab_manager.switch_to(tab_type)
        
    def _on_command_execute(self, command: str) -> None:
        """Execute a command from the palette"""
        if command.startswith("switch_"):
            tab_map = {
                "switch_project": TabType.PROJECT,
                "switch_chat": TabType.CHAT,
                "switch_dev": TabType.DEVELOPMENT,
                "switch_design": TabType.DESIGN,
                "switch_deploy": TabType.DEPLOY,
                "switch_monitor": TabType.MONITOR,
            }
            if command in tab_map:
                self.tab_manager.switch_to(tab_map[command])
        elif command == "quit":
            self.stop()
        
        self.command_palette.toggle()
        
    def _render_header(self) -> Panel:
        """Render the header"""
        header_text = Text()
        header_text.append("NEXUS", style=f"bold {self.theme.primary}")
        header_text.append(" - ", style="dim")
        header_text.append("Intelligent Development Platform", style=self.theme.secondary)
        header_text.append(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
        
        return Panel(
            Align.center(header_text),
            border_style=self.theme.border,
            box=ROUNDED
        )
        
    def _render_tabs(self) -> Panel:
        """Render the tab bar"""
        tab_text = Text()
        
        for i, tab_type in enumerate(self.tab_manager.tab_order):
            if i > 0:
                tab_text.append(" │ ", style="dim")
                
            tab = self.tab_manager.tabs[tab_type]
            style = self.theme.selected if tab.is_active else ""
            
            # Add keyboard shortcut hint
            shortcut = f"F{i+1}"
            tab_text.append(f"{shortcut}:", style="dim")
            tab_text.append(tab.name, style=style)
            
        # Add help text
        tab_text.append("\n", style="")
        tab_text.append("Tab/Shift+Tab: Navigate │ Ctrl+P: Commands │ Ctrl+Q: Quit", style="dim")
        
        return Panel(
            Align.center(tab_text),
            border_style=self.theme.border,
            box=ROUNDED
        )
        
    def _render_status(self) -> Panel:
        """Render the status bar"""
        status_items = [
            ("Connected", self.theme.success),
            ("CPU: 45%", self.theme.info),
            ("Mem: 2.1GB", self.theme.warning),
            ("Tasks: 7", self.theme.accent),
        ]
        
        status_text = Text()
        for i, (item, style) in enumerate(status_items):
            if i > 0:
                status_text.append(" │ ", style="dim")
            status_text.append(item, style=style)
            
        return Panel(
            status_text,
            border_style=self.theme.border,
            box=ROUNDED,
            height=1
        )
        
    def _update_display(self) -> None:
        """Update the entire display"""
        # Update header
        self.layout["header"].update(self._render_header())
        
        # Update tabs
        self.layout["tabs"].update(self._render_tabs())
        
        # Update main content
        active_tab = self.tab_manager.get_active_tab()
        if active_tab:
            content = active_tab.render()
            
            # Overlay command palette if visible
            if self.command_palette.visible:
                palette_panel = self.command_palette.render()
                if palette_panel:
                    # Create overlay effect
                    overlay_layout = Layout()
                    overlay_layout.split_column(
                        Layout(palette_panel, size=15),
                        Layout(content)
                    )
                    self.layout["main"].update(overlay_layout)
                else:
                    self.layout["main"].update(content)
            else:
                self.layout["main"].update(content)
        
        # Update status
        self.layout["status"].update(self._render_status())
        
    def _setup_keyboard_handlers(self) -> None:
        """Setup keyboard event handlers"""
        def on_press(key):
            try:
                if hasattr(key, 'char'):
                    if self.command_palette.visible:
                        # Handle command palette input
                        if key.char:
                            self.command_palette.filter += key.char
                    else:
                        # Pass to active tab
                        active_tab = self.tab_manager.get_active_tab()
                        if active_tab:
                            active_tab.handle_input(key.char)
                            
                elif hasattr(key, 'name'):
                    if key == pynput_keyboard.Key.tab:
                        if self.command_palette.visible:
                            commands = self.command_palette.get_filtered_commands()
                            if commands:
                                self.command_palette.selected_index = (self.command_palette.selected_index + 1) % len(commands)
                        else:
                            # Check if shift is pressed
                            self.tab_manager.next_tab()
                            
                    elif key == pynput_keyboard.Key.esc:
                        if self.command_palette.visible:
                            self.command_palette.toggle()
                            
                    elif key == pynput_keyboard.Key.enter:
                        if self.command_palette.visible:
                            commands = self.command_palette.get_filtered_commands()
                            if commands and self.command_palette.selected_index < len(commands):
                                command = commands[self.command_palette.selected_index][0]
                                self._on_command_execute(command)
                                
                    elif key == pynput_keyboard.Key.backspace:
                        if self.command_palette.visible and self.command_palette.filter:
                            self.command_palette.filter = self.command_palette.filter[:-1]
                            
                    elif key == pynput_keyboard.Key.up:
                        if self.command_palette.visible:
                            commands = self.command_palette.get_filtered_commands()
                            if commands and self.command_palette.selected_index > 0:
                                self.command_palette.selected_index -= 1
                        else:
                            active_tab = self.tab_manager.get_active_tab()
                            if active_tab:
                                active_tab.handle_input("up")
                                
                    elif key == pynput_keyboard.Key.down:
                        if self.command_palette.visible:
                            commands = self.command_palette.get_filtered_commands()
                            if commands and self.command_palette.selected_index < len(commands) - 1:
                                self.command_palette.selected_index += 1
                        else:
                            active_tab = self.tab_manager.get_active_tab()
                            if active_tab:
                                active_tab.handle_input("down")
                                
                    # Function keys for direct tab switching
                    elif hasattr(key, 'vk') and 112 <= key.vk <= 117:  # F1-F6
                        tab_index = key.vk - 112
                        if tab_index < len(self.tab_manager.tab_order):
                            self.tab_manager.switch_to(self.tab_manager.tab_order[tab_index])
                            
            except AttributeError:
                pass
                
        def on_release(key):
            # Check for Ctrl+P (command palette)
            if key == pynput_keyboard.Key.ctrl_l or key == pynput_keyboard.Key.ctrl_r:
                return
                
            # Check for Ctrl+Q (quit)
            try:
                if hasattr(key, 'char') and key.char == 'q':
                    self.stop()
                elif hasattr(key, 'char') and key.char == 'p':
                    self.command_palette.toggle()
            except:
                pass
                
        self.keyboard_listener = pynput_keyboard.Listener(
            on_press=on_press,
            on_release=on_release
        )
        
    def run(self) -> None:
        """Run the terminal UI"""
        self.running = True
        
        # Setup keyboard handlers
        self._setup_keyboard_handlers()
        self.keyboard_listener.start()
        
        try:
            with Live(self.layout, console=self.console, screen=True, refresh_per_second=10) as live:
                while self.running:
                    self._update_display()
                    live.update(self.layout)
                    # Small delay to prevent high CPU usage
                    import time
                    time.sleep(0.1)
        finally:
            if self.keyboard_listener:
                self.keyboard_listener.stop()
                
    def stop(self) -> None:
        """Stop the UI"""
        self.running = False
        
    # Public API for programmatic control (e.g., voice commands)
    
    def switch_tab(self, tab_name: str) -> bool:
        """Switch to a tab by name (for voice control integration)"""
        tab_map = {
            "project": TabType.PROJECT,
            "chat": TabType.CHAT,
            "development": TabType.DEVELOPMENT,
            "design": TabType.DESIGN,
            "deploy": TabType.DEPLOY,
            "monitor": TabType.MONITOR,
        }
        
        tab_name_lower = tab_name.lower()
        if tab_name_lower in tab_map:
            self.tab_manager.switch_to(tab_map[tab_name_lower])
            return True
        return False
        
    def execute_command(self, command: str) -> bool:
        """Execute a command programmatically"""
        if command in self.command_palette.commands:
            self._on_command_execute(command)
            return True
        return False
        
    def get_current_tab(self) -> Optional[str]:
        """Get the name of the current tab"""
        if self.tab_manager.active_tab:
            return self.tab_manager.active_tab.value
        return None


# Example usage and voice control integration
class VoiceControlAdapter:
    """Adapter for integrating voice control with NEXUS UI"""
    
    def __init__(self, ui: NexusTerminalUI):
        self.ui = ui
        
    def process_voice_command(self, command: str) -> str:
        """Process a voice command and return response"""
        command_lower = command.lower()
        
        # Tab switching commands
        tab_keywords = ["project", "chat", "development", "design", "deploy", "monitor"]
        for keyword in tab_keywords:
            if keyword in command_lower and ("switch" in command_lower or "go to" in command_lower):
                if self.ui.switch_tab(keyword):
                    return f"Switched to {keyword} tab"
                    
        # Other commands
        if "command palette" in command_lower or "commands" in command_lower:
            self.ui.command_palette.toggle()
            return "Command palette opened"
            
        if "quit" in command_lower or "exit" in command_lower:
            self.ui.stop()
            return "Exiting NEXUS UI"
            
        return "Command not recognized"


def main():
    """Main entry point"""
    # Create and run the UI
    ui = NexusTerminalUI()
    
    # Example of programmatic tab switching (for demonstration)
    # This could be triggered by voice commands, API calls, etc.
    import threading
    import time
    
    def demo_tab_switching():
        """Demo function showing programmatic tab switching"""
        time.sleep(5)  # Wait 5 seconds
        ui.switch_tab("chat")
        time.sleep(3)
        ui.switch_tab("development")
        time.sleep(3)
        ui.switch_tab("monitor")
        
    # Uncomment to see demo
    # demo_thread = threading.Thread(target=demo_tab_switching)
    # demo_thread.daemon = True
    # demo_thread.start()
    
    try:
        ui.run()
    except KeyboardInterrupt:
        pass
    finally:
        print("\nNEXUS UI terminated.")


if __name__ == "__main__":
    main()