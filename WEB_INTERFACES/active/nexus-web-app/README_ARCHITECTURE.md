# NEXUS Web App Architecture

## Overview
The NEXUS Web App is the primary user interface for NEXUS 2.0, providing a real-time collaborative environment with AI integration.

## Directory Structure

### Frontend Components
```
├── index.html              # Main entry point
├── nexus-interface.js      # Core UI logic and event handling
├── styles.css             # Main styling
├── consciousness-sync.js   # Real-time synchronization
├── livekit-integration.js  # Video/audio capabilities
└── hexagonal-brain-visualizer.js  # AI visualization
```

### Voice & AI Integration
```
├── nexus-voice-enhanced.js      # Voice command processing
├── nexus-voice-multimodal.js    # Multi-modal voice features
├── nexus-conversation-ai.js     # AI conversation handler
├── nexus-multi-model-ai.js      # Multiple AI model support
└── emergency-chat.js            # Fallback chat interface
```

### Backend Services
```
backend/
├── consciousness-websocket-client.js  # WebSocket client
├── nexus-consciousness-connector.py   # Python bridge
└── real-time-sync-manager.js        # Sync coordination
```

### Server Components
```
├── server.js                    # Main Node.js server
├── server-v2.js                # Enhanced server version
├── unified-nexus-server.js     # All-in-one server
├── app.js                      # Express app configuration
└── gateway/
    └── nexus-api-gateway.js    # API gateway
```

### IDE Integration
```
ide/
├── nexus-ide.html              # IDE interface
├── nexus-ide-layout.js         # IDE layout manager
├── nexus-dev-assistant.js      # Development assistant
├── monaco-loader.js            # Monaco editor loader
└── editor/
    ├── monaco-nexus-integration.js
    └── consciousness-linter.js
```

### Context Management
```
context/
├── nexus-mega-context.js       # Large context handling
├── sliding-window-manager.js   # Context windowing
├── context-compressor.js       # Context compression
├── embedding-generator.py      # Vector embeddings
└── nexus-vector-store.py      # Vector storage
```

### Launch Scripts
```
├── start-nexus-v5-complete.sh  # Full system launch
├── start-nexus-web.sh         # Web-only launch
├── start-nexus-complete.sh    # Legacy launcher
├── stop-nexus-v5.sh          # Stop all services
└── stop-nexus-complete.sh    # Legacy stop script
```

## Dependencies & Connections

### External Services
1. **Python Backend** (Port 8000)
   - nexus_webinar_interface.py
   - consciousness_core.py
   - Various processors

2. **LiveKit Server** (Port 7880)
   - Real-time video/audio
   - Screen sharing
   - Recording capabilities

3. **MCP Server** (Port 3000)
   - Model Context Protocol
   - AI model management

4. **Redis** (Port 6379)
   - Session management
   - Pub/sub messaging
   - Caching

### Frontend Dependencies
- **JavaScript Libraries**
  - WebSocket API
  - MediaStream API
  - Monaco Editor
  - Chart.js (visualizations)

### Communication Flow
```
User Browser
    ↓
Node.js Server (8080)
    ↓
API Gateway
    ├── Python Services (8000)
    ├── LiveKit (7880)
    ├── MCP Server (3000)
    └── Redis (6379)
```

## Key Features

### 1. Real-time Collaboration
- WebSocket-based messaging
- Synchronized cursors
- Shared workspace
- Live video/audio

### 2. AI Integration
- Multiple AI models (Claude, GPT, local)
- Context-aware responses
- Code understanding
- Natural language processing

### 3. Development Tools
- Integrated IDE
- File management
- Terminal access
- Git integration

### 4. Memory Systems
- Context preservation
- Session history
- Knowledge graphs
- Vector search

## Configuration

### Environment Variables
```bash
NODE_ENV=production
PORT=8080
BACKEND_URL=http://localhost:8000
LIVEKIT_URL=ws://localhost:7880
REDIS_URL=redis://localhost:6379
```

### Config Files
- `processors/processor-config.json` - Processor settings
- `ide/config/ide-config.js` - IDE configuration
- `database/schema.sql` - Database schema

## Launching the System

### Development Mode
```bash
npm install
npm run dev
```

### Production Mode
```bash
./start-nexus-v5-complete.sh
```

### Testing
```bash
npm test
node test-integration.js
```

## Troubleshooting

### Common Issues
1. **Port conflicts** - Check ports 8080, 8000, 7880, 3000
2. **Missing dependencies** - Run `npm install`
3. **Python services down** - Check Python logs
4. **WebSocket errors** - Verify backend is running

### Debug Mode
```bash
DEBUG=* npm start
```

### Logs Location
- `logs/web-server.log`
- `logs/consciousness-core.log`
- `logs/mcp-server.log`