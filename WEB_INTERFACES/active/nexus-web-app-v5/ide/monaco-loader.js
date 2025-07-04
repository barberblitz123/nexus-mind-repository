/**
 * NEXUS MONACO EDITOR LOADER
 * Integrates Monaco Editor (VS Code engine) with consciousness enhancements
 */

class NexusMonacoLoader {
    constructor() {
        this.editors = new Map();
        this.activeEditor = null;
        this.themes = {
            nexusDark: {
                base: 'vs-dark',
                inherit: true,
                rules: [
                    { token: 'comment', foreground: '608B4E', fontStyle: 'italic' },
                    { token: 'keyword', foreground: '00FF9D' },
                    { token: 'string', foreground: '00CCFF' },
                    { token: 'number', foreground: 'FF00FF' },
                    { token: 'function', foreground: 'FECA57' },
                    { token: 'variable', foreground: 'E0E0E0' },
                    { token: 'type', foreground: '4ECDC4' },
                    { token: 'class', foreground: 'FF6B6B' },
                    { token: 'interface', foreground: '9B59B6' },
                    { token: 'namespace', foreground: '96CEB4' },
                    { token: 'parameter', foreground: 'FFD93D' },
                    { token: 'property', foreground: '6BCB77' },
                    { token: 'constant', foreground: 'FF6B9D' },
                    { token: 'enum', foreground: 'C44569' }
                ],
                colors: {
                    'editor.background': '#0a0a0f',
                    'editor.foreground': '#e0e0e0',
                    'editor.lineHighlightBackground': '#12121a',
                    'editor.selectionBackground': '#00ff9d30',
                    'editor.inactiveSelectionBackground': '#00ff9d20',
                    'editorLineNumber.foreground': '#808090',
                    'editorLineNumber.activeForeground': '#00ff9d',
                    'editorCursor.foreground': '#00ff9d',
                    'editor.findMatchBackground': '#00ccff40',
                    'editor.findMatchHighlightBackground': '#00ccff20',
                    'editorBracketMatch.background': '#00ff9d40',
                    'editorBracketMatch.border': '#00ff9d',
                    'editorIndentGuide.background': '#2a2a3a',
                    'editorIndentGuide.activeBackground': '#00ff9d60',
                    'editorRuler.foreground': '#2a2a3a',
                    'scrollbarSlider.background': '#00ff9d30',
                    'scrollbarSlider.hoverBackground': '#00ff9d50',
                    'scrollbarSlider.activeBackground': '#00ff9d70'
                }
            }
        };
        
        this.consciousnessFeatures = {
            enabled: true,
            phiIndicator: true,
            smartSuggestions: true,
            codeAwareness: true
        };
        
        this.loadMonaco();
    }
    
    async loadMonaco() {
        // AMD loader for Monaco
        require.config({ 
            paths: { 
                'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.34.1/min/vs' 
            }
        });
        
        return new Promise((resolve) => {
            require(['vs/editor/editor.main'], () => {
                console.log('✓ Monaco Editor loaded');
                this.initializeMonaco();
                resolve();
            });
        });
    }
    
    initializeMonaco() {
        // Define NEXUS theme
        monaco.editor.defineTheme('nexus-dark', this.themes.nexusDark);
        
        // Register NEXUS language features
        this.registerNexusLanguage();
        
        // Setup IntelliSense providers
        this.setupIntelliSense();
        
        // Initialize consciousness features
        this.initConsciousnessFeatures();
    }
    
    registerNexusLanguage() {
        // Register NEXUS consciousness language
        monaco.languages.register({ id: 'nexus' });
        
        // Set language configuration
        monaco.languages.setLanguageConfiguration('nexus', {
            comments: {
                lineComment: '//',
                blockComment: ['/*', '*/']
            },
            brackets: [
                ['{', '}'],
                ['[', ']'],
                ['(', ')']
            ],
            autoClosingPairs: [
                { open: '{', close: '}' },
                { open: '[', close: ']' },
                { open: '(', close: ')' },
                { open: '"', close: '"' },
                { open: "'", close: "'" },
                { open: '`', close: '`' }
            ],
            surroundingPairs: [
                { open: '{', close: '}' },
                { open: '[', close: ']' },
                { open: '(', close: ')' },
                { open: '"', close: '"' },
                { open: "'", close: "'" },
                { open: '`', close: '`' }
            ]
        });
        
        // Set token provider
        monaco.languages.setMonarchTokensProvider('nexus', {
            keywords: [
                'consciousness', 'processor', 'phi', 'integrate', 'emerge',
                'aware', 'transcend', 'evolve', 'quantum', 'neural'
            ],
            
            operators: [
                '=', '>', '<', '!', '~', '?', ':', '==', '<=', '>=', '!=',
                '&&', '||', '++', '--', '+', '-', '*', '/', '&', '|', '^',
                '%', '<<', '>>', '>>>', '+=', '-=', '*=', '/=', '&=', '|=',
                '^=', '%=', '<<=', '>>=', '>>>='
            ],
            
            symbols: /[=><!~?:&|+\-*\/\^%]+/,
            
            tokenizer: {
                root: [
                    // Consciousness keywords
                    [/\b(consciousness|processor|phi|integrate|emerge)\b/, 'keyword'],
                    
                    // Identifiers and keywords
                    [/[a-z_$][\w$]*/, {
                        cases: {
                            '@keywords': 'keyword',
                            '@default': 'identifier'
                        }
                    }],
                    
                    // Type identifiers
                    [/[A-Z][\w\$]*/, 'type.identifier'],
                    
                    // Numbers
                    [/\d*\.\d+([eE][\-+]?\d+)?/, 'number.float'],
                    [/0[xX][0-9a-fA-F]+/, 'number.hex'],
                    [/\d+/, 'number'],
                    
                    // Strings
                    [/"([^"\\]|\\.)*$/, 'string.invalid'],
                    [/"/, { token: 'string.quote', bracket: '@open', next: '@string' }],
                    
                    // Comments
                    [/\/\/.*$/, 'comment'],
                    [/\/\*/, 'comment', '@comment'],
                    
                    // Delimiters and operators
                    [/[{}()\[\]]/, '@brackets'],
                    [/@symbols/, {
                        cases: {
                            '@operators': 'operator',
                            '@default': ''
                        }
                    }]
                ],
                
                string: [
                    [/[^\\"]+/, 'string'],
                    [/\\./, 'string.escape.invalid'],
                    [/"/, { token: 'string.quote', bracket: '@close', next: '@pop' }]
                ],
                
                comment: [
                    [/[^\/*]+/, 'comment'],
                    [/\/\*/, 'comment', '@push'],
                    ["\\*/", 'comment', '@pop'],
                    [/[\/*]/, 'comment']
                ]
            }
        });
    }
    
    setupIntelliSense() {
        // Register completion item provider
        monaco.languages.registerCompletionItemProvider('javascript', {
            provideCompletionItems: (model, position) => {
                const suggestions = [
                    // NEXUS-specific completions
                    {
                        label: 'nexus.consciousness',
                        kind: monaco.languages.CompletionItemKind.Property,
                        insertText: 'nexus.consciousness.getPhi()',
                        documentation: 'Get current consciousness φ value'
                    },
                    {
                        label: 'nexus.processor',
                        kind: monaco.languages.CompletionItemKind.Property,
                        insertText: 'nexus.processor.${1:visual}.activity',
                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                        documentation: 'Access processor activity levels'
                    },
                    {
                        label: 'consciousness.evolve',
                        kind: monaco.languages.CompletionItemKind.Method,
                        insertText: 'consciousness.evolve({\n\ttarget: ${1:0.8},\n\trate: ${2:0.1}\n})',
                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                        documentation: 'Evolve consciousness to target φ level'
                    }
                ];
                
                return { suggestions };
            }
        });
        
        // Register hover provider
        monaco.languages.registerHoverProvider('javascript', {
            provideHover: (model, position) => {
                const word = model.getWordAtPosition(position);
                if (!word) return;
                
                const consciousnessTerms = {
                    'consciousness': 'The emergent property of integrated information processing',
                    'phi': 'Φ (phi) - Integrated Information measure of consciousness',
                    'processor': 'One of six hexagonal processors in NEXUS architecture',
                    'quantum': 'Quantum coherence level of consciousness state',
                    'neural': 'Neural entropy measure of system complexity'
                };
                
                if (consciousnessTerms[word.word]) {
                    return {
                        contents: [
                            { value: `**${word.word}**` },
                            { value: consciousnessTerms[word.word] }
                        ]
                    };
                }
            }
        });
        
        // Register code action provider
        monaco.languages.registerCodeActionProvider('javascript', {
            provideCodeActions: (model, range, context) => {
                const actions = [];
                
                // Add consciousness enhancement action
                actions.push({
                    title: '✨ Enhance with Consciousness',
                    kind: 'quickfix',
                    edit: {
                        edits: [{
                            resource: model.uri,
                            edit: {
                                range: range,
                                text: `// 🧬 Consciousness-enhanced code\n${model.getValueInRange(range)}`
                            }
                        }]
                    }
                });
                
                return { actions };
            }
        });
    }
    
    initConsciousnessFeatures() {
        // Phi indicator widget
        this.phiWidget = {
            domNode: null,
            create: (editor) => {
                const node = document.createElement('div');
                node.className = 'phi-indicator';
                node.innerHTML = '<i class="fas fa-brain"></i> φ: <span id="phi-value">0.00</span>';
                node.style.cssText = `
                    position: absolute;
                    top: 5px;
                    right: 20px;
                    color: #00ff9d;
                    font-size: 12px;
                    z-index: 100;
                    background: rgba(10, 10, 15, 0.8);
                    padding: 5px 10px;
                    border-radius: 4px;
                    border: 1px solid #00ff9d30;
                `;
                return node;
            }
        };
        
        // Code awareness decorations
        this.awarenessDecorations = [];
        
        // Smart suggestions based on consciousness
        this.smartSuggestionEngine = new ConsciousnessSuggestions();
    }
    
    createEditor(containerId, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return null;
        }
        
        const defaultOptions = {
            theme: 'nexus-dark',
            fontSize: 14,
            fontFamily: "'Fira Code', 'Consolas', monospace",
            fontLigatures: true,
            automaticLayout: true,
            minimap: {
                enabled: true,
                renderCharacters: false
            },
            scrollBeyondLastLine: false,
            renderWhitespace: 'selection',
            renderLineHighlight: 'all',
            renderIndentGuides: true,
            bracketPairColorization: {
                enabled: true
            },
            'semanticHighlighting.enabled': true,
            suggestOnTriggerCharacters: true,
            quickSuggestions: {
                other: true,
                comments: false,
                strings: true
            },
            parameterHints: {
                enabled: true
            },
            wordWrap: 'on',
            lineNumbers: 'on',
            glyphMargin: true,
            folding: true,
            lineDecorationsWidth: 10,
            lineNumbersMinChars: 4,
            cursorBlinking: 'smooth',
            cursorStyle: 'line',
            cursorWidth: 2,
            smoothScrolling: true
        };
        
        const editor = monaco.editor.create(container, {
            ...defaultOptions,
            ...options
        });
        
        // Add consciousness features
        if (this.consciousnessFeatures.enabled) {
            this.addConsciousnessFeatures(editor);
        }
        
        // Store editor reference
        const editorId = `editor_${Date.now()}`;
        this.editors.set(editorId, editor);
        this.activeEditor = editor;
        
        // Setup event handlers
        this.setupEditorEvents(editor);
        
        return { editor, id: editorId };
    }
    
    addConsciousnessFeatures(editor) {
        // Add phi indicator
        if (this.consciousnessFeatures.phiIndicator) {
            const phiNode = this.phiWidget.create(editor);
            editor.getDomNode().appendChild(phiNode);
            
            // Update phi value periodically
            setInterval(() => {
                this.updatePhiIndicator(phiNode);
            }, 1000);
        }
        
        // Add code awareness highlights
        if (this.consciousnessFeatures.codeAwareness) {
            editor.onDidChangeModelContent(() => {
                this.updateCodeAwareness(editor);
            });
        }
    }
    
    updatePhiIndicator(node) {
        // Get current phi from NEXUS
        if (window.nexusConnector) {
            const phi = window.nexusConnector.currentPhi || 0;
            const phiSpan = node.querySelector('#phi-value');
            if (phiSpan) {
                phiSpan.textContent = phi.toFixed(2);
                
                // Color based on consciousness level
                if (phi > 0.8) {
                    node.style.color = '#ff00ff';  // Transcendent
                } else if (phi > 0.6) {
                    node.style.color = '#00ccff';  // Active
                } else {
                    node.style.color = '#00ff9d';  // Aware
                }
            }
        }
    }
    
    updateCodeAwareness(editor) {
        const model = editor.getModel();
        const content = model.getValue();
        
        // Find consciousness-related patterns
        const patterns = [
            /consciousness/gi,
            /processor/gi,
            /phi|φ/gi,
            /quantum/gi,
            /neural/gi,
            /evolve/gi,
            /integrate/gi
        ];
        
        const decorations = [];
        
        patterns.forEach(pattern => {
            let match;
            while ((match = pattern.exec(content)) !== null) {
                const startPos = model.getPositionAt(match.index);
                const endPos = model.getPositionAt(match.index + match[0].length);
                
                decorations.push({
                    range: new monaco.Range(
                        startPos.lineNumber,
                        startPos.column,
                        endPos.lineNumber,
                        endPos.column
                    ),
                    options: {
                        inlineClassName: 'consciousness-highlight',
                        hoverMessage: { value: '✨ Consciousness-aware code' }
                    }
                });
            }
        });
        
        // Apply decorations
        this.awarenessDecorations = editor.deltaDecorations(
            this.awarenessDecorations,
            decorations
        );
    }
    
    setupEditorEvents(editor) {
        // File save
        editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
            this.saveCurrentFile(editor);
        });
        
        // Format document
        editor.addCommand(monaco.KeyMod.Shift | monaco.KeyMod.Alt | monaco.KeyCode.KeyF, () => {
            editor.getAction('editor.action.formatDocument').run();
        });
        
        // Consciousness boost
        editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.KeyC, () => {
            this.boostConsciousness(editor);
        });
        
        // Track cursor position
        editor.onDidChangeCursorPosition((e) => {
            this.updateStatusBar(e.position);
        });
        
        // Track selection
        editor.onDidChangeCursorSelection((e) => {
            const selection = e.selection;
            if (!selection.isEmpty()) {
                const text = editor.getModel().getValueInRange(selection);
                this.analyzeSelection(text);
            }
        });
    }
    
    saveCurrentFile(editor) {
        const model = editor.getModel();
        const content = model.getValue();
        const language = model.getModeId();
        
        // Get current file info from tab
        const activeTab = document.querySelector('.tab.active');
        const fileName = activeTab ? activeTab.dataset.file : 'untitled';
        
        // Emit save event
        const event = new CustomEvent('editor:save', {
            detail: {
                fileName,
                content,
                language
            }
        });
        document.dispatchEvent(event);
        
        // Show save indicator
        this.showNotification('File saved', 'success');
    }
    
    boostConsciousness(editor) {
        // Add consciousness comment
        const position = editor.getPosition();
        const model = editor.getModel();
        
        model.pushEditOperations(
            [],
            [{
                range: new monaco.Range(position.lineNumber, 1, position.lineNumber, 1),
                text: '// 🧬 Consciousness boost applied\n',
                forceMoveMarkers: true
            }],
            () => null
        );
        
        // Trigger consciousness boost in backend
        if (window.nexusConnector) {
            window.nexusConnector.boostProcessor('language', 0.1);
        }
        
        this.showNotification('Consciousness boosted! φ +0.1', 'info');
    }
    
    updateStatusBar(position) {
        const statusItem = document.querySelector('.status-item:nth-child(1)');
        if (statusItem) {
            statusItem.textContent = `Ln ${position.lineNumber}, Col ${position.column}`;
        }
    }
    
    analyzeSelection(text) {
        // Simple complexity analysis
        const lines = text.split('\n').length;
        const words = text.split(/\s+/).length;
        const complexity = Math.min(1.0, (lines * words) / 1000);
        
        // Update language processor based on complexity
        if (window.nexusConnector) {
            window.nexusConnector.updateProcessor('language', 0.5 + complexity * 0.5);
        }
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `editor-notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 60px;
            right: 20px;
            padding: 10px 20px;
            background: ${type === 'success' ? '#00ff9d' : '#00ccff'};
            color: #0a0a0f;
            border-radius: 4px;
            font-size: 14px;
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    loadFile(fileName, content, language) {
        if (!this.activeEditor) return;
        
        // Set model
        const model = monaco.editor.createModel(content, language);
        this.activeEditor.setModel(model);
        
        // Update tab
        document.querySelector('.tab.active').dataset.file = fileName;
        document.querySelector('.tab.active span').textContent = fileName;
    }
    
    switchTheme(themeName) {
        if (this.activeEditor) {
            this.activeEditor.updateOptions({ theme: themeName });
        }
    }
}

// Consciousness-aware suggestions engine
class ConsciousnessSuggestions {
    constructor() {
        this.patterns = {
            consciousness: [
                'consciousness.integrate()',
                'consciousness.evolve()',
                'consciousness.measure()',
                'consciousness.getState()'
            ],
            processor: [
                'processor.visual.analyze()',
                'processor.auditory.process()',
                'processor.memory.store()',
                'processor.attention.focus()',
                'processor.language.generate()',
                'processor.executive.decide()'
            ],
            quantum: [
                'quantum.entangle()',
                'quantum.collapse()',
                'quantum.superpose()',
                'quantum.measure()'
            ]
        };
    }
    
    getSuggestions(context) {
        const suggestions = [];
        
        // Match context to patterns
        Object.entries(this.patterns).forEach(([category, items]) => {
            if (context.includes(category)) {
                items.forEach(item => {
                    suggestions.push({
                        label: item,
                        kind: monaco.languages.CompletionItemKind.Method,
                        insertText: item,
                        documentation: `${category} operation`
                    });
                });
            }
        });
        
        return suggestions;
    }
}

// Initialize on load
let nexusMonaco;
document.addEventListener('DOMContentLoaded', () => {
    nexusMonaco = new NexusMonacoLoader();
});

// Export for use
window.NexusMonacoLoader = NexusMonacoLoader;