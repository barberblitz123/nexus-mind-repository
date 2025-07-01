#!/usr/bin/env python3
"""
Quick launcher for the NEXUS Demo
Run this to see the impressive 5-minute showcase!
"""

import subprocess
import sys
import os

def check_requirements():
    """Ensure all required packages are installed"""
    required_packages = ['rich', 'pillow']
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def main():
    """Launch the demo with proper environment setup"""
    # Clear screen
    os.system('clear' if os.name == 'posix' else 'cls')
    
    # Check requirements
    check_requirements()
    
    # Run the demo
    print("\n🚀 Launching NEXUS Demo Project...\n")
    subprocess.run([sys.executable, "nexus_demo_project.py"])

if __name__ == "__main__":
    main()