#!/usr/bin/env python3
"""
NEXUS 2.0 Simple Launcher
Starts working NEXUS components with proper health checks
"""

import asyncio
import subprocess
import sys
import os
import time
import signal
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel
from rich.live import Live

console = Console()

class SimpleNEXUSLauncher:
    def __init__(self):
        self.console = console
        self.processes = {}
        self.running = True
        
    def print_banner(self):
        """Print NEXUS 2.0 banner"""
        banner = """
[bold green]╔════════════════════════════════════════════════════════╗
║                   NEXUS 2.0 SIMPLE                    ║
║              Enhanced AI System Launcher               ║
╚════════════════════════════════════════════════════════╝[/bold green]
        """
        self.console.print(banner)
        
    def check_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return True
        except:
            return False
            
    async def start_enhanced_manus(self) -> bool:
        """Start Enhanced MANUS web interface"""
        if not self.check_port_available(8002):
            self.console.print("[yellow]Port 8002 in use, trying 8003...[/yellow]")
            if not self.check_port_available(8003):
                self.console.print("[red]Ports 8002 and 8003 are busy[/red]")
                return False
            port = 8003
        else:
            port = 8002
            
        try:
            # Create a simple web interface launcher
            launcher_code = f'''
import sys
import os
sys.path.append(os.getcwd())

from manus_web_interface_v2 import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port={port})
'''
            
            with open('temp_manus_launcher.py', 'w') as f:
                f.write(launcher_code)
                
            process = subprocess.Popen(
                [sys.executable, 'temp_manus_launcher.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes['manus'] = process
            
            # Wait for startup
            await asyncio.sleep(3)
            
            # Check if it's running
            if process.poll() is not None:
                return False
                
            # Health check
            for i in range(10):
                try:
                    response = requests.get(f'http://localhost:{port}/', timeout=2)
                    if response.status_code < 500:
                        self.console.print(f"✓ Enhanced MANUS started on port {port}")
                        return True
                except:
                    await asyncio.sleep(1)
                    
            return False
            
        except Exception as e:
            self.console.print(f"[red]Failed to start Enhanced MANUS: {e}[/red]")
            return False
            
    async def start_simple_web(self) -> bool:
        """Start simple NEXUS web interface"""
        if not self.check_port_available(8001):
            self.console.print("[yellow]Port 8001 in use, trying 8004...[/yellow]")
            if not self.check_port_available(8004):
                return False
            port = 8004
        else:
            port = 8001
            
        try:
            # Modify simple web to use different port if needed
            if port != 8001:
                with open('simple_nexus_web.py', 'r') as f:
                    content = f.read()
                content = content.replace('8001', str(port))
                with open('temp_simple_web.py', 'w') as f:
                    f.write(content)
                script = 'temp_simple_web.py'
            else:
                script = 'simple_nexus_web.py'
                
            process = subprocess.Popen(
                [sys.executable, script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes['simple_web'] = process
            
            # Wait for startup
            await asyncio.sleep(2)
            
            # Health check
            for i in range(5):
                try:
                    response = requests.get(f'http://localhost:{port}/', timeout=2)
                    if response.status_code == 200:
                        self.console.print(f"✓ Simple NEXUS Web started on port {port}")
                        return True
                except:
                    await asyncio.sleep(1)
                    
            return False
            
        except Exception as e:
            self.console.print(f"[red]Failed to start Simple Web: {e}[/red]")
            return False
            
    async def start_consciousness_core(self) -> bool:
        """Start NEXUS consciousness core (optional)"""
        try:
            # Try to start the unified core
            process = subprocess.Popen(
                [sys.executable, 'nexus-mobile-project/backend/central-consciousness-core/unified_nexus_core.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes['consciousness'] = process
            
            # Wait for startup
            await asyncio.sleep(3)
            
            # Check if it's running (no health check needed)
            if process.poll() is None:
                self.console.print("✓ Consciousness Core started")
                return True
            else:
                self.console.print("[yellow]⚠ Consciousness Core failed to start (optional)[/yellow]")
                return False
                
        except Exception as e:
            self.console.print(f"[yellow]⚠ Consciousness Core not available: {e}[/yellow]")
            return False
            
    async def start_all_services(self):
        """Start all available services"""
        services = [
            ("Simple NEXUS Web", self.start_simple_web),
            ("Enhanced MANUS", self.start_enhanced_manus),
            ("Consciousness Core", self.start_consciousness_core),
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Starting services...", total=len(services))
            
            for name, start_func in services:
                progress.update(task, description=f"Starting {name}...")
                
                try:
                    success = await start_func()
                    if success:
                        self.console.print(f"✓ {name} started successfully")
                    else:
                        self.console.print(f"[yellow]⚠ {name} failed to start[/yellow]")
                except Exception as e:
                    self.console.print(f"[red]✗ {name} error: {e}[/red]")
                    
                progress.advance(task)
                
    def get_service_status(self) -> Table:
        """Get status table of all services"""
        table = Table(title="NEXUS 2.0 Service Status")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("PID", style="yellow")
        
        services = {
            'simple_web': 'Simple NEXUS Web',
            'manus': 'Enhanced MANUS',
            'consciousness': 'Consciousness Core'
        }
        
        for service_id, name in services.items():
            process = self.processes.get(service_id)
            
            if process and process.poll() is None:
                status = "[green]Running[/green]"
                pid = str(process.pid)
            else:
                status = "[red]Stopped[/red]"
                pid = "N/A"
                
            table.add_row(name, status, pid)
            
        return table
        
    def shutdown(self, signum=None, frame=None):
        """Gracefully shutdown all services"""
        self.console.print("\n[yellow]Shutting down NEXUS 2.0...[/yellow]")
        self.running = False
        
        # Stop all processes
        for service_id, process in self.processes.items():
            if process and process.poll() is None:
                self.console.print(f"Stopping {service_id}...")
                process.terminate()
                
                # Give it time to shutdown gracefully
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    
        # Clean up temp files
        for temp_file in ['temp_manus_launcher.py', 'temp_simple_web.py']:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                    
        self.console.print("[green]All services stopped[/green]")
        sys.exit(0)
        
    async def monitor_services(self):
        """Monitor services with live display"""
        with Live(self.get_service_status(), refresh_per_second=1, console=self.console) as live:
            while self.running:
                live.update(self.get_service_status())
                await asyncio.sleep(1)
                
    async def run(self):
        """Main launcher routine"""
        self.print_banner()
        
        # Register shutdown handler
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        
        try:
            # Start all services
            self.console.print("\n[bold]Starting NEXUS 2.0 services...[/bold]\n")
            await self.start_all_services()
            
            # Show access points
            self.console.print("\n[bold green]NEXUS 2.0 is ready![/bold green]\n")
            
            # Find which ports are actually running
            running_services = []
            for port in [8001, 8002, 8003, 8004]:
                try:
                    response = requests.get(f'http://localhost:{port}/', timeout=1)
                    if response.status_code < 500:
                        running_services.append(port)
                except:
                    pass
                    
            if running_services:
                self.console.print("🌐 Access points:")
                for port in running_services:
                    if port in [8001, 8004]:
                        self.console.print(f"  • Simple NEXUS Interface: [cyan]http://localhost:{port}[/cyan]")
                    elif port in [8002, 8003]:
                        self.console.print(f"  • Enhanced MANUS Interface: [cyan]http://localhost:{port}[/cyan]")
            else:
                self.console.print("[red]No web interfaces are running[/red]")
                
            self.console.print("\nPress Ctrl+C to stop all services\n")
            
            # Start monitoring
            await self.monitor_services()
            
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            self.console.print(f"\n[red]Error: {str(e)}[/red]")
            self.shutdown()

def main():
    """Main entry point"""
    launcher = SimpleNEXUSLauncher()
    
    try:
        asyncio.run(launcher.run())
    except KeyboardInterrupt:
        launcher.shutdown()

if __name__ == "__main__":
    main()