#!/usr/bin/env python3
"""
NEXUS 2.0 Simple Demo - Without repetition issues
Shows Stage Manager + Desktop Manager concept clearly
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List

class SimpleStageManager:
    """Simplified Stage Manager for demo"""
    def __init__(self):
        self.agents = {}
        self.active_agents = []
        
    def create_agent(self, task: str) -> str:
        """Create a single agent for a task"""
        agent_id = str(uuid.uuid4())[:8]
        agent_type = self._determine_type(task)
        
        self.agents[agent_id] = {
            "id": agent_id,
            "type": agent_type,
            "task": task,
            "state": "working",
            "created": datetime.now()
        }
        
        self.active_agents.append(agent_id)
        return agent_id
        
    def _determine_type(self, task: str) -> str:
        """Determine agent type from task"""
        task_lower = task.lower()
        if "analyze" in task_lower:
            return "Analyzer"
        elif "build" in task_lower or "create" in task_lower:
            return "Developer"
        elif "test" in task_lower:
            return "Tester"
        elif "document" in task_lower:
            return "Documenter"
        else:
            return "General"
            
    def get_display(self) -> str:
        """Get visual display of agents"""
        display = "\n╔══════════ STAGE MANAGER ══════════╗\n"
        
        if not self.active_agents:
            display += "║  No active agents                 ║\n"
        else:
            for agent_id in self.active_agents[:4]:  # Show max 4
                agent = self.agents[agent_id]
                display += f"║ [{agent['type']}] {agent['state']:<8} ║\n"
                display += f"║  Task: {agent['task'][:25]:<25} ║\n"
                display += "║" + "─" * 35 + "║\n"
                
        display += "╚═══════════════════════════════════╝"
        return display

class SimpleDesktopManager:
    """Simplified Desktop Manager for demo"""
    def __init__(self):
        self.chat_history = []
        self.preview_content = "Ready for output..."
        
    def add_message(self, sender: str, message: str):
        """Add a single message to chat"""
        self.chat_history.append({
            "sender": sender,
            "message": message,
            "time": datetime.now().strftime("%H:%M:%S")
        })
        
    def update_preview(self, content: str):
        """Update preview pane"""
        self.preview_content = content
        
    def get_chat_display(self) -> str:
        """Get chat display"""
        display = "\n╔════════════ CHAT ═════════════╗\n"
        
        # Show last 5 messages
        recent = self.chat_history[-5:] if self.chat_history else []
        
        for msg in recent:
            sender = msg['sender'][:4].upper()
            text = msg['message'][:25]
            display += f"║ {sender}: {text:<25} ║\n"
            
        display += "╚═══════════════════════════════╝"
        return display
        
    def get_preview_display(self) -> str:
        """Get preview display"""
        display = "\n╔══════════ PREVIEW ════════════╗\n"
        
        lines = self.preview_content.split('\n')[:5]
        for line in lines:
            display += f"║ {line[:30]:<30} ║\n"
            
        display += "╚═══════════════════════════════╝"
        return display

class SimpleNexusDemo:
    """Simple demo without repetition issues"""
    def __init__(self):
        self.stage = SimpleStageManager()
        self.desktop = SimpleDesktopManager()
        self.running = True
        
    def process_command(self, command: str):
        """Process a single command - NO REPETITION"""
        # Add user message ONCE
        self.desktop.add_message("You", command)
        
        # Create ONE agent
        agent_id = self.stage.create_agent(command)
        agent = self.stage.agents[agent_id]
        
        # Agent responds ONCE
        self.desktop.add_message(
            agent['type'], 
            f"Starting: {command}"
        )
        
        # Update preview ONCE
        self.desktop.update_preview(
            f"Working on: {command}\n" +
            f"Agent Type: {agent['type']}\n" +
            f"Status: In Progress..."
        )
        
    def display(self):
        """Show the current state"""
        print("\033[H\033[J")  # Clear screen
        print("=" * 50)
        print("   NEXUS 2.0 - Simple Demo (No Repetition)")
        print("=" * 50)
        
        # Show stage manager
        print(self.stage.get_display())
        
        # Show chat and preview side by side
        chat = self.desktop.get_chat_display().split('\n')
        preview = self.desktop.get_preview_display().split('\n')
        
        for i in range(max(len(chat), len(preview))):
            chat_line = chat[i] if i < len(chat) else " " * 35
            preview_line = preview[i] if i < len(preview) else ""
            print(f"{chat_line}  {preview_line}")
            
        print("\n" + "=" * 50)
        
    async def run(self):
        """Run the demo"""
        print("NEXUS 2.0 Simple Demo")
        print("Type commands like: 'analyze my code', 'build api', 'test system'")
        print("Type 'quit' to exit\n")
        
        while self.running:
            # Display current state
            self.display()
            
            # Get command
            command = input("\n> ").strip()
            
            if command.lower() == 'quit':
                self.running = False
                break
                
            if command:
                # Process command ONCE - no repetition!
                self.process_command(command)
                
                # Simulate agent work
                await asyncio.sleep(1)
                
                # Update agent state
                for agent_id in self.stage.active_agents:
                    self.stage.agents[agent_id]['state'] = 'completed'
                    
        print("\nGoodbye!")

def main():
    """Run the simple demo"""
    demo = SimpleNexusDemo()
    asyncio.run(demo.run())

if __name__ == "__main__":
    main()