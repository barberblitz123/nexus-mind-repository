#!/usr/bin/env python3
"""
NEXUS UI State Manager - Redux-like state management for terminal UI
Provides centralized state management with undo/redo support
"""

from typing import Any, Dict, List, Optional, Callable, Union, Type
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
import json
import pickle
import asyncio
from collections import deque
from copy import deepcopy
import threading
from functools import wraps


class ActionType(Enum):
    """Standard action types for UI state changes"""
    # File actions
    FILE_OPEN = auto()
    FILE_CLOSE = auto()
    FILE_SAVE = auto()
    FILE_MODIFY = auto()
    FILE_CREATE = auto()
    FILE_DELETE = auto()
    FILE_RENAME = auto()
    
    # Editor actions
    EDITOR_CURSOR_MOVE = auto()
    EDITOR_TEXT_INSERT = auto()
    EDITOR_TEXT_DELETE = auto()
    EDITOR_SELECTION_CHANGE = auto()
    EDITOR_BREAKPOINT_TOGGLE = auto()
    EDITOR_FOLD_TOGGLE = auto()
    
    # UI actions
    UI_TAB_ACTIVATE = auto()
    UI_TAB_CLOSE = auto()
    UI_TAB_REORDER = auto()
    UI_SIDEBAR_TOGGLE = auto()
    UI_TERMINAL_TOGGLE = auto()
    UI_THEME_CHANGE = auto()
    UI_LAYOUT_CHANGE = auto()
    UI_WINDOW_RESIZE = auto()
    
    # Workspace actions
    WORKSPACE_CHANGE = auto()
    WORKSPACE_SETTINGS_UPDATE = auto()
    WORKSPACE_SESSION_SAVE = auto()
    WORKSPACE_SESSION_RESTORE = auto()
    
    # Search actions
    SEARCH_START = auto()
    SEARCH_UPDATE = auto()
    SEARCH_RESULT_SELECT = auto()
    SEARCH_CLEAR = auto()
    
    # Debug actions
    DEBUG_START = auto()
    DEBUG_STOP = auto()
    DEBUG_PAUSE = auto()
    DEBUG_STEP = auto()
    DEBUG_BREAKPOINT_ADD = auto()
    DEBUG_BREAKPOINT_REMOVE = auto()
    
    # Terminal actions
    TERMINAL_CREATE = auto()
    TERMINAL_CLOSE = auto()
    TERMINAL_OUTPUT = auto()
    TERMINAL_INPUT = auto()
    
    # Custom actions
    CUSTOM = auto()


@dataclass
class Action:
    """Represents a state change action"""
    type: ActionType
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    meta: Optional[Dict[str, Any]] = None


@dataclass
class EditorState:
    """State for a single editor instance"""
    file_path: Optional[str] = None
    content: str = ""
    language: str = "text"
    cursor_position: tuple[int, int] = (0, 0)
    selection: Optional[tuple[tuple[int, int], tuple[int, int]]] = None
    modified: bool = False
    breakpoints: List[int] = field(default_factory=list)
    folded_regions: List[tuple[int, int]] = field(default_factory=list)
    scroll_position: tuple[int, int] = (0, 0)
    undo_stack: List[Dict[str, Any]] = field(default_factory=list)
    redo_stack: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TabState:
    """State for a single tab"""
    id: str
    title: str
    type: str  # "editor", "preview", "terminal", etc.
    icon: Optional[str] = None
    closable: bool = True
    pinned: bool = False
    active: bool = False
    editor_state: Optional[EditorState] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TerminalState:
    """State for a terminal instance"""
    id: str
    title: str
    shell: str
    cwd: str
    output_history: List[str] = field(default_factory=list)
    command_history: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    active: bool = False


@dataclass
class SearchState:
    """State for search operations"""
    query: str = ""
    results: List[Dict[str, Any]] = field(default_factory=list)
    active_result_index: int = -1
    search_type: str = "text"  # "text", "regex", "files"
    case_sensitive: bool = False
    whole_word: bool = False
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)


@dataclass
class DebugState:
    """State for debugging session"""
    active: bool = False
    paused: bool = False
    current_file: Optional[str] = None
    current_line: Optional[int] = None
    breakpoints: Dict[str, List[int]] = field(default_factory=dict)
    call_stack: List[Dict[str, Any]] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    watch_expressions: List[str] = field(default_factory=list)


@dataclass
class UIState:
    """Complete UI state"""
    # Layout
    show_sidebar_left: bool = True
    show_sidebar_right: bool = True
    show_terminal: bool = True
    sidebar_width_left: int = 300
    sidebar_width_right: int = 300
    terminal_height: int = 200
    
    # Theme
    theme: str = "dark"
    font_size: int = 14
    font_family: str = "monospace"
    
    # Tabs
    tabs: List[TabState] = field(default_factory=list)
    active_tab_id: Optional[str] = None
    tab_order: List[str] = field(default_factory=list)
    
    # File Explorer
    expanded_directories: List[str] = field(default_factory=list)
    selected_files: List[str] = field(default_factory=list)
    
    # Terminals
    terminals: List[TerminalState] = field(default_factory=list)
    active_terminal_id: Optional[str] = None
    
    # Search
    search_state: SearchState = field(default_factory=SearchState)
    
    # Debug
    debug_state: DebugState = field(default_factory=DebugState)
    
    # Workspace
    workspace_path: Optional[str] = None
    recent_files: List[str] = field(default_factory=list)
    recent_projects: List[str] = field(default_factory=list)
    
    # Settings
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"


class StateManager:
    """
    Redux-like state manager for NEXUS UI
    Provides centralized state management with time-travel debugging
    """
    
    def __init__(
        self,
        initial_state: Optional[UIState] = None,
        persist_path: Optional[Path] = None,
        max_history: int = 100
    ):
        self.state = initial_state or UIState()
        self.persist_path = persist_path
        self.max_history = max_history
        
        # History for undo/redo
        self.past_states: deque = deque(maxlen=max_history)
        self.future_states: deque = deque(maxlen=max_history)
        
        # Middleware and subscribers
        self.middleware: List[Callable] = []
        self.subscribers: List[Callable] = []
        self.action_handlers: Dict[ActionType, Callable] = {}
        
        # Async support
        self.event_loop = None
        self._lock = threading.RLock()
        
        # Register default action handlers
        self._register_default_handlers()
        
        # Load persisted state if available
        if persist_path and persist_path.exists():
            self.load_state()
    
    def _register_default_handlers(self):
        """Register default action handlers"""
        # File actions
        self.register_handler(ActionType.FILE_OPEN, self._handle_file_open)
        self.register_handler(ActionType.FILE_CLOSE, self._handle_file_close)
        self.register_handler(ActionType.FILE_SAVE, self._handle_file_save)
        self.register_handler(ActionType.FILE_MODIFY, self._handle_file_modify)
        
        # Editor actions
        self.register_handler(ActionType.EDITOR_CURSOR_MOVE, self._handle_cursor_move)
        self.register_handler(ActionType.EDITOR_TEXT_INSERT, self._handle_text_insert)
        self.register_handler(ActionType.EDITOR_TEXT_DELETE, self._handle_text_delete)
        
        # UI actions
        self.register_handler(ActionType.UI_TAB_ACTIVATE, self._handle_tab_activate)
        self.register_handler(ActionType.UI_TAB_CLOSE, self._handle_tab_close)
        self.register_handler(ActionType.UI_SIDEBAR_TOGGLE, self._handle_sidebar_toggle)
        self.register_handler(ActionType.UI_TERMINAL_TOGGLE, self._handle_terminal_toggle)
        self.register_handler(ActionType.UI_THEME_CHANGE, self._handle_theme_change)
    
    def dispatch(self, action: Action) -> None:
        """
        Dispatch an action to update state
        Goes through middleware before reaching reducers
        """
        with self._lock:
            # Save current state for undo
            self.past_states.append(deepcopy(self.state))
            self.future_states.clear()  # Clear redo stack on new action
            
            # Apply middleware
            final_action = action
            for middleware in self.middleware:
                final_action = middleware(final_action, self.state)
                if final_action is None:
                    return  # Action was blocked
            
            # Handle action
            if final_action.type in self.action_handlers:
                handler = self.action_handlers[final_action.type]
                self.state = handler(self.state, final_action)
            else:
                # Default handler for custom actions
                self._handle_custom_action(self.state, final_action)
            
            # Update timestamp
            self.state.last_updated = datetime.now()
            
            # Notify subscribers
            self._notify_subscribers(final_action)
            
            # Persist state if configured
            if self.persist_path:
                self.save_state()
    
    def dispatch_async(self, action: Action) -> asyncio.Future:
        """Dispatch action asynchronously"""
        if not self.event_loop:
            self.event_loop = asyncio.get_event_loop()
        
        future = asyncio.Future()
        
        def _dispatch():
            try:
                self.dispatch(action)
                future.set_result(self.state)
            except Exception as e:
                future.set_exception(e)
        
        self.event_loop.call_soon_threadsafe(_dispatch)
        return future
    
    def get_state(self) -> UIState:
        """Get current state (immutable copy)"""
        with self._lock:
            return deepcopy(self.state)
    
    def subscribe(self, callback: Callable[[UIState, Action], None]) -> Callable:
        """
        Subscribe to state changes
        Returns unsubscribe function
        """
        self.subscribers.append(callback)
        
        def unsubscribe():
            if callback in self.subscribers:
                self.subscribers.remove(callback)
        
        return unsubscribe
    
    def add_middleware(self, middleware: Callable[[Action, UIState], Action]) -> None:
        """Add middleware to process actions before they reach reducers"""
        self.middleware.append(middleware)
    
    def register_handler(self, action_type: ActionType, handler: Callable[[UIState, Action], UIState]) -> None:
        """Register a handler for a specific action type"""
        self.action_handlers[action_type] = handler
    
    def undo(self) -> bool:
        """Undo last action"""
        with self._lock:
            if not self.past_states:
                return False
            
            # Save current state to future
            self.future_states.append(deepcopy(self.state))
            
            # Restore previous state
            self.state = self.past_states.pop()
            
            # Notify subscribers
            undo_action = Action(
                type=ActionType.CUSTOM,
                payload={"action": "undo"}
            )
            self._notify_subscribers(undo_action)
            
            return True
    
    def redo(self) -> bool:
        """Redo last undone action"""
        with self._lock:
            if not self.future_states:
                return False
            
            # Save current state to past
            self.past_states.append(deepcopy(self.state))
            
            # Restore future state
            self.state = self.future_states.pop()
            
            # Notify subscribers
            redo_action = Action(
                type=ActionType.CUSTOM,
                payload={"action": "redo"}
            )
            self._notify_subscribers(redo_action)
            
            return True
    
    def save_state(self, path: Optional[Path] = None) -> None:
        """Save state to disk"""
        save_path = path or self.persist_path
        if not save_path:
            return
        
        with self._lock:
            state_dict = asdict(self.state)
            
            # Convert datetime objects to ISO format
            def convert_dates(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: convert_dates(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_dates(item) for item in obj]
                return obj
            
            state_dict = convert_dates(state_dict)
            
            # Save as JSON
            save_path.write_text(json.dumps(state_dict, indent=2))
    
    def load_state(self, path: Optional[Path] = None) -> None:
        """Load state from disk"""
        load_path = path or self.persist_path
        if not load_path or not load_path.exists():
            return
        
        with self._lock:
            try:
                state_dict = json.loads(load_path.read_text())
                
                # Convert ISO dates back to datetime
                def parse_dates(obj):
                    if isinstance(obj, str):
                        try:
                            return datetime.fromisoformat(obj)
                        except:
                            return obj
                    elif isinstance(obj, dict):
                        return {k: parse_dates(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [parse_dates(item) for item in obj]
                    return obj
                
                state_dict = parse_dates(state_dict)
                
                # Create new state from dict
                self.state = self._dict_to_state(state_dict)
                
                # Clear history
                self.past_states.clear()
                self.future_states.clear()
                
            except Exception as e:
                print(f"Failed to load state: {e}")
    
    def _dict_to_state(self, data: Dict[str, Any]) -> UIState:
        """Convert dictionary to UIState object"""
        # Convert nested dataclasses
        if "tabs" in data:
            data["tabs"] = [
                TabState(**tab) if isinstance(tab, dict) else tab
                for tab in data["tabs"]
            ]
        
        if "terminals" in data:
            data["terminals"] = [
                TerminalState(**term) if isinstance(term, dict) else term
                for term in data["terminals"]
            ]
        
        if "search_state" in data and isinstance(data["search_state"], dict):
            data["search_state"] = SearchState(**data["search_state"])
        
        if "debug_state" in data and isinstance(data["debug_state"], dict):
            data["debug_state"] = DebugState(**data["debug_state"])
        
        return UIState(**data)
    
    def _notify_subscribers(self, action: Action) -> None:
        """Notify all subscribers of state change"""
        for subscriber in self.subscribers:
            try:
                subscriber(self.state, action)
            except Exception as e:
                print(f"Subscriber error: {e}")
    
    # Default action handlers
    def _handle_file_open(self, state: UIState, action: Action) -> UIState:
        """Handle file open action"""
        file_path = action.payload.get("file_path")
        content = action.payload.get("content", "")
        language = action.payload.get("language", "text")
        
        # Create new tab
        tab_id = f"editor-{len(state.tabs)}"
        editor_state = EditorState(
            file_path=file_path,
            content=content,
            language=language
        )
        
        tab = TabState(
            id=tab_id,
            title=Path(file_path).name if file_path else "Untitled",
            type="editor",
            editor_state=editor_state
        )
        
        state.tabs.append(tab)
        state.tab_order.append(tab_id)
        state.active_tab_id = tab_id
        
        # Add to recent files
        if file_path and file_path not in state.recent_files:
            state.recent_files.insert(0, file_path)
            state.recent_files = state.recent_files[:20]  # Keep last 20
        
        return state
    
    def _handle_file_close(self, state: UIState, action: Action) -> UIState:
        """Handle file close action"""
        tab_id = action.payload.get("tab_id")
        
        # Remove tab
        state.tabs = [tab for tab in state.tabs if tab.id != tab_id]
        if tab_id in state.tab_order:
            state.tab_order.remove(tab_id)
        
        # Activate another tab if needed
        if state.active_tab_id == tab_id:
            if state.tab_order:
                state.active_tab_id = state.tab_order[-1]
            else:
                state.active_tab_id = None
        
        return state
    
    def _handle_file_save(self, state: UIState, action: Action) -> UIState:
        """Handle file save action"""
        tab_id = action.payload.get("tab_id")
        
        # Find tab and mark as not modified
        for tab in state.tabs:
            if tab.id == tab_id and tab.editor_state:
                tab.editor_state.modified = False
                break
        
        return state
    
    def _handle_file_modify(self, state: UIState, action: Action) -> UIState:
        """Handle file modification"""
        tab_id = action.payload.get("tab_id")
        content = action.payload.get("content")
        
        # Find tab and update content
        for tab in state.tabs:
            if tab.id == tab_id and tab.editor_state:
                tab.editor_state.content = content
                tab.editor_state.modified = True
                break
        
        return state
    
    def _handle_cursor_move(self, state: UIState, action: Action) -> UIState:
        """Handle cursor movement"""
        tab_id = action.payload.get("tab_id")
        position = action.payload.get("position")
        
        # Find tab and update cursor position
        for tab in state.tabs:
            if tab.id == tab_id and tab.editor_state:
                tab.editor_state.cursor_position = position
                break
        
        return state
    
    def _handle_text_insert(self, state: UIState, action: Action) -> UIState:
        """Handle text insertion"""
        tab_id = action.payload.get("tab_id")
        text = action.payload.get("text")
        position = action.payload.get("position")
        
        # Find tab and insert text
        for tab in state.tabs:
            if tab.id == tab_id and tab.editor_state:
                # Simple text insertion (real implementation would be more complex)
                content = tab.editor_state.content
                lines = content.split("\n")
                line, col = position
                
                if 0 <= line < len(lines):
                    current_line = lines[line]
                    lines[line] = current_line[:col] + text + current_line[col:]
                    tab.editor_state.content = "\n".join(lines)
                    tab.editor_state.modified = True
                    tab.editor_state.cursor_position = (line, col + len(text))
                
                break
        
        return state
    
    def _handle_text_delete(self, state: UIState, action: Action) -> UIState:
        """Handle text deletion"""
        tab_id = action.payload.get("tab_id")
        start = action.payload.get("start")
        end = action.payload.get("end")
        
        # Find tab and delete text
        for tab in state.tabs:
            if tab.id == tab_id and tab.editor_state:
                # Simple deletion (real implementation would be more complex)
                content = tab.editor_state.content
                lines = content.split("\n")
                
                # Delete within single line for simplicity
                if start[0] == end[0]:
                    line_idx = start[0]
                    if 0 <= line_idx < len(lines):
                        line = lines[line_idx]
                        lines[line_idx] = line[:start[1]] + line[end[1]:]
                        tab.editor_state.content = "\n".join(lines)
                        tab.editor_state.modified = True
                        tab.editor_state.cursor_position = start
                
                break
        
        return state
    
    def _handle_tab_activate(self, state: UIState, action: Action) -> UIState:
        """Handle tab activation"""
        tab_id = action.payload.get("tab_id")
        
        # Update active tab
        state.active_tab_id = tab_id
        
        # Update tab active states
        for tab in state.tabs:
            tab.active = (tab.id == tab_id)
        
        return state
    
    def _handle_tab_close(self, state: UIState, action: Action) -> UIState:
        """Handle tab close"""
        return self._handle_file_close(state, action)
    
    def _handle_sidebar_toggle(self, state: UIState, action: Action) -> UIState:
        """Handle sidebar toggle"""
        side = action.payload.get("side", "left")
        
        if side == "left":
            state.show_sidebar_left = not state.show_sidebar_left
        else:
            state.show_sidebar_right = not state.show_sidebar_right
        
        return state
    
    def _handle_terminal_toggle(self, state: UIState, action: Action) -> UIState:
        """Handle terminal toggle"""
        state.show_terminal = not state.show_terminal
        return state
    
    def _handle_theme_change(self, state: UIState, action: Action) -> UIState:
        """Handle theme change"""
        theme = action.payload.get("theme")
        if theme:
            state.theme = theme
        
        return state
    
    def _handle_custom_action(self, state: UIState, action: Action) -> UIState:
        """Handle custom actions"""
        # Custom actions can modify state directly through payload
        custom_handler = action.payload.get("handler")
        if callable(custom_handler):
            return custom_handler(state, action)
        
        return state


# Decorator for connecting components to state
def connect(
    map_state_to_props: Optional[Callable[[UIState], Dict[str, Any]]] = None,
    map_dispatch_to_props: Optional[Callable[[Callable], Dict[str, Callable]]] = None
):
    """
    Decorator to connect a widget to the state manager
    Similar to React Redux connect()
    """
    def decorator(widget_class):
        original_init = widget_class.__init__
        
        @wraps(original_init)
        def new_init(self, *args, state_manager: StateManager = None, **kwargs):
            # Store state manager reference
            self._state_manager = state_manager
            
            # Map state to props if provided
            if map_state_to_props and state_manager:
                state_props = map_state_to_props(state_manager.get_state())
                kwargs.update(state_props)
            
            # Map dispatch to props if provided
            if map_dispatch_to_props and state_manager:
                dispatch_props = map_dispatch_to_props(state_manager.dispatch)
                for key, value in dispatch_props.items():
                    setattr(self, key, value)
            
            # Subscribe to state changes
            if state_manager:
                def on_state_change(state: UIState, action: Action):
                    if map_state_to_props:
                        new_props = map_state_to_props(state)
                        for key, value in new_props.items():
                            if hasattr(self, key):
                                setattr(self, key, value)
                
                self._unsubscribe = state_manager.subscribe(on_state_change)
            
            # Call original init
            original_init(self, *args, **kwargs)
        
        widget_class.__init__ = new_init
        
        # Add cleanup method
        if hasattr(widget_class, "on_unmount"):
            original_unmount = widget_class.on_unmount
            
            def new_unmount(self):
                if hasattr(self, "_unsubscribe"):
                    self._unsubscribe()
                original_unmount()
            
            widget_class.on_unmount = new_unmount
        
        return widget_class
    
    return decorator


# Middleware examples
def logger_middleware(action: Action, state: UIState) -> Action:
    """Log all actions"""
    print(f"[{action.timestamp}] {action.type.name}: {action.payload}")
    return action


def validation_middleware(action: Action, state: UIState) -> Action:
    """Validate actions before they're processed"""
    # Example: Prevent closing unsaved files
    if action.type == ActionType.FILE_CLOSE:
        tab_id = action.payload.get("tab_id")
        for tab in state.tabs:
            if tab.id == tab_id and tab.editor_state and tab.editor_state.modified:
                # Block the action or modify it
                print(f"Warning: Attempting to close modified file in tab {tab_id}")
                # Could return None to block, or modify the action
    
    return action


# Export all components
__all__ = [
    "StateManager",
    "UIState",
    "EditorState",
    "TabState",
    "TerminalState",
    "SearchState",
    "DebugState",
    "Action",
    "ActionType",
    "connect",
    "logger_middleware",
    "validation_middleware",
]