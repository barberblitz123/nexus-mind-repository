# NEXUS 2.0 Core Systems

This directory contains the core Python modules that power NEXUS 2.0.

## Directory Structure

### Core Infrastructure
- `nexus_config_production.py` - Configuration management
- `nexus_database_production.py` - Database connections and ORM
- `nexus_integration_core.py` - Central integration hub (MessageBus, ServiceDiscovery)
- `nexus_core_production.py` - Main production core with health checks
- `nexus_startup_manager.py` - Service lifecycle management

### MANUS System (Continuous Agent)
- `manus_continuous_agent.py` - Task queue and execution engine
- `manus_nexus_integration.py` - Bridge between MANUS and NEXUS
- `manus_web_interface.py` - Original web UI
- `manus_web_interface_v2.py` - Enhanced web UI with more features

### Memory Systems
- `nexus_memory_core.py` - Base memory architecture
- `nexus_episodic_memory.py` - Event-based memory (experiences)
- `nexus_semantic_memory.py` - Knowledge graph (facts)
- `nexus_working_memory.py` - Short-term active memory
- `nexus_mem0_core.py` - Advanced block-based memory system
- `nexus_memory_types.py` - Memory data structures

### Web Scraping
- `nexus_web_scraper.py` - Core scraping functionality
- `nexus_scraper_stealth.py` - Anti-detection mechanisms
- `nexus_scraper_proxies.py` - Proxy rotation and management

### Analysis & Tools
- `nexus_performance_analyzer.py` - Performance profiling
- `nexus_bug_detector.py` - Automatic bug detection
- `nexus_security_scanner.py` - Security vulnerability scanning
- `nexus_doc_generator.py` - Documentation generation
- `nexus_project_generator.py` - Project scaffolding

### User Interfaces
- `nexus_webinar_interface.py` - Main webinar/collaboration interface
- `nexus_minimal.py` - Minimal UI for testing

### Specialized Features
- `nexus_vision_processor.py` - Computer vision capabilities
- `nexus_voice_control.py` - Voice command processing
- `nexus_unified_tools.py` - Common utilities
- `nexus_omnipotent_core.py` - Advanced AI integration
- `nexus_enhanced_manus.py` - Enhanced MANUS features

## Dependencies

### External Libraries
- FastAPI - Web framework
- Redis - Caching and pub/sub
- PostgreSQL - Main database
- Consul/etcd - Service discovery
- Prometheus - Metrics
- OpenTelemetry - Tracing

### Internal Dependencies
Most modules depend on:
1. `nexus_config_production.py` (configuration)
2. `nexus_integration_core.py` (service communication)
3. `nexus_database_production.py` (data persistence)

## Entry Points

### Web Services
```bash
# Webinar interface (main UI)
python nexus_webinar_interface.py

# MANUS web interface
python manus_web_interface_v2.py
```

### Demo/Testing
```bash
# Demo webinar
python demo_nexus_webinar.py

# Minimal test interface
python nexus_minimal.py
```

## Service Communication

All services communicate through the `nexus_integration_core.py` MessageBus:
- Pub/sub messaging
- Service discovery
- Health monitoring
- Distributed transactions

## Configuration

Services read configuration from:
1. `nexus_config_production.py`
2. Environment variables
3. Config files in `../configs/`

## Adding New Services

1. Import `nexus_integration_core`
2. Register with ServiceDiscovery
3. Subscribe to relevant MessageBus topics
4. Implement health check endpoint
5. Add to `nexus_startup_manager.py`