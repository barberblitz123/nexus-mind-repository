#!/usr/bin/env python3
"""
NEXUS Launcher - Ultra-fast, VSCode-like startup experience
Single entry point for the entire NEXUS ecosystem
"""

import argparse
import asyncio
import json
import os
import sys
import time
import signal
import subprocess
import tempfile
import shutil
import hashlib
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import psutil
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

# Try to import system-specific modules
try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

try:
    import speech_recognition as sr
    HAS_VOICE = True
except ImportError:
    HAS_VOICE = False

try:
    import cv2
    HAS_VISION = True
except ImportError:
    HAS_VISION = False

console = Console()

# Version info
NEXUS_VERSION = "2.0.0"
UPDATE_CHECK_URL = "https://api.github.com/repos/nexusmind/nexus/releases/latest"
CONFIG_DIR = Path.home() / ".nexus"
CONFIG_FILE = CONFIG_DIR / "config.json"
PID_FILE = CONFIG_DIR / "nexus.pid"
LOG_FILE = CONFIG_DIR / "nexus.log"

class NEXUSLauncher:
    def __init__(self):
        self.console = console
        self.config = self.load_config()
        self.processes: Dict[str, subprocess.Popen] = {}
        self.startup_time = None
        self.daemon_mode = False
        self.voice_enabled = False
        self.vision_enabled = False
        self.project_path = None
        self.theme = "dark"
        self.api_port = 8002
        self.tray_icon = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Ensure config directory exists
        CONFIG_DIR.mkdir(exist_ok=True)
        
    def load_config(self) -> dict:
        """Load or create configuration"""
        default_config = {
            "version": NEXUS_VERSION,
            "theme": "dark",
            "api_port": 8002,
            "auto_update": True,
            "startup_services": [
                "consciousness_core",
                "manus_web",
                "unified_memory"
            ],
            "services": {
                "consciousness_core": {
                    "name": "Consciousness Core",
                    "command": "python nexus-mobile-project/backend/central-consciousness-core/consciousness_core_real.py",
                    "port": 8080,
                    "health_endpoint": "/health",
                    "required": True,
                    "startup_delay": 0.5
                },
                "manus_web": {
                    "name": "MANUS Enhanced",
                    "command": "python nexus_enhanced_manus.py",
                    "port": 8002,
                    "health_endpoint": "/api/stats",
                    "required": True,
                    "startup_delay": 0.5
                },
                "unified_memory": {
                    "name": "Unified Memory System",
                    "command": "python nexus_memory_core.py",
                    "port": 8003,
                    "health_endpoint": "/health",
                    "required": True,
                    "startup_delay": 0.3
                },
                "nexus_web": {
                    "name": "NEXUS Web App",
                    "command": "cd nexus-web-app && npm start",
                    "port": 3000,
                    "health_endpoint": "/",
                    "required": False,
                    "startup_delay": 2.0
                },
                "react_dashboard": {
                    "name": "React Dashboard",
                    "command": "cd nexus-web-app/react-dashboard && npm start",
                    "port": 3001,
                    "health_endpoint": "/",
                    "required": False,
                    "startup_delay": 2.0
                },
                "voice_control": {
                    "name": "Voice Control",
                    "command": "python nexus_voice_control.py",
                    "port": 8004,
                    "health_endpoint": "/health",
                    "required": False,
                    "startup_delay": 1.0
                },
                "vision_processor": {
                    "name": "Vision Processor",
                    "command": "python nexus_vision_processor.py",
                    "port": 8005,
                    "health_endpoint": "/health",
                    "required": False,
                    "startup_delay": 1.0
                }
            },
            "themes": {
                "dark": {
                    "primary": "#0a0e27",
                    "secondary": "#1a1f3a",
                    "accent": "#00ff88",
                    "text": "#ffffff"
                },
                "light": {
                    "primary": "#ffffff",
                    "secondary": "#f5f5f5",
                    "accent": "#0066cc",
                    "text": "#000000"
                },
                "matrix": {
                    "primary": "#000000",
                    "secondary": "#001100",
                    "accent": "#00ff00",
                    "text": "#00ff00"
                }
            },
            "environment": {
                "NEXUS_MODE": "production",
                "NEXUS_LOG_LEVEL": "INFO",
                "PYTHONUNBUFFERED": "1",
                "NODE_ENV": "production"
            }
        }
        
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    user_config = json.load(f)
                    # Merge configs
                    default_config.update(user_config)
            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not load config: {e}[/yellow]")
                
        return default_config
        
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.console.print(f"[red]Error saving config: {e}[/red]")
            
    def parse_arguments(self) -> argparse.Namespace:
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(
            description="NEXUS Launcher - Omnipotent AI System",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  nexus                    # Start with default configuration
  nexus --voice --vision   # Enable voice and vision
  nexus --project ./myapp  # Open specific project
  nexus --daemon           # Run in background
  nexus stop               # Stop daemon
  nexus status             # Check system status
            """
        )
        
        # Commands
        parser.add_argument('command', nargs='?', choices=['start', 'stop', 'restart', 'status'],
                          default='start', help='Command to execute')
        
        # Options
        parser.add_argument('--voice', action='store_true',
                          help='Enable voice control')
        parser.add_argument('--vision', action='store_true',
                          help='Enable vision processing')
        parser.add_argument('--project', type=str,
                          help='Open specific project directory')
        parser.add_argument('--theme', choices=['dark', 'light', 'matrix'],
                          help='UI theme')
        parser.add_argument('--port', type=int,
                          help='API port (default: 8002)')
        parser.add_argument('--daemon', '-d', action='store_true',
                          help='Run in daemon mode')
        parser.add_argument('--no-update', action='store_true',
                          help='Disable auto-update check')
        parser.add_argument('--fast', action='store_true',
                          help='Fast startup (skip optional services)')
        parser.add_argument('--debug', action='store_true',
                          help='Enable debug mode')
        
        return parser.parse_args()
        
    async def check_for_updates(self) -> Optional[str]:
        """Check for available updates"""
        if not self.config.get('auto_update', True):
            return None
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(UPDATE_CHECK_URL, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        latest_version = data.get('tag_name', '').lstrip('v')
                        if latest_version and latest_version != NEXUS_VERSION:
                            return latest_version
        except:
            pass
            
        return None
        
    async def download_update(self, version: str) -> bool:
        """Download and prepare update"""
        self.console.print(f"[yellow]Downloading NEXUS {version}...[/yellow]")
        # In a real implementation, this would download and prepare the update
        # For now, we'll just simulate it
        await asyncio.sleep(2)
        return True
        
    def check_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return True
        except:
            return False
            
    async def start_service_fast(self, service_id: str, service_config: dict) -> bool:
        """Start a service with minimal overhead"""
        name = service_config['name']
        
        # Check port availability
        if 'port' in service_config:
            if not self.check_port_available(service_config['port']):
                # Try to find the process using the port and kill it if it's ours
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        for conn in proc.connections():
                            if conn.laddr.port == service_config['port']:
                                if 'nexus' in proc.info['name'].lower():
                                    proc.kill()
                                    await asyncio.sleep(0.5)
                                    break
                    except:
                        pass
                        
                if not self.check_port_available(service_config['port']):
                    return False
                    
        # Set up environment
        env = os.environ.copy()
        env.update(self.config['environment'])
        if self.theme:
            env['NEXUS_THEME'] = self.theme
        if self.project_path:
            env['NEXUS_PROJECT'] = self.project_path
            
        # Start process
        try:
            if service_config['command'].startswith('cd '):
                # Handle directory change commands
                parts = service_config['command'].split(' && ')
                cwd = parts[0].replace('cd ', '')
                cmd = ' '.join(parts[1:])
                
                # Check if npm packages are installed
                if 'npm' in cmd and not (Path(cwd) / 'node_modules').exists():
                    self.console.print(f"[yellow]Installing dependencies for {name}...[/yellow]")
                    install_proc = subprocess.run(['npm', 'install'], cwd=cwd, capture_output=True)
                    if install_proc.returncode != 0:
                        return False
                        
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    cwd=cwd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True  # Detach from parent
                )
            else:
                process = subprocess.Popen(
                    service_config['command'],
                    shell=True,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True
                )
                
            self.processes[service_id] = process
            
            # Minimal wait for critical services
            if service_config.get('required', False):
                await asyncio.sleep(service_config.get('startup_delay', 0.3))
            
            return process.poll() is None
            
        except Exception as e:
            return False
            
    async def parallel_service_startup(self, services_to_start: List[str]):
        """Start multiple services in parallel for faster startup"""
        tasks = []
        for service_id in services_to_start:
            if service_id in self.config['services']:
                service_config = self.config['services'][service_id]
                task = self.start_service_fast(service_id, service_config)
                tasks.append((service_id, task))
                
        # Wait for all services to start
        results = []
        for service_id, task in tasks:
            try:
                success = await task
                results.append((service_id, success))
            except Exception:
                results.append((service_id, False))
                
        return results
        
    def create_tray_icon(self):
        """Create system tray icon"""
        if not HAS_TRAY:
            return
            
        # Create icon image
        image = Image.new('RGB', (64, 64), color='black')
        draw = ImageDraw.Draw(image)
        draw.ellipse([16, 16, 48, 48], fill='#00ff88')
        
        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem("Open NEXUS", self.open_nexus),
            pystray.MenuItem("Status", self.show_status),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self.quit_from_tray)
        )
        
        self.tray_icon = pystray.Icon("NEXUS", image, "NEXUS AI", menu)
        
    def open_nexus(self, icon, item):
        """Open NEXUS interface"""
        import webbrowser
        webbrowser.open(f"http://localhost:{self.api_port}")
        
    def show_status(self, icon, item):
        """Show system status"""
        # In daemon mode, we'd show a notification
        pass
        
    def quit_from_tray(self, icon, item):
        """Quit from system tray"""
        icon.stop()
        self.shutdown()
        
    async def run_fast_startup(self):
        """Ultra-fast startup sequence"""
        self.startup_time = time.time()
        
        # Banner with version
        banner = f"""[bold green]
╔═══════════════════════════════════════╗
║         NEXUS v{NEXUS_VERSION}         ║
║    Lightning Fast AI System           ║
╚═══════════════════════════════════════╝[/bold green]"""
        self.console.print(banner)
        
        # Check for updates in background
        update_task = None
        if not self.args.no_update:
            update_task = asyncio.create_task(self.check_for_updates())
            
        # Determine services to start
        if self.args.fast:
            services_to_start = ["consciousness_core", "manus_web"]
        else:
            services_to_start = self.config['startup_services'].copy()
            
        # Add optional services based on flags
        if self.voice_enabled and HAS_VOICE:
            services_to_start.append("voice_control")
        if self.vision_enabled and HAS_VISION:
            services_to_start.append("vision_processor")
            
        # Start services in parallel
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=self.console,
            transient=True
        ) as progress:
            task = progress.add_task("Starting NEXUS...", total=len(services_to_start))
            
            # Start all services in parallel
            results = await self.parallel_service_startup(services_to_start)
            
            # Update progress
            for service_id, success in results:
                if success:
                    progress.advance(task)
                else:
                    service_name = self.config['services'][service_id]['name']
                    self.console.print(f"[red]✗ Failed to start {service_name}[/red]")
                    
        # Check update result
        if update_task:
            new_version = await update_task
            if new_version:
                self.console.print(f"\n[yellow]Update available: v{new_version}[/yellow]")
                self.console.print("Run 'nexus update' to install\n")
                
        # Calculate startup time
        startup_duration = time.time() - self.startup_time
        
        # Show ready message with URLs
        self.console.print(f"\n[bold green]✓ NEXUS ready in {startup_duration:.1f}s[/bold green]\n")
        
        # Display access points
        table = Table(show_header=False, box=None)
        table.add_column("", style="cyan")
        table.add_column("", style="white")
        
        table.add_row("Web Interface:", f"http://localhost:{self.api_port}")
        table.add_row("API Endpoint:", f"http://localhost:{self.api_port}/api")
        table.add_row("CLI:", "nexus [command]")
        
        if self.project_path:
            table.add_row("Project:", self.project_path)
            
        self.console.print(table)
        
        if not self.daemon_mode:
            self.console.print("\nPress Ctrl+C to stop\n")
            
    def write_pid_file(self):
        """Write PID file for daemon mode"""
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
            
    def read_pid_file(self) -> Optional[int]:
        """Read PID from file"""
        if PID_FILE.exists():
            try:
                with open(PID_FILE, 'r') as f:
                    return int(f.read().strip())
            except:
                pass
        return None
        
    def remove_pid_file(self):
        """Remove PID file"""
        if PID_FILE.exists():
            PID_FILE.unlink()
            
    def is_running(self) -> bool:
        """Check if NEXUS is already running"""
        pid = self.read_pid_file()
        if pid:
            try:
                # Check if process exists
                process = psutil.Process(pid)
                return 'nexus' in process.name().lower()
            except psutil.NoSuchProcess:
                self.remove_pid_file()
        return False
        
    def stop_daemon(self):
        """Stop running daemon"""
        pid = self.read_pid_file()
        if pid:
            try:
                process = psutil.Process(pid)
                process.terminate()
                process.wait(timeout=5)
                self.console.print("[green]✓ NEXUS daemon stopped[/green]")
            except psutil.NoSuchProcess:
                self.console.print("[yellow]NEXUS daemon not running[/yellow]")
            except psutil.TimeoutExpired:
                process.kill()
                self.console.print("[yellow]NEXUS daemon force stopped[/yellow]")
            finally:
                self.remove_pid_file()
        else:
            self.console.print("[yellow]No NEXUS daemon found[/yellow]")
            
    def show_status(self):
        """Show system status"""
        if self.is_running():
            pid = self.read_pid_file()
            self.console.print(f"[green]✓ NEXUS is running (PID: {pid})[/green]")
            
            # Try to get service status
            try:
                response = requests.get(f"http://localhost:{self.api_port}/api/stats", timeout=2)
                if response.status_code == 200:
                    stats = response.json()
                    self.console.print(f"\nActive goals: {stats.get('active_goals', 0)}")
                    self.console.print(f"Memory usage: {stats.get('memory_usage', 'N/A')}")
            except:
                pass
        else:
            self.console.print("[red]✗ NEXUS is not running[/red]")
            
    def run_daemon(self):
        """Run in daemon mode"""
        if platform.system() != 'Windows':
            # Fork to background
            pid = os.fork()
            if pid > 0:
                # Parent process
                self.console.print(f"[green]✓ NEXUS daemon started (PID: {pid})[/green]")
                sys.exit(0)
                
            # Child process
            os.setsid()
            
            # Redirect stdout/stderr to log file
            with open(LOG_FILE, 'a') as log:
                os.dup2(log.fileno(), sys.stdout.fileno())
                os.dup2(log.fileno(), sys.stderr.fileno())
                
        self.daemon_mode = True
        self.write_pid_file()
        
        # Create tray icon if available
        if HAS_TRAY:
            self.create_tray_icon()
            
    def shutdown(self, signum=None, frame=None):
        """Gracefully shutdown all services"""
        if self.daemon_mode:
            self.remove_pid_file()
            
        # Stop all processes
        for service_id, process in self.processes.items():
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    
        if not self.daemon_mode:
            self.console.print("\n[green]✓ NEXUS shutdown complete[/green]")
            
        sys.exit(0)
        
    async def run(self):
        """Main launcher routine"""
        # Parse arguments
        self.args = self.parse_arguments()
        
        # Handle commands
        if self.args.command == 'stop':
            self.stop_daemon()
            return
        elif self.args.command == 'status':
            self.show_status()
            return
        elif self.args.command == 'restart':
            self.stop_daemon()
            await asyncio.sleep(1)
            
        # Check if already running
        if self.is_running():
            self.console.print("[yellow]NEXUS is already running[/yellow]")
            if Confirm.ask("Open NEXUS interface?"):
                import webbrowser
                webbrowser.open(f"http://localhost:{self.api_port}")
            return
            
        # Apply configuration from arguments
        if self.args.theme:
            self.theme = self.args.theme
            self.config['theme'] = self.args.theme
        if self.args.port:
            self.api_port = self.args.port
            self.config['api_port'] = self.args.port
            self.config['services']['manus_web']['port'] = self.args.port
        if self.args.project:
            self.project_path = os.path.abspath(self.args.project)
        self.voice_enabled = self.args.voice
        self.vision_enabled = self.args.vision
        
        # Save configuration
        self.save_config()
        
        # Run in daemon mode if requested
        if self.args.daemon:
            self.run_daemon()
            
        # Register signal handlers
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        
        try:
            # Fast startup
            await self.run_fast_startup()
            
            # Keep running
            if self.daemon_mode and HAS_TRAY and self.tray_icon:
                # Run tray icon
                self.tray_icon.run()
            else:
                # Wait forever
                while True:
                    await asyncio.sleep(1)
                    
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            self.console.print(f"[red]Error: {str(e)}[/red]")
            if self.args.debug:
                import traceback
                traceback.print_exc()
            self.shutdown()

def main():
    """Main entry point"""
    launcher = NEXUSLauncher()
    asyncio.run(launcher.run())

if __name__ == "__main__":
    main()