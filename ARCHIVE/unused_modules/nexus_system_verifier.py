#!/usr/bin/env python3
"""
NEXUS System Verifier
Comprehensive verification system for all NEXUS production components
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
import importlib.util
import subprocess
import psutil
import socket
import aiohttp
import asyncpg
import redis.asyncio as redis
from dataclasses import dataclass, field
from enum import Enum
import yaml
import traceback
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('nexus_verification.log')
    ]
)
logger = logging.getLogger(__name__)
console = Console()


class ComponentStatus(Enum):
    """Component verification status"""
    PENDING = "pending"
    CHECKING = "checking"
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    FIXED = "fixed"


@dataclass
class VerificationResult:
    """Result of a verification check"""
    component: str
    status: ComponentStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[Exception] = None
    fix_available: bool = False
    fix_function: Optional[Callable] = None


@dataclass
class SystemHealth:
    """Overall system health status"""
    healthy_components: int = 0
    warning_components: int = 0
    error_components: int = 0
    total_components: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    @property
    def is_healthy(self) -> bool:
        return self.error_components == 0
    
    @property
    def health_percentage(self) -> float:
        if self.total_components == 0:
            return 0.0
        return (self.healthy_components / self.total_components) * 100


class NexusSystemVerifier:
    """Main system verification class"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("nexus_production_config.yaml")
        self.config = self._load_config()
        self.results: List[VerificationResult] = []
        self.fixes_applied: List[str] = []
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration file"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    async def verify_all(self, auto_fix: bool = False) -> SystemHealth:
        """Run all verification checks"""
        console.print(Panel.fit(
            "[bold cyan]NEXUS System Verification Starting[/bold cyan]\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            title="System Verifier"
        ))
        
        health = SystemHealth()
        
        # Define all verification checks
        checks = [
            # Core components
            ("Python Environment", self.verify_python_environment),
            ("Required Packages", self.verify_required_packages),
            ("File Structure", self.verify_file_structure),
            ("Import Integrity", self.verify_imports),
            
            # Services
            ("Database Connection", self.verify_database),
            ("Redis Connection", self.verify_redis),
            ("RabbitMQ Connection", self.verify_rabbitmq),
            
            # Network
            ("Required Ports", self.verify_ports),
            ("API Endpoints", self.verify_api_endpoints),
            
            # Features
            ("Voice Components", self.verify_voice_components),
            ("Vision Components", self.verify_vision_components),
            ("Agent Communication", self.verify_agent_communication),
            
            # Security
            ("Authentication System", self.verify_authentication),
            ("Encryption Keys", self.verify_encryption),
            
            # UI Components
            ("Terminal UI", self.verify_terminal_ui),
            ("Web Interface", self.verify_web_interface),
            
            # Launcher
            ("Unified Launcher", self.verify_launcher),
            
            # Performance
            ("System Resources", self.verify_system_resources),
            ("Service Health", self.verify_service_health)
        ]
        
        health.total_components = len(checks)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Verifying components...", total=len(checks))
            
            for name, check_func in checks:
                progress.update(task, description=f"Checking {name}...")
                
                try:
                    result = await check_func()
                    self.results.append(result)
                    
                    # Update health stats
                    if result.status == ComponentStatus.HEALTHY:
                        health.healthy_components += 1
                    elif result.status == ComponentStatus.WARNING:
                        health.warning_components += 1
                    elif result.status == ComponentStatus.ERROR:
                        health.error_components += 1
                        
                        # Apply fix if available and auto_fix is enabled
                        if auto_fix and result.fix_available and result.fix_function:
                            fix_result = await self._apply_fix(result)
                            if fix_result.status == ComponentStatus.FIXED:
                                health.error_components -= 1
                                health.healthy_components += 1
                    
                except Exception as e:
                    logger.error(f"Error checking {name}: {e}")
                    result = VerificationResult(
                        component=name,
                        status=ComponentStatus.ERROR,
                        message=f"Check failed: {str(e)}",
                        error=e
                    )
                    self.results.append(result)
                    health.error_components += 1
                
                progress.advance(task)
        
        health.end_time = datetime.now()
        
        # Generate report
        self._print_verification_report(health)
        
        return health
    
    async def verify_python_environment(self) -> VerificationResult:
        """Verify Python environment"""
        required_version = (3, 9)
        current_version = sys.version_info[:2]
        
        if current_version >= required_version:
            return VerificationResult(
                component="Python Environment",
                status=ComponentStatus.HEALTHY,
                message=f"Python {current_version[0]}.{current_version[1]} meets requirements",
                details={
                    "required": f"{required_version[0]}.{required_version[1]}+",
                    "current": f"{current_version[0]}.{current_version[1]}",
                    "executable": sys.executable
                }
            )
        else:
            return VerificationResult(
                component="Python Environment",
                status=ComponentStatus.ERROR,
                message=f"Python {required_version[0]}.{required_version[1]}+ required",
                details={
                    "required": f"{required_version[0]}.{required_version[1]}+",
                    "current": f"{current_version[0]}.{current_version[1]}"
                }
            )
    
    async def verify_required_packages(self) -> VerificationResult:
        """Verify all required packages are installed"""
        required_packages = [
            'aiohttp', 'asyncpg', 'redis', 'celery', 'prometheus_client',
            'opentelemetry', 'rich', 'pydantic', 'fastapi', 'uvicorn',
            'graphene', 'msgpack', 'pyzmq', 'consul', 'etcd3',
            'psutil', 'pyyaml', 'python-multipart', 'websockets',
            'httpx', 'sqlalchemy', 'alembic', 'tenacity', 'circuitbreaker'
        ]
        
        missing_packages = []
        installed_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                installed_packages.append(package)
            except ImportError:
                missing_packages.append(package)
        
        if not missing_packages:
            return VerificationResult(
                component="Required Packages",
                status=ComponentStatus.HEALTHY,
                message="All required packages installed",
                details={
                    "total": len(required_packages),
                    "installed": len(installed_packages)
                }
            )
        else:
            async def fix_packages():
                """Install missing packages"""
                try:
                    cmd = [sys.executable, "-m", "pip", "install"] + missing_packages
                    subprocess.run(cmd, check=True, capture_output=True)
                    return True
                except subprocess.CalledProcessError:
                    return False
            
            return VerificationResult(
                component="Required Packages",
                status=ComponentStatus.ERROR,
                message=f"{len(missing_packages)} packages missing",
                details={
                    "missing": missing_packages,
                    "installed": installed_packages
                },
                fix_available=True,
                fix_function=fix_packages
            )
    
    async def verify_file_structure(self) -> VerificationResult:
        """Verify all required files exist"""
        required_files = [
            'nexus_integration_core.py',
            'nexus_core_production.py',
            'nexus_config_production.py',
            'nexus_database_production.py',
            'nexus_launcher_production.py',
            'nexus_terminal_ui.py',
            'nexus_enhanced_manus.py',
            'nexus_unified_tools.py',
            'nexus_memory_core.py',
            'nexus_voice_control.py',
            'nexus_vision_processor.py',
            'nexus_web_scraper.py'
        ]
        
        missing_files = []
        existing_files = []
        
        for file in required_files:
            file_path = Path(file)
            if file_path.exists():
                existing_files.append(file)
            else:
                missing_files.append(file)
        
        if not missing_files:
            return VerificationResult(
                component="File Structure",
                status=ComponentStatus.HEALTHY,
                message="All required files present",
                details={
                    "total": len(required_files),
                    "existing": len(existing_files)
                }
            )
        else:
            return VerificationResult(
                component="File Structure",
                status=ComponentStatus.ERROR,
                message=f"{len(missing_files)} files missing",
                details={
                    "missing": missing_files,
                    "existing": existing_files
                }
            )
    
    async def verify_imports(self) -> VerificationResult:
        """Verify all imports work correctly"""
        import_errors = []
        successful_imports = []
        
        modules_to_check = [
            'nexus_integration_core',
            'nexus_core_production',
            'nexus_config_production',
            'nexus_enhanced_manus',
            'nexus_unified_tools',
            'nexus_memory_core'
        ]
        
        for module in modules_to_check:
            try:
                spec = importlib.util.find_spec(module)
                if spec is None:
                    import_errors.append(f"{module}: Module not found")
                else:
                    # Try to import the module
                    importlib.import_module(module)
                    successful_imports.append(module)
            except Exception as e:
                import_errors.append(f"{module}: {str(e)}")
        
        if not import_errors:
            return VerificationResult(
                component="Import Integrity",
                status=ComponentStatus.HEALTHY,
                message="All imports successful",
                details={
                    "total": len(modules_to_check),
                    "successful": len(successful_imports)
                }
            )
        else:
            return VerificationResult(
                component="Import Integrity",
                status=ComponentStatus.ERROR,
                message=f"{len(import_errors)} import errors",
                details={
                    "errors": import_errors,
                    "successful": successful_imports
                }
            )
    
    async def verify_database(self) -> VerificationResult:
        """Verify database connection"""
        try:
            db_url = self.config.get('database', {}).get('url', 'postgresql://localhost/nexus')
            
            # Test connection
            conn = await asyncpg.connect(db_url, timeout=5)
            version = await conn.fetchval('SELECT version()')
            await conn.close()
            
            return VerificationResult(
                component="Database Connection",
                status=ComponentStatus.HEALTHY,
                message="Database connection successful",
                details={
                    "url": db_url.replace(db_url.split('@')[0].split('//')[1], '***'),
                    "version": version.split(',')[0]
                }
            )
        except Exception as e:
            return VerificationResult(
                component="Database Connection",
                status=ComponentStatus.ERROR,
                message=f"Database connection failed: {str(e)}",
                error=e
            )
    
    async def verify_redis(self) -> VerificationResult:
        """Verify Redis connection"""
        try:
            redis_url = self.config.get('redis', {}).get('url', 'redis://localhost:6379')
            
            # Test connection
            client = redis.from_url(redis_url)
            await client.ping()
            info = await client.info()
            await client.close()
            
            return VerificationResult(
                component="Redis Connection",
                status=ComponentStatus.HEALTHY,
                message="Redis connection successful",
                details={
                    "url": redis_url,
                    "version": info.get('redis_version', 'unknown'),
                    "uptime_days": info.get('uptime_in_days', 0)
                }
            )
        except Exception as e:
            return VerificationResult(
                component="Redis Connection",
                status=ComponentStatus.ERROR,
                message=f"Redis connection failed: {str(e)}",
                error=e
            )
    
    async def verify_rabbitmq(self) -> VerificationResult:
        """Verify RabbitMQ connection"""
        try:
            # Check if RabbitMQ management API is accessible
            mgmt_url = self.config.get('rabbitmq', {}).get('management_url', 'http://localhost:15672')
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{mgmt_url}/api/overview", 
                                     auth=aiohttp.BasicAuth('guest', 'guest'),
                                     timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return VerificationResult(
                            component="RabbitMQ Connection",
                            status=ComponentStatus.HEALTHY,
                            message="RabbitMQ connection successful",
                            details={
                                "version": data.get('rabbitmq_version', 'unknown'),
                                "erlang_version": data.get('erlang_version', 'unknown')
                            }
                        )
                    else:
                        raise Exception(f"HTTP {resp.status}")
        except Exception as e:
            return VerificationResult(
                component="RabbitMQ Connection",
                status=ComponentStatus.WARNING,
                message=f"RabbitMQ not accessible: {str(e)}",
                details={"note": "RabbitMQ is optional but recommended"}
            )
    
    async def verify_ports(self) -> VerificationResult:
        """Verify required ports are available"""
        required_ports = {
            8080: "API Server",
            5555: "ZMQ Communication",
            9090: "Metrics Server",
            8000: "Web Interface"
        }
        
        blocked_ports = []
        available_ports = []
        
        for port, service in required_ports.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            try:
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    # Port is in use (which might be good if it's our service)
                    blocked_ports.append(f"{port} ({service})")
                else:
                    available_ports.append(f"{port} ({service})")
            except:
                available_ports.append(f"{port} ({service})")
        
        if len(available_ports) == len(required_ports):
            return VerificationResult(
                component="Required Ports",
                status=ComponentStatus.HEALTHY,
                message="All required ports available",
                details={
                    "ports": required_ports,
                    "available": available_ports
                }
            )
        else:
            return VerificationResult(
                component="Required Ports",
                status=ComponentStatus.WARNING,
                message="Some ports may be in use",
                details={
                    "in_use": blocked_ports,
                    "available": available_ports
                }
            )
    
    async def verify_api_endpoints(self) -> VerificationResult:
        """Verify API endpoints are accessible"""
        api_url = f"http://localhost:8080"
        
        try:
            async with aiohttp.ClientSession() as session:
                # Check health endpoint
                async with session.get(f"{api_url}/health", 
                                     timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        health_data = await resp.json()
                        return VerificationResult(
                            component="API Endpoints",
                            status=ComponentStatus.HEALTHY,
                            message="API endpoints accessible",
                            details=health_data
                        )
                    else:
                        raise Exception(f"Health check returned {resp.status}")
        except Exception as e:
            return VerificationResult(
                component="API Endpoints",
                status=ComponentStatus.WARNING,
                message="API not running",
                details={"note": "Start NEXUS to enable API"}
            )
    
    async def verify_voice_components(self) -> VerificationResult:
        """Verify voice control components"""
        try:
            # Check if speech recognition packages are available
            import speech_recognition
            import pyttsx3
            
            return VerificationResult(
                component="Voice Components",
                status=ComponentStatus.HEALTHY,
                message="Voice components available",
                details={
                    "speech_recognition": "installed",
                    "text_to_speech": "installed"
                }
            )
        except ImportError as e:
            return VerificationResult(
                component="Voice Components",
                status=ComponentStatus.WARNING,
                message="Voice components not fully installed",
                details={"missing": str(e)},
                fix_available=True,
                fix_function=lambda: subprocess.run([sys.executable, "-m", "pip", "install", "SpeechRecognition", "pyttsx3"])
            )
    
    async def verify_vision_components(self) -> VerificationResult:
        """Verify vision processing components"""
        try:
            # Check if vision packages are available
            import cv2
            import PIL
            
            return VerificationResult(
                component="Vision Components",
                status=ComponentStatus.HEALTHY,
                message="Vision components available",
                details={
                    "opencv": cv2.__version__,
                    "pillow": PIL.__version__
                }
            )
        except ImportError as e:
            return VerificationResult(
                component="Vision Components",
                status=ComponentStatus.WARNING,
                message="Vision components not fully installed",
                details={"missing": str(e)},
                fix_available=True,
                fix_function=lambda: subprocess.run([sys.executable, "-m", "pip", "install", "opencv-python", "Pillow"])
            )
    
    async def verify_agent_communication(self) -> VerificationResult:
        """Verify agent communication system"""
        try:
            import zmq
            
            # Test ZMQ context creation
            context = zmq.Context()
            socket = context.socket(zmq.REP)
            socket.close()
            context.term()
            
            return VerificationResult(
                component="Agent Communication",
                status=ComponentStatus.HEALTHY,
                message="ZMQ communication system ready",
                details={
                    "zmq_version": zmq.zmq_version(),
                    "pyzmq_version": zmq.pyzmq_version()
                }
            )
        except Exception as e:
            return VerificationResult(
                component="Agent Communication",
                status=ComponentStatus.ERROR,
                message=f"Agent communication error: {str(e)}",
                error=e
            )
    
    async def verify_authentication(self) -> VerificationResult:
        """Verify authentication system"""
        try:
            import jwt
            
            # Test JWT creation
            test_payload = {"user": "test", "exp": time.time() + 3600}
            test_secret = "test_secret"
            token = jwt.encode(test_payload, test_secret, algorithm="HS256")
            decoded = jwt.decode(token, test_secret, algorithms=["HS256"])
            
            return VerificationResult(
                component="Authentication System",
                status=ComponentStatus.HEALTHY,
                message="JWT authentication system ready",
                details={
                    "jwt_library": "PyJWT",
                    "algorithms": ["HS256", "RS256"]
                }
            )
        except Exception as e:
            return VerificationResult(
                component="Authentication System",
                status=ComponentStatus.ERROR,
                message=f"Authentication error: {str(e)}",
                error=e
            )
    
    async def verify_encryption(self) -> VerificationResult:
        """Verify encryption keys and systems"""
        try:
            from cryptography.fernet import Fernet
            
            # Test encryption
            key = Fernet.generate_key()
            f = Fernet(key)
            encrypted = f.encrypt(b"test data")
            decrypted = f.decrypt(encrypted)
            
            return VerificationResult(
                component="Encryption Keys",
                status=ComponentStatus.HEALTHY,
                message="Encryption system functional",
                details={
                    "library": "cryptography",
                    "algorithms": ["Fernet", "AES"]
                }
            )
        except Exception as e:
            return VerificationResult(
                component="Encryption Keys",
                status=ComponentStatus.ERROR,
                message=f"Encryption error: {str(e)}",
                error=e
            )
    
    async def verify_terminal_ui(self) -> VerificationResult:
        """Verify terminal UI components"""
        try:
            from rich.console import Console
            from rich.table import Table
            
            # Test console creation
            test_console = Console()
            test_table = Table(title="Test")
            
            return VerificationResult(
                component="Terminal UI",
                status=ComponentStatus.HEALTHY,
                message="Terminal UI components ready",
                details={
                    "library": "rich",
                    "features": ["tables", "panels", "progress", "syntax"]
                }
            )
        except Exception as e:
            return VerificationResult(
                component="Terminal UI",
                status=ComponentStatus.ERROR,
                message=f"Terminal UI error: {str(e)}",
                error=e
            )
    
    async def verify_web_interface(self) -> VerificationResult:
        """Verify web interface components"""
        try:
            import fastapi
            import uvicorn
            
            return VerificationResult(
                component="Web Interface",
                status=ComponentStatus.HEALTHY,
                message="Web interface components ready",
                details={
                    "fastapi_version": fastapi.__version__,
                    "server": "uvicorn"
                }
            )
        except Exception as e:
            return VerificationResult(
                component="Web Interface",
                status=ComponentStatus.ERROR,
                message=f"Web interface error: {str(e)}",
                error=e
            )
    
    async def verify_launcher(self) -> VerificationResult:
        """Verify unified launcher"""
        launcher_path = Path("nexus_launcher_production.py")
        
        if launcher_path.exists():
            try:
                # Check if launcher can be imported
                spec = importlib.util.spec_from_file_location("launcher", launcher_path)
                launcher = importlib.util.module_from_spec(spec)
                
                return VerificationResult(
                    component="Unified Launcher",
                    status=ComponentStatus.HEALTHY,
                    message="Launcher ready",
                    details={
                        "path": str(launcher_path),
                        "size": f"{launcher_path.stat().st_size / 1024:.1f} KB"
                    }
                )
            except Exception as e:
                return VerificationResult(
                    component="Unified Launcher",
                    status=ComponentStatus.ERROR,
                    message=f"Launcher error: {str(e)}",
                    error=e
                )
        else:
            return VerificationResult(
                component="Unified Launcher",
                status=ComponentStatus.ERROR,
                message="Launcher not found",
                details={"expected_path": str(launcher_path)}
            )
    
    async def verify_system_resources(self) -> VerificationResult:
        """Verify system has adequate resources"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_count = psutil.cpu_count()
        
        issues = []
        
        # Check memory (minimum 4GB recommended)
        if memory.total < 4 * 1024 * 1024 * 1024:
            issues.append(f"Low memory: {memory.total / (1024**3):.1f}GB (4GB recommended)")
        
        # Check disk space (minimum 10GB recommended)
        if disk.free < 10 * 1024 * 1024 * 1024:
            issues.append(f"Low disk space: {disk.free / (1024**3):.1f}GB free (10GB recommended)")
        
        # Check CPU cores (minimum 2 recommended)
        if cpu_count < 2:
            issues.append(f"Low CPU cores: {cpu_count} (2+ recommended)")
        
        if not issues:
            return VerificationResult(
                component="System Resources",
                status=ComponentStatus.HEALTHY,
                message="System resources adequate",
                details={
                    "memory_total": f"{memory.total / (1024**3):.1f}GB",
                    "memory_available": f"{memory.available / (1024**3):.1f}GB",
                    "disk_free": f"{disk.free / (1024**3):.1f}GB",
                    "cpu_cores": cpu_count
                }
            )
        else:
            return VerificationResult(
                component="System Resources",
                status=ComponentStatus.WARNING,
                message="System resources below recommended",
                details={
                    "issues": issues,
                    "memory_total": f"{memory.total / (1024**3):.1f}GB",
                    "disk_free": f"{disk.free / (1024**3):.1f}GB",
                    "cpu_cores": cpu_count
                }
            )
    
    async def verify_service_health(self) -> VerificationResult:
        """Verify overall service health"""
        healthy_services = 0
        total_services = 0
        service_details = {}
        
        # Check various services
        services = {
            "nexus_core": "ps aux | grep nexus_core",
            "redis": "redis-cli ping",
            "postgresql": "pg_isready"
        }
        
        for service, check_cmd in services.items():
            total_services += 1
            try:
                result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    healthy_services += 1
                    service_details[service] = "running"
                else:
                    service_details[service] = "not running"
            except:
                service_details[service] = "check failed"
        
        if healthy_services == total_services:
            return VerificationResult(
                component="Service Health",
                status=ComponentStatus.HEALTHY,
                message="All services healthy",
                details=service_details
            )
        else:
            return VerificationResult(
                component="Service Health",
                status=ComponentStatus.WARNING,
                message=f"{healthy_services}/{total_services} services running",
                details=service_details
            )
    
    async def _apply_fix(self, result: VerificationResult) -> VerificationResult:
        """Apply a fix for a component"""
        console.print(f"[yellow]Attempting to fix {result.component}...[/yellow]")
        
        try:
            if asyncio.iscoroutinefunction(result.fix_function):
                success = await result.fix_function()
            else:
                success = result.fix_function()
            
            if success:
                self.fixes_applied.append(result.component)
                return VerificationResult(
                    component=result.component,
                    status=ComponentStatus.FIXED,
                    message=f"Successfully fixed {result.component}",
                    details=result.details
                )
            else:
                return result
        except Exception as e:
            logger.error(f"Failed to apply fix for {result.component}: {e}")
            return result
    
    def _print_verification_report(self, health: SystemHealth):
        """Print detailed verification report"""
        # Create summary table
        summary_table = Table(title="Verification Summary", box="ROUNDED")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="white")
        
        summary_table.add_row("Total Components", str(health.total_components))
        summary_table.add_row("Healthy", f"[green]{health.healthy_components}[/green]")
        summary_table.add_row("Warnings", f"[yellow]{health.warning_components}[/yellow]")
        summary_table.add_row("Errors", f"[red]{health.error_components}[/red]")
        summary_table.add_row("Health Score", f"{health.health_percentage:.1f}%")
        summary_table.add_row("Duration", f"{(health.end_time - health.start_time).total_seconds():.2f}s")
        
        console.print(summary_table)
        
        # Create detailed results table
        details_table = Table(title="Component Status", box="ROUNDED")
        details_table.add_column("Component", style="cyan", width=30)
        details_table.add_column("Status", style="white", width=10)
        details_table.add_column("Message", style="white", width=50)
        
        for result in self.results:
            status_color = {
                ComponentStatus.HEALTHY: "green",
                ComponentStatus.WARNING: "yellow",
                ComponentStatus.ERROR: "red",
                ComponentStatus.FIXED: "blue",
                ComponentStatus.PENDING: "gray",
                ComponentStatus.CHECKING: "cyan"
            }.get(result.status, "white")
            
            details_table.add_row(
                result.component,
                f"[{status_color}]{result.status.value}[/{status_color}]",
                result.message
            )
        
        console.print(details_table)
        
        # Print fixes applied
        if self.fixes_applied:
            fixes_panel = Panel(
                "\n".join(f"✓ {fix}" for fix in self.fixes_applied),
                title="[green]Fixes Applied[/green]",
                border_style="green"
            )
            console.print(fixes_panel)
        
        # Print recommendations
        if health.error_components > 0 or health.warning_components > 0:
            recommendations = self._generate_recommendations()
            if recommendations:
                rec_panel = Panel(
                    "\n".join(f"• {rec}" for rec in recommendations),
                    title="[yellow]Recommendations[/yellow]",
                    border_style="yellow"
                )
                console.print(rec_panel)
        
        # Save report to file
        self._save_report(health)
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on verification results"""
        recommendations = []
        
        for result in self.results:
            if result.status == ComponentStatus.ERROR:
                if "Database" in result.component:
                    recommendations.append("Ensure PostgreSQL is installed and running")
                elif "Redis" in result.component:
                    recommendations.append("Start Redis server: redis-server")
                elif "Packages" in result.component:
                    recommendations.append("Run: pip install -r requirements.txt")
                elif "Imports" in result.component:
                    recommendations.append("Check Python path and module locations")
            elif result.status == ComponentStatus.WARNING:
                if "Ports" in result.component:
                    recommendations.append("Some ports may be in use by NEXUS or other services")
                elif "Resources" in result.component:
                    recommendations.append("Consider upgrading system resources for optimal performance")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _save_report(self, health: SystemHealth):
        """Save verification report to file"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "health": {
                "is_healthy": health.is_healthy,
                "percentage": health.health_percentage,
                "healthy_components": health.healthy_components,
                "warning_components": health.warning_components,
                "error_components": health.error_components,
                "total_components": health.total_components
            },
            "results": [
                {
                    "component": r.component,
                    "status": r.status.value,
                    "message": r.message,
                    "details": r.details,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self.results
            ],
            "fixes_applied": self.fixes_applied
        }
        
        report_path = Path("nexus_verification_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Verification report saved to {report_path}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NEXUS System Verifier")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--auto-fix", action="store_true", help="Automatically apply fixes")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    
    args = parser.parse_args()
    
    config_path = Path(args.config) if args.config else None
    verifier = NexusSystemVerifier(config_path)
    
    try:
        health = await verifier.verify_all(auto_fix=args.auto_fix)
        
        if args.json:
            # Output JSON results
            results = {
                "healthy": health.is_healthy,
                "health_percentage": health.health_percentage,
                "components": {
                    "healthy": health.healthy_components,
                    "warning": health.warning_components,
                    "error": health.error_components,
                    "total": health.total_components
                }
            }
            print(json.dumps(results, indent=2))
        
        # Exit with appropriate code
        sys.exit(0 if health.is_healthy else 1)
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        console.print(f"[red]Verification failed: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())