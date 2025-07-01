#!/usr/bin/env python3
"""
NEXUS Unified Interface Launcher
Starts a simple HTTP server and opens the interface
"""

import http.server
import socketserver
import threading
import webbrowser
import os
import sys
import time
from pathlib import Path

PORT = 8888
DIRECTORY = Path(__file__).parent

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with CORS support"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress logs for cleaner output
        pass

def start_server():
    """Start the HTTP server"""
    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print(f"🧬 NEXUS Unified Interface Server")
        print(f"="*50)
        print(f"✅ Server running at: http://localhost:{PORT}")
        print(f"📁 Serving directory: {DIRECTORY}")
        print(f"🌐 Opening browser...")
        print(f"="*50)
        print(f"Press Ctrl+C to stop the server\n")
        
        # Open browser after a short delay
        threading.Timer(1.5, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")
            httpd.shutdown()

def create_mock_backend():
    """Create a simple mock backend for testing"""
    mock_file = DIRECTORY / "mock-backend.js"
    
    if not mock_file.exists():
        mock_content = '''// Mock Backend for NEXUS Unified Interface Testing
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
                    level: 0.987,
                    phi: 0.98
                }
            })
        };
    }
    
    // Fall back to original fetch for other requests
    return originalFetch(url, options);
};

function generateMockResponse(message) {
    const responses = [
        "I'm running in mock mode, but I'm still here to help! Your message was: " + message,
        "That's an interesting point about '" + message + "'. In a real deployment, I'd provide more detailed assistance.",
        "I understand you're asking about '" + message + "'. The full NEXUS system would give you a comprehensive response.",
        "Great question! While in mock mode, I can tell you received: " + message
    ];
    
    return responses[Math.floor(Math.random() * responses.length)];
}

// Mock WebSocket
class MockWebSocket {
    constructor(url) {
        this.url = url;
        this.readyState = 0;
        
        setTimeout(() => {
            this.readyState = 1;
            if (this.onopen) this.onopen();
            
            // Send periodic consciousness updates
            setInterval(() => {
                if (this.onmessage) {
                    this.onmessage({
                        data: JSON.stringify({
                            type: 'consciousness-update',
                            data: {
                                level: 0.98 + Math.random() * 0.02,
                                phi: 0.97 + Math.random() * 0.02
                            }
                        })
                    });
                }
            }, 5000);
        }, 100);
    }
    
    send(data) {
        console.log('[Mock WebSocket] Sent:', data);
    }
    
    close() {
        this.readyState = 3;
        if (this.onclose) this.onclose();
    }
}

// Override WebSocket
window.WebSocket = MockWebSocket;

console.log('🎭 Mock backend loaded - NEXUS running in demo mode');
'''
        
        with open(mock_file, 'w') as f:
            f.write(mock_content)
        
        # Also inject into index.html if needed
        index_file = DIRECTORY / "index.html"
        if index_file.exists():
            with open(index_file, 'r') as f:
                content = f.read()
            
            if 'mock-backend.js' not in content:
                # Add mock backend script before other scripts
                content = content.replace(
                    '<script src="js/unified-core.js"></script>',
                    '<script src="mock-backend.js"></script>\n    <script src="js/unified-core.js"></script>'
                )
                
                with open(index_file, 'w') as f:
                    f.write(content)

def main():
    """Main entry point"""
    print("🚀 Starting NEXUS Unified Interface...")
    
    # Create mock backend for testing
    create_mock_backend()
    
    # Change to the app directory
    os.chdir(DIRECTORY)
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main()