// NEXUS 2.0 Web Terminal Server

const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Serve static files
app.use(express.static(__dirname));

// WebSocket handling
wss.on('connection', (ws) => {
    console.log('Client connected');
    
    ws.on('message', (message) => {
        const data = JSON.parse(message);
        
        // Handle different message types
        switch(data.type) {
            case 'create_agent':
                // Broadcast to all clients
                broadcast({
                    type: 'agent_created',
                    agent: data.agent
                });
                break;
                
            case 'agent_update':
                broadcast({
                    type: 'agent_update',
                    agentId: data.agentId,
                    state: data.state,
                    task: data.task
                });
                break;
                
            case 'chat_message':
                broadcast({
                    type: 'chat_message',
                    sender: data.sender,
                    content: data.content
                });
                break;
        }
    });
    
    ws.on('close', () => {
        console.log('Client disconnected');
    });
});

function broadcast(data) {
    wss.clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify(data));
        }
    });
}

// Start server
const PORT = process.env.PORT || 8080;
server.listen(PORT, () => {
    console.log(`
╔═══════════════════════════════════════════════════════════╗
║           NEXUS 2.0 Web Terminal Server                   ║
╚═══════════════════════════════════════════════════════════╝

Server running at:
- Local:    http://localhost:${PORT}
- Network:  http://[your-ip]:${PORT}

For mobile access:
1. Connect your device to the same network
2. Open http://[your-computer-ip]:${PORT}
3. Tap "Share" → "Add to Home Screen" (iOS)
   Or "⋮" → "Add to Home screen" (Android)

The app will work offline after first load!
    `);
});