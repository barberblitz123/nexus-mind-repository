#!/usr/bin/env python3
"""
NEXUS 2.0 WebSocket Server
Bridges the web interface with the Python agent system
Now with REAL connection to the agent system!
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime
from typing import Dict, List, Set, Any
import sys
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    # Import the REAL connector!
    from interfaces.nexus_connector import get_connector, NEXUSConnector
    REAL_SYSTEM_AVAILABLE = True
    logger.info("✅ REAL NEXUS system loaded successfully!")
except ImportError as e:
    logger.warning(f"Could not load REAL NEXUS system: {e}")
    # Try alternative import path
    try:
        from nexus_connector import get_connector, NEXUSConnector
        REAL_SYSTEM_AVAILABLE = True
        logger.info("✅ REAL NEXUS system loaded successfully (alternative path)!")
    except ImportError as e2:
        logger.warning(f"Could not load REAL NEXUS system from alternative path: {e2}")
        REAL_SYSTEM_AVAILABLE = False
    
    # Fallback to demo mode if needed
    class NEXUSConnector:
        def __init__(self):
            self.agents = {}
            logger.warning("Running in DEMO mode - not connected to real agents!")
            
        async def create_agent(self, agent_id, name, agent_type):
            return {"agent_id": agent_id, "name": name, "type": agent_type, "status": "demo"}
            
        async def execute_agent_task(self, agent_id, task):
            return {"success": False, "output": "Running in demo mode", "error": None}
            
        async def get_system_metrics(self):
            return {"demo": True}
            
    def get_connector():
        return NEXUSConnector()

class NEXUSWebSocketServer:
    def __init__(self):
        # Get the REAL connector - this connects to actual agents!
        self.connector = get_connector()
        
        # Track WebSocket clients
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        
        logger.info(f"🚀 WebSocket server initialized with {'REAL' if REAL_SYSTEM_AVAILABLE else 'DEMO'} system")
        
    async def register(self, websocket):
        """Register a new client connection"""
        self.clients.add(websocket)
        logger.info(f"✅ Client connected. Total clients: {len(self.clients)}")
        
        # Send initial state from the real system
        await self.send_initial_state(websocket)
        
    async def unregister(self, websocket):
        """Remove a client connection"""
        self.clients.discard(websocket)
        logger.info(f"👋 Client disconnected. Total clients: {len(self.clients)}")
        
    async def send_initial_state(self, websocket):
        """Send the current state to a newly connected client"""
        try:
            # Get metrics from the real system
            metrics = await self.connector.get_system_metrics()
            
            # Get list of active agents - handle case where agents might not have expected structure
            agents = []
            if hasattr(self.connector, 'agents') and self.connector.agents:
                for agent_id, executor in self.connector.agents.items():
                    try:
                        tasks_completed = 0
                        if hasattr(executor, 'memory') and isinstance(executor.memory, dict):
                            tasks_completed = executor.memory.get("tasks_completed", 0)
                        
                        agents.append({
                            "id": agent_id,
                            "name": f"Agent-{agent_id[:8]}",
                            "type": "developer",
                            "state": "ready",
                            "tasks_completed": tasks_completed
                        })
                    except Exception as e:
                        logger.warning(f"Error processing agent {agent_id}: {e}")
            
            await websocket.send(json.dumps({
                "type": "initial_state",
                "data": {
                    "agents": agents,
                    "metrics": metrics,
                    "system_status": "connected"
                }
            }))
            logger.info(f"✅ Sent initial state with {len(agents)} agents")
            
        except Exception as e:
            logger.error(f"❌ Error sending initial state: {e}")
            # Send a basic response to keep connection alive
            await websocket.send(json.dumps({
                "type": "initial_state",
                "data": {
                    "agents": [],
                    "metrics": {"status": "connected"},
                    "system_status": "connected"
                }
            }))
            
    async def handle_message(self, websocket, message: str):
        """Process incoming messages from clients"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            logger.info(f"📨 Received command: {msg_type}")
            
            # Handle different message types
            if msg_type == 'chat':
                # User sent a chat message
                content = data.get('content', '')
                await self.handle_chat_message(content)
                
            elif msg_type == 'create_agent':
                # Create a new agent
                agent_data = await self.connector.create_agent(
                    data.get('agent_id', f'agent-{datetime.now().timestamp()}'),
                    data.get('name', 'New Agent'),
                    data.get('agent_type', 'developer')
                )
                await self.broadcast_update('agent_created', agent_data)
                
            elif msg_type == 'execute_task':
                # Execute task on agent
                result = await self.connector.execute_agent_task(
                    data.get('agent_id'),
                    data.get('task')
                )
                await self.broadcast_update('task_result', result)
                
            elif msg_type == 'get_logs':
                # Export and send logs
                log_path = await self.connector.export_logs()
                await websocket.send(json.dumps({
                    "type": "logs_exported",
                    "path": log_path
                }))
                
            elif msg_type == 'get_metrics':
                # Get system metrics
                metrics = await self.connector.get_system_metrics()
                await websocket.send(json.dumps({
                    "type": "metrics",
                    "data": metrics
                }))
                
        except json.JSONDecodeError:
            logger.error(f"❌ Invalid JSON received: {message}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON format"
            }))
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
            await websocket.send(json.dumps({
                "type": "error", 
                "message": str(e)
            }))
            
    async def handler(self, websocket, path):
        """Handle a client connection"""
        await self.register(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        finally:
            await self.unregister(websocket)

    async def handle_chat_message(self, content: str):
        """Handle chat messages and create agents based on requests"""
        try:
            logger.info(f"📨 Processing chat message: {content}")
            
            # For any message, create an agent to handle it
            agent_id = f'agent-{datetime.now().strftime("%H%M%S")}'
            
            # Determine agent type based on content
            content_lower = content.lower()
            agent_type = 'general'
            
            if any(word in content_lower for word in ['analyz', 'examine', 'inspect', 'review']):
                agent_type = 'analyst'
            elif any(word in content_lower for word in ['build', 'create', 'develop', 'code']):
                agent_type = 'developer'
            elif any(word in content_lower for word in ['deploy', 'devops', 'infrastructure']):
                agent_type = 'devops'
            elif any(word in content_lower for word in ['test', 'verify', 'validate']):
                agent_type = 'tester'
            
            # Create agent with real NEXUS system
            agent_data = await self.connector.create_agent(
                agent_id,
                f"{agent_type.title()} Agent",
                agent_type
            )
            
            logger.info(f"✅ Created agent: {agent_data}")
            await self.broadcast_update('agent_created', agent_data)
            
            # Execute the task
            result = await self.connector.execute_agent_task(agent_id, content)
            logger.info(f"✅ Task result: {result}")
            
            await self.broadcast_update('task_result', {
                'agent_id': agent_id,
                **result
            })
            
        except Exception as e:
            logger.error(f"❌ Error handling chat message: {e}")
            # Send error response
            await self.broadcast_update('error', {
                'message': f"Error processing request: {str(e)}",
                'original_content': content
            })
    
    async def broadcast_update(self, update_type: str, data: dict):
        """Broadcast updates to all connected clients"""
        message = json.dumps({
            "type": update_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
        # Send to all connected clients
        if self.clients:
            await asyncio.wait([client.send(message) for client in self.clients])

async def main():
    """Start the WebSocket server"""
    server = NEXUSWebSocketServer()
    
    # Start WebSocket server
    logger.info("🌐 Starting NEXUS WebSocket server on ws://localhost:8765")
    if REAL_SYSTEM_AVAILABLE:
        logger.info("🎯 Web interface is now CONNECTED to the real agent system!")
        logger.info("✨ Agents will execute REAL code, not simulations!")
    else:
        logger.info("⚠️  Running in DEMO mode - install dependencies for real execution")
    
    async with websockets.serve(server.handler, "localhost", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")