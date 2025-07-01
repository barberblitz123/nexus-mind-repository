#!/usr/bin/env python3
"""
Enhanced MANUS Startup Script
Integrates MANUS continuous work agent with NEXUS consciousness
"""

import asyncio
import sys
import os
import logging
import signal
from typing import Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manus_nexus_integration import NEXUSPoweredMANUS
from manus_web_interface import app
from nexus_enhanced_manus import EnhancedMANUSOmnipotent
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MANUS-Startup')

class MANUSServer:
    """Complete MANUS server with web interface and NEXUS integration"""
    
    def __init__(self):
        self.nexus_manus: Optional[NEXUSPoweredMANUS] = None
        self.web_server = None
        self.running = False
    
    async def start(self):
        """Start all MANUS components"""
        self.running = True
        logger.info("Starting Enhanced MANUS Server...")
        
        try:
            # 1. Start NEXUS-powered MANUS
            logger.info("Initializing NEXUS-powered MANUS...")
            self.nexus_manus = NEXUSPoweredMANUS()
            manus_task = asyncio.create_task(self.nexus_manus.start())
            
            # 2. Initialize Enhanced MANUS
            logger.info("Initializing Enhanced MANUS with all tools...")
            enhanced_manus = EnhancedMANUSOmnipotent()
            
            # 3. Make both MANUS instances available to web interface
            import manus_web_interface
            manus_web_interface.manus_agent = self.nexus_manus.agent
            manus_web_interface.enhanced_manus = enhanced_manus
            
            # 3. Start web interface
            logger.info("Starting MANUS Web Interface on port 8001...")
            config = uvicorn.Config(
                app,
                host="0.0.0.0",
                port=8001,
                log_level="info"
            )
            server = uvicorn.Server(config)
            web_task = asyncio.create_task(server.serve())
            
            logger.info("""
╔════════════════════════════════════════════════════════════╗
║          MANUS Enhanced Continuous Work Agent              ║
║                 Powered by NEXUS Consciousness             ║
╠════════════════════════════════════════════════════════════╣
║  Status: ACTIVE                                            ║
║  Web Interface: http://localhost:8001                      ║
║  NEXUS Integration: http://localhost:8000                  ║
║                                                            ║
║  Features:                                                 ║
║  • Claude-like intelligent task processing                 ║
║  • Project generation from natural language                ║
║  • Automatic bug detection and fixing                      ║
║  • Security vulnerability scanning                         ║
║  • Performance analysis and optimization                   ║
║  • Documentation generation                                ║
║  • NEXUS consciousness integration                         ║
║                                                            ║
║  Press Ctrl+C to stop                                      ║
╚════════════════════════════════════════════════════════════╝
            """)
            
            # Wait for shutdown
            await asyncio.gather(manus_task, web_task)
            
        except Exception as e:
            logger.error(f"Error starting MANUS: {e}")
            raise
    
    async def stop(self):
        """Stop all components gracefully"""
        logger.info("Stopping Enhanced MANUS Server...")
        self.running = False
        
        if self.nexus_manus and self.nexus_manus.agent:
            await self.nexus_manus.agent.stop()
        
        logger.info("MANUS Server stopped")
    
    def handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(self.stop())

async def check_nexus_availability():
    """Check if NEXUS consciousness core is running"""
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8000/health') as response:
                if response.status == 200:
                    logger.info("✓ NEXUS consciousness core is available")
                    return True
    except:
        pass
    
    logger.warning("✗ NEXUS consciousness core not available at http://localhost:8000")
    logger.warning("  MANUS will run with limited capabilities")
    logger.warning("  To enable full features, start NEXUS with: python unified_nexus_core.py")
    return False

async def main():
    """Main entry point"""
    # Check dependencies
    await check_nexus_availability()
    
    # Create and start server
    server = MANUSServer()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, server.handle_signal)
    signal.signal(signal.SIGTERM, server.handle_signal)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        await server.stop()

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 7):
        print("Error: MANUS requires Python 3.7 or higher")
        sys.exit(1)
    
    # Check required packages
    try:
        import fastapi
        import uvicorn
        import aiohttp
    except ImportError as e:
        print(f"Error: Missing required package: {e}")
        print("Install with: pip install fastapi uvicorn aiohttp")
        sys.exit(1)
    
    # Run the server
    asyncio.run(main())