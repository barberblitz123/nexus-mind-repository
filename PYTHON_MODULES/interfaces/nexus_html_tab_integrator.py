#!/usr/bin/env python3
"""
NEXUS 2.0 HTML Tab Integrator
Converts HTML files into integrated tabs within NEXUS interface
Supports both terminal and web interfaces
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from html.parser import HTMLParser

@dataclass
class HTMLTab:
    """Represents an HTML file as a tab"""
    name: str
    title: str
    html_path: str
    content: str
    styles: str
    scripts: str
    order: int = 0

class HTMLExtractor(HTMLParser):
    """Extracts components from HTML files"""
    
    def __init__(self):
        super().__init__()
        self.title = "Untitled"
        self.styles = []
        self.scripts = []
        self.body_content = []
        self.in_title = False
        self.in_style = False
        self.in_script = False
        self.in_body = False
        
    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True
        elif tag == "style":
            self.in_style = True
        elif tag == "script":
            self.in_script = True
        elif tag == "body":
            self.in_body = True
            
    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "style":
            self.in_style = False
        elif tag == "script":
            self.in_script = False
        elif tag == "body":
            self.in_body = False
            
    def handle_data(self, data):
        if self.in_title:
            self.title = data.strip()
        elif self.in_style:
            self.styles.append(data)
        elif self.in_script:
            self.scripts.append(data)
        elif self.in_body:
            self.body_content.append(data)

class NEXUSHTMLTabIntegrator:
    """Integrates HTML files as tabs in NEXUS interface"""
    
    def __init__(self):
        self.tabs: List[HTMLTab] = []
        self.custom_tabs_config = {
            "stage_management": {
                "name": "Stage Management",
                "icon": "🎭",
                "order": 7,
                "shortcut": "7"
            },
            "desktop_prototype": {
                "name": "Desktop Prototype", 
                "icon": "🖥️",
                "order": 8,
                "shortcut": "8"
            }
        }
        
    def load_html_file(self, html_path: str, tab_type: str) -> Optional[HTMLTab]:
        """Load and parse an HTML file into a tab"""
        if not os.path.exists(html_path):
            print(f"❌ HTML file not found: {html_path}")
            return None
            
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Extract components
        parser = HTMLExtractor()
        parser.feed(html_content)
        
        # Get tab config
        config = self.custom_tabs_config.get(tab_type, {})
        
        tab = HTMLTab(
            name=config.get("name", parser.title),
            title=parser.title,
            html_path=html_path,
            content=html_content,
            styles="\n".join(parser.styles),
            scripts="\n".join(parser.scripts),
            order=config.get("order", 99)
        )
        
        self.tabs.append(tab)
        return tab
        
    def generate_terminal_tab_code(self) -> str:
        """Generate Python code for terminal tabs"""
        code = '''
# Additional HTML-based tabs for NEXUS Terminal UI
class StageManagementTab(Container):
    """Stage Management Interface Tab"""
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("🎭 Stage Management", classes="tab-title")
            yield Rule()
            # Terminal representation of HTML content
            yield TextLog(id="stage-content", wrap=True)
            
    def on_mount(self) -> None:
        # Load HTML content and convert to terminal display
        content_widget = self.query_one("#stage-content")
        content_widget.write("Stage Management Interface")
        content_widget.write("=" * 50)
        # Add converted HTML content here

class DesktopPrototypeTab(Container):
    """Desktop Prototype Interface Tab"""
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("🖥️ Desktop Prototype", classes="tab-title")
            yield Rule()
            yield TextLog(id="prototype-content", wrap=True)
            
    def on_mount(self) -> None:
        content_widget = self.query_one("#prototype-content")
        content_widget.write("Desktop Prototype Interface")
        content_widget.write("=" * 50)
        # Add converted HTML content here
'''
        return code
        
    def generate_web_interface_code(self) -> str:
        """Generate web interface code with HTML tabs"""
        template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEXUS 2.0 Agent Interface</title>
    <style>
        /* NEXUS 2.0 Unified Styles */
        body {
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
        }
        
        .nexus-container {
            display: flex;
            height: 100vh;
            overflow: hidden;
        }
        
        .nexus-sidebar {
            width: 60px;
            background: #1a1a1a;
            border-right: 1px solid #333;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding-top: 10px;
        }
        
        .tab-button {
            width: 50px;
            height: 50px;
            background: transparent;
            border: none;
            color: #888;
            font-size: 24px;
            cursor: pointer;
            position: relative;
            margin-bottom: 10px;
            border-radius: 8px;
            transition: all 0.2s;
        }
        
        .tab-button:hover {
            background: #2a2a2a;
            color: #fff;
        }
        
        .tab-button.active {
            background: #3a3a3a;
            color: #00ff88;
        }
        
        .tab-button .shortcut {
            position: absolute;
            bottom: 2px;
            right: 2px;
            font-size: 10px;
            color: #666;
        }
        
        .nexus-main {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: #0f0f0f;
        }
        
        .tab-content {
            display: none;
            flex: 1;
            padding: 20px;
            overflow-y: auto;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .tab-content iframe {
            width: 100%;
            height: 100%;
            border: none;
            background: white;
            border-radius: 8px;
        }
        
        /* Custom HTML tab styles */
        {custom_styles}
    </style>
</head>
<body>
    <div class="nexus-container">
        <div class="nexus-sidebar">
            <button class="tab-button active" data-tab="terminal" title="Terminal">
                💻<span class="shortcut">1</span>
            </button>
            <button class="tab-button" data-tab="development" title="Development">
                🔧<span class="shortcut">2</span>
            </button>
            <button class="tab-button" data-tab="chat" title="AI Chat">
                💬<span class="shortcut">3</span>
            </button>
            <button class="tab-button" data-tab="design" title="Design">
                🎨<span class="shortcut">4</span>
            </button>
            <button class="tab-button" data-tab="deploy" title="Deploy">
                🚀<span class="shortcut">5</span>
            </button>
            <button class="tab-button" data-tab="monitor" title="Monitor">
                📊<span class="shortcut">6</span>
            </button>
            <button class="tab-button" data-tab="stage" title="Stage Management">
                🎭<span class="shortcut">7</span>
            </button>
            <button class="tab-button" data-tab="prototype" title="Desktop Prototype">
                🖥️<span class="shortcut">8</span>
            </button>
        </div>
        
        <div class="nexus-main">
            <div class="tab-content active" id="terminal-tab">
                <h2>Terminal Interface</h2>
                <div id="terminal"></div>
            </div>
            
            <div class="tab-content" id="development-tab">
                <h2>Development Environment</h2>
            </div>
            
            <div class="tab-content" id="chat-tab">
                <h2>AI Assistant Chat</h2>
            </div>
            
            <div class="tab-content" id="design-tab">
                <h2>Design Tools</h2>
            </div>
            
            <div class="tab-content" id="deploy-tab">
                <h2>Deployment Manager</h2>
            </div>
            
            <div class="tab-content" id="monitor-tab">
                <h2>System Monitor</h2>
            </div>
            
            <!-- Custom HTML Tabs -->
            <div class="tab-content" id="stage-tab">
                {stage_management_content}
            </div>
            
            <div class="tab-content" id="prototype-tab">
                {desktop_prototype_content}
            </div>
        </div>
    </div>
    
    <script>
        // Tab switching logic
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', () => {
                // Remove active class from all
                document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
                
                // Add active to clicked
                button.classList.add('active');
                const tabId = button.dataset.tab + '-tab';
                document.getElementById(tabId).classList.add('active');
            });
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key >= '1' && e.key <= '8') {
                const index = parseInt(e.key) - 1;
                const button = document.querySelectorAll('.tab-button')[index];
                if (button) button.click();
            }
        });
        
        {custom_scripts}
    </script>
</body>
</html>
'''
        return template
        
    def integrate_into_terminal_ui(self, terminal_ui_path: str):
        """Integrate HTML tabs into terminal UI"""
        # Read existing terminal UI
        with open(terminal_ui_path, 'r') as f:
            content = f.read()
            
        # Find where to insert new tabs
        # Add import for HTML content handling
        imports_insert = "from textual.widgets import ("
        new_import = "from textual.widgets import ("
        
        # Add tab classes
        tab_code = self.generate_terminal_tab_code()
        
        # Update tab configuration
        tab_config = '''
        # Add custom HTML tabs
        self.tabs["stage_management"] = StageManagementTab()
        self.tabs["desktop_prototype"] = DesktopPrototypeTab()
'''
        
        # Save updated file
        output_path = terminal_ui_path.replace('.py', '_with_html_tabs.py')
        with open(output_path, 'w') as f:
            f.write(content)
            f.write("\n\n# HTML TAB INTEGRATION\n")
            f.write(tab_code)
            
        return output_path
        
    def create_unified_web_interface(self, stage_html: str, prototype_html: str) -> str:
        """Create a unified web interface with integrated HTML tabs"""
        # Load HTML files
        stage_tab = self.load_html_file(stage_html, "stage_management")
        prototype_tab = self.load_html_file(prototype_html, "desktop_prototype")
        
        if not stage_tab or not prototype_tab:
            return None
            
        # Generate web interface
        template = self.generate_web_interface_code()
        
        # Replace placeholders
        html_content = template.format(
            custom_styles=stage_tab.styles + "\n" + prototype_tab.styles,
            stage_management_content=stage_tab.content,
            desktop_prototype_content=prototype_tab.content,
            custom_scripts=stage_tab.scripts + "\n" + prototype_tab.scripts
        )
        
        # Save unified interface
        output_path = "NEXUS_2.0_AGENT/interfaces/nexus_unified_web_with_custom_tabs.html"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(html_content)
            
        return output_path

def create_integration_launcher():
    """Create a launcher that integrates custom HTML files"""
    launcher_code = '''#!/usr/bin/env python3
"""
NEXUS 2.0 Launcher with Custom HTML Tabs
"""

import sys
import os
from nexus_html_tab_integrator import NEXUSHTMLTabIntegrator

def main():
    print("🚀 NEXUS 2.0 with Custom HTML Tabs")
    print("=" * 50)
    
    # Check for HTML files
    stage_html = "configs/stage_management.html"
    prototype_html = "configs/desktop_prototype.html"
    
    if not os.path.exists(stage_html):
        print(f"⚠️  Stage Management HTML not found at: {stage_html}")
        print("Please copy your stage_management.html to NEXUS_2.0_AGENT/configs/")
        
    if not os.path.exists(prototype_html):
        print(f"⚠️  Desktop Prototype HTML not found at: {prototype_html}")
        print("Please copy your desktop_prototype.html to NEXUS_2.0_AGENT/configs/")
        
    if not os.path.exists(stage_html) or not os.path.exists(prototype_html):
        print("\\nPlace your HTML files in the configs directory and run again.")
        return
        
    # Create integrator
    integrator = NEXUSHTMLTabIntegrator()
    
    print("\\n🔧 Integration Options:")
    print("1. Web Interface (Recommended for HTML content)")
    print("2. Terminal Interface (Limited HTML rendering)")
    print("3. Both Interfaces")
    
    choice = input("\\nSelect option (1-3): ").strip()
    
    if choice in ["1", "3"]:
        print("\\n🌐 Creating Web Interface with HTML tabs...")
        web_path = integrator.create_unified_web_interface(stage_html, prototype_html)
        if web_path:
            print(f"✅ Web interface created: {web_path}")
            print("   Open in browser: python -m http.server 8080")
            
    if choice in ["2", "3"]:
        print("\\n💻 Integrating into Terminal Interface...")
        terminal_path = "core/nexus_terminal_ui_advanced.py"
        if os.path.exists(terminal_path):
            new_path = integrator.integrate_into_terminal_ui(terminal_path)
            print(f"✅ Terminal interface updated: {new_path}")
        else:
            print("❌ Terminal UI not found")
            
if __name__ == "__main__":
    main()
'''
    
    with open("NEXUS_2.0_AGENT/launch_with_custom_tabs.py", "w") as f:
        f.write(launcher_code)
        
    os.chmod("NEXUS_2.0_AGENT/launch_with_custom_tabs.py", 0o755)

# Create the launcher
if __name__ == "__main__":
    create_integration_launcher()
    print("✅ HTML Tab Integration System Created!")
    print("\nTo use:")
    print("1. Copy your HTML files to NEXUS_2.0_AGENT/configs/")
    print("   - stage_management.html")
    print("   - desktop_prototype.html")
    print("2. Run: python NEXUS_2.0_AGENT/launch_with_custom_tabs.py")