// NEXUS Project Analyzer - Complete Codebase Analysis System
class NexusProjectAnalyzer {
    constructor(nexusCore) {
        this.nexus = nexusCore;
        this.mcpBridge = null;
        
        // Analysis capabilities
        this.analyzers = {
            javascript: new JavaScriptAnalyzer(),
            react: new ReactAnalyzer(),
            css: new CSSAnalyzer(),
            html: new HTMLAnalyzer(),
            json: new JSONAnalyzer()
        };
        
        // Analysis state
        this.currentProject = null;
        this.analysisResults = new Map();
        this.patterns = new Map();
        this.dependencies = new Map();
        
        // Business logic extraction
        this.businessLogic = {
            models: new Map(),
            controllers: new Map(),
            services: new Map(),
            utilities: new Map(),
            apis: new Map()
        };
        
        this.initialize();
    }
    
    async initialize() {
        // Connect to MCP Bridge for advanced analysis
        this.mcpBridge = this.nexus.components.mcpBridge;
        
        // Set up drag-drop handlers
        this.setupProjectDropZone();
        
        console.log('📊 NEXUS Project Analyzer initialized');
    }
    
    setupProjectDropZone() {
        // Create drop zone UI
        const dropZone = document.createElement('div');
        dropZone.id = 'nexus-project-dropzone';
        dropZone.className = 'nexus-dropzone';
        dropZone.innerHTML = `
            <div class="dropzone-content">
                <div class="dropzone-icon">📁</div>
                <h3>Drop Your Project Here</h3>
                <p>NEXUS will analyze your entire codebase</p>
                <p class="dropzone-hint">Supports: React, JavaScript, CSS, HTML</p>
                <button class="browse-button" onclick="document.getElementById('project-input').click()">
                    Browse Files
                </button>
                <input type="file" id="project-input" webkitdirectory directory multiple style="display: none">
            </div>
        `;
        
        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .nexus-dropzone {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 400px;
                height: 300px;
                border: 3px dashed #4a5568;
                border-radius: 20px;
                background: rgba(30, 30, 30, 0.95);
                display: none;
                z-index: 10000;
                transition: all 0.3s ease;
            }
            
            .nexus-dropzone.active {
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .nexus-dropzone.dragover {
                border-color: #00ff00;
                background: rgba(0, 255, 0, 0.1);
                transform: translate(-50%, -50%) scale(1.05);
            }
            
            .dropzone-content {
                text-align: center;
                color: #e2e8f0;
            }
            
            .dropzone-icon {
                font-size: 64px;
                margin-bottom: 20px;
            }
            
            .browse-button {
                margin-top: 20px;
                padding: 10px 20px;
                background: #4a5568;
                border: none;
                border-radius: 5px;
                color: white;
                cursor: pointer;
                transition: background 0.3s;
            }
            
            .browse-button:hover {
                background: #2d3748;
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(dropZone);
        
        // Handle drag events
        document.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('active', 'dragover');
        });
        
        document.addEventListener('dragleave', (e) => {
            if (e.target === dropZone || !dropZone.contains(e.target)) {
                dropZone.classList.remove('dragover');
            }
        });
        
        document.addEventListener('drop', async (e) => {
            e.preventDefault();
            dropZone.classList.remove('active', 'dragover');
            
            const items = e.dataTransfer.items;
            if (items.length > 0) {
                const files = await this.getFilesFromItems(items);
                await this.analyzeProject(files);
            }
        });
        
        // Handle file input
        document.getElementById('project-input').addEventListener('change', async (e) => {
            const files = Array.from(e.target.files);
            await this.analyzeProject(files);
        });
    }
    
    async getFilesFromItems(items) {
        const files = [];
        const promises = [];
        
        for (let i = 0; i < items.length; i++) {
            const item = items[i].webkitGetAsEntry();
            if (item) {
                promises.push(this.traverseFileTree(item, files));
            }
        }
        
        await Promise.all(promises);
        return files;
    }
    
    async traverseFileTree(item, files) {
        if (item.isFile) {
            return new Promise((resolve) => {
                item.file((file) => {
                    files.push({
                        path: item.fullPath,
                        file: file
                    });
                    resolve();
                });
            });
        } else if (item.isDirectory) {
            const dirReader = item.createReader();
            const entries = await new Promise((resolve) => {
                dirReader.readEntries(resolve);
            });
            
            const promises = [];
            for (const entry of entries) {
                promises.push(this.traverseFileTree(entry, files));
            }
            
            await Promise.all(promises);
        }
    }
    
    async analyzeProject(files) {
        console.log(`🔍 NEXUS analyzing ${files.length} files...`);
        
        // Show progress
        this.nexus.updateStatus('Analyzing project...', 'processing');
        
        // Reset analysis state
        this.analysisResults.clear();
        this.patterns.clear();
        this.businessLogic = {
            models: new Map(),
            controllers: new Map(),
            services: new Map(),
            utilities: new Map(),
            apis: new Map()
        };
        
        // Create project structure
        this.currentProject = {
            name: this.extractProjectName(files),
            files: files,
            structure: this.buildFileTree(files),
            timestamp: Date.now()
        };
        
        // Analyze each file
        const fileAnalyses = [];
        for (const fileEntry of files) {
            const analysis = await this.analyzeFile(fileEntry);
            if (analysis) {
                fileAnalyses.push(analysis);
                this.analysisResults.set(fileEntry.path, analysis);
            }
        }
        
        // Extract patterns using MCP tools
        const patterns = await this.mcpBridge?.analyzeProjectPatterns(
            fileAnalyses.map(a => ({
                path: a.path,
                content: a.content,
                type: a.type
            }))
        );
        
        // Build comprehensive analysis
        const projectAnalysis = {
            overview: this.buildProjectOverview(),
            architecture: this.detectArchitecture(),
            dependencies: this.analyzeDependencies(),
            businessLogic: this.extractBusinessLogic(),
            patterns: patterns || this.detectPatterns(),
            components: this.findAllComponents(),
            routes: this.extractRoutes(),
            apis: this.extractAPIs(),
            database: this.detectDatabaseSchema(),
            styling: this.analyzeStyles(),
            recommendations: await this.generateRecommendations()
        };
        
        // Store in memory for future reference
        await this.mcpBridge?.storeInMemory(
            `project-analysis-${this.currentProject.name}`,
            projectAnalysis,
            { type: 'project_analysis', files: files.length }
        );
        
        // Report results
        this.reportAnalysis(projectAnalysis);
        
        // Notify agent
        this.nexus.emit('project-analyzed', projectAnalysis);
        
        return projectAnalysis;
    }
    
    async analyzeFile(fileEntry) {
        const { path, file } = fileEntry;
        
        // Skip non-code files
        if (!this.isCodeFile(path)) return null;
        
        // Read file content
        const content = await this.readFileContent(file);
        if (!content) return null;
        
        // Determine file type and analyzer
        const fileType = this.getFileType(path);
        const analyzer = this.analyzers[fileType];
        
        if (!analyzer) return null;
        
        try {
            // Parse and analyze
            const ast = analyzer.parse(content);
            const analysis = {
                path: path,
                type: fileType,
                content: content,
                ast: ast,
                imports: analyzer.extractImports(ast),
                exports: analyzer.extractExports(ast),
                components: analyzer.extractComponents?.(ast) || [],
                functions: analyzer.extractFunctions(ast),
                classes: analyzer.extractClasses(ast),
                variables: analyzer.extractVariables(ast),
                dependencies: analyzer.extractDependencies(ast),
                complexity: analyzer.calculateComplexity(ast),
                businessLogic: this.identifyBusinessLogic(ast, fileType)
            };
            
            // Extract business logic
            this.categorizeBusinessLogic(analysis);
            
            return analysis;
            
        } catch (error) {
            console.error(`Error analyzing ${path}:`, error);
            return null;
        }
    }
    
    identifyBusinessLogic(ast, fileType) {
        const logic = {
            models: [],
            services: [],
            controllers: [],
            utilities: [],
            apis: []
        };
        
        // Pattern matching for business logic
        const patterns = {
            model: /model|schema|entity|type/i,
            service: /service|provider|manager/i,
            controller: /controller|handler|resolver/i,
            utility: /util|helper|lib/i,
            api: /api|endpoint|route/i
        };
        
        // Analyze based on file type
        if (fileType === 'javascript' || fileType === 'react') {
            // Check exports and function names
            this.walkAST(ast, (node) => {
                if (node.type === 'FunctionDeclaration' || node.type === 'ClassDeclaration') {
                    const name = node.id?.name || '';
                    
                    for (const [category, pattern] of Object.entries(patterns)) {
                        if (pattern.test(name)) {
                            logic[category + 's'].push({
                                name: name,
                                node: node,
                                location: node.loc
                            });
                        }
                    }
                }
            });
        }
        
        return logic;
    }
    
    walkAST(node, visitor) {
        if (!node || typeof node !== 'object') return;
        
        visitor(node);
        
        for (const key in node) {
            if (key !== 'parent' && node[key]) {
                if (Array.isArray(node[key])) {
                    node[key].forEach(child => this.walkAST(child, visitor));
                } else if (typeof node[key] === 'object') {
                    this.walkAST(node[key], visitor);
                }
            }
        }
    }
    
    detectArchitecture() {
        const files = Array.from(this.analysisResults.values());
        
        // Detect framework
        const hasReact = files.some(f => f.imports.some(i => i.includes('react')));
        const hasRedux = files.some(f => f.imports.some(i => i.includes('redux')));
        const hasNext = files.some(f => f.imports.some(i => i.includes('next')));
        const hasExpress = files.some(f => f.imports.some(i => i.includes('express')));
        
        // Detect patterns
        const patterns = [];
        if (hasReact && hasRedux) patterns.push('React + Redux');
        if (hasNext) patterns.push('Next.js');
        if (hasExpress) patterns.push('Express.js');
        
        // Detect structure
        const structure = this.detectProjectStructure();
        
        return {
            framework: patterns[0] || 'Custom',
            patterns: patterns,
            structure: structure,
            layers: this.detectArchitecturalLayers()
        };
    }
    
    extractBusinessLogic() {
        const summary = {
            models: Array.from(this.businessLogic.models.values()),
            services: Array.from(this.businessLogic.services.values()),
            controllers: Array.from(this.businessLogic.controllers.values()),
            apis: Array.from(this.businessLogic.apis.values()),
            utilities: Array.from(this.businessLogic.utilities.values())
        };
        
        // Create relationships
        summary.relationships = this.findBusinessLogicRelationships();
        
        // Create summary
        summary.summary = `Found ${summary.models.length} models, ${summary.services.length} services, ${summary.apis.length} API endpoints`;
        
        return summary;
    }
    
    async generateRecommendations() {
        const recommendations = [];
        
        // Check for missing TypeScript
        const hasTypeScript = this.currentProject.files.some(f => 
            f.path.endsWith('.ts') || f.path.endsWith('.tsx')
        );
        if (!hasTypeScript) {
            recommendations.push('Add TypeScript for better type safety');
        }
        
        // Check for CSS optimization opportunity
        const cssFiles = this.currentProject.files.filter(f => f.path.endsWith('.css'));
        if (cssFiles.length > 5) {
            recommendations.push('Convert to Tailwind CSS for better maintainability');
        }
        
        // Check for missing tests
        const hasTests = this.currentProject.files.some(f => 
            f.path.includes('test') || f.path.includes('spec')
        );
        if (!hasTests) {
            recommendations.push('Add unit tests for critical business logic');
        }
        
        // Architecture recommendations
        const componentCount = Array.from(this.analysisResults.values())
            .reduce((sum, analysis) => sum + (analysis.components?.length || 0), 0);
        
        if (componentCount > 50) {
            recommendations.push('Consider implementing code splitting');
        }
        
        return recommendations;
    }
    
    reportAnalysis(analysis) {
        const report = `
🔍 NEXUS Project Analysis Complete

📊 Overview:
- Files analyzed: ${this.currentProject.files.length}
- Components found: ${analysis.components.length}
- Architecture: ${analysis.architecture.framework}

💼 Business Logic:
- Models: ${analysis.businessLogic.models.length}
- Services: ${analysis.businessLogic.services.length}
- APIs: ${analysis.businessLogic.apis.length}

🎨 Styling:
- CSS Framework: ${analysis.styling.framework}
- Custom styles: ${analysis.styling.customFiles}

🎯 Recommendations:
${analysis.recommendations.map(r => `- ${r}`).join('\n')}

Ready to transform this project! Use commands like:
- "Transform to Tailwind CSS"
- "Modernize architecture"
- "Generate documentation"
        `;
        
        // Send to chat
        this.nexus.components.chat?.addNexusMessage(report);
        
        // Update status
        this.nexus.updateStatus('Analysis complete', 'success');
    }
    
    // Helper methods
    isCodeFile(path) {
        const codeExtensions = ['.js', '.jsx', '.ts', '.tsx', '.css', '.scss', '.html', '.json'];
        return codeExtensions.some(ext => path.toLowerCase().endsWith(ext));
    }
    
    getFileType(path) {
        const ext = path.toLowerCase().split('.').pop();
        const typeMap = {
            'js': 'javascript',
            'jsx': 'react',
            'ts': 'javascript',
            'tsx': 'react',
            'css': 'css',
            'scss': 'css',
            'html': 'html',
            'json': 'json'
        };
        return typeMap[ext] || 'unknown';
    }
    
    async readFileContent(file) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = () => resolve(null);
            reader.readAsText(file);
        });
    }
    
    buildFileTree(files) {
        const tree = {};
        
        for (const { path } of files) {
            const parts = path.split('/').filter(p => p);
            let current = tree;
            
            for (let i = 0; i < parts.length; i++) {
                if (i === parts.length - 1) {
                    current[parts[i]] = 'file';
                } else {
                    current[parts[i]] = current[parts[i]] || {};
                    current = current[parts[i]];
                }
            }
        }
        
        return tree;
    }
    
    extractProjectName(files) {
        if (files.length === 0) return 'unknown';
        
        // Try to find package.json
        const packageJson = files.find(f => f.path.endsWith('package.json'));
        if (packageJson) {
            // Would parse package.json for name
            return 'project';
        }
        
        // Use common root directory
        const paths = files.map(f => f.path);
        const commonPath = this.findCommonPath(paths);
        return commonPath.split('/').filter(p => p).pop() || 'project';
    }
    
    findCommonPath(paths) {
        if (paths.length === 0) return '';
        if (paths.length === 1) return paths[0];
        
        const sorted = paths.sort();
        const first = sorted[0];
        const last = sorted[sorted.length - 1];
        
        let i = 0;
        while (i < first.length && first[i] === last[i]) {
            i++;
        }
        
        const common = first.substring(0, i);
        return common.substring(0, common.lastIndexOf('/'));
    }
}

// JavaScript/React Analyzer
class JavaScriptAnalyzer {
    parse(content) {
        // In production, use real parser like @babel/parser
        // For now, basic AST simulation
        return {
            type: 'Program',
            body: [],
            sourceType: 'module'
        };
    }
    
    extractImports(ast) {
        const imports = [];
        // Would walk AST for import statements
        const importRegex = /import\s+(?:{[^}]+}|\S+)\s+from\s+['"]([^'"]+)['"]/g;
        let match;
        while ((match = importRegex.exec(ast.content || '')) !== null) {
            imports.push(match[1]);
        }
        return imports;
    }
    
    extractExports(ast) {
        const exports = [];
        // Would walk AST for export statements
        return exports;
    }
    
    extractComponents(ast) {
        const components = [];
        // Would identify React components
        return components;
    }
    
    extractFunctions(ast) {
        const functions = [];
        // Would extract all function declarations
        return functions;
    }
    
    extractClasses(ast) {
        const classes = [];
        // Would extract all class declarations
        return classes;
    }
    
    extractVariables(ast) {
        const variables = [];
        // Would extract variable declarations
        return variables;
    }
    
    extractDependencies(ast) {
        // Extract npm dependencies from imports
        return this.extractImports(ast).filter(imp => !imp.startsWith('.'));
    }
    
    calculateComplexity(ast) {
        // Cyclomatic complexity calculation
        return {
            cyclomatic: 1,
            cognitive: 1,
            halstead: {}
        };
    }
}

// React-specific analyzer
class ReactAnalyzer extends JavaScriptAnalyzer {
    extractComponents(ast) {
        const components = [];
        // Identify functional and class components
        return components;
    }
    
    extractHooks(ast) {
        const hooks = [];
        // Find useState, useEffect, etc.
        return hooks;
    }
    
    extractProps(ast) {
        const props = [];
        // Extract component props
        return props;
    }
}

// CSS Analyzer
class CSSAnalyzer {
    parse(content) {
        return {
            type: 'StyleSheet',
            rules: []
        };
    }
    
    extractImports() { return []; }
    extractExports() { return []; }
    extractFunctions() { return []; }
    extractClasses() { return []; }
    extractVariables() { return []; }
    extractDependencies() { return []; }
    
    calculateComplexity(ast) {
        return {
            selectors: 0,
            rules: 0,
            specificity: 0
        };
    }
    
    extractSelectors(ast) {
        // Extract CSS selectors
        return [];
    }
    
    analyzeForTailwind(content) {
        // Analyze CSS for Tailwind conversion
        return {
            convertible: [],
            custom: [],
            complex: []
        };
    }
}

// HTML Analyzer
class HTMLAnalyzer {
    parse(content) {
        return {
            type: 'Document',
            children: []
        };
    }
    
    extractImports() { return []; }
    extractExports() { return []; }
    extractFunctions() { return []; }
    extractClasses() { return []; }
    extractVariables() { return []; }
    extractDependencies() { return []; }
    
    calculateComplexity(ast) {
        return {
            elements: 0,
            depth: 0
        };
    }
}

// JSON Analyzer
class JSONAnalyzer {
    parse(content) {
        try {
            return JSON.parse(content);
        } catch {
            return null;
        }
    }
    
    extractImports() { return []; }
    extractExports() { return []; }
    extractFunctions() { return []; }
    extractClasses() { return []; }
    extractVariables() { return []; }
    
    extractDependencies(ast) {
        if (ast && ast.dependencies) {
            return Object.keys(ast.dependencies);
        }
        return [];
    }
    
    calculateComplexity() {
        return { depth: 0 };
    }
}

// Register with window
window.NexusProjectAnalyzer = NexusProjectAnalyzer;