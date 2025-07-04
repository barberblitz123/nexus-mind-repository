// NEXUS 2.0 Web Terminal Application

class NexusWebApp {
    constructor() {
        this.agents = new Map();
        this.terminal = null;
        this.activePanel = 'chat';
        this.activeAgentId = null;
        this.ws = null;
        
        this.init();
    }
    
    init() {
        // Initialize terminal
        this.initTerminal();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Connect to backend (if available)
        this.connectWebSocket();
        
        // Mobile detection
        this.detectMobile();
        
        // Add welcome message
        this.addChatMessage('system', 'Welcome to NEXUS 2.0 Web Terminal!');
        this.addChatMessage('system', 'Type "help" for available commands.');
    }
    
    initTerminal() {
        const Terminal = window.Terminal;
        const FitAddon = window.FitAddon.FitAddon;
        
        this.terminal = new Terminal({
            theme: {
                background: '#0a0a0a',
                foreground: '#00ff00',
                cursor: '#00ff00',
                selection: 'rgba(0, 255, 0, 0.3)'
            },
            cursorBlink: true,
            fontSize: 14,
            fontFamily: 'Monaco, Menlo, monospace'
        });
        
        const fitAddon = new FitAddon();
        this.terminal.loadAddon(fitAddon);
        
        const container = document.getElementById('terminal-container');
        this.terminal.open(container);
        fitAddon.fit();
        
        // Handle terminal input
        this.terminal.onData(data => {
            this.handleTerminalInput(data);
        });
        
        // Resize terminal on window resize
        window.addEventListener('resize', () => fitAddon.fit());
        
        // Initial prompt
        this.terminal.writeln('NEXUS 2.0 Terminal');
        this.terminal.writeln('================');
        this.terminal.write('\r\n$ ');
    }
    
    setupEventListeners() {
        // Chat input
        const chatInput = document.getElementById('chat-input');
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        
        // Window resize for responsive layout
        window.addEventListener('resize', () => this.handleResize());
    }
    
    connectWebSocket() {
        // Try to connect to backend WebSocket
        try {
            this.ws = new WebSocket('ws://localhost:8080/ws');
            
            this.ws.onopen = () => {
                console.log('Connected to NEXUS backend');
                document.getElementById('connection-status').classList.add('connected');
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleBackendMessage(data);
            };
            
            this.ws.onerror = () => {
                console.log('Running in standalone mode');
                document.getElementById('connection-status').classList.remove('connected');
            };
        } catch (e) {
            console.log('WebSocket not available, running standalone');
        }
    }
    
    createAgent(type = 'general', name = null) {
        const agentId = `agent-${Date.now()}`;
        const agentName = name || `${type.charAt(0).toUpperCase() + type.slice(1)} Agent`;
        
        const agent = {
            id: agentId,
            name: agentName,
            type: type,
            state: 'idle',
            task: null,
            created: new Date()
        };
        
        this.agents.set(agentId, agent);
        this.renderAgentWindow(agent);
        this.updateAgentCount();
        
        this.addChatMessage('system', `Created new agent: ${agentName}`);
        
        return agent;
    }
    
    renderAgentWindow(agent) {
        const container = document.getElementById('agent-windows');
        const agentDiv = document.createElement('div');
        agentDiv.className = 'agent-window';
        agentDiv.id = agent.id;
        agentDiv.onclick = () => this.selectAgent(agent.id);
        
        agentDiv.innerHTML = `
            <div class="agent-name">${agent.name}</div>
            <div class="agent-state ${agent.state}">${agent.state}</div>
            <div class="agent-task">${agent.task || 'No active task'}</div>
        `;
        
        container.appendChild(agentDiv);
    }
    
    selectAgent(agentId) {
        // Remove previous selection
        document.querySelectorAll('.agent-window').forEach(el => {
            el.classList.remove('active');
        });
        
        // Add selection to current
        document.getElementById(agentId).classList.add('active');
        this.activeAgentId = agentId;
        
        const agent = this.agents.get(agentId);
        this.addChatMessage('system', `Selected: ${agent.name}`);
    }
    
    updateAgentState(agentId, state, task = null) {
        const agent = this.agents.get(agentId);
        if (!agent) return;
        
        agent.state = state;
        if (task) agent.task = task;
        
        const agentDiv = document.getElementById(agentId);
        if (agentDiv) {
            agentDiv.querySelector('.agent-state').textContent = state;
            agentDiv.querySelector('.agent-state').className = `agent-state ${state}`;
            agentDiv.querySelector('.agent-task').textContent = task || 'No active task';
        }
    }
    
    handleCommand(command) {
        const parts = command.split(' ');
        const cmd = parts[0].toLowerCase();
        
        switch (cmd) {
            case 'help':
                this.showHelp();
                break;
                
            case 'create':
                if (parts[1] === 'agent') {
                    const type = parts[2] || 'general';
                    this.createAgent(type);
                }
                break;
                
            case 'list':
                this.listAgents();
                break;
                
            case 'task':
                if (this.activeAgentId && parts.length > 1) {
                    const task = parts.slice(1).join(' ');
                    this.assignTask(this.activeAgentId, task);
                }
                break;
                
            case 'clear':
                this.clearChat();
                break;
                
            default:
                // If not a command, treat as a task assignment
                if (command.includes('build') || command.includes('create') || 
                    command.includes('analyze') || command.includes('fix')) {
                    this.autoAssignTask(command);
                } else {
                    this.addChatMessage('system', `Unknown command: ${cmd}`);
                }
        }
    }
    
    autoAssignTask(task) {
        // Determine agent type based on task
        let agentType = 'general';
        if (task.includes('code') || task.includes('build')) {
            agentType = 'developer';
        } else if (task.includes('research') || task.includes('analyze')) {
            agentType = 'researcher';
        } else if (task.includes('test') || task.includes('verify')) {
            agentType = 'tester';
        }
        
        // Create agent for task
        const agent = this.createAgent(agentType);
        this.assignTask(agent.id, task);
    }
    
    assignTask(agentId, task) {
        const agent = this.agents.get(agentId);
        if (!agent) return;
        
        this.updateAgentState(agentId, 'working', task);
        this.addChatMessage(agent.name, `Starting task: ${task}`);
        
        // Simulate task execution
        this.simulateTaskExecution(agentId, task);
    }
    
    simulateTaskExecution(agentId, task) {
        const agent = this.agents.get(agentId);
        
        // Show in terminal
        this.terminal.writeln(`\r\n[${agent.name}] Executing: ${task}`);
        
        // Simulate steps
        const steps = [
            'Analyzing requirements...',
            'Planning approach...',
            'Implementing solution...',
            'Testing implementation...',
            'Task completed!'
        ];
        
        let stepIndex = 0;
        const interval = setInterval(() => {
            if (stepIndex < steps.length) {
                this.terminal.writeln(`[${agent.name}] ${steps[stepIndex]}`);
                this.addChatMessage(agent.name, steps[stepIndex]);
                
                if (stepIndex === steps.length - 1) {
                    this.updateAgentState(agentId, 'idle', 'Task completed');
                }
                
                stepIndex++;
            } else {
                clearInterval(interval);
                this.terminal.write('\r\n$ ');
            }
        }, 2000);
    }
    
    showHelp() {
        const helpText = `
NEXUS 2.0 Commands:
- help              Show this help
- create agent [type]  Create new agent
- list              List all agents
- task [description]   Assign task to selected agent
- clear             Clear chat
- [any task]        Auto-create agent and assign task

Agent Types: developer, researcher, tester, designer, general
        `;
        
        this.addChatMessage('system', helpText);
    }
    
    listAgents() {
        if (this.agents.size === 0) {
            this.addChatMessage('system', 'No agents created yet.');
            return;
        }
        
        let list = 'Active Agents:\n';
        this.agents.forEach(agent => {
            list += `- ${agent.name} (${agent.state})\n`;
        });
        
        this.addChatMessage('system', list);
    }
    
    sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        this.addChatMessage('user', message);
        this.handleCommand(message);
        
        input.value = '';
    }
    
    addChatMessage(sender, content) {
        const messagesDiv = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        
        let senderClass = 'system';
        if (sender === 'user') senderClass = 'user';
        else if (sender !== 'system') senderClass = 'agent';
        
        messageDiv.className = `message ${senderClass}`;
        messageDiv.innerHTML = `
            <span class="sender">${sender}:</span>
            <span class="content">${content}</span>
        `;
        
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
    
    clearChat() {
        const messagesDiv = document.getElementById('chat-messages');
        messagesDiv.innerHTML = '';
        this.addChatMessage('system', 'Chat cleared.');
    }
    
    updateAgentCount() {
        document.getElementById('agent-count').textContent = `Agents: ${this.agents.size}`;
    }
    
    detectMobile() {
        const isMobile = window.innerWidth <= 768;
        if (isMobile) {
            document.body.classList.add('mobile');
            this.showPanel('chat');
        }
    }
    
    handleResize() {
        this.detectMobile();
    }
    
    handleTerminalInput(data) {
        // Echo input
        this.terminal.write(data);
        
        // Handle special keys
        if (data === '\r') {
            this.terminal.write('\n$ ');
        }
    }
    
    handleBackendMessage(data) {
        // Handle messages from backend
        if (data.type === 'agent_update') {
            this.updateAgentState(data.agentId, data.state, data.task);
        } else if (data.type === 'chat_message') {
            this.addChatMessage(data.sender, data.content);
        }
    }
}

// Global functions for HTML onclick handlers
function createAgent() {
    window.app.createAgent();
}

function sendMessage() {
    window.app.sendMessage();
}

function arrangeGrid() {
    window.app.addChatMessage('system', 'Grid arrangement applied');
}

function arrangeCascade() {
    window.app.addChatMessage('system', 'Cascade arrangement applied');
}

function switchPreview() {
    const selector = document.getElementById('preview-selector');
    const value = selector.value;
    
    // Hide all previews
    document.getElementById('terminal-container').style.display = 'none';
    document.getElementById('code-preview').style.display = 'none';
    document.getElementById('output-preview').style.display = 'none';
    
    // Show selected
    if (value === 'terminal') {
        document.getElementById('terminal-container').style.display = 'block';
    } else if (value === 'code') {
        document.getElementById('code-preview').style.display = 'block';
    } else if (value === 'output') {
        document.getElementById('output-preview').style.display = 'block';
    }
}

function showPanel(panel) {
    // Remove all panel classes
    document.body.classList.remove('show-stage', 'show-chat', 'show-preview');
    
    // Add specific panel class
    if (panel === 'stage') {
        document.body.classList.add('show-stage');
    } else if (panel === 'chat') {
        document.body.classList.add('show-chat');
    } else if (panel === 'preview') {
        document.body.classList.add('show-preview');
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new NexusWebApp();
});