#!/usr/bin/env python3
"""
NEXUS Production CLI - Natural Language Interface
Advanced command-line interface with NLP, suggestions, and scripting
"""

import asyncio
import json
import os
import readline
import shlex
import subprocess
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import click
import pygments
from pygments.lexers import JsonLexer, YamlLexer, PythonLexer
from pygments.formatters import TerminalFormatter
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
import requests
import yaml
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.markdown import Markdown
import spacy
from transformers import pipeline


# Natural Language Processor
class NLPProcessor:
    """Process natural language commands"""
    
    def __init__(self):
        self.console = Console()
        self.intent_classifier = None
        self.ner_model = None
        self.command_patterns = {
            'create': ['create', 'make', 'build', 'generate', 'new'],
            'list': ['list', 'show', 'display', 'get', 'find'],
            'start': ['start', 'run', 'launch', 'begin', 'initiate'],
            'stop': ['stop', 'halt', 'kill', 'terminate', 'end'],
            'status': ['status', 'state', 'health', 'check'],
            'deploy': ['deploy', 'publish', 'release', 'push'],
            'config': ['config', 'configure', 'setup', 'settings'],
            'help': ['help', 'assist', 'guide', 'explain']
        }
        
        try:
            # Load spaCy model for entity recognition
            self.nlp = spacy.load("en_core_web_sm")
        except:
            self.console.print("[yellow]NLP model not found. Installing...[/yellow]")
            subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
    
    def parse_command(self, text: str) -> Dict[str, Any]:
        """Parse natural language command"""
        doc = self.nlp(text.lower())
        
        # Extract intent
        intent = None
        for cmd_type, keywords in self.command_patterns.items():
            for token in doc:
                if token.text in keywords:
                    intent = cmd_type
                    break
            if intent:
                break
        
        # Extract entities
        entities = {
            'services': [],
            'files': [],
            'configs': [],
            'actions': []
        }
        
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PRODUCT']:
                entities['services'].append(ent.text)
            elif ent.label_ == 'GPE':
                entities['configs'].append(ent.text)
        
        # Extract custom entities
        for token in doc:
            if token.pos_ == 'NOUN':
                # Check if it looks like a service name
                if any(x in token.text for x in ['service', 'api', 'core', 'nexus']):
                    entities['services'].append(token.text)
                # Check if it looks like a file
                elif '.' in token.text or '/' in token.text:
                    entities['files'].append(token.text)
        
        return {
            'intent': intent or 'unknown',
            'entities': entities,
            'original': text,
            'tokens': [token.text for token in doc]
        }
    
    def suggest_command(self, parsed: Dict[str, Any]) -> Optional[str]:
        """Suggest actual command based on parsed input"""
        intent = parsed['intent']
        entities = parsed['entities']
        
        suggestions = {
            'create': {
                'service': 'nexus service create {name}',
                'project': 'nexus project init {name}',
                'plugin': 'nexus plugin create {name}'
            },
            'list': {
                'services': 'nexus service list',
                'plugins': 'nexus plugin list',
                'projects': 'nexus project list'
            },
            'start': {
                'service': 'nexus service start {name}',
                'all': 'nexus start',
                'core': 'nexus core start'
            },
            'stop': {
                'service': 'nexus service stop {name}',
                'all': 'nexus stop',
                'core': 'nexus core stop'
            },
            'status': {
                'all': 'nexus status',
                'service': 'nexus service status {name}',
                'health': 'nexus health check'
            },
            'deploy': {
                'project': 'nexus deploy {project}',
                'service': 'nexus service deploy {name}'
            }
        }
        
        # Try to match intent with entities
        if intent in suggestions:
            # Determine sub-type based on entities
            if entities['services']:
                if 'service' in suggestions[intent]:
                    return suggestions[intent]['service'].format(
                        name=entities['services'][0]
                    )
            elif 'all' in parsed['original'] or not entities['services']:
                if 'all' in suggestions[intent]:
                    return suggestions[intent]['all']
        
        return None


# Command Completer
class NexusCompleter(Completer):
    """Advanced command completion"""
    
    def __init__(self, cli):
        self.cli = cli
        self.commands = {
            'service': ['create', 'list', 'start', 'stop', 'status', 'deploy', 'logs'],
            'project': ['init', 'list', 'build', 'test', 'deploy'],
            'plugin': ['create', 'list', 'install', 'uninstall', 'update'],
            'config': ['get', 'set', 'list', 'edit'],
            'core': ['start', 'stop', 'restart', 'status'],
            'health': ['check', 'report'],
            'backup': ['create', 'restore', 'list'],
            'update': ['check', 'apply']
        }
    
    def get_completions(self, document, complete_event):
        """Get command completions"""
        text = document.text_before_cursor
        words = text.split()
        
        if not words:
            # Top-level commands
            for cmd in self.commands.keys():
                yield Completion(cmd, start_position=0)
        elif len(words) == 1:
            # Complete first word
            for cmd in self.commands.keys():
                if cmd.startswith(words[0]):
                    yield Completion(
                        cmd,
                        start_position=-len(words[0]),
                        display_meta=f"NEXUS {cmd} commands"
                    )
        elif len(words) == 2:
            # Complete subcommand
            cmd = words[0]
            if cmd in self.commands:
                for subcmd in self.commands[cmd]:
                    if subcmd.startswith(words[1]):
                        yield Completion(
                            subcmd,
                            start_position=-len(words[1])
                        )
        else:
            # Context-aware completion
            if words[0] == 'service' and words[1] in ['start', 'stop', 'status']:
                # Complete with service names
                services = self._get_services()
                for service in services:
                    if service.startswith(words[-1]):
                        yield Completion(
                            service,
                            start_position=-len(words[-1])
                        )
    
    def _get_services(self) -> List[str]:
        """Get available service names"""
        try:
            # Query NEXUS API for services
            response = requests.get('http://localhost:8080/services')
            if response.status_code == 200:
                data = response.json()
                return [s['name'] for s in data.get('services', [])]
        except:
            pass
        return []


# Command Classes
@dataclass
class CommandResult:
    """Command execution result"""
    success: bool
    output: Any
    error: Optional[str] = None
    duration: Optional[float] = None


class Command(ABC):
    """Base command class"""
    
    def __init__(self, cli):
        self.cli = cli
        self.console = Console()
    
    @abstractmethod
    async def execute(self, args: List[str]) -> CommandResult:
        """Execute the command"""
        pass
    
    def format_output(self, data: Any, format: str = 'json'):
        """Format output data"""
        if format == 'json':
            json_str = json.dumps(data, indent=2)
            lexer = JsonLexer()
            formatted = pygments.highlight(json_str, lexer, TerminalFormatter())
            return formatted
        elif format == 'yaml':
            yaml_str = yaml.dump(data, default_flow_style=False)
            lexer = YamlLexer()
            formatted = pygments.highlight(yaml_str, lexer, TerminalFormatter())
            return formatted
        elif format == 'table' and isinstance(data, list):
            return self._format_table(data)
        else:
            return str(data)
    
    def _format_table(self, data: List[Dict]) -> str:
        """Format data as table"""
        if not data:
            return "No data"
        
        table = Table()
        
        # Add columns
        for key in data[0].keys():
            table.add_column(key.title())
        
        # Add rows
        for item in data:
            table.add_row(*[str(v) for v in item.values()])
        
        # Render to string
        from io import StringIO
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True)
        console.print(table)
        return buffer.getvalue()


class ServiceCommand(Command):
    """Service management commands"""
    
    async def execute(self, args: List[str]) -> CommandResult:
        """Execute service command"""
        if not args:
            return CommandResult(False, None, "No subcommand provided")
        
        subcommand = args[0]
        
        if subcommand == 'list':
            return await self._list_services()
        elif subcommand == 'start':
            if len(args) < 2:
                return CommandResult(False, None, "Service name required")
            return await self._start_service(args[1])
        elif subcommand == 'stop':
            if len(args) < 2:
                return CommandResult(False, None, "Service name required")
            return await self._stop_service(args[1])
        elif subcommand == 'status':
            if len(args) < 2:
                return await self._all_status()
            return await self._service_status(args[1])
        else:
            return CommandResult(False, None, f"Unknown subcommand: {subcommand}")
    
    async def _list_services(self) -> CommandResult:
        """List all services"""
        try:
            response = requests.get(f"{self.cli.api_url}/services")
            response.raise_for_status()
            return CommandResult(True, response.json()['services'])
        except Exception as e:
            return CommandResult(False, None, str(e))
    
    async def _start_service(self, name: str) -> CommandResult:
        """Start a service"""
        try:
            response = requests.post(
                f"{self.cli.api_url}/services/{name}/start"
            )
            response.raise_for_status()
            return CommandResult(True, {"message": f"Service {name} started"})
        except Exception as e:
            return CommandResult(False, None, str(e))
    
    async def _stop_service(self, name: str) -> CommandResult:
        """Stop a service"""
        try:
            response = requests.post(
                f"{self.cli.api_url}/services/{name}/stop"
            )
            response.raise_for_status()
            return CommandResult(True, {"message": f"Service {name} stopped"})
        except Exception as e:
            return CommandResult(False, None, str(e))
    
    async def _service_status(self, name: str) -> CommandResult:
        """Get service status"""
        try:
            response = requests.get(
                f"{self.cli.api_url}/services/{name}/status"
            )
            response.raise_for_status()
            return CommandResult(True, response.json())
        except Exception as e:
            return CommandResult(False, None, str(e))
    
    async def _all_status(self) -> CommandResult:
        """Get status of all services"""
        try:
            response = requests.get(f"{self.cli.api_url}/services")
            response.raise_for_status()
            services = response.json()['services']
            
            # Format as status table
            status_data = []
            for service in services:
                status_data.append({
                    'name': service['name'],
                    'status': service['status'],
                    'host': f"{service['host']}:{service['port']}",
                    'version': service['version']
                })
            
            return CommandResult(True, status_data)
        except Exception as e:
            return CommandResult(False, None, str(e))


class ProjectCommand(Command):
    """Project management commands"""
    
    async def execute(self, args: List[str]) -> CommandResult:
        """Execute project command"""
        if not args:
            return CommandResult(False, None, "No subcommand provided")
        
        subcommand = args[0]
        
        if subcommand == 'init':
            if len(args) < 2:
                return CommandResult(False, None, "Project name required")
            return await self._init_project(args[1])
        elif subcommand == 'list':
            return await self._list_projects()
        elif subcommand == 'build':
            if len(args) < 2:
                return CommandResult(False, None, "Project name required")
            return await self._build_project(args[1])
        else:
            return CommandResult(False, None, f"Unknown subcommand: {subcommand}")
    
    async def _init_project(self, name: str) -> CommandResult:
        """Initialize new project"""
        try:
            # Call project generator
            from nexus_project_generator import ProjectGenerator
            
            generator = ProjectGenerator()
            project_dir = await generator.create_project(
                name=name,
                project_type='full-stack',
                features=['api', 'frontend', 'database']
            )
            
            return CommandResult(
                True,
                {"message": f"Project {name} created at {project_dir}"}
            )
        except Exception as e:
            return CommandResult(False, None, str(e))
    
    async def _list_projects(self) -> CommandResult:
        """List projects"""
        try:
            # Find project directories
            projects = []
            project_root = Path.home() / '.nexus' / 'projects'
            
            if project_root.exists():
                for project_dir in project_root.iterdir():
                    if project_dir.is_dir():
                        config_file = project_dir / 'nexus.yaml'
                        if config_file.exists():
                            with open(config_file) as f:
                                config = yaml.safe_load(f)
                            
                            projects.append({
                                'name': config.get('name', project_dir.name),
                                'type': config.get('type', 'unknown'),
                                'path': str(project_dir),
                                'created': datetime.fromtimestamp(
                                    config_file.stat().st_ctime
                                ).isoformat()
                            })
            
            return CommandResult(True, projects)
        except Exception as e:
            return CommandResult(False, None, str(e))
    
    async def _build_project(self, name: str) -> CommandResult:
        """Build project"""
        try:
            project_dir = Path.home() / '.nexus' / 'projects' / name
            
            if not project_dir.exists():
                return CommandResult(False, None, f"Project {name} not found")
            
            # Run build command
            process = await asyncio.create_subprocess_exec(
                'make', 'build',
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return CommandResult(
                    True,
                    {"message": f"Project {name} built successfully"}
                )
            else:
                return CommandResult(
                    False,
                    None,
                    stderr.decode()
                )
        except Exception as e:
            return CommandResult(False, None, str(e))


# Script Executor
class ScriptExecutor:
    """Execute NEXUS scripts"""
    
    def __init__(self, cli):
        self.cli = cli
        self.variables = {}
        self.console = Console()
    
    async def execute_file(self, filepath: Path) -> bool:
        """Execute script file"""
        if not filepath.exists():
            self.console.print(f"[red]Script not found: {filepath}[/red]")
            return False
        
        self.console.print(f"[cyan]Executing script: {filepath}[/cyan]")
        
        with open(filepath) as f:
            lines = f.readlines()
        
        return await self.execute_lines(lines)
    
    async def execute_lines(self, lines: List[str]) -> bool:
        """Execute multiple script lines"""
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Variable substitution
            line = self._substitute_variables(line)
            
            # Execute line
            try:
                await self.execute_line(line)
            except Exception as e:
                self.console.print(
                    f"[red]Error on line {i}: {e}[/red]"
                )
                return False
        
        return True
    
    async def execute_line(self, line: str) -> Any:
        """Execute single script line"""
        # Handle variable assignment
        if '=' in line and not line.startswith('nexus'):
            var_name, value = line.split('=', 1)
            var_name = var_name.strip()
            value = value.strip()
            
            # Evaluate value
            if value.startswith('`') and value.endswith('`'):
                # Command substitution
                cmd = value[1:-1]
                result = await self.cli.execute_command(cmd)
                if result.success:
                    self.variables[var_name] = result.output
            else:
                # Direct assignment
                self.variables[var_name] = value
            
            return None
        
        # Handle control structures
        if line.startswith('if '):
            # Simple if statement
            condition = line[3:].strip()
            # TODO: Implement condition evaluation
            return True
        
        # Execute as command
        return await self.cli.execute_command(line)
    
    def _substitute_variables(self, line: str) -> str:
        """Substitute variables in line"""
        for var_name, value in self.variables.items():
            line = line.replace(f"${{{var_name}}}", str(value))
            line = line.replace(f"${var_name}", str(value))
        return line


# Main CLI Class
class NexusCLI:
    """NEXUS Production CLI"""
    
    def __init__(self, api_url: str = "http://localhost:8080"):
        self.api_url = api_url
        self.console = Console()
        self.nlp_processor = NLPProcessor()
        self.script_executor = ScriptExecutor(self)
        self.history_file = Path.home() / '.nexus' / 'cli_history'
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Command registry
        self.commands = {
            'service': ServiceCommand(self),
            'project': ProjectCommand(self),
            'help': self._help_command,
            'exit': self._exit_command,
            'clear': self._clear_command
        }
        
        # Setup prompt
        self.session = PromptSession(
            history=FileHistory(str(self.history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            completer=NexusCompleter(self),
            style=self._get_style()
        )
    
    def _get_style(self) -> Style:
        """Get prompt style"""
        return Style.from_dict({
            'prompt': '#00aa00 bold',
            'input': '#ffffff',
            'output': '#aaaaaa'
        })
    
    async def run_interactive(self):
        """Run interactive mode"""
        self._print_banner()
        
        while True:
            try:
                # Get input
                user_input = await self.session.prompt_async(
                    'nexus> ',
                    multiline=False
                )
                
                if not user_input.strip():
                    continue
                
                # Check for natural language
                if not user_input.startswith('nexus') and not user_input.startswith('!'):
                    # Try to parse as natural language
                    parsed = self.nlp_processor.parse_command(user_input)
                    
                    if parsed['intent'] != 'unknown':
                        suggested = self.nlp_processor.suggest_command(parsed)
                        if suggested:
                            self.console.print(
                                f"[dim]Interpreted as: {suggested}[/dim]"
                            )
                            user_input = suggested
                        else:
                            self.console.print(
                                "[yellow]Could not interpret command. "
                                "Try 'help' for available commands.[/yellow]"
                            )
                            continue
                
                # Execute command
                result = await self.execute_command(user_input)
                
                # Display result
                if result.success:
                    if result.output:
                        output = self._format_output(result.output)
                        self.console.print(output)
                else:
                    self.console.print(f"[red]Error: {result.error}[/red]")
                
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
    
    async def run_batch(self, commands: List[str]):
        """Run commands in batch mode"""
        for cmd in commands:
            self.console.print(f"[cyan]> {cmd}[/cyan]")
            result = await self.execute_command(cmd)
            
            if result.success:
                if result.output:
                    self.console.print(self._format_output(result.output))
            else:
                self.console.print(f"[red]Error: {result.error}[/red]")
                return False
        
        return True
    
    async def run_script(self, script_path: Path):
        """Run a script file"""
        return await self.script_executor.execute_file(script_path)
    
    async def execute_command(self, command: str) -> CommandResult:
        """Execute a command"""
        import time
        start_time = time.time()
        
        # Parse command
        if command.startswith('!'):
            # Shell command
            return await self._execute_shell(command[1:])
        
        # Remove 'nexus' prefix if present
        if command.startswith('nexus '):
            command = command[6:]
        
        # Split into parts
        parts = shlex.split(command)
        if not parts:
            return CommandResult(False, None, "Empty command")
        
        cmd_name = parts[0]
        args = parts[1:]
        
        # Execute command
        if cmd_name in self.commands:
            handler = self.commands[cmd_name]
            
            if isinstance(handler, Command):
                result = await handler.execute(args)
            else:
                result = await handler(args)
            
            # Add duration
            result.duration = time.time() - start_time
            return result
        else:
            return CommandResult(
                False,
                None,
                f"Unknown command: {cmd_name}. Try 'help'"
            )
    
    async def _execute_shell(self, command: str) -> CommandResult:
        """Execute shell command"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return CommandResult(True, stdout.decode())
            else:
                return CommandResult(False, None, stderr.decode())
        except Exception as e:
            return CommandResult(False, None, str(e))
    
    async def _help_command(self, args: List[str]) -> CommandResult:
        """Show help"""
        help_text = """
NEXUS CLI Commands:

Service Management:
  service list              List all services
  service start <name>      Start a service
  service stop <name>       Stop a service
  service status [name]     Show service status

Project Management:
  project init <name>       Initialize new project
  project list             List all projects
  project build <name>     Build a project

System Commands:
  help                     Show this help
  clear                    Clear screen
  exit                     Exit CLI

Natural Language:
  You can also use natural language commands like:
  - "start the api service"
  - "show me all services"
  - "create a new project called myapp"

Shell Commands:
  !<command>               Execute shell command

Script Execution:
  nexus --script <file>    Execute script file
        """
        return CommandResult(True, help_text)
    
    async def _exit_command(self, args: List[str]) -> CommandResult:
        """Exit CLI"""
        self.console.print("[yellow]Goodbye![/yellow]")
        sys.exit(0)
    
    async def _clear_command(self, args: List[str]) -> CommandResult:
        """Clear screen"""
        os.system('clear' if os.name != 'nt' else 'cls')
        return CommandResult(True, None)
    
    def _print_banner(self):
        """Print CLI banner"""
        banner = """
╔═══════════════════════════════════════════╗
║     NEXUS Mind Repository CLI v1.0.0      ║
║                                           ║
║  Type 'help' for commands                 ║
║  Use natural language or structured cmds  ║
║  Press Ctrl+C to cancel, Ctrl+D to exit   ║
╚═══════════════════════════════════════════╝
        """
        self.console.print(banner, style="cyan")
    
    def _format_output(self, data: Any) -> str:
        """Format output for display"""
        # Determine format based on data type
        if isinstance(data, str):
            return data
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            # Table format for list of dicts
            return ServiceCommand(self).format_output(data, 'table')
        else:
            # JSON format for everything else
            return ServiceCommand(self).format_output(data, 'json')


# Remote Execution
class RemoteExecutor:
    """Execute commands on remote NEXUS instances"""
    
    def __init__(self, host: str, port: int = 8080, token: Optional[str] = None):
        self.base_url = f"http://{host}:{port}"
        self.token = token
        self.console = Console()
    
    async def execute(self, command: str) -> CommandResult:
        """Execute command remotely"""
        headers = {}
        if self.token:
            headers['Authorization'] = f"Bearer {self.token}"
        
        try:
            response = requests.post(
                f"{self.base_url}/cli/execute",
                json={'command': command},
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            return CommandResult(
                data['success'],
                data.get('output'),
                data.get('error')
            )
        except Exception as e:
            return CommandResult(False, None, str(e))


# Plugin Support
class CLIPlugin(ABC):
    """Base class for CLI plugins"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name"""
        pass
    
    @property
    @abstractmethod
    def commands(self) -> Dict[str, Callable]:
        """Plugin commands"""
        pass
    
    @abstractmethod
    async def initialize(self, cli: NexusCLI):
        """Initialize plugin"""
        pass


class PluginManager:
    """Manage CLI plugins"""
    
    def __init__(self, cli: NexusCLI):
        self.cli = cli
        self.plugins: Dict[str, CLIPlugin] = {}
        self.plugin_dir = Path.home() / '.nexus' / 'cli_plugins'
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
    
    async def load_plugins(self):
        """Load all plugins"""
        for plugin_file in self.plugin_dir.glob('*.py'):
            try:
                await self.load_plugin(plugin_file)
            except Exception as e:
                print(f"Failed to load plugin {plugin_file}: {e}")
    
    async def load_plugin(self, plugin_path: Path):
        """Load a single plugin"""
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(
            plugin_path.stem,
            plugin_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find plugin class
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, CLIPlugin) and 
                attr != CLIPlugin):
                
                # Create instance
                plugin = attr()
                await plugin.initialize(self.cli)
                
                # Register commands
                for cmd_name, handler in plugin.commands.items():
                    self.cli.commands[f"{plugin.name}:{cmd_name}"] = handler
                
                self.plugins[plugin.name] = plugin
                print(f"Loaded plugin: {plugin.name}")


# Main CLI entry point
@click.command()
@click.option('--api-url', default='http://localhost:8080', help='NEXUS API URL')
@click.option('--script', type=click.Path(exists=True), help='Execute script file')
@click.option('--command', '-c', help='Execute single command')
@click.option('--remote', help='Remote host for execution')
@click.option('--token', help='Authentication token for remote execution')
@click.option('--format', type=click.Choice(['json', 'yaml', 'table']), default='json')
@click.option('--batch', type=click.Path(exists=True), help='Execute batch file')
def main(api_url, script, command, remote, token, format, batch):
    """NEXUS Production CLI"""
    
    async def run():
        # Setup CLI
        if remote:
            # Remote execution mode
            executor = RemoteExecutor(remote, token=token)
            
            if command:
                result = await executor.execute(command)
                if result.success:
                    print(result.output)
                else:
                    print(f"Error: {result.error}", file=sys.stderr)
                    sys.exit(1)
            else:
                print("Remote interactive mode not supported")
                sys.exit(1)
        else:
            # Local execution
            cli = NexusCLI(api_url)
            
            # Load plugins
            plugin_manager = PluginManager(cli)
            await plugin_manager.load_plugins()
            
            if script:
                # Script mode
                success = await cli.run_script(Path(script))
                sys.exit(0 if success else 1)
            elif command:
                # Single command mode
                result = await cli.execute_command(command)
                if result.success:
                    if result.output:
                        print(cli._format_output(result.output))
                else:
                    print(f"Error: {result.error}", file=sys.stderr)
                    sys.exit(1)
            elif batch:
                # Batch mode
                with open(batch) as f:
                    commands = [line.strip() for line in f if line.strip()]
                success = await cli.run_batch(commands)
                sys.exit(0 if success else 1)
            else:
                # Interactive mode
                await cli.run_interactive()
    
    # Run async main
    asyncio.run(run())


if __name__ == '__main__':
    main()