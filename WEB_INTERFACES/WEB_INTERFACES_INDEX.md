# WEB INTERFACES INDEX

This directory contains all web interfaces for the NEXUS 2.0 project, organized by their current status.

## Directory Structure

```
WEB_INTERFACES/
├── active/          # Currently used web applications
├── experimental/    # Test and experimental interfaces
└── deprecated/      # Old interfaces no longer in active use
```

## Active Interfaces

### 1. nexus-web-app
- **Location**: `active/nexus-web-app/`
- **Purpose**: Main NEXUS V5 web interface with real-time collaboration
- **Features**: Chat, video, AI integration, websocket communication
- **Launch**: `npm start` (runs on port 8080)
- **Key Files**: 
  - `unified-nexus-server.js` - Main server
  - `nexus-interface.js` - Frontend logic
  - `index.html` - Main UI

### 2. nexus-web-app-v5
- **Location**: `active/nexus-web-app-v5/`
- **Purpose**: Alternative V5 implementation (duplicate of above)
- **Features**: Same as nexus-web-app
- **Status**: Check which version is actually being used

### 3. nexus-mobile-project
- **Location**: `active/nexus-mobile-project/`
- **Purpose**: Mobile deployment and backend services
- **Features**: Docker deployment, MCP server, mobile configurations
- **Components**:
  - `backend/` - Backend services and MCP integration
  - `deployment/` - Docker and deployment configs
  - `nexus-v5-mobile.html` - Mobile web interface

## Experimental Interfaces

### 1. nexus-minimal
- **Location**: `experimental/nexus-minimal/`
- **Purpose**: Minimal implementation for testing core features
- **Features**: Basic chat and websocket functionality
- **Status**: Simplified version for experimentation

### 2. nexus-unified-app
- **Location**: `experimental/nexus-unified-app/`
- **Purpose**: Unified application with advanced features
- **Features**: 
  - Audio/voice integration
  - Visual integration
  - IDE integration
  - Project analyzer
  - Consciousness bridge
- **Status**: Experimental unified interface with many advanced features

## Deprecated Interfaces

### 1. nexus-consciousness-live
- **Location**: `deprecated/nexus-consciousness-live/`
- **Purpose**: Early consciousness interface implementation
- **Features**: Multiple HTML interfaces for different views
- **Files**:
  - `nexus-consciousness-interface.html`
  - `nexus-interface.html`
  - `nexus-vision-interface.html`
  - Various server implementations
- **Status**: Superseded by newer implementations

## How to Use

1. **For production use**: Use interfaces in the `active/` directory
2. **For testing new features**: Try interfaces in `experimental/`
3. **For reference**: Check `deprecated/` for older implementations

## Primary Entry Point

The main web interface is `active/nexus-web-app/`. To start:

```bash
cd WEB_INTERFACES/active/nexus-web-app/
npm install  # First time only
npm start    # Starts on port 8080
```

## Notes

- Most interfaces use Node.js/Express backend with WebSocket support
- Common ports: 8080 (web), 8000 (backend), 3000 (MCP)
- All interfaces integrate with AI models (Claude, OpenAI, etc.)
- Mobile project includes Docker deployment configurations