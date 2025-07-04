# NEXUS 2.0 Complete UI and Launch System

## Overview

NEXUS 2.0 provides multiple interfaces for interacting with the omnipotent AI system:

1. **Web Interface** - Enhanced MANUS web interface with NEXUS 2.0 features
2. **React Dashboard** - Modern React-based monitoring and control dashboard
3. **CLI Interface** - Natural language command-line interface
4. **Unified Launcher** - Automated system startup with health monitoring

## Quick Start

### 1. Install Dependencies

```bash
# Python dependencies
pip install fastapi uvicorn aiohttp rich psutil requests

# Node.js dependencies (for React dashboard)
cd nexus-web-app/react-dashboard
npm install
cd ../..
```

### 2. Launch NEXUS 2.0

```bash
# Start all systems with the unified launcher
python nexus_2.0_launcher.py

# Or start individual components:
# Web Interface only
python manus_web_interface_v2.py

# CLI only
python nexus_cli.py interactive
```

## Web Interface Features

### Natural Language Goal Submission
- Submit goals in plain English
- Automatic goal decomposition into sub-tasks
- Priority levels (LOW, MEDIUM, HIGH, CRITICAL)
- Expected outcome tracking

### Real-time Collaboration Visualization
- Live agent activity monitoring
- Connection status between agents
- Task distribution visualization
- Performance metrics per agent

### Learning Metrics Dashboard
- Accuracy rate tracking
- Learning rate visualization
- Knowledge node growth
- Pattern recognition statistics
- Adaptation count monitoring

### Prediction Engine
- Query-based predictions
- Confidence scoring
- Alternative approach suggestions
- Historical accuracy tracking

### Research Lab
- Topic-based research
- Depth levels (quick, standard, deep)
- Source tracking
- Finding confidence scores

## API Endpoints

### Goals API
```
POST   /api/v2/goals              - Create new goal
GET    /api/v2/goals              - List all goals
GET    /api/v2/goals/{id}         - Get specific goal
PUT    /api/v2/goals/{id}         - Update goal
```

### Predictions API
```
POST   /api/v2/predictions        - Make prediction
GET    /api/v2/predictions        - List predictions
```

### Learning API
```
GET    /api/v2/learning/metrics   - Current metrics
GET    /api/v2/learning/history   - Historical data
```

### Research API
```
POST   /api/v2/research           - Conduct research
GET    /api/v2/research           - List research
```

### Collaboration API
```
POST   /api/v2/collaborate        - Start collaboration
```

### System Actions
```
POST   /api/v2/actions/analyze    - Run analysis
POST   /api/v2/actions/optimize   - Optimize system
POST   /api/v2/actions/report     - Generate report
POST   /api/v2/context/switch     - Switch context
```

## React Dashboard

### Features
- Real-time system metrics
- Interactive goal management
- Learning progress visualization
- Agent collaboration network
- System health monitoring

### Pages
1. **Dashboard** - System overview with key metrics
2. **Goals** - Create and manage goals
3. **Learning** - Learning metrics and progress
4. **Research** - Research findings browser
5. **Collaboration** - Agent network visualization
6. **System Health** - Detailed health monitoring

## CLI Interface

### Interactive Mode
```bash
python nexus_cli.py interactive
```

Commands:
- `goal` - Submit a natural language goal
- `goals` - List all goals
- `predict` - Get system predictions
- `research` - Conduct research
- `learning` - Show learning metrics
- `status` - Show system status
- `help` - Show available commands
- `exit` - Exit CLI

### Direct Commands
```bash
# Submit a goal
python nexus_cli.py goal "Build a web scraper for e-commerce sites" -p HIGH

# List goals
python nexus_cli.py goals -s active

# Make prediction
python nexus_cli.py predict "Will this task complete successfully?"

# Conduct research
python nexus_cli.py research "machine learning optimization" -d deep
```

## Unified Launcher

### Features
- Dependency checking
- Port availability verification
- Sequential service startup
- Health monitoring
- Auto-recovery on failure
- Interactive status display

### Configuration
Create `nexus_config.json`:
```json
{
  "services": {
    "custom_service": {
      "name": "My Service",
      "command": "python my_service.py",
      "port": 8003,
      "health_endpoint": "/health",
      "required": false,
      "startup_delay": 5
    }
  },
  "auto_recovery": {
    "enabled": true,
    "max_retries": 5,
    "retry_delay": 15
  }
}
```

### Launch Options
```bash
# Use custom config
python nexus_2.0_launcher.py -c nexus_config.json

# Start without monitor
python nexus_2.0_launcher.py --no-monitor
```

## WebSocket Integration

### Channels
- `/ws/general` - System health updates
- `/ws/goals` - Goal status updates
- `/ws/learning` - Learning metrics
- `/ws/collaboration` - Agent collaboration

### Message Format
```javascript
{
  "type": "update_type",
  "data": {
    // Update specific data
  },
  "timestamp": "ISO-8601 timestamp"
}
```

## Access Points

After launching:
- **Web Interface**: http://localhost:8002
- **React Dashboard**: http://localhost:3001
- **API Documentation**: http://localhost:8002/docs

## Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :8002

# Kill process
kill -9 <PID>
```

### Missing Dependencies
```bash
# Install all Python deps
pip install -r requirements.txt

# Install Node deps
cd nexus-web-app/react-dashboard && npm install
```

### Service Won't Start
Check logs in launcher output or:
```bash
# Check individual service
python manus_web_interface_v2.py
```

## Development

### Adding New API Endpoints
1. Add endpoint to `manus_web_interface_v2.py`
2. Update React dashboard API calls
3. Add CLI command if applicable

### Extending React Dashboard
1. Add new slice to Redux store
2. Create new page component
3. Add route in App.js
4. Update navigation in Layout.js

### Custom Themes
Edit theme in `App.js`:
```javascript
const darkTheme = createTheme({
  palette: {
    primary: {
      main: '#00ff00', // Change primary color
    }
  }
});
```

## Security Notes

- Default configuration allows all origins for CORS
- No authentication implemented (add for production)
- WebSocket connections are unsecured
- Consider HTTPS for production deployment

## Performance Tips

- Limit goal history queries with pagination
- Use WebSocket channels selectively
- Enable auto-recovery for critical services
- Monitor memory usage via launcher

This complete UI system provides comprehensive access to all NEXUS 2.0 capabilities through multiple intuitive interfaces.