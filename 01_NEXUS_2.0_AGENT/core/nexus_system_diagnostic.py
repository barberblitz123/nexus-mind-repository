#!/usr/bin/env python3
"""
NEXUS 2.0 System Diagnostic Tool
Automatically checks system health and reports missing components
"""

import os
import sys
import importlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class NexusSystemDiagnostic:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.report = []
        self.missing_files = []
        self.found_files = []
        self.import_errors = []
        self.working_components = []
        
    def add_report(self, message: str, level: str = "INFO"):
        """Add a line to the diagnostic report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.report.append(f"[{timestamp}] [{level}] {message}")
        print(f"[{level}] {message}")
        
    def check_file_exists(self, filename: str, description: str) -> bool:
        """Check if a file exists"""
        file_path = self.base_path / filename
        if file_path.exists():
            self.found_files.append((filename, description))
            self.add_report(f"✅ {filename} - FOUND ({description})")
            return True
        else:
            self.missing_files.append((filename, description))
            self.add_report(f"❌ {filename} - MISSING ({description})", "ERROR")
            return False
            
    def check_import(self, module_name: str, class_name: str, description: str) -> bool:
        """Check if a module can be imported"""
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, class_name):
                self.working_components.append((module_name, description))
                self.add_report(f"✅ {module_name}.{class_name} - IMPORTABLE")
                return True
            else:
                self.import_errors.append((module_name, f"Class {class_name} not found"))
                self.add_report(f"❌ {module_name}.{class_name} - CLASS NOT FOUND", "ERROR")
                return False
        except ImportError as e:
            self.import_errors.append((module_name, str(e)))
            self.add_report(f"❌ {module_name} - IMPORT ERROR: {e}", "ERROR")
            return False
            
    def check_core_components(self):
        """Check all core NEXUS 2.0 components"""
        self.add_report("="*60)
        self.add_report("NEXUS 2.0 SYSTEM DIAGNOSTIC REPORT")
        self.add_report("="*60)
        
        # Core component files
        core_files = [
            ("nexus_stage_manager.py", "Manages agent windows"),
            ("nexus_desktop_manager.py", "Chat and preview interface"),
            ("nexus_task_orchestrator.py", "Connects chat to agents"),
            ("nexus_autonomous_agent.py", "Self-directed AI agent"),
            ("nexus_agent_orchestrator_advanced.py", "Multi-agent management"),
            ("nexus_tabbed_interface.py", "5-tab terminal interface"),
            ("nexus_integrated_workspace.py", "Original full UI"),
            ("nexus_simple_demo.py", "Demo without bugs"),
            ("nexus_terminal_ui_advanced.py", "VS Code-like terminal"),
            ("nexus_terminal_app.py", "Simple terminal UI"),
            ("nexus_integrated_terminal.py", "Terminal session management"),
        ]
        
        self.add_report("\n📁 Checking Core Files:")
        for filename, description in core_files:
            self.check_file_exists(filename, description)
            
    def check_imports(self):
        """Check if core modules can be imported"""
        self.add_report("\n📦 Checking Module Imports:")
        
        imports_to_check = [
            ("nexus_stage_manager", "StageManager", "Agent window management"),
            ("nexus_desktop_manager", "DesktopManager", "Chat/Preview interface"),
            ("nexus_task_orchestrator", "TaskOrchestrator", "Task processing"),
            ("nexus_autonomous_agent", "AutonomousMANUS", "Autonomous agent"),
            ("nexus_agent_orchestrator_advanced", "AgentOrchestrator", "Agent orchestration"),
        ]
        
        for module, class_name, description in imports_to_check:
            self.check_import(module, class_name, description)
            
    def check_dependencies(self):
        """Check Python package dependencies"""
        self.add_report("\n📚 Checking Dependencies:")
        
        packages = {
            "textual": "Terminal UI framework",
            "rich": "Terminal formatting",
            "psutil": "System monitoring",
            "aiofiles": "Async file operations",
            "websockets": "WebSocket support"
        }
        
        for package, description in packages.items():
            try:
                __import__(package)
                self.add_report(f"✅ {package} - INSTALLED ({description})")
            except ImportError:
                self.add_report(f"❌ {package} - NOT INSTALLED ({description})", "WARNING")
                
    def check_web_interface(self):
        """Check web interface components"""
        self.add_report("\n🌐 Checking Web Interface:")
        
        web_files = [
            ("../interfaces/nexus_tabbed_web.html", "Web UI HTML"),
            ("../interfaces/nexus_tabbed_web.js", "Web UI JavaScript"),
            ("../interfaces/nexus_websocket_server.py", "WebSocket server"),
            ("../interfaces/launch_web_interface.sh", "Web launcher script"),
        ]
        
        for rel_path, description in web_files:
            file_path = self.base_path / rel_path
            if file_path.exists():
                self.add_report(f"✅ {rel_path} - FOUND ({description})")
            else:
                self.add_report(f"❌ {rel_path} - MISSING ({description})", "WARNING")
                
    def generate_summary(self):
        """Generate a summary of the diagnostic results"""
        self.add_report("\n" + "="*60)
        self.add_report("DIAGNOSTIC SUMMARY")
        self.add_report("="*60)
        
        total_core_files = 11
        found_count = len([f for f, _ in self.found_files if "nexus_" in f])
        missing_count = len([f for f, _ in self.missing_files if "nexus_" in f])
        
        self.add_report(f"\n📊 Core Files Status:")
        self.add_report(f"  Total Expected: {total_core_files}")
        self.add_report(f"  Found: {found_count}")
        self.add_report(f"  Missing: {missing_count}")
        
        if self.missing_files:
            self.add_report(f"\n❌ Missing Critical Files:")
            for file, desc in self.missing_files[:5]:  # Show first 5
                self.add_report(f"  - {file}: {desc}")
                
        if self.import_errors:
            self.add_report(f"\n❌ Import Errors:")
            for module, error in self.import_errors[:5]:
                self.add_report(f"  - {module}: {error}")
                
        # Overall health status
        if missing_count == 0 and len(self.import_errors) == 0:
            self.add_report(f"\n✅ SYSTEM STATUS: HEALTHY")
        elif missing_count < 5:
            self.add_report(f"\n⚠️  SYSTEM STATUS: PARTIALLY FUNCTIONAL")
        else:
            self.add_report(f"\n❌ SYSTEM STATUS: CRITICAL - CORE FILES MISSING")
            
    def generate_fix_script(self):
        """Generate a script to fix missing files"""
        if self.missing_files:
            self.add_report(f"\n🔧 Generating Fix Commands:")
            self.add_report("Run these commands to restore missing files:")
            
            for file, _ in self.missing_files[:5]:
                if file.endswith('.py'):
                    self.add_report(f"  # Create {file}")
                    self.add_report(f"  touch {file}")
                    
    def save_report(self):
        """Save the diagnostic report to a file"""
        report_path = self.base_path / f"diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_path, 'w') as f:
            f.write('\n'.join(self.report))
        self.add_report(f"\n📄 Report saved to: {report_path}")
        
    def run_full_diagnostic(self):
        """Run the complete system diagnostic"""
        self.check_core_components()
        self.check_imports()
        self.check_dependencies()
        self.check_web_interface()
        self.generate_summary()
        self.generate_fix_script()
        self.save_report()

def main():
    """Run the diagnostic tool"""
    diagnostic = NexusSystemDiagnostic()
    diagnostic.run_full_diagnostic()

if __name__ == "__main__":
    main()