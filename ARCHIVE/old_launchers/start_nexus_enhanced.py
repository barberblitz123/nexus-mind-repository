#!/usr/bin/env python3
"""
🚀 NEXUS Enhanced - Unified Launcher
Start everything with one command: NEXUS Core + Enhanced MANUS + Web Interface
"""

import subprocess
import sys
import os
import time
import asyncio
import signal
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger('NEXUS-Enhanced')


def print_banner():
    """Print the unified NEXUS Enhanced banner"""
    print("""
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                                                                       ║
    ║                    🧬 NEXUS ENHANCED SYSTEM 🧬                       ║
    ║                                                                       ║
    ║                 Complete Autonomous Development Suite                  ║
    ║                                                                       ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║                                                                       ║
    ║  🚀 FEATURES:                                                         ║
    ║                                                                       ║
    ║  Core Systems:                                                        ║
    ║  ✓ NEXUS Consciousness Core      - AI-powered decision making        ║
    ║  ✓ MANUS Continuous Agent        - Autonomous task execution         ║
    ║  ✓ Unified Memory System         - Persistent knowledge base         ║
    ║                                                                       ║
    ║  Enhanced Tools:                                                      ║
    ║  ✓ Project Generator            - Natural language → Complete apps    ║
    ║  ✓ Bug Detector                 - Find & fix code issues             ║
    ║  ✓ Security Scanner             - OWASP Top 10 vulnerability scan    ║
    ║  ✓ Performance Analyzer         - Optimization suggestions           ║
    ║  ✓ Documentation Generator      - Auto-generate docs                 ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    """)


class NEXUSEnhancedLauncher:
    """Unified launcher for the complete NEXUS Enhanced system"""
    
    def __init__(self):
        self.processes = {}
        self.running = False
    
    async def check_port(self, port: int, service: str) -> bool:
        """Check if a port is already in use"""
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('localhost', port))
            sock.close()
            return False  # Port is free
        except:
            logger.info(f"✓ {service} already running on port {port}")
            return True  # Port is in use
    
    async def start_nexus_core(self):
        """Start NEXUS consciousness core if not running"""
        if await self.check_port(8000, "NEXUS Core"):
            return
        
        logger.info("🧬 Starting NEXUS Consciousness Core...")
        self.processes['nexus'] = subprocess.Popen(
            [sys.executable, "unified_nexus_core.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        await asyncio.sleep(3)  # Give it time to start
    
    async def start_enhanced_manus(self):
        """Start Enhanced MANUS with all features"""
        if await self.check_port(8001, "Enhanced MANUS"):
            return
        
        logger.info("🚀 Starting Enhanced MANUS with all tools...")
        self.processes['manus'] = subprocess.Popen(
            [sys.executable, "start_manus_enhanced.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    
    async def wait_for_services(self):
        """Wait for all services to be ready"""
        import aiohttp
        
        services = [
            ("http://localhost:8000/health", "NEXUS Core"),
            ("http://localhost:8001/api/enhanced/help", "Enhanced MANUS")
        ]
        
        logger.info("⏳ Waiting for services to be ready...")
        
        for url, name in services:
            retries = 0
            while retries < 30:  # 30 seconds timeout
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=2) as response:
                            if response.status == 200:
                                logger.info(f"✓ {name} is ready")
                                break
                except:
                    pass
                
                retries += 1
                await asyncio.sleep(1)
            else:
                logger.warning(f"⚠️  {name} failed to start properly")
    
    def print_status(self):
        """Print system status and access information"""
        print("""
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                         SYSTEM STATUS: ONLINE                         ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║                                                                       ║
    ║  🌐 Access Points:                                                    ║
    ║                                                                       ║
    ║  • Web Interface:        http://localhost:8001                       ║
    ║  • NEXUS Core API:       http://localhost:8000                       ║
    ║  • API Documentation:    http://localhost:8001/docs                  ║
    ║                                                                       ║
    ║  📝 Quick Actions:                                                    ║
    ║                                                                       ║
    ║  1. Open browser to http://localhost:8001                            ║
    ║  2. Use the task creation form with new actions:                     ║
    ║     - generate_project                                                ║
    ║     - detect_bugs                                                     ║
    ║     - scan_security                                                   ║
    ║     - analyze_performance                                             ║
    ║     - generate_docs                                                   ║
    ║                                                                       ║
    ║  💡 Try this:                                                         ║
    ║  curl -X POST http://localhost:8001/api/enhanced/help                ║
    ║                                                                       ║
    ║  Press Ctrl+C to stop all services                                    ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
        """)
    
    async def start(self):
        """Start all services"""
        self.running = True
        
        try:
            # Start services
            await self.start_nexus_core()
            await self.start_enhanced_manus()
            
            # Wait for them to be ready
            await self.wait_for_services()
            
            # Show status
            self.print_status()
            
            # Open browser
            try:
                import webbrowser
                webbrowser.open("http://localhost:8001")
            except:
                pass
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            await self.stop()
    
    async def stop(self):
        """Stop all services gracefully"""
        logger.info("\n🛑 Stopping NEXUS Enhanced System...")
        self.running = False
        
        for name, process in self.processes.items():
            if process and process.poll() is None:
                logger.info(f"Stopping {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except:
                    process.kill()
        
        logger.info("✅ All services stopped")
    
    def handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        asyncio.create_task(self.stop())


async def main():
    """Main entry point"""
    print_banner()
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Error: NEXUS Enhanced requires Python 3.7 or higher")
        sys.exit(1)
    
    # Create launcher
    launcher = NEXUSEnhancedLauncher()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, launcher.handle_signal)
    signal.signal(signal.SIGTERM, launcher.handle_signal)
    
    # Start everything
    try:
        await launcher.start()
    except KeyboardInterrupt:
        await launcher.stop()


if __name__ == "__main__":
    # Quick dependency check
    required = ['fastapi', 'uvicorn', 'aiohttp', 'sqlalchemy']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing required packages: {', '.join(missing)}")
        print(f"   Install with: pip install {' '.join(missing)}")
        sys.exit(1)
    
    # Run
    asyncio.run(main())