#!/usr/bin/env python3
"""
LAUNCH REAL NEXUS 2.0

This launches the ACTUAL autonomous agent system with:
- Real code execution
- File operations
- Comprehensive logging
- Easy log extraction
- Auditing capabilities
"""

import os
import sys
import asyncio
import subprocess
import signal
from datetime import datetime
from pathlib import Path

# Add paths for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'interfaces'))

# Import our components
from core.nexus_logger import get_logger
from interfaces.nexus_connector import get_connector


def print_banner():
    """Print NEXUS startup banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                         NEXUS 2.0 AGENT                           ║
    ║                    REAL Autonomous Execution                      ║
    ╚═══════════════════════════════════════════════════════════════════╝
    
    🚀 Starting REAL agent system with:
       ✅ Actual code execution (not simulation)
       ✅ Real file operations
       ✅ Comprehensive logging system
       ✅ Easy log extraction
       ✅ Full auditing capabilities
       ✅ Agent memory and learning
    """
    print(banner)


def setup_signal_handlers(logger):
    """Setup graceful shutdown handlers"""
    def signal_handler(sig, frame):
        print("\n\n📊 Saving session logs...")
        logger.save_session_log()
        print(f"✅ Logs saved to: {logger.log_dir}")
        print("\n👋 NEXUS shutdown complete")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def launch_terminal_interface():
    """Launch the terminal-based interface"""
    print("\n🖥️  Launching Terminal Interface...")
    
    # Launch the tabbed interface
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "core/nexus_tabbed_interface.py",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    return process


async def launch_web_interface():
    """Launch the web interface with real connector"""
    print("\n🌐 Launching Web Interface...")
    
    # Launch WebSocket server (Python)
    websocket_process = await asyncio.create_subprocess_exec(
        sys.executable,
        "interfaces/nexus_websocket_server.py",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Launch web server (Node.js) on port 8000
    web_server_process = await asyncio.create_subprocess_exec(
        "node",
        "web_version/stage_desktop_server.js",
        env={**os.environ, "PORT": "8000"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    return [websocket_process, web_server_process]


async def monitor_system(logger, connector):
    """Monitor system health and performance"""
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds
        
        # Get metrics
        metrics = await connector.get_system_metrics()
        
        # Log system status
        logger.log_system_event("System Health Check", {
            "agents_active": metrics['agents']['active'],
            "tasks_completed": metrics['agents']['total_tasks_completed'],
            "errors": metrics['total_errors']
        })
        
        # Auto-save if many activities
        if len(logger.activity_log) > 1000:
            logger.save_session_log()
            logger.info("Auto-saved session log due to high activity")


def show_commands():
    """Show available commands"""
    print("""
    📋 Available Commands:
    
    1. In Terminal UI:
       - Tab between sections with Tab key
       - Type in chat to create agents
       - View logs in Debug tab
    
    2. In Web UI:
       - Open http://localhost:8000 in browser
       - Chat creates real agents
       - Agents execute actual code
    
    3. Log Management:
       - Logs auto-saved to: nexus_logs/
       - Press Ctrl+C for graceful shutdown
       - Session logs exported on exit
    
    4. Quick Commands:
       - "create agent to analyze code" - Creates analyst agent
       - "create agent to build API" - Creates developer agent
       - "create agent for deployment" - Creates DevOps agent
    """)


async def main():
    """Main entry point"""
    print_banner()
    
    # Initialize logger
    logger = get_logger()
    logger.info("NEXUS 2.0 Starting - REAL Execution Mode", audit=True)
    
    # Initialize connector
    connector = get_connector()
    
    # Setup signal handlers
    setup_signal_handlers(logger)
    
    # Get launch mode from user
    print("\n🎯 Select Launch Mode:")
    print("   1. Terminal Interface Only")
    print("   2. Web Interface Only")
    print("   3. Both Terminal + Web (Recommended)")
    print("   4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    processes = []
    
    try:
        if choice == '1':
            # Terminal only
            term_process = await launch_terminal_interface()
            processes.append(term_process)
            
        elif choice == '2':
            # Web only
            web_processes = await launch_web_interface()
            processes.extend(web_processes)
            print("\n✅ Web interface started!")
            print("🌐 Open http://localhost:8000 in your browser")
            
        elif choice == '3':
            # Both
            term_process = await launch_terminal_interface()
            web_processes = await launch_web_interface()
            processes.extend([term_process] + web_processes)
            print("\n✅ Both interfaces started!")
            print("🖥️  Terminal UI is running")
            print("🌐 Open http://localhost:8000 for web UI")
            
        elif choice == '4':
            print("👋 Exiting...")
            return
            
        else:
            print("❌ Invalid choice")
            return
        
        # Show commands
        show_commands()
        
        # Start monitoring
        monitor_task = asyncio.create_task(monitor_system(logger, connector))
        
        print("\n🚀 NEXUS 2.0 is running with REAL agent execution!")
        print("📊 Logs are being saved to: nexus_logs/")
        print("⌨️  Press Ctrl+C to stop and export logs\n")
        
        # Wait for processes
        if processes:
            await asyncio.gather(*[p.wait() for p in processes])
        else:
            # Just run monitoring
            await monitor_task
            
    except KeyboardInterrupt:
        print("\n⚠️  Shutdown requested...")
    finally:
        # Kill any running processes
        for p in processes:
            if p.returncode is None:
                p.terminate()
                await p.wait()
        
        # Save final logs
        logger.save_session_log()
        print(f"\n✅ Final logs saved to: {logger.log_dir}")
        print("\n📊 Session Summary:")
        metrics = await connector.get_system_metrics()
        print(f"   Total Tasks Completed: {metrics['agents']['total_tasks_completed']}")
        print(f"   Total Errors: {metrics['total_errors']}")
        print(f"   Log Files: {list(logger.log_dir.glob('*.log'))}")


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required")
        sys.exit(1)
    
    # Run the launcher
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)