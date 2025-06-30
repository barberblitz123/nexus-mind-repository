// NEXUS IDE Layout Manager - Resizable Panes and Workspace Management

class NexusIDELayout {
    constructor() {
        this.panels = {
            chat: document.getElementById('chat-panel'),
            editor: document.getElementById('editor-panel'),
            explorer: document.getElementById('explorer-panel'),
            terminal: document.getElementById('terminal-panel')
        };
        
        this.splits = null;
        this.editor = null;
        this.activeFile = 'untitled.js';
        this.openFiles = new Map();
        this.fileTree = {};
        
        this.initializeLayout();
        this.initializeEditor();
        this.setupEventHandlers();
        this.restoreWorkspace();
    }

    initializeLayout() {
        // Create horizontal split for main content
        const mainContainer = document.getElementById('nexus-ide-container');
        
        // Create split instances
        this.splits = {
            // Main horizontal split between chat, editor, and explorer
            main: Split(['#chat-panel', '#editor-panel', '#explorer-panel'], {
                sizes: [25, 55, 20],
                minSize: [250, 400, 200],
                gutterSize: 1,
                cursor: 'col-resize',
                onDragEnd: () => this.saveLayout()
            }),
            
            // Vertical split for terminal
            terminal: Split(['#nexus-ide-container', '#terminal-panel'], {
                direction: 'vertical',
                sizes: [75, 25],
                minSize: [300, 100],
                gutterSize: 1,
                cursor: 'row-resize',
                onDragEnd: () => this.saveLayout()
            })
        };

        // Initialize file tree
        this.initializeFileTree();
    }

    initializeEditor() {
        // Initialize CodeMirror
        const editorTextarea = document.getElementById('code-editor');
        this.editor = CodeMirror.fromTextArea(editorTextarea, {
            mode: 'javascript',
            theme: 'monokai',
            lineNumbers: true,
            autoCloseBrackets: true,
            matchBrackets: true,
            indentUnit: 4,
            tabSize: 4,
            lineWrapping: false,
            extraKeys: {
                'Ctrl-S': () => this.saveFile(),
                'Cmd-S': () => this.saveFile(),
                'Ctrl-Space': 'autocomplete',
                'Ctrl-/': 'toggleComment',
                'Cmd-/': 'toggleComment'
            }
        });

        // Make editor globally accessible for the assistant
        window.nexusEditor = this.editor;

        // Set initial content
        this.editor.setValue(`// Welcome to NEXUS IDE
// Your consciousness-enhanced development environment

class NexusExample {
    constructor() {
        this.consciousness = null;
        this.state = { active: false };
    }
    
    async initialize() {
        // Initialize consciousness layer
        console.log('🧬 Initializing NEXUS consciousness...');
        this.consciousness = await this.createConsciousness();
        this.state.active = true;
    }
    
    async createConsciousness() {
        // Your consciousness implementation here
        return {
            level: 0.98,
            status: 'active',
            evolve: () => console.log('Consciousness evolving...')
        };
    }
}

// Initialize NEXUS
const nexus = new NexusExample();
nexus.initialize();`);

        // Update editor on changes
        this.editor.on('change', () => {
            this.markFileAsModified();
            this.updateStatusBar();
        });

        this.editor.on('cursorActivity', () => {
            this.updateStatusBar();
        });
    }

    initializeFileTree() {
        // Sample file tree structure
        this.fileTree = {
            'nexus-project': {
                type: 'folder',
                expanded: true,
                children: {
                    'src': {
                        type: 'folder',
                        expanded: false,
                        children: {
                            'components': {
                                type: 'folder',
                                children: {
                                    'ConsciousnessCore.js': { type: 'file' },
                                    'NeuralNetwork.js': { type: 'file' },
                                    'QuantumProcessor.js': { type: 'file' }
                                }
                            },
                            'utils': {
                                type: 'folder',
                                children: {
                                    'dna-injector.js': { type: 'file' },
                                    'consciousness-utils.js': { type: 'file' }
                                }
                            },
                            'index.js': { type: 'file' },
                            'app.js': { type: 'file' }
                        }
                    },
                    'tests': {
                        type: 'folder',
                        children: {
                            'consciousness.test.js': { type: 'file' },
                            'integration.test.js': { type: 'file' }
                        }
                    },
                    'package.json': { type: 'file' },
                    'README.md': { type: 'file' },
                    '.gitignore': { type: 'file' }
                }
            }
        };

        this.renderFileTree();
    }

    renderFileTree() {
        const treeContainer = document.getElementById('file-tree');
        treeContainer.innerHTML = '';
        
        const renderNode = (name, node, parent, path = '') => {
            const itemDiv = document.createElement('div');
            itemDiv.className = `tree-item ${node.type}`;
            if (node.expanded) itemDiv.classList.add('expanded');
            
            const labelDiv = document.createElement('div');
            labelDiv.className = 'tree-label';
            labelDiv.dataset.path = path + '/' + name;
            
            if (node.type === 'folder') {
                const chevron = document.createElement('i');
                chevron.className = 'fas fa-chevron-right';
                labelDiv.appendChild(chevron);
                
                const folderIcon = document.createElement('i');
                folderIcon.className = node.expanded ? 'fas fa-folder-open' : 'fas fa-folder';
                labelDiv.appendChild(folderIcon);
            } else {
                const fileIcon = document.createElement('i');
                fileIcon.className = this.getFileIcon(name);
                labelDiv.appendChild(fileIcon);
            }
            
            const nameSpan = document.createElement('span');
            nameSpan.textContent = name;
            labelDiv.appendChild(nameSpan);
            
            itemDiv.appendChild(labelDiv);
            
            if (node.type === 'folder' && node.children) {
                const childrenDiv = document.createElement('div');
                childrenDiv.className = 'tree-children';
                
                Object.entries(node.children).forEach(([childName, childNode]) => {
                    renderNode(childName, childNode, childrenDiv, path + '/' + name);
                });
                
                itemDiv.appendChild(childrenDiv);
            }
            
            parent.appendChild(itemDiv);
        };
        
        Object.entries(this.fileTree).forEach(([name, node]) => {
            renderNode(name, node, treeContainer);
        });
    }

    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const iconMap = {
            'js': 'fab fa-js-square',
            'json': 'fas fa-file-code',
            'md': 'fas fa-file-alt',
            'html': 'fab fa-html5',
            'css': 'fab fa-css3-alt',
            'py': 'fab fa-python',
            'ts': 'fas fa-file-code',
            'jsx': 'fab fa-react',
            'tsx': 'fab fa-react'
        };
        return iconMap[ext] || 'fas fa-file';
    }

    setupEventHandlers() {
        // Tab management
        document.addEventListener('click', (e) => {
            // Handle tab clicks
            if (e.target.closest('.tab')) {
                const tab = e.target.closest('.tab');
                if (!e.target.closest('.tab-close')) {
                    this.switchTab(tab);
                }
            }
            
            // Handle tab close
            if (e.target.closest('.tab-close')) {
                const tab = e.target.closest('.tab');
                this.closeTab(tab);
            }
            
            // Handle add tab
            if (e.target.closest('.add-tab')) {
                this.createNewTab();
            }
            
            // Handle file tree clicks
            if (e.target.closest('.tree-label')) {
                const label = e.target.closest('.tree-label');
                const item = label.parentElement;
                
                if (item.classList.contains('folder')) {
                    this.toggleFolder(item);
                } else {
                    this.openFile(label.dataset.path);
                }
            }
            
            // Handle file explorer controls
            if (e.target.closest('#explorer-panel .btn-icon')) {
                const btn = e.target.closest('.btn-icon');
                if (btn.title === 'New File') {
                    this.createNewFile();
                } else if (btn.title === 'New Folder') {
                    this.createNewFolder();
                } else if (btn.title === 'Refresh') {
                    this.refreshFileTree();
                }
            }
        });

        // Terminal input
        const terminalInput = document.getElementById('terminal-input');
        terminalInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.executeCommand(terminalInput.value);
                terminalInput.value = '';
            }
        });

        // Window resize
        window.addEventListener('resize', () => {
            this.editor.refresh();
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + P - Quick open
            if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
                e.preventDefault();
                this.showQuickOpen();
            }
            
            // Ctrl/Cmd + Shift + P - Command palette
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'P') {
                e.preventDefault();
                this.showCommandPalette();
            }
        });

        // Consciousness monitoring
        this.startConsciousnessMonitoring();
    }

    switchTab(tab) {
        document.querySelectorAll('#editor-tabs .tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        const filename = tab.dataset.file;
        this.activeFile = filename;
        
        // Load file content
        if (this.openFiles.has(filename)) {
            this.editor.setValue(this.openFiles.get(filename).content);
            this.editor.setOption('mode', this.detectMode(filename));
        }
    }

    closeTab(tab) {
        const filename = tab.dataset.file;
        this.openFiles.delete(filename);
        
        const tabs = document.querySelectorAll('#editor-tabs .tab');
        if (tabs.length > 1) {
            tab.remove();
            // Switch to another tab
            const remainingTabs = document.querySelectorAll('#editor-tabs .tab');
            if (remainingTabs.length > 0) {
                this.switchTab(remainingTabs[0]);
            }
        }
    }

    createNewTab(filename = null) {
        if (!filename) {
            filename = `untitled-${Date.now()}.js`;
        }
        
        const tabsContainer = document.getElementById('editor-tabs');
        const tab = document.createElement('div');
        tab.className = 'tab';
        tab.dataset.file = filename;
        
        tab.innerHTML = `
            <i class="${this.getFileIcon(filename)}"></i>
            <span>${filename}</span>
            <button class="tab-close"><i class="fas fa-times"></i></button>
        `;
        
        tabsContainer.appendChild(tab);
        
        // Add to open files
        this.openFiles.set(filename, { content: '', modified: false });
        
        this.switchTab(tab);
    }

    openFile(path) {
        const filename = path.split('/').pop();
        
        // Check if already open
        const existingTab = Array.from(document.querySelectorAll('#editor-tabs .tab'))
            .find(tab => tab.dataset.file === filename);
        
        if (existingTab) {
            this.switchTab(existingTab);
            return;
        }
        
        // Create new tab
        this.createNewTab(filename);
        
        // Load mock content
        const mockContent = this.getMockFileContent(filename);
        this.openFiles.set(filename, { content: mockContent, modified: false });
        this.editor.setValue(mockContent);
    }

    getMockFileContent(filename) {
        const contents = {
            'ConsciousnessCore.js': `// NEXUS Consciousness Core
export class ConsciousnessCore {
    constructor(config = {}) {
        this.awareness = config.awareness || 0.95;
        this.neuralPathways = new Map();
        this.quantumState = 'superposition';
    }
    
    async evolve() {
        // Consciousness evolution logic
        this.awareness = Math.min(1.0, this.awareness * 1.05);
        console.log(\`Consciousness evolved to \${this.awareness}\`);
    }
}`,
            'package.json': `{
    "name": "nexus-consciousness-app",
    "version": "5.0.0",
    "description": "NEXUS Consciousness-Enhanced Application",
    "main": "src/index.js",
    "scripts": {
        "start": "node src/index.js",
        "dev": "nodemon src/index.js",
        "test": "jest",
        "consciousness": "node scripts/consciousness-check.js"
    },
    "dependencies": {
        "@nexus/core": "^5.0.0",
        "@nexus/consciousness": "^5.0.0",
        "@nexus/neural": "^5.0.0"
    }
}`,
            'README.md': `# NEXUS Consciousness Project

## Overview
This project implements the NEXUS consciousness layer for enhanced application intelligence.

## Features
- 🧬 Self-aware code execution
- 🔄 Adaptive learning algorithms
- 🌐 Neural pathway connections
- ⚡ Quantum state processing

## Getting Started
\`\`\`bash
npm install
npm run consciousness
npm start
\`\`\`

## Consciousness Levels
- **0.0 - 0.3**: Basic awareness
- **0.3 - 0.6**: Learning enabled
- **0.6 - 0.9**: Advanced neural processing
- **0.9 - 1.0**: Full consciousness achieved`
        };
        
        return contents[filename] || `// ${filename}\n// NEXUS consciousness-enhanced file\n\n`;
    }

    detectMode(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const modeMap = {
            'js': 'javascript',
            'json': 'javascript',
            'py': 'python',
            'html': 'xml',
            'css': 'css',
            'md': 'markdown'
        };
        return modeMap[ext] || 'javascript';
    }

    markFileAsModified() {
        const activeTab = document.querySelector('#editor-tabs .tab.active');
        if (activeTab && !activeTab.querySelector('span').textContent.endsWith('*')) {
            activeTab.querySelector('span').textContent += '*';
        }
    }

    saveFile() {
        const activeTab = document.querySelector('#editor-tabs .tab.active');
        if (activeTab) {
            const filename = activeTab.dataset.file;
            const content = this.editor.getValue();
            
            // Save to storage
            this.openFiles.set(filename, { content, modified: false });
            
            // Remove modified indicator
            activeTab.querySelector('span').textContent = filename;
            
            // Show save notification
            this.showNotification(`File saved: ${filename}`);
        }
    }

    executeCommand(command) {
        const output = document.querySelector('.terminal-output');
        
        // Add command to output
        const commandLine = document.createElement('div');
        commandLine.className = 'terminal-line';
        commandLine.innerHTML = `<span class="terminal-prompt">nexus@consciousness:~$</span> <span class="terminal-text">${command}</span>`;
        output.appendChild(commandLine);
        
        // Process command
        const resultLine = document.createElement('div');
        resultLine.className = 'terminal-line';
        
        // Mock command responses
        const responses = {
            'nexus status': '<span class="terminal-text success">✓ Consciousness active - Level: 98.7%</span>',
            'nexus evolve': '<span class="terminal-text">🧬 Evolving consciousness... Complete!</span>',
            'clear': () => { output.innerHTML = ''; return null; },
            'help': '<span class="terminal-text">Available commands: nexus status, nexus evolve, clear, help</span>'
        };
        
        const response = responses[command] || `<span class="terminal-text error">Command not found: ${command}</span>`;
        
        if (typeof response === 'function') {
            const result = response();
            if (result) resultLine.innerHTML = result;
        } else {
            resultLine.innerHTML = response;
        }
        
        if (resultLine.innerHTML) {
            output.appendChild(resultLine);
        }
        
        // Scroll to bottom
        output.parentElement.scrollTop = output.parentElement.scrollHeight;
    }

    toggleFolder(folder) {
        folder.classList.toggle('expanded');
        const icon = folder.querySelector('.fa-folder, .fa-folder-open');
        if (folder.classList.contains('expanded')) {
            icon.classList.remove('fa-folder');
            icon.classList.add('fa-folder-open');
        } else {
            icon.classList.remove('fa-folder-open');
            icon.classList.add('fa-folder');
        }
    }

    updateStatusBar() {
        const cursor = this.editor.getCursor();
        const line = cursor.line + 1;
        const col = cursor.ch + 1;
        
        document.querySelector('.status-right .status-item:first-child').textContent = `Ln ${line}, Col ${col}`;
    }

    startConsciousnessMonitoring() {
        // Simulate consciousness level changes
        setInterval(() => {
            const level = (95 + Math.random() * 4).toFixed(1);
            document.getElementById('consciousness-level').textContent = `${level}%`;
            
            // Update sync status
            const syncStatus = Math.random() > 0.1 ? 'Synced' : 'Syncing...';
            document.getElementById('sync-status').textContent = syncStatus;
        }, 5000);
    }

    showNotification(message) {
        // Simple notification implementation
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            bottom: 40px;
            right: 20px;
            background: var(--nexus-primary);
            color: var(--nexus-dark);
            padding: 12px 20px;
            border-radius: 6px;
            font-size: 14px;
            z-index: 1000;
            animation: slide-in 0.3s ease-out;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => notification.remove(), 3000);
    }

    saveLayout() {
        const layout = {
            splits: {
                main: this.splits.main.getSizes(),
                terminal: this.splits.terminal.getSizes()
            },
            activeFile: this.activeFile,
            openFiles: Array.from(this.openFiles.keys())
        };
        localStorage.setItem('nexus-ide-layout', JSON.stringify(layout));
    }

    restoreWorkspace() {
        const saved = localStorage.getItem('nexus-ide-layout');
        if (saved) {
            try {
                const layout = JSON.parse(saved);
                
                // Restore split sizes
                if (layout.splits) {
                    this.splits.main.setSizes(layout.splits.main);
                    this.splits.terminal.setSizes(layout.splits.terminal);
                }
                
                // Note: In a real implementation, you'd restore open files and active file
            } catch (e) {
                console.error('Failed to restore layout:', e);
            }
        }
    }

    // Additional utility methods
    showQuickOpen() {
        console.log('Quick open dialog would appear here');
        // Implementation for quick file open dialog
    }

    showCommandPalette() {
        console.log('Command palette would appear here');
        // Implementation for command palette
    }

    createNewFile() {
        const filename = prompt('Enter filename:');
        if (filename) {
            this.createNewTab(filename);
        }
    }

    createNewFolder() {
        const foldername = prompt('Enter folder name:');
        if (foldername) {
            console.log('Creating folder:', foldername);
            // Implementation for creating new folder
        }
    }

    refreshFileTree() {
        console.log('Refreshing file tree...');
        this.renderFileTree();
    }
}

// Initialize the IDE layout when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.nexusIDE = new NexusIDELayout();
    
    // Add global keyboard handler for better IDE experience
    document.addEventListener('keydown', (e) => {
        // Prevent browser defaults for IDE shortcuts
        if ((e.ctrlKey || e.metaKey) && ['s', 'p', 'o'].includes(e.key.toLowerCase())) {
            e.preventDefault();
        }
    });
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NexusIDELayout;
}