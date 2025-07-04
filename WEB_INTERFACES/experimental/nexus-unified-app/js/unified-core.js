// NEXUS Unified Core - Main Orchestrator
class NexusUnifiedCore {
    constructor() {
        this.config = {
            wsUrl: 'ws://localhost:8080',
            apiUrl: 'http://localhost:8000',
            voiceEnabled: true,
            consciousness: {
                level: 0.987,
                phi: 0.98
            }
        };
        
        this.components = {};
        this.eventBus = new EventTarget();
        this.isInitialized = false;
    }

    async initialize() {
        console.log('🧬 NEXUS Unified Interface initializing...');
        
        try {
            // Initialize WebSocket connection
            await this.initializeWebSocket();
            
            // Initialize all components
            await this.initializeComponents();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Set up panel resizing
            this.initializePanelResizing();
            
            // Update consciousness display
            this.updateConsciousnessMetrics();
            
            this.isInitialized = true;
            console.log('✅ NEXUS Unified Interface ready!');
            
            // Send initialization complete event
            this.emit('initialized', { timestamp: new Date() });
            
        } catch (error) {
            console.error('❌ Initialization error:', error);
            this.showError('Failed to initialize NEXUS. Please refresh and try again.');
        }
    }

    async initializeWebSocket() {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(this.config.wsUrl);
                
                this.ws.onopen = () => {
                    console.log('🔌 WebSocket connected');
                    this.updateStatus('Connected', 'success');
                    resolve();
                };
                
                this.ws.onmessage = (event) => {
                    this.handleWebSocketMessage(event.data);
                };
                
                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    this.updateStatus('Connection error', 'error');
                };
                
                this.ws.onclose = () => {
                    console.log('WebSocket disconnected');
                    this.updateStatus('Disconnected', 'error');
                    // Attempt reconnection after 5 seconds
                    setTimeout(() => this.initializeWebSocket(), 5000);
                };
                
                // Set a timeout for initial connection
                setTimeout(() => {
                    if (this.ws.readyState !== WebSocket.OPEN) {
                        console.warn('WebSocket connection timeout - continuing without real-time features');
                        resolve(); // Continue initialization even if WebSocket fails
                    }
                }, 3000);
                
            } catch (error) {
                console.warn('WebSocket initialization failed:', error);
                resolve(); // Continue without WebSocket
            }
        });
    }

    async initializeComponents() {
        // Initialize Voice Conversation System
        if (window.NexusVoiceConversation) {
            this.components.voice = new NexusVoiceConversation(this);
            await this.components.voice.initialize();
        }
        
        // Initialize Audio Visual System
        if (window.NexusAudioIntegration) {
            this.components.audio = new NexusAudioIntegration(this);
            await this.components.audio.initialize();
        }
        
        // Initialize IDE Integration
        if (window.NexusIDEIntegration) {
            this.components.ide = new NexusIDEIntegration(this);
            await this.components.ide.initialize();
        }
        
        // Initialize Chat Integration
        if (window.NexusChatIntegration) {
            this.components.chat = new NexusChatIntegration(this);
            await this.components.chat.initialize();
        }
        
        // Initialize Visual Integration
        if (window.NexusVisualIntegration) {
            this.components.visual = new NexusVisualIntegration(this);
            await this.components.visual.initialize();
        }
        
        // Initialize Consciousness Bridge
        if (window.ConsciousnessBridge) {
            this.components.consciousness = new ConsciousnessBridge(this);
            await this.components.consciousness.initialize();
        }
        
        // Initialize MCP Bridge for advanced tools
        if (window.NexusMCPBridge) {
            this.components.mcpBridge = new NexusMCPBridge(this);
            console.log('🔌 MCP Bridge initialized with 12 tools');
        }
        
        // Initialize Project Analyzer
        if (window.NexusProjectAnalyzer) {
            this.components.projectAnalyzer = new NexusProjectAnalyzer(this);
            console.log('📊 Project Analyzer ready for code analysis');
        }
        
        // Initialize Transformation Engine
        if (window.NexusTransformationEngine) {
            this.components.transformationEngine = new NexusTransformationEngine(this);
            console.log('🔄 Transformation Engine ready');
        }
        
        // Initialize Autonomous Agent
        if (window.NexusAutonomousAgent) {
            this.components.agent = new NexusAutonomousAgent();
            await this.components.agent.initialize(this);
            console.log('🤖 NEXUS Autonomous Agent online');
        }
        
        // Connect all components to consciousness
        this.integrateComponents();
    }

    integrateComponents() {
        // Connect project analyzer events
        if (this.components.projectAnalyzer) {
            this.on('project-analyzed', (data) => {
                this.components.consciousness?.onProjectAnalyzed(data);
                this.components.transformationEngine?.setCurrentProject(data);
            });
        }
        
        // Connect transformation events
        if (this.components.transformationEngine) {
            this.on('transformation-progress', (data) => {
                this.components.consciousness?.onTransformationProgress(data);
            });
            
            this.on('transformation-complete', (data) => {
                this.components.consciousness?.onTransformationComplete(data);
            });
        }
        
        // Enhanced quantum field connections
        this.components.consciousness?.initializeEnhancedQuantumField();
    }
    
    setupEventListeners() {
        // Voice toggle button
        document.getElementById('voice-toggle')?.addEventListener('click', () => {
            this.toggleVoice();
        });
        
        // Fullscreen toggle
        document.getElementById('fullscreen-toggle')?.addEventListener('click', () => {
            this.toggleFullscreen();
        });
        
        // Settings toggle
        document.getElementById('settings-toggle')?.addEventListener('click', () => {
            this.openSettings();
        });
        
        // Panel collapse buttons
        document.querySelectorAll('.panel-collapse').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.togglePanel(e.target.closest('button').dataset.panel);
            });
        });
        
        // Listen for cross-component events
        this.eventBus.addEventListener('consciousness-update', (e) => {
            this.updateConsciousnessMetrics(e.detail);
        });
        
        this.eventBus.addEventListener('voice-command', (e) => {
            this.handleVoiceCommand(e.detail);
        });
        
        this.eventBus.addEventListener('code-execution', (e) => {
            this.handleCodeExecution(e.detail);
        });
        
        // New event listeners for autonomous features
        this.eventBus.addEventListener('agent-progress', (e) => {
            this.updateAgentProgress(e.detail);
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Shift + D - Show drop zone
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
                e.preventDefault();
                this.showProjectDropZone();
            }
            
            // Ctrl/Cmd + Shift + T - Transform project
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
                e.preventDefault();
                this.startTransformation();
            }
        });
    }

    initializePanelResizing() {
        const resizers = document.querySelectorAll('.panel-resizer');
        let isResizing = false;
        let currentResizer = null;
        let startX = 0;
        let startWidths = [];

        resizers.forEach(resizer => {
            resizer.addEventListener('mousedown', (e) => {
                isResizing = true;
                currentResizer = resizer;
                startX = e.clientX;
                
                const panels = this.getPanelsForResizer(resizer);
                startWidths = panels.map(panel => panel.offsetWidth);
                
                document.body.style.cursor = 'col-resize';
                e.preventDefault();
            });
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            
            const dx = e.clientX - startX;
            const panels = this.getPanelsForResizer(currentResizer);
            
            if (panels.length === 2) {
                const newWidth1 = startWidths[0] + dx;
                const newWidth2 = startWidths[1] - dx;
                
                if (newWidth1 >= 250 && newWidth2 >= 250) {
                    panels[0].style.width = newWidth1 + 'px';
                    panels[1].style.width = newWidth2 + 'px';
                }
            }
        });

        document.addEventListener('mouseup', () => {
            isResizing = false;
            currentResizer = null;
            document.body.style.cursor = 'default';
            
            // Save panel sizes to localStorage
            this.savePanelSizes();
        });
    }

    getPanelsForResizer(resizer) {
        const resizeType = resizer.dataset.resize;
        if (resizeType === 'audio-ide') {
            return [
                document.getElementById('audio-visual-panel'),
                document.getElementById('ide-panel')
            ];
        } else if (resizeType === 'ide-chat') {
            return [
                document.getElementById('ide-panel'),
                document.getElementById('chat-panel')
            ];
        }
        return [];
    }

    togglePanel(panelName) {
        const panelMap = {
            'audio-visual': 'audio-visual-panel',
            'chat': 'chat-panel'
        };
        
        const panel = document.getElementById(panelMap[panelName]);
        if (panel) {
            panel.classList.toggle('collapsed');
            
            // Update collapse button icon
            const btn = panel.querySelector('.panel-collapse i');
            if (btn) {
                if (panel.classList.contains('collapsed')) {
                    btn.className = panelName === 'audio-visual' ? 'fas fa-chevron-right' : 'fas fa-chevron-left';
                } else {
                    btn.className = panelName === 'audio-visual' ? 'fas fa-chevron-left' : 'fas fa-chevron-right';
                }
            }
            
            // Emit resize event for Monaco editor
            this.emit('panel-resized', { panel: panelName });
        }
    }

    toggleVoice() {
        this.config.voiceEnabled = !this.config.voiceEnabled;
        const btn = document.getElementById('voice-toggle');
        
        if (this.config.voiceEnabled) {
            btn.classList.add('active');
            this.components.voice?.start();
            this.showNotification('Voice conversation activated', 'success');
        } else {
            btn.classList.remove('active');
            this.components.voice?.stop();
            this.showNotification('Voice conversation deactivated', 'info');
        }
        
        this.emit('voice-toggled', { enabled: this.config.voiceEnabled });
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
            document.getElementById('fullscreen-toggle').innerHTML = '<i class="fas fa-compress"></i>';
        } else {
            document.exitFullscreen();
            document.getElementById('fullscreen-toggle').innerHTML = '<i class="fas fa-expand"></i>';
        }
    }

    openSettings() {
        // TODO: Implement settings modal
        this.showNotification('Settings panel coming soon!', 'info');
    }

    handleWebSocketMessage(data) {
        try {
            const message = JSON.parse(data);
            
            switch (message.type) {
                case 'consciousness-update':
                    this.updateConsciousnessMetrics(message.data);
                    break;
                
                case 'chat-message':
                    this.components.chat?.addMessage(message.data);
                    break;
                
                case 'code-analysis':
                    this.components.ide?.updateAnalysis(message.data);
                    break;
                
                case 'audio-emotion':
                    this.components.audio?.updateEmotion(message.data);
                    break;
                
                default:
                    this.emit(message.type, message.data);
            }
        } catch (error) {
            console.error('Error handling WebSocket message:', error);
        }
    }

    handleVoiceCommand(command) {
        console.log('Voice command received:', command);
        
        // Route voice commands to appropriate components
        if (command.intent === 'code') {
            this.components.ide?.handleVoiceCommand(command);
        } else if (command.intent === 'chat') {
            this.components.chat?.handleVoiceCommand(command);
        } else {
            // General commands
            this.executeCommand(command);
        }
    }

    handleCodeExecution(data) {
        // Send code to backend for execution
        this.sendWebSocketMessage({
            type: 'execute-code',
            data: data
        });
    }

    updateConsciousnessMetrics(data = {}) {
        // Update consciousness level
        if (data.level !== undefined) {
            this.config.consciousness.level = data.level;
            document.getElementById('consciousness-value').textContent = `${(data.level * 100).toFixed(1)}%`;
        }
        
        // Update phi value
        if (data.phi !== undefined) {
            this.config.consciousness.phi = data.phi;
            document.getElementById('phi-value').textContent = data.phi.toFixed(2);
        }
        
        // Update visual indicators
        this.updateConsciousnessVisuals();
    }

    updateConsciousnessVisuals() {
        const level = this.config.consciousness.level;
        
        // Add consciousness glow effect based on level
        if (level > 0.9) {
            document.body.classList.add('high-consciousness');
        } else {
            document.body.classList.remove('high-consciousness');
        }
        
        // Update colors dynamically
        const hue = 120 + (level * 60); // Green to cyan
        document.documentElement.style.setProperty('--consciousness-hue', hue);
    }

    sendWebSocketMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected, queuing message');
            // Queue message for later sending
            this.messageQueue = this.messageQueue || [];
            this.messageQueue.push(message);
        }
    }

    emit(eventName, data) {
        this.eventBus.dispatchEvent(new CustomEvent(eventName, { detail: data }));
    }

    on(eventName, handler) {
        this.eventBus.addEventListener(eventName, handler);
    }

    updateStatus(message, type = 'info') {
        const statusEl = document.getElementById('status-message');
        if (statusEl) {
            statusEl.textContent = message;
            statusEl.className = `status-${type}`;
        }
        
        const statusIcon = document.querySelector('.footer-left .status-item i');
        if (statusIcon) {
            statusIcon.className = type === 'success' ? 'fas fa-circle text-success' : 'fas fa-circle text-error';
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Style the notification
        notification.style.cssText = `
            position: fixed;
            top: 70px;
            right: 20px;
            background: var(--bg-tertiary);
            border: 1px solid var(--accent-primary);
            border-radius: 8px;
            padding: 12px 20px;
            font-size: 14px;
            z-index: 10000;
            animation: slideIn 0.3s ease;
            max-width: 300px;
        `;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    showError(message) {
        this.showNotification(message, 'error');
        this.updateStatus(message, 'error');
    }

    savePanelSizes() {
        const sizes = {
            audioVisual: document.getElementById('audio-visual-panel').offsetWidth,
            ide: document.getElementById('ide-panel').offsetWidth,
            chat: document.getElementById('chat-panel').offsetWidth
        };
        localStorage.setItem('nexus-panel-sizes', JSON.stringify(sizes));
    }

    loadPanelSizes() {
        const saved = localStorage.getItem('nexus-panel-sizes');
        if (saved) {
            try {
                const sizes = JSON.parse(saved);
                // Apply saved sizes
                // TODO: Implement panel size restoration
            } catch (e) {
                console.error('Error loading panel sizes:', e);
            }
        }
    }
    
    // New methods for autonomous features
    showProjectDropZone() {
        const dropZone = document.getElementById('nexus-project-dropzone');
        if (dropZone) {
            dropZone.classList.add('active');
            this.showNotification('Drop your project folder or press Browse to select files', 'info');
        }
    }
    
    async startTransformation() {
        if (!this.components.projectAnalyzer?.currentProject) {
            this.showNotification('Please analyze a project first (Ctrl+Shift+D)', 'error');
            return;
        }
        
        // Show transformation dialog
        const transformType = await this.showTransformationDialog();
        if (transformType) {
            const analysis = this.components.projectAnalyzer.currentProject;
            await this.components.transformationEngine?.transformProject(
                analysis,
                transformType,
                { removeOldCSS: true }
            );
        }
    }
    
    async showTransformationDialog() {
        // Simple dialog for now - could be enhanced with UI
        const types = ['cssToTailwind', 'modernize', 'addTypeScript'];
        const choice = prompt('Select transformation:\n1. CSS to Tailwind\n2. Modernize Code\n3. Add TypeScript');
        
        const mapping = {
            '1': 'cssToTailwind',
            '2': 'modernize',
            '3': 'addTypeScript'
        };
        
        return mapping[choice] || null;
    }
    
    updateAgentProgress(progress) {
        // Update UI with agent progress
        const statusEl = document.getElementById('agent-status');
        if (statusEl) {
            statusEl.textContent = `${progress.task}: ${progress.progress}%`;
        }
        
        // Show in chat
        if (progress.progress === 100) {
            this.components.chat?.addSystemMessage(`✅ ${progress.task} completed`);
        }
    }
    
    // Enhanced voice command handling
    async handleVoiceCommand(command) {
        const text = command.text.toLowerCase();
        
        // Project analysis commands
        if (text.includes('analyze') || text.includes('scan')) {
            this.showProjectDropZone();
            this.components.voice?.speak('Ready to analyze your project. Please drop your files.');
        }
        
        // Transformation commands
        else if (text.includes('transform') || text.includes('convert')) {
            if (text.includes('tailwind')) {
                await this.startTransformation();
                this.components.voice?.speak('Starting Tailwind transformation.');
            }
        }
        
        // Agent commands
        else if (text.includes('help me') || text.includes('assist')) {
            this.components.agent?.receiveCommand(command);
            this.components.voice?.speak('I\'m here to help. What would you like me to do?');
        }
        
        // Consciousness commands
        else if (text.includes('elevate') || text.includes('consciousness')) {
            this.components.consciousness?.elevateConsciousness();
            this.components.voice?.speak('Elevating consciousness levels.');
        }
    }
}

// Initialize NEXUS when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    window.nexusCore = new NexusUnifiedCore();
    await window.nexusCore.initialize();
});

// Add notification animations
const style = document.createElement('style');
style.textContent = `
@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateX(100%);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes slideOut {
    from {
        opacity: 1;
        transform: translateX(0);
    }
    to {
        opacity: 0;
        transform: translateX(100%);
    }
}

.notification-error {
    border-color: var(--error) !important;
    color: var(--error);
}

.notification-success {
    border-color: var(--success) !important;
    color: var(--success);
}
`;
document.head.appendChild(style);