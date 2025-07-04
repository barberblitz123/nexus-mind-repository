#!/usr/bin/env python3
"""
NEXUS Integration Core Launcher
Connects all NEXUS components through the central hub
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from nexus_integration_core import (
    NexusIntegrationCore, 
    ServiceInfo, 
    ServiceStatus,
    MessagePriority
)

# Import NEXUS components to integrate
from nexus_memory_core import NexusMemoryCore
from nexus_omnipotent_core import NexusOmnipotentCore
from nexus_enhanced_manus import EnhancedManusAgent
from nexus_web_scraper import NexusWebScraper
from nexus_unified_tools import UnifiedToolsService

class NexusComponentAdapter:
    """Adapter to integrate existing NEXUS components with the integration core"""
    
    def __init__(self, integration_core: NexusIntegrationCore):
        self.core = integration_core
        self.components = {}
    
    async def register_memory_core(self):
        """Register memory core as a service"""
        memory_core = NexusMemoryCore()
        self.components['memory'] = memory_core
        
        # Register service
        await self.core.service_registry.register(ServiceInfo(
            id="nexus-memory",
            name="nexus-memory-core",
            version="2.0.0",
            host="localhost",
            port=8081,  # Would be actual port in production
            capabilities=[
                "memory-storage",
                "memory-retrieval",
                "episodic-memory",
                "semantic-memory",
                "working-memory"
            ],
            health_check_url="/health",
            metadata={
                "component_type": "core",
                "max_memory_size": 1000000
            }
        ))
        
        # Subscribe to memory events
        async def handle_memory_request(message):
            action = message.payload.get('action')
            if action == 'store':
                result = await memory_core.store_memory(
                    message.payload.get('content'),
                    message.payload.get('memory_type', 'episodic')
                )
                await self.core.message_bus.publish(
                    f"memory.response.{message.correlation_id}",
                    {"success": True, "result": result}
                )
            elif action == 'retrieve':
                result = await memory_core.retrieve_memories(
                    message.payload.get('query'),
                    message.payload.get('limit', 10)
                )
                await self.core.message_bus.publish(
                    f"memory.response.{message.correlation_id}",
                    {"success": True, "result": result}
                )
        
        self.core.message_bus.subscribe("memory.request", handle_memory_request)
        
        print("Memory Core integrated successfully")
    
    async def register_omnipotent_core(self):
        """Register omnipotent core as a service"""
        omnipotent = NexusOmnipotentCore()
        await omnipotent.initialize()
        self.components['omnipotent'] = omnipotent
        
        # Register service
        await self.core.service_registry.register(ServiceInfo(
            id="nexus-omnipotent",
            name="nexus-omnipotent-core",
            version="1.0.0",
            host="localhost",
            port=8082,
            capabilities=[
                "code-generation",
                "project-scaffolding",
                "analysis",
                "optimization",
                "security-scanning"
            ],
            health_check_url="/health"
        ))
        
        # Handle omnipotent requests
        async def handle_omnipotent_request(message):
            task_type = message.payload.get('task_type')
            
            if task_type == 'generate_project':
                result = await omnipotent.project_generator.generate_project(
                    message.payload.get('project_type'),
                    message.payload.get('project_name'),
                    message.payload.get('options', {})
                )
            elif task_type == 'analyze_code':
                result = await omnipotent.performance_analyzer.analyze_file(
                    message.payload.get('file_path')
                )
            elif task_type == 'scan_security':
                result = await omnipotent.security_scanner.scan_directory(
                    message.payload.get('directory')
                )
            else:
                result = {"error": f"Unknown task type: {task_type}"}
            
            await self.core.message_bus.publish(
                f"omnipotent.response.{message.correlation_id}",
                result
            )
        
        self.core.message_bus.subscribe("omnipotent.request", handle_omnipotent_request)
        
        print("Omnipotent Core integrated successfully")
    
    async def register_manus_agent(self):
        """Register enhanced MANUS agent"""
        manus = EnhancedManusAgent()
        self.components['manus'] = manus
        
        # Register service
        await self.core.service_registry.register(ServiceInfo(
            id="nexus-manus",
            name="nexus-enhanced-manus",
            version="2.0.0",
            host="localhost",
            port=8083,
            capabilities=[
                "autonomous-execution",
                "task-planning",
                "goal-reasoning",
                "context-awareness"
            ],
            health_check_url="/health"
        ))
        
        # Handle MANUS tasks
        async def handle_manus_task(message):
            task = message.payload
            
            # Store in MANUS task queue
            await manus.task_queue.put({
                'id': message.id,
                'description': task.get('description'),
                'priority': task.get('priority', 'normal'),
                'context': task.get('context', {})
            })
            
            # Acknowledge task received
            await self.core.message_bus.publish(
                "manus.task.acknowledged",
                {"task_id": message.id}
            )
        
        self.core.message_bus.subscribe("manus.task.submit", handle_manus_task)
        
        # Start MANUS processing loop
        asyncio.create_task(self._manus_processor(manus))
        
        print("MANUS Agent integrated successfully")
    
    async def _manus_processor(self, manus):
        """Process MANUS tasks and publish results"""
        while True:
            try:
                if not manus.task_queue.empty():
                    task = await manus.task_queue.get()
                    
                    # Process task
                    result = await manus.process_task_with_context(
                        task['description'],
                        task['context']
                    )
                    
                    # Publish result
                    await self.core.message_bus.publish(
                        "manus.task.completed",
                        {
                            "task_id": task['id'],
                            "result": result,
                            "timestamp": asyncio.get_event_loop().time()
                        }
                    )
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"MANUS processor error: {e}")
                await asyncio.sleep(5)
    
    async def setup_inter_component_communication(self):
        """Setup communication patterns between components"""
        
        # Memory-Omnipotent integration
        async def omnipotent_memory_handler(message):
            """Store omnipotent results in memory"""
            if message.topic == "omnipotent.analysis.complete":
                await self.core.message_bus.publish(
                    "memory.request",
                    {
                        "action": "store",
                        "content": message.payload,
                        "memory_type": "semantic",
                        "tags": ["analysis", "omnipotent"]
                    }
                )
        
        self.core.message_bus.subscribe("omnipotent.analysis.*", omnipotent_memory_handler)
        
        # MANUS-Memory integration
        async def manus_memory_handler(message):
            """Allow MANUS to query memories"""
            if message.topic == "manus.memory.query":
                await self.core.message_bus.publish(
                    "memory.request",
                    {
                        "action": "retrieve",
                        "query": message.payload.get('query'),
                        "correlation_id": message.id
                    },
                    correlation_id=message.id
                )
        
        self.core.message_bus.subscribe("manus.memory.query", manus_memory_handler)
        
        print("Inter-component communication established")

async def main():
    """Launch integrated NEXUS system"""
    
    # Configuration
    config = {
        'api_host': '0.0.0.0',
        'api_port': 8080,
        'state_file': 'nexus_integration_state.json',
        'plugin_dir': 'nexus_plugins'
    }
    
    # Create integration core
    core = NexusIntegrationCore(config)
    
    # Create component adapter
    adapter = NexusComponentAdapter(core)
    
    try:
        # Start integration core
        await core.start()
        
        print("\n=== NEXUS Integration Core Started ===")
        print(f"API Gateway: http://localhost:{config['api_port']}")
        print(f"GraphQL: http://localhost:{config['api_port']}/graphql")
        print(f"WebSocket: ws://localhost:{config['api_port']}/ws")
        print("\n")
        
        # Register components
        await adapter.register_memory_core()
        await adapter.register_omnipotent_core()
        await adapter.register_manus_agent()
        
        # Setup inter-component communication
        await adapter.setup_inter_component_communication()
        
        print("\n=== All Components Integrated ===")
        print("System ready for operations")
        print("\nAvailable services:")
        
        # List all services
        for name, instances in core.service_registry.services.items():
            for instance in instances:
                print(f"  - {instance.name} v{instance.version} [{instance.status.value}]")
                print(f"    Capabilities: {', '.join(instance.capabilities)}")
        
        print("\nPress Ctrl+C to shutdown")
        
        # Example: Publish a startup event
        await core.message_bus.publish(
            "system.startup.complete",
            {
                "timestamp": asyncio.get_event_loop().time(),
                "services": list(core.service_registry.services.keys())
            },
            priority=MessagePriority.HIGH
        )
        
        # Keep running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        print("\n\nShutdown requested...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await core.stop()
        print("NEXUS Integration Core stopped")

if __name__ == "__main__":
    asyncio.run(main())