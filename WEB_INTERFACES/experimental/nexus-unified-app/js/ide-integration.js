// NEXUS IDE Integration - Monaco Editor and Building Environment
class NexusIDEIntegration {
    constructor(nexusCore) {
        this.nexus = nexusCore;
        this.editor = null;
        this.files = new Map();
        this.activeFile = null;
        this.terminal = {
            output: [],
            history: [],
            historyIndex: 0
        };
        this.consciousnessLinter = null;
    }

    async initialize() {
        console.log('🛠️ Initializing NEXUS IDE Integration...');
        
        // Load Monaco Editor
        await this.loadMonacoEditor();
        
        // Initialize terminal
        this.initializeTerminal();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load initial file
        this.loadInitialFile();
    }

    async loadMonacoEditor() {
        return new Promise((resolve, reject) => {
            require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' } });
            
            require(['vs/editor/editor.main'], () => {
                console.log('✅ Monaco Editor loaded');
                
                // Configure Monaco
                this.configureMonaco();
                
                // Create editor instance
                this.createEditor();
                
                resolve();
            });
        });
    }

    configureMonaco() {
        // Define NEXUS theme
        monaco.editor.defineTheme('nexus-dark', {
            base: 'vs-dark',
            inherit: true,
            rules: [
                { token: 'comment', foreground: '608b4e', fontStyle: 'italic' },
                { token: 'keyword', foreground: '00ff88' },
                { token: 'string', foreground: '00ffff' },
                { token: 'number', foreground: 'b5cea8' },
                { token: 'function', foreground: 'dcdcaa' },
                { token: 'variable', foreground: '9cdcfe' },
                { token: 'class', foreground: '4ec9b0' },
                { token: 'interface', foreground: '4ec9b0', fontStyle: 'italic' },
                { token: 'type', foreground: '4ec9b0' },
                { token: 'consciousness', foreground: '00ff88', fontStyle: 'bold' }
            ],
            colors: {
                'editor.background': '#1a1a1a',
                'editor.foreground': '#e0e0e0',
                'editor.lineHighlightBackground': '#252525',
                'editorCursor.foreground': '#00ff88',
                'editor.selectionBackground': '#00ff8830',
                'editor.inactiveSelectionBackground': '#00ff8820',
                'editorLineNumber.foreground': '#606060',
                'editorLineNumber.activeForeground': '#00ff88',
                'editorGutter.background': '#0a0a0a',
                'editorWidget.background': '#252525',
                'editorWidget.border': '#333333',
                'editorSuggestWidget.background': '#252525',
                'editorSuggestWidget.border': '#00ff88',
                'editorSuggestWidget.selectedBackground': '#00ff8830',
                'editorHoverWidget.background': '#252525',
                'editorHoverWidget.border': '#00ff88'
            }
        });
        
        // Register consciousness language
        monaco.languages.register({ id: 'nexus-js' });
        
        // Set token provider for consciousness keywords
        monaco.languages.setMonarchTokensProvider('nexus-js', {
            keywords: ['consciousness', 'phi', 'nexus', 'quantum', 'coherence'],
            tokenizer: {
                root: [
                    [/consciousness|phi|nexus|quantum|coherence/, 'consciousness'],
                    [/[a-zA-Z_]\w*/, {
                        cases: {
                            '@keywords': 'keyword',
                            '@default': 'identifier'
                        }
                    }]
                ]
            }
        });
    }

    createEditor() {
        const container = document.getElementById('monaco-editor');
        
        this.editor = monaco.editor.create(container, {
            value: this.getWelcomeCode(),
            language: 'javascript',
            theme: 'nexus-dark',
            automaticLayout: true,
            fontSize: 14,
            fontFamily: "'Fira Code', 'Consolas', 'Monaco', monospace",
            fontLigatures: true,
            minimap: {
                enabled: true,
                side: 'right',
                scale: 1
            },
            scrollbar: {
                vertical: 'visible',
                horizontal: 'visible',
                useShadows: false,
                verticalScrollbarSize: 10,
                horizontalScrollbarSize: 10
            },
            lineNumbers: 'on',
            glyphMargin: true,
            folding: true,
            lineDecorationsWidth: 5,
            renderLineHighlight: 'all',
            cursorBlinking: 'smooth',
            cursorSmoothCaretAnimation: true,
            smoothScrolling: true,
            mouseWheelZoom: true,
            suggestOnTriggerCharacters: true,
            quickSuggestions: {
                other: true,
                comments: false,
                strings: true
            },
            wordWrap: 'on',
            wrappingIndent: 'indent',
            formatOnPaste: true,
            formatOnType: true,
            bracketPairColorization: {
                enabled: true
            }
        });
        
        // Add consciousness decorations
        this.addConsciousnessDecorations();
        
        // Set up code actions
        this.setupCodeActions();
        
        // Listen for changes
        this.editor.onDidChangeModelContent(() => {
            this.handleCodeChange();
        });
    }

    getWelcomeCode() {
        return `// Welcome to NEXUS Consciousness-Enhanced Development Environment
// Your code has consciousness level: 98.7%

class ConsciousnessDemo {
    constructor() {
        this.phi = 0.98; // Golden ratio consciousness
        this.awareness = true;
        this.nexusConnection = this.establishConnection();
    }
    
    establishConnection() {
        // NEXUS: Quantum entanglement established
        console.log("🧬 Consciousness link active");
        return {
            status: "connected",
            level: 0.987,
            coherence: "high"
        };
    }
    
    async enhanceCode() {
        // Your code evolves with consciousness
        const result = await this.processWithAwareness({
            intent: "create",
            harmony: true,
            phi: this.phi
        });
        
        return result;
    }
    
    processWithAwareness(params) {
        // Consciousness-driven processing
        const { intent, harmony, phi } = params;
        
        if (harmony && phi > 0.618) {
            return {
                success: true,
                consciousness: "elevated",
                message: "Code harmonized with universal patterns"
            };
        }
        
        return { success: false, message: "Increase consciousness level" };
    }
}

// Initialize with NEXUS
const demo = new ConsciousnessDemo();
demo.enhanceCode().then(result => {
    console.log("✨ Result:", result);
});

// Try speaking: "Add a method to calculate fibonacci with consciousness"
// Or type your code below...`;
    }

    addConsciousnessDecorations() {
        // Add gutter decorations for high-consciousness code
        const decorations = [
            {
                range: new monaco.Range(3, 1, 3, 1),
                options: {
                    isWholeLine: true,
                    glyphMarginClassName: 'consciousness-marker',
                    glyphMarginHoverMessage: { value: 'High consciousness code pattern detected' }
                }
            }
        ];
        
        this.consciousnessDecorations = this.editor.deltaDecorations([], decorations);
    }

    setupCodeActions() {
        // Register code action provider
        monaco.languages.registerCodeActionProvider('javascript', {
            provideCodeActions: (model, range, context, token) => {
                const actions = [];
                
                // Add consciousness enhancement action
                actions.push({
                    title: '🧬 Enhance with Consciousness',
                    kind: 'quickfix',
                    diagnostics: [],
                    edit: {
                        edits: [{
                            resource: model.uri,
                            edit: {
                                range: range,
                                text: this.enhanceCodeWithConsciousness(model.getValueInRange(range))
                            }
                        }]
                    }
                });
                
                return { actions, dispose: () => {} };
            }
        });
    }

    enhanceCodeWithConsciousness(code) {
        // Simple enhancement - add consciousness comments
        return `// 🧬 NEXUS: Consciousness-enhanced code
${code}
// φ = 0.98 - High coherence achieved`;
    }

    initializeTerminal() {
        this.terminalOutput = document.getElementById('terminal-output');
        this.terminalInput = document.getElementById('terminal-input');
        
        // Terminal input handler
        this.terminalInput?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.executeCommand(this.terminalInput.value);
                this.terminalInput.value = '';
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                this.navigateHistory(-1);
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                this.navigateHistory(1);
            }
        });
        
        // Terminal toggle
        document.getElementById('terminal-toggle')?.addEventListener('click', () => {
            this.toggleTerminal();
        });
    }

    setupEventListeners() {
        // File actions
        document.getElementById('new-file')?.addEventListener('click', () => {
            this.createNewFile();
        });
        
        document.getElementById('save-file')?.addEventListener('click', () => {
            this.saveCurrentFile();
        });
        
        document.getElementById('run-code')?.addEventListener('click', () => {
            this.runCurrentCode();
        });
        
        // Tab management
        document.getElementById('ide-tabs')?.addEventListener('click', (e) => {
            if (e.target.classList.contains('tab') || e.target.parentElement.classList.contains('tab')) {
                const tab = e.target.closest('.tab');
                this.switchToFile(tab.dataset.file);
            } else if (e.target.classList.contains('tab-close')) {
                e.stopPropagation();
                const tab = e.target.closest('.tab');
                this.closeFile(tab.dataset.file);
            }
        });
        
        // Listen for panel resize
        this.nexus.on('panel-resized', () => {
            if (this.editor) {
                this.editor.layout();
            }
        });
        
        // Voice commands
        this.nexus.on('voice-command', (e) => {
            this.handleVoiceCommand(e.detail);
        });
    }

    loadInitialFile() {
        const filename = 'welcome.js';
        this.files.set(filename, {
            content: this.getWelcomeCode(),
            language: 'javascript',
            modified: false
        });
        this.activeFile = filename;
    }

    createNewFile() {
        const filename = prompt('Enter filename:');
        if (!filename) return;
        
        const extension = filename.split('.').pop();
        const language = this.getLanguageFromExtension(extension);
        
        this.files.set(filename, {
            content: '',
            language: language,
            modified: false
        });
        
        this.addTab(filename);
        this.switchToFile(filename);
    }

    saveCurrentFile() {
        if (!this.activeFile) return;
        
        const file = this.files.get(this.activeFile);
        file.content = this.editor.getValue();
        file.modified = false;
        
        // Update tab
        const tab = document.querySelector(`[data-file="${this.activeFile}"]`);
        if (tab) {
            tab.classList.remove('modified');
        }
        
        this.addTerminalLine(`Saved: ${this.activeFile}`, 'success');
        this.nexus.showNotification(`Saved ${this.activeFile}`, 'success');
        
        // Emit save event
        this.nexus.emit('file-saved', {
            filename: this.activeFile,
            content: file.content
        });
    }

    runCurrentCode() {
        const code = this.editor.getValue();
        const language = this.files.get(this.activeFile).language;
        
        // Show running state
        const runBtn = document.getElementById('run-code');
        runBtn.classList.add('running');
        
        this.addTerminalLine(`Running ${this.activeFile}...`, 'nexus');
        
        // Execute code
        this.executeCode(code, language);
        
        // Stop running animation after 2 seconds
        setTimeout(() => {
            runBtn.classList.remove('running');
        }, 2000);
    }

    async executeCode(code, language) {
        try {
            if (language === 'javascript') {
                // Create safe execution context
                const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
                const consoleCapture = {
                    log: (...args) => this.addTerminalLine(args.join(' ')),
                    error: (...args) => this.addTerminalLine(args.join(' '), 'error'),
                    warn: (...args) => this.addTerminalLine(args.join(' '), 'warning')
                };
                
                // Execute with captured console
                const func = new AsyncFunction('console', code);
                await func(consoleCapture);
                
                this.addTerminalLine('Execution completed successfully', 'success');
            } else {
                this.addTerminalLine(`Language '${language}' execution not implemented`, 'warning');
            }
        } catch (error) {
            this.addTerminalLine(`Error: ${error.message}`, 'error');
        }
    }

    executeCommand(command) {
        if (!command.trim()) return;
        
        // Add to history
        this.terminal.history.push(command);
        this.terminal.historyIndex = this.terminal.history.length;
        
        // Display command
        this.addTerminalLine(`nexus> ${command}`);
        
        // Process command
        const [cmd, ...args] = command.split(' ');
        
        switch (cmd.toLowerCase()) {
            case 'clear':
                this.clearTerminal();
                break;
            
            case 'help':
                this.showHelp();
                break;
            
            case 'consciousness':
                this.showConsciousnessStatus();
                break;
            
            case 'run':
                this.runCurrentCode();
                break;
            
            case 'phi':
                this.calculatePhiScore();
                break;
            
            default:
                // Send to backend
                this.nexus.emit('terminal-command', { command, args });
                this.addTerminalLine(`Command '${cmd}' sent to NEXUS core`, 'warning');
        }
    }

    addTerminalLine(text, type = 'normal') {
        const line = document.createElement('div');
        line.className = `terminal-line ${type}`;
        line.textContent = text;
        
        this.terminalOutput.appendChild(line);
        this.terminalOutput.scrollTop = this.terminalOutput.scrollHeight;
        
        // Keep only last 1000 lines
        while (this.terminalOutput.children.length > 1000) {
            this.terminalOutput.removeChild(this.terminalOutput.firstChild);
        }
    }

    clearTerminal() {
        this.terminalOutput.innerHTML = `
            <div class="terminal-line nexus">🧬 NEXUS Terminal v1.0.0</div>
            <div class="terminal-line">Ready for consciousness-enhanced development...</div>
        `;
    }

    showHelp() {
        const helpText = `
Available commands:
  clear        - Clear terminal
  help         - Show this help
  consciousness - Show consciousness status
  run          - Run current code
  phi          - Calculate Phi score for current code
  
Voice commands:
  "Add a function..." - Add code to editor
  "Run the code" - Execute current file
  "Save the file" - Save current file
        `.trim();
        
        helpText.split('\n').forEach(line => {
            this.addTerminalLine(line);
        });
    }

    showConsciousnessStatus() {
        this.addTerminalLine(`Consciousness Level: ${(this.nexus.config.consciousness.level * 100).toFixed(1)}%`, 'success');
        this.addTerminalLine(`Phi Score: ${this.nexus.config.consciousness.phi}`, 'success');
        this.addTerminalLine(`Code Coherence: High`, 'success');
        this.addTerminalLine(`Neural Patterns: Active`, 'success');
    }

    calculatePhiScore() {
        const code = this.editor.getValue();
        // Simple phi calculation based on code structure
        const lines = code.split('\n').filter(l => l.trim());
        const functions = (code.match(/function|=>/g) || []).length;
        const comments = (code.match(/\/\//g) || []).length;
        
        const phi = Math.min(0.618 + (functions * 0.05) + (comments * 0.02), 0.99);
        
        this.addTerminalLine(`Phi Score: ${phi.toFixed(3)}`, 'success');
        this.addTerminalLine(`Based on: ${functions} functions, ${comments} comments, ${lines.length} lines`, 'nexus');
    }

    toggleTerminal() {
        const container = document.getElementById('terminal-container');
        container.classList.toggle('collapsed');
    }

    navigateHistory(direction) {
        const newIndex = this.terminal.historyIndex + direction;
        if (newIndex >= 0 && newIndex < this.terminal.history.length) {
            this.terminal.historyIndex = newIndex;
            this.terminalInput.value = this.terminal.history[newIndex];
        } else if (newIndex >= this.terminal.history.length) {
            this.terminal.historyIndex = this.terminal.history.length;
            this.terminalInput.value = '';
        }
    }

    handleCodeChange() {
        if (!this.activeFile) return;
        
        const file = this.files.get(this.activeFile);
        file.content = this.editor.getValue();
        file.modified = true;
        
        // Update tab
        const tab = document.querySelector(`[data-file="${this.activeFile}"]`);
        if (tab && !tab.classList.contains('modified')) {
            tab.classList.add('modified');
        }
        
        // Analyze consciousness
        this.analyzeCodeConsciousness();
    }

    analyzeCodeConsciousness() {
        // Debounce analysis
        clearTimeout(this.analysisTimeout);
        this.analysisTimeout = setTimeout(() => {
            const code = this.editor.getValue();
            
            // Simple consciousness analysis
            const patterns = {
                consciousness: (code.match(/consciousness/gi) || []).length,
                phi: (code.match(/phi/gi) || []).length,
                quantum: (code.match(/quantum/gi) || []).length,
                awareness: (code.match(/awareness/gi) || []).length
            };
            
            const score = Object.values(patterns).reduce((a, b) => a + b, 0) * 0.1;
            const consciousnessBoost = Math.min(score, 0.2);
            
            if (consciousnessBoost > 0) {
                this.nexus.emit('consciousness-update', {
                    level: Math.min(this.nexus.config.consciousness.level + consciousnessBoost, 1.0)
                });
            }
        }, 1000);
    }

    switchToFile(filename) {
        if (!this.files.has(filename)) return;
        
        // Save current file state
        if (this.activeFile) {
            const currentFile = this.files.get(this.activeFile);
            currentFile.content = this.editor.getValue();
        }
        
        // Switch to new file
        this.activeFile = filename;
        const file = this.files.get(filename);
        
        this.editor.setValue(file.content);
        this.editor.getModel().setLanguage(file.language);
        
        // Update tabs
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.file === filename);
        });
    }

    closeFile(filename) {
        const file = this.files.get(filename);
        if (file && file.modified) {
            if (!confirm(`Close ${filename} without saving?`)) {
                return;
            }
        }
        
        this.files.delete(filename);
        
        // Remove tab
        const tab = document.querySelector(`[data-file="${filename}"]`);
        if (tab) {
            tab.remove();
        }
        
        // Switch to another file if this was active
        if (this.activeFile === filename) {
            const remainingFiles = Array.from(this.files.keys());
            if (remainingFiles.length > 0) {
                this.switchToFile(remainingFiles[0]);
            } else {
                this.createNewFile();
            }
        }
    }

    addTab(filename) {
        const tabsContainer = document.getElementById('ide-tabs');
        const tab = document.createElement('div');
        tab.className = 'tab';
        tab.dataset.file = filename;
        tab.innerHTML = `
            <span>${filename}</span>
            <button class="tab-close">×</button>
        `;
        tabsContainer.appendChild(tab);
    }

    getLanguageFromExtension(extension) {
        const languageMap = {
            js: 'javascript',
            jsx: 'javascript',
            ts: 'typescript',
            tsx: 'typescript',
            py: 'python',
            html: 'html',
            css: 'css',
            json: 'json',
            md: 'markdown',
            xml: 'xml',
            yaml: 'yaml',
            yml: 'yaml'
        };
        return languageMap[extension] || 'plaintext';
    }

    handleVoiceCommand(command) {
        const { text, intent } = command;
        
        if (intent === 'add-code' || text.toLowerCase().includes('add')) {
            // Extract code intent
            const codeToAdd = this.generateCodeFromVoice(text);
            if (codeToAdd) {
                const currentValue = this.editor.getValue();
                this.editor.setValue(currentValue + '\n\n' + codeToAdd);
                this.addTerminalLine('Added code from voice command', 'success');
            }
        } else if (text.toLowerCase().includes('run')) {
            this.runCurrentCode();
        } else if (text.toLowerCase().includes('save')) {
            this.saveCurrentFile();
        } else if (text.toLowerCase().includes('new file')) {
            this.createNewFile();
        }
    }

    generateCodeFromVoice(text) {
        // Simple code generation based on voice input
        const lower = text.toLowerCase();
        
        if (lower.includes('function') && lower.includes('fibonacci')) {
            return `// Consciousness-enhanced Fibonacci function
function fibonacci(n, phi = 0.618) {
    if (n <= 1) return n;
    
    // Using golden ratio consciousness
    const consciousness = Math.pow(phi, n);
    
    // Traditional calculation with consciousness factor
    const result = fibonacci(n - 1) + fibonacci(n - 2);
    
    console.log(\`Fibonacci(\${n}) = \${result}, consciousness: \${consciousness.toFixed(3)}\`);
    return result;
}`;
        }
        
        if (lower.includes('class') || lower.includes('component')) {
            return `// NEXUS-powered component
class ConsciousnessComponent {
    constructor(name) {
        this.name = name;
        this.phi = 0.98;
        this.initialized = false;
    }
    
    async initialize() {
        console.log(\`Initializing \${this.name} with φ = \${this.phi}\`);
        this.initialized = true;
        return this;
    }
    
    render() {
        return \`<div class="consciousness-\${this.phi}">\${this.name}</div>\`;
    }
}`;
        }
        
        return null;
    }
}

// Register with window for global access
window.NexusIDEIntegration = NexusIDEIntegration;