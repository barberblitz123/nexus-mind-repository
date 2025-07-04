#!/usr/bin/env python3
"""
NEXUS Vision Commands - Vision-based development commands
Enables visual-driven development and debugging
"""

import asyncio
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
import cv2
import numpy as np
from dataclasses import dataclass
from PIL import Image

from nexus_vision_engine import NexusVisionEngine, VisionResult
from nexus_vision_analyzer import NexusVisionAnalyzer, DesignPattern, ColorPalette

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VisionCommand:
    """Vision-based command"""
    name: str
    description: str
    handler: Callable
    requires_selection: bool = False
    output_type: str = 'code'  # code, analysis, file

class NexusVisionCommands:
    """Vision-based command system for development"""
    
    def __init__(self, vision_engine: Optional[NexusVisionEngine] = None,
                 vision_analyzer: Optional[NexusVisionAnalyzer] = None):
        """Initialize command system"""
        self.engine = vision_engine or NexusVisionEngine()
        self.analyzer = vision_analyzer or NexusVisionAnalyzer(self.engine)
        self.commands = self._register_commands()
        self.workspace_dir = Path("vision_workspace")
        self.workspace_dir.mkdir(exist_ok=True)
        self.template_cache = {}
        
    def _register_commands(self) -> Dict[str, VisionCommand]:
        """Register all vision commands"""
        return {
            'implement_design': VisionCommand(
                name='implement_design',
                description='Convert UI mockup to code',
                handler=self.implement_design_from_mockup,
                output_type='code'
            ),
            'fix_error': VisionCommand(
                name='fix_error',
                description='Debug and fix error from screenshot',
                handler=self.fix_error_from_screenshot,
                output_type='code'
            ),
            'create_similar': VisionCommand(
                name='create_similar',
                description='Create component similar to screenshot',
                handler=self.create_similar_component,
                output_type='code'
            ),
            'analyze_ui': VisionCommand(
                name='analyze_ui',
                description='Analyze UI/UX and provide insights',
                handler=self.analyze_ui_comprehensive,
                output_type='analysis'
            ),
            'extract_text': VisionCommand(
                name='extract_text',
                description='Extract all text from image',
                handler=self.extract_text_from_image,
                output_type='text'
            ),
            'diagram_to_code': VisionCommand(
                name='diagram_to_code',
                description='Convert diagram/flowchart to code',
                handler=self.convert_diagram_to_code,
                output_type='code'
            ),
            'visual_debug': VisionCommand(
                name='visual_debug',
                description='Visual debugging assistance',
                handler=self.visual_debugging_assistant,
                output_type='analysis'
            ),
            'extract_design_system': VisionCommand(
                name='extract_design_system',
                description='Extract complete design system',
                handler=self.extract_design_system_command,
                output_type='file'
            ),
            'compare_designs': VisionCommand(
                name='compare_designs',
                description='Compare two designs/screenshots',
                handler=self.compare_designs,
                requires_selection=True,
                output_type='analysis'
            ),
            'accessibility_audit': VisionCommand(
                name='accessibility_audit',
                description='Perform accessibility audit',
                handler=self.accessibility_audit,
                output_type='analysis'
            )
        }
    
    async def execute_command(self, command_name: str, image_path: str,
                            options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a vision command"""
        if command_name not in self.commands:
            return {
                'success': False,
                'error': f'Unknown command: {command_name}'
            }
        
        command = self.commands[command_name]
        
        try:
            # Execute command
            result = await command.handler(image_path, options or {})
            
            return {
                'success': True,
                'command': command_name,
                'output_type': command.output_type,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def implement_design_from_mockup(self, image_path: str, 
                                         options: Dict[str, Any]) -> Dict[str, Any]:
        """Convert UI mockup to implementation code"""
        framework = options.get('framework', 'react')
        style_system = options.get('style_system', 'css')
        
        # Analyze the mockup
        vision_result = await self.engine.analyze_image(image_path,
            f"Analyze this UI mockup and describe the components, layout, and styling needed to implement it in {framework}")
        
        # Extract design patterns
        patterns = await self.analyzer.analyze_ui_patterns(image_path)
        
        # Extract colors
        palette = await self.analyzer.analyze_color_palette(image_path)
        
        # Generate code based on framework
        if framework == 'react':
            code = await self._generate_react_code(vision_result, patterns, palette, style_system)
        elif framework == 'vue':
            code = await self._generate_vue_code(vision_result, patterns, palette, style_system)
        elif framework == 'html':
            code = await self._generate_html_code(vision_result, patterns, palette, style_system)
        else:
            code = {'error': f'Unsupported framework: {framework}'}
        
        return {
            'code': code,
            'design_analysis': {
                'patterns': [p.pattern_type for p in patterns],
                'colors': {
                    'primary': palette.primary,
                    'secondary': palette.secondary,
                    'background': palette.background,
                    'text': palette.text
                }
            }
        }
    
    async def _generate_react_code(self, vision_result: VisionResult, 
                                 patterns: List[DesignPattern],
                                 palette: ColorPalette,
                                 style_system: str) -> Dict[str, str]:
        """Generate React component code"""
        # Extract component structure from vision analysis
        analysis = vision_result.content
        
        # Component template
        component_name = "GeneratedComponent"
        
        # Generate styles
        if style_system == 'styled-components':
            styles = self._generate_styled_components(patterns, palette)
        elif style_system == 'tailwind':
            styles = self._generate_tailwind_classes(patterns, palette)
        else:
            styles = self._generate_css_modules(patterns, palette)
        
        # Build component code
        react_code = f"""import React from 'react';
{styles['imports']}

const {component_name} = () => {{
  return (
    <div className="{styles.get('container_class', 'container')}">
"""
        
        # Add components based on patterns
        for pattern in patterns:
            if pattern.pattern_type == 'navbar':
                react_code += f"""      <nav className="{styles.get('navbar_class', 'navbar')}">
        <div className="nav-brand">Logo</div>
        <ul className="nav-links">
          <li><a href="#">Home</a></li>
          <li><a href="#">About</a></li>
          <li><a href="#">Contact</a></li>
        </ul>
      </nav>
"""
            elif pattern.pattern_type == 'button':
                react_code += f"""      <button className="{styles.get('button_class', 'button')}">
        Click Me
      </button>
"""
            elif pattern.pattern_type == 'card':
                react_code += f"""      <div className="{styles.get('card_class', 'card')}">
        <h3>Card Title</h3>
        <p>Card content goes here</p>
      </div>
"""
        
        react_code += """    </div>
  );
};

export default """ + component_name + ";"
        
        # Generate complete file structure
        return {
            'component.jsx': react_code,
            'styles': styles.get('styles_file', ''),
            'index.js': f"export {{ default as {component_name} }} from './{component_name}';"
        }
    
    def _generate_styled_components(self, patterns: List[DesignPattern], 
                                  palette: ColorPalette) -> Dict[str, str]:
        """Generate styled-components styles"""
        imports = "import styled from 'styled-components';"
        
        styles = f"""
const Container = styled.div`
  background-color: {palette.background};
  color: {palette.text};
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
`;

const Button = styled.button`
  background-color: {palette.primary};
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  
  &:hover {{
    opacity: 0.9;
  }}
`;

const Card = styled.div`
  background-color: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin: 16px 0;
`;
"""
        
        return {
            'imports': imports,
            'styles_file': styles,
            'container_class': 'Container',
            'button_class': 'Button',
            'card_class': 'Card'
        }
    
    def _generate_tailwind_classes(self, patterns: List[DesignPattern], 
                                 palette: ColorPalette) -> Dict[str, str]:
        """Generate Tailwind CSS classes"""
        # Map colors to Tailwind classes
        color_map = {
            '#ffffff': 'white',
            '#000000': 'black',
            '#f3f4f6': 'gray-100',
            '#e5e7eb': 'gray-200'
        }
        
        bg_class = color_map.get(palette.background, 'white')
        text_class = color_map.get(palette.text, 'black')
        
        return {
            'imports': '',
            'container_class': f'min-h-screen bg-{bg_class} text-{text_class}',
            'button_class': 'px-6 py-3 bg-blue-500 text-white rounded hover:bg-blue-600',
            'card_class': 'bg-white rounded-lg shadow-md p-6 my-4',
            'navbar_class': 'bg-white shadow-sm px-6 py-4 flex justify-between items-center'
        }
    
    def _generate_css_modules(self, patterns: List[DesignPattern], 
                            palette: ColorPalette) -> Dict[str, str]:
        """Generate CSS modules"""
        css = f"""
.container {{
  background-color: {palette.background};
  color: {palette.text};
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}}

.button {{
  background-color: {palette.primary};
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}}

.button:hover {{
  opacity: 0.9;
}}

.card {{
  background-color: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin: 16px 0;
}}

.navbar {{
  background-color: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}}
"""
        
        return {
            'imports': "import styles from './styles.module.css';",
            'styles_file': css,
            'container_class': 'styles.container',
            'button_class': 'styles.button',
            'card_class': 'styles.card',
            'navbar_class': 'styles.navbar'
        }
    
    async def _generate_vue_code(self, vision_result: VisionResult, 
                               patterns: List[DesignPattern],
                               palette: ColorPalette,
                               style_system: str) -> Dict[str, str]:
        """Generate Vue component code"""
        # Similar to React but with Vue syntax
        vue_code = """<template>
  <div class="container">
"""
        
        for pattern in patterns:
            if pattern.pattern_type == 'navbar':
                vue_code += """    <nav class="navbar">
      <div class="nav-brand">Logo</div>
      <ul class="nav-links">
        <li><a href="#">Home</a></li>
        <li><a href="#">About</a></li>
        <li><a href="#">Contact</a></li>
      </ul>
    </nav>
"""
            elif pattern.pattern_type == 'button':
                vue_code += """    <button class="button" @click="handleClick">
      Click Me
    </button>
"""
        
        vue_code += """  </div>
</template>

<script>
export default {
  name: 'GeneratedComponent',
  methods: {
    handleClick() {
      console.log('Button clicked');
    }
  }
}
</script>

<style scoped>
""" + self._generate_css_modules(patterns, palette)['styles_file'] + """
</style>"""
        
        return {
            'Component.vue': vue_code
        }
    
    async def _generate_html_code(self, vision_result: VisionResult, 
                                patterns: List[DesignPattern],
                                palette: ColorPalette,
                                style_system: str) -> Dict[str, str]:
        """Generate plain HTML/CSS code"""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Page</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
"""
        
        for pattern in patterns:
            if pattern.pattern_type == 'navbar':
                html += """        <nav class="navbar">
            <div class="nav-brand">Logo</div>
            <ul class="nav-links">
                <li><a href="#">Home</a></li>
                <li><a href="#">About</a></li>
                <li><a href="#">Contact</a></li>
            </ul>
        </nav>
"""
        
        html += """    </div>
</body>
</html>"""
        
        css = self._generate_css_modules(patterns, palette)['styles_file']
        
        return {
            'index.html': html,
            'styles.css': css
        }
    
    async def fix_error_from_screenshot(self, image_path: str, 
                                      options: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze error screenshot and provide fix"""
        context = options.get('context', {})
        
        # Analyze error screenshot
        prompt = """Analyze this error screenshot:
        1. Identify the error message and type
        2. Understand the context and stack trace
        3. Determine the root cause
        4. Provide a detailed fix with code
        5. Suggest preventive measures"""
        
        vision_result = await self.engine.analyze_image(image_path, prompt)
        
        # Extract error details
        error_analysis = self._parse_error_analysis(vision_result.content)
        
        # Generate fix based on error type
        fix = await self._generate_error_fix(error_analysis, context)
        
        return {
            'error_analysis': error_analysis,
            'fix': fix,
            'preventive_measures': error_analysis.get('preventive_measures', [])
        }
    
    def _parse_error_analysis(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Parse error analysis from vision result"""
        analysis = {
            'error_type': 'unknown',
            'error_message': '',
            'stack_trace': [],
            'root_cause': '',
            'affected_files': []
        }
        
        # Extract from vision analysis
        description = content.get('description', '')
        code_blocks = content.get('code_blocks', [])
        
        # Parse error type from description
        if 'TypeError' in description:
            analysis['error_type'] = 'TypeError'
        elif 'SyntaxError' in description:
            analysis['error_type'] = 'SyntaxError'
        elif 'ReferenceError' in description:
            analysis['error_type'] = 'ReferenceError'
        
        # Extract error message and stack trace from code blocks
        for block in code_blocks:
            code = block.get('code', '')
            if 'at ' in code and ':' in code:  # Likely stack trace
                analysis['stack_trace'] = code.split('\n')
        
        return analysis
    
    async def _generate_error_fix(self, error_analysis: Dict[str, Any], 
                                context: Dict[str, Any]) -> Dict[str, str]:
        """Generate fix for the error"""
        error_type = error_analysis.get('error_type', 'unknown')
        
        fixes = {}
        
        if error_type == 'TypeError':
            fixes['explanation'] = "Type error detected. This usually occurs when trying to access properties of null/undefined or using wrong types."
            fixes['code'] = """// Add null checks
if (object && object.property) {
    // Safe to access
    const value = object.property;
}

// Or use optional chaining
const value = object?.property;

// For function calls
if (typeof myFunction === 'function') {
    myFunction();
}"""
        
        elif error_type == 'SyntaxError':
            fixes['explanation'] = "Syntax error found. Check for missing brackets, quotes, or semicolons."
            fixes['code'] = """// Common syntax fixes:
// 1. Missing closing bracket
function myFunction() {
    // code here
} // <- Make sure this is present

// 2. Missing quotes
const message = "Hello World"; // <- Both quotes needed

// 3. Invalid JSON
const validJson = {
    "key": "value", // <- Use double quotes in JSON
    "number": 123
};"""
        
        return fixes
    
    async def create_similar_component(self, image_path: str, 
                                     options: Dict[str, Any]) -> Dict[str, Any]:
        """Create component similar to screenshot"""
        framework = options.get('framework', 'react')
        component_name = options.get('name', 'SimilarComponent')
        
        # Analyze the reference component
        vision_result = await self.engine.analyze_image(image_path,
            "Analyze this UI component in detail: structure, styling, interactions, and behavior")
        
        # Extract patterns and design
        patterns = await self.analyzer.analyze_ui_patterns(image_path)
        palette = await self.analyzer.analyze_color_palette(image_path)
        
        # Extract any visible text/content
        text_data = await self.engine.extract_text_with_layout(image_path)
        
        # Generate similar component
        if framework == 'react':
            code = await self._generate_similar_react_component(
                vision_result, patterns, palette, text_data, component_name
            )
        else:
            code = {'error': f'Framework {framework} not yet supported'}
        
        return {
            'code': code,
            'analysis': {
                'detected_features': self._extract_component_features(vision_result),
                'patterns': [p.pattern_type for p in patterns],
                'colors_used': {
                    'primary': palette.primary,
                    'secondary': palette.secondary
                }
            }
        }
    
    async def _generate_similar_react_component(self, vision_result: VisionResult,
                                             patterns: List[DesignPattern],
                                             palette: ColorPalette,
                                             text_data: Dict[str, Any],
                                             component_name: str) -> Dict[str, str]:
        """Generate React component similar to reference"""
        # Extract component structure
        features = self._extract_component_features(vision_result)
        
        # Build component
        component = f"""import React, {{ useState }} from 'react';
import './styles.css';

const {component_name} = ({{ """
        
        # Add props based on detected features
        props = []
        if 'title' in features:
            props.append('title = "Title"')
        if 'content' in features:
            props.append('content = "Content"')
        if 'onClick' in features:
            props.append('onClick')
        
        component += ', '.join(props) + """ }) => {
  const [state, setState] = useState({});
  
  return (
    <div className="component-container">
"""
        
        # Add elements based on patterns
        for pattern in patterns:
            if pattern.pattern_type == 'card':
                component += """      <div className="card">
        {title && <h3>{title}</h3>}
        {content && <p>{content}</p>}
      </div>
"""
        
        component += """    </div>
  );
};

export default """ + component_name + ";"
        
        # Generate styles
        styles = f""".component-container {{
  padding: 16px;
}}

.card {{
  background-color: {palette.background};
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}}

.card h3 {{
  color: {palette.text};
  margin: 0 0 12px 0;
  font-size: 18px;
  font-weight: 600;
}}

.card p {{
  color: {palette.text};
  margin: 0;
  line-height: 1.5;
}}"""
        
        return {
            f'{component_name}.jsx': component,
            'styles.css': styles
        }
    
    def _extract_component_features(self, vision_result: VisionResult) -> List[str]:
        """Extract component features from vision analysis"""
        features = []
        
        content = vision_result.content
        description = content.get('description', '').lower()
        
        # Detect common features
        if 'title' in description or 'heading' in description:
            features.append('title')
        if 'button' in description or 'click' in description:
            features.append('onClick')
        if 'text' in description or 'content' in description:
            features.append('content')
        if 'image' in description or 'icon' in description:
            features.append('image')
        if 'list' in description:
            features.append('list')
        if 'form' in description or 'input' in description:
            features.append('form')
        
        return features
    
    async def analyze_ui_comprehensive(self, image_path: str, 
                                     options: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive UI/UX analysis"""
        # Perform multiple analyses
        patterns = await self.analyzer.analyze_ui_patterns(image_path)
        palette = await self.analyzer.analyze_color_palette(image_path)
        accessibility = await self.analyzer.analyze_accessibility(image_path)
        performance = await self.analyzer.analyze_performance_metrics(image_path)
        
        # Get AI insights
        vision_result = await self.engine.analyze_image(image_path,
            """Analyze this UI and provide:
            1. Overall design quality assessment
            2. User experience insights
            3. Visual hierarchy analysis
            4. Consistency evaluation
            5. Improvement suggestions""")
        
        return {
            'design_patterns': {
                'detected': [p.pattern_type for p in patterns],
                'count': len(patterns),
                'confidence': np.mean([p.confidence for p in patterns])
            },
            'color_analysis': {
                'palette': {
                    'primary': palette.primary,
                    'secondary': palette.secondary,
                    'accent': palette.accent,
                    'background': palette.background,
                    'text': palette.text
                },
                'semantic_colors': palette.semantic
            },
            'accessibility': {
                'issues': [
                    {
                        'type': issue.issue_type,
                        'severity': issue.severity,
                        'description': issue.description,
                        'suggestion': issue.suggestion
                    }
                    for issue in accessibility
                ],
                'score': max(0, 100 - len(accessibility) * 10)
            },
            'performance': performance,
            'ai_insights': vision_result.content
        }
    
    async def extract_text_from_image(self, image_path: str, 
                                    options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract all text from image with layout preservation"""
        preserve_layout = options.get('preserve_layout', True)
        output_format = options.get('format', 'text')
        
        # Extract text with layout
        text_data = await self.engine.extract_text_with_layout(image_path)
        
        if output_format == 'json':
            return {
                'text': text_data['full_text'],
                'blocks': text_data['blocks'],
                'word_count': len(text_data['full_text'].split()),
                'line_count': len(text_data['full_text'].split('\n'))
            }
        elif output_format == 'markdown':
            # Convert to markdown
            markdown = self._convert_to_markdown(text_data)
            return {
                'markdown': markdown,
                'text': text_data['full_text']
            }
        else:
            return {
                'text': text_data['full_text']
            }
    
    def _convert_to_markdown(self, text_data: Dict[str, Any]) -> str:
        """Convert extracted text to markdown format"""
        markdown = ""
        
        # Process blocks
        for block_num in sorted(text_data['blocks'].keys()):
            block = text_data['blocks'][block_num]
            
            for par_num in sorted(block.keys()):
                paragraph = block[par_num]
                
                # Estimate if it's a heading based on size
                if paragraph and paragraph[0]['height'] > 20:
                    # Likely a heading
                    text = ' '.join(item['text'] for item in paragraph if item['text'].strip())
                    markdown += f"## {text}\n\n"
                else:
                    # Regular paragraph
                    text = ' '.join(item['text'] for item in paragraph if item['text'].strip())
                    if text:
                        markdown += f"{text}\n\n"
        
        return markdown.strip()
    
    async def convert_diagram_to_code(self, image_path: str, 
                                    options: Dict[str, Any]) -> Dict[str, Any]:
        """Convert diagram/flowchart to code"""
        output_format = options.get('format', 'python')
        diagram_type = options.get('type', 'auto')
        
        # Analyze diagram
        diagram_data = await self.engine.analyze_diagram(image_path)
        
        # Get AI interpretation
        prompt = f"""Analyze this diagram and convert it to {output_format} code:
        1. Identify the diagram type (flowchart, sequence, class, etc.)
        2. Extract all nodes/components and their relationships
        3. Generate equivalent {output_format} code structure
        4. Include comments explaining the logic
        5. Suggest best practices for implementation"""
        
        vision_result = await self.engine.analyze_image(image_path, prompt)
        
        # Generate code based on diagram type
        if diagram_type == 'auto':
            diagram_type = self._detect_diagram_type(diagram_data, vision_result)
        
        if diagram_type == 'flowchart':
            code = self._generate_flowchart_code(diagram_data, output_format)
        elif diagram_type == 'class':
            code = self._generate_class_diagram_code(diagram_data, output_format)
        elif diagram_type == 'sequence':
            code = self._generate_sequence_diagram_code(diagram_data, output_format)
        else:
            # Use AI-generated code
            code = self._extract_code_from_vision_result(vision_result)
        
        return {
            'diagram_type': diagram_type,
            'code': code,
            'diagram_analysis': diagram_data,
            'ai_interpretation': vision_result.content
        }
    
    def _detect_diagram_type(self, diagram_data: Dict[str, Any], 
                           vision_result: VisionResult) -> str:
        """Detect type of diagram"""
        description = vision_result.content.get('description', '').lower()
        
        if 'flowchart' in description or 'flow' in description:
            return 'flowchart'
        elif 'class' in description or 'uml' in description:
            return 'class'
        elif 'sequence' in description:
            return 'sequence'
        elif 'state' in description:
            return 'state'
        
        # Analyze shapes
        shapes = diagram_data.get('shapes', [])
        if shapes:
            rectangles = sum(1 for s in shapes if s['type'] == 'rectangle')
            circles = sum(1 for s in shapes if s['type'] == 'circle')
            
            if circles > rectangles:
                return 'state'
            else:
                return 'flowchart'
        
        return 'flowchart'
    
    def _generate_flowchart_code(self, diagram_data: Dict[str, Any], 
                                language: str) -> Dict[str, str]:
        """Generate code from flowchart"""
        if language == 'python':
            code = """# Generated from flowchart
def process_flow():
    \"\"\"Main process flow\"\"\"
    
    # Start
    print("Process started")
    
"""
            
            # Add nodes as functions
            for i, shape in enumerate(diagram_data.get('shapes', [])):
                if shape['type'] == 'rectangle':
                    code += f"""    # Step {i+1}
    result_{i} = process_step_{i}()
    
"""
            
            code += """    # End
    print("Process completed")
    return result

# Define individual steps
"""
            
            for i, shape in enumerate(diagram_data.get('shapes', [])):
                if shape['type'] == 'rectangle':
                    code += f"""
def process_step_{i}():
    \"\"\"Process step {i+1}\"\"\"
    # TODO: Implement step logic
    return True
"""
            
            return {'main.py': code}
        
        return {'error': f'Language {language} not supported yet'}
    
    def _generate_class_diagram_code(self, diagram_data: Dict[str, Any], 
                                   language: str) -> Dict[str, str]:
        """Generate code from class diagram"""
        if language == 'python':
            code = """# Generated from class diagram
from abc import ABC, abstractmethod
from typing import List, Optional

"""
            
            # Generate classes based on rectangles
            for i, shape in enumerate(diagram_data.get('shapes', [])):
                if shape['type'] == 'rectangle':
                    code += f"""
class Class{i}:
    \"\"\"Generated class {i}\"\"\"
    
    def __init__(self):
        self.attribute1 = None
        self.attribute2 = None
    
    def method1(self):
        \"\"\"Method 1\"\"\"
        pass
    
    def method2(self):
        \"\"\"Method 2\"\"\"
        pass
"""
            
            return {'classes.py': code}
        
        return {'error': f'Language {language} not supported yet'}
    
    def _generate_sequence_diagram_code(self, diagram_data: Dict[str, Any], 
                                      language: str) -> Dict[str, str]:
        """Generate code from sequence diagram"""
        if language == 'python':
            code = """# Generated from sequence diagram
import asyncio
from typing import Any

class Actor:
    \"\"\"Base actor class\"\"\"
    def __init__(self, name: str):
        self.name = name
    
    async def send_message(self, target: 'Actor', message: str, data: Any = None):
        \"\"\"Send message to another actor\"\"\"
        print(f"{self.name} -> {target.name}: {message}")
        return await target.receive_message(self, message, data)
    
    async def receive_message(self, sender: 'Actor', message: str, data: Any = None):
        \"\"\"Receive message from another actor\"\"\"
        # Override in subclasses
        return None

# Generated actors
"""
            
            # Add actors based on shapes
            actor_count = len([s for s in diagram_data.get('shapes', []) if s['type'] == 'rectangle'])
            
            for i in range(actor_count):
                code += f"""
class Actor{i}(Actor):
    def __init__(self):
        super().__init__("Actor{i}")
    
    async def receive_message(self, sender: Actor, message: str, data: Any = None):
        # Process message
        if message == "request":
            return await self.handle_request(sender, data)
        return None
    
    async def handle_request(self, sender: Actor, data: Any):
        # TODO: Implement request handling
        return {{"status": "success"}}
"""
            
            return {'sequence.py': code}
        
        return {'error': f'Language {language} not supported yet'}
    
    def _extract_code_from_vision_result(self, vision_result: VisionResult) -> Dict[str, str]:
        """Extract code from vision result"""
        code_blocks = vision_result.content.get('code_blocks', [])
        
        if code_blocks:
            # Use the first code block
            return {
                'generated_code.py': code_blocks[0].get('code', '# No code generated')
            }
        
        return {
            'generated_code.py': '# Could not generate code from diagram'
        }
    
    async def visual_debugging_assistant(self, image_path: str, 
                                       options: Dict[str, Any]) -> Dict[str, Any]:
        """Provide visual debugging assistance"""
        issue_type = options.get('issue', 'general')
        
        # Analyze screenshot for debugging
        prompt = f"""Analyze this screenshot for debugging:
        1. Identify any visual issues or anomalies
        2. Look for error messages or warnings
        3. Check UI element alignment and spacing
        4. Identify potential rendering issues
        5. Suggest debugging steps for {issue_type} issues"""
        
        vision_result = await self.engine.analyze_image(image_path, prompt)
        
        # Perform specific analyses
        patterns = await self.analyzer.analyze_ui_patterns(image_path)
        
        # Look for common issues
        issues = self._detect_visual_issues(image_path, patterns)
        
        # Generate debugging steps
        debugging_steps = self._generate_debugging_steps(issue_type, issues, vision_result)
        
        return {
            'detected_issues': issues,
            'debugging_steps': debugging_steps,
            'ai_analysis': vision_result.content,
            'recommendations': self._generate_recommendations(issues)
        }
    
    def _detect_visual_issues(self, image_path: str, patterns: List[DesignPattern]) -> List[Dict[str, Any]]:
        """Detect common visual issues"""
        issues = []
        
        # Load image for analysis
        image = cv2.imread(image_path)
        
        # Check for alignment issues
        pattern_positions = []
        for pattern in patterns:
            for bounds in pattern.examples:
                pattern_positions.append(bounds)
        
        # Check horizontal alignment
        x_positions = [p[0] for p in pattern_positions]
        if x_positions:
            x_counts = Counter(x_positions)
            misaligned = [x for x, count in x_counts.items() if count == 1]
            if misaligned:
                issues.append({
                    'type': 'alignment',
                    'description': 'Elements may be misaligned horizontally',
                    'severity': 'medium'
                })
        
        # Check for overlapping elements
        for i, bounds1 in enumerate(pattern_positions):
            for bounds2 in pattern_positions[i+1:]:
                if self._check_overlap(bounds1, bounds2):
                    issues.append({
                        'type': 'overlap',
                        'description': 'Overlapping UI elements detected',
                        'severity': 'high',
                        'location': bounds1
                    })
        
        return issues
    
    def _check_overlap(self, bounds1: Tuple[int, int, int, int], 
                      bounds2: Tuple[int, int, int, int]) -> bool:
        """Check if two bounding boxes overlap"""
        x1_min, y1_min, x1_max, y1_max = bounds1
        x2_min, y2_min, x2_max, y2_max = bounds2
        
        return not (x1_max < x2_min or x2_max < x1_min or 
                   y1_max < y2_min or y2_max < y1_min)
    
    def _generate_debugging_steps(self, issue_type: str, issues: List[Dict], 
                                vision_result: VisionResult) -> List[str]:
        """Generate debugging steps based on issue type"""
        steps = []
        
        if issue_type == 'layout':
            steps.extend([
                "1. Check CSS box model properties (margin, padding, border)",
                "2. Verify flexbox/grid container settings",
                "3. Inspect computed styles in DevTools",
                "4. Check for conflicting CSS rules",
                "5. Verify responsive breakpoints"
            ])
        elif issue_type == 'rendering':
            steps.extend([
                "1. Check browser console for errors",
                "2. Verify all assets are loading correctly",
                "3. Check for CSS specificity issues",
                "4. Test in different browsers",
                "5. Disable browser extensions"
            ])
        elif issue_type == 'interaction':
            steps.extend([
                "1. Check event listeners in DevTools",
                "2. Verify JavaScript is loading correctly",
                "3. Check for event propagation issues",
                "4. Test with console.log statements",
                "5. Check for z-index stacking issues"
            ])
        
        # Add specific steps based on detected issues
        for issue in issues:
            if issue['type'] == 'alignment':
                steps.append("- Use CSS Grid or Flexbox for consistent alignment")
            elif issue['type'] == 'overlap':
                steps.append("- Check position and z-index properties")
        
        return steps
    
    def _generate_recommendations(self, issues: List[Dict]) -> List[str]:
        """Generate recommendations based on issues"""
        recommendations = []
        
        issue_types = [issue['type'] for issue in issues]
        
        if 'alignment' in issue_types:
            recommendations.append("Consider using a grid system for consistent layout")
        
        if 'overlap' in issue_types:
            recommendations.append("Review z-index stacking and position properties")
        
        if len(issues) > 3:
            recommendations.append("Consider refactoring the component structure")
        
        return recommendations
    
    async def extract_design_system_command(self, image_path: str, 
                                          options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract complete design system from screenshots"""
        # Handle multiple images
        image_paths = options.get('additional_images', [])
        image_paths.insert(0, image_path)
        
        # Extract design system
        design_system = await self.analyzer.extract_design_system(image_paths)
        
        # Generate design system files
        files = self._generate_design_system_files(design_system)
        
        # Save to workspace
        output_dir = self.workspace_dir / f"design_system_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir.mkdir(exist_ok=True)
        
        for filename, content in files.items():
            with open(output_dir / filename, 'w') as f:
                f.write(content)
        
        return {
            'design_system': design_system,
            'output_directory': str(output_dir),
            'files_created': list(files.keys())
        }
    
    def _generate_design_system_files(self, design_system: Dict[str, Any]) -> Dict[str, str]:
        """Generate design system files"""
        files = {}
        
        # Generate tokens file
        tokens = {
            'colors': design_system['colors'].__dict__ if design_system['colors'] else {},
            'spacing': design_system['spacing'],
            'typography': design_system['typography']
        }
        files['tokens.json'] = json.dumps(tokens, indent=2)
        
        # Generate CSS variables
        css_vars = ":root {\n"
        if design_system['colors']:
            css_vars += f"  --color-primary: {design_system['colors'].primary};\n"
            css_vars += f"  --color-background: {design_system['colors'].background};\n"
            css_vars += f"  --color-text: {design_system['colors'].text};\n"
        
        for i, spacing in enumerate(design_system['spacing']):
            css_vars += f"  --spacing-{i}: {spacing}px;\n"
        
        css_vars += "}"
        files['variables.css'] = css_vars
        
        # Generate component library
        components = "// Component Library\n\n"
        for comp_type, variations in design_system['components'].items():
            components += f"// {comp_type.upper()} Components\n"
            for i, variant in enumerate(variations):
                components += f"// Variant {i+1}: {variant.get('properties', {})}\n\n"
        
        files['components.js'] = components
        
        return files
    
    async def compare_designs(self, image_path: str, 
                            options: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two designs/screenshots"""
        second_image = options.get('compare_with')
        if not second_image:
            return {'error': 'Second image path required for comparison'}
        
        # Perform visual diff
        diff_result = await self.analyzer.visual_diff(image_path, second_image)
        
        # Analyze design changes
        design_changes = diff_result.get('changes', [])
        
        # Generate change report
        report = self._generate_change_report(design_changes, diff_result)
        
        return {
            'similarity_score': diff_result['similarity'],
            'total_changes': diff_result['differences_count'],
            'diff_image': diff_result['diff_image'],
            'changes': design_changes,
            'report': report
        }
    
    def _generate_change_report(self, changes: List[Dict], diff_result: Dict) -> str:
        """Generate human-readable change report"""
        report = f"# Design Comparison Report\n\n"
        report += f"Similarity Score: {diff_result['similarity']:.1%}\n"
        report += f"Total Differences: {diff_result['differences_count']}\n\n"
        
        if changes:
            report += "## Changes Detected:\n\n"
            for change in changes:
                if change['type'] == 'added':
                    report += f"- Added {change['count']} {change['element']}(s)\n"
                elif change['type'] == 'removed':
                    report += f"- Removed {change['count']} {change['element']}(s)\n"
                elif change['type'] == 'color_change':
                    report += f"- Changed {change['element']} from {change['from']} to {change['to']}\n"
        
        return report
    
    async def accessibility_audit(self, image_path: str, 
                                options: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive accessibility audit"""
        # Run accessibility analysis
        issues = await self.analyzer.analyze_accessibility(image_path)
        
        # Group issues by type
        issues_by_type = defaultdict(list)
        for issue in issues:
            issues_by_type[issue.issue_type].append(issue)
        
        # Calculate accessibility score
        severity_weights = {
            'critical': 10,
            'high': 5,
            'medium': 2,
            'low': 1
        }
        
        total_penalty = sum(severity_weights.get(issue.severity, 1) for issue in issues)
        score = max(0, 100 - total_penalty)
        
        # Generate report
        report = self._generate_accessibility_report(issues_by_type, score)
        
        return {
            'score': score,
            'total_issues': len(issues),
            'issues_by_type': {
                issue_type: [
                    {
                        'severity': issue.severity,
                        'description': issue.description,
                        'suggestion': issue.suggestion,
                        'location': issue.location
                    }
                    for issue in issues_list
                ]
                for issue_type, issues_list in issues_by_type.items()
            },
            'report': report,
            'wcag_compliance': self._check_wcag_compliance(issues_by_type)
        }
    
    def _generate_accessibility_report(self, issues_by_type: Dict[str, List], 
                                     score: int) -> str:
        """Generate accessibility report"""
        report = f"# Accessibility Audit Report\n\n"
        report += f"**Overall Score: {score}/100**\n\n"
        
        if not issues_by_type:
            report += "✅ No accessibility issues detected!\n"
        else:
            report += "## Issues Found:\n\n"
            
            for issue_type, issues in issues_by_type.items():
                report += f"### {issue_type.replace('_', ' ').title()}\n\n"
                for issue in issues:
                    report += f"- **{issue.severity.upper()}**: {issue.description}\n"
                    report += f"  - Suggestion: {issue.suggestion}\n\n"
        
        report += "\n## Recommendations:\n\n"
        report += "1. Fix all critical and high severity issues first\n"
        report += "2. Test with screen readers\n"
        report += "3. Verify keyboard navigation\n"
        report += "4. Use automated testing tools\n"
        
        return report
    
    def _check_wcag_compliance(self, issues_by_type: Dict[str, List]) -> Dict[str, bool]:
        """Check WCAG compliance levels"""
        # Count critical issues
        critical_count = sum(
            1 for issues in issues_by_type.values()
            for issue in issues
            if issue.severity == 'critical'
        )
        
        high_count = sum(
            1 for issues in issues_by_type.values()
            for issue in issues
            if issue.severity == 'high'
        )
        
        return {
            'level_a': critical_count == 0,
            'level_aa': critical_count == 0 and high_count < 3,
            'level_aaa': len(issues_by_type) == 0
        }


if __name__ == "__main__":
    # Example usage
    async def main():
        commands = NexusVisionCommands()
        
        # Test implement design command
        result = await commands.execute_command(
            'implement_design',
            'mockup.png',
            {'framework': 'react', 'style_system': 'tailwind'}
        )
        
        if result['success']:
            print("Generated code:")
            print(result['result']['code'])
    
    asyncio.run(main())