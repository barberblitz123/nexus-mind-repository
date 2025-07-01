#!/usr/bin/env python3
"""
NEXUS 2.0 Simple Launcher
Quick start launcher with minimal configuration
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint
import asyncio

console = Console()

class SimpleNexusUI:
    """Simplified NEXUS launcher for quick start"""
    
    def __init__(self):
        self.home_dir = Path.home() / '.nexus'
        self.config_file = self.home_dir / 'config.json'
        self.project_dir = Path.cwd()
        self.config = self.load_config()
        
    def load_config(self) -> Dict:
        """Load or create minimal configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        
        # Create minimal config
        return {
            'theme': 'dark',
            'auto_detect': True,
            'services': {
                'core': True,
                'web_ui': True,
                'terminal_ui': True
            }
        }
    
    def save_config(self):
        """Save configuration"""
        self.home_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def detect_project_type(self) -> Optional[str]:
        """Auto-detect project type from current directory"""
        detectors = {
            'package.json': 'nodejs',
            'requirements.txt': 'python',
            'Cargo.toml': 'rust',
            'go.mod': 'golang',
            'pom.xml': 'java',
            'build.gradle': 'java',
            'composer.json': 'php',
            'Gemfile': 'ruby',
            '.csproj': 'dotnet',
            'flutter.yaml': 'flutter',
            'Package.swift': 'swift'
        }
        
        for file, project_type in detectors.items():
            if (self.project_dir / file).exists():
                return project_type
            
            # Check for pattern matches
            if '*' in file:
                for path in self.project_dir.glob(file):
                    return project_type
        
        return None
    
    def quick_start_wizard(self):
        """Quick start wizard for new users"""
        console.print("\n[bold cyan]NEXUS Quick Start Wizard[/bold cyan]\n")
        
        # Project detection
        project_type = self.detect_project_type()
        if project_type:
            console.print(f"[green]✓ Detected {project_type} project[/green]")
        else:
            console.print("[yellow]No project detected in current directory[/yellow]")
        
        # Ask what to do
        console.print("\nWhat would you like to do?")
        console.print("1. Start NEXUS in current directory")
        console.print("2. Create a new project")
        console.print("3. Import existing project")
        console.print("4. Configure NEXUS")
        
        choice = Prompt.ask("Select option", choices=['1', '2', '3', '4'])
        
        if choice == '1':
            self.start_nexus()
        elif choice == '2':
            self.create_project()
        elif choice == '3':
            self.import_project()
        elif choice == '4':
            self.configure()
    
    def start_nexus(self):
        """Start NEXUS with minimal configuration"""
        console.print("\n[bold]Starting NEXUS...[/bold]\n")
        
        # Show what will be started
        table = Table(title="NEXUS Services")
        table.add_column("Service", style="cyan")
        table.add_column("Port", style="green")
        table.add_column("Description")
        
        table.add_row("Core API", "8001", "Main NEXUS API")
        table.add_row("Web UI", "8000", "Web interface")
        table.add_row("Terminal UI", "N/A", "This interface")
        
        console.print(table)
        console.print()
        
        if Confirm.ask("Start NEXUS services?"):
            self.launch_services()
    
    def launch_services(self):
        """Launch core NEXUS services"""
        try:
            # Start core services in background
            console.print("[yellow]Starting core services...[/yellow]")
            
            # Check if services are already running
            if self.check_services():
                console.print("[green]✓ Services already running[/green]")
            else:
                # Start services
                self.start_core_service()
                self.start_web_ui()
            
            # Launch terminal UI
            console.print("\n[bold]Launching Terminal UI...[/bold]")
            time.sleep(1)
            
            # Import and run the terminal UI
            try:
                from nexus_terminal_ui import NexusTerminalUI
                ui = NexusTerminalUI()
                asyncio.run(ui.run())
            except ImportError:
                # Fallback to basic interface
                self.basic_terminal_interface()
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down...[/yellow]")
            self.shutdown_services()
    
    def check_services(self) -> bool:
        """Check if services are running"""
        try:
            import requests
            response = requests.get('http://localhost:8001/health', timeout=1)
            return response.status_code == 200
        except:
            return False
    
    def start_core_service(self):
        """Start core NEXUS service"""
        # Try to start using existing launcher
        launcher_candidates = [
            'nexus_core_production.py',
            'nexus_launcher.py',
            'nexus_integration_core.py'
        ]
        
        for launcher in launcher_candidates:
            if Path(launcher).exists():
                subprocess.Popen([sys.executable, launcher], 
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
                console.print(f"[green]✓ Started core service[/green]")
                return
        
        console.print("[red]✗ Core service not found[/red]")
    
    def start_web_ui(self):
        """Start web UI service"""
        ui_candidates = [
            'manus_web_interface_v2.py',
            'simple_nexus_web.py',
            'nexus_web_interface.py'
        ]
        
        for ui in ui_candidates:
            if Path(ui).exists():
                subprocess.Popen([sys.executable, ui],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
                console.print(f"[green]✓ Started web UI[/green]")
                return
        
        console.print("[yellow]! Web UI not found[/yellow]")
    
    def basic_terminal_interface(self):
        """Basic terminal interface when full UI is not available"""
        console.print("\n[bold cyan]NEXUS Terminal (Basic Mode)[/bold cyan]")
        console.print("[dim]Type 'help' for commands, 'exit' to quit[/dim]\n")
        
        while True:
            try:
                command = Prompt.ask("[cyan]nexus[/cyan]")
                
                if command == 'exit':
                    break
                elif command == 'help':
                    self.show_help()
                elif command == 'status':
                    self.show_status()
                elif command.startswith('create '):
                    project_name = command.split(' ', 1)[1]
                    self.create_project(project_name)
                elif command == 'web':
                    console.print("[cyan]Web UI available at: http://localhost:8000[/cyan]")
                else:
                    console.print(f"[red]Unknown command: {command}[/red]")
                    
            except KeyboardInterrupt:
                break
        
        console.print("\n[yellow]Goodbye![/yellow]")
    
    def show_help(self):
        """Show help information"""
        help_text = """
[bold]NEXUS Commands:[/bold]
  help     - Show this help
  status   - Show service status
  create   - Create new project
  web      - Show web UI URL
  exit     - Exit NEXUS
  
[bold]Examples:[/bold]
  create myapp     - Create a new project called 'myapp'
  status          - Check if services are running
        """
        console.print(help_text)
    
    def show_status(self):
        """Show service status"""
        services = {
            'Core API': 'http://localhost:8001/health',
            'Web UI': 'http://localhost:8000',
            'Memory System': 'http://localhost:8001/memory/status'
        }
        
        table = Table(title="Service Status")
        table.add_column("Service", style="cyan")
        table.add_column("Status")
        table.add_column("URL")
        
        for service, url in services.items():
            try:
                import requests
                response = requests.get(url, timeout=1)
                status = "[green]● Running[/green]" if response.status_code < 500 else "[yellow]● Error[/yellow]"
            except:
                status = "[red]● Offline[/red]"
            
            table.add_row(service, status, url)
        
        console.print(table)
    
    def create_project(self, name: Optional[str] = None):
        """Create a new project"""
        if not name:
            name = Prompt.ask("Project name")
        
        project_type = Prompt.ask(
            "Project type",
            choices=['python', 'nodejs', 'react', 'vue', 'api', 'fullstack'],
            default='python'
        )
        
        console.print(f"\n[yellow]Creating {project_type} project: {name}...[/yellow]")
        
        # Send to NEXUS if available
        if self.check_services():
            try:
                import requests
                response = requests.post('http://localhost:8001/projects/create', json={
                    'name': name,
                    'type': project_type
                })
                if response.status_code == 200:
                    console.print(f"[green]✓ Project '{name}' created successfully![/green]")
                else:
                    console.print(f"[red]✗ Failed to create project[/red]")
            except:
                console.print(f"[red]✗ Could not connect to NEXUS services[/red]")
        else:
            # Fallback to basic creation
            project_path = Path(name)
            project_path.mkdir(exist_ok=True)
            
            # Create basic structure based on type
            if project_type == 'python':
                (project_path / 'requirements.txt').touch()
                (project_path / 'main.py').write_text('#!/usr/bin/env python3\n\nprint("Hello from NEXUS!")\n')
                (project_path / 'README.md').write_text(f'# {name}\n\nCreated with NEXUS\n')
            
            console.print(f"[green]✓ Basic project structure created at: {project_path}[/green]")
    
    def import_project(self):
        """Import existing project"""
        path = Prompt.ask("Project path", default=".")
        project_path = Path(path).resolve()
        
        if not project_path.exists():
            console.print(f"[red]Path does not exist: {project_path}[/red]")
            return
        
        # Detect project type
        os.chdir(project_path)
        project_type = self.detect_project_type()
        
        if project_type:
            console.print(f"[green]✓ Detected {project_type} project at: {project_path}[/green]")
            
            # Create NEXUS config for project
            nexus_config = {
                'project_type': project_type,
                'path': str(project_path),
                'imported_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(project_path / '.nexus.json', 'w') as f:
                json.dump(nexus_config, f, indent=2)
            
            console.print("[green]✓ Project imported successfully![/green]")
            
            if Confirm.ask("Start NEXUS for this project?"):
                self.start_nexus()
        else:
            console.print("[yellow]Could not detect project type[/yellow]")
            if Confirm.ask("Import anyway?"):
                console.print("[green]✓ Project imported[/green]")
    
    def configure(self):
        """Configure NEXUS settings"""
        console.print("\n[bold cyan]NEXUS Configuration[/bold cyan]\n")
        
        # Theme
        theme = Prompt.ask("Theme", choices=['dark', 'light', 'auto'], default=self.config.get('theme', 'dark'))
        self.config['theme'] = theme
        
        # Auto-detect
        auto_detect = Confirm.ask("Enable project auto-detection?", default=self.config.get('auto_detect', True))
        self.config['auto_detect'] = auto_detect
        
        # Services
        console.print("\n[bold]Services to enable:[/bold]")
        self.config['services']['core'] = Confirm.ask("Core API?", default=True)
        self.config['services']['web_ui'] = Confirm.ask("Web UI?", default=True)
        self.config['services']['terminal_ui'] = Confirm.ask("Terminal UI?", default=True)
        
        # Save
        self.save_config()
        console.print("\n[green]✓ Configuration saved![/green]")
    
    def shutdown_services(self):
        """Shutdown all services"""
        console.print("[yellow]Shutting down services...[/yellow]")
        
        # Try graceful shutdown via API
        try:
            import requests
            requests.post('http://localhost:8001/shutdown')
        except:
            pass
        
        console.print("[green]✓ Services stopped[/green]")
    
    def run(self):
        """Main entry point"""
        # Show welcome
        banner = Panel.fit(
            "[bold cyan]NEXUS 2.0[/bold cyan]\n"
            "AI Development Platform\n"
            "[dim]Simple Mode[/dim]",
            border_style="cyan"
        )
        console.print(banner)
        
        # Check if first run
        if not self.config_file.exists():
            self.quick_start_wizard()
            self.save_config()
        else:
            # Show menu
            console.print("\n[bold]What would you like to do?[/bold]")
            console.print("1. Start NEXUS")
            console.print("2. Create new project")
            console.print("3. Configure")
            console.print("4. Exit")
            
            choice = Prompt.ask("Select", choices=['1', '2', '3', '4'])
            
            if choice == '1':
                self.start_nexus()
            elif choice == '2':
                self.create_project()
            elif choice == '3':
                self.configure()

def main():
    """Main entry point"""
    ui = SimpleNexusUI()
    try:
        ui.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")

if __name__ == '__main__':
    main()