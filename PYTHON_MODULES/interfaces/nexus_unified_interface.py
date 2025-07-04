#!/usr/bin/env python3
"""
NEXUS 2.0 Unified Interface
Works on any device - Terminal, Web, Mobile, Desktop
Adaptive interface that detects the environment and provides the best experience
"""

import os
import sys
import platform
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

class NexusInterface(ABC):
    """Abstract base class for all NEXUS interfaces"""
    
    @abstractmethod
    def initialize(self):
        pass
    
    @abstractmethod
    def display(self, content: Any):
        pass
    
    @abstractmethod
    def get_input(self, prompt: str) -> str:
        pass
    
    @abstractmethod
    def run(self):
        pass

class TerminalInterface(NexusInterface):
    """Rich terminal interface for desktop/laptop"""
    def __init__(self):
        self.name = "Terminal Interface"
        
    def initialize(self):
        try:
            from rich.console import Console
            from rich.layout import Layout
            self.console = Console()
            self.use_rich = True
        except ImportError:
            self.use_rich = False
            
    def display(self, content: Any):
        if self.use_rich:
            self.console.print(content)
        else:
            print(content)
            
    def get_input(self, prompt: str) -> str:
        return input(prompt)
        
    def run(self):
        # Import the terminal UI
        from nexus_terminal_ui_advanced import NEXUSTerminalApp
        app = NEXUSTerminalApp()
        app.run()

class WebInterface(NexusInterface):
    """Web-based interface accessible from any browser"""
    def __init__(self, host="0.0.0.0", port=8080):
        self.name = "Web Interface"
        self.host = host
        self.port = port
        
    def initialize(self):
        try:
            import flask
            import flask_socketio
            self.flask_available = True
        except ImportError:
            self.flask_available = False
            
    def display(self, content: Any):
        # Web display handled by templates
        pass
        
    def get_input(self, prompt: str) -> str:
        # Web input handled by forms/websockets
        pass
        
    def run(self):
        if self.flask_available:
            from nexus_web_universal import create_app
            app = create_app()
            app.run(host=self.host, port=self.port)
        else:
            print("Flask not available. Install with: pip install flask flask-socketio")

class MobileInterface(NexusInterface):
    """Mobile-optimized interface"""
    def __init__(self):
        self.name = "Mobile Interface"
        
    def initialize(self):
        # Mobile-specific initialization
        self.screen_size = self._detect_screen_size()
        
    def _detect_screen_size(self):
        # Detect if running on mobile device
        return "small" if self._is_mobile() else "large"
        
    def _is_mobile(self):
        # Check various indicators of mobile environment
        return (
            'ANDROID_ROOT' in os.environ or
            'ANDROID_DATA' in os.environ or
            platform.machine().startswith('arm') or
            os.path.exists('/system/app/')  # Android
        )
        
    def display(self, content: Any):
        # Simplified display for mobile
        print(f"[NEXUS] {content}")
        
    def get_input(self, prompt: str) -> str:
        return input(f"➤ {prompt}: ")
        
    def run(self):
        # Run simplified mobile interface
        from nexus_mobile_cli import run_mobile_interface
        run_mobile_interface()

class UnifiedNexusLauncher:
    """Automatically detects environment and launches appropriate interface"""
    
    def __init__(self):
        self.environment = self._detect_environment()
        self.interface = self._select_interface()
        
    def _detect_environment(self) -> Dict[str, Any]:
        """Detect the current runtime environment"""
        env = {
            "platform": platform.system(),
            "machine": platform.machine(),
            "python_version": sys.version,
            "is_tty": sys.stdin.isatty() if hasattr(sys.stdin, 'isatty') else False,
            "is_jupyter": 'ipykernel' in sys.modules,
            "is_colab": 'google.colab' in sys.modules,
            "is_mobile": self._is_mobile_device(),
            "is_web": self._is_web_environment(),
            "has_display": self._has_display()
        }
        return env
        
    def _is_mobile_device(self) -> bool:
        """Check if running on mobile device"""
        mobile_indicators = [
            'ANDROID_ROOT' in os.environ,
            'ANDROID_DATA' in os.environ,
            platform.machine().startswith('arm'),
            os.path.exists('/system/app/'),  # Android
            os.path.exists('/var/mobile/')   # iOS (jailbroken)
        ]
        return any(mobile_indicators)
        
    def _is_web_environment(self) -> bool:
        """Check if running in web context"""
        return (
            os.environ.get('SERVER_SOFTWARE', '').startswith('gunicorn') or
            os.environ.get('WERKZEUG_RUN_MAIN') is not None or
            'flask' in sys.modules
        )
        
    def _has_display(self) -> bool:
        """Check if display is available"""
        if platform.system() == 'Windows':
            return True
        return os.environ.get('DISPLAY') is not None
        
    def _select_interface(self) -> NexusInterface:
        """Select the best interface based on environment"""
        if self.environment['is_web']:
            return WebInterface()
        elif self.environment['is_mobile']:
            return MobileInterface()
        elif self.environment['is_tty'] and self.environment['has_display']:
            return TerminalInterface()
        else:
            # Fallback to web interface for maximum compatibility
            return WebInterface()
            
    def print_environment_info(self):
        """Display detected environment information"""
        print("🔍 NEXUS 2.0 Environment Detection")
        print("=" * 50)
        for key, value in self.environment.items():
            print(f"{key}: {value}")
        print(f"\nSelected Interface: {self.interface.name}")
        print("=" * 50)
        
    def launch(self):
        """Launch NEXUS with the appropriate interface"""
        print("""
        ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗    ██████╗    ██████╗ 
        ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝    ╚════██╗  ██╔═████╗
        ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗     █████╔╝  ██║██╔██║
        ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║    ██╔═══╝   ████╔╝██║
        ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║    ███████╗██╗╚██████╔╝
        ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝    ╚══════╝╚═╝ ╚═════╝ 
        
        Unified Adaptive Interface - Works Anywhere!
        """)
        
        self.print_environment_info()
        
        # Initialize and run the selected interface
        self.interface.initialize()
        
        # Allow user to override interface selection
        if self.environment['is_tty']:
            print("\n🎯 Interface Options:")
            print("1. Use detected interface")
            print("2. Force Terminal Interface")
            print("3. Force Web Interface")
            print("4. Force Mobile Interface")
            
            choice = input("\nSelect option (1-4) [1]: ").strip() or "1"
            
            if choice == "2":
                self.interface = TerminalInterface()
            elif choice == "3":
                self.interface = WebInterface()
            elif choice == "4":
                self.interface = MobileInterface()
                
            self.interface.initialize()
            
        print(f"\n🚀 Launching {self.interface.name}...")
        self.interface.run()

# Integration point for user files
class UserFileIntegrator:
    """Integrates user-provided files into NEXUS interface"""
    
    def __init__(self, file1_path: Optional[str] = None, file2_path: Optional[str] = None):
        self.file1_path = file1_path
        self.file2_path = file2_path
        self.integrated_config = {}
        
    def load_user_files(self):
        """Load and parse user files"""
        if self.file1_path and os.path.exists(self.file1_path):
            with open(self.file1_path, 'r') as f:
                # Parse based on file type
                content1 = f.read()
                # Add parsing logic based on your file format
                
        if self.file2_path and os.path.exists(self.file2_path):
            with open(self.file2_path, 'r') as f:
                content2 = f.read()
                # Add parsing logic
                
    def integrate_into_interface(self, interface: NexusInterface):
        """Integrate user configurations into the interface"""
        # This is where we'll merge user files into NEXUS
        pass

if __name__ == "__main__":
    # Check for user files passed as arguments
    user_file1 = sys.argv[1] if len(sys.argv) > 1 else None
    user_file2 = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Create integrator if user files provided
    if user_file1 or user_file2:
        integrator = UserFileIntegrator(user_file1, user_file2)
        integrator.load_user_files()
    
    # Launch unified NEXUS
    launcher = UnifiedNexusLauncher()
    launcher.launch()