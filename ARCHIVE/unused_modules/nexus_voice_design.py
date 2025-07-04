#!/usr/bin/env python3
"""
NEXUS Voice-to-Design System
Translates voice commands into design actions with natural language understanding
"""

import re
import json
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComponentType(Enum):
    """Supported component types"""
    BUTTON = "button"
    TEXT = "text"
    IMAGE = "image"
    FORM = "form"
    INPUT = "input"
    CONTAINER = "container"
    NAVIGATION = "navigation"
    GRID = "grid"
    FLEX = "flex"
    CARD = "card"
    LIST = "list"
    HEADER = "header"
    FOOTER = "footer"
    SIDEBAR = "sidebar"
    MODAL = "modal"
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    TEXTAREA = "textarea"
    LINK = "link"
    ICON = "icon"


class LayoutType(Enum):
    """Layout types"""
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"
    GRID = "grid"
    FLEX = "flex"
    ABSOLUTE = "absolute"
    RELATIVE = "relative"
    FIXED = "fixed"


class Position(Enum):
    """Position values"""
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    TOP_LEFT = "top-left"
    TOP_RIGHT = "top-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_RIGHT = "bottom-right"


@dataclass
class StyleProperties:
    """Design style properties"""
    color: Optional[str] = None
    background_color: Optional[str] = None
    font_size: Optional[str] = None
    font_weight: Optional[str] = None
    font_family: Optional[str] = None
    padding: Optional[Union[str, Dict[str, str]]] = None
    margin: Optional[Union[str, Dict[str, str]]] = None
    border: Optional[str] = None
    border_radius: Optional[str] = None
    width: Optional[str] = None
    height: Optional[str] = None
    display: Optional[str] = None
    position: Optional[str] = None
    text_align: Optional[str] = None
    justify_content: Optional[str] = None
    align_items: Optional[str] = None
    flex_direction: Optional[str] = None
    gap: Optional[str] = None
    opacity: Optional[float] = None
    z_index: Optional[int] = None
    box_shadow: Optional[str] = None
    transform: Optional[str] = None
    transition: Optional[str] = None
    cursor: Optional[str] = None
    overflow: Optional[str] = None
    
    def to_css(self) -> Dict[str, Any]:
        """Convert to CSS properties"""
        css = {}
        for key, value in self.__dict__.items():
            if value is not None:
                css_key = key.replace('_', '-')
                css[css_key] = value
        return css


@dataclass
class Component:
    """Design component"""
    id: str
    type: ComponentType
    properties: Dict[str, Any] = field(default_factory=dict)
    styles: StyleProperties = field(default_factory=StyleProperties)
    children: List['Component'] = field(default_factory=list)
    parent_id: Optional[str] = None
    position: Optional[Position] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary"""
        return {
            'id': self.id,
            'type': self.type.value,
            'properties': self.properties,
            'styles': self.styles.to_css(),
            'children': [child.to_dict() for child in self.children],
            'parent_id': self.parent_id,
            'position': self.position.value if self.position else None
        }


class NaturalLanguageParser:
    """Parse natural language design commands"""
    
    def __init__(self):
        # Color mappings
        self.colors = {
            'red': '#FF0000', 'blue': '#0000FF', 'green': '#008000',
            'yellow': '#FFFF00', 'orange': '#FFA500', 'purple': '#800080',
            'pink': '#FFC0CB', 'black': '#000000', 'white': '#FFFFFF',
            'gray': '#808080', 'grey': '#808080', 'brown': '#A52A2A',
            'navy': '#000080', 'teal': '#008080', 'cyan': '#00FFFF',
            'magenta': '#FF00FF', 'lime': '#00FF00', 'indigo': '#4B0082',
            'violet': '#8B00FF', 'turquoise': '#40E0D0', 'gold': '#FFD700',
            'silver': '#C0C0C0', 'maroon': '#800000', 'olive': '#808000'
        }
        
        # Size mappings
        self.sizes = {
            'tiny': '8px', 'small': '12px', 'medium': '16px',
            'large': '20px', 'huge': '32px', 'massive': '48px',
            'extra small': '10px', 'extra large': '24px'
        }
        
        # Component patterns
        self.component_patterns = {
            ComponentType.BUTTON: r'(?:add|create|make|insert)\s+(?:a\s+)?button',
            ComponentType.FORM: r'(?:add|create|make|insert)\s+(?:a\s+)?form',
            ComponentType.INPUT: r'(?:add|create|make|insert)\s+(?:an?\s+)?(?:input|field|textbox)',
            ComponentType.NAVIGATION: r'(?:add|create|make|insert)\s+(?:a\s+)?(?:navigation|nav|navbar|menu)',
            ComponentType.CONTAINER: r'(?:add|create|make|insert)\s+(?:a\s+)?(?:container|div|box|section)',
            ComponentType.GRID: r'(?:create|make)\s+(?:a\s+)?grid',
            ComponentType.CARD: r'(?:add|create|make|insert)\s+(?:a\s+)?card',
            ComponentType.HEADER: r'(?:add|create|make|insert)\s+(?:a\s+)?header',
            ComponentType.FOOTER: r'(?:add|create|make|insert)\s+(?:a\s+)?footer',
            ComponentType.SIDEBAR: r'(?:add|create|make|insert)\s+(?:a\s+)?sidebar',
            ComponentType.TEXT: r'(?:add|create|make|insert)\s+(?:a\s+)?(?:text|label|paragraph|heading)',
            ComponentType.IMAGE: r'(?:add|create|make|insert)\s+(?:an?\s+)?(?:image|picture|photo)',
            ComponentType.LINK: r'(?:add|create|make|insert)\s+(?:a\s+)?link',
            ComponentType.LIST: r'(?:add|create|make|insert)\s+(?:a\s+)?list',
            ComponentType.MODAL: r'(?:add|create|make|insert)\s+(?:a\s+)?modal',
            ComponentType.DROPDOWN: r'(?:add|create|make|insert)\s+(?:a\s+)?dropdown',
            ComponentType.CHECKBOX: r'(?:add|create|make|insert)\s+(?:a\s+)?checkbox',
            ComponentType.RADIO: r'(?:add|create|make|insert)\s+(?:a\s+)?radio',
            ComponentType.TEXTAREA: r'(?:add|create|make|insert)\s+(?:a\s+)?textarea'
        }
        
        # Position patterns
        self.position_patterns = {
            Position.TOP: r'(?:at|to|on)\s+(?:the\s+)?top',
            Position.BOTTOM: r'(?:at|to|on)\s+(?:the\s+)?bottom',
            Position.LEFT: r'(?:at|to|on)\s+(?:the\s+)?left',
            Position.RIGHT: r'(?:at|to|on)\s+(?:the\s+)?right',
            Position.CENTER: r'(?:in|at|to)\s+(?:the\s+)?(?:center|middle)',
            Position.TOP_LEFT: r'(?:at|to|on)\s+(?:the\s+)?top[\s-]?left',
            Position.TOP_RIGHT: r'(?:at|to|on)\s+(?:the\s+)?top[\s-]?right',
            Position.BOTTOM_LEFT: r'(?:at|to|on)\s+(?:the\s+)?bottom[\s-]?left',
            Position.BOTTOM_RIGHT: r'(?:at|to|on)\s+(?:the\s+)?bottom[\s-]?right'
        }
        
        # Layout patterns
        self.layout_patterns = {
            LayoutType.GRID: r'(?:in\s+a\s+)?grid(?:\s+layout)?',
            LayoutType.VERTICAL: r'(?:stack(?:ed)?|arrange(?:d)?)\s+(?:them\s+)?vertical(?:ly)?',
            LayoutType.HORIZONTAL: r'(?:arrange(?:d)?|place(?:d)?)\s+(?:them\s+)?horizontal(?:ly)?|(?:side[\s-]?by[\s-]?side|next\s+to)',
            LayoutType.FLEX: r'(?:flex(?:box)?|flexible)\s+(?:layout)?'
        }
    
    def parse_color(self, text: str) -> Optional[str]:
        """Extract color from text"""
        text_lower = text.lower()
        
        # Check for hex colors
        hex_match = re.search(r'#[0-9A-Fa-f]{3,6}', text)
        if hex_match:
            return hex_match.group()
        
        # Check for RGB/RGBA
        rgb_match = re.search(r'rgb[a]?\([^)]+\)', text)
        if rgb_match:
            return rgb_match.group()
        
        # Check for named colors
        for color_name, color_value in self.colors.items():
            if color_name in text_lower:
                return color_value
        
        return None
    
    def parse_size(self, text: str) -> Optional[str]:
        """Extract size from text"""
        text_lower = text.lower()
        
        # Check for pixel values
        px_match = re.search(r'(\d+)\s*(?:px|pixels?)', text)
        if px_match:
            return f"{px_match.group(1)}px"
        
        # Check for percentage
        percent_match = re.search(r'(\d+)\s*%', text)
        if percent_match:
            return f"{percent_match.group(1)}%"
        
        # Check for named sizes
        for size_name, size_value in self.sizes.items():
            if size_name in text_lower:
                return size_value
        
        # Check for relative sizes
        if 'larger' in text_lower or 'bigger' in text_lower:
            return '1.2em'
        elif 'smaller' in text_lower:
            return '0.8em'
        
        return None
    
    def parse_component_type(self, text: str) -> Optional[ComponentType]:
        """Extract component type from text"""
        text_lower = text.lower()
        
        for comp_type, pattern in self.component_patterns.items():
            if re.search(pattern, text_lower):
                return comp_type
        
        return None
    
    def parse_position(self, text: str) -> Optional[Position]:
        """Extract position from text"""
        text_lower = text.lower()
        
        for position, pattern in self.position_patterns.items():
            if re.search(pattern, text_lower):
                return position
        
        return None
    
    def parse_layout(self, text: str) -> Optional[LayoutType]:
        """Extract layout type from text"""
        text_lower = text.lower()
        
        for layout, pattern in self.layout_patterns.items():
            if re.search(pattern, text_lower):
                return layout
        
        # Check for column count
        col_match = re.search(r'(\d+)[\s-]?column', text_lower)
        if col_match:
            return LayoutType.GRID
        
        return None
    
    def parse_style_properties(self, text: str) -> StyleProperties:
        """Extract style properties from text"""
        styles = StyleProperties()
        text_lower = text.lower()
        
        # Color
        if 'color' in text_lower and 'background' not in text_lower:
            color = self.parse_color(text)
            if color:
                styles.color = color
        
        # Background color
        if 'background' in text_lower or 'bg' in text_lower:
            color = self.parse_color(text)
            if color:
                styles.background_color = color
        
        # Font size
        if 'font' in text_lower or 'text' in text_lower:
            size = self.parse_size(text)
            if size:
                styles.font_size = size
        
        # Padding
        if 'padding' in text_lower:
            size = self.parse_size(text)
            if size:
                styles.padding = size
        
        # Margin
        if 'margin' in text_lower or 'spacing' in text_lower:
            size = self.parse_size(text)
            if size:
                styles.margin = size
        
        # Border radius
        if 'rounded' in text_lower or 'radius' in text_lower:
            if 'fully' in text_lower or 'circle' in text_lower:
                styles.border_radius = '50%'
            else:
                size = self.parse_size(text)
                styles.border_radius = size or '8px'
        
        # Text alignment
        if 'center' in text_lower and ('align' in text_lower or 'text' in text_lower):
            styles.text_align = 'center'
        elif 'left' in text_lower and 'align' in text_lower:
            styles.text_align = 'left'
        elif 'right' in text_lower and 'align' in text_lower:
            styles.text_align = 'right'
        
        # Width/Height
        width_match = re.search(r'width\s*(?:of\s*)?(\d+)\s*(?:px|pixels?|%)', text_lower)
        if width_match:
            styles.width = f"{width_match.group(1)}{'px' if 'px' in width_match.group() else '%'}"
        
        height_match = re.search(r'height\s*(?:of\s*)?(\d+)\s*(?:px|pixels?|%)', text_lower)
        if height_match:
            styles.height = f"{height_match.group(1)}{'px' if 'px' in height_match.group() else '%'}"
        
        # Shadow
        if 'shadow' in text_lower:
            if 'drop' in text_lower or 'box' in text_lower:
                styles.box_shadow = '0 4px 6px rgba(0, 0, 0, 0.1)'
        
        # Font weight
        if 'bold' in text_lower:
            styles.font_weight = 'bold'
        elif 'light' in text_lower:
            styles.font_weight = '300'
        
        return styles
    
    def parse_form_fields(self, text: str) -> List[Dict[str, str]]:
        """Extract form field specifications from text"""
        fields = []
        text_lower = text.lower()
        
        # Common field patterns
        field_patterns = [
            (r'email\s*(?:field|input)?', {'type': 'email', 'name': 'email', 'placeholder': 'Enter email'}),
            (r'password\s*(?:field|input)?', {'type': 'password', 'name': 'password', 'placeholder': 'Enter password'}),
            (r'(?:user)?name\s*(?:field|input)?', {'type': 'text', 'name': 'username', 'placeholder': 'Enter username'}),
            (r'phone\s*(?:field|input)?', {'type': 'tel', 'name': 'phone', 'placeholder': 'Enter phone number'}),
            (r'date\s*(?:field|input)?', {'type': 'date', 'name': 'date'}),
            (r'number\s*(?:field|input)?', {'type': 'number', 'name': 'number', 'placeholder': 'Enter number'}),
            (r'search\s*(?:field|input)?', {'type': 'search', 'name': 'search', 'placeholder': 'Search...'}),
            (r'url\s*(?:field|input)?', {'type': 'url', 'name': 'url', 'placeholder': 'Enter URL'}),
        ]
        
        for pattern, field_config in field_patterns:
            if re.search(pattern, text_lower):
                fields.append(field_config)
        
        return fields


class VoiceCommandProcessor:
    """Process voice commands and generate design actions"""
    
    def __init__(self):
        self.parser = NaturalLanguageParser()
        self.component_counter = 0
        self.components: Dict[str, Component] = {}
        self.selected_component_id: Optional[str] = None
    
    def generate_component_id(self, comp_type: ComponentType) -> str:
        """Generate unique component ID"""
        self.component_counter += 1
        return f"{comp_type.value}_{self.component_counter}"
    
    def process_design_command(self, command: str) -> Dict[str, Any]:
        """Process a design command"""
        command_lower = command.lower()
        
        # Check for component creation
        comp_type = self.parser.parse_component_type(command)
        if comp_type:
            return self._create_component(command, comp_type)
        
        # Check for layout command
        layout_type = self.parser.parse_layout(command)
        if layout_type:
            return self._apply_layout(command, layout_type)
        
        # Check for style update
        if any(word in command_lower for word in ['make', 'change', 'set', 'update', 'modify']):
            return self._update_styles(command)
        
        # Check for property command
        if any(word in command_lower for word in ['font', 'color', 'size', 'padding', 'margin', 'align']):
            return self._update_properties(command)
        
        return {
            'success': False,
            'message': 'Could not understand the command',
            'command': command
        }
    
    def _create_component(self, command: str, comp_type: ComponentType) -> Dict[str, Any]:
        """Create a new component"""
        component_id = self.generate_component_id(comp_type)
        position = self.parser.parse_position(command)
        styles = self.parser.parse_style_properties(command)
        properties = {}
        
        # Handle specific component types
        if comp_type == ComponentType.BUTTON:
            # Extract button text
            text_match = re.search(r'(?:with\s+text|saying|labeled)\s*["\']?([^"\']+)["\']?', command.lower())
            if text_match:
                properties['text'] = text_match.group(1)
            else:
                properties['text'] = 'Button'
            
            # Default button styles
            if not styles.padding:
                styles.padding = '10px 20px'
            if not styles.border_radius:
                styles.border_radius = '4px'
            if not styles.background_color:
                styles.background_color = '#007bff'
            if not styles.color:
                styles.color = '#ffffff'
            styles.border = 'none'
            styles.cursor = 'pointer'
        
        elif comp_type == ComponentType.FORM:
            # Extract form fields
            fields = self.parser.parse_form_fields(command)
            if fields:
                properties['fields'] = fields
            
            # Default form styles
            if not styles.padding:
                styles.padding = '20px'
            styles.display = 'flex'
            styles.flex_direction = 'column'
            styles.gap = '15px'
        
        elif comp_type == ComponentType.NAVIGATION:
            # Extract navigation items
            nav_items = []
            if 'home' in command.lower():
                nav_items.append({'text': 'Home', 'href': '/'})
            if 'about' in command.lower():
                nav_items.append({'text': 'About', 'href': '/about'})
            if 'contact' in command.lower():
                nav_items.append({'text': 'Contact', 'href': '/contact'})
            if 'services' in command.lower():
                nav_items.append({'text': 'Services', 'href': '/services'})
            
            if not nav_items:
                nav_items = [
                    {'text': 'Home', 'href': '/'},
                    {'text': 'About', 'href': '/about'},
                    {'text': 'Contact', 'href': '/contact'}
                ]
            
            properties['items'] = nav_items
            
            # Default nav styles
            styles.display = 'flex'
            styles.justify_content = 'space-between'
            styles.align_items = 'center'
            styles.padding = '15px 30px'
            if not styles.background_color:
                styles.background_color = '#333333'
            if not styles.color:
                styles.color = '#ffffff'
        
        elif comp_type == ComponentType.GRID:
            # Extract column count
            col_match = re.search(r'(\d+)[\s-]?column', command.lower())
            if col_match:
                properties['columns'] = int(col_match.group(1))
            else:
                properties['columns'] = 3
            
            styles.display = 'grid'
            styles.gap = '20px'
        
        elif comp_type == ComponentType.CARD:
            # Default card styles
            if not styles.padding:
                styles.padding = '20px'
            if not styles.border_radius:
                styles.border_radius = '8px'
            if not styles.box_shadow:
                styles.box_shadow = '0 2px 4px rgba(0,0,0,0.1)'
            if not styles.background_color:
                styles.background_color = '#ffffff'
        
        # Create component
        component = Component(
            id=component_id,
            type=comp_type,
            properties=properties,
            styles=styles,
            position=position
        )
        
        self.components[component_id] = component
        self.selected_component_id = component_id
        
        return {
            'success': True,
            'action': 'create_component',
            'component': component.to_dict(),
            'message': f'Created {comp_type.value} component'
        }
    
    def _update_styles(self, command: str) -> Dict[str, Any]:
        """Update styles of selected component"""
        if not self.selected_component_id:
            return {
                'success': False,
                'message': 'No component selected'
            }
        
        component = self.components[self.selected_component_id]
        new_styles = self.parser.parse_style_properties(command)
        
        # Update component styles
        for key, value in new_styles.__dict__.items():
            if value is not None:
                setattr(component.styles, key, value)
        
        return {
            'success': True,
            'action': 'update_styles',
            'component_id': self.selected_component_id,
            'styles': component.styles.to_css(),
            'message': 'Updated component styles'
        }
    
    def _update_properties(self, command: str) -> Dict[str, Any]:
        """Update properties based on command"""
        if not self.selected_component_id:
            return {
                'success': False,
                'message': 'No component selected'
            }
        
        component = self.components[self.selected_component_id]
        new_styles = self.parser.parse_style_properties(command)
        
        # Update specific properties
        updates = {}
        
        for key, value in new_styles.__dict__.items():
            if value is not None:
                setattr(component.styles, key, value)
                updates[key] = value
        
        return {
            'success': True,
            'action': 'update_properties',
            'component_id': self.selected_component_id,
            'updates': updates,
            'message': 'Updated component properties'
        }
    
    def _apply_layout(self, command: str, layout_type: LayoutType) -> Dict[str, Any]:
        """Apply layout to components"""
        if len(self.components) < 2:
            return {
                'success': False,
                'message': 'Need at least 2 components to apply layout'
            }
        
        # Create container
        container_id = self.generate_component_id(ComponentType.CONTAINER)
        container_styles = StyleProperties()
        
        if layout_type == LayoutType.GRID:
            container_styles.display = 'grid'
            # Extract column count
            col_match = re.search(r'(\d+)[\s-]?column', command.lower())
            if col_match:
                cols = int(col_match.group(1))
                container_styles.grid_template_columns = f'repeat({cols}, 1fr)'
            else:
                container_styles.grid_template_columns = 'repeat(auto-fit, minmax(200px, 1fr))'
            container_styles.gap = '20px'
        
        elif layout_type == LayoutType.VERTICAL:
            container_styles.display = 'flex'
            container_styles.flex_direction = 'column'
            container_styles.gap = '15px'
        
        elif layout_type == LayoutType.HORIZONTAL:
            container_styles.display = 'flex'
            container_styles.flex_direction = 'row'
            container_styles.gap = '15px'
        
        elif layout_type == LayoutType.FLEX:
            container_styles.display = 'flex'
            container_styles.flex_wrap = 'wrap'
            container_styles.gap = '15px'
        
        container = Component(
            id=container_id,
            type=ComponentType.CONTAINER,
            styles=container_styles
        )
        
        # Move existing components into container
        for comp_id, comp in self.components.items():
            if comp.parent_id is None:
                comp.parent_id = container_id
                container.children.append(comp)
        
        self.components[container_id] = container
        
        return {
            'success': True,
            'action': 'apply_layout',
            'layout_type': layout_type.value,
            'container_id': container_id,
            'message': f'Applied {layout_type.value} layout'
        }
    
    def select_component(self, component_id: str) -> Dict[str, Any]:
        """Select a component for editing"""
        if component_id in self.components:
            self.selected_component_id = component_id
            return {
                'success': True,
                'action': 'select_component',
                'component_id': component_id,
                'message': f'Selected component {component_id}'
            }
        return {
            'success': False,
            'message': f'Component {component_id} not found'
        }
    
    def get_design_tree(self) -> Dict[str, Any]:
        """Get the complete design tree"""
        root_components = [
            comp.to_dict() for comp in self.components.values()
            if comp.parent_id is None
        ]
        
        return {
            'success': True,
            'action': 'get_design_tree',
            'components': root_components,
            'selected_id': self.selected_component_id
        }
    
    def generate_html(self) -> str:
        """Generate HTML from components"""
        html_parts = []
        
        def render_component(comp: Component, indent: int = 0) -> str:
            indent_str = '  ' * indent
            
            # Generate HTML tag
            if comp.type == ComponentType.BUTTON:
                tag = 'button'
            elif comp.type == ComponentType.FORM:
                tag = 'form'
            elif comp.type == ComponentType.INPUT:
                tag = 'input'
            elif comp.type == ComponentType.NAVIGATION:
                tag = 'nav'
            elif comp.type == ComponentType.CONTAINER:
                tag = 'div'
            elif comp.type == ComponentType.TEXT:
                tag = 'p'
            elif comp.type == ComponentType.HEADER:
                tag = 'header'
            elif comp.type == ComponentType.FOOTER:
                tag = 'footer'
            else:
                tag = 'div'
            
            # Generate style string
            style_dict = comp.styles.to_css()
            style_str = '; '.join([f'{k}: {v}' for k, v in style_dict.items()])
            
            # Generate attributes
            attrs = [f'id="{comp.id}"']
            if style_str:
                attrs.append(f'style="{style_str}"')
            
            # Add type-specific attributes
            if comp.type == ComponentType.INPUT and 'type' in comp.properties:
                attrs.append(f'type="{comp.properties["type"]}"')
                if 'placeholder' in comp.properties:
                    attrs.append(f'placeholder="{comp.properties["placeholder"]}"')
            
            attr_str = ' '.join(attrs)
            
            # Generate content
            if comp.type == ComponentType.BUTTON and 'text' in comp.properties:
                content = comp.properties['text']
            elif comp.type == ComponentType.FORM and 'fields' in comp.properties:
                # Generate form fields
                field_html = []
                for field in comp.properties['fields']:
                    field_html.append(
                        f'{indent_str}  <input type="{field["type"]}" '
                        f'name="{field["name"]}" '
                        f'placeholder="{field.get("placeholder", "")}" />'
                    )
                content = '\n' + '\n'.join(field_html) + '\n' + indent_str
            elif comp.type == ComponentType.NAVIGATION and 'items' in comp.properties:
                # Generate nav items
                nav_html = []
                for item in comp.properties['items']:
                    nav_html.append(
                        f'{indent_str}  <a href="{item["href"]}">{item["text"]}</a>'
                    )
                content = '\n' + '\n'.join(nav_html) + '\n' + indent_str
            elif comp.children:
                # Render children
                child_html = []
                for child in comp.children:
                    child_html.append(render_component(child, indent + 1))
                content = '\n' + '\n'.join(child_html) + '\n' + indent_str
            else:
                content = ''
            
            # Self-closing tags
            if tag in ['input', 'img', 'br', 'hr']:
                return f'{indent_str}<{tag} {attr_str} />'
            else:
                return f'{indent_str}<{tag} {attr_str}>{content}</{tag}>'
        
        # Render root components
        for comp in self.components.values():
            if comp.parent_id is None:
                html_parts.append(render_component(comp))
        
        return '\n'.join(html_parts)
    
    def generate_css(self) -> str:
        """Generate CSS from components"""
        css_parts = []
        
        for comp in self.components.values():
            style_dict = comp.styles.to_css()
            if style_dict:
                css_rule = f'#{comp.id} {{\n'
                for prop, value in style_dict.items():
                    css_rule += f'  {prop}: {value};\n'
                css_rule += '}'
                css_parts.append(css_rule)
        
        return '\n\n'.join(css_parts)


class VoiceDesignSystem:
    """Main voice-to-design system"""
    
    def __init__(self):
        self.processor = VoiceCommandProcessor()
        self.command_history: List[Tuple[str, Dict[str, Any]]] = []
    
    def process_voice_command(self, command: str) -> Dict[str, Any]:
        """Process a voice command and return result"""
        logger.info(f"Processing command: {command}")
        
        # Process the command
        result = self.processor.process_design_command(command)
        
        # Add to history
        self.command_history.append((command, result))
        
        # Add additional data
        result['html'] = self.processor.generate_html()
        result['css'] = self.processor.generate_css()
        result['design_tree'] = self.processor.get_design_tree()
        
        logger.info(f"Command result: {result['message']}")
        return result
    
    def undo_last_command(self) -> Dict[str, Any]:
        """Undo the last command"""
        if not self.command_history:
            return {
                'success': False,
                'message': 'No commands to undo'
            }
        
        # Remove last command
        last_command = self.command_history.pop()
        
        # TODO: Implement proper undo functionality
        # For now, just return the previous state
        
        return {
            'success': True,
            'action': 'undo',
            'undone_command': last_command[0],
            'message': 'Command undone'
        }
    
    def get_command_history(self) -> List[Dict[str, Any]]:
        """Get command history"""
        return [
            {
                'command': cmd,
                'result': result
            }
            for cmd, result in self.command_history
        ]
    
    def clear_design(self) -> Dict[str, Any]:
        """Clear all components"""
        self.processor.components.clear()
        self.processor.selected_component_id = None
        self.command_history.clear()
        
        return {
            'success': True,
            'action': 'clear_design',
            'message': 'Design cleared'
        }
    
    def export_design(self, format: str = 'html') -> Dict[str, Any]:
        """Export the design in specified format"""
        if format == 'html':
            html = self.processor.generate_html()
            css = self.processor.generate_css()
            
            full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice Design Export</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        {css}
    </style>
</head>
<body>
    {html}
</body>
</html>"""
            
            return {
                'success': True,
                'action': 'export_design',
                'format': format,
                'content': full_html,
                'message': 'Design exported as HTML'
            }
        
        elif format == 'json':
            design_data = {
                'components': [comp.to_dict() for comp in self.processor.components.values()],
                'command_history': self.get_command_history()
            }
            
            return {
                'success': True,
                'action': 'export_design',
                'format': format,
                'content': json.dumps(design_data, indent=2),
                'message': 'Design exported as JSON'
            }
        
        else:
            return {
                'success': False,
                'message': f'Unsupported export format: {format}'
            }


# Example usage and testing
if __name__ == "__main__":
    # Create voice design system
    vds = VoiceDesignSystem()
    
    # Test commands
    test_commands = [
        "Add a button to the center",
        "Make it blue with rounded corners",
        "Create a navigation bar at the top",
        "Add a form with email and password fields",
        "Create a two-column layout",
        "Add a card with 20 pixels of padding",
        "Make the font larger",
        "Change the color to red",
        "Center align the text",
        "Stack them vertically",
        "Make it responsive"
    ]
    
    print("NEXUS Voice-to-Design System Demo")
    print("-" * 50)
    
    for command in test_commands:
        print(f"\nCommand: {command}")
        result = vds.process_voice_command(command)
        print(f"Result: {result['message']}")
        if result['success']:
            print(f"Action: {result['action']}")
    
    print("\n" + "-" * 50)
    print("Generated HTML:")
    print(vds.processor.generate_html())
    
    print("\n" + "-" * 50)
    print("Generated CSS:")
    print(vds.processor.generate_css())
    
    # Export design
    export_result = vds.export_design('html')
    with open('voice_design_export.html', 'w') as f:
        f.write(export_result['content'])
    print("\nDesign exported to voice_design_export.html")