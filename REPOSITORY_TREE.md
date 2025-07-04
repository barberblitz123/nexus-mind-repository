# NEXUS Repository Tree Structure

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
