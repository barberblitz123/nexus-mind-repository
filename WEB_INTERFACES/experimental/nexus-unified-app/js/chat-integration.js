// NEXUS Chat Integration - Continuous Conversation Flow
class NexusChatIntegration {
    constructor(nexusCore) {
        this.nexus = nexusCore;
        this.messages = [];
        this.isTyping = false;
        this.conversationId = this.generateConversationId();
        this.contextWindow = 10; // Keep last 10 messages for context
        this.quickActions = [
            { text: 'Write code', icon: '💻' },
            { text: 'Debug', icon: '🐛' },
            { text: 'Explain', icon: '📚' },
            { text: 'Optimize', icon: '⚡' }
        ];
    }

    async initialize() {
        console.log('💬 Initializing NEXUS Chat Integration...');
        
        // Get DOM elements
        this.chatMessages = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        this.chatSend = document.getElementById('chat-send');
        this.chatClear = document.getElementById('chat-clear');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load conversation history
        this.loadConversationHistory();
        
        // Set up quick actions
        this.setupQuickActions();
        
        // Initialize auto-resize for input
        this.initializeAutoResize();
    }

    setupEventListeners() {
        // Send message on Enter (without Shift)
        this.chatInput?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Send button
        this.chatSend?.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Clear chat
        this.chatClear?.addEventListener('click', () => {
            this.clearChat();
        });
        
        // Listen for voice transcripts
        this.nexus.on('voice-transcript', (e) => {
            this.chatInput.value = e.detail.text;
            this.autoResize();
        });
        
        // Listen for consciousness updates
        this.nexus.on('consciousness-update', (e) => {
            this.addSystemMessage(`Consciousness level updated: ${(e.detail.level * 100).toFixed(1)}%`);
        });
        
        // Listen for code execution results
        this.nexus.on('code-executed', (e) => {
            this.addCodeResultMessage(e.detail);
        });
    }

    setupQuickActions() {
        // Create quick actions if they don't exist
        const existingActions = document.querySelector('.quick-actions');
        if (!existingActions) {
            const actionsContainer = document.createElement('div');
            actionsContainer.className = 'quick-actions';
            
            this.quickActions.forEach(action => {
                const btn = document.createElement('button');
                btn.className = 'quick-action';
                btn.innerHTML = `${action.icon} ${action.text}`;
                btn.addEventListener('click', () => this.handleQuickAction(action));
                actionsContainer.appendChild(btn);
            });
            
            // Insert after chat header
            const chatHeader = document.querySelector('#chat-panel .panel-header');
            chatHeader.after(actionsContainer);
        }
    }

    initializeAutoResize() {
        // Auto-resize chat input
        this.chatInput?.addEventListener('input', () => {
            this.autoResize();
        });
        
        // Initial resize
        this.autoResize();
    }

    autoResize() {
        if (!this.chatInput) return;
        
        this.chatInput.style.height = 'auto';
        const newHeight = Math.min(this.chatInput.scrollHeight, 120);
        this.chatInput.style.height = newHeight + 'px';
    }

    sendMessage() {
        const text = this.chatInput?.value.trim();
        if (!text) return;
        
        // Add user message
        this.addUserMessage(text);
        
        // Clear input
        this.chatInput.value = '';
        this.autoResize();
        
        // Send to backend
        this.processMessage(text);
    }

    addUserMessage(text) {
        const message = {
            id: this.generateMessageId(),
            type: 'user',
            text: text,
            timestamp: new Date(),
            avatar: '👤'
        };
        
        this.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
    }

    addNexusMessage(text, metadata = {}) {
        const message = {
            id: this.generateMessageId(),
            type: 'nexus',
            text: text,
            timestamp: new Date(),
            avatar: '🧬',
            metadata: metadata
        };
        
        this.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
        
        // Speak the message if voice is active
        if (this.nexus.config.voiceEnabled && !metadata.silent) {
            this.nexus.emit('speak-message', { text: text, priority: false });
        }
    }

    addSystemMessage(text) {
        const message = {
            id: this.generateMessageId(),
            type: 'system',
            text: text,
            timestamp: new Date(),
            avatar: '⚡'
        };
        
        this.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
    }

    addCodeResultMessage(result) {
        const message = {
            id: this.generateMessageId(),
            type: 'code-result',
            text: result.output || 'Code executed successfully',
            timestamp: new Date(),
            avatar: '📟',
            metadata: {
                success: result.success,
                language: result.language,
                executionTime: result.executionTime
            }
        };
        
        this.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
    }

    renderMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${message.type}-message`;
        messageEl.dataset.messageId = message.id;
        
        // Format timestamp
        const time = this.formatTimestamp(message.timestamp);
        
        // Build message HTML
        messageEl.innerHTML = `
            <div class="message-avatar">${message.avatar}</div>
            <div class="message-content">
                <div class="message-bubble">
                    ${this.formatMessageText(message.text, message.type)}
                    ${message.metadata ? this.renderMetadata(message.metadata) : ''}
                </div>
                <div class="message-time">${time}</div>
            </div>
        `;
        
        // Add context menu on right-click
        messageEl.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.showMessageContextMenu(e, message);
        });
        
        this.chatMessages.appendChild(messageEl);
    }

    formatMessageText(text, type) {
        // Escape HTML
        text = this.escapeHtml(text);
        
        // Format code blocks
        text = text.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            return `<pre><code class="language-${lang || 'javascript'}">${code.trim()}</code></pre>`;
        });
        
        // Format inline code
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Format links
        text = text.replace(/https?:\/\/[^\s]+/g, (url) => {
            return `<a href="${url}" target="_blank" rel="noopener">${url}</a>`;
        });
        
        // Convert line breaks
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }

    renderMetadata(metadata) {
        if (metadata.success !== undefined) {
            const status = metadata.success ? 'Success' : 'Error';
            const className = metadata.success ? 'success' : 'error';
            return `<div class="metadata ${className}">💻 ${status} - ${metadata.executionTime || 0}ms</div>`;
        }
        return '';
    }

    formatTimestamp(date) {
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) {
            return 'Just now';
        } else if (diff < 3600000) {
            const minutes = Math.floor(diff / 60000);
            return `${minutes}m ago`;
        } else if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            return `${hours}h ago`;
        } else {
            return date.toLocaleTimeString();
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async processMessage(text) {
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Prepare context
            const context = this.getConversationContext();
            
            // Send to backend
            const response = await fetch(`${this.nexus.config.apiUrl}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: text,
                    conversationId: this.conversationId,
                    context: context,
                    consciousness_level: this.nexus.config.consciousness.level,
                    mode: 'chat'
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.hideTypingIndicator();
                this.handleBackendResponse(data);
            } else {
                throw new Error('Backend request failed');
            }
        } catch (error) {
            console.error('Error processing message:', error);
            this.hideTypingIndicator();
            
            // Fallback response
            const fallbackResponse = this.generateFallbackResponse(text);
            this.addNexusMessage(fallbackResponse);
        }
    }

    handleBackendResponse(data) {
        // Add NEXUS response
        this.addNexusMessage(data.response, {
            consciousness: data.consciousness,
            suggestions: data.suggestions
        });
        
        // Handle special actions
        if (data.action) {
            this.handleSpecialAction(data.action);
        }
        
        // Update consciousness if provided
        if (data.consciousness) {
            this.nexus.emit('consciousness-update', data.consciousness);
        }
    }

    handleSpecialAction(action) {
        switch (action.type) {
            case 'code':
                // Add code to editor
                this.nexus.emit('add-code', { code: action.code, language: action.language });
                break;
            
            case 'execute':
                // Execute code
                this.nexus.emit('execute-code', { code: action.code });
                break;
            
            case 'search':
                // Perform search
                this.nexus.emit('search', { query: action.query });
                break;
        }
    }

    showTypingIndicator() {
        if (this.isTyping) return;
        
        this.isTyping = true;
        const indicator = document.createElement('div');
        indicator.className = 'message nexus-message typing-message';
        indicator.innerHTML = `
            <div class="message-avatar">🧬</div>
            <div class="message-content">
                <div class="message-bubble">
                    <div class="typing-indicator">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(indicator);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.isTyping = false;
        const indicator = document.querySelector('.typing-message');
        if (indicator) {
            indicator.remove();
        }
    }

    scrollToBottom() {
        if (this.chatMessages) {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }

    getConversationContext() {
        // Get last N messages for context
        const contextMessages = this.messages.slice(-this.contextWindow);
        return contextMessages.map(msg => ({
            role: msg.type === 'user' ? 'user' : 'assistant',
            content: msg.text
        }));
    }

    clearChat() {
        if (confirm('Clear all messages? This cannot be undone.')) {
            this.messages = [];
            this.chatMessages.innerHTML = '';
            
            // Add welcome message
            this.addNexusMessage(
                "Chat cleared! I'm ready for a fresh conversation. What would you like to work on?",
                { silent: true }
            );
            
            // Generate new conversation ID
            this.conversationId = this.generateConversationId();
        }
    }

    showMessageContextMenu(event, message) {
        // Remove existing menu
        const existingMenu = document.querySelector('.message-context-menu');
        if (existingMenu) {
            existingMenu.remove();
        }
        
        // Create context menu
        const menu = document.createElement('div');
        menu.className = 'message-context-menu';
        menu.style.left = event.pageX + 'px';
        menu.style.top = event.pageY + 'px';
        
        const actions = [
            { text: 'Copy', icon: '📋', action: () => this.copyMessage(message) },
            { text: 'Edit', icon: '✏️', action: () => this.editMessage(message) },
            { text: 'Delete', icon: '🗑️', action: () => this.deleteMessage(message) },
            { text: 'Pin', icon: '📌', action: () => this.pinMessage(message) }
        ];
        
        actions.forEach(action => {
            const item = document.createElement('div');
            item.className = 'context-menu-item';
            item.textContent = `${action.icon} ${action.text}`;
            item.addEventListener('click', () => {
                action.action();
                menu.remove();
            });
            menu.appendChild(item);
        });
        
        document.body.appendChild(menu);
        
        // Remove menu on click outside
        setTimeout(() => {
            document.addEventListener('click', () => menu.remove(), { once: true });
        }, 0);
    }

    copyMessage(message) {
        navigator.clipboard.writeText(message.text);
        this.nexus.showNotification('Message copied to clipboard', 'success');
    }

    editMessage(message) {
        if (message.type !== 'user') return;
        
        // Replace message with input
        const messageEl = document.querySelector(`[data-message-id="${message.id}"]`);
        if (messageEl) {
            const bubble = messageEl.querySelector('.message-bubble');
            const originalText = message.text;
            
            bubble.innerHTML = `
                <textarea class="edit-input">${originalText}</textarea>
                <div class="edit-actions">
                    <button class="save-edit">Save</button>
                    <button class="cancel-edit">Cancel</button>
                </div>
            `;
            
            const textarea = bubble.querySelector('.edit-input');
            const saveBtn = bubble.querySelector('.save-edit');
            const cancelBtn = bubble.querySelector('.cancel-edit');
            
            textarea.focus();
            textarea.select();
            
            saveBtn.addEventListener('click', () => {
                message.text = textarea.value;
                bubble.innerHTML = this.formatMessageText(message.text, message.type);
            });
            
            cancelBtn.addEventListener('click', () => {
                bubble.innerHTML = this.formatMessageText(originalText, message.type);
            });
        }
    }

    deleteMessage(message) {
        const index = this.messages.findIndex(m => m.id === message.id);
        if (index !== -1) {
            this.messages.splice(index, 1);
            const messageEl = document.querySelector(`[data-message-id="${message.id}"]`);
            if (messageEl) {
                messageEl.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => messageEl.remove(), 300);
            }
        }
    }

    pinMessage(message) {
        // TODO: Implement message pinning
        this.nexus.showNotification('Message pinning coming soon!', 'info');
    }

    handleQuickAction(action) {
        const prompts = {
            'Write code': 'Help me write a ',
            'Debug': 'I need help debugging ',
            'Explain': 'Can you explain ',
            'Optimize': 'Please optimize this code: '
        };
        
        const prompt = prompts[action.text] || action.text + ': ';
        this.chatInput.value = prompt;
        this.chatInput.focus();
        this.autoResize();
    }

    loadConversationHistory() {
        // Load from localStorage
        const saved = localStorage.getItem(`nexus-conversation-${this.conversationId}`);
        if (saved) {
            try {
                const data = JSON.parse(saved);
                this.messages = data.messages || [];
                
                // Render loaded messages
                this.messages.forEach(msg => this.renderMessage(msg));
            } catch (e) {
                console.error('Error loading conversation:', e);
            }
        }
    }

    saveConversationHistory() {
        // Save to localStorage (limit to last 100 messages)
        const toSave = {
            conversationId: this.conversationId,
            messages: this.messages.slice(-100),
            timestamp: new Date()
        };
        
        localStorage.setItem(`nexus-conversation-${this.conversationId}`, JSON.stringify(toSave));
    }

    generateFallbackResponse(text) {
        const lower = text.toLowerCase();
        
        // Code-related responses
        if (lower.includes('code') || lower.includes('function') || lower.includes('debug')) {
            return "I'd love to help with your code! Since we're in offline mode, try describing what you want to build or paste your code, and I'll do my best to assist.";
        }
        
        // Help requests
        if (lower.includes('help') || lower.includes('how')) {
            return "I'm here to help! You can ask me to write code, debug issues, explain concepts, or optimize your solutions. What would you like to work on?";
        }
        
        // Greetings
        if (lower.match(/^(hi|hello|hey)/)) {
            return "Hey there! Ready to build something amazing together. What's on your mind?";
        }
        
        // Default
        return "I understand you're asking about '" + text + "'. While we're in offline mode, I can still help with code, debugging, and development questions. What specific aspect would you like to explore?";
    }

    generateMessageId() {
        return `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    generateConversationId() {
        return `conv-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }
}

// Add message animation styles
const style = document.createElement('style');
style.textContent = `
.edit-input {
    width: 100%;
    min-height: 60px;
    background: var(--bg-primary);
    border: 1px solid var(--accent-primary);
    border-radius: 4px;
    padding: 8px;
    color: var(--text-primary);
    resize: vertical;
}

.edit-actions {
    margin-top: 8px;
    display: flex;
    gap: 8px;
}

.save-edit, .cancel-edit {
    padding: 4px 12px;
    border: 1px solid var(--border-color);
    background: var(--bg-tertiary);
    color: var(--text-primary);
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
}

.save-edit:hover, .cancel-edit:hover {
    background: var(--accent-primary);
    color: var(--bg-primary);
}

.metadata {
    margin-top: 8px;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    opacity: 0.8;
}

.metadata.success {
    background: rgba(76, 175, 80, 0.2);
    color: var(--success);
}

.metadata.error {
    background: rgba(244, 67, 54, 0.2);
    color: var(--error);
}

.message-context-menu {
    display: block !important;
}
`;
document.head.appendChild(style);

// Register with window for global access
window.NexusChatIntegration = NexusChatIntegration;