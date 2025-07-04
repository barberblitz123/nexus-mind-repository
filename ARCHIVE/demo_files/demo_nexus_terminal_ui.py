#!/usr/bin/env python3
"""
Demo script for NEXUS Terminal UI
Shows various features and integration examples
"""

import time
import threading
from nexus_terminal_ui import NexusTerminalUI, VoiceControlAdapter, TabType

def simulate_voice_commands(voice_adapter: VoiceControlAdapter):
    """Simulate voice commands for demonstration"""
    time.sleep(3)
    
    commands = [
        ("Switch to chat tab", 2),
        ("Go to development", 2),
        ("Switch to monitor tab", 2),
        ("Open command palette", 2),
        ("Switch to project", 2),
    ]
    
    for command, delay in commands:
        print(f"\n[Voice Command]: {command}")
        response = voice_adapter.process_voice_command(command)
        print(f"[Response]: {response}")
        time.sleep(delay)

def main():
    """Run the NEXUS Terminal UI demo"""
    print("Starting NEXUS Terminal UI Demo...")
    print("=" * 50)
    print("Keyboard shortcuts:")
    print("  F1-F6: Switch tabs directly")
    print("  Tab/Shift+Tab: Navigate tabs")
    print("  Ctrl+P: Open command palette")
    print("  Ctrl+Q: Quit")
    print("  Arrow keys: Navigate within tabs")
    print("=" * 50)
    print("\nPress any key to start...")
    input()
    
    # Create the UI
    ui = NexusTerminalUI()
    
    # Create voice control adapter
    voice_adapter = VoiceControlAdapter(ui)
    
    # Start voice command simulation in background
    # Uncomment to see automated demo
    # voice_thread = threading.Thread(target=simulate_voice_commands, args=(voice_adapter,))
    # voice_thread.daemon = True
    # voice_thread.start()
    
    # Run the UI
    try:
        ui.run()
    except KeyboardInterrupt:
        print("\nUI interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print("\nNEXUS Terminal UI Demo completed.")

if __name__ == "__main__":
    main()