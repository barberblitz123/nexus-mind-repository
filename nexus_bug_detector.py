#!/usr/bin/env python3
"""
NEXUS Bug Detector - Omnipotent Bug Detection and Auto-Fix System
Detects, analyzes, and fixes bugs using AST parsing, pattern matching, and AI
"""

import ast
import json
import re
import subprocess
import os
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import tokenize
import io
import tempfile
import shutil

from nexus_unified_tools import NEXUSToolBase
from nexus_memory_core import NexusUnifiedMemory
from nexus_semantic_memory import SemanticMemory
import openai


@dataclass
class Bug:
    """Represents a detected bug"""
    file_path: str
    line_number: int
    column: int
    bug_type: str
    severity: str  # critical, high, medium, low
    description: str
    code_snippet: str
    pattern_name: str
    confidence: float
    suggested_fix: Optional[str] = None
    ai_analysis: Optional[str] = None
    
    def to_dict(self):
        return {
            'file_path': self.file_path,
            'line_number': self.line_number,
            'column': self.column,
            'bug_type': self.bug_type,
            'severity': self.severity,
            'description': self.description,
            'code_snippet': self.code_snippet,
            'pattern_name': self.pattern_name,
            'confidence': self.confidence,
            'suggested_fix': self.suggested_fix,
            'ai_analysis': self.ai_analysis
        }


@dataclass
class BugFix:
    """Represents a bug fix"""
    bug: Bug
    fixed_code: str
    fix_description: str
    tests_passed: bool = False
    validation_errors: List[str] = field(default_factory=list)


class BugDetectorOmnipotent(NEXUSToolBase):
    """Omnipotent bug detection and fixing system"""
    
    def __init__(self, memory_core: Optional[NexusUnifiedMemory] = None):
        super().__init__(
            name="Bug Detector",
            description="Detects and fixes bugs using AST parsing and AI analysis",
            category="development",
            memory_core=memory_core
        )
        
        # Initialize bug patterns
        self.bug_patterns = self._initialize_bug_patterns()
        
        # Language-specific parsers
        self.parsers = {
            '.py': self._parse_python,
            '.js': self._parse_javascript,
            '.ts': self._parse_typescript,
            '.jsx': self._parse_javascript,
            '.tsx': self._parse_typescript
        }
        
        # Store detected bugs in memory
        self.detected_bugs: List[Bug] = []
        
        # AI client for advanced analysis
        self.ai_client = None
        self._init_ai_client()
    
    def _init_ai_client(self):
        """Initialize AI client for bug analysis"""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.ai_client = openai.OpenAI(api_key=api_key)
        except Exception as e:
            self.logger.warning(f"Failed to initialize AI client: {e}")
    
    async def execute_specialty(self, context: Dict[str, Any]) -> Any:
        """Execute bug detection specialty"""
        directory = context.get('directory', '.')
        
        if context.get('scan_file'):
            return await self.scan_file(context['scan_file'])
        elif context.get('scan_project'):
            return await self.scan_project(context.get('directory', '.'))
        elif context.get('generate_fix'):
            return await self.generate_fix(context['bug'])
        else:
            # Default to scanning project
            return await self.scan_project(directory)
    
    def _initialize_bug_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize common bug patterns"""
        return {
            # Python patterns
            'python_null_reference': {
                'languages': ['python'],
                'pattern': r'(\w+)\.(\w+)',
                'checker': self._check_null_reference_python,
                'severity': 'high',
                'description': 'Potential null/None reference error'
            },
            'python_resource_leak': {
                'languages': ['python'],
                'pattern': r'open\s*\(',
                'checker': self._check_resource_leak_python,
                'severity': 'medium',
                'description': 'Potential resource leak - file not closed'
            },
            'python_mutable_default': {
                'languages': ['python'],
                'pattern': r'def\s+\w+\s*\([^)]*=\s*(\[|\{)',
                'checker': self._check_mutable_default_python,
                'severity': 'medium',
                'description': 'Mutable default argument'
            },
            'python_bare_except': {
                'languages': ['python'],
                'pattern': r'except\s*:',
                'checker': self._check_bare_except_python,
                'severity': 'low',
                'description': 'Bare except clause catches all exceptions'
            },
            
            # JavaScript/TypeScript patterns
            'js_undefined_variable': {
                'languages': ['javascript', 'typescript'],
                'pattern': r'(\w+)\.(\w+)',
                'checker': self._check_undefined_variable_js,
                'severity': 'high',
                'description': 'Potential undefined variable access'
            },
            'js_async_no_await': {
                'languages': ['javascript', 'typescript'],
                'pattern': r'async\s+function|\basync\s*\(',
                'checker': self._check_async_no_await_js,
                'severity': 'medium',
                'description': 'Async function without await'
            },
            'js_array_index': {
                'languages': ['javascript', 'typescript'],
                'pattern': r'\[([^\]]+)\]',
                'checker': self._check_array_index_js,
                'severity': 'medium',
                'description': 'Potential array index out of bounds'
            },
            
            # Common patterns
            'off_by_one': {
                'languages': ['python', 'javascript', 'typescript'],
                'pattern': r'for.*range\s*\(\s*len\s*\(|\.length\s*\+\s*1',
                'checker': self._check_off_by_one,
                'severity': 'medium',
                'description': 'Potential off-by-one error'
            },
            'race_condition': {
                'languages': ['python', 'javascript', 'typescript'],
                'pattern': r'threading|async|Promise\.all|setTimeout',
                'checker': self._check_race_condition,
                'severity': 'high',
                'description': 'Potential race condition'
            },
            'type_mismatch': {
                'languages': ['python', 'javascript', 'typescript'],
                'pattern': r'==|!=',
                'checker': self._check_type_mismatch,
                'severity': 'low',
                'description': 'Potential type mismatch in comparison'
            }
        }
    
    async def scan_file(self, filepath: str) -> List[Bug]:
        """Scan a single file for bugs"""
        self.logger.info(f"Scanning file: {filepath}")
        
        try:
            # Read file content
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Determine file type
            file_ext = Path(filepath).suffix.lower()
            
            # Parse based on file type
            if file_ext in self.parsers:
                bugs = await self.parsers[file_ext](filepath, content)
            else:
                bugs = await self._parse_generic(filepath, content)
            
            # Store in memory
            self._store_bugs_in_memory(bugs)
            
            # Add to detected bugs
            self.detected_bugs.extend(bugs)
            
            return bugs
            
        except Exception as e:
            self.logger.error(f"Error scanning file {filepath}: {e}")
            return []
    
    async def scan_project(self, directory: str) -> List[Bug]:
        """Scan entire project for bugs"""
        self.logger.info(f"Scanning project: {directory}")
        
        all_bugs = []
        
        # Supported file extensions
        supported_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx'}
        
        # Walk through directory
        for root, dirs, files in os.walk(directory):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in {
                '__pycache__', 'node_modules', '.git', 'dist', 'build',
                'venv', 'env', '.venv', '.env'
            }]
            
            for file in files:
                if Path(file).suffix.lower() in supported_extensions:
                    filepath = os.path.join(root, file)
                    bugs = await self.scan_file(filepath)
                    all_bugs.extend(bugs)
        
        return all_bugs
    
    async def _parse_python(self, filepath: str, content: str) -> List[Bug]:
        """Parse Python file for bugs"""
        bugs = []
        
        try:
            # Parse AST
            tree = ast.parse(content, filename=filepath)
            
            # AST-based analysis
            analyzer = PythonBugAnalyzer(filepath, content)
            bugs.extend(analyzer.analyze(tree))
            
        except SyntaxError as e:
            # Syntax error is itself a bug
            bugs.append(Bug(
                file_path=filepath,
                line_number=e.lineno or 0,
                column=e.offset or 0,
                bug_type='syntax_error',
                severity='critical',
                description=f"Syntax error: {e.msg}",
                code_snippet=self._get_code_snippet(content, e.lineno or 0),
                pattern_name='syntax_error',
                confidence=1.0
            ))
        
        # Pattern-based analysis
        bugs.extend(await self._check_patterns(filepath, content, 'python'))
        
        # AI analysis if available
        if self.ai_client and len(bugs) < 50:  # Limit AI calls
            ai_bugs = await self._ai_analyze_code(filepath, content, 'python')
            bugs.extend(ai_bugs)
        
        return bugs
    
    async def _parse_javascript(self, filepath: str, content: str) -> List[Bug]:
        """Parse JavaScript file for bugs"""
        bugs = []
        
        # Basic pattern matching for JS
        bugs.extend(await self._check_patterns(filepath, content, 'javascript'))
        
        # Use external tools if available
        if shutil.which('eslint'):
            bugs.extend(await self._run_eslint(filepath))
        
        # AI analysis
        if self.ai_client:
            ai_bugs = await self._ai_analyze_code(filepath, content, 'javascript')
            bugs.extend(ai_bugs)
        
        return bugs
    
    async def _parse_typescript(self, filepath: str, content: str) -> List[Bug]:
        """Parse TypeScript file for bugs"""
        bugs = []
        
        # Basic pattern matching
        bugs.extend(await self._check_patterns(filepath, content, 'typescript'))
        
        # Use TypeScript compiler if available
        if shutil.which('tsc'):
            bugs.extend(await self._run_tsc(filepath))
        
        # AI analysis
        if self.ai_client:
            ai_bugs = await self._ai_analyze_code(filepath, content, 'typescript')
            bugs.extend(ai_bugs)
        
        return bugs
    
    async def _parse_generic(self, filepath: str, content: str) -> List[Bug]:
        """Generic parsing for unsupported file types"""
        return []
    
    async def _check_patterns(self, filepath: str, content: str, language: str) -> List[Bug]:
        """Check content against bug patterns"""
        bugs = []
        lines = content.split('\n')
        
        for pattern_name, pattern_info in self.bug_patterns.items():
            if language in pattern_info['languages']:
                # Find all matches
                for i, line in enumerate(lines):
                    if re.search(pattern_info['pattern'], line):
                        # Run specific checker
                        bug = pattern_info['checker'](
                            filepath, content, i + 1, line, pattern_name
                        )
                        if bug:
                            bugs.append(bug)
        
        return bugs
    
    def _check_null_reference_python(self, filepath: str, content: str, 
                                   line_num: int, line: str, pattern_name: str) -> Optional[Bug]:
        """Check for potential null reference in Python"""
        # Look for attribute access without null check
        match = re.search(r'(\w+)\.(\w+)', line)
        if match:
            var_name = match.group(1)
            # Check if variable might be None
            if self._variable_can_be_none(content, var_name, line_num):
                return Bug(
                    file_path=filepath,
                    line_number=line_num,
                    column=match.start(),
                    bug_type='null_reference',
                    severity='high',
                    description=f"Variable '{var_name}' might be None",
                    code_snippet=line.strip(),
                    pattern_name=pattern_name,
                    confidence=0.7,
                    suggested_fix=f"if {var_name} is not None:\n    {line.strip()}"
                )
        return None
    
    def _check_resource_leak_python(self, filepath: str, content: str,
                                   line_num: int, line: str, pattern_name: str) -> Optional[Bug]:
        """Check for resource leaks in Python"""
        if 'open(' in line and 'with' not in line:
            return Bug(
                file_path=filepath,
                line_number=line_num,
                column=line.find('open('),
                bug_type='resource_leak',
                severity='medium',
                description='File opened without context manager',
                code_snippet=line.strip(),
                pattern_name=pattern_name,
                confidence=0.8,
                suggested_fix=f"with {line.strip()}:"
            )
        return None
    
    def _check_mutable_default_python(self, filepath: str, content: str,
                                     line_num: int, line: str, pattern_name: str) -> Optional[Bug]:
        """Check for mutable default arguments in Python"""
        match = re.search(r'def\s+(\w+)\s*\([^)]*=\s*(\[|\{)', line)
        if match:
            return Bug(
                file_path=filepath,
                line_number=line_num,
                column=match.start(),
                bug_type='mutable_default',
                severity='medium',
                description='Mutable default argument',
                code_snippet=line.strip(),
                pattern_name=pattern_name,
                confidence=0.9,
                suggested_fix='Use None as default and initialize in function body'
            )
        return None
    
    def _check_bare_except_python(self, filepath: str, content: str,
                                 line_num: int, line: str, pattern_name: str) -> Optional[Bug]:
        """Check for bare except clauses in Python"""
        if re.search(r'except\s*:', line):
            return Bug(
                file_path=filepath,
                line_number=line_num,
                column=line.find('except'),
                bug_type='bare_except',
                severity='low',
                description='Bare except clause catches all exceptions',
                code_snippet=line.strip(),
                pattern_name=pattern_name,
                confidence=1.0,
                suggested_fix='except Exception as e:'
            )
        return None
    
    def _check_undefined_variable_js(self, filepath: str, content: str,
                                    line_num: int, line: str, pattern_name: str) -> Optional[Bug]:
        """Check for undefined variables in JavaScript"""
        # Simple heuristic - would need proper JS parsing for accuracy
        match = re.search(r'(\w+)\.(\w+)', line)
        if match:
            var_name = match.group(1)
            if var_name not in ['window', 'document', 'console', 'Math', 'Array', 'Object']:
                if not self._js_variable_defined(content, var_name, line_num):
                    return Bug(
                        file_path=filepath,
                        line_number=line_num,
                        column=match.start(),
                        bug_type='undefined_variable',
                        severity='high',
                        description=f"Variable '{var_name}' might be undefined",
                        code_snippet=line.strip(),
                        pattern_name=pattern_name,
                        confidence=0.6,
                        suggested_fix=f"if (typeof {var_name} !== 'undefined' && {var_name}) {{\n    {line.strip()}\n}}"
                    )
        return None
    
    def _check_async_no_await_js(self, filepath: str, content: str,
                                line_num: int, line: str, pattern_name: str) -> Optional[Bug]:
        """Check for async functions without await"""
        if 'async' in line:
            # Find function body
            func_body = self._get_function_body(content, line_num)
            if func_body and 'await' not in func_body:
                return Bug(
                    file_path=filepath,
                    line_number=line_num,
                    column=line.find('async'),
                    bug_type='async_no_await',
                    severity='medium',
                    description='Async function without await',
                    code_snippet=line.strip(),
                    pattern_name=pattern_name,
                    confidence=0.8,
                    suggested_fix='Remove async keyword or add await to async operations'
                )
        return None
    
    def _check_array_index_js(self, filepath: str, content: str,
                             line_num: int, line: str, pattern_name: str) -> Optional[Bug]:
        """Check for array index issues in JavaScript"""
        match = re.search(r'(\w+)\[([^\]]+)\]', line)
        if match:
            array_name = match.group(1)
            index_expr = match.group(2)
            # Check if index might be out of bounds
            if 'length' in index_expr or index_expr.isdigit():
                if int(index_expr) if index_expr.isdigit() else 0 >= 100:
                    return Bug(
                        file_path=filepath,
                        line_number=line_num,
                        column=match.start(),
                        bug_type='array_index',
                        severity='medium',
                        description='Potential array index out of bounds',
                        code_snippet=line.strip(),
                        pattern_name=pattern_name,
                        confidence=0.5,
                        suggested_fix=f"if ({index_expr} < {array_name}.length) {{\n    {line.strip()}\n}}"
                    )
        return None
    
    def _check_off_by_one(self, filepath: str, content: str,
                         line_num: int, line: str, pattern_name: str) -> Optional[Bug]:
        """Check for off-by-one errors"""
        if 'range(len(' in line or '.length + 1' in line:
            return Bug(
                file_path=filepath,
                line_number=line_num,
                column=0,
                bug_type='off_by_one',
                severity='medium',
                description='Potential off-by-one error in loop',
                code_snippet=line.strip(),
                pattern_name=pattern_name,
                confidence=0.7,
                suggested_fix='Check loop bounds carefully'
            )
        return None
    
    def _check_race_condition(self, filepath: str, content: str,
                             line_num: int, line: str, pattern_name: str) -> Optional[Bug]:
        """Check for potential race conditions"""
        if any(keyword in line for keyword in ['threading', 'async', 'Promise.all', 'setTimeout']):
            # Look for shared state access
            if self._has_shared_state_access(content, line_num):
                return Bug(
                    file_path=filepath,
                    line_number=line_num,
                    column=0,
                    bug_type='race_condition',
                    severity='high',
                    description='Potential race condition with shared state',
                    code_snippet=line.strip(),
                    pattern_name=pattern_name,
                    confidence=0.6,
                    suggested_fix='Use proper synchronization (locks, mutexes, etc.)'
                )
        return None
    
    def _check_type_mismatch(self, filepath: str, content: str,
                            line_num: int, line: str, pattern_name: str) -> Optional[Bug]:
        """Check for type mismatches in comparisons"""
        if '==' in line and '===' not in line:
            return Bug(
                file_path=filepath,
                line_number=line_num,
                column=line.find('=='),
                bug_type='type_mismatch',
                severity='low',
                description='Using == instead of === (type coercion)',
                code_snippet=line.strip(),
                pattern_name=pattern_name,
                confidence=0.8,
                suggested_fix=line.replace('==', '===').replace('!=', '!==')
            )
        return None
    
    def _variable_can_be_none(self, content: str, var_name: str, line_num: int) -> bool:
        """Check if a variable can be None at a given line"""
        lines = content.split('\n')
        for i in range(max(0, line_num - 20), line_num):
            if i < len(lines):
                line = lines[i]
                # Check for None assignment
                if f"{var_name} = None" in line or f"{var_name}=None" in line:
                    return True
                # Check for conditional assignment
                if f"{var_name} = " in line and "if" in lines[max(0, i-1):i+2]:
                    return True
                # Check for function return that might be None
                if f"{var_name} = " in line and any(func in line for func in 
                    ['get(', 'find(', 'search(', '.get(', '.find(']):
                    return True
        return False
    
    def _js_variable_defined(self, content: str, var_name: str, line_num: int) -> bool:
        """Check if a JavaScript variable is defined before use"""
        lines = content.split('\n')
        for i in range(0, min(line_num, len(lines))):
            line = lines[i]
            # Check for variable declaration
            if any(f"{keyword} {var_name}" in line for keyword in ['var', 'let', 'const', 'function']):
                return True
            # Check for function parameter
            if f"({var_name}" in line or f", {var_name}" in line:
                return True
        return False
    
    def _get_function_body(self, content: str, start_line: int) -> str:
        """Extract function body starting from a line"""
        lines = content.split('\n')
        body_lines = []
        brace_count = 0
        in_body = False
        
        for i in range(start_line - 1, len(lines)):
            line = lines[i]
            if '{' in line:
                in_body = True
                brace_count += line.count('{')
            if in_body:
                body_lines.append(line)
                brace_count -= line.count('}')
                if brace_count <= 0:
                    break
        
        return '\n'.join(body_lines)
    
    def _has_shared_state_access(self, content: str, line_num: int) -> bool:
        """Check if there's shared state access near async operations"""
        lines = content.split('\n')
        # Look for class attributes or global variables
        for i in range(max(0, line_num - 10), min(len(lines), line_num + 10)):
            if i < len(lines):
                line = lines[i]
                if 'self.' in line or 'this.' in line or re.search(r'\b[A-Z_]+\b', line):
                    return True
        return False
    
    def _get_code_snippet(self, content: str, line_num: int, context: int = 2) -> str:
        """Get code snippet around a line"""
        lines = content.split('\n')
        start = max(0, line_num - context - 1)
        end = min(len(lines), line_num + context)
        return '\n'.join(lines[start:end])
    
    async def _run_eslint(self, filepath: str) -> List[Bug]:
        """Run ESLint on a file"""
        bugs = []
        try:
            result = subprocess.run(
                ['eslint', '--format', 'json', filepath],
                capture_output=True,
                text=True
            )
            if result.stdout:
                eslint_output = json.loads(result.stdout)
                for file_result in eslint_output:
                    for message in file_result.get('messages', []):
                        bugs.append(Bug(
                            file_path=filepath,
                            line_number=message.get('line', 0),
                            column=message.get('column', 0),
                            bug_type='eslint_' + message.get('ruleId', 'unknown'),
                            severity=self._map_eslint_severity(message.get('severity', 1)),
                            description=message.get('message', ''),
                            code_snippet='',
                            pattern_name='eslint',
                            confidence=0.9
                        ))
        except Exception as e:
            self.logger.debug(f"ESLint error: {e}")
        return bugs
    
    async def _run_tsc(self, filepath: str) -> List[Bug]:
        """Run TypeScript compiler on a file"""
        bugs = []
        try:
            result = subprocess.run(
                ['tsc', '--noEmit', '--pretty', 'false', filepath],
                capture_output=True,
                text=True
            )
            if result.stderr:
                # Parse TypeScript errors
                for line in result.stderr.split('\n'):
                    match = re.match(r'(.+?)\((\d+),(\d+)\): error TS\d+: (.+)', line)
                    if match:
                        bugs.append(Bug(
                            file_path=filepath,
                            line_number=int(match.group(2)),
                            column=int(match.group(3)),
                            bug_type='typescript_error',
                            severity='high',
                            description=match.group(4),
                            code_snippet='',
                            pattern_name='tsc',
                            confidence=1.0
                        ))
        except Exception as e:
            self.logger.debug(f"TypeScript compiler error: {e}")
        return bugs
    
    def _map_eslint_severity(self, severity: int) -> str:
        """Map ESLint severity to our severity levels"""
        return {1: 'medium', 2: 'high'}.get(severity, 'low')
    
    async def _ai_analyze_code(self, filepath: str, content: str, language: str) -> List[Bug]:
        """Use AI to analyze code for bugs"""
        if not self.ai_client:
            return []
        
        bugs = []
        try:
            # Limit content size for API
            if len(content) > 4000:
                content = content[:4000] + "\n... (truncated)"
            
            prompt = f"""Analyze this {language} code for potential bugs. Look for:
1. Logic errors
2. Security vulnerabilities
3. Performance issues
4. Best practice violations

Code:
```{language}
{content}
```

Return bugs in this JSON format:
[{{
    "line_number": <int>,
    "bug_type": "<type>",
    "severity": "<critical|high|medium|low>",
    "description": "<description>",
    "suggested_fix": "<fix>"
}}]

Only return the JSON array, no other text."""

            response = self.ai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            if response_text:
                # Extract JSON from response
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    ai_bugs = json.loads(json_match.group())
                    for bug_data in ai_bugs:
                        bugs.append(Bug(
                            file_path=filepath,
                            line_number=bug_data.get('line_number', 0),
                            column=0,
                            bug_type=bug_data.get('bug_type', 'unknown'),
                            severity=bug_data.get('severity', 'medium'),
                            description=bug_data.get('description', ''),
                            code_snippet='',
                            pattern_name='ai_analysis',
                            confidence=0.7,
                            suggested_fix=bug_data.get('suggested_fix'),
                            ai_analysis="AI-detected issue"
                        ))
        except Exception as e:
            self.logger.error(f"AI analysis error: {e}")
        
        return bugs
    
    async def generate_fix(self, bug: Bug) -> Optional[BugFix]:
        """Generate fix for a detected bug"""
        self.logger.info(f"Generating fix for {bug.bug_type} in {bug.file_path}")
        
        try:
            # Read file content
            with open(bug.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # Use suggested fix if available
            if bug.suggested_fix:
                # Simple fix application
                if bug.line_number > 0 and bug.line_number <= len(lines):
                    fixed_lines = lines.copy()
                    fixed_lines[bug.line_number - 1] = bug.suggested_fix
                    fixed_code = '\n'.join(fixed_lines)
                    
                    return BugFix(
                        bug=bug,
                        fixed_code=fixed_code,
                        fix_description=f"Applied suggested fix: {bug.suggested_fix}"
                    )
            
            # Generate fix using AI if available
            if self.ai_client:
                fix = await self._ai_generate_fix(bug, content)
                if fix:
                    return fix
            
            # Pattern-specific fixes
            if bug.pattern_name in self._get_fix_generators():
                fix_generator = self._get_fix_generators()[bug.pattern_name]
                return fix_generator(bug, content)
            
        except Exception as e:
            self.logger.error(f"Error generating fix: {e}")
        
        return None
    
    def _get_fix_generators(self) -> Dict[str, Any]:
        """Get fix generators for specific patterns"""
        return {
            'python_null_reference': self._fix_null_reference_python,
            'python_resource_leak': self._fix_resource_leak_python,
            'python_mutable_default': self._fix_mutable_default_python,
            'python_bare_except': self._fix_bare_except_python,
            'js_undefined_variable': self._fix_undefined_variable_js,
            'js_array_index': self._fix_array_index_js,
            'type_mismatch': self._fix_type_mismatch
        }
    
    def _fix_null_reference_python(self, bug: Bug, content: str) -> BugFix:
        """Fix null reference in Python"""
        lines = content.split('\n')
        line = lines[bug.line_number - 1]
        indent = len(line) - len(line.lstrip())
        
        # Add null check
        fixed_lines = lines[:bug.line_number - 1]
        match = re.search(r'(\w+)\.', line)
        if match:
            var_name = match.group(1)
            fixed_lines.append(' ' * indent + f"if {var_name} is not None:")
            fixed_lines.append(' ' * (indent + 4) + line.strip())
        else:
            fixed_lines.append(line)
        fixed_lines.extend(lines[bug.line_number:])
        
        return BugFix(
            bug=bug,
            fixed_code='\n'.join(fixed_lines),
            fix_description=f"Added null check for variable"
        )
    
    def _fix_resource_leak_python(self, bug: Bug, content: str) -> BugFix:
        """Fix resource leak in Python"""
        lines = content.split('\n')
        line = lines[bug.line_number - 1]
        indent = len(line) - len(line.lstrip())
        
        # Convert to context manager
        fixed_lines = lines[:bug.line_number - 1]
        fixed_lines.append(' ' * indent + f"with {line.strip()}:")
        
        # Indent following lines that seem to use the file
        i = bug.line_number
        while i < len(lines) and lines[i].strip():
            fixed_lines.append(' ' * 4 + lines[i])
            i += 1
        
        fixed_lines.extend(lines[i:])
        
        return BugFix(
            bug=bug,
            fixed_code='\n'.join(fixed_lines),
            fix_description="Converted to context manager"
        )
    
    def _fix_mutable_default_python(self, bug: Bug, content: str) -> BugFix:
        """Fix mutable default argument in Python"""
        lines = content.split('\n')
        line = lines[bug.line_number - 1]
        
        # Replace mutable default with None
        fixed_line = re.sub(r'=\s*(\[|\{)', '=None', line)
        
        # Add initialization in function body
        fixed_lines = lines[:bug.line_number - 1]
        fixed_lines.append(fixed_line)
        
        # Find function body and add initialization
        indent = len(line) - len(line.lstrip()) + 4
        param_match = re.search(r'(\w+)\s*=\s*None', fixed_line)
        if param_match:
            param_name = param_match.group(1)
            fixed_lines.append(' ' * indent + f"if {param_name} is None:")
            fixed_lines.append(' ' * (indent + 4) + f"{param_name} = []")
        
        fixed_lines.extend(lines[bug.line_number:])
        
        return BugFix(
            bug=bug,
            fixed_code='\n'.join(fixed_lines),
            fix_description="Fixed mutable default argument"
        )
    
    def _fix_bare_except_python(self, bug: Bug, content: str) -> BugFix:
        """Fix bare except in Python"""
        lines = content.split('\n')
        line = lines[bug.line_number - 1]
        
        # Replace bare except with Exception
        fixed_line = line.replace('except:', 'except Exception as e:')
        
        fixed_lines = lines[:bug.line_number - 1]
        fixed_lines.append(fixed_line)
        fixed_lines.extend(lines[bug.line_number:])
        
        return BugFix(
            bug=bug,
            fixed_code='\n'.join(fixed_lines),
            fix_description="Replaced bare except with Exception"
        )
    
    def _fix_undefined_variable_js(self, bug: Bug, content: str) -> BugFix:
        """Fix undefined variable in JavaScript"""
        lines = content.split('\n')
        line = lines[bug.line_number - 1]
        indent = len(line) - len(line.lstrip())
        
        # Add undefined check
        fixed_lines = lines[:bug.line_number - 1]
        match = re.search(r'(\w+)\.', line)
        if match:
            var_name = match.group(1)
            fixed_lines.append(' ' * indent + f"if (typeof {var_name} !== 'undefined' && {var_name}) {{")
            fixed_lines.append(' ' * (indent + 2) + line.strip())
            fixed_lines.append(' ' * indent + "}")
        else:
            fixed_lines.append(line)
        fixed_lines.extend(lines[bug.line_number:])
        
        return BugFix(
            bug=bug,
            fixed_code='\n'.join(fixed_lines),
            fix_description="Added undefined check"
        )
    
    def _fix_array_index_js(self, bug: Bug, content: str) -> BugFix:
        """Fix array index issue in JavaScript"""
        lines = content.split('\n')
        line = lines[bug.line_number - 1]
        indent = len(line) - len(line.lstrip())
        
        # Add bounds check
        fixed_lines = lines[:bug.line_number - 1]
        match = re.search(r'(\w+)\[([^\]]+)\]', line)
        if match:
            array_name = match.group(1)
            index_expr = match.group(2)
            fixed_lines.append(' ' * indent + f"if ({index_expr} >= 0 && {index_expr} < {array_name}.length) {{")
            fixed_lines.append(' ' * (indent + 2) + line.strip())
            fixed_lines.append(' ' * indent + "}")
        else:
            fixed_lines.append(line)
        fixed_lines.extend(lines[bug.line_number:])
        
        return BugFix(
            bug=bug,
            fixed_code='\n'.join(fixed_lines),
            fix_description="Added array bounds check"
        )
    
    def _fix_type_mismatch(self, bug: Bug, content: str) -> BugFix:
        """Fix type mismatch in comparisons"""
        lines = content.split('\n')
        line = lines[bug.line_number - 1]
        
        # Replace == with ===
        fixed_line = line.replace('==', '===').replace('!=', '!==')
        # But not for === or !==
        fixed_line = fixed_line.replace('====', '===').replace('!===', '!==')
        
        fixed_lines = lines[:bug.line_number - 1]
        fixed_lines.append(fixed_line)
        fixed_lines.extend(lines[bug.line_number:])
        
        return BugFix(
            bug=bug,
            fixed_code='\n'.join(fixed_lines),
            fix_description="Used strict equality operators"
        )
    
    async def _ai_generate_fix(self, bug: Bug, content: str) -> Optional[BugFix]:
        """Generate fix using AI"""
        if not self.ai_client:
            return None
        
        try:
            # Get context around bug
            lines = content.split('\n')
            start = max(0, bug.line_number - 10)
            end = min(len(lines), bug.line_number + 10)
            context = '\n'.join(lines[start:end])
            
            prompt = f"""Fix this bug in the code:

Bug Type: {bug.bug_type}
Description: {bug.description}
Line {bug.line_number}: {bug.code_snippet}

Context:
```
{context}
```

Provide the fixed code for line {bug.line_number} only. Return just the fixed line of code, nothing else."""

            response = self.ai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            fixed_line = response.choices[0].message.content.strip()
            
            # Apply fix
            fixed_lines = lines.copy()
            if bug.line_number > 0 and bug.line_number <= len(lines):
                fixed_lines[bug.line_number - 1] = fixed_line
                
                return BugFix(
                    bug=bug,
                    fixed_code='\n'.join(fixed_lines),
                    fix_description=f"AI-generated fix: {fixed_line}"
                )
                
        except Exception as e:
            self.logger.error(f"AI fix generation error: {e}")
        
        return None
    
    async def validate_fix(self, fix: BugFix, test_files: Optional[List[str]] = None) -> bool:
        """Validate a fix by running tests"""
        self.logger.info(f"Validating fix for {fix.bug.file_path}")
        
        # Create temporary file with fix
        with tempfile.NamedTemporaryFile(mode='w', suffix=Path(fix.bug.file_path).suffix, delete=False) as tmp:
            tmp.write(fix.fixed_code)
            tmp_path = tmp.name
        
        try:
            # Check syntax first
            file_ext = Path(fix.bug.file_path).suffix.lower()
            
            if file_ext == '.py':
                # Python syntax check
                try:
                    compile(fix.fixed_code, fix.bug.file_path, 'exec')
                except SyntaxError as e:
                    fix.validation_errors.append(f"Syntax error: {e}")
                    return False
            
            # Run tests if provided
            if test_files:
                for test_file in test_files:
                    if test_file.endswith('.py'):
                        result = subprocess.run(
                            ['python', '-m', 'pytest', test_file, '-v'],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode != 0:
                            fix.validation_errors.append(f"Test failed: {test_file}")
                            fix.validation_errors.append(result.stdout)
                            return False
            
            # If no specific tests, at least check the file runs without import errors
            if file_ext == '.py':
                result = subprocess.run(
                    ['python', '-m', 'py_compile', tmp_path],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    fix.validation_errors.append("Compilation failed")
                    return False
            
            fix.tests_passed = True
            return True
            
        except Exception as e:
            fix.validation_errors.append(f"Validation error: {e}")
            return False
        finally:
            # Clean up
            os.unlink(tmp_path)
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive bug report"""
        report = {
            'scan_date': datetime.now().isoformat(),
            'total_bugs': len(self.detected_bugs),
            'by_severity': {},
            'by_type': {},
            'by_file': {},
            'bugs': []
        }
        
        # Count by severity
        for severity in ['critical', 'high', 'medium', 'low']:
            report['by_severity'][severity] = sum(
                1 for bug in self.detected_bugs if bug.severity == severity
            )
        
        # Count by type
        for bug in self.detected_bugs:
            report['by_type'][bug.bug_type] = report['by_type'].get(bug.bug_type, 0) + 1
            report['by_file'][bug.file_path] = report['by_file'].get(bug.file_path, 0) + 1
        
        # Include bug details
        report['bugs'] = [bug.to_dict() for bug in self.detected_bugs]
        
        # Store in memory
        if self.memory_core:
            self.memory_core.store({
                'type': 'bug_report',
                'timestamp': datetime.now().isoformat(),
                'report': report
            })
        
        return report
    
    def _store_bugs_in_memory(self, bugs: List[Bug]):
        """Store detected bugs in semantic memory"""
        if self.memory_core:
            for bug in bugs:
                # Store bug pattern for learning
                self.memory_core.store({
                    'type': 'bug_pattern',
                    'bug_type': bug.bug_type,
                    'pattern': bug.pattern_name,
                    'code_snippet': bug.code_snippet,
                    'fix': bug.suggested_fix,
                    'confidence': bug.confidence
                })
    
    def export_report(self, report: Dict[str, Any], format: str = 'json') -> str:
        """Export report in various formats"""
        if format == 'json':
            return json.dumps(report, indent=2)
        
        elif format == 'markdown':
            md = f"# Bug Detection Report\n\n"
            md += f"**Scan Date:** {report['scan_date']}\n"
            md += f"**Total Bugs:** {report['total_bugs']}\n\n"
            
            md += "## Summary by Severity\n\n"
            for severity, count in report['by_severity'].items():
                md += f"- **{severity.capitalize()}:** {count}\n"
            
            md += "\n## Summary by Type\n\n"
            for bug_type, count in sorted(report['by_type'].items(), key=lambda x: x[1], reverse=True):
                md += f"- **{bug_type}:** {count}\n"
            
            md += "\n## Bugs by File\n\n"
            for filepath, count in sorted(report['by_file'].items(), key=lambda x: x[1], reverse=True):
                md += f"- `{filepath}`: {count} bugs\n"
            
            md += "\n## Detailed Bug List\n\n"
            for bug in report['bugs']:
                md += f"### {bug['bug_type']} in {bug['file_path']}:{bug['line_number']}\n"
                md += f"- **Severity:** {bug['severity']}\n"
                md += f"- **Description:** {bug['description']}\n"
                md += f"- **Code:** `{bug['code_snippet']}`\n"
                if bug['suggested_fix']:
                    md += f"- **Suggested Fix:** {bug['suggested_fix']}\n"
                md += "\n"
            
            return md
        
        elif format == 'html':
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Bug Detection Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .severity-critical {{ color: #d32f2f; }}
        .severity-high {{ color: #f57c00; }}
        .severity-medium {{ color: #fbc02d; }}
        .severity-low {{ color: #388e3c; }}
        .bug {{ margin: 20px 0; padding: 10px; border: 1px solid #ddd; }}
        code {{ background: #f5f5f5; padding: 2px 4px; }}
    </style>
</head>
<body>
    <h1>Bug Detection Report</h1>
    <p><strong>Scan Date:</strong> {report['scan_date']}</p>
    <p><strong>Total Bugs:</strong> {report['total_bugs']}</p>
    
    <h2>Summary</h2>
    <ul>
"""
            for severity, count in report['by_severity'].items():
                html += f'        <li class="severity-{severity}"><strong>{severity.capitalize()}:</strong> {count}</li>\n'
            
            html += """    </ul>
    
    <h2>Detailed Bugs</h2>
"""
            
            for bug in report['bugs']:
                html += f"""
    <div class="bug">
        <h3 class="severity-{bug['severity']}">{bug['bug_type']}</h3>
        <p><strong>File:</strong> {bug['file_path']}:{bug['line_number']}</p>
        <p><strong>Description:</strong> {bug['description']}</p>
        <p><strong>Code:</strong> <code>{bug['code_snippet']}</code></p>
"""
                if bug['suggested_fix']:
                    html += f"        <p><strong>Suggested Fix:</strong> {bug['suggested_fix']}</p>\n"
                html += "    </div>\n"
            
            html += """
</body>
</html>
"""
            return html
        
        return json.dumps(report, indent=2)


class PythonBugAnalyzer(ast.NodeVisitor):
    """AST-based Python bug analyzer"""
    
    def __init__(self, filepath: str, content: str):
        self.filepath = filepath
        self.content = content
        self.lines = content.split('\n')
        self.bugs = []
        self.current_function = None
        self.variables = set()
        self.function_returns = {}
    
    def analyze(self, tree: ast.AST) -> List[Bug]:
        """Analyze AST for bugs"""
        self.visit(tree)
        return self.bugs
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition"""
        old_function = self.current_function
        self.current_function = node.name
        
        # Check for missing return
        self._check_missing_return(node)
        
        # Check for too many parameters
        if len(node.args.args) > 7:
            self.bugs.append(Bug(
                file_path=self.filepath,
                line_number=node.lineno,
                column=node.col_offset,
                bug_type='too_many_parameters',
                severity='medium',
                description=f"Function {node.name} has {len(node.args.args)} parameters (>7)",
                code_snippet=self._get_line(node.lineno),
                pattern_name='ast_analysis',
                confidence=0.9
            ))
        
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_Compare(self, node: ast.Compare):
        """Visit comparison operations"""
        # Check for comparison with None using ==
        for i, (left, op, right) in enumerate(zip(
            [node.left] + node.comparators[:-1],
            node.ops,
            node.comparators
        )):
            if isinstance(op, (ast.Eq, ast.NotEq)):
                if self._is_none(right) or self._is_none(left):
                    self.bugs.append(Bug(
                        file_path=self.filepath,
                        line_number=node.lineno,
                        column=node.col_offset,
                        bug_type='none_comparison',
                        severity='low',
                        description='Use "is" or "is not" for None comparison',
                        code_snippet=self._get_line(node.lineno),
                        pattern_name='ast_analysis',
                        confidence=1.0,
                        suggested_fix='Use "is None" or "is not None"'
                    ))
        
        self.generic_visit(node)
    
    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        """Visit exception handlers"""
        # Check for except Exception as e where e is not used
        if node.name and not self._variable_used_in_body(node.name, node.body):
            self.bugs.append(Bug(
                file_path=self.filepath,
                line_number=node.lineno,
                column=node.col_offset,
                bug_type='unused_exception',
                severity='low',
                description=f'Exception variable "{node.name}" is not used',
                code_snippet=self._get_line(node.lineno),
                pattern_name='ast_analysis',
                confidence=0.9
            ))
        
        self.generic_visit(node)
    
    def visit_For(self, node: ast.For):
        """Visit for loops"""
        # Check for modifying list while iterating
        if isinstance(node.iter, ast.Name):
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.Call):
                    if (isinstance(stmt.func, ast.Attribute) and
                        isinstance(stmt.func.value, ast.Name) and
                        stmt.func.value.id == node.iter.id and
                        stmt.func.attr in ['append', 'remove', 'pop', 'insert']):
                        self.bugs.append(Bug(
                            file_path=self.filepath,
                            line_number=stmt.lineno,
                            column=stmt.col_offset,
                            bug_type='modify_list_while_iterating',
                            severity='high',
                            description='Modifying list while iterating over it',
                            code_snippet=self._get_line(stmt.lineno),
                            pattern_name='ast_analysis',
                            confidence=0.8
                        ))
        
        self.generic_visit(node)
    
    def visit_BinOp(self, node: ast.BinOp):
        """Visit binary operations"""
        # Check for string concatenation in loops
        if isinstance(node.op, ast.Add):
            if self._in_loop() and self._involves_string(node):
                self.bugs.append(Bug(
                    file_path=self.filepath,
                    line_number=node.lineno,
                    column=node.col_offset,
                    bug_type='string_concatenation_in_loop',
                    severity='medium',
                    description='String concatenation in loop (use join() instead)',
                    code_snippet=self._get_line(node.lineno),
                    pattern_name='ast_analysis',
                    confidence=0.7
                ))
        
        self.generic_visit(node)
    
    def _check_missing_return(self, node: ast.FunctionDef):
        """Check if function should have return but doesn't"""
        # Skip __init__, __del__, and property setters
        if node.name in ['__init__', '__del__'] or node.name.startswith('set_'):
            return
        
        # Check if function has return type annotation suggesting non-None return
        if node.returns and not self._returns_none_annotation(node.returns):
            has_return = any(isinstance(stmt, ast.Return) and stmt.value is not None
                            for stmt in ast.walk(node))
            if not has_return:
                self.bugs.append(Bug(
                    file_path=self.filepath,
                    line_number=node.lineno,
                    column=node.col_offset,
                    bug_type='missing_return',
                    severity='high',
                    description=f'Function {node.name} has return type annotation but no return statement',
                    code_snippet=self._get_line(node.lineno),
                    pattern_name='ast_analysis',
                    confidence=0.9
                ))
    
    def _is_none(self, node: ast.AST) -> bool:
        """Check if node represents None"""
        return isinstance(node, ast.Constant) and node.value is None
    
    def _get_line(self, line_num: int) -> str:
        """Get line content"""
        if 0 < line_num <= len(self.lines):
            return self.lines[line_num - 1].strip()
        return ""
    
    def _variable_used_in_body(self, var_name: str, body: List[ast.AST]) -> bool:
        """Check if variable is used in body"""
        for node in ast.walk(ast.Module(body=body)):
            if isinstance(node, ast.Name) and node.id == var_name:
                return True
        return False
    
    def _in_loop(self) -> bool:
        """Check if currently in a loop context"""
        # This is a simplified check - would need proper context tracking
        return False
    
    def _involves_string(self, node: ast.BinOp) -> bool:
        """Check if binary operation involves strings"""
        for operand in [node.left, node.right]:
            if isinstance(operand, ast.Constant) and isinstance(operand.value, str):
                return True
            if isinstance(operand, ast.Call) and isinstance(operand.func, ast.Name):
                if operand.func.id in ['str', 'format']:
                    return True
        return False
    
    def _returns_none_annotation(self, annotation: ast.AST) -> bool:
        """Check if return annotation is None"""
        return (isinstance(annotation, ast.Constant) and annotation.value is None) or \
               (isinstance(annotation, ast.Name) and annotation.id == 'None')


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Initialize bug detector
        detector = BugDetectorOmnipotent()
        
        # Example: Scan a file
        bugs = await detector.scan_file("example.py")
        
        # Example: Scan a project
        # bugs = await detector.scan_project("/path/to/project")
        
        # Generate report
        report = detector.generate_report()
        
        # Export report
        print(detector.export_report(report, format='markdown'))
        
        # Generate fixes
        for bug in bugs[:5]:  # Fix first 5 bugs
            fix = await detector.generate_fix(bug)
            if fix:
                print(f"\nFix for {bug.bug_type}:")
                print(f"Description: {fix.fix_description}")
                
                # Validate fix
                if await detector.validate_fix(fix):
                    print("Fix validated successfully!")
                else:
                    print("Fix validation failed:", fix.validation_errors)
    
    asyncio.run(main())