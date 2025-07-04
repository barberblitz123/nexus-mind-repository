# Migration Guide After Repository Organization

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

- nexus-web-app → 02_WEB_INTERFACES/active/
- cleanup_log_20250702_160359.json → 04_CONFIGURATIONS/json/
- nexus_terminal_ui_requirements.txt → 04_CONFIGURATIONS/requirements/
- requirements.txt → 04_CONFIGURATIONS/requirements/
- nexus_integration_requirements.txt → 04_CONFIGURATIONS/requirements/
- requirements_vision.txt → 04_CONFIGURATIONS/requirements/
- requirements_live_preview.txt → 04_CONFIGURATIONS/requirements/
- manus_requirements.txt → 04_CONFIGURATIONS/requirements/
- requirements_local_only.txt → 04_CONFIGURATIONS/requirements/
- nexus_launcher_requirements.txt → 04_CONFIGURATIONS/requirements/
- NEXUS_2.0_ORGANIZED.md → 05_DOCUMENTATION/nexus_docs/
- NEXUS_WEBINAR_README.md → 05_DOCUMENTATION/nexus_docs/
- NEXUS_INFINITY_ROADMAP.md → 05_DOCUMENTATION/nexus_docs/
- SECURITY.md → 05_DOCUMENTATION/general/
- TROUBLESHOOTING.md → 05_DOCUMENTATION/general/
- REPOSITORY_MAP.md → 05_DOCUMENTATION/general/
- ORGANIZATION_SUMMARY.md → 05_DOCUMENTATION/general/
- SYSTEM_DEPENDENCY_TREE.md → 05_DOCUMENTATION/general/
- CLEANUP_REPORT.md → 05_DOCUMENTATION/general/
- REPOSITORY_ORGANIZATION_PLAN.md → 05_DOCUMENTATION/general/
- PYTHON_MODULES_ORGANIZATION_SUMMARY.md → 05_DOCUMENTATION/general/
- GITHUB_STRUCTURE.md → 05_DOCUMENTATION/general/
- nexus_vision_processor.py → 03_PYTHON_MODULES/processors/
- nexus_project_generator.py → 03_PYTHON_MODULES/utilities/
- nexus_database_production.py → 03_PYTHON_MODULES/core_systems/
- manus_web_interface_v2.py → 03_PYTHON_MODULES/integrations/
- nexus_performance_analyzer.py → 03_PYTHON_MODULES/utilities/
- demo_nexus_webinar.py → 03_PYTHON_MODULES/utilities/
- manus_continuous_agent.py → 03_PYTHON_MODULES/agents/
- nexus_config_production.py → 03_PYTHON_MODULES/core_systems/
- nexus_webinar_interface.py → 03_PYTHON_MODULES/utilities/
- nexus_security_scanner.py → 03_PYTHON_MODULES/utilities/
- nexus_episodic_memory.py → 03_PYTHON_MODULES/memory/
- nexus_enhanced_manus.py → 03_PYTHON_MODULES/utilities/
- nexus_memory_core.py → 03_PYTHON_MODULES/memory/
- nexus_core_production.py → 03_PYTHON_MODULES/core_systems/
- nexus_integration_core.py → 03_PYTHON_MODULES/integrations/
- manus_nexus_integration.py → 03_PYTHON_MODULES/integrations/
- nexus_startup_manager.py → 03_PYTHON_MODULES/core_systems/
- nexus_scraper_proxies.py → 03_PYTHON_MODULES/scrapers/
- manus_web_interface.py → 03_PYTHON_MODULES/integrations/
- nexus_mem0_core.py → 03_PYTHON_MODULES/memory/
- nexus_scraper_stealth.py → 03_PYTHON_MODULES/scrapers/
- nexus_memory_types.py → 03_PYTHON_MODULES/memory/
- nexus_doc_generator.py → 03_PYTHON_MODULES/utilities/
- nexus_working_memory.py → 03_PYTHON_MODULES/memory/
- nexus_voice_control.py → 03_PYTHON_MODULES/processors/
- nexus_semantic_memory.py → 03_PYTHON_MODULES/memory/
- nexus_omnipotent_core.py → 03_PYTHON_MODULES/utilities/
- nexus_bug_detector.py → 03_PYTHON_MODULES/utilities/
- nexus_minimal.py → 03_PYTHON_MODULES/utilities/
- nexus_web_scraper.py → 03_PYTHON_MODULES/scrapers/
- nexus_unified_tools.py → 03_PYTHON_MODULES/utilities/