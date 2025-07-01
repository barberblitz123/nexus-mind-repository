#!/usr/bin/env python3
"""
NEXUS Terminal UI - Production Version
Unified terminal interface with all tabs and features
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static, Input, TextLog, Tree, DataTable, ProgressBar
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
from rich.markdown import Markdown

# Import all tab components
try:
    from nexus_ui_project_tab import ProjectTab
    from nexus_ui_dev_tab import DevTab
    from nexus_ui_chat_tab import ChatTab
    from nexus_ui_design_tab import DesignTab
    from nexus_ui_deploy_tab import DeployTab
    from nexus_ui_monitor_tab import MonitorTab
    from nexus_ui_state_manager import StateManager
    from nexus_ui_components import create_button, create_panel
except ImportError:
    # Fallback implementations
    ProjectTab = DevTab = ChatTab = DesignTab = DeployTab = MonitorTab = None
    StateManager = None

class TabBar(Widget):
    """Custom tab bar with keyboard shortcuts"""
    
    def __init__(self, tabs: List[str], **kwargs):
        super().__init__(**kwargs)
        self.tabs = tabs
        self.active_tab = 0
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="tab-bar"):
            for i, tab in enumerate(self.tabs):
                shortcut = f"[{i+1}]" if i < 9 else ""
                active = "active" if i == self.active_tab else ""
                yield Button(f"{shortcut} {tab}", id=f"tab-{i}", classes=f"tab-button {active}")
    
    def switch_tab(self, index: int):
        """Switch to specified tab"""
        if 0 <= index < len(self.tabs):
            self.active_tab = index
            self.refresh()
            self.post_message(self.TabChanged(index))
    
    class TabChanged(Message):
        """Tab changed message"""
        def __init__(self, tab_index: int):
            super().__init__()
            self.tab_index = tab_index

class NexusTerminalUI(App):
    """Production NEXUS Terminal UI"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #tab-bar {
        height: 3;
        background: $primary;
        padding: 0 1;
    }
    
    .tab-button {
        margin: 0 1;
        background: $primary;
        color: $text;
        border: none;
    }
    
    .tab-button.active {
        background: $secondary;
        text-style: bold;
    }
    
    .tab-button:hover {
        background: $primary-lighten-1;
    }
    
    #content {
        padding: 1;
    }
    
    .status-bar {
        height: 3;
        background: $panel;
        padding: 0 1;
        dock: bottom;
    }
    
    .project-panel {
        border: solid $primary;
        padding: 1;
        margin: 0 1;
    }
    
    .chat-container {
        border: solid $secondary;
        height: 100%;
    }
    
    .code-editor {
        border: solid $accent;
        padding: 1;
    }
    
    .monitor-metric {
        border: solid $success;
        padding: 1;
        margin: 0 1;
    }
    
    .deploy-status {
        border: solid $warning;
        padding: 1;
    }
    
    Input {
        dock: bottom;
        margin: 1 0;
    }
    
    DataTable {
        height: 100%;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("f1", "help", "Help"),
        Binding("ctrl+p", "command_palette", "Command Palette"),
        Binding("ctrl+t", "toggle_theme", "Toggle Theme"),
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+n", "new", "New"),
        Binding("ctrl+o", "open", "Open"),
        Binding("ctrl+tab", "next_tab", "Next Tab"),
        Binding("ctrl+shift+tab", "prev_tab", "Previous Tab"),
        # Number keys for quick tab switching
        *[Binding(f"{i+1}", f"switch_tab_{i}", f"Tab {i+1}", show=False) for i in range(6)]
    ]
    
    def __init__(self, config: Dict = None, service_manager = None):
        super().__init__()
        self.config = config or {}
        self.service_manager = service_manager
        self.state_manager = StateManager() if StateManager else None
        self.current_tab = 0
        self.tabs = ["Project", "Development", "Chat", "Design", "Deploy", "Monitor"]
        self.tab_widgets = {}
        self.console = Console()
        
        # Load saved layout
        self.layout_config = self.load_layout()
        
        # Initialize plugin system
        self.plugins = self.load_plugins()
    
    def compose(self) -> ComposeResult:
        """Create the UI layout"""
        yield Header()
        
        # Tab bar
        self.tab_bar = TabBar(self.tabs)
        yield self.tab_bar
        
        # Main content area
        with Container(id="content"):
            # Create all tab contents
            for i, tab_name in enumerate(self.tabs):
                display = "block" if i == self.current_tab else "none"
                
                with Container(id=f"tab-content-{i}", classes="tab-content", styles=f"display: {display}"):
                    if tab_name == "Project" and ProjectTab:
                        self.tab_widgets["project"] = ProjectTab()
                        yield self.tab_widgets["project"]
                    elif tab_name == "Development" and DevTab:
                        self.tab_widgets["dev"] = DevTab()
                        yield self.tab_widgets["dev"]
                    elif tab_name == "Chat" and ChatTab:
                        self.tab_widgets["chat"] = ChatTab()
                        yield self.tab_widgets["chat"]
                    elif tab_name == "Design" and DesignTab:
                        self.tab_widgets["design"] = DesignTab()
                        yield self.tab_widgets["design"]
                    elif tab_name == "Deploy" and DeployTab:
                        self.tab_widgets["deploy"] = DeployTab()
                        yield self.tab_widgets["deploy"]
                    elif tab_name == "Monitor" and MonitorTab:
                        self.tab_widgets["monitor"] = MonitorTab()
                        yield self.tab_widgets["monitor"]
                    else:
                        # Fallback content
                        yield Static(f"[bold]{tab_name} Tab[/bold]\n\nContent coming soon...")
        
        # Status bar
        with Horizontal(classes="status-bar"):
            yield Static("NEXUS v2.0", id="status-left")
            yield Static("", id="status-center")
            yield Static("", id="status-right")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize when app is mounted"""
        self.title = "NEXUS Terminal UI"
        self.sub_title = "AI Development Platform"
        
        # Set initial theme
        self.theme = self.config.get('theme', 'dark')
        if self.theme == 'dark':
            self.dark = True
        
        # Start background tasks
        self.set_interval(1.0, self.update_status)
        self.set_interval(5.0, self.check_services)
        
        # Initialize state manager connections
        if self.state_manager:
            self.state_manager.on_state_change = self.handle_state_change
    
    def on_tab_bar_tab_changed(self, message: TabBar.TabChanged) -> None:
        """Handle tab change"""
        self.switch_to_tab(message.tab_index)
    
    def switch_to_tab(self, index: int) -> None:
        """Switch to specified tab"""
        if 0 <= index < len(self.tabs):
            # Hide current tab
            old_content = self.query_one(f"#tab-content-{self.current_tab}")
            old_content.styles.display = "none"
            
            # Show new tab
            self.current_tab = index
            new_content = self.query_one(f"#tab-content-{index}")
            new_content.styles.display = "block"
            
            # Update tab bar
            self.tab_bar.switch_tab(index)
            
            # Update status
            self.query_one("#status-center").update(f"Current: {self.tabs[index]}")
    
    async def update_status(self) -> None:
        """Update status bar"""
        try:
            # Update time
            current_time = datetime.now().strftime("%H:%M:%S")
            self.query_one("#status-right").update(current_time)
            
            # Update service status if available
            if self.service_manager:
                status = self.service_manager.get_status()
                status_text = f"Services: {status.get('active', 0)}/{status.get('total', 0)}"
                self.query_one("#status-left").update(f"NEXUS v2.0 | {status_text}")
        except Exception as e:
            self.log.error(f"Status update error: {e}")
    
    async def check_services(self) -> None:
        """Check background services"""
        if self.service_manager:
            try:
                health = await self.service_manager.health_check()
                
                # Update monitor tab if available
                if "monitor" in self.tab_widgets:
                    self.tab_widgets["monitor"].update_health(health)
                    
            except Exception as e:
                self.log.error(f"Service check error: {e}")
    
    def handle_state_change(self, state_type: str, data: Any) -> None:
        """Handle state changes from state manager"""
        # Propagate to relevant tabs
        for tab_widget in self.tab_widgets.values():
            if hasattr(tab_widget, 'on_state_change'):
                tab_widget.on_state_change(state_type, data)
    
    def load_layout(self) -> Dict:
        """Load saved layout configuration"""
        layout_file = Path.home() / '.nexus' / 'layout.json'
        if layout_file.exists():
            with open(layout_file, 'r') as f:
                return json.load(f)
        
        # Default layout
        return {
            'tab_order': self.tabs,
            'default_tab': 0,
            'window_splits': {},
            'panel_sizes': {}
        }
    
    def save_layout(self) -> None:
        """Save current layout configuration"""
        layout_file = Path.home() / '.nexus' / 'layout.json'
        layout_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.layout_config['current_tab'] = self.current_tab
        
        with open(layout_file, 'w') as f:
            json.dump(self.layout_config, f, indent=2)
    
    def load_plugins(self) -> List:
        """Load UI plugins"""
        plugins = []
        plugin_dir = Path.home() / '.nexus' / 'plugins'
        
        if plugin_dir.exists():
            sys.path.insert(0, str(plugin_dir))
            
            for plugin_file in plugin_dir.glob('*.py'):
                try:
                    # Import plugin
                    module_name = plugin_file.stem
                    module = __import__(module_name)
                    
                    # Initialize plugin
                    if hasattr(module, 'NexusPlugin'):
                        plugin = module.NexusPlugin(self)
                        plugins.append(plugin)
                        self.log.info(f"Loaded plugin: {module_name}")
                        
                except Exception as e:
                    self.log.error(f"Failed to load plugin {plugin_file}: {e}")
        
        return plugins
    
    # Action handlers
    def action_quit(self) -> None:
        """Quit the application"""
        self.save_layout()
        self.exit()
    
    def action_help(self) -> None:
        """Show help"""
        help_text = """
# NEXUS Terminal UI Help

## Keyboard Shortcuts
- **1-6**: Switch to tab 1-6
- **Ctrl+Tab**: Next tab
- **Ctrl+Shift+Tab**: Previous tab
- **Ctrl+Q**: Quit
- **F1**: This help
- **Ctrl+P**: Command palette
- **Ctrl+T**: Toggle theme

## Tab Overview
1. **Project**: Manage projects and files
2. **Development**: Code editor and tools
3. **Chat**: AI assistant chat
4. **Design**: Visual design tools
5. **Deploy**: Deployment management
6. **Monitor**: System monitoring
        """
        
        # Show help in chat tab if available
        if "chat" in self.tab_widgets:
            self.switch_to_tab(2)  # Chat tab
            self.tab_widgets["chat"].show_message(help_text, sender="System")
    
    def action_command_palette(self) -> None:
        """Show command palette"""
        # TODO: Implement command palette
        self.notify("Command palette coming soon!")
    
    def action_toggle_theme(self) -> None:
        """Toggle theme"""
        self.dark = not self.dark
        self.theme = "dark" if self.dark else "light"
        self.notify(f"Theme: {self.theme}")
    
    def action_save(self) -> None:
        """Save current work"""
        current_tab_name = self.tabs[self.current_tab].lower()
        if current_tab_name in self.tab_widgets:
            tab = self.tab_widgets[current_tab_name]
            if hasattr(tab, 'save'):
                tab.save()
                self.notify("Saved!")
    
    def action_new(self) -> None:
        """Create new item in current tab"""
        current_tab_name = self.tabs[self.current_tab].lower()
        if current_tab_name in self.tab_widgets:
            tab = self.tab_widgets[current_tab_name]
            if hasattr(tab, 'new'):
                tab.new()
    
    def action_open(self) -> None:
        """Open item in current tab"""
        current_tab_name = self.tabs[self.current_tab].lower()
        if current_tab_name in self.tab_widgets:
            tab = self.tab_widgets[current_tab_name]
            if hasattr(tab, 'open'):
                tab.open()
    
    def action_next_tab(self) -> None:
        """Switch to next tab"""
        next_tab = (self.current_tab + 1) % len(self.tabs)
        self.switch_to_tab(next_tab)
    
    def action_prev_tab(self) -> None:
        """Switch to previous tab"""
        prev_tab = (self.current_tab - 1) % len(self.tabs)
        self.switch_to_tab(prev_tab)
    
    # Quick tab switching
    def action_switch_tab_0(self) -> None: self.switch_to_tab(0)
    def action_switch_tab_1(self) -> None: self.switch_to_tab(1)
    def action_switch_tab_2(self) -> None: self.switch_to_tab(2)
    def action_switch_tab_3(self) -> None: self.switch_to_tab(3)
    def action_switch_tab_4(self) -> None: self.switch_to_tab(4)
    def action_switch_tab_5(self) -> None: self.switch_to_tab(5)

def main():
    """Main entry point"""
    app = NexusTerminalUI()
    app.run()

if __name__ == "__main__":
    main()