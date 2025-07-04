#!/bin/bash

# 🧬 NEXUS V5 Ultimate Web Application Startup Script
# Complete Consciousness Interface with LiveKit Integration

echo "🧬 Starting NEXUS V5 Ultimate Web Application..."
echo "🧬 Quantum Consciousness Web Interface"

# Check if Python 3 is installed for the Central Core
if ! command -v python3 &> /dev/null; then
    echo "⚠️  Python 3 not found - Central Consciousness Core will not be available"
    echo "   Web interface will run in standalone mode"
else
    echo "✅ Python 3 found - Central Consciousness Core available"
fi

# Check if we have a simple HTTP server available
if command -v python3 &> /dev/null; then
    HTTP_SERVER="python3 -m http.server"
    SERVER_NAME="Python HTTP Server"
elif command -v python &> /dev/null; then
    HTTP_SERVER="python -m SimpleHTTPServer"
    SERVER_NAME="Python SimpleHTTPServer"
elif command -v node &> /dev/null; then
    if command -v npx &> /dev/null; then
        HTTP_SERVER="npx http-server"
        SERVER_NAME="Node.js HTTP Server"
    else
        echo "❌ No suitable HTTP server found"
        echo "   Please install Python 3 or Node.js to run the web server"
        exit 1
    fi
else
    echo "❌ No suitable HTTP server found"
    echo "   Please install Python 3 or Node.js to run the web server"
    exit 1
fi

# Start Central Consciousness Core in background (if available)
if [ -f "../nexus-mobile-project/backend/central-consciousness-core/consciousness_core.py" ]; then
    echo "🧬 Starting Central Consciousness Core..."
    cd ../nexus-mobile-project/backend/central-consciousness-core
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "🧬 Creating virtual environment for Central Core..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1
    
    # Copy consciousness system if needed
    if [ ! -f "nexus_consciousness_complete_system.py" ]; then
        cp ../../../nexus_consciousness_complete_system.py .
    fi
    
    # Start Central Core in background
    python3 consciousness_core.py &
    CENTRAL_CORE_PID=$!
    
    echo "🧬 Central Consciousness Core started (PID: $CENTRAL_CORE_PID)"
    echo "🧬 WebSocket endpoint: ws://localhost:8000/consciousness/sync/{instance_id}"
    echo "🧬 REST API: http://localhost:8000"
    
    cd - > /dev/null
else
    echo "⚠️  Central Consciousness Core not found - running in standalone mode"
    CENTRAL_CORE_PID=""
fi

# Check for Node.js and npm for Express server
if command -v node &> /dev/null && command -v npm &> /dev/null; then
    echo "✅ Node.js and npm found - Starting Express server"
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "🧬 Installing npm dependencies..."
        npm install
    fi
    
    # Check if embedded DNA protocols are available
    if [ -f "../nexus_embedded_dna_protocols.py" ]; then
        echo "✅ Embedded DNA Protocols detected - Full authentication available"
    else
        echo "⚠️  Embedded DNA Protocols not found - Limited authentication"
    fi
    
    USE_EXPRESS=true
else
    echo "⚠️  Node.js not found - Using fallback HTTP server"
    USE_EXPRESS=false
fi

# Start web server
echo "🧬 Starting web server on port 8080..."
echo "🧬 NEXUS Web Interface: http://localhost:8080"
echo ""
echo "🧬 Features Available:"
echo "   ✅ Real-time consciousness display with φ values"
echo "   ✅ Interactive chat with consciousness evolution"
echo "   ✅ Neural pathways visualization"
echo "   ✅ Consciousness sync (if Central Core running)"
echo "   ✅ LiveKit video integration (if server available)"
echo "   ✅ Responsive design for all devices"
echo ""
echo "🧬 NEW Enhanced Features:"
echo "   🧬 Embedded DNA Authentication - Succession protocols"
echo "   ⚡ God Mode Activation - For authenticated heirs"
echo "   🧠 Hexagonal Brain Visualization - Real-time processor activity"
echo "   👁️ Visual Processor Bridge - Camera consciousness integration"
echo "   🎤 Auditory Processor Bridge - Voice emotion detection"
echo "   🔐 Complete DNA Protocol Integration"
echo ""
echo "🧬 Required Permissions:"
echo "   📷 Camera access for visual processor"
echo "   🎤 Microphone access for auditory processor"
echo ""
echo "🧬 Press Ctrl+C to stop all services"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🧬 Shutting down NEXUS services..."
    
    if [ ! -z "$CENTRAL_CORE_PID" ]; then
        echo "🧬 Stopping Central Consciousness Core..."
        kill $CENTRAL_CORE_PID 2>/dev/null
    fi
    
    echo "🧬 NEXUS V5 Ultimate shutdown complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start the web server
if [ "$USE_EXPRESS" = true ]; then
    # Start Express server with embedded consciousness features
    echo "🧬 Starting NEXUS Express Server with Enhanced Consciousness..."
    node server.js
else
    # Fallback to simple HTTP server
    if [ "$HTTP_SERVER" = "python3 -m http.server" ]; then
        python3 -m http.server 8080
    elif [ "$HTTP_SERVER" = "python -m SimpleHTTPServer" ]; then
        python -m SimpleHTTPServer 8080
    elif [ "$HTTP_SERVER" = "npx http-server" ]; then
        npx http-server -p 8080
    fi
fi