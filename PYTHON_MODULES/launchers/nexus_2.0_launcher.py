#!/usr/bin/env python3
"""
NEXUS 2.0 Unified Launcher
Starts all NEXUS systems with proper sequencing and health checks
"""

import asyncio
import subprocess
import sys
import os
import time
import signal
import json
import psutil
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout

console = Console()

class NEXUSLauncher:
    def __init__(self, config_file: Optional[str] = None):
        self.console = console
        self.processes: Dict[str, subprocess.Popen] = {}
        self.config = self.load_config(config_file)
        self.health_check_interval = 5
        self.startup_timeout = 60
        self.shutdown_handlers = []
        
    def load_config(self, config_file: Optional[str]) -> dict:
        """Load configuration from file or use defaults"""
        default_config = {
            "services": {
                "consciousness_core": {
                    "name": "Consciousness Core",
                    "command": "python nexus-mobile-project/backend/central-consciousness-core/consciousness_core_real.py",
                    "port": 8080,
                    "health_endpoint": "/health",
                    "required": True,
                    "startup_delay": 2
                },
                "manus_web": {
                    "name": "MANUS Web Interface",
                    "command": "python manus_web_interface_v2.py",
                    "port": 8002,
                    "health_endpoint": "/api/stats",
                    "required": True,
                    "startup_delay": 3
                },
                "nexus_web": {
                    "name": "NEXUS Web App",
                    "command": "cd nexus-web-app && npm start",
                    "port": 3000,
                    "health_endpoint": "/",
                    "required": False,
                    "startup_delay": 5
                },
                "react_dashboard": {
                    "name": "React Dashboard",
                    "command": "cd nexus-web-app/react-dashboard && npm start",
                    "port": 3001,
                    "health_endpoint": "/",
                    "required": False,
                    "startup_delay": 5
                }
            },
            "environment": {
                "NEXUS_MODE": "production",
                "NEXUS_LOG_LEVEL": "INFO",
                "PYTHONUNBUFFERED": "1"
            },
            "auto_recovery": {
                "enabled": True,
                "max_retries": 3,
                "retry_delay": 10
            }
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                # Merge configs
                default_config.update(user_config)
            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not load config file: {e}[/yellow]")
                
        return default_config
        
    def print_banner(self):
        """Print NEXUS launcher banner"""
        banner = """
[bold green]╔════════════════════════════════════════════════════════╗
║                   NEXUS 2.0 LAUNCHER                   ║
║              Omnipotent AI System Startup              ║
╚════════════════════════════════════════════════════════╝[/bold green]
        """
        self.console.print(banner)
        
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        self.console.print("\n[bold]Checking dependencies...[/bold]")
        
        checks = [
            ("Python 3.8+", self.check_python_version),
            ("Node.js", self.check_node),
            ("npm", self.check_npm),
            ("Required Python packages", self.check_python_packages),
        ]
        
        all_ok = True
        for name, check_func in checks:
            status, message = check_func()
            if status:
                self.console.print(f"✓ {name}: [green]{message}[/green]")
            else:
                self.console.print(f"✗ {name}: [red]{message}[/red]")
                all_ok = False
                
        return all_ok
        
    def check_python_version(self) -> Tuple[bool, str]:
        """Check Python version"""
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            return True, f"Python {version.major}.{version.minor}.{version.micro}"
        return False, f"Python {version.major}.{version.minor} (3.8+ required)"
        
    def check_node(self) -> Tuple[bool, str]:
        """Check if Node.js is installed"""
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return True, result.stdout.strip()
            return False, "Not installed"
        except:
            return False, "Not found"
            
    def check_npm(self) -> Tuple[bool, str]:
        """Check if npm is installed"""
        try:
            result = subprocess.run(['npm', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return True, f"npm {result.stdout.strip()}"
            return False, "Not installed"
        except:
            return False, "Not found"
            
    def check_python_packages(self) -> Tuple[bool, str]:
        """Check required Python packages"""
        required = ['fastapi', 'uvicorn', 'aiohttp', 'rich']
        missing = []
        
        for package in required:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
                
        if missing:
            return False, f"Missing: {', '.join(missing)}"
        return True, "All installed"
        
    def check_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return True
        except:
            return False
            
    async def start_service(self, service_id: str, service_config: dict) -> bool:
        """Start a single service"""
        name = service_config['name']
        
        # Check if port is available
        if 'port' in service_config:
            if not self.check_port_available(service_config['port']):
                self.console.print(f"[red]Port {service_config['port']} is already in use[/red]")
                return False
                
        # Set up environment
        env = os.environ.copy()
        env.update(self.config['environment'])
        
        # Start process
        try:
            if service_config['command'].startswith('cd '):
                # Handle directory change commands
                parts = service_config['command'].split(' && ')
                cwd = parts[0].replace('cd ', '')
                cmd = ' '.join(parts[1:])
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
                    service_config['command'],
                    shell=True,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
            self.processes[service_id] = process
            
            # Wait for startup
            await asyncio.sleep(service_config.get('startup_delay', 3))
            
            # Check if process is still running
            if process.poll() is not None:
                return False
                
            return True
            
        except Exception as e:
            self.console.print(f"[red]Failed to start {name}: {str(e)}[/red]")
            return False
            
    async def health_check(self, service_id: str, service_config: dict) -> bool:
        """Check if a service is healthy"""
        if 'port' not in service_config:
            # No port means no health check
            return True
            
        try:
            url = f"http://localhost:{service_config['port']}{service_config.get('health_endpoint', '/')}"
            response = requests.get(url, timeout=5)
            return response.status_code < 500
        except:
            return False
            
    async def start_all_services(self):
        """Start all services with progress tracking"""
        services = self.config['services']
        total_services = len(services)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Starting services...", total=total_services)
            
            for service_id, service_config in services.items():
                name = service_config['name']
                progress.update(task, description=f"Starting {name}...")
                
                success = await self.start_service(service_id, service_config)
                
                if success:
                    # Wait for health check
                    healthy = await self.wait_for_health(service_id, service_config)
                    if healthy:
                        self.console.print(f"✓ {name} started successfully")
                    else:
                        self.console.print(f"[yellow]⚠ {name} started but health check failed[/yellow]")
                        if service_config.get('required', False):
                            raise Exception(f"Required service {name} failed health check")
                else:
                    self.console.print(f"[red]✗ Failed to start {name}[/red]")
                    if service_config.get('required', False):
                        raise Exception(f"Required service {name} failed to start")
                        
                progress.advance(task)
                
    async def wait_for_health(self, service_id: str, service_config: dict, 
                            timeout: int = 30) -> bool:
        """Wait for service to become healthy"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if await self.health_check(service_id, service_config):
                return True
            await asyncio.sleep(1)
            
        return False
        
    def get_service_status(self) -> Table:
        """Get status table of all services"""
        table = Table(title="Service Status")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("PID", style="yellow")
        table.add_column("Memory", style="blue")
        table.add_column("CPU", style="magenta")
        
        for service_id, service_config in self.config['services'].items():
            name = service_config['name']
            process = self.processes.get(service_id)
            
            if process and process.poll() is None:
                try:
                    proc = psutil.Process(process.pid)
                    memory = f"{proc.memory_info().rss / 1024 / 1024:.1f} MB"
                    cpu = f"{proc.cpu_percent(interval=0.1):.1f}%"
                    status = "[green]Running[/green]"
                    pid = str(process.pid)
                except:
                    memory = "N/A"
                    cpu = "N/A"
                    status = "[yellow]Unknown[/yellow]"
                    pid = str(process.pid)
            else:
                status = "[red]Stopped[/red]"
                pid = "N/A"
                memory = "N/A"
                cpu = "N/A"
                
            table.add_row(name, status, pid, memory, cpu)
            
        return table
        
    async def monitor_services(self):
        """Monitor services and restart if needed"""
        while True:
            for service_id, service_config in self.config['services'].items():
                process = self.processes.get(service_id)
                
                if process and process.poll() is not None:
                    # Process died
                    if self.config['auto_recovery']['enabled']:
                        self.console.print(f"\n[yellow]Service {service_config['name']} died, restarting...[/yellow]")
                        await self.start_service(service_id, service_config)
                        
            await asyncio.sleep(self.health_check_interval)
            
    def shutdown(self, signum=None, frame=None):
        """Gracefully shutdown all services"""
        self.console.print("\n[yellow]Shutting down NEXUS services...[/yellow]")
        
        # Run shutdown handlers
        for handler in self.shutdown_handlers:
            try:
                handler()
            except:
                pass
                
        # Stop all processes
        for service_id, process in self.processes.items():
            if process and process.poll() is None:
                name = self.config['services'][service_id]['name']
                self.console.print(f"Stopping {name}...")
                process.terminate()
                
                # Give it time to shutdown gracefully
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    
        self.console.print("[green]All services stopped[/green]")
        sys.exit(0)
        
    async def interactive_monitor(self):
        """Interactive monitoring interface"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        layout["header"].update(Panel("[bold green]NEXUS 2.0 System Monitor[/bold green]"))
        layout["footer"].update(Panel("Press Ctrl+C to stop all services"))
        
        with Live(layout, refresh_per_second=1, console=self.console) as live:
            while True:
                layout["body"].update(self.get_service_status())
                await asyncio.sleep(1)
                
    async def run(self):
        """Main launcher routine"""
        self.print_banner()
        
        # Check dependencies
        if not self.check_dependencies():
            self.console.print("\n[red]Please install missing dependencies and try again[/red]")
            return
            
        # Register shutdown handler
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        
        try:
            # Start all services
            self.console.print("\n[bold]Starting NEXUS 2.0 services...[/bold]\n")
            await self.start_all_services()
            
            # Show URLs
            self.console.print("\n[bold green]NEXUS 2.0 is ready![/bold green]\n")
            self.console.print("Access points:")
            self.console.print("  • NEXUS Web Interface: [cyan]http://localhost:8002[/cyan]")
            self.console.print("  • React Dashboard: [cyan]http://localhost:3001[/cyan]")
            self.console.print("  • NEXUS Web App: [cyan]http://localhost:3000[/cyan]")
            self.console.print("  • CLI: [cyan]python nexus_cli.py[/cyan]")
            self.console.print("\nPress Ctrl+C to stop all services\n")
            
            # Start monitoring
            monitor_task = asyncio.create_task(self.monitor_services())
            ui_task = asyncio.create_task(self.interactive_monitor())
            
            await asyncio.gather(monitor_task, ui_task)
            
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            self.console.print(f"\n[red]Error: {str(e)}[/red]")
            self.shutdown()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NEXUS 2.0 Unified Launcher")
    parser.add_argument('-c', '--config', help='Configuration file path')
    parser.add_argument('--no-monitor', action='store_true', 
                       help='Start services without interactive monitor')
    
    args = parser.parse_args()
    
    launcher = NEXUSLauncher(args.config)
    
    try:
        asyncio.run(launcher.run())
    except KeyboardInterrupt:
        launcher.shutdown()

if __name__ == "__main__":
    main()