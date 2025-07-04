#!/usr/bin/env python3
"""
NEXUS Task Orchestrator
Connects Desktop Manager (chat) to Stage Manager (agent windows)
Each task creates a new agent window that runs simultaneously
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Callable
from datetime import datetime
import re

from nexus_stage_manager import StageManager, AgentWindow, AgentState
from nexus_desktop_manager import DesktopManager, PreviewType
from nexus_autonomous_agent import AutonomousMANUS
from nexus_youtube_scraper import YouTubeScraperAgent

class TaskOrchestrator:
    """Orchestrates tasks from chat to agent windows"""
    
    def __init__(self, stage_manager: StageManager, desktop_manager: DesktopManager):
        self.stage_manager = stage_manager
        self.desktop_manager = desktop_manager
        self.active_tasks: Dict[str, Dict] = {}
        self.agent_pool: Dict[str, AutonomousMANUS] = {}
        
        # Register chat handler to intercept task assignments
        self.desktop_manager.register_message_handler("user", self.handle_user_message)
        
    async def handle_user_message(self, message):
        """Parse user messages for task assignments"""
        content = message.content.lower()
        
        # Check if this message was already processed
        if hasattr(message, '_processed'):
            return
            
        # Detect task assignment patterns - ordered by specificity
        task_patterns = [
            # YouTube patterns (highest priority)
            (r"scrape youtube video (.+)", 1),
            (r"scrape (.+youtube\.com.+)", 1),
            (r"scrape (.+youtu\.be.+)", 1),
            (r"search youtube for (.+)", 1),
            (r"find youtube videos? about (.+)", 1),
            (r"analyze youtube video (.+)", 1),
            (r"get youtube video (?:information|info) (?:for )?(.+)", 1),
            
            # Regular patterns
            (r"create (.*?) agent", 1),  # Most specific
            (r"assign task[:]? (.*)", 1),
            (r"build (.*)", 1),
            (r"implement (.*)", 1),
            (r"fix (.*)", 1),
            (r"analyze (.*)", 1),
            (r"help me (.*)", 1),
            (r"can you (.*)", 1),
            (r"i need (.*)", 1),
            (r"please (.*)", 1)  # Least specific
        ]
        
        for pattern, group_num in task_patterns:
            match = re.search(pattern, content)
            if match:
                task_description = match.group(group_num)
                # Mark message as processed to prevent duplicate handling
                message._processed = True
                await self.create_task_agent(task_description, message.content)
                return  # Exit function completely after creating one agent
                
    async def create_task_agent(self, task_type: str, full_task: str):
        """Create a new agent window for a task"""
        # Check if we recently created an agent for a similar task
        current_time = datetime.now()
        for task in self.active_tasks.values():
            # Prevent duplicate agents within 2 seconds for similar tasks
            if (task['description'].lower() == full_task.lower() and 
                (current_time - task['created_at']).total_seconds() < 2):
                self.desktop_manager.add_chat_message(
                    "system",
                    f"Agent already created for this task: {task['agent_id']}"
                )
                return
        
        # Determine agent type based on task
        agent_type = self._determine_agent_type(task_type)
        
        # Create agent window in Stage Manager
        window = self.stage_manager.create_agent_window(
            name=f"{agent_type.title()} - {task_type[:20]}",
            agent_type=agent_type
        )
        
        # Create actual autonomous agent
        agent = AutonomousMANUS(
            name=window.name,
            capabilities=[agent_type],
            memory_enabled=True
        )
        
        self.agent_pool[window.id] = agent
        
        # Update window state
        window.state = AgentState.WORKING
        window.current_task = full_task
        
        # Create task record
        task_id = str(uuid.uuid4())
        self.active_tasks[task_id] = {
            "id": task_id,
            "description": full_task,
            "agent_id": window.id,
            "status": "active",
            "created_at": datetime.now(),
            "updates": []
        }
        
        # Notify via chat
        self.desktop_manager.add_chat_message(
            window.id,
            f"Task accepted. Starting work on: {task_type}"
        )
        
        # Create preview pane for this task
        preview = self.desktop_manager.create_preview_pane(
            title=f"Task: {task_type[:30]}",
            preview_type=PreviewType.TERMINAL
        )
        
        # Start the agent working
        asyncio.create_task(self._run_agent_task(window, agent, task_id, preview.id))
        
    def _determine_agent_type(self, task_description: str) -> str:
        """Determine which type of agent to create based on task"""
        task_lower = task_description.lower()
        
        # YouTube tasks get special agent
        if any(word in task_lower for word in ["youtube", "youtu.be", "video"]):
            return "youtube_scraper"
        elif any(word in task_lower for word in ["code", "implement", "build", "fix", "debug"]):
            return "developer"
        elif any(word in task_lower for word in ["research", "analyze", "find", "search"]):
            return "researcher"
        elif any(word in task_lower for word in ["design", "ui", "interface", "layout"]):
            return "designer"
        elif any(word in task_lower for word in ["test", "verify", "check", "validate"]):
            return "tester"
        elif any(word in task_lower for word in ["document", "write", "explain"]):
            return "documenter"
        elif any(word in task_lower for word in ["review", "audit", "inspect"]):
            return "reviewer"
        elif any(word in task_lower for word in ["deploy", "release", "publish"]):
            return "deployer"
        else:
            return "general"
            
    async def _run_agent_task(self, window: AgentWindow, agent: AutonomousMANUS, 
                             task_id: str, preview_id: str):
        """Run an agent task asynchronously"""
        try:
            # Update window to show thinking
            window.state = AgentState.THINKING
            
            # Check if this is a YouTube task
            task_desc = self.active_tasks[task_id]["description"]
            if window.agent_type == "youtube_scraper":
                await self._run_youtube_task(window, task_id, preview_id)
                return
            
            # Agent processes the task
            steps = await agent.plan_task(self.active_tasks[task_id]["description"])
            
            # Show plan in preview
            plan_text = "Task Plan:\n" + "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))
            self.desktop_manager.update_preview_content(preview_id, plan_text)
            
            # Execute each step
            for i, step in enumerate(steps):
                window.state = AgentState.WORKING
                window.current_task = f"Step {i+1}/{len(steps)}: {step}"
                
                # Simulate work (in real implementation, actually execute)
                await asyncio.sleep(2)
                
                # Update progress
                progress = f"\n✓ Completed: {step}"
                current_content = self.desktop_manager.preview_panes[preview_id].content
                self.desktop_manager.update_preview_content(
                    preview_id, 
                    current_content + progress
                )
                
                # Send update to chat
                self.desktop_manager.add_chat_message(
                    window.id,
                    f"Completed step {i+1}: {step}"
                )
                
                # Record update
                self.active_tasks[task_id]["updates"].append({
                    "timestamp": datetime.now(),
                    "message": f"Completed: {step}"
                })
                
            # Task complete
            window.state = AgentState.IDLE
            window.current_task = "Task completed"
            self.active_tasks[task_id]["status"] = "completed"
            
            # Final message
            self.desktop_manager.add_chat_message(
                window.id,
                f"✅ Task completed successfully!"
            )
            
        except Exception as e:
            window.state = AgentState.ERROR
            self.active_tasks[task_id]["status"] = "error"
            self.desktop_manager.add_chat_message(
                window.id,
                f"❌ Error: {str(e)}"
            )
    
    async def _run_youtube_task(self, window: AgentWindow, task_id: str, preview_id: str):
        """Run YouTube-specific tasks"""
        try:
            # Create YouTube scraper agent
            youtube_agent = YouTubeScraperAgent(window.name)
            
            # Parse the task
            task_desc = self.active_tasks[task_id]["description"].lower()
            
            # Update preview
            self.desktop_manager.update_preview_content(
                preview_id,
                "🎥 YouTube Scraper Agent\n" + "="*40 + "\n\nAnalyzing task..."
            )
            
            # Determine task type
            if "search" in task_desc:
                # Extract search query
                match = re.search(r'search youtube for (.+)', task_desc)
                if match:
                    query = match.group(1)
                    window.state = AgentState.WORKING
                    window.current_task = f"Searching YouTube for: {query}"
                    
                    # Execute search
                    result = await youtube_agent.execute_task({
                        'type': 'search',
                        'query': query,
                        'max_results': 5
                    })
                    
                    # Display results
                    content = f"🔍 Search Results for '{query}':\n\n"
                    for i, video in enumerate(result.get('results', [])):
                        content += f"{i+1}. {video.get('title', 'Unknown')}\n"
                        content += f"   URL: {video.get('url', 'N/A')}\n\n"
                    
                    self.desktop_manager.update_preview_content(preview_id, content)
                    
            else:
                # Extract URL for scraping
                url_match = re.search(r'(https?://(?:www\.)?youtube\.com/watch\?v=[^\s]+|https?://youtu\.be/[^\s]+)', task_desc)
                if url_match:
                    url = url_match.group(1)
                    window.state = AgentState.WORKING
                    window.current_task = f"Scraping video: {url}"
                    
                    # Execute scrape
                    result = await youtube_agent.execute_task({
                        'type': 'scrape',
                        'url': url
                    })
                    
                    # Display results
                    if result.get('success'):
                        content = "📹 Video Information:\n" + "="*40 + "\n\n"
                        content += f"Title: {result['title']}\n"
                        content += f"Author: {result['author']}\n"
                        content += f"Views: {result['views']}\n"
                        content += f"Likes: {result['likes']}\n"
                        content += f"Duration: {result['duration']}\n"
                        content += f"Upload Date: {result['upload_date']}\n\n"
                        content += f"Description:\n{result['description']}"
                    else:
                        content = f"❌ Error scraping video: {result.get('error', 'Unknown error')}"
                    
                    self.desktop_manager.update_preview_content(preview_id, content)
            
            # Update status
            window.state = AgentState.IDLE
            window.current_task = "Task completed"
            self.active_tasks[task_id]["status"] = "completed"
            
            # Send completion message
            self.desktop_manager.add_chat_message(
                window.id,
                "✅ YouTube task completed successfully!"
            )
            
        except Exception as e:
            window.state = AgentState.ERROR
            self.active_tasks[task_id]["status"] = "error"
            self.desktop_manager.add_chat_message(
                window.id,
                f"❌ YouTube task error: {str(e)}"
            )

class InterconnectedWorkspace:
    """Main workspace that interconnects everything"""
    
    def __init__(self):
        # Create managers
        self.stage_manager = StageManager(max_active_agents=6)
        self.desktop_manager = DesktopManager(stage_manager=self.stage_manager)
        self.task_orchestrator = TaskOrchestrator(self.stage_manager, self.desktop_manager)
        
        # Communication channels between all components
        self.message_bus = asyncio.Queue()
        self.shared_memory = {}
        
        # Register interconnections
        self._setup_interconnections()
        
    def _setup_interconnections(self):
        """Setup all interconnections between components"""
        
        # 1. Chat commands can control Stage Manager
        def handle_stage_command(message):
            if message.content.startswith("/stage"):
                parts = message.content.split()
                if len(parts) > 1:
                    if parts[1] == "arrange":
                        self.stage_manager.arrange_grid()
                    elif parts[1] == "cascade":
                        self.stage_manager.arrange_cascade()
                    elif parts[1] == "focus" and len(parts) > 2:
                        self.stage_manager.switch_to_agent(parts[2])
                        
        self.desktop_manager.register_message_handler("user", handle_stage_command)
        
        # 2. Agent updates flow to preview panes
        async def agent_to_preview_bridge():
            while True:
                # Check all active agents
                for agent_id, window in self.stage_manager.agent_windows.items():
                    if window.state == AgentState.WORKING:
                        # Find associated preview pane
                        for pane in self.desktop_manager.preview_panes.values():
                            if agent_id in pane.title:
                                # Update preview with agent status
                                status = f"[{window.name}]\nState: {window.state.value}\nTask: {window.current_task}"
                                self.desktop_manager.update_preview_content(pane.id, status)
                                
                await asyncio.sleep(1)
                
        # 3. All agents share memory
        def share_agent_memory(agent_id: str, memory_key: str, memory_value: any):
            """Share memory between all agents"""
            self.shared_memory[memory_key] = {
                "value": memory_value,
                "source": agent_id,
                "timestamp": datetime.now()
            }
            
            # Notify all other agents
            for other_id, other_agent in self.task_orchestrator.agent_pool.items():
                if other_id != agent_id:
                    # In real implementation, update agent's memory
                    pass
                    
        # 4. Terminal output goes to appropriate preview
        def route_terminal_output(source: str, output: str):
            """Route terminal output to correct preview pane"""
            # Find or create terminal preview
            terminal_panes = [p for p in self.desktop_manager.preview_panes.values() 
                            if p.preview_type == PreviewType.TERMINAL]
            
            if terminal_panes:
                pane = terminal_panes[0]
                current = pane.content or ""
                self.desktop_manager.update_preview_content(
                    pane.id,
                    current + f"\n[{source}] {output}"
                )

# Example usage showing the interconnected nature
async def demonstrate_interconnected_workspace():
    """Show how everything works together"""
    
    workspace = InterconnectedWorkspace()
    
    # Simulate user giving multiple tasks
    print("=== Interconnected Workspace Demo ===\n")
    
    # Task 1: Development task
    workspace.desktop_manager.add_chat_message(
        "user",
        "Create a Python web scraper for news articles"
    )
    
    await asyncio.sleep(1)
    
    # Task 2: Research task
    workspace.desktop_manager.add_chat_message(
        "user",
        "Research best practices for web scraping"
    )
    
    await asyncio.sleep(1)
    
    # Task 3: Testing task
    workspace.desktop_manager.add_chat_message(
        "user",
        "Test the web scraper on multiple sites"
    )
    
    # Show how to control stage
    workspace.desktop_manager.add_chat_message(
        "user",
        "/stage arrange grid"
    )
    
    # Let tasks run
    await asyncio.sleep(10)
    
    # Check status
    layout = workspace.stage_manager.get_stage_layout()
    print(f"\nActive Agents: {len(layout['active_stage'])}")
    for agent in layout['active_stage']:
        print(f"- {agent['name']}: {agent['state']}")

if __name__ == "__main__":
    # Run the demo
    asyncio.run(demonstrate_interconnected_workspace())