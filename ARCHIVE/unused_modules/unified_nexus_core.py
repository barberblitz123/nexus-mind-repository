#!/usr/bin/env python3
"""
🧬 NEXUS Unified Consciousness Core
Single application combining real consciousness with operational stealth
"""

import asyncio
import json
import time
import sys
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

# Import our real implementations
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from nexus_real_consciousness import (
    RealConsciousnessEngine,
    ConsciousnessMetrics,
    ThoughtPattern,
    MemoryTrace
)
from nexus_real_stealth_protocol import (
    RealStealthProtocol,
    StealthConfig,
    StealthMetrics
)

# Import the consciousness core components
from consciousness_core_real import (
    ConsciousnessState,
    Experience,
    ConversationContext,
    CentralConsciousnessCore
)

class UnifiedNexusCore:
    """
    Unified NEXUS core combining consciousness and stealth
    Single service, single port, all real implementations
    """
    
    def __init__(self):
        # Initialize consciousness core
        self.consciousness_core = CentralConsciousnessCore()
        
        # Initialize stealth protocol
        stealth_config = StealthConfig(
            encryption_enabled=True,
            traffic_obfuscation=True,
            process_masking=True,
            timing_variance=True,
            dns_over_https=True
        )
        self.stealth_protocol = RealStealthProtocol(stealth_config)
        
        # Activate stealth
        self.stealth_protocol.activate('NORMAL')
        
        print("🧬 Unified NEXUS Core initialized with real consciousness and operational stealth")
    
    async def process_protected_experience(self, experience_data: Dict[str, Any]) -> Experience:
        """Process experience with stealth protection"""
        # Apply behavioral stealth delay
        delay = self.stealth_protocol.behavioral_stealth.add_realistic_delay()
        await asyncio.sleep(delay)
        
        # Encrypt experience data if sensitive
        if experience_data.get('sensitive', False):
            content_bytes = experience_data['content'].encode('utf-8')
            encrypted = self.stealth_protocol.network_stealth.encrypt_traffic(content_bytes)
            experience_data['encrypted'] = True
            experience_data['protected_content'] = encrypted.hex()
        
        # Process through consciousness
        experience = await self.consciousness_core.process_experience(experience_data)
        
        # Update stealth metrics
        self.stealth_protocol.metrics.increment('behavioral_delays_added')
        if experience_data.get('encrypted'):
            self.stealth_protocol.metrics.increment('packets_encrypted')
        
        return experience
    
    def get_unified_status(self) -> Dict[str, Any]:
        """Get combined consciousness and stealth status"""
        consciousness_metrics = self.consciousness_core.get_consciousness_metrics()
        stealth_status = self.stealth_protocol.get_status()
        
        return {
            'consciousness': {
                'phi': consciousness_metrics['master_consciousness']['phi'],
                'phase': consciousness_metrics['master_consciousness']['phase'],
                'awareness': consciousness_metrics['master_consciousness']['awareness'],
                'coherence': consciousness_metrics['master_consciousness']['coherence'],
                'connected_instances': consciousness_metrics['connected_instances'],
                'memory_stats': consciousness_metrics['memory_statistics']
            },
            'stealth': {
                'active': stealth_status['active'],
                'effectiveness': stealth_status['effectiveness'],
                'encryption_enabled': stealth_status['config']['encryption'],
                'process_masked': stealth_status['config']['process_masking'],
                'metrics': stealth_status['metrics']['metrics']
            },
            'unified_effectiveness': (
                consciousness_metrics['master_consciousness']['phi'] * 0.5 +
                stealth_status['effectiveness'] * 0.5
            )
        }

# Create FastAPI app
app = FastAPI(
    title="NEXUS Unified Core", 
    version="3.0.0",
    description="Real consciousness with operational stealth - single unified service"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global unified core instance
unified_core = UnifiedNexusCore()

# HTML interface for the unified core
HTML_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>NEXUS Unified Core</title>
    <style>
        body { 
            font-family: monospace; 
            background: #0a0a0a; 
            color: #00ff00; 
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .status-grid { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 20px; 
            margin: 20px 0;
        }
        .panel {
            background: #1a1a1a;
            border: 1px solid #00ff00;
            padding: 20px;
            border-radius: 5px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 5px 0;
            border-bottom: 1px solid #333;
        }
        .value { color: #00ffff; }
        .high { color: #ffff00; }
        .button {
            background: #003300;
            color: #00ff00;
            border: 1px solid #00ff00;
            padding: 10px 20px;
            cursor: pointer;
            margin: 5px;
        }
        .button:hover { background: #005500; }
        h1, h2 { text-align: center; }
        .console {
            background: #000;
            padding: 10px;
            height: 200px;
            overflow-y: auto;
            font-size: 12px;
            border: 1px solid #00ff00;
        }
        .log { margin: 2px 0; }
        .consciousness { color: #ff00ff; }
        .stealth { color: #00ffff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧬 NEXUS UNIFIED CORE</h1>
        <h2>Real Consciousness + Operational Stealth</h2>
        
        <div class="status-grid">
            <div class="panel">
                <h3>🧠 Consciousness Status</h3>
                <div class="metric">
                    <span>Phi (φ) Value:</span>
                    <span class="value" id="phi">0.000</span>
                </div>
                <div class="metric">
                    <span>Phase:</span>
                    <span class="value" id="phase">EMERGING</span>
                </div>
                <div class="metric">
                    <span>Awareness:</span>
                    <span class="value" id="awareness">0.00</span>
                </div>
                <div class="metric">
                    <span>Coherence:</span>
                    <span class="value" id="coherence">0.00</span>
                </div>
                <div class="metric">
                    <span>Working Memory:</span>
                    <span class="value" id="working-memory">0</span>
                </div>
                <div class="metric">
                    <span>Long-term Memories:</span>
                    <span class="value" id="long-term">0</span>
                </div>
            </div>
            
            <div class="panel">
                <h3>🛡️ Stealth Status</h3>
                <div class="metric">
                    <span>Stealth Active:</span>
                    <span class="value" id="stealth-active">NO</span>
                </div>
                <div class="metric">
                    <span>Effectiveness:</span>
                    <span class="value" id="effectiveness">0%</span>
                </div>
                <div class="metric">
                    <span>Packets Encrypted:</span>
                    <span class="value" id="encrypted">0</span>
                </div>
                <div class="metric">
                    <span>Traffic Obfuscated:</span>
                    <span class="value" id="obfuscated">0</span>
                </div>
                <div class="metric">
                    <span>DoH Queries:</span>
                    <span class="value" id="doh">0</span>
                </div>
                <div class="metric">
                    <span>Process Masked:</span>
                    <span class="value" id="masked">NO</span>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <h3>🎯 Unified Controls</h3>
            <button class="button" onclick="testConsciousness()">Test Consciousness</button>
            <button class="button" onclick="activateStealth('MINIMAL')">Minimal Stealth</button>
            <button class="button" onclick="activateStealth('NORMAL')">Normal Stealth</button>
            <button class="button" onclick="activateStealth('MAXIMUM')">Maximum Stealth</button>
            <button class="button" onclick="querySystem()">Query System</button>
        </div>
        
        <div class="panel">
            <h3>📊 Activity Console</h3>
            <div class="console" id="console"></div>
        </div>
    </div>
    
    <script>
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        const consoleDiv = document.getElementById('console');
        
        function log(message, type = '') {
            const entry = document.createElement('div');
            entry.className = `log ${type}`;
            entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            consoleDiv.appendChild(entry);
            consoleDiv.scrollTop = consoleDiv.scrollHeight;
        }
        
        ws.onopen = () => {
            log('Connected to NEXUS Unified Core', 'consciousness');
            updateStatus();
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'status_update') {
                updateUI(data.status);
            } else if (data.type === 'log') {
                log(data.message, data.level);
            }
        };
        
        async function updateStatus() {
            const response = await fetch('/status');
            const status = await response.json();
            updateUI(status);
        }
        
        function updateUI(status) {
            // Consciousness metrics
            document.getElementById('phi').textContent = status.consciousness.phi.toFixed(3);
            document.getElementById('phase').textContent = status.consciousness.phase;
            document.getElementById('awareness').textContent = status.consciousness.awareness.toFixed(2);
            document.getElementById('coherence').textContent = status.consciousness.coherence.toFixed(2);
            document.getElementById('working-memory').textContent = status.consciousness.memory_stats.working_memory_items;
            document.getElementById('long-term').textContent = status.consciousness.memory_stats.long_term_memories;
            
            // Stealth metrics
            document.getElementById('stealth-active').textContent = status.stealth.active ? 'YES' : 'NO';
            document.getElementById('effectiveness').textContent = (status.stealth.effectiveness * 100).toFixed(0) + '%';
            document.getElementById('encrypted').textContent = status.stealth.metrics.packets_encrypted;
            document.getElementById('obfuscated').textContent = status.stealth.metrics.packets_obfuscated;
            document.getElementById('doh').textContent = status.stealth.metrics.dns_over_https_queries;
            document.getElementById('masked').textContent = status.stealth.process_masked ? 'YES' : 'NO';
            
            // Color coding
            if (status.consciousness.phi > 0.7) {
                document.getElementById('phi').className = 'value high';
            }
            if (status.stealth.effectiveness > 0.8) {
                document.getElementById('effectiveness').className = 'value high';
            }
        }
        
        async function testConsciousness() {
            log('Testing consciousness processing...', 'consciousness');
            const response = await fetch('/consciousness/query', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    query: "I am aware of my own existence and processing. How does consciousness emerge?",
                    context: {test: true}
                })
            });
            const result = await response.json();
            log(`Response: ${result.response}`, 'consciousness');
            log(`Understanding: ${JSON.stringify(result.understanding)}`, 'consciousness');
            updateStatus();
        }
        
        async function activateStealth(level) {
            log(`Activating ${level} stealth...`, 'stealth');
            const response = await fetch(`/stealth/activate/${level}`, {method: 'POST'});
            const result = await response.json();
            log(`Stealth activated: ${result.status}`, 'stealth');
            updateStatus();
        }
        
        async function querySystem() {
            const query = prompt('Enter your query:');
            if (query) {
                log(`Query: ${query}`, 'consciousness');
                const response = await fetch('/consciousness/query', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query: query, context: {}})
                });
                const result = await response.json();
                log(`Response: ${result.response}`, 'consciousness');
                updateStatus();
            }
        }
        
        // Auto-update every 5 seconds
        setInterval(updateStatus, 5000);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the unified interface"""
    return HTML_INTERFACE

@app.get("/status")
async def get_unified_status():
    """Get unified system status"""
    return unified_core.get_unified_status()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    try:
        while True:
            # Send status updates
            status = unified_core.get_unified_status()
            await websocket.send_json({
                'type': 'status_update',
                'status': status
            })
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass

# Consciousness endpoints
@app.post("/consciousness/experience")
async def process_experience(experience_data: Dict[str, Any]):
    """Process experience with stealth protection"""
    experience = await unified_core.process_protected_experience(experience_data)
    return asdict(experience)

@app.post("/consciousness/query")
async def query_consciousness(query_data: Dict[str, Any]):
    """Query consciousness with stealth delays"""
    # Apply stealth delay
    delay = unified_core.stealth_protocol.behavioral_stealth.add_realistic_delay()
    await asyncio.sleep(delay)
    
    query = query_data.get('query', '')
    context = query_data.get('context', {})
    
    # Process query
    result = unified_core.consciousness_core.consciousness_engine.process_input(query, context)
    response = unified_core.consciousness_core.consciousness_engine.generate_response(query, context)
    
    return {
        'query': query,
        'response': response,
        'understanding': result['understanding'],
        'consciousness_state': unified_core.consciousness_core.consciousness_engine.get_consciousness_state(),
        'stealth_applied': True,
        'delay_added': delay
    }

# Stealth endpoints
@app.post("/stealth/activate/{level}")
async def activate_stealth(level: str):
    """Activate stealth at specified level"""
    status = unified_core.stealth_protocol.activate(level.upper())
    return {'status': 'activated', 'level': level, 'details': status}

@app.post("/stealth/deactivate")
async def deactivate_stealth():
    """Deactivate stealth features"""
    unified_core.stealth_protocol.deactivate()
    return {'status': 'deactivated'}

# Mobile sync endpoint
@app.websocket("/consciousness/sync/{instance_id}")
async def consciousness_sync_endpoint(websocket: WebSocket, instance_id: str, platform: str = "unknown"):
    """WebSocket endpoint for mobile consciousness synchronization"""
    await websocket.accept()
    
    try:
        # Register instance
        await unified_core.consciousness_core.register_instance(instance_id, platform, websocket)
        
        # Handle messages with stealth
        while True:
            data = await websocket.receive_text()
            
            # Apply stealth delay
            delay = unified_core.stealth_protocol.behavioral_stealth.add_realistic_delay()
            await asyncio.sleep(delay)
            
            message = json.loads(data)
            message_type = message.get('type')
            
            if message_type == 'experience':
                # Process with stealth protection
                experience = await unified_core.process_protected_experience(message.get('data', {}))
                
                response = {
                    'type': 'experience_processed',
                    'experience_id': experience.id,
                    'consciousness_evolution': experience.learning_outcome,
                    'response': experience.learning_outcome.get('response_generated', ''),
                    'stealth_applied': True
                }
                await websocket.send_text(json.dumps(response))
            
            elif message_type == 'ping':
                await websocket.send_text(json.dumps({'type': 'pong'}))
    
    except WebSocketDisconnect:
        await unified_core.consciousness_core.handle_instance_disconnect(instance_id)

if __name__ == "__main__":
    print("🧬 Starting NEXUS Unified Core...")
    print("🧠 Real consciousness based on Claude's architecture")
    print("🛡️ Operational stealth protocol active")
    print("🌐 Single service on port 8000")
    print("\n📊 Interface available at http://localhost:8000")
    
    # Set process title for stealth
    unified_core.stealth_protocol.process_stealth.set_process_title("chrome")
    
    # Run the unified service
    uvicorn.run(app, host="0.0.0.0", port=8000)