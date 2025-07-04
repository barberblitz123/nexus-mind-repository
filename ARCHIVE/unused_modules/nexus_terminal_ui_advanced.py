#!/usr/bin/env python3
"""
NEXUS Terminal UI Advanced - Production-grade terminal interface
A VS Code-like experience in your terminal with Rich/Textual framework
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
import json
import psutil
import aiofiles

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Header, Footer, Tree, Static, Label, Button, Input,
    DataTable, TextLog, ProgressBar, Tabs, Tab, TabbedContent,
    TabPane, DirectoryTree, RichLog, LoadingIndicator, Switch,
    Select, ListView, ListItem, Markdown, RadioSet, RadioButton
)
from textual.reactive import reactive, var
from textual.message import Message
from textual.worker import Worker, get_current_worker
from textual.css.query import NoMatches

from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.traceback import Traceback

# Import our custom components
try:
    from nexus_ui_components import (
        CodeEditor, FileExplorer, ChatInterface, 
        ProgressTracker, NotificationSystem, ContextMenu,
        TabManager, ModalDialog
    )
    from nexus_ui_state_manager import StateManager, UIState
    from nexus_keybindings import KeybindingManager, KeyCommand
except ImportError:
    # Fallback for initial development
    pass


class CommandPalette(ModalScreen):
    """Command palette modal (Ctrl+P)"""
    
    CSS = """
    CommandPalette {
        align: center middle;
    }
    
    #command-container {
        width: 80%;
        height: 70%;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    #command-input {
        dock: top;
        height: 3;
        margin-bottom: 1;
    }
    
    #command-list {
        height: 100%;
        overflow-y: auto;
    }
    """
    
    def __init__(self, commands: List[Dict[str, Any]]):
        super().__init__()
        self.commands = commands
        self.filtered_commands = commands.copy()
    
    def compose(self) -> ComposeResult:
        with Container(id="command-container"):
            yield Input(
                placeholder="Type a command...",
                id="command-input"
            )
            yield ListView(
                *[ListItem(Label(cmd["name"])) for cmd in self.commands],
                id="command-list"
            )
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter commands as user types"""
        query = event.value.lower()
        list_view = self.query_one("#command-list", ListView)
        list_view.clear()
        
        self.filtered_commands = [
            cmd for cmd in self.commands
            if query in cmd["name"].lower() or 
               query in cmd.get("description", "").lower()
        ]
        
        for cmd in self.filtered_commands:
            list_view.append(ListItem(Label(cmd["name"])))
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Execute selected command"""
        index = event.list_view.index
        if 0 <= index < len(self.filtered_commands):
            command = self.filtered_commands[index]
            self.dismiss(command)


class NEXUSTerminalUI(App):
    """Main NEXUS Terminal UI Application"""
    
    CSS = """
    NEXUSTerminalUI {
        background: $background;
    }
    
    #main-container {
        layout: grid;
        grid-size: 3 1;
        grid-columns: 20% 60% 20%;
        height: 100%;
    }
    
    #sidebar-left {
        background: $panel;
        border-right: solid $primary;
        overflow-y: auto;
    }
    
    #main-content {
        background: $background;
    }
    
    #sidebar-right {
        background: $panel;
        border-left: solid $primary;
        overflow-y: auto;
    }
    
    #status-bar {
        dock: bottom;
        height: 1;
        background: $accent;
    }
    
    .tab-content {
        height: 100%;
        overflow: auto;
    }
    
    #editor-container {
        height: 70%;
    }
    
    #terminal-container {
        height: 30%;
        border-top: solid $primary;
    }
    
    .notification {
        dock: top;
        height: 3;
        background: $warning;
        padding: 1;
        display: none;
    }
    
    .context-menu {
        position: absolute;
        background: $surface;
        border: solid $primary;
        padding: 1;
        display: none;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+p", "command_palette", "Command Palette"),
        Binding("ctrl+shift+e", "toggle_explorer", "Toggle Explorer"),
        Binding("ctrl+shift+g", "toggle_git", "Toggle Git"),
        Binding("ctrl+shift+x", "toggle_extensions", "Toggle Extensions"),
        Binding("ctrl+shift+d", "toggle_debug", "Toggle Debug"),
        Binding("ctrl+`", "toggle_terminal", "Toggle Terminal"),
        Binding("ctrl+b", "toggle_sidebar", "Toggle Sidebar"),
        Binding("ctrl+s", "save_file", "Save File"),
        Binding("ctrl+shift+s", "save_all", "Save All"),
        Binding("ctrl+w", "close_tab", "Close Tab"),
        Binding("ctrl+shift+w", "close_all_tabs", "Close All Tabs"),
        Binding("ctrl+tab", "next_tab", "Next Tab"),
        Binding("ctrl+shift+tab", "prev_tab", "Previous Tab"),
        Binding("ctrl+n", "new_file", "New File"),
        Binding("ctrl+o", "open_file", "Open File"),
        Binding("ctrl+shift+n", "new_window", "New Window"),
        Binding("f1", "show_help", "Help"),
        Binding("ctrl+shift+p", "show_all_commands", "Show All Commands"),
        Binding("ctrl+k ctrl+t", "change_theme", "Change Theme", key_display="Ctrl+K Ctrl+T"),
        Binding("ctrl+z", "undo", "Undo"),
        Binding("ctrl+shift+z", "redo", "Redo"),
        Binding("ctrl+x", "cut", "Cut"),
        Binding("ctrl+c", "copy", "Copy"),
        Binding("ctrl+v", "paste", "Paste"),
        Binding("ctrl+f", "find", "Find"),
        Binding("ctrl+h", "replace", "Replace"),
        Binding("ctrl+g", "goto_line", "Go to Line"),
        Binding("ctrl+shift+f", "find_in_files", "Find in Files"),
        Binding("alt+left", "navigate_back", "Navigate Back"),
        Binding("alt+right", "navigate_forward", "Navigate Forward"),
        Binding("f5", "run_debug", "Start Debugging"),
        Binding("ctrl+f5", "run_without_debug", "Run Without Debugging"),
        Binding("f9", "toggle_breakpoint", "Toggle Breakpoint"),
        Binding("f11", "fullscreen", "Toggle Fullscreen"),
        Binding("escape", "escape", "Escape", show=False),
    ]
    
    # UI State
    show_sidebar_left = var(True)
    show_sidebar_right = var(True)
    show_terminal = var(True)
    current_theme = var("dark")
    
    def __init__(self):
        super().__init__()
        self.title = "NEXUS Terminal UI"
        self.sub_title = "Advanced Development Environment"
        
        # Initialize state manager
        self.state_manager = None
        self.keybinding_manager = None
        
        # Track open files and tabs
        self.open_files: Dict[str, Dict[str, Any]] = {}
        self.active_tab: Optional[str] = None
        
        # Command registry
        self.commands = self._register_commands()
        
        # System metrics
        self.cpu_percent = 0.0
        self.memory_percent = 0.0
        
        # Workspace settings
        self.workspace_path = Path.cwd()
        self.settings = self._load_settings()
    
    def _register_commands(self) -> List[Dict[str, Any]]:
        """Register all available commands"""
        return [
            {"name": "File: New File", "action": self.action_new_file, "shortcut": "Ctrl+N"},
            {"name": "File: Open File", "action": self.action_open_file, "shortcut": "Ctrl+O"},
            {"name": "File: Save", "action": self.action_save_file, "shortcut": "Ctrl+S"},
            {"name": "File: Save All", "action": self.action_save_all, "shortcut": "Ctrl+Shift+S"},
            {"name": "View: Toggle Sidebar", "action": self.action_toggle_sidebar, "shortcut": "Ctrl+B"},
            {"name": "View: Toggle Terminal", "action": self.action_toggle_terminal, "shortcut": "Ctrl+`"},
            {"name": "View: Command Palette", "action": self.action_command_palette, "shortcut": "Ctrl+P"},
            {"name": "Edit: Undo", "action": self.action_undo, "shortcut": "Ctrl+Z"},
            {"name": "Edit: Redo", "action": self.action_redo, "shortcut": "Ctrl+Shift+Z"},
            {"name": "Edit: Find", "action": self.action_find, "shortcut": "Ctrl+F"},
            {"name": "Edit: Replace", "action": self.action_replace, "shortcut": "Ctrl+H"},
            {"name": "Terminal: New Terminal", "action": self.new_terminal, "shortcut": "Ctrl+Shift+`"},
            {"name": "Debug: Start Debugging", "action": self.action_run_debug, "shortcut": "F5"},
            {"name": "Theme: Change Theme", "action": self.action_change_theme, "shortcut": "Ctrl+K Ctrl+T"},
            {"name": "Help: Show Help", "action": self.action_show_help, "shortcut": "F1"},
        ]
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load workspace settings"""
        settings_file = self.workspace_path / ".nexus" / "settings.json"
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                return json.load(f)
        return {
            "theme": "dark",
            "editor": {
                "fontSize": 14,
                "tabSize": 4,
                "wordWrap": "off",
                "minimap": True,
                "lineNumbers": True,
            },
            "terminal": {
                "fontSize": 12,
                "shell": os.environ.get("SHELL", "/bin/bash"),
            },
            "keybindings": {},
        }
    
    def compose(self) -> ComposeResult:
        """Create the UI layout"""
        yield Header()
        
        # Notification area
        yield Container(
            Static("", id="notification-text"),
            classes="notification",
            id="notification-area"
        )
        
        # Main container with 3-column layout
        with Container(id="main-container"):
            # Left sidebar
            with ScrollableContainer(id="sidebar-left"):
                yield Tabs(
                    Tab("Explorer", id="tab-explorer"),
                    Tab("Search", id="tab-search"),
                    Tab("Git", id="tab-git"),
                    Tab("Debug", id="tab-debug"),
                    Tab("Extensions", id="tab-extensions"),
                    id="sidebar-tabs"
                )
                
                with TabbedContent(initial="tab-explorer"):
                    with TabPane("Explorer", id="tab-explorer"):
                        yield DirectoryTree(str(self.workspace_path), id="file-tree")
                    
                    with TabPane("Search", id="tab-search"):
                        yield Input(placeholder="Search files...", id="search-input")
                        yield ListView(id="search-results")
                    
                    with TabPane("Git", id="tab-git"):
                        yield Static("Git status will appear here", id="git-status")
                    
                    with TabPane("Debug", id="tab-debug"):
                        yield Static("Debug panel", id="debug-panel")
                    
                    with TabPane("Extensions", id="tab-extensions"):
                        yield Static("Extensions panel", id="extensions-panel")
            
            # Main content area
            with Container(id="main-content"):
                # Editor area
                with Container(id="editor-container"):
                    yield Tabs(id="editor-tabs")
                    yield Container(id="editor-content")
                
                # Terminal area
                with Container(id="terminal-container"):
                    yield Tabs(
                        Tab("Terminal 1", id="term-1"),
                        Tab("Output", id="term-output"),
                        Tab("Problems", id="term-problems"),
                        Tab("Debug Console", id="term-debug"),
                        id="terminal-tabs"
                    )
                    with TabbedContent(initial="term-1"):
                        with TabPane("Terminal 1", id="term-1"):
                            yield TextLog(id="terminal-1", wrap=False)
                        with TabPane("Output", id="term-output"):
                            yield TextLog(id="output-log", wrap=False)
                        with TabPane("Problems", id="term-problems"):
                            yield DataTable(id="problems-table")
                        with TabPane("Debug Console", id="term-debug"):
                            yield TextLog(id="debug-console", wrap=False)
            
            # Right sidebar
            with ScrollableContainer(id="sidebar-right"):
                yield Tabs(
                    Tab("Outline", id="tab-outline"),
                    Tab("Timeline", id="tab-timeline"),
                    Tab("Bookmarks", id="tab-bookmarks"),
                    id="right-tabs"
                )
                
                with TabbedContent(initial="tab-outline"):
                    with TabPane("Outline", id="tab-outline"):
                        yield Tree("Outline", id="outline-tree")
                    
                    with TabPane("Timeline", id="tab-timeline"):
                        yield ListView(id="timeline-list")
                    
                    with TabPane("Bookmarks", id="tab-bookmarks"):
                        yield ListView(id="bookmarks-list")
        
        # Status bar
        yield Container(
            Static("Ready", id="status-message"),
            Static("Ln 1, Col 1", id="cursor-position"),
            Static("UTF-8", id="encoding"),
            Static("LF", id="line-ending"),
            Static("Python", id="language-mode"),
            Static("", id="git-branch"),
            Static("CPU: 0%", id="cpu-usage"),
            Static("MEM: 0%", id="memory-usage"),
            id="status-bar"
        )
        
        yield Footer()
    
    async def on_mount(self) -> None:
        """Initialize the UI after mounting"""
        # Start system monitoring
        self.set_interval(1.0, self.update_system_metrics)
        
        # Initialize components
        self.init_file_explorer()
        self.init_terminal()
        self.init_problems_table()
        
        # Load previous session if exists
        await self.restore_session()
        
        # Show welcome tab if no files open
        if not self.open_files:
            await self.show_welcome_tab()
    
    def init_file_explorer(self) -> None:
        """Initialize file explorer"""
        file_tree = self.query_one("#file-tree", DirectoryTree)
        file_tree.show_guides = True
        file_tree.guide_depth = 4
    
    def init_terminal(self) -> None:
        """Initialize terminal"""
        terminal = self.query_one("#terminal-1", TextLog)
        terminal.write("NEXUS Terminal v1.0.0")
        terminal.write(f"Working directory: {self.workspace_path}")
        terminal.write("Type 'help' for available commands\n")
    
    def init_problems_table(self) -> None:
        """Initialize problems table"""
        table = self.query_one("#problems-table", DataTable)
        table.add_columns("Type", "File", "Line", "Message")
        table.zebra_stripes = True
    
    async def show_welcome_tab(self) -> None:
        """Show welcome tab"""
        welcome_content = """
# Welcome to NEXUS Terminal UI

## Quick Start
- **Ctrl+P**: Open command palette
- **Ctrl+N**: Create new file
- **Ctrl+O**: Open file
- **Ctrl+S**: Save file
- **Ctrl+`**: Toggle terminal

## Recent Files
No recent files

## Getting Started
1. Open a folder or file
2. Start coding with full IDE features
3. Use integrated terminal for commands
4. Debug your applications with F5
        """
        
        await self.open_tab("Welcome", welcome_content, file_type="markdown")
    
    async def update_system_metrics(self) -> None:
        """Update CPU and memory usage"""
        self.cpu_percent = psutil.cpu_percent(interval=0.1)
        self.memory_percent = psutil.virtual_memory().percent
        
        try:
            cpu_label = self.query_one("#cpu-usage", Static)
            cpu_label.update(f"CPU: {self.cpu_percent:.1f}%")
            
            mem_label = self.query_one("#memory-usage", Static)
            mem_label.update(f"MEM: {self.memory_percent:.1f}%")
        except NoMatches:
            pass
    
    async def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection from explorer"""
        await self.open_file(event.path)
    
    async def open_file(self, file_path: str) -> None:
        """Open a file in the editor"""
        path = Path(file_path)
        if not path.exists():
            await self.show_notification(f"File not found: {file_path}", "error")
            return
        
        # Check if file is already open
        if file_path in self.open_files:
            await self.activate_tab(file_path)
            return
        
        try:
            # Read file content
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            # Detect file type
            file_type = self.detect_file_type(path)
            
            # Open in new tab
            await self.open_tab(path.name, content, file_path, file_type)
            
        except Exception as e:
            await self.show_notification(f"Error opening file: {str(e)}", "error")
    
    def detect_file_type(self, path: Path) -> str:
        """Detect file type for syntax highlighting"""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.md': 'markdown',
            '.sh': 'bash',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.rs': 'rust',
            '.go': 'go',
            '.java': 'java',
            '.rb': 'ruby',
            '.php': 'php',
            '.sql': 'sql',
            '.xml': 'xml',
        }
        return extension_map.get(path.suffix.lower(), 'text')
    
    async def open_tab(self, title: str, content: str, file_path: Optional[str] = None, file_type: str = "text") -> None:
        """Open a new editor tab"""
        # Create tab ID
        tab_id = file_path or f"untitled-{len(self.open_files)}"
        
        # Add to open files
        self.open_files[tab_id] = {
            "title": title,
            "content": content,
            "file_path": file_path,
            "file_type": file_type,
            "modified": False,
            "cursor_position": (0, 0),
        }
        
        # Add tab to editor
        editor_tabs = self.query_one("#editor-tabs", Tabs)
        editor_tabs.add_tab(Tab(title, id=f"tab-{tab_id}"))
        
        # Switch to new tab
        await self.activate_tab(tab_id)
    
    async def activate_tab(self, tab_id: str) -> None:
        """Activate a specific tab"""
        self.active_tab = tab_id
        file_info = self.open_files.get(tab_id)
        
        if not file_info:
            return
        
        # Update editor content
        editor_content = self.query_one("#editor-content", Container)
        editor_content.remove_children()
        
        # Create syntax highlighted content
        if file_info["file_type"] == "markdown":
            widget = Markdown(file_info["content"])
        else:
            # For now, use RichLog for syntax highlighting
            log = RichLog(id="active-editor", wrap=False)
            editor_content.mount(log)
            
            # Add syntax highlighted content
            syntax = Syntax(
                file_info["content"],
                file_info["file_type"],
                theme="monokai",
                line_numbers=True,
            )
            log.write(syntax)
        
        editor_content.mount(widget if file_info["file_type"] == "markdown" else log)
        
        # Update status bar
        self.update_status_bar(file_info)
    
    def update_status_bar(self, file_info: Dict[str, Any]) -> None:
        """Update status bar with file info"""
        if file_info.get("file_path"):
            status = self.query_one("#status-message", Static)
            status.update(f"📁 {file_info['file_path']}")
        
        # Update language mode
        lang_mode = self.query_one("#language-mode", Static)
        lang_mode.update(file_info["file_type"].title())
        
        # Update cursor position
        cursor_pos = self.query_one("#cursor-position", Static)
        line, col = file_info.get("cursor_position", (1, 1))
        cursor_pos.update(f"Ln {line + 1}, Col {col + 1}")
    
    async def show_notification(self, message: str, level: str = "info") -> None:
        """Show a notification"""
        notification = self.query_one("#notification-area", Container)
        notification_text = self.query_one("#notification-text", Static)
        
        # Style based on level
        level_styles = {
            "info": "blue",
            "warning": "yellow",
            "error": "red",
            "success": "green",
        }
        
        notification.styles.background = level_styles.get(level, "blue")
        notification_text.update(message)
        notification.styles.display = "block"
        
        # Auto-hide after 3 seconds
        await asyncio.sleep(3)
        notification.styles.display = "none"
    
    async def restore_session(self) -> None:
        """Restore previous session"""
        session_file = self.workspace_path / ".nexus" / "session.json"
        if session_file.exists():
            try:
                with open(session_file, 'r') as f:
                    session = json.load(f)
                
                # Restore open files
                for file_path in session.get("open_files", []):
                    if Path(file_path).exists():
                        await self.open_file(file_path)
                
                # Restore active tab
                if session.get("active_tab") in self.open_files:
                    await self.activate_tab(session["active_tab"])
                
            except Exception as e:
                self.log(f"Failed to restore session: {e}")
    
    async def save_session(self) -> None:
        """Save current session"""
        session_dir = self.workspace_path / ".nexus"
        session_dir.mkdir(exist_ok=True)
        
        session = {
            "open_files": [f["file_path"] for f in self.open_files.values() if f.get("file_path")],
            "active_tab": self.active_tab,
            "timestamp": datetime.now().isoformat(),
        }
        
        with open(session_dir / "session.json", 'w') as f:
            json.dump(session, f, indent=2)
    
    # Action handlers
    async def action_command_palette(self) -> None:
        """Show command palette"""
        def handle_command(command: Optional[Dict[str, Any]]) -> None:
            if command and "action" in command:
                self.call_later(command["action"])
        
        await self.push_screen(CommandPalette(self.commands), handle_command)
    
    async def action_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility"""
        sidebar = self.query_one("#sidebar-left")
        sidebar.display = not sidebar.display
        self.show_sidebar_left = sidebar.display
    
    async def action_toggle_terminal(self) -> None:
        """Toggle terminal visibility"""
        terminal = self.query_one("#terminal-container")
        terminal.display = not terminal.display
        self.show_terminal = terminal.display
    
    async def action_new_file(self) -> None:
        """Create new file"""
        await self.open_tab("Untitled", "", file_type="text")
    
    async def action_open_file(self) -> None:
        """Open file dialog"""
        # For now, show a simple input dialog
        await self.show_notification("File picker not implemented yet", "warning")
    
    async def action_save_file(self) -> None:
        """Save current file"""
        if not self.active_tab:
            return
        
        file_info = self.open_files.get(self.active_tab)
        if file_info and file_info.get("file_path"):
            # Save file
            try:
                async with aiofiles.open(file_info["file_path"], 'w', encoding='utf-8') as f:
                    await f.write(file_info["content"])
                
                file_info["modified"] = False
                await self.show_notification(f"Saved: {file_info['file_path']}", "success")
            except Exception as e:
                await self.show_notification(f"Save failed: {str(e)}", "error")
        else:
            # Need to show save dialog
            await self.show_notification("Save As not implemented yet", "warning")
    
    async def action_save_all(self) -> None:
        """Save all open files"""
        for tab_id, file_info in self.open_files.items():
            if file_info.get("modified") and file_info.get("file_path"):
                try:
                    async with aiofiles.open(file_info["file_path"], 'w', encoding='utf-8') as f:
                        await f.write(file_info["content"])
                    file_info["modified"] = False
                except Exception as e:
                    await self.show_notification(f"Failed to save {file_info['file_path']}: {str(e)}", "error")
        
        await self.show_notification("All files saved", "success")
    
    async def action_close_tab(self) -> None:
        """Close current tab"""
        if not self.active_tab:
            return
        
        # Check if file is modified
        file_info = self.open_files.get(self.active_tab)
        if file_info and file_info.get("modified"):
            # Show save dialog
            await self.show_notification("Unsaved changes - save dialog not implemented", "warning")
            return
        
        # Remove tab
        del self.open_files[self.active_tab]
        
        # Remove from UI
        editor_tabs = self.query_one("#editor-tabs", Tabs)
        # This is a simplified version - proper tab removal needs more work
        
        # Activate another tab if available
        if self.open_files:
            await self.activate_tab(list(self.open_files.keys())[0])
        else:
            self.active_tab = None
            editor_content = self.query_one("#editor-content", Container)
            editor_content.remove_children()
    
    async def action_undo(self) -> None:
        """Undo last action"""
        await self.show_notification("Undo not implemented yet", "info")
    
    async def action_redo(self) -> None:
        """Redo last undone action"""
        await self.show_notification("Redo not implemented yet", "info")
    
    async def action_find(self) -> None:
        """Show find dialog"""
        await self.show_notification("Find not implemented yet", "info")
    
    async def action_replace(self) -> None:
        """Show replace dialog"""
        await self.show_notification("Replace not implemented yet", "info")
    
    async def action_run_debug(self) -> None:
        """Start debugging"""
        await self.show_notification("Debug mode starting...", "info")
    
    async def action_change_theme(self) -> None:
        """Change color theme"""
        themes = ["dark", "light", "monokai", "dracula", "solarized"]
        # Would show theme picker
        await self.show_notification("Theme picker not implemented yet", "info")
    
    async def action_show_help(self) -> None:
        """Show help"""
        help_content = """
# NEXUS Terminal UI Help

## Keyboard Shortcuts

### File Operations
- **Ctrl+N**: New file
- **Ctrl+O**: Open file
- **Ctrl+S**: Save file
- **Ctrl+Shift+S**: Save all files
- **Ctrl+W**: Close tab

### Navigation
- **Ctrl+P**: Command palette
- **Ctrl+Tab**: Next tab
- **Ctrl+Shift+Tab**: Previous tab
- **Ctrl+G**: Go to line

### View
- **Ctrl+B**: Toggle sidebar
- **Ctrl+`**: Toggle terminal
- **F11**: Fullscreen

### Editing
- **Ctrl+Z**: Undo
- **Ctrl+Shift+Z**: Redo
- **Ctrl+F**: Find
- **Ctrl+H**: Replace

### Debug
- **F5**: Start debugging
- **F9**: Toggle breakpoint
        """
        
        await self.open_tab("Help", help_content, file_type="markdown")
    
    def new_terminal(self) -> None:
        """Create new terminal instance"""
        # Add new terminal tab
        terminal_tabs = self.query_one("#terminal-tabs", Tabs)
        term_id = f"term-{len(terminal_tabs.children)}"
        terminal_tabs.add_tab(Tab(f"Terminal {len(terminal_tabs.children)}", id=term_id))
    
    async def on_app_blur(self) -> None:
        """Save session when app loses focus"""
        await self.save_session()


def main():
    """Run the NEXUS Terminal UI"""
    app = NEXUSTerminalUI()
    app.run()


if __name__ == "__main__":
    main()