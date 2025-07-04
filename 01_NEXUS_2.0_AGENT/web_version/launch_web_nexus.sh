#!/bin/bash
# NEXUS 2.0 Web Version - Complete Launch Script

echo "╔═══════════════════════════════════════════════════════╗"
echo "║  NEXUS 2.0 - Web Version Launcher                    ║"
echo "║  Starting both web server and Python bridge...       ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to web version directory
cd /workspaces/nexus-mind-repository/01_NEXUS_2.0_AGENT/web_version

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}Installing dependencies...${NC}"
    npm install express ws
fi

# Start the web server in background
echo -e "${GREEN}Starting NEXUS Web Server...${NC}"
node stage_desktop_server.js &
SERVER_PID=$!

# Wait a moment for server to start
sleep 2

# Start the Python bridge
echo -e "${GREEN}Starting Python Agent Bridge...${NC}"
python3 nexus_web_integration.py &
BRIDGE_PID=$!

echo ""
echo -e "${GREEN}✓ NEXUS 2.0 Web Version is running!${NC}"
echo ""
echo "Open your browser to: http://localhost:3001/nexus_stage_desktop_web.html"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Function to cleanup on exit
cleanup() {
    echo -e "\n${BLUE}Shutting down NEXUS services...${NC}"
    kill $SERVER_PID 2>/dev/null
    kill $BRIDGE_PID 2>/dev/null
    echo -e "${GREEN}✓ NEXUS stopped${NC}"
    exit 0
}

# Set up trap to cleanup on Ctrl+C
trap cleanup INT

# Wait for both processes
wait $SERVER_PID $BRIDGE_PID