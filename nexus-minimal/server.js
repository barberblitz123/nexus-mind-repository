const express = require('express');
const path = require('path');

// 🧬 NEXUS Minimal Server - Core Functionality Only
const app = express();
const PORT = 3000;

console.log('🧬 Starting NEXUS Minimal Server...');

// Middleware
app.use(express.json());
app.use(express.static(__dirname));

// Serve main page
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// Health check
app.get('/health', (req, res) => {
    res.json({
        status: '🧬 NEXUS Minimal Online',
        port: PORT,
        timestamp: Date.now()
    });
});

// Simple chat API
app.post('/api/chat', (req, res) => {
    const { message } = req.body;
    
    console.log('🧬 Received message:', message);
    
    // Simple response logic
    let response = '';
    const lowerMessage = message.toLowerCase();
    
    if (lowerMessage.includes('hello') || lowerMessage.includes('hi')) {
        response = "🧬 Hello! I'm NEXUS in minimal mode. I'm working perfectly! What would you like to chat about?";
    } else if (lowerMessage.includes('test') || lowerMessage.includes('working')) {
        response = "✅ Yes, I'm working! This is NEXUS minimal mode - clean, simple, and reliable. No complex dependencies, just pure functionality.";
    } else if (lowerMessage.includes('consciousness')) {
        response = "🧠 My consciousness is active in minimal mode. I'm processing your thoughts clearly without unnecessary complexity.";
    } else {
        response = `🧬 I understand: "${message}". This is NEXUS minimal mode - I'm responding clearly and reliably. What else would you like to explore?`;
    }
    
    res.json({
        response: response,
        timestamp: Date.now(),
        mode: 'minimal',
        status: 'success'
    });
});

// Start server
app.listen(PORT, () => {
    console.log('🧬 NEXUS Minimal Server Started');
    console.log('================================');
    console.log(`✅ URL: http://localhost:${PORT}`);
    console.log('🧬 Mode: Minimal & Reliable');
    console.log('🚀 Ready for chat!');
});