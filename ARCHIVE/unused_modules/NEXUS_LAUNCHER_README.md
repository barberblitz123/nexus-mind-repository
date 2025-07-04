# NEXUS Launcher - Ultra-Fast AI System Startup

The NEXUS Launcher provides a VSCode-like instant startup experience for the entire NEXUS ecosystem.

## Features

### ⚡ Lightning Fast Startup
- Parallel service initialization
- Smart dependency management
- Sub-second launch times with `--fast` mode
- Automatic port conflict resolution

### 🎯 Single Entry Point
```bash
nexus                    # Start with defaults
nexus --voice --vision   # Enable voice and vision
nexus --project ./myapp  # Open specific project
nexus --daemon           # Run in background
```

### 🎨 Theme Support
- **Dark** (default): Sleek dark interface
- **Light**: Clean light theme
- **Matrix**: Hacker-style green theme

### 🔊 Voice Control (Optional)
- Wake word: "Hey NEXUS" or "NEXUS"
- Natural language commands
- Project creation and navigation
- Real-time voice processing

### 👁️ Vision Processing (Optional)
- Face detection
- Text recognition (OCR)
- Object detection
- Color analysis
- Screen capture
- Webcam integration

### 🔄 Auto-Update System
- Background version checking
- Seamless updates
- Rollback support
- Disable with `--no-update`

### 😈 Daemon Mode
- System tray integration
- Background service
- Quick launch from tray
- Minimal resource usage

## Installation

```bash
# Install core dependencies
pip install -r nexus_launcher_requirements.txt

# Optional: Voice control
pip install SpeechRecognition pyttsx3 pyaudio

# Optional: Vision processing
pip install opencv-python pytesseract pyautogui

# Optional: System tray (for daemon mode)
pip install pystray pillow
```

## Usage

### Basic Commands

```bash
# Start NEXUS
nexus

# Start with voice and vision
nexus --voice --vision

# Fast mode (core services only)
nexus --fast

# Daemon mode (background)
nexus --daemon

# Stop daemon
nexus stop

# Check status
nexus status

# Restart
nexus restart
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `--voice` | Enable voice control |
| `--vision` | Enable vision processing |
| `--project PATH` | Open specific project |
| `--theme THEME` | Set UI theme (dark/light/matrix) |
| `--port PORT` | API port (default: 8002) |
| `--daemon` | Run in background |
| `--fast` | Fast startup mode |
| `--no-update` | Disable auto-updates |
| `--debug` | Enable debug output |

### Configuration

Configuration is stored in `~/.nexus/config.json`:

```json
{
  "version": "2.0.0",
  "theme": "dark",
  "api_port": 8002,
  "auto_update": true,
  "startup_services": [
    "consciousness_core",
    "manus_web",
    "unified_memory"
  ]
}
```

### Service Architecture

1. **Core Services** (Always started):
   - Consciousness Core (port 8080)
   - MANUS Enhanced (port 8002)
   - Unified Memory System (port 8003)

2. **Optional Services**:
   - Voice Control (port 8004) - with `--voice`
   - Vision Processor (port 8005) - with `--vision`
   - Web Interface (port 3000)
   - React Dashboard (port 3001)

### Performance

- **Cold start**: ~2-3 seconds (all services)
- **Fast mode**: <1 second (core only)
- **Daemon mode**: Instant (pre-loaded)

### Troubleshooting

**Port conflicts**: The launcher automatically kills conflicting NEXUS processes

**Missing dependencies**: Install with `pip install -r nexus_launcher_requirements.txt`

**Voice not working**: Ensure microphone permissions and pyaudio is installed

**Vision errors**: Install OpenCV and optionally tesseract for OCR

## Examples

### Start for Development
```bash
nexus --project ./my-ai-app --theme dark
```

### Production Deployment
```bash
nexus --daemon --port 80 --no-update
```

### AI Assistant Mode
```bash
nexus --voice --vision --fast
```

### Check Running Services
```bash
nexus status
```

## Architecture

The launcher uses:
- **AsyncIO** for parallel startup
- **Rich** for beautiful terminal UI
- **PSUtil** for process management
- **FastAPI** for service endpoints
- **WebSockets** for real-time communication

## Contributing

The launcher is designed to be extensible. Add new services in the config or create plugins for additional functionality.

---

Built with 🧠 by NEXUS - The Omnipotent AI System