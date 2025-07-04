# ⚠️ NEXUS Stage + Desktop Manager - Separate Application

## 🎯 IMPORTANT: This is a STANDALONE Application

This folder contains a **completely separate application** that implements the Stage Manager + Desktop Manager concept.

## 📁 Application Location
```
/workspaces/nexus-mind-repository/NEXUS_STAGE_DESKTOP_APP/
```

## 🔑 Key Points

1. **This is NOT part of the main NEXUS 2.0 system**
2. **It's a self-contained terminal application**
3. **Has its own dependencies and configuration**
4. **Can run independently without other NEXUS components**

## 🚀 To Run This Application

```bash
cd NEXUS_STAGE_DESKTOP_APP
./install_and_run.sh
```

Or manually:
```bash
cd NEXUS_STAGE_DESKTOP_APP
pip install -r requirements.txt
python launch_interconnected_demo.py
```

## 📋 What's in This Application

- **Stage Manager**: Window management for AI agents
- **Desktop Manager**: Chat and preview interface
- **Task Orchestrator**: Automatic agent creation from commands
- **Integrated Workspace**: Complete terminal UI

## 🔧 Application Files

```
NEXUS_STAGE_DESKTOP_APP/
├── core/                         # Application core
│   ├── nexus_stage_manager.py    # Window management
│   ├── nexus_desktop_manager.py  # Chat/preview
│   ├── nexus_integrated_workspace.py # Full UI
│   ├── nexus_task_orchestrator.py # Task automation
│   └── agent_base.py            # Base agent (no external deps)
├── launch_interconnected_demo.py # Main launcher
├── requirements.txt             # This app's dependencies
├── APP_MANIFEST.json           # Application manifest
└── README.md                   # Application documentation
```

## ❌ What This is NOT

- NOT the web interface (that's in 02_WEB_INTERFACES/)
- NOT the NEXUS 2.0 Agent system (that's in 01_NEXUS_2.0_AGENT/)
- NOT dependent on other NEXUS modules
- NOT a web application (it's terminal-based)

## ✅ What This IS

- A standalone terminal application
- A visual implementation of multi-agent collaboration
- A complete Stage + Desktop manager system
- An independent project that can be run anywhere

---

**Remember: This is its own separate application with its own functionality!**