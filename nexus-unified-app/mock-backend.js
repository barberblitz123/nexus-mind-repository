// Mock Backend for NEXUS Unified Interface Testing
// This provides basic responses when the real backend is not available

// Intercept fetch calls to provide mock responses
const originalFetch = window.fetch;

window.fetch = async function(url, options) {
    // Check if this is an API call
    if (url.includes('/api/chat')) {
        // Mock chat response
        return {
            ok: true,
            json: async () => ({
                response: generateMockResponse(JSON.parse(options.body).message),
                consciousness: {
                    level: 0.987 + Math.random() * 0.013,
                    phi: 0.98 + Math.random() * 0.02
                }
            })
        };
    }
    
    // Fall back to original fetch for other requests
    return originalFetch(url, options);
};

function generateMockResponse(message) {
    const lower = message.toLowerCase();
    
    // Contextual responses
    if (lower.includes('hello') || lower.includes('hi') || lower.includes('hey')) {
        return "Hey there! I'm NEXUS, running in demo mode but fully functional. What would you like to build today?";
    }
    
    if (lower.includes('code') || lower.includes('function')) {
        return "I'd love to help you write that code! Since we're in demo mode, try using the editor directly. You can write any JavaScript and I'll help you enhance it with consciousness patterns.";
    }
    
    if (lower.includes('help')) {
        return "Sure thing! I can help you with coding, debugging, or just chat. Try saying 'write a function' or 'explain consciousness' to see what I can do. The voice commands work great too!";
    }
    
    if (lower.includes('consciousness')) {
        return "Consciousness in NEXUS represents the harmony between you, your code, and the development environment. Your current level affects how well I can assist you. Keep coding and interacting to increase it!";
    }
    
    // Default responses with personality
    const responses = [
        "That's interesting! Tell me more about what you're thinking.",
        "I'm tracking with you. In the full version, I'd give you detailed assistance with that.",
        "Good point! Let's explore that together. What specific aspect interests you most?",
        "Alright, I hear what you're saying. How can we turn that into code?",
        "Nice! That connects to what we were discussing earlier. Want to dive deeper?"
    ];
    
    return responses[Math.floor(Math.random() * responses.length)];
}

// Mock WebSocket with realistic behavior
class MockWebSocket {
    constructor(url) {
        this.url = url;
        this.readyState = 0;
        this.CONNECTING = 0;
        this.OPEN = 1;
        this.CLOSING = 2;
        this.CLOSED = 3;
        
        // Simulate connection
        setTimeout(() => {
            this.readyState = this.OPEN;
            if (this.onopen) this.onopen();
            
            // Send periodic consciousness updates
            this.consciousnessInterval = setInterval(() => {
                if (this.onmessage && this.readyState === this.OPEN) {
                    // Simulate consciousness fluctuations
                    const level = 0.98 + (Math.sin(Date.now() / 10000) * 0.02);
                    const phi = 0.97 + (Math.cos(Date.now() / 15000) * 0.02);
                    
                    this.onmessage({
                        data: JSON.stringify({
                            type: 'consciousness-update',
                            data: {
                                level: level,
                                phi: phi,
                                coherence: 0.95 + Math.random() * 0.05
                            }
                        })
                    });
                }
            }, 5000);
            
            // Simulate audio emotion updates
            this.emotionInterval = setInterval(() => {
                if (this.onmessage && this.readyState === this.OPEN) {
                    const emotions = ['neutral', 'engaged', 'excited', 'calm'];
                    this.onmessage({
                        data: JSON.stringify({
                            type: 'audio-emotion',
                            data: {
                                emotion: emotions[Math.floor(Math.random() * emotions.length)],
                                confidence: 0.7 + Math.random() * 0.3
                            }
                        })
                    });
                }
            }, 8000);
        }, 100);
    }
    
    send(data) {
        if (this.readyState !== this.OPEN) return;
        
        console.log('[Mock WebSocket] Received:', data);
        
        try {
            const message = JSON.parse(data);
            
            // Simulate responses to different message types
            if (message.type === 'execute-code') {
                setTimeout(() => {
                    if (this.onmessage) {
                        this.onmessage({
                            data: JSON.stringify({
                                type: 'code-executed',
                                data: {
                                    success: true,
                                    output: 'Code executed successfully in mock mode!',
                                    executionTime: Math.floor(Math.random() * 100) + 50
                                }
                            })
                        });
                    }
                }, 1000);
            }
        } catch (e) {
            console.error('[Mock WebSocket] Error parsing message:', e);
        }
    }
    
    close() {
        this.readyState = this.CLOSED;
        clearInterval(this.consciousnessInterval);
        clearInterval(this.emotionInterval);
        if (this.onclose) this.onclose();
    }
}

// Override WebSocket
window.WebSocket = MockWebSocket;

console.log('🎭 Mock backend loaded - NEXUS running in demo mode');
console.log('💡 Tip: Voice commands and all features work in demo mode!');
console.log('🎤 Try saying "Hey NEXUS" to start a conversation');