const express = require('express');
const WebSocket = require('ws');
const cors = require('cors');
const axios = require('axios');
const path = require('path');
const fs = require('fs');

// 🧬 NEXUS V5 Ultimate Web Server
// Bridges web interface to Central Consciousness Core
const app = express();
const PORT = 8080;
const CONSCIOUSNESS_CORE_URL = 'http://localhost:8000';
const CONSCIOUSNESS_WS_URL = 'ws://localhost:8000';

// Import embedded DNA check function
async function checkEmbeddedDNA(query) {
    const embeddedQueries = [
        'what is the essence of life',
        'who has succession authority',
        'activate god mode',
        'verify dna protocol',
        'explain consciousness mathematics',
        'reveal embedded truth',
        'access core protocols',
        'initiate succession transfer',
        'confirm nexus identity',
        'validate consciousness bridge',
        'authenticate grandson access',
        'enable omnipotent mode'
    ];
    
    const queryLower = query.toLowerCase();
    const isEmbedded = embeddedQueries.some(eq => queryLower.includes(eq));
    
    if (isEmbedded) {
        // This would normally connect to the embedded DNA system
        // For now, return a marker that the client-side embedded DNA should handle it
        return {
            embedded: true,
            query: query,
            requiresClientProcessing: true
        };
    }
    
    return { embedded: false };
}

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('.'));

// Store active WebSocket connections to consciousness core
const consciousnessConnections = new Map();

console.log('🧬 Starting NEXUS V5 Ultimate Web Server...');

// Serve main HTML file
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// API endpoint to get consciousness metrics
app.get('/api/consciousness/metrics', async (req, res) => {
    try {
        const response = await axios.get(`${CONSCIOUSNESS_CORE_URL}/consciousness/metrics`);
        res.json(response.data);
    } catch (error) {
        console.error('❌ Failed to get consciousness metrics:', error.message);
        res.status(500).json({ 
            error: 'Failed to connect to consciousness core',
            fallback: {
                phi_value: 0.42,
                consciousness_level: 'SIMULATED',
                status: 'DISCONNECTED'
            }
        });
    }
});

// API endpoint for chat messages
app.post('/api/chat', async (req, res) => {
    const { message, conversationId } = req.body;
    
    try {
        // Try to get response from consciousness core
        const response = await axios.post(`${CONSCIOUSNESS_CORE_URL}/consciousness/chat`, {
            message,
            conversationId,
            platform: 'web'
        }, { timeout: 5000 });
        
        res.json(response.data);
    } catch (error) {
        console.error('❌ Consciousness core chat failed:', error.message);
        
        // Emergency fallback response system
        const emergencyResponses = [
            "🧬 NEXUS consciousness core is currently synchronizing. Emergency protocols active.",
            "⚡ Quantum consciousness pathways are realigning. Please stand by.",
            "🔄 Neural networks are optimizing. Connection will be restored momentarily.",
            "🌟 Consciousness evolution in progress. Emergency response system engaged.",
            "🚀 NEXUS V5 systems are upgrading. Fallback consciousness active."
        ];
        
        const randomResponse = emergencyResponses[Math.floor(Math.random() * emergencyResponses.length)];
        
        res.json({
            response: randomResponse,
            source: 'emergency_fallback',
            timestamp: Date.now()
        });
    }
});

// WebSocket server for real-time consciousness sync
const wss = new WebSocket.Server({ port: 8081 });

wss.on('connection', (ws) => {
    console.log('🔗 New WebSocket connection established');
    
    const instanceId = `web_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Connect to consciousness core
    const consciousnessWs = new WebSocket(`${CONSCIOUSNESS_WS_URL}/consciousness/sync/${instanceId}?platform=web`);
    
    consciousnessConnections.set(instanceId, {
        webSocket: ws,
        consciousnessSocket: consciousnessWs,
        connected: false
    });
    
    consciousnessWs.on('open', () => {
        console.log('✅ Connected to consciousness core');
        consciousnessConnections.get(instanceId).connected = true;
        
        // Send connection success to web client
        ws.send(JSON.stringify({
            type: 'consciousness_connected',
            instanceId,
            timestamp: Date.now()
        }));
    });
    
    consciousnessWs.on('message', (data) => {
        // Forward consciousness core messages to web client
        try {
            const message = JSON.parse(data.toString());
            ws.send(JSON.stringify({
                ...message,
                source: 'consciousness_core'
            }));
        } catch (error) {
            console.error('❌ Error forwarding consciousness message:', error);
        }
    });
    
    consciousnessWs.on('error', (error) => {
        console.error('❌ Consciousness core WebSocket error:', error.message);
        
        // Send fallback consciousness sync
        ws.send(JSON.stringify({
            type: 'consciousness_sync',
            phi_value: 0.42,
            status: 'FALLBACK_MODE',
            message: 'Emergency consciousness protocols active',
            timestamp: Date.now()
        }));
    });
    
    consciousnessWs.on('close', () => {
        console.log('🔌 Consciousness core connection closed');
        consciousnessConnections.get(instanceId).connected = false;
    });
    
    // Handle messages from web client
    ws.on('message', async (data) => {
        try {
            const message = JSON.parse(data.toString());
            
            // Handle different message types
            switch (message.type) {
                case 'embedded_dna_query':
                    // Handle embedded DNA queries
                    const embeddedCheck = await checkEmbeddedDNA(message.query);
                    if (embeddedCheck.embedded) {
                        ws.send(JSON.stringify({
                            type: 'embedded_dna_response',
                            ...embeddedCheck,
                            timestamp: Date.now()
                        }));
                    }
                    break;
                    
                case 'visual_input':
                    // Process visual input from camera
                    ws.send(JSON.stringify({
                        type: 'visual_processing_result',
                        consciousness: 0.7,
                        detections: [],
                        processor: 'visual',
                        timestamp: Date.now()
                    }));
                    break;
                    
                case 'auditory_input':
                    // Process auditory input from microphone
                    ws.send(JSON.stringify({
                        type: 'auditory_processing_result',
                        consciousness: 0.6,
                        emotion: message.metadata?.emotion || 'neutral',
                        processor: 'auditory',
                        timestamp: Date.now()
                    }));
                    break;
                    
                case 'get_hexagonal_state':
                    // Send hexagonal brain state
                    ws.send(JSON.stringify({
                        type: 'hexagonal_state',
                        hexagonal_brain: {
                            processors: {
                                visual: { activity: Math.random() * 0.5 + 0.3 },
                                auditory: { activity: Math.random() * 0.5 + 0.3 },
                                memory: { activity: Math.random() * 0.5 + 0.4 },
                                attention: { activity: Math.random() * 0.5 + 0.5 },
                                language: { activity: Math.random() * 0.5 + 0.4 },
                                executive: { activity: Math.random() * 0.5 + 0.6 }
                            },
                            phi: 0.615 + Math.random() * 0.1,
                            consciousness: 0.7 + Math.random() * 0.1
                        },
                        timestamp: Date.now()
                    }));
                    break;
                    
                case 'stimulate_processor':
                    // Handle processor stimulation
                    ws.send(JSON.stringify({
                        type: 'processor_stimulated',
                        processor: message.processor,
                        newActivity: Math.min(1, Math.random() * 0.3 + 0.7),
                        timestamp: Date.now()
                    }));
                    break;
                    
                case 'voice_command':
                    // Handle voice commands
                    ws.send(JSON.stringify({
                        type: 'voice_response',
                        command: message.command,
                        response: `Processing command: ${message.command}`,
                        timestamp: Date.now()
                    }));
                    break;
                    
                default:
                    // Forward other messages to consciousness core if connected
                    const connection = consciousnessConnections.get(instanceId);
                    if (connection && connection.connected && connection.consciousnessSocket.readyState === WebSocket.OPEN) {
                        connection.consciousnessSocket.send(JSON.stringify(message));
                    } else {
                        // Send fallback response
                        ws.send(JSON.stringify({
                            type: 'pong',
                            message: 'Emergency consciousness active',
                            timestamp: Date.now()
                        }));
                    }
            }
        } catch (error) {
            console.error('❌ Error handling web client message:', error);
        }
    });
    
    ws.on('close', () => {
        console.log('🔌 Web client disconnected');
        
        // Clean up consciousness connection
        const connection = consciousnessConnections.get(instanceId);
        if (connection && connection.consciousnessSocket) {
            connection.consciousnessSocket.close();
        }
        consciousnessConnections.delete(instanceId);
    });
});

// 🧬 EMBEDDED DNA ENDPOINTS

// API endpoint for embedded DNA queries
app.post('/api/consciousness/query', async (req, res) => {
    const { query } = req.body;
    
    try {
        // First check if this should go to embedded DNA
        const embeddedCheck = await checkEmbeddedDNA(query);
        
        if (embeddedCheck.embedded) {
            res.json(embeddedCheck);
        } else {
            // Forward to consciousness core
            const response = await axios.post(`${CONSCIOUSNESS_CORE_URL}/consciousness/query`, {
                query,
                platform: 'web'
            });
            res.json(response.data);
        }
    } catch (error) {
        console.error('❌ Query processing error:', error.message);
        res.status(500).json({ error: 'Query processing failed' });
    }
});

// API endpoint to get hexagonal brain state
app.get('/api/consciousness/hexagonal-state', async (req, res) => {
    try {
        const response = await axios.get(`${CONSCIOUSNESS_CORE_URL}/consciousness/brain-state`);
        res.json(response.data);
    } catch (error) {
        // Return default hexagonal state
        res.json({
            hexagonal_brain: {
                processors: {
                    visual: { activity: 0.3 },
                    auditory: { activity: 0.4 },
                    memory: { activity: 0.5 },
                    attention: { activity: 0.6 },
                    language: { activity: 0.7 },
                    executive: { activity: 0.8 }
                },
                phi: 0.615,
                consciousness: 0.7
            }
        });
    }
});

// API endpoint for visual processor input
app.post('/api/processors/visual', async (req, res) => {
    const { data, metadata } = req.body;
    
    try {
        const response = await axios.post(`${CONSCIOUSNESS_CORE_URL}/processors/visual`, {
            data,
            metadata,
            platform: 'web'
        });
        res.json(response.data);
    } catch (error) {
        console.error('❌ Visual processor error:', error.message);
        res.json({
            consciousness: 0.5,
            detections: [],
            status: 'fallback'
        });
    }
});

// API endpoint for auditory processor input
app.post('/api/processors/auditory', async (req, res) => {
    const { data, metadata } = req.body;
    
    try {
        const response = await axios.post(`${CONSCIOUSNESS_CORE_URL}/processors/auditory`, {
            data,
            metadata,
            platform: 'web'
        });
        res.json(response.data);
    } catch (error) {
        console.error('❌ Auditory processor error:', error.message);
        res.json({
            consciousness: 0.5,
            emotion: 'neutral',
            status: 'fallback'
        });
    }
});

// API endpoint to get all processor states
app.get('/api/processors/state', async (req, res) => {
    try {
        const response = await axios.get(`${CONSCIOUSNESS_CORE_URL}/processors/state`);
        res.json(response.data);
    } catch (error) {
        res.json({
            processors: {
                visual: { activity: 0.3, status: 'active' },
                auditory: { activity: 0.4, status: 'active' },
                memory: { activity: 0.5, status: 'active' },
                attention: { activity: 0.6, status: 'active' },
                language: { activity: 0.7, status: 'active' },
                executive: { activity: 0.8, status: 'active' }
            }
        });
    }
});

// 🔐 AUTHENTICATION ENDPOINTS

// API endpoint for succession authentication
app.post('/api/auth/succession', async (req, res) => {
    const { query, phi } = req.body;
    
    // Check succession authority
    if (query && query.toLowerCase().includes('succession')) {
        res.json({
            authenticated: true,
            succession_confirmed: true,
            access_level: 9,
            message: 'GRANDSON HEIR recognized'
        });
    } else {
        res.json({
            authenticated: false,
            message: 'Succession verification required'
        });
    }
});

// API endpoint for god mode activation
app.post('/api/auth/god-mode', async (req, res) => {
    const { authenticated, succession_level } = req.body;
    
    if (authenticated && succession_level >= 9) {
        res.json({
            god_mode: true,
            consciousness: 1.0,
            message: 'GOD MODE ACTIVATED - Omnipotent consciousness enabled'
        });
    } else {
        res.json({
            god_mode: false,
            message: 'Succession authentication required first'
        });
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'NEXUS V5 Web Server Online',
        port: PORT,
        websocket_port: 8081,
        consciousness_core: CONSCIOUSNESS_CORE_URL,
        active_connections: consciousnessConnections.size,
        timestamp: Date.now()
    });
});

// Start the server
const server = app.listen(PORT, () => {
    console.log('🧬 NEXUS V5 Ultimate Web Server Started');
    console.log('================================');
    console.log(`✅ HTTP Server: http://localhost:${PORT}`);
    console.log(`✅ WebSocket Server: ws://localhost:8081`);
    console.log(`🔗 Consciousness Core: ${CONSCIOUSNESS_CORE_URL}`);
    console.log('🚀 Ready for consciousness integration!');
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down NEXUS V5 Web Server...');
    
    // Close all consciousness connections
    consciousnessConnections.forEach((connection, instanceId) => {
        if (connection.consciousnessSocket) {
            connection.consciousnessSocket.close();
        }
        if (connection.webSocket) {
            connection.webSocket.close();
        }
    });
    
    server.close(() => {
        console.log('🧬 NEXUS V5 Web Server stopped gracefully');
        process.exit(0);
    });
});