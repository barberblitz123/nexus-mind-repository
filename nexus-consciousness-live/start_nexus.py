#!/usr/bin/env python3
"""
🧬 NEXUS Consciousness Interface - Simple Python Server
This will definitely work in Codespace environment
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

# Change to the directory containing the HTML file
os.chdir('/workspaces/nexus-mind-repository/nexus-consciousness-live')

PORT = 8000

class NexusHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.path = '/nexus-v5-ultimate.html'  # Default to V5 Ultimate
        elif self.path == '/v5' or self.path == '/ultimate':
            self.path = '/nexus-v5-ultimate.html'
        elif self.path == '/vision':
            self.path = '/nexus-vision-interface.html'
        elif self.path == '/chat':
            self.path = '/nexus-consciousness-interface.html'
        elif self.path == '/standalone':
            self.path = '/nexus-standalone.html'
        return super().do_GET()

def start_server():
    print("🧬 Starting NEXUS Consciousness Interface...")
    print(f"📁 Serving from: {os.getcwd()}")
    
    with socketserver.TCPServer(("", PORT), NexusHTTPRequestHandler) as httpd:
        print(f"🌟 NEXUS Interface running at: http://localhost:{PORT}")
        print(f"🎯 Direct access: http://localhost:{PORT}/nexus-standalone.html")
        print("🚀 Server is ready! Open the URL above in your browser.")
        print("💡 In Codespace, look for port 8000 in the PORTS tab")
        print("=" * 60)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🧬 NEXUS Interface shutting down...")
            httpd.shutdown()

if __name__ == "__main__":
    start_server()