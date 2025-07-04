#!/usr/bin/env python3
"""
NEXUS UI Components - Reusable components for terminal UI
Production-grade UI widgets with advanced features
"""

from typing import Optional, List, Dict, Any, Callable, Union, Tuple
from datetime import datetime
import asyncio
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Static, Label, Button, Input, TextLog, Tree, TreeNode,
    DataTable, ProgressBar, ListView, ListItem, Markdown,
    Tabs, Tab, TabbedContent, TabPane, RichLog, DirectoryTree
)
from textual.reactive import reactive, var
from textual.message import Message
from textual.widget import Widget
from textual.timer import Timer
from textual.worker import Worker, WorkerState

from rich.syntax import Syntax
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.console import Console, RenderableType
from rich.pretty import Pretty
from rich.markdown import Markdown as RichMarkdown


class NotificationLevel(Enum):
    """Notification severity levels"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


@dataclass
class Notification:
    """Notification data structure"""
    message: str
    level: NotificationLevel
    timestamp: datetime
    duration: float = 3.0
    actions: Optional[List[Dict[str, Any]]] = None


class CodeEditor(Widget):
    """Advanced code editor with LSP support"""
    
    CSS = """
    CodeEditor {
        layout: vertical;
        height: 100%;
        border: solid $primary;
    }
    
    .editor-header {
        height: 3;
        background: $surface;
        padding: 0 1;
    }
    
    .editor-content {
        height: 1fr;
        overflow: auto;
    }
    
    .editor-gutter {
        width: 5;
        background: $panel;
        color: $text-muted;
    }
    
    .editor-minimap {
        width: 10;
        background: $panel;
        opacity: 0.7;
    }
    
    .editor-statusbar {
        height: 1;
        background: $surface;
        color: $text-muted;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+z", "undo", "Undo"),
        Binding("ctrl+shift+z", "redo", "Redo"),
        Binding("ctrl+f", "find", "Find"),
        Binding("ctrl+h", "replace", "Replace"),
        Binding("ctrl+g", "goto_line", "Go to Line"),
        Binding("ctrl+/", "toggle_comment", "Toggle Comment"),
        Binding("ctrl+d", "duplicate_line", "Duplicate Line"),
        Binding("alt+up", "move_line_up", "Move Line Up"),
        Binding("alt+down", "move_line_down", "Move Line Down"),
        Binding("ctrl+space", "autocomplete", "Autocomplete"),
        Binding("f12", "go_to_definition", "Go to Definition"),
        Binding("shift+f12", "find_references", "Find References"),
    ]
    
    content = reactive("")
    language = reactive("text")
    file_path = reactive("")
    modified = reactive(False)
    cursor_position = reactive((0, 0))
    selection = reactive(None)
    
    def __init__(
        self,
        content: str = "",
        language: str = "text",
        file_path: str = "",
        read_only: bool = False,
        show_line_numbers: bool = True,
        show_minimap: bool = True,
        tab_size: int = 4,
        word_wrap: bool = False,
        theme: str = "monokai",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.content = content
        self.language = language
        self.file_path = file_path
        self.read_only = read_only
        self.show_line_numbers = show_line_numbers
        self.show_minimap = show_minimap
        self.tab_size = tab_size
        self.word_wrap = word_wrap
        self.theme = theme
        
        # Editor state
        self.lines = content.split("\n") if content else [""]
        self.undo_stack = []
        self.redo_stack = []
        self.breakpoints = set()
        self.folded_regions = set()
        
        # LSP client (placeholder)
        self.lsp_client = None
    
    def compose(self) -> ComposeResult:
        """Compose the editor layout"""
        # Header with file info and actions
        with Container(classes="editor-header"):
            yield Label(self.file_path or "Untitled", id="editor-title")
            yield Label("", id="editor-modified")
        
        # Main editor area
        with Horizontal(classes="editor-main"):
            # Line numbers gutter
            if self.show_line_numbers:
                yield Container(classes="editor-gutter", id="line-numbers")
            
            # Code content
            yield RichLog(
                wrap=self.word_wrap,
                highlight=True,
                markup=True,
                classes="editor-content",
                id="code-content"
            )
            
            # Minimap
            if self.show_minimap:
                yield Container(classes="editor-minimap", id="minimap")
        
        # Status bar
        with Container(classes="editor-statusbar"):
            yield Label(f"Ln {self.cursor_position[0] + 1}, Col {self.cursor_position[1] + 1}")
            yield Label(self.language.title())
            yield Label("UTF-8")
            yield Label("LF")
    
    def on_mount(self) -> None:
        """Initialize editor after mounting"""
        self.render_content()
        self.update_line_numbers()
    
    def render_content(self) -> None:
        """Render the code content with syntax highlighting"""
        content_widget = self.query_one("#code-content", RichLog)
        content_widget.clear()
        
        if self.content:
            syntax = Syntax(
                self.content,
                self.language,
                theme=self.theme,
                line_numbers=False,  # We handle line numbers separately
                word_wrap=self.word_wrap,
                tab_size=self.tab_size,
            )
            content_widget.write(syntax)
    
    def update_line_numbers(self) -> None:
        """Update line numbers gutter"""
        if not self.show_line_numbers:
            return
        
        gutter = self.query_one("#line-numbers", Container)
        gutter.remove_children()
        
        for i, line in enumerate(self.lines):
            line_num = i + 1
            classes = []
            
            # Check for breakpoints
            if i in self.breakpoints:
                classes.append("breakpoint")
            
            # Check if current line
            if i == self.cursor_position[0]:
                classes.append("current-line")
            
            label = Label(
                str(line_num).rjust(4),
                classes=" ".join(classes) if classes else None
            )
            gutter.mount(label)
    
    def insert_text(self, text: str) -> None:
        """Insert text at cursor position"""
        if self.read_only:
            return
        
        line, col = self.cursor_position
        current_line = self.lines[line]
        
        # Save state for undo
        self.save_undo_state()
        
        # Insert text
        new_line = current_line[:col] + text + current_line[col:]
        self.lines[line] = new_line
        
        # Update cursor position
        self.cursor_position = (line, col + len(text))
        
        # Mark as modified
        self.modified = True
        self.update_content()
    
    def delete_text(self, count: int = 1, forward: bool = True) -> None:
        """Delete text at cursor position"""
        if self.read_only:
            return
        
        line, col = self.cursor_position
        
        # Save state for undo
        self.save_undo_state()
        
        if forward:
            # Delete forward
            current_line = self.lines[line]
            if col < len(current_line):
                self.lines[line] = current_line[:col] + current_line[col + count:]
            elif line < len(self.lines) - 1:
                # Join with next line
                self.lines[line] = current_line + self.lines[line + 1]
                del self.lines[line + 1]
        else:
            # Delete backward (backspace)
            if col > 0:
                current_line = self.lines[line]
                self.lines[line] = current_line[:col - count] + current_line[col:]
                self.cursor_position = (line, col - count)
            elif line > 0:
                # Join with previous line
                prev_line = self.lines[line - 1]
                self.lines[line - 1] = prev_line + self.lines[line]
                del self.lines[line]
                self.cursor_position = (line - 1, len(prev_line))
        
        self.modified = True
        self.update_content()
    
    def new_line(self) -> None:
        """Insert a new line at cursor position"""
        if self.read_only:
            return
        
        line, col = self.cursor_position
        current_line = self.lines[line]
        
        # Save state for undo
        self.save_undo_state()
        
        # Split the current line
        self.lines[line] = current_line[:col]
        self.lines.insert(line + 1, current_line[col:])
        
        # Auto-indent
        indent = len(current_line) - len(current_line.lstrip())
        if indent > 0:
            self.lines[line + 1] = " " * indent + self.lines[line + 1]
            self.cursor_position = (line + 1, indent)
        else:
            self.cursor_position = (line + 1, 0)
        
        self.modified = True
        self.update_content()
    
    def update_content(self) -> None:
        """Update the content from lines"""
        self.content = "\n".join(self.lines)
        self.render_content()
        self.update_line_numbers()
    
    def save_undo_state(self) -> None:
        """Save current state to undo stack"""
        state = {
            "lines": self.lines.copy(),
            "cursor": self.cursor_position,
            "selection": self.selection,
        }
        self.undo_stack.append(state)
        
        # Limit undo stack size
        if len(self.undo_stack) > 100:
            self.undo_stack.pop(0)
        
        # Clear redo stack on new action
        self.redo_stack.clear()
    
    def action_undo(self) -> None:
        """Undo last action"""
        if not self.undo_stack:
            return
        
        # Save current state to redo stack
        current_state = {
            "lines": self.lines.copy(),
            "cursor": self.cursor_position,
            "selection": self.selection,
        }
        self.redo_stack.append(current_state)
        
        # Restore previous state
        state = self.undo_stack.pop()
        self.lines = state["lines"]
        self.cursor_position = state["cursor"]
        self.selection = state["selection"]
        
        self.update_content()
    
    def action_redo(self) -> None:
        """Redo last undone action"""
        if not self.redo_stack:
            return
        
        # Save current state to undo stack
        current_state = {
            "lines": self.lines.copy(),
            "cursor": self.cursor_position,
            "selection": self.selection,
        }
        self.undo_stack.append(current_state)
        
        # Restore next state
        state = self.redo_stack.pop()
        self.lines = state["lines"]
        self.cursor_position = state["cursor"]
        self.selection = state["selection"]
        
        self.update_content()
    
    def action_save(self) -> None:
        """Save the file"""
        if self.file_path:
            self.post_message(self.SaveRequested(self.file_path, self.content))
            self.modified = False
    
    def action_find(self) -> None:
        """Show find dialog"""
        self.post_message(self.FindRequested())
    
    def action_replace(self) -> None:
        """Show replace dialog"""
        self.post_message(self.ReplaceRequested())
    
    def action_goto_line(self) -> None:
        """Show go to line dialog"""
        self.post_message(self.GotoLineRequested())
    
    def action_toggle_comment(self) -> None:
        """Toggle comment for current line or selection"""
        # Language-specific comment syntax
        comment_syntax = {
            "python": "#",
            "javascript": "//",
            "typescript": "//",
            "java": "//",
            "c": "//",
            "cpp": "//",
            "rust": "//",
            "go": "//",
            "ruby": "#",
            "shell": "#",
            "yaml": "#",
            "html": "<!--",
            "css": "/*",
        }
        
        comment = comment_syntax.get(self.language, "#")
        line = self.cursor_position[0]
        
        self.save_undo_state()
        
        current_line = self.lines[line]
        trimmed = current_line.lstrip()
        
        if trimmed.startswith(comment):
            # Uncomment
            indent = len(current_line) - len(trimmed)
            self.lines[line] = current_line[:indent] + trimmed[len(comment):].lstrip()
        else:
            # Comment
            indent = len(current_line) - len(trimmed)
            self.lines[line] = current_line[:indent] + comment + " " + trimmed
        
        self.modified = True
        self.update_content()
    
    def action_autocomplete(self) -> None:
        """Trigger autocomplete"""
        self.post_message(self.AutocompleteRequested(self.cursor_position))
    
    def toggle_breakpoint(self, line: int) -> None:
        """Toggle breakpoint on a line"""
        if line in self.breakpoints:
            self.breakpoints.remove(line)
        else:
            self.breakpoints.add(line)
        
        self.update_line_numbers()
        self.post_message(self.BreakpointToggled(line))
    
    # Custom messages
    class SaveRequested(Message):
        def __init__(self, file_path: str, content: str):
            self.file_path = file_path
            self.content = content
            super().__init__()
    
    class FindRequested(Message):
        pass
    
    class ReplaceRequested(Message):
        pass
    
    class GotoLineRequested(Message):
        pass
    
    class AutocompleteRequested(Message):
        def __init__(self, position: Tuple[int, int]):
            self.position = position
            super().__init__()
    
    class BreakpointToggled(Message):
        def __init__(self, line: int):
            self.line = line
            super().__init__()


class FileExplorer(Widget):
    """Enhanced file explorer with search and filtering"""
    
    CSS = """
    FileExplorer {
        layout: vertical;
        border: solid $primary;
    }
    
    .explorer-header {
        height: 3;
        background: $surface;
        padding: 0 1;
    }
    
    .explorer-search {
        height: 3;
        padding: 0 1;
    }
    
    .explorer-tree {
        height: 1fr;
        overflow-y: auto;
    }
    
    .file-item {
        padding-left: 1;
    }
    
    .file-item.selected {
        background: $accent;
    }
    
    .file-item.modified {
        color: $warning;
    }
    """
    
    def __init__(
        self,
        root_path: str = ".",
        show_hidden: bool = False,
        file_filter: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.root_path = Path(root_path).resolve()
        self.show_hidden = show_hidden
        self.file_filter = file_filter or []
        self.expanded_dirs = set()
        self.selected_path = None
        self.file_watchers = {}
    
    def compose(self) -> ComposeResult:
        """Compose the file explorer"""
        with Container(classes="explorer-header"):
            yield Label(f"Explorer: {self.root_path.name}")
            yield Button("⟳", id="refresh-button", variant="minimal")
        
        yield Input(
            placeholder="Search files...",
            classes="explorer-search",
            id="search-input"
        )
        
        yield DirectoryTree(
            str(self.root_path),
            classes="explorer-tree",
            id="file-tree"
        )
    
    def on_mount(self) -> None:
        """Initialize file explorer"""
        self.refresh_tree()
        self.setup_file_watching()
    
    def refresh_tree(self) -> None:
        """Refresh the file tree"""
        tree = self.query_one("#file-tree", DirectoryTree)
        tree.reload()
    
    def setup_file_watching(self) -> None:
        """Set up file system watching"""
        # This would integrate with watchdog or similar
        pass
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "refresh-button":
            self.refresh_tree()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes"""
        if event.input.id == "search-input":
            self.filter_tree(event.value)
    
    def filter_tree(self, query: str) -> None:
        """Filter the tree based on search query"""
        tree = self.query_one("#file-tree", DirectoryTree)
        # Implement filtering logic
        # This would hide/show nodes based on the search query
    
    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection"""
        self.selected_path = event.path
        self.post_message(self.FileSelected(event.path))
    
    class FileSelected(Message):
        def __init__(self, path: str):
            self.path = path
            super().__init__()


class ChatInterface(Widget):
    """AI chat interface for interaction"""
    
    CSS = """
    ChatInterface {
        layout: vertical;
        border: solid $primary;
    }
    
    .chat-messages {
        height: 1fr;
        overflow-y: auto;
        padding: 1;
    }
    
    .chat-input-container {
        height: 5;
        border-top: solid $primary;
        padding: 1;
    }
    
    .message {
        margin-bottom: 1;
        padding: 1;
    }
    
    .message.user {
        background: $primary;
        align: right;
    }
    
    .message.assistant {
        background: $surface;
        align: left;
    }
    
    .message.system {
        background: $warning;
        align: center;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages = []
        self.is_processing = False
    
    def compose(self) -> ComposeResult:
        """Compose the chat interface"""
        yield ScrollableContainer(
            classes="chat-messages",
            id="message-container"
        )
        
        with Container(classes="chat-input-container"):
            yield Input(
                placeholder="Type your message...",
                id="chat-input"
            )
            yield Button("Send", id="send-button", variant="primary")
    
    def add_message(self, content: str, role: str = "user") -> None:
        """Add a message to the chat"""
        message = {
            "content": content,
            "role": role,
            "timestamp": datetime.now(),
        }
        self.messages.append(message)
        
        # Create message widget
        message_widget = Container(
            Markdown(content) if "```" in content else Label(content),
            classes=f"message {role}"
        )
        
        container = self.query_one("#message-container", ScrollableContainer)
        container.mount(message_widget)
        
        # Scroll to bottom
        container.scroll_end()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle send button press"""
        if event.button.id == "send-button":
            self.send_message()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle enter key in input"""
        if event.input.id == "chat-input":
            self.send_message()
    
    def send_message(self) -> None:
        """Send the current message"""
        if self.is_processing:
            return
        
        input_widget = self.query_one("#chat-input", Input)
        message = input_widget.value.strip()
        
        if not message:
            return
        
        # Clear input
        input_widget.value = ""
        
        # Add user message
        self.add_message(message, "user")
        
        # Set processing state
        self.is_processing = True
        
        # Post message event
        self.post_message(self.MessageSent(message))
    
    def receive_response(self, response: str) -> None:
        """Receive and display assistant response"""
        self.add_message(response, "assistant")
        self.is_processing = False
    
    class MessageSent(Message):
        def __init__(self, content: str):
            self.content = content
            super().__init__()


class ProgressTracker(Widget):
    """Progress tracking for long operations"""
    
    CSS = """
    ProgressTracker {
        layout: vertical;
        padding: 1;
        border: solid $primary;
    }
    
    .progress-item {
        margin-bottom: 1;
    }
    
    .progress-bar {
        height: 1;
    }
    
    .progress-label {
        color: $text-muted;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tasks = {}
    
    def compose(self) -> ComposeResult:
        """Compose the progress tracker"""
        yield Container(id="progress-container")
    
    def add_task(
        self,
        task_id: str,
        description: str,
        total: Optional[int] = None,
        auto_remove: bool = True
    ) -> None:
        """Add a new task to track"""
        task = {
            "description": description,
            "total": total,
            "completed": 0,
            "auto_remove": auto_remove,
            "start_time": datetime.now(),
        }
        self.tasks[task_id] = task
        
        # Create progress widget
        with Container(classes="progress-item", id=f"task-{task_id}") as item:
            item.mount(Label(description, classes="progress-label"))
            item.mount(ProgressBar(total=total or 100, id=f"progress-{task_id}"))
        
        container = self.query_one("#progress-container", Container)
        container.mount(item)
    
    def update_task(self, task_id: str, completed: int) -> None:
        """Update task progress"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task["completed"] = completed
        
        # Update progress bar
        try:
            progress_bar = self.query_one(f"#progress-{task_id}", ProgressBar)
            progress_bar.update(completed=completed)
            
            # Auto-remove if completed
            if task["auto_remove"] and task["total"] and completed >= task["total"]:
                self.remove_task(task_id)
        except:
            pass
    
    def remove_task(self, task_id: str) -> None:
        """Remove a task"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            
            try:
                item = self.query_one(f"#task-{task_id}", Container)
                item.remove()
            except:
                pass


class NotificationSystem(Widget):
    """System-wide notification management"""
    
    CSS = """
    NotificationSystem {
        layer: notification;
        dock: top;
        height: auto;
        max-height: 30%;
        overflow-y: auto;
    }
    
    .notification {
        margin: 1;
        padding: 1;
        border: solid;
        opacity: 0.95;
    }
    
    .notification.info {
        background: $primary;
        border-color: $primary-darken-1;
    }
    
    .notification.success {
        background: $success;
        border-color: $success-darken-1;
    }
    
    .notification.warning {
        background: $warning;
        border-color: $warning-darken-1;
    }
    
    .notification.error {
        background: $error;
        border-color: $error-darken-1;
    }
    
    .notification-header {
        margin-bottom: 1;
    }
    
    .notification-actions {
        margin-top: 1;
    }
    """
    
    def __init__(self, max_notifications: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.max_notifications = max_notifications
        self.notifications: List[Notification] = []
        self.notification_widgets = {}
    
    def compose(self) -> ComposeResult:
        """Compose the notification system"""
        yield Container(id="notification-container")
    
    def show_notification(
        self,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        duration: float = 3.0,
        actions: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Show a notification"""
        notification = Notification(
            message=message,
            level=level,
            timestamp=datetime.now(),
            duration=duration,
            actions=actions
        )
        
        # Generate unique ID
        notif_id = f"notif-{id(notification)}"
        
        # Add to list
        self.notifications.append(notification)
        
        # Create notification widget
        with Container(
            classes=f"notification {level.value}",
            id=notif_id
        ) as notif_widget:
            # Header with timestamp and close button
            with Horizontal(classes="notification-header"):
                notif_widget.mount(
                    Label(notification.timestamp.strftime("%H:%M:%S"))
                )
                notif_widget.mount(
                    Button("✕", id=f"close-{notif_id}", variant="minimal")
                )
            
            # Message
            notif_widget.mount(Label(message))
            
            # Actions
            if actions:
                with Horizontal(classes="notification-actions"):
                    for action in actions:
                        notif_widget.mount(
                            Button(
                                action["label"],
                                id=f"action-{notif_id}-{action['id']}",
                                variant=action.get("variant", "primary")
                            )
                        )
        
        # Add to container
        container = self.query_one("#notification-container", Container)
        container.mount(notif_widget)
        
        # Store widget reference
        self.notification_widgets[notif_id] = notif_widget
        
        # Limit notifications
        if len(self.notifications) > self.max_notifications:
            oldest = self.notifications.pop(0)
            oldest_id = f"notif-{id(oldest)}"
            if oldest_id in self.notification_widgets:
                self.notification_widgets[oldest_id].remove()
                del self.notification_widgets[oldest_id]
        
        # Auto-dismiss after duration
        if duration > 0:
            self.set_timer(duration, lambda: self.dismiss_notification(notif_id))
        
        return notif_id
    
    def dismiss_notification(self, notif_id: str) -> None:
        """Dismiss a notification"""
        if notif_id in self.notification_widgets:
            self.notification_widgets[notif_id].remove()
            del self.notification_widgets[notif_id]
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle notification button presses"""
        button_id = event.button.id
        
        if button_id.startswith("close-"):
            notif_id = button_id.replace("close-", "")
            self.dismiss_notification(notif_id)
        elif button_id.startswith("action-"):
            parts = button_id.split("-")
            if len(parts) >= 3:
                notif_id = f"notif-{parts[1]}"
                action_id = "-".join(parts[2:])
                self.post_message(self.ActionPressed(notif_id, action_id))
    
    class ActionPressed(Message):
        def __init__(self, notification_id: str, action_id: str):
            self.notification_id = notification_id
            self.action_id = action_id
            super().__init__()


class ContextMenu(Widget):
    """Context menu system for right-click actions"""
    
    CSS = """
    ContextMenu {
        layer: menu;
        position: absolute;
        background: $surface;
        border: solid $primary;
        padding: 0;
        width: auto;
        height: auto;
        display: none;
    }
    
    .menu-item {
        padding: 0 2;
        height: 3;
    }
    
    .menu-item:hover {
        background: $accent;
    }
    
    .menu-item.disabled {
        opacity: 0.5;
    }
    
    .menu-separator {
        height: 1;
        border-top: solid $primary;
        margin: 0 1;
    }
    """
    
    def __init__(self, items: List[Dict[str, Any]], **kwargs):
        super().__init__(**kwargs)
        self.items = items
    
    def compose(self) -> ComposeResult:
        """Compose the context menu"""
        for item in self.items:
            if item.get("separator"):
                yield Container(classes="menu-separator")
            else:
                classes = "menu-item"
                if item.get("disabled"):
                    classes += " disabled"
                
                yield Button(
                    item["label"],
                    id=f"menu-{item['id']}",
                    classes=classes,
                    variant="minimal"
                )
    
    def show_at(self, x: int, y: int) -> None:
        """Show menu at specific position"""
        self.styles.offset = (x, y)
        self.styles.display = "block"
    
    def hide(self) -> None:
        """Hide the menu"""
        self.styles.display = "none"
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle menu item selection"""
        if event.button.id.startswith("menu-"):
            item_id = event.button.id.replace("menu-", "")
            
            # Find the item
            item = next((i for i in self.items if i["id"] == item_id), None)
            if item and not item.get("disabled"):
                self.post_message(self.ItemSelected(item_id, item))
                self.hide()
    
    class ItemSelected(Message):
        def __init__(self, item_id: str, item: Dict[str, Any]):
            self.item_id = item_id
            self.item = item
            super().__init__()


class TabManager(Widget):
    """Advanced tab management system"""
    
    CSS = """
    TabManager {
        layout: vertical;
        height: 100%;
    }
    
    .tab-bar {
        height: 3;
        background: $surface;
        layout: horizontal;
    }
    
    .tab {
        padding: 0 2;
        margin-right: 1;
        height: 3;
    }
    
    .tab.active {
        background: $primary;
        color: $text;
    }
    
    .tab.modified::after {
        content: " •";
        color: $warning;
    }
    
    .tab-content-area {
        height: 1fr;
        overflow: hidden;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tabs = {}
        self.active_tab_id = None
        self.tab_order = []
    
    def compose(self) -> ComposeResult:
        """Compose the tab manager"""
        yield Container(classes="tab-bar", id="tab-bar")
        yield Container(classes="tab-content-area", id="tab-content")
    
    def add_tab(
        self,
        tab_id: str,
        title: str,
        content: Widget,
        closable: bool = True,
        icon: Optional[str] = None
    ) -> None:
        """Add a new tab"""
        tab_data = {
            "title": title,
            "content": content,
            "closable": closable,
            "icon": icon,
            "modified": False,
        }
        
        self.tabs[tab_id] = tab_data
        self.tab_order.append(tab_id)
        
        # Create tab button
        tab_label = f"{icon} {title}" if icon else title
        tab_button = Button(
            tab_label,
            id=f"tab-{tab_id}",
            classes="tab",
            variant="minimal"
        )
        
        tab_bar = self.query_one("#tab-bar", Container)
        tab_bar.mount(tab_button)
        
        # Add close button if closable
        if closable:
            close_button = Button(
                "✕",
                id=f"close-tab-{tab_id}",
                classes="tab-close",
                variant="minimal"
            )
            tab_bar.mount(close_button)
        
        # Activate if first tab
        if len(self.tabs) == 1:
            self.activate_tab(tab_id)
    
    def activate_tab(self, tab_id: str) -> None:
        """Activate a specific tab"""
        if tab_id not in self.tabs:
            return
        
        # Update active state
        self.active_tab_id = tab_id
        
        # Update tab buttons
        tab_bar = self.query_one("#tab-bar", Container)
        for button in tab_bar.query(Button):
            if button.id == f"tab-{tab_id}":
                button.add_class("active")
            else:
                button.remove_class("active")
        
        # Update content
        content_area = self.query_one("#tab-content", Container)
        content_area.remove_children()
        content_area.mount(self.tabs[tab_id]["content"])
        
        # Post activation event
        self.post_message(self.TabActivated(tab_id))
    
    def close_tab(self, tab_id: str) -> None:
        """Close a tab"""
        if tab_id not in self.tabs:
            return
        
        # Check if modified
        tab_data = self.tabs[tab_id]
        if tab_data["modified"]:
            # Post close request for confirmation
            self.post_message(self.TabCloseRequested(tab_id))
            return
        
        # Remove tab
        del self.tabs[tab_id]
        self.tab_order.remove(tab_id)
        
        # Remove UI elements
        tab_bar = self.query_one("#tab-bar", Container)
        try:
            tab_button = tab_bar.query_one(f"#tab-{tab_id}", Button)
            tab_button.remove()
            
            close_button = tab_bar.query_one(f"#close-tab-{tab_id}", Button)
            close_button.remove()
        except:
            pass
        
        # Activate another tab if needed
        if self.active_tab_id == tab_id and self.tab_order:
            self.activate_tab(self.tab_order[-1])
        elif not self.tab_order:
            content_area = self.query_one("#tab-content", Container)
            content_area.remove_children()
    
    def mark_modified(self, tab_id: str, modified: bool = True) -> None:
        """Mark a tab as modified"""
        if tab_id in self.tabs:
            self.tabs[tab_id]["modified"] = modified
            
            # Update UI
            try:
                tab_button = self.query_one(f"#tab-{tab_id}", Button)
                if modified:
                    tab_button.add_class("modified")
                else:
                    tab_button.remove_class("modified")
            except:
                pass
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle tab button presses"""
        button_id = event.button.id
        
        if button_id.startswith("tab-"):
            tab_id = button_id.replace("tab-", "")
            self.activate_tab(tab_id)
        elif button_id.startswith("close-tab-"):
            tab_id = button_id.replace("close-tab-", "")
            self.close_tab(tab_id)
    
    class TabActivated(Message):
        def __init__(self, tab_id: str):
            self.tab_id = tab_id
            super().__init__()
    
    class TabCloseRequested(Message):
        def __init__(self, tab_id: str):
            self.tab_id = tab_id
            super().__init__()


class ModalDialog(Container):
    """Base class for modal dialogs"""
    
    CSS = """
    ModalDialog {
        layer: dialog;
        align: center middle;
        background: $background 50%;
    }
    
    .dialog-container {
        background: $surface;
        border: solid $primary;
        padding: 2;
        width: 50%;
        height: auto;
        max-height: 80%;
    }
    
    .dialog-header {
        margin-bottom: 2;
        text-align: center;
    }
    
    .dialog-content {
        margin-bottom: 2;
    }
    
    .dialog-buttons {
        layout: horizontal;
        align: right;
    }
    
    .dialog-buttons Button {
        margin-left: 1;
    }
    """
    
    def __init__(
        self,
        title: str,
        content: Union[str, Widget],
        buttons: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.title = title
        self.content = content
        self.buttons = buttons or [
            {"label": "OK", "id": "ok", "variant": "primary"},
            {"label": "Cancel", "id": "cancel", "variant": "default"},
        ]
    
    def compose(self) -> ComposeResult:
        """Compose the dialog"""
        with Container(classes="dialog-container"):
            yield Label(self.title, classes="dialog-header")
            
            with Container(classes="dialog-content"):
                if isinstance(self.content, str):
                    yield Label(self.content)
                else:
                    yield self.content
            
            with Container(classes="dialog-buttons"):
                for button in self.buttons:
                    yield Button(
                        button["label"],
                        id=f"dialog-{button['id']}",
                        variant=button.get("variant", "default")
                    )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle dialog button presses"""
        if event.button.id.startswith("dialog-"):
            button_id = event.button.id.replace("dialog-", "")
            self.dismiss(button_id)
    
    def dismiss(self, result: Any = None) -> None:
        """Dismiss the dialog with a result"""
        self.post_message(self.Dismissed(result))
        self.remove()
    
    class Dismissed(Message):
        def __init__(self, result: Any):
            self.result = result
            super().__init__()


# Export all components
__all__ = [
    "CodeEditor",
    "FileExplorer",
    "ChatInterface",
    "ProgressTracker",
    "NotificationSystem",
    "ContextMenu",
    "TabManager",
    "ModalDialog",
    "NotificationLevel",
    "Notification",
]