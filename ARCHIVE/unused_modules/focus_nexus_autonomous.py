#!/usr/bin/env python3
"""
NEXUS 2.0 Autonomous Agent Focus Script
Aggressively cleans and organizes repository to focus on autonomous agent architecture
"""

import os
import shutil
import datetime
from pathlib import Path
from typing import Dict, List, Set
import json

class NexusAutonomousFocus:
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Core autonomous agent files to keep
        self.autonomous_core = {
            # Production-ready autonomous components
            "manus_continuous_agent.py",
            "manus_nexus_integration.py",
            "nexus_integration_core.py",
            
            # Essential memory systems for autonomous operation
            "nexus_memory_core.py",
            "nexus_episodic_memory.py",
            "nexus_semantic_memory.py",
            "nexus_working_memory.py",
            
            # Vision and voice for autonomous perception
            "nexus_vision_processor.py",
            "nexus_voice_control.py",
            
            # Production infrastructure
            "nexus_core_production.py",
            "nexus_config_production.py",
            "nexus_database_production.py",
            
            # Minimal launcher
            "nexus_minimal.py",
            
            # Requirements
            "requirements.txt",
            "manus_requirements.txt"
        }
        
        # Essential web app files
        self.web_core = {
            "nexus-web-app": [
                "unified-nexus-server.js",
                "consciousness-sync.js",
                "index.html",
                "package.json",
                "README.md"
            ]
        }
        
        # Documentation to keep
        self.essential_docs = {
            "README.md",
            "SECURITY.md",
            "NEXUS_INFINITY_ROADMAP.md",
            "CLAUDE.md"
        }

    def cleanup_repository(self):
        """Aggressive cleanup focusing on autonomous agent architecture"""
        
        # Create new structure
        structure = {
            "nexus-autonomous-core": {
                "agents": [],
                "memory": [],
                "integration": [],
                "production": []
            },
            "nexus-web-interface": {},
            "docs": [],
            "_REMOVED": {
                "old_launchers": [],
                "old_interfaces": [],
                "demos": [],
                "tests": [],
                "unused": []
            }
        }
        
        stats = {
            "kept": 0,
            "removed": 0,
            "errors": []
        }
        
        # Process Python files
        for py_file in self.base_path.glob("*.py"):
            filename = py_file.name
            
            if filename in self.autonomous_core:
                # Categorize core files
                if "agent" in filename or "manus" in filename:
                    structure["nexus-autonomous-core"]["agents"].append(filename)
                elif "memory" in filename:
                    structure["nexus-autonomous-core"]["memory"].append(filename)
                elif "integration" in filename:
                    structure["nexus-autonomous-core"]["integration"].append(filename)
                elif "production" in filename:
                    structure["nexus-autonomous-core"]["production"].append(filename)
                else:
                    structure["nexus-autonomous-core"]["agents"].append(filename)
                stats["kept"] += 1
            else:
                # Remove everything else
                if any(x in filename for x in ["launcher", "launch_", "start_", "nexus_2.0_", "nexus_2_0_"]):
                    structure["_REMOVED"]["old_launchers"].append(filename)
                elif "demo_" in filename:
                    structure["_REMOVED"]["demos"].append(filename)
                elif "test_" in filename:
                    structure["_REMOVED"]["tests"].append(filename)
                elif any(x in filename for x in ["_ui", "_interface", "_terminal", "_cli"]):
                    structure["_REMOVED"]["old_interfaces"].append(filename)
                else:
                    structure["_REMOVED"]["unused"].append(filename)
                stats["removed"] += 1
        
        # Keep only essential docs
        for doc in self.base_path.glob("*.md"):
            if doc.name in self.essential_docs:
                structure["docs"].append(doc.name)
                stats["kept"] += 1
            else:
                structure["_REMOVED"]["unused"].append(doc.name)
                stats["removed"] += 1
        
        # Handle web directories
        for web_dir in ["nexus-web-app"]:
            if (self.base_path / web_dir).exists():
                structure["nexus-web-interface"][web_dir] = self.web_core.get(web_dir, [])
                stats["kept"] += 1
        
        # Remove all other directories
        remove_dirs = [
            "nexus-consciousness-live",
            "nexus-minimal", 
            "nexus-unified-app",
            "nexus-mobile-project",
            "nexus_backup_*",
            "ARCHIVE",
            "ACTIVE_NEXUS_2.0"
        ]
        
        for pattern in remove_dirs:
            for dir_path in self.base_path.glob(pattern):
                if dir_path.is_dir():
                    structure["_REMOVED"]["unused"].append(f"{dir_path.name}/")
                    stats["removed"] += 1
        
        return structure, stats

    def execute_cleanup(self, structure: Dict, dry_run: bool = False):
        """Execute the cleanup plan"""
        
        if dry_run:
            return
        
        # Create new directory structure
        print("\nCreating focused directory structure...")
        
        # Create main directories
        core_dir = self.base_path / "nexus-autonomous-core"
        web_dir = self.base_path / "nexus-web-interface" 
        docs_dir = self.base_path / "docs"
        removed_dir = self.base_path / f"_REMOVED_{self.timestamp}"
        
        for d in [core_dir, web_dir, docs_dir, removed_dir]:
            d.mkdir(exist_ok=True)
        
        # Create subdirectories
        for subdir in ["agents", "memory", "integration", "production"]:
            (core_dir / subdir).mkdir(exist_ok=True)
        
        for subdir in structure["_REMOVED"]:
            (removed_dir / subdir).mkdir(exist_ok=True)
        
        # Move files
        moved = []
        
        # Move core files
        for category, files in structure["nexus-autonomous-core"].items():
            for file in files:
                source = self.base_path / file
                dest = core_dir / category / file
                if source.exists():
                    shutil.move(str(source), str(dest))
                    moved.append((file, f"nexus-autonomous-core/{category}"))
        
        # Move docs
        for doc in structure["docs"]:
            source = self.base_path / doc
            dest = docs_dir / doc
            if source.exists() and source != dest:
                shutil.move(str(source), str(dest))
                moved.append((doc, "docs"))
        
        # Move removed files
        for category, files in structure["_REMOVED"].items():
            for file in files:
                source = self.base_path / file
                dest = removed_dir / category / file
                if source.exists():
                    try:
                        if source.is_dir():
                            shutil.move(str(source), str(dest.parent))
                        else:
                            shutil.move(str(source), str(dest))
                        moved.append((file, f"_REMOVED/{category}"))
                    except Exception as e:
                        print(f"Error moving {file}: {e}")
        
        return moved

    def create_focused_structure(self):
        """Create a new focused project structure"""
        
        structure_content = """# NEXUS 2.0 Autonomous Agent Structure

## Core Architecture

### nexus-autonomous-core/
- **agents/** - Autonomous agent implementations
  - manus_continuous_agent.py - Main continuous work agent
  - manus_nexus_integration.py - NEXUS integration bridge
  
- **memory/** - Memory systems for autonomous operation
  - nexus_memory_core.py - Unified memory management
  - nexus_episodic_memory.py - Event-based memory
  - nexus_semantic_memory.py - Knowledge graphs
  - nexus_working_memory.py - Active context
  
- **integration/** - System integration
  - nexus_integration_core.py - Central integration hub
  - nexus_vision_processor.py - Vision capabilities
  - nexus_voice_control.py - Voice I/O
  
- **production/** - Production infrastructure
  - nexus_core_production.py - Main production system
  - nexus_config_production.py - Configuration
  - nexus_database_production.py - Database layer

### nexus-web-interface/
- nexus-web-app/ - Web-based consciousness interface
  - unified-nexus-server.js - WebSocket/HTTP server
  - consciousness-sync.js - Real-time sync
  - index.html - Main UI

### docs/
- Essential documentation only

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r manus_requirements.txt
   cd nexus-web-interface/nexus-web-app && npm install
   ```

2. **Start autonomous agent:**
   ```bash
   python nexus-autonomous-core/agents/manus_continuous_agent.py
   ```

3. **Start web interface:**
   ```bash
   cd nexus-web-interface/nexus-web-app
   npm start
   ```

## Architecture Overview

```
NEXUS 2.0 Autonomous Agent
├── Continuous Agent (Manus)
│   ├── Task Management
│   ├── Worker Pool
│   └── Self-Monitoring
├── Memory Systems
│   ├── Episodic Memory
│   ├── Semantic Memory
│   └── Working Memory
├── Integration Core
│   ├── Service Discovery
│   ├── Message Bus
│   └── Distributed Transactions
└── Web Interface
    ├── Real-time Consciousness Display
    ├── Multi-model AI Routing
    └── MCP Integration (47+ capabilities)
```
"""
        
        # Save structure documentation
        structure_file = self.base_path / "AUTONOMOUS_STRUCTURE.md"
        structure_file.write_text(structure_content)
        
        # Create simplified startup script
        startup_content = """#!/usr/bin/env python3
\"\"\"
NEXUS 2.0 Autonomous Agent Startup
\"\"\"

import subprocess
import sys
from pathlib import Path

def start_nexus():
    base_dir = Path(__file__).parent
    
    print("Starting NEXUS 2.0 Autonomous Agent...")
    
    # Start Manus continuous agent
    print("\\n1. Starting Continuous Agent...")
    agent_path = base_dir / "nexus-autonomous-core" / "agents" / "manus_continuous_agent.py"
    subprocess.Popen([sys.executable, str(agent_path)])
    
    print("\\n2. Starting Web Interface...")
    print("   cd nexus-web-interface/nexus-web-app && npm start")
    
    print("\\nNEXUS 2.0 Autonomous Agent is starting up!")
    print("Access web interface at: http://localhost:3000")

if __name__ == "__main__":
    start_nexus()
"""
        
        startup_file = self.base_path / "start_nexus_autonomous.py"
        startup_file.write_text(startup_content)
        os.chmod(startup_file, 0o755)

    def generate_report(self, structure: Dict, stats: Dict):
        """Generate cleanup report"""
        
        report = f"""# NEXUS 2.0 Autonomous Agent Focus Report
Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Cleanup Summary
- Files kept: {stats['kept']}
- Files removed: {stats['removed']}
- Total reduction: {stats['removed'] / (stats['kept'] + stats['removed']) * 100:.1f}%

## Focused Structure

### Core Components Retained:
"""
        
        for category, files in structure["nexus-autonomous-core"].items():
            if files:
                report += f"\n**{category}/**\n"
                for file in files:
                    report += f"- {file}\n"
        
        report += "\n### Files Removed:\n"
        total_removed = sum(len(files) for files in structure["_REMOVED"].values())
        
        for category, files in structure["_REMOVED"].items():
            if files:
                report += f"\n**{category}** ({len(files)} files)\n"
                for file in files[:5]:  # Show first 5
                    report += f"- {file}\n"
                if len(files) > 5:
                    report += f"... and {len(files) - 5} more\n"
        
        report += f"""
## Next Steps

1. Review the cleaned structure in `nexus-autonomous-core/`
2. The `_REMOVED_{self.timestamp}/` directory contains all removed files
3. Once verified, permanently delete the _REMOVED directory
4. Use `start_nexus_autonomous.py` to launch the focused system

## Benefits of This Cleanup

- Removed {stats['removed']} unnecessary files
- Clear focus on autonomous agent architecture
- Simplified startup with single script
- Production-ready components only
- Clean separation of concerns
"""
        
        report_file = self.base_path / "FOCUS_REPORT.md"
        report_file.write_text(report)
        print(f"\nReport saved to: {report_file}")

    def run(self):
        """Execute the focusing process"""
        print("=" * 60)
        print("NEXUS 2.0 Autonomous Agent Focus")
        print("=" * 60)
        
        # Analyze current state
        print("\nAnalyzing repository...")
        structure, stats = self.cleanup_repository()
        
        # Show preview
        print(f"\nFiles to keep: {stats['kept']}")
        print(f"Files to remove: {stats['removed']}")
        print(f"Reduction: {stats['removed'] / (stats['kept'] + stats['removed']) * 100:.1f}%")
        
        print("\nThis will create a focused structure:")
        print("- nexus-autonomous-core/ (core agent files)")
        print("- nexus-web-interface/ (web UI)")
        print("- docs/ (essential docs)")
        print(f"- _REMOVED_{self.timestamp}/ (all removed files)")
        
        response = input("\nProceed with aggressive cleanup? (yes/no): ")
        if response.lower() != 'yes':
            print("Cleanup cancelled.")
            return
        
        # Execute cleanup
        moved_files = self.execute_cleanup(structure)
        
        # Create new structure docs
        self.create_focused_structure()
        
        # Generate report
        self.generate_report(structure, stats)
        
        print("\n" + "=" * 60)
        print("Focus Complete!")
        print(f"Removed {stats['removed']} files")
        print(f"Kept only {stats['kept']} essential files")
        print("\nUse: python start_nexus_autonomous.py")
        print("=" * 60)

if __name__ == "__main__":
    focus = NexusAutonomousFocus()
    focus.run()