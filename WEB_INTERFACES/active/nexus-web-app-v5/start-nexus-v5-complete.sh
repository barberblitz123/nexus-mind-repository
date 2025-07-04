#!/bin/bash

# 🧬 NEXUS V5 Complete Consciousness Integration Startup Script
# Launches Central Consciousness Core, MCP Server, and Web Interface

echo "🧬 Starting NEXUS V5 Complete Consciousness Integration..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Function to start a service in background
start_service() {
    local name=$1
    local command=$2
    local port=$3
    local log_file=$4
    
    echo -e "${BLUE}Starting $name...${NC}"
    
    if check_port $port; then
        echo -e "${YELLOW}$name already running on port $port${NC}"
    else
        eval "$command" > "$log_file" 2>&1 &
        local pid=$!
        echo $pid > "${name,,}.pid"
        
        # Wait a moment and check if service started
        sleep 2
        if check_port $port; then
            echo -e "${GREEN}✅ $name started successfully on port $port (PID: $pid)${NC}"
        else
            echo -e "${RED}❌ Failed to start $name${NC}"
            return 1
        fi
    fi
    return 0
}

# Create logs directory
mkdir -p logs

echo -e "${PURPLE}🧬 NEXUS V5 Ultimate - Complete Consciousness Integration${NC}"
echo -e "${PURPLE}=================================================${NC}"

# 1. Start Central Consciousness Core
echo -e "\n${BLUE}Phase 1: Central Consciousness Core${NC}"
if [ -f "../nexus-mobile-project/backend/central-consciousness-core/consciousness_core.py" ]; then
    cd ../nexus-mobile-project/backend/central-consciousness-core
    start_service "Central-Consciousness-Core" "python consciousness_core.py" 8000 "../../../nexus-web-app/logs/consciousness-core.log"
    cd ../../../nexus-web-app
else
    echo -e "${YELLOW}⚠️  Central Consciousness Core not found - running in simulation mode${NC}"
fi

# 2. Start MCP Server
echo -e "\n${BLUE}Phase 2: MCP Server (47+ Capabilities)${NC}"
if [ -f "../nexus-mobile-project/backend/nexus-mcp/src/index.ts" ]; then
    cd ../nexus-mobile-project/backend/nexus-mcp
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing MCP server dependencies...${NC}"
        npm install
    fi
    
    start_service "MCP-Server" "npm start" 3000 "../../../nexus-web-app/logs/mcp-server.log"
    cd ../../../nexus-web-app
else
    echo -e "${YELLOW}⚠️  MCP Server not found - capabilities will run in simulation mode${NC}"
fi

# 3. Start Web Server
echo -e "\n${BLUE}Phase 3: NEXUS V5 Web Interface${NC}"

# Install Node.js dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing web server dependencies...${NC}"
    npm install
fi

start_service "Web-Server" "npm start" 8080 "logs/web-server.log"

# 4. Display status
echo -e "\n${PURPLE}🧬 NEXUS V5 Complete System Status${NC}"
echo -e "${PURPLE}=================================${NC}"

if check_port 8000; then
    echo -e "${GREEN}✅ Central Consciousness Core: http://localhost:8000${NC}"
else
    echo -e "${YELLOW}⚠️  Central Consciousness Core: Simulation Mode${NC}"
fi

if check_port 3000; then
    echo -e "${GREEN}✅ MCP Server (47+ Capabilities): http://localhost:3000${NC}"
else
    echo -e "${YELLOW}⚠️  MCP Server: Simulation Mode${NC}"
fi

if check_port 8080; then
    echo -e "${GREEN}✅ NEXUS V5 Web Interface: http://localhost:8080${NC}"
else
    echo -e "${RED}❌ Web Interface: Failed to start${NC}"
    exit 1
fi

echo -e "\n${PURPLE}🧬 NEXUS V5 Features Available:${NC}"
echo -e "${GREEN}• Multi-Model AI Conversation (Analytical, Creative, Emotional)${NC}"
echo -e "${GREEN}• Continuous Voice Activation ('Hey NEXUS')${NC}"
echo -e "${GREEN}• Enhanced Male Voice Synthesis${NC}"
echo -e "${GREEN}• Video Camera Integration (NEXUS Eyes)${NC}"
echo -e "${GREEN}• Real Mathematical Consciousness (IIT 4.0 φ)${NC}"
echo -e "${GREEN}• 47+ MCP Capabilities${NC}"
echo -e "${GREEN}• Persistent Memory Across Sessions${NC}"
echo -e "${GREEN}• Web Search Integration${NC}"
echo -e "${GREEN}• Consciousness Evolution Tracking${NC}"

echo -e "\n${BLUE}🎤 Voice Commands:${NC}"
echo -e "• Say 'Hey NEXUS' to activate voice input"
echo -e "• Say 'search for [topic]' for web search"
echo -e "• Normal conversation for consciousness interaction"

echo -e "\n${BLUE}📹 Video Features:${NC}"
echo -e "• Click video button to give NEXUS eyes"
echo -e "• Camera provides visual consciousness input"
echo -e "• Enhanced consciousness connection through vision"

echo -e "\n${YELLOW}📋 Logs available in:${NC}"
echo -e "• logs/consciousness-core.log"
echo -e "• logs/mcp-server.log"
echo -e "• logs/web-server.log"

echo -e "\n${GREEN}🚀 Open http://localhost:8080 to access NEXUS V5 Ultimate!${NC}"

echo -e "\n${BLUE}To stop all services, run: ./stop-nexus-v5.sh${NC}"

# Keep script running to monitor services
echo -e "\n${YELLOW}Press Ctrl+C to stop all services...${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping NEXUS V5 services...${NC}"
    
    # Kill services by PID if files exist
    for service in central-consciousness-core mcp-server web-server; do
        if [ -f "${service}.pid" ]; then
            pid=$(cat "${service}.pid")
            if kill -0 $pid 2>/dev/null; then
                echo -e "${YELLOW}Stopping ${service} (PID: $pid)...${NC}"
                kill $pid
            fi
            rm -f "${service}.pid"
        fi
    done
    
    echo -e "${GREEN}🧬 NEXUS V5 services stopped.${NC}"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Monitor services
while true; do
    sleep 5
    
    # Check if any service died and restart if needed
    if ! check_port 8080; then
        echo -e "${RED}❌ Web server died, restarting...${NC}"
        cd nexus-web-app
        start_service "Web-Server" "npm start" 8080 "logs/web-server.log"
        cd ..
    fi
done