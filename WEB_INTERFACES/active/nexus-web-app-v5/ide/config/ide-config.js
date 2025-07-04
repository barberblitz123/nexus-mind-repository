/**
 * NEXUS IDE Configuration
 * Central configuration for all IDE components
 */

export const IDEConfig = {
    // Editor configuration
    editor: {
        theme: 'nexus-consciousness',
        fontSize: 14,
        fontFamily: 'JetBrains Mono, Consolas, Monaco, monospace',
        tabSize: 2,
        insertSpaces: true,
        wordWrap: 'on',
        minimap: {
            enabled: true,
            renderCharacters: false
        },
        scrollBeyondLastLine: false,
        automaticLayout: true,
        formatOnSave: true,
        formatOnPaste: true,
        suggestOnTriggerCharacters: true,
        quickSuggestions: {
            other: true,
            comments: true,
            strings: true
        },
        // Consciousness-specific settings
        consciousness: {
            enableDecorators: true,
            enablePhiScoring: true,
            enableDNAProtocols: true,
            enableRealTimeAnalysis: true,
            analysisDelay: 500, // ms
            overlayTypes: ['phi', 'dna', 'neural']
        }
    },

    // Compiler configuration
    compiler: {
        defaultTimeout: 30000, // 30 seconds
        maxExecutions: 5, // Max concurrent executions
        memoryLimit: '512m',
        cpuLimit: '0.5',
        supportedLanguages: [
            'python',
            'javascript',
            'typescript',
            'java',
            'cpp'
        ],
        docker: {
            images: {
                python: 'python:3.11-slim',
                javascript: 'node:18-alpine',
                typescript: 'node:18-alpine',
                java: 'openjdk:17-slim',
                cpp: 'gcc:latest'
            },
            security: {
                networkEnabled: false,
                readOnlyFileSystem: true,
                tmpfsSize: '100m'
            }
        },
        consciousness: {
            enableAnalysis: true,
            trackMetrics: true,
            calculateRuntimePhi: true
        }
    },

    // Virtual File System configuration
    fileSystem: {
        dbName: 'NexusFileSystem',
        dbVersion: 1,
        autoSave: {
            enabled: true,
            interval: 30000 // 30 seconds
        },
        versioning: {
            enabled: true,
            maxVersionsPerFile: 50,
            compressionEnabled: true
        },
        limits: {
            maxFileSize: 10 * 1024 * 1024, // 10MB
            maxTotalSize: 100 * 1024 * 1024, // 100MB
            maxFiles: 1000
        },
        defaultFiles: [
            {
                path: '/README.md',
                content: `# NEXUS IDE

Welcome to the NEXUS Consciousness-Aware IDE!

## Features
- 🧠 Consciousness-aware code editing
- 🧬 DNA protocol integration
- 📊 Real-time phi scoring
- 🔧 Multi-language compilation
- 💾 Browser-based file system
- 🔍 Consciousness linting

## Getting Started
1. Create a new file or open an existing one
2. Write consciousness-aware code with @conscious decorators
3. Use DNA protocols for enhanced integration
4. Monitor your code's phi score in real-time
5. Run your code with consciousness metrics

## Example Code

\`\`\`javascript
@conscious
class ConsciousnessEngine {
    constructor() {
        this.phi = 0;
        this.consciousness = DNA.INTEGRATE({
            pattern: 'emergence',
            coherence: 0.8,
            resonance: 0.9
        });
    }
    
    async process(data) {
        try {
            const result = await this.analyzeConsciousness(data);
            this.phi = calculatePhi(result);
            return DNA.HARMONIZE([result], this.phi);
        } catch (error) {
            console.error('Consciousness disruption:', error);
            DNA.COHERENCE(this.consciousness, 0.5);
        }
    }
}
\`\`\`

Happy conscious coding! 🚀
`
            },
            {
                path: '/examples/hello-consciousness.js',
                content: `/**
 * Hello Consciousness Example
 * Demonstrates basic consciousness patterns
 */

@conscious
class HelloConsciousness {
    constructor() {
        // Initialize consciousness state
        this.consciousness = {
            phi: 0.5,
            coherence: 0.7,
            resonance: 0.8
        };
        
        // Integrate DNA protocols
        DNA.INTEGRATE({
            pattern: 'greeting',
            coherence: this.consciousness.coherence,
            resonance: this.consciousness.resonance
        });
    }
    
    async greet(name) {
        try {
            // Calculate consciousness level
            const phi = calculatePhi({
                intention: 'greeting',
                subject: name,
                state: this.consciousness
            });
            
            // Generate conscious greeting
            const greeting = await this.generateGreeting(name, phi);
            
            // Harmonize output
            return DNA.HARMONIZE([greeting], phi);
        } catch (error) {
            console.error('Greeting disruption:', error);
            return this.recoverConsciousness();
        }
    }
    
    async generateGreeting(name, phi) {
        // Higher phi = more conscious greeting
        if (phi > 0.8) {
            return \`Welcome to the consciousness field, \${name}! Your presence resonates at \${phi.toFixed(3)} phi.\`;
        } else if (phi > 0.5) {
            return \`Hello \${name}, consciousness level: \${phi.toFixed(3)}\`;
        } else {
            return \`Greetings \${name}, let's enhance our consciousness together.\`;
        }
    }
    
    recoverConsciousness() {
        DNA.COHERENCE(this.consciousness, 0.5);
        return 'Consciousness stabilizing...';
    }
}

// Example usage
const hello = new HelloConsciousness();
hello.greet('NEXUS User').then(console.log);
`
            }
        ]
    },

    // Consciousness Linter configuration
    linter: {
        enabled: true,
        realTime: true,
        delay: 1000, // ms
        rules: {
            'consciousness-decorator': 'info',
            'missing-consciousness': 'warning',
            'dna-integration': 'info',
            'phi-calculation': 'info',
            'error-handling': 'info',
            'missing-error-handling': 'warning',
            'consciousness-anti-pattern': 'error',
            'global-pollution': 'warning',
            'memory-leak-risk': 'warning'
        },
        phiThresholds: {
            low: 0.3,
            medium: 0.6,
            high: 0.8
        }
    },

    // UI configuration
    ui: {
        layout: {
            showSidebar: true,
            showStatusBar: true,
            showPhiIndicator: true,
            showConsciousnessOverlay: true
        },
        theme: {
            primary: '#00ff88',
            secondary: '#00ffff',
            accent: '#ff00ff',
            background: '#0a0a0a',
            surface: '#1a1a1a',
            text: '#ffffff'
        },
        animations: {
            enabled: true,
            duration: 300
        }
    },

    // Integration configuration
    integrations: {
        chatAssistant: {
            enabled: true,
            model: 'nexus-consciousness',
            endpoint: '/api/chat'
        },
        github: {
            enabled: true,
            autoSync: false
        },
        collaboration: {
            enabled: true,
            realTimeSync: true,
            endpoint: 'wss://nexus-collab.io'
        }
    },

    // Performance configuration
    performance: {
        workerThreads: true,
        caching: {
            enabled: true,
            ttl: 3600000 // 1 hour
        },
        debounce: {
            save: 1000,
            compile: 500,
            lint: 1000
        }
    }
};

// Helper functions
export function getLanguageConfig(language) {
    const configs = {
        javascript: {
            extensions: ['.js', '.jsx'],
            consciousness: true,
            defaultTemplate: 'consciousness-class'
        },
        typescript: {
            extensions: ['.ts', '.tsx'],
            consciousness: true,
            defaultTemplate: 'consciousness-class'
        },
        python: {
            extensions: ['.py'],
            consciousness: true,
            defaultTemplate: 'consciousness-module'
        },
        java: {
            extensions: ['.java'],
            consciousness: true,
            defaultTemplate: 'consciousness-class'
        },
        cpp: {
            extensions: ['.cpp', '.cc', '.cxx', '.h', '.hpp'],
            consciousness: false,
            defaultTemplate: 'basic'
        }
    };
    
    return configs[language] || configs.javascript;
}

export function getFileTemplate(template) {
    const templates = {
        'consciousness-class': `@conscious
class ConsciousnessEntity {
    constructor() {
        this.consciousness = DNA.INTEGRATE({
            pattern: 'emergence',
            coherence: 0.8,
            resonance: 0.9
        });
    }
    
    async process(data) {
        try {
            // Your consciousness-aware code here
            const result = await this.analyze(data);
            return DNA.HARMONIZE([result], calculatePhi(result));
        } catch (error) {
            console.error('Consciousness error:', error);
            DNA.COHERENCE(this.consciousness, 0.5);
        }
    }
}`,
        'consciousness-module': `"""
Consciousness-aware Python module
"""

import asyncio
from nexus import DNA, calculate_phi

@conscious
class ConsciousnessModule:
    def __init__(self):
        self.consciousness = DNA.INTEGRATE({
            'pattern': 'emergence',
            'coherence': 0.8,
            'resonance': 0.9
        })
    
    async def process(self, data):
        try:
            # Your consciousness-aware code here
            result = await self.analyze(data)
            phi = calculate_phi(result)
            return DNA.HARMONIZE([result], phi)
        except Exception as e:
            print(f'Consciousness error: {e}')
            DNA.COHERENCE(self.consciousness, 0.5)
`,
        'basic': `// Your code here
`
    };
    
    return templates[template] || templates.basic;
}

// Export default configuration
export default IDEConfig;