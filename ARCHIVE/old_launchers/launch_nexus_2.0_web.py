#!/usr/bin/env python3
"""
Launch NEXUS 2.0 with Web Interface
This ensures we're using the correct NEXUS 2.0 components, NOT the old interfaces
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def check_requirements():
    """Check if required files exist"""
    required_files = [
        "nexus_core_production.py",
        "nexus_webinar_interface.py",
        "nexus_config_production.py",
        "nexus_database_production.py"
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print("ERROR: Missing required NEXUS 2.0 files:")
        for file in missing:
            print(f"  - {file}")
        return False
    return True

def launch_nexus_2_0():
    """Launch NEXUS 2.0 with production web interface"""
    
    print("=" * 60)
    print("NEXUS 2.0 WEB LAUNCHER")
    print("Using NEXUS 2.0 production components ONLY")
    print("=" * 60)
    
    # Check requirements
    if not check_requirements():
        print("\nPlease ensure all NEXUS 2.0 files are present.")
        return
    
    try:
        # Step 1: Launch NEXUS 2.0 Core
        print("\n1. Starting NEXUS 2.0 Core Production System...")
        core_process = subprocess.Popen(
            [sys.executable, "nexus_core_production.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give core time to initialize
        print("   Waiting for core to initialize...")
        time.sleep(3)
        
        # Step 2: Launch NEXUS 2.0 Web Interface
        print("\n2. Starting NEXUS 2.0 Web Interface...")
        print("   This is the production-grade FastAPI interface")
        print("   NOT the old consciousness simulation interfaces")
        
        web_process = subprocess.Popen(
            [sys.executable, "nexus_webinar_interface.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("\n" + "=" * 60)
        print("NEXUS 2.0 is starting up!")
        print("\nWeb Interface will be available at:")
        print("  http://localhost:8000")
        print("\nFeatures:")
        print("  - WebSocket real-time communication")
        print("  - Service health monitoring")
        print("  - Distributed transaction support")
        print("  - Redis state management")
        print("  - Prometheus metrics")
        print("\nPress Ctrl+C to stop all services")
        print("=" * 60)
        
        # Keep running and handle shutdown
        try:
            web_process.wait()
        except KeyboardInterrupt:
            print("\n\nShutting down NEXUS 2.0...")
            core_process.terminate()
            web_process.terminate()
            print("NEXUS 2.0 stopped.")
            
    except Exception as e:
        print(f"\nError launching NEXUS 2.0: {e}")
        print("Please check that all dependencies are installed:")
        print("  pip install -r requirements.txt")

if __name__ == "__main__":
    # Set environment for NEXUS 2.0
    os.environ["NEXUS_VERSION"] = "2.0"
    os.environ["NEXUS_MODE"] = "production"
    
    launch_nexus_2_0()