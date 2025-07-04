# NEXUS 2.0 - REAL Autonomous Agent System

## 🚀 What Makes This REAL (Not Simulation)

This is **NOT** a UI simulation. NEXUS 2.0 agents:
- ✅ **Execute actual Python code** via subprocess
- ✅ **Run real shell commands** (with security filters)
- ✅ **Create and modify files** on the filesystem
- ✅ **Have persistent memory** that learns from tasks
- ✅ **Log every action** for complete auditability
- ✅ **Export logs easily** for analysis

## 🎯 Quick Start - Simple Execution

```bash
# Option 1: Launch Everything (Recommended)
python launch_real_nexus.py
# Choose option 3 for both Terminal + Web interfaces

# Option 2: Terminal Only
cd core
python nexus_tabbed_interface.py

# Option 3: Web Only
cd interfaces
./launch_web_interface.sh
```

## 📦 What You Get

### 1. Real Agent Execution
```python
# When you type: "create agent to analyze my code"
# The agent ACTUALLY:
- Runs 'find . -name "*.py"' in subprocess
- Parses Python files with AST
- Executes analysis code
- Returns REAL results
```

### 2. Comprehensive Logging System
- **Colored Terminal Output**: Easy to read logs
- **File Logging**: Everything saved to `nexus_logs/`
- **Real-time Debug Tab**: See logs as they happen
- **Easy Export**: One command to export all logs

### 3. Auditing Capabilities
- Every agent action is tracked
- Task execution times recorded
- Error patterns analyzed
- Success/failure rates monitored
- Complete audit trail in `nexus_logs/audit/`

## 📋 How to Use It

### Creating Agents (Natural Language)
```
"create agent to analyze my repository"
"make an agent for building a REST API"
"spawn agent to deploy my application"
```

### Viewing Logs

**Terminal UI**:
- Press Tab to navigate to Debug tab (6th tab)
- See live logs, activity monitor, error tracker

**Export Logs**:
```bash
# Logs are auto-saved to nexus_logs/
ls nexus_logs/

# View latest log
tail -f nexus_logs/latest.log

# Export specific date range
# (In debug console or via API)
```

### Understanding Log Files

```
nexus_logs/
├── nexus_20240703_143022.log    # Main log file
├── latest.log                    # Symlink to current log
├── debug.log                     # Detailed debug info
├── agents/                       # Per-agent logs
├── errors/                       # Error details with traces
├── audit/                        # Audit trail
└── exports/                      # Exported log bundles
```

## 🔧 Configuration

### Agent Capabilities

Agents have different capabilities based on type:

**Developer Agent**:
- ✅ Execute code
- ✅ Write files
- ✅ Read files
- ⛔ Limited shell access

**Analyst Agent**:
- ✅ Execute code
- ✅ Read files
- ⛔ No file writing
- ⛔ No shell access

**DevOps Agent**:
- ✅ Full shell access
- ✅ Network access
- ✅ File operations

## 🔍 Debugging & Monitoring

### Debug Commands (in Debug Tab)
```
log info Testing the logger
log error Simulating an error
agent                        # Show all agents
memory                       # Show memory usage
save                        # Force save logs
level DEBUG                 # Set log level
help                        # Show all commands
```

### Monitoring Metrics
```python
# Automatically tracked:
- Task execution times
- Success/failure rates
- Error frequency by component
- Agent performance metrics
- System resource usage
```

## 🌐 Web Interface Integration

The web interface is **FULLY CONNECTED** to the real agent system:

1. Open http://localhost:8000
2. Type in chat to create agents
3. Agents execute REAL code
4. See results in real-time
5. Access logs via UI

## 📊 Log Export & Analysis

### Export Logs Programmatically
```python
from nexus_logger import get_logger

logger = get_logger()

# Export last 7 days as JSON
export_path = logger.export_logs(
    start_date="2024-06-26",
    end_date="2024-07-03",
    format="json"
)

# Export as CSV for analysis
export_path = logger.export_logs(format="csv")
```

### Analyze Agent Performance
```python
# Get metrics summary
metrics = logger.get_metrics_summary()
print(f"Total tasks: {metrics['task_metrics']['total_tasks']}")
print(f"Average time: {metrics['task_metrics']['average_time']:.2f}s")
print(f"Error rate: {metrics['total_errors'] / metrics['task_metrics']['total_tasks'] * 100:.1f}%")
```

## ⚠️ Security Considerations

- Agents run in isolated directories (`/tmp/nexus_agents/`)
- Dangerous commands are filtered
- All actions are logged for audit
- Resource limits can be configured

## 🐛 Troubleshooting

### "Module not found" Error
```bash
# Install required dependencies
pip install textual websockets colorama psutil
```

### "Permission denied" Error
```bash
# Make scripts executable
chmod +x launch_real_nexus.py
chmod +x interfaces/launch_web_interface.sh
```

### Logs Not Appearing
- Check `nexus_logs/` directory exists
- Ensure write permissions
- Look for errors in `nexus_logs/errors/`

## 🚀 Advanced Usage

### Custom Agent Types
```python
# In nexus_connector.py, add new agent type:
elif agent_type == "security":
    capabilities.can_read_files = True
    capabilities.can_execute_code = True
    capabilities.can_access_network = False
```

### Batch Task Execution
```python
# Create multiple agents for parallel tasks
tasks = [
    "analyze security vulnerabilities",
    "check code quality metrics",
    "generate API documentation"
]

for i, task in enumerate(tasks):
    agent_id = f"batch-agent-{i}"
    await connector.create_agent(agent_id, f"Agent {i}", "analyst")
    await connector.execute_agent_task(agent_id, task)
```

## 📝 Summary

**This is REAL**:
- Agents execute actual code—not simulations
- Every action is logged and auditable
- Logs are easy to access and export
- System learns from successes and failures
- Full visibility into what's happening

**Simple to Use**:
- Natural language commands
- One-click log export
- Real-time monitoring
- Graceful shutdown saves everything

**Start Now**:
```bash
python launch_real_nexus.py
```

Choose option 3, and watch your agents come to life! 🎆