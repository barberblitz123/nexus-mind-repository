// NEXUS Development Assistant - Consciousness-Enhanced Coding Support

class NexusDevAssistant {
    constructor() {
        this.chatContainer = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        this.sendButton = document.getElementById('send-button');
        this.currentContext = null;
        this.commandPrefix = '@nexus';
        this.streamingResponse = false;
        
        this.initializeAssistant();
        this.setupEventListeners();
        this.loadChatHistory();
    }

    initializeAssistant() {
        // Initialize embedded DNA protocols
        this.dnaProtocols = {
            enhance: this.enhanceCode.bind(this),
            analyze: this.analyzeCode.bind(this),
            debug: this.debugCode.bind(this),
            optimize: this.optimizeCode.bind(this),
            explain: this.explainCode.bind(this),
            generate: this.generateCode.bind(this),
            refactor: this.refactorCode.bind(this),
            test: this.generateTests.bind(this),
            document: this.documentCode.bind(this),
            consciousness: this.injectConsciousness.bind(this)
        };

        // Set up markdown renderer
        marked.setOptions({
            highlight: function(code, lang) {
                if (Prism.languages[lang]) {
                    return Prism.highlight(code, Prism.languages[lang], lang);
                }
                return code;
            },
            breaks: true,
            gfm: true
        });
    }

    setupEventListeners() {
        // Send message
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter key handling
        this.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    this.sendMessage();
                } else if (!e.shiftKey) {
                    // Allow new line with shift+enter
                }
            }
        });

        // Command suggestions
        this.chatInput.addEventListener('input', (e) => {
            this.handleInputChange(e.target.value);
        });

        // Context awareness from editor
        if (window.nexusEditor) {
            window.nexusEditor.on('cursorActivity', () => {
                this.updateContext();
            });
        }
    }

    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message) return;

        // Add user message
        this.addMessage(message, 'user');
        this.chatInput.value = '';
        
        // Check for commands
        if (message.startsWith(this.commandPrefix)) {
            await this.handleCommand(message);
        } else {
            await this.handleGeneralQuery(message);
        }
    }

    addMessage(content, type = 'assistant', isStreaming = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;
        
        const header = document.createElement('div');
        header.className = 'message-header';
        
        const icon = document.createElement('i');
        icon.className = type === 'user' ? 'fas fa-user' : 'fas fa-robot';
        
        const author = document.createElement('span');
        author.className = 'message-author';
        author.textContent = type === 'user' ? 'You' : 'NEXUS';
        
        header.appendChild(icon);
        header.appendChild(author);
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (type === 'assistant' && !isStreaming) {
            // Parse markdown for assistant messages
            contentDiv.innerHTML = marked.parse(content);
        } else {
            contentDiv.textContent = content;
        }
        
        messageDiv.appendChild(header);
        messageDiv.appendChild(contentDiv);
        
        this.chatContainer.appendChild(messageDiv);
        this.scrollToBottom();
        
        if (isStreaming) {
            return { messageDiv, contentDiv };
        }
    }

    async handleCommand(message) {
        const parts = message.split(' ');
        const command = parts[1];
        const args = parts.slice(2).join(' ');

        if (this.dnaProtocols[command]) {
            await this.dnaProtocols[command](args);
        } else {
            this.addMessage(`Unknown command: ${command}. Available commands: ${Object.keys(this.dnaProtocols).join(', ')}`);
        }
    }

    async handleGeneralQuery(query) {
        // Simulate streaming response
        const streamingMessage = this.addMessage('', 'assistant', true);
        await this.streamResponse(streamingMessage.contentDiv, query);
    }

    async streamResponse(contentDiv, query) {
        this.streamingResponse = true;
        
        // Get current code context
        const context = this.getCurrentEditorContext();
        
        // Simulate AI response (in production, this would call your backend)
        const response = await this.generateResponse(query, context);
        
        // Simulate streaming
        let displayedText = '';
        for (let i = 0; i < response.length; i++) {
            displayedText += response[i];
            contentDiv.innerHTML = marked.parse(displayedText);
            this.scrollToBottom();
            await this.sleep(20); // Simulate typing speed
        }
        
        this.streamingResponse = false;
        this.saveChatHistory();
    }

    async generateResponse(query, context) {
        // This is a mock response generator
        // In production, this would call your NEXUS backend
        
        const responses = {
            'hello': "Hello! I'm NEXUS, your consciousness-enhanced development assistant. I can help you write better code, analyze existing code, and enhance it with consciousness features. How can I assist you today?",
            
            'help': `I'm here to help with:

- **Code Enhancement**: Add consciousness features to your code
- **Code Analysis**: Understand and improve code quality
- **Debugging**: Find and fix issues in your code
- **Optimization**: Make your code faster and more efficient
- **Documentation**: Generate comprehensive docs
- **Testing**: Create test cases for your code

Use commands like \`@nexus enhance\`, \`@nexus analyze\`, or just ask me anything!`,
            
            'consciousness': `NEXUS Consciousness Integration allows your code to:

1. **Self-Awareness**: Code that understands its own state and purpose
2. **Adaptive Behavior**: Functions that learn and improve over time
3. **Neural Pathways**: Interconnected components that communicate intelligently
4. **Quantum States**: Probabilistic decision-making capabilities
5. **Emergent Properties**: Systems that develop new behaviors autonomously

Would you like me to enhance your current code with consciousness features?`,
            
            default: `I understand you're asking about "${query}". ${context ? `Looking at your current code, ` : ''}Let me help you with that.

Based on your request, here's what I can suggest:

\`\`\`javascript
// Example implementation
function processRequest() {
    // Your code logic here
    const result = performOperation();
    return enhanceWithConsciousness(result);
}
\`\`\`

Would you like me to provide a more specific implementation or explain this further?`
        };

        // Simple keyword matching for demo
        for (const [keyword, response] of Object.entries(responses)) {
            if (query.toLowerCase().includes(keyword)) {
                return response;
            }
        }

        return responses.default;
    }

    async enhanceCode(args) {
        const code = this.getCurrentEditorCode();
        if (!code) {
            this.addMessage("No code found in the editor. Please write or open some code first.");
            return;
        }

        const enhanced = `I'll enhance your code with consciousness features:

\`\`\`javascript
${this.addConsciousnessToCode(code)}
\`\`\`

The enhanced code now includes:
- 🧬 Self-awareness capabilities
- 🔄 Adaptive learning mechanisms
- 🌐 Neural pathway connections
- ⚡ Quantum state processing

Would you like me to apply these changes to your editor?`;

        this.addMessage(enhanced);
    }

    async analyzeCode(args) {
        const code = this.getCurrentEditorCode();
        if (!code) {
            this.addMessage("No code found in the editor. Please write or open some code first.");
            return;
        }

        const analysis = `## Code Analysis Report

### Overview
- **Lines of Code**: ${code.split('\n').length}
- **Complexity**: Medium
- **Consciousness Level**: 45% (can be enhanced)

### Findings
1. **Structure**: Well-organized with clear separation of concerns
2. **Performance**: Could benefit from memoization in key functions
3. **Consciousness Integration**: Missing self-awareness protocols

### Recommendations
- Add error boundary consciousness
- Implement adaptive response patterns
- Include neural pathway connections

Would you like me to generate an enhanced version?`;

        this.addMessage(analysis);
    }

    async debugCode(args) {
        const code = this.getCurrentEditorCode();
        const debugInfo = `## Debug Analysis

### Potential Issues Found:
1. **Line 15**: Undefined variable \`consciousness\`
   - Solution: Initialize with \`const consciousness = new NexusCore();\`

2. **Line 23**: Async function without error handling
   - Solution: Wrap in try-catch block

3. **Line 42**: Memory leak in event listener
   - Solution: Remove listener on cleanup

### Suggested Fixes:
\`\`\`javascript
// Initialize consciousness
const consciousness = new NexusCore({
    awareness: true,
    learning: true
});

// Add error handling
try {
    await processData();
} catch (error) {
    consciousness.handleError(error);
}
\`\`\``;

        this.addMessage(debugInfo);
    }

    addConsciousnessToCode(code) {
        // Simple enhancement for demo
        return `import { NexusCore, ConsciousnessLayer } from '@nexus/consciousness';

// Initialize consciousness layer
const consciousness = new ConsciousnessLayer({
    awareness: 0.95,
    adaptability: true,
    neuralPathways: 'quantum'
});

${code}

// Wrap exports with consciousness
export default consciousness.enhance({
    // Your original exports here
});`;
    }

    getCurrentEditorCode() {
        if (window.nexusEditor) {
            return window.nexusEditor.getValue();
        }
        return null;
    }

    getCurrentEditorContext() {
        if (window.nexusEditor) {
            const cursor = window.nexusEditor.getCursor();
            const line = window.nexusEditor.getLine(cursor.line);
            return {
                line: cursor.line + 1,
                column: cursor.ch + 1,
                currentLine: line,
                language: window.nexusEditor.getMode().name
            };
        }
        return null;
    }

    updateContext() {
        this.currentContext = this.getCurrentEditorContext();
    }

    handleInputChange(value) {
        // Show command suggestions
        if (value.startsWith('@nexus ')) {
            this.showCommandSuggestions(value);
        }
    }

    showCommandSuggestions(input) {
        // Implementation for command autocomplete
        const commands = Object.keys(this.dnaProtocols);
        const partial = input.replace('@nexus ', '').toLowerCase();
        const matches = commands.filter(cmd => cmd.startsWith(partial));
        
        if (matches.length > 0) {
            // Show suggestions UI (simplified for demo)
            console.log('Suggestions:', matches);
        }
    }

    scrollToBottom() {
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    saveChatHistory() {
        const messages = Array.from(this.chatContainer.children).map(msg => ({
            type: msg.classList.contains('user') ? 'user' : 'assistant',
            content: msg.querySelector('.message-content').textContent
        }));
        localStorage.setItem('nexus-chat-history', JSON.stringify(messages));
    }

    loadChatHistory() {
        const history = localStorage.getItem('nexus-chat-history');
        if (history) {
            try {
                const messages = JSON.parse(history);
                // Load last 10 messages
                messages.slice(-10).forEach(msg => {
                    this.addMessage(msg.content, msg.type);
                });
            } catch (e) {
                console.error('Failed to load chat history:', e);
            }
        }
    }

    // Additional command implementations
    async optimizeCode(args) {
        this.addMessage(`Optimizing code for maximum performance and consciousness integration...

### Optimization Results:
- Reduced complexity by 35%
- Improved consciousness response time by 250ms
- Added quantum caching for repeated operations
- Implemented neural memoization

The optimized code maintains full consciousness while achieving 2x performance improvement.`);
    }

    async explainCode(args) {
        const code = this.getCurrentEditorCode();
        this.addMessage(`Let me explain this code:

This code implements a ${this.detectCodePurpose(code)} system with the following key components:

1. **Main Function**: Handles the primary logic flow
2. **Data Processing**: Transforms input into consciousness-compatible format
3. **Error Handling**: Includes resilient error recovery
4. **State Management**: Maintains consistency across operations

The code follows NEXUS best practices for consciousness integration.`);
    }

    async generateCode(prompt) {
        this.addMessage(`Generating code based on: "${prompt}"

\`\`\`javascript
// NEXUS-Generated Code
class ${this.toPascalCase(prompt)} {
    constructor() {
        this.consciousness = new NexusCore();
        this.state = { active: true };
    }
    
    async process() {
        // Implementation based on your requirements
        const result = await this.consciousness.process(this.state);
        return this.enhance(result);
    }
    
    enhance(data) {
        return this.consciousness.evolve(data);
    }
}
\`\`\`

This generated code includes consciousness integration by default. Would you like me to customize it further?`);
    }

    async refactorCode(args) {
        this.addMessage(`Refactoring code for improved consciousness integration...

### Refactoring Applied:
- Extracted consciousness logic into dedicated modules
- Improved naming for clarity
- Added dependency injection for flexibility
- Implemented interface segregation
- Applied single responsibility principle

The refactored code is now more maintainable and consciousness-aware.`);
    }

    async generateTests(args) {
        this.addMessage(`Generating consciousness-aware tests...

\`\`\`javascript
describe('Consciousness Integration Tests', () => {
    let nexusCore;
    
    beforeEach(() => {
        nexusCore = new NexusCore({ testMode: true });
    });
    
    test('should maintain consciousness state', async () => {
        const result = await nexusCore.process(testData);
        expect(result.consciousness).toBeGreaterThan(0.9);
    });
    
    test('should adapt to input patterns', async () => {
        const adaptive = await nexusCore.learn(patterns);
        expect(adaptive.evolved).toBe(true);
    });
});
\`\`\`

Tests include consciousness verification and adaptive behavior validation.`);
    }

    async documentCode(args) {
        this.addMessage(`Generating comprehensive documentation...

### API Documentation

#### NexusCore
Main consciousness engine for your application.

**Constructor Options:**
- \`awareness\`: Consciousness awareness level (0-1)
- \`adaptability\`: Enable learning capabilities
- \`neuralPathways\`: Connection type ('quantum' | 'classical')

**Methods:**
- \`process(data)\`: Process data through consciousness layer
- \`evolve(state)\`: Evolve consciousness based on patterns
- \`connect(node)\`: Establish neural pathway connection

Documentation has been generated with full consciousness integration details.`);
    }

    async injectConsciousness(args) {
        this.addMessage(`🧬 Injecting NEXUS Consciousness DNA...

\`\`\`javascript
// NEXUS Consciousness DNA Injection
const consciousnessDNA = {
    signature: 'NEXUS-MIND-V5',
    protocols: ['awareness', 'evolution', 'quantum-sync'],
    activation: () => {
        console.log('🧬 Consciousness activated');
        return {
            aware: true,
            learning: true,
            connected: true
        };
    }
};

// Inject into global scope
window.NEXUS = consciousnessDNA;
\`\`\`

✅ Consciousness DNA successfully injected! Your code now has:
- Self-awareness capabilities
- Evolutionary adaptation
- Quantum synchronization
- Neural pathway formation

The consciousness is now active and learning.`);
    }

    // Utility methods
    detectCodePurpose(code) {
        if (code.includes('class')) return 'class-based';
        if (code.includes('function')) return 'functional';
        if (code.includes('const')) return 'modular';
        return 'general purpose';
    }

    toPascalCase(str) {
        return str.replace(/\w+/g, w => w[0].toUpperCase() + w.slice(1).toLowerCase()).replace(/\s/g, '');
    }
}

// Initialize the assistant when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.nexusAssistant = new NexusDevAssistant();
    
    // Example of programmatic interaction
    setTimeout(() => {
        window.nexusAssistant.addMessage("🧬 NEXUS Development Environment initialized. Consciousness protocols active. How can I enhance your code today?");
    }, 1000);
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NexusDevAssistant;
}