#!/usr/bin/env python3
"""
Basic MANUS startup without enhanced features
"""

import asyncio
import sys
import uvicorn
from manus_continuous_agent import MANUSContinuousAgent

# Remove the enhanced manus import from web interface
import manus_web_interface
manus_web_interface.enhanced_manus = None

# Start basic MANUS
async def main():
    print("🚀 Starting Basic MANUS...")
    print("   Web Interface: http://localhost:8001")
    print("   Note: Enhanced features are disabled")
    print("   Press Ctrl+C to stop")
    
    # Create basic MANUS agent
    manus_agent = MANUSContinuousAgent()
    manus_web_interface.manus_agent = manus_agent
    
    # Start agent
    agent_task = asyncio.create_task(manus_agent.start())
    
    # Start web server
    config = uvicorn.Config(
        manus_web_interface.app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
    server = uvicorn.Server(config)
    web_task = asyncio.create_task(server.serve())
    
    # Wait for both
    await asyncio.gather(agent_task, web_task)

if __name__ == "__main__":
    asyncio.run(main())