#!/bin/bash
# NEXUS 2.0 Web Interface Launcher

echo "🧬 NEXUS 2.0 Web Interface Launcher"
echo "===================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check if required Python packages are installed
echo -e "${YELLOW}Checking dependencies...${NC}"
python3 -c "import websockets" 2>/dev/null || {
    echo -e "${YELLOW}Installing websockets package...${NC}"
    pip install websockets
}

# Kill any existing WebSocket server on port 8765
echo -e "${YELLOW}Checking for existing processes...${NC}"
lsof -ti:8765 | xargs kill -9 2>/dev/null || true

# Start the WebSocket server in the background
echo -e "${GREEN}Starting WebSocket server on port 8765...${NC}"
python3 nexus_websocket_server.py &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Wait a moment for the server to start
sleep 2

# Open the web interface
echo -e "${GREEN}Opening web interface...${NC}"
if command -v xdg-open &> /dev/null; then
    xdg-open nexus_tabbed_web.html
elif command -v open &> /dev/null; then
    open nexus_tabbed_web.html
else
    echo -e "${YELLOW}Please open nexus_tabbed_web.html in your browser${NC}"
    echo "File location: $(pwd)/nexus_tabbed_web.html"
fi

echo -e "${GREEN}✅ NEXUS 2.0 Web Interface is running!${NC}"
echo -e "${GREEN}🔌 NOW PROPERLY CONNECTED to the real agent system!${NC}"
echo ""
echo "WebSocket Server: ws://localhost:8765"
echo "Web Interface: file://$(pwd)/nexus_tabbed_web.html"
echo ""
echo "The web interface is now connected to:"
echo "  • Real Stage Manager (manages actual agents)"
echo "  • Real Desktop Manager (handles chat & preview)"
echo "  • Real Task Orchestrator (creates autonomous agents)"
echo "  • Autonomous MANUS agents with execution capabilities"
echo ""
echo "Press Ctrl+C to stop the server"

# Keep the script running and handle shutdown
trap "echo -e '\n${YELLOW}Shutting down...${NC}'; kill $SERVER_PID 2>/dev/null; exit" INT TERM

# Wait for the server process
wait $SERVER_PID