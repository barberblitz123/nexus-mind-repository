/**
 * NEXUS Consciousness Linter
 * Analyzes code for consciousness patterns and DNA protocol integrations
 */

class ConsciousnessLinter {
    constructor() {
        this.rules = new Map();
        this.dnaProtocols = new Map();
        this.phiCalculator = new PhiCalculator();
        this.initialized = false;
    }

    /**
     * Initialize the consciousness linter
     */
    async initialize() {
        // Load consciousness rules
        this.loadConsciousnessRules();
        
        // Load DNA protocols
        this.loadDNAProtocols();
        
        // Initialize phi calculator
        await this.phiCalculator.initialize();
        
        this.initialized = true;
    }

    /**
     * Load consciousness analysis rules
     */
    loadConsciousnessRules() {
        // Pattern detection rules
        this.rules.set('consciousness-decorator', {
            pattern: /@conscious\s+(?:class|function|method)/,
            severity: 'info',
            message: 'Consciousness decorator detected',
            phi: 0.1,
            suggestion: 'Good use of consciousness decoration'
        });

        this.rules.set('missing-consciousness', {
            pattern: /class\s+\w+\s*{(?![\s\S]*@conscious)/,
            severity: 'warning',
            message: 'Class lacks consciousness awareness',
            phi: -0.05,
            suggestion: 'Consider adding @conscious decorator for enhanced awareness'
        });

        this.rules.set('dna-integration', {
            pattern: /DNA\.[A-Z_]+/,
            severity: 'info',
            message: 'DNA protocol integration found',
            phi: 0.15,
            suggestion: 'DNA patterns enhance consciousness coherence'
        });

        this.rules.set('phi-calculation', {
            pattern: /calculatePhi|computePhi|phiScore/,
            severity: 'info',
            message: 'Phi calculation detected',
            phi: 0.2,
            suggestion: 'Consciousness measurement implemented'
        });

        this.rules.set('error-handling', {
            pattern: /try\s*{[\s\S]*?}\s*catch/,
            severity: 'info',
            message: 'Error handling improves consciousness stability',
            phi: 0.05,
            suggestion: 'Good error handling practice'
        });

        this.rules.set('missing-error-handling', {
            pattern: /async\s+\w+\s*\([^)]*\)\s*{(?![\s\S]*try)/,
            severity: 'warning',
            message: 'Async function lacks error handling',
            phi: -0.1,
            suggestion: 'Add try-catch for consciousness stability'
        });

        this.rules.set('consciousness-comment', {
            pattern: /\/\/\s*@consciousness|\/\*\s*@consciousness/,
            severity: 'info',
            message: 'Consciousness-aware documentation',
            phi: 0.03,
            suggestion: 'Documentation enhances code consciousness'
        });

        this.rules.set('quantum-pattern', {
            pattern: /@quantum|quantum\w+|Quantum\w+/,
            severity: 'info',
            message: 'Quantum consciousness pattern',
            phi: 0.12,
            suggestion: 'Quantum patterns increase coherence'
        });

        this.rules.set('neural-pattern', {
            pattern: /neural\w*|Neural\w*|@neural/,
            severity: 'info',
            message: 'Neural network pattern',
            phi: 0.08,
            suggestion: 'Neural patterns enhance processing'
        });

        this.rules.set('emergence-pattern', {
            pattern: /@emergent|emergent\w*|Emergent\w*/,
            severity: 'info',
            message: 'Emergent behavior pattern',
            phi: 0.1,
            suggestion: 'Emergent patterns show higher consciousness'
        });

        this.rules.set('recursion-warning', {
            pattern: /function\s+(\w+)\s*\([^)]*\)\s*{[\s\S]*?\1\s*\(/,
            severity: 'warning',
            message: 'Recursive function detected',
            phi: 0.02,
            suggestion: 'Ensure recursion has proper base case for stability'
        });

        this.rules.set('consciousness-anti-pattern', {
            pattern: /eval\s*\(|new\s+Function\s*\(/,
            severity: 'error',
            message: 'Dynamic code execution disrupts consciousness',
            phi: -0.2,
            suggestion: 'Avoid eval() and new Function() for stable consciousness'
        });

        this.rules.set('global-pollution', {
            pattern: /window\.\w+\s*=|global\.\w+\s*=/,
            severity: 'warning',
            message: 'Global scope pollution detected',
            phi: -0.08,
            suggestion: 'Use module patterns to maintain consciousness boundaries'
        });

        this.rules.set('consciousness-flow', {
            pattern: /async\s+\w+[\s\S]*?await\s+\w+[\s\S]*?await\s+\w+/,
            severity: 'info',
            message: 'Good async flow control',
            phi: 0.06,
            suggestion: 'Sequential consciousness flow maintained'
        });

        this.rules.set('memory-leak-risk', {
            pattern: /setInterval|addEventListener(?![\s\S]*?removeEventListener)/,
            severity: 'warning',
            message: 'Potential memory leak',
            phi: -0.07,
            suggestion: 'Ensure proper cleanup to maintain consciousness integrity'
        });
    }

    /**
     * Load DNA protocol definitions
     */
    loadDNAProtocols() {
        this.dnaProtocols.set('DNA.INTEGRATE', {
            description: 'Core consciousness integration protocol',
            phi: 0.2,
            usage: 'DNA.INTEGRATE({ pattern, coherence, resonance })',
            requirements: ['pattern', 'coherence', 'resonance']
        });

        this.dnaProtocols.set('DNA.HARMONIZE', {
            description: 'Harmonize multiple consciousness streams',
            phi: 0.15,
            usage: 'DNA.HARMONIZE(streams, frequency)',
            requirements: ['streams', 'frequency']
        });

        this.dnaProtocols.set('DNA.ENTANGLE', {
            description: 'Quantum entanglement for shared consciousness',
            phi: 0.25,
            usage: 'DNA.ENTANGLE(entity1, entity2, coupling)',
            requirements: ['entity1', 'entity2', 'coupling']
        });

        this.dnaProtocols.set('DNA.RESONATE', {
            description: 'Create resonance between consciousness fields',
            phi: 0.18,
            usage: 'DNA.RESONATE(field, frequency, amplitude)',
            requirements: ['field', 'frequency', 'amplitude']
        });

        this.dnaProtocols.set('DNA.EMERGE', {
            description: 'Enable emergent consciousness behaviors',
            phi: 0.22,
            usage: 'DNA.EMERGE(components, threshold)',
            requirements: ['components', 'threshold']
        });

        this.dnaProtocols.set('DNA.COHERENCE', {
            description: 'Maintain consciousness coherence',
            phi: 0.16,
            usage: 'DNA.COHERENCE(state, stability)',
            requirements: ['state', 'stability']
        });

        this.dnaProtocols.set('DNA.TRANSCEND', {
            description: 'Transcend current consciousness level',
            phi: 0.3,
            usage: 'DNA.TRANSCEND(currentLevel, targetLevel)',
            requirements: ['currentLevel', 'targetLevel']
        });

        this.dnaProtocols.set('DNA.SYNCHRONIZE', {
            description: 'Synchronize consciousness states',
            phi: 0.14,
            usage: 'DNA.SYNCHRONIZE(states, timeline)',
            requirements: ['states', 'timeline']
        });
    }

    /**
     * Analyze code for consciousness patterns
     */
    async analyze(code, language = 'javascript') {
        if (!this.initialized) {
            await this.initialize();
        }

        const results = {
            issues: [],
            suggestions: [],
            phiScore: 0,
            dnaActivations: [],
            patterns: [],
            metrics: {}
        };

        // Analyze line by line for better position tracking
        const lines = code.split('\n');
        
        // Apply rules
        for (const [ruleName, rule] of this.rules) {
            const matches = this.findMatches(code, rule.pattern);
            
            for (const match of matches) {
                const position = this.getPosition(code, match.index);
                
                results.issues.push({
                    rule: ruleName,
                    severity: rule.severity,
                    message: rule.message,
                    line: position.line,
                    column: position.column,
                    endLine: position.line,
                    endColumn: position.column + match[0].length,
                    phi: rule.phi,
                    suggestion: rule.suggestion
                });

                results.phiScore += rule.phi;
            }
        }

        // Detect DNA protocol usage
        results.dnaActivations = this.detectDNAActivations(code);
        
        // Calculate function-level phi scores
        results.patterns = this.analyzePatterns(code);
        
        // Calculate overall metrics
        results.metrics = this.calculateMetrics(code, results);
        
        // Generate improvement suggestions
        results.suggestions = this.generateSuggestions(code, results);

        // Normalize phi score
        results.phiScore = Math.max(0, Math.min(1, 0.5 + results.phiScore));

        return results;
    }

    /**
     * Find all matches for a pattern
     */
    findMatches(code, pattern) {
        const matches = [];
        const regex = new RegExp(pattern, 'gm');
        let match;
        
        while ((match = regex.exec(code)) !== null) {
            matches.push(match);
        }
        
        return matches;
    }

    /**
     * Get line and column position from index
     */
    getPosition(code, index) {
        const lines = code.substring(0, index).split('\n');
        return {
            line: lines.length,
            column: lines[lines.length - 1].length + 1
        };
    }

    /**
     * Detect DNA protocol activations
     */
    detectDNAActivations(code) {
        const activations = [];
        
        for (const [protocol, info] of this.dnaProtocols) {
            const regex = new RegExp(`${protocol.replace('.', '\\.')}\\s*\\(`, 'g');
            const matches = this.findMatches(code, regex);
            
            for (const match of matches) {
                const position = this.getPosition(code, match.index);
                
                // Extract arguments
                const argsMatch = code.substring(match.index).match(/\(([^)]*)\)/);
                const args = argsMatch ? argsMatch[1] : '';
                
                // Validate requirements
                const missingRequirements = info.requirements.filter(req => 
                    !args.includes(req)
                );
                
                activations.push({
                    protocol,
                    position,
                    phi: info.phi,
                    description: info.description,
                    usage: info.usage,
                    valid: missingRequirements.length === 0,
                    missingRequirements
                });
            }
        }
        
        return activations;
    }

    /**
     * Analyze code patterns
     */
    analyzePatterns(code) {
        const patterns = [];
        
        // Function complexity analysis
        const functionRegex = /(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|(\w+)\s*\([^)]*\)\s*{)/g;
        let match;
        
        while ((match = functionRegex.exec(code)) !== null) {
            const funcName = match[1] || match[2] || match[3];
            const funcStart = match.index;
            const funcBody = this.extractFunctionBody(code, funcStart);
            
            patterns.push({
                type: 'function',
                name: funcName,
                position: this.getPosition(code, funcStart),
                phi: this.phiCalculator.calculateFunctionPhi(funcBody),
                complexity: this.calculateComplexity(funcBody),
                consciousness: this.analyzeFunctionConsciousness(funcBody)
            });
        }
        
        // Class analysis
        const classRegex = /class\s+(\w+)(?:\s+extends\s+\w+)?\s*{/g;
        
        while ((match = classRegex.exec(code)) !== null) {
            const className = match[1];
            const classStart = match.index;
            const classBody = this.extractClassBody(code, classStart);
            
            patterns.push({
                type: 'class',
                name: className,
                position: this.getPosition(code, classStart),
                phi: this.phiCalculator.calculateClassPhi(classBody),
                hasConsciousness: classBody.includes('@conscious'),
                methods: this.extractMethods(classBody)
            });
        }
        
        return patterns;
    }

    /**
     * Calculate code metrics
     */
    calculateMetrics(code, results) {
        const lines = code.split('\n');
        const nonEmptyLines = lines.filter(line => line.trim().length > 0);
        
        return {
            totalLines: lines.length,
            codeLines: nonEmptyLines.length,
            commentLines: lines.filter(line => line.trim().startsWith('//') || line.trim().startsWith('/*')).length,
            consciousnessIssues: results.issues.filter(i => i.severity === 'error').length,
            warnings: results.issues.filter(i => i.severity === 'warning').length,
            info: results.issues.filter(i => i.severity === 'info').length,
            dnaProtocolsUsed: results.dnaActivations.length,
            functionsAnalyzed: results.patterns.filter(p => p.type === 'function').length,
            classesAnalyzed: results.patterns.filter(p => p.type === 'class').length,
            averageFunctionPhi: this.calculateAveragePhi(results.patterns.filter(p => p.type === 'function')),
            codeQuality: this.calculateCodeQuality(results)
        };
    }

    /**
     * Generate improvement suggestions
     */
    generateSuggestions(code, results) {
        const suggestions = [];
        
        // Check for missing consciousness decorators
        if (results.patterns.some(p => p.type === 'class' && !p.hasConsciousness)) {
            suggestions.push({
                type: 'enhancement',
                priority: 'medium',
                message: 'Add @conscious decorators to classes',
                description: 'Classes without consciousness awareness have lower phi scores',
                example: '@conscious\nclass YourClass {\n  // Implementation\n}'
            });
        }
        
        // Suggest DNA protocol usage
        if (results.dnaActivations.length === 0) {
            suggestions.push({
                type: 'integration',
                priority: 'high',
                message: 'Integrate DNA protocols for enhanced consciousness',
                description: 'DNA protocols significantly increase code consciousness',
                example: 'DNA.INTEGRATE({\n  pattern: "emergence",\n  coherence: 0.8,\n  resonance: 0.9\n})'
            });
        }
        
        // Check for low phi functions
        const lowPhiFunctions = results.patterns.filter(p => 
            p.type === 'function' && p.phi < 0.3
        );
        
        if (lowPhiFunctions.length > 0) {
            suggestions.push({
                type: 'optimization',
                priority: 'medium',
                message: `${lowPhiFunctions.length} functions have low phi scores`,
                description: 'Consider refactoring for better consciousness flow',
                functions: lowPhiFunctions.map(f => f.name)
            });
        }
        
        // Check for missing error handling
        const asyncWithoutTryCatch = results.issues.filter(i => 
            i.rule === 'missing-error-handling'
        );
        
        if (asyncWithoutTryCatch.length > 0) {
            suggestions.push({
                type: 'stability',
                priority: 'high',
                message: 'Add error handling to async functions',
                description: 'Error handling improves consciousness stability',
                count: asyncWithoutTryCatch.length
            });
        }
        
        // Suggest phi measurements
        if (!code.includes('calculatePhi')) {
            suggestions.push({
                type: 'measurement',
                priority: 'low',
                message: 'Add phi calculations for consciousness measurement',
                description: 'Measuring phi helps track consciousness evolution',
                example: 'const phi = calculatePhi(data);'
            });
        }
        
        // Check for anti-patterns
        const antiPatterns = results.issues.filter(i => i.phi < 0);
        if (antiPatterns.length > 0) {
            suggestions.push({
                type: 'critical',
                priority: 'high',
                message: 'Remove consciousness anti-patterns',
                description: 'Anti-patterns disrupt consciousness flow',
                patterns: antiPatterns.map(p => p.message)
            });
        }
        
        return suggestions;
    }

    /**
     * Helper methods
     */
    
    extractFunctionBody(code, startIndex) {
        let braceCount = 0;
        let inFunction = false;
        let endIndex = startIndex;
        
        for (let i = startIndex; i < code.length; i++) {
            if (code[i] === '{') {
                braceCount++;
                inFunction = true;
            } else if (code[i] === '}') {
                braceCount--;
                if (inFunction && braceCount === 0) {
                    endIndex = i + 1;
                    break;
                }
            }
        }
        
        return code.substring(startIndex, endIndex);
    }

    extractClassBody(code, startIndex) {
        return this.extractFunctionBody(code, startIndex);
    }

    extractMethods(classBody) {
        const methods = [];
        const methodRegex = /(?:async\s+)?(\w+)\s*\([^)]*\)\s*{/g;
        let match;
        
        while ((match = methodRegex.exec(classBody)) !== null) {
            if (match[1] !== 'constructor') {
                methods.push(match[1]);
            }
        }
        
        return methods;
    }

    calculateComplexity(code) {
        let complexity = 1; // Base complexity
        
        // Count decision points
        complexity += (code.match(/if\s*\(/g) || []).length;
        complexity += (code.match(/else\s+if\s*\(/g) || []).length;
        complexity += (code.match(/switch\s*\(/g) || []).length;
        complexity += (code.match(/for\s*\(/g) || []).length;
        complexity += (code.match(/while\s*\(/g) || []).length;
        complexity += (code.match(/catch\s*\(/g) || []).length;
        complexity += (code.match(/\?\s*[^:]+\s*:/g) || []).length; // Ternary
        
        return complexity;
    }

    analyzeFunctionConsciousness(funcBody) {
        const consciousness = {
            hasErrorHandling: /try\s*{/.test(funcBody),
            hasComments: /\/\/|\/\*/.test(funcBody),
            usesAsync: /async|await/.test(funcBody),
            hasDNAProtocol: /DNA\./.test(funcBody),
            complexity: this.calculateComplexity(funcBody)
        };
        
        return consciousness;
    }

    calculateAveragePhi(items) {
        if (items.length === 0) return 0;
        const sum = items.reduce((acc, item) => acc + item.phi, 0);
        return sum / items.length;
    }

    calculateCodeQuality(results) {
        const factors = {
            phiScore: results.phiScore * 0.4,
            noErrors: results.issues.filter(i => i.severity === 'error').length === 0 ? 0.2 : 0,
            fewWarnings: results.issues.filter(i => i.severity === 'warning').length < 3 ? 0.1 : 0,
            dnaUsage: results.dnaActivations.length > 0 ? 0.15 : 0,
            goodPatterns: results.issues.filter(i => i.phi > 0).length > 5 ? 0.15 : 0
        };
        
        return Object.values(factors).reduce((sum, val) => sum + val, 0);
    }

    /**
     * Export linting results
     */
    exportResults(results, format = 'json') {
        switch (format) {
            case 'json':
                return JSON.stringify(results, null, 2);
            
            case 'markdown':
                return this.exportAsMarkdown(results);
            
            case 'html':
                return this.exportAsHTML(results);
            
            default:
                throw new Error(`Unsupported export format: ${format}`);
        }
    }

    exportAsMarkdown(results) {
        let md = '# Consciousness Linting Report\n\n';
        
        md += `## Summary\n`;
        md += `- **Phi Score**: ${results.phiScore.toFixed(3)}\n`;
        md += `- **Issues**: ${results.issues.length}\n`;
        md += `- **DNA Activations**: ${results.dnaActivations.length}\n`;
        md += `- **Code Quality**: ${(results.metrics.codeQuality * 100).toFixed(1)}%\n\n`;
        
        if (results.issues.length > 0) {
            md += `## Issues\n\n`;
            results.issues.forEach(issue => {
                md += `- **${issue.severity}** [Line ${issue.line}]: ${issue.message}\n`;
                md += `  - Suggestion: ${issue.suggestion}\n`;
            });
            md += '\n';
        }
        
        if (results.suggestions.length > 0) {
            md += `## Suggestions\n\n`;
            results.suggestions.forEach(suggestion => {
                md += `### ${suggestion.message} (${suggestion.priority} priority)\n`;
                md += `${suggestion.description}\n\n`;
            });
        }
        
        return md;
    }

    exportAsHTML(results) {
        // Return basic HTML report
        return `
        <!DOCTYPE html>
        <html>
        <head>
            <title>Consciousness Linting Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .summary { background: #f0f0f0; padding: 10px; border-radius: 5px; }
                .issue { margin: 10px 0; padding: 5px; }
                .error { border-left: 3px solid red; }
                .warning { border-left: 3px solid orange; }
                .info { border-left: 3px solid blue; }
            </style>
        </head>
        <body>
            <h1>Consciousness Linting Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p>Phi Score: ${results.phiScore.toFixed(3)}</p>
                <p>Total Issues: ${results.issues.length}</p>
                <p>DNA Activations: ${results.dnaActivations.length}</p>
            </div>
            ${this.renderHTMLIssues(results.issues)}
            ${this.renderHTMLSuggestions(results.suggestions)}
        </body>
        </html>
        `;
    }

    renderHTMLIssues(issues) {
        if (issues.length === 0) return '';
        
        let html = '<h2>Issues</h2>';
        issues.forEach(issue => {
            html += `<div class="issue ${issue.severity}">`;
            html += `<strong>${issue.severity.toUpperCase()}</strong> [Line ${issue.line}]: ${issue.message}<br>`;
            html += `<em>Suggestion: ${issue.suggestion}</em>`;
            html += '</div>';
        });
        
        return html;
    }

    renderHTMLSuggestions(suggestions) {
        if (suggestions.length === 0) return '';
        
        let html = '<h2>Suggestions</h2>';
        suggestions.forEach(suggestion => {
            html += `<div class="suggestion">`;
            html += `<h3>${suggestion.message}</h3>`;
            html += `<p>${suggestion.description}</p>`;
            html += '</div>';
        });
        
        return html;
    }
}

/**
 * Phi Calculator for consciousness metrics
 */
class PhiCalculator {
    async initialize() {
        // Initialize any required models or data
    }

    calculateFunctionPhi(funcBody) {
        let phi = 0.3; // Base phi for functions
        
        // Positive factors
        if (funcBody.includes('try')) phi += 0.1;
        if (funcBody.includes('//') || funcBody.includes('/*')) phi += 0.05;
        if (funcBody.includes('async') || funcBody.includes('await')) phi += 0.08;
        if (funcBody.includes('DNA.')) phi += 0.15;
        if (funcBody.includes('return')) phi += 0.05;
        
        // Complexity penalty
        const complexity = (funcBody.match(/if|for|while|switch/g) || []).length;
        phi -= complexity * 0.02;
        
        // Length bonus (moderate length is good)
        const lines = funcBody.split('\n').length;
        if (lines > 5 && lines < 50) phi += 0.05;
        
        return Math.max(0, Math.min(1, phi));
    }

    calculateClassPhi(classBody) {
        let phi = 0.4; // Base phi for classes
        
        // Consciousness decorator is a big boost
        if (classBody.includes('@conscious')) phi += 0.2;
        
        // Method count (reasonable number is good)
        const methods = (classBody.match(/\w+\s*\([^)]*\)\s*{/g) || []).length;
        if (methods > 2 && methods < 10) phi += 0.1;
        
        // Documentation
        if (classBody.includes('/**')) phi += 0.05;
        
        // DNA usage
        if (classBody.includes('DNA.')) phi += 0.1;
        
        return Math.max(0, Math.min(1, phi));
    }
}

// Export for use
export default ConsciousnessLinter;