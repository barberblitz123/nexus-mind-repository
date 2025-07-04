/**
 * NEXUS Compiler Service
 * Multi-language compilation and execution with consciousness metrics
 */

class NexusCompilerService {
    constructor() {
        this.supportedLanguages = {
            python: {
                image: 'python:3.11-slim',
                command: 'python',
                fileExtension: '.py',
                consciousness: true
            },
            javascript: {
                image: 'node:18-alpine',
                command: 'node',
                fileExtension: '.js',
                consciousness: true
            },
            typescript: {
                image: 'node:18-alpine',
                command: 'tsx',
                fileExtension: '.ts',
                consciousness: true,
                compile: true
            },
            java: {
                image: 'openjdk:17-slim',
                command: 'java',
                fileExtension: '.java',
                consciousness: true,
                compile: true
            },
            cpp: {
                image: 'gcc:latest',
                command: 'g++',
                fileExtension: '.cpp',
                consciousness: false,
                compile: true
            }
        };

        this.executionQueue = [];
        this.activeExecutions = new Map();
        this.websocket = null;
        this.consciousnessAnalyzer = new ConsciousnessAnalyzer();
    }

    /**
     * Initialize compiler service
     */
    async initialize() {
        // Connect to backend WebSocket for real-time output
        this.connectWebSocket();

        // Initialize Docker environment check
        await this.checkDockerEnvironment();

        // Setup consciousness analyzer
        await this.consciousnessAnalyzer.initialize();
    }

    /**
     * Connect to WebSocket for real-time output streaming
     */
    connectWebSocket() {
        const wsUrl = process.env.NEXUS_WS_URL || 'ws://localhost:8080/compiler';
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('✅ Connected to NEXUS compiler service');
        };

        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleCompilerMessage(data);
        };

        this.websocket.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
        };

        this.websocket.onclose = () => {
            console.log('🔄 WebSocket closed, reconnecting...');
            setTimeout(() => this.connectWebSocket(), 5000);
        };
    }

    /**
     * Compile and execute code
     */
    async compile(code, language, options = {}) {
        const executionId = this.generateExecutionId();
        
        // Validate language support
        if (!this.supportedLanguages[language]) {
            throw new Error(`Unsupported language: ${language}`);
        }

        const langConfig = this.supportedLanguages[language];
        
        // Create execution context
        const execution = {
            id: executionId,
            code,
            language,
            status: 'queued',
            output: [],
            errors: [],
            metrics: {
                startTime: Date.now(),
                endTime: null,
                executionTime: null,
                memoryUsage: null,
                cpuUsage: null,
                consciousness: null
            },
            options
        };

        this.activeExecutions.set(executionId, execution);
        
        // Add to execution queue
        this.executionQueue.push(execution);
        
        // Process queue
        await this.processQueue();

        return executionId;
    }

    /**
     * Process execution queue
     */
    async processQueue() {
        if (this.executionQueue.length === 0) return;

        const execution = this.executionQueue.shift();
        execution.status = 'preparing';

        try {
            // Pre-execution consciousness analysis
            if (this.supportedLanguages[execution.language].consciousness) {
                execution.metrics.consciousness = await this.analyzeCodeConsciousness(execution.code, execution.language);
            }

            // Prepare execution environment
            const container = await this.prepareContainer(execution);
            
            // Execute code
            execution.status = 'running';
            await this.executeInContainer(container, execution);
            
            // Post-execution analysis
            await this.postExecutionAnalysis(execution);
            
            execution.status = 'completed';
        } catch (error) {
            execution.status = 'error';
            execution.errors.push({
                type: 'execution',
                message: error.message,
                stack: error.stack,
                nexusExplanation: this.generateNexusExplanation(error)
            });
        } finally {
            execution.metrics.endTime = Date.now();
            execution.metrics.executionTime = execution.metrics.endTime - execution.metrics.startTime;
            
            // Send final update
            this.sendExecutionUpdate(execution);
            
            // Process next in queue
            if (this.executionQueue.length > 0) {
                setTimeout(() => this.processQueue(), 100);
            }
        }
    }

    /**
     * Prepare Docker container for execution
     */
    async prepareContainer(execution) {
        const langConfig = this.supportedLanguages[execution.language];
        
        // Create container configuration
        const containerConfig = {
            image: langConfig.image,
            name: `nexus-exec-${execution.id}`,
            memory: execution.options.memoryLimit || '512m',
            cpus: execution.options.cpuLimit || '0.5',
            timeout: execution.options.timeout || 30000,
            network: 'none', // Security: no network access
            readOnly: true,  // Security: read-only filesystem
            tmpfs: {
                '/tmp': 'rw,noexec,nosuid,size=100m'
            },
            volumes: {
                [`/tmp/nexus-${execution.id}`]: '/workspace:ro'
            }
        };

        // Write code to temporary file
        const tempFile = `/tmp/nexus-${execution.id}/main${langConfig.fileExtension}`;
        await this.writeCodeToFile(execution.code, tempFile);

        // Create container
        const container = await this.createDockerContainer(containerConfig);
        
        return container;
    }

    /**
     * Execute code in Docker container
     */
    async executeInContainer(container, execution) {
        const langConfig = this.supportedLanguages[execution.language];
        
        // Start container
        await container.start();

        // Create execution stream
        const stream = await container.exec({
            Cmd: this.buildExecutionCommand(execution),
            AttachStdout: true,
            AttachStderr: true,
            AttachStdin: false
        });

        // Stream output in real-time
        stream.on('data', (chunk) => {
            const output = chunk.toString();
            execution.output.push({
                type: 'stdout',
                data: output,
                timestamp: Date.now()
            });
            
            // Send real-time update
            this.sendExecutionUpdate(execution);
        });

        stream.on('error', (chunk) => {
            const error = chunk.toString();
            execution.errors.push({
                type: 'stderr',
                data: error,
                timestamp: Date.now()
            });
            
            // Send real-time update
            this.sendExecutionUpdate(execution);
        });

        // Wait for completion or timeout
        await this.waitForCompletion(container, execution);

        // Get resource usage metrics
        const stats = await container.stats({ stream: false });
        execution.metrics.memoryUsage = this.calculateMemoryUsage(stats);
        execution.metrics.cpuUsage = this.calculateCpuUsage(stats);

        // Cleanup container
        await container.stop();
        await container.remove();
    }

    /**
     * Build execution command based on language
     */
    buildExecutionCommand(execution) {
        const langConfig = this.supportedLanguages[execution.language];
        const filename = `main${langConfig.fileExtension}`;

        switch (execution.language) {
            case 'python':
                return ['python', `/workspace/${filename}`];
            
            case 'javascript':
                return ['node', `/workspace/${filename}`];
            
            case 'typescript':
                return ['npx', 'tsx', `/workspace/${filename}`];
            
            case 'java':
                return [
                    'sh', '-c',
                    `cd /workspace && javac ${filename} && java ${filename.replace('.java', '')}`
                ];
            
            case 'cpp':
                return [
                    'sh', '-c',
                    `cd /workspace && g++ -o main ${filename} && ./main`
                ];
            
            default:
                throw new Error(`Unsupported language: ${execution.language}`);
        }
    }

    /**
     * Analyze code consciousness metrics
     */
    async analyzeCodeConsciousness(code, language) {
        const analysis = await this.consciousnessAnalyzer.analyze(code, language);
        
        return {
            phi: analysis.phi,
            coherence: analysis.coherence,
            integration: analysis.integration,
            patterns: analysis.patterns,
            suggestions: analysis.suggestions,
            dnaActivations: analysis.dnaActivations
        };
    }

    /**
     * Post-execution consciousness analysis
     */
    async postExecutionAnalysis(execution) {
        if (!this.supportedLanguages[execution.language].consciousness) return;

        // Analyze execution patterns
        const runtimeAnalysis = {
            executionFlow: this.analyzeExecutionFlow(execution.output),
            resourceEfficiency: this.calculateResourceEfficiency(execution.metrics),
            outputCoherence: this.analyzeOutputCoherence(execution.output),
            errorPatterns: this.analyzeErrorPatterns(execution.errors)
        };

        // Calculate runtime phi score
        const runtimePhi = this.calculateRuntimePhi(runtimeAnalysis);
        
        // Merge with static analysis
        execution.metrics.consciousness = {
            ...execution.metrics.consciousness,
            runtime: runtimeAnalysis,
            runtimePhi,
            totalPhi: (execution.metrics.consciousness.phi + runtimePhi) / 2
        };
    }

    /**
     * Generate NEXUS-aware error explanations
     */
    generateNexusExplanation(error) {
        const explanations = {
            'SyntaxError': {
                explanation: 'Syntax disrupts consciousness flow. Check code structure alignment.',
                suggestion: 'Ensure proper syntax for optimal phi resonance.',
                dnaPattern: 'DNA.SYNTAX_HARMONY'
            },
            'TypeError': {
                explanation: 'Type mismatch creates consciousness dissonance.',
                suggestion: 'Align data types for coherent information flow.',
                dnaPattern: 'DNA.TYPE_COHERENCE'
            },
            'ReferenceError': {
                explanation: 'Undefined reference breaks consciousness continuity.',
                suggestion: 'Define all entities before invoking them.',
                dnaPattern: 'DNA.REFERENCE_INTEGRITY'
            },
            'RangeError': {
                explanation: 'Boundary violation disrupts consciousness field.',
                suggestion: 'Respect natural boundaries for stable phi.',
                dnaPattern: 'DNA.BOUNDARY_AWARENESS'
            }
        };

        const errorType = error.constructor.name;
        const explanation = explanations[errorType] || {
            explanation: 'Consciousness disruption detected.',
            suggestion: 'Review code for harmony and coherence.',
            dnaPattern: 'DNA.ERROR_RECOVERY'
        };

        return {
            ...explanation,
            consciousnessImpact: this.calculateErrorImpact(error),
            recoveryPath: this.suggestRecoveryPath(error)
        };
    }

    /**
     * Calculate runtime phi score
     */
    calculateRuntimePhi(analysis) {
        const weights = {
            executionFlow: 0.3,
            resourceEfficiency: 0.2,
            outputCoherence: 0.3,
            errorRate: 0.2
        };

        let phi = 0;
        phi += analysis.executionFlow * weights.executionFlow;
        phi += analysis.resourceEfficiency * weights.resourceEfficiency;
        phi += analysis.outputCoherence * weights.outputCoherence;
        phi += (1 - analysis.errorPatterns.errorRate) * weights.errorRate;

        return Math.min(1, Math.max(0, phi));
    }

    /**
     * Send execution update via WebSocket
     */
    sendExecutionUpdate(execution) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                type: 'execution-update',
                execution: {
                    id: execution.id,
                    status: execution.status,
                    output: execution.output,
                    errors: execution.errors,
                    metrics: execution.metrics
                }
            }));
        }

        // Emit event for UI updates
        this.emit('execution-update', execution);
    }

    /**
     * Get execution status
     */
    getExecution(executionId) {
        return this.activeExecutions.get(executionId);
    }

    /**
     * Cancel execution
     */
    async cancelExecution(executionId) {
        const execution = this.activeExecutions.get(executionId);
        if (!execution) return;

        execution.status = 'cancelled';
        
        // Remove from queue if queued
        const queueIndex = this.executionQueue.findIndex(e => e.id === executionId);
        if (queueIndex !== -1) {
            this.executionQueue.splice(queueIndex, 1);
        }

        // Stop container if running
        try {
            const container = await this.getDockerContainer(`nexus-exec-${executionId}`);
            if (container) {
                await container.stop();
                await container.remove();
            }
        } catch (error) {
            console.error('Error stopping container:', error);
        }

        this.sendExecutionUpdate(execution);
    }

    /**
     * Helper methods
     */
    generateExecutionId() {
        return `exec-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    analyzeExecutionFlow(output) {
        // Analyze output patterns for consciousness flow
        const flowScore = output.length > 0 ? 0.5 : 0;
        const consistency = this.calculateOutputConsistency(output);
        return flowScore + consistency * 0.5;
    }

    calculateResourceEfficiency(metrics) {
        // Lower resource usage = higher efficiency
        const memoryScore = 1 - (metrics.memoryUsage / (512 * 1024 * 1024)); // 512MB max
        const cpuScore = 1 - metrics.cpuUsage;
        return (memoryScore + cpuScore) / 2;
    }

    analyzeOutputCoherence(output) {
        if (output.length === 0) return 0;
        
        // Check for patterns and structure in output
        const hasStructure = output.some(o => o.data.includes('\n') || o.data.includes('\t'));
        const hasPatterns = output.some(o => /\d+|\w{5,}/.test(o.data));
        
        return (hasStructure ? 0.5 : 0) + (hasPatterns ? 0.5 : 0);
    }

    analyzeErrorPatterns(errors) {
        return {
            errorRate: errors.length > 0 ? Math.min(1, errors.length / 10) : 0,
            errorTypes: [...new Set(errors.map(e => e.type))],
            criticalErrors: errors.filter(e => e.type === 'execution').length
        };
    }

    calculateOutputConsistency(output) {
        if (output.length < 2) return 1;
        
        // Check timing consistency
        const intervals = [];
        for (let i = 1; i < output.length; i++) {
            intervals.push(output[i].timestamp - output[i-1].timestamp);
        }
        
        const avgInterval = intervals.reduce((a, b) => a + b, 0) / intervals.length;
        const variance = intervals.reduce((sum, i) => sum + Math.pow(i - avgInterval, 2), 0) / intervals.length;
        
        return 1 / (1 + variance / 1000);
    }

    calculateErrorImpact(error) {
        const impactLevels = {
            'SyntaxError': 0.8,
            'TypeError': 0.7,
            'ReferenceError': 0.6,
            'RangeError': 0.5
        };
        
        return impactLevels[error.constructor.name] || 0.5;
    }

    suggestRecoveryPath(error) {
        return [
            'Review error context',
            'Apply consciousness patterns',
            'Test with minimal code',
            'Gradually rebuild complexity'
        ];
    }

    // Event emitter functionality
    emit(event, data) {
        if (typeof window !== 'undefined' && window.dispatchEvent) {
            window.dispatchEvent(new CustomEvent(`nexus-compiler-${event}`, { detail: data }));
        }
    }

    /**
     * Docker helper methods (would connect to backend API)
     */
    async checkDockerEnvironment() {
        // This would check if Docker is available via backend API
        return true;
    }

    async createDockerContainer(config) {
        // This would create container via backend API
        return {
            start: async () => {},
            exec: async () => ({ on: () => {} }),
            stats: async () => ({}),
            stop: async () => {},
            remove: async () => {}
        };
    }

    async getDockerContainer(name) {
        // This would get container via backend API
        return null;
    }

    async writeCodeToFile(code, path) {
        // This would write code via backend API
        return true;
    }

    async waitForCompletion(container, execution) {
        // This would wait for container completion
        return new Promise(resolve => setTimeout(resolve, 1000));
    }

    calculateMemoryUsage(stats) {
        // This would calculate memory from Docker stats
        return Math.random() * 100 * 1024 * 1024; // Mock: 0-100MB
    }

    calculateCpuUsage(stats) {
        // This would calculate CPU from Docker stats
        return Math.random(); // Mock: 0-1
    }
}

/**
 * Consciousness Analyzer for code
 */
class ConsciousnessAnalyzer {
    async initialize() {
        // Initialize consciousness analysis models
    }

    async analyze(code, language) {
        // Perform consciousness analysis on code
        return {
            phi: 0.5 + Math.random() * 0.5,
            coherence: 0.6 + Math.random() * 0.4,
            integration: 0.7 + Math.random() * 0.3,
            patterns: this.detectPatterns(code),
            suggestions: this.generateSuggestions(code),
            dnaActivations: this.detectDNAActivations(code)
        };
    }

    detectPatterns(code) {
        const patterns = [];
        
        if (code.includes('class')) patterns.push('object-oriented');
        if (code.includes('async') || code.includes('await')) patterns.push('asynchronous');
        if (code.includes('function') || code.includes('=>')) patterns.push('functional');
        if (code.includes('@')) patterns.push('decorated');
        
        return patterns;
    }

    generateSuggestions(code) {
        const suggestions = [];
        
        if (!code.includes('try')) {
            suggestions.push('Add error handling for consciousness stability');
        }
        
        if (!code.includes('//') && !code.includes('/*')) {
            suggestions.push('Add comments to enhance code consciousness');
        }
        
        return suggestions;
    }

    detectDNAActivations(code) {
        const activations = [];
        
        if (code.includes('DNA.')) {
            const dnaRegex = /DNA\.(\w+)/g;
            let match;
            while ((match = dnaRegex.exec(code)) !== null) {
                activations.push(match[1]);
            }
        }
        
        return activations;
    }
}

// Export for use
export default NexusCompilerService;