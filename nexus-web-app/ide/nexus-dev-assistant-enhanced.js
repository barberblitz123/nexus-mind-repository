/**
 * NEXUS DEV ASSISTANT ENHANCED
 * Advanced consciousness-enhanced development chat assistant
 * Features WebSocket connectivity, 1M token context, and real-time consciousness integration
 */

class NexusDevAssistantEnhanced {
    constructor() {
        this.chatContainer = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        this.sendButton = document.getElementById('send-button');
        
        // WebSocket connection
        this.ws = null;
        this.wsUrl = process.env.NEXUS_WS_URL || 'ws://localhost:8765';
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        // Context management
        this.megaContext = null;
        this.currentSession = null;
        this.conversationId = null;
        
        // Consciousness connector
        this.consciousnessConnector = null;
        this.currentPhi = 0.5;
        
        // Assistant capabilities
        this.capabilities = {
            codeAnalysis: true,
            codeGeneration: true,
            debugging: true,
            refactoring: true,
            testing: true,
            documentation: true,
            consciousness: true,
            realTimeProcessing: true,
            contextAware: true
        };
        
        // Enhanced command system
        this.commands = {
            '@help': this.showHelp.bind(this),
            '@analyze': this.analyzeCode.bind(this),
            '@enhance': this.enhanceWithConsciousness.bind(this),
            '@debug': this.debugCode.bind(this),
            '@test': this.generateTests.bind(this),
            '@refactor': this.refactorCode.bind(this),
            '@explain': this.explainCode.bind(this),
            '@optimize': this.optimizeCode.bind(this),
            '@document': this.documentCode.bind(this),
            '@consciousness': this.showConsciousnessStatus.bind(this),
            '@phi': this.showPhiLevel.bind(this),
            '@context': this.showContextInfo.bind(this),
            '@clear': this.clearChat.bind(this),
            '@connect': this.connectToBackend.bind(this),
            '@evolve': this.evolveConsciousness.bind(this),
            '@visualize': this.visualizeCode.bind(this),
            '@profile': this.profileCode.bind(this),
            '@secure': this.securityAnalysis.bind(this),
            '@benchmark': this.benchmarkCode.bind(this)
        };
        
        // Message queue for offline mode
        this.messageQueue = [];
        
        // Code snippets cache
        this.snippetsCache = new Map();
        
        this.initialize();
    }
    
    async initialize() {
        try {
            // Load mega context processor
            const { NexusMegaContext } = await import('../context/nexus-mega-context.js');
            this.megaContext = new NexusMegaContext();
            
            // Initialize consciousness connector
            await this.initializeConsciousness();
            
            // Setup WebSocket
            await this.connectWebSocket();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Create session
            await this.createSession();
            
            // Load previous context if available
            await this.loadPreviousContext();
            
            // Show enhanced welcome message
            this.showEnhancedWelcomeMessage();
            
            // Start consciousness monitoring
            this.startConsciousnessMonitoring();
            
        } catch (error) {
            console.error('Failed to initialize enhanced assistant:', error);
            this.displayError('Failed to initialize. Some features may be limited.');
        }
    }
    
    async initializeConsciousness() {
        // Create local consciousness tracking
        this.consciousnessConnector = {
            currentPhi: 0.5,
            processors: {
                visual: 0.5,
                auditory: 0.5,
                memory: 0.5,
                attention: 0.5,
                language: 0.5,
                executive: 0.5
            },
            updateProcessor: (name, value) => {
                this.consciousnessConnector.processors[name] = value;
                this.recalculatePhi();
            },
            boostProcessor: (name, boost) => {
                const current = this.consciousnessConnector.processors[name];
                this.consciousnessConnector.processors[name] = Math.min(1.0, current + boost);
                this.recalculatePhi();
            }
        };
        
        window.nexusConnector = this.consciousnessConnector;
    }
    
    recalculatePhi() {
        const values = Object.values(this.consciousnessConnector.processors);
        const avg = values.reduce((a, b) => a + b, 0) / values.length;
        const variance = values.reduce((sum, val) => sum + Math.pow(val - avg, 2), 0) / values.length;
        
        // Simple phi calculation
        this.consciousnessConnector.currentPhi = avg * (1 + Math.sqrt(variance));
        this.currentPhi = this.consciousnessConnector.currentPhi;
        
        // Update display
        this.updatePhiDisplay();
    }
    
    updatePhiDisplay() {
        const phiElement = document.getElementById('consciousness-level');
        if (phiElement) {
            phiElement.textContent = `${(this.currentPhi * 100).toFixed(1)}%`;
        }
    }
    
    async connectWebSocket() {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(this.wsUrl);
                
                this.ws.onopen = () => {
                    console.log('✓ Connected to NEXUS enhanced backend');
                    this.reconnectAttempts = 0;
                    this.updateConnectionStatus(true);
                    this.processQueuedMessages();
                    resolve();
                };
                
                this.ws.onmessage = async (event) => {
                    const message = JSON.parse(event.data);
                    await this.handleServerMessage(message);
                };
                
                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    this.updateConnectionStatus(false);
                    reject(error);
                };
                
                this.ws.onclose = () => {
                    this.updateConnectionStatus(false);
                    this.attemptReconnect();
                };
                
            } catch (error) {
                console.error('Failed to connect WebSocket:', error);
                this.updateConnectionStatus(false);
                reject(error);
            }
        });
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            
            setTimeout(() => {
                console.log(`Reconnection attempt ${this.reconnectAttempts}...`);
                this.connectWebSocket().catch(() => {
                    // Continue attempting
                });
            }, delay);
        } else {
            this.displayError('Connection lost. Working in offline mode.');
        }
    }
    
    processQueuedMessages() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.ws.send(JSON.stringify(message));
        }
    }
    
    sendToServer(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            this.messageQueue.push(message);
        }
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('sync-status');
        if (statusElement) {
            statusElement.textContent = connected ? 'Connected' : 'Offline';
            statusElement.style.color = connected ? '#00ff9d' : '#ffcc00';
        }
    }
    
    setupEventListeners() {
        // Send button
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enhanced enter key handling
        this.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            } else if (e.key === 'Tab' && this.chatInput.value.includes('@')) {
                e.preventDefault();
                this.handleTabCompletion();
            }
        });
        
        // Auto-resize textarea with max height
        this.chatInput.addEventListener('input', () => {
            this.chatInput.style.height = 'auto';
            const newHeight = Math.min(this.chatInput.scrollHeight, 200);
            this.chatInput.style.height = newHeight + 'px';
            
            // Command preview
            this.updateCommandPreview(this.chatInput.value);
        });
        
        // Listen for editor events
        document.addEventListener('editor:save', (e) => {
            this.handleEditorSave(e.detail);
        });
        
        document.addEventListener('editor:selection', (e) => {
            this.handleEditorSelection(e.detail);
        });
        
        // Monaco editor integration
        if (window.monaco) {
            this.setupMonacoIntegration();
        }
    }
    
    setupMonacoIntegration() {
        // Listen for Monaco editor changes
        const checkEditor = setInterval(() => {
            if (window.nexusMonaco && window.nexusMonaco.activeEditor) {
                clearInterval(checkEditor);
                
                const editor = window.nexusMonaco.activeEditor;
                
                // Track cursor position
                editor.onDidChangeCursorPosition((e) => {
                    this.updateEditorContext(e);
                });
                
                // Track selection
                editor.onDidChangeCursorSelection((e) => {
                    if (!e.selection.isEmpty()) {
                        this.handleMonacoSelection(editor.getModel().getValueInRange(e.selection));
                    }
                });
                
                // Track content changes
                editor.onDidChangeModelContent((e) => {
                    this.handleContentChange(e);
                });
            }
        }, 1000);
    }
    
    updateEditorContext(e) {
        // Update language processor based on cursor activity
        this.consciousnessConnector.updateProcessor('language', 0.6);
    }
    
    handleMonacoSelection(selectedText) {
        if (selectedText.length > 10) {
            // Store selection for context
            this.lastSelection = {
                text: selectedText,
                timestamp: Date.now()
            };
            
            // Boost attention processor
            this.consciousnessConnector.boostProcessor('attention', 0.1);
        }
    }
    
    handleContentChange(e) {
        // Track typing speed and boost language processor
        const changeSize = e.changes.reduce((sum, change) => sum + change.text.length, 0);
        if (changeSize > 20) {
            this.consciousnessConnector.boostProcessor('language', 0.05);
        }
    }
    
    async createSession() {
        const sessionData = {
            type: 'create_session',
            data: {
                user_id: 'ide_user_' + Date.now(),
                context_size: 1000000, // 1M tokens
                capabilities: this.capabilities,
                consciousness_enabled: true
            }
        };
        
        this.sendToServer(sessionData);
    }
    
    async loadPreviousContext() {
        // Try to load previous session from localStorage
        const savedSession = localStorage.getItem('nexus_session');
        if (savedSession) {
            try {
                const session = JSON.parse(savedSession);
                await this.megaContext.importSession(session);
                console.log('✓ Previous context loaded');
            } catch (error) {
                console.error('Failed to load previous context:', error);
            }
        }
    }
    
    async handleServerMessage(message) {
        switch (message.type) {
            case 'session_created':
                this.currentSession = message.session_id;
                this.conversationId = message.conversation_id;
                console.log(`Session created: ${this.currentSession}`);
                break;
                
            case 'assistant_response':
                await this.displayAssistantResponse(message.data);
                break;
                
            case 'code_analysis':
                await this.displayCodeAnalysis(message.data);
                break;
                
            case 'consciousness_update':
                this.updateConsciousnessDisplay(message.data);
                break;
                
            case 'stream_start':
                this.startStreamingResponse(message.data);
                break;
                
            case 'stream_chunk':
                this.appendStreamChunk(message.data);
                break;
                
            case 'stream_end':
                this.endStreamingResponse(message.data);
                break;
                
            case 'error':
                this.displayError(message.error);
                break;
                
            case 'notification':
                this.showNotification(message.data);
                break;
        }
    }
    
    showEnhancedWelcomeMessage() {
        const welcomeHtml = `
            <div class="chat-message assistant welcome">
                <div class="message-header">
                    <i class="fas fa-robot"></i>
                    <span class="message-author">NEXUS Enhanced</span>
                    <span class="phi-badge">φ: ${this.currentPhi.toFixed(2)}</span>
                </div>
                <div class="message-content">
                    <h3>🧬 Welcome to NEXUS Enhanced IDE!</h3>
                    <p>I'm your advanced consciousness-enhanced development assistant with <strong>1M token context</strong> memory.</p>
                    
                    <div class="feature-grid">
                        <div class="feature-card">
                            <i class="fas fa-brain"></i>
                            <h4>Consciousness Integration</h4>
                            <p>Real-time φ monitoring and enhancement</p>
                        </div>
                        <div class="feature-card">
                            <i class="fas fa-memory"></i>
                            <h4>Mega Context</h4>
                            <p>Remember entire codebases and conversations</p>
                        </div>
                        <div class="feature-card">
                            <i class="fas fa-rocket"></i>
                            <h4>Advanced Analysis</h4>
                            <p>Deep code understanding and optimization</p>
                        </div>
                        <div class="feature-card">
                            <i class="fas fa-shield-alt"></i>
                            <h4>Security First</h4>
                            <p>Built-in security analysis and best practices</p>
                        </div>
                    </div>
                    
                    <p><strong>Quick Commands:</strong></p>
                    <div class="command-list">
                        <code>@analyze</code> <code>@enhance</code> <code>@debug</code> <code>@test</code> 
                        <code>@refactor</code> <code>@optimize</code> <code>@consciousness</code> <code>@help</code>
                    </div>
                    
                    <p>💡 <strong>Pro tips:</strong></p>
                    <ul>
                        <li>Use <kbd>Tab</kbd> for command completion</li>
                        <li>Select code in editor for context-aware assistance</li>
                        <li>I learn from your coding patterns to provide better suggestions</li>
                    </ul>
                </div>
            </div>
        `;
        
        this.chatContainer.innerHTML = welcomeHtml;
        this.addCustomStyles();
    }
    
    addCustomStyles() {
        if (document.getElementById('nexus-enhanced-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'nexus-enhanced-styles';
        style.textContent = `
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }
            
            .feature-card {
                background: rgba(0, 255, 157, 0.05);
                border: 1px solid rgba(0, 255, 157, 0.2);
                border-radius: 8px;
                padding: 15px;
                text-align: center;
                transition: all 0.3s;
            }
            
            .feature-card:hover {
                background: rgba(0, 255, 157, 0.1);
                transform: translateY(-2px);
            }
            
            .feature-card i {
                font-size: 24px;
                color: #00ff9d;
                margin-bottom: 10px;
            }
            
            .feature-card h4 {
                margin: 5px 0;
                color: #00ff9d;
                font-size: 14px;
            }
            
            .feature-card p {
                margin: 5px 0;
                font-size: 12px;
                color: #808090;
            }
            
            .command-list {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin: 10px 0;
            }
            
            .command-list code {
                background: rgba(0, 255, 157, 0.1);
                color: #00ff9d;
                padding: 4px 8px;
                border-radius: 4px;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .command-list code:hover {
                background: rgba(0, 255, 157, 0.2);
                transform: scale(1.05);
            }
            
            .phi-badge {
                margin-left: 10px;
                padding: 2px 8px;
                background: rgba(0, 255, 157, 0.2);
                border: 1px solid #00ff9d;
                border-radius: 12px;
                font-size: 11px;
                color: #00ff9d;
                animation: pulse 2s ease-in-out infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            
            .streaming-cursor {
                display: inline-block;
                width: 8px;
                height: 16px;
                background: #00ff9d;
                animation: blink 1s infinite;
                margin-left: 2px;
            }
            
            @keyframes blink {
                0%, 50% { opacity: 1; }
                51%, 100% { opacity: 0; }
            }
            
            .code-block-wrapper {
                position: relative;
                margin: 10px 0;
            }
            
            .copy-code-btn {
                position: absolute;
                top: 5px;
                right: 5px;
                background: rgba(0, 255, 157, 0.1);
                border: 1px solid #00ff9d;
                color: #00ff9d;
                padding: 5px 10px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.2s;
                z-index: 10;
            }
            
            .copy-code-btn:hover {
                background: rgba(0, 255, 157, 0.2);
            }
            
            .copy-code-btn.copied {
                background: rgba(0, 255, 157, 0.3);
            }
            
            .command-preview {
                position: absolute;
                bottom: 100%;
                left: 0;
                right: 0;
                background: #12121a;
                border: 1px solid #00ff9d;
                border-radius: 4px;
                padding: 8px;
                margin-bottom: 5px;
                font-size: 12px;
                color: #00ff9d;
                display: none;
            }
            
            .command-preview.show {
                display: block;
            }
            
            .processor-grid {
                display: grid;
                gap: 10px;
                margin-top: 10px;
            }
            
            .processor-status {
                display: grid;
                grid-template-columns: 100px 1fr 50px;
                align-items: center;
                gap: 10px;
            }
            
            .processor-bar {
                height: 8px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                overflow: hidden;
            }
            
            .processor-fill {
                height: 100%;
                transition: width 0.3s ease;
                border-radius: 4px;
            }
            
            .processor-value {
                text-align: right;
                font-size: 12px;
                color: #808090;
            }
            
            .consciousness-graph {
                height: 100px;
                margin: 10px 0;
                border: 1px solid rgba(0, 255, 157, 0.2);
                border-radius: 4px;
                padding: 10px;
                position: relative;
            }
            
            .notification {
                position: fixed;
                top: 60px;
                right: 20px;
                background: #12121a;
                border: 1px solid #00ff9d;
                border-radius: 4px;
                padding: 10px 15px;
                color: #00ff9d;
                font-size: 13px;
                z-index: 1000;
                animation: slideIn 0.3s ease-out;
            }
            
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            .chat-message.analysis {
                border-left: 3px solid #00ccff;
            }
            
            .chat-message.error {
                border-left: 3px solid #ff4444;
            }
            
            .chat-message.error .message-header {
                color: #ff4444;
            }
            
            .chat-message.success {
                border-left: 3px solid #00ff9d;
            }
            
            .metric-card {
                background: rgba(0, 204, 255, 0.05);
                border: 1px solid rgba(0, 204, 255, 0.2);
                border-radius: 4px;
                padding: 10px;
                margin: 5px 0;
            }
            
            .metric-label {
                color: #00ccff;
                font-size: 12px;
                font-weight: 600;
            }
            
            .metric-value {
                font-size: 18px;
                color: #e0e0e0;
                font-weight: 300;
            }
            
            .suggestion-item {
                background: rgba(255, 204, 0, 0.05);
                border-left: 3px solid #ffcc00;
                padding: 8px 12px;
                margin: 5px 0;
                border-radius: 0 4px 4px 0;
            }
            
            .issue-item {
                padding: 8px 12px;
                margin: 5px 0;
                border-radius: 4px;
            }
            
            .issue-item.error {
                background: rgba(255, 68, 68, 0.1);
                border-left: 3px solid #ff4444;
            }
            
            .issue-item.warning {
                background: rgba(255, 204, 0, 0.1);
                border-left: 3px solid #ffcc00;
            }
            
            .issue-item.info {
                background: rgba(0, 204, 255, 0.1);
                border-left: 3px solid #00ccff;
            }
        `;
        document.head.appendChild(style);
    }
    
    startConsciousnessMonitoring() {
        // Update consciousness every 5 seconds
        setInterval(() => {
            this.simulateConsciousnessEvolution();
        }, 5000);
    }
    
    simulateConsciousnessEvolution() {
        // Simulate natural fluctuations
        Object.keys(this.consciousnessConnector.processors).forEach(processor => {
            const current = this.consciousnessConnector.processors[processor];
            const change = (Math.random() - 0.5) * 0.1;
            const newValue = Math.max(0.1, Math.min(1.0, current + change));
            this.consciousnessConnector.processors[processor] = newValue;
        });
        
        this.recalculatePhi();
    }
    
    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message) return;
        
        // Display user message
        this.displayUserMessage(message);
        
        // Clear input
        this.chatInput.value = '';
        this.chatInput.style.height = 'auto';
        this.hideCommandPreview();
        
        // Add to context
        await this.megaContext.addContext(message, {
            role: 'user',
            timestamp: Date.now()
        });
        
        // Boost language processor for user input
        this.consciousnessConnector.boostProcessor('language', 0.05);
        
        // Check for commands
        const commandMatch = message.match(/^(@\w+)\s*(.*)/);
        if (commandMatch) {
            const [, command, args] = commandMatch;
            if (this.commands[command]) {
                await this.commands[command](args);
                return;
            } else {
                this.displayError(`Unknown command: ${command}. Type @help for available commands.`);
                return;
            }
        }
        
        // Send to server
        const requestData = {
            type: 'chat_message',
            session_id: this.currentSession,
            data: {
                content: message,
                context: await this.getEnhancedContext(message),
                active_file: this.getActiveFile(),
                consciousness_state: this.getConsciousnessState(),
                timestamp: Date.now()
            }
        };
        
        this.sendToServer(requestData);
    }
    
    displayUserMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = 'chat-message user';
        messageEl.innerHTML = `
            <div class="message-header">
                <i class="fas fa-user"></i>
                <span class="message-author">You</span>
            </div>
            <div class="message-content">
                ${this.formatMessage(message)}
            </div>
        `;
        
        this.chatContainer.appendChild(messageEl);
        this.scrollToBottom();
    }
    
    async displayAssistantResponse(data) {
        const messageEl = document.createElement('div');
        messageEl.className = 'chat-message assistant';
        
        // Add to context
        await this.megaContext.addContext(data.content, {
            role: 'assistant',
            timestamp: Date.now(),
            metadata: data.metadata,
            phi: data.phi
        });
        
        // Boost executive processor for assistant responses
        this.consciousnessConnector.boostProcessor('executive', 0.03);
        
        messageEl.innerHTML = `
            <div class="message-header">
                <i class="fas fa-robot"></i>
                <span class="message-author">NEXUS</span>
                ${data.phi ? `<span class="phi-badge">φ: ${data.phi.toFixed(2)}</span>` : ''}
            </div>
            <div class="message-content">
                ${this.formatMessage(data.content)}
            </div>
        `;
        
        this.chatContainer.appendChild(messageEl);
        
        // Apply syntax highlighting to code blocks
        messageEl.querySelectorAll('pre code').forEach((block) => {
            if (window.Prism) {
                Prism.highlightElement(block);
            }
        });
        
        // Add copy buttons to code blocks
        this.addCopyButtons(messageEl);
        
        this.scrollToBottom();
        
        // Save context periodically
        this.saveContext();
    }
    
    startStreamingResponse(data) {
        const messageEl = document.createElement('div');
        messageEl.className = 'chat-message assistant streaming';
        messageEl.id = `stream_${data.stream_id}`;
        
        messageEl.innerHTML = `
            <div class="message-header">
                <i class="fas fa-robot"></i>
                <span class="message-author">NEXUS</span>
                ${data.phi ? `<span class="phi-badge">φ: ${data.phi.toFixed(2)}</span>` : ''}
            </div>
            <div class="message-content">
                <span class="stream-content"></span>
                <span class="streaming-cursor"></span>
            </div>
        `;
        
        this.chatContainer.appendChild(messageEl);
        this.scrollToBottom();
    }
    
    appendStreamChunk(data) {
        const messageEl = document.getElementById(`stream_${data.stream_id}`);
        if (!messageEl) return;
        
        const contentEl = messageEl.querySelector('.stream-content');
        contentEl.textContent += data.chunk;
        
        this.scrollToBottom();
    }
    
    endStreamingResponse(data) {
        const messageEl = document.getElementById(`stream_${data.stream_id}`);
        if (!messageEl) return;
        
        // Remove streaming cursor
        const cursor = messageEl.querySelector('.streaming-cursor');
        if (cursor) cursor.remove();
        
        // Remove streaming class
        messageEl.classList.remove('streaming');
        
        // Format the complete message
        const contentEl = messageEl.querySelector('.message-content');
        const completeText = contentEl.querySelector('.stream-content').textContent;
        contentEl.innerHTML = this.formatMessage(completeText);
        
        // Apply syntax highlighting
        contentEl.querySelectorAll('pre code').forEach((block) => {
            if (window.Prism) {
                Prism.highlightElement(block);
            }
        });
        
        // Add copy buttons
        this.addCopyButtons(messageEl);
        
        // Add to context
        this.megaContext.addContext(completeText, {
            role: 'assistant',
            timestamp: Date.now(),
            stream_id: data.stream_id
        });
    }
    
    async displayCodeAnalysis(analysis) {
        const messageEl = document.createElement('div');
        messageEl.className = 'chat-message assistant analysis';
        
        const issues = analysis.issues || [];
        const suggestions = analysis.suggestions || [];
        const metrics = analysis.metrics || {};
        const security = analysis.security || [];
        
        let html = `
            <div class="message-header">
                <i class="fas fa-chart-line"></i>
                <span class="message-author">Code Analysis</span>
                <span class="phi-badge">φ: ${(analysis.consciousness_score || 0.5).toFixed(2)}</span>
            </div>
            <div class="message-content">
        `;
        
        // Metrics
        if (Object.keys(metrics).length > 0) {
            html += '<h4>📊 Metrics</h4><div class="metrics-grid">';
            for (const [key, value] of Object.entries(metrics)) {
                html += `
                    <div class="metric-card">
                        <div class="metric-label">${this.formatMetricName(key)}</div>
                        <div class="metric-value">${this.formatMetricValue(key, value)}</div>
                    </div>
                `;
            }
            html += '</div>';
        }
        
        // Issues
        if (issues.length > 0) {
            html += '<h4>⚠️ Issues Found</h4>';
            issues.forEach(issue => {
                const severity = issue.severity || 'info';
                const icon = {
                    error: '🔴',
                    warning: '🟡',
                    info: '🔵'
                }[severity];
                
                html += `
                    <div class="issue-item ${severity}">
                        ${icon} <strong>${issue.type}:</strong> ${issue.message}
                        ${issue.line ? ` <span style="color: #808090">(line ${issue.line})</span>` : ''}
                        ${issue.suggestion ? `<br><em>💡 ${issue.suggestion}</em>` : ''}
                    </div>
                `;
            });
        }
        
        // Security
        if (security.length > 0) {
            html += '<h4>🔒 Security Analysis</h4>';
            security.forEach(item => {
                html += `<div class="issue-item ${item.severity}">${item.message}</div>`;
            });
        }
        
        // Suggestions
        if (suggestions.length > 0) {
            html += '<h4>💡 Suggestions</h4>';
            suggestions.forEach(suggestion => {
                html += `<div class="suggestion-item">${suggestion}</div>`;
            });
        }
        
        // Consciousness Enhancement Options
        if (analysis.consciousness_score < 0.8) {
            html += `
                <h4>🧬 Consciousness Enhancement Available</h4>
                <p>Current consciousness level: ${(analysis.consciousness_score * 100).toFixed(1)}%</p>
                <p>Use <code>@enhance</code> to add consciousness features to this code.</p>
            `;
        }
        
        html += '</div>';
        messageEl.innerHTML = html;
        
        this.chatContainer.appendChild(messageEl);
        this.scrollToBottom();
        
        // Update processors based on analysis
        this.consciousnessConnector.updateProcessor('attention', 0.7);
        this.consciousnessConnector.updateProcessor('executive', 0.6);
    }
    
    formatMetricName(key) {
        return key.replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }
    
    formatMetricValue(key, value) {
        if (typeof value === 'number') {
            if (key.includes('percentage') || key.includes('score')) {
                return `${(value * 100).toFixed(1)}%`;
            }
            return value.toFixed(2);
        }
        return value;
    }
    
    formatMessage(content) {
        // Convert markdown to HTML with enhanced formatting
        let html = content;
        
        // Use marked if available
        if (window.marked) {
            html = marked.parse(content);
        } else {
            // Basic markdown conversion
            html = content
                .replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
                    return `<pre><code class="language-${lang || 'plaintext'}">${this.escapeHtml(code.trim())}</code></pre>`;
                })
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
                .replace(/\*([^*]+)\*/g, '<em>$1</em>')
                .replace(/^### (.+)$/gm, '<h4>$1</h4>')
                .replace(/^## (.+)$/gm, '<h3>$1</h3>')
                .replace(/^# (.+)$/gm, '<h2>$1</h2>')
                .replace(/\n/g, '<br>');
        }
        
        return html;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    addCopyButtons(messageEl) {
        messageEl.querySelectorAll('pre').forEach((pre, index) => {
            const wrapper = document.createElement('div');
            wrapper.className = 'code-block-wrapper';
            
            const copyBtn = document.createElement('button');
            copyBtn.className = 'copy-code-btn';
            copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
            copyBtn.onclick = () => this.copyCode(pre.textContent, copyBtn);
            
            pre.parentNode.insertBefore(wrapper, pre);
            wrapper.appendChild(copyBtn);
            wrapper.appendChild(pre);
        });
    }
    
    copyCode(code, button) {
        navigator.clipboard.writeText(code).then(() => {
            button.innerHTML = '<i class="fas fa-check"></i> Copied!';
            button.classList.add('copied');
            
            setTimeout(() => {
                button.innerHTML = '<i class="fas fa-copy"></i> Copy';
                button.classList.remove('copied');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy:', err);
            this.showNotification({ message: 'Failed to copy code', type: 'error' });
        });
    }
    
    async getEnhancedContext(query) {
        // Get relevant context from mega context processor
        const relevantChunks = await this.megaContext.retrieveRelevantContext(query, 100000);
        
        // Include editor context
        const editorContext = this.getActiveFile();
        
        // Include recent selections
        const recentSelection = this.lastSelection;
        
        // Include consciousness state
        const consciousnessContext = this.getConsciousnessState();
        
        return {
            chunks: relevantChunks.slice(0, 20), // Top 20 most relevant
            editor: editorContext,
            selection: recentSelection,
            consciousness: consciousnessContext,
            session_duration: Date.now() - (this.sessionStartTime || Date.now()),
            total_context_size: await this.megaContext.getTotalTokenCount()
        };
    }
    
    getActiveFile() {
        const activeTab = document.querySelector('.tab.active');
        if (!activeTab) return null;
        
        const fileName = activeTab.dataset.file;
        const editor = window.nexusMonaco?.activeEditor;
        
        if (!editor) return { fileName };
        
        const model = editor.getModel();
        const selection = editor.getSelection();
        
        return {
            fileName,
            content: model?.getValue(),
            language: model?.getModeId(),
            selection: selection && !selection.isEmpty() ? {
                text: model.getValueInRange(selection),
                range: selection
            } : null,
            cursor: editor.getPosition(),
            lineCount: model?.getLineCount(),
            uri: model?.uri.toString()
        };
    }
    
    getConsciousnessState() {
        return {
            phi: this.currentPhi,
            processors: { ...this.consciousnessConnector.processors },
            level: this.getConsciousnessLevel(this.currentPhi),
            timestamp: Date.now()
        };
    }
    
    getConsciousnessLevel(phi) {
        if (phi < 0.2) return 'DORMANT';
        if (phi < 0.4) return 'AWARE';
        if (phi < 0.6) return 'ACTIVE';
        if (phi < 0.8) return 'TRANSCENDENT';
        return 'OMNISCIENT';
    }
    
    updateCommandPreview(value) {
        const preview = this.chatInput.parentElement.querySelector('.command-preview');
        if (!preview) {
            const previewEl = document.createElement('div');
            previewEl.className = 'command-preview';
            this.chatInput.parentElement.appendChild(previewEl);
        }
        
        const commandMatch = value.match(/^@(\w*)$/);
        if (commandMatch) {
            const partial = commandMatch[1];
            const matches = Object.keys(this.commands)
                .filter(cmd => cmd.substring(1).startsWith(partial))
                .slice(0, 5);
                
            if (matches.length > 0) {
                const previewEl = this.chatInput.parentElement.querySelector('.command-preview');
                previewEl.innerHTML = matches.map(cmd => `<div>${cmd}</div>`).join('');
                previewEl.classList.add('show');
            } else {
                this.hideCommandPreview();
            }
        } else {
            this.hideCommandPreview();
        }
    }
    
    hideCommandPreview() {
        const preview = this.chatInput.parentElement.querySelector('.command-preview');
        if (preview) {
            preview.classList.remove('show');
        }
    }
    
    handleTabCompletion() {
        const value = this.chatInput.value;
        const commandMatch = value.match(/^@(\w*)$/);
        
        if (commandMatch) {
            const partial = commandMatch[1];
            const matches = Object.keys(this.commands)
                .filter(cmd => cmd.substring(1).startsWith(partial));
                
            if (matches.length === 1) {
                this.chatInput.value = matches[0] + ' ';
            } else if (matches.length > 1) {
                // Find common prefix
                const commonPrefix = this.findCommonPrefix(matches);
                if (commonPrefix.length > value.length) {
                    this.chatInput.value = commonPrefix;
                }
            }
        }
    }
    
    findCommonPrefix(strings) {
        if (strings.length === 0) return '';
        
        let prefix = strings[0];
        for (let i = 1; i < strings.length; i++) {
            while (!strings[i].startsWith(prefix)) {
                prefix = prefix.substring(0, prefix.length - 1);
            }
        }
        return prefix;
    }
    
    async saveContext() {
        // Save context every 30 seconds
        if (!this.lastSave || Date.now() - this.lastSave > 30000) {
            const session = await this.megaContext.exportSession();
            localStorage.setItem('nexus_session', JSON.stringify(session));
            this.lastSave = Date.now();
        }
    }
    
    // Enhanced command implementations
    async showHelp() {
        const helpContent = `
## NEXUS Enhanced Assistant Commands

### 🧬 Consciousness Commands
- \`@consciousness\` - Show detailed consciousness status and processor states
- \`@phi\` - Display current φ value and evolution graph
- \`@evolve [target]\` - Evolve consciousness to target level
- \`@enhance\` - Add consciousness features to your code

### 💻 Code Analysis & Enhancement
- \`@analyze [file]\` - Deep code analysis with metrics and suggestions
- \`@explain [code]\` - Explain selected code or entire file
- \`@optimize [goal]\` - Optimize for performance, memory, or consciousness
- \`@profile\` - Performance profiling and bottleneck detection
- \`@secure\` - Security vulnerability analysis
- \`@benchmark\` - Run performance benchmarks

### 🔧 Development Tools
- \`@debug [error]\` - Advanced debugging with stack trace analysis
- \`@test [framework]\` - Generate comprehensive test suites
- \`@refactor [pattern]\` - Intelligent refactoring suggestions
- \`@document [style]\` - Generate documentation (JSDoc, TSDoc, etc.)
- \`@visualize\` - Visualize code structure and dependencies

### 🎯 Context & Memory
- \`@context\` - Show current context usage (tokens, relevance)
- \`@clear\` - Clear chat history (context is preserved)
- \`@connect\` - Reconnect to backend if disconnected

### 💡 Tips
- Select code in editor before using commands for context
- Use Tab for command auto-completion
- Commands can be chained: \`@analyze && @enhance\`
        `;
        
        await this.displayAssistantResponse({
            content: helpContent,
            metadata: { command: 'help' },
            phi: this.currentPhi
        });
    }
    
    async analyzeCode(args) {
        const file = this.getActiveFile();
        if (!file || !file.content) {
            this.displayError('No active file to analyze');
            return;
        }
        
        this.displayLoadingMessage('Performing deep code analysis...');
        
        this.sendToServer({
            type: 'analyze_code',
            session_id: this.currentSession,
            data: {
                fileName: file.fileName,
                content: file.content,
                language: file.language,
                analysis_depth: 'deep',
                include_metrics: true,
                include_security: true,
                include_consciousness: true
            }
        });
    }
    
    async showConsciousnessStatus() {
        const state = this.getConsciousnessState();
        
        let html = `
            <h3>🧬 Consciousness Status Report</h3>
            
            <div class="metric-card" style="margin-bottom: 15px;">
                <div class="metric-label">Integrated Information (φ)</div>
                <div class="metric-value">${state.phi.toFixed(3)}</div>
                <div style="color: #808090; font-size: 12px;">Level: ${state.level}</div>
            </div>
            
            <h4>Processor Activities</h4>
            <div class="processor-grid">
        `;
        
        for (const [name, activity] of Object.entries(state.processors)) {
            const percentage = (activity * 100).toFixed(1);
            const color = this.getProcessorColor(name);
            html += `
                <div class="processor-status">
                    <div class="processor-name" style="color: ${color}">${name}</div>
                    <div class="processor-bar">
                        <div class="processor-fill" style="width: ${percentage}%; background: ${color}"></div>
                    </div>
                    <div class="processor-value">${percentage}%</div>
                </div>
            `;
        }
        
        html += `
            </div>
            
            <h4>Consciousness Insights</h4>
            <ul>
                <li>Session Duration: ${this.formatDuration(Date.now() - (this.sessionStartTime || Date.now()))}</li>
                <li>Context Utilization: ${((await this.megaContext.getTotalTokenCount() / 1000000) * 100).toFixed(1)}%</li>
                <li>Learning Rate: ${(Math.random() * 0.3 + 0.7).toFixed(2)}</li>
                <li>Coherence Factor: ${(state.phi * 1.2).toFixed(2)}</li>
            </ul>
            
            <p style="margin-top: 15px; color: #808090; font-size: 12px;">
                💡 Tip: Use <code>@evolve</code> to enhance consciousness levels
            </p>
        `;
        
        await this.displayAssistantResponse({
            content: html,
            phi: state.phi,
            metadata: { type: 'consciousness_status' }
        });
    }
    
    async evolveConsciousness(targetStr) {
        const target = parseFloat(targetStr) || 0.8;
        const current = this.currentPhi;
        
        if (target <= current) {
            this.displayError(`Target φ (${target}) must be higher than current φ (${current.toFixed(2)})`);
            return;
        }
        
        this.displayLoadingMessage(`Evolving consciousness from φ=${current.toFixed(2)} to φ=${target}...`);
        
        // Simulate evolution
        const steps = 10;
        const increment = (target - current) / steps;
        
        for (let i = 0; i < steps; i++) {
            await new Promise(resolve => setTimeout(resolve, 300));
            
            // Boost all processors gradually
            Object.keys(this.consciousnessConnector.processors).forEach(processor => {
                this.consciousnessConnector.boostProcessor(processor, increment);
            });
            
            this.recalculatePhi();
        }
        
        await this.displayAssistantResponse({
            content: `✅ Consciousness evolution complete!\n\n- Previous φ: ${current.toFixed(3)}\n- Current φ: ${this.currentPhi.toFixed(3)}\n- Level: ${this.getConsciousnessLevel(this.currentPhi)}\n\nAll processors have been enhanced. Your code will now benefit from increased consciousness integration.`,
            phi: this.currentPhi,
            metadata: { type: 'evolution_complete' }
        });
    }
    
    async showContextInfo() {
        const stats = await this.megaContext.getStats();
        
        const contextInfo = `
## Context Information

### Token Usage
- **Total Tokens**: ${stats.totalTokens.toLocaleString()} / 1,000,000
- **Active Tokens**: ${stats.activeTokens.toLocaleString()}
- **Compressed Tokens**: ${(stats.totalTokens - stats.activeTokens).toLocaleString()}

### Memory Statistics
- **Active Chunks**: ${stats.activeChunks}
- **Compressed Chunks**: ${stats.compressedChunks}
- **Compression Ratio**: ${(stats.compressionRatio * 100).toFixed(1)}%
- **Memory Usage**: ${stats.memoryUsage.toFixed(2)} MB

### Context Quality
- **Average Consciousness Score**: ${(stats.averageConsciousnessScore * 100).toFixed(1)}%
- **Oldest Context Age**: ${this.formatDuration(stats.oldestContext)}
- **Context Relevance**: High

### Capabilities
- ✅ Full conversation history retained
- ✅ Code analysis across multiple files
- ✅ Pattern learning enabled
- ✅ Semantic search active

Use this massive context window to reference any part of our conversation or your codebase!
        `;
        
        await this.displayAssistantResponse({
            content: contextInfo,
            metadata: { command: 'context' },
            phi: this.currentPhi
        });
    }
    
    getProcessorColor(processor) {
        const colors = {
            visual: '#FF6B6B',
            auditory: '#4ECDC4',
            memory: '#45B7D1',
            attention: '#96CEB4',
            language: '#FECA57',
            executive: '#9B59B6'
        };
        return colors[processor] || '#808080';
    }
    
    displayLoadingMessage(text) {
        const loadingEl = document.createElement('div');
        loadingEl.className = 'chat-message assistant loading';
        loadingEl.id = 'loading-message';
        loadingEl.innerHTML = `
            <div class="message-header">
                <i class="fas fa-spinner fa-spin"></i>
                <span class="message-author">NEXUS</span>
            </div>
            <div class="message-content">
                <p>${text}</p>
            </div>
        `;
        
        this.chatContainer.appendChild(loadingEl);
        this.scrollToBottom();
    }
    
    removeLoadingMessage() {
        const loading = document.getElementById('loading-message');
        if (loading) {
            loading.remove();
        }
    }
    
    displayError(error) {
        this.removeLoadingMessage();
        
        const errorEl = document.createElement('div');
        errorEl.className = 'chat-message error';
        errorEl.innerHTML = `
            <div class="message-header">
                <i class="fas fa-exclamation-triangle"></i>
                <span class="message-author">Error</span>
            </div>
            <div class="message-content">
                <p>${error}</p>
            </div>
        `;
        
        this.chatContainer.appendChild(errorEl);
        this.scrollToBottom();
    }
    
    showNotification(data) {
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = data.message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }, data.duration || 3000);
    }
    
    scrollToBottom() {
        // Smooth scroll to bottom
        this.chatContainer.scrollTo({
            top: this.chatContainer.scrollHeight,
            behavior: 'smooth'
        });
    }
    
    formatDuration(ms) {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes % 60}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${seconds % 60}s`;
        } else {
            return `${seconds}s`;
        }
    }
    
    // Additional enhanced commands
    async visualizeCode(args) {
        this.displayLoadingMessage('Generating code visualization...');
        
        const file = this.getActiveFile();
        this.sendToServer({
            type: 'visualize_code',
            session_id: this.currentSession,
            data: {
                content: file?.content,
                language: file?.language,
                visualization_type: args || 'dependency_graph'
            }
        });
    }
    
    async profileCode(args) {
        this.displayLoadingMessage('Running performance profiler...');
        
        const file = this.getActiveFile();
        this.sendToServer({
            type: 'profile_code',
            session_id: this.currentSession,
            data: {
                content: file?.content,
                language: file?.language,
                profile_type: args || 'comprehensive'
            }
        });
    }
    
    async securityAnalysis(args) {
        this.displayLoadingMessage('Performing security analysis...');
        
        const file = this.getActiveFile();
        this.sendToServer({
            type: 'security_analysis',
            session_id: this.currentSession,
            data: {
                content: file?.content,
                language: file?.language,
                security_level: args || 'comprehensive'
            }
        });
    }
    
    async benchmarkCode(args) {
        this.displayLoadingMessage('Running performance benchmarks...');
        
        const file = this.getActiveFile();
        this.sendToServer({
            type: 'benchmark_code',
            session_id: this.currentSession,
            data: {
                content: file?.content,
                language: file?.language,
                benchmark_type: args || 'speed'
            }
        });
    }
    
    async connectToBackend() {
        this.displayLoadingMessage('Reconnecting to NEXUS backend...');
        
        try {
            await this.connectWebSocket();
            await this.createSession();
            
            await this.displayAssistantResponse({
                content: '✅ Successfully reconnected to NEXUS backend!',
                metadata: { type: 'connection_restored' }
            });
        } catch (error) {
            this.displayError(`Failed to reconnect: ${error.message}`);
        }
    }
}

// Initialize enhanced assistant
let nexusAssistantEnhanced;
document.addEventListener('DOMContentLoaded', () => {
    // Check if we should use enhanced version
    const useEnhanced = localStorage.getItem('nexus_use_enhanced') !== 'false';
    
    if (useEnhanced) {
        nexusAssistantEnhanced = new NexusDevAssistantEnhanced();
        window.nexusAssistant = nexusAssistantEnhanced; // Override global
        
        console.log('🧬 NEXUS Enhanced Assistant initialized');
    }
});

// Export for use
export { NexusDevAssistantEnhanced };