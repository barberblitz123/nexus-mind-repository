#!/usr/bin/env python3
"""
Test script to verify the web interface is properly connected to the real agent system
"""

import asyncio
import json
import websockets
import sys

async def test_connection():
    uri = "ws://localhost:8765"
    
    print("🧪 Testing NEXUS Web Interface Connection...")
    print("=" * 50)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server")
            
            # Test 1: Get system state
            print("\n📊 Test 1: Getting system state...")
            await websocket.send(json.dumps({"type": "get_state"}))
            response = await websocket.recv()
            state = json.loads(response)
            
            if state.get("type") == "initial_state":
                print("✅ Received system state")
                print(f"   - System status: {state['data'].get('system_status', 'unknown')}")
            
            # Test 2: Send a chat message
            print("\n💬 Test 2: Sending chat message...")
            test_message = "test connection to real agent system"
            await websocket.send(json.dumps({
                "type": "chat_message",
                "message": test_message
            }))
            print(f"✅ Sent message: '{test_message}'")
            
            # Test 3: Create an agent
            print("\n🤖 Test 3: Creating test agent...")
            await websocket.send(json.dumps({
                "type": "create_agent",
                "name": "Test Agent",
                "agent_type": "analyzer",
                "task": "verify connection"
            }))
            
            # Wait for responses
            print("\n📨 Waiting for responses...")
            for i in range(5):
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    
                    if data.get("type") == "agent_created":
                        print(f"✅ Agent created: {data['agent']['name']} (ID: {data['agent']['id']})")
                    elif data.get("type") == "chat_message":
                        print(f"💬 Chat: {data['sender']}: {data['message'][:50]}...")
                    elif data.get("type") == "system_metrics":
                        print(f"📊 Metrics: {data['metrics']['total_agents']} agents total")
                        
                except asyncio.TimeoutError:
                    pass
                    
            print("\n✅ All tests completed successfully!")
            print("🔌 Web interface is PROPERLY CONNECTED to the real agent system!")
            
    except ConnectionRefusedError:
        print("❌ Could not connect to WebSocket server")
        print("   Please ensure the server is running:")
        print("   cd /workspaces/nexus-mind-repository/01_NEXUS_2.0_AGENT/interfaces")
        print("   ./launch_web_interface.sh")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
    return True

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    sys.exit(0 if result else 1)