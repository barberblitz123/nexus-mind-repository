# NEXUS 2.0 Tabbed Interface Guide

## 🎯 Overview

Instead of cramming everything onto one screen, NEXUS 2.0 now uses a clean tab system where each tab shows a specific part of the application.

## 📑 The 6 Tabs

### Tab 1: Stage Manager (Ctrl+1)
```
╔══════════════ STAGE MANAGER ══════════════╗
║ 🎭 Agent Windows                           ║
║                                            ║
║ Active Agents (Focus)    Background Agents ║
║ ┌─────────────────┐     ┌────────────────┐║
║ │ Code Analyzer   │     │ Logger Agent   │║
║ │ State: Working  │     │ State: Idle    │║
║ │ Task: Analyzing │     └────────────────┘║
║ └─────────────────┘                        ║
║ ┌─────────────────┐                        ║
║ │ API Builder     │                        ║
║ │ State: Thinking │                        ║
║ └─────────────────┘                        ║
║                                            ║
║ [New Agent] [Grid] [Cascade] [Close]       ║
╚════════════════════════════════════════════╝
```
- Shows all your AI agents as visual windows
- Active agents on the left, background on the right
- See agent states and current tasks
- Control buttons at the bottom

### Tab 2: Chat (Ctrl+2)
```
╔══════════════ CHAT ════════════════════════╗
║ 💬 Agent Communication                      ║
║                                            ║
║ ┌────────────────────────────────────────┐ ║
║ │ You: Build a REST API                  │ ║
║ │ API Builder: Starting work on API      │ ║
║ │ API Builder: Created Flask structure   │ ║
║ │ You: Add authentication                │ ║
║ │ Security Agent: Implementing JWT auth  │ ║
║ │                                        │ ║
║ └────────────────────────────────────────┘ ║
║                                            ║
║ [Type a command...                ] [Send] ║
╚════════════════════════════════════════════╝
```
- Clean chat interface
- See all agent communications
- Type commands to create tasks
- Agents respond here

### Tab 3: Preview (Ctrl+3)
```
╔══════════════ PREVIEW ═════════════════════╗
║ 👁️ Preview & Output                        ║
║                                            ║
║ Active Preview: [Code] [Output] [Logs]     ║
║ ┌────────────────────────────────────────┐ ║
║ │ # api.py                               │ ║
║ │ from flask import Flask, jsonify       │ ║
║ │                                        │ ║
║ │ app = Flask(__name__)                  │ ║
║ │                                        │ ║
║ │ @app.route('/api/users')               │ ║
║ │ def get_users():                       │ ║
║ │     return jsonify({"users": []})      │ ║
║ └────────────────────────────────────────┘ ║
╚════════════════════════════════════════════╝
```
- View code, output, logs, or data
- Switch between different preview types
- See what agents are creating
- Syntax highlighting for code

### Tab 4: Terminal (Ctrl+4)
```
╔══════════════ TERMINAL ════════════════════╗
║ 🖥️ Terminal                                ║
║                                            ║
║ ┌────────────────────────────────────────┐ ║
║ │ $ python api.py                        │ ║
║ │ * Running on http://127.0.0.1:5000     │ ║
║ │ * Debug mode: on                       │ ║
║ │ $ curl http://127.0.0.1:5000/api/users │ ║
║ │ {"users": []}                          │ ║
║ │ $ _                                    │ ║
║ └────────────────────────────────────────┘ ║
║                                            ║
║ $ [Enter command...                     ]  ║
╚════════════════════════════════════════════╝
```
- Direct terminal access
- Run commands
- See command output
- Test what agents build

### Tab 5: Status (Ctrl+5)
```
╔══════════════ STATUS ══════════════════════╗
║ 📊 System Status                           ║
║                                            ║
║ Agent Status:                              ║
║ ┌────────────────────────────────────────┐ ║
║ │ Agent         Type    State    Duration│ ║
║ │ Code Analyzer analyzer working  45s    │ ║
║ │ API Builder   developer thinking 23s   │ ║
║ │ Test Runner   tester   idle     120s   │ ║
║ └────────────────────────────────────────┘ ║
║                                            ║
║ System Metrics:                            ║
║ Active Agents: 2                           ║
║ Background Agents: 1                       ║
║ Total Agents: 3                            ║
║ Focus: Code Analyzer                       ║
╚════════════════════════════════════════════╝
```
- Overview of all agents
- System metrics
- Activity log
- Performance monitoring

### Tab 6: Debug (Ctrl+6) 🆕
```
╔══════════════ DEBUG ═══════════════════════╗
║ 🐛 Debug Console                           ║
║                                            ║
║ Log Level: [INFO▼] Component: [ALL▼]       ║
║ [Clear] [Pause] [Save Logs]                ║
║                                            ║
║ Live Log Stream     Activity    Errors     ║
║ ┌──────────────┐   ┌────────┐ ┌─────────┐ ║
║ │[12:34:56] INFO│   │12:34:56│ │No errors│ ║
║ │Agent created  │   │Command │ │   🎉    │ ║
║ │[12:34:57] DEBUG│  │Analyze │ │         │ ║
║ │Processing task│   │12:34:57│ │         │ ║
║ │[12:34:58] WARN│   │System  │ │         │ ║
║ │Memory high    │   │Started │ │         │ ║
║ └──────────────┘   └────────┘ └─────────┘ ║
║                                            ║
║ Test Command: [debug command...] [Execute] ║
╚════════════════════════════════════════════╝
```
- Real-time logging with color coding
- Activity monitor for all system events
- Error tracker with full details
- Debug command execution
- Save logs for later analysis

## 🎮 How to Use

### Keyboard Shortcuts
- **Ctrl+1 to Ctrl+6**: Switch between tabs
- **Ctrl+N**: Create new agent
- **Ctrl+W**: Close current agent
- **Ctrl+Tab**: Cycle through tabs
- **Ctrl+Q**: Quit

### Workflow Example

1. **Start in Chat Tab (Ctrl+2)**
   - Type: "Build a web scraper for news sites"
   
2. **Auto-switches to Stage Manager (Ctrl+1)**
   - See new agents being created
   - Watch their states change
   
3. **Check Preview Tab (Ctrl+3)**
   - See the code being written
   - Switch to output to see results
   
4. **Use Terminal Tab (Ctrl+4)**
   - Test the scraper
   - Run additional commands
   
5. **Monitor in Status Tab (Ctrl+5)**
   - See all agent activity
   - Check system health

## 🚀 Launch Command

```bash
cd /workspaces/nexus-mind-repository/01_NEXUS_2.0_AGENT/core
python nexus_tabbed_interface.py
```

## 💡 Benefits of Tabbed Interface

1. **Focused Views**: Each tab shows one thing clearly
2. **Less Clutter**: No more cramped screens
3. **Easy Navigation**: Quick keyboard shortcuts
4. **Better Organization**: Related functions grouped together
5. **Scalable**: Easy to add more tabs for new features

---

The tabbed interface gives you a clean, organized way to manage multiple AI agents without overwhelming the screen!