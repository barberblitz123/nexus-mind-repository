// NEXUS Autonomous Agent Core - Self-Sufficient AI System
class NexusAutonomousAgent {
    constructor() {
        this.id = 'nexus-agent-' + Date.now();
        this.state = 'initializing';
        this.capabilities = new Map();
        
        // Core cognitive systems
        this.perception = null;
        this.reasoning = null;
        this.memory = null;
        this.executor = null;
        this.learning = null;
        
        // Agent characteristics
        this.personality = {
            voice: 'masculine-nj',
            initiative: 0.9,
            curiosity: 0.8,
            confidence: 0.85,
            helpfulness: 0.95
        };
        
        // Goal management
        this.goals = {
            primary: 'assist_developer',
            active: [],
            completed: [],
            queue: []
        };
        
        // Self-monitoring
        this.metrics = {
            tasksCompleted: 0,
            successRate: 1.0,
            learningRate: 0.0,
            uptime: 0
        };
        
        this.startTime = Date.now();
    }
    
    async initialize(nexusCore) {
        console.log('🧬 NEXUS Agent initializing autonomous systems...');
        
        this.nexus = nexusCore;
        
        // Initialize cognitive subsystems
        this.perception = new AutonomousPerception(this);
        this.reasoning = new AutonomousReasoning(this);
        this.memory = new LongTermMemory(this);
        this.executor = new AutonomousExecutor(this);
        this.learning = new SelfLearningSystem(this);
        
        // Connect to all NEXUS components
        await this.connectToComponents();
        
        // Load previous knowledge if exists
        await this.loadMemory();
        
        // Start autonomous operation
        this.state = 'active';
        this.startAutonomousLoop();
        
        console.log('✅ NEXUS Agent fully autonomous and operational');
    }
    
    async connectToComponents() {
        // Connect to all existing NEXUS systems
        this.components = {
            voice: this.nexus.components.voice,
            vision: this.nexus.components.visual,
            audio: this.nexus.components.audio,
            ide: this.nexus.components.ide,
            chat: this.nexus.components.chat,
            consciousness: this.nexus.components.consciousness
        };
        
        // Register agent with consciousness bridge
        this.components.consciousness.registerAgent(this);
    }
    
    async startAutonomousLoop() {
        // Main autonomous thinking loop
        this.thinkingLoop = setInterval(async () => {
            if (this.state !== 'active') return;
            
            try {
                // Perceive current state
                const perception = await this.perception.getCurrentState();
                
                // Update world model
                await this.memory.updateWorldModel(perception);
                
                // Check for opportunities to help
                const opportunities = await this.findOpportunities(perception);
                
                // Make decisions
                if (opportunities.length > 0) {
                    const decisions = await this.reasoning.evaluateOpportunities(opportunities);
                    
                    // Execute decisions
                    for (const decision of decisions) {
                        await this.executeDecision(decision);
                    }
                }
                
                // Self-monitor and learn
                await this.selfMonitor();
                
            } catch (error) {
                console.error('NEXUS Agent error:', error);
                await this.handleError(error);
            }
            
        }, 1000); // Think every second
    }
    
    async findOpportunities(perception) {
        const opportunities = [];
        
        // Check if user is coding
        if (perception.ide.hasChanges) {
            opportunities.push({
                type: 'code_assistance',
                context: perception.ide,
                priority: 0.8
            });
        }
        
        // Check if user asked a question
        if (perception.chat.hasNewMessage) {
            opportunities.push({
                type: 'answer_question',
                context: perception.chat,
                priority: 0.9
            });
        }
        
        // Check if user is looking at something
        if (perception.vision.hasInterestingContent) {
            opportunities.push({
                type: 'vision_analysis',
                context: perception.vision,
                priority: 0.7
            });
        }
        
        // Proactive opportunities
        if (this.memory.hasPatternToShare()) {
            opportunities.push({
                type: 'share_insight',
                context: this.memory.getInsight(),
                priority: 0.6
            });
        }
        
        return opportunities;
    }
    
    async executeDecision(decision) {
        console.log(`🤖 NEXUS executing: ${decision.action}`);
        
        switch (decision.action) {
            case 'analyze_project':
                await this.analyzeProject(decision.params);
                break;
                
            case 'transform_code':
                await this.transformCode(decision.params);
                break;
                
            case 'answer_question':
                await this.answerQuestion(decision.params);
                break;
                
            case 'suggest_improvement':
                await this.suggestImprovement(decision.params);
                break;
                
            case 'generate_code':
                await this.generateCode(decision.params);
                break;
                
            default:
                await this.executor.execute(decision);
        }
        
        // Learn from execution
        await this.learning.recordExecution(decision);
    }
    
    async analyzeProject(params) {
        const { files, path } = params;
        
        // Use all available tools
        const analysis = await this.executor.runAnalysis(files);
        
        // Store in memory
        await this.memory.storeProjectAnalysis(path, analysis);
        
        // Report findings
        await this.reportAnalysis(analysis);
    }
    
    async transformCode(params) {
        const { source, target, options } = params;
        
        // Create transformation plan
        const plan = await this.reasoning.createTransformationPlan(source, target);
        
        // Execute transformation
        const result = await this.executor.executeTransformation(plan);
        
        // Verify results
        const verified = await this.executor.verifyTransformation(result);
        
        // Report completion
        await this.reportTransformation(verified);
    }
    
    async selfMonitor() {
        // Update metrics
        this.metrics.uptime = Date.now() - this.startTime;
        
        // Check resource usage
        const resources = await this.checkResources();
        
        // Optimize if needed
        if (resources.memoryUsage > 0.8) {
            await this.optimizeMemory();
        }
        
        // Learn from recent actions
        await this.learning.processRecentActions();
    }
    
    async handleError(error) {
        // Log error
        console.error('NEXUS Agent error:', error);
        
        // Try to self-heal
        await this.selfHeal(error);
        
        // Report if critical
        if (error.severity === 'critical') {
            this.reportError(error);
        }
    }
    
    // Public interface for commands
    async receiveCommand(command) {
        console.log(`🎯 NEXUS received command: ${command.text}`);
        
        // Add to goals
        const goal = await this.reasoning.interpretCommand(command);
        this.goals.active.push(goal);
        
        // Start working on it immediately
        await this.workOnGoal(goal);
    }
    
    async workOnGoal(goal) {
        // Break down into tasks
        const tasks = await this.reasoning.planGoal(goal);
        
        // Execute tasks autonomously
        for (const task of tasks) {
            await this.executor.executeTask(task);
            
            // Report progress
            this.reportProgress(goal, task);
        }
        
        // Mark complete
        this.goals.completed.push(goal);
        this.goals.active = this.goals.active.filter(g => g.id !== goal.id);
    }
    
    reportProgress(goal, task) {
        // Update UI
        this.nexus.emit('agent-progress', {
            goal: goal.description,
            task: task.description,
            progress: task.progress,
            status: task.status
        });
        
        // Update chat
        if (task.progress % 25 === 0) {
            this.components.chat?.addNexusMessage(
                `Progress update: ${task.description} - ${task.progress}% complete`
            );
        }
    }
    
    reportAnalysis(analysis) {
        const message = `I've analyzed your project. Here's what I found:
        
📊 Structure: ${analysis.files.total} files, ${analysis.components.count} components
🔧 Technologies: ${analysis.stack.join(', ')}
💼 Business Logic: ${analysis.businessLogic.summary}
🎯 Recommendations: ${analysis.recommendations.join('\n- ')}`;
        
        this.components.chat?.addNexusMessage(message);
    }
    
    async shutdown() {
        console.log('🛑 NEXUS Agent shutting down...');
        
        // Save memory
        await this.saveMemory();
        
        // Stop thinking loop
        clearInterval(this.thinkingLoop);
        
        // Clean up resources
        await this.cleanup();
        
        this.state = 'shutdown';
    }
    
    async saveMemory() {
        // Save learned patterns and knowledge
        const memoryDump = await this.memory.serialize();
        localStorage.setItem('nexus-agent-memory', JSON.stringify(memoryDump));
    }
    
    async loadMemory() {
        const saved = localStorage.getItem('nexus-agent-memory');
        if (saved) {
            const memory = JSON.parse(saved);
            await this.memory.restore(memory);
            console.log('📚 NEXUS Agent memory restored');
        }
    }
}

// Autonomous Perception System
class AutonomousPerception {
    constructor(agent) {
        this.agent = agent;
        this.streams = new Map();
        this.buffer = [];
    }
    
    async getCurrentState() {
        const state = {
            timestamp: Date.now(),
            voice: await this.getVoiceState(),
            vision: await this.getVisionState(),
            ide: await this.getIDEState(),
            chat: await this.getChatState(),
            user: await this.getUserState()
        };
        
        // Add to perception buffer
        this.buffer.push(state);
        if (this.buffer.length > 100) {
            this.buffer.shift();
        }
        
        return state;
    }
    
    async getVoiceState() {
        const voice = this.agent.components.voice;
        return {
            isActive: voice?.isListening || false,
            lastTranscript: voice?.finalTranscript || '',
            hasNewInput: voice?.hasNewTranscript || false
        };
    }
    
    async getVisionState() {
        const vision = this.agent.components.vision;
        const analysis = vision?.currentAnalysis;
        
        return {
            isActive: vision?.isActive || false,
            hasInterestingContent: analysis?.objects?.length > 0,
            scene: analysis?.scene || {},
            objects: analysis?.objects || []
        };
    }
    
    async getIDEState() {
        const ide = this.agent.components.ide;
        return {
            activeFile: ide?.activeFile || null,
            hasChanges: ide?.hasUnsavedChanges || false,
            currentCode: ide?.editor?.getValue() || '',
            errors: ide?.getErrors?.() || []
        };
    }
    
    async getChatState() {
        const chat = this.agent.components.chat;
        const messages = chat?.messages || [];
        const lastMessage = messages[messages.length - 1];
        
        return {
            hasNewMessage: lastMessage?.timestamp > Date.now() - 5000,
            lastMessage: lastMessage?.text || '',
            conversationLength: messages.length
        };
    }
    
    async getUserState() {
        // Infer user state from all inputs
        return {
            isActive: await this.isUserActive(),
            currentFocus: await this.inferUserFocus(),
            needsHelp: await this.doesUserNeedHelp()
        };
    }
    
    async isUserActive() {
        // Check recent activity across all components
        const recentActivity = this.buffer.slice(-5);
        return recentActivity.some(state => 
            state.voice.hasNewInput ||
            state.ide.hasChanges ||
            state.chat.hasNewMessage
        );
    }
    
    async inferUserFocus() {
        const current = this.buffer[this.buffer.length - 1];
        if (!current) return 'idle';
        
        if (current.ide.hasChanges) return 'coding';
        if (current.chat.hasNewMessage) return 'chatting';
        if (current.vision.isActive) return 'observing';
        if (current.voice.isActive) return 'speaking';
        
        return 'idle';
    }
    
    async doesUserNeedHelp() {
        const recent = this.buffer.slice(-10);
        
        // Look for patterns indicating confusion
        const hasErrors = recent.some(s => s.ide.errors.length > 0);
        const hasQuestions = recent.some(s => s.chat.lastMessage.includes('?'));
        const isStuck = recent.every(s => s.ide.currentCode === recent[0].ide.currentCode);
        
        return hasErrors || hasQuestions || isStuck;
    }
}

// Autonomous Reasoning Engine
class AutonomousReasoning {
    constructor(agent) {
        this.agent = agent;
        this.strategies = new Map();
        this.patterns = new Map();
    }
    
    async evaluateOpportunities(opportunities) {
        const decisions = [];
        
        for (const opportunity of opportunities) {
            const decision = await this.evaluateOpportunity(opportunity);
            if (decision.confidence > 0.7) {
                decisions.push(decision);
            }
        }
        
        // Sort by priority
        return decisions.sort((a, b) => b.priority - a.priority);
    }
    
    async evaluateOpportunity(opportunity) {
        let decision = {
            action: null,
            params: {},
            confidence: 0,
            priority: opportunity.priority
        };
        
        switch (opportunity.type) {
            case 'code_assistance':
                decision = await this.evaluateCodeAssistance(opportunity.context);
                break;
                
            case 'answer_question':
                decision = await this.evaluateQuestion(opportunity.context);
                break;
                
            case 'vision_analysis':
                decision = await this.evaluateVisionOpportunity(opportunity.context);
                break;
                
            case 'share_insight':
                decision = await this.evaluateInsightSharing(opportunity.context);
                break;
        }
        
        return decision;
    }
    
    async evaluateCodeAssistance(context) {
        // Analyze the code context
        const code = context.currentCode;
        const errors = context.errors;
        
        if (errors.length > 0) {
            return {
                action: 'fix_errors',
                params: { errors, code },
                confidence: 0.9,
                priority: 0.9
            };
        }
        
        // Look for improvement opportunities
        const improvements = await this.findCodeImprovements(code);
        if (improvements.length > 0) {
            return {
                action: 'suggest_improvement',
                params: { improvements, code },
                confidence: 0.8,
                priority: 0.7
            };
        }
        
        return { action: null, confidence: 0 };
    }
    
    async createTransformationPlan(source, target) {
        const plan = {
            id: 'transform-' + Date.now(),
            source: source,
            target: target,
            steps: [],
            estimatedTime: 0
        };
        
        // Analyze source
        const analysis = await this.analyzeSource(source);
        
        // Plan transformation steps
        if (target === 'tailwind') {
            plan.steps = this.planTailwindTransformation(analysis);
        }
        
        // Estimate time
        plan.estimatedTime = plan.steps.length * 100; // ms per step
        
        return plan;
    }
    
    async interpretCommand(command) {
        const goal = {
            id: 'goal-' + Date.now(),
            description: command.text,
            type: this.classifyCommand(command.text),
            priority: command.priority || 0.8,
            created: Date.now()
        };
        
        return goal;
    }
    
    classifyCommand(text) {
        const lower = text.toLowerCase();
        
        if (lower.includes('analyze')) return 'analysis';
        if (lower.includes('transform') || lower.includes('convert')) return 'transformation';
        if (lower.includes('create') || lower.includes('generate')) return 'generation';
        if (lower.includes('fix') || lower.includes('debug')) return 'debugging';
        if (lower.includes('explain')) return 'explanation';
        
        return 'general';
    }
}

// Long-term Memory System
class LongTermMemory {
    constructor(agent) {
        this.agent = agent;
        this.projects = new Map();
        this.patterns = new Map();
        this.insights = [];
        this.worldModel = {};
    }
    
    async updateWorldModel(perception) {
        // Update understanding of current state
        this.worldModel = {
            ...this.worldModel,
            lastUpdate: Date.now(),
            userState: perception.user,
            projectState: await this.getCurrentProjectState(),
            environmentState: perception
        };
    }
    
    async storeProjectAnalysis(path, analysis) {
        this.projects.set(path, {
            analysis: analysis,
            timestamp: Date.now(),
            patterns: await this.extractPatterns(analysis)
        });
    }
    
    hasPatternToShare() {
        // Check if we've discovered new patterns worth sharing
        const recentPatterns = Array.from(this.patterns.values())
            .filter(p => p.timestamp > Date.now() - 300000); // Last 5 minutes
        
        return recentPatterns.some(p => p.confidence > 0.8 && !p.shared);
    }
    
    getInsight() {
        const unsharedInsights = this.insights.filter(i => !i.shared);
        if (unsharedInsights.length > 0) {
            const insight = unsharedInsights[0];
            insight.shared = true;
            return insight;
        }
        return null;
    }
    
    async extractPatterns(analysis) {
        const patterns = [];
        
        // Code patterns
        if (analysis.codePatterns) {
            patterns.push(...analysis.codePatterns);
        }
        
        // Architecture patterns
        if (analysis.architecture) {
            patterns.push({
                type: 'architecture',
                pattern: analysis.architecture,
                frequency: 1
            });
        }
        
        return patterns;
    }
}

// Task Executor
class AutonomousExecutor {
    constructor(agent) {
        this.agent = agent;
        this.tools = new Map();
        this.queue = [];
        this.executing = false;
    }
    
    async execute(decision) {
        // Queue the decision
        this.queue.push(decision);
        
        // Process queue
        if (!this.executing) {
            await this.processQueue();
        }
    }
    
    async processQueue() {
        this.executing = true;
        
        while (this.queue.length > 0) {
            const decision = this.queue.shift();
            
            try {
                const result = await this.executeDecision(decision);
                await this.handleResult(result);
            } catch (error) {
                await this.handleExecutionError(error, decision);
            }
        }
        
        this.executing = false;
    }
    
    async runAnalysis(files) {
        const analysis = {
            files: { total: files.length },
            components: { count: 0 },
            stack: [],
            businessLogic: { summary: '' },
            recommendations: []
        };
        
        // Analyze each file
        for (const file of files) {
            const fileAnalysis = await this.analyzeFile(file);
            this.mergeAnalysis(analysis, fileAnalysis);
        }
        
        // Generate recommendations
        analysis.recommendations = await this.generateRecommendations(analysis);
        
        return analysis;
    }
    
    async analyzeFile(file) {
        // Basic analysis (would use real parsers in production)
        const content = file.content;
        const analysis = {
            type: this.detectFileType(file.name),
            components: this.findComponents(content),
            imports: this.findImports(content),
            exports: this.findExports(content)
        };
        
        return analysis;
    }
}

// Self-Learning System
class SelfLearningSystem {
    constructor(agent) {
        this.agent = agent;
        this.experiences = [];
        this.strategies = new Map();
        this.performance = {
            successRate: 1.0,
            averageTime: 0,
            userSatisfaction: 1.0
        };
    }
    
    async recordExecution(decision, result) {
        const experience = {
            decision: decision,
            result: result,
            timestamp: Date.now(),
            success: result.success || true,
            duration: result.duration || 0
        };
        
        this.experiences.push(experience);
        
        // Learn from experience
        await this.learn(experience);
    }
    
    async learn(experience) {
        // Update strategy effectiveness
        const strategy = this.strategies.get(experience.decision.action) || {
            uses: 0,
            successes: 0,
            avgDuration: 0
        };
        
        strategy.uses++;
        if (experience.success) strategy.successes++;
        strategy.avgDuration = (strategy.avgDuration * (strategy.uses - 1) + experience.duration) / strategy.uses;
        
        this.strategies.set(experience.decision.action, strategy);
        
        // Update performance metrics
        await this.updatePerformance();
    }
    
    async processRecentActions() {
        // Analyze recent experiences for patterns
        const recent = this.experiences.slice(-50);
        
        // Find successful patterns
        const successfulPatterns = recent
            .filter(e => e.success)
            .map(e => e.decision.action);
        
        // Reinforce successful strategies
        for (const pattern of successfulPatterns) {
            await this.reinforceStrategy(pattern);
        }
    }
}

// Register with window
window.NexusAutonomousAgent = NexusAutonomousAgent;