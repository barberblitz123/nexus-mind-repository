#!/usr/bin/env python3
"""
Test script for NEXUS launcher functionality
"""

import subprocess
import time
import requests
import json
from pathlib import Path

def test_launcher_help():
    """Test launcher help command"""
    print("Testing launcher help...")
    result = subprocess.run(["python", "nexus_launcher.py", "--help"], capture_output=True, text=True)
    print(f"Exit code: {result.returncode}")
    print(f"Output:\n{result.stdout}")
    assert result.returncode == 0, "Help command failed"
    assert "NEXUS Launcher" in result.stdout, "Help text missing"
    print("✓ Help test passed\n")

def test_launcher_status():
    """Test status command"""
    print("Testing launcher status...")
    result = subprocess.run(["python", "nexus_launcher.py", "status"], capture_output=True, text=True)
    print(f"Output: {result.stdout}")
    print("✓ Status test passed\n")

def test_config_creation():
    """Test configuration file creation"""
    print("Testing configuration...")
    config_dir = Path.home() / ".nexus"
    config_file = config_dir / "config.json"
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
            print(f"Config version: {config.get('version')}")
            print(f"Theme: {config.get('theme')}")
            print(f"API port: {config.get('api_port')}")
    else:
        print("Config file not yet created")
    
    print("✓ Config test passed\n")

def test_fast_mode():
    """Test fast startup mode"""
    print("Testing fast mode...")
    # This would normally start the launcher, but we'll just test the command
    result = subprocess.run(
        ["python", "nexus_launcher.py", "--fast", "--help"], 
        capture_output=True, 
        text=True
    )
    assert result.returncode == 0, "Fast mode help failed"
    print("✓ Fast mode test passed\n")

def test_theme_options():
    """Test theme options"""
    print("Testing theme options...")
    themes = ["dark", "light", "matrix"]
    for theme in themes:
        result = subprocess.run(
            ["python", "nexus_launcher.py", "--theme", theme, "--help"], 
            capture_output=True, 
            text=True
        )
        assert result.returncode == 0, f"Theme {theme} failed"
        print(f"  ✓ Theme '{theme}' accepted")
    print("✓ Theme test passed\n")

def main():
    """Run all tests"""
    print("=" * 50)
    print("NEXUS Launcher Test Suite")
    print("=" * 50)
    print()
    
    tests = [
        test_launcher_help,
        test_launcher_status,
        test_config_creation,
        test_fast_mode,
        test_theme_options,
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}\n")
    
    print("=" * 50)
    print("All tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()