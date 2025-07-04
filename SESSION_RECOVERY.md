# SESSION_RECOVERY.md - Quick Recovery Guide

## 🚀 Quick Start Commands

### Launch NEXUS 2.0 Web Interface
```bash
cd nexus-web-app/ && npm start
# Opens at http://localhost:8080
```

### Launch Full System with AI Features
```bash
cd nexus-web-app/ && ./start-nexus-v5-complete.sh
# Starts backend (8000), MCP (3000), web (8080)
```

### Check What's Running
```bash
lsof -i :8080  # Web interface
lsof -i :8000  # Python backend
lsof -i :3000  # MCP server
ps aux | grep nexus  # All NEXUS processes
```

### Kill All NEXUS Processes
```bash
pkill -f nexus
pkill -f "node.*server"
```

## 📁 Key File Locations

### Main Entry Points
- Web Interface: `/nexus-web-app/unified-nexus-server.js`
- Python Backend: `/nexus-web-app/backend/nexus-consciousness-connector.py`
- MCP Server: `/nexus-mobile-project/backend/nexus-mcp/src/index.ts`
- Webinar Interface: `/nexus_webinar_interface.py`

### Configuration Files
- Web Config: `/nexus-web-app/package.json`
- Python Config: `/nexus_config_production.py`
- Docker Config: `/nexus-mobile-project/deployment/local/docker-compose.yml`

### Launch Scripts
- Simple: `/nexus-web-app/start-nexus-web.sh`
- Complete: `/nexus-web-app/start-nexus-v5-complete.sh`
- Docker: `/nexus-mobile-project/deployment/local/start-nexus.sh`

## 🔧 Common Issues & Fixes

### Issue: "Cannot find module" errors
```bash
cd nexus-web-app/ && npm install
cd nexus-mobile-project/backend/nexus-mcp/ && npm install
```

### Issue: Port already in use
```bash
# Find and kill process on port
lsof -ti:8080 | xargs kill -9
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

### Issue: Python module not found
```bash
pip install -r requirements.txt
pip install flask flask-cors flask-socketio
```

### Issue: Permission denied on scripts
```bash
chmod +x nexus-web-app/start-*.sh
chmod +x nexus-mobile-project/deployment/local/*.sh
```

### Issue: Database connection failed
```bash
# Start Redis
redis-server &

# Check PostgreSQL (if using Docker)
docker ps | grep postgres
```

## 🧪 Testing Commands

### Test Web Server
```bash
curl http://localhost:8080
```

### Test Python Backend
```bash
curl http://localhost:8000/api/health
```

### Test MCP Server
```bash
curl http://localhost:3000/health
```

### Check Logs
```bash
# Web logs
tail -f nexus-web-app/logs/web-server.log

# Python logs
tail -f nexus-web-app/logs/consciousness-core.log

# MCP logs
tail -f nexus-web-app/logs/mcp-server.log
```

## 🔍 Debugging Toolkit

### See All NEXUS Files
```bash
find . -name "*nexus*" -type f | grep -v node_modules | sort
```

### Check Git Status
```bash
git status --short | head -20
```

### View Active Ports
```bash
netstat -tlnp | grep -E "8080|8000|3000"
```

### Monitor Real-time Logs
```bash
tail -f nexus-web-app/logs/*.log
```

## 🆘 Emergency Reset

### Complete Reset
```bash
# Stop everything
pkill -f nexus
pkill -f node

# Clean up
rm -rf nexus-web-app/node_modules
rm -rf nexus-web-app/logs/*

# Reinstall
cd nexus-web-app/
npm install

# Restart
npm start
```

### Quick Restart
```bash
cd nexus-web-app/
pkill -f "node.*unified-nexus-server"
npm start
```

## 📝 Important Notes

1. **Primary Focus**: The web app in `nexus-web-app/` is the main interface
2. **Repository State**: Currently reorganizing 200+ files into clear structure
3. **Active Development**: Webinar interface is the most complete component
4. **Session Loss**: Use this guide + CLAUDE.md to quickly resume work

## 🎯 Next Actions After Recovery

1. Check CLAUDE.md for current state
2. Run cleanup script if not done: `python organize_nexus_repository.py`
3. Launch NEXUS 2.0: `cd nexus-web-app/ && npm start`
4. Verify at: http://localhost:8080