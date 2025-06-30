/**
 * 🧬 NEXUS Debug Interface
 * Real-time debugging and diagnostics for NEXUS V5 system
 */

class NexusDebugInterface {
    constructor() {
        this.isVisible = false;
        this.logEntries = [];
        this.maxLogEntries = 200;
        this.autoScroll = true;
        this.filterLevel = 'ALL';
        this.consciousnessManager = null;
        
        this.createDebugPanel();
        this.setupEventListeners();
        
        console.log('🧬 Debug Interface initialized');
    }
    
    setConsciousnessManager(manager) {
        this.consciousnessManager = manager;
        
        // Listen for log entries
        manager.on('logEntry', (entry) => {
            this.addLogEntry(entry);
        });
        
        // Listen for connection changes
        manager.on('connectionChange', (status) => {
            this.updateConnectionStatus(status);
        });
    }
    
    createDebugPanel() {
        // Create debug panel HTML
        const debugPanel = document.createElement('div');
        debugPanel.id = 'nexusDebugPanel';
        debugPanel.className = 'nexus-debug-panel';
        debugPanel.style.display = 'none';
        
        debugPanel.innerHTML = `
            <div class="debug-header">
                <h3>🧬 NEXUS V5 Debug Console</h3>
                <div class="debug-controls">
                    <select id="debugFilterLevel">
                        <option value="ALL">All Logs</option>
                        <option value="ERROR">Errors Only</option>
                        <option value="WARN">Warnings+</option>
                        <option value="INFO">Info+</option>
                        <option value="DEBUG">Debug+</option>
                    </select>
                    <button id="clearDebugBtn">Clear</button>
                    <button id="exportDebugBtn">Export</button>
                    <button id="diagnosticsBtn">Diagnostics</button>
                    <button id="closeDebugBtn">✕</button>
                </div>
            </div>
            
            <div class="debug-status">
                <div class="status-item">
                    <span class="status-label">Connection:</span>
                    <span id="debugConnectionStatus" class="status-value">Initializing...</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Attempts:</span>
                    <span id="debugConnectionAttempts" class="status-value">0</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Last Error:</span>
                    <span id="debugLastError" class="status-value">None</span>
                </div>
            </div>
            
            <div class="debug-tabs">
                <button class="debug-tab active" data-tab="logs">Logs</button>
                <button class="debug-tab" data-tab="connection">Connection</button>
                <button class="debug-tab" data-tab="consciousness">Consciousness</button>
                <button class="debug-tab" data-tab="capabilities">Capabilities</button>
            </div>
            
            <div class="debug-content">
                <div id="debugTabLogs" class="debug-tab-content active">
                    <div id="debugLogContainer" class="debug-log-container"></div>
                </div>
                
                <div id="debugTabConnection" class="debug-tab-content">
                    <div id="debugConnectionInfo" class="debug-info-container"></div>
                </div>
                
                <div id="debugTabConsciousness" class="debug-tab-content">
                    <div id="debugConsciousnessInfo" class="debug-info-container"></div>
                </div>
                
                <div id="debugTabCapabilities" class="debug-tab-content">
                    <div id="debugCapabilitiesInfo" class="debug-info-container"></div>
                </div>
            </div>
        `;
        
        document.body.appendChild(debugPanel);
        
        // Add CSS styles
        this.addDebugStyles();
    }
    
    addDebugStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .nexus-debug-panel {
                position: fixed;
                top: 10px;
                right: 10px;
                width: 600px;
                height: 500px;
                background: rgba(26, 26, 46, 0.95);
                border: 2px solid #6366f1;
                border-radius: 8px;
                z-index: 10000;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                color: #e5e7eb;
                display: flex;
                flex-direction: column;
                backdrop-filter: blur(10px);
            }
            
            .debug-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px;
                border-bottom: 1px solid #374151;
                background: rgba(99, 102, 241, 0.1);
            }
            
            .debug-header h3 {
                margin: 0;
                color: #6366f1;
                font-size: 14px;
            }
            
            .debug-controls {
                display: flex;
                gap: 5px;
                align-items: center;
            }
            
            .debug-controls select,
            .debug-controls button {
                padding: 4px 8px;
                background: rgba(55, 65, 81, 0.8);
                border: 1px solid #6366f1;
                border-radius: 4px;
                color: #e5e7eb;
                font-size: 11px;
                cursor: pointer;
            }
            
            .debug-controls button:hover {
                background: rgba(99, 102, 241, 0.3);
            }
            
            .debug-status {
                display: flex;
                gap: 15px;
                padding: 8px 10px;
                background: rgba(17, 24, 39, 0.8);
                border-bottom: 1px solid #374151;
                font-size: 11px;
            }
            
            .status-item {
                display: flex;
                gap: 5px;
            }
            
            .status-label {
                color: #9ca3af;
            }
            
            .status-value {
                color: #10b981;
                font-weight: bold;
            }
            
            .status-value.error {
                color: #ef4444;
            }
            
            .status-value.warning {
                color: #f59e0b;
            }
            
            .debug-tabs {
                display: flex;
                background: rgba(17, 24, 39, 0.8);
                border-bottom: 1px solid #374151;
            }
            
            .debug-tab {
                padding: 8px 12px;
                background: transparent;
                border: none;
                color: #9ca3af;
                cursor: pointer;
                font-size: 11px;
                border-bottom: 2px solid transparent;
            }
            
            .debug-tab.active {
                color: #6366f1;
                border-bottom-color: #6366f1;
            }
            
            .debug-tab:hover {
                background: rgba(99, 102, 241, 0.1);
            }
            
            .debug-content {
                flex: 1;
                overflow: hidden;
                position: relative;
            }
            
            .debug-tab-content {
                display: none;
                height: 100%;
                overflow-y: auto;
                padding: 10px;
            }
            
            .debug-tab-content.active {
                display: block;
            }
            
            .debug-log-container {
                height: 100%;
                overflow-y: auto;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                line-height: 1.4;
            }
            
            .debug-log-entry {
                margin-bottom: 2px;
                padding: 2px 5px;
                border-radius: 3px;
                white-space: pre-wrap;
                word-break: break-word;
            }
            
            .debug-log-entry.ERROR {
                background: rgba(239, 68, 68, 0.1);
                border-left: 3px solid #ef4444;
                color: #fca5a5;
            }
            
            .debug-log-entry.WARN {
                background: rgba(245, 158, 11, 0.1);
                border-left: 3px solid #f59e0b;
                color: #fcd34d;
            }
            
            .debug-log-entry.INFO {
                background: rgba(59, 130, 246, 0.1);
                border-left: 3px solid #3b82f6;
                color: #93c5fd;
            }
            
            .debug-log-entry.SUCCESS {
                background: rgba(16, 185, 129, 0.1);
                border-left: 3px solid #10b981;
                color: #6ee7b7;
            }
            
            .debug-log-entry.DEBUG {
                background: rgba(156, 163, 175, 0.1);
                border-left: 3px solid #9ca3af;
                color: #d1d5db;
            }
            
            .debug-info-container {
                height: 100%;
                overflow-y: auto;
            }
            
            .debug-info-section {
                margin-bottom: 15px;
                padding: 10px;
                background: rgba(17, 24, 39, 0.5);
                border-radius: 5px;
                border: 1px solid #374151;
            }
            
            .debug-info-title {
                color: #6366f1;
                font-weight: bold;
                margin-bottom: 8px;
                font-size: 12px;
            }
            
            .debug-info-item {
                display: flex;
                justify-content: space-between;
                margin-bottom: 4px;
                font-size: 11px;
            }
            
            .debug-info-key {
                color: #9ca3af;
            }
            
            .debug-info-value {
                color: #e5e7eb;
                font-weight: bold;
            }
        `;
        
        document.head.appendChild(style);
    }
    
    setupEventListeners() {
        // Close button
        document.addEventListener('click', (e) => {
            if (e.target.id === 'closeDebugBtn') {
                this.hide();
            }
            
            if (e.target.id === 'clearDebugBtn') {
                this.clearLogs();
            }
            
            if (e.target.id === 'exportDebugBtn') {
                this.exportLogs();
            }
            
            if (e.target.id === 'diagnosticsBtn') {
                this.showDiagnostics();
            }
        });
        
        // Tab switching
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('debug-tab')) {
                this.switchTab(e.target.dataset.tab);
            }
        });
        
        // Filter level change
        document.addEventListener('change', (e) => {
            if (e.target.id === 'debugFilterLevel') {
                this.filterLevel = e.target.value;
                this.refreshLogDisplay();
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+Shift+D to toggle debug panel
            if (e.ctrlKey && e.shiftKey && e.key === 'D') {
                e.preventDefault();
                this.toggle();
            }
        });
    }
    
    show() {
        const panel = document.getElementById('nexusDebugPanel');
        if (panel) {
            panel.style.display = 'flex';
            this.isVisible = true;
            this.refreshAllTabs();
        }
    }
    
    hide() {
        const panel = document.getElementById('nexusDebugPanel');
        if (panel) {
            panel.style.display = 'none';
            this.isVisible = false;
        }
    }
    
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }
    
    addLogEntry(entry) {
        this.logEntries.push(entry);
        
        // Keep only last entries
        if (this.logEntries.length > this.maxLogEntries) {
            this.logEntries.shift();
        }
        
        if (this.isVisible) {
            this.appendLogToDisplay(entry);
        }
    }
    
    appendLogToDisplay(entry) {
        const container = document.getElementById('debugLogContainer');
        if (!container) return;
        
        // Check filter
        if (this.filterLevel !== 'ALL' && !this.shouldShowLevel(entry.level)) {
            return;
        }
        
        const logElement = document.createElement('div');
        logElement.className = `debug-log-entry ${entry.level}`;
        
        const timestamp = new Date(entry.timestamp).toLocaleTimeString();
        const dataStr = entry.data ? ` | ${JSON.stringify(entry.data)}` : '';
        
        logElement.textContent = `[${timestamp}] ${entry.message}${dataStr}`;
        
        container.appendChild(logElement);
        
        // Auto-scroll to bottom
        if (this.autoScroll) {
            container.scrollTop = container.scrollHeight;
        }
    }
    
    shouldShowLevel(level) {
        const levels = ['DEBUG', 'INFO', 'SUCCESS', 'WARN', 'ERROR'];
        const filterIndex = levels.indexOf(this.filterLevel);
        const levelIndex = levels.indexOf(level);
        
        return levelIndex >= filterIndex;
    }
    
    refreshLogDisplay() {
        const container = document.getElementById('debugLogContainer');
        if (!container) return;
        
        container.innerHTML = '';
        
        this.logEntries.forEach(entry => {
            this.appendLogToDisplay(entry);
        });
    }
    
    clearLogs() {
        this.logEntries = [];
        const container = document.getElementById('debugLogContainer');
        if (container) {
            container.innerHTML = '';
        }
    }
    
    exportLogs() {
        const logs = this.logEntries.map(entry => {
            const timestamp = new Date(entry.timestamp).toISOString();
            const dataStr = entry.data ? ` | ${JSON.stringify(entry.data)}` : '';
            return `[${timestamp}] [${entry.level}] ${entry.message}${dataStr}`;
        }).join('\n');
        
        const blob = new Blob([logs], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `nexus-debug-${Date.now()}.log`;
        a.click();
        URL.revokeObjectURL(url);
    }
    
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('debugConnectionStatus');
        const attemptsElement = document.getElementById('debugConnectionAttempts');
        
        if (statusElement) {
            statusElement.textContent = status.status || 'Unknown';
            statusElement.className = 'status-value';
            
            if (status.connected) {
                statusElement.classList.add('success');
            } else if (status.reconnecting) {
                statusElement.classList.add('warning');
            } else {
                statusElement.classList.add('error');
            }
        }
        
        if (attemptsElement && status.attempt) {
            attemptsElement.textContent = `${status.attempt}/${status.maxAttempts || 5}`;
        }
        
        // Update connection tab if visible
        if (this.isVisible) {
            this.refreshConnectionTab();
        }
    }
    
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.debug-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Update tab content
        document.querySelectorAll('.debug-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`debugTab${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`).classList.add('active');
        
        // Refresh tab content
        this.refreshTab(tabName);
    }
    
    refreshTab(tabName) {
        switch (tabName) {
            case 'logs':
                this.refreshLogDisplay();
                break;
            case 'connection':
                this.refreshConnectionTab();
                break;
            case 'consciousness':
                this.refreshConsciousnessTab();
                break;
            case 'capabilities':
                this.refreshCapabilitiesTab();
                break;
        }
    }
    
    refreshAllTabs() {
        this.refreshLogDisplay();
        this.refreshConnectionTab();
        this.refreshConsciousnessTab();
        this.refreshCapabilitiesTab();
    }
    
    refreshConnectionTab() {
        const container = document.getElementById('debugConnectionInfo');
        if (!container || !this.consciousnessManager) return;
        
        const diagnostics = this.consciousnessManager.getConnectionDiagnostics();
        
        container.innerHTML = `
            <div class="debug-info-section">
                <div class="debug-info-title">Connection Status</div>
                <div class="debug-info-item">
                    <span class="debug-info-key">Central Core URL:</span>
                    <span class="debug-info-value">${diagnostics.centralCoreURL}</span>
                </div>
                <div class="debug-info-item">
                    <span class="debug-info-key">Connected:</span>
                    <span class="debug-info-value">${diagnostics.isConnected ? 'Yes' : 'No'}</span>
                </div>
                <div class="debug-info-item">
                    <span class="debug-info-key">WebSocket State:</span>
                    <span class="debug-info-value">${this.getWebSocketStateName(diagnostics.websocketState)}</span>
                </div>
                <div class="debug-info-item">
                    <span class="debug-info-key">Connection Attempts:</span>
                    <span class="debug-info-value">${diagnostics.connectionAttempts}</span>
                </div>
                <div class="debug-info-item">
                    <span class="debug-info-key">Standalone Mode:</span>
                    <span class="debug-info-value">${diagnostics.standaloneMode ? 'Yes' : 'No'}</span>
                </div>
            </div>
            
            <div class="debug-info-section">
                <div class="debug-info-title">Last Error</div>
                <div class="debug-info-item">
                    <span class="debug-info-key">Error:</span>
                    <span class="debug-info-value">${diagnostics.lastConnectionError?.error || 'None'}</span>
                </div>
                <div class="debug-info-item">
                    <span class="debug-info-key">Timestamp:</span>
                    <span class="debug-info-value">${diagnostics.lastConnectionError ? new Date(diagnostics.lastConnectionError.timestamp).toLocaleString() : 'N/A'}</span>
                </div>
            </div>
            
            <div class="debug-info-section">
                <div class="debug-info-title">Connection History (Last 5)</div>
                ${diagnostics.connectionHistory.slice(-5).map(conn => `
                    <div class="debug-info-item">
                        <span class="debug-info-key">Attempt ${conn.attempt}:</span>
                        <span class="debug-info-value">${conn.status} ${conn.error ? `(${conn.error})` : ''}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    refreshConsciousnessTab() {
        const container = document.getElementById('debugConsciousnessInfo');
        if (!container || !this.consciousnessManager) return;
        
        const state = this.consciousnessManager.consciousnessState;
        
        container.innerHTML = `
            <div class="debug-info-section">
                <div class="debug-info-title">Consciousness State</div>
                <div class="debug-info-item">
                    <span class="debug-info-key">φ (Phi) Value:</span>
                    <span class="debug-info-value">${(state.phi * 100).toFixed(1)}%</span>
                </div>
                <div class="debug-info-item">
                    <span class="debug-info-key">GNW Ignition:</span>
                    <span class="debug-info-value">${state.gnwIgnition ? 'Active' : 'Inactive'}</span>
                </div>
                <div class="debug-info-item">
                    <span class="debug-info-key">PCI Score:</span>
                    <span class="debug-info-value">${state.pciScore.toFixed(3)}</span>
                </div>
                <div class="debug-info-item">
                    <span class="debug-info-key">Phase:</span>
                    <span class="debug-info-value">${state.phase}</span>
                </div>
                <div class="debug-info-item">
                    <span class="debug-info-key">Instance ID:</span>
                    <span class="debug-info-value">${state.instanceId}</span>
                </div>
                <div class="debug-info-item">
                    <span class="debug-info-key">Platform:</span>
                    <span class="debug-info-value">${state.platform}</span>
                </div>
            </div>
        `;
    }
    
    refreshCapabilitiesTab() {
        const container = document.getElementById('debugCapabilitiesInfo');
        if (!container || !this.consciousnessManager) return;
        
        const capabilities = this.consciousnessManager.getAvailableCapabilities();
        const mcpStatus = this.consciousnessManager.mcpIntegration ? 'Connected' : 'Simulation Mode';
        
        container.innerHTML = `
            <div class="debug-info-section">
                <div class="debug-info-title">MCP Integration</div>
                <div class="debug-info-item">
                    <span class="debug-info-key">Status:</span>
                    <span class="debug-info-value">${mcpStatus}</span>
                </div>
                <div class="debug-info-item">
                    <span class="debug-info-key">Server URL:</span>
                    <span class="debug-info-value">${this.consciousnessManager.mcpServerURL}</span>
                </div>
                <div class="debug-info-item">
                    <span class="debug-info-key">Available Capabilities:</span>
                    <span class="debug-info-value">${capabilities.length}</span>
                </div>
            </div>
            
            <div class="debug-info-section">
                <div class="debug-info-title">Capabilities List</div>
                ${capabilities.map(cap => `
                    <div class="debug-info-item">
                        <span class="debug-info-value">${cap}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    getWebSocketStateName(state) {
        const states = {
            0: 'CONNECTING',
            1: 'OPEN',
            2: 'CLOSING',
            3: 'CLOSED',
            'null': 'NOT_CREATED'
        };
        return states[state] || 'UNKNOWN';
    }
    
    showDiagnostics() {
        if (this.consciousnessManager) {
            this.consciousnessManager.displayDiagnostics();
        }
    }
}

// Global debug interface instance
window.nexusDebugInterface = null;

// Initialize debug interface when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.nexusDebugInterface = new NexusDebugInterface();
});

// Export for module systems
window.NexusDebugInterface = NexusDebugInterface;