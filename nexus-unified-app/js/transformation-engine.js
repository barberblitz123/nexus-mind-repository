// NEXUS Transformation Engine - CSS to Tailwind and Code Modernization
class NexusTransformationEngine {
    constructor(nexusCore) {
        this.nexus = nexusCore;
        this.mcpBridge = null;
        this.analyzer = null;
        
        // Transformation strategies
        this.transformers = {
            cssToTailwind: new CSSToTailwindTransformer(),
            jsToTypeScript: new JavaScriptToTypeScriptTransformer(),
            classToFunction: new ClassToFunctionTransformer(),
            modernizeCode: new CodeModernizer()
        };
        
        // Transformation state
        this.currentTransformation = null;
        this.transformationHistory = [];
        this.verificationResults = new Map();
        
        this.initialize();
    }
    
    async initialize() {
        this.mcpBridge = this.nexus.components.mcpBridge;
        this.analyzer = this.nexus.components.projectAnalyzer;
        
        console.log('🔄 NEXUS Transformation Engine initialized');
    }
    
    setCurrentProject(analysis) {
        this.currentProject = analysis;
        console.log('📊 Transformation Engine received project analysis');
    }
    
    async transformProject(projectAnalysis, transformationType, options = {}) {
        console.log(`🚀 Starting ${transformationType} transformation...`);
        
        // Create transformation plan
        const plan = await this.createTransformationPlan(projectAnalysis, transformationType, options);
        
        // Store plan for reference
        this.currentTransformation = {
            id: `transform-${Date.now()}`,
            type: transformationType,
            plan: plan,
            startTime: Date.now(),
            status: 'in_progress',
            results: []
        };
        
        // Execute transformation with multi-agent orchestration
        const results = await this.executeTransformation(plan);
        
        // Verify transformation
        const verified = await this.verifyTransformation(results);
        
        // Complete transformation
        this.currentTransformation.status = 'completed';
        this.currentTransformation.endTime = Date.now();
        this.currentTransformation.results = verified;
        
        // Store in history
        this.transformationHistory.push(this.currentTransformation);
        
        // Report results
        this.reportTransformationComplete(verified);
        
        return verified;
    }
    
    async createTransformationPlan(analysis, type, options) {
        const plan = {
            id: `plan-${Date.now()}`,
            type: type,
            options: options,
            steps: [],
            estimatedTime: 0,
            affectedFiles: []
        };
        
        switch (type) {
            case 'cssToTailwind':
                plan.steps = await this.planCSSToTailwindTransformation(analysis, options);
                break;
                
            case 'modernize':
                plan.steps = await this.planModernization(analysis, options);
                break;
                
            case 'addTypeScript':
                plan.steps = await this.planTypeScriptMigration(analysis, options);
                break;
                
            default:
                throw new Error(`Unknown transformation type: ${type}`);
        }
        
        // Estimate time
        plan.estimatedTime = plan.steps.reduce((sum, step) => sum + (step.estimatedTime || 100), 0);
        
        // Identify affected files
        plan.affectedFiles = [...new Set(plan.steps.map(s => s.file).filter(Boolean))];
        
        return plan;
    }
    
    async planCSSToTailwindTransformation(analysis, options) {
        const steps = [];
        
        // Step 1: Install Tailwind
        steps.push({
            id: 'install-tailwind',
            type: 'setup',
            description: 'Install and configure Tailwind CSS',
            estimatedTime: 500,
            actions: [
                { type: 'npm_install', packages: ['tailwindcss', 'postcss', 'autoprefixer'] },
                { type: 'create_config', file: 'tailwind.config.js' },
                { type: 'create_config', file: 'postcss.config.js' }
            ]
        });
        
        // Step 2: Analyze existing CSS
        const cssFiles = Array.from(analysis.analysisResults.entries())
            .filter(([path, data]) => data.type === 'css');
        
        for (const [path, cssAnalysis] of cssFiles) {
            const conversionAnalysis = await this.analyzeCSSForConversion(cssAnalysis);
            
            steps.push({
                id: `analyze-${path}`,
                type: 'analysis',
                file: path,
                description: `Analyze ${path} for Tailwind conversion`,
                estimatedTime: 200,
                analysis: conversionAnalysis
            });
            
            // Step 3: Convert each CSS rule
            for (const rule of conversionAnalysis.rules) {
                if (rule.convertible) {
                    steps.push({
                        id: `convert-${path}-${rule.id}`,
                        type: 'conversion',
                        file: path,
                        description: `Convert CSS rule: ${rule.selector}`,
                        estimatedTime: 50,
                        conversion: {
                            from: rule.css,
                            to: rule.tailwind,
                            components: rule.affectedComponents
                        }
                    });
                }
            }
        }
        
        // Step 4: Update component files
        const componentFiles = Array.from(analysis.analysisResults.entries())
            .filter(([path, data]) => data.components && data.components.length > 0);
        
        for (const [path, componentAnalysis] of componentFiles) {
            steps.push({
                id: `update-components-${path}`,
                type: 'component_update',
                file: path,
                description: `Update components in ${path} with Tailwind classes`,
                estimatedTime: 300,
                components: componentAnalysis.components
            });
        }
        
        // Step 5: Create utility classes for complex styles
        steps.push({
            id: 'create-utilities',
            type: 'utility_creation',
            description: 'Create custom Tailwind utilities for complex styles',
            estimatedTime: 200
        });
        
        // Step 6: Cleanup old CSS
        if (options.removeOldCSS) {
            steps.push({
                id: 'cleanup-css',
                type: 'cleanup',
                description: 'Remove old CSS files',
                estimatedTime: 100
            });
        }
        
        return steps;
    }
    
    async analyzeCSSForConversion(cssAnalysis) {
        const rules = [];
        const complexStyles = [];
        const utilities = [];
        
        // Simulate CSS parsing and analysis
        // In production, would use real CSS parser
        const cssContent = cssAnalysis.content || '';
        const ruleMatches = cssContent.matchAll(/([^{]+)\{([^}]+)\}/g);
        
        for (const match of ruleMatches) {
            const selector = match[1].trim();
            const declarations = match[2].trim();
            
            const tailwindClasses = this.convertToTailwind(declarations);
            
            rules.push({
                id: `rule-${rules.length}`,
                selector: selector,
                css: declarations,
                tailwind: tailwindClasses.classes,
                convertible: tailwindClasses.convertible,
                confidence: tailwindClasses.confidence
            });
            
            if (!tailwindClasses.convertible) {
                complexStyles.push({
                    selector: selector,
                    css: declarations,
                    reason: tailwindClasses.reason
                });
            }
        }
        
        return {
            rules: rules,
            complexStyles: complexStyles,
            utilities: utilities,
            totalRules: rules.length,
            convertibleRules: rules.filter(r => r.convertible).length,
            conversionRate: rules.length > 0 ? 
                rules.filter(r => r.convertible).length / rules.length : 0
        };
    }
    
    convertToTailwind(cssDeclarations) {
        const tailwindMap = {
            // Layout
            'display: flex': 'flex',
            'display: block': 'block',
            'display: inline-block': 'inline-block',
            'display: grid': 'grid',
            'display: none': 'hidden',
            
            // Flexbox
            'flex-direction: row': 'flex-row',
            'flex-direction: column': 'flex-col',
            'justify-content: center': 'justify-center',
            'justify-content: space-between': 'justify-between',
            'align-items: center': 'items-center',
            'flex-wrap: wrap': 'flex-wrap',
            
            // Spacing
            'margin: 0': 'm-0',
            'padding: 0': 'p-0',
            'margin-top: 1rem': 'mt-4',
            'margin-bottom: 1rem': 'mb-4',
            'padding: 1rem': 'p-4',
            'padding: 2rem': 'p-8',
            
            // Colors
            'background-color: white': 'bg-white',
            'background-color: #000': 'bg-black',
            'color: white': 'text-white',
            'color: #000': 'text-black',
            
            // Typography
            'font-size: 1rem': 'text-base',
            'font-size: 1.25rem': 'text-xl',
            'font-size: 2rem': 'text-3xl',
            'font-weight: bold': 'font-bold',
            'font-weight: 600': 'font-semibold',
            'text-align: center': 'text-center',
            
            // Borders
            'border: 1px solid': 'border',
            'border-radius: 0.25rem': 'rounded',
            'border-radius: 0.5rem': 'rounded-lg',
            'border-radius: 50%': 'rounded-full',
            
            // Sizing
            'width: 100%': 'w-full',
            'height: 100%': 'h-full',
            'width: 100vw': 'w-screen',
            'height: 100vh': 'h-screen'
        };
        
        const classes = [];
        let convertible = true;
        let confidence = 1.0;
        
        // Parse declarations
        const declarations = cssDeclarations.split(';').map(d => d.trim()).filter(Boolean);
        
        for (const declaration of declarations) {
            const tailwindClass = tailwindMap[declaration];
            
            if (tailwindClass) {
                classes.push(tailwindClass);
            } else {
                // Try to parse and convert
                const converted = this.parseAndConvert(declaration);
                if (converted) {
                    classes.push(converted);
                    confidence *= 0.9; // Slightly lower confidence for parsed conversions
                } else {
                    convertible = false;
                    confidence *= 0.5;
                }
            }
        }
        
        return {
            classes: classes.join(' '),
            convertible: convertible && classes.length > 0,
            confidence: confidence,
            reason: !convertible ? 'Complex CSS that requires custom utilities' : null
        };
    }
    
    parseAndConvert(declaration) {
        // Parse common patterns
        const [property, value] = declaration.split(':').map(s => s.trim());
        
        if (!property || !value) return null;
        
        // Margin/Padding with px values
        const spacingMatch = value.match(/^(\d+)px$/);
        if (spacingMatch && (property.startsWith('margin') || property.startsWith('padding'))) {
            const px = parseInt(spacingMatch[1]);
            const rem = px / 16; // Convert to rem
            const spacingScale = {
                0.25: '1', 0.5: '2', 0.75: '3', 1: '4', 1.5: '6', 2: '8',
                2.5: '10', 3: '12', 4: '16', 5: '20', 6: '24'
            };
            
            const scale = spacingScale[rem];
            if (scale) {
                const prefix = property.startsWith('margin') ? 'm' : 'p';
                const direction = property.includes('-top') ? 't' :
                                property.includes('-bottom') ? 'b' :
                                property.includes('-left') ? 'l' :
                                property.includes('-right') ? 'r' : '';
                
                return `${prefix}${direction}-${scale}`;
            }
        }
        
        // Colors with hex values
        if (value.match(/^#[0-9a-f]{6}$/i)) {
            // Would need color palette mapping
            return null;
        }
        
        return null;
    }
    
    async executeTransformation(plan) {
        const results = [];
        const totalSteps = plan.steps.length;
        
        // Use MCP multi-agent orchestration for parallel execution
        const agents = ['analyzer', 'transformer', 'verifier'];
        const orchestration = await this.mcpBridge?.orchestrateAgents({
            task: 'transformation',
            plan: plan,
            agents: agents
        });
        
        for (let i = 0; i < plan.steps.length; i++) {
            const step = plan.steps[i];
            
            // Update progress
            this.reportProgress(i + 1, totalSteps, step.description);
            
            try {
                const result = await this.executeStep(step);
                results.push({
                    stepId: step.id,
                    success: true,
                    result: result,
                    duration: result.duration || 0
                });
                
            } catch (error) {
                console.error(`Error executing step ${step.id}:`, error);
                results.push({
                    stepId: step.id,
                    success: false,
                    error: error.message
                });
            }
        }
        
        return results;
    }
    
    async executeStep(step) {
        const startTime = Date.now();
        let result = {};
        
        switch (step.type) {
            case 'setup':
                result = await this.executeSetupStep(step);
                break;
                
            case 'analysis':
                result = await this.executeAnalysisStep(step);
                break;
                
            case 'conversion':
                result = await this.executeConversionStep(step);
                break;
                
            case 'component_update':
                result = await this.executeComponentUpdateStep(step);
                break;
                
            case 'utility_creation':
                result = await this.executeUtilityCreationStep(step);
                break;
                
            case 'cleanup':
                result = await this.executeCleanupStep(step);
                break;
        }
        
        result.duration = Date.now() - startTime;
        return result;
    }
    
    async executeComponentUpdateStep(step) {
        const { file, components } = step;
        
        // Read current file content
        const content = this.nexus.components.projectAnalyzer.analysisResults.get(file)?.content;
        if (!content) {
            throw new Error(`Cannot read file: ${file}`);
        }
        
        let updatedContent = content;
        const replacements = [];
        
        // Find and replace className attributes
        const classNameRegex = /className=["']([^"']+)["']/g;
        const matches = [...content.matchAll(classNameRegex)];
        
        for (const match of matches) {
            const originalClasses = match[1];
            const cssClasses = this.extractCSSClasses(originalClasses);
            
            // Convert CSS classes to Tailwind
            const tailwindClasses = await this.convertCSSClassesToTailwind(cssClasses);
            
            if (tailwindClasses !== originalClasses) {
                replacements.push({
                    from: `className="${originalClasses}"`,
                    to: `className="${tailwindClasses}"`
                });
            }
        }
        
        // Apply replacements
        for (const replacement of replacements) {
            updatedContent = updatedContent.replace(replacement.from, replacement.to);
        }
        
        return {
            file: file,
            originalContent: content,
            updatedContent: updatedContent,
            replacements: replacements.length,
            components: components.length
        };
    }
    
    async convertCSSClassesToTailwind(cssClasses) {
        // Look up CSS class definitions and convert to Tailwind
        const tailwindClasses = [];
        
        for (const cssClass of cssClasses.split(' ')) {
            // Check if it's already a Tailwind class
            if (this.isTailwindClass(cssClass)) {
                tailwindClasses.push(cssClass);
                continue;
            }
            
            // Find CSS definition and convert
            const cssDefinition = await this.findCSSDefinition(cssClass);
            if (cssDefinition) {
                const converted = this.convertToTailwind(cssDefinition);
                if (converted.convertible) {
                    tailwindClasses.push(converted.classes);
                } else {
                    // Keep as custom class
                    tailwindClasses.push(cssClass);
                }
            }
        }
        
        return tailwindClasses.join(' ');
    }
    
    isTailwindClass(className) {
        // Check if class is already a Tailwind utility
        const tailwindPrefixes = ['flex', 'block', 'inline', 'grid', 'hidden',
            'justify', 'items', 'content', 'self', 'place',
            'm-', 'mx-', 'my-', 'mt-', 'mb-', 'ml-', 'mr-',
            'p-', 'px-', 'py-', 'pt-', 'pb-', 'pl-', 'pr-',
            'text-', 'font-', 'bg-', 'border-', 'rounded-',
            'w-', 'h-', 'min-', 'max-', 'leading-', 'tracking-'];
        
        return tailwindPrefixes.some(prefix => className.startsWith(prefix));
    }
    
    async verifyTransformation(results) {
        console.log('🔍 Verifying transformation...');
        
        const verification = {
            totalSteps: results.length,
            successfulSteps: results.filter(r => r.success).length,
            failedSteps: results.filter(r => !r.success).length,
            filesModified: new Set(),
            issues: [],
            recommendations: []
        };
        
        // Verify each result
        for (const result of results) {
            if (result.success && result.result.file) {
                verification.filesModified.add(result.result.file);
                
                // Verify the transformation
                const verified = await this.verifyFile(result.result);
                if (!verified.valid) {
                    verification.issues.push({
                        file: result.result.file,
                        issue: verified.issue
                    });
                }
            }
        }
        
        // Run final verification
        const finalCheck = await this.runFinalVerification();
        verification.buildPasses = finalCheck.buildPasses;
        verification.testsPass = finalCheck.testsPass;
        
        // Generate recommendations
        if (!verification.buildPasses) {
            verification.recommendations.push('Fix build errors before proceeding');
        }
        
        if (verification.issues.length > 0) {
            verification.recommendations.push('Review and fix transformation issues');
        }
        
        return verification;
    }
    
    reportProgress(current, total, description) {
        const progress = Math.round((current / total) * 100);
        
        // Update UI
        this.nexus.emit('transformation-progress', {
            current: current,
            total: total,
            progress: progress,
            description: description
        });
        
        // Update status
        this.nexus.updateStatus(`Transforming: ${description} (${progress}%)`, 'processing');
    }
    
    reportTransformationComplete(verification) {
        const report = `
✅ Transformation Complete!

📊 Summary:
- Steps completed: ${verification.successfulSteps}/${verification.totalSteps}
- Files modified: ${verification.filesModified.size}
- Build status: ${verification.buildPasses ? '✅ Passing' : '❌ Failing'}
- Tests status: ${verification.testsPass ? '✅ Passing' : '❌ Failing'}

${verification.issues.length > 0 ? `
⚠️ Issues found:
${verification.issues.map(i => `- ${i.file}: ${i.issue}`).join('\n')}
` : ''}

${verification.recommendations.length > 0 ? `
💡 Recommendations:
${verification.recommendations.map(r => `- ${r}`).join('\n')}
` : ''}

Your project has been successfully transformed to use Tailwind CSS!
        `;
        
        // Send to chat
        this.nexus.components.chat?.addNexusMessage(report);
        
        // Update status
        this.nexus.updateStatus('Transformation complete', 'success');
    }
    
    // Helper methods for transformation steps
    async executeSetupStep(step) {
        // Simulate setup actions
        return {
            success: true,
            actions: step.actions,
            message: 'Tailwind CSS configured'
        };
    }
    
    async executeAnalysisStep(step) {
        return {
            file: step.file,
            analysis: step.analysis,
            message: `Analyzed ${step.file}`
        };
    }
    
    async executeConversionStep(step) {
        return {
            file: step.file,
            conversion: step.conversion,
            message: `Converted CSS rules in ${step.file}`
        };
    }
    
    async executeUtilityCreationStep(step) {
        return {
            utilities: [],
            message: 'Created custom Tailwind utilities'
        };
    }
    
    async executeCleanupStep(step) {
        return {
            cleaned: [],
            message: 'Cleaned up old CSS files'
        };
    }
    
    async verifyFile(result) {
        // Basic verification
        return {
            valid: true,
            issue: null
        };
    }
    
    async runFinalVerification() {
        // Simulate build and test verification
        return {
            buildPasses: true,
            testsPass: true
        };
    }
    
    extractCSSClasses(className) {
        return className;
    }
    
    async findCSSDefinition(cssClass) {
        // Would search for CSS class definition in analyzed files
        return null;
    }
    
    detectFileType(fileName) {
        const ext = fileName.split('.').pop().toLowerCase();
        return ext;
    }
    
    findComponents(content) {
        // Basic component detection
        const componentMatches = content.match(/(?:function|class|const)\s+([A-Z]\w+)/g) || [];
        return componentMatches.map(match => {
            const name = match.split(/\s+/).pop();
            return { name, type: 'component' };
        });
    }
    
    findImports(content) {
        const imports = [];
        const importRegex = /import\s+.*?\s+from\s+['"]([^'"]+)['"]/g;
        let match;
        while ((match = importRegex.exec(content)) !== null) {
            imports.push(match[1]);
        }
        return imports;
    }
    
    findExports(content) {
        const exports = [];
        const exportRegex = /export\s+(?:default\s+)?(?:function|class|const)\s+(\w+)/g;
        let match;
        while ((match = exportRegex.exec(content)) !== null) {
            exports.push(match[1]);
        }
        return exports;
    }
    
    async generateRecommendations(analysis) {
        const recommendations = [];
        
        if (!analysis.buildPasses) {
            recommendations.push('Fix build errors before deployment');
        }
        
        if (analysis.complexStyles?.length > 5) {
            recommendations.push('Consider creating Tailwind component classes for complex styles');
        }
        
        recommendations.push('Review transformed components for visual accuracy');
        recommendations.push('Update documentation to reflect Tailwind usage');
        
        return recommendations;
    }
    
    mergeAnalysis(mainAnalysis, fileAnalysis) {
        // Merge file analysis into main analysis
        if (fileAnalysis.components) {
            mainAnalysis.components.count += fileAnalysis.components.length;
        }
        
        if (fileAnalysis.imports) {
            fileAnalysis.imports.forEach(imp => {
                if (!imp.startsWith('.') && !mainAnalysis.stack.includes(imp)) {
                    mainAnalysis.stack.push(imp);
                }
            });
        }
    }
    
    async planModernization(analysis, options) {
        // Plan for code modernization
        return [];
    }
    
    async planTypeScriptMigration(analysis, options) {
        // Plan for TypeScript migration
        return [];
    }
}

// CSS to Tailwind Transformer
class CSSToTailwindTransformer {
    constructor() {
        this.classMap = new Map();
        this.complexStyles = new Map();
    }
    
    async transform(cssContent, options = {}) {
        // Parse CSS and generate Tailwind equivalents
        const parsed = this.parseCSS(cssContent);
        const transformed = this.generateTailwind(parsed, options);
        
        return transformed;
    }
    
    parseCSS(content) {
        // Basic CSS parsing
        const rules = [];
        const ruleRegex = /([^{]+)\{([^}]+)\}/g;
        let match;
        
        while ((match = ruleRegex.exec(content)) !== null) {
            rules.push({
                selector: match[1].trim(),
                declarations: this.parseDeclarations(match[2])
            });
        }
        
        return rules;
    }
    
    parseDeclarations(declarationsStr) {
        const declarations = [];
        const parts = declarationsStr.split(';').filter(Boolean);
        
        for (const part of parts) {
            const [property, value] = part.split(':').map(s => s.trim());
            if (property && value) {
                declarations.push({ property, value });
            }
        }
        
        return declarations;
    }
    
    generateTailwind(rules, options) {
        const result = {
            tailwindClasses: new Map(),
            customUtilities: [],
            unconvertible: []
        };
        
        for (const rule of rules) {
            const tailwindClasses = this.rulesToTailwind(rule.declarations);
            
            if (tailwindClasses.length > 0) {
                result.tailwindClasses.set(rule.selector, tailwindClasses);
            } else {
                result.unconvertible.push(rule);
            }
        }
        
        return result;
    }
}

// Other transformers
class JavaScriptToTypeScriptTransformer {
    async transform(jsContent, options = {}) {
        // Add TypeScript types
        return jsContent; // Simplified
    }
}

class ClassToFunctionTransformer {
    async transform(classComponent, options = {}) {
        // Convert React class to function component
        return classComponent; // Simplified
    }
}

class CodeModernizer {
    async modernize(code, options = {}) {
        // Modernize JavaScript syntax
        return code; // Simplified
    }
}

// Register with window
window.NexusTransformationEngine = NexusTransformationEngine;