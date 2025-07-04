# NEXUS 2.0 Python Modules

This directory contains all Python modules organized by functionality. The modules have been categorized to make the codebase more maintainable and easier to understand.

## Directory Structure

```
PYTHON_MODULES/
├── agents/          # Agent-related modules (autonomous, orchestrator, etc.)
├── consciousness/   # Consciousness simulation modules
├── core_systems/    # Core production modules (config, database, startup)
├── integrations/    # Integration modules (MANUS integration, etc.)
├── interfaces/      # User interfaces (webinar, web interfaces)
├── launchers/       # System launchers and entry points
├── memory/          # Memory systems (episodic, semantic, working)
├── plugins/         # Plugin system modules
├── processors/      # Processing modules (vision, voice, etc.)
├── scrapers/        # Web scraping modules
├── ui_terminal/     # Terminal UI modules
└── utilities/       # Utility modules (analyzers, generators, etc.)
```

## Quick Start

To use modules from this organized structure:

```python
# Example imports
from PYTHON_MODULES.agents import nexus_autonomous_agent
from PYTHON_MODULES.memory import nexus_memory_core
from PYTHON_MODULES.interfaces import nexus_webinar_interface
```

## Module Categories

### 1. Agents (3 modules)
- Autonomous agents with goal-directed behavior
- Agent orchestration and coordination
- Continuous learning agents

### 2. Memory (6 modules)
- Core memory management
- Episodic, semantic, and working memory
- Mem0 integration for persistence

### 3. Scrapers (3 modules)
- Web scraping with stealth capabilities
- Proxy management
- Content extraction

### 4. UI Terminal (5 modules)
- Terminal-based user interfaces
- Desktop and window management
- Integrated terminal features

### 5. Integrations (6 modules)
- MANUS-NEXUS integration
- Web interface connections
- Cross-component bridging

### 6. Core Systems (5 modules)
- Production configuration
- Database operations
- Service startup management

### 7. Utilities (6 modules)
- Documentation generation
- Performance analysis
- Security scanning
- Bug detection

### 8. Consciousness (4 modules)
- AI consciousness simulation
- Unified consciousness core
- Complete consciousness system

### 9. Processors (2 modules)
- Vision and image processing
- Voice control and commands

### 10. Interfaces (6 modules)
- Webinar interface
- Web interfaces
- Unified interface system

### 11. Launchers (4 modules)
- System entry points
- Agent system launcher
- Minimal and custom launchers

### 12. Plugins (1 module)
- Example monitor plugin
- Plugin system framework

## Important Notes

1. **Active Modules**: The most current production modules are copies from `ACTIVE_NEXUS_2.0/core/`
2. **Module Relationships**: See `MODULE_RELATIONSHIPS.md` for detailed interaction patterns
3. **Import Paths**: Update any existing imports to use the new `PYTHON_MODULES` structure
4. **Dependencies**: Each category has minimal cross-dependencies for modularity

## Next Steps

1. Update import statements in active code to use this structure
2. Remove duplicate files from other locations
3. Add proper module documentation to each `__init__.py`
4. Create unit tests for each module category