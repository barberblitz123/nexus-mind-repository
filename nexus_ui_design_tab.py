#!/usr/bin/env python3
"""
NEXUS Design Tab - Visual design tools in terminal
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import OrderedDict

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Condition, has_focus
from prompt_toolkit.formatted_text import FormattedText, StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import (
    Container, HSplit, VSplit, Window, WindowAlign,
    ConditionalContainer, ScrollablePane, DynamicContainer,
    FloatContainer, Float
)
from prompt_toolkit.layout.controls import FormattedTextControl, BufferControl
from prompt_toolkit.layout.dimension import Dimension, D
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import (
    Button, Label, Frame, Box, Dialog,
    TextArea, RadioList, Checkbox
)

from nexus_vision_processor import VisionProcessor
from nexus_voice_design import VoiceDesignEngine


class DesignTool(Enum):
    SELECT = "select"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    LINE = "line"
    TEXT = "text"
    IMAGE = "image"
    COMPONENT = "component"
    PAN = "pan"
    ZOOM = "zoom"


class ComponentType(Enum):
    BUTTON = "button"
    INPUT = "input"
    CARD = "card"
    NAVBAR = "navbar"
    SIDEBAR = "sidebar"
    MODAL = "modal"
    TABLE = "table"
    FORM = "form"
    HERO = "hero"
    FOOTER = "footer"


@dataclass
class Color:
    """Represents a color with various formats"""
    hex: str
    rgb: Tuple[int, int, int]
    hsl: Tuple[int, int, int]
    name: Optional[str] = None
    
    @classmethod
    def from_hex(cls, hex_color: str) -> 'Color':
        """Create color from hex string"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        # TODO: Convert to HSL
        return cls(hex=f"#{hex_color}", rgb=rgb, hsl=(0, 0, 0))


@dataclass
class Typography:
    """Typography settings"""
    font_family: str = "Inter"
    font_size: int = 16
    font_weight: str = "normal"
    line_height: float = 1.5
    letter_spacing: float = 0
    text_transform: str = "none"


@dataclass
class DesignElement:
    """Base class for design elements"""
    id: str
    type: str
    position: Tuple[int, int]
    size: Tuple[int, int]
    style: Dict[str, Any] = field(default_factory=dict)
    children: List['DesignElement'] = field(default_factory=list)
    locked: bool = False
    visible: bool = True
    name: str = ""


@dataclass
class Layer:
    """Design layer"""
    id: str
    name: str
    elements: List[DesignElement] = field(default_factory=list)
    visible: bool = True
    locked: bool = False
    opacity: float = 1.0


@dataclass
class DesignSystem:
    """Design system configuration"""
    colors: Dict[str, Color] = field(default_factory=dict)
    typography: Dict[str, Typography] = field(default_factory=dict)
    spacing: List[int] = field(default_factory=lambda: [4, 8, 12, 16, 24, 32, 48, 64])
    breakpoints: Dict[str, int] = field(default_factory=lambda: {
        'mobile': 640,
        'tablet': 768,
        'desktop': 1024,
        'wide': 1280
    })
    shadows: Dict[str, str] = field(default_factory=dict)
    borders: Dict[str, str] = field(default_factory=dict)


class CanvasRenderer:
    """Renders design to ASCII art canvas"""
    
    def __init__(self, width: int = 80, height: int = 40):
        self.width = width
        self.height = height
        self.canvas = [[' ' for _ in range(width)] for _ in range(height)]
        self.colors = [[None for _ in range(width)] for _ in range(height)]
    
    def clear(self):
        """Clear canvas"""
        self.canvas = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        self.colors = [[None for _ in range(self.width)] for _ in range(self.height)]
    
    def draw_rectangle(self, x: int, y: int, w: int, h: int, style: Dict[str, Any]):
        """Draw rectangle on canvas"""
        # Draw borders
        for i in range(w):
            if 0 <= x + i < self.width:
                if 0 <= y < self.height:
                    self.canvas[y][x + i] = '─'
                if 0 <= y + h - 1 < self.height:
                    self.canvas[y + h - 1][x + i] = '─'
        
        for i in range(h):
            if 0 <= y + i < self.height:
                if 0 <= x < self.width:
                    self.canvas[y + i][x] = '│'
                if 0 <= x + w - 1 < self.width:
                    self.canvas[y + i][x + w - 1] = '│'
        
        # Draw corners
        if 0 <= x < self.width and 0 <= y < self.height:
            self.canvas[y][x] = '┌'
        if 0 <= x + w - 1 < self.width and 0 <= y < self.height:
            self.canvas[y][x + w - 1] = '┐'
        if 0 <= x < self.width and 0 <= y + h - 1 < self.height:
            self.canvas[y + h - 1][x] = '└'
        if 0 <= x + w - 1 < self.width and 0 <= y + h - 1 < self.height:
            self.canvas[y + h - 1][x + w - 1] = '┘'
        
        # Fill if background color
        if 'backgroundColor' in style:
            for row in range(1, h - 1):
                for col in range(1, w - 1):
                    if 0 <= y + row < self.height and 0 <= x + col < self.width:
                        self.canvas[y + row][x + col] = '█'
                        self.colors[y + row][x + col] = style['backgroundColor']
    
    def draw_circle(self, cx: int, cy: int, r: int, style: Dict[str, Any]):
        """Draw circle on canvas"""
        # Simple ASCII circle approximation
        for y in range(max(0, cy - r), min(self.height, cy + r + 1)):
            for x in range(max(0, cx - r), min(self.width, cx + r + 1)):
                dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if abs(dist - r) < 0.5:
                    self.canvas[y][x] = '●'
                elif dist < r and 'backgroundColor' in style:
                    self.canvas[y][x] = '○'
    
    def draw_text(self, x: int, y: int, text: str, style: Dict[str, Any]):
        """Draw text on canvas"""
        for i, char in enumerate(text):
            if 0 <= x + i < self.width and 0 <= y < self.height:
                self.canvas[y][x + i] = char
    
    def render_element(self, element: DesignElement):
        """Render a design element"""
        x, y = element.position
        w, h = element.size
        
        if element.type == 'rectangle':
            self.draw_rectangle(x, y, w, h, element.style)
        elif element.type == 'circle':
            r = min(w, h) // 2
            self.draw_circle(x + w // 2, y + h // 2, r, element.style)
        elif element.type == 'text':
            text = element.style.get('text', 'Text')
            self.draw_text(x, y, text, element.style)
        
        # Render children
        for child in element.children:
            self.render_element(child)
    
    def get_canvas_text(self) -> List[str]:
        """Get canvas as list of strings"""
        return [''.join(row) for row in self.canvas]


class DesignInterface:
    """Main design interface"""
    
    def __init__(self, parent_app=None):
        self.parent_app = parent_app
        self.current_tool = DesignTool.SELECT
        self.selected_elements: List[DesignElement] = []
        self.layers: List[Layer] = [Layer(id="layer1", name="Layer 1")]
        self.active_layer_index = 0
        self.design_system = self._create_default_design_system()
        self.canvas_renderer = CanvasRenderer()
        self.zoom_level = 1.0
        self.pan_offset = (0, 0)
        self.grid_visible = True
        self.snap_to_grid = True
        self.grid_size = 8
        
        # Components
        self.vision_processor = VisionProcessor()
        self.voice_design = VoiceDesignEngine()
        
        # UI state
        self.property_panel_visible = True
        self.layers_panel_visible = True
        self.component_library_visible = True
        self.color_picker_visible = False
        
        # Buffers
        self.search_buffer = Buffer()
        self.export_dialog_buffer = Buffer()
        
        # Key bindings
        self.kb = KeyBindings()
        self._setup_key_bindings()
        
        # Styles
        self.style = Style.from_dict({
            'canvas': 'bg:#1a1a1a #ffffff',
            'canvas.grid': '#333333',
            'canvas.selection': 'bg:#0066cc',
            'panel': 'bg:#2d2d2d #cccccc',
            'panel.header': 'bg:#1e1e1e #ffffff bold',
            'tool': 'bg:#3d3d3d #cccccc',
            'tool.active': 'bg:#0066cc #ffffff',
            'property': '#888888',
            'property.value': '#ffffff',
            'layer': 'bg:#2d2d2d #cccccc',
            'layer.active': 'bg:#0066cc #ffffff',
            'component': 'bg:#3d3d3d #cccccc',
            'component.hover': 'bg:#4d4d4d #ffffff',
            'color': 'bg:#ffffff #000000',
            'ruler': 'bg:#1e1e1e #666666',
        })
        
        # Initialize with default elements
        self._create_default_elements()
    
    def _create_default_design_system(self) -> DesignSystem:
        """Create default design system"""
        return DesignSystem(
            colors={
                'primary': Color.from_hex('#0066cc'),
                'secondary': Color.from_hex('#6c757d'),
                'success': Color.from_hex('#28a745'),
                'danger': Color.from_hex('#dc3545'),
                'warning': Color.from_hex('#ffc107'),
                'info': Color.from_hex('#17a2b8'),
                'light': Color.from_hex('#f8f9fa'),
                'dark': Color.from_hex('#343a40'),
            },
            typography={
                'heading1': Typography(font_size=32, font_weight='bold'),
                'heading2': Typography(font_size=24, font_weight='bold'),
                'heading3': Typography(font_size=20, font_weight='semibold'),
                'body': Typography(font_size=16),
                'small': Typography(font_size=14),
                'caption': Typography(font_size=12),
            },
            shadows={
                'sm': '0 1px 2px rgba(0,0,0,0.05)',
                'md': '0 4px 6px rgba(0,0,0,0.1)',
                'lg': '0 10px 15px rgba(0,0,0,0.1)',
                'xl': '0 20px 25px rgba(0,0,0,0.1)',
            },
            borders={
                'thin': '1px solid',
                'medium': '2px solid',
                'thick': '4px solid',
                'rounded': 'border-radius: 4px',
                'pill': 'border-radius: 9999px',
            }
        )
    
    def _create_default_elements(self):
        """Create some default elements"""
        # Add a button component
        button = DesignElement(
            id="btn1",
            type="rectangle",
            position=(10, 5),
            size=(20, 3),
            name="Primary Button",
            style={
                'backgroundColor': self.design_system.colors['primary'].hex,
                'color': '#ffffff',
                'borderRadius': 4,
                'text': 'Click Me'
            }
        )
        
        # Add a card
        card = DesignElement(
            id="card1",
            type="rectangle",
            position=(35, 5),
            size=(30, 10),
            name="Card Component",
            style={
                'backgroundColor': '#ffffff',
                'borderColor': '#e0e0e0',
                'borderWidth': 1,
                'padding': 16,
                'boxShadow': self.design_system.shadows['md']
            }
        )
        
        self.layers[0].elements.extend([button, card])
    
    def _setup_key_bindings(self):
        """Setup keyboard shortcuts"""
        
        # Tool selection
        @self.kb.add('v')
        def select_tool(event):
            """Select/move tool"""
            self.current_tool = DesignTool.SELECT
        
        @self.kb.add('r')
        def rectangle_tool(event):
            """Rectangle tool"""
            self.current_tool = DesignTool.RECTANGLE
        
        @self.kb.add('c')
        def circle_tool(event):
            """Circle tool"""
            self.current_tool = DesignTool.CIRCLE
        
        @self.kb.add('t')
        def text_tool(event):
            """Text tool"""
            self.current_tool = DesignTool.TEXT
        
        @self.kb.add('l')
        def line_tool(event):
            """Line tool"""
            self.current_tool = DesignTool.LINE
        
        # View controls
        @self.kb.add('c-plus')
        def zoom_in(event):
            """Zoom in"""
            self.zoom_level = min(self.zoom_level * 1.2, 5.0)
        
        @self.kb.add('c-minus')
        def zoom_out(event):
            """Zoom out"""
            self.zoom_level = max(self.zoom_level / 1.2, 0.2)
        
        @self.kb.add('c-0')
        def zoom_reset(event):
            """Reset zoom"""
            self.zoom_level = 1.0
        
        @self.kb.add('g')
        def toggle_grid(event):
            """Toggle grid"""
            self.grid_visible = not self.grid_visible
        
        @self.kb.add('s-g')
        def toggle_snap(event):
            """Toggle snap to grid"""
            self.snap_to_grid = not self.snap_to_grid
        
        # Element operations
        @self.kb.add('c-c')
        def copy_elements(event):
            """Copy selected elements"""
            self._copy_elements()
        
        @self.kb.add('c-v')
        def paste_elements(event):
            """Paste elements"""
            self._paste_elements()
        
        @self.kb.add('c-d')
        def duplicate_elements(event):
            """Duplicate selected elements"""
            self._duplicate_elements()
        
        @self.kb.add('delete')
        def delete_elements(event):
            """Delete selected elements"""
            self._delete_elements()
        
        @self.kb.add('c-g')
        def group_elements(event):
            """Group selected elements"""
            self._group_elements()
        
        @self.kb.add('c-s-g')
        def ungroup_elements(event):
            """Ungroup selected elements"""
            self._ungroup_elements()
        
        # Alignment
        @self.kb.add('a-left')
        def align_left(event):
            """Align left"""
            self._align_elements('left')
        
        @self.kb.add('a-right')
        def align_right(event):
            """Align right"""
            self._align_elements('right')
        
        @self.kb.add('a-up')
        def align_top(event):
            """Align top"""
            self._align_elements('top')
        
        @self.kb.add('a-down')
        def align_bottom(event):
            """Align bottom"""
            self._align_elements('bottom')
        
        # Export
        @self.kb.add('c-e')
        def export_design(event):
            """Export design"""
            self._show_export_dialog()
        
        # Voice commands
        @self.kb.add('c-m')
        async def voice_command(event):
            """Voice design command"""
            await self._handle_voice_command()
    
    @property
    def current_layer(self) -> Optional[Layer]:
        """Get current active layer"""
        if 0 <= self.active_layer_index < len(self.layers):
            return self.layers[self.active_layer_index]
        return None
    
    def _snap_to_grid(self, x: int, y: int) -> Tuple[int, int]:
        """Snap coordinates to grid"""
        if self.snap_to_grid:
            x = round(x / self.grid_size) * self.grid_size
            y = round(y / self.grid_size) * self.grid_size
        return x, y
    
    def _copy_elements(self):
        """Copy selected elements to clipboard"""
        # TODO: Implement copy
        pass
    
    def _paste_elements(self):
        """Paste elements from clipboard"""
        # TODO: Implement paste
        pass
    
    def _duplicate_elements(self):
        """Duplicate selected elements"""
        if not self.selected_elements or not self.current_layer:
            return
        
        for element in self.selected_elements:
            # Create copy with offset
            new_element = DesignElement(
                id=f"{element.id}_copy",
                type=element.type,
                position=(element.position[0] + 10, element.position[1] + 10),
                size=element.size,
                style=element.style.copy(),
                name=f"{element.name} Copy"
            )
            self.current_layer.elements.append(new_element)
    
    def _delete_elements(self):
        """Delete selected elements"""
        if not self.selected_elements or not self.current_layer:
            return
        
        for element in self.selected_elements:
            if element in self.current_layer.elements:
                self.current_layer.elements.remove(element)
        
        self.selected_elements.clear()
    
    def _group_elements(self):
        """Group selected elements"""
        if len(self.selected_elements) < 2:
            return
        
        # Create group element
        # TODO: Implement grouping
        pass
    
    def _ungroup_elements(self):
        """Ungroup selected elements"""
        # TODO: Implement ungrouping
        pass
    
    def _align_elements(self, direction: str):
        """Align selected elements"""
        if len(self.selected_elements) < 2:
            return
        
        if direction == 'left':
            min_x = min(e.position[0] for e in self.selected_elements)
            for element in self.selected_elements:
                element.position = (min_x, element.position[1])
        elif direction == 'right':
            max_x = max(e.position[0] + e.size[0] for e in self.selected_elements)
            for element in self.selected_elements:
                element.position = (max_x - element.size[0], element.position[1])
        elif direction == 'top':
            min_y = min(e.position[1] for e in self.selected_elements)
            for element in self.selected_elements:
                element.position = (element.position[0], min_y)
        elif direction == 'bottom':
            max_y = max(e.position[1] + e.size[1] for e in self.selected_elements)
            for element in self.selected_elements:
                element.position = (element.position[0], max_y - element.size[1])
    
    def _show_export_dialog(self):
        """Show export dialog"""
        # TODO: Implement export dialog
        pass
    
    async def _handle_voice_command(self):
        """Handle voice design command"""
        command = await self.voice_design.listen_for_command()
        
        if "create button" in command.lower():
            # Create button at center
            button = DesignElement(
                id=f"btn_{len(self.current_layer.elements)}",
                type="rectangle",
                position=(40, 20),
                size=(20, 3),
                name="Voice Button",
                style={
                    'backgroundColor': self.design_system.colors['primary'].hex,
                    'color': '#ffffff',
                    'text': 'Button'
                }
            )
            self.current_layer.elements.append(button)
            self.selected_elements = [button]
        
        # TODO: Add more voice commands
    
    def _render_canvas(self) -> List[str]:
        """Render design canvas"""
        self.canvas_renderer.clear()
        
        # Render grid if visible
        if self.grid_visible:
            for y in range(0, self.canvas_renderer.height, self.grid_size):
                for x in range(0, self.canvas_renderer.width, self.grid_size):
                    if x < self.canvas_renderer.width and y < self.canvas_renderer.height:
                        self.canvas_renderer.canvas[y][x] = '·'
        
        # Render elements from all visible layers
        for layer in self.layers:
            if layer.visible:
                for element in layer.elements:
                    if element.visible:
                        self.canvas_renderer.render_element(element)
        
        # Render selection
        for element in self.selected_elements:
            x, y = element.position
            w, h = element.size
            # Draw selection handles
            if 0 <= x < self.canvas_renderer.width and 0 <= y < self.canvas_renderer.height:
                self.canvas_renderer.canvas[y][x] = '◆'
            if 0 <= x + w - 1 < self.canvas_renderer.width and 0 <= y < self.canvas_renderer.height:
                self.canvas_renderer.canvas[y][x + w - 1] = '◆'
            if 0 <= x < self.canvas_renderer.width and 0 <= y + h - 1 < self.canvas_renderer.height:
                self.canvas_renderer.canvas[y + h - 1][x] = '◆'
            if 0 <= x + w - 1 < self.canvas_renderer.width and 0 <= y + h - 1 < self.canvas_renderer.height:
                self.canvas_renderer.canvas[y + h - 1][x + w - 1] = '◆'
        
        return self.canvas_renderer.get_canvas_text()
    
    def _create_tools_panel(self) -> Container:
        """Create tools panel"""
        tools = []
        
        for tool in DesignTool:
            is_active = tool == self.current_tool
            style = 'class:tool.active' if is_active else 'class:tool'
            
            icon_map = {
                DesignTool.SELECT: '↖',
                DesignTool.RECTANGLE: '□',
                DesignTool.CIRCLE: '○',
                DesignTool.LINE: '╱',
                DesignTool.TEXT: 'T',
                DesignTool.IMAGE: '🖼',
                DesignTool.COMPONENT: '◈',
                DesignTool.PAN: '✋',
                DesignTool.ZOOM: '🔍',
            }
            
            tools.append(
                Window(
                    FormattedTextControl(
                        text=f" {icon_map.get(tool, '?')} "
                    ),
                    width=4,
                    height=1,
                    style=style
                )
            )
        
        return Frame(
            HSplit(tools),
            title="Tools",
            style='class:panel'
        )
    
    def _create_properties_panel(self) -> Container:
        """Create properties panel"""
        if not self.selected_elements:
            content = Window(
                FormattedTextControl(text="No selection")
            )
        else:
            element = self.selected_elements[0]  # Show first selected
            
            props = []
            props.append(Window(FormattedTextControl(
                text=f"Type: {element.type}\nName: {element.name}"
            ), height=2))
            
            props.append(Window(FormattedTextControl(text="─" * 20), height=1))
            
            # Position and size
            props.append(Window(FormattedTextControl(
                text=f"X: {element.position[0]}  Y: {element.position[1]}\n"
                     f"W: {element.size[0]}  H: {element.size[1]}"
            ), height=2))
            
            props.append(Window(FormattedTextControl(text="─" * 20), height=1))
            
            # Style properties
            style_text = "Style:\n"
            for key, value in element.style.items():
                style_text += f"  {key}: {value}\n"
            
            props.append(Window(FormattedTextControl(text=style_text)))
            
            content = HSplit(props)
        
        return ConditionalContainer(
            Frame(
                ScrollablePane(content),
                title="Properties",
                style='class:panel'
            ),
            filter=Condition(lambda: self.property_panel_visible)
        )
    
    def _create_layers_panel(self) -> Container:
        """Create layers panel"""
        layers = []
        
        for i, layer in enumerate(reversed(self.layers)):
            idx = len(self.layers) - i - 1
            is_active = idx == self.active_layer_index
            style = 'class:layer.active' if is_active else 'class:layer'
            
            visibility = '👁' if layer.visible else '👁‍🗨'
            lock = '🔒' if layer.locked else '  '
            
            layers.append(
                Window(
                    FormattedTextControl(
                        text=f"{visibility} {lock} {layer.name} ({len(layer.elements)})"
                    ),
                    height=1,
                    style=style
                )
            )
        
        return ConditionalContainer(
            Frame(
                HSplit(layers),
                title="Layers",
                style='class:panel'
            ),
            filter=Condition(lambda: self.layers_panel_visible)
        )
    
    def _create_component_library(self) -> Container:
        """Create component library panel"""
        components = []
        
        for comp_type in ComponentType:
            components.append(
                Window(
                    FormattedTextControl(
                        text=f"  {comp_type.value.title()}"
                    ),
                    height=1,
                    style='class:component'
                )
            )
        
        return ConditionalContainer(
            Frame(
                ScrollablePane(HSplit(components)),
                title="Components",
                style='class:panel'
            ),
            filter=Condition(lambda: self.component_library_visible)
        )
    
    def _create_color_palette(self) -> Container:
        """Create color palette"""
        colors = []
        
        for name, color in self.design_system.colors.items():
            colors.append(
                Window(
                    FormattedTextControl(
                        text=f"  ■ {name}: {color.hex}"
                    ),
                    height=1,
                    style=f"fg:{color.hex}"
                )
            )
        
        return Frame(
            HSplit(colors),
            title="Colors",
            style='class:panel'
        )
    
    def _create_canvas(self) -> Container:
        """Create main canvas area"""
        # Rulers
        h_ruler = Window(
            FormattedTextControl(
                text=lambda: ''.join(str(i % 10) for i in range(80))
            ),
            height=1,
            style='class:ruler'
        )
        
        v_ruler = Window(
            FormattedTextControl(
                text=lambda: '\n'.join(str(i % 10) for i in range(40))
            ),
            width=2,
            style='class:ruler'
        )
        
        # Canvas
        canvas_text = lambda: '\n'.join(self._render_canvas())
        canvas = Window(
            FormattedTextControl(text=canvas_text),
            style='class:canvas'
        )
        
        # Status bar
        status = Window(
            FormattedTextControl(
                text=lambda: f" Tool: {self.current_tool.value} | "
                            f"Zoom: {int(self.zoom_level * 100)}% | "
                            f"Grid: {'ON' if self.grid_visible else 'OFF'} | "
                            f"Snap: {'ON' if self.snap_to_grid else 'OFF'} | "
                            f"Selected: {len(self.selected_elements)}"
            ),
            height=1,
            style='class:status-bar'
        )
        
        return HSplit([
            h_ruler,
            VSplit([
                v_ruler,
                canvas
            ]),
            status
        ])
    
    def create_layout(self) -> Container:
        """Create the design tab layout"""
        # Left sidebar
        left_sidebar = VSplit([
            self._create_tools_panel(),
            self._create_component_library()
        ])
        
        # Right sidebar
        right_sidebar = HSplit([
            self._create_properties_panel(),
            self._create_layers_panel(),
            self._create_color_palette()
        ])
        
        # Main layout
        return VSplit([
            left_sidebar,
            self._create_canvas(),
            right_sidebar
        ])


def create_design_tab(parent_app=None) -> Container:
    """Factory function to create design tab"""
    design = DesignInterface(parent_app)
    return design.create_layout()