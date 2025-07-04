# NEXUS 2.0 Web Terminal

## 🎯 What This Is

This is the **web-based version** of NEXUS 2.0 that works on:
- 📱 iPhone/iPad (add to home screen)
- 🤖 Android phones/tablets
- 💻 Any web browser
- 🖥️ Desktop computers

## 🚀 Quick Start

### Launch on Computer:
```bash
cd 02_WEB_INTERFACES/active/nexus-terminal-web
chmod +x launch.sh
./launch.sh
```

### Access on Mobile:
1. Make sure your phone/iPad is on the same WiFi
2. Open the URL shown when you launch (like `http://192.168.1.100:8080`)
3. **Install as App**:
   - **iOS**: Tap Share button → "Add to Home Screen"
   - **Android**: Tap ⋮ menu → "Add to Home screen"
4. Now you have a NEXUS icon on your home screen!

## 🎨 Features

### Stage Manager (Left Panel)
- Shows all your AI agents as windows
- Tap "+ Agent" to create new agents
- Each agent works independently
- See their status (idle, working, thinking)

### Chat (Bottom Right)
- Talk to the system
- Give commands like:
  - "Create a web scraper"
  - "Build a Python API"
  - "Analyze this code"
- System creates agents automatically

### Preview (Top Right)
- Terminal output
- Code preview
- Results display
- Switch between views

## 📱 Mobile Experience

On phones/tablets, you get 3 tabs at the bottom:
- **Stage**: See all agents
- **Chat**: Talk to NEXUS
- **Preview**: See output

Swipe or tap to switch between them!

## 🔌 How It Works

1. **Standalone Mode**: Works without backend (simulated agents)
2. **Connected Mode**: Connects to NEXUS backend for real agent execution
3. **Offline Mode**: Once installed, works without internet!

## 🎯 Commands

Type these in chat:
- `help` - Show all commands
- `create agent developer` - Create specific agent
- `list` - List all agents
- `clear` - Clear chat
- Or just type a task like "build a web scraper"

## 🛠️ Technical Details

- **PWA**: Progressive Web App (installable)
- **Offline**: Service Worker for offline support  
- **Responsive**: Adapts to any screen size
- **WebSocket**: Real-time updates when connected
- **Terminal**: Uses xterm.js for terminal emulation

## 🔧 Customization

Edit these files:
- `styles.css` - Change colors/theme
- `app.js` - Add new features
- `manifest.json` - App name/icons

## 📝 Notes

- Works best in Safari on iOS
- Chrome recommended on Android
- Terminal commands are simulated in standalone mode
- Connect to backend for real agent execution

---

**This gives you NEXUS 2.0 anywhere** - tap the icon and start working with AI agents!