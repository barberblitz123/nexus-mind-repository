#!/usr/bin/env python3
"""
Test the integrated tabbed interface with debug logging
"""

import sys
import os

# Add the core directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work"""
    try:
        from nexus_tabbed_interface import NEXUSTabbedInterface
        from nexus_logger import get_logger
        from nexus_debug_tab import DebugTab
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_logger():
    """Test logger functionality"""
    try:
        from nexus_logger import get_logger
        logger = get_logger("TEST")
        
        # Test different log levels
        logger.debug("Debug test message")
        logger.info("Info test message")
        logger.warning("Warning test message")
        logger.error("Error test message")
        
        # Test special logging
        logger.log_command("test command", "test")
        logger.log_system_event("Test event", {"detail": "test"})
        logger.log_agent_activity("test-agent", "Test activity", {"data": "test"})
        
        print("✅ Logger tests passed")
        return True
    except Exception as e:
        print(f"❌ Logger test failed: {e}")
        return False

def main():
    """Run tests"""
    print("Testing NEXUS 2.0 Debug Integration...")
    print("-" * 50)
    
    if not test_imports():
        print("\nFix import errors before proceeding")
        return 1
        
    if not test_logger():
        print("\nLogger tests failed")
        return 1
        
    print("\n✅ All tests passed!")
    print("\nTo run the full application:")
    print("  python nexus_tabbed_interface.py")
    print("\nDebug features:")
    print("  - Press Ctrl+6 to switch to Debug tab")
    print("  - View live log stream")
    print("  - Monitor agent activity")
    print("  - Track errors")
    print("  - Execute debug commands")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())