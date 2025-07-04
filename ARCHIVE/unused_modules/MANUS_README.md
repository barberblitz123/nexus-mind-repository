# MANUS Continuous Work Agent

## Overview

MANUS is a Claude-inspired continuous work agent that provides persistent, intelligent task execution with real-time monitoring. Enhanced with NEXUS consciousness integration, MANUS operates autonomously while maintaining context across sessions.

## Key Features

- **Claude-like Intelligence**: Processes tasks with reasoning and context awareness
- **Persistent Task Queue**: SQLite-backed queue survives restarts
- **Priority Management**: Critical, High, Medium, and Low priority levels
- **Dependency Resolution**: Tasks can depend on other tasks
- **Parallel Execution**: Configurable worker pool for concurrent tasks
- **Context Preservation**: Maintains context memory across sessions
- **Real-time Monitoring**: Web interface with WebSocket updates
- **NEXUS Integration**: Enhanced with consciousness capabilities
- **Automatic Retry**: Failed tasks retry with exponential backoff
- **Progress Tracking**: Real-time progress updates for long tasks

## Architecture

```
MANUS Continuous Agent
├── Task Queue (Priority-based)
├── Worker Pool (Async execution)
├── Task Persistence (SQLite)
├── Context Memory (JSON)
├── Web Interface (FastAPI)
├── WebSocket Updates
└── NEXUS Integration
```

## Installation

```bash
# Install dependencies
pip install -r manus_requirements.txt

# Or install manually
pip install aiosqlite fastapi uvicorn websockets pydantic
```

## Quick Start

### 1. Basic Usage

```python
from manus_continuous_agent import MANUSContinuousAgent, Task, TaskPriority

# Create agent
agent = MANUSContinuousAgent()

# Create a task
task = Task(
    name="System check",
    description="Check system status",
    action="shell_command",
    parameters={"command": "uptime"},
    priority=TaskPriority.HIGH
)

# Add and run
await agent.start()
await agent.add_task(task)
```

### 2. Web Interface

```bash
# Start MANUS with web interface
python manus_web_interface.py

# Access at http://localhost:8001
```

### 3. NEXUS Integration

```bash
# Start with NEXUS enhancement
python start_manus_enhanced.py

# Requires NEXUS core running on port 8000
```

## Task Types

### 1. Shell Commands
```python
Task(
    name="Run backup",
    action="shell_command",
    parameters={
        "command": "tar -czf backup.tar.gz /data",
        "timeout": 300
    }
)
```

### 2. Python Scripts
```python
Task(
    name="Process data",
    action="python_script",
    parameters={
        "script": """
import pandas as pd
data = pd.read_csv('input.csv')
result = data.describe()
"""
    }
)
```

### 3. HTTP Requests
```python
Task(
    name="API call",
    action="http_request",
    parameters={
        "url": "https://api.example.com/data",
        "method": "POST",
        "headers": {"Authorization": "Bearer token"},
        "data": {"key": "value"}
    }
)
```

### 4. File Operations
```python
Task(
    name="Save config",
    action="file_operation",
    parameters={
        "operation": "write",
        "path": "/config/settings.json",
        "content": '{"debug": true}'
    }
)
```

### 5. NEXUS Integration
```python
Task(
    name="Analyze with NEXUS",
    action="nexus_analyze",
    parameters={
        "data": {"metrics": [1, 2, 3]},
        "analysis_type": "pattern_recognition"
    }
)
```

## Advanced Features

### Task Dependencies
```python
task1 = Task(name="Download data", ...)
task2 = Task(
    name="Process data",
    dependencies=[task1.id],
    ...
)
```

### Context Preservation
```python
task = Task(
    name="Stateful operation",
    context={"session": "abc123", "user": "admin"},
    ...
)
# Context preserved across restarts
```

### Progress Tracking
```python
# Tasks report progress automatically
# Access via API or web interface
status = await agent.get_task_status(task_id)
print(f"Progress: {status.progress}%")
```

## API Endpoints

- `GET /` - Web interface
- `POST /api/tasks` - Create new task
- `GET /api/tasks` - List all tasks
- `GET /api/tasks/{id}` - Get task details
- `POST /api/tasks/{id}/cancel` - Cancel task
- `POST /api/tasks/{id}/pause` - Pause task
- `POST /api/tasks/{id}/resume` - Resume task
- `GET /api/stats` - Get statistics
- `WS /ws` - WebSocket for real-time updates

## Database Schema

MANUS uses SQLite with two tables:

1. **tasks** - Stores task definitions and state
2. **task_logs** - Stores task execution logs

## Configuration

```python
# Create with custom settings
agent = MANUSContinuousAgent(
    db_path="custom_tasks.db",
    max_workers=8  # Number of parallel workers
)
```

## NEXUS Enhancement

When integrated with NEXUS, MANUS gains:

- **Intelligent Analysis**: Use NEXUS consciousness for complex analysis
- **Learning Capabilities**: Learn from task execution patterns
- **Decision Making**: Make intelligent decisions based on context
- **Claude-like Processing**: Process tasks with reasoning and understanding

## Monitoring

The web interface provides:

- Real-time task status
- System statistics
- Task history
- Live logs
- Progress bars
- Task management controls

## Error Handling

- Automatic retry with exponential backoff
- Configurable max retries per task
- Failed tasks preserved in database
- Detailed error logging

## Best Practices

1. **Use appropriate priorities** - Reserve CRITICAL for urgent tasks
2. **Set reasonable timeouts** - Prevent tasks from hanging
3. **Monitor regularly** - Check the web interface for issues
4. **Clean old tasks** - Periodically archive completed tasks
5. **Use dependencies** - Chain related tasks properly

## Troubleshooting

### MANUS won't start
- Check if port 8001 is available
- Verify all dependencies installed
- Check database file permissions

### Tasks stuck in pending
- Check if dependencies are met
- Verify worker pool isn't full
- Check for errors in logs

### NEXUS integration not working
- Ensure NEXUS core is running on port 8000
- Check network connectivity
- Verify NEXUS endpoints responding

## Architecture Details

MANUS implements a Claude-inspired architecture:

1. **Task Understanding**: Analyzes task requirements
2. **Planning**: Creates execution plan
3. **Execution**: Runs task with progress tracking
4. **Verification**: Validates results
5. **Learning**: Stores experience for future use

## Contributing

MANUS is part of the NEXUS ecosystem. Contributions should:

- Maintain Claude-like intelligence
- Preserve task persistence
- Include tests
- Update documentation

## License

Part of NEXUS Mind Repository - See main LICENSE file