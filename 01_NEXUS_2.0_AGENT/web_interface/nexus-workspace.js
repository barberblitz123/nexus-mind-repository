// NEXUS 2.0 Development Workspace - Functional JavaScript

class NexusWorkspace {
    constructor() {
        this.agents = new Map();
        this.files = new Map();
        this.activeFile = null;
        this.activeAgent = null;
        
        this.initializeElements();
        this.setupEventListeners();
        this.setupDragDrop();
        this.addWelcomeMessage();
    }

    initializeElements() {
        // Stage Manager
        this.agentWindows = document.getElementById('agentWindows');
        this.newAgentBtn = document.getElementById('newAgentBtn');
        
        // Code Area
        this.dropZone = document.getElementById('dropZone');
        this.fileInput = document.getElementById('fileInput');
        this.codeEditor = document.getElementById('codeEditor');
        this.codeContent = document.getElementById('codeContent');
        this.fileTabs = document.getElementById('fileTabs');
        
        // Chat
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendBtn = document.getElementById('sendBtn');
        
        // Media
        this.cameraBtn = document.getElementById('cameraBtn');
        this.micBtn = document.getElementById('micBtn');
        this.videoContainer = document.getElementById('videoContainer');
        this.localVideo = document.getElementById('localVideo');
    }

    setupEventListeners() {
        // New Agent button
        this.newAgentBtn.addEventListener('click', () => this.createAgent());
        
        // Chat
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        
        // File input
        this.fileInput.addEventListener('change', (e) => this.handleFiles(e.target.files));
        this.dropZone.addEventListener('click', () => {
            if (!this.activeFile) this.fileInput.click();
        });
        
        // Media controls
        this.cameraBtn.addEventListener('click', () => this.toggleCamera());
        this.micBtn.addEventListener('click', () => this.toggleMicrophone());
    }

    setupDragDrop() {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => {
                this.dropZone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => {
                this.dropZone.classList.remove('dragover');
            });
        });

        this.dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            this.handleFiles(files);
        });
    }

    handleFiles(files) {
        Array.from(files).forEach(file => {
            if (this.isValidFile(file)) {
                this.loadFile(file);
            }
        });
    }

    isValidFile(file) {
        const validExtensions = ['.js', '.py', '.html', '.css', '.json', '.md', '.txt', '.jsx', '.ts', '.tsx'];
        return validExtensions.some(ext => file.name.endsWith(ext));
    }

    async loadFile(file) {
        const content = await file.text();
        const fileId = Date.now().toString();
        
        this.files.set(fileId, {
            id: fileId,
            name: file.name,
            content: content,
            language: this.detectLanguage(file.name)
        });
        
        this.addFileTab(fileId, file.name);
        this.showFile(fileId);
        
        // Automatically analyze the file
        this.analyzeFile(fileId);
    }

    detectLanguage(filename) {
        const ext = filename.split('.').pop();
        const langMap = {
            'js': 'javascript',
            'py': 'python',
            'html': 'html',
            'css': 'css',
            'json': 'json',
            'md': 'markdown',
            'jsx': 'javascript',
            'ts': 'typescript',
            'tsx': 'typescript'
        };
        return langMap[ext] || 'text';
    }

    addFileTab(fileId, filename) {
        const tab = document.createElement('div');
        tab.className = 'file-tab';
        tab.textContent = filename;
        tab.dataset.fileId = fileId;
        tab.addEventListener('click', () => this.showFile(fileId));
        
        this.fileTabs.appendChild(tab);
    }

    showFile(fileId) {
        const file = this.files.get(fileId);
        if (!file) return;
        
        // Update active file
        this.activeFile = fileId;
        
        // Update tabs
        document.querySelectorAll('.file-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.fileId === fileId);
        });
        
        // Show code
        this.codeContent.textContent = file.content;
        this.dropZone.querySelector('.drop-message').classList.add('hidden');
        this.codeEditor.classList.remove('hidden');
        
        // Syntax highlighting (you could add Prism.js or similar here)
        this.codeContent.className = `language-${file.language}`;
    }

    analyzeFile(fileId) {
        const file = this.files.get(fileId);
        if (!file) return;
        
        // Create an analyzer agent
        const agent = this.createAgent('analyzer', `Analyzing ${file.name}`);
        
        // Simulate analysis
        setTimeout(() => {
            this.addChatMessage(agent.name, `Analysis of ${file.name}:`);
            
            // Basic analysis
            const lines = file.content.split('\n').length;
            const size = (file.content.length / 1024).toFixed(2);
            
            this.addChatMessage(agent.name, `- Lines: ${lines}`);
            this.addChatMessage(agent.name, `- Size: ${size} KB`);
            this.addChatMessage(agent.name, `- Language: ${file.language}`);
            
            // Language-specific analysis
            if (file.language === 'javascript' || file.language === 'typescript') {
                const functions = (file.content.match(/function\s+\w+|const\s+\w+\s*=\s*\(/g) || []).length;
                this.addChatMessage(agent.name, `- Functions found: ${functions}`);
            } else if (file.language === 'python') {
                const functions = (file.content.match(/def\s+\w+/g) || []).length;
                const classes = (file.content.match(/class\s+\w+/g) || []).length;
                this.addChatMessage(agent.name, `- Functions: ${functions}, Classes: ${classes}`);
            }
            
            this.updateAgentStatus(agent.id, 'completed');
        }, 1500);
    }

    createAgent(type = 'general', task = 'Ready') {
        const agentTypes = {
            'analyzer': { name: 'Code Analyzer', icon: '🔍' },
            'developer': { name: 'Developer', icon: '💻' },
            'debugger': { name: 'Debugger', icon: '🐛' },
            'optimizer': { name: 'Optimizer', icon: '⚡' },
            'documenter': { name: 'Documenter', icon: '📝' },
            'general': { name: 'Assistant', icon: '🤖' }
        };
        
        const agentInfo = agentTypes[type] || agentTypes.general;
        const agentId = Date.now().toString();
        
        const agent = {
            id: agentId,
            type: type,
            name: agentInfo.name,
            icon: agentInfo.icon,
            status: 'working',
            task: task
        };
        
        this.agents.set(agentId, agent);
        this.renderAgent(agent);
        
        return agent;
    }

    renderAgent(agent) {
        const agentWindow = document.createElement('div');
        agentWindow.className = 'agent-window';
        agentWindow.dataset.agentId = agent.id;
        agentWindow.innerHTML = `
            <div class="agent-name">${agent.icon} ${agent.name}</div>
            <div class="agent-status ${agent.status}">${agent.task}</div>
        `;
        
        agentWindow.addEventListener('click', () => this.selectAgent(agent.id));
        this.agentWindows.appendChild(agentWindow);
        
        // Auto-select new agent
        this.selectAgent(agent.id);
    }

    selectAgent(agentId) {
        this.activeAgent = agentId;
        
        document.querySelectorAll('.agent-window').forEach(window => {
            window.classList.toggle('active', window.dataset.agentId === agentId);
        });
    }

    updateAgentStatus(agentId, status, task = null) {
        const agent = this.agents.get(agentId);
        if (!agent) return;
        
        agent.status = status;
        if (task) agent.task = task;
        
        const window = document.querySelector(`[data-agent-id="${agentId}"]`);
        if (window) {
            const statusEl = window.querySelector('.agent-status');
            statusEl.className = `agent-status ${status}`;
            statusEl.textContent = agent.task;
        }
    }

    sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message) return;
        
        this.addChatMessage('You', message, 'user');
        this.chatInput.value = '';
        
        // Process the message
        this.processUserMessage(message);
    }

    processUserMessage(message) {
        const lowerMessage = message.toLowerCase();
        
        // Determine what kind of agent to create based on the message
        if (lowerMessage.includes('analyze') || lowerMessage.includes('review')) {
            const agent = this.createAgent('analyzer', 'Analyzing code...');
            setTimeout(() => {
                this.addChatMessage(agent.name, 'I\'ll analyze your code for potential issues.');
                this.performCodeAnalysis(agent);
            }, 500);
        }
        else if (lowerMessage.includes('fix') || lowerMessage.includes('debug')) {
            const agent = this.createAgent('debugger', 'Debugging...');
            setTimeout(() => {
                this.addChatMessage(agent.name, 'Looking for bugs and issues...');
                this.performDebugging(agent);
            }, 500);
        }
        else if (lowerMessage.includes('optimize') || lowerMessage.includes('improve')) {
            const agent = this.createAgent('optimizer', 'Optimizing...');
            setTimeout(() => {
                this.addChatMessage(agent.name, 'Analyzing code for optimization opportunities...');
                this.performOptimization(agent);
            }, 500);
        }
        else if (lowerMessage.includes('document') || lowerMessage.includes('comment')) {
            const agent = this.createAgent('documenter', 'Documenting...');
            setTimeout(() => {
                this.addChatMessage(agent.name, 'I\'ll add documentation to your code.');
                this.performDocumentation(agent);
            }, 500);
        }
        else {
            const agent = this.createAgent('general', 'Processing...');
            setTimeout(() => {
                this.addChatMessage(agent.name, 'How can I help you with your code?');
                this.updateAgentStatus(agent.id, 'completed', 'Ready');
            }, 500);
        }
    }

    performCodeAnalysis(agent) {
        if (!this.activeFile) {
            this.addChatMessage(agent.name, 'Please drop a code file first.');
            this.updateAgentStatus(agent.id, 'completed', 'No file');
            return;
        }
        
        const file = this.files.get(this.activeFile);
        setTimeout(() => {
            // Simulate analysis results
            this.addChatMessage(agent.name, 'Analysis complete. Found:');
            this.addChatMessage(agent.name, '• No syntax errors');
            this.addChatMessage(agent.name, '• 2 potential improvements');
            this.addChatMessage(agent.name, '• Code follows most best practices');
            this.updateAgentStatus(agent.id, 'completed', 'Analysis done');
        }, 2000);
    }

    performDebugging(agent) {
        if (!this.activeFile) {
            this.addChatMessage(agent.name, 'Please drop a code file first.');
            this.updateAgentStatus(agent.id, 'completed', 'No file');
            return;
        }
        
        setTimeout(() => {
            this.addChatMessage(agent.name, 'Debug scan complete:');
            this.addChatMessage(agent.name, '• No critical errors found');
            this.addChatMessage(agent.name, '• Consider adding error handling in main function');
            this.updateAgentStatus(agent.id, 'completed', 'Debug complete');
        }, 2000);
    }

    performOptimization(agent) {
        if (!this.activeFile) {
            this.addChatMessage(agent.name, 'Please drop a code file first.');
            this.updateAgentStatus(agent.id, 'completed', 'No file');
            return;
        }
        
        setTimeout(() => {
            this.addChatMessage(agent.name, 'Optimization suggestions:');
            this.addChatMessage(agent.name, '• Consider using const instead of let where applicable');
            this.addChatMessage(agent.name, '• Could combine similar functions');
            this.updateAgentStatus(agent.id, 'completed', 'Optimized');
        }, 2000);
    }

    performDocumentation(agent) {
        if (!this.activeFile) {
            this.addChatMessage(agent.name, 'Please drop a code file first.');
            this.updateAgentStatus(agent.id, 'completed', 'No file');
            return;
        }
        
        setTimeout(() => {
            this.addChatMessage(agent.name, 'Documentation suggestions:');
            this.addChatMessage(agent.name, '• Add JSDoc comments to functions');
            this.addChatMessage(agent.name, '• Include parameter descriptions');
            this.addChatMessage(agent.name, '• Add a file header comment');
            this.updateAgentStatus(agent.id, 'completed', 'Documented');
        }, 2000);
    }

    addChatMessage(sender, content, type = 'agent') {
        const messageEl = document.createElement('div');
        messageEl.className = `chat-message ${type}`;
        messageEl.innerHTML = `
            <div class="sender">${sender}</div>
            <div class="content">${content}</div>
        `;
        
        this.chatMessages.appendChild(messageEl);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    async toggleCamera() {
        if (this.cameraBtn.classList.contains('active')) {
            // Stop camera
            if (this.localStream) {
                this.localStream.getTracks().forEach(track => track.stop());
                this.localStream = null;
            }
            this.cameraBtn.classList.remove('active');
            this.videoContainer.classList.add('hidden');
        } else {
            // Start camera
            try {
                this.localStream = await navigator.mediaDevices.getUserMedia({ video: true });
                this.localVideo.srcObject = this.localStream;
                this.cameraBtn.classList.add('active');
                this.videoContainer.classList.remove('hidden');
            } catch (err) {
                console.error('Camera access denied:', err);
                this.addChatMessage('System', 'Camera access denied. Please check permissions.');
            }
        }
    }

    toggleMicrophone() {
        // Toggle microphone functionality
        this.micBtn.classList.toggle('active');
        
        if (this.micBtn.classList.contains('active')) {
            this.addChatMessage('System', 'Voice input activated. (Demo mode)');
        } else {
            this.addChatMessage('System', 'Voice input deactivated.');
        }
    }

    addWelcomeMessage() {
        this.addChatMessage('System', 'Welcome to NEXUS 2.0 Development Workspace!');
        this.addChatMessage('System', 'Drop your code files above to get started.');
        this.addChatMessage('System', 'Try commands like: "analyze my code", "fix bugs", "optimize", or "add documentation"');
    }
}

// Initialize workspace when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.nexusWorkspace = new NexusWorkspace();
});