#!/usr/bin/env python3
"""
NEXUS Service Manager
Manages all NEXUS background services with health monitoring and auto-recovery
"""

import asyncio
import subprocess
import psutil
import json
import time
import signal
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from enum import Enum
import threading
from collections import deque

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """Service status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
    RECOVERING = "recovering"

@dataclass
class ServiceConfig:
    """Service configuration"""
    name: str
    command: List[str]
    working_dir: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    dependencies: List[str] = None
    health_check: Optional[Callable] = None
    health_check_interval: int = 30
    restart_policy: str = "on-failure"
    max_restarts: int = 3
    restart_delay: int = 5
    startup_timeout: int = 60
    shutdown_timeout: int = 30
    log_file: Optional[str] = None
    required: bool = True

class ServiceInstance:
    """Individual service instance"""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.status = ServiceStatus.STOPPED
        self.pid: Optional[int] = None
        self.start_time: Optional[datetime] = None
        self.restart_count = 0
        self.last_health_check: Optional[datetime] = None
        self.health_status = "unknown"
        self.logs = deque(maxlen=1000)
        self.metrics = {
            'cpu_percent': 0.0,
            'memory_mb': 0.0,
            'uptime_seconds': 0
        }
    
    def is_running(self) -> bool:
        """Check if service is running"""
        if self.process and self.process.poll() is None:
            return True
        return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        if self.pid and self.is_running():
            try:
                proc = psutil.Process(self.pid)
                self.metrics['cpu_percent'] = proc.cpu_percent(interval=0.1)
                self.metrics['memory_mb'] = proc.memory_info().rss / 1024 / 1024
                
                if self.start_time:
                    self.metrics['uptime_seconds'] = (datetime.now() - self.start_time).total_seconds()
            except psutil.NoSuchProcess:
                pass
        
        return self.metrics

class ServiceManager:
    """Main service manager"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.services: Dict[str, ServiceInstance] = {}
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # Initialize service configurations
        self._init_services()
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _init_services(self):
        """Initialize service configurations"""
        service_configs = {
            'memory_core': ServiceConfig(
                name="Memory Core",
                command=[sys.executable, "nexus_memory_core.py"],
                health_check=self._check_memory_health,
                required=True
            ),
            'api_server': ServiceConfig(
                name="API Server",
                command=[sys.executable, "nexus_core_production.py"],
                health_check=self._check_api_health,
                dependencies=["memory_core"],
                required=True
            ),
            'websocket_server': ServiceConfig(
                name="WebSocket Server",
                command=[sys.executable, "-m", "uvicorn", "nexus_websocket:app", "--port", "8002"],
                health_check=self._check_websocket_health,
                dependencies=["api_server"],
                required=True
            ),
            'web_ui': ServiceConfig(
                name="Web UI",
                command=[sys.executable, "manus_web_interface_v2.py"],
                health_check=self._check_web_health,
                dependencies=["api_server"],
                required=False
            ),
            'background_tasks': ServiceConfig(
                name="Background Tasks",
                command=[sys.executable, "-m", "celery", "-A", "nexus_tasks", "worker"],
                dependencies=["memory_core"],
                required=False
            ),
            'monitoring': ServiceConfig(
                name="Monitoring Service",
                command=[sys.executable, "nexus_monitoring_production.py"],
                required=False
            ),
            'voice_engine': ServiceConfig(
                name="Voice Engine",
                command=[sys.executable, "nexus_voice_engine.py"],
                required=False,
                restart_policy="unless-stopped"
            ),
            'vision_engine': ServiceConfig(
                name="Vision Engine",
                command=[sys.executable, "nexus_vision_engine.py"],
                required=False,
                restart_policy="unless-stopped"
            )
        }
        
        # Create service instances
        for service_id, config in service_configs.items():
            # Check if service file exists
            if len(config.command) > 1 and config.command[0] == sys.executable:
                service_file = config.command[1]
                if not service_file.startswith("-") and not Path(service_file).exists():
                    logger.warning(f"Service file not found: {service_file}")
                    if config.required:
                        logger.error(f"Required service {service_id} missing!")
                    continue
            
            self.services[service_id] = ServiceInstance(config)
    
    def start_service(self, service_id: str) -> bool:
        """Start a specific service"""
        if service_id not in self.services:
            logger.error(f"Unknown service: {service_id}")
            return False
        
        service = self.services[service_id]
        
        if service.is_running():
            logger.info(f"Service {service_id} already running")
            return True
        
        # Check dependencies
        if service.config.dependencies:
            for dep in service.config.dependencies:
                if dep in self.services and not self.services[dep].is_running():
                    logger.info(f"Starting dependency {dep} for {service_id}")
                    if not self.start_service(dep):
                        logger.error(f"Failed to start dependency {dep}")
                        return False
        
        try:
            logger.info(f"Starting service: {service_id}")
            service.status = ServiceStatus.STARTING
            
            # Prepare environment
            env = os.environ.copy()
            if service.config.env:
                env.update(service.config.env)
            
            # Prepare log file
            log_file = None
            if service.config.log_file:
                log_path = Path(service.config.log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                log_file = open(log_path, 'a')
            
            # Start process
            service.process = subprocess.Popen(
                service.config.command,
                cwd=service.config.working_dir,
                env=env,
                stdout=log_file or subprocess.PIPE,
                stderr=log_file or subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            service.pid = service.process.pid
            service.start_time = datetime.now()
            service.status = ServiceStatus.RUNNING
            
            logger.info(f"Service {service_id} started with PID {service.pid}")
            
            # Emit event
            self._emit_event('service_started', {'service_id': service_id, 'pid': service.pid})
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start service {service_id}: {e}")
            service.status = ServiceStatus.FAILED
            return False
    
    def stop_service(self, service_id: str, timeout: int = None) -> bool:
        """Stop a specific service"""
        if service_id not in self.services:
            return False
        
        service = self.services[service_id]
        
        if not service.is_running():
            logger.info(f"Service {service_id} not running")
            return True
        
        try:
            logger.info(f"Stopping service: {service_id}")
            service.status = ServiceStatus.STOPPING
            
            timeout = timeout or service.config.shutdown_timeout
            
            # Try graceful shutdown first
            if os.name != 'nt':
                os.killpg(os.getpgid(service.process.pid), signal.SIGTERM)
            else:
                service.process.terminate()
            
            # Wait for process to end
            try:
                service.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                logger.warning(f"Service {service_id} didn't stop gracefully, forcing...")
                if os.name != 'nt':
                    os.killpg(os.getpgid(service.process.pid), signal.SIGKILL)
                else:
                    service.process.kill()
                service.process.wait()
            
            service.status = ServiceStatus.STOPPED
            service.process = None
            service.pid = None
            
            logger.info(f"Service {service_id} stopped")
            
            # Emit event
            self._emit_event('service_stopped', {'service_id': service_id})
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop service {service_id}: {e}")
            return False
    
    def restart_service(self, service_id: str) -> bool:
        """Restart a service"""
        logger.info(f"Restarting service: {service_id}")
        
        if self.stop_service(service_id):
            time.sleep(2)  # Brief delay before restart
            return self.start_service(service_id)
        
        return False
    
    async def monitor_services(self):
        """Monitor services health and auto-recover"""
        logger.info("Starting service monitor")
        
        while self.running:
            try:
                for service_id, service in self.services.items():
                    if service.status == ServiceStatus.RUNNING:
                        # Check if process is still alive
                        if not service.is_running():
                            logger.warning(f"Service {service_id} died unexpectedly")
                            await self._handle_service_failure(service_id)
                        
                        # Run health check
                        elif service.config.health_check:
                            now = datetime.now()
                            if (not service.last_health_check or 
                                (now - service.last_health_check).seconds > service.config.health_check_interval):
                                
                                health_ok = await self._run_health_check(service_id)
                                service.last_health_check = now
                                
                                if not health_ok:
                                    logger.warning(f"Service {service_id} health check failed")
                                    await self._handle_service_failure(service_id)
                        
                        # Update metrics
                        service.get_metrics()
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(5)
    
    async def _run_health_check(self, service_id: str) -> bool:
        """Run health check for a service"""
        service = self.services[service_id]
        
        try:
            if asyncio.iscoroutinefunction(service.config.health_check):
                result = await service.config.health_check()
            else:
                result = service.config.health_check()
            
            service.health_status = "healthy" if result else "unhealthy"
            return result
            
        except Exception as e:
            logger.error(f"Health check failed for {service_id}: {e}")
            service.health_status = "error"
            return False
    
    async def _handle_service_failure(self, service_id: str):
        """Handle service failure with restart policy"""
        service = self.services[service_id]
        
        # Check restart policy
        if service.config.restart_policy == "never":
            service.status = ServiceStatus.FAILED
            return
        
        if service.config.restart_policy == "on-failure" or service.config.restart_policy == "always":
            if service.restart_count < service.config.max_restarts:
                service.restart_count += 1
                service.status = ServiceStatus.RECOVERING
                
                logger.info(f"Attempting to restart {service_id} (attempt {service.restart_count}/{service.config.max_restarts})")
                
                # Wait before restart
                await asyncio.sleep(service.config.restart_delay)
                
                if self.start_service(service_id):
                    logger.info(f"Service {service_id} recovered successfully")
                    # Reset restart count after successful recovery
                    await asyncio.sleep(60)  # Wait 1 minute
                    service.restart_count = 0
                else:
                    logger.error(f"Failed to restart {service_id}")
                    service.status = ServiceStatus.FAILED
            else:
                logger.error(f"Service {service_id} exceeded max restarts")
                service.status = ServiceStatus.FAILED
                
                # Emit failure event
                self._emit_event('service_failed', {
                    'service_id': service_id, 
                    'restart_count': service.restart_count
                })
    
    def start_all(self):
        """Start all services"""
        logger.info("Starting all services")
        self.running = True
        
        # Start monitoring
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.monitor_task = loop.create_task(self.monitor_services())
        
        # Start services in dependency order
        started = set()
        
        def start_with_deps(service_id: str):
            if service_id in started:
                return True
            
            service = self.services.get(service_id)
            if not service:
                return False
            
            # Start dependencies first
            if service.config.dependencies:
                for dep in service.config.dependencies:
                    if not start_with_deps(dep):
                        return False
            
            # Start service
            if self.start_service(service_id):
                started.add(service_id)
                return True
            
            return False
        
        # Start all services
        for service_id in self.services:
            start_with_deps(service_id)
        
        # Run monitor
        try:
            loop.run_until_complete(self.monitor_task)
        except asyncio.CancelledError:
            pass
    
    def shutdown_all(self):
        """Shutdown all services gracefully"""
        logger.info("Shutting down all services")
        self.running = False
        
        # Cancel monitoring
        if self.monitor_task:
            self.monitor_task.cancel()
        
        # Stop services in reverse dependency order
        stopped = set()
        
        def stop_with_deps(service_id: str):
            if service_id in stopped:
                return
            
            # Stop dependent services first
            for other_id, other_service in self.services.items():
                if other_service.config.dependencies and service_id in other_service.config.dependencies:
                    stop_with_deps(other_id)
            
            # Stop service
            self.stop_service(service_id)
            stopped.add(service_id)
        
        # Stop all services
        for service_id in self.services:
            stop_with_deps(service_id)
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        total = len(self.services)
        running = sum(1 for s in self.services.values() if s.status == ServiceStatus.RUNNING)
        failed = sum(1 for s in self.services.values() if s.status == ServiceStatus.FAILED)
        
        return {
            'total': total,
            'active': running,
            'failed': failed,
            'services': {
                service_id: {
                    'name': service.config.name,
                    'status': service.status.value,
                    'pid': service.pid,
                    'uptime': service.metrics['uptime_seconds'],
                    'cpu_percent': service.metrics['cpu_percent'],
                    'memory_mb': service.metrics['memory_mb'],
                    'health': service.health_status,
                    'restart_count': service.restart_count
                }
                for service_id, service in self.services.items()
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services"""
        health = {
            'healthy': True,
            'services': {}
        }
        
        for service_id, service in self.services.items():
            service_health = {
                'running': service.is_running(),
                'status': service.status.value,
                'health_check': 'not_configured'
            }
            
            if service.is_running() and service.config.health_check:
                health_ok = await self._run_health_check(service_id)
                service_health['health_check'] = 'passed' if health_ok else 'failed'
                
                if not health_ok and service.config.required:
                    health['healthy'] = False
            
            health['services'][service_id] = service_health
        
        return health
    
    def on(self, event: str, handler: Callable):
        """Register event handler"""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)
    
    def _emit_event(self, event: str, data: Any):
        """Emit event to handlers"""
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals"""
        logger.info(f"Received signal {signum}")
        self.shutdown_all()
        sys.exit(0)
    
    # Health check implementations
    def _check_memory_health(self) -> bool:
        """Check memory core health"""
        try:
            import requests
            resp = requests.get('http://localhost:8001/memory/health', timeout=5)
            return resp.status_code == 200
        except:
            return False
    
    def _check_api_health(self) -> bool:
        """Check API server health"""
        try:
            import requests
            resp = requests.get('http://localhost:8001/health', timeout=5)
            return resp.status_code == 200
        except:
            return False
    
    def _check_websocket_health(self) -> bool:
        """Check WebSocket server health"""
        try:
            import requests
            resp = requests.get('http://localhost:8002/health', timeout=5)
            return resp.status_code == 200
        except:
            return False
    
    def _check_web_health(self) -> bool:
        """Check web UI health"""
        try:
            import requests
            resp = requests.get('http://localhost:8000', timeout=5)
            return resp.status_code == 200
        except:
            return False

def main():
    """Main entry point for testing"""
    manager = ServiceManager()
    
    try:
        manager.start_all()
    except KeyboardInterrupt:
        manager.shutdown_all()

if __name__ == "__main__":
    main()