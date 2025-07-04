# NEXUS 2.0 - Quick Reference Card

## 🚀 Essential Commands

### Start NEXUS (One Command)
```bash
cd /workspaces/nexus-mind-repository/nexus-web-app && npm start
```
Then open: http://localhost:3000

### Start Everything (Full Stack)
```bash
# Terminal 1: Web Server
cd nexus-web-app && npm start

# Terminal 2: Python Services
python nexus_integration_core.py

# Terminal 3: Manus (optional)
python manus_web_interface_v2.py
```

## 📁 Key Files

| Component | File | Purpose |
|-----------|------|---------|
| Web Server | `nexus-web-app/unified-nexus-server.js` | Main server |
| UI | `nexus-web-app/index.html` | User interface |
| Python Core | `nexus_integration_core.py` | Integration hub |
| Memory | `nexus_memory_core.py` | Memory system |
| Config | `nexus_config_production.py` | Settings |

## 🛠️ Quick Fixes

### Reset Everything
```bash
# Kill all NEXUS processes
pkill -f nexus
pkill -f node

# Clear memory
rm -rf nexus_memory_store/*

# Fresh start
cd nexus-web-app && npm start
```

### Check Status
```bash
# Is it running?
ps aux | grep -E "nexus|unified"

# Check ports
netstat -tunlp | grep -E "3000|5000"

# View logs
tail -f nexus_logs/*.log
```

### Test Connection
```bash
# Test web server
curl http://localhost:3000

# Test Python API
curl http://localhost:5000/health
```

## 🔗 URLs

- Main Interface: http://localhost:3000
- Simple Test: http://localhost:3000/test-simple.html
- Python API: http://localhost:5000
- Manus UI: http://localhost:5001

## 💡 Tips

1. **Use Chrome/Edge** for best compatibility
2. **Allow mic/camera** when prompted
3. **Check console** (F12) for errors
4. **Localhost only** for security

## 🆘 Emergency

If nothing works:
```bash
# Full reset
cd /workspaces/nexus-mind-repository
git stash
git pull
cd nexus-web-app
rm -rf node_modules package-lock.json
npm install
npm start
```

---
*Keep this card handy for quick recovery!*