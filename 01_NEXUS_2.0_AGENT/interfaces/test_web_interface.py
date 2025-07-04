#!/usr/bin/env python3
"""
Quick test to verify the web interface components are working
"""

import os
import sys
from pathlib import Path

def test_files_exist():
    """Check if all required files exist"""
    required_files = [
        "nexus_tabbed_web.html",
        "nexus_tabbed_web.js", 
        "nexus_websocket_server.py",
        "launch_web_interface.sh",
        "WEB_INTERFACE_README.md"
    ]
    
    print("🧬 NEXUS 2.0 Web Interface Test")
    print("=" * 40)
    print("\n📁 Checking required files...")
    
    all_good = True
    for file in required_files:
        path = Path(file)
        if path.exists():
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} MISSING!")
            all_good = False
    
    return all_good

def test_imports():
    """Test if Python imports work"""
    print("\n📦 Testing Python imports...")
    
    try:
        # Add parent directory to path
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from core.nexus_stage_manager import StageManager
        print("  ✓ StageManager imported")
        
        from core.nexus_desktop_manager import DesktopManager
        print("  ✓ DesktopManager imported")
        
        from core.nexus_task_orchestrator import NEXUSTaskOrchestrator
        print("  ✓ TaskOrchestrator imported")
        
        return True
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False

def test_websocket():
    """Test if websockets module is available"""
    print("\n🔌 Testing WebSocket support...")
    
    try:
        import websockets
        print("  ✓ websockets module available")
        return True
    except ImportError:
        print("  ✗ websockets module not found")
        print("    Run: pip install websockets")
        return False

def main():
    """Run all tests"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    tests = [
        test_files_exist(),
        test_imports(),
        test_websocket()
    ]
    
    if all(tests):
        print("\n✅ All tests passed! Web interface is ready to launch.")
        print("\nTo start the web interface:")
        print("  ./launch_web_interface.sh")
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())