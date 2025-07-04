#!/usr/bin/env python3
"""
NEXUS Documentation Generator - Omnipotent Documentation System
Automatically generates comprehensive documentation from codebases
"""

import os
import ast
import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import markdown
try:
    import pdfkit
except ImportError:
    pdfkit = None
from dataclasses import dataclass, field

from nexus_unified_tools import NEXUSToolBase
from nexus_memory_core import NexusUnifiedMemory
from nexus_memory_types import MemoryEntry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CodeEntity:
    """Represents a parsed code entity (function, class, etc.)"""
    name: str
    type: str  # 'function', 'class', 'method', 'module'
    signature: str
    docstring: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    returns: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    methods: List['CodeEntity'] = field(default_factory=list)
    attributes: List[Dict[str, str]] = field(default_factory=list)
    source_file: Optional[str] = None
    line_number: Optional[int] = None


class DocGeneratorOmnipotent(NEXUSToolBase):
    """
    NEXUS Documentation Generator with omnipotent capabilities
    Automatically generates comprehensive documentation from codebases
    """
    
    def __init__(self):
        super().__init__(
            name="DocGenerator",
            description="Omnipotent documentation generation system",
            version="1.0.0"
        )
        self.memory = NexusUnifiedMemory()
        self.parsed_entities: List[CodeEntity] = []
        self.documentation_templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, str]:
        """Load documentation templates from memory or defaults"""
        templates = {
            "api_function": """
## {name}

{signature}

{docstring}

### Parameters
{parameters}

### Returns
{returns}

### Example
```python
{example}
```
""",
            "api_class": """
## Class: {name}

{docstring}

### Constructor
{constructor}

### Attributes
{attributes}

### Methods
{methods}

### Example Usage
```python
{example}
```
""",
            "user_guide_section": """
# {title}

{description}

## Key Features
{features}

## Getting Started
{getting_started}

## Examples
{examples}
""",
            "architecture_mermaid": """
```mermaid
graph TD
    {nodes}
    {connections}
```
"""
        }
        
        # Try to load custom templates from memory
        try:
            stored_templates = self.memory.retrieve(
                query="documentation_templates",
                stage="semantic"
            )
            if stored_templates:
                templates.update(stored_templates[0].get('data', {}))
        except Exception as e:
            logger.warning(f"Could not load stored templates: {e}")
            
        return templates
    
    def parse_codebase(self, directory: str) -> List[CodeEntity]:
        """Parse all files in directory and extract code entities"""
        self.parsed_entities = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            raise ValueError(f"Directory {directory} does not exist")
        
        # Parse Python files
        for py_file in directory_path.rglob("*.py"):
            try:
                entities = self._parse_python_file(str(py_file))
                self.parsed_entities.extend(entities)
            except Exception as e:
                logger.error(f"Error parsing {py_file}: {e}")
        
        # Parse JavaScript/TypeScript files
        for js_file in directory_path.rglob("*.js"):
            try:
                entities = self._parse_javascript_file(str(js_file))
                self.parsed_entities.extend(entities)
            except Exception as e:
                logger.error(f"Error parsing {js_file}: {e}")
                
        for ts_file in directory_path.rglob("*.ts"):
            try:
                entities = self._parse_javascript_file(str(ts_file))
                self.parsed_entities.extend(entities)
            except Exception as e:
                logger.error(f"Error parsing {ts_file}: {e}")
        
        # Store parsed entities in memory
        self.memory.store(
            content={
                'parsed_entities': [self._entity_to_dict(e) for e in self.parsed_entities],
                'directory': directory,
                'timestamp': datetime.now().isoformat()
            },
            stage="semantic",
            metadata={'type': 'parsed_codebase', 'directory': directory}
        )
        
        logger.info(f"Parsed {len(self.parsed_entities)} entities from {directory}")
        return self.parsed_entities
    
    def _parse_python_file(self, file_path: str) -> List[CodeEntity]:
        """Parse a Python file using AST"""
        entities = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            return entities
        
        # Extract module docstring
        module_docstring = ast.get_docstring(tree)
        if module_docstring:
            entities.append(CodeEntity(
                name=Path(file_path).stem,
                type='module',
                signature=f"module {Path(file_path).stem}",
                docstring=module_docstring,
                source_file=file_path,
                line_number=1
            ))
        
        # Parse top-level entities
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                entity = self._parse_python_function(node, file_path)
                entities.append(entity)
            elif isinstance(node, ast.ClassDef):
                entity = self._parse_python_class(node, file_path)
                entities.append(entity)
        
        return entities
    
    def _parse_python_function(self, node: ast.FunctionDef, file_path: str) -> CodeEntity:
        """Parse a Python function definition"""
        # Extract parameters
        parameters = []
        for arg in node.args.args:
            param = {'name': arg.arg}
            # Check for type annotation
            if arg.annotation:
                param['type'] = ast.unparse(arg.annotation)
            parameters.append(param)
        
        # Extract return type
        returns = None
        if node.returns:
            returns = ast.unparse(node.returns)
        
        # Extract decorators
        decorators = []
        for decorator in node.decorator_list:
            decorators.append(ast.unparse(decorator))
        
        # Build signature
        params_str = ', '.join([p['name'] for p in parameters])
        signature = f"def {node.name}({params_str})"
        if returns:
            signature += f" -> {returns}"
        
        return CodeEntity(
            name=node.name,
            type='function',
            signature=signature,
            docstring=ast.get_docstring(node),
            parameters=parameters,
            returns=returns,
            decorators=decorators,
            source_file=file_path,
            line_number=node.lineno
        )
    
    def _parse_python_class(self, node: ast.ClassDef, file_path: str) -> CodeEntity:
        """Parse a Python class definition"""
        methods = []
        attributes = []
        
        # Parse methods and attributes
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method = self._parse_python_function(item, file_path)
                method.type = 'method'
                methods.append(method)
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                # Class attribute with type annotation
                attr = {
                    'name': item.target.id,
                    'type': ast.unparse(item.annotation) if item.annotation else 'Any'
                }
                attributes.append(attr)
        
        # Extract decorators
        decorators = []
        for decorator in node.decorator_list:
            decorators.append(ast.unparse(decorator))
        
        return CodeEntity(
            name=node.name,
            type='class',
            signature=f"class {node.name}",
            docstring=ast.get_docstring(node),
            methods=methods,
            attributes=attributes,
            decorators=decorators,
            source_file=file_path,
            line_number=node.lineno
        )
    
    def _parse_javascript_file(self, file_path: str) -> List[CodeEntity]:
        """Parse JavaScript/TypeScript file using regex patterns"""
        entities = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse functions
        function_pattern = r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\((.*?)\)(?:\s*:\s*([\w<>]+))?\s*{'
        for match in re.finditer(function_pattern, content):
            name = match.group(1)
            params = match.group(2)
            returns = match.group(3)
            
            # Extract JSDoc if present
            jsdoc_pattern = rf'/\*\*[\s\S]*?\*/\s*(?:export\s+)?(?:async\s+)?function\s+{name}'
            jsdoc_match = re.search(jsdoc_pattern, content)
            docstring = None
            if jsdoc_match:
                docstring = self._parse_jsdoc(jsdoc_match.group(0))
            
            signature = f"function {name}({params})"
            if returns:
                signature += f": {returns}"
            
            entities.append(CodeEntity(
                name=name,
                type='function',
                signature=signature,
                docstring=docstring,
                source_file=file_path
            ))
        
        # Parse classes
        class_pattern = r'(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{'
        for match in re.finditer(class_pattern, content):
            name = match.group(1)
            extends = match.group(2)
            
            signature = f"class {name}"
            if extends:
                signature += f" extends {extends}"
            
            entities.append(CodeEntity(
                name=name,
                type='class',
                signature=signature,
                source_file=file_path
            ))
        
        # Parse arrow functions assigned to variables
        arrow_pattern = r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\((.*?)\)(?:\s*:\s*([\w<>]+))?\s*=>'
        for match in re.finditer(arrow_pattern, content):
            name = match.group(1)
            params = match.group(2)
            returns = match.group(3)
            
            signature = f"const {name} = ({params})"
            if returns:
                signature += f": {returns}"
            signature += " => ..."
            
            entities.append(CodeEntity(
                name=name,
                type='function',
                signature=signature,
                source_file=file_path
            ))
        
        return entities
    
    def _parse_jsdoc(self, jsdoc_text: str) -> str:
        """Extract description from JSDoc comment"""
        lines = jsdoc_text.split('\n')
        description_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('*') and not line.startswith('* @'):
                description_lines.append(line[1:].strip())
        
        return ' '.join(description_lines)
    
    def _entity_to_dict(self, entity: CodeEntity) -> Dict[str, Any]:
        """Convert CodeEntity to dictionary for storage"""
        return {
            'name': entity.name,
            'type': entity.type,
            'signature': entity.signature,
            'docstring': entity.docstring,
            'parameters': entity.parameters,
            'returns': entity.returns,
            'decorators': entity.decorators,
            'methods': [self._entity_to_dict(m) for m in entity.methods],
            'attributes': entity.attributes,
            'source_file': entity.source_file,
            'line_number': entity.line_number
        }
    
    def generate_api_docs(self, output_file: str = "api_documentation.md") -> str:
        """Generate API documentation from parsed entities"""
        if not self.parsed_entities:
            raise ValueError("No parsed entities found. Run parse_codebase first.")
        
        sections = []
        
        # Group entities by type and module
        modules = {}
        for entity in self.parsed_entities:
            module_name = Path(entity.source_file).stem if entity.source_file else 'unknown'
            if module_name not in modules:
                modules[module_name] = []
            modules[module_name].append(entity)
        
        # Generate documentation for each module
        for module_name, entities in modules.items():
            sections.append(f"# Module: {module_name}\n")
            
            # Functions
            functions = [e for e in entities if e.type == 'function']
            if functions:
                sections.append("## Functions\n")
                for func in functions:
                    sections.append(self._generate_function_doc(func))
            
            # Classes
            classes = [e for e in entities if e.type == 'class']
            if classes:
                sections.append("## Classes\n")
                for cls in classes:
                    sections.append(self._generate_class_doc(cls))
        
        # Combine all sections
        api_docs = "\n".join(sections)
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(api_docs)
        
        # Store in memory
        self.memory.store(
            content={'api_docs': api_docs, 'file': output_file},
            stage="semantic",
            metadata={'type': 'api_documentation', 'timestamp': datetime.now().isoformat()}
        )
        
        logger.info(f"Generated API documentation: {output_file}")
        return api_docs
    
    def _generate_function_doc(self, func: CodeEntity) -> str:
        """Generate documentation for a function"""
        # Generate parameter documentation
        params_doc = []
        for param in func.parameters:
            param_str = f"- **{param['name']}**"
            if 'type' in param:
                param_str += f" (`{param['type']}`)"
            params_doc.append(param_str)
        
        # Generate example
        example = self._generate_example_for_function(func)
        
        return self.documentation_templates['api_function'].format(
            name=func.name,
            signature=f"```python\n{func.signature}\n```",
            docstring=func.docstring or "No description available.",
            parameters="\n".join(params_doc) if params_doc else "No parameters",
            returns=f"`{func.returns}`" if func.returns else "None",
            example=example
        )
    
    def _generate_class_doc(self, cls: CodeEntity) -> str:
        """Generate documentation for a class"""
        # Find constructor
        constructor = next((m for m in cls.methods if m.name == '__init__'), None)
        constructor_doc = self._generate_function_doc(constructor) if constructor else "Default constructor"
        
        # Generate attributes documentation
        attrs_doc = []
        for attr in cls.attributes:
            attrs_doc.append(f"- **{attr['name']}** (`{attr.get('type', 'Any')}`)")
        
        # Generate methods documentation
        methods_doc = []
        for method in cls.methods:
            if method.name != '__init__':
                methods_doc.append(f"### {method.name}\n{self._generate_function_doc(method)}")
        
        # Generate example
        example = self._generate_example_for_class(cls)
        
        return self.documentation_templates['api_class'].format(
            name=cls.name,
            docstring=cls.docstring or "No description available.",
            constructor=constructor_doc,
            attributes="\n".join(attrs_doc) if attrs_doc else "No attributes",
            methods="\n\n".join(methods_doc) if methods_doc else "No methods",
            example=example
        )
    
    def _generate_example_for_function(self, func: CodeEntity) -> str:
        """Generate usage example for a function"""
        # Simple example generation - can be enhanced with AI
        params = [p['name'] for p in func.parameters]
        param_values = []
        
        for param in func.parameters:
            if 'type' in param:
                if 'str' in param['type']:
                    param_values.append(f'"{param["name"]}_value"')
                elif 'int' in param['type']:
                    param_values.append('42')
                elif 'bool' in param['type']:
                    param_values.append('True')
                else:
                    param_values.append(f'{param["name"]}_value')
            else:
                param_values.append(f'{param["name"]}_value')
        
        example = f"# Example usage\nresult = {func.name}({', '.join(param_values)})"
        if func.returns:
            example += f"\nprint(result)  # Returns {func.returns}"
        
        return example
    
    def _generate_example_for_class(self, cls: CodeEntity) -> str:
        """Generate usage example for a class"""
        # Find constructor parameters
        constructor = next((m for m in cls.methods if m.name == '__init__'), None)
        
        if constructor and constructor.parameters:
            # Skip 'self' parameter
            params = constructor.parameters[1:] if constructor.parameters[0]['name'] == 'self' else constructor.parameters
            param_values = []
            
            for param in params:
                if 'type' in param:
                    if 'str' in param['type']:
                        param_values.append(f'"{param["name"]}_value"')
                    elif 'int' in param['type']:
                        param_values.append('42')
                    else:
                        param_values.append(f'{param["name"]}_value')
                else:
                    param_values.append(f'{param["name"]}_value')
            
            example = f"# Create instance\nobj = {cls.name}({', '.join(param_values)})"
        else:
            example = f"# Create instance\nobj = {cls.name}()"
        
        # Add method calls
        public_methods = [m for m in cls.methods if not m.name.startswith('_')][:3]
        for method in public_methods:
            example += f"\n\n# Call {method.name}\nobj.{method.name}()"
        
        return example
    
    def generate_user_guide(self, 
                          title: str = "User Guide",
                          description: str = "Complete guide for using this software",
                          output_file: str = "user_guide.md") -> str:
        """Generate user-facing documentation"""
        # Analyze parsed entities to understand functionality
        features = self._analyze_features()
        getting_started = self._generate_getting_started()
        examples = self._generate_user_examples()
        
        user_guide = self.documentation_templates['user_guide_section'].format(
            title=title,
            description=description,
            features=features,
            getting_started=getting_started,
            examples=examples
        )
        
        # Add architecture diagram
        architecture = self.generate_architecture_diagram()
        user_guide += f"\n\n## System Architecture\n\n{architecture}"
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(user_guide)
        
        # Store in memory
        self.memory.store(
            content={'user_guide': user_guide, 'file': output_file},
            stage="semantic",
            metadata={'type': 'user_guide', 'timestamp': datetime.now().isoformat()}
        )
        
        logger.info(f"Generated user guide: {output_file}")
        return user_guide
    
    def _analyze_features(self) -> str:
        """Analyze codebase to extract key features"""
        features = []
        
        # Group by functionality
        functionality_groups = {}
        for entity in self.parsed_entities:
            # Simple categorization based on name patterns
            if 'auth' in entity.name.lower():
                category = 'Authentication'
            elif 'db' in entity.name.lower() or 'database' in entity.name.lower():
                category = 'Database'
            elif 'api' in entity.name.lower():
                category = 'API'
            elif 'ui' in entity.name.lower() or 'view' in entity.name.lower():
                category = 'User Interface'
            else:
                category = 'Core Functionality'
            
            if category not in functionality_groups:
                functionality_groups[category] = []
            functionality_groups[category].append(entity)
        
        # Generate feature descriptions
        for category, entities in functionality_groups.items():
            feature = f"- **{category}**: "
            entity_names = [e.name for e in entities[:3]]
            feature += f"Includes {', '.join(entity_names)}"
            if len(entities) > 3:
                feature += f" and {len(entities) - 3} more components"
            features.append(feature)
        
        return "\n".join(features)
    
    def _generate_getting_started(self) -> str:
        """Generate getting started section"""
        steps = [
            "1. **Installation**: Install required dependencies",
            "2. **Configuration**: Set up your environment",
            "3. **First Run**: Execute the main application",
            "4. **Basic Usage**: Explore core features"
        ]
        
        # Look for main entry points
        main_functions = [e for e in self.parsed_entities if e.name in ['main', 'run', 'start', 'app']]
        if main_functions:
            steps.append(f"5. **Entry Point**: Run `{main_functions[0].name}()` to start")
        
        return "\n".join(steps)
    
    def _generate_user_examples(self) -> str:
        """Generate user-friendly examples"""
        examples = []
        
        # Find high-level functions/classes
        public_entities = [e for e in self.parsed_entities if not e.name.startswith('_')]
        
        # Generate examples for top 3 most important looking entities
        for entity in public_entities[:3]:
            if entity.docstring:
                example = f"### {entity.name}\n\n{entity.docstring}\n\n"
                if entity.type == 'function':
                    example += self._generate_example_for_function(entity)
                else:
                    example += self._generate_example_for_class(entity)
                examples.append(example)
        
        return "\n\n".join(examples)
    
    def generate_architecture_diagram(self, output_file: str = "architecture.md") -> str:
        """Create visual architecture diagrams using mermaid"""
        # Analyze relationships between modules
        modules = {}
        relationships = []
        
        for entity in self.parsed_entities:
            if entity.source_file:
                module = Path(entity.source_file).stem
                if module not in modules:
                    modules[module] = {
                        'classes': [],
                        'functions': [],
                        'imports': []
                    }
                
                if entity.type == 'class':
                    modules[module]['classes'].append(entity.name)
                elif entity.type == 'function':
                    modules[module]['functions'].append(entity.name)
        
        # Generate mermaid diagram
        nodes = []
        for module, content in modules.items():
            node_label = f"{module}"
            if content['classes']:
                node_label += f"\\n[{len(content['classes'])} classes]"
            if content['functions']:
                node_label += f"\\n[{len(content['functions'])} functions]"
            nodes.append(f'    {module}["{node_label}"]')
        
        # Detect relationships (simplified - can be enhanced)
        connections = []
        module_names = list(modules.keys())
        for i, module1 in enumerate(module_names):
            for module2 in module_names[i+1:]:
                # Check if modules might be related
                if any(keyword in module1 and keyword in module2 
                      for keyword in ['api', 'db', 'auth', 'core', 'utils']):
                    connections.append(f'    {module1} --> {module2}')
        
        diagram = self.documentation_templates['architecture_mermaid'].format(
            nodes='\n'.join(nodes),
            connections='\n'.join(connections) if connections else '    %% No connections detected'
        )
        
        # Save diagram
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Architecture Diagram\n\n{diagram}")
        
        logger.info(f"Generated architecture diagram: {output_file}")
        return diagram
    
    def sync_documentation(self, watch_directory: str, output_directory: str = "docs"):
        """Keep documentation in sync with code changes"""
        logger.info(f"Starting documentation sync for {watch_directory}")
        
        # Create output directory if it doesn't exist
        Path(output_directory).mkdir(exist_ok=True)
        
        # Initial generation
        self.parse_codebase(watch_directory)
        
        api_docs_path = os.path.join(output_directory, "api_reference.md")
        user_guide_path = os.path.join(output_directory, "user_guide.md")
        architecture_path = os.path.join(output_directory, "architecture.md")
        
        self.generate_api_docs(api_docs_path)
        self.generate_user_guide(output_file=user_guide_path)
        self.generate_architecture_diagram(architecture_path)
        
        # Convert to HTML
        self.convert_to_html(api_docs_path, os.path.join(output_directory, "api_reference.html"))
        self.convert_to_html(user_guide_path, os.path.join(output_directory, "user_guide.html"))
        
        logger.info(f"Documentation synchronized to {output_directory}")
        
        # Store sync info in memory
        self.memory.store(
            content={
                'watch_directory': watch_directory,
                'output_directory': output_directory,
                'last_sync': datetime.now().isoformat(),
                'generated_files': [api_docs_path, user_guide_path, architecture_path]
            },
            stage="episodic",
            metadata={'type': 'documentation_sync', 'directory': watch_directory}
        )
    
    def convert_to_html(self, markdown_file: str, output_file: str):
        """Convert Markdown to HTML"""
        with open(markdown_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Convert to HTML with extensions
        html_content = markdown.markdown(
            md_content,
            extensions=['extra', 'codehilite', 'toc', 'tables']
        )
        
        # Wrap in HTML template
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{Path(markdown_file).stem}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        .codehilite {{ background: #f4f4f4; padding: 10px; border-radius: 5px; }}
        h1, h2, h3 {{ color: #333; }}
        .mermaid {{ text-align: center; }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{startOnLoad:true}});</script>
</head>
<body>
{html_content}
</body>
</html>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        logger.info(f"Converted to HTML: {output_file}")
    
    def convert_to_pdf(self, html_file: str, output_file: str):
        """Convert HTML to PDF"""
        if not pdfkit:
            logger.warning("pdfkit not available. Install with: pip install pdfkit")
            logger.info("Also requires wkhtmltopdf: sudo apt-get install wkhtmltopdf")
            return
        
        try:
            pdfkit.from_file(html_file, output_file)
            logger.info(f"Converted to PDF: {output_file}")
        except Exception as e:
            logger.error(f"Error converting to PDF: {e}")
            logger.info("Make sure wkhtmltopdf is installed: sudo apt-get install wkhtmltopdf")
    
    def generate_from_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Generate documentation from a custom template"""
        if template_name not in self.documentation_templates:
            raise ValueError(f"Template {template_name} not found")
        
        template = self.documentation_templates[template_name]
        return template.format(**context)
    
    def add_custom_template(self, name: str, template: str):
        """Add a custom documentation template"""
        self.documentation_templates[name] = template
        
        # Store in memory
        self.memory.store(
            content={'template_name': name, 'template': template},
            stage="semantic",
            metadata={'type': 'documentation_template', 'name': name}
        )
        
        logger.info(f"Added custom template: {name}")
    
    def execute_specialty(self, **kwargs) -> Dict[str, Any]:
        """Execute documentation generation specialty - Enhanced MANUS integration"""
        action = kwargs.get('action', 'generate')
        directory = kwargs.get('directory', '.')
        output_dir = kwargs.get('output_dir', 'docs')
        
        try:
            if action == 'generate':
                # Full documentation generation
                self.parse_codebase(directory)
                
                # Create output directory
                Path(output_dir).mkdir(exist_ok=True)
                
                # Generate all documentation types
                api_docs_path = os.path.join(output_dir, "api_reference.md")
                user_guide_path = os.path.join(output_dir, "user_guide.md")
                architecture_path = os.path.join(output_dir, "architecture.md")
                
                api_docs = self.generate_api_docs(api_docs_path)
                user_guide = self.generate_user_guide(output_file=user_guide_path)
                architecture = self.generate_architecture_diagram(architecture_path)
                
                # Convert to HTML
                self.convert_to_html(api_docs_path, os.path.join(output_dir, "api_reference.html"))
                self.convert_to_html(user_guide_path, os.path.join(output_dir, "user_guide.html"))
                
                return {
                    "success": True,
                    "action": "full_documentation_generation",
                    "files_generated": [api_docs_path, user_guide_path, architecture_path],
                    "entities_parsed": len(self.parsed_entities),
                    "summary": f"Generated complete documentation for {len(self.parsed_entities)} code entities"
                }
            
            elif action == 'api_only':
                # Generate only API documentation
                self.parse_codebase(directory)
                Path(output_dir).mkdir(exist_ok=True)
                
                api_docs_path = os.path.join(output_dir, "api_reference.md")
                api_docs = self.generate_api_docs(api_docs_path)
                
                return {
                    "success": True,
                    "action": "api_documentation_generation",
                    "file_generated": api_docs_path,
                    "entities_parsed": len(self.parsed_entities),
                    "summary": f"Generated API documentation for {len(self.parsed_entities)} code entities"
                }
            
            elif action == 'user_guide':
                # Generate only user guide
                self.parse_codebase(directory)
                Path(output_dir).mkdir(exist_ok=True)
                
                user_guide_path = os.path.join(output_dir, "user_guide.md")
                user_guide = self.generate_user_guide(
                    title=kwargs.get('title', 'User Guide'),
                    description=kwargs.get('description', 'Complete guide for using this software'),
                    output_file=user_guide_path
                )
                
                return {
                    "success": True,
                    "action": "user_guide_generation",
                    "file_generated": user_guide_path,
                    "summary": "Generated comprehensive user guide"
                }
            
            elif action == 'architecture':
                # Generate only architecture diagram
                self.parse_codebase(directory)
                Path(output_dir).mkdir(exist_ok=True)
                
                architecture_path = os.path.join(output_dir, "architecture.md")
                architecture = self.generate_architecture_diagram(architecture_path)
                
                return {
                    "success": True,
                    "action": "architecture_diagram_generation",
                    "file_generated": architecture_path,
                    "summary": "Generated system architecture diagram"
                }
            
            elif action == 'sync':
                # Sync documentation with codebase
                self.sync_documentation(directory, output_dir)
                
                return {
                    "success": True,
                    "action": "documentation_sync",
                    "watch_directory": directory,
                    "output_directory": output_dir,
                    "summary": "Documentation synchronized with codebase"
                }
            
            elif action == 'parse_only':
                # Just parse the codebase and return entities
                entities = self.parse_codebase(directory)
                
                # Group entities by type
                by_type = {'modules': 0, 'classes': 0, 'functions': 0, 'methods': 0}
                for entity in entities:
                    if entity.type in by_type:
                        by_type[entity.type] += 1
                    elif entity.type == 'method':
                        by_type['methods'] += 1
                
                return {
                    "success": True,
                    "action": "codebase_parsing",
                    "entities_found": len(entities),
                    "breakdown": by_type,
                    "summary": f"Parsed {len(entities)} code entities from {directory}"
                }
            
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            self.logger.error(f"Documentation generator specialty execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": action
            }


def main():
    """Example usage of the Documentation Generator"""
    generator = DocGeneratorOmnipotent()
    
    # Parse a codebase
    print("Parsing codebase...")
    entities = generator.parse_codebase(".")
    print(f"Found {len(entities)} code entities")
    
    # Generate documentation
    print("\nGenerating API documentation...")
    generator.generate_api_docs("docs/api_reference.md")
    
    print("\nGenerating user guide...")
    generator.generate_user_guide(
        title="NEXUS Documentation System",
        description="Omnipotent documentation generator for modern codebases"
    )
    
    print("\nGenerating architecture diagram...")
    generator.generate_architecture_diagram()
    
    print("\nSyncing documentation...")
    generator.sync_documentation(".", "docs")
    
    print("\nDocumentation generation complete!")


if __name__ == "__main__":
    main()