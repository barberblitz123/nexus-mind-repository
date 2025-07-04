// NEXUS Visual Integration - High-Level Vision System
class NexusVisualIntegration {
    constructor(nexusCore) {
        this.nexus = nexusCore;
        this.video = null;
        this.canvas = null;
        this.ctx = null;
        this.stream = null;
        this.isActive = false;
        this.processing = false;
        
        // Enhanced vision capabilities
        this.visionCapabilities = {
            objectDetection: true,
            textRecognition: true,
            faceDetection: true,
            sceneAnalysis: true,
            colorAnalysis: true,
            motionDetection: true,
            softwareAnalysis: true
        };
        
        // Vision state
        this.currentAnalysis = null;
        this.visualMemory = [];
        this.maxMemoryFrames = 50;
        this.detectedObjects = new Map();
        this.sceneContext = {
            type: 'unknown',
            confidence: 0,
            description: ''
        };
        
        // Offline AI models (simulated for demo)
        this.offlineModels = {
            objectDetection: new OfflineObjectDetector(),
            textExtraction: new OfflineTextExtractor(),
            sceneClassifier: new OfflineSceneClassifier()
        };
        
        // Frame processing
        this.frameInterval = 100; // Process every 100ms for real-time
        this.lastFrameTime = 0;
        this.analysisQueue = [];
    }

    async initialize() {
        console.log('👁️ Initializing NEXUS Visual Integration...');
        
        // Create visual panel UI
        await this.createVisualPanel();
        
        // Initialize offline models
        await this.initializeOfflineModels();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load vision preferences
        this.loadVisionSettings();
        
        console.log('✅ Visual system ready');
    }

    async createVisualPanel() {
        // Add visual panel to the unified interface
        const visualPanel = document.createElement('div');
        visualPanel.id = 'visual-panel';
        visualPanel.className = 'visual-panel-overlay';
        visualPanel.innerHTML = `
            <div class="visual-panel-header">
                <h3>👁️ NEXUS Vision</h3>
                <div class="visual-controls">
                    <button id="toggle-vision" class="vision-btn" title="Toggle Vision">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button id="capture-screen" class="vision-btn" title="Capture Screen">
                        <i class="fas fa-desktop"></i>
                    </button>
                    <button id="vision-settings" class="vision-btn" title="Settings">
                        <i class="fas fa-cog"></i>
                    </button>
                    <button id="close-vision" class="vision-btn" title="Minimize">
                        <i class="fas fa-minus"></i>
                    </button>
                </div>
            </div>
            
            <div class="visual-panel-content">
                <div class="vision-display">
                    <video id="vision-video" autoplay muted playsinline></video>
                    <canvas id="vision-canvas"></canvas>
                    <div id="vision-overlay" class="vision-overlay"></div>
                    <div class="vision-status">
                        <span id="vision-status-text">Initializing...</span>
                    </div>
                </div>
                
                <div class="vision-analysis">
                    <div class="analysis-tabs">
                        <button class="tab-btn active" data-tab="objects">Objects</button>
                        <button class="tab-btn" data-tab="text">Text</button>
                        <button class="tab-btn" data-tab="scene">Scene</button>
                        <button class="tab-btn" data-tab="software">Software</button>
                    </div>
                    
                    <div class="analysis-content">
                        <div id="objects-tab" class="tab-content active">
                            <h4>Detected Objects</h4>
                            <ul id="detected-objects" class="detection-list"></ul>
                        </div>
                        
                        <div id="text-tab" class="tab-content">
                            <h4>Extracted Text</h4>
                            <div id="extracted-text" class="text-content"></div>
                        </div>
                        
                        <div id="scene-tab" class="tab-content">
                            <h4>Scene Analysis</h4>
                            <div id="scene-analysis" class="scene-info"></div>
                        </div>
                        
                        <div id="software-tab" class="tab-content">
                            <h4>Software Analysis</h4>
                            <div id="software-analysis" class="software-info"></div>
                        </div>
                    </div>
                </div>
                
                <div class="vision-actions">
                    <button id="start-project" class="action-btn">
                        <i class="fas fa-rocket"></i> Start Project from Vision
                    </button>
                    <button id="analyze-software" class="action-btn">
                        <i class="fas fa-code"></i> Analyze Software
                    </button>
                    <button id="extract-colors" class="action-btn">
                        <i class="fas fa-palette"></i> Extract Colors
                    </button>
                </div>
            </div>
        `;
        
        // Add to main container but hidden initially
        document.body.appendChild(visualPanel);
        
        // Get canvas and video elements
        this.video = document.getElementById('vision-video');
        this.canvas = document.getElementById('vision-canvas');
        this.ctx = this.canvas.getContext('2d');
        
        // Add styles
        this.addVisualStyles();
    }

    addVisualStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .visual-panel-overlay {
                position: fixed;
                top: 70px;
                right: 20px;
                width: 480px;
                height: 600px;
                background: var(--bg-secondary);
                border: 2px solid var(--accent-primary);
                border-radius: 12px;
                display: none;
                flex-direction: column;
                z-index: 1000;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
            }
            
            .visual-panel-overlay.active {
                display: flex;
            }
            
            .visual-panel-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px;
                border-bottom: 1px solid var(--border-color);
                cursor: move;
            }
            
            .visual-controls {
                display: flex;
                gap: 10px;
            }
            
            .vision-btn {
                background: none;
                border: 1px solid var(--border-color);
                color: var(--text-primary);
                width: 32px;
                height: 32px;
                border-radius: 4px;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .vision-btn:hover {
                background: var(--accent-primary);
                color: var(--bg-primary);
            }
            
            .visual-panel-content {
                flex: 1;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .vision-display {
                position: relative;
                height: 240px;
                background: #000;
                overflow: hidden;
            }
            
            #vision-video, #vision-canvas {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }
            
            #vision-canvas {
                position: absolute;
                top: 0;
                left: 0;
                pointer-events: none;
            }
            
            .vision-overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                pointer-events: none;
            }
            
            .detection-box {
                position: absolute;
                border: 2px solid var(--accent-primary);
                background: rgba(0, 255, 136, 0.1);
                transition: all 0.3s ease;
            }
            
            .detection-label {
                position: absolute;
                top: -25px;
                left: 0;
                background: var(--accent-primary);
                color: var(--bg-primary);
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                white-space: nowrap;
            }
            
            .vision-status {
                position: absolute;
                top: 10px;
                left: 10px;
                background: rgba(0, 0, 0, 0.8);
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                color: var(--accent-primary);
            }
            
            .vision-analysis {
                flex: 1;
                display: flex;
                flex-direction: column;
                border-top: 1px solid var(--border-color);
            }
            
            .analysis-tabs {
                display: flex;
                border-bottom: 1px solid var(--border-color);
            }
            
            .tab-btn {
                flex: 1;
                padding: 10px;
                background: none;
                border: none;
                color: var(--text-secondary);
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .tab-btn.active {
                color: var(--accent-primary);
                border-bottom: 2px solid var(--accent-primary);
            }
            
            .analysis-content {
                flex: 1;
                overflow-y: auto;
                padding: 15px;
            }
            
            .tab-content {
                display: none;
            }
            
            .tab-content.active {
                display: block;
            }
            
            .detection-list {
                list-style: none;
                padding: 0;
            }
            
            .detection-item {
                display: flex;
                justify-content: space-between;
                padding: 8px;
                margin-bottom: 5px;
                background: var(--bg-tertiary);
                border-radius: 4px;
            }
            
            .detection-confidence {
                color: var(--accent-primary);
                font-weight: bold;
            }
            
            .vision-actions {
                display: flex;
                gap: 10px;
                padding: 15px;
                border-top: 1px solid var(--border-color);
            }
            
            .action-btn {
                flex: 1;
                padding: 10px;
                background: var(--bg-tertiary);
                border: 1px solid var(--border-color);
                color: var(--text-primary);
                border-radius: 6px;
                cursor: pointer;
                transition: all 0.3s ease;
                font-size: 12px;
            }
            
            .action-btn:hover {
                background: var(--accent-primary);
                color: var(--bg-primary);
                transform: translateY(-2px);
            }
            
            .minimized {
                height: 50px !important;
                overflow: hidden;
            }
            
            .minimized .visual-panel-content {
                display: none;
            }
            
            /* Draggable styles */
            .dragging {
                opacity: 0.8;
                cursor: move;
            }
        `;
        document.head.appendChild(style);
    }

    async initializeOfflineModels() {
        // Initialize offline AI models for standalone operation
        console.log('🧠 Loading offline vision models...');
        
        // These would be actual TensorFlow.js or ONNX models in production
        // For now, we'll use sophisticated algorithms that work offline
        
        this.offlineModels.ready = true;
        console.log('✅ Offline models ready');
    }

    setupEventListeners() {
        // Vision toggle
        const visionBtn = document.querySelector('#vision-toggle');
        visionBtn?.addEventListener('click', () => {
            this.toggleVision();
        });
        
        // Panel controls
        document.getElementById('toggle-vision')?.addEventListener('click', () => {
            this.toggleCamera();
        });
        
        document.getElementById('capture-screen')?.addEventListener('click', () => {
            this.captureScreen();
        });
        
        document.getElementById('close-vision')?.addEventListener('click', () => {
            this.minimizePanel();
        });
        
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
        
        // Action buttons
        document.getElementById('start-project')?.addEventListener('click', () => {
            this.startProjectFromVision();
        });
        
        document.getElementById('analyze-software')?.addEventListener('click', () => {
            this.analyzeSoftwareInterface();
        });
        
        document.getElementById('extract-colors')?.addEventListener('click', () => {
            this.extractColorPalette();
        });
        
        // Make panel draggable
        this.makePanelDraggable();
        
        // Listen for voice commands
        this.nexus.on('voice-command', (e) => {
            this.handleVoiceCommand(e.detail);
        });
    }

    async toggleVision() {
        const panel = document.getElementById('visual-panel');
        if (panel.classList.contains('active')) {
            panel.classList.remove('active');
            this.stopCamera();
        } else {
            panel.classList.add('active');
            await this.startCamera();
        }
    }

    async startCamera() {
        try {
            const constraints = {
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user'
                }
            };
            
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.video.srcObject = this.stream;
            
            this.video.onloadedmetadata = () => {
                this.canvas.width = this.video.videoWidth;
                this.canvas.height = this.video.videoHeight;
                this.isActive = true;
                this.startProcessing();
                this.updateStatus('Vision active');
            };
            
        } catch (error) {
            console.error('Camera access error:', error);
            this.updateStatus('Camera access denied - Demo mode');
            this.startDemoMode();
        }
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        this.isActive = false;
        this.processing = false;
    }

    startProcessing() {
        this.processing = true;
        
        const processFrame = (timestamp) => {
            if (!this.processing) return;
            
            // Throttle processing
            if (timestamp - this.lastFrameTime < this.frameInterval) {
                requestAnimationFrame(processFrame);
                return;
            }
            
            this.lastFrameTime = timestamp;
            
            // Process current frame
            this.processFrame();
            
            requestAnimationFrame(processFrame);
        };
        
        requestAnimationFrame(processFrame);
    }

    async processFrame() {
        if (!this.video || !this.ctx) return;
        
        // Draw current frame
        this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        
        // Get image data
        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        
        // Perform multiple analyses in parallel
        const [objects, text, scene, colors] = await Promise.all([
            this.detectObjects(imageData),
            this.extractText(imageData),
            this.analyzeScene(imageData),
            this.analyzeColors(imageData)
        ]);
        
        // Update current analysis
        this.currentAnalysis = {
            objects,
            text,
            scene,
            colors,
            timestamp: Date.now()
        };
        
        // Update displays
        this.updateAnalysisDisplay();
        
        // Draw detection overlays
        this.drawDetections(objects);
        
        // Update visual memory
        this.updateVisualMemory();
        
        // Emit vision update
        this.nexus.emit('vision-update', this.currentAnalysis);
    }

    async detectObjects(imageData) {
        // Use offline object detection
        const objects = await this.offlineModels.objectDetection.detect(imageData);
        
        // Update detected objects map
        objects.forEach(obj => {
            this.detectedObjects.set(obj.id, {
                ...obj,
                lastSeen: Date.now()
            });
        });
        
        return objects;
    }

    async extractText(imageData) {
        // Use offline OCR
        const text = await this.offlineModels.textExtraction.extract(imageData);
        return text;
    }

    async analyzeScene(imageData) {
        // Use offline scene classifier
        const scene = await this.offlineModels.sceneClassifier.classify(imageData);
        this.sceneContext = scene;
        return scene;
    }

    analyzeColors(imageData) {
        const data = imageData.data;
        const colorMap = new Map();
        
        // Sample colors
        for (let i = 0; i < data.length; i += 4 * 10) { // Sample every 10th pixel
            const r = Math.floor(data[i] / 32) * 32;
            const g = Math.floor(data[i + 1] / 32) * 32;
            const b = Math.floor(data[i + 2] / 32) * 32;
            const key = `${r},${g},${b}`;
            
            colorMap.set(key, (colorMap.get(key) || 0) + 1);
        }
        
        // Get dominant colors
        const sortedColors = Array.from(colorMap.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(([color, count]) => {
                const [r, g, b] = color.split(',').map(Number);
                return {
                    rgb: `rgb(${r}, ${g}, ${b})`,
                    hex: this.rgbToHex(r, g, b),
                    count
                };
            });
        
        return {
            dominant: sortedColors,
            palette: this.generateColorPalette(sortedColors)
        };
    }

    rgbToHex(r, g, b) {
        return '#' + [r, g, b].map(x => {
            const hex = x.toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        }).join('');
    }

    generateColorPalette(colors) {
        // Generate a harmonious color palette
        return colors.map(color => ({
            primary: color.hex,
            secondary: this.adjustColor(color.hex, 0.2),
            accent: this.adjustColor(color.hex, -0.3)
        }));
    }

    adjustColor(hex, factor) {
        // Adjust color brightness
        const rgb = hex.match(/\w\w/g).map(x => parseInt(x, 16));
        const adjusted = rgb.map(c => Math.max(0, Math.min(255, c + (c * factor))));
        return this.rgbToHex(...adjusted);
    }

    drawDetections(objects) {
        const overlay = document.getElementById('vision-overlay');
        overlay.innerHTML = '';
        
        objects.forEach(obj => {
            const box = document.createElement('div');
            box.className = 'detection-box';
            
            // Scale coordinates to video display size
            const scaleX = this.video.offsetWidth / this.canvas.width;
            const scaleY = this.video.offsetHeight / this.canvas.height;
            
            box.style.left = `${obj.bbox.x * scaleX}px`;
            box.style.top = `${obj.bbox.y * scaleY}px`;
            box.style.width = `${obj.bbox.width * scaleX}px`;
            box.style.height = `${obj.bbox.height * scaleY}px`;
            
            const label = document.createElement('div');
            label.className = 'detection-label';
            label.textContent = `${obj.class} ${Math.round(obj.confidence * 100)}%`;
            box.appendChild(label);
            
            overlay.appendChild(box);
        });
    }

    updateAnalysisDisplay() {
        // Update objects tab
        const objectsList = document.getElementById('detected-objects');
        objectsList.innerHTML = '';
        
        this.currentAnalysis.objects.forEach(obj => {
            const li = document.createElement('li');
            li.className = 'detection-item';
            li.innerHTML = `
                <span>${obj.class}</span>
                <span class="detection-confidence">${Math.round(obj.confidence * 100)}%</span>
            `;
            objectsList.appendChild(li);
        });
        
        // Update text tab
        const textContent = document.getElementById('extracted-text');
        textContent.innerHTML = this.currentAnalysis.text.blocks.map(block => 
            `<p>${block.text}</p>`
        ).join('');
        
        // Update scene tab
        const sceneInfo = document.getElementById('scene-analysis');
        sceneInfo.innerHTML = `
            <p><strong>Scene Type:</strong> ${this.currentAnalysis.scene.type}</p>
            <p><strong>Confidence:</strong> ${Math.round(this.currentAnalysis.scene.confidence * 100)}%</p>
            <p><strong>Description:</strong> ${this.currentAnalysis.scene.description}</p>
            <p><strong>Detected Elements:</strong> ${this.currentAnalysis.scene.elements.join(', ')}</p>
        `;
        
        // Update NEXUS with vision data
        if (this.currentAnalysis.objects.length > 0 || this.currentAnalysis.text.blocks.length > 0) {
            this.nexus.emit('vision-analysis', this.currentAnalysis);
        }
    }

    async captureScreen() {
        try {
            // Use screen capture API
            const screenStream = await navigator.mediaDevices.getDisplayMedia({
                video: {
                    mediaSource: 'screen'
                }
            });
            
            // Temporarily switch to screen
            const oldStream = this.stream;
            this.video.srcObject = screenStream;
            
            // Capture after a moment
            setTimeout(async () => {
                await this.analyzeSoftwareInterface();
                
                // Switch back to camera
                screenStream.getTracks().forEach(track => track.stop());
                this.video.srcObject = oldStream;
            }, 500);
            
        } catch (error) {
            console.error('Screen capture error:', error);
            this.nexus.showNotification('Screen capture requires permission', 'warning');
        }
    }

    async analyzeSoftwareInterface() {
        if (!this.currentAnalysis) return;
        
        // Analyze for software UI elements
        const analysis = {
            uiElements: [],
            layout: '',
            framework: '',
            components: []
        };
        
        // Detect UI patterns
        if (this.currentAnalysis.text.blocks.length > 0) {
            // Look for common UI text
            const allText = this.currentAnalysis.text.blocks.map(b => b.text).join(' ').toLowerCase();
            
            // Detect framework
            if (allText.includes('react')) analysis.framework = 'React';
            else if (allText.includes('vue')) analysis.framework = 'Vue';
            else if (allText.includes('angular')) analysis.framework = 'Angular';
            
            // Detect UI elements
            if (allText.includes('button')) analysis.uiElements.push('buttons');
            if (allText.includes('input') || allText.includes('form')) analysis.uiElements.push('forms');
            if (allText.includes('menu') || allText.includes('nav')) analysis.uiElements.push('navigation');
            if (allText.includes('table') || allText.includes('grid')) analysis.uiElements.push('data display');
        }
        
        // Analyze layout from objects
        if (this.currentAnalysis.objects.length > 0) {
            const positions = this.currentAnalysis.objects.map(obj => obj.bbox);
            
            // Simple layout detection
            const avgY = positions.reduce((sum, p) => sum + p.y, 0) / positions.length;
            const avgX = positions.reduce((sum, p) => sum + p.x, 0) / positions.length;
            
            if (positions.some(p => p.x < this.canvas.width * 0.2)) {
                analysis.layout = 'sidebar layout';
            } else if (positions.every(p => Math.abs(p.y - avgY) < 50)) {
                analysis.layout = 'horizontal layout';
            } else {
                analysis.layout = 'grid layout';
            }
        }
        
        // Generate project suggestion
        const suggestion = this.generateProjectSuggestion(analysis);
        
        // Update software tab
        const softwareInfo = document.getElementById('software-analysis');
        softwareInfo.innerHTML = `
            <p><strong>Detected Framework:</strong> ${analysis.framework || 'Unknown'}</p>
            <p><strong>UI Elements:</strong> ${analysis.uiElements.join(', ') || 'None detected'}</p>
            <p><strong>Layout Type:</strong> ${analysis.layout || 'Unknown'}</p>
            <hr>
            <p><strong>Project Suggestion:</strong></p>
            <p>${suggestion}</p>
        `;
        
        // Switch to software tab
        this.switchTab('software');
        
        // Notify chat
        this.nexus.components.chat?.addNexusMessage(
            `I analyzed the software interface. ${suggestion}`,
            { silent: true }
        );
    }

    generateProjectSuggestion(analysis) {
        let suggestion = "Based on what I see, I suggest creating ";
        
        if (analysis.framework) {
            suggestion += `a ${analysis.framework} application `;
        } else {
            suggestion += "a web application ";
        }
        
        if (analysis.uiElements.includes('forms')) {
            suggestion += "with form handling and validation ";
        }
        
        if (analysis.uiElements.includes('data display')) {
            suggestion += "with data visualization components ";
        }
        
        if (analysis.layout) {
            suggestion += `using a ${analysis.layout} `;
        }
        
        suggestion += "similar to what's displayed. Would you like me to generate the initial code structure?";
        
        return suggestion;
    }

    async startProjectFromVision() {
        if (!this.currentAnalysis) {
            this.nexus.showNotification('Please wait for vision analysis', 'warning');
            return;
        }
        
        // Generate project based on what we see
        let projectCode = '';
        let projectDescription = '';
        
        // If we detected a software interface
        if (this.currentAnalysis.scene.type === 'screen' || this.currentAnalysis.scene.type === 'interface') {
            projectDescription = "Creating a web interface based on the visual analysis...";
            projectCode = this.generateInterfaceCode();
        }
        // If we detected objects
        else if (this.currentAnalysis.objects.length > 0) {
            const mainObject = this.currentAnalysis.objects[0].class;
            projectDescription = `Creating an application related to ${mainObject}...`;
            projectCode = this.generateObjectBasedCode(mainObject);
        }
        // If we detected text
        else if (this.currentAnalysis.text.blocks.length > 0) {
            projectDescription = "Creating a text processing application...";
            projectCode = this.generateTextBasedCode();
        }
        // Default creative project
        else {
            projectDescription = "Creating a creative project based on the scene...";
            projectCode = this.generateCreativeCode();
        }
        
        // Add to IDE
        this.nexus.components.ide?.createNewFile();
        
        // Send to chat
        this.nexus.components.chat?.addNexusMessage(projectDescription);
        
        // Add code to editor
        setTimeout(() => {
            this.nexus.emit('add-code', { code: projectCode, language: 'javascript' });
        }, 500);
    }

    generateInterfaceCode() {
        return `// Generated from NEXUS Vision Analysis
// Detected: ${this.currentAnalysis.scene.description}

import React, { useState, useEffect } from 'react';
import './App.css';

const VisionGeneratedApp = () => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    
    // Detected colors from vision
    const colorPalette = ${JSON.stringify(this.currentAnalysis.colors.dominant.slice(0, 3), null, 4)};
    
    useEffect(() => {
        // Initialize based on vision analysis
        console.log('🧬 NEXUS Vision detected:', ${JSON.stringify(this.currentAnalysis.scene)});
        setLoading(false);
    }, []);
    
    return (
        <div className="app" style={{
            backgroundColor: colorPalette[0]?.hex || '#1a1a1a',
            minHeight: '100vh'
        }}>
            <header style={{
                backgroundColor: colorPalette[1]?.hex || '#2a2a2a',
                padding: '20px'
            }}>
                <h1>Vision-Generated Interface</h1>
                <p>Created from: ${this.currentAnalysis.scene.type}</p>
            </header>
            
            <main style={{ padding: '20px' }}>
                ${this.currentAnalysis.objects.map(obj => `
                <div className="${obj.class}-section">
                    <h2>${obj.class} Component</h2>
                    <p>Confidence: ${Math.round(obj.confidence * 100)}%</p>
                </div>`).join('')}
            </main>
        </div>
    );
};

export default VisionGeneratedApp;`;
    }

    generateObjectBasedCode(objectType) {
        return `// NEXUS Vision detected: ${objectType}
// Creating an interactive ${objectType} application

class ${this.capitalizeFirst(objectType)}App {
    constructor() {
        this.name = "${objectType} Vision App";
        this.detectedAt = new Date();
        this.visionData = ${JSON.stringify(this.currentAnalysis, null, 4)};
    }
    
    initialize() {
        console.log(\`Initializing \${this.name}\`);
        console.log('Based on NEXUS vision analysis');
        
        // Create interactive elements based on detected object
        this.createInterface();
    }
    
    createInterface() {
        const container = document.createElement('div');
        container.className = 'vision-app';
        
        // Add detected object visualization
        const visualization = this.createVisualization();
        container.appendChild(visualization);
        
        // Add controls
        const controls = this.createControls();
        container.appendChild(controls);
        
        document.body.appendChild(container);
    }
    
    createVisualization() {
        const viz = document.createElement('div');
        viz.innerHTML = \`
            <h2>Interactive ${objectType}</h2>
            <canvas id="object-canvas"></canvas>
            <div class="object-info">
                <p>Detected with \${${Math.round(this.currentAnalysis.objects[0]?.confidence * 100 || 0)}}% confidence</p>
                <p>Scene: \${this.visionData.scene.description}</p>
            </div>
        \`;
        return viz;
    }
    
    createControls() {
        const controls = document.createElement('div');
        controls.className = 'vision-controls';
        controls.innerHTML = \`
            <button onclick="app.analyze()">Analyze More</button>
            <button onclick="app.interact()">Interact</button>
            <button onclick="app.export()">Export Data</button>
        \`;
        return controls;
    }
    
    analyze() {
        console.log('Analyzing ${objectType}...', this.visionData);
        // Add analysis logic
    }
    
    interact() {
        console.log('Interacting with ${objectType}...');
        // Add interaction logic
    }
    
    export() {
        const data = {
            object: '${objectType}',
            timestamp: this.detectedAt,
            analysis: this.visionData
        };
        console.log('Exporting:', data);
        // Add export logic
    }
}

// Initialize the app
const app = new ${this.capitalizeFirst(objectType)}App();
app.initialize();`;
    }

    generateTextBasedCode() {
        const extractedText = this.currentAnalysis.text.blocks.map(b => b.text).join(' ');
        
        return `// NEXUS Vision Text Extraction App
// Extracted text: "${extractedText.substring(0, 100)}..."

class TextProcessorApp {
    constructor() {
        this.extractedText = ${JSON.stringify(extractedText)};
        this.textBlocks = ${JSON.stringify(this.currentAnalysis.text.blocks)};
    }
    
    async processText() {
        console.log('Processing extracted text...');
        
        // Analyze text structure
        const analysis = {
            wordCount: this.extractedText.split(/\\s+/).length,
            sentences: this.extractedText.split(/[.!?]+/).length,
            blocks: this.textBlocks.length,
            language: this.detectLanguage()
        };
        
        return analysis;
    }
    
    detectLanguage() {
        // Simple language detection
        const commonEnglishWords = ['the', 'is', 'at', 'which', 'on'];
        const words = this.extractedText.toLowerCase().split(/\\s+/);
        const englishCount = words.filter(w => commonEnglishWords.includes(w)).length;
        
        return englishCount > words.length * 0.02 ? 'English' : 'Unknown';
    }
    
    generateSummary() {
        const sentences = this.extractedText.split(/[.!?]+/).filter(s => s.trim());
        return sentences.slice(0, 3).join('. ') + '.';
    }
    
    extractKeywords() {
        const words = this.extractedText.toLowerCase().split(/\\s+/);
        const wordFreq = {};
        
        words.forEach(word => {
            if (word.length > 4) {
                wordFreq[word] = (wordFreq[word] || 0) + 1;
            }
        });
        
        return Object.entries(wordFreq)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10)
            .map(([word]) => word);
    }
}

// Create and run the app
const textApp = new TextProcessorApp();
textApp.processText().then(analysis => {
    console.log('Text Analysis:', analysis);
    console.log('Summary:', textApp.generateSummary());
    console.log('Keywords:', textApp.extractKeywords());
});`;
    }

    generateCreativeCode() {
        const colors = this.currentAnalysis.colors.dominant.slice(0, 5);
        
        return `// NEXUS Vision Creative Generator
// Inspired by the scene: ${this.currentAnalysis.scene.description}

class CreativeVisionApp {
    constructor() {
        this.colors = ${JSON.stringify(colors, null, 4)};
        this.scene = ${JSON.stringify(this.currentAnalysis.scene)};
        this.canvas = null;
        this.ctx = null;
    }
    
    initialize() {
        // Create canvas
        this.canvas = document.createElement('canvas');
        this.canvas.width = 800;
        this.canvas.height = 600;
        this.ctx = this.canvas.getContext('2d');
        
        document.body.appendChild(this.canvas);
        
        // Start creative generation
        this.generateArt();
        this.animate();
    }
    
    generateArt() {
        // Create gradient background from detected colors
        const gradient = this.ctx.createLinearGradient(0, 0, this.canvas.width, this.canvas.height);
        this.colors.forEach((color, i) => {
            gradient.addColorStop(i / this.colors.length, color.hex);
        });
        
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Add creative elements based on scene
        this.drawSceneElements();
    }
    
    drawSceneElements() {
        const elements = this.scene.elements || [];
        
        elements.forEach((element, i) => {
            const x = Math.random() * this.canvas.width;
            const y = Math.random() * this.canvas.height;
            const size = 20 + Math.random() * 50;
            
            this.ctx.fillStyle = this.colors[i % this.colors.length]?.hex || '#fff';
            this.ctx.globalAlpha = 0.7;
            
            // Draw different shapes based on scene
            if (this.scene.type === 'nature') {
                // Organic shapes
                this.drawOrganic(x, y, size);
            } else if (this.scene.type === 'urban') {
                // Geometric shapes
                this.drawGeometric(x, y, size);
            } else {
                // Abstract shapes
                this.drawAbstract(x, y, size);
            }
        });
        
        this.ctx.globalAlpha = 1;
    }
    
    drawOrganic(x, y, size) {
        // Draw organic, nature-inspired shapes
        this.ctx.beginPath();
        for (let i = 0; i < 6; i++) {
            const angle = (i / 6) * Math.PI * 2;
            const radius = size + Math.sin(angle * 3) * size * 0.3;
            const px = x + Math.cos(angle) * radius;
            const py = y + Math.sin(angle) * radius;
            
            if (i === 0) this.ctx.moveTo(px, py);
            else this.ctx.lineTo(px, py);
        }
        this.ctx.closePath();
        this.ctx.fill();
    }
    
    drawGeometric(x, y, size) {
        // Draw geometric, urban-inspired shapes
        this.ctx.fillRect(x - size/2, y - size/2, size, size);
        this.ctx.strokeStyle = this.colors[0]?.hex || '#fff';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(x - size/2 - 5, y - size/2 - 5, size + 10, size + 10);
    }
    
    drawAbstract(x, y, size) {
        // Draw abstract shapes
        this.ctx.beginPath();
        this.ctx.arc(x, y, size, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Add inner details
        this.ctx.beginPath();
        this.ctx.arc(x, y, size * 0.6, 0, Math.PI * 2);
        this.ctx.strokeStyle = this.colors[1]?.hex || '#fff';
        this.ctx.lineWidth = 3;
        this.ctx.stroke();
    }
    
    animate() {
        // Add subtle animation
        const time = Date.now() * 0.001;
        
        this.ctx.save();
        this.ctx.globalCompositeOperation = 'screen';
        this.ctx.globalAlpha = 0.02;
        
        // Animated elements
        for (let i = 0; i < 5; i++) {
            const x = (Math.sin(time + i) + 1) * this.canvas.width / 2;
            const y = (Math.cos(time + i * 0.7) + 1) * this.canvas.height / 2;
            
            this.ctx.fillStyle = this.colors[i % this.colors.length]?.hex || '#fff';
            this.ctx.beginPath();
            this.ctx.arc(x, y, 50, 0, Math.PI * 2);
            this.ctx.fill();
        }
        
        this.ctx.restore();
        
        requestAnimationFrame(() => this.animate());
    }
}

// Launch the creative app
const creativeApp = new CreativeVisionApp();
creativeApp.initialize();

// Log vision data
console.log('🎨 Created from NEXUS Vision:', creativeApp.scene);`;
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    extractColorPalette() {
        if (!this.currentAnalysis || !this.currentAnalysis.colors) {
            this.nexus.showNotification('No colors detected yet', 'warning');
            return;
        }
        
        const colors = this.currentAnalysis.colors.dominant;
        
        // Generate CSS variables
        const cssVars = colors.map((color, i) => 
            `--color-${i + 1}: ${color.hex};`
        ).join('\n');
        
        // Generate color palette code
        const paletteCode = `// NEXUS Vision Extracted Color Palette
// Extracted at: ${new Date().toISOString()}

const colorPalette = {
    colors: ${JSON.stringify(colors, null, 4)},
    
    // CSS Variables
    cssVariables: \`
${cssVars}
    \`,
    
    // Tailwind Config
    tailwind: {
        theme: {
            extend: {
                colors: {
${colors.map((color, i) => `                    'vision-${i + 1}': '${color.hex}',`).join('\n')}
                }
            }
        }
    },
    
    // Material UI Theme
    mui: {
        palette: {
            primary: {
                main: '${colors[0]?.hex || '#000'}',
            },
            secondary: {
                main: '${colors[1]?.hex || '#fff'}',
            },
            background: {
                default: '${colors[2]?.hex || '#f5f5f5'}',
            }
        }
    }
};

// Usage example
console.log('Extracted colors:', colorPalette.colors);
document.documentElement.style.cssText = colorPalette.cssVariables;`;
        
        // Add to IDE
        this.nexus.emit('add-code', { code: paletteCode, language: 'javascript' });
        
        // Show in chat
        this.nexus.components.chat?.addNexusMessage(
            `I extracted ${colors.length} colors from the vision feed. I've added the color palette code to the editor with CSS variables, Tailwind config, and Material UI theme options.`
        );
    }

    updateVisualMemory() {
        // Store frame in memory
        this.visualMemory.push({
            analysis: this.currentAnalysis,
            timestamp: Date.now()
        });
        
        // Limit memory size
        if (this.visualMemory.length > this.maxMemoryFrames) {
            this.visualMemory.shift();
        }
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        
        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tabName}-tab`);
        });
    }

    minimizePanel() {
        const panel = document.getElementById('visual-panel');
        panel.classList.toggle('minimized');
    }

    makePanelDraggable() {
        const panel = document.getElementById('visual-panel');
        const header = panel.querySelector('.visual-panel-header');
        let isDragging = false;
        let currentX;
        let currentY;
        let initialX;
        let initialY;
        
        header.addEventListener('mousedown', (e) => {
            if (e.target.closest('.visual-controls')) return;
            
            isDragging = true;
            panel.classList.add('dragging');
            
            initialX = e.clientX - panel.offsetLeft;
            initialY = e.clientY - panel.offsetTop;
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            
            e.preventDefault();
            currentX = e.clientX - initialX;
            currentY = e.clientY - initialY;
            
            panel.style.left = `${currentX}px`;
            panel.style.top = `${currentY}px`;
            panel.style.right = 'auto';
        });
        
        document.addEventListener('mouseup', () => {
            isDragging = false;
            panel.classList.remove('dragging');
        });
    }

    handleVoiceCommand(command) {
        const { text } = command;
        const lower = text.toLowerCase();
        
        if (lower.includes('see') || lower.includes('vision') || lower.includes('camera')) {
            this.toggleVision();
        } else if (lower.includes('capture') || lower.includes('screenshot')) {
            this.captureScreen();
        } else if (lower.includes('analyze') && lower.includes('software')) {
            this.analyzeSoftwareInterface();
        } else if (lower.includes('color')) {
            this.extractColorPalette();
        } else if (lower.includes('start project')) {
            this.startProjectFromVision();
        }
    }

    updateStatus(text) {
        const statusEl = document.getElementById('vision-status-text');
        if (statusEl) {
            statusEl.textContent = text;
        }
    }

    startDemoMode() {
        // Demo mode for when camera isn't available
        this.isActive = true;
        this.processing = true;
        
        const demoFrame = () => {
            if (!this.processing) return;
            
            // Create demo visualization
            const time = Date.now() * 0.001;
            const width = 640;
            const height = 480;
            
            this.canvas.width = width;
            this.canvas.height = height;
            
            // Create gradient background
            const gradient = this.ctx.createLinearGradient(0, 0, width, height);
            gradient.addColorStop(0, `hsl(${(time * 30) % 360}, 70%, 50%)`);
            gradient.addColorStop(1, `hsl(${(time * 30 + 180) % 360}, 70%, 40%)`);
            
            this.ctx.fillStyle = gradient;
            this.ctx.fillRect(0, 0, width, height);
            
            // Add demo objects
            for (let i = 0; i < 3; i++) {
                const x = width/2 + Math.sin(time + i * 2) * 150;
                const y = height/2 + Math.cos(time + i * 2) * 100;
                
                this.ctx.fillStyle = `hsla(${i * 120}, 70%, 60%, 0.8)`;
                this.ctx.beginPath();
                this.ctx.arc(x, y, 40, 0, Math.PI * 2);
                this.ctx.fill();
            }
            
            // Simulate object detection
            if (Math.random() > 0.95) {
                this.currentAnalysis = {
                    objects: [
                        { class: 'demo object', confidence: 0.95, bbox: { x: 100, y: 100, width: 80, height: 80 } }
                    ],
                    text: { blocks: [{ text: 'Demo Mode Active' }] },
                    scene: { type: 'demo', confidence: 1, description: 'Demo visualization', elements: ['shapes', 'colors'] },
                    colors: {
                        dominant: [
                            { rgb: 'rgb(255,0,0)', hex: '#ff0000' },
                            { rgb: 'rgb(0,255,0)', hex: '#00ff00' },
                            { rgb: 'rgb(0,0,255)', hex: '#0000ff' }
                        ]
                    }
                };
                this.updateAnalysisDisplay();
            }
            
            requestAnimationFrame(demoFrame);
        };
        
        demoFrame();
    }

    loadVisionSettings() {
        // Load saved vision preferences
        const saved = localStorage.getItem('nexus-vision-settings');
        if (saved) {
            const settings = JSON.parse(saved);
            Object.assign(this.visionCapabilities, settings);
        }
    }

    saveVisionSettings() {
        localStorage.setItem('nexus-vision-settings', JSON.stringify(this.visionCapabilities));
    }
}

// Offline AI Models (Simulated for standalone operation)
class OfflineObjectDetector {
    async detect(imageData) {
        // Simulate object detection using edge detection and pattern matching
        const objects = [];
        const data = imageData.data;
        const width = imageData.width;
        const height = imageData.height;
        
        // Simple edge detection to find objects
        const edges = this.detectEdges(data, width, height);
        const regions = this.findRegions(edges, width, height);
        
        // Classify regions as objects
        regions.forEach((region, i) => {
            const classification = this.classifyRegion(region, data, width);
            if (classification.confidence > 0.5) {
                objects.push({
                    id: `obj_${i}`,
                    class: classification.class,
                    confidence: classification.confidence,
                    bbox: region.bbox
                });
            }
        });
        
        return objects;
    }
    
    detectEdges(data, width, height) {
        const edges = new Uint8Array(width * height);
        
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                const idx = (y * width + x) * 4;
                const center = (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
                
                // Sobel operator
                const gx = 
                    -1 * data[idx - 4 - width * 4] + 
                    -2 * data[idx - 4] + 
                    -1 * data[idx - 4 + width * 4] +
                    1 * data[idx + 4 - width * 4] + 
                    2 * data[idx + 4] + 
                    1 * data[idx + 4 + width * 4];
                
                const gy = 
                    -1 * data[idx - width * 4 - 4] + 
                    -2 * data[idx - width * 4] + 
                    -1 * data[idx - width * 4 + 4] +
                    1 * data[idx + width * 4 - 4] + 
                    2 * data[idx + width * 4] + 
                    1 * data[idx + width * 4 + 4];
                
                const magnitude = Math.sqrt(gx * gx + gy * gy);
                edges[y * width + x] = magnitude > 50 ? 255 : 0;
            }
        }
        
        return edges;
    }
    
    findRegions(edges, width, height) {
        const regions = [];
        const visited = new Set();
        
        for (let y = 0; y < height; y += 20) {
            for (let x = 0; x < width; x += 20) {
                const key = `${x},${y}`;
                if (!visited.has(key) && edges[y * width + x] > 0) {
                    const region = this.floodFill(edges, x, y, width, height, visited);
                    if (region.pixels > 100) {
                        regions.push(region);
                    }
                }
            }
        }
        
        return regions;
    }
    
    floodFill(edges, startX, startY, width, height, visited) {
        const stack = [[startX, startY]];
        let minX = startX, maxX = startX;
        let minY = startY, maxY = startY;
        let pixels = 0;
        
        while (stack.length > 0) {
            const [x, y] = stack.pop();
            const key = `${x},${y}`;
            
            if (visited.has(key) || x < 0 || x >= width || y < 0 || y >= height) {
                continue;
            }
            
            if (edges[y * width + x] === 0) {
                continue;
            }
            
            visited.add(key);
            pixels++;
            
            minX = Math.min(minX, x);
            maxX = Math.max(maxX, x);
            minY = Math.min(minY, y);
            maxY = Math.max(maxY, y);
            
            stack.push([x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]);
        }
        
        return {
            bbox: {
                x: minX,
                y: minY,
                width: maxX - minX,
                height: maxY - minY
            },
            pixels
        };
    }
    
    classifyRegion(region, data, width) {
        // Simple classification based on region properties
        const aspectRatio = region.bbox.width / region.bbox.height;
        const size = region.bbox.width * region.bbox.height;
        
        // Analyze color within region
        let r = 0, g = 0, b = 0, count = 0;
        for (let y = region.bbox.y; y < region.bbox.y + region.bbox.height; y += 5) {
            for (let x = region.bbox.x; x < region.bbox.x + region.bbox.width; x += 5) {
                const idx = (y * width + x) * 4;
                r += data[idx];
                g += data[idx + 1];
                b += data[idx + 2];
                count++;
            }
        }
        
        r /= count;
        g /= count;
        b /= count;
        
        // Simple classification rules
        if (aspectRatio > 0.8 && aspectRatio < 1.2 && r > 200) {
            return { class: 'face', confidence: 0.7 };
        } else if (aspectRatio > 2 && b > 150) {
            return { class: 'screen', confidence: 0.6 };
        } else if (size > 10000) {
            return { class: 'background', confidence: 0.5 };
        } else if (g > r && g > b) {
            return { class: 'plant', confidence: 0.6 };
        } else {
            return { class: 'object', confidence: 0.5 };
        }
    }
}

class OfflineTextExtractor {
    async extract(imageData) {
        // Simulate OCR using pattern matching
        // In a real implementation, this would use tesseract.js or similar
        const blocks = [];
        
        // Detect high contrast regions that might be text
        const textRegions = this.findTextRegions(imageData);
        
        textRegions.forEach((region, i) => {
            blocks.push({
                text: `Text block ${i + 1}`,
                confidence: 0.8,
                bbox: region.bbox
            });
        });
        
        return { blocks };
    }
    
    findTextRegions(imageData) {
        // Simplified text region detection
        const regions = [];
        const data = imageData.data;
        const width = imageData.width;
        const height = imageData.height;
        
        // Look for horizontal lines of consistent color (text lines)
        for (let y = 0; y < height; y += 20) {
            let consecutiveLight = 0;
            let startX = 0;
            
            for (let x = 0; x < width; x++) {
                const idx = (y * width + x) * 4;
                const brightness = (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
                
                if (brightness > 200) {
                    if (consecutiveLight === 0) startX = x;
                    consecutiveLight++;
                } else {
                    if (consecutiveLight > 50) {
                        regions.push({
                            bbox: {
                                x: startX,
                                y: y - 10,
                                width: consecutiveLight,
                                height: 20
                            }
                        });
                    }
                    consecutiveLight = 0;
                }
            }
        }
        
        return regions;
    }
}

class OfflineSceneClassifier {
    async classify(imageData) {
        // Analyze overall image characteristics
        const data = imageData.data;
        let totalBrightness = 0;
        let colorVariance = 0;
        let edges = 0;
        
        // Calculate image statistics
        for (let i = 0; i < data.length; i += 4) {
            const brightness = (data[i] + data[i + 1] + data[i + 2]) / 3;
            totalBrightness += brightness;
            
            if (i > 4) {
                const diff = Math.abs(brightness - (data[i - 4] + data[i - 3] + data[i - 2]) / 3);
                if (diff > 30) edges++;
            }
        }
        
        const avgBrightness = totalBrightness / (data.length / 4);
        const edgeDensity = edges / (data.length / 4);
        
        // Classify based on statistics
        let type = 'unknown';
        let description = '';
        let elements = [];
        
        if (avgBrightness > 200 && edgeDensity < 0.1) {
            type = 'screen';
            description = 'Computer screen or display';
            elements = ['display', 'interface', 'digital'];
        } else if (avgBrightness < 100) {
            type = 'dark';
            description = 'Dark or low-light scene';
            elements = ['shadows', 'low-light'];
        } else if (edgeDensity > 0.3) {
            type = 'complex';
            description = 'Complex scene with many objects';
            elements = ['multiple objects', 'detailed'];
        } else {
            type = 'simple';
            description = 'Simple scene with few elements';
            elements = ['minimal', 'clean'];
        }
        
        return {
            type,
            confidence: 0.7,
            description,
            elements
        };
    }
}

// Register with window for global access
window.NexusVisualIntegration = NexusVisualIntegration;