#!/usr/bin/env python3
"""
NEXUS Editor Integration - Advanced Code Editor for Terminal UI
Provides syntax highlighting, code completion, multi-file support, and AI-powered features
"""

import os
import sys
import asyncio
import json
import re
import subprocess
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import threading
from queue import Queue
import time

# Terminal UI components
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.table import Table
from rich import box

# Syntax highlighting and parsing
try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer_for_filename
    from pygments.formatters import TerminalFormatter, Terminal256Formatter
    from pygments.styles import get_style_by_name
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

# Code analysis
import ast
import tokenize
import io

# File watching
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Web server for preview
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser
import websocket
from websocket import create_connection


class EditorMode(Enum):
    """Editor modes"""
    NORMAL = "normal"
    INSERT = "insert"
    VISUAL = "visual"
    COMMAND = "command"
    SEARCH = "search"


class FileType(Enum):
    """Supported file types"""
    PYTHON = ("python", [".py", ".pyw"], "python")
    JAVASCRIPT = ("javascript", [".js", ".mjs"], "javascript")
    TYPESCRIPT = ("typescript", [".ts", ".tsx"], "typescript")
    HTML = ("html", [".html", ".htm"], "html")
    CSS = ("css", [".css", ".scss", ".sass"], "css")
    REACT = ("react", [".jsx", ".tsx"], "javascript")
    VUE = ("vue", [".vue"], "javascript")
    MARKDOWN = ("markdown", [".md", ".markdown"], "markdown")
    JSON = ("json", [".json"], "json")
    YAML = ("yaml", [".yml", ".yaml"], "yaml")
    TEXT = ("text", [".txt"], "text")
    
    def __init__(self, name: str, extensions: List[str], lexer: str):
        self.display_name = name
        self.extensions = extensions
        self.lexer_name = lexer


@dataclass
class EditorBuffer:
    """Represents an open file in the editor"""
    file_path: Path
    content: List[str] = field(default_factory=list)
    cursor_line: int = 0
    cursor_col: int = 0
    modified: bool = False
    file_type: FileType = FileType.TEXT
    syntax_tree: Optional[Any] = None
    error_lines: Set[int] = field(default_factory=set)
    bookmarks: Set[int] = field(default_factory=set)
    undo_stack: List[List[str]] = field(default_factory=list)
    redo_stack: List[List[str]] = field(default_factory=list)


@dataclass
class CompletionItem:
    """Code completion item"""
    label: str
    kind: str  # function, variable, class, etc.
    detail: Optional[str] = None
    documentation: Optional[str] = None
    insert_text: Optional[str] = None
    score: float = 0.0


@dataclass
class DiagnosticItem:
    """Code diagnostic/error item"""
    line: int
    column: int
    severity: str  # error, warning, info
    message: str
    source: str = "nexus"


class CodeAnalyzer:
    """Analyzes code for errors, completions, and suggestions"""
    
    def __init__(self):
        self.builtin_completions = self._load_builtin_completions()
        
    def _load_builtin_completions(self) -> Dict[str, List[CompletionItem]]:
        """Load built-in completions for each language"""
        return {
            "python": [
                CompletionItem("def", "keyword", "Define a function"),
                CompletionItem("class", "keyword", "Define a class"),
                CompletionItem("import", "keyword", "Import a module"),
                CompletionItem("from", "keyword", "Import from module"),
                CompletionItem("if", "keyword", "Conditional statement"),
                CompletionItem("for", "keyword", "For loop"),
                CompletionItem("while", "keyword", "While loop"),
                CompletionItem("try", "keyword", "Try block"),
                CompletionItem("except", "keyword", "Exception handler"),
                CompletionItem("finally", "keyword", "Finally block"),
                CompletionItem("return", "keyword", "Return from function"),
                CompletionItem("yield", "keyword", "Yield value"),
                CompletionItem("async", "keyword", "Async function"),
                CompletionItem("await", "keyword", "Await async call"),
                CompletionItem("with", "keyword", "Context manager"),
                CompletionItem("lambda", "keyword", "Lambda function"),
                CompletionItem("print()", "function", "Print to stdout"),
                CompletionItem("len()", "function", "Get length"),
                CompletionItem("range()", "function", "Generate range"),
                CompletionItem("enumerate()", "function", "Enumerate iterable"),
                CompletionItem("zip()", "function", "Zip iterables"),
                CompletionItem("map()", "function", "Map function"),
                CompletionItem("filter()", "function", "Filter iterable"),
            ],
            "javascript": [
                CompletionItem("function", "keyword", "Define function"),
                CompletionItem("const", "keyword", "Constant declaration"),
                CompletionItem("let", "keyword", "Variable declaration"),
                CompletionItem("var", "keyword", "Variable declaration"),
                CompletionItem("if", "keyword", "Conditional statement"),
                CompletionItem("else", "keyword", "Else clause"),
                CompletionItem("for", "keyword", "For loop"),
                CompletionItem("while", "keyword", "While loop"),
                CompletionItem("return", "keyword", "Return from function"),
                CompletionItem("async", "keyword", "Async function"),
                CompletionItem("await", "keyword", "Await promise"),
                CompletionItem("class", "keyword", "Define class"),
                CompletionItem("extends", "keyword", "Class inheritance"),
                CompletionItem("import", "keyword", "Import module"),
                CompletionItem("export", "keyword", "Export module"),
                CompletionItem("console.log()", "function", "Log to console"),
                CompletionItem("setTimeout()", "function", "Set timeout"),
                CompletionItem("setInterval()", "function", "Set interval"),
                CompletionItem("Promise", "class", "Promise constructor"),
                CompletionItem("Array", "class", "Array constructor"),
                CompletionItem("Object", "class", "Object constructor"),
            ],
            "html": [
                CompletionItem("<div>", "tag", "Division element"),
                CompletionItem("<span>", "tag", "Inline element"),
                CompletionItem("<p>", "tag", "Paragraph"),
                CompletionItem("<h1>", "tag", "Heading 1"),
                CompletionItem("<a>", "tag", "Anchor/link"),
                CompletionItem("<img>", "tag", "Image"),
                CompletionItem("<input>", "tag", "Input field"),
                CompletionItem("<button>", "tag", "Button"),
                CompletionItem("<form>", "tag", "Form"),
                CompletionItem("<table>", "tag", "Table"),
                CompletionItem("<ul>", "tag", "Unordered list"),
                CompletionItem("<li>", "tag", "List item"),
                CompletionItem("class=", "attribute", "CSS class"),
                CompletionItem("id=", "attribute", "Element ID"),
                CompletionItem("style=", "attribute", "Inline style"),
                CompletionItem("href=", "attribute", "Link URL"),
                CompletionItem("src=", "attribute", "Source URL"),
            ],
            "css": [
                CompletionItem("color:", "property", "Text color"),
                CompletionItem("background:", "property", "Background"),
                CompletionItem("margin:", "property", "Margin"),
                CompletionItem("padding:", "property", "Padding"),
                CompletionItem("display:", "property", "Display type"),
                CompletionItem("position:", "property", "Position type"),
                CompletionItem("width:", "property", "Width"),
                CompletionItem("height:", "property", "Height"),
                CompletionItem("font-size:", "property", "Font size"),
                CompletionItem("font-family:", "property", "Font family"),
                CompletionItem("border:", "property", "Border"),
                CompletionItem("flex:", "property", "Flexbox"),
                CompletionItem("grid:", "property", "Grid layout"),
                CompletionItem("@media", "at-rule", "Media query"),
                CompletionItem("@keyframes", "at-rule", "Animation"),
                CompletionItem(":hover", "pseudo", "Hover state"),
                CompletionItem(":active", "pseudo", "Active state"),
                CompletionItem(":focus", "pseudo", "Focus state"),
            ]
        }
    
    def analyze_python(self, code: str) -> Tuple[Optional[ast.AST], List[DiagnosticItem]]:
        """Analyze Python code for syntax errors"""
        diagnostics = []
        tree = None
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            diagnostics.append(DiagnosticItem(
                line=e.lineno - 1 if e.lineno else 0,
                column=e.offset - 1 if e.offset else 0,
                severity="error",
                message=str(e.msg)
            ))
        except Exception as e:
            diagnostics.append(DiagnosticItem(
                line=0,
                column=0,
                severity="error",
                message=str(e)
            ))
        
        return tree, diagnostics
    
    def get_completions(self, buffer: EditorBuffer, line: str, col: int) -> List[CompletionItem]:
        """Get code completions for current position"""
        completions = []
        
        # Get prefix to complete
        prefix = ""
        for i in range(col - 1, -1, -1):
            if i < len(line) and line[i].isalnum() or line[i] in "_":
                prefix = line[i] + prefix
            else:
                break
        
        # Get built-in completions
        lang_completions = self.builtin_completions.get(
            buffer.file_type.display_name, []
        )
        
        # Filter by prefix
        for item in lang_completions:
            if item.label.lower().startswith(prefix.lower()):
                item.score = len(prefix) / len(item.label)
                completions.append(item)
        
        # Add context-aware completions from current file
        if buffer.file_type == FileType.PYTHON and buffer.syntax_tree:
            completions.extend(self._get_python_context_completions(
                buffer.syntax_tree, prefix
            ))
        
        # Sort by score
        completions.sort(key=lambda x: x.score, reverse=True)
        
        return completions[:20]  # Limit to top 20
    
    def _get_python_context_completions(self, tree: ast.AST, prefix: str) -> List[CompletionItem]:
        """Get context-aware Python completions"""
        completions = []
        
        # Find all defined names in the file
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith(prefix):
                    completions.append(CompletionItem(
                        node.name + "()",
                        "function",
                        f"Function defined at line {node.lineno}"
                    ))
            elif isinstance(node, ast.ClassDef):
                if node.name.startswith(prefix):
                    completions.append(CompletionItem(
                        node.name,
                        "class",
                        f"Class defined at line {node.lineno}"
                    ))
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if node.id.startswith(prefix):
                    completions.append(CompletionItem(
                        node.id,
                        "variable",
                        "Variable"
                    ))
        
        return completions


class TerminalEmulator:
    """Embedded terminal emulator"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.output_queue = Queue()
        self.input_queue = Queue()
        self.cwd = os.getcwd()
        
    def start(self):
        """Start the terminal process"""
        self.process = subprocess.Popen(
            [os.environ.get("SHELL", "/bin/bash")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=self.cwd,
            env=os.environ.copy(),
            universal_newlines=True,
            bufsize=0
        )
        
        # Start output reader thread
        threading.Thread(target=self._read_output, daemon=True).start()
        
    def _read_output(self):
        """Read output from terminal process"""
        if not self.process:
            return
            
        for line in iter(self.process.stdout.readline, ''):
            if line:
                self.output_queue.put(line.rstrip())
    
    def send_input(self, command: str):
        """Send input to terminal"""
        if self.process and self.process.stdin:
            self.process.stdin.write(command + '\n')
            self.process.stdin.flush()
    
    def get_output(self) -> List[str]:
        """Get all available output"""
        output = []
        while not self.output_queue.empty():
            output.append(self.output_queue.get())
        return output
    
    def stop(self):
        """Stop the terminal process"""
        if self.process:
            self.process.terminate()
            self.process.wait()


class PreviewServer:
    """Live preview server with hot reload"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.websocket_clients: List[websocket.WebSocket] = []
        self.file_watcher: Optional[Observer] = None
        
    def start(self, root_dir: str):
        """Start the preview server"""
        os.chdir(root_dir)
        
        # Start HTTP server
        handler = SimpleHTTPRequestHandler
        self.server = HTTPServer(('localhost', self.port), handler)
        self.server_thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True
        )
        self.server_thread.start()
        
        # Start file watcher
        self._start_file_watcher(root_dir)
        
        # Open in browser
        webbrowser.open(f'http://localhost:{self.port}')
    
    def _start_file_watcher(self, root_dir: str):
        """Start watching files for changes"""
        event_handler = FileChangeHandler(self)
        self.file_watcher = Observer()
        self.file_watcher.schedule(event_handler, root_dir, recursive=True)
        self.file_watcher.start()
    
    def notify_reload(self, file_path: str):
        """Notify clients to reload"""
        # In a real implementation, this would use WebSockets
        # to send reload messages to connected clients
        pass
    
    def stop(self):
        """Stop the preview server"""
        if self.server:
            self.server.shutdown()
        if self.file_watcher:
            self.file_watcher.stop()


class FileChangeHandler(FileSystemEventHandler):
    """Handle file changes for hot reload"""
    
    def __init__(self, preview_server: PreviewServer):
        self.preview_server = preview_server
        self.debounce_timers: Dict[str, threading.Timer] = {}
        
    def on_modified(self, event):
        if not event.is_directory:
            # Debounce rapid changes
            if event.src_path in self.debounce_timers:
                self.debounce_timers[event.src_path].cancel()
            
            timer = threading.Timer(
                0.5,
                lambda: self.preview_server.notify_reload(event.src_path)
            )
            self.debounce_timers[event.src_path] = timer
            timer.start()


class AIAssistant:
    """AI-powered coding assistant"""
    
    def __init__(self):
        self.suggestion_cache: Dict[str, List[str]] = {}
        
    async def get_inline_suggestion(self, buffer: EditorBuffer, line: str, col: int) -> Optional[str]:
        """Get AI-powered inline suggestion"""
        # In a real implementation, this would call an AI model
        # For now, return context-aware suggestions
        
        context = self._get_context(buffer, buffer.cursor_line)
        
        # Simple pattern-based suggestions
        if buffer.file_type == FileType.PYTHON:
            if line.strip().startswith("def ") and not line.strip().endswith(":"):
                return "):"
            elif line.strip().startswith("class ") and not line.strip().endswith(":"):
                return ":"
            elif line.strip() == "if ":
                return "condition:"
            elif line.strip().startswith("for ") and " in " not in line:
                return "item in items:"
        
        elif buffer.file_type in [FileType.JAVASCRIPT, FileType.TYPESCRIPT]:
            if line.strip().startswith("function ") and not line.strip().endswith("{"):
                return "() {"
            elif line.strip() == "if ":
                return "(condition) {"
            elif line.strip().startswith("for ") and "(" not in line:
                return "(let i = 0; i < length; i++) {"
        
        return None
    
    def _get_context(self, buffer: EditorBuffer, line_num: int, context_lines: int = 5) -> str:
        """Get surrounding context for AI analysis"""
        start = max(0, line_num - context_lines)
        end = min(len(buffer.content), line_num + context_lines + 1)
        return '\n'.join(buffer.content[start:end])
    
    async def suggest_refactoring(self, buffer: EditorBuffer, start_line: int, end_line: int) -> Optional[str]:
        """Suggest code refactoring"""
        code = '\n'.join(buffer.content[start_line:end_line + 1])
        
        # Simple refactoring suggestions
        suggestions = []
        
        if buffer.file_type == FileType.PYTHON:
            # Check for long functions
            if code.count('\n') > 20 and code.strip().startswith('def '):
                suggestions.append("Consider breaking this function into smaller functions")
            
            # Check for nested loops
            if code.count('for ') > 2:
                suggestions.append("Consider extracting nested loops into separate functions")
            
            # Check for repeated code
            lines = code.split('\n')
            for i in range(len(lines) - 3):
                if lines[i] == lines[i + 2] and lines[i + 1] == lines[i + 3]:
                    suggestions.append("Detected repeated code - consider extracting to a function")
                    break
        
        return '\n'.join(suggestions) if suggestions else None


class NexusEditor:
    """Main editor class integrating all components"""
    
    def __init__(self):
        self.console = Console()
        self.buffers: Dict[str, EditorBuffer] = {}
        self.active_buffer: Optional[str] = None
        self.mode = EditorMode.NORMAL
        self.layout = Layout()
        self.analyzer = CodeAnalyzer()
        self.terminal = TerminalEmulator()
        self.preview_server = PreviewServer()
        self.ai_assistant = AIAssistant()
        self.split_mode = "single"  # single, horizontal, vertical
        self.command_history: List[str] = []
        self.search_pattern: str = ""
        self.status_message: str = ""
        
        # Configure layout
        self._setup_layout()
        
    def _setup_layout(self):
        """Setup the terminal UI layout"""
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="terminal", size=10, visible=False),
            Layout(name="status", size=1)
        )
        
        # Split main area for editor panes
        self.layout["main"].split_row(
            Layout(name="editor", ratio=2),
            Layout(name="sidebar", size=30, visible=False)
        )
    
    def open_file(self, file_path: str) -> bool:
        """Open a file in the editor"""
        path = Path(file_path).resolve()
        
        if not path.exists():
            # Create new file
            path.touch()
        
        if str(path) in self.buffers:
            self.active_buffer = str(path)
            return True
        
        try:
            # Read file content
            content = path.read_text().splitlines()
            
            # Detect file type
            file_type = self._detect_file_type(path)
            
            # Create buffer
            buffer = EditorBuffer(
                file_path=path,
                content=content,
                file_type=file_type
            )
            
            # Analyze initial content
            if file_type == FileType.PYTHON:
                tree, diagnostics = self.analyzer.analyze_python('\n'.join(content))
                buffer.syntax_tree = tree
                buffer.error_lines = {d.line for d in diagnostics if d.severity == "error"}
            
            self.buffers[str(path)] = buffer
            self.active_buffer = str(path)
            
            self.status_message = f"Opened {path.name}"
            return True
            
        except Exception as e:
            self.status_message = f"Error opening file: {e}"
            return False
    
    def _detect_file_type(self, path: Path) -> FileType:
        """Detect file type from extension"""
        ext = path.suffix.lower()
        
        for file_type in FileType:
            if ext in file_type.extensions:
                return file_type
        
        return FileType.TEXT
    
    def save_file(self, buffer_key: Optional[str] = None) -> bool:
        """Save the current or specified buffer"""
        if buffer_key is None:
            buffer_key = self.active_buffer
        
        if not buffer_key or buffer_key not in self.buffers:
            return False
        
        buffer = self.buffers[buffer_key]
        
        try:
            buffer.file_path.write_text('\n'.join(buffer.content))
            buffer.modified = False
            self.status_message = f"Saved {buffer.file_path.name}"
            return True
        except Exception as e:
            self.status_message = f"Error saving: {e}"
            return False
    
    def get_editor_display(self) -> Panel:
        """Get the editor display panel"""
        if not self.active_buffer or self.active_buffer not in self.buffers:
            return Panel("No file open", title="Editor")
        
        buffer = self.buffers[self.active_buffer]
        
        # Prepare content with syntax highlighting
        lines = []
        for i, line in enumerate(buffer.content):
            line_num = i + 1
            
            # Line number
            line_str = f"{line_num:4d} "
            
            # Error indicator
            if i in buffer.error_lines:
                line_str = f"[red]{line_str}[/red]"
            elif i in buffer.bookmarks:
                line_str = f"[yellow]{line_str}[/yellow]"
            else:
                line_str = f"[dim]{line_str}[/dim]"
            
            # Content with syntax highlighting
            if PYGMENTS_AVAILABLE and buffer.file_type != FileType.TEXT:
                try:
                    lexer = get_lexer_by_name(buffer.file_type.lexer_name)
                    highlighted = highlight(line, lexer, TerminalFormatter())
                    line_str += highlighted.rstrip()
                except:
                    line_str += line
            else:
                line_str += line
            
            # Cursor
            if i == buffer.cursor_line:
                lines.append(f"> {line_str}")
            else:
                lines.append(f"  {line_str}")
        
        # Add empty lines if needed
        if not lines:
            lines = ["  1    "]
        
        content = '\n'.join(lines)
        
        # Title with mode indicator
        mode_color = {
            EditorMode.NORMAL: "green",
            EditorMode.INSERT: "blue",
            EditorMode.VISUAL: "yellow",
            EditorMode.COMMAND: "magenta",
            EditorMode.SEARCH: "cyan"
        }.get(self.mode, "white")
        
        title = f"[{mode_color}]{self.mode.value.upper()}[/{mode_color}] - {buffer.file_path.name}"
        if buffer.modified:
            title += " [red]*[/red]"
        
        return Panel(content, title=title, box=box.ROUNDED)
    
    def get_terminal_display(self) -> Panel:
        """Get the terminal display panel"""
        output = self.terminal.get_output()
        
        # Keep last N lines
        max_lines = 8
        if len(output) > max_lines:
            output = output[-max_lines:]
        
        content = '\n'.join(output)
        if not content:
            content = "Terminal ready..."
        
        return Panel(content, title="Terminal", box=box.ROUNDED)
    
    def get_status_display(self) -> Text:
        """Get the status bar display"""
        if not self.active_buffer or self.active_buffer not in self.buffers:
            return Text("No file open")
        
        buffer = self.buffers[self.active_buffer]
        
        # Build status components
        parts = []
        
        # File info
        parts.append(f"{buffer.file_path.name}")
        if buffer.modified:
            parts.append("[modified]")
        
        # Position
        parts.append(f"Ln {buffer.cursor_line + 1}, Col {buffer.cursor_col + 1}")
        
        # File type
        parts.append(buffer.file_type.display_name.upper())
        
        # Errors/warnings
        if buffer.error_lines:
            parts.append(f"[red]Errors: {len(buffer.error_lines)}[/red]")
        
        # Message
        if self.status_message:
            parts.append(f"| {self.status_message}")
        
        return Text(" ".join(parts))
    
    def handle_insert_mode_key(self, key: str):
        """Handle key press in insert mode"""
        if not self.active_buffer:
            return
        
        buffer = self.buffers[self.active_buffer]
        
        if key == "escape":
            self.mode = EditorMode.NORMAL
        elif key == "backspace":
            if buffer.cursor_col > 0:
                line = buffer.content[buffer.cursor_line]
                buffer.content[buffer.cursor_line] = (
                    line[:buffer.cursor_col - 1] + line[buffer.cursor_col:]
                )
                buffer.cursor_col -= 1
                buffer.modified = True
        elif key == "enter":
            line = buffer.content[buffer.cursor_line]
            # Split line at cursor
            buffer.content[buffer.cursor_line] = line[:buffer.cursor_col]
            buffer.content.insert(buffer.cursor_line + 1, line[buffer.cursor_col:])
            buffer.cursor_line += 1
            buffer.cursor_col = 0
            buffer.modified = True
        elif len(key) == 1:
            # Insert character
            line = buffer.content[buffer.cursor_line]
            buffer.content[buffer.cursor_line] = (
                line[:buffer.cursor_col] + key + line[buffer.cursor_col:]
            )
            buffer.cursor_col += 1
            buffer.modified = True
    
    def handle_normal_mode_key(self, key: str):
        """Handle key press in normal mode"""
        if not self.active_buffer:
            return
        
        buffer = self.buffers[self.active_buffer]
        
        # Mode changes
        if key == "i":
            self.mode = EditorMode.INSERT
        elif key == "a":
            self.mode = EditorMode.INSERT
            buffer.cursor_col += 1
        elif key == "v":
            self.mode = EditorMode.VISUAL
        elif key == ":":
            self.mode = EditorMode.COMMAND
        elif key == "/":
            self.mode = EditorMode.SEARCH
        
        # Navigation
        elif key == "h" and buffer.cursor_col > 0:
            buffer.cursor_col -= 1
        elif key == "l" and buffer.cursor_col < len(buffer.content[buffer.cursor_line]):
            buffer.cursor_col += 1
        elif key == "j" and buffer.cursor_line < len(buffer.content) - 1:
            buffer.cursor_line += 1
            # Adjust column
            line_len = len(buffer.content[buffer.cursor_line])
            if buffer.cursor_col > line_len:
                buffer.cursor_col = line_len
        elif key == "k" and buffer.cursor_line > 0:
            buffer.cursor_line -= 1
            # Adjust column
            line_len = len(buffer.content[buffer.cursor_line])
            if buffer.cursor_col > line_len:
                buffer.cursor_col = line_len
        
        # Line operations
        elif key == "dd":
            if buffer.content:
                buffer.content.pop(buffer.cursor_line)
                if buffer.cursor_line >= len(buffer.content) and buffer.cursor_line > 0:
                    buffer.cursor_line -= 1
                buffer.modified = True
        elif key == "o":
            buffer.content.insert(buffer.cursor_line + 1, "")
            buffer.cursor_line += 1
            buffer.cursor_col = 0
            self.mode = EditorMode.INSERT
            buffer.modified = True
        elif key == "O":
            buffer.content.insert(buffer.cursor_line, "")
            buffer.cursor_col = 0
            self.mode = EditorMode.INSERT
            buffer.modified = True
    
    async def run(self):
        """Run the editor main loop"""
        # Start terminal
        self.terminal.start()
        
        with Live(self.layout, refresh_per_second=10, screen=True) as live:
            while True:
                # Update display
                self.layout["header"].update(
                    Panel("NEXUS Code Editor - AI-Powered Development Environment", 
                          style="bold blue")
                )
                self.layout["editor"].update(self.get_editor_display())
                
                if self.layout["terminal"].visible:
                    self.layout["terminal"].update(self.get_terminal_display())
                
                self.layout["status"].update(self.get_status_display())
                
                # Handle input (simplified - in real implementation would use proper input handling)
                await asyncio.sleep(0.1)
                
                # Check for AI suggestions
                if self.mode == EditorMode.INSERT and self.active_buffer:
                    buffer = self.buffers[self.active_buffer]
                    line = buffer.content[buffer.cursor_line] if buffer.cursor_line < len(buffer.content) else ""
                    suggestion = await self.ai_assistant.get_inline_suggestion(
                        buffer, line, buffer.cursor_col
                    )
                    if suggestion:
                        self.status_message = f"Suggestion: {suggestion}"


def main():
    """Main entry point"""
    editor = NexusEditor()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        for file_path in sys.argv[1:]:
            editor.open_file(file_path)
    
    # Run editor
    try:
        asyncio.run(editor.run())
    except KeyboardInterrupt:
        pass
    finally:
        editor.terminal.stop()
        if editor.preview_server.server:
            editor.preview_server.stop()


if __name__ == "__main__":
    main()