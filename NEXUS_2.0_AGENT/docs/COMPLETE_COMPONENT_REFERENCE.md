# NEXUS 2.0 AGENT - Complete Component Reference

## 📁 Folder Structure
```
/workspaces/nexus-mind-repository/NEXUS_2.0_AGENT/
├── core/               # Core system components
├── interfaces/         # User interface adapters
├── agents/            # Agent implementations
├── configs/           # Configuration files & user customizations
└── docs/              # Documentation
```

## 🔧 Core Components (`/core/`)

### 1. **nexus_stage_manager.py**
- **Purpose**: Manages multiple autonomous agents in windows (like macOS Stage Manager)
- **Key Classes**: 
  - `StageManager` - Main manager class
  - `AgentWindow` - Individual agent window representation
  - `AgentState` - Agent states (IDLE, WORKING, THINKING, etc.)
- **Features**:
  - Active stage (4 agents max)
  - Side stage for inactive agents
  - Agent grouping
  - Window arrangements (cascade/grid)
  - Session save/load

### 2. **nexus_desktop_manager.py**
- **Purpose**: Chat and preview window management
- **Key Classes**:
  - `DesktopManager` - Main desktop environment
  - `ChatMessage` - Chat message structure
  - `PreviewPane` - Preview window for code/output
  - `PreviewType` - Types of preview content
- **Features**:
  - Chat interface
  - Multiple preview panes
  - Command system
  - Workspace persistence

### 3. **nexus_integrated_workspace.py** ⭐ MAIN ENTRY POINT
- **Purpose**: Complete integrated terminal UI combining Stage + Desktop managers
- **Launch**: `python nexus_integrated_workspace.py`
- **Features**:
  - Visual agent windows
  - Integrated chat
  - Preview tabs
  - Command palette
  - Keyboard shortcuts

### 4. **nexus_autonomous_agent.py**
- **Purpose**: Self-directed autonomous MANUS agent
- **Key Classes**:
  - `AutonomousMANUS` - Main agent class
  - `AgentCapability` - Agent skills/abilities
  - `GoalReasoner` - Goal planning system
- **Features**:
  - Self-improvement
  - Goal reasoning
  - Task generation
  - Memory integration

### 5. **nexus_agent_orchestrator_advanced.py**
- **Purpose**: Manages multiple agents working together
- **Features**:
  - Dynamic agent scaling
  - Fault tolerance
  - Load balancing
  - Health monitoring
  - Resource management

### 6. **nexus_terminal_ui_advanced.py**
- **Purpose**: VS Code-like terminal interface
- **Features**:
  - File explorer
  - Code editor
  - Terminal sessions
  - Git integration
  - Debug console

### 7. **nexus_terminal_app.py**
- **Purpose**: Simpler self-contained terminal UI
- **Features**:
  - 6 main tabs
  - Basic functionality
  - No external dependencies

### 8. **nexus_integrated_terminal.py**
- **Purpose**: Advanced terminal session management
- **Features**:
  - Multiple terminal types (local, SSH, Docker)
  - Session persistence
  - Command history
  - Environment management

### 9. **launch_nexus_agent_system.py**
- **Purpose**: Launcher script for individual components
- **Usage**: `python launch_nexus_agent_system.py`
- **Options**:
  1. Terminal UI Advanced
  2. Terminal UI Production
  3. Autonomous Agent
  4. Agent Orchestrator
  5. Full System

## 🌐 Interface Components (`/interfaces/`)

### 1. **nexus_unified_interface.py**
- **Purpose**: Adaptive interface that works on any device
- **Features**:
  - Auto-detects environment (terminal/web/mobile)
  - Device-specific UI selection
  - User file integration support
- **Classes**:
  - `UnifiedNexusLauncher` - Main launcher
  - `TerminalInterface` - Desktop terminal UI
  - `WebInterface` - Browser-based UI
  - `MobileInterface` - Mobile-optimized UI

### 2. **nexus_html_tab_integrator.py** (if present)
- **Purpose**: Integrate HTML-based custom tabs
- **Usage**: For adding web-based components to terminal UI

## 📝 Configuration (`/configs/`)

### Purpose
- Store user customizations
- Custom agent definitions
- Interface configurations
- Your uploaded files go here

### Adding Your Files
```bash
# Copy your files here:
cp ~/Downloads/stage_manager_config.json /workspaces/nexus-mind-repository/NEXUS_2.0_AGENT/configs/
cp ~/Downloads/desktop_manager_config.json /workspaces/nexus-mind-repository/NEXUS_2.0_AGENT/configs/
```

## 🚀 Quick Launch Commands

### Full Integrated System (Recommended)
```bash
cd /workspaces/nexus-mind-repository/NEXUS_2.0_AGENT/core
python nexus_integrated_workspace.py
```

### Individual Components
```bash
# Stage Manager only
python nexus_stage_manager.py

# Desktop Manager only
python nexus_desktop_manager.py

# Autonomous Agent
python nexus_autonomous_agent.py

# Terminal UI
python nexus_terminal_ui_advanced.py

# Unified Interface (any device)
cd ../interfaces
python nexus_unified_interface.py
```

## 🔌 Integration Points

### To Add Custom Features

1. **Custom Agent Types**:
   - Edit `AGENT_TYPES` in `nexus_stage_manager.py`
   - Add new agent classes in `/agents/`

2. **Custom Preview Types**:
   - Add to `PreviewType` enum in `nexus_desktop_manager.py`
   - Register handlers with `register_preview_handler()`

3. **Custom Commands**:
   - Add to `execute_command()` in `nexus_desktop_manager.py`
   - Format: `command subcommand arguments`

4. **Custom UI Themes**:
   - Edit CSS in `nexus_integrated_workspace.py`
   - Modify color schemes and layouts

## 📋 Key Concepts

### Stage Manager
- **Active Stage**: Currently visible agents (max 4)
- **Side Stage**: Inactive but ready agents
- **Minimized**: Hidden agents
- **Stage Groups**: Named collections of agents

### Desktop Manager
- **Chat Panel**: Communication with agents
- **Preview Panes**: View code, output, docs
- **Command System**: Control via text commands
- **Workspace**: Saveable configuration

### Integration
- Stage Manager provides agent windows
- Desktop Manager provides chat/preview
- Integrated Workspace combines both visually

## 🛠️ Customization Examples

### Add a New Agent Type
```python
# In nexus_stage_manager.py
AGENT_TYPES["analyzer"] = "Code Analysis Agent"

# Create the agent
analyzer = stage_manager.create_agent_window("Analyzer", "analyzer")
```

### Add a Custom Preview
```python
# In nexus_desktop_manager.py
desktop_manager.create_preview_pane("Results", PreviewType.DATA)
desktop_manager.update_preview_content(pane_id, analysis_results)
```

### Create Agent Group
```python
# Group agents for a task
stage_manager.create_stage_group("backend_team", [api_agent.id, db_agent.id, test_agent.id])
stage_manager.activate_stage_group("backend_team")
```

## 📚 References for Enhancement

When you want to enhance specific features, reference these files:

1. **Agent Behavior**: `nexus_autonomous_agent.py`
2. **Window Management**: `nexus_stage_manager.py`
3. **Chat/Preview**: `nexus_desktop_manager.py`
4. **UI Layout**: `nexus_integrated_workspace.py`
5. **Device Adaptation**: `nexus_unified_interface.py`
6. **Terminal Features**: `nexus_terminal_ui_advanced.py`

---

This is the complete reference for NEXUS 2.0 AGENT. All components are in the `/workspaces/nexus-mind-repository/NEXUS_2.0_AGENT/` folder.