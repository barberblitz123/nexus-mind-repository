#!/usr/bin/env python3
"""
NEXUS Connector - Bridges the web interface with the real agent system
This is what actually connects everything together!
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Import the REAL components
from nexus_stage_manager import StageManager, AgentWindow, AgentState
from nexus_desktop_manager import DesktopManager, PreviewType, ChatMessage
from nexus_task_orchestrator import TaskOrchestrator
from nexus_autonomous_agent import AutonomousMANUS

# Import YouTube connector for scraping capabilities
try:
    from nexus_youtube_connector import YouTubeAgentConnector
    YOUTUBE_AVAILABLE = True
except ImportError:
    YOUTUBE_AVAILABLE = False
    logger.warning("YouTube scraping not available - install required packages")

logger = logging.getLogger(__name__)

class NEXUSConnector:
    """Connects the web interface to the real NEXUS system"""
    
    def __init__(self):
        # Initialize the REAL managers
        self.stage_manager = StageManager(max_active_agents=6)
        self.desktop_manager = DesktopManager(stage_manager=self.stage_manager)
        self.task_orchestrator = TaskOrchestrator(
            self.stage_manager, 
            self.desktop_manager
        )
        
        # Initialize YouTube connector if available
        self.youtube_connector = YouTubeAgentConnector() if YOUTUBE_AVAILABLE else None
        
        # Track websocket connections
        self.websocket_clients = set()
        
        # Setup message routing
        self._setup_message_routing()
        
    def _setup_message_routing(self):
        """Connect the managers to broadcast updates to web clients"""
        
        # Override desktop manager's add_chat_message to broadcast
        original_add_chat = self.desktop_manager.add_chat_message
        
        def broadcast_chat_message(sender: str, content: str, **kwargs):
            # Call original method
            msg = original_add_chat(sender, content, **kwargs)
            
            # Broadcast to web clients
            asyncio.create_task(self.broadcast_to_web({
                "type": "chat_message",
                "sender": sender,
                "message": content,
                "time": datetime.now().isoformat()
            }))
            
            return msg
            
        self.desktop_manager.add_chat_message = broadcast_chat_message
        
    async def broadcast_to_web(self, data: Dict[str, Any]):
        """Send updates to all connected web clients"""
        if self.websocket_clients:
            message = json.dumps(data)
            # Send to all connected clients
            disconnected = set()
            for client in self.websocket_clients:
                try:
                    await client.send(message)
                except:
                    disconnected.add(client)
            
            # Remove disconnected clients
            self.websocket_clients -= disconnected
            
    async def handle_web_command(self, command: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process commands from the web interface"""
        cmd_type = command.get('type')
        
        if cmd_type == 'chat_message':
            return await self._handle_chat_message(command)
        elif cmd_type == 'create_agent':
            return await self._handle_create_agent(command)
        elif cmd_type == 'terminal_command':
            return await self._handle_terminal_command(command)
        elif cmd_type == 'focus_agent':
            return await self._handle_focus_agent(command)
        elif cmd_type == 'get_state':
            return await self._get_current_state()
        elif cmd_type == 'youtube_command':
            return await self._handle_youtube_command(command)
        else:
            return {"error": f"Unknown command type: {cmd_type}"}
            
    async def _handle_chat_message(self, command: Dict[str, Any]):
        """Process a chat message - this triggers the REAL task orchestrator"""
        message = command.get('message', '')
        
        # Add to chat history
        self.desktop_manager.add_chat_message('user', message)
        
        # Check if this is a YouTube-related request
        if self._is_youtube_request(message):
            return await self._handle_youtube_chat(message)
        
        # Process through the REAL task orchestrator
        # This is where agents get created based on the message!
        await self.task_orchestrator.handle_user_message(
            ChatMessage(
                id="msg-" + str(datetime.now().timestamp()),
                sender="user",
                content=message,
                timestamp=datetime.now()
            )
        )
        
        return {"status": "processed"}
        
    async def _handle_create_agent(self, command: Dict[str, Any]):
        """Manually create an agent"""
        name = command.get('name', 'New Agent')
        agent_type = command.get('agent_type', 'general')
        task = command.get('task', '')
        
        # Create through stage manager
        window = self.stage_manager.create_agent_window(name, agent_type)
        window.current_task = task
        window.state = AgentState.WORKING
        
        # Create the actual autonomous agent
        agent = AutonomousMANUS(
            name=name,
            capabilities=[agent_type],
            memory_enabled=True
        )
        
        # Store in orchestrator's agent pool
        self.task_orchestrator.agent_pool[window.id] = agent
        
        # Broadcast the creation
        await self.broadcast_to_web({
            "type": "agent_created",
            "agent": {
                "id": window.id,
                "name": window.name,
                "type": window.agent_type,
                "state": window.state.value,
                "task": window.current_task,
                "createdAt": window.created_at.isoformat()
            }
        })
        
        # Start the agent working
        asyncio.create_task(
            self.task_orchestrator._run_agent_task(
                window, agent, window.id, 
                self.desktop_manager.create_preview_pane(
                    f"Output: {name}", PreviewType.TERMINAL
                ).id
            )
        )
        
        return {"status": "created", "agent_id": window.id}
        
    async def _handle_terminal_command(self, command: Dict[str, Any]):
        """Execute a terminal command"""
        cmd = command.get('command', '')
        
        # Execute through desktop manager
        result = self.desktop_manager.execute_command(cmd)
        
        # Broadcast output
        await self.broadcast_to_web({
            "type": "terminal_output",
            "output": str(result)
        })
        
        return result
        
    async def _handle_focus_agent(self, command: Dict[str, Any]):
        """Focus on a specific agent"""
        agent_id = command.get('agent_id')
        
        if agent_id:
            self.stage_manager.switch_to_agent(agent_id)
            
            await self.broadcast_to_web({
                "type": "agent_focused",
                "agent_id": agent_id
            })
            
        return {"status": "focused"}
        
    async def _get_current_state(self):
        """Get the complete current state of the system"""
        # Get stage layout
        stage_layout = self.stage_manager.get_stage_layout()
        
        # Get chat history
        chat_messages = [
            {
                "sender": msg.sender,
                "message": msg.content,
                "time": msg.timestamp.isoformat()
            }
            for msg in self.desktop_manager.chat_history[-50:]
        ]
        
        # Get preview panes
        preview_panes = [
            {
                "id": pane.id,
                "title": pane.title,
                "type": pane.preview_type.value,
                "content": pane.content[:1000] if pane.content else None
            }
            for pane in self.desktop_manager.preview_panes.values()
        ]
        
        return {
            "stage_layout": stage_layout,
            "chat_messages": chat_messages,
            "preview_panes": preview_panes,
            "system_status": "connected"
        }
        
    async def monitor_agents(self):
        """Monitor agent states and broadcast updates"""
        while True:
            # Check all agents
            for agent_id, window in self.stage_manager.agent_windows.items():
                # Broadcast state updates
                await self.broadcast_to_web({
                    "type": "agent_updated",
                    "agent": {
                        "id": agent_id,
                        "state": window.state.value,
                        "task": window.current_task
                    }
                })
                
            # Send system metrics
            await self.broadcast_to_web({
                "type": "system_metrics",
                "metrics": {
                    "active_agents": len(self.stage_manager.active_stage),
                    "background_agents": len(self.stage_manager.side_stage),
                    "total_agents": len(self.stage_manager.agent_windows),
                    "memory_usage": "Real memory data",
                    "cpu_usage": "Real CPU data"
                }
            })
            
            await asyncio.sleep(2)  # Update every 2 seconds
    
    def _is_youtube_request(self, message: str) -> bool:
        """Check if the message is YouTube-related"""
        import re
        
        # Check for YouTube URLs
        youtube_patterns = [
            r'youtube\.com/watch\?v=',
            r'youtu\.be/',
            r'youtube\.com/playlist',
            r'youtube\.com/channel/'
        ]
        
        # Check for YouTube keywords
        youtube_keywords = ['youtube', 'video', 'transcript', 'captions', 'subtitles']
        
        message_lower = message.lower()
        
        # Check patterns
        for pattern in youtube_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        
        # Check keywords with URL
        if any(keyword in message_lower for keyword in youtube_keywords) and ('http' in message_lower or 'www' in message_lower):
            return True
        
        return False
    
    async def _handle_youtube_chat(self, message: str):
        """Handle YouTube-related chat messages"""
        if not self.youtube_connector:
            # YouTube not available - create agent to handle it
            error_msg = "YouTube scraping capabilities not available. I need to install: yt-dlp, youtube-transcript-api"
            self.desktop_manager.add_chat_message('system', error_msg)
            
            # Create an enhancement agent
            window = self.stage_manager.create_agent_window(
                "YouTube Enhancement Agent",
                "self_enhancement"
            )
            window.current_task = "Install YouTube scraping dependencies"
            window.state = AgentState.WORKING
            
            # Broadcast the limitation
            await self.broadcast_to_web({
                "type": "enhancement_needed",
                "capability": "YouTube scraping",
                "packages": ["yt-dlp", "youtube-transcript-api"],
                "message": error_msg
            })
            
            return {"status": "enhancement_needed"}
        
        # Process through YouTube connector
        try:
            # Import the process_chat_message function
            from nexus_youtube_connector import process_chat_message
            result = await process_chat_message(message)
            
            # Create a YouTube scraping agent
            window = self.stage_manager.create_agent_window(
                "YouTube Scraper",
                "youtube_scraper"
            )
            window.current_task = f"Processing: {message[:50]}..."
            window.state = AgentState.WORKING
            
            # Handle the result
            if result.get("status") == "enhancement_needed":
                # Self-enhancement response
                response = result.get("user_message", "I need additional capabilities for this task.")
                self.desktop_manager.add_chat_message('YouTube Agent', response)
                window.state = AgentState.WAITING
            elif result.get("success"):
                # Success response
                if "data" in result and "metadata" in result["data"]:
                    meta = result["data"]["metadata"]
                    response = f"✅ Successfully scraped: {meta.get('title', 'Video')}\n"
                    response += f"Duration: {meta.get('duration', 0)} seconds\n"
                    response += f"Views: {meta.get('view_count', 0)}"
                else:
                    response = "✅ YouTube scraping completed successfully!"
                
                self.desktop_manager.add_chat_message('YouTube Agent', response)
                window.state = AgentState.COMPLETED
                
                # Create preview pane with results
                preview = self.desktop_manager.create_preview_pane(
                    "YouTube Results",
                    PreviewType.DATA
                )
                preview.content = json.dumps(result, indent=2)
            else:
                # Error response
                error = result.get("error", "Unknown error")
                self.desktop_manager.add_chat_message('YouTube Agent', f"❌ Error: {error}")
                window.state = AgentState.ERROR
            
            # Broadcast result
            await self.broadcast_to_web({
                "type": "youtube_result",
                "result": result,
                "agent_id": window.id
            })
            
            return {"status": "processed", "result": result}
            
        except Exception as e:
            logger.error(f"YouTube processing error: {e}")
            self.desktop_manager.add_chat_message('system', f"Error processing YouTube request: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def _handle_youtube_command(self, command: Dict[str, Any]):
        """Handle direct YouTube commands"""
        if not self.youtube_connector:
            return {
                "status": "error",
                "error": "YouTube capabilities not available",
                "enhancement_needed": True,
                "packages": ["yt-dlp", "youtube-transcript-api"]
            }
        
        # Extract command details
        youtube_cmd = command.get("youtube_command", "help")
        params = command.get("params", {})
        
        # Execute through YouTube connector
        try:
            result = await self.youtube_connector.handle_command(youtube_cmd, params)
            
            # Broadcast result
            await self.broadcast_to_web({
                "type": "youtube_command_result",
                "command": youtube_cmd,
                "result": result
            })
            
            return result
            
        except Exception as e:
            logger.error(f"YouTube command error: {e}")
            return {"status": "error", "error": str(e)}

# Singleton instance
_connector_instance = None

def get_connector() -> NEXUSConnector:
    """Get the singleton connector instance"""
    global _connector_instance
    if _connector_instance is None:
        _connector_instance = NEXUSConnector()
    return _connector_instance