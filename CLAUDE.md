# CLAUDE.md - NEXUS 2.0 Session Context

## Current State (Updated: 2025-07-03)

### What is NEXUS 2.0?
NEXUS 2.0 is a **Terminal-Based Multi-Agent Development Environment**:
- Multiple AI agents working in parallel (like Claude's multi-agent system)
- Stage Manager for agent windows
- Desktop Manager for chat and preview
- Everything interconnected in one terminal UI
- NOT a web browser application!

### Repository Status
- **Total Files**: Organized from 200+ files into clean structure
- **Solution**: Repository is now organized with numbered directories
- **Main System**: Located in `01_NEXUS_2.0_AGENT/`

### 🎯 THE REAL NEXUS 2.0 AGENT SYSTEM

#### Primary Interface: Terminal-Based Agent System
- **Location**: `01_NEXUS_2.0_AGENT/core/`
- **Main Entry**: `python nexus_integrated_workspace.py`
- **Type**: Terminal UI (like vim, tmux, htop)
- **Features**: Multiple AI agents, Stage Manager, Desktop Manager, all interconnected
- **NOT**: A web browser interface!

#### How to Launch THE REAL NEXUS 2.0:
```bash
# SIMPLEST - Launch everything with one command:
cd /workspaces/nexus-mind-repository/01_NEXUS_2.0_AGENT
python launch_real_nexus.py

# Choose option 3 for both Terminal + Web interfaces
# Agents will execute REAL code, not simulations!
```

### 📁 Repository Organization

The repository is now organized into numbered directories:
```
01_NEXUS_2.0_AGENT/      ← THE REAL NEXUS 2.0 (Terminal-based agents)
02_WEB_INTERFACES/       ← Web browser interfaces (different projects)
03_PYTHON_MODULES/       ← Organized Python code
04_CONFIGURATIONS/       ← Config files
05_DOCUMENTATION/        ← All docs
06_TESTS_AND_DEMOS/      ← Tests and demos
07_SCRIPTS_AND_TOOLS/    ← Scripts
08_DATA_AND_CACHE/       ← Data storage
09_BACKUPS/              ← Backups
10_ARCHIVE/              ← Old/deprecated code
```

### Recent Work
- ✅ Created Stage Manager + Desktop Manager system
- ✅ Built interconnected terminal-based agent system
- ✅ Organized entire repository into clean structure
- ✅ Created clear documentation and launch guides
- ✅ Implemented task orchestration for automatic agent creation
- ✅ Fixed command repetition bug in task orchestrator
- ✅ Created Tab System with 5 focused tabs
- ✅ Integrated comprehensive Debug Tab (6th tab) with logging system!
- ✅ Created Web Version with same Tab System!
- ✅ Connected Web Interface to REAL agent system!
- ✅ **NEW: Implemented REAL agent execution (not simulation)**
- ✅ **NEW: Added comprehensive logging with easy extraction**
- ✅ **NEW: Full auditing system for all agent actions**
- ✅ **Agents now execute actual code via subprocess!**
- ✅ **LATEST: YouTube scraping with self-enhancement capability!**
- ✅ **LATEST: Agents recognize missing capabilities and suggest solutions!**

### 🧠 NEW: Self-Enhancement Capability

#### 🔧 What is Self-Enhancement?
When NEXUS agents encounter tasks they can't complete, they now:
- **Recognize** what capabilities they're missing
- **Identify** specific packages or tools needed
- **Provide** exact installation instructions
- **Track** success/failure rates for improvement

#### 🎥 YouTube Scraping Example
```bash
# Test the self-enhancement capability:
cd 01_NEXUS_2.0_AGENT
python demo_youtube_scraping.py

# When asked to scrape transcripts without youtube-transcript-api:
# Agent responds: "I need to install youtube-transcript-api to extract transcripts"
# Provides: pip install youtube-transcript-api
```

#### 🚀 How It Works
1. User requests: "Scrape this YouTube video with transcript and comments"
2. Agent checks its capabilities
3. If missing: Creates "YouTube Enhancement Agent" in Stage Manager
4. Shows exactly what's needed and how to get it
5. After enhancement: Can complete the task!

### 🌐 Web + Terminal Versions - BOTH REAL!

#### 🚀 REAL Agent Execution (Not Simulation!)
- **Agents execute actual Python code** via subprocess
- **Run real shell commands** with security filters
- **Create/modify real files** on the filesystem
- **Comprehensive logging** to `nexus_logs/`
- **Easy log export** for analysis
- **Full audit trail** of all actions

#### 🎯 Launch Options
1. **Everything (Recommended)**: `python launch_real_nexus.py`
2. **Terminal Only**: `cd core && python nexus_tabbed_interface.py`
3. **Web Only**: `cd interfaces && ./launch_web_interface.sh`
4. **Demo**: `python demo_real_execution.py`

#### 📋 Key Files
- `nexus_connector.py` - REAL agent execution engine with YouTube support
- `nexus_logger.py` - Comprehensive logging system
- `launch_real_nexus.py` - Simple unified launcher
- `REAL_NEXUS_README.md` - Complete documentation
- `nexus_youtube_scraper_enhanced.py` - YouTube scraper with self-enhancement
- `demo_youtube_scraping.py` - Self-enhancement demonstration

### Key Components We Built

1. **nexus_stage_manager.py** - Manages multiple agent windows
2. **nexus_desktop_manager.py** - Chat and preview interface
3. **nexus_integrated_workspace.py** - Complete terminal UI
4. **nexus_task_orchestrator.py** - Connects everything together
5. **nexus_tabbed_interface.py** - Clean 6-tab interface
6. **nexus_logger.py** - Comprehensive logging with colors and file output
7. **nexus_debug_tab.py** - Debug tab with live logs, activity monitor, error tracker
8. **nexus_connector.py** - Bridges web interface to REAL agent execution
9. **launch_real_nexus.py** - Simple launcher for the complete system
10. **demo_real_execution.py** - Demonstrates real code execution
11. **nexus_youtube_scraper_enhanced.py** - NEW! YouTube scraper with self-enhancement
12. **nexus_youtube_connector.py** - NEW! Connects YouTube scraping to NEXUS system
13. **demo_youtube_scraping.py** - NEW! Demonstrates self-enhancement capability

### Session Recovery Tips
- Always check this file first when resuming
- **EASIEST LAUNCH**: `cd 01_NEXUS_2.0_AGENT && python launch_real_nexus.py`
- Read `01_NEXUS_2.0_AGENT/REAL_NEXUS_README.md` for complete guide
- The system now executes REAL code, not simulations!
- Logs are saved to `nexus_logs/` with easy export options

### ⚠️ Common Confusion to Avoid

**Web Interfaces** (in `02_WEB_INTERFACES/`):
- Browser-based
- Single page applications
- Like ChatGPT or Claude web interface
- NOT the real NEXUS 2.0 Agent system

**NEXUS 2.0 Agent** (in `01_NEXUS_2.0_AGENT/`):
- Terminal-based
- Multiple AI agents working together
- Visual representation of agents in windows
- Like having multiple Claudes working together
- THIS is the real NEXUS 2.0!