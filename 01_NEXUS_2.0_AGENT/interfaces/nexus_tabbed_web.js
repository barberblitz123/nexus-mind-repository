// NEXUS 2.0 Tabbed Web Interface JavaScript

// Global state
let agents = new Map();
let activeAgents = [];
let sideAgents = [];
let focusedAgentId = null;
let chatHistory = [];
let terminalHistory = [];
let currentPreviewType = 'code';
let ws = null;

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    initializeWebSocket();
    setupKeyboardShortcuts();
    updateClock();
    setInterval(updateClock, 1000);
    setInterval(updateAgentDurations, 1000);
    
    // Add welcome message
    addChatMessage('system', 'Welcome to NEXUS 2.0 Web Interface! Type commands to create agents.');
    addTerminalLine('NEXUS 2.0 Terminal Ready');
    
    // Create demo agents
    setTimeout(() => createDemoAgents(), 1000);
});

// WebSocket connection to backend
function initializeWebSocket() {
    const wsUrl = 'ws://localhost:8765';
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('Connected to NEXUS backend');
        document.getElementById('system-status').textContent = 'Connected';
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleBackendMessage(data);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        document.getElementById('system-status').textContent = 'Error';
    };
    
    ws.onclose = () => {
        document.getElementById('system-status').textContent = 'Disconnected';
        // Reconnect after 3 seconds
        setTimeout(initializeWebSocket, 3000);
    };
}

// Handle messages from backend
function handleBackendMessage(data) {
    switch (data.type) {
        case 'agent_created':
            addAgent(data.agent);
            break;
        case 'agent_updated':
            updateAgent(data.agent);
            break;
        case 'chat_message':
            addChatMessage(data.sender, data.message);
            break;
        case 'preview_update':
            updatePreview(data.content, data.previewType);
            break;
        case 'terminal_output':
            addTerminalLine(data.output);
            break;
        case 'terminal_clear':
            document.getElementById('terminal-output').innerHTML = '';
            break;
        case 'agent_focused':
            focusedAgentId = data.agent_id;
            updateStageDisplay();
            break;
        case 'system_metrics':
            updateSystemMetricsFromServer(data.metrics);
            break;
    }
}

// Tab switching
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update tab panels
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

// Keyboard shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey) {
            switch (e.key) {
                case '1':
                    e.preventDefault();
                    switchToTab('stage');
                    break;
                case '2':
                    e.preventDefault();
                    switchToTab('chat');
                    break;
                case '3':
                    e.preventDefault();
                    switchToTab('preview');
                    break;
                case '4':
                    e.preventDefault();
                    switchToTab('terminal');
                    break;
                case '5':
                    e.preventDefault();
                    switchToTab('status');
                    break;
                case 'n':
                    e.preventDefault();
                    createNewAgent();
                    break;
            }
        }
    });
}

function switchToTab(tabName) {
    const buttons = document.querySelectorAll('.tab-button');
    const panels = document.querySelectorAll('.tab-panel');
    
    buttons.forEach(btn => btn.classList.remove('active'));
    panels.forEach(panel => panel.classList.remove('active'));
    
    buttons.forEach(btn => {
        if (btn.textContent.toLowerCase().includes(tabName)) {
            btn.classList.add('active');
        }
    });
    
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

// Agent management
function addAgent(agentData) {
    const agent = {
        id: agentData.id || generateId(),
        name: agentData.name,
        type: agentData.type,
        state: agentData.state || 'idle',
        task: agentData.task || null,
        createdAt: agentData.createdAt ? new Date(agentData.createdAt) : new Date(),
        lastActive: new Date()
    };
    
    agents.set(agent.id, agent);
    
    // Add to active stage if room
    if (activeAgents.length < 4) {
        activeAgents.push(agent.id);
        if (!focusedAgentId) {
            focusedAgentId = agent.id;
        }
    } else {
        sideAgents.push(agent.id);
    }
    
    updateStageDisplay();
    updateStatusDisplay();
    updateAgentCount();
    
    return agent;
}

function createAgent(name, type, task) {
    return addAgent({
        name: name,
        type: type,
        task: task
    });
}

function createNewAgent() {
    switchToTab('chat');
    document.getElementById('chat-input').focus();
    document.getElementById('chat-input').placeholder = "Describe the task for the new agent...";
}

function createDemoAgents() {
    createAgent('Code Analyzer', 'analyzer', 'Analyzing code structure');
    createAgent('API Builder', 'developer', 'Building REST API');
    createAgent('Test Runner', 'tester', 'Running unit tests');
    
    // Set some to working state
    const agentIds = Array.from(agents.keys());
    if (agentIds[0]) updateAgentState(agentIds[0], 'working');
    if (agentIds[1]) updateAgentState(agentIds[1], 'thinking');
}

function updateAgentState(agentId, state) {
    const agent = agents.get(agentId);
    if (agent) {
        agent.state = state;
        agent.lastActive = new Date();
        updateStageDisplay();
        updateStatusDisplay();
    }
}

function updateAgent(agentData) {
    const agent = agents.get(agentData.id);
    if (agent) {
        if (agentData.state) agent.state = agentData.state;
        if (agentData.task) agent.task = agentData.task;
        agent.lastActive = new Date();
        updateStageDisplay();
        updateStatusDisplay();
    }
}

// Stage Manager display
function updateStageDisplay() {
    const activeContainer = document.getElementById('active-agents');
    const sideContainer = document.getElementById('side-agents');
    
    activeContainer.innerHTML = '';
    sideContainer.innerHTML = '';
    
    // Active agents
    activeAgents.forEach(agentId => {
        const agent = agents.get(agentId);
        if (agent) {
            activeContainer.appendChild(createAgentWindow(agent, agentId === focusedAgentId));
        }
    });
    
    // Side agents
    sideAgents.forEach(agentId => {
        const agent = agents.get(agentId);
        if (agent) {
            sideContainer.appendChild(createAgentWindow(agent, false));
        }
    });
}

function createAgentWindow(agent, isFocused) {
    const div = document.createElement('div');
    div.className = `agent-window ${isFocused ? 'focused' : ''}`;
    div.innerHTML = `
        <h3>${agent.name}</h3>
        <div class="agent-info">
            <p>Type: ${agent.type}</p>
            <p>Task: ${agent.task || 'Idle'}</p>
            <span class="agent-state state-${agent.state}">${agent.state.toUpperCase()}</span>
        </div>
    `;
    
    div.onclick = () => focusAgent(agent.id);
    
    return div;
}

function focusAgent(agentId) {
    focusedAgentId = agentId;
    updateStageDisplay();
}

// Chat functionality
function handleChatInput(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (message) {
        addChatMessage('user', message);
        processCommand(message);
        input.value = '';
    }
}

function addChatMessage(sender, message) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    
    const time = new Date().toLocaleTimeString();
    messageDiv.innerHTML = `
        <strong>${sender}:</strong> ${message}
        <span style="float: right; opacity: 0.6; font-size: 12px;">${time}</span>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    chatHistory.push({ sender, message, time });
}

function processCommand(command) {
    // Send command to backend via WebSocket
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'chat_message',
            message: command
        }));
    } else {
        // Fallback for when not connected
        addChatMessage('system', 'Not connected to backend. Running in demo mode.');
        processDemoCommand(command);
    }
}

function processDemoCommand(command) {
    const cmdLower = command.toLowerCase();
    
    // Detect task patterns for demo mode
    if (cmdLower.includes('create') || cmdLower.includes('build') || 
        cmdLower.includes('analyze') || cmdLower.includes('test')) {
        
        let agentType = 'general';
        let taskName = command;
        
        if (cmdLower.includes('analyze')) {
            agentType = 'analyzer';
        } else if (cmdLower.includes('build') || cmdLower.includes('create')) {
            agentType = 'developer';
        } else if (cmdLower.includes('test')) {
            agentType = 'tester';
        } else if (cmdLower.includes('document')) {
            agentType = 'documenter';
        }
        
        const agentName = `${agentType.charAt(0).toUpperCase() + agentType.slice(1)} Agent`;
        const agent = createAgent(agentName, agentType, command);
        
        updateAgentState(agent.id, 'working');
        addChatMessage(agentName, `Starting work on: ${command}`);
        
        // Simulate agent work
        setTimeout(() => {
            updateAgentState(agent.id, 'thinking');
            addChatMessage(agentName, 'Analyzing requirements...');
        }, 2000);
        
        setTimeout(() => {
            updateAgentState(agent.id, 'working');
            addChatMessage(agentName, 'Implementing solution...');
            updatePreview(`// Working on: ${command}\nfunction implement() {\n  // Implementation in progress...\n}`, 'code');
        }, 4000);
        
        setTimeout(() => {
            updateAgentState(agent.id, 'idle');
            addChatMessage(agentName, 'Task completed!');
        }, 8000);
    }
}

// Preview functionality
function setPreviewType(type) {
    currentPreviewType = type;
    updatePreviewDisplay();
}

function updatePreview(content, type) {
    if (type === currentPreviewType) {
        const previewContent = document.getElementById('preview-content');
        previewContent.innerHTML = `<pre class="code-preview">${escapeHtml(content)}</pre>`;
    }
}

function updatePreviewDisplay() {
    const previewContent = document.getElementById('preview-content');
    
    switch (currentPreviewType) {
        case 'code':
            previewContent.innerHTML = '<pre class="code-preview">// Code will appear here when agents are working...</pre>';
            break;
        case 'output':
            previewContent.innerHTML = '<pre>Output will appear here...</pre>';
            break;
        case 'logs':
            previewContent.innerHTML = '<pre>Logs will appear here...</pre>';
            break;
        case 'data':
            previewContent.innerHTML = '<pre>Data will appear here...</pre>';
            break;
    }
}

// Terminal functionality
function handleTerminalInput(event) {
    if (event.key === 'Enter') {
        const input = document.getElementById('terminal-input');
        const command = input.value.trim();
        
        if (command) {
            addTerminalLine(`$ ${command}`);
            executeTerminalCommand(command);
            input.value = '';
        }
    }
}

function addTerminalLine(line) {
    const output = document.getElementById('terminal-output');
    const lineDiv = document.createElement('div');
    lineDiv.className = 'terminal-line';
    lineDiv.textContent = line;
    output.appendChild(lineDiv);
    output.scrollTop = output.scrollHeight;
    
    terminalHistory.push(line);
}

function executeTerminalCommand(command) {
    // Send to backend if connected
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'terminal_command',
            command: command
        }));
    } else {
        // Fallback simulation
        const parts = command.split(' ');
        const cmd = parts[0];
        
        switch (cmd) {
            case 'ls':
                addTerminalLine('agents/  configs/  data/  logs/');
                break;
            case 'status':
                addTerminalLine(`Active agents: ${activeAgents.length}`);
                addTerminalLine(`Background agents: ${sideAgents.length}`);
                break;
            case 'help':
                addTerminalLine('Available commands: ls, status, clear, help');
                break;
            case 'clear':
                document.getElementById('terminal-output').innerHTML = '';
                break;
            default:
                addTerminalLine(`Command not found: ${cmd}`);
        }
    }
}

// Status display
function updateStatusDisplay() {
    updateAgentTable();
    updateSystemMetrics();
    updateActivityLog();
}

function updateAgentTable() {
    const tbody = document.getElementById('agent-table-body');
    tbody.innerHTML = '';
    
    agents.forEach(agent => {
        const row = document.createElement('tr');
        const duration = Math.floor((new Date() - agent.createdAt) / 1000);
        
        row.innerHTML = `
            <td>${agent.name}</td>
            <td>${agent.type}</td>
            <td><span class="agent-state state-${agent.state}">${agent.state}</span></td>
            <td>${duration}s</td>
        `;
        
        tbody.appendChild(row);
    });
}

function updateSystemMetrics() {
    document.getElementById('active-count').textContent = activeAgents.length;
    document.getElementById('background-count').textContent = sideAgents.length;
    document.getElementById('memory-usage').textContent = `${Math.floor(Math.random() * 100 + 50)} MB`;
    document.getElementById('cpu-usage').textContent = `${Math.floor(Math.random() * 30 + 10)}%`;
}

function updateActivityLog() {
    const log = document.getElementById('activity-log');
    
    // Add recent activity
    if (chatHistory.length > 0) {
        const recent = chatHistory.slice(-5);
        log.innerHTML = recent.map(msg => 
            `<div style="margin-bottom: 5px;">[${msg.time}] ${msg.sender}: ${msg.message.substring(0, 30)}...</div>`
        ).join('');
    }
}

// Utility functions
function generateId() {
    return 'agent-' + Math.random().toString(36).substr(2, 9);
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function updateClock() {
    const clock = document.getElementById('clock');
    clock.textContent = new Date().toLocaleTimeString();
}

function updateAgentCount() {
    document.getElementById('agent-count').textContent = agents.size;
}

function updateAgentDurations() {
    if (document.getElementById('status-tab').classList.contains('active')) {
        updateAgentTable();
    }
}

function updateSystemMetricsFromServer(metrics) {
    if (metrics.active_agents !== undefined) {
        document.getElementById('active-count').textContent = metrics.active_agents;
    }
    if (metrics.total_agents !== undefined) {
        document.getElementById('background-count').textContent = metrics.total_agents - metrics.active_agents;
    }
    if (metrics.memory_usage !== undefined) {
        document.getElementById('memory-usage').textContent = metrics.memory_usage;
    }
    if (metrics.cpu_usage !== undefined) {
        document.getElementById('cpu-usage').textContent = metrics.cpu_usage;
    }
}