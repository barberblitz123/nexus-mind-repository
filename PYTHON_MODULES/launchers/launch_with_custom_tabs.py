#!/usr/bin/env python3
"""
NEXUS 2.0 Launcher with Custom HTML Tabs
Integrates your Stage Management and Desktop Prototype HTML files
"""

import sys
import os
import subprocess
from pathlib import Path

# Add interfaces to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'interfaces'))

from nexus_html_tab_integrator import NEXUSHTMLTabIntegrator

def main():
    print("""
    ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗    ██████╗    ██████╗ 
    ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝    ╚════██╗  ██╔═████╗
    ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗     █████╔╝  ██║██╔██║
    ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║    ██╔═══╝   ████╔╝██║
    ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║    ███████╗██╗╚██████╔╝
    ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝    ╚══════╝╚═╝ ╚═════╝ 
    
    🎭 With Custom HTML Tab Integration 🖥️
    """)
    print("=" * 60)
    
    # Check for HTML files
    configs_dir = os.path.join(os.path.dirname(__file__), 'configs')
    stage_html = os.path.join(configs_dir, 'stage_management.html')
    prototype_html = os.path.join(configs_dir, 'desktop_prototype.html')
    
    print("📁 Looking for HTML files in:", configs_dir)
    
    if not os.path.exists(configs_dir):
        os.makedirs(configs_dir, exist_ok=True)
        print(f"📂 Created configs directory: {configs_dir}")
    
    if not os.path.exists(stage_html):
        print(f"\n⚠️  Stage Management HTML not found!")
        print(f"   Expected at: {stage_html}")
        print("\n   To add your file:")
        print(f"   cp ~/Downloads/stage_management.html {stage_html}")
        
    if not os.path.exists(prototype_html):
        print(f"\n⚠️  Desktop Prototype HTML not found!")
        print(f"   Expected at: {prototype_html}")
        print("\n   To add your file:")
        print(f"   cp ~/Downloads/desktop_prototype.html {prototype_html}")
        
    if not os.path.exists(stage_html) or not os.path.exists(prototype_html):
        print("\n" + "=" * 60)
        print("📝 Instructions:")
        print("1. Copy your HTML files to the configs directory")
        print("2. Make sure they're named:")
        print("   - stage_management.html")
        print("   - desktop_prototype.html")
        print("3. Run this script again")
        print("\n💡 Tip: You can also drag & drop files into VS Code")
        return
        
    # Create integrator
    integrator = NEXUSHTMLTabIntegrator()
    
    print("\n✅ Found both HTML files!")
    print("\n🔧 Integration Options:")
    print("1. Web Interface (Best for HTML content) - RECOMMENDED")
    print("2. Terminal Interface (Limited HTML rendering)")
    print("3. Both Interfaces")
    print("4. Quick Preview (Opens HTML directly)")
    
    choice = input("\nSelect option (1-4) [1]: ").strip() or "1"
    
    if choice in ["1", "3"]:
        print("\n🌐 Creating Unified Web Interface with HTML tabs...")
        web_path = integrator.create_unified_web_interface(stage_html, prototype_html)
        if web_path:
            print(f"✅ Web interface created: {web_path}")
            print("\n🚀 To launch:")
            print("   cd NEXUS_2.0_AGENT")
            print("   python -m http.server 8080")
            print("   Then open: http://localhost:8080/interfaces/nexus_unified_web_with_custom_tabs.html")
            
            # Option to auto-launch
            launch = input("\n🚀 Launch web server now? (y/n) [y]: ").strip().lower()
            if launch != 'n':
                print("\n Starting web server on http://localhost:8080")
                os.chdir(os.path.dirname(__file__))
                subprocess.run([sys.executable, "-m", "http.server", "8080"])
            
    if choice in ["2", "3"]:
        print("\n💻 Integrating into Terminal Interface...")
        terminal_path = os.path.join(os.path.dirname(__file__), "core/nexus_terminal_ui_advanced.py")
        if os.path.exists(terminal_path):
            new_path = integrator.integrate_into_terminal_ui(terminal_path)
            print(f"✅ Terminal interface updated: {new_path}")
            print("\n🚀 To launch terminal UI:")
            print(f"   python {new_path}")
        else:
            print("❌ Terminal UI not found at:", terminal_path)
            
    if choice == "4":
        print("\n👀 Quick Preview Mode")
        print(f"1. Stage Management: file://{os.path.abspath(stage_html)}")
        print(f"2. Desktop Prototype: file://{os.path.abspath(prototype_html)}")
        print("\nOpening in default browser...")
        import webbrowser
        webbrowser.open(f"file://{os.path.abspath(stage_html)}")
        webbrowser.open(f"file://{os.path.abspath(prototype_html)}")

if __name__ == "__main__":
    main()