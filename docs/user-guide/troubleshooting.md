# Troubleshooting Guide

This guide helps you resolve common issues with NEXUS. For issues not covered here, visit our support forum or contact support@nexus-mind.ai.

## Table of Contents
- [Installation Issues](#installation-issues)
- [Voice Control Problems](#voice-control-problems)
- [Performance Issues](#performance-issues)
- [AI Assistant Issues](#ai-assistant-issues)
- [Editor Problems](#editor-problems)
- [Connection Issues](#connection-issues)
- [Project Issues](#project-issues)
- [Debugging Problems](#debugging-problems)
- [Error Messages](#common-error-messages)
- [Recovery Procedures](#recovery-procedures)

## Installation Issues

### Python Dependencies Failed

**Problem**: `pip install` fails with dependency conflicts

**Solutions**:

1. **Use Virtual Environment**
   ```bash
   python -m venv nexus_env
   source nexus_env/bin/activate  # On Windows: nexus_env\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Update pip**
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Install Dependencies Individually**
   ```bash
   pip install numpy==1.21.0
   pip install tensorflow==2.8.0
   # Continue with other dependencies
   ```

4. **Use conda Instead**
   ```bash
   conda create -n nexus python=3.9
   conda activate nexus
   conda install --file requirements.txt
   ```

### Node.js Module Errors

**Problem**: `npm install` fails or modules not found

**Solutions**:

1. **Clear npm Cache**
   ```bash
   npm cache clean --force
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **Use Correct Node Version**
   ```bash
   nvm use 16  # or the version specified in .nvmrc
   npm install
   ```

3. **Permission Issues (macOS/Linux)**
   ```bash
   sudo npm install -g npm@latest
   npm install
   ```

### NEXUS Won't Start

**Problem**: Application fails to launch

**Diagnostic Steps**:

1. **Check Logs**
   ```bash
   tail -f nexus_logs/nexus_debug_*.log
   ```

2. **Verify Services**
   ```bash
   python nexus_cli.py status
   ```

3. **Test Components**
   ```bash
   # Test backend
   python test_nexus_integration.py
   
   # Test frontend
   cd nexus-web-app
   npm test
   ```

**Common Fixes**:

1. **Port Conflicts**
   ```bash
   # Check if ports are in use
   lsof -i :3000  # Frontend
   lsof -i :5000  # Backend
   
   # Kill conflicting processes or change ports in config
   ```

2. **Missing Configuration**
   ```bash
   cp nexus_config.example.json nexus_config.json
   # Edit configuration file
   ```

3. **Database Issues**
   ```bash
   python nexus_db_migrations.py
   ```

## Voice Control Problems

### Microphone Not Detected

**Problem**: NEXUS doesn't recognize microphone

**Solutions**:

1. **Check System Permissions**
   - **Windows**: Settings > Privacy > Microphone
   - **macOS**: System Preferences > Security & Privacy > Microphone
   - **Linux**: Check PulseAudio/ALSA settings

2. **Test Microphone**
   ```voice
   "Test microphone input"
   ```
   
   Or manually:
   ```bash
   python nexus_voice_control.py --test-mic
   ```

3. **Select Different Microphone**
   - Open Settings: `Ctrl/Cmd + ,`
   - Navigate to Voice Control
   - Select correct input device

### Voice Commands Not Recognized

**Problem**: NEXUS doesn't understand commands

**Solutions**:

1. **Run Voice Calibration**
   ```voice
   "Calibrate voice recognition"
   ```

2. **Check Language Settings**
   ```voice
   "Change language to English US"
   ```

3. **Improve Recognition**:
   - Speak clearly and at normal pace
   - Reduce background noise
   - Use headset microphone
   - Increase microphone gain

4. **Reset Voice Profile**
   ```bash
   rm -rf ~/.nexus/voice_profile
   python nexus_voice_control.py --recalibrate
   ```

### Voice Activation Not Working

**Problem**: "Hey NEXUS" doesn't activate

**Solutions**:

1. **Adjust Sensitivity**
   ```json
   // In nexus_config.json
   {
     "voice": {
       "activation_sensitivity": 0.7  // Increase for easier activation
     }
   }
   ```

2. **Use Alternative Activation**:
   - Press `Ctrl/Cmd + Shift + V`
   - Click microphone icon
   - Use push-to-talk mode

3. **Check CPU Usage**
   - High CPU can affect wake word detection
   - Close unnecessary applications
   - Enable GPU acceleration if available

## Performance Issues

### Slow Response Times

**Problem**: NEXUS responds slowly to commands

**Solutions**:

1. **Check System Resources**
   ```bash
   # Monitor NEXUS resource usage
   python nexus_performance_analyzer.py
   ```

2. **Optimize Settings**:
   ```json
   {
     "performance": {
       "max_workers": 4,
       "cache_size": "2GB",
       "enable_gpu": true
     }
   }
   ```

3. **Clear Caches**
   ```bash
   python nexus_cli.py clear-cache
   ```

4. **Disable Unnecessary Features**:
   - Turn off real-time collaboration if not needed
   - Reduce AI suggestion frequency
   - Disable unused extensions

### High Memory Usage

**Problem**: NEXUS consuming too much RAM

**Solutions**:

1. **Limit Memory Usage**
   ```json
   {
     "memory": {
       "max_heap_size": "4G",
       "max_buffer_size": "1G"
     }
   }
   ```

2. **Close Unused Projects**
   ```voice
   "Close all inactive projects"
   ```

3. **Restart Services**
   ```bash
   python nexus_cli.py restart
   ```

### UI Freezing

**Problem**: Interface becomes unresponsive

**Solutions**:

1. **Check Browser Console**
   - Press F12
   - Look for JavaScript errors
   - Report errors to support

2. **Disable Hardware Acceleration**
   - Browser settings > Advanced > System
   - Toggle "Use hardware acceleration"

3. **Use Different Browser**
   - Chrome/Edge recommended
   - Firefox as alternative
   - Safari for macOS

## AI Assistant Issues

### AI Not Responding

**Problem**: AI assistant doesn't generate responses

**Solutions**:

1. **Check API Keys**
   ```bash
   python nexus_cli.py check-api-keys
   ```

2. **Verify Connection**
   ```bash
   curl https://api.nexus-mind.ai/health
   ```

3. **Use Local Model**
   ```json
   {
     "ai": {
       "use_local_model": true,
       "model_path": "./models/nexus-local"
     }
   }
   ```

### Poor Code Suggestions

**Problem**: AI suggestions are irrelevant or incorrect

**Solutions**:

1. **Update Context**
   ```voice
   "Refresh project context"
   ```

2. **Provide More Information**:
   - Add comments describing intent
   - Use descriptive variable names
   - Include type hints

3. **Train on Your Code**
   ```voice
   "Learn from this project"
   ```

4. **Adjust AI Settings**:
   ```json
   {
     "ai": {
       "suggestion_confidence": 0.8,
       "context_window": 2000,
       "language_specific": true
     }
   }
   ```

## Editor Problems

### Syntax Highlighting Not Working

**Problem**: Code appears without colors

**Solutions**:

1. **Reinstall Language Support**
   ```voice
   "Reinstall Python language support"
   ```

2. **Check File Associations**
   - Settings > File Associations
   - Ensure extensions mapped correctly

3. **Reset Editor Cache**
   ```bash
   rm -rf ~/.nexus/editor_cache
   ```

### IntelliSense Not Working

**Problem**: No code completions appearing

**Solutions**:

1. **Rebuild Project Index**
   ```voice
   "Rebuild project index"
   ```

2. **Check Language Server**
   ```bash
   python nexus_cli.py check-lsp
   ```

3. **Install Missing Types**
   ```bash
   # For Python
   pip install types-requests types-flask
   
   # For TypeScript
   npm install --save-dev @types/node @types/react
   ```

## Connection Issues

### Cannot Connect to Backend

**Problem**: "Failed to connect to NEXUS server"

**Solutions**:

1. **Check Services Running**
   ```bash
   ps aux | grep nexus
   netstat -an | grep 5000
   ```

2. **Restart Backend**
   ```bash
   python nexus_cli.py restart-backend
   ```

3. **Check Firewall**
   - Allow localhost connections
   - Add NEXUS to firewall exceptions

### WebSocket Disconnections

**Problem**: Real-time features stop working

**Solutions**:

1. **Check Network Stability**
   ```bash
   ping -c 10 localhost
   ```

2. **Increase Timeout**
   ```json
   {
     "websocket": {
       "ping_interval": 30,
       "ping_timeout": 10,
       "reconnect_attempts": 5
     }
   }
   ```

3. **Use Polling Fallback**
   ```json
   {
     "realtime": {
       "transport": ["websocket", "polling"]
     }
   }
   ```

## Project Issues

### Cannot Open Project

**Problem**: Project fails to load

**Solutions**:

1. **Check Project Path**
   ```bash
   ls -la /path/to/project
   ```

2. **Repair Project**
   ```voice
   "Repair project configuration"
   ```

3. **Re-import Project**
   ```voice
   "Remove project from workspace"
   "Import project from folder"
   ```

### Git Integration Not Working

**Problem**: Git commands fail

**Solutions**:

1. **Check Git Installation**
   ```bash
   git --version
   which git
   ```

2. **Configure Git Path**
   ```json
   {
     "git": {
       "path": "/usr/bin/git"
     }
   }
   ```

3. **Reset Git Integration**
   ```bash
   python nexus_cli.py reset-git
   ```

## Debugging Problems

### Breakpoints Not Hit

**Problem**: Debugger skips breakpoints

**Solutions**:

1. **Check Debug Configuration**
   - Ensure correct file paths
   - Verify entry point
   - Check working directory

2. **Source Maps (JavaScript)**
   ```json
   {
     "debug": {
       "sourceMaps": true,
       "outFiles": ["${workspaceFolder}/dist/**/*.js"]
     }
   }
   ```

3. **Python Path Issues**
   ```json
   {
     "python": {
       "defaultInterpreterPath": "/usr/bin/python3"
     }
   }
   ```

### Variables Not Showing

**Problem**: Can't inspect variables while debugging

**Solutions**:

1. **Enable Variable Loading**
   ```json
   {
     "debug": {
       "showSubVariables": true,
       "variablePageSize": 100
     }
   }
   ```

2. **Optimize Debug Build**
   - Disable optimizations
   - Include debug symbols
   - Use debug configuration

## Common Error Messages

### "NEXUS Core Not Initialized"

**Cause**: Core services failed to start

**Fix**:
```bash
python nexus_cli.py init-core
python nexus_cli.py start
```

### "Memory Limit Exceeded"

**Cause**: Project too large for allocated memory

**Fix**:
1. Increase memory limit in settings
2. Exclude unnecessary folders (node_modules, etc.)
3. Enable incremental processing

### "Voice Model Not Found"

**Cause**: Voice recognition models not downloaded

**Fix**:
```bash
python nexus_cli.py download-models --voice
```

### "API Rate Limit Reached"

**Cause**: Too many AI requests

**Fix**:
1. Enable request caching
2. Use local models
3. Upgrade API plan

## Recovery Procedures

### Complete Reset

**When nothing else works**:

1. **Backup Settings**
   ```bash
   cp -r ~/.nexus ~/.nexus_backup
   ```

2. **Clean Install**
   ```bash
   python nexus_cli.py uninstall
   rm -rf ~/.nexus
   python nexus_cli.py install
   ```

3. **Restore Settings**
   ```bash
   cp ~/.nexus_backup/settings.json ~/.nexus/
   ```

### Safe Mode

**Start NEXUS with minimal features**:

```bash
python launch_nexus_enhanced.py --safe-mode
```

Safe mode disables:
- Extensions
- Voice control
- AI features
- Custom configurations

### Debug Mode

**Get detailed debugging information**:

```bash
python launch_nexus_enhanced.py --debug --log-level=DEBUG
```

This creates detailed logs in `nexus_logs/debug_*.log`

### Emergency Commands

**Voice Commands Always Available**:
- "Emergency stop" - Stops all operations
- "Reset NEXUS" - Restarts core services
- "Safe mode" - Switches to safe mode
- "Show logs" - Displays recent errors

## Getting Further Help

### Diagnostic Information

When contacting support, include:

1. **System Info**
   ```bash
   python nexus_cli.py sysinfo > nexus_diagnostic.txt
   ```

2. **Recent Logs**
   ```bash
   tail -n 1000 nexus_logs/nexus_debug_*.log > recent_logs.txt
   ```

3. **Configuration** (remove sensitive data)
   ```bash
   cat nexus_config.json | grep -v "api_key\|password" > config_sanitized.json
   ```

### Support Channels

- **Documentation**: Say "Open documentation"
- **Community Forum**: [community.nexus-mind.ai](https://community.nexus-mind.ai)
- **GitHub Issues**: [github.com/nexus-mind/nexus/issues](https://github.com/nexus-mind/nexus/issues)
- **Email Support**: support@nexus-mind.ai
- **Emergency Hotline**: Available for enterprise customers

### Self-Diagnosis Tool

Run comprehensive diagnostics:

```bash
python nexus_cli.py diagnose
```

This tool:
- Checks all components
- Verifies configurations
- Tests connections
- Suggests fixes
- Generates support ticket

Remember: Most issues have simple solutions. Stay calm, follow the steps, and NEXUS will be back up and running quickly!