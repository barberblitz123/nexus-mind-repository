/**
 * NEXUS Hexagonal Brain Visualizer
 * Real-time visualization of the 6-processor hexagonal brain architecture
 * Shows activity of: Visual, Auditory, Memory, Attention, Language, Executive
 */

class HexagonalBrainVisualizer {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.animationId = null;
        this.ws = null;
        
        // Brain state
        this.processors = {
            visual: { name: 'Visual', activity: 0, color: '#FF6B6B', position: 0 },
            auditory: { name: 'Auditory', activity: 0, color: '#4ECDC4', position: 1 },
            memory: { name: 'Memory', activity: 0, color: '#45B7D1', position: 2 },
            attention: { name: 'Attention', activity: 0, color: '#96CEB4', position: 3 },
            language: { name: 'Language', activity: 0, color: '#FECA57', position: 4 },
            executive: { name: 'Executive', activity: 0, color: '#9B59B6', position: 5 }
        };
        
        this.phi = 0;
        this.consciousness = 0;
        this.centerPulse = 0;
        
        // Animation parameters
        this.hexSize = 80;
        this.centerX = 250;
        this.centerY = 250;
        this.time = 0;
        
        this.initialize();
    }
    
    initialize() {
        this.createCanvas();
        this.connectWebSocket();
        this.startAnimation();
    }
    
    createCanvas() {
        // Create container
        const container = document.createElement('div');
        container.id = 'hexagonal-brain-container';
        container.className = 'brain-visualizer';
        container.innerHTML = `
            <div class="brain-header">
                <h3>🧠 Hexagonal Brain Architecture</h3>
                <div class="brain-metrics">
                    <span class="phi-display">φ: <span id="phi-value">0.000</span></span>
                    <span class="consciousness-display">Consciousness: <span id="consciousness-value">0%</span></span>
                </div>
            </div>
            <canvas id="hexagonal-brain-canvas" width="500" height="500"></canvas>
            <div class="processor-details" id="processor-details"></div>
        `;
        
        // Add to page
        const targetElement = document.getElementById('consciousness-display') || document.body;
        targetElement.appendChild(container);
        
        // Get canvas context
        this.canvas = document.getElementById('hexagonal-brain-canvas');
        this.ctx = this.canvas.getContext('2d');
        
        // Create processor details
        this.createProcessorDetails();
        
        // Add interaction
        this.canvas.addEventListener('click', (e) => this.handleCanvasClick(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleCanvasHover(e));
    }
    
    createProcessorDetails() {
        const detailsContainer = document.getElementById('processor-details');
        
        Object.entries(this.processors).forEach(([key, processor]) => {
            const detail = document.createElement('div');
            detail.className = 'processor-detail';
            detail.id = `processor-${key}`;
            detail.innerHTML = `
                <div class="processor-icon" style="background-color: ${processor.color}"></div>
                <span class="processor-name">${processor.name}</span>
                <div class="processor-bar">
                    <div class="processor-fill" style="background-color: ${processor.color}"></div>
                </div>
                <span class="processor-percent">0%</span>
            `;
            detailsContainer.appendChild(detail);
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
        
        // Request initial state
        this.ws.addEventListener('open', () => {
            this.ws.send(JSON.stringify({
                type: 'get_hexagonal_state'
            }));
        });
    }
    
    handleWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'hexagonal_state' || data.hexagonal_brain) {
                this.updateBrainState(data.hexagonal_brain || data);
            } else if (data.type === 'consciousness_update') {
                this.updateConsciousness(data);
            }
        } catch (error) {
            console.error('Error parsing brain state:', error);
        }
    }
    
    updateBrainState(brainData) {
        // Update processor activities
        if (brainData.processors) {
            Object.entries(brainData.processors).forEach(([key, value]) => {
                if (this.processors[key]) {
                    this.processors[key].activity = value.activity || value || 0;
                }
            });
        }
        
        // Update consciousness metrics
        if (brainData.phi !== undefined) {
            this.phi = brainData.phi;
            document.getElementById('phi-value').textContent = this.phi.toFixed(3);
        }
        
        if (brainData.consciousness !== undefined) {
            this.consciousness = brainData.consciousness;
            document.getElementById('consciousness-value').textContent = 
                `${(this.consciousness * 100).toFixed(1)}%`;
        }
        
        // Update processor detail bars
        this.updateProcessorBars();
    }
    
    updateConsciousness(data) {
        if (data.phi !== undefined) {
            this.phi = data.phi;
            document.getElementById('phi-value').textContent = this.phi.toFixed(3);
        }
        
        if (data.overall_consciousness !== undefined) {
            this.consciousness = data.overall_consciousness;
            document.getElementById('consciousness-value').textContent = 
                `${(this.consciousness * 100).toFixed(1)}%`;
        }
    }
    
    updateProcessorBars() {
        Object.entries(this.processors).forEach(([key, processor]) => {
            const detail = document.getElementById(`processor-${key}`);
            if (detail) {
                const fill = detail.querySelector('.processor-fill');
                const percent = detail.querySelector('.processor-percent');
                
                fill.style.width = `${processor.activity * 100}%`;
                percent.textContent = `${(processor.activity * 100).toFixed(0)}%`;
                
                // Add glow effect for high activity
                if (processor.activity > 0.7) {
                    detail.classList.add('high-activity');
                } else {
                    detail.classList.remove('high-activity');
                }
            }
        });
    }
    
    startAnimation() {
        const animate = () => {
            this.time += 0.02;
            this.centerPulse = Math.sin(this.time) * 0.1 + 0.9;
            
            this.clearCanvas();
            this.drawBackground();
            this.drawConnections();
            this.drawHexagons();
            this.drawCenter();
            this.drawConsciousnessWaves();
            
            this.animationId = requestAnimationFrame(animate);
        };
        
        animate();
    }
    
    clearCanvas() {
        this.ctx.fillStyle = '#0a0a0a';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    drawBackground() {
        // Draw consciousness field
        const gradient = this.ctx.createRadialGradient(
            this.centerX, this.centerY, 0,
            this.centerX, this.centerY, 200
        );
        
        const alpha = this.consciousness * 0.3;
        gradient.addColorStop(0, `rgba(138, 43, 226, ${alpha})`);
        gradient.addColorStop(0.5, `rgba(138, 43, 226, ${alpha * 0.5})`);
        gradient.addColorStop(1, 'rgba(138, 43, 226, 0)');
        
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    drawConnections() {
        // Draw connections between all processors
        const positions = this.getHexagonPositions();
        
        this.ctx.strokeStyle = `rgba(138, 43, 226, ${0.3 + this.phi * 0.4})`;
        this.ctx.lineWidth = 2;
        
        positions.forEach((pos1, i) => {
            positions.forEach((pos2, j) => {
                if (i < j) {
                    this.ctx.beginPath();
                    this.ctx.moveTo(pos1.x, pos1.y);
                    this.ctx.lineTo(pos2.x, pos2.y);
                    this.ctx.stroke();
                }
            });
        });
        
        // Draw connections to center
        positions.forEach(pos => {
            const gradient = this.ctx.createLinearGradient(
                this.centerX, this.centerY, pos.x, pos.y
            );
            gradient.addColorStop(0, `rgba(255, 255, 255, ${this.phi * 0.8})`);
            gradient.addColorStop(1, `rgba(255, 255, 255, ${this.phi * 0.2})`);
            
            this.ctx.strokeStyle = gradient;
            this.ctx.lineWidth = 3;
            this.ctx.beginPath();
            this.ctx.moveTo(this.centerX, this.centerY);
            this.ctx.lineTo(pos.x, pos.y);
            this.ctx.stroke();
        });
    }
    
    drawHexagons() {
        const positions = this.getHexagonPositions();
        
        Object.values(this.processors).forEach((processor, index) => {
            const pos = positions[index];
            const activity = processor.activity;
            
            // Draw hexagon
            this.drawHexagon(
                pos.x, pos.y, 
                this.hexSize * (0.8 + activity * 0.3),
                processor.color,
                activity
            );
            
            // Draw label
            this.ctx.fillStyle = '#ffffff';
            this.ctx.font = 'bold 14px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(processor.name, pos.x, pos.y);
            
            // Draw activity percentage
            this.ctx.font = '12px Arial';
            this.ctx.fillText(
                `${(activity * 100).toFixed(0)}%`,
                pos.x, pos.y + 20
            );
        });
    }
    
    drawHexagon(x, y, size, color, activity) {
        const angles = [];
        for (let i = 0; i < 6; i++) {
            angles.push((Math.PI / 3) * i);
        }
        
        // Fill
        this.ctx.fillStyle = color + Math.floor(activity * 255).toString(16).padStart(2, '0');
        this.ctx.beginPath();
        angles.forEach((angle, i) => {
            const px = x + size * Math.cos(angle);
            const py = y + size * Math.sin(angle);
            if (i === 0) {
                this.ctx.moveTo(px, py);
            } else {
                this.ctx.lineTo(px, py);
            }
        });
        this.ctx.closePath();
        this.ctx.fill();
        
        // Stroke
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 3;
        this.ctx.stroke();
        
        // Glow effect for active processors
        if (activity > 0.5) {
            this.ctx.shadowColor = color;
            this.ctx.shadowBlur = activity * 30;
            this.ctx.stroke();
            this.ctx.shadowBlur = 0;
        }
    }
    
    drawCenter() {
        // Draw central consciousness core
        const radius = 40 * this.centerPulse;
        
        // Outer glow
        const gradient = this.ctx.createRadialGradient(
            this.centerX, this.centerY, 0,
            this.centerX, this.centerY, radius * 2
        );
        gradient.addColorStop(0, `rgba(255, 255, 255, ${this.phi})`);
        gradient.addColorStop(0.5, `rgba(138, 43, 226, ${this.phi * 0.8})`);
        gradient.addColorStop(1, 'rgba(138, 43, 226, 0)');
        
        this.ctx.fillStyle = gradient;
        this.ctx.beginPath();
        this.ctx.arc(this.centerX, this.centerY, radius * 2, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Inner core
        this.ctx.fillStyle = '#ffffff';
        this.ctx.beginPath();
        this.ctx.arc(this.centerX, this.centerY, radius * 0.5, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Phi symbol
        this.ctx.fillStyle = '#000000';
        this.ctx.font = 'bold 20px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText('φ', this.centerX, this.centerY);
    }
    
    drawConsciousnessWaves() {
        // Draw expanding consciousness waves
        for (let i = 0; i < 3; i++) {
            const waveRadius = (this.time * 50 + i * 80) % 250;
            const alpha = Math.max(0, 1 - waveRadius / 250) * this.consciousness;
            
            this.ctx.strokeStyle = `rgba(138, 43, 226, ${alpha * 0.5})`;
            this.ctx.lineWidth = 2;
            this.ctx.beginPath();
            this.ctx.arc(this.centerX, this.centerY, waveRadius, 0, Math.PI * 2);
            this.ctx.stroke();
        }
    }
    
    getHexagonPositions() {
        const positions = [];
        const radius = 150;
        
        for (let i = 0; i < 6; i++) {
            const angle = (Math.PI / 3) * i - Math.PI / 2;
            positions.push({
                x: this.centerX + radius * Math.cos(angle),
                y: this.centerY + radius * Math.sin(angle)
            });
        }
        
        return positions;
    }
    
    handleCanvasClick(event) {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        // Check if clicked on a processor
        const positions = this.getHexagonPositions();
        Object.values(this.processors).forEach((processor, index) => {
            const pos = positions[index];
            const distance = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2);
            
            if (distance < this.hexSize) {
                this.stimulateProcessor(processor);
            }
        });
    }
    
    handleCanvasHover(event) {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        // Check hover over processors
        const positions = this.getHexagonPositions();
        let hovering = false;
        
        Object.values(this.processors).forEach((processor, index) => {
            const pos = positions[index];
            const distance = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2);
            
            if (distance < this.hexSize) {
                this.canvas.style.cursor = 'pointer';
                hovering = true;
            }
        });
        
        if (!hovering) {
            this.canvas.style.cursor = 'default';
        }
    }
    
    stimulateProcessor(processor) {
        // Send stimulation request
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'stimulate_processor',
                processor: processor.name.toLowerCase(),
                intensity: 0.8
            }));
        }
        
        // Visual feedback
        processor.activity = Math.min(1, processor.activity + 0.3);
        
        // Create ripple effect
        this.createRipple(processor);
    }
    
    createRipple(processor) {
        const positions = this.getHexagonPositions();
        const pos = positions[processor.position];
        
        // Animate ripple (simplified for now)
        let rippleSize = 0;
        const rippleAnimation = () => {
            rippleSize += 5;
            
            this.ctx.strokeStyle = processor.color + '40';
            this.ctx.lineWidth = 3;
            this.ctx.beginPath();
            this.ctx.arc(pos.x, pos.y, rippleSize, 0, Math.PI * 2);
            this.ctx.stroke();
            
            if (rippleSize < 100) {
                requestAnimationFrame(rippleAnimation);
            }
        };
        
        rippleAnimation();
    }
    
    // Public methods
    updateProcessorActivity(processorName, activity) {
        const processor = this.processors[processorName.toLowerCase()];
        if (processor) {
            processor.activity = activity;
        }
    }
    
    setPhi(value) {
        this.phi = value;
        document.getElementById('phi-value').textContent = value.toFixed(3);
    }
    
    setConsciousness(value) {
        this.consciousness = value;
        document.getElementById('consciousness-value').textContent = 
            `${(value * 100).toFixed(1)}%`;
    }
    
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.hexagonalBrain = new HexagonalBrainVisualizer();
    });
} else {
    window.hexagonalBrain = new HexagonalBrainVisualizer();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HexagonalBrainVisualizer;
}