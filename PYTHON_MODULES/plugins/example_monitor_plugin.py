#!/usr/bin/env python3
"""
Example Monitor Plugin for NEXUS Integration Core
Demonstrates plugin system capabilities
"""

import asyncio
import time
from typing import Dict, Any
from nexus_integration_core import Plugin, PluginContext

class SystemMonitorPlugin(Plugin):
    """
    Example plugin that monitors system health and publishes metrics
    """
    
    @property
    def name(self) -> str:
        return "system-monitor"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    async def initialize(self, context: PluginContext):
        """Initialize the monitor plugin"""
        self.context = context
        self.monitoring_task = None
        self.metrics = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'service_count': 0,
            'message_rate': 0
        }
        
        print(f"Initializing {self.name} plugin v{self.version}")
        
        # Register as a service
        from nexus_integration_core import ServiceInfo
        await self.context.service_registry.register(ServiceInfo(
            id=self.name,
            name=self.name,
            version=self.version,
            host="localhost",
            port=0,  # No dedicated port
            capabilities=["monitoring", "metrics"],
            metadata={"type": "plugin"}
        ))
        
        # Subscribe to system events
        self.context.message_bus.subscribe(
            "system.*",
            self._handle_system_event
        )
        
        # Start monitoring
        self.monitoring_task = asyncio.create_task(self._monitor_loop())
        
        # Register hooks
        self.context.plugin_system.register_hook(
            "before_service_invoke",
            self._before_service_invoke,
            self.name
        )
    
    async def shutdown(self):
        """Clean shutdown"""
        print(f"Shutting down {self.name} plugin")
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Deregister service
        await self.context.service_registry.deregister(
            self.name,
            self.name
        )
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                # Collect metrics
                await self._collect_metrics()
                
                # Publish metrics
                await self.context.message_bus.publish(
                    "metrics.system",
                    self.metrics
                )
                
                # Update state
                await self.context.state_store.set(
                    "system_metrics",
                    self.metrics
                )
                
                await asyncio.sleep(10)  # Every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Monitor error: {e}")
                await asyncio.sleep(5)
    
    async def _collect_metrics(self):
        """Collect system metrics"""
        # Count services
        total_services = 0
        for service_list in self.context.service_registry.services.values():
            total_services += len(service_list)
        
        self.metrics['service_count'] = total_services
        self.metrics['timestamp'] = time.time()
        
        # Simulate CPU/Memory (in real plugin would use psutil)
        import random
        self.metrics['cpu_usage'] = random.uniform(10, 50)
        self.metrics['memory_usage'] = random.uniform(30, 70)
    
    async def _handle_system_event(self, message):
        """Handle system events"""
        # Count message rate
        self.metrics['message_rate'] = self.metrics.get('message_rate', 0) + 1
    
    async def _before_service_invoke(self, service_name: str, data: Dict[str, Any]):
        """Hook called before service invocation"""
        print(f"Service {service_name} being invoked with: {data}")
        
        # Could add metrics, validation, etc.
        await self.context.message_bus.publish(
            "audit.service_invoke",
            {
                "service": service_name,
                "timestamp": time.time(),
                "data": data
            }
        )