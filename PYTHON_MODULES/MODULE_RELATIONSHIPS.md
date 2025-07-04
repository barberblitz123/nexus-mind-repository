# NEXUS 2.0 Python Module Relationships

## Directory Structure Overview

The Python modules have been organized into the following logical categories:

### 1. **agents/** - Agent-Related Modules
- `manus_continuous_agent.py` - Continuous learning agent with web scraping
- `nexus_autonomous_agent.py` - Autonomous agent with goal-directed behavior
- `nexus_agent_orchestrator_advanced.py` - Advanced agent orchestration system

**Relationships**: These agents use memory systems from `memory/` and integration capabilities from `integrations/`.

### 2. **memory/** - Memory System Modules
- `nexus_memory_core.py` - Core memory management system
- `nexus_memory_types.py` - Memory type definitions
- `nexus_episodic_memory.py` - Episodic memory for event storage
- `nexus_semantic_memory.py` - Semantic memory for knowledge
- `nexus_working_memory.py` - Short-term working memory
- `nexus_mem0_core.py` - Mem0 integration for persistent memory

**Relationships**: Memory modules are used by agents, interfaces, and core systems for context retention.

### 3. **scrapers/** - Web Scraping Modules
- `nexus_web_scraper.py` - Main web scraping functionality
- `nexus_scraper_proxies.py` - Proxy management for scraping
- `nexus_scraper_stealth.py` - Stealth scraping techniques

**Relationships**: Used by agents and interfaces for web research capabilities.

### 4. **ui_terminal/** - Terminal UI Modules
- `nexus_terminal_app.py` - Main terminal application
- `nexus_terminal_ui_advanced.py` - Advanced terminal UI features
- `nexus_integrated_terminal.py` - Integrated terminal with NEXUS features
- `nexus_desktop_manager.py` - Desktop environment management
- `nexus_stage_manager.py` - Stage/window management

**Relationships**: Provides terminal-based interfaces for NEXUS functionality.

### 5. **integrations/** - Integration Modules
- `nexus_integration_core.py` - Core integration framework
- `manus_nexus_integration.py` - MANUS-NEXUS integration
- `nexus_enhanced_manus.py` - Enhanced MANUS capabilities
- `manus_continuous_agent.py` - MANUS continuous agent
- `manus_web_interface*.py` - MANUS web interfaces

**Relationships**: Bridges different NEXUS components and external services.

### 6. **core_systems/** - Production Core Modules
- `nexus_core_production.py` - Main production core
- `nexus_config_production.py` - Configuration management
- `nexus_database_production.py` - Database operations
- `nexus_startup_manager.py` - Service startup management
- `nexus_omnipotent_core.py` - Advanced omnipotent capabilities

**Relationships**: Foundation modules that other components build upon.

### 7. **utilities/** - Utility Modules
- `nexus_unified_tools.py` - Unified tool collection
- `nexus_doc_generator.py` - Documentation generation
- `nexus_bug_detector.py` - Bug detection system
- `nexus_performance_analyzer.py` - Performance analysis
- `nexus_security_scanner.py` - Security scanning
- `nexus_project_generator.py` - Project scaffolding

**Relationships**: Support tools used across the system.

### 8. **consciousness/** - Consciousness System Modules
- `consciousness_core.py` - Core consciousness system
- `consciousness_core_real.py` - Real consciousness implementation
- `nexus_consciousness_complete_system.py` - Complete consciousness system
- `unified_nexus_core.py` - Unified consciousness core

**Relationships**: Advanced AI consciousness simulation used by agents and interfaces.

### 9. **processors/** - Processing Modules
- `nexus_vision_processor.py` - Vision/image processing
- `nexus_voice_control.py` - Voice control processing
- `auditory-processor-real.py` - Audio processing
- `visual-processor-real.py` - Visual processing
- `ml-model-loader.py` - ML model loading
- `processor-integration-example.py` - Integration examples

**Relationships**: Provides sensory processing for interfaces and agents.

### 10. **interfaces/** - Interface Modules
- `nexus_webinar_interface.py` - Main webinar interface
- `demo_nexus_webinar.py` - Webinar demo
- `manus_web_interface*.py` - MANUS web interfaces
- `nexus_unified_interface.py` - Unified interface system
- `nexus_html_tab_integrator.py` - HTML tab integration

**Relationships**: User-facing interfaces that utilize all other modules.

### 11. **launchers/** - Launcher Modules
- `nexus_2.0_launcher.py` - Main NEXUS 2.0 launcher
- `nexus_minimal.py` - Minimal launcher
- `launch_nexus_agent_system.py` - Agent system launcher
- `launch_with_custom_tabs.py` - Custom tab launcher

**Relationships**: Entry points that bootstrap and initialize the system.

## Key Module Interactions

1. **Agents → Memory**: Agents use memory systems for context and learning
2. **Interfaces → Agents**: Interfaces create and manage agents
3. **Core Systems → All**: Provides foundation for all components
4. **Processors → Interfaces**: Enables multimodal interactions
5. **Scrapers → Agents**: Provides web research capabilities
6. **Utilities → All**: Support tools used throughout

## Import Examples

```python
# From an interface module
from PYTHON_MODULES.agents import nexus_autonomous_agent
from PYTHON_MODULES.memory import nexus_memory_core
from PYTHON_MODULES.core_systems import nexus_config_production

# From an agent module
from PYTHON_MODULES.memory import nexus_episodic_memory
from PYTHON_MODULES.scrapers import nexus_web_scraper
from PYTHON_MODULES.integrations import nexus_integration_core
```

## Module Dependencies

- **High-level** (interfaces, launchers) → **Mid-level** (agents, processors) → **Low-level** (core_systems, memory)
- **Horizontal dependencies**: integrations connect different subsystems
- **Utilities**: standalone tools with minimal dependencies

## Notes

- Each module directory contains an `__init__.py` file for proper Python packaging
- The active production modules are in `ACTIVE_NEXUS_2.0/core/`
- Archive modules are in `ARCHIVE/` for reference
- Web app specific modules remain in their respective web app directories