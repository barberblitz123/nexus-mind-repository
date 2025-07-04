#!/usr/bin/env python3
"""
NEXUS 2.0 Full Agent System Launcher
The REAL NEXUS 2.0 - Terminal-based autonomous development environment
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_dependencies():
    """Check and install required dependencies"""
    print("🔍 Checking dependencies for NEXUS 2.0 Agent System...")
    
    required_packages = [
        "textual",
        "rich", 
        "psutil",
        "aiofiles",
        "asyncio",
        "requests",
        "flask",
        "flask-cors",
        "flask-socketio"
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} installed")
        except ImportError:
            print(f"📦 Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)

def launch_nexus_agent_system():
    """Launch the full NEXUS 2.0 autonomous agent system"""
    print("\n" + "="*60)
    print("🚀 NEXUS 2.0 FULL AGENT SYSTEM")
    print("="*60)
    print("\nThis is the REAL NEXUS 2.0:")
    print("✓ Terminal-based development environment")
    print("✓ Autonomous agent capabilities") 
    print("✓ Multiple integrated terminals")
    print("✓ Full IDE-like interface")
    print("✓ NOT just a web chat interface!")
    print("="*60 + "\n")
    
    # Check dependencies
    check_dependencies()
    
    # Choose which component to launch
    print("\n🎯 Select NEXUS 2.0 Component to Launch:")
    print("1. Terminal UI Advanced (VS Code-like interface)")
    print("2. Terminal UI Production (Modular tab system)")
    print("3. Autonomous Agent (Self-directed MANUS)")
    print("4. Agent Orchestrator (Multi-agent system)")
    print("5. Full System (All components)")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        print("\n🖥️  Launching NEXUS Terminal UI Advanced...")
        print("This provides a full VS Code-like experience in the terminal")
        # Fix the import issue first
        fix_terminal_ui()
        subprocess.run([sys.executable, "nexus_terminal_ui_advanced.py"])
        
    elif choice == "2":
        print("\n🖥️  Launching NEXUS Terminal UI Production...")
        subprocess.run([sys.executable, "nexus_terminal_ui_production.py"])
        
    elif choice == "3":
        print("\n🤖 Launching Autonomous MANUS Agent...")
        subprocess.run([sys.executable, "nexus_autonomous_agent.py"])
        
    elif choice == "4":
        print("\n🎭 Launching Agent Orchestrator...")
        subprocess.run([sys.executable, "nexus_agent_orchestrator_advanced.py"])
        
    elif choice == "5":
        print("\n🌐 Launching Full NEXUS 2.0 System...")
        launch_full_system()
        
    else:
        print("❌ Invalid choice")

def fix_terminal_ui():
    """Fix import issues in terminal UI"""
    print("🔧 Fixing terminal UI compatibility...")
    
    # Read the file
    with open("nexus_terminal_ui_advanced.py", "r") as f:
        content = f.read()
    
    # Fix the TextLog import (renamed in newer Textual versions)
    content = content.replace("from textual.widgets import (", 
                            "from textual.widgets import (")
    content = content.replace("TextLog,", "RichLog as TextLog,")
    
    # Write it back
    with open("nexus_terminal_ui_advanced.py", "w") as f:
        f.write(content)
    
    print("✓ Terminal UI fixed")

def launch_full_system():
    """Launch all NEXUS 2.0 components"""
    processes = []
    
    try:
        # 1. Start the terminal UI
        print("🖥️  Starting Terminal UI...")
        fix_terminal_ui()
        terminal_proc = subprocess.Popen([sys.executable, "nexus_terminal_ui_advanced.py"])
        processes.append(terminal_proc)
        time.sleep(2)
        
        # 2. Start the autonomous agent
        print("🤖 Starting Autonomous Agent...")
        agent_proc = subprocess.Popen([sys.executable, "nexus_autonomous_agent.py"])
        processes.append(agent_proc)
        time.sleep(2)
        
        # 3. Start the orchestrator
        print("🎭 Starting Agent Orchestrator...")
        orch_proc = subprocess.Popen([sys.executable, "nexus_agent_orchestrator_advanced.py"])
        processes.append(orch_proc)
        
        print("\n✅ NEXUS 2.0 Full Agent System is running!")
        print("Press Ctrl+C to stop all components")
        
        # Wait for interrupt
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down NEXUS 2.0...")
        for proc in processes:
            proc.terminate()
        for proc in processes:
            proc.wait()
        print("✅ NEXUS 2.0 shut down complete")

if __name__ == "__main__":
    print("""
    ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗    ██████╗    ██████╗ 
    ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝    ╚════██╗  ██╔═████╗
    ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗     █████╔╝  ██║██╔██║
    ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║    ██╔═══╝   ████╔╝██║
    ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║    ███████╗██╗╚██████╔╝
    ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝    ╚══════╝╚═╝ ╚═════╝ 
    
    The REAL Autonomous Agent System - Not Just Another Chat Bot!
    """)
    
    launch_nexus_agent_system()