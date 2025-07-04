#!/usr/bin/env python3
'''
Launch NEXUS/MANUS Web Application
'''

import subprocess
import sys
import time
import webbrowser

print("🚀 Launching NEXUS/MANUS Web Application...")
print("=" * 50)

# Check if NEXUS core is needed
try:
    import requests
    response = requests.get('http://localhost:8000/health', timeout=2)
    print("✅ NEXUS core is already running")
except:
    print("⚠️  NEXUS core not running - MANUS will work with limited features")
    print("   To enable full features, run: python unified_nexus_core.py")

print("\n📡 Starting MANUS Enhanced Web Interface...")
print("   Web UI will be available at: http://localhost:8001")
print("   Press Ctrl+C to stop\n")

# Start the enhanced MANUS
try:
    subprocess.run([sys.executable, "start_manus_enhanced.py"])
except KeyboardInterrupt:
    print("\n👋 Shutting down NEXUS/MANUS...")
