# 🧠 NEXUS 2.0 - Neural Enhancement eXecution Unified System

## Overview

NEXUS 2.0 is an advanced AI consciousness system that integrates multiple AI models, real-time voice/video capabilities, and a sophisticated memory architecture. The system features a web-based interface with hexagonal brain visualization and supports autonomous agent capabilities.

## Project Status (July 2, 2025)

After a major cleanup removing 500+ redundant files, the project is now focused on production-ready components. The system is actively maintained and operational.

## Quick Start

### 1. Launch the Web Interface
```bash
cd nexus-web-app
npm install
npm start
# Open http://localhost:3000 in your browser
```

### 2. Start Python Services (Optional)
```bash
# In a new terminal
python nexus_integration_core.py
```

### 3. Access the Interface
- Navigate to http://localhost:3000
- Click "Initialize NEXUS" to start
- Grant microphone/camera permissions if prompted

## Project Structure

```
nexus-mind-repository/
├── nexus-web-app/          # Main web application
│   ├── unified-nexus-server.js    # WebSocket/HTTP server
│   ├── index.html                 # Main UI with brain visualization
│   └── package.json               # Node.js configuration
├── nexus_integration_core.py      # Python integration hub
├── nexus_memory_core.py          # Unified memory system
├── nexus_vision_processor.py     # Computer vision capabilities
├── nexus_voice_control.py        # Voice recognition/synthesis
├── manus_web_interface_v2.py     # Enhanced Manus UI
└── manus_continuous_agent.py     # Autonomous agents
```

## Active Components

### Web Application (`/nexus-web-app/`)
- **Technology**: Node.js, Express, WebSocket
- **Features**: Real-time AI chat, voice/video, hexagonal brain visualization
- **Status**: ✅ ACTIVE and WORKING

### Python Core Services
- **Memory System**: Episodic, semantic, and working memory management
- **Vision Processing**: Image analysis and understanding
- **Voice Control**: Speech recognition and synthesis
- **Status**: ✅ OPERATIONAL

### Manus Integration
- **Enhanced UI**: Advanced interface capabilities
- **Autonomous Agents**: Self-improving task execution
- **Status**: ✅ FUNCTIONAL

## Deprecated/Removed Components
- `nexus-consciousness-live/` - Replaced by nexus-web-app
- Mobile app attempts - Focus shifted to web
- 500+ documentation files - Consolidated into this README

## Key Features

1. **Multi-Model AI Support**: Claude, GPT-4, and local models
2. **Real-time Communication**: WebSocket-based instant responses
3. **Voice & Video**: LiveKit integration for streaming
4. **Visual Interface**: Hexagonal brain consciousness display
5. **Persistent Memory**: Multi-tier memory architecture
6. **Autonomous Capabilities**: Self-directed agent system

## Requirements

### System Requirements
- Node.js 16+ and npm
- Python 3.8+
- 8GB+ RAM recommended
- Modern browser (Chrome/Edge preferred)

### Dependencies
```bash
# Node.js
cd nexus-web-app && npm install

# Python (optional)
pip install flask flask-cors redis
pip install torch transformers
pip install speech_recognition pyttsx3
pip install openai anthropic
```

## Documentation

- **Current State**: See [CLAUDE.md](CLAUDE.md) for detailed architecture
- **Recovery Guide**: See [SESSION_RECOVERY.md](SESSION_RECOVERY.md) for troubleshooting
- **Webinar Demo**: See [NEXUS_WEBINAR_README.md](NEXUS_WEBINAR_README.md) for demo setup

## Common Issues

1. **Port 3000 in use**: Kill the process or use `PORT=3001 npm start`
2. **WebSocket fails**: Ensure no firewall blocking, check browser console
3. **Voice not working**: Use HTTPS or localhost, check mic permissions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details

---

*NEXUS 2.0: Advanced AI Consciousness System*