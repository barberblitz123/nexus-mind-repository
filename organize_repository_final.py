#!/usr/bin/env python3
"""
NEXUS Repository Final Organization Script
Creates a clean tree structure with all files properly categorized
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import json

class RepositoryOrganizer:
    def __init__(self):
        self.base_path = Path(".")
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.moved_files = []
        
        # Define the new structure
        self.structure = {
            "01_NEXUS_2.0_AGENT": "The REAL NEXUS 2.0 system (keep as is)",
            "02_WEB_INTERFACES": {
                "active": ["nexus-web-app"],
                "experimental": ["nexus-minimal", "nexus-unified-app"],
                "deprecated": ["nexus-consciousness-live"]
            },
            "03_PYTHON_MODULES": {
                "agents": ["nexus_agent_*.py", "nexus_autonomous_*.py", "nexus_*orchestrator*.py"],
                "memory": ["nexus_memory_*.py", "nexus_episodic*.py", "nexus_semantic*.py", "nexus_working*.py", "*mem0*.py"],
                "scrapers": ["nexus_scraper*.py", "nexus_web_scraper*.py", "*scraper*.py"],
                "ui_terminal": ["nexus_terminal*.py", "nexus_ui_*.py", "nexus_integrated_terminal.py"],
                "integrations": ["nexus_integration*.py", "manus_*.py", "*_integration.py"],
                "core_systems": ["nexus_*_production.py", "nexus_config*.py", "nexus_database*.py", "nexus_startup*.py"],
                "consciousness": ["nexus_consciousness*.py", "nexus_dna*.py", "nexus_essence*.py", "nexus_real_*.py"],
                "processors": ["nexus_voice*.py", "nexus_vision*.py", "nexus_audio*.py", "*processor*.py"],
                "launchers": ["launch_*.py", "start_*.py", "run_*.py", "nexus_launcher*.py"],
                "utilities": ["nexus_*_analyzer.py", "nexus_*_scanner.py", "nexus_*_generator.py", "fix_*.py", "setup_*.py"]
            },
            "04_CONFIGURATIONS": {
                "yaml": ["*.yaml", "*.yml"],
                "json": ["*.json"],
                "requirements": ["*requirements*.txt"],
                "docker": ["docker-compose*.yml", "Dockerfile*"]
            },
            "05_DOCUMENTATION": {
                "nexus_docs": ["NEXUS_*.md"],
                "guides": ["*_GUIDE.md", "*_README.md", "HOW_TO_*.md"],
                "general": ["README.md", "SECURITY.md", "TROUBLESHOOTING.md", "*.md"]
            },
            "06_TESTS_AND_DEMOS": {
                "tests": ["test_*.py", "*_test.py"],
                "demos": ["demo_*.py", "*_demo.py"]
            },
            "07_SCRIPTS_AND_TOOLS": {
                "shell": ["*.sh"],
                "python": ["organize_*.py", "cleanup_*.py"]
            },
            "08_DATA_AND_CACHE": {
                "databases": ["*.db"],
                "cache": ["nexus_scraper_cache", "__pycache__"],
                "logs": ["logs", "nexus_logs", "*.log"],
                "data": ["data", "uploads", "nexus_core", "nexus_mem0", "nexus_dna_mem0"]
            },
            "09_BACKUPS": ["nexus_backup_*", "BACKUP_*"],
            "10_ARCHIVE": "Keep existing ARCHIVE folder"
        }

    def create_directories(self):
        """Create the new directory structure"""
        print("Creating new directory structure...")
        
        for main_dir, content in self.structure.items():
            if isinstance(content, str):
                continue  # Skip folders we're keeping as-is
                
            main_path = self.base_path / main_dir
            main_path.mkdir(exist_ok=True)
            
            if isinstance(content, dict):
                for subdir in content:
                    subpath = main_path / subdir
                    subpath.mkdir(exist_ok=True)

    def move_web_interfaces(self):
        """Move web interfaces to organized structure"""
        print("\n📁 Organizing web interfaces...")
        
        web_dir = self.base_path / "02_WEB_INTERFACES"
        
        # Move interfaces based on category
        moves = {
            "active": ["nexus-web-app"],
            "experimental": ["nexus-minimal", "nexus-unified-app"],
            "deprecated": ["nexus-consciousness-live"]
        }
        
        for category, interfaces in moves.items():
            for interface in interfaces:
                source = self.base_path / interface
                if source.exists() and source.is_dir():
                    dest = web_dir / category / interface
                    if not dest.exists():
                        print(f"  Moving {interface} to {category}/")
                        shutil.move(str(source), str(dest))
                        self.moved_files.append((interface, f"02_WEB_INTERFACES/{category}/"))

    def move_python_modules(self):
        """Move Python files to appropriate categories"""
        print("\n🐍 Organizing Python modules...")
        
        modules_dir = self.base_path / "03_PYTHON_MODULES"
        
        # Process each category
        for category, patterns in self.structure["03_PYTHON_MODULES"].items():
            category_dir = modules_dir / category
            
            for pattern in patterns:
                for file in self.base_path.glob(pattern):
                    if file.is_file() and file.parent == self.base_path:
                        dest = category_dir / file.name
                        if not dest.exists():
                            print(f"  Moving {file.name} to {category}/")
                            shutil.move(str(file), str(dest))
                            self.moved_files.append((file.name, f"03_PYTHON_MODULES/{category}/"))

    def move_configurations(self):
        """Move configuration files"""
        print("\n⚙️  Organizing configuration files...")
        
        config_dir = self.base_path / "04_CONFIGURATIONS"
        
        for category, patterns in self.structure["04_CONFIGURATIONS"].items():
            category_dir = config_dir / category
            
            for pattern in patterns:
                for file in self.base_path.glob(pattern):
                    if file.is_file() and file.parent == self.base_path:
                        # Skip special files
                        if file.name in ["package.json", "package-lock.json"]:
                            continue
                            
                        dest = category_dir / file.name
                        if not dest.exists():
                            print(f"  Moving {file.name} to {category}/")
                            shutil.move(str(file), str(dest))
                            self.moved_files.append((file.name, f"04_CONFIGURATIONS/{category}/"))

    def move_documentation(self):
        """Move documentation files"""
        print("\n📚 Organizing documentation...")
        
        docs_dir = self.base_path / "05_DOCUMENTATION"
        
        # Process each category
        for category, patterns in self.structure["05_DOCUMENTATION"].items():
            category_dir = docs_dir / category
            
            for pattern in patterns:
                for file in self.base_path.glob(pattern):
                    if file.is_file() and file.parent == self.base_path:
                        # Keep essential docs in root
                        if file.name in ["README.md", "CLAUDE.md", "SESSION_RECOVERY.md"]:
                            continue
                            
                        dest = category_dir / file.name
                        if not dest.exists():
                            print(f"  Moving {file.name} to {category}/")
                            shutil.move(str(file), str(dest))
                            self.moved_files.append((file.name, f"05_DOCUMENTATION/{category}/"))

    def move_tests_and_demos(self):
        """Move test and demo files"""
        print("\n🧪 Organizing tests and demos...")
        
        test_dir = self.base_path / "06_TESTS_AND_DEMOS"
        
        for category, patterns in self.structure["06_TESTS_AND_DEMOS"].items():
            category_dir = test_dir / category
            
            for pattern in patterns:
                for file in self.base_path.glob(pattern):
                    if file.is_file() and file.parent == self.base_path:
                        dest = category_dir / file.name
                        if not dest.exists():
                            print(f"  Moving {file.name} to {category}/")
                            shutil.move(str(file), str(dest))
                            self.moved_files.append((file.name, f"06_TESTS_AND_DEMOS/{category}/"))

    def move_active_nexus_contents(self):
        """Move contents from ACTIVE_NEXUS_2.0 to proper locations"""
        print("\n📦 Reorganizing ACTIVE_NEXUS_2.0 contents...")
        
        active_dir = self.base_path / "ACTIVE_NEXUS_2.0"
        if not active_dir.exists():
            return
            
        # Move core Python files
        core_dir = active_dir / "core"
        if core_dir.exists():
            for file in core_dir.glob("*.py"):
                # Determine category
                category = self._categorize_python_file(file.name)
                if category:
                    dest_dir = self.base_path / "03_PYTHON_MODULES" / category
                    dest = dest_dir / file.name
                    if not dest.exists():
                        print(f"  Moving {file.name} from ACTIVE_NEXUS_2.0/core to PYTHON_MODULES/{category}/")
                        shutil.move(str(file), str(dest))
                        self.moved_files.append((file.name, f"03_PYTHON_MODULES/{category}/"))
        
        # Move web apps
        web_apps_dir = active_dir / "web_apps"
        if web_apps_dir.exists():
            for app_dir in web_apps_dir.iterdir():
                if app_dir.is_dir():
                    category = "active" if "web-app" in app_dir.name else "experimental"
                    dest = self.base_path / "02_WEB_INTERFACES" / category / app_dir.name
                    if not dest.exists():
                        print(f"  Moving {app_dir.name} from ACTIVE_NEXUS_2.0 to WEB_INTERFACES/{category}/")
                        shutil.move(str(app_dir), str(dest))
                        self.moved_files.append((app_dir.name, f"02_WEB_INTERFACES/{category}/"))

    def _categorize_python_file(self, filename):
        """Determine which category a Python file belongs to"""
        categories = {
            "agents": ["agent", "autonomous", "orchestrator"],
            "memory": ["memory", "episodic", "semantic", "working", "mem0"],
            "scrapers": ["scraper", "web_scraper"],
            "ui_terminal": ["terminal", "ui_"],
            "integrations": ["integration", "manus_"],
            "core_systems": ["_production", "config", "database", "startup"],
            "consciousness": ["consciousness", "dna", "essence"],
            "processors": ["voice", "vision", "audio", "processor"],
            "launchers": ["launch_", "start_", "run_"],
            "utilities": ["analyzer", "scanner", "generator", "fix_", "setup_"]
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in filename.lower():
                    return category
        
        return "utilities"  # Default category

    def create_tree_documentation(self):
        """Create comprehensive tree documentation"""
        print("\n📝 Creating tree documentation...")
        
        tree_doc = """# NEXUS Repository Tree Structure

## 🌳 Complete Organization Tree

```
nexus-mind-repository/
│
├── 01_NEXUS_2.0_AGENT/          # ⭐ The REAL NEXUS 2.0 System
│   ├── core/                    # Core agent components
│   ├── interfaces/              # Unified interfaces
│   ├── agents/                  # Agent implementations
│   ├── configs/                 # User configurations
│   └── docs/                    # System documentation
│
├── 02_WEB_INTERFACES/           # 🌐 All Web UIs
│   ├── active/                  # Currently used
│   │   └── nexus-web-app/      # Main webinar interface
│   ├── experimental/            # Test interfaces
│   │   ├── nexus-minimal/      # Minimal implementation
│   │   └── nexus-unified-app/  # Advanced unified UI
│   └── deprecated/              # Old interfaces
│       └── nexus-consciousness-live/
│
├── 03_PYTHON_MODULES/           # 🐍 Organized Python Code
│   ├── agents/                  # Autonomous agents
│   ├── memory/                  # Memory systems
│   ├── scrapers/                # Web scraping
│   ├── ui_terminal/             # Terminal interfaces
│   ├── integrations/            # System integrations
│   ├── core_systems/            # Production core
│   ├── consciousness/           # AI consciousness
│   ├── processors/              # Vision/voice processing
│   ├── launchers/               # Entry points
│   └── utilities/               # Helper tools
│
├── 04_CONFIGURATIONS/           # ⚙️  Config Files
│   ├── yaml/                    # YAML configs
│   ├── json/                    # JSON configs
│   ├── requirements/            # Python requirements
│   └── docker/                  # Docker configs
│
├── 05_DOCUMENTATION/            # 📚 All Documentation
│   ├── nexus_docs/              # NEXUS-specific docs
│   ├── guides/                  # How-to guides
│   └── general/                 # General docs
│
├── 06_TESTS_AND_DEMOS/          # 🧪 Tests & Demos
│   ├── tests/                   # Test files
│   └── demos/                   # Demo files
│
├── 07_SCRIPTS_AND_TOOLS/        # 🛠️  Scripts
│   ├── shell/                   # Shell scripts
│   └── python/                  # Python scripts
│
├── 08_DATA_AND_CACHE/           # 💾 Data Storage
│   ├── databases/               # Database files
│   ├── cache/                   # Cache directories
│   ├── logs/                    # Log files
│   └── data/                    # Data directories
│
├── 09_BACKUPS/                  # 💼 Backups
│
├── 10_ARCHIVE/                  # 📦 Archived/Old Files
│
├── README.md                    # Main readme
├── CLAUDE.md                    # Session context
├── SESSION_RECOVERY.md          # Recovery guide
└── REPOSITORY_MAP.md            # This file
```

## 🔗 System Relationships

### NEXUS 2.0 Agent System
```
01_NEXUS_2.0_AGENT/
    ├── Uses → 03_PYTHON_MODULES/agents/
    ├── Uses → 03_PYTHON_MODULES/ui_terminal/
    └── Config → 04_CONFIGURATIONS/
```

### Web Interfaces
```
02_WEB_INTERFACES/active/nexus-web-app/
    ├── Backend → 03_PYTHON_MODULES/interfaces/
    ├── Config → 04_CONFIGURATIONS/json/
    └── Deployment → 04_CONFIGURATIONS/docker/
```

### Python Module Dependencies
```
03_PYTHON_MODULES/
    ├── core_systems/ → Provides base for all
    ├── integrations/ → Connects components
    ├── agents/ → Uses memory/, processors/
    └── interfaces/ → Uses all modules
```

## 📍 Quick Navigation

- **Want the REAL NEXUS 2.0?** → `01_NEXUS_2.0_AGENT/`
- **Looking for web UI?** → `02_WEB_INTERFACES/active/`
- **Need a Python module?** → `03_PYTHON_MODULES/`
- **Configuration files?** → `04_CONFIGURATIONS/`
- **Documentation?** → `05_DOCUMENTATION/`

## 🚀 Entry Points

1. **NEXUS 2.0 Agent System**: `01_NEXUS_2.0_AGENT/core/nexus_integrated_workspace.py`
2. **Web Interface**: `02_WEB_INTERFACES/active/nexus-web-app/`
3. **Python API**: `03_PYTHON_MODULES/interfaces/nexus_webinar_interface.py`
4. **MANUS Agent**: `03_PYTHON_MODULES/integrations/manus_continuous_agent.py`
"""
        
        with open("REPOSITORY_TREE.md", "w") as f:
            f.write(tree_doc)
            
        print("  Created REPOSITORY_TREE.md")

    def create_migration_guide(self):
        """Create a guide for updating imports after reorganization"""
        guide = """# Migration Guide After Repository Organization

## Import Path Updates

After reorganization, update your imports as follows:

### Old → New Import Paths

```python
# Agents
from nexus_autonomous_agent import Agent
→ from PYTHON_MODULES.agents.nexus_autonomous_agent import Agent

# Memory
from nexus_memory_core import Memory
→ from PYTHON_MODULES.memory.nexus_memory_core import Memory

# Terminal UI
from nexus_terminal_ui_advanced import UI
→ from PYTHON_MODULES.ui_terminal.nexus_terminal_ui_advanced import UI

# Integrations
from nexus_integration_core import Integration
→ from PYTHON_MODULES.integrations.nexus_integration_core import Integration
```

## Quick Fix Script

Run this to update imports automatically:
```bash
python update_imports.py
```

## File Locations

All files have been moved to organized directories:
"""
        
        # Add moved files list
        for old, new in self.moved_files:
            guide += f"\n- {old} → {new}"
            
        with open("MIGRATION_GUIDE.md", "w") as f:
            f.write(guide)

    def run(self):
        """Execute the complete organization"""
        print("=" * 60)
        print("NEXUS Repository Final Organization")
        print("=" * 60)
        
        # Create directories
        self.create_directories()
        
        # Move files by category
        self.move_web_interfaces()
        self.move_python_modules()
        self.move_configurations()
        self.move_documentation()
        self.move_tests_and_demos()
        self.move_active_nexus_contents()
        
        # Create documentation
        self.create_tree_documentation()
        self.create_migration_guide()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"✅ Organization Complete!")
        print(f"Files moved: {len(self.moved_files)}")
        print(f"\nCreated:")
        print("- REPOSITORY_TREE.md - Complete tree structure")
        print("- MIGRATION_GUIDE.md - Import update guide")
        print("\nThe repository is now cleanly organized!")
        print("=" * 60)

if __name__ == "__main__":
    organizer = RepositoryOrganizer()
    organizer.run()