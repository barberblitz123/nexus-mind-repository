# NEXUS 2.0 Repository Map

## Overview
This document provides a complete map of the NEXUS 2.0 repository structure, showing how different systems connect and their dependencies.

## Repository Structure

```
nexus-mind-repository/
├── ACTIVE_NEXUS_2.0/          # Currently active components
├── ARCHIVE/                   # Deprecated/old versions
├── NEXUS_2.0_AGENT/          # Agent system components
├── nexus-web-app/            # Main web interface (PRIMARY)
├── nexus-mobile-project/     # Mobile/iPad deployment
└── Core Files/               # Root-level launchers and configs
```

## Major Systems

### 1. NEXUS Core System
**Location**: `ACTIVE_NEXUS_2.0/core/`

#### Entry Points
- `nexus_core_production.py` - Main production core
- `nexus_integration_core.py` - Central integration hub
- `nexus_startup_manager.py` - Service orchestration

#### Core Components
```
nexus_core_production.py
    ├── imports: nexus_config_production, nexus_database_production
    ├── provides: NexusProductionCore, ServiceHealthCheck, MetricsCollector
    └── used by: nexus_webinar_interface.py, manus systems

nexus_integration_core.py
    ├── provides: MessageBus, ServiceDiscovery, StateManager
    ├── external deps: redis, consul, etcd3, prometheus, opentelemetry
    └── used by: Most production services

nexus_startup_manager.py
    ├── provides: StartupManager, ServiceStatus
    └── manages: All service lifecycles
```

### 2. MANUS System (Continuous Work Agent)
**Location**: `ACTIVE_NEXUS_2.0/core/manus_*.py`

#### Components
```
manus_continuous_agent.py
    ├── standalone: Task management system
    └── provides: TaskQueue, TaskExecutor, ContextPreserver

manus_nexus_integration.py
    ├── imports: nexus_integration_core, nexus_memory_core
    └── bridges: MANUS ←→ NEXUS systems

manus_web_interface.py / manus_web_interface_v2.py
    ├── imports: FastAPI, nexus_integration_core
    └── provides: Web UI for MANUS
```

### 3. Memory System
**Location**: `ACTIVE_NEXUS_2.0/core/nexus_*memory*.py`

#### Architecture
```
nexus_memory_core.py (Base)
    ├── nexus_episodic_memory.py
    │   └── Event-based memory storage
    ├── nexus_semantic_memory.py
    │   └── Knowledge graph storage
    ├── nexus_working_memory.py
    │   └── Short-term active memory
    └── nexus_mem0_core.py
        └── Advanced memory blocks system
```

### 4. Web Scraping System
**Location**: `ACTIVE_NEXUS_2.0/core/nexus_*scraper*.py`

#### Components
```
nexus_web_scraper.py
    ├── imports: BeautifulSoup, requests, selenium
    └── provides: WebScraper, ContentExtractor

nexus_scraper_stealth.py
    ├── extends: nexus_web_scraper
    └── adds: Anti-detection, browser spoofing

nexus_scraper_proxies.py
    └── provides: Proxy rotation, rate limiting
```

### 5. Webinar Interface (Main UI)
**Location**: `ACTIVE_NEXUS_2.0/core/nexus_webinar_interface.py`

#### Dependencies
```
nexus_webinar_interface.py
    ├── imports: All core systems
    ├── provides: FastAPI web server
    └── features: WebSockets, streaming, collaboration
```

### 6. Web Application
**Location**: `nexus-web-app/`

#### Structure
```
nexus-web-app/
├── Frontend
│   ├── index.html - Main entry
│   ├── nexus-interface.js - Core UI logic
│   └── styles.css - Styling
├── Backend
│   ├── server.js - Node.js server
│   ├── unified-nexus-server.js - Integrated server
│   └── consciousness-sync.js - Real-time sync
├── IDE Integration
│   └── ide/ - Monaco editor integration
└── Launch Scripts
    ├── start-nexus-v5-complete.sh
    └── start-nexus-web.sh
```

### 7. Mobile/iPad Deployment
**Location**: `nexus-mobile-project/`

#### Structure
```
nexus-mobile-project/
├── backend/
│   ├── central-consciousness-core/
│   ├── livekit/ - Video/audio
│   └── nexus-mcp/ - Model Context Protocol
├── deployment/
│   └── local/
│       ├── docker-compose.yml
│       └── start-nexus.sh
└── mobile/
    └── ios-app/ - Swift/iOS code
```

### 8. Utility Systems

#### Documentation Generator
- `nexus_doc_generator.py` - Auto-generates docs
- `nexus_project_generator.py` - Creates project structures

#### Analysis Tools
- `nexus_performance_analyzer.py` - Performance profiling
- `nexus_bug_detector.py` - Bug detection
- `nexus_security_scanner.py` - Security analysis

#### Vision & Voice
- `nexus_vision_processor.py` - Image/video processing
- `nexus_voice_control.py` - Voice commands

## Dependency Graph

### Level 1 - Core Infrastructure
```
nexus_config_production.py (No deps)
nexus_database_production.py → config
```

### Level 2 - Integration Layer
```
nexus_integration_core.py → config, database
    ├── MessageBus
    ├── ServiceDiscovery
    └── StateManager
```

### Level 3 - Core Services
```
nexus_core_production.py → integration_core, config, database
nexus_startup_manager.py → integration_core
nexus_memory_core.py → integration_core
```

### Level 4 - Feature Services
```
nexus_webinar_interface.py → core_production, integration_core, startup_manager
manus_nexus_integration.py → integration_core, memory_core
nexus_web_scraper.py → integration_core
```

### Level 5 - UI/Applications
```
manus_web_interface.py → manus_nexus_integration
nexus-web-app/server.js → (HTTP API calls to Python services)
```

## Launch Sequences

### 1. Full System Launch
```bash
cd nexus-web-app/
./start-nexus-v5-complete.sh
```
Starts: Database → Redis → Core Services → Web UI

### 2. Web-Only Launch
```bash
cd nexus-web-app/
npm start
```
Starts: Node.js server only (requires backend services)

### 3. Docker Production
```bash
cd nexus-mobile-project/deployment/local/
./start-nexus.sh
```
Starts: All services in containers

### 4. Development Launch
```bash
python nexus_2.0_launcher.py
```
Starts: Minimal services for development

## Common Issues & Solutions

### Circular Dependencies
Found one circular dependency:
- `nexus_webinar_interface.py` <-> `nexus_startup_manager.py`
  - This appears intentional for service registration
  - The startup manager needs to know about services, and services register with it

### Broken Imports
Active system analysis:
- ✅ All imports in ACTIVE_NEXUS_2.0/core/ are valid
- ✅ Cross-directory imports (e.g., to nexus-web-app/) work correctly
- ⚠️ Some archived files may reference moved modules

### Service Discovery
- All services register with integration_core
- Health checks via startup_manager

## Active vs Archived

### Actively Used
- Everything in `ACTIVE_NEXUS_2.0/`
- `nexus-web-app/` - Primary interface
- `nexus-mobile-project/` - Deployment configs

### Archived (Not Used)
- Everything in `ARCHIVE/`
- Old launcher scripts in root
- Duplicate files from reorganization

## Next Steps
1. Clean up duplicate files
2. Fix import paths in archived files (if needed)
3. Create service-specific README files
4. Add dependency injection configuration