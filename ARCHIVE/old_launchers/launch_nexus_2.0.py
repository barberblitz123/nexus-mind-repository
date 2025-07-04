#!/usr/bin/env python3
"""
NEXUS 2.0 Quick Launcher
Simple script to launch NEXUS 2.0 after repository cleanup
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_requirements():
    """Check if required components are available"""
    checks = {
        "Node.js": "node --version",
        "npm": "npm --version",
        "Python": "python3 --version",
        "Git": "git --version"
    }
    
    print("Checking requirements...")
    for name, cmd in checks.items():
        try:
            subprocess.run(cmd.split(), capture_output=True, check=True)
            print(f"✓ {name} installed")
        except:
            print(f"✗ {name} not found - please install")
            return False
    return True

def find_nexus_web_app():
    """Find the nexus-web-app directory"""
    possible_paths = [
        Path("nexus-web-app"),
        Path("ACTIVE_NEXUS_2.0/web_apps/nexus-web-app"),
        Path("../nexus-web-app"),
        Path("./nexus-web-app")
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_dir():
            return path
    
    return None

def launch_nexus():
    """Launch NEXUS 2.0"""
    if not check_requirements():
        print("\nPlease install missing requirements first.")
        return
    
    # Find web app directory
    web_app_dir = find_nexus_web_app()
    if not web_app_dir:
        print("\n❌ Could not find nexus-web-app directory!")
        print("Please run from the repository root or after cleanup.")
        return
    
    print(f"\n✓ Found NEXUS web app at: {web_app_dir}")
    
    # Change to web app directory
    os.chdir(web_app_dir)
    
    # Check if node_modules exists
    if not Path("node_modules").exists():
        print("\nInstalling dependencies...")
        subprocess.run(["npm", "install"], check=True)
    
    # Kill any existing processes on our ports
    print("\nCleaning up old processes...")
    for port in [8080, 8000, 3000]:
        try:
            subprocess.run(f"lsof -ti:{port} | xargs kill -9", shell=True, capture_output=True)
        except:
            pass
    
    # Launch based on available scripts
    if Path("start-nexus-v5-complete.sh").exists():
        print("\n🚀 Launching NEXUS 2.0 (Full System)...")
        print("This will start:")
        print("- Web Interface on http://localhost:8080")
        print("- Python Backend on http://localhost:8000")
        print("- MCP Server on http://localhost:3000")
        subprocess.run(["bash", "start-nexus-v5-complete.sh"])
    elif Path("unified-nexus-server.js").exists():
        print("\n🚀 Launching NEXUS 2.0 (Web Only)...")
        print("Starting web interface on http://localhost:8080")
        subprocess.run(["npm", "start"])
    else:
        print("\n❌ Could not find launch scripts!")
        print("Available files:")
        subprocess.run(["ls", "-la"])

def main():
    print("=" * 60)
    print("NEXUS 2.0 Quick Launcher")
    print("=" * 60)
    
    # Check if cleanup has been done
    if Path("ACTIVE_NEXUS_2.0").exists() and Path("ARCHIVE").exists():
        print("\n✓ Repository has been cleaned up")
    else:
        print("\n⚠️  Repository cleanup not detected")
        print("Run 'python organize_nexus_repository.py' first for best results")
        response = input("\nContinue anyway? (yes/no): ")
        if response.lower() != 'yes':
            return
    
    launch_nexus()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✋ NEXUS 2.0 launcher stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nCheck SESSION_RECOVERY.md for troubleshooting")