# NEXUS 2.0 Web Version - Launch Instructions

## Quick Start

### Step 1: Install Dependencies
```bash
cd /workspaces/nexus-mind-repository/01_NEXUS_2.0_AGENT/web_version
npm install express ws
```

### Step 2: Launch the Server
```bash
node stage_desktop_server.js
```

### Step 3: Open in Browser
Open your browser and navigate to:
```
http://localhost:3001/nexus_stage_desktop_web.html
```

## What You'll See

1. **Stage Manager (Left Side)**
   - Shows all active agents
   - Color-coded status indicators
   - Click agents to view their output

2. **Desktop Manager (Right Side)**
   - Preview tabs at the top
   - Chat interface at the bottom
   - Type commands to create agents

## Example Commands to Try

- "Build a Python API for user management"
- "Analyze the code in this repository"
- "Create a test suite for the authentication module"
- "Research best practices for microservices"

## Features

- **Real-time Updates**: See agents working in real-time
- **Multiple Agents**: Run many agents simultaneously
- **Tab Management**: Each agent gets its own preview tab
- **WebSocket Communication**: Live updates without refreshing

## Integration with Python Agents

To connect with actual Python agents instead of simulated ones:
```bash
# Run the integration script (coming next)
python nexus_web_integration.py
```

## Troubleshooting

- **Port Already in Use**: Change PORT in stage_desktop_server.js
- **Cannot Connect**: Ensure no firewall blocking port 3001
- **Blank Page**: Check browser console for errors

## Architecture

```
Browser (nexus_stage_desktop_web.html)
    ↓ WebSocket
Server (stage_desktop_server.js)
    ↓ Optional Integration
Python Agents (nexus_web_integration.py)
```