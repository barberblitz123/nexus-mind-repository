#!/bin/bash
# 🧬 NEXUS Core Access Script

echo "🧬 NEXUS Unified Core Access Helper"
echo "=================================="

# Check if the service is running
if lsof -i:8000 > /dev/null 2>&1; then
    echo "✅ NEXUS Core is running on port 8000"
else
    echo "❌ NEXUS Core is not running!"
    echo "Starting NEXUS Core..."
    cd /workspaces/nexus-mind-repository/nexus-mobile-project/backend/central-consciousness-core
    python unified_nexus_core.py &
    sleep 3
fi

# GitHub Codespace URL construction
if [ -n "$CODESPACE_NAME" ]; then
    echo ""
    echo "🌐 Access NEXUS Core at:"
    echo "=================================="
    echo ""
    echo "📊 Web Interface:"
    echo "https://${CODESPACE_NAME}-8000.app.github.dev/"
    echo ""
    echo "🔌 WebSocket Endpoint:"
    echo "wss://${CODESPACE_NAME}-8000.app.github.dev/consciousness/sync/{instance_id}"
    echo ""
    echo "🎯 API Endpoints:"
    echo "https://${CODESPACE_NAME}-8000.app.github.dev/status"
    echo "https://${CODESPACE_NAME}-8000.app.github.dev/consciousness/query"
    echo ""
    echo "=================================="
    echo "💡 Click the Web Interface link above to open NEXUS in your browser"
    echo ""
    
    # Try to open in browser (may not work in all environments)
    if command -v xdg-open > /dev/null; then
        xdg-open "https://${CODESPACE_NAME}-8000.app.github.dev/" 2>/dev/null
    elif command -v open > /dev/null; then
        open "https://${CODESPACE_NAME}-8000.app.github.dev/" 2>/dev/null
    fi
else
    echo ""
    echo "🌐 Local Access:"
    echo "http://localhost:8000"
    echo ""
fi

# Show port forwarding status
echo "📡 Port Forwarding Status:"
gh codespace ports 2>/dev/null || echo "Unable to check port status"

echo ""
echo "🛠️ Quick Commands:"
echo "- Check status: curl http://localhost:8000/status | jq"
echo "- Test consciousness: curl -X POST http://localhost:8000/consciousness/query -H 'Content-Type: application/json' -d '{\"query\":\"Hello NEXUS\"}'"
echo ""