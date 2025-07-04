#!/usr/bin/env python3
"""
NEXUS 2.0 Desktop Manager
Manages chat interface and preview panes for code/output
"""

from textual.app import ComposeResult
from textual.widgets import Static, Input, RichLog, Label, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.binding import Binding
from textual.reactive import reactive
from textual.message import Message
from rich.panel import Panel
from rich.syntax import Syntax
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from datetime import datetime
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
from enum import Enum
import asyncio
import json

class PreviewType(Enum):
    """Types of content that can be previewed"""
    CODE = "code"
    OUTPUT = "output"
    MARKDOWN = "markdown"
    JSON = "json"
    ERROR = "error"
    IMAGE = "image"
    DIFF = "diff"

@dataclass
class ChatMessage:
    """Represents a chat message"""
    sender: str
    content: str
    timestamp: datetime
    message_type: Literal["user", "agent", "system"]
    metadata: Optional[Dict] = None

@dataclass
class PreviewContent:
    """Content for a preview pane"""
    title: str
    content: str
    preview_type: PreviewType
    language: Optional[str] = None
    line_numbers: bool = True
    metadata: Optional[Dict] = None

class ChatInterface(Container):
    """Chat interface component"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages: List[ChatMessage] = []
        self.message_handlers = []
        
    def compose(self) -> ComposeResult:
        """Compose the chat UI"""
        with Vertical():
            yield Label("💬 NEXUS Chat", id="chat-header")
            yield RichLog(id="chat-messages", wrap=True, highlight=True, markup=True)
            yield Input(placeholder="Type your message here...", id="chat-input")
            
    def add_message(self, message: ChatMessage):
        """Add a message to the chat"""
        self.messages.append(message)
        
        # Format the message
        time_str = message.timestamp.strftime("%H:%M:%S")
        sender_style = {
            "user": "bold cyan",
            "agent": "bold green",
            "system": "bold yellow"
        }.get(message.message_type, "white")
        
        # Update the RichLog
        log = self.query_one("#chat-messages", RichLog)
        log.write(f"[{sender_style}][{time_str}] {message.sender}:[/{sender_style}] {message.content}")
        
        # Notify handlers
        for handler in self.message_handlers:
            handler(message)
            
    def add_user_message(self, content: str):
        """Add a user message"""
        message = ChatMessage(
            sender="User",
            content=content,
            timestamp=datetime.now(),
            message_type="user"
        )
        self.add_message(message)
        
    def add_agent_message(self, agent_name: str, content: str, metadata: Optional[Dict] = None):
        """Add an agent message"""
        message = ChatMessage(
            sender=agent_name,
            content=content,
            timestamp=datetime.now(),
            message_type="agent",
            metadata=metadata
        )
        self.add_message(message)
        
    def add_system_message(self, content: str):
        """Add a system message"""
        message = ChatMessage(
            sender="System",
            content=content,
            timestamp=datetime.now(),
            message_type="system"
        )
        self.add_message(message)
        
    def clear_chat(self):
        """Clear all messages"""
        self.messages.clear()
        log = self.query_one("#chat-messages", RichLog)
        log.clear()
        
    def export_chat_history(self) -> List[Dict]:
        """Export chat history as JSON-serializable list"""
        return [
            {
                "sender": msg.sender,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "type": msg.message_type,
                "metadata": msg.metadata
            }
            for msg in self.messages
        ]

class PreviewPane(Container):
    """Individual preview pane for displaying content"""
    
    def __init__(self, pane_id: str, title: str = "Preview", **kwargs):
        super().__init__(**kwargs)
        self.pane_id = pane_id
        self.title = title
        self.current_content: Optional[PreviewContent] = None
        
    def compose(self) -> ComposeResult:
        """Compose the preview pane UI"""
        with Vertical():
            yield Label(f"👁️ {self.title}", id=f"preview-header-{self.pane_id}")
            yield ScrollableContainer(id=f"preview-content-{self.pane_id}")
            
    def show_content(self, content: PreviewContent):
        """Display content in the preview pane"""
        self.current_content = content
        container = self.query_one(f"#preview-content-{self.pane_id}", ScrollableContainer)
        
        # Clear existing content
        container.remove_children()
        
        # Update title
        header = self.query_one(f"#preview-header-{self.pane_id}", Label)
        header.update(f"👁️ {content.title}")
        
        # Render based on preview type
        if content.preview_type == PreviewType.CODE:
            syntax = Syntax(
                content.content,
                content.language or "python",
                theme="monokai",
                line_numbers=content.line_numbers
            )
            container.mount(Static(syntax))
            
        elif content.preview_type == PreviewType.MARKDOWN:
            md = Markdown(content.content)
            container.mount(Static(md))
            
        elif content.preview_type == PreviewType.JSON:
            try:
                parsed = json.loads(content.content)
                pretty = json.dumps(parsed, indent=2)
                syntax = Syntax(pretty, "json", theme="monokai")
                container.mount(Static(syntax))
            except:
                container.mount(Static(content.content))
                
        elif content.preview_type == PreviewType.ERROR:
            error_panel = Panel(
                content.content,
                title="⚠️ Error",
                border_style="red",
                expand=False
            )
            container.mount(Static(error_panel))
            
        elif content.preview_type == PreviewType.OUTPUT:
            output_panel = Panel(
                content.content,
                title="📤 Output",
                border_style="green",
                expand=False
            )
            container.mount(Static(output_panel))
            
        else:
            # Default text display
            container.mount(Static(content.content))
            
    def clear(self):
        """Clear the preview pane"""
        self.current_content = None
        container = self.query_one(f"#preview-content-{self.pane_id}", ScrollableContainer)
        container.remove_children()

class DesktopManager:
    """Manages the desktop interface with chat and preview panes"""
    
    def __init__(self):
        self.chat_interface: Optional[ChatInterface] = None
        self.preview_panes: Dict[str, PreviewPane] = {}
        self.active_pane_id: Optional[str] = None
        self.layout_mode = "horizontal"  # horizontal, vertical, grid
        
    def create_chat_interface(self) -> ChatInterface:
        """Create the chat interface"""
        self.chat_interface = ChatInterface(id="desktop-chat")
        return self.chat_interface
        
    def create_preview_pane(self, pane_id: str, title: str) -> PreviewPane:
        """Create a new preview pane"""
        pane = PreviewPane(pane_id=pane_id, title=title, id=f"preview-{pane_id}")
        self.preview_panes[pane_id] = pane
        
        # Set as active if first pane
        if not self.active_pane_id:
            self.active_pane_id = pane_id
            
        return pane
        
    def remove_preview_pane(self, pane_id: str):
        """Remove a preview pane"""
        if pane_id in self.preview_panes:
            del self.preview_panes[pane_id]
            
            # Update active pane if needed
            if self.active_pane_id == pane_id:
                self.active_pane_id = list(self.preview_panes.keys())[0] if self.preview_panes else None
                
    def show_code(self, pane_id: str, code: str, language: str = "python", title: Optional[str] = None):
        """Show code in a preview pane"""
        if pane_id not in self.preview_panes:
            self.create_preview_pane(pane_id, title or f"Code: {language}")
            
        content = PreviewContent(
            title=title or f"Code: {language}",
            content=code,
            preview_type=PreviewType.CODE,
            language=language
        )
        self.preview_panes[pane_id].show_content(content)
        
    def show_output(self, pane_id: str, output: str, title: Optional[str] = None):
        """Show output in a preview pane"""
        if pane_id not in self.preview_panes:
            self.create_preview_pane(pane_id, title or "Output")
            
        content = PreviewContent(
            title=title or "Output",
            content=output,
            preview_type=PreviewType.OUTPUT
        )
        self.preview_panes[pane_id].show_content(content)
        
    def show_error(self, pane_id: str, error: str, title: Optional[str] = None):
        """Show error in a preview pane"""
        if pane_id not in self.preview_panes:
            self.create_preview_pane(pane_id, title or "Error")
            
        content = PreviewContent(
            title=title or "Error",
            content=error,
            preview_type=PreviewType.ERROR
        )
        self.preview_panes[pane_id].show_content(content)
        
    def show_markdown(self, pane_id: str, markdown: str, title: Optional[str] = None):
        """Show markdown in a preview pane"""
        if pane_id not in self.preview_panes:
            self.create_preview_pane(pane_id, title or "Documentation")
            
        content = PreviewContent(
            title=title or "Documentation",
            content=markdown,
            preview_type=PreviewType.MARKDOWN
        )
        self.preview_panes[pane_id].show_content(content)
        
    def add_chat_message(self, sender: str, content: str, message_type: Literal["user", "agent", "system"] = "agent"):
        """Add a message to the chat interface"""
        if self.chat_interface:
            message = ChatMessage(
                sender=sender,
                content=content,
                timestamp=datetime.now(),
                message_type=message_type
            )
            self.chat_interface.add_message(message)
            
    def get_chat_history(self) -> List[ChatMessage]:
        """Get the chat history"""
        if self.chat_interface:
            return self.chat_interface.messages
        return []
        
    def switch_to_pane(self, pane_id: str):
        """Switch active preview pane"""
        if pane_id in self.preview_panes:
            self.active_pane_id = pane_id
            
    def set_layout_mode(self, mode: Literal["horizontal", "vertical", "grid"]):
        """Set the layout mode for preview panes"""
        self.layout_mode = mode
        
    def get_active_pane(self) -> Optional[PreviewPane]:
        """Get the currently active preview pane"""
        if self.active_pane_id:
            return self.preview_panes.get(self.active_pane_id)
        return None

class DesktopManagerWidget(Container):
    """Textual widget for the Desktop Manager"""
    
    def __init__(self, desktop_manager: DesktopManager, **kwargs):
        super().__init__(**kwargs)
        self.desktop_manager = desktop_manager
        
    def compose(self) -> ComposeResult:
        """Compose the desktop manager UI"""
        # Create layout based on mode
        if self.desktop_manager.layout_mode == "horizontal":
            with Horizontal():
                # Chat on the left
                if self.desktop_manager.chat_interface:
                    yield self.desktop_manager.chat_interface
                    
                # Preview panes on the right
                with Vertical(id="preview-container"):
                    for pane in self.desktop_manager.preview_panes.values():
                        yield pane
        else:
            # Vertical layout
            with Vertical():
                # Chat on top
                if self.desktop_manager.chat_interface:
                    yield self.desktop_manager.chat_interface
                    
                # Preview panes below
                with Horizontal(id="preview-container"):
                    for pane in self.desktop_manager.preview_panes.values():
                        yield pane

# Helper functions for common use cases
def create_code_preview(desktop_manager: DesktopManager, filename: str, code: str, language: str = "python"):
    """Create a code preview pane"""
    pane_id = f"code-{filename.replace('.', '_')}"
    desktop_manager.show_code(pane_id, code, language, f"📄 {filename}")
    return pane_id

def create_output_preview(desktop_manager: DesktopManager, title: str, output: str):
    """Create an output preview pane"""
    pane_id = f"output-{title.lower().replace(' ', '_')}"
    desktop_manager.show_output(pane_id, output, title)
    return pane_id

def create_error_preview(desktop_manager: DesktopManager, error_msg: str):
    """Create an error preview pane"""
    pane_id = "error-display"
    desktop_manager.show_error(pane_id, error_msg, "⚠️ Error Details")
    return pane_id

# Demo function
async def demo_desktop_manager():
    """Demonstrate Desktop Manager capabilities"""
    dm = DesktopManager()
    
    # Create chat interface
    chat = dm.create_chat_interface()
    
    # Add some messages
    dm.add_chat_message("User", "Analyze the nexus_core.py file", "user")
    dm.add_chat_message("Code Analyzer", "Starting analysis...", "agent")
    
    # Create preview panes
    code_pane = create_code_preview(dm, "nexus_core.py", "def main():\n    print('Hello NEXUS!')", "python")
    output_pane = create_output_preview(dm, "Analysis Results", "File contains 150 lines\n5 classes\n20 functions")
    
    # Add more chat messages
    dm.add_chat_message("Code Analyzer", "Analysis complete! Found 5 classes and 20 functions.", "agent")
    dm.add_chat_message("System", "Preview panes updated with results", "system")
    
    print(f"Desktop Manager created with {len(dm.preview_panes)} preview panes")
    print(f"Chat has {len(dm.get_chat_history())} messages")

if __name__ == "__main__":
    asyncio.run(demo_desktop_manager())