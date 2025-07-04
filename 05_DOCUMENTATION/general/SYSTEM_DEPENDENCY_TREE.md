# NEXUS 2.0 System Dependency Tree

## Visual Dependency Tree

```
┌─────────────────────────────────────────────────────────────┐
│                      NEXUS 2.0 SYSTEM                        │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    CONFIGURATION LAYER                       │
├─────────────────────────────────────────────────────────────┤
│  nexus_config_production.py (No dependencies)               │
│    └── Provides: ProductionConfig, env vars, settings       │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     DATABASE LAYER                           │
├─────────────────────────────────────────────────────────────┤
│  nexus_database_production.py                               │
│    ├── Depends on: nexus_config_production                  │
│    └── Provides: DatabaseManager, ORM models                │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   INTEGRATION LAYER                          │
├─────────────────────────────────────────────────────────────┤
│  nexus_integration_core.py                                  │
│    ├── Depends on: config, database                         │
│    └── Provides: MessageBus, ServiceDiscovery, StateManager │
└─────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
┌───────────────────────────┐ ┌───────────────────────────────┐
│      CORE SERVICES        │ │       MEMORY SYSTEM           │
├───────────────────────────┤ ├───────────────────────────────┤
│ nexus_core_production.py  │ │ nexus_memory_core.py          │
│   └── Health, Metrics     │ │   ├── nexus_memory_types.py   │
│                           │ │   ├── nexus_working_memory.py │
│ nexus_startup_manager.py  │ │   ├── nexus_episodic_memory.py│
│   └── Service lifecycle   │ │   ├── nexus_semantic_memory.py│
│                           │ │   └── nexus_mem0_core.py      │
└───────────────────────────┘ └───────────────────────────────┘
                │                             │
                └──────────┬──────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    FEATURE SERVICES                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   MANUS SYSTEM  │  │  WEB SCRAPING   │  │   TOOLS     │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────┤ │
│  │ manus_continuous│  │ nexus_web_      │  │ nexus_bug_  │ │
│  │ _agent.py       │  │ scraper.py      │  │ detector.py │ │
│  │                 │  │                 │  │             │ │
│  │ manus_nexus_    │  │ nexus_scraper_  │  │ nexus_doc_  │ │
│  │ integration.py  │  │ stealth.py      │  │ generator.py│ │
│  │                 │  │                 │  │             │ │
│  │ manus_web_      │  │ nexus_scraper_  │  │ nexus_perf_ │ │
│  │ interface.py    │  │ proxies.py      │  │ analyzer.py │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ VISION & VOICE  │  │   ADVANCED AI   │                  │
│  ├─────────────────┤  ├─────────────────┤                  │
│  │ nexus_vision_   │  │ nexus_omnipotent│                  │
│  │ processor.py    │  │ _core.py        │                  │
│  │                 │  │                 │                  │
│  │ nexus_voice_    │  │ nexus_enhanced_ │                  │
│  │ control.py      │  │ manus.py        │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACES                           │
├─────────────────────────────────────────────────────────────┤
│  nexus_webinar_interface.py (Main Web UI - FastAPI)         │
│    ├── Depends on: All core services                        │
│    └── Provides: REST API, WebSocket, Streaming             │
│                                                              │
│  nexus-web-app/ (Node.js Frontend)                          │
│    ├── server.js, unified-nexus-server.js                   │
│    └── Communicates with Python backend via HTTP/WS         │
└─────────────────────────────────────────────────────────────┘
```

## Service Communication Patterns

### 1. Direct Dependencies (Import)
```
A.py imports B → A depends on B
Example: nexus_core_production imports nexus_config_production
```

### 2. MessageBus Communication
```
A.py ← MessageBus → B.py
Services publish/subscribe without direct imports
Example: MANUS publishes task events, monitors subscribe
```

### 3. HTTP/WebSocket Communication
```
Frontend (JS) ← HTTP/WS → Backend (Python)
Example: nexus-web-app/server.js calls nexus_webinar_interface.py
```

## Dependency Rules

### ✅ Allowed Dependencies
1. **Downward Only**: Higher layers can depend on lower layers
2. **Same Layer**: Services at same layer can communicate via MessageBus
3. **Config First**: Everything can depend on config layer

### ❌ Avoided Patterns
1. **Upward Dependencies**: Lower layers should not import higher layers
2. **Cross-Feature**: Feature services should not directly import each other
3. **Circular Imports**: Avoided except for startup_manager registration

## Module Relationships

### Core Infrastructure
```
nexus_config_production.py
    ↓ (used by everything)
nexus_database_production.py
    ↓ (used by services needing persistence)
nexus_integration_core.py
    ↓ (used by all services for communication)
```

### Memory System Hierarchy
```
nexus_memory_types.py (base types)
    ↓
nexus_memory_core.py (orchestrator)
    ├── nexus_working_memory.py
    ├── nexus_episodic_memory.py
    ├── nexus_semantic_memory.py
    └── nexus_mem0_core.py
```

### MANUS System Flow
```
manus_continuous_agent.py (standalone)
    ↓
manus_nexus_integration.py (bridge)
    ↓
manus_web_interface.py (UI)
```

### Tool Services
```
nexus_unified_tools.py (shared utilities)
    ↓
├── nexus_bug_detector.py
├── nexus_doc_generator.py
├── nexus_performance_analyzer.py
└── nexus_security_scanner.py
```

## Launch Sequence

### 1. Configuration Load
```
nexus_config_production.py
```

### 2. Database Initialize
```
nexus_database_production.py
```

### 3. Integration Core Start
```
nexus_integration_core.py
    ├── Redis connection
    ├── Service discovery
    └── Message bus
```

### 4. Core Services Start
```
nexus_core_production.py
nexus_startup_manager.py
nexus_memory_core.py
```

### 5. Feature Services Register
```
All feature services register with startup_manager
```

### 6. Web Interface Launch
```
nexus_webinar_interface.py (Python API)
nexus-web-app/server.js (Node.js UI)
```

## Key Integration Points

### 1. Service Registration
All services register with `nexus_startup_manager.py` via `nexus_integration_core.py`

### 2. Memory Access
Services access memory through `nexus_memory_core.py` API

### 3. Configuration
All services read from `nexus_config_production.py`

### 4. Health Monitoring
`nexus_core_production.py` monitors all registered services

### 5. Event Communication
`nexus_integration_core.py` MessageBus handles all events