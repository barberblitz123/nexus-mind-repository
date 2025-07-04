# NEXUS 2.0 Debug Tab Guide

## Overview
The Debug Tab is the 6th tab in the NEXUS 2.0 Tabbed Interface, providing comprehensive logging, monitoring, and debugging capabilities.

## How to Access

### Launch the Application
```bash
cd /workspaces/nexus-mind-repository/01_NEXUS_2.0_AGENT/core
python nexus_tabbed_interface.py
```

### Switch to Debug Tab
- Press `Ctrl+6` to switch to the Debug tab
- Or click on the "Debug" tab in the interface

## Debug Tab Features

### 1. Live Log Stream (Left Panel)
- Real-time display of all system logs
- Color-coded by log level:
  - 🔵 DEBUG: Cyan
  - 🟢 INFO: Green
  - 🟡 WARNING: Yellow
  - 🔴 ERROR: Red
  - 🔴🟡 CRITICAL: Red on Yellow

### 2. Activity Monitor (Middle Panel)
- Shows recent system activities
- Displays:
  - Timestamp
  - Activity type (Command, System, Agent)
  - Brief description

### 3. Error Tracker (Right Panel)
- Lists all errors with full details
- Shows error type, message, and context
- Helps identify and debug issues

### 4. Control Buttons
- **Log Level**: Filter logs by severity
- **Component Filter**: Show logs from specific components
- **Clear**: Clear the log display
- **Pause/Resume**: Pause log updates
- **Save Logs**: Save current session to file

### 5. Debug Command Line
Execute debug commands directly:

#### Available Commands:
- `log <level> <message>` - Log a test message
- `agent` - Show information about all agents
- `error` - Generate a test error
- `memory` - Show memory usage statistics
- `save` - Save session logs
- `level <level>` - Set logging level
- `help` - Show all available commands

## What Gets Logged

### Automatic Logging:
1. **System Events**
   - Application startup/shutdown
   - Component initialization
   - Configuration changes

2. **Agent Activities**
   - Agent creation/deletion
   - Task assignments
   - State changes
   - Completion status

3. **User Commands**
   - Chat commands
   - Terminal commands
   - Debug commands

4. **Errors**
   - Full error messages
   - Stack traces
   - Context information

## Log Files

Logs are saved to the `logs/` directory:
- `nexus_YYYYMMDD_HHMMSS.log` - Main log file
- `latest.log` - Symlink to most recent log
- `debug.log` - Detailed debug information
- `error_YYYYMMDD_HHMMSS.json` - Individual error reports
- `session_YYYYMMDD_HHMMSS.json` - Complete session data

## Tips for Debugging

1. **Monitor Agent Behavior**
   - Watch the Activity Monitor for agent state changes
   - Check if agents are completing tasks

2. **Track Commands**
   - See all user commands in the log stream
   - Verify commands are being processed correctly

3. **Error Investigation**
   - Check Error Tracker for any issues
   - Look at error context for debugging clues

4. **Performance Monitoring**
   - Use `memory` command to check resource usage
   - Watch for memory leaks or high CPU usage

5. **Save Important Sessions**
   - Click "Save Logs" to preserve debugging sessions
   - Useful for later analysis or bug reports

## Example Debug Session

1. Switch to Debug tab (`Ctrl+6`)
2. Create an agent in Chat tab (`Ctrl+2`)
3. Return to Debug tab to see:
   - Command logged in live stream
   - Agent creation in Activity Monitor
   - Any errors in Error Tracker
4. Execute debug command: `agent`
   - See detailed agent information
5. Save session: Click "Save Logs"

## Integration with Other Tabs

The Debug tab automatically logs activities from:
- **Stage Manager**: Agent window operations
- **Chat**: User commands and responses
- **Terminal**: Terminal commands
- **Status**: System metrics updates

All activities across the system are centralized in the Debug tab for easy monitoring and troubleshooting.