#!/usr/bin/env python3
"""
NEXUS 2.0 Interconnected Demo
Shows how Stage Manager + Desktop Manager work together
Just like Claude's multi-agent system but in your terminal!
"""

import os
import sys
from pathlib import Path

# Add core to path
sys.path.append(str(Path(__file__).parent / "core"))

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║          NEXUS 2.0 - Interconnected Workspace             ║
    ║                                                           ║
    ║  This is what you're launching:                           ║
    ║  • A TERMINAL UI (not web!)                               ║
    ║  • Multiple AI agents in windows (Stage Manager)          ║
    ║  • Chat interface to control them (Desktop Manager)       ║
    ║  • Everything interconnected and working together         ║
    ╚═══════════════════════════════════════════════════════════╝
    
    How it works:
    
    1. You type: "Build a web scraper"
       
    2. System creates agent windows:
       ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
       │ Developer   │ │ Researcher  │ │ Tester      │
       │ Agent       │ │ Agent       │ │ Agent       │
       │ [Working]   │ │ [Thinking]  │ │ [Idle]      │
       └─────────────┘ └─────────────┘ └─────────────┘
       
    3. All agents work simultaneously:
       • Developer writes code
       • Researcher finds best practices  
       • Tester prepares test cases
       
    4. You see everything in one terminal interface!
    
    Select what to launch:
    
    1. Full Integrated System (Stage + Desktop + Agents)
    2. Simple Demo (See agents in action)
    3. Task Orchestrator (How tasks create agents)
    4. Individual Managers (Explore components)
    
    """)
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == "1":
        print("\n🚀 Launching Full Integrated System...")
        print("This is the complete NEXUS 2.0 experience!\n")
        from nexus_integrated_workspace import NEXUSIntegratedWorkspace
        app = NEXUSIntegratedWorkspace()
        app.run()
        
    elif choice == "2":
        print("\n🎭 Running Simple Demo...")
        print("Watch how agents work together:\n")
        import asyncio
        from nexus_task_orchestrator import demonstrate_interconnected_workspace
        asyncio.run(demonstrate_interconnected_workspace())
        
    elif choice == "3":
        print("\n🔄 Launching Task Orchestrator...")
        print("See how your commands create agent windows:\n")
        from nexus_task_orchestrator import InterconnectedWorkspace
        workspace = InterconnectedWorkspace()
        print("Task Orchestrator initialized!")
        print("Try commands like:")
        print("- 'Create a Python web scraper'")
        print("- 'Analyze this code for bugs'")
        print("- 'Build a REST API'")
        
    elif choice == "4":
        print("\n🧩 Individual Components:")
        print("1. Stage Manager - Manage agent windows")
        print("2. Desktop Manager - Chat and preview")
        print("3. Autonomous Agent - Single agent demo")
        
        sub_choice = input("\nSelect component (1-3): ").strip()
        
        if sub_choice == "1":
            from nexus_stage_manager import StageManager
            print("\n📊 Stage Manager Demo")
            stage = StageManager()
            # Create some demo agents
            stage.create_agent_window("Developer", "developer")
            stage.create_agent_window("Researcher", "researcher")
            stage.create_agent_window("Tester", "tester")
            layout = stage.get_stage_layout()
            print(f"Created {len(layout['active_stage'])} agent windows")
            
        elif sub_choice == "2":
            from nexus_desktop_manager import DesktopManager
            print("\n💬 Desktop Manager Demo")
            desktop = DesktopManager()
            desktop.add_chat_message("user", "Hello NEXUS!")
            desktop.add_chat_message("system", "Welcome! I'm ready to help.")
            print("Chat system initialized")
            
        elif sub_choice == "3":
            from agent_base import AutonomousMANUS
            print("\n🤖 Autonomous Agent Demo")
            agent = AutonomousMANUS("Demo Agent")
            print(f"Created: {agent.name}")
            print(f"Capabilities: {agent.capabilities}")
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()