# NEXUS Live Preview System

A powerful real-time preview system for web development that supports multiple frameworks with hot reload, terminal preview, and performance monitoring.

## Features

### 1. **Preview Server**
- Local development server with WebSocket support
- Automatic hot reload on file changes
- Multi-framework support (React, Vue, Vanilla JS, Static HTML)
- Comprehensive error handling and recovery

### 2. **Terminal Preview**
- ASCII art rendering of web content
- Component hierarchy visualization
- Interactive element detection
- CSS style inspection

### 3. **Web Preview**
- Full browser preview with hot reload injection
- Device emulation for responsive testing
- Performance metrics tracking
- State synchronization

### 4. **Synchronization**
- Bi-directional updates between code and preview
- Component state preservation
- Interaction event capture
- Real-time performance monitoring

### 5. **Preview Features**
- Component isolation and playground
- Props experimentation
- State inspection tools
- Route navigation support

## Installation

```bash
# Install dependencies
pip install -r requirements_live_preview.txt

# Run the demo setup
python demo_live_preview.py
```

## Usage

### Basic Usage

```bash
# Preview current directory
python nexus_live_preview.py

# Preview specific directory
python nexus_live_preview.py --root ./my-project

# Custom ports
python nexus_live_preview.py --port 3000 --ws-port 3001
```

### Command Line Options

- `--port`: HTTP server port (default: 3000)
- `--ws-port`: WebSocket port (default: 3001)
- `--root`: Root directory to serve (default: current directory)
- `--entry`: Entry file name (default: index.html)
- `--framework`: Framework type (auto, react, vue, vanilla, static)
- `--no-terminal`: Disable terminal preview
- `--no-hot-reload`: Disable hot reload
- `--no-performance`: Disable performance monitoring

### Framework-Specific Usage

#### React
```bash
python nexus_live_preview.py --root ./react-app --framework react
```

#### Vue
```bash
python nexus_live_preview.py --root ./vue-app --framework vue
```

#### Vanilla JavaScript
```bash
python nexus_live_preview.py --root ./vanilla-app --framework vanilla
```

#### Static HTML
```bash
python nexus_live_preview.py --root ./static-site --framework static
```

## Demo Projects

Run the demo script to create example projects:

```bash
python demo_live_preview.py
```

This creates four demo projects:
1. **React Counter App** - Interactive counter with state management
2. **Vue Todo App** - Todo list with Vue 3
3. **Vanilla JS Canvas** - Interactive drawing canvas
4. **Static Website** - Responsive static site

## Architecture

### Core Components

1. **PreviewServer**
   - Main HTTP server
   - Route handling
   - Hot reload injection

2. **WebSocketHandler**
   - Real-time communication
   - State synchronization
   - Event broadcasting

3. **TerminalRenderer**
   - HTML to ASCII conversion
   - Component tree visualization
   - Style table generation

4. **FileWatcher**
   - File system monitoring
   - Change detection
   - Debouncing

5. **PerformanceMonitor**
   - CPU/Memory tracking
   - Response time measurement
   - Metrics aggregation

### Hot Reload Flow

```
File Change → FileWatcher → WebSocket Broadcast → Client Reload
     ↓                                                    ↓
Terminal Update ← TerminalRenderer ← HTML Content ← Server Update
```

## API Endpoints

### HTTP Endpoints

- `GET /` - Serve index with hot reload injection
- `GET /api/performance` - Get performance metrics
- `GET /api/component/{id}` - Get component state
- `POST /api/interaction` - Handle user interactions
- `Static /*` - Serve static files

### WebSocket Messages

#### Client → Server
```javascript
{
  "type": "state_update",
  "componentId": "counter",
  "state": { "count": 5 }
}

{
  "type": "interaction",
  "element": "BUTTON",
  "id": "submit-btn",
  "eventType": "click"
}
```

#### Server → Client
```javascript
{
  "type": "reload",
  "file": "/path/to/changed/file.js",
  "timestamp": "2024-01-01T12:00:00"
}

{
  "type": "interaction_received",
  "data": { ... }
}
```

## Terminal Preview

The terminal preview provides a text-based representation of your web page:

```
┌─ Welcome to React Counter Demo ─┐
│                                 │
│  Component Hierarchy            │
│  ├─ div.container              │
│  │  ├─ div.counter             │
│  │  │  ├─ h1                   │
│  │  │  │  └─ "React Counter"   │
│  │  │  ├─ div.count-display    │
│  │  │  │  └─ "0"               │
│  │  │  └─ button (3)           │
│  │  └─ p                       │
│                                 │
│  Interactive Elements:          │
│  3 buttons                      │
└─────────────────────────────────┘
```

## Performance Monitoring

Real-time metrics tracking:

```json
{
  "uptime": 120.5,
  "metrics": {
    "cpu_usage": [{"value": 15.2, "timestamp": 0.1}],
    "memory_usage": [{"value": 45.8, "timestamp": 0.1}],
    "response_times": [{"value": 12.5, "timestamp": 0.1}],
    "render_times": [{"value": 8.3, "timestamp": 0.1}]
  },
  "summary": {
    "avg_cpu": 14.8,
    "avg_memory": 44.2,
    "avg_response_time": 11.9,
    "avg_render_time": 7.8
  }
}
```

## Advanced Features

### Component Playground

The system includes a component playground for testing components in isolation:

```python
# In your preview setup
playground = ComponentPlayground("react")
playground.register_component("Button", {
    "text": "string",
    "onClick": "function",
    "disabled": "boolean"
})
```

### Device Emulation

Test responsive designs with device presets:

```python
# Available devices
devices = ["iphone-12", "ipad", "desktop", "galaxy-s21"]

# Viewport is automatically adjusted based on device
```

### Custom Build Commands

For projects with build steps:

```python
config = PreviewConfig(
    build_command="npm run build",
    dev_command="npm run dev"
)
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Use different ports
   python nexus_live_preview.py --port 3001 --ws-port 3002
   ```

2. **Hot reload not working**
   - Check WebSocket connection in browser console
   - Ensure file extensions are watched (.js, .jsx, .css, etc.)
   - Verify no firewall blocking WebSocket

3. **Terminal preview garbled**
   - Ensure terminal supports Unicode
   - Try disabling terminal preview: `--no-terminal`

4. **Performance issues**
   - Disable performance monitoring: `--no-performance`
   - Limit file watching scope with specific root directory

## Integration with NEXUS

The Live Preview system integrates seamlessly with other NEXUS components:

```python
from nexus_live_preview import PreviewServer, PreviewConfig
from nexus_unified_tools import ToolRegistry

# Register preview as a NEXUS tool
tool_registry = ToolRegistry()
tool_registry.register_tool(
    "live_preview",
    PreviewServer,
    config=PreviewConfig(port=3000)
)
```

## Contributing

When adding new features:

1. Extend `PreviewServer` for new endpoints
2. Add framework support in `FrameworkDetector`
3. Enhance `TerminalRenderer` for better visualization
4. Update `WebSocketHandler` for new message types

## License

Part of the NEXUS Mind Repository - MIT License