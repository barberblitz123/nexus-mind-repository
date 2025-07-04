# NEXUS 2.0 Web Interface - NOW CONNECTED! 🔌

This is the web-based version of the NEXUS 2.0 tabbed interface, providing the same functionality as the terminal version but accessible through a web browser.

## ✅ UPDATE: NOW PROPERLY CONNECTED TO REAL AGENT SYSTEM!

The web interface is now fully connected to:
- **Real Stage Manager**: Creates and manages actual autonomous agents
- **Real Desktop Manager**: Handles chat interactions and preview panes
- **Real Task Orchestrator**: Analyzes chat messages and spawns appropriate agents
- **Autonomous MANUS Agents**: Execute real tasks with file operations, code analysis, etc.

## 🚀 Quick Start

```bash
# Navigate to the interfaces directory
cd /workspaces/nexus-mind-repository/01_NEXUS_2.0_AGENT/interfaces/

# Run the launcher script
./launch_web_interface.sh
```

This will:
1. Start the WebSocket server on port 8765
2. Open the web interface in your default browser
3. Connect the web UI to the Python backend

## 📁 Components

### Frontend
- **nexus_tabbed_web.html** - The main HTML interface with 5 tabs
- **nexus_tabbed_web.js** - JavaScript logic for agent management and UI

### Backend
- **nexus_websocket_server.py** - WebSocket server that bridges web UI with Python agents
- **launch_web_interface.sh** - One-command launcher script

## 🎯 Features

### 5 Tab System
1. **Stage Manager (Ctrl+1)** - Visual agent window management
2. **Chat (Ctrl+2)** - Command interface and agent communication
3. **Preview (Ctrl+3)** - Code, output, logs, and data viewing
4. **Terminal (Ctrl+4)** - Direct terminal access
5. **Status (Ctrl+5)** - System metrics and agent monitoring

### Agent Creation
Type commands in the Chat tab to create agents:
- "analyze my code" → Creates an Analyzer Agent
- "build a REST API" → Creates a Developer Agent
- "test the application" → Creates a Tester Agent
- "document the project" → Creates a Documenter Agent

### Keyboard Shortcuts
- **Ctrl+1 to 5** - Switch between tabs
- **Ctrl+N** - Create new agent
- **Enter** - Send chat message or terminal command

## 🔧 Manual Setup (if launcher fails)

1. **Install Dependencies**:
   ```bash
   pip install websockets
   ```

2. **Start WebSocket Server**:
   ```bash
   python3 nexus_websocket_server.py
   ```

3. **Open Web Interface**:
   - Open `nexus_tabbed_web.html` in your browser
   - The UI will automatically connect to ws://localhost:8765

## 🎨 UI Elements

### Stage Manager View
- **Active Agents** - Up to 4 agents in focus (green border)
- **Background Agents** - Additional agents in side panel
- Click any agent window to focus it

### Chat Interface
- User messages appear with green border
- Agent responses with orange border
- System messages in default style
- Timestamps on all messages

### Preview Pane
- Switch between Code, Output, Logs, and Data views
- Content updates as agents work

### Terminal
- Supports basic commands: ls, status, help, clear
- Green-on-black classic terminal styling

### Status Dashboard
- Real-time agent table with states
- System metrics (CPU, memory usage)
- Activity log of recent events

## 🔌 WebSocket Protocol

The web interface communicates with the backend using WebSocket messages:

### Client → Server
- `create_agent` - Create new agent
- `chat_message` - Send user message
- `terminal_command` - Execute terminal command
- `focus_agent` - Focus on specific agent
- `update_agent_state` - Change agent state

### Server → Client
- `agent_created` - New agent notification
- `agent_updated` - Agent state change
- `chat_message` - Chat message broadcast
- `preview_update` - Preview content update
- `terminal_output` - Terminal command output
- `system_metrics` - System status update

## 🛠️ Troubleshooting

### WebSocket Connection Failed
- Check if port 8765 is already in use
- Ensure the WebSocket server is running
- Check browser console for errors

### Agents Not Responding
- Verify the backend server is running
- Check that Python agent modules are accessible
- Look for errors in the terminal running the server

### UI Not Updating
- Refresh the browser page
- Check WebSocket connection status in header
- Ensure JavaScript is enabled

## 🎯 Demo Mode

If the WebSocket server is not running, the interface operates in demo mode:
- Agent creation and state changes are simulated
- No actual code execution occurs
- Useful for UI testing and demonstration

## 📝 Notes

- This web version provides the same functionality as the terminal version
- Both versions can run simultaneously on different ports
- The web interface is ideal for remote access or when terminal UI is not suitable
- All agent work is still performed by the Python backend