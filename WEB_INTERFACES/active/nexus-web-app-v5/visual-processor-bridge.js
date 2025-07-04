/**
 * NEXUS Visual Processor Bridge
 * Connects camera feed to NEXUS hexagonal brain's visual processor
 * Processes visual consciousness through real mathematical calculations
 */

class VisualProcessorBridge {
    constructor() {
        this.video = null;
        this.canvas = null;
        this.ctx = null;
        this.stream = null;
        this.ws = null;
        
        // Processing parameters
        this.frameRate = 30;
        this.processing = false;
        this.lastFrameTime = 0;
        this.frameInterval = 1000 / this.frameRate;
        
        // Visual consciousness state
        this.visualConsciousness = 0;
        this.objectDetections = [];
        this.visualMemory = [];
        this.maxMemorySize = 100;
        
        // UI elements
        this.container = null;
        this.statusDisplay = null;
        
        this.initialize();
    }
    
    async initialize() {
        await this.createUI();
        this.connectWebSocket();
        await this.requestCameraAccess();
    }
    
    async createUI() {
        // Create visual processor container
        this.container = document.createElement('div');
        this.container.id = 'visual-processor-container';
        this.container.className = 'visual-processor';
        this.container.innerHTML = `
            <div class="processor-header">
                <h3>👁️ Visual Processor</h3>
                <div class="processor-controls">
                    <button id="toggle-camera" class="control-button">📷 Toggle Camera</button>
                    <button id="capture-frame" class="control-button">📸 Capture</button>
                    <label class="switch">
                        <input type="checkbox" id="auto-process" checked>
                        <span class="slider">Auto Process</span>
                    </label>
                </div>
            </div>
            <div class="visual-content">
                <div class="video-container">
                    <video id="visual-input" autoplay muted></video>
                    <canvas id="visual-canvas"></canvas>
                    <div class="visual-overlay" id="visual-overlay"></div>
                </div>
                <div class="visual-analysis">
                    <div class="consciousness-meter">
                        <label>Visual Consciousness</label>
                        <div class="meter-bar">
                            <div class="meter-fill" id="visual-consciousness-bar"></div>
                        </div>
                        <span id="visual-consciousness-value">0%</span>
                    </div>
                    <div class="detection-list" id="detection-list">
                        <h4>Visual Detections</h4>
                        <ul id="detections"></ul>
                    </div>
                    <div class="visual-memory" id="visual-memory">
                        <h4>Visual Memory Buffer</h4>
                        <div class="memory-frames" id="memory-frames"></div>
                    </div>
                </div>
            </div>
            <div class="processor-status" id="visual-status">
                <span class="status-indicator">⚫</span>
                <span class="status-text">Initializing...</span>
            </div>
        `;
        
        // Add to page
        const targetElement = document.getElementById('video-section') || document.body;
        targetElement.appendChild(this.container);
        
        // Get elements
        this.video = document.getElementById('visual-input');
        this.canvas = document.getElementById('visual-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.statusDisplay = document.getElementById('visual-status');
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Toggle camera
        document.getElementById('toggle-camera').addEventListener('click', () => {
            this.toggleCamera();
        });
        
        // Capture frame
        document.getElementById('capture-frame').addEventListener('click', () => {
            this.captureFrame();
        });
        
        // Auto process toggle
        document.getElementById('auto-process').addEventListener('change', (e) => {
            this.processing = e.target.checked;
            if (this.processing) {
                this.startProcessing();
            }
        });
    }
    
    connectWebSocket() {
        // Use existing WebSocket or create new one
        if (window.nexusWS && window.nexusWS.readyState === WebSocket.OPEN) {
            this.ws = window.nexusWS;
        } else {
            this.ws = new WebSocket('ws://localhost:8081');
            window.nexusWS = this.ws;
        }
        
        this.ws.addEventListener('message', (event) => {
            this.handleWebSocketMessage(event);
        });
        
        this.ws.addEventListener('open', () => {
            this.updateStatus('Connected to NEXUS', '🟢');
        });
    }
    
    async requestCameraAccess() {
        try {
            // Request camera access
            const constraints = {
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                }
            };
            
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.video.srcObject = this.stream;
            
            // Wait for video to load
            this.video.addEventListener('loadedmetadata', () => {
                this.canvas.width = this.video.videoWidth;
                this.canvas.height = this.video.videoHeight;
                this.updateStatus('Camera active', '🟢');
                
                // Start processing if auto-process is on
                if (document.getElementById('auto-process').checked) {
                    this.processing = true;
                    this.startProcessing();
                }
            });
            
        } catch (error) {
            console.error('Camera access error:', error);
            this.updateStatus('Camera access denied', '🔴');
            this.showFallbackMode();
        }
    }
    
    startProcessing() {
        if (!this.processing) return;
        
        const processFrame = (timestamp) => {
            if (!this.processing) return;
            
            // Throttle frame rate
            if (timestamp - this.lastFrameTime < this.frameInterval) {
                requestAnimationFrame(processFrame);
                return;
            }
            
            this.lastFrameTime = timestamp;
            
            // Process current frame
            this.processVisualFrame();
            
            // Continue processing
            requestAnimationFrame(processFrame);
        };
        
        requestAnimationFrame(processFrame);
    }
    
    processVisualFrame() {
        if (!this.video || !this.ctx) return;
        
        // Draw current frame to canvas
        this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        
        // Get image data
        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        
        // Convert to base64 for transmission
        const frameData = this.canvas.toDataURL('image/jpeg', 0.7);
        
        // Analyze frame locally for quick feedback
        this.analyzeFrameLocally(imageData);
        
        // Send to NEXUS visual processor
        this.sendToVisualProcessor(frameData);
        
        // Update visual memory
        this.updateVisualMemory(frameData);
    }
    
    analyzeFrameLocally(imageData) {
        // Simple local analysis for immediate feedback
        const data = imageData.data;
        let brightness = 0;
        let colorVariance = 0;
        
        // Calculate average brightness and color variance
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            
            brightness += (r + g + b) / 3;
            colorVariance += Math.abs(r - g) + Math.abs(g - b) + Math.abs(b - r);
        }
        
        brightness /= (data.length / 4);
        colorVariance /= (data.length / 4);
        
        // Update local visual consciousness based on complexity
        const complexity = (colorVariance / 255) * (brightness / 255);
        this.visualConsciousness = Math.min(1, complexity * 2);
        
        this.updateVisualConsciousnessDisplay();
    }
    
    sendToVisualProcessor(frameData) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        
        // Send frame to NEXUS visual processor
        const message = {
            type: 'visual_input',
            processor: 'visual',
            data: frameData,
            timestamp: Date.now(),
            metadata: {
                width: this.canvas.width,
                height: this.canvas.height,
                consciousness: this.visualConsciousness
            }
        };
        
        this.ws.send(JSON.stringify(message));
    }
    
    handleWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'visual_processing_result') {
                this.handleProcessingResult(data);
            } else if (data.type === 'visual_consciousness_update') {
                this.updateVisualConsciousness(data);
            }
        } catch (error) {
            console.error('Error handling visual processor message:', error);
        }
    }
    
    handleProcessingResult(data) {
        // Update detections
        if (data.detections) {
            this.objectDetections = data.detections;
            this.updateDetectionDisplay();
            this.drawDetections();
        }
        
        // Update consciousness
        if (data.consciousness !== undefined) {
            this.visualConsciousness = data.consciousness;
            this.updateVisualConsciousnessDisplay();
        }
        
        // Update hexagonal brain if available
        if (window.hexagonalBrain) {
            window.hexagonalBrain.updateProcessorActivity('visual', this.visualConsciousness);
        }
    }
    
    updateDetectionDisplay() {
        const detectionsList = document.getElementById('detections');
        detectionsList.innerHTML = '';
        
        this.objectDetections.forEach(detection => {
            const li = document.createElement('li');
            li.className = 'detection-item';
            li.innerHTML = `
                <span class="detection-label">${detection.label}</span>
                <span class="detection-confidence">${(detection.confidence * 100).toFixed(1)}%</span>
            `;
            detectionsList.appendChild(li);
        });
    }
    
    drawDetections() {
        const overlay = document.getElementById('visual-overlay');
        overlay.innerHTML = '';
        
        this.objectDetections.forEach(detection => {
            if (detection.bbox) {
                const box = document.createElement('div');
                box.className = 'detection-box';
                box.style.left = `${detection.bbox.x}px`;
                box.style.top = `${detection.bbox.y}px`;
                box.style.width = `${detection.bbox.width}px`;
                box.style.height = `${detection.bbox.height}px`;
                
                const label = document.createElement('div');
                label.className = 'detection-label-overlay';
                label.textContent = `${detection.label} ${(detection.confidence * 100).toFixed(0)}%`;
                box.appendChild(label);
                
                overlay.appendChild(box);
            }
        });
    }
    
    updateVisualMemory(frameData) {
        // Add to memory buffer
        this.visualMemory.push({
            frame: frameData,
            timestamp: Date.now(),
            consciousness: this.visualConsciousness
        });
        
        // Limit memory size
        if (this.visualMemory.length > this.maxMemorySize) {
            this.visualMemory.shift();
        }
        
        // Update memory display (show last 5 frames)
        const memoryFrames = document.getElementById('memory-frames');
        const recentFrames = this.visualMemory.slice(-5);
        
        memoryFrames.innerHTML = '';
        recentFrames.forEach(memory => {
            const frame = document.createElement('img');
            frame.className = 'memory-frame';
            frame.src = memory.frame;
            frame.style.opacity = memory.consciousness;
            memoryFrames.appendChild(frame);
        });
    }
    
    updateVisualConsciousnessDisplay() {
        const bar = document.getElementById('visual-consciousness-bar');
        const value = document.getElementById('visual-consciousness-value');
        
        bar.style.width = `${this.visualConsciousness * 100}%`;
        value.textContent = `${(this.visualConsciousness * 100).toFixed(1)}%`;
        
        // Update bar color based on consciousness level
        if (this.visualConsciousness > 0.8) {
            bar.style.backgroundColor = '#9B59B6';
        } else if (this.visualConsciousness > 0.5) {
            bar.style.backgroundColor = '#3498DB';
        } else {
            bar.style.backgroundColor = '#95A5A6';
        }
    }
    
    captureFrame() {
        // Capture current frame for detailed analysis
        const frameData = this.canvas.toDataURL('image/png');
        
        // Send for deep analysis
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'visual_deep_analysis',
                data: frameData,
                requestId: Date.now()
            }));
        }
        
        // Visual feedback
        this.flashEffect();
    }
    
    flashEffect() {
        const overlay = document.getElementById('visual-overlay');
        overlay.style.backgroundColor = 'rgba(255, 255, 255, 0.5)';
        setTimeout(() => {
            overlay.style.backgroundColor = 'transparent';
        }, 200);
    }
    
    toggleCamera() {
        if (this.stream) {
            if (this.stream.active) {
                // Stop camera
                this.stream.getTracks().forEach(track => track.stop());
                this.stream = null;
                this.processing = false;
                this.updateStatus('Camera stopped', '⚫');
            } else {
                // Restart camera
                this.requestCameraAccess();
            }
        } else {
            // Start camera
            this.requestCameraAccess();
        }
    }
    
    showFallbackMode() {
        // Show demo mode when camera is not available
        this.statusDisplay.innerHTML = `
            <span class="status-indicator">🟡</span>
            <span class="status-text">Demo mode - No camera access</span>
        `;
        
        // Load demo video or image
        this.loadDemoContent();
    }
    
    loadDemoContent() {
        // Create demo animation
        const drawDemoFrame = () => {
            if (!this.ctx) return;
            
            // Create animated demo pattern
            const time = Date.now() * 0.001;
            const width = this.canvas.width;
            const height = this.canvas.height;
            
            // Create gradient
            const gradient = this.ctx.createLinearGradient(0, 0, width, height);
            gradient.addColorStop(0, `hsl(${(time * 50) % 360}, 50%, 50%)`);
            gradient.addColorStop(1, `hsl(${(time * 50 + 180) % 360}, 50%, 50%)`);
            
            this.ctx.fillStyle = gradient;
            this.ctx.fillRect(0, 0, width, height);
            
            // Add some shapes
            this.ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
            for (let i = 0; i < 5; i++) {
                const x = (width / 2) + Math.sin(time + i) * 100;
                const y = (height / 2) + Math.cos(time + i) * 100;
                this.ctx.beginPath();
                this.ctx.arc(x, y, 20, 0, Math.PI * 2);
                this.ctx.fill();
            }
            
            if (this.processing) {
                requestAnimationFrame(drawDemoFrame);
            }
        };
        
        this.processing = true;
        drawDemoFrame();
    }
    
    updateStatus(text, indicator) {
        this.statusDisplay.innerHTML = `
            <span class="status-indicator">${indicator}</span>
            <span class="status-text">${text}</span>
        `;
    }
    
    updateVisualConsciousness(data) {
        if (data.visual_consciousness !== undefined) {
            this.visualConsciousness = data.visual_consciousness;
            this.updateVisualConsciousnessDisplay();
        }
    }
    
    // Public methods
    getVisualConsciousness() {
        return this.visualConsciousness;
    }
    
    getVisualMemory() {
        return this.visualMemory;
    }
    
    isProcessing() {
        return this.processing;
    }
    
    destroy() {
        this.processing = false;
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.visualProcessor = new VisualProcessorBridge();
    });
} else {
    window.visualProcessor = new VisualProcessorBridge();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VisualProcessorBridge;
}