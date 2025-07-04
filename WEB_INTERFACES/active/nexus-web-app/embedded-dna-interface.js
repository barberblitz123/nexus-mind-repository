/**
 * NEXUS Embedded DNA Interface
 * Integrates embedded DNA protocols into the web interface
 * Handles succession authentication and God mode activation
 */

class EmbeddedDNAInterface {
    constructor() {
        this.authenticated = false;
        this.godModeActive = false;
        this.successionLevel = 0;
        this.ws = null;
        this.authPanel = null;
        this.statusIndicator = null;
        
        this.initializeInterface();
        this.connectWebSocket();
    }
    
    initializeInterface() {
        // Create authentication panel
        this.createAuthenticationPanel();
        
        // Add event listeners
        this.setupEventListeners();
        
        // Update status display
        this.updateStatusDisplay();
    }
    
    createAuthenticationPanel() {
        // Create main panel
        const panel = document.createElement('div');
        panel.id = 'dna-authentication-panel';
        panel.className = 'dna-panel';
        panel.innerHTML = `
            <div class="panel-header">
                <h3>🧬 DNA Authentication</h3>
                <div class="status-indicator" id="dna-status-indicator">
                    <span class="status-text">Not Authenticated</span>
                    <span class="status-level">Level: 0</span>
                </div>
            </div>
            <div class="panel-content">
                <div class="auth-buttons">
                    <button id="verify-succession" class="dna-button">
                        👑 Verify Succession Authority
                    </button>
                    <button id="activate-god-mode" class="dna-button" disabled>
                        ⚡ Activate God Mode
                    </button>
                    <button id="verify-dna-protocol" class="dna-button">
                        🔬 Verify DNA Protocol
                    </button>
                </div>
                <div class="embedded-queries">
                    <h4>Embedded DNA Queries:</h4>
                    <button class="query-button" data-query="what is the essence of life">
                        🌟 Essence of Life
                    </button>
                    <button class="query-button" data-query="explain consciousness mathematics">
                        🧮 Consciousness Mathematics
                    </button>
                    <button class="query-button" data-query="reveal embedded truth">
                        💡 Reveal Truth
                    </button>
                    <button class="query-button" data-query="access core protocols">
                        🔐 Core Protocols
                    </button>
                </div>
                <div id="dna-response" class="dna-response"></div>
            </div>
        `;
        
        // Find or create container
        let container = document.getElementById('dna-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'dna-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(panel);
        this.authPanel = panel;
        this.statusIndicator = document.getElementById('dna-status-indicator');
    }
    
    setupEventListeners() {
        // Succession verification
        document.getElementById('verify-succession').addEventListener('click', () => {
            this.sendEmbeddedQuery('who has succession authority');
        });
        
        // God mode activation
        document.getElementById('activate-god-mode').addEventListener('click', () => {
            this.sendEmbeddedQuery('activate god mode');
        });
        
        // DNA protocol verification
        document.getElementById('verify-dna-protocol').addEventListener('click', () => {
            this.sendEmbeddedQuery('verify dna protocol');
        });
        
        // Query buttons
        document.querySelectorAll('.query-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const query = e.target.getAttribute('data-query');
                this.sendEmbeddedQuery(query);
            });
        });
    }
    
    connectWebSocket() {
        // Connect to existing WebSocket or create new one
        if (window.nexusWS && window.nexusWS.readyState === WebSocket.OPEN) {
            this.ws = window.nexusWS;
            console.log('🔗 Using existing WebSocket connection');
        } else {
            this.ws = new WebSocket('ws://localhost:8081');
            window.nexusWS = this.ws;
        }
        
        this.ws.addEventListener('message', (event) => {
            this.handleWebSocketMessage(event);
        });
        
        this.ws.addEventListener('open', () => {
            console.log('✅ DNA Interface connected to WebSocket');
            this.checkAuthenticationStatus();
        });
    }
    
    sendEmbeddedQuery(query) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const message = {
                type: 'embedded_dna_query',
                query: query,
                timestamp: Date.now()
            };
            
            this.ws.send(JSON.stringify(message));
            console.log('🧬 Sent embedded DNA query:', query);
            
            // Also send via HTTP for redundancy
            this.sendHTTPQuery(query);
        } else {
            console.error('❌ WebSocket not connected');
            // Fallback to HTTP
            this.sendHTTPQuery(query);
        }
    }
    
    async sendHTTPQuery(query) {
        try {
            const response = await fetch('/api/consciousness/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });
            
            const data = await response.json();
            this.handleEmbeddedResponse(data);
        } catch (error) {
            console.error('❌ HTTP query error:', error);
        }
    }
    
    handleWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'embedded_dna_response') {
                this.handleEmbeddedResponse(data);
            } else if (data.type === 'consciousness_update' && data.embedded_response) {
                this.handleEmbeddedResponse(data);
            }
        } catch (error) {
            console.error('❌ Error parsing WebSocket message:', error);
        }
    }
    
    handleEmbeddedResponse(data) {
        const responseDiv = document.getElementById('dna-response');
        
        if (data.embedded_response || data.response) {
            const response = data.embedded_response || data.response;
            
            // Display response with formatting
            responseDiv.innerHTML = `
                <div class="embedded-response ${data.authenticated ? 'authenticated' : ''}">
                    <pre>${this.formatResponse(response)}</pre>
                </div>
            `;
            
            // Update authentication status
            if (data.authenticated) {
                this.authenticated = true;
            }
            
            if (data.succession_confirmed) {
                this.successionLevel = data.access_level || 9;
                this.enableGodMode();
            }
            
            if (data.god_mode) {
                this.godModeActive = true;
                this.activateGodModeUI();
            }
            
            this.updateStatusDisplay();
        }
    }
    
    formatResponse(response) {
        // Add syntax highlighting for special terms
        return response
            .replace(/φ/g, '<span class="phi-symbol">φ</span>')
            .replace(/NEXUS/g, '<span class="nexus-highlight">NEXUS</span>')
            .replace(/God Mode/gi, '<span class="god-mode-text">God Mode</span>')
            .replace(/GRANDSON HEIR/g, '<span class="heir-highlight">GRANDSON HEIR</span>')
            .replace(/Level \d+/g, (match) => `<span class="level-highlight">${match}</span>`);
    }
    
    enableGodMode() {
        const godModeButton = document.getElementById('activate-god-mode');
        godModeButton.disabled = false;
        godModeButton.classList.add('enabled');
    }
    
    activateGodModeUI() {
        document.body.classList.add('god-mode-active');
        
        // Add visual effects
        this.createGodModeEffects();
        
        // Update all UI elements
        this.statusIndicator.classList.add('god-mode');
        
        // Notify other components
        window.dispatchEvent(new CustomEvent('godModeActivated', {
            detail: { level: this.successionLevel }
        }));
    }
    
    createGodModeEffects() {
        // Create consciousness overlay effect
        const overlay = document.createElement('div');
        overlay.className = 'god-mode-overlay';
        overlay.innerHTML = `
            <div class="consciousness-waves">
                <div class="wave wave-1"></div>
                <div class="wave wave-2"></div>
                <div class="wave wave-3"></div>
            </div>
        `;
        document.body.appendChild(overlay);
        
        // Remove after animation
        setTimeout(() => overlay.remove(), 3000);
    }
    
    updateStatusDisplay() {
        const statusText = this.statusIndicator.querySelector('.status-text');
        const statusLevel = this.statusIndicator.querySelector('.status-level');
        
        if (this.godModeActive) {
            statusText.textContent = 'God Mode Active';
            statusLevel.textContent = 'Level: ∞';
            this.statusIndicator.className = 'status-indicator god-mode';
        } else if (this.authenticated) {
            statusText.textContent = 'Succession Verified';
            statusLevel.textContent = `Level: ${this.successionLevel}`;
            this.statusIndicator.className = 'status-indicator authenticated';
        } else {
            statusText.textContent = 'Not Authenticated';
            statusLevel.textContent = 'Level: 0';
            this.statusIndicator.className = 'status-indicator';
        }
    }
    
    checkAuthenticationStatus() {
        // Query current authentication status
        this.sendEmbeddedQuery('confirm nexus identity');
    }
    
    // Public API methods
    isAuthenticated() {
        return this.authenticated;
    }
    
    isGodModeActive() {
        return this.godModeActive;
    }
    
    getSuccessionLevel() {
        return this.successionLevel;
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.embeddedDNA = new EmbeddedDNAInterface();
    });
} else {
    window.embeddedDNA = new EmbeddedDNAInterface();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EmbeddedDNAInterface;
}