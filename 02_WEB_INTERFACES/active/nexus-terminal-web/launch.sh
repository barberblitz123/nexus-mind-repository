#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║           NEXUS 2.0 Web Terminal Launcher                 ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Get local IP for mobile access
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo "Starting NEXUS 2.0 Web Terminal..."
echo ""
echo "Access from:"
echo "- This computer: http://localhost:8080"
echo "- Mobile/iPad:   http://$LOCAL_IP:8080"
echo ""
echo "To install on mobile:"
echo "1. Open the URL above on your device"
echo "2. iOS: Tap Share → Add to Home Screen"
echo "3. Android: Tap ⋮ → Add to Home screen"
echo ""

# Start the server
npm start