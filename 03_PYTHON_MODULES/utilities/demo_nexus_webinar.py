#!/usr/bin/env python3
"""
NEXUS Webinar Interface Demo
Demonstrates the webinar functionality with the new NEXUS 2.0 build
"""

import asyncio
import aiohttp
import json
import uuid
from datetime import datetime
from typing import Dict, Any

# Configuration
WEBINAR_BASE_URL = "http://localhost:8003"
DEMO_SESSION_ID = "demo-session-" + str(uuid.uuid4())[:8]


class WebinarDemo:
    """Demo client for NEXUS Webinar Interface"""
    
    def __init__(self):
        self.session = None
        self.ws = None
        
    async def create_session(self) -> Dict[str, Any]:
        """Create a new webinar session"""
        async with aiohttp.ClientSession() as session:
            data = {
                "title": "NEXUS 2.0 Demo Webinar",
                "description": "Demonstrating the new webinar interface",
                "host_id": "demo-host",
                "max_participants": 50,
                "features": {
                    "chat": True,
                    "video": True,
                    "screen_share": True,
                    "ai_assistance": True
                }
            }
            
            async with session.post(
                f"{WEBINAR_BASE_URL}/api/webinar/create",
                json=data
            ) as resp:
                result = await resp.json()
                print(f"✅ Created session: {result['session_id']}")
                return result
    
    async def join_session(self, session_id: str, user_id: str, display_name: str, role: str = "participant"):
        """Join a webinar session"""
        async with aiohttp.ClientSession() as session:
            data = {
                "session_id": session_id,
                "user_id": user_id,
                "display_name": display_name,
                "role": role
            }
            
            async with session.post(
                f"{WEBINAR_BASE_URL}/api/webinar/join",
                json=data
            ) as resp:
                result = await resp.json()
                print(f"✅ {display_name} joined as {role}")
                return result
    
    async def connect_websocket(self, session_id: str, user_id: str):
        """Connect to webinar WebSocket"""
        ws_url = f"ws://localhost:8003/ws/webinar"
        
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url) as ws:
                # Authenticate
                await ws.send_json({
                    "type": "authenticate",
                    "session_id": session_id,
                    "user_id": user_id
                })
                
                print(f"✅ WebSocket connected for {user_id}")
                
                # Listen for messages
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        await self.handle_websocket_message(data)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f'❌ WebSocket error: {ws.exception()}')
                        break
    
    async def handle_websocket_message(self, data: Dict[str, Any]):
        """Handle incoming WebSocket messages"""
        msg_type = data.get("type")
        
        if msg_type == "participant_joined":
            print(f"👤 {data['participant']['display_name']} joined")
        elif msg_type == "participant_left":
            print(f"👤 {data['display_name']} left")
        elif msg_type == "chat_message":
            msg = data["message"]
            print(f"💬 {msg['author']}: {msg['content']}")
        elif msg_type == "ai_response":
            print(f"🤖 AI: {data['response']['content']}")
        elif msg_type == "system_notification":
            print(f"📢 System: {data['message']}")
    
    async def send_chat_message(self, ws, session_id: str, user_id: str, message: str):
        """Send a chat message"""
        await ws.send_json({
            "type": "chat_message",
            "session_id": session_id,
            "user_id": user_id,
            "message": message
        })
    
    async def query_ai_assistant(self, session_id: str, query: str) -> Dict[str, Any]:
        """Query the AI assistant"""
        async with aiohttp.ClientSession() as session:
            data = {
                "session_id": session_id,
                "query": query,
                "context": {
                    "demo": True,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            async with session.post(
                f"{WEBINAR_BASE_URL}/api/webinar/ai-assist",
                json=data
            ) as resp:
                result = await resp.json()
                print(f"🤖 AI Response: {result['content']}")
                return result
    
    async def check_health(self):
        """Check webinar service health"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{WEBINAR_BASE_URL}/health") as resp:
                health = await resp.json()
                print(f"🏥 Service Health: {health['status']}")
                return health


async def run_demo():
    """Run the webinar demo"""
    print("🚀 NEXUS Webinar Interface Demo")
    print("=" * 50)
    
    demo = WebinarDemo()
    
    # 1. Check service health
    print("\n1. Checking service health...")
    try:
        await demo.check_health()
    except Exception as e:
        print(f"❌ Service not available: {e}")
        print("Make sure the webinar interface is running:")
        print("  python nexus_webinar_interface.py")
        return
    
    # 2. Create a session
    print("\n2. Creating webinar session...")
    session_result = await demo.create_session()
    session_id = session_result["session_id"]
    
    # 3. Join as host
    print("\n3. Joining as host...")
    await demo.join_session(session_id, "host-001", "Demo Host", "host")
    
    # 4. Join as participants
    print("\n4. Adding participants...")
    participants = [
        ("user-001", "Alice", "participant"),
        ("user-002", "Bob", "participant"),
        ("user-003", "Charlie", "viewer")
    ]
    
    for user_id, name, role in participants:
        await demo.join_session(session_id, user_id, name, role)
        await asyncio.sleep(0.5)
    
    # 5. Test AI assistant
    print("\n5. Testing AI assistant...")
    await demo.query_ai_assistant(
        session_id,
        "What are the best practices for running an effective webinar?"
    )
    
    # 6. Simulate chat messages
    print("\n6. Simulating chat activity...")
    print("(WebSocket simulation - in real usage, connect via WebSocket)")
    
    messages = [
        ("Alice", "Hello everyone! 👋"),
        ("Bob", "Hi Alice! Excited for the demo"),
        ("Demo Host", "Welcome everyone! Let's get started"),
        ("Charlie", "Thanks for hosting this session!")
    ]
    
    for author, message in messages:
        print(f"💬 {author}: {message}")
        await asyncio.sleep(1)
    
    # 7. List sessions
    print("\n7. Listing active sessions...")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{WEBINAR_BASE_URL}/api/webinar/sessions") as resp:
            sessions = await resp.json()
            print(f"📋 Active sessions: {len(sessions)}")
            for sess in sessions:
                print(f"   - {sess.get('title', 'Untitled')} ({sess['id']})")
    
    print("\n✅ Demo completed!")
    print("\nTo see the full interface, open: http://localhost:8003")
    print("You can join with session ID:", session_id)


async def interactive_client():
    """Interactive WebSocket client for testing"""
    print("🎙️ NEXUS Webinar Interactive Client")
    print("=" * 50)
    
    session_id = input("Enter session ID (or press Enter for new): ").strip()
    
    demo = WebinarDemo()
    
    if not session_id:
        # Create new session
        result = await demo.create_session()
        session_id = result["session_id"]
    
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    display_name = input("Enter your name: ").strip() or "Anonymous"
    role = input("Enter role (host/participant/viewer) [participant]: ").strip() or "participant"
    
    # Join session
    await demo.join_session(session_id, user_id, display_name, role)
    
    print(f"\n✅ Joined session: {session_id}")
    print("Connecting to WebSocket...")
    
    # In a real implementation, this would maintain the WebSocket connection
    # and allow interactive messaging
    print("\n💡 Tip: Use the web interface for full interactive experience")
    print(f"   Open: http://localhost:8003")
    print(f"   Session ID: {session_id}")


async def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        await interactive_client()
    else:
        await run_demo()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()