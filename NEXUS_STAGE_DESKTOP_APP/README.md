# NEXUS Stage + Desktop Manager Application

## 🎯 What This Is

This is a **standalone terminal application** that implements:
- **Stage Manager**: Multiple AI agent windows (like macOS Stage Manager)
- **Desktop Manager**: Chat interface and preview panes
- **Task Orchestrator**: Automatically creates agents from your commands
- **Interconnected Workspace**: Everything working together

## 📁 This Application's Structure

```
NEXUS_STAGE_DESKTOP_APP/
├── core/                           # Core application components
│   ├── nexus_stage_manager.py      # Agent window management
│   ├── nexus_desktop_manager.py    # Chat and preview management
│   ├── nexus_integrated_workspace.py # Complete UI combining both
│   └── nexus_task_orchestrator.py  # Task → Agent automation
├── docs/                           # Documentation
│   └── HOW_IT_WORKS.md            # Detailed explanation
├── configs/                        # Configuration files
├── scripts/                        # Helper scripts
├── tests/                          # Test files
├── launch_interconnected_demo.py   # Main launcher
└── README.md                       # This file
```

## 🚀 Quick Start

### Launch the Complete Application
```bash
cd NEXUS_STAGE_DESKTOP_APP
python launch_interconnected_demo.py
# Choose option 1 for full experience
```

### Or Launch Components Directly

#### Full Integrated UI
```bash
python core/nexus_integrated_workspace.py
```

#### Just Stage Manager
```bash
python core/nexus_stage_manager.py
```

#### Just Desktop Manager
```bash
python core/nexus_desktop_manager.py
```

## 💡 How It Works

1. **You type commands in chat**
   - "Build a web scraper"
   - "Analyze this code"
   - "Create a REST API"

2. **System automatically creates agent windows**
   - Developer Agent
   - Research Agent
   - Test Agent
   - etc.

3. **All agents work simultaneously**
   - Share memory
   - Communicate via chat
   - Update preview panes

4. **Everything in one terminal interface**
   - No web browser needed
   - Pure terminal UI
   - Real-time updates

## 🔧 Key Features

### Stage Manager
- Multiple agent windows
- Active stage (visible agents)
- Side stage (background agents)
- Window arrangements (grid/cascade)
- Agent grouping

### Desktop Manager
- Chat interface
- Multiple preview panes
- Command system
- Workspace save/load
- Terminal output routing

### Task Orchestrator
- Automatic agent creation
- Task breakdown
- Progress tracking
- Inter-agent communication

### Interconnected Design
- Shared memory between agents
- Unified terminal session
- Synchronized state
- Real-time updates

## 📋 Commands

### Chat Commands
- `/stage arrange` - Arrange agent windows in grid
- `/stage cascade` - Cascade agent windows
- `/stage focus <agent_id>` - Focus specific agent
- `/preview open <type> <title>` - Open preview pane
- `/workspace save <filename>` - Save current setup

### Keyboard Shortcuts
- `Ctrl+Tab` - Next agent
- `Ctrl+Shift+Tab` - Previous agent
- `Ctrl+N` - New agent
- `Ctrl+P` - Command palette
- `Ctrl+S` - Save workspace
- `F1` - Help

## 🎯 Use Cases

### Development Task
```
You: "Create a Python web API with authentication"
→ Creates: Developer, Security, Database, Test agents
→ All work together to build complete API
```

### Research Task
```
You: "Research best practices for web scraping"
→ Creates: Research, Documentation agents
→ Compile findings and create report
```

### Analysis Task
```
You: "Analyze this codebase for security issues"
→ Creates: Security, Code Review, Report agents
→ Scan code and generate security report
```

## 🔌 Requirements

- Python 3.8+
- Terminal with Unicode support
- Dependencies:
  ```bash
  pip install textual rich psutil aiofiles
  ```

## ⚙️ Configuration

Configuration files go in `configs/`:
- `stage_config.json` - Stage Manager settings
- `desktop_config.json` - Desktop Manager settings
- `agents_config.json` - Agent type definitions

## 🧪 Testing

Run tests:
```bash
python -m pytest tests/
```

## 📝 Notes

- This is a **standalone application**
- **Not** a web interface
- **Not** dependent on other NEXUS components
- Can be run independently
- Terminal-based UI only

---

**This is the Stage + Desktop Manager system as its own complete application!**