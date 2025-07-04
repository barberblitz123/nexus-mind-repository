#!/usr/bin/env python3
"""
NEXUS Development Tab - Advanced IDE features in terminal
"""

import asyncio
import os
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

import aiofiles
from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import PathCompleter, WordCompleter, merge_completers
from prompt_toolkit.document import Document
from prompt_toolkit.filters import Condition, has_focus, to_filter
from prompt_toolkit.formatted_text import FormattedText, StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import (
    Container, HSplit, VSplit, Window, WindowAlign,
    ConditionalContainer, ScrollablePane, DynamicContainer,
    FloatContainer, Float, CompletionsMenu
)
from prompt_toolkit.layout.controls import FormattedTextControl, BufferControl
from prompt_toolkit.layout.dimension import Dimension, D
from prompt_toolkit.layout.processors import (
    BeforeInput, AfterInput, HighlightIncrementalSearchProcessor,
    HighlightSelectionProcessor, DisplayMultipleCursors
)
from prompt_toolkit.lexers import PygmentsLexer, DynamicLexer
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType
from prompt_toolkit.search import SearchState
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import (
    TextArea, Button, Label, Frame, Box,
    SearchToolbar, Dialog, MenuContainer, MenuItem
)
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename, guess_lexer
from pygments.styles import get_style_by_name
import watchdog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from nexus_live_preview import LivePreviewEngine
from nexus_code_intelligence import CodeIntelligence
from nexus_terminal_ui_advanced import TerminalMultiplexer


class FileType(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    HTML = "html"
    CSS = "css"
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"
    TEXT = "text"
    UNKNOWN = "unknown"


@dataclass
class EditorTab:
    """Represents an open file tab"""
    filepath: Path
    buffer: Buffer
    file_type: FileType
    modified: bool = False
    breakpoints: Set[int] = field(default_factory=set)
    last_saved: Optional[datetime] = None
    cursor_position: int = 0
    selection: Optional[Tuple[int, int]] = None


@dataclass
class Breakpoint:
    """Represents a debugging breakpoint"""
    file: Path
    line: int
    condition: Optional[str] = None
    hit_count: int = 0
    enabled: bool = True


@dataclass
class Variable:
    """Represents a debug variable"""
    name: str
    value: Any
    type_name: str
    scope: str
    expandable: bool = False
    children: List['Variable'] = field(default_factory=list)


class FileWatcher(FileSystemEventHandler):
    """Watch files for changes"""
    
    def __init__(self, dev_interface):
        self.dev_interface = dev_interface
        self.debounce_timers = {}
    
    def on_modified(self, event):
        if not event.is_directory:
            filepath = Path(event.src_path)
            # Debounce rapid changes
            if filepath in self.debounce_timers:
                self.debounce_timers[filepath].cancel()
            
            timer = threading.Timer(0.5, self._handle_file_change, args=[filepath])
            self.debounce_timers[filepath] = timer
            timer.start()
    
    def _handle_file_change(self, filepath: Path):
        """Handle file change after debounce"""
        asyncio.create_task(self.dev_interface.reload_file(filepath))


class DebuggerInterface:
    """Integrated debugger interface"""
    
    def __init__(self):
        self.breakpoints: Dict[Path, Set[Breakpoint]] = defaultdict(set)
        self.current_frame = None
        self.call_stack = []
        self.variables: Dict[str, List[Variable]] = {
            'local': [],
            'global': [],
            'builtin': []
        }
        self.is_running = False
        self.is_paused = False
    
    def add_breakpoint(self, file: Path, line: int, condition: Optional[str] = None):
        """Add a breakpoint"""
        bp = Breakpoint(file=file, line=line, condition=condition)
        self.breakpoints[file].add(bp)
    
    def remove_breakpoint(self, file: Path, line: int):
        """Remove a breakpoint"""
        self.breakpoints[file] = {
            bp for bp in self.breakpoints[file] 
            if bp.line != line
        }
    
    def toggle_breakpoint(self, file: Path, line: int):
        """Toggle a breakpoint"""
        existing = next(
            (bp for bp in self.breakpoints[file] if bp.line == line),
            None
        )
        if existing:
            self.breakpoints[file].remove(existing)
        else:
            self.add_breakpoint(file, line)
    
    async def start_debugging(self, command: str):
        """Start debugging session"""
        self.is_running = True
        # TODO: Integrate with actual debugger
        pass
    
    async def step_over(self):
        """Step over current line"""
        pass
    
    async def step_into(self):
        """Step into function"""
        pass
    
    async def step_out(self):
        """Step out of function"""
        pass
    
    async def continue_execution(self):
        """Continue execution"""
        self.is_paused = False
    
    async def pause_execution(self):
        """Pause execution"""
        self.is_paused = True
    
    async def stop_debugging(self):
        """Stop debugging session"""
        self.is_running = False
        self.is_paused = False


class DevelopmentInterface:
    """Main development interface"""
    
    def __init__(self, parent_app=None):
        self.parent_app = parent_app
        self.tabs: List[EditorTab] = []
        self.active_tab_index = 0
        self.file_tree_visible = True
        self.terminal_visible = True
        self.preview_visible = True
        self.debugger_visible = False
        
        # Components
        self.code_intelligence = CodeIntelligence()
        self.live_preview = LivePreviewEngine()
        self.terminal_mux = TerminalMultiplexer()
        self.debugger = DebuggerInterface()
        self.file_watcher = FileWatcher(self)
        self.observer = Observer()
        
        # UI elements
        self.search_toolbar = SearchToolbar()
        self.file_tree_search = Buffer()
        self.quick_open_buffer = Buffer()
        self.command_palette_buffer = Buffer()
        
        # Key bindings
        self.kb = KeyBindings()
        self._setup_key_bindings()
        
        # Styles
        self.style = Style.from_dict({
            'editor': '#ffffff bg:#1e1e1e',
            'editor.line-number': '#858585',
            'editor.current-line': 'bg:#2a2a2a',
            'editor.selection': 'bg:#264f78',
            'editor.matching-bracket': 'bg:#3a3a3a bold',
            'editor.breakpoint': 'bg:#8b0000',
            'editor.current-debug-line': 'bg:#ffff00 #000000',
            'tab': 'bg:#2d2d2d #cccccc',
            'tab.active': 'bg:#1e1e1e #ffffff bold',
            'tab.modified': 'bg:#2d2d2d #ffaa00',
            'file-tree': 'bg:#252526 #cccccc',
            'file-tree.selected': 'bg:#094771 #ffffff',
            'terminal': 'bg:#1e1e1e #cccccc',
            'preview': 'bg:#ffffff #000000',
            'toolbar': 'bg:#007acc #ffffff',
            'toolbar.button': 'bg:#005a9e #ffffff',
            'status-bar': 'bg:#007acc #ffffff',
            'debug.variable': '#4ec9b0',
            'debug.value': '#ce9178',
            'debug.type': '#569cd6',
        })
        
        # Start file watcher
        self._start_file_watcher()
    
    def _setup_key_bindings(self):
        """Setup keyboard shortcuts"""
        
        # File operations
        @self.kb.add('c-s')
        async def save_file(event):
            """Save current file"""
            await self.save_current_file()
        
        @self.kb.add('c-s', 's')
        async def save_all_files(event):
            """Save all files"""
            await self.save_all_files()
        
        @self.kb.add('c-o')
        def open_file(event):
            """Quick open file"""
            self._show_quick_open()
        
        @self.kb.add('c-w')
        def close_tab(event):
            """Close current tab"""
            self.close_current_tab()
        
        # Navigation
        @self.kb.add('c-pagedown')
        def next_tab(event):
            """Go to next tab"""
            self.next_tab()
        
        @self.kb.add('c-pageup')
        def previous_tab(event):
            """Go to previous tab"""
            self.previous_tab()
        
        @self.kb.add('c-g')
        def goto_line(event):
            """Go to line"""
            self._show_goto_line()
        
        # View toggles
        @self.kb.add('c-b')
        def toggle_file_tree(event):
            """Toggle file tree"""
            self.file_tree_visible = not self.file_tree_visible
            event.app.invalidate()
        
        @self.kb.add('c-`')
        def toggle_terminal(event):
            """Toggle terminal"""
            self.terminal_visible = not self.terminal_visible
            event.app.invalidate()
        
        @self.kb.add('c-p', 'r')
        def toggle_preview(event):
            """Toggle preview"""
            self.preview_visible = not self.preview_visible
            event.app.invalidate()
        
        # Debugging
        @self.kb.add('f9')
        def toggle_breakpoint(event):
            """Toggle breakpoint"""
            if self.current_tab:
                line = self._get_current_line()
                self.debugger.toggle_breakpoint(
                    self.current_tab.filepath,
                    line
                )
        
        @self.kb.add('f5')
        async def start_debugging(event):
            """Start/Continue debugging"""
            if not self.debugger.is_running:
                await self.debugger.start_debugging("python " + str(self.current_tab.filepath))
            else:
                await self.debugger.continue_execution()
        
        @self.kb.add('f10')
        async def step_over(event):
            """Step over"""
            await self.debugger.step_over()
        
        @self.kb.add('f11')
        async def step_into(event):
            """Step into"""
            await self.debugger.step_into()
        
        @self.kb.add('s-f11')
        async def step_out(event):
            """Step out"""
            await self.debugger.step_out()
        
        # Code actions
        @self.kb.add('c-space')
        def show_completions(event):
            """Show code completions"""
            event.current_buffer.start_completion()
        
        @self.kb.add('c-/')
        def toggle_comment(event):
            """Toggle comment"""
            self._toggle_comment()
        
        @self.kb.add('c-d')
        def duplicate_line(event):
            """Duplicate line"""
            self._duplicate_line()
        
        @self.kb.add('a-up')
        def move_line_up(event):
            """Move line up"""
            self._move_line(-1)
        
        @self.kb.add('a-down')
        def move_line_down(event):
            """Move line down"""
            self._move_line(1)
        
        # Command palette
        @self.kb.add('c-s-p')
        def show_command_palette(event):
            """Show command palette"""
            self._show_command_palette()
    
    @property
    def current_tab(self) -> Optional[EditorTab]:
        """Get current active tab"""
        if 0 <= self.active_tab_index < len(self.tabs):
            return self.tabs[self.active_tab_index]
        return None
    
    def _get_file_type(self, filepath: Path) -> FileType:
        """Determine file type from path"""
        ext = filepath.suffix.lower()
        mapping = {
            '.py': FileType.PYTHON,
            '.js': FileType.JAVASCRIPT,
            '.ts': FileType.TYPESCRIPT,
            '.html': FileType.HTML,
            '.css': FileType.CSS,
            '.md': FileType.MARKDOWN,
            '.json': FileType.JSON,
            '.yml': FileType.YAML,
            '.yaml': FileType.YAML,
        }
        return mapping.get(ext, FileType.TEXT)
    
    async def open_file(self, filepath: Path):
        """Open a file in a new tab"""
        # Check if already open
        for i, tab in enumerate(self.tabs):
            if tab.filepath == filepath:
                self.active_tab_index = i
                return
        
        # Create new tab
        try:
            async with aiofiles.open(filepath, 'r') as f:
                content = await f.read()
            
            # Create buffer with appropriate lexer
            file_type = self._get_file_type(filepath)
            lexer = get_lexer_for_filename(str(filepath), stripall=True)
            
            buffer = Buffer(
                document=Document(content),
                multiline=True,
                completer=self._create_completer(file_type),
                lexer=PygmentsLexer(lexer)
            )
            
            # Add change callback
            buffer.on_text_changed += self._on_buffer_changed
            
            tab = EditorTab(
                filepath=filepath,
                buffer=buffer,
                file_type=file_type,
                last_saved=datetime.now()
            )
            
            self.tabs.append(tab)
            self.active_tab_index = len(self.tabs) - 1
            
            # Start watching this file
            self.observer.schedule(
                self.file_watcher,
                str(filepath.parent),
                recursive=False
            )
            
            # Update preview if applicable
            if file_type in [FileType.HTML, FileType.MARKDOWN]:
                await self.live_preview.update_preview(filepath)
            
        except Exception as e:
            # Handle error
            pass
    
    def _create_completer(self, file_type: FileType):
        """Create appropriate completer for file type"""
        path_completer = PathCompleter()
        
        if file_type == FileType.PYTHON:
            # Python-specific completions
            return merge_completers([
                path_completer,
                WordCompleter([
                    'def', 'class', 'import', 'from', 'if', 'else',
                    'elif', 'for', 'while', 'try', 'except', 'finally',
                    'with', 'as', 'return', 'yield', 'lambda', 'pass',
                    'break', 'continue', 'async', 'await'
                ])
            ])
        elif file_type in [FileType.JAVASCRIPT, FileType.TYPESCRIPT]:
            # JS/TS completions
            return merge_completers([
                path_completer,
                WordCompleter([
                    'function', 'const', 'let', 'var', 'class', 'extends',
                    'import', 'export', 'from', 'if', 'else', 'for',
                    'while', 'do', 'switch', 'case', 'default', 'return',
                    'async', 'await', 'try', 'catch', 'finally'
                ])
            ])
        else:
            return path_completer
    
    def _on_buffer_changed(self, buffer):
        """Handle buffer text change"""
        # Mark tab as modified
        if self.current_tab:
            self.current_tab.modified = True
            
            # Update live preview for applicable files
            if self.current_tab.file_type in [FileType.HTML, FileType.MARKDOWN]:
                asyncio.create_task(
                    self.live_preview.update_preview_content(
                        self.current_tab.filepath,
                        buffer.text
                    )
                )
    
    async def save_current_file(self):
        """Save the current file"""
        if not self.current_tab:
            return
        
        try:
            async with aiofiles.open(self.current_tab.filepath, 'w') as f:
                await f.write(self.current_tab.buffer.text)
            
            self.current_tab.modified = False
            self.current_tab.last_saved = datetime.now()
        except Exception as e:
            # Handle error
            pass
    
    async def save_all_files(self):
        """Save all modified files"""
        for tab in self.tabs:
            if tab.modified:
                try:
                    async with aiofiles.open(tab.filepath, 'w') as f:
                        await f.write(tab.buffer.text)
                    
                    tab.modified = False
                    tab.last_saved = datetime.now()
                except Exception as e:
                    # Handle error
                    pass
    
    def close_current_tab(self):
        """Close the current tab"""
        if not self.current_tab:
            return
        
        # TODO: Check if file is modified and prompt to save
        
        self.tabs.pop(self.active_tab_index)
        if self.active_tab_index >= len(self.tabs) and self.tabs:
            self.active_tab_index = len(self.tabs) - 1
    
    def next_tab(self):
        """Switch to next tab"""
        if self.tabs:
            self.active_tab_index = (self.active_tab_index + 1) % len(self.tabs)
    
    def previous_tab(self):
        """Switch to previous tab"""
        if self.tabs:
            self.active_tab_index = (self.active_tab_index - 1) % len(self.tabs)
    
    def _get_current_line(self) -> int:
        """Get current line number in editor"""
        if not self.current_tab:
            return 0
        
        document = self.current_tab.buffer.document
        return document.cursor_position_row + 1
    
    def _toggle_comment(self):
        """Toggle comment for current line/selection"""
        if not self.current_tab:
            return
        
        # Get comment syntax for file type
        comment_map = {
            FileType.PYTHON: '#',
            FileType.JAVASCRIPT: '//',
            FileType.TYPESCRIPT: '//',
            FileType.HTML: '<!-- -->',
            FileType.CSS: '/* */',
        }
        
        comment = comment_map.get(self.current_tab.file_type, '#')
        # TODO: Implement comment toggling logic
    
    def _duplicate_line(self):
        """Duplicate current line"""
        if not self.current_tab:
            return
        
        buffer = self.current_tab.buffer
        document = buffer.document
        current_line = document.current_line
        
        # Insert duplicate line below
        buffer.insert_text('\n' + current_line)
    
    def _move_line(self, direction: int):
        """Move current line up or down"""
        if not self.current_tab:
            return
        
        # TODO: Implement line moving logic
    
    def _show_quick_open(self):
        """Show quick open dialog"""
        # TODO: Implement quick open dialog
        pass
    
    def _show_goto_line(self):
        """Show go to line dialog"""
        # TODO: Implement goto line dialog
        pass
    
    def _show_command_palette(self):
        """Show command palette"""
        # TODO: Implement command palette
        pass
    
    async def reload_file(self, filepath: Path):
        """Reload file from disk"""
        for tab in self.tabs:
            if tab.filepath == filepath and not tab.modified:
                try:
                    async with aiofiles.open(filepath, 'r') as f:
                        content = await f.read()
                    tab.buffer.set_document(Document(content))
                except Exception as e:
                    # Handle error
                    pass
    
    def _start_file_watcher(self):
        """Start file watcher"""
        self.observer.start()
    
    def _create_editor_window(self, tab: EditorTab) -> Window:
        """Create editor window for a tab"""
        # Line numbers
        line_numbers = Window(
            FormattedTextControl(
                text=self._get_line_numbers,
                focusable=False
            ),
            width=6,
            style='class:editor.line-number'
        )
        
        # Breakpoint gutter
        breakpoint_gutter = Window(
            FormattedTextControl(
                text=lambda: self._get_breakpoint_gutter(tab),
                focusable=False
            ),
            width=2,
            style='class:editor'
        )
        
        # Main editor
        editor = Window(
            BufferControl(
                buffer=tab.buffer,
                lexer=DynamicLexer(
                    lambda: get_lexer_for_filename(
                        str(tab.filepath), stripall=True
                    )
                ),
                include_default_input_processors=False,
                input_processors=[
                    HighlightSelectionProcessor(),
                    HighlightIncrementalSearchProcessor(),
                    DisplayMultipleCursors(),
                ],
                preview_search=True,
                search_buffer_control=self.search_toolbar.control
            ),
            wrap_lines=False,
            style='class:editor'
        )
        
        return VSplit([
            line_numbers,
            breakpoint_gutter,
            editor
        ])
    
    def _get_line_numbers(self) -> str:
        """Get line numbers for current editor"""
        if not self.current_tab:
            return ""
        
        document = self.current_tab.buffer.document
        current_line = document.cursor_position_row
        
        result = []
        for i, line in enumerate(document.lines):
            if i == current_line:
                result.append(f"{i + 1:>5} ")
            else:
                result.append(f"{i + 1:>5} ")
        
        return '\n'.join(result)
    
    def _get_breakpoint_gutter(self, tab: EditorTab) -> str:
        """Get breakpoint gutter display"""
        if not tab:
            return ""
        
        document = tab.buffer.document
        result = []
        
        for i in range(len(document.lines)):
            line_num = i + 1
            if line_num in tab.breakpoints:
                result.append("● ")
            else:
                result.append("  ")
        
        return '\n'.join(result)
    
    def _create_tabs_bar(self) -> Container:
        """Create tabs bar"""
        tabs = []
        
        for i, tab in enumerate(self.tabs):
            is_active = i == self.active_tab_index
            style = 'class:tab.active' if is_active else 'class:tab'
            if tab.modified:
                style = 'class:tab.modified'
            
            tab_text = f" {tab.filepath.name} "
            if tab.modified:
                tab_text += "●"
            
            tabs.append(
                Window(
                    FormattedTextControl(text=tab_text),
                    width=len(tab_text) + 2,
                    style=style,
                    dont_extend_width=True
                )
            )
        
        return VSplit(tabs, padding=0) if tabs else Window(content=FormattedTextControl())
    
    def _create_file_tree(self) -> Container:
        """Create file tree panel"""
        # TODO: Implement actual file tree
        return Frame(
            Window(
                FormattedTextControl(
                    text="File Explorer\n\n" + 
                         "📁 src/\n" +
                         "  📄 main.py\n" +
                         "  📄 utils.py\n" +
                         "📁 tests/\n" +
                         "  📄 test_main.py\n" +
                         "📄 README.md"
                )
            ),
            title="Explorer",
            style='class:file-tree'
        )
    
    def _create_terminal_panel(self) -> Container:
        """Create terminal panel"""
        return Frame(
            self.terminal_mux.create_layout(),
            title="Terminal",
            style='class:terminal'
        )
    
    def _create_preview_panel(self) -> Container:
        """Create preview panel"""
        return Frame(
            Window(
                FormattedTextControl(
                    text=lambda: self.live_preview.get_preview_content()
                )
            ),
            title="Live Preview",
            style='class:preview'
        )
    
    def _create_debug_panel(self) -> Container:
        """Create debug panel"""
        # Variables view
        variables = Window(
            FormattedTextControl(
                text=self._format_variables
            ),
            style='class:debug'
        )
        
        # Call stack view
        call_stack = Window(
            FormattedTextControl(
                text=self._format_call_stack
            ),
            style='class:debug'
        )
        
        # Breakpoints view
        breakpoints = Window(
            FormattedTextControl(
                text=self._format_breakpoints
            ),
            style='class:debug'
        )
        
        return HSplit([
            Frame(variables, title="Variables"),
            Frame(call_stack, title="Call Stack"),
            Frame(breakpoints, title="Breakpoints")
        ])
    
    def _format_variables(self) -> str:
        """Format variables for display"""
        result = []
        
        for scope, vars in self.debugger.variables.items():
            if vars:
                result.append(f"[{scope.upper()}]")
                for var in vars:
                    result.append(
                        f"  {var.name}: {var.value} ({var.type_name})"
                    )
                result.append("")
        
        return '\n'.join(result) if result else "No variables"
    
    def _format_call_stack(self) -> str:
        """Format call stack for display"""
        if not self.debugger.call_stack:
            return "No call stack"
        
        result = []
        for i, frame in enumerate(self.debugger.call_stack):
            result.append(f"{i}: {frame}")
        
        return '\n'.join(result)
    
    def _format_breakpoints(self) -> str:
        """Format breakpoints for display"""
        result = []
        
        for file, breakpoints in self.debugger.breakpoints.items():
            if breakpoints:
                result.append(f"{file.name}:")
                for bp in sorted(breakpoints, key=lambda x: x.line):
                    status = "●" if bp.enabled else "○"
                    result.append(f"  {status} Line {bp.line}")
                    if bp.condition:
                        result.append(f"    Condition: {bp.condition}")
                result.append("")
        
        return '\n'.join(result) if result else "No breakpoints"
    
    def _create_toolbar(self) -> Container:
        """Create toolbar with quick actions"""
        buttons = VSplit([
            Button("Run", handler=lambda: asyncio.create_task(self._run_file())),
            Button("Debug", handler=lambda: asyncio.create_task(self.debugger.start_debugging(""))),
            Button("Stop", handler=lambda: asyncio.create_task(self.debugger.stop_debugging())),
            Button("Save", handler=lambda: asyncio.create_task(self.save_current_file())),
            Button("Save All", handler=lambda: asyncio.create_task(self.save_all_files())),
            Button("Find", handler=lambda: self.search_toolbar.open_search()),
            Button("Replace", handler=lambda: self._show_replace()),
            Button("Format", handler=lambda: asyncio.create_task(self._format_code())),
        ], padding=1, style='class:toolbar')
        
        return Window(
            content=FormattedTextControl(),
            height=3,
            style='class:toolbar'
        )
    
    async def _run_file(self):
        """Run current file"""
        if not self.current_tab:
            return
        
        # Save file first
        await self.save_current_file()
        
        # Run based on file type
        if self.current_tab.file_type == FileType.PYTHON:
            cmd = f"python {self.current_tab.filepath}"
        elif self.current_tab.file_type == FileType.JAVASCRIPT:
            cmd = f"node {self.current_tab.filepath}"
        else:
            return
        
        # Run in terminal
        await self.terminal_mux.run_command(cmd)
    
    def _show_replace(self):
        """Show find and replace dialog"""
        # TODO: Implement find and replace
        pass
    
    async def _format_code(self):
        """Format current file"""
        if not self.current_tab:
            return
        
        # Format based on file type
        if self.current_tab.file_type == FileType.PYTHON:
            # Use black or autopep8
            pass
        elif self.current_tab.file_type in [FileType.JAVASCRIPT, FileType.TYPESCRIPT]:
            # Use prettier
            pass
        # TODO: Implement formatting
    
    def create_layout(self) -> Container:
        """Create the development tab layout"""
        # Main editor area
        if self.current_tab:
            editor_area = DynamicContainer(
                lambda: self._create_editor_window(self.current_tab)
            )
        else:
            editor_area = Window(
                FormattedTextControl(text="No files open\n\nPress Ctrl+O to open a file")
            )
        
        # Left panel (file tree)
        left_panel = ConditionalContainer(
            self._create_file_tree(),
            filter=Condition(lambda: self.file_tree_visible)
        )
        
        # Right panel (preview/debug)
        right_panel = ConditionalContainer(
            DynamicContainer(
                lambda: self._create_preview_panel() if self.preview_visible
                       else self._create_debug_panel()
            ),
            filter=Condition(lambda: self.preview_visible or self.debugger_visible)
        )
        
        # Bottom panel (terminal)
        bottom_panel = ConditionalContainer(
            self._create_terminal_panel(),
            filter=Condition(lambda: self.terminal_visible)
        )
        
        # Main layout
        main_area = HSplit([
            # Tabs bar
            self._create_tabs_bar(),
            # Editor and side panels
            VSplit([
                left_panel,
                HSplit([
                    # Toolbar
                    self._create_toolbar(),
                    # Editor
                    editor_area,
                    # Search toolbar
                    self.search_toolbar
                ]),
                right_panel
            ]),
            # Terminal
            bottom_panel
        ])
        
        return FloatContainer(
            content=main_area,
            floats=[
                # Quick open dialog
                Float(
                    ConditionalContainer(
                        Dialog(
                            title="Quick Open",
                            body=Window(
                                BufferControl(buffer=self.quick_open_buffer)
                            )
                        ),
                        filter=has_focus(self.quick_open_buffer)
                    )
                ),
                # Command palette
                Float(
                    ConditionalContainer(
                        Dialog(
                            title="Command Palette",
                            body=Window(
                                BufferControl(buffer=self.command_palette_buffer)
                            )
                        ),
                        filter=has_focus(self.command_palette_buffer)
                    )
                )
            ]
        )


def create_dev_tab(parent_app=None) -> Container:
    """Factory function to create development tab"""
    dev = DevelopmentInterface(parent_app)
    return dev.create_layout()