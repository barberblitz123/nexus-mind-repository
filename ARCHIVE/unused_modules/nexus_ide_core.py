#!/usr/bin/env python3
"""
NEXUS IDE Core - Advanced Integrated Development Environment
"""

import asyncio
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
import threading
from concurrent.futures import ThreadPoolExecutor
import difflib
import tempfile
import shutil

# Third-party imports
try:
    import pygments
    from pygments.lexers import get_lexer_by_name, guess_lexer_for_filename
    from pygments.formatters import TerminalFormatter
    from pygments.styles import get_style_by_name
except ImportError:
    pygments = None

try:
    import git
except ImportError:
    git = None

try:
    from pylsp import lsp
    from pylsp.config import config as lsp_config
except ImportError:
    lsp = None

# Import NEXUS components
from nexus_memory_core import NexusMemoryCore
from nexus_unified_tools import UnifiedToolSystem


@dataclass
class EditorTab:
    """Represents an editor tab"""
    file_path: Path
    content: str
    cursor_position: Tuple[int, int] = (0, 0)
    selection: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
    dirty: bool = False
    language: str = "text"
    breakpoints: Set[int] = field(default_factory=set)
    bookmarks: Set[int] = field(default_factory=set)
    fold_regions: List[Tuple[int, int]] = field(default_factory=list)
    
    
@dataclass
class CodeCompletion:
    """Code completion suggestion"""
    text: str
    label: str
    detail: Optional[str] = None
    documentation: Optional[str] = None
    kind: str = "text"
    insert_text: Optional[str] = None
    score: float = 0.0
    

@dataclass
class Diagnostic:
    """Code diagnostic (error/warning)"""
    line: int
    column: int
    message: str
    severity: str = "error"  # error, warning, info, hint
    source: str = "nexus"
    code: Optional[str] = None
    

@dataclass
class DebugBreakpoint:
    """Debug breakpoint"""
    file_path: Path
    line: int
    condition: Optional[str] = None
    hit_count: int = 0
    enabled: bool = True
    

class SyntaxHighlighter:
    """Syntax highlighting engine"""
    
    def __init__(self):
        self.style = "monokai"
        self.formatter = TerminalFormatter(style=self.style) if pygments else None
        self._lexer_cache = {}
        
    def highlight(self, code: str, language: str) -> str:
        """Highlight code with syntax coloring"""
        if not pygments:
            return code
            
        try:
            # Check cache first
            if language not in self._lexer_cache:
                self._lexer_cache[language] = get_lexer_by_name(language)
            
            lexer = self._lexer_cache[language]
            return pygments.highlight(code, lexer, self.formatter)
        except Exception:
            return code
            
    def detect_language(self, file_path: Path) -> str:
        """Detect language from file extension"""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "jsx",
            ".tsx": "tsx",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".r": "r",
            ".m": "matlab",
            ".jl": "julia",
            ".lua": "lua",
            ".dart": "dart",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".less": "less",
            ".xml": "xml",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".ini": "ini",
            ".md": "markdown",
            ".rst": "rst",
            ".tex": "latex",
            ".sh": "bash",
            ".ps1": "powershell",
            ".sql": "sql",
            ".dockerfile": "dockerfile",
            ".makefile": "makefile",
            ".cmake": "cmake",
            ".vim": "vim",
            ".el": "elisp",
        }
        
        suffix = file_path.suffix.lower()
        return extension_map.get(suffix, "text")
        

class IntelliSenseEngine:
    """AI-enhanced IntelliSense/autocomplete engine"""
    
    def __init__(self, memory_core: NexusMemoryCore):
        self.memory = memory_core
        self.lsp_clients = {}
        self.ai_cache = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def get_completions(
        self,
        file_path: Path,
        content: str,
        cursor_pos: Tuple[int, int],
        language: str
    ) -> List[CodeCompletion]:
        """Get code completions at cursor position"""
        completions = []
        
        # Get LSP completions
        if lsp and language in self.lsp_clients:
            lsp_completions = await self._get_lsp_completions(
                file_path, content, cursor_pos, language
            )
            completions.extend(lsp_completions)
            
        # Get AI-enhanced completions
        ai_completions = await self._get_ai_completions(
            content, cursor_pos, language
        )
        completions.extend(ai_completions)
        
        # Get snippet completions
        snippet_completions = self._get_snippet_completions(
            content, cursor_pos, language
        )
        completions.extend(snippet_completions)
        
        # Sort by score and deduplicate
        seen = set()
        unique_completions = []
        for comp in sorted(completions, key=lambda x: x.score, reverse=True):
            if comp.text not in seen:
                seen.add(comp.text)
                unique_completions.append(comp)
                
        return unique_completions[:20]  # Limit to top 20
        
    async def _get_ai_completions(
        self,
        content: str,
        cursor_pos: Tuple[int, int],
        language: str
    ) -> List[CodeCompletion]:
        """Get AI-powered completions"""
        # Extract context around cursor
        lines = content.split('\n')
        line_idx, col_idx = cursor_pos
        
        if line_idx >= len(lines):
            return []
            
        current_line = lines[line_idx]
        prefix = current_line[:col_idx]
        
        # Build context
        context_start = max(0, line_idx - 10)
        context_end = min(len(lines), line_idx + 5)
        context = '\n'.join(lines[context_start:context_end])
        
        # Check cache
        cache_key = f"{language}:{prefix}:{hash(context)}"
        if cache_key in self.ai_cache:
            return self.ai_cache[cache_key]
            
        # Generate completions using memory
        query = f"""
        Language: {language}
        Context:
        {context}
        
        Current line prefix: {prefix}
        
        Suggest code completions for the cursor position.
        """
        
        suggestions = await self.memory.query(query, context_type="code_completion")
        
        completions = []
        for i, suggestion in enumerate(suggestions[:5]):
            completions.append(CodeCompletion(
                text=suggestion.get("completion", ""),
                label=suggestion.get("label", ""),
                detail=suggestion.get("detail", ""),
                documentation=suggestion.get("doc", ""),
                kind="ai",
                score=0.9 - (i * 0.1)
            ))
            
        self.ai_cache[cache_key] = completions
        return completions
        
    def _get_snippet_completions(
        self,
        content: str,
        cursor_pos: Tuple[int, int],
        language: str
    ) -> List[CodeCompletion]:
        """Get snippet completions"""
        snippets = {
            "python": {
                "def": "def ${1:function_name}(${2:params}):\n    ${3:pass}",
                "class": "class ${1:ClassName}:\n    def __init__(self, ${2:params}):\n        ${3:pass}",
                "if": "if ${1:condition}:\n    ${2:pass}",
                "for": "for ${1:item} in ${2:iterable}:\n    ${3:pass}",
                "try": "try:\n    ${1:pass}\nexcept ${2:Exception} as e:\n    ${3:pass}",
                "with": "with ${1:expression} as ${2:var}:\n    ${3:pass}",
            },
            "javascript": {
                "func": "function ${1:name}(${2:params}) {\n    ${3:}\n}",
                "arrow": "const ${1:name} = (${2:params}) => {\n    ${3:}\n}",
                "class": "class ${1:ClassName} {\n    constructor(${2:params}) {\n        ${3:}\n    }\n}",
                "if": "if (${1:condition}) {\n    ${2:}\n}",
                "for": "for (${1:let i = 0}; ${2:i < length}; ${3:i++}) {\n    ${4:}\n}",
                "promise": "new Promise((resolve, reject) => {\n    ${1:}\n})",
            }
        }
        
        lang_snippets = snippets.get(language, {})
        completions = []
        
        lines = content.split('\n')
        if cursor_pos[0] < len(lines):
            current_line = lines[cursor_pos[0]]
            prefix = current_line[:cursor_pos[1]].strip()
            
            for trigger, snippet in lang_snippets.items():
                if trigger.startswith(prefix):
                    completions.append(CodeCompletion(
                        text=trigger,
                        label=f"{trigger} (snippet)",
                        detail="Code snippet",
                        insert_text=snippet,
                        kind="snippet",
                        score=0.7
                    ))
                    
        return completions
        

class ErrorDetector:
    """Real-time error detection engine"""
    
    def __init__(self):
        self.linters = {
            "python": ["pylint", "flake8", "mypy"],
            "javascript": ["eslint", "jshint"],
            "typescript": ["tslint", "eslint"],
            "go": ["golint", "go vet"],
            "rust": ["clippy"],
            "java": ["checkstyle"],
            "cpp": ["cpplint", "cppcheck"],
        }
        self.diagnostics_cache = {}
        
    async def detect_errors(
        self,
        file_path: Path,
        content: str,
        language: str
    ) -> List[Diagnostic]:
        """Detect errors in code"""
        diagnostics = []
        
        # Syntax check
        syntax_errors = self._check_syntax(content, language)
        diagnostics.extend(syntax_errors)
        
        # Run linters
        if language in self.linters:
            linter_errors = await self._run_linters(
                file_path, content, language
            )
            diagnostics.extend(linter_errors)
            
        # AI-based error detection
        ai_errors = await self._ai_error_detection(content, language)
        diagnostics.extend(ai_errors)
        
        return diagnostics
        
    def _check_syntax(self, content: str, language: str) -> List[Diagnostic]:
        """Basic syntax checking"""
        diagnostics = []
        
        if language == "python":
            try:
                compile(content, "<string>", "exec")
            except SyntaxError as e:
                diagnostics.append(Diagnostic(
                    line=e.lineno - 1 if e.lineno else 0,
                    column=e.offset - 1 if e.offset else 0,
                    message=str(e),
                    severity="error",
                    source="syntax"
                ))
                
        return diagnostics
        
    async def _run_linters(
        self,
        file_path: Path,
        content: str,
        language: str
    ) -> List[Diagnostic]:
        """Run external linters"""
        diagnostics = []
        
        # Save content to temp file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=file_path.suffix,
            delete=False
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
            
        try:
            for linter in self.linters.get(language, []):
                if shutil.which(linter):
                    result = await self._run_linter(linter, tmp_path, language)
                    diagnostics.extend(result)
        finally:
            os.unlink(tmp_path)
            
        return diagnostics
        
    async def _ai_error_detection(
        self,
        content: str,
        language: str
    ) -> List[Diagnostic]:
        """AI-based error detection"""
        # This would integrate with the AI model for advanced error detection
        return []
        

class GitIntegration:
    """Git integration with visual diff"""
    
    def __init__(self):
        self.repo = None
        self.diff_cache = {}
        
    def init_repo(self, path: Path):
        """Initialize git repository"""
        if git:
            try:
                self.repo = git.Repo(path)
            except git.InvalidGitRepositoryError:
                self.repo = git.Repo.init(path)
                
    def get_status(self) -> Dict[str, Any]:
        """Get repository status"""
        if not self.repo:
            return {}
            
        status = {
            "branch": self.repo.active_branch.name,
            "modified": [],
            "added": [],
            "deleted": [],
            "untracked": [],
            "staged": []
        }
        
        # Get file status
        for item in self.repo.index.diff(None):
            status["modified"].append(item.a_path)
            
        for item in self.repo.index.diff("HEAD"):
            status["staged"].append(item.a_path)
            
        status["untracked"] = self.repo.untracked_files
        
        return status
        
    def get_diff(self, file_path: Path) -> List[str]:
        """Get visual diff for file"""
        if not self.repo:
            return []
            
        try:
            # Get diff
            diff = self.repo.git.diff(file_path)
            return diff.split('\n')
        except Exception:
            return []
            
    def stage_file(self, file_path: Path):
        """Stage file for commit"""
        if self.repo:
            self.repo.index.add([str(file_path)])
            
    def commit(self, message: str):
        """Commit staged changes"""
        if self.repo:
            self.repo.index.commit(message)
            

class RefactoringTools:
    """Code refactoring tools"""
    
    def __init__(self):
        self.refactorings = {
            "rename": self.rename_symbol,
            "extract_method": self.extract_method,
            "extract_variable": self.extract_variable,
            "inline": self.inline_variable,
            "move": self.move_definition,
        }
        
    async def rename_symbol(
        self,
        content: str,
        old_name: str,
        new_name: str,
        language: str
    ) -> str:
        """Rename symbol throughout code"""
        # Simple implementation - would be enhanced with AST parsing
        pattern = rf'\b{re.escape(old_name)}\b'
        return re.sub(pattern, new_name, content)
        
    async def extract_method(
        self,
        content: str,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        method_name: str,
        language: str
    ) -> str:
        """Extract selected code into method"""
        lines = content.split('\n')
        
        # Extract selection
        selected_lines = []
        for i in range(start_pos[0], end_pos[0] + 1):
            if i < len(lines):
                selected_lines.append(lines[i])
                
        # Create method
        if language == "python":
            method = f"def {method_name}():\n"
            for line in selected_lines:
                method += f"    {line}\n"
                
            # Replace selection with method call
            lines[start_pos[0]:end_pos[0] + 1] = [f"{method_name}()"]
            
            # Insert method definition
            lines.insert(start_pos[0] - 1, method)
            
        return '\n'.join(lines)
        
    async def extract_variable(
        self,
        content: str,
        expression: str,
        var_name: str,
        cursor_pos: Tuple[int, int],
        language: str
    ) -> str:
        """Extract expression into variable"""
        lines = content.split('\n')
        line_idx = cursor_pos[0]
        
        if line_idx < len(lines):
            line = lines[line_idx]
            
            # Create variable assignment
            if language == "python":
                assignment = f"{var_name} = {expression}"
                new_line = line.replace(expression, var_name)
                
                # Insert assignment before current line
                indent = len(line) - len(line.lstrip())
                lines.insert(line_idx, ' ' * indent + assignment)
                lines[line_idx + 1] = new_line
                
        return '\n'.join(lines)
        
    async def inline_variable(
        self,
        content: str,
        var_name: str,
        language: str
    ) -> str:
        """Inline variable usage"""
        # Would be implemented with proper AST parsing
        return content
        
    async def move_definition(
        self,
        content: str,
        definition: str,
        target_line: int,
        language: str
    ) -> str:
        """Move definition to new location"""
        # Would be implemented with proper AST parsing
        return content
        

class CodeGenerator:
    """AI-powered code generation from natural language"""
    
    def __init__(self, memory_core: NexusMemoryCore):
        self.memory = memory_core
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, str]:
        """Load code generation templates"""
        return {
            "python_class": """class {class_name}:
    \"\"\"
    {description}
    \"\"\"
    
    def __init__(self{params}):
        {init_body}
        
    {methods}
""",
            "javascript_component": """const {component_name} = ({props}) => {{
    {hooks}
    
    {logic}
    
    return (
        {jsx}
    );
}};

export default {component_name};
""",
        }
        
    async def generate_code(
        self,
        prompt: str,
        language: str,
        context: Optional[str] = None
    ) -> str:
        """Generate code from natural language prompt"""
        # Build generation prompt
        generation_prompt = f"""
        Generate {language} code for the following request:
        {prompt}
        
        Context:
        {context or 'No additional context'}
        
        Requirements:
        - Follow best practices for {language}
        - Include proper error handling
        - Add helpful comments
        - Make it production-ready
        """
        
        # Query memory for code generation
        result = await self.memory.query(
            generation_prompt,
            context_type="code_generation"
        )
        
        if result and len(result) > 0:
            return result[0].get("code", "")
            
        return ""
        

class NexusIDECore:
    """Core IDE functionality"""
    
    def __init__(self):
        self.memory = NexusMemoryCore()
        self.tools = UnifiedToolSystem()
        
        # Initialize components
        self.tabs: List[EditorTab] = []
        self.active_tab_index = 0
        self.highlighter = SyntaxHighlighter()
        self.intellisense = IntelliSenseEngine(self.memory)
        self.error_detector = ErrorDetector()
        self.git = GitIntegration()
        self.refactoring = RefactoringTools()
        self.code_generator = CodeGenerator(self.memory)
        
        # Settings
        self.settings = {
            "theme": "dark",
            "font_size": 14,
            "tab_size": 4,
            "auto_save": True,
            "auto_format": True,
            "show_minimap": True,
            "show_line_numbers": True,
            "word_wrap": False,
        }
        
        # Debug state
        self.debug_session = None
        self.breakpoints: List[DebugBreakpoint] = []
        
        # Extension system
        self.extensions = {}
        self.extension_api = self._create_extension_api()
        
    def _create_extension_api(self) -> Dict[str, Any]:
        """Create API for extensions"""
        return {
            "registerCommand": self.register_command,
            "registerLanguageProvider": self.register_language_provider,
            "registerTheme": self.register_theme,
            "getActiveEditor": self.get_active_editor,
            "showMessage": self.show_message,
            "createOutputChannel": self.create_output_channel,
        }
        
    async def open_file(self, file_path: Path) -> EditorTab:
        """Open file in new tab"""
        # Check if already open
        for tab in self.tabs:
            if tab.file_path == file_path:
                self.active_tab_index = self.tabs.index(tab)
                return tab
                
        # Read file content
        try:
            content = file_path.read_text()
        except Exception as e:
            content = ""
            
        # Detect language
        language = self.highlighter.detect_language(file_path)
        
        # Create new tab
        tab = EditorTab(
            file_path=file_path,
            content=content,
            language=language
        )
        
        self.tabs.append(tab)
        self.active_tab_index = len(self.tabs) - 1
        
        # Initialize git for directory
        self.git.init_repo(file_path.parent)
        
        return tab
        
    async def save_file(self, tab_index: Optional[int] = None) -> bool:
        """Save file"""
        if tab_index is None:
            tab_index = self.active_tab_index
            
        if 0 <= tab_index < len(self.tabs):
            tab = self.tabs[tab_index]
            
            try:
                # Format code if enabled
                if self.settings["auto_format"]:
                    tab.content = await self.format_code(
                        tab.content,
                        tab.language
                    )
                    
                # Write to file
                tab.file_path.write_text(tab.content)
                tab.dirty = False
                
                return True
            except Exception as e:
                print(f"Error saving file: {e}")
                return False
                
        return False
        
    async def get_completions(
        self,
        tab_index: Optional[int] = None
    ) -> List[CodeCompletion]:
        """Get code completions for current position"""
        if tab_index is None:
            tab_index = self.active_tab_index
            
        if 0 <= tab_index < len(self.tabs):
            tab = self.tabs[tab_index]
            
            return await self.intellisense.get_completions(
                tab.file_path,
                tab.content,
                tab.cursor_position,
                tab.language
            )
            
        return []
        
    async def get_diagnostics(
        self,
        tab_index: Optional[int] = None
    ) -> List[Diagnostic]:
        """Get diagnostics for current file"""
        if tab_index is None:
            tab_index = self.active_tab_index
            
        if 0 <= tab_index < len(self.tabs):
            tab = self.tabs[tab_index]
            
            return await self.error_detector.detect_errors(
                tab.file_path,
                tab.content,
                tab.language
            )
            
        return []
        
    async def format_code(self, content: str, language: str) -> str:
        """Format code"""
        formatters = {
            "python": "black",
            "javascript": "prettier",
            "typescript": "prettier",
            "go": "gofmt",
            "rust": "rustfmt",
            "java": "google-java-format",
            "cpp": "clang-format",
        }
        
        formatter = formatters.get(language)
        if formatter and shutil.which(formatter):
            try:
                # Use formatter
                with tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix=f".{language}",
                    delete=False
                ) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                    
                # Run formatter
                subprocess.run([formatter, tmp_path], check=True)
                
                # Read formatted content
                formatted = Path(tmp_path).read_text()
                os.unlink(tmp_path)
                
                return formatted
            except Exception:
                pass
                
        return content
        
    async def refactor_code(
        self,
        refactoring_type: str,
        **kwargs
    ) -> Optional[str]:
        """Perform code refactoring"""
        if self.active_tab_index < len(self.tabs):
            tab = self.tabs[self.active_tab_index]
            
            if refactoring_type in self.refactoring.refactorings:
                refactor_func = self.refactoring.refactorings[refactoring_type]
                
                new_content = await refactor_func(
                    tab.content,
                    language=tab.language,
                    **kwargs
                )
                
                tab.content = new_content
                tab.dirty = True
                
                return new_content
                
        return None
        
    async def generate_code_from_prompt(
        self,
        prompt: str,
        insert_at_cursor: bool = True
    ) -> Optional[str]:
        """Generate code from natural language"""
        if self.active_tab_index < len(self.tabs):
            tab = self.tabs[self.active_tab_index]
            
            # Get context around cursor
            lines = tab.content.split('\n')
            context_start = max(0, tab.cursor_position[0] - 20)
            context_end = min(len(lines), tab.cursor_position[0] + 20)
            context = '\n'.join(lines[context_start:context_end])
            
            # Generate code
            generated = await self.code_generator.generate_code(
                prompt,
                tab.language,
                context
            )
            
            if generated and insert_at_cursor:
                # Insert at cursor position
                line_idx, col_idx = tab.cursor_position
                
                if line_idx < len(lines):
                    line = lines[line_idx]
                    new_line = line[:col_idx] + generated + line[col_idx:]
                    lines[line_idx] = new_line
                else:
                    lines.append(generated)
                    
                tab.content = '\n'.join(lines)
                tab.dirty = True
                
            return generated
            
        return None
        
    def set_breakpoint(self, file_path: Path, line: int, condition: Optional[str] = None):
        """Set debug breakpoint"""
        breakpoint = DebugBreakpoint(
            file_path=file_path,
            line=line,
            condition=condition
        )
        self.breakpoints.append(breakpoint)
        
        # Update tab if open
        for tab in self.tabs:
            if tab.file_path == file_path:
                tab.breakpoints.add(line)
                
    def remove_breakpoint(self, file_path: Path, line: int):
        """Remove debug breakpoint"""
        self.breakpoints = [
            bp for bp in self.breakpoints
            if not (bp.file_path == file_path and bp.line == line)
        ]
        
        # Update tab if open
        for tab in self.tabs:
            if tab.file_path == file_path:
                tab.breakpoints.discard(line)
                
    def get_active_editor(self) -> Optional[EditorTab]:
        """Get active editor tab"""
        if 0 <= self.active_tab_index < len(self.tabs):
            return self.tabs[self.active_tab_index]
        return None
        
    def register_command(self, command_id: str, handler: Callable):
        """Register IDE command"""
        # Command registration logic
        pass
        
    def register_language_provider(self, language: str, provider: Any):
        """Register language support provider"""
        # Language provider registration
        pass
        
    def register_theme(self, theme_id: str, theme_data: Dict):
        """Register color theme"""
        # Theme registration
        pass
        
    def show_message(self, message: str, level: str = "info"):
        """Show message to user"""
        print(f"[{level.upper()}] {message}")
        
    def create_output_channel(self, name: str):
        """Create output channel for extension"""
        # Output channel creation
        return {
            "append": lambda text: print(f"[{name}] {text}"),
            "clear": lambda: None,
            "show": lambda: None,
        }


async def main():
    """Test IDE core functionality"""
    ide = NexusIDECore()
    
    # Test file operations
    test_file = Path("test_ide.py")
    test_file.write_text("""
def hello_world():
    print("Hello, World!")
    
if __name__ == "__main__":
    hello_world()
""")
    
    # Open file
    tab = await ide.open_file(test_file)
    print(f"Opened {tab.file_path}")
    
    # Get completions
    tab.cursor_position = (2, 10)  # After 'print('
    completions = await ide.get_completions()
    print(f"Completions: {[c.label for c in completions[:5]]}")
    
    # Get diagnostics
    diagnostics = await ide.get_diagnostics()
    print(f"Diagnostics: {diagnostics}")
    
    # Generate code
    generated = await ide.generate_code_from_prompt(
        "Add a function that calculates factorial"
    )
    print(f"Generated code:\n{generated}")
    
    # Save file
    await ide.save_file()
    
    # Cleanup
    test_file.unlink()


if __name__ == "__main__":
    asyncio.run(main())