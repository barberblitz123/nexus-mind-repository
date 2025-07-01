#!/usr/bin/env python3
"""
NEXUS Integration Core Client
Example client for interacting with the integration core
"""

import asyncio
import aiohttp
import json
from typing import Any, Dict, Optional

class NexusIntegrationClient:
    """Client for interacting with NEXUS Integration Core"""
    
    def __init__(self, base_url: str = "http://localhost:8080", token: Optional[str] = None):
        self.base_url = base_url
        self.token = token
        self.session = None
        self.ws = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()
    
    def _headers(self):
        """Get request headers"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def health_check(self) -> Dict[str, Any]:
        """Check system health"""
        async with self.session.get(f"{self.base_url}/health") as resp:
            return await resp.json()
    
    async def list_services(self) -> Dict[str, Any]:
        """List all registered services"""
        async with self.session.get(
            f"{self.base_url}/services",
            headers=self._headers()
        ) as resp:
            return await resp.json()
    
    async def invoke_service(self, service_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a service method"""
        async with self.session.post(
            f"{self.base_url}/services/{service_name}/invoke",
            json=data,
            headers=self._headers()
        ) as resp:
            return await resp.json()
    
    async def get_state(self, key: str) -> Dict[str, Any]:
        """Get state value"""
        async with self.session.get(
            f"{self.base_url}/state/{key}",
            headers=self._headers()
        ) as resp:
            return await resp.json()
    
    async def set_state(self, key: str, value: Any, 
                       expected_version: Optional[int] = None) -> Dict[str, Any]:
        """Set state value"""
        data = {"value": value}
        if expected_version is not None:
            data["expected_version"] = expected_version
        
        async with self.session.put(
            f"{self.base_url}/state/{key}",
            json=data,
            headers=self._headers()
        ) as resp:
            return await resp.json()
    
    async def publish_event(self, topic: str, payload: Any, priority: int = 1) -> Dict[str, Any]:
        """Publish an event"""
        async with self.session.post(
            f"{self.base_url}/events/{topic}",
            json={"payload": payload, "priority": priority},
            headers=self._headers()
        ) as resp:
            return await resp.json()
    
    async def connect_websocket(self):
        """Connect to WebSocket for real-time events"""
        ws_url = self.base_url.replace("http", "ws") + "/ws"
        self.ws = await self.session.ws_connect(ws_url)
        return self.ws
    
    async def subscribe_to_events(self, topic: str):
        """Subscribe to events via WebSocket"""
        if not self.ws:
            await self.connect_websocket()
        
        await self.ws.send_json({
            "type": "subscribe",
            "topic": topic
        })
    
    async def graphql_query(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute GraphQL query"""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        async with self.session.post(
            f"{self.base_url}/graphql",
            json=payload,
            headers=self._headers()
        ) as resp:
            return await resp.json()

# Example usage functions
async def demo_basic_operations():
    """Demonstrate basic client operations"""
    async with NexusIntegrationClient() as client:
        print("=== NEXUS Integration Client Demo ===\n")
        
        # Health check
        health = await client.health_check()
        print(f"System Health: {health['status']}")
        print(f"Active Services: {health['services']}\n")
        
        # List services
        services = await client.list_services()
        print("Registered Services:")
        for service in services['services']:
            print(f"  - {service['name']} v{service['version']} [{service['status']}]")
            print(f"    Capabilities: {', '.join(service['capabilities'])}")
        print()
        
        # Set and get state
        await client.set_state("demo_counter", 0)
        state = await client.get_state("demo_counter")
        print(f"Initial state: {state}")
        
        # Update state
        await client.set_state("demo_counter", 1, expected_version=state['version'])
        state = await client.get_state("demo_counter")
        print(f"Updated state: {state}")
        
        # Publish event
        result = await client.publish_event(
            "demo.test",
            {"message": "Hello from client!", "timestamp": asyncio.get_event_loop().time()},
            priority=2
        )
        print(f"\nPublished event: {result['message_id']}")

async def demo_graphql():
    """Demonstrate GraphQL operations"""
    async with NexusIntegrationClient() as client:
        print("\n=== GraphQL Demo ===\n")
        
        # Query all services
        query = """
        query {
            services {
                id
                name
                status
                capabilities
            }
        }
        """
        
        result = await client.graphql_query(query)
        print("GraphQL Services Query:")
        print(json.dumps(result, indent=2))
        
        # Query specific state
        query = """
        query GetState($key: String!) {
            state(key: $key) {
                key
                value
                version
            }
        }
        """
        
        result = await client.graphql_query(
            query,
            {"key": "system_metrics"}
        )
        print("\nGraphQL State Query:")
        print(json.dumps(result, indent=2))

async def demo_websocket_events():
    """Demonstrate WebSocket event subscription"""
    async with NexusIntegrationClient() as client:
        print("\n=== WebSocket Demo ===\n")
        
        # Connect and subscribe
        await client.connect_websocket()
        await client.subscribe_to_events("system.*")
        await client.subscribe_to_events("metrics.*")
        
        print("Subscribed to system and metrics events")
        print("Waiting for events (press Ctrl+C to stop)...\n")
        
        # Listen for events
        try:
            async for msg in client.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if data['type'] == 'event':
                        print(f"Event: {data['topic']}")
                        print(f"Payload: {json.dumps(data['payload'], indent=2)}")
                        print(f"Timestamp: {data['timestamp']}\n")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"WebSocket error: {msg.data}")
        except KeyboardInterrupt:
            print("\nStopping event listener...")

async def demo_service_invocation():
    """Demonstrate service invocation"""
    async with NexusIntegrationClient() as client:
        print("\n=== Service Invocation Demo ===\n")
        
        # Example: Invoke memory service
        print("Storing memory...")
        result = await client.publish_event(
            "memory.request",
            {
                "action": "store",
                "content": {
                    "text": "This is a test memory",
                    "context": "demo",
                    "importance": 0.8
                },
                "memory_type": "episodic"
            }
        )
        print(f"Memory store request: {result['message_id']}")
        
        # Example: Query memories
        print("\nQuerying memories...")
        result = await client.publish_event(
            "memory.request",
            {
                "action": "retrieve",
                "query": "test",
                "limit": 5
            }
        )
        print(f"Memory query request: {result['message_id']}")
        
        # Example: Submit MANUS task
        print("\nSubmitting MANUS task...")
        result = await client.publish_event(
            "manus.task.submit",
            {
                "description": "Analyze the current system performance",
                "priority": "high",
                "context": {
                    "requester": "demo_client",
                    "timeout": 300
                }
            }
        )
        print(f"MANUS task submitted: {result['message_id']}")

async def main():
    """Run all demos"""
    try:
        # Basic operations
        await demo_basic_operations()
        
        # GraphQL
        await demo_graphql()
        
        # Service invocation
        await demo_service_invocation()
        
        # WebSocket events (interactive)
        print("\n" + "="*50)
        print("Press Enter to start WebSocket event listener (Ctrl+C to stop)")
        input()
        await demo_websocket_events()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("NEXUS Integration Core Client")
    print("Make sure the integration core is running on http://localhost:8080")
    print("="*50 + "\n")
    
    asyncio.run(main())