#!/usr/bin/env python3
"""
NEXUS Complete System Launcher
The ultimate AI pair programmer that lives in your terminal
"""

import asyncio
import subprocess
import sys
import os
import time
import signal
import json
import shutil
import platform
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.align import Align
from rich.text import Text
from rich import box

console = Console()

# ASCII Art Banner
NEXUS_BANNER = """
[bold cyan]
███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
[/bold cyan]
[dim white]Your AI Pair Programmer • Omnipotent • Omniscient • Omnipresent[/dim white]
"""

class NEXUSCompleteLauncher:
    def __init__(self):
        self.console = console
        self.processes: Dict[str, subprocess.Popen] = {}
        self.config = self._load_config()
        self.startup_sequence = []
        self.health_checks_passed = False
        self.launch_time = None
        
    def _load_config(self) -> dict:
        """Load complete NEXUS configuration"""
        return {
            "services": {
                # Core Services
                "consciousness_core": {
                    "name": "🧠 Consciousness Core",
                    "command": "python nexus-mobile-project/backend/central-consciousness-core/consciousness_core_real.py",
                    "port": 8080,
                    "health_endpoint": "/health",
                    "required": True,
                    "startup_delay": 2,
                    "description": "Real Claude-based consciousness"
                },
                "integration_hub": {
                    "name": "🔌 Integration Hub",
                    "command": "python nexus_integration_hub.py",
                    "port": 8081,
                    "health_endpoint": "/api/health",
                    "required": True,
                    "startup_delay": 2,
                    "description": "Central event bus and API gateway"
                },
                "manus_agent": {
                    "name": "🤖 MANUS Agent",
                    "command": "python manus_nexus_integration.py",
                    "port": 8002,
                    "health_endpoint": "/api/stats",
                    "required": True,
                    "startup_delay": 3,
                    "description": "Continuous autonomous work agent"
                },
                
                # UI Services
                "terminal_ui": {
                    "name": "💻 Terminal UI",
                    "command": "python nexus_terminal_ui_advanced.py",
                    "port": None,
                    "required": False,
                    "startup_delay": 1,
                    "description": "Advanced terminal interface"
                },
                "voice_control": {
                    "name": "🎤 Voice Control",
                    "command": "python nexus_voice_control.py",
                    "port": 8004,
                    "health_endpoint": "/health",
                    "required": False,
                    "startup_delay": 2,
                    "description": "Voice command interface"
                },
                "vision_processor": {
                    "name": "👁️ Vision Processor",
                    "command": "python nexus_vision_processor.py",
                    "port": 8005,
                    "health_endpoint": "/health",
                    "required": False,
                    "startup_delay": 2,
                    "description": "Screenshot and image analysis"
                },
                
                # Development Services
                "project_generator": {
                    "name": "🏗️ Project Generator",
                    "command": "python nexus_project_generator.py",
                    "port": 8006,
                    "health_endpoint": "/health",
                    "required": False,
                    "startup_delay": 2,
                    "description": "Lovable-style app generation"
                },
                "code_analyzer": {
                    "name": "🔍 Code Analyzer",
                    "command": "python nexus_performance_analyzer.py",
                    "port": 8007,
                    "health_endpoint": "/health",
                    "required": False,
                    "startup_delay": 2,
                    "description": "Performance and bug detection"
                },
                
                # Web Interfaces (Optional)
                "web_dashboard": {
                    "name": "🌐 Web Dashboard",
                    "command": "cd nexus-web-app && npm start",
                    "port": 3000,
                    "health_endpoint": "/",
                    "required": False,
                    "startup_delay": 5,
                    "description": "React-based web interface"
                },
                "react_dashboard": {
                    "name": "📊 React Dashboard",
                    "command": "cd nexus-web-app/react-dashboard && npm start",
                    "port": 3001,
                    "health_endpoint": "/",
                    "required": False,
                    "startup_delay": 5,
                    "description": "Enhanced React dashboard"
                }
            },
            "environment": {
                "NEXUS_MODE": "production",
                "NEXUS_LOG_LEVEL": "INFO",
                "PYTHONUNBUFFERED": "1",
                "NEXUS_MEMORY_ENABLED": "true",
                "NEXUS_OMNIPOTENT": "true"
            },
            "features": {
                "voice_enabled": True,
                "vision_enabled": True,
                "web_scraping": True,
                "autonomous_mode": True,
                "memory_system": True,
                "consciousness": True
            },
            "theme": "cyberpunk",
            "startup_sound": True,
            "animations": True
        }
    
    def print_banner(self):
        """Print the NEXUS banner with animation"""
        if self.config.get("animations", True):
            # Animated reveal
            lines = NEXUS_BANNER.strip().split('\n')
            for line in lines:
                self.console.print(line)
                time.sleep(0.05)
        else:
            self.console.print(NEXUS_BANNER)
        
        # System info
        info_panel = Panel(
            f"[bold white]Version:[/bold white] 2.0.0\n"
            f"[bold white]Platform:[/bold white] {platform.system()} {platform.machine()}\n"
            f"[bold white]Python:[/bold white] {sys.version.split()[0]}\n"
            f"[bold white]Mode:[/bold white] {self.config['environment']['NEXUS_MODE']}",
            title="[bold cyan]System Information[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(info_panel)
    
    def check_prerequisites(self) -> bool:
        """Check all prerequisites are met"""
        self.console.print("\n[bold]🔍 Checking prerequisites...[/bold]\n")
        
        checks = [
            ("Python 3.8+", self._check_python),
            ("Node.js", self._check_node),
            ("npm", self._check_npm),
            ("Git", self._check_git),
            ("Required Python packages", self._check_python_packages),
            ("Network connectivity", self._check_network),
            ("Available ports", self._check_ports),
            ("Disk space", self._check_disk_space),
        ]
        
        all_passed = True
        table = Table(title="Prerequisite Checks", box=box.ROUNDED)
        table.add_column("Component", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Details")
        
        for name, check_func in checks:
            status, details = check_func()
            if status:
                table.add_row(name, "[green]✓ PASS[/green]", details)
            else:
                table.add_row(name, "[red]✗ FAIL[/red]", details)
                all_passed = False
        
        self.console.print(table)
        return all_passed
    
    def _check_python(self) -> Tuple[bool, str]:
        """Check Python version"""
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            return True, f"Python {version.major}.{version.minor}.{version.micro}"
        return False, f"Python {version.major}.{version.minor} (3.8+ required)"
    
    def _check_node(self) -> Tuple[bool, str]:
        """Check Node.js installation"""
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                return True, result.stdout.strip()
            return False, "Not installed"
        except:
            return False, "Not found in PATH"
    
    def _check_npm(self) -> Tuple[bool, str]:
        """Check npm installation"""
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                return True, f"npm {result.stdout.strip()}"
            return False, "Not installed"
        except:
            return False, "Not found in PATH"
    
    def _check_git(self) -> Tuple[bool, str]:
        """Check Git installation"""
        try:
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                return True, result.stdout.strip()
            return False, "Not installed"
        except:
            return False, "Not found in PATH"
    
    def _check_python_packages(self) -> Tuple[bool, str]:
        """Check required Python packages"""
        required = [
            'fastapi', 'uvicorn', 'aiohttp', 'rich', 'click',
            'numpy', 'pandas', 'websockets', 'psutil'
        ]
        missing = []
        
        for package in required:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        if missing:
            return False, f"Missing: {', '.join(missing)}"
        return True, "All packages installed"
    
    def _check_network(self) -> Tuple[bool, str]:
        """Check network connectivity"""
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True, "Internet connection available"
        except:
            return True, "Local mode (no internet)"
    
    def _check_ports(self) -> Tuple[bool, str]:
        """Check if required ports are available"""
        required_ports = [8080, 8081, 8002, 8004, 8005, 8006, 8007]
        blocked = []
        
        for port in required_ports:
            try:
                import socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
            except:
                blocked.append(str(port))
        
        if blocked:
            return False, f"Ports in use: {', '.join(blocked)}"
        return True, "All ports available"
    
    def _check_disk_space(self) -> Tuple[bool, str]:
        """Check available disk space"""
        import shutil
        stat = shutil.disk_usage(".")
        free_gb = stat.free / (1024 ** 3)
        
        if free_gb < 1:
            return False, f"{free_gb:.1f}GB free (1GB required)"
        return True, f"{free_gb:.1f}GB free"
    
    async def start_services(self):
        """Start all NEXUS services with progress tracking"""
        self.launch_time = datetime.now()
        
        # Filter services based on configuration
        services_to_start = {}
        for service_id, service_config in self.config['services'].items():
            if service_config.get('required', False):
                services_to_start[service_id] = service_config
            elif service_id == 'terminal_ui':
                # Always include terminal UI unless specifically disabled
                services_to_start[service_id] = service_config
            elif service_id == 'voice_control' and self.config['features']['voice_enabled']:
                services_to_start[service_id] = service_config
            elif service_id == 'vision_processor' and self.config['features']['vision_enabled']:
                services_to_start[service_id] = service_config
        
        total_services = len(services_to_start)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task("🚀 Starting NEXUS services...", total=total_services)
            
            for service_id, service_config in services_to_start.items():
                name = service_config['name']
                desc = service_config.get('description', '')
                
                progress.update(task, description=f"Starting {name}...")
                
                success = await self._start_service(service_id, service_config)
                
                if success:
                    self.startup_sequence.append({
                        'service': name,
                        'status': 'started',
                        'time': datetime.now()
                    })
                    self.console.print(f"✓ {name} - {desc}")
                else:
                    self.console.print(f"[red]✗ Failed to start {name}[/red]")
                    if service_config.get('required', False):
                        raise Exception(f"Required service {name} failed to start")
                
                progress.advance(task)
        
        # Perform health checks
        await self._perform_health_checks(services_to_start)
    
    async def _start_service(self, service_id: str, service_config: dict) -> bool:
        """Start a single service"""
        command = service_config['command']
        env = os.environ.copy()
        env.update(self.config['environment'])
        
        try:
            if command.startswith('cd '):
                # Handle directory change commands
                parts = command.split(' && ')
                cwd = parts[0].replace('cd ', '')
                cmd = ' '.join(parts[1:])
                
                # Check if directory exists
                if not os.path.exists(cwd):
                    self.console.print(f"[yellow]Directory {cwd} not found, skipping[/yellow]")
                    return False
                
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    cwd=cwd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            self.processes[service_id] = process
            
            # Wait for startup
            await asyncio.sleep(service_config.get('startup_delay', 2))
            
            # Check if process is still running
            if process.poll() is not None:
                return False
            
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error starting service: {e}[/red]")
            return False
    
    async def _perform_health_checks(self, services: Dict[str, dict]):
        """Perform health checks on started services"""
        self.console.print("\n[bold]🏥 Performing health checks...[/bold]\n")
        
        healthy_services = 0
        total_services = len([s for s in services.values() if s.get('port')])
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Checking service health...", total=total_services)
            
            for service_id, service_config in services.items():
                if not service_config.get('port'):
                    continue
                
                name = service_config['name']
                healthy = await self._check_service_health(service_config)
                
                if healthy:
                    healthy_services += 1
                    self.console.print(f"✓ {name} is [green]healthy[/green]")
                else:
                    self.console.print(f"✗ {name} is [red]unhealthy[/red]")
                
                progress.advance(task)
        
        self.health_checks_passed = (healthy_services == total_services)
        
        if self.health_checks_passed:
            self.console.print("\n[bold green]✨ All services are healthy![/bold green]")
        else:
            self.console.print(f"\n[yellow]⚠️ {total_services - healthy_services} services unhealthy[/yellow]")
    
    async def _check_service_health(self, service_config: dict) -> bool:
        """Check if a service is healthy"""
        if not service_config.get('port'):
            return True
        
        import aiohttp
        
        url = f"http://localhost:{service_config['port']}{service_config.get('health_endpoint', '/')}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    return response.status < 500
        except:
            return False
    
    def show_startup_summary(self):
        """Show startup summary and access information"""
        # Calculate startup time
        startup_time = (datetime.now() - self.launch_time).total_seconds()
        
        # Create summary panel
        summary = Panel(
            f"[bold green]🎉 NEXUS is ready![/bold green]\n\n"
            f"[bold]Startup time:[/bold] {startup_time:.1f} seconds\n"
            f"[bold]Services started:[/bold] {len(self.startup_sequence)}\n"
            f"[bold]Health status:[/bold] {'✓ All healthy' if self.health_checks_passed else '⚠️ Some unhealthy'}\n\n"
            f"[bold cyan]Access Points:[/bold cyan]\n"
            f"  • Terminal UI: Run 'nexus' command\n"
            f"  • Web Interface: http://localhost:8002\n"
            f"  • API Gateway: http://localhost:8081\n"
            f"  • Voice Control: Say 'Hey NEXUS'\n\n"
            f"[bold cyan]Quick Commands:[/bold cyan]\n"
            f"  • nexus create <project> - Create new project\n"
            f"  • nexus chat - Open chat interface\n"
            f"  • nexus status - Check system status\n"
            f"  • nexus help - Show all commands\n\n"
            f"[dim]Press Ctrl+C to stop all services[/dim]",
            title="[bold cyan]NEXUS Startup Complete[/bold cyan]",
            border_style="cyan",
            box=box.DOUBLE
        )
        
        self.console.print("\n")
        self.console.print(summary)
        
        # Play startup sound if enabled
        if self.config.get('startup_sound', True):
            self._play_startup_sound()
    
    def _play_startup_sound(self):
        """Play startup sound effect"""
        try:
            # Simple beep for now
            if platform.system() == "Darwin":  # macOS
                os.system("afplay /System/Library/Sounds/Glass.aiff")
            elif platform.system() == "Linux":
                os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null")
            elif platform.system() == "Windows":
                import winsound
                winsound.Beep(1000, 200)
        except:
            pass  # Ignore sound errors
    
    async def monitor_loop(self):
        """Main monitoring loop with live dashboard"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=4)
        )
        
        # Header
        header_text = Text("NEXUS System Monitor", style="bold cyan")
        layout["header"].update(Panel(Align.center(header_text), border_style="cyan"))
        
        # Footer with instructions
        footer_text = (
            "[bold]Commands:[/bold] "
            "[cyan]r[/cyan]estart service | "
            "[cyan]s[/cyan]top service | "
            "[cyan]l[/cyan]ogs | "
            "[cyan]h[/cyan]elp | "
            "[cyan]q[/cyan]uit"
        )
        layout["footer"].update(Panel(footer_text, border_style="dim"))
        
        with Live(layout, refresh_per_second=1, console=self.console) as live:
            while True:
                # Update body with service status
                layout["body"].update(self._create_status_panel())
                
                await asyncio.sleep(1)
                
                # Check for crashed services
                for service_id, process in list(self.processes.items()):
                    if process.poll() is not None:
                        # Service crashed, attempt restart
                        service_config = self.config['services'].get(service_id)
                        if service_config and service_config.get('required', False):
                            self.console.print(f"\n[yellow]Service {service_config['name']} crashed, restarting...[/yellow]")
                            await self._start_service(service_id, service_config)
    
    def _create_status_panel(self) -> Panel:
        """Create status panel for monitoring"""
        table = Table(box=box.SIMPLE)
        table.add_column("Service", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("PID")
        table.add_column("CPU %", justify="right")
        table.add_column("Memory", justify="right")
        
        try:
            import psutil
            
            for service_id, process in self.processes.items():
                service_config = self.config['services'].get(service_id, {})
                name = service_config.get('name', service_id)
                
                if process.poll() is None:
                    try:
                        proc = psutil.Process(process.pid)
                        cpu_percent = proc.cpu_percent(interval=0.1)
                        memory_mb = proc.memory_info().rss / 1024 / 1024
                        
                        table.add_row(
                            name,
                            "[green]● Running[/green]",
                            str(process.pid),
                            f"{cpu_percent:.1f}%",
                            f"{memory_mb:.1f} MB"
                        )
                    except:
                        table.add_row(
                            name,
                            "[green]● Running[/green]",
                            str(process.pid),
                            "N/A",
                            "N/A"
                        )
                else:
                    table.add_row(
                        name,
                        "[red]● Stopped[/red]",
                        "-",
                        "-",
                        "-"
                    )
        except ImportError:
            # psutil not available
            for service_id, process in self.processes.items():
                service_config = self.config['services'].get(service_id, {})
                name = service_config.get('name', service_id)
                
                if process.poll() is None:
                    table.add_row(name, "[green]● Running[/green]", str(process.pid), "-", "-")
                else:
                    table.add_row(name, "[red]● Stopped[/red]", "-", "-", "-")
        
        return Panel(table, title="Service Status", border_style="cyan")
    
    def shutdown(self, signum=None, frame=None):
        """Gracefully shutdown all services"""
        self.console.print("\n[yellow]🛑 Shutting down NEXUS...[/yellow]")
        
        # Stop services in reverse order
        for service_id in reversed(list(self.processes.keys())):
            process = self.processes[service_id]
            service_config = self.config['services'].get(service_id, {})
            name = service_config.get('name', service_id)
            
            if process and process.poll() is None:
                self.console.print(f"Stopping {name}...")
                process.terminate()
                
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        self.console.print("[green]✓ All services stopped[/green]")
        self.console.print("\n[bold cyan]Thank you for using NEXUS![/bold cyan]")
        sys.exit(0)
    
    async def run(self):
        """Main launcher routine"""
        try:
            # Print banner
            self.print_banner()
            
            # Check prerequisites
            if not self.check_prerequisites():
                self.console.print("\n[red]❌ Prerequisites not met. Please install missing components.[/red]")
                return
            
            # Start services
            self.console.print("\n[bold]🚀 Launching NEXUS...[/bold]\n")
            await self.start_services()
            
            # Show startup summary
            self.show_startup_summary()
            
            # Setup signal handlers
            signal.signal(signal.SIGINT, self.shutdown)
            signal.signal(signal.SIGTERM, self.shutdown)
            
            # Start monitoring
            await self.monitor_loop()
            
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            self.console.print(f"\n[red]❌ Error: {str(e)}[/red]")
            self.shutdown()


@click.command()
@click.option('--minimal', is_flag=True, help='Start only core services')
@click.option('--no-ui', is_flag=True, help='Start without terminal UI')
@click.option('--no-voice', is_flag=True, help='Disable voice control')
@click.option('--no-web', is_flag=True, help='Disable web interfaces')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def main(minimal, no_ui, no_voice, no_web, debug):
    """Launch NEXUS - Your AI Pair Programmer"""
    
    launcher = NEXUSCompleteLauncher()
    
    # Apply command line options
    if minimal:
        # Only start core services
        for service_id in list(launcher.config['services'].keys()):
            if service_id not in ['consciousness_core', 'integration_hub', 'manus_agent']:
                del launcher.config['services'][service_id]
    
    if no_ui:
        if 'terminal_ui' in launcher.config['services']:
            del launcher.config['services']['terminal_ui']
    
    if no_voice:
        launcher.config['features']['voice_enabled'] = False
    
    if no_web:
        for service_id in ['web_dashboard', 'react_dashboard']:
            if service_id in launcher.config['services']:
                del launcher.config['services'][service_id]
    
    if debug:
        launcher.config['environment']['NEXUS_LOG_LEVEL'] = 'DEBUG'
    
    # Run the launcher
    asyncio.run(launcher.run())


if __name__ == "__main__":
    main()