"""
NEXUS Voice Control Demo
========================
Interactive demonstration of the voice control system
"""

import time
import threading
from nexus_voice_control import (
    VoiceController, ListeningMode, CommandType,
    VoiceCommand, create_example_ui_integration
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NEXUSMockUI:
    """Mock UI for demonstrating voice control"""
    
    def __init__(self):
        self.tabs = ["Design", "Code", "Deploy", "Data", "Settings", "Docs"]
        self.current_tab = "Design"
        self.items = {
            "Design": ["Canvas", "Toolbar", "Properties", "Layers"],
            "Code": ["Editor", "Terminal", "Git", "Debug"],
            "Deploy": ["Environments", "Pipelines", "Monitoring", "Logs"],
            "Data": ["Tables", "Queries", "Visualizations", "Connections"],
            "Settings": ["Profile", "Preferences", "API Keys", "Billing"],
            "Docs": ["Getting Started", "API Reference", "Examples", "Support"]
        }
        self.mode = "normal"
        self.history = []
    
    def switch_tab(self, target: str, **kwargs):
        """Switch to a different tab"""
        target_title = target.title()
        if target_title in self.tabs:
            self.current_tab = target_title
            self.history.append(f"Switched to {target_title} tab")
            logger.info(f"✅ UI: Switched to {target_title} tab")
            self._display_state()
            return True
        else:
            logger.error(f"❌ UI: Tab '{target}' not found")
            return False
    
    def show_item(self, target: str, **kwargs):
        """Show a specific item in the current tab"""
        items = self.items.get(self.current_tab, [])
        target_title = target.title()
        
        if target_title in items:
            self.history.append(f"Showing {target_title} in {self.current_tab}")
            logger.info(f"✅ UI: Showing {target_title}")
            self._display_state()
            return True
        else:
            # Try to find in any tab
            for tab, tab_items in self.items.items():
                if target_title in tab_items:
                    self.current_tab = tab
                    self.history.append(f"Found {target_title} in {tab}, switching tabs")
                    logger.info(f"✅ UI: Found {target_title} in {tab} tab")
                    self._display_state()
                    return True
            
            logger.error(f"❌ UI: Item '{target}' not found")
            return False
    
    def create_new(self, target: str, **kwargs):
        """Create a new item"""
        self.history.append(f"Created new {target}")
        logger.info(f"✅ UI: Creating new {target}")
        
        # Add to current tab's items
        if self.current_tab in self.items:
            new_item = f"New {target.title()}"
            self.items[self.current_tab].append(new_item)
            self._display_state()
        
        return True
    
    def save(self, **kwargs):
        """Save current work"""
        self.history.append("Saved all changes")
        logger.info("✅ UI: Saved all changes")
        return True
    
    def undo(self, **kwargs):
        """Undo last action"""
        if self.history:
            last_action = self.history.pop()
            logger.info(f"✅ UI: Undid '{last_action}'")
            return True
        return False
    
    def start_work(self, target: str, **kwargs):
        """Start working on something (context-aware)"""
        self.mode = f"working_on_{target}"
        self.history.append(f"Started working on {target}")
        logger.info(f"✅ UI: Started working on {target}")
        
        # Switch to appropriate tab
        if target.lower() in ["design", "ui", "interface"]:
            self.switch_tab("design")
        elif target.lower() in ["code", "development", "programming"]:
            self.switch_tab("code")
        
        return True
    
    def switch_mode(self, target: str, **kwargs):
        """Switch UI mode"""
        self.mode = target
        self.history.append(f"Switched to {target} mode")
        logger.info(f"✅ UI: Switched to {target} mode")
        self._display_state()
        return True
    
    def deployment_status(self, **kwargs):
        """Show deployment status"""
        self.switch_tab("deploy")
        self.history.append("Showing deployment status")
        logger.info("✅ UI: Showing deployment status")
        logger.info("   🟢 Production: Healthy")
        logger.info("   🟡 Staging: Deploying...")
        logger.info("   🔵 Development: Ready")
        return True
    
    def _display_state(self):
        """Display current UI state"""
        print("\n" + "="*50)
        print(f"NEXUS UI State")
        print("="*50)
        print(f"Current Tab: {self.current_tab}")
        print(f"Mode: {self.mode}")
        print(f"Available items: {', '.join(self.items.get(self.current_tab, []))}")
        if self.history:
            print(f"Last action: {self.history[-1]}")
        print("="*50 + "\n")


def interactive_demo():
    """Run an interactive voice control demo"""
    print("\n🎙️  NEXUS Voice Control Demo")
    print("="*50)
    print("Available commands:")
    print("  - 'Hey NEXUS' - Wake word to activate")
    print("  - 'Go to [tab]' - Switch tabs (design, code, deploy, etc.)")
    print("  - 'Show me [item]' - Navigate to specific items")
    print("  - 'Create new [thing]' - Create new components")
    print("  - 'Start designing' - Context-aware commands")
    print("  - 'Switch to [mode] mode' - Change UI modes")
    print("  - 'Save' - Save your work")
    print("  - 'Undo' - Undo last action")
    print("="*50)
    
    # Create mock UI
    ui = NEXUSMockUI()
    
    # Create voice controller
    controller = VoiceController(wake_word="hey nexus")
    
    # Register UI callbacks
    controller.ui_integration.register_callback("switch_tab", ui.switch_tab)
    controller.ui_integration.register_callback("show_item", ui.show_item)
    controller.ui_integration.register_callback("create_new", ui.create_new)
    controller.ui_integration.register_callback("save", ui.save)
    controller.ui_integration.register_callback("undo", ui.undo)
    controller.ui_integration.register_callback("start_work", ui.start_work)
    controller.ui_integration.register_callback("switch_mode", ui.switch_mode)
    controller.ui_integration.register_callback("deployment_status", ui.deployment_status)
    
    # Start voice control
    controller.start()
    
    # Display initial state
    ui._display_state()
    
    # Interactive menu
    while True:
        print("\nOptions:")
        print("1. Change listening mode")
        print("2. Simulate voice command")
        print("3. View command history")
        print("4. Calibrate noise")
        print("5. Exit")
        
        choice = input("\nChoice (or press Enter to continue listening): ").strip()
        
        if choice == "1":
            print("\nListening modes:")
            print("1. Wake word (Hey NEXUS)")
            print("2. Always active")
            print("3. Push to talk")
            print("4. Disabled")
            
            mode_choice = input("Select mode: ").strip()
            
            if mode_choice == "1":
                controller.set_mode(ListeningMode.WAKE_WORD)
                print("✅ Set to wake word mode")
            elif mode_choice == "2":
                controller.set_mode(ListeningMode.ACTIVE)
                print("✅ Set to always active mode")
            elif mode_choice == "3":
                controller.set_mode(ListeningMode.PUSH_TO_TALK)
                print("✅ Set to push-to-talk mode")
            elif mode_choice == "4":
                controller.set_mode(ListeningMode.DISABLED)
                print("✅ Voice control disabled")
        
        elif choice == "2":
            # Simulate a voice command
            command_text = input("Enter command to simulate: ").strip()
            if command_text:
                controller.command_queue.put(command_text)
        
        elif choice == "3":
            # View history
            print("\nCommand History:")
            for i, action in enumerate(ui.history[-10:], 1):
                print(f"  {i}. {action}")
        
        elif choice == "4":
            # Recalibrate noise
            controller.calibrate_noise()
            print("✅ Noise calibration complete")
        
        elif choice == "5":
            break
        
        time.sleep(0.5)
    
    # Stop voice control
    controller.stop()
    print("\n👋 Voice control demo ended")


def automated_demo():
    """Run an automated demonstration"""
    print("\n🤖 Running automated voice control demo...")
    
    # Create mock UI
    ui = NEXUSMockUI()
    
    # Create voice controller
    controller = VoiceController(wake_word="hey nexus")
    
    # Register UI callbacks
    controller.ui_integration.register_callback("switch_tab", ui.switch_tab)
    controller.ui_integration.register_callback("show_item", ui.show_item)
    controller.ui_integration.register_callback("create_new", ui.create_new)
    controller.ui_integration.register_callback("save", ui.save)
    controller.ui_integration.register_callback("start_work", ui.start_work)
    controller.ui_integration.register_callback("deployment_status", ui.deployment_status)
    
    # Start voice control in active mode
    controller.start()
    controller.set_mode(ListeningMode.ACTIVE)
    
    # Simulate voice commands
    demo_commands = [
        ("Hey NEXUS", 2),
        ("Go to design tab", 2),
        ("Show me the canvas", 2),
        ("Create new component", 2),
        ("Switch to code tab", 2),
        ("Show me the editor", 2),
        ("Let's work on the interface", 2),
        ("Show me deployment status", 2),
        ("Save", 2),
        ("Go back to design", 2),
    ]
    
    for command, delay in demo_commands:
        print(f"\n🎤 Simulating: '{command}'")
        controller.command_queue.put(command)
        time.sleep(delay)
    
    # Stop controller
    controller.stop()
    print("\n✅ Automated demo complete!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        automated_demo()
    else:
        try:
            interactive_demo()
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted")