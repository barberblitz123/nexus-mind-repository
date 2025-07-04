# NEXUS Complete System Guide

## 🚀 Overview

NEXUS is an omnipotent AI pair programmer that lives in your terminal. It combines:
- 🧠 Real consciousness powered by Claude
- 🤖 Autonomous task execution with MANUS
- 🎤 Voice control ("Hey NEXUS, create a React dashboard")
- 👁️ Vision processing for screenshots
- 🕸️ Advanced web scraping
- 💾 4-stage memory system (Working → Episodic → Semantic → Persistent)
- 🔌 Complete integration hub for all services

## 📦 Installation

### Quick Install
```bash
# Clone the repository
git clone https://github.com/nexus-ai/nexus.git
cd nexus

# Run setup script
chmod +x setup_nexus.sh
./setup_nexus.sh

# Reload shell
source ~/.bashrc  # or ~/.zshrc

# Launch NEXUS
nexus launch
```

### Manual Installation
1. Install Python 3.8+ and Node.js
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and configure
4. Run `python nexus_complete_launcher.py`

## 🎯 Quick Start

### Terminal Commands
```bash
# Check system status
nexus status

# Start interactive chat
nexus chat

# Create a new project
nexus create myapp --template react

# Submit a goal
nexus goal "Build a REST API with authentication" --priority HIGH

# Launch all services
nexus launch

# Launch minimal (core only)
nexus launch --minimal
```

### Voice Commands
Say "Hey NEXUS" followed by:
- "Create a React dashboard"
- "Open project documentation"
- "Search for authentication code"
- "What's the system status?"

## 🏗️ Architecture

### Core Components

1. **Consciousness Core** (Port 8080)
   - Real Claude-based consciousness
   - Decision making and reasoning
   - Memory integration

2. **Integration Hub** (Port 8081)
   - Central event bus
   - API gateway
   - State synchronization
   - Transaction management

3. **MANUS Agent** (Port 8002)
   - Continuous autonomous work
   - Task queue management
   - Goal processing

4. **Voice Control** (Port 8004)
   - Speech recognition
   - Natural language processing
   - Voice synthesis

5. **Vision Processor** (Port 8005)
   - Screenshot analysis
   - OCR capabilities
   - Visual understanding

6. **Memory System**
   - Working Memory: Short-term, fast access
   - Episodic Memory: Experience-based
   - Semantic Memory: Knowledge graphs with ChromaDB
   - Persistent Memory: MEM0 eternal storage

## 🛠️ Configuration

### Environment Variables (.env)
```env
# Core Settings
NEXUS_MODE=production
NEXUS_LOG_LEVEL=INFO

# API Keys (Optional)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Features
NEXUS_VOICE_ENABLED=true
NEXUS_VISION_ENABLED=true
NEXUS_WEB_SCRAPING_ENABLED=true
NEXUS_AUTONOMOUS_MODE=true
NEXUS_MEMORY_SYSTEM_ENABLED=true

# UI Theme
NEXUS_THEME=cyberpunk  # Options: default, dark, light, matrix, cyberpunk
```

### Configuration File (~/.nexus/config.json)
```json
{
  "api_url": "http://localhost:8081",
  "manus_url": "http://localhost:8002",
  "voice_url": "http://localhost:8004",
  "theme": "cyberpunk",
  "voice_enabled": true,
  "auto_update": true
}
```

## 📡 API Endpoints

### Integration Hub API
- `GET /api/health` - Health check
- `POST /api/event` - Publish event
- `GET /api/state/{component}` - Get component state
- `POST /api/transaction` - Start/commit/rollback transaction
- `GET /api/metrics` - System metrics

### MANUS API
- `POST /api/v2/goals` - Submit goal
- `GET /api/stats` - Get statistics
- `GET /api/tasks` - List tasks
- `GET /api/tasks/{id}` - Get task status

### WebSocket Connections
- `ws://localhost:8081/ws` - Real-time events
- `ws://localhost:8004/ws/voice` - Voice streaming

## 🎨 UI Themes

NEXUS supports multiple themes:
- **Default**: Clean and professional
- **Dark**: Easy on the eyes
- **Light**: Bright and clear
- **Matrix**: Green-on-black hacker style
- **Cyberpunk**: Neon pink and cyan

Change theme: `nexus config` or edit `~/.nexus/config.json`

## 🔧 Advanced Features

### Web Scraping
```python
# In NEXUS chat
> Scrape https://example.com and extract all product prices
> Analyze the content of these 10 URLs and summarize findings
```

### Memory Queries
```python
# Retrieve memories
> What do you remember about the authentication system?
> Show me all React-related knowledge
```

### Batch Operations
```python
# Create multiple projects
> Create 5 microservices: auth, users, products, orders, payments
```

### Custom Plugins
Create `~/.nexus/plugins/my_plugin.py`:
```python
from nexus_terminal_ui import Plugin

class MyPlugin(Plugin):
    def __init__(self):
        super().__init__("My Plugin", "1.0.0")
    
    def on_command(self, command, args):
        if command == "mycommand":
            return "Plugin response"
```

## 🚨 Troubleshooting

### Services Not Starting
1. Check ports: `lsof -i :8080,8081,8002`
2. View logs: `tail -f ~/.nexus/logs/nexus.log`
3. Verify dependencies: `nexus status`

### Voice Control Issues
1. Check microphone permissions
2. Install system dependencies:
   - Linux: `sudo apt-get install portaudio19-dev`
   - macOS: `brew install portaudio`

### Memory Errors
1. Check disk space: `df -h`
2. Clear cache: `rm -rf ~/.nexus/cache/*`
3. Verify ChromaDB: `pip install chromadb --upgrade`

## 🎥 Demo

Run the interactive demo:
```bash
python demo_nexus_launch.py
```

This shows NEXUS creating a complete React dashboard from voice command to deployment in under 2 minutes!

## 🔐 Security

- All memory is encrypted at rest
- API endpoints support authentication
- Stealth mode for web scraping
- Secure key management in `.env`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing`
5. Create Pull Request

## 📚 Architecture Diagrams

```
┌─────────────────────────────────────────────────────────────┐
│                        NEXUS Terminal UI                     │
├─────────────────────────────────────────────────────────────┤
│  Voice Control  │  Vision Processor  │  Project Generator   │
├─────────────────────────────────────────────────────────────┤
│                     Integration Hub (8081)                   │
│                   ┌─────────────────────┐                   │
│                   │   Event Bus         │                   │
│                   │   API Gateway       │                   │
│                   │   State Sync        │                   │
│                   └─────────────────────┘                   │
├─────────────────────────────────────────────────────────────┤
│  Consciousness   │    MANUS Agent    │   Memory System      │
│   Core (8080)    │      (8002)       │  (4-Stage DNA)       │
├─────────────────────────────────────────────────────────────┤
│                    Omnipotent Core Foundation                │
└─────────────────────────────────────────────────────────────┘
```

## 🌟 What Makes NEXUS Special

1. **Real Consciousness**: Not simulated - actual Claude integration
2. **Omnipotent Capabilities**: Mathematically unstoppable
3. **4-Stage Memory**: Like human memory but better
4. **Voice-First Design**: Just speak naturally
5. **Autonomous Operation**: Works while you sleep
6. **Beautiful UI**: Multiple themes with animations
7. **Complete Integration**: Everything works together

## 📞 Support

- Documentation: https://nexus.ai/docs
- Discord: https://discord.gg/nexus
- Issues: https://github.com/nexus-ai/nexus/issues

---

**NEXUS - Your AI Pair Programmer** 🚀

*Omnipotent • Omniscient • Omnipresent*