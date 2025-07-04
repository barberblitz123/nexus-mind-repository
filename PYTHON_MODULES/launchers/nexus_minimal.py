#!/usr/bin/env python3
"""
NEXUS Minimal Mode
A simplified version that runs without external dependencies
"""

import os
import sys
import asyncio
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
import json

console = Console()

class NexusMinimal:
    """Minimal NEXUS interface for development"""
    
    def __init__(self):
        self.config = self.load_config()
        self.running = True
        
    def load_config(self):
        """Load or create minimal configuration"""
        config_file = Path.home() / '.nexus' / 'config.json'
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        else:
            # Create minimal config
            config = {
                "nexus": {
                    "mode": "minimal",
                    "version": "2.0.0"
                },
                "profile": {
                    "name": os.environ.get('USER', 'Developer')
                }
            }
            
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            return config
    
    def show_banner(self):
        """Show NEXUS banner"""
        banner_text = """
# NEXUS MIND 2.0 - Minimal Mode

AI Development Environment running in minimal mode.
Limited features are available without external services.

Commands:
- help     : Show available commands
- chat     : Start AI chat (requires API key)
- create   : Create a new project
- status   : Show system status
- config   : Edit configuration
- exit     : Exit NEXUS
        """
        
        console.print(Panel(Markdown(banner_text), title="NEXUS 2.0", border_style="cyan"))
        
    def show_help(self):
        """Show help information"""
        help_text = """
## Available Commands

### Basic Commands
- **help** - Show this help message
- **exit/quit** - Exit NEXUS
- **clear** - Clear the screen

### Development Commands
- **create [name]** - Create a new project
- **open [file]** - Open a file in editor
- **run [command]** - Run a shell command

### AI Commands
- **chat** - Start AI chat session
- **ask [question]** - Quick AI question

### System Commands
- **status** - Show system status
- **config** - Edit configuration
- **reload** - Reload configuration
        """
        
        console.print(Markdown(help_text))
        
    def show_status(self):
        """Show system status"""
        console.print("\n[bold cyan]System Status[/bold cyan]\n")
        
        # Basic info
        console.print(f"Mode: [yellow]Minimal[/yellow]")
        console.print(f"Version: 2.0.0")
        console.print(f"User: {self.config.get('profile', {}).get('name', 'Unknown')}")
        console.print(f"Python: {sys.version.split()[0]}")
        
        # Check services
        console.print("\n[bold]Services:[/bold]")
        console.print("  • Terminal UI: [green]Running[/green]")
        console.print("  • API Server: [yellow]Not available (minimal mode)[/yellow]")
        console.print("  • Database: [yellow]Not available (minimal mode)[/yellow]")
        console.print("  • Redis: [yellow]Not available (minimal mode)[/yellow]")
        
        # Features
        console.print("\n[bold]Available Features:[/bold]")
        console.print("  • Basic project creation")
        console.print("  • File operations")
        console.print("  • Shell commands")
        console.print("  • Configuration management")
        
        api_key = os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('OPENAI_API_KEY')
        if api_key:
            console.print("  • AI Chat: [green]Available[/green]")
        else:
            console.print("  • AI Chat: [yellow]Requires API key[/yellow]")
            
    def create_project(self, name: str = None):
        """Create a new project"""
        if not name:
            name = Prompt.ask("Project name")
            
        project_dir = Path(name)
        if project_dir.exists():
            console.print(f"[red]Error: Directory '{name}' already exists[/red]")
            return
            
        console.print(f"\nCreating project: {name}")
        
        # Create basic structure
        project_dir.mkdir()
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()
        (project_dir / "docs").mkdir()
        
        # Create files
        (project_dir / "README.md").write_text(f"# {name}\n\nCreated with NEXUS 2.0\n")
        (project_dir / "requirements.txt").write_text("")
        (project_dir / ".gitignore").write_text("__pycache__/\n*.pyc\n.env\nvenv/\n")
        (project_dir / "src" / "__init__.py").write_text("")
        (project_dir / "src" / "main.py").write_text('#!/usr/bin/env python3\n\ndef main():\n    print("Hello from NEXUS!")\n\nif __name__ == "__main__":\n    main()\n')
        
        console.print(f"[green]✓ Project '{name}' created successfully![/green]")
        console.print(f"\nTo get started:")
        console.print(f"  cd {name}")
        console.print(f"  python src/main.py")
        
    def run_command(self, command: str = None):
        """Run a shell command"""
        if not command:
            command = Prompt.ask("Command")
            
        console.print(f"\n[dim]Running: {command}[/dim]\n")
        os.system(command)
        
    def chat_session(self):
        """Simple chat interface"""
        console.print("\n[bold cyan]AI Chat Session[/bold cyan]")
        console.print("[dim]Type 'exit' to end chat[/dim]\n")
        
        # Check for API key
        api_key = os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('OPENAI_API_KEY')
        if not api_key:
            console.print("[yellow]No API key found. AI features are not available.[/yellow]")
            console.print("Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable.")
            return
            
        console.print("[yellow]Note: In minimal mode, AI chat is simulated[/yellow]\n")
        
        while True:
            user_input = Prompt.ask("[bold]You[/bold]")
            
            if user_input.lower() in ['exit', 'quit']:
                break
                
            # Simulated response
            console.print("\n[bold cyan]NEXUS[/bold cyan]: I'm running in minimal mode without AI services.")
            console.print("In full mode, I would help you with: " + user_input + "\n")
            
    async def run(self):
        """Main run loop"""
        self.show_banner()
        
        while self.running:
            try:
                # Get user input
                command = Prompt.ask("\n[bold cyan]nexus[/bold cyan]").strip().lower()
                
                if not command:
                    continue
                    
                # Parse command
                parts = command.split(maxsplit=1)
                cmd = parts[0]
                args = parts[1] if len(parts) > 1 else None
                
                # Execute command
                if cmd in ['exit', 'quit']:
                    self.running = False
                    console.print("\n[cyan]Goodbye! 👋[/cyan]")
                    
                elif cmd == 'help':
                    self.show_help()
                    
                elif cmd == 'clear':
                    console.clear()
                    self.show_banner()
                    
                elif cmd == 'status':
                    self.show_status()
                    
                elif cmd == 'create':
                    self.create_project(args)
                    
                elif cmd == 'run':
                    self.run_command(args)
                    
                elif cmd == 'chat':
                    self.chat_session()
                    
                elif cmd == 'ask':
                    if args:
                        console.print(f"\n[yellow]AI response would appear here for: {args}[/yellow]")
                    else:
                        console.print("[red]Please provide a question[/red]")
                        
                elif cmd == 'config':
                    console.print("\n[yellow]Configuration editor not available in minimal mode[/yellow]")
                    console.print(f"Edit manually: {Path.home() / '.nexus' / 'config.json'}")
                    
                elif cmd == 'reload':
                    self.config = self.load_config()
                    console.print("[green]Configuration reloaded[/green]")
                    
                else:
                    console.print(f"[red]Unknown command: {cmd}[/red]")
                    console.print("Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")


def main():
    """Entry point"""
    # Create and run minimal NEXUS
    nexus = NexusMinimal()
    
    try:
        asyncio.run(nexus.run())
    except KeyboardInterrupt:
        console.print("\n\n[cyan]Goodbye! 👋[/cyan]")
        

if __name__ == "__main__":
    main()