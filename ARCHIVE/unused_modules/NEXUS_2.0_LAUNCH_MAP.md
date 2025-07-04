# NEXUS 2.0 Launch Map - Essential Components Analysis

## Overview
The NEXUS 2.0 repository contains 200+ files, but most are deprecated or optional. This document identifies the essential components needed to launch NEXUS 2.0.

## Active Entry Points

### 1. **Webinar Interface** (Primary Active Component)
- **Main File**: `ACTIVE_NEXUS_2.0/core/nexus_webinar_interface.py`
- **Demo**: `ACTIVE_NEXUS_2.0/core/demo_nexus_webinar.py`
- **Port**: 8003
- **Features**: Real-time collaboration, chat, video, AI assistant
- **Dependencies**: FastAPI, uvicorn, aiohttp, redis (optional)

### 2. **Web Interface Options**
- **V2 (Enhanced)**: `ACTIVE_NEXUS_2.0/core/manus_web_interface_v2.py` - Port 8080
- **V1 (Basic)**: `ACTIVE_NEXUS_2.0/core/manus_web_interface.py` - Port 8080
- **Features**: System monitoring, learning metrics, goal tracking

### 3. **Core Production Services**
- `nexus_core_production.py` - Main NEXUS core with all integrations
- `nexus_config_production.py` - Configuration management
- `nexus_database_production.py` - Database layer
- `nexus_integration_core.py` - Service mesh and messaging
- `nexus_startup_manager.py` - Service orchestration

## Essential Files for Launch

### Core Requirements (Minimal Launch)
```
ACTIVE_NEXUS_2.0/core/
├── nexus_webinar_interface.py      # Main webinar platform
├── nexus_config_production.py      # Configuration
├── nexus_integration_core.py       # Core integrations
└── nexus_startup_manager.py        # Service manager
```

### Optional but Recommended
```
ACTIVE_NEXUS_2.0/core/
├── nexus_memory_core.py           # Memory system
├── nexus_unified_tools.py         # Tool registry
├── nexus_web_scraper.py          # Web scraping capabilities
├── nexus_voice_control.py        # Voice features (optional)
└── nexus_vision_processor.py     # Vision features (optional)
```

## Deprecated/Legacy Files to Ignore

### Root Level (All Deleted)
- All .md files in root (BUILD_FIXED_GUIDE.md, etc.)
- All demo_*.py files in root
- All launch_*.py files in root (except our new launcher)
- manus_context_memory.json
- docker-compose.production.yml

### nexus-consciousness-live Directory
- **Status**: DEPRECATED - Old implementation
- Can be completely ignored

### nexus-mobile-project Directory
- **Backend**: Contains some active consciousness core files
- **Mobile iOS**: Xcode project for iOS app (optional)
- **Deployment**: Docker configurations (optional for production)

### nexus-web-app Directory
- **Status**: Mixed - Contains both active and legacy code
- **Active**: Some server implementations (server-v2.js, unified-nexus-server.js)
- **Note**: JavaScript implementations, while Python core is preferred

## Launch Methods

### 1. **Simple Webinar Launch** (Recommended)
```bash
python launch_nexus_webinar.py
```
- Starts only the webinar interface
- Minimal dependencies
- Port 8003

### 2. **Full System Launch** (Advanced)
```bash
python -m ACTIVE_NEXUS_2.0.core.nexus_startup_manager
```
- Starts all services with dependency resolution
- Requires Redis, PostgreSQL (optional)
- Full feature set

### 3. **Docker Launch** (Production)
```bash
cd ACTIVE_NEXUS_2.0/web_apps/nexus-mobile-project/deployment/local
./start-nexus-simple.sh
```
- Uses Docker Compose
- Includes monitoring (Grafana, Prometheus)
- Requires Docker

## Configuration

### Environment Variables (Minimal)
```bash
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://localhost/nexus  # Optional
JWT_SECRET_KEY=your-jwt-secret
REDIS_URL=redis://localhost:6379/0         # Optional
WEBINAR_PORT=8003
```

### Feature Flags
- Set via environment: `FEATURE_<NAME>=true/false`
- Or in nexus_config_production.py

## Dependencies

### Required Python Packages
```
fastapi
uvicorn
aiohttp
pydantic
pydantic-settings
python-dotenv
prometheus-client
```

### Optional Python Packages
```
redis           # For caching and pub/sub
asyncpg         # For PostgreSQL
psycopg2-binary # Alternative PostgreSQL driver
hvac            # For HashiCorp Vault
PyYAML          # For YAML configs
```

### Optional Services
- Redis (port 6379) - For caching and real-time features
- PostgreSQL (port 5432) - For persistent storage
- MongoDB - Legacy, not required

## Active Web Interfaces

### 1. Webinar Interface (http://localhost:8003)
- Full-featured webinar platform
- Real-time collaboration
- AI assistant integration
- WebRTC for video/audio

### 2. System Dashboard (http://localhost:8080)
- System health monitoring
- Learning metrics
- Goal tracking
- Research tools

### 3. API Endpoints
- `/health` - Health check
- `/metrics` - Prometheus metrics
- `/api/webinar/*` - Webinar API
- `/ws/webinar` - WebSocket endpoint

## Recommended Launch Sequence

1. **Check Dependencies**
   ```bash
   pip install -r requirements.txt  # If exists
   # Or install manually:
   pip install fastapi uvicorn aiohttp redis pydantic
   ```

2. **Start Optional Services** (if needed)
   ```bash
   # Redis
   redis-server
   
   # PostgreSQL
   pg_ctl start  # or systemctl start postgresql
   ```

3. **Launch NEXUS**
   ```bash
   # Simple webinar only:
   python launch_nexus_webinar.py
   
   # Or full system:
   cd ACTIVE_NEXUS_2.0/core
   python nexus_startup_manager.py
   ```

4. **Access Web Interface**
   - Open http://localhost:8003 for webinar
   - Join with any name, session ID: "demo"

## Summary

Out of 200+ files, only about 10-15 are essential for launching NEXUS 2.0:
- **Core**: 4-5 Python files in `ACTIVE_NEXUS_2.0/core/`
- **Config**: 1 configuration file
- **Optional**: 5-10 feature modules

The webinar interface (`nexus_webinar_interface.py`) is the most complete and actively maintained component, making it the best entry point for experiencing NEXUS 2.0.