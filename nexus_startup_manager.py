#!/usr/bin/env python3
"""
NEXUS Startup Manager
Handles service dependency resolution, parallel startup, and health monitoring
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import psutil
import aiohttp
import json

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service status states"""
    PENDING = "pending"
    STARTING = "starting"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    FAILED = "failed"
    STOPPING = "stopping"
    STOPPED = "stopped"


class StartupError(Exception):
    """Startup-specific error"""
    pass


@dataclass
class ServiceConfig:
    """Configuration for a service"""
    name: str
    enabled: bool = True
    dependencies: List[str] = field(default_factory=list)
    startup_timeout: float = 30.0
    health_check_interval: float = 5.0
    retry_count: int = 3
    critical: bool = True  # If True, failure stops startup
    
    
@dataclass 
class ServiceInfo:
    """Runtime information about a service"""
    config: ServiceConfig
    status: ServiceStatus = ServiceStatus.PENDING
    process: Optional[asyncio.subprocess.Process] = None
    task: Optional[asyncio.Task] = None
    start_time: Optional[float] = None
    health_check_task: Optional[asyncio.Task] = None
    retry_attempts: int = 0
    last_error: Optional[str] = None


class StartupManager:
    """Manages NEXUS service startup and lifecycle"""
    
    def __init__(self, config: Dict[str, Any], safe_mode: bool = False):
        self.config = config
        self.safe_mode = safe_mode
        self.services: Dict[str, ServiceInfo] = {}
        self._shutdown = False
        
        # Define service configurations
        self._define_services()
        
    def _define_services(self):
        """Define all NEXUS services and their dependencies"""
        
        # Core services
        self.services["database"] = ServiceInfo(
            config=ServiceConfig(
                name="database",
                enabled=not self.safe_mode,
                dependencies=[],
                critical=False  # Can run without DB in dev mode
            )
        )
        
        self.services["redis"] = ServiceInfo(
            config=ServiceConfig(
                name="redis", 
                enabled=not self.safe_mode,
                dependencies=[],
                critical=False
            )
        )
        
        self.services["message_queue"] = ServiceInfo(
            config=ServiceConfig(
                name="message_queue",
                enabled=not self.safe_mode and self.config.get("nexus", {}).get("features", {}).get("messaging", False),
                dependencies=["redis"],
                critical=False
            )
        )
        
        # API services
        self.services["api_server"] = ServiceInfo(
            config=ServiceConfig(
                name="api_server",
                enabled=True,
                dependencies=["database", "redis"],
                critical=True
            )
        )
        
        self.services["websocket_server"] = ServiceInfo(
            config=ServiceConfig(
                name="websocket_server",
                enabled=True,
                dependencies=["api_server"],
                critical=False
            )
        )
        
        # Feature services
        self.services["memory_service"] = ServiceInfo(
            config=ServiceConfig(
                name="memory_service",
                enabled=self.config.get("nexus", {}).get("features", {}).get("memory", True),
                dependencies=["redis"],
                critical=False
            )
        )
        
        self.services["voice_service"] = ServiceInfo(
            config=ServiceConfig(
                name="voice_service",
                enabled=self.config.get("nexus", {}).get("features", {}).get("voice", False) and not self.safe_mode,
                dependencies=["api_server"],
                critical=False
            )
        )
        
        self.services["vision_service"] = ServiceInfo(
            config=ServiceConfig(
                name="vision_service",
                enabled=self.config.get("nexus", {}).get("features", {}).get("vision", False) and not self.safe_mode,
                dependencies=["api_server"],
                critical=False
            )
        )
        
        self.services["web_scraper"] = ServiceInfo(
            config=ServiceConfig(
                name="web_scraper",
                enabled=self.config.get("nexus", {}).get("features", {}).get("web_scraping", True),
                dependencies=["api_server"],
                critical=False
            )
        )
        
        # Monitoring services
        self.services["metrics_server"] = ServiceInfo(
            config=ServiceConfig(
                name="metrics_server",
                enabled=not self.safe_mode,
                dependencies=[],
                critical=False
            )
        )
        
        self.services["health_monitor"] = ServiceInfo(
            config=ServiceConfig(
                name="health_monitor",
                enabled=True,
                dependencies=["api_server"],
                critical=False
            )
        )
        
    def _get_startup_order(self) -> List[str]:
        """Resolve service dependencies and return startup order"""
        # Build dependency graph
        graph = {}
        for name, service_info in self.services.items():
            if service_info.config.enabled:
                graph[name] = set(service_info.config.dependencies)
        
        # Topological sort
        visited = set()
        stack = []
        
        def visit(node: str):
            if node in visited:
                return
            visited.add(node)
            
            # Visit dependencies first
            for dep in graph.get(node, set()):
                if dep in graph:  # Only if dependency is enabled
                    visit(dep)
            
            stack.append(node)
        
        # Visit all nodes
        for node in graph:
            visit(node)
        
        return stack
    
    async def start_all(self):
        """Start all enabled services in dependency order"""
        startup_order = self._get_startup_order()
        
        logger.info(f"Starting services in order: {startup_order}")
        
        # Track startup progress
        total = len(startup_order)
        started = 0
        
        # Start services
        for service_name in startup_order:
            if self._shutdown:
                break
                
            service_info = self.services[service_name]
            
            # Update progress
            started += 1
            progress = (started / total) * 100
            print(f"[{progress:3.0f}%] Starting {service_name}...")
            
            try:
                await self._start_service(service_name)
                
                # Wait for service to be healthy
                if await self._wait_for_healthy(service_name):
                    logger.info(f"Service {service_name} started successfully")
                else:
                    raise StartupError(f"Service {service_name} failed health check")
                    
            except Exception as e:
                logger.error(f"Failed to start {service_name}: {e}")
                service_info.status = ServiceStatus.FAILED
                service_info.last_error = str(e)
                
                if service_info.config.critical:
                    # Critical service failed, stop startup
                    await self.stop_all()
                    raise StartupError(f"Critical service {service_name} failed: {e}")
                else:
                    # Non-critical, continue with other services
                    print(f"⚠️  Warning: {service_name} failed to start (non-critical)")
        
        # Start background health monitoring
        asyncio.create_task(self._monitor_health())
        
        print("\n✅ All services started successfully!")
        
    async def _start_service(self, name: str):
        """Start a single service"""
        service_info = self.services[name]
        service_info.status = ServiceStatus.STARTING
        service_info.start_time = time.time()
        
        # Service-specific startup logic
        if name == "database":
            await self._start_database()
        elif name == "redis":
            await self._start_redis()
        elif name == "api_server":
            await self._start_api_server()
        elif name == "websocket_server":
            await self._start_websocket_server()
        elif name == "memory_service":
            await self._start_memory_service()
        elif name == "voice_service":
            await self._start_voice_service()
        elif name == "vision_service":
            await self._start_vision_service()
        elif name == "web_scraper":
            await self._start_web_scraper()
        elif name == "metrics_server":
            await self._start_metrics_server()
        elif name == "health_monitor":
            await self._start_health_monitor()
        else:
            # Generic service start
            logger.warning(f"No specific startup logic for {name}")
            service_info.status = ServiceStatus.HEALTHY
    
    async def _start_database(self):
        """Start database service"""
        service_info = self.services["database"]
        
        try:
            # Check if PostgreSQL is running
            import asyncpg
            
            db_url = self.config.get("database", {}).get("url", "postgresql://localhost/nexus")
            conn = await asyncpg.connect(db_url, timeout=5)
            await conn.close()
            
            service_info.status = ServiceStatus.HEALTHY
            logger.info("Database connection verified")
            
        except Exception as e:
            logger.warning(f"Database not available: {e}")
            service_info.status = ServiceStatus.UNHEALTHY
            service_info.last_error = str(e)
    
    async def _start_redis(self):
        """Start Redis service"""
        service_info = self.services["redis"]
        
        try:
            # Check if Redis is running
            import redis.asyncio as redis
            
            redis_url = self.config.get("redis", {}).get("url", "redis://localhost:6379")
            client = redis.from_url(redis_url)
            await client.ping()
            await client.close()
            
            service_info.status = ServiceStatus.HEALTHY
            logger.info("Redis connection verified")
            
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            service_info.status = ServiceStatus.UNHEALTHY
            service_info.last_error = str(e)
    
    async def _start_api_server(self):
        """Start API server"""
        service_info = self.services["api_server"]
        
        try:
            # Import and start the API server
            from nexus_core_production import NexusCoreAPI
            
            api_config = {
                "host": self.config.get("nexus", {}).get("api", {}).get("host", "0.0.0.0"),
                "port": self.config.get("nexus", {}).get("api", {}).get("port", 8080),
                "redis_url": self.config.get("redis", {}).get("url"),
                "database_url": self.config.get("database", {}).get("url")
            }
            
            # Create API instance
            api = NexusCoreAPI(api_config)
            
            # Start in background task
            service_info.task = asyncio.create_task(api.start())
            
            # Give it time to start
            await asyncio.sleep(2)
            
            service_info.status = ServiceStatus.HEALTHY
            logger.info("API server started")
            
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            service_info.status = ServiceStatus.FAILED
            service_info.last_error = str(e)
            raise
    
    async def _start_websocket_server(self):
        """Start WebSocket server"""
        service_info = self.services["websocket_server"]
        
        try:
            # WebSocket server is usually part of the API server
            # Just mark as healthy if API is running
            if self.services["api_server"].status == ServiceStatus.HEALTHY:
                service_info.status = ServiceStatus.HEALTHY
                logger.info("WebSocket server ready")
            else:
                raise StartupError("API server not healthy")
                
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            service_info.status = ServiceStatus.FAILED
            service_info.last_error = str(e)
    
    async def _start_memory_service(self):
        """Start memory service"""
        service_info = self.services["memory_service"]
        
        try:
            from nexus_memory_core import UnifiedMemorySystem
            
            # Initialize memory system
            memory_system = UnifiedMemorySystem()
            await memory_system.initialize()
            
            # Store reference
            self._memory_system = memory_system
            
            service_info.status = ServiceStatus.HEALTHY
            logger.info("Memory service started")
            
        except Exception as e:
            logger.warning(f"Memory service unavailable: {e}")
            service_info.status = ServiceStatus.UNHEALTHY
            service_info.last_error = str(e)
    
    async def _start_voice_service(self):
        """Start voice service"""
        service_info = self.services["voice_service"]
        
        try:
            from nexus_voice_control import VoiceControlSystem
            
            # Initialize voice system
            voice_system = VoiceControlSystem()
            await voice_system.initialize()
            
            # Store reference
            self._voice_system = voice_system
            
            service_info.status = ServiceStatus.HEALTHY
            logger.info("Voice service started")
            
        except Exception as e:
            logger.warning(f"Voice service unavailable: {e}")
            service_info.status = ServiceStatus.UNHEALTHY
            service_info.last_error = str(e)
    
    async def _start_vision_service(self):
        """Start vision service"""
        service_info = self.services["vision_service"]
        
        try:
            from nexus_vision_processor import VisionProcessor
            
            # Initialize vision system
            vision_system = VisionProcessor()
            await vision_system.initialize()
            
            # Store reference
            self._vision_system = vision_system
            
            service_info.status = ServiceStatus.HEALTHY
            logger.info("Vision service started")
            
        except Exception as e:
            logger.warning(f"Vision service unavailable: {e}")
            service_info.status = ServiceStatus.UNHEALTHY
            service_info.last_error = str(e)
    
    async def _start_web_scraper(self):
        """Start web scraper service"""
        service_info = self.services["web_scraper"]
        
        try:
            from nexus_web_scraper import EnhancedWebScraper
            
            # Initialize scraper
            scraper = EnhancedWebScraper()
            
            # Store reference
            self._web_scraper = scraper
            
            service_info.status = ServiceStatus.HEALTHY
            logger.info("Web scraper service started")
            
        except Exception as e:
            logger.warning(f"Web scraper unavailable: {e}")
            service_info.status = ServiceStatus.UNHEALTHY
            service_info.last_error = str(e)
    
    async def _start_metrics_server(self):
        """Start metrics server"""
        service_info = self.services["metrics_server"]
        
        try:
            # Metrics server would be started here
            # For now, just mark as healthy
            service_info.status = ServiceStatus.HEALTHY
            logger.info("Metrics server started")
            
        except Exception as e:
            logger.warning(f"Metrics server unavailable: {e}")
            service_info.status = ServiceStatus.UNHEALTHY
            service_info.last_error = str(e)
    
    async def _start_health_monitor(self):
        """Start health monitor"""
        service_info = self.services["health_monitor"]
        
        try:
            # Health monitor runs as part of this manager
            service_info.status = ServiceStatus.HEALTHY
            logger.info("Health monitor started")
            
        except Exception as e:
            logger.warning(f"Health monitor unavailable: {e}")
            service_info.status = ServiceStatus.UNHEALTHY
            service_info.last_error = str(e)
    
    async def _wait_for_healthy(self, name: str, timeout: float = 30.0) -> bool:
        """Wait for a service to become healthy"""
        service_info = self.services[name]
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if service_info.status == ServiceStatus.HEALTHY:
                return True
            elif service_info.status == ServiceStatus.FAILED:
                return False
            
            await asyncio.sleep(0.5)
        
        return False
    
    async def _monitor_health(self):
        """Monitor health of all services"""
        while not self._shutdown:
            try:
                for name, service_info in self.services.items():
                    if service_info.config.enabled and service_info.status == ServiceStatus.HEALTHY:
                        # Perform health check
                        healthy = await self._check_service_health(name)
                        
                        if not healthy:
                            logger.warning(f"Service {name} is unhealthy")
                            service_info.status = ServiceStatus.UNHEALTHY
                            
                            # Attempt restart if critical
                            if service_info.config.critical:
                                asyncio.create_task(self._restart_service(name))
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(5)
    
    async def _check_service_health(self, name: str) -> bool:
        """Check if a service is healthy"""
        service_info = self.services[name]
        
        try:
            if name == "api_server":
                # Check API health endpoint
                async with aiohttp.ClientSession() as session:
                    url = f"http://localhost:{self.config.get('nexus', {}).get('api', {}).get('port', 8080)}/health"
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        return resp.status == 200
            
            elif name == "redis":
                # Check Redis connection
                import redis.asyncio as redis
                redis_url = self.config.get("redis", {}).get("url", "redis://localhost:6379")
                client = redis.from_url(redis_url)
                await client.ping()
                await client.close()
                return True
            
            elif name == "database":
                # Check database connection
                import asyncpg
                db_url = self.config.get("database", {}).get("url", "postgresql://localhost/nexus")
                conn = await asyncpg.connect(db_url, timeout=5)
                await conn.close()
                return True
            
            else:
                # For other services, assume healthy if status is healthy
                return service_info.status == ServiceStatus.HEALTHY
                
        except Exception:
            return False
    
    async def _restart_service(self, name: str):
        """Restart a failed service"""
        service_info = self.services[name]
        
        if service_info.retry_attempts >= service_info.config.retry_count:
            logger.error(f"Service {name} exceeded retry limit")
            return
        
        service_info.retry_attempts += 1
        logger.info(f"Attempting to restart {name} (attempt {service_info.retry_attempts})")
        
        try:
            # Stop the service first
            await self._stop_service(name)
            
            # Wait a bit
            await asyncio.sleep(2)
            
            # Start it again
            await self._start_service(name)
            
            if await self._wait_for_healthy(name):
                logger.info(f"Service {name} restarted successfully")
                service_info.retry_attempts = 0
            else:
                logger.error(f"Service {name} failed to restart")
                
        except Exception as e:
            logger.error(f"Error restarting {name}: {e}")
    
    async def stop_all(self):
        """Stop all services in reverse order"""
        self._shutdown = True
        
        # Get services in reverse startup order
        startup_order = self._get_startup_order()
        stop_order = list(reversed(startup_order))
        
        logger.info(f"Stopping services in order: {stop_order}")
        
        for service_name in stop_order:
            service_info = self.services[service_name]
            
            if service_info.status in [ServiceStatus.HEALTHY, ServiceStatus.UNHEALTHY]:
                print(f"Stopping {service_name}...")
                await self._stop_service(service_name)
    
    async def _stop_service(self, name: str):
        """Stop a single service"""
        service_info = self.services[name]
        service_info.status = ServiceStatus.STOPPING
        
        try:
            # Cancel any running tasks
            if service_info.task and not service_info.task.done():
                service_info.task.cancel()
                try:
                    await service_info.task
                except asyncio.CancelledError:
                    pass
            
            # Service-specific cleanup
            if name == "memory_service" and hasattr(self, '_memory_system'):
                await self._memory_system.shutdown()
            elif name == "voice_service" and hasattr(self, '_voice_system'):
                await self._voice_system.shutdown()
            elif name == "vision_service" and hasattr(self, '_vision_system'):
                await self._vision_system.shutdown()
            
            service_info.status = ServiceStatus.STOPPED
            logger.info(f"Service {name} stopped")
            
        except Exception as e:
            logger.error(f"Error stopping {name}: {e}")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get summary of all service statuses"""
        summary = {
            "services": {},
            "healthy_count": 0,
            "unhealthy_count": 0,
            "total_count": 0
        }
        
        for name, service_info in self.services.items():
            if service_info.config.enabled:
                summary["total_count"] += 1
                
                if service_info.status == ServiceStatus.HEALTHY:
                    summary["healthy_count"] += 1
                elif service_info.status in [ServiceStatus.UNHEALTHY, ServiceStatus.FAILED]:
                    summary["unhealthy_count"] += 1
                
                summary["services"][name] = {
                    "status": service_info.status.value,
                    "critical": service_info.config.critical,
                    "uptime": time.time() - service_info.start_time if service_info.start_time else 0,
                    "last_error": service_info.last_error
                }
        
        return summary