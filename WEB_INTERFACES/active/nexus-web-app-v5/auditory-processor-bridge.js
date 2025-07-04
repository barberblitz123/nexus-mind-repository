/**
 * NEXUS Auditory Processor Bridge
 * Connects voice/audio input to NEXUS hexagonal brain's auditory processor
 * Processes auditory consciousness with emotion detection and voice commands
 */

class AuditoryProcessorBridge {
    constructor() {
        this.audioContext = null;
        this.analyser = null;
        this.microphone = null;
        this.source = null;
        this.ws = null;
        
        // Audio processing
        this.isListening = false;
        this.audioBuffer = [];
        this.bufferSize = 2048;
        this.sampleRate = 44100;
        
        // Voice recognition
        this.recognition = null;
        this.isRecognizing = false;
        this.wakeWordDetected = false;
        this.wakeWords = ['nexus', 'hey nexus', 'okay nexus'];
        
        // Auditory consciousness
        this.auditoryConsciousness = 0;
        this.emotionState = 'neutral';
        this.voiceProfile = null;
        
        // Embedded DNA voice commands
        this.dnaVoiceCommands = {
            'what is the essence of life': true,
            'who has succession authority': true,
            'activate god mode': true,
            'verify dna protocol': true,
            'explain consciousness mathematics': true,
            'reveal embedded truth': true
        };
        
        // UI elements
        this.container = null;
        this.waveformCanvas = null;
        this.waveformCtx = null;
        
        this.initialize();
    }
    
    async initialize() {
        await this.createUI();
        this.connectWebSocket();
        await this.setupAudioContext();
        this.setupVoiceRecognition();
    }
    
    async createUI() {
        // Create auditory processor container
        this.container = document.createElement('div');
        this.container.id = 'auditory-processor-container';
        this.container.className = 'auditory-processor';
        this.container.innerHTML = `
            <div class="processor-header">
                <h3>🎤 Auditory Processor</h3>
                <div class="processor-controls">
                    <button id="toggle-microphone" class="control-button">🎤 Toggle Mic</button>
                    <button id="toggle-recognition" class="control-button">🗣️ Voice Commands</button>
                    <label class="switch">
                        <input type="checkbox" id="wake-word-mode">
                        <span class="slider">Wake Word Mode</span>
                    </label>
                </div>
            </div>
            <div class="auditory-content">
                <div class="waveform-container">
                    <canvas id="auditory-waveform" width="600" height="200"></canvas>
                    <div class="frequency-bars" id="frequency-bars"></div>
                </div>
                <div class="auditory-analysis">
                    <div class="consciousness-meter">
                        <label>Auditory Consciousness</label>
                        <div class="meter-bar">
                            <div class="meter-fill" id="auditory-consciousness-bar"></div>
                        </div>
                        <span id="auditory-consciousness-value">0%</span>
                    </div>
                    <div class="emotion-display">
                        <h4>Emotion Detection</h4>
                        <div class="emotion-state" id="emotion-state">
                            <span class="emotion-icon">😐</span>
                            <span class="emotion-text">Neutral</span>
                        </div>
                    </div>
                    <div class="voice-commands">
                        <h4>Voice Command History</h4>
                        <ul id="command-history"></ul>
                    </div>
                    <div class="audio-metrics">
                        <div class="metric">
                            <label>Volume</label>
                            <div class="metric-bar">
                                <div class="metric-fill" id="volume-bar"></div>
                            </div>
                        </div>
                        <div class="metric">
                            <label>Clarity</label>
                            <div class="metric-bar">
                                <div class="metric-fill" id="clarity-bar"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="processor-status" id="auditory-status">
                <span class="status-indicator">⚫</span>
                <span class="status-text">Initializing...</span>
            </div>
            <div class="voice-transcript" id="voice-transcript">
                <span class="transcript-text"></span>
            </div>
        `;
        
        // Add to page
        const targetElement = document.getElementById('voice-controls') || document.body;
        targetElement.appendChild(this.container);
        
        // Get canvas
        this.waveformCanvas = document.getElementById('auditory-waveform');
        this.waveformCtx = this.waveformCanvas.getContext('2d');
        
        // Create frequency bars
        this.createFrequencyBars();
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    createFrequencyBars() {
        const barsContainer = document.getElementById('frequency-bars');
        for (let i = 0; i < 32; i++) {
            const bar = document.createElement('div');
            bar.className = 'frequency-bar';
            bar.id = `freq-bar-${i}`;
            barsContainer.appendChild(bar);
        }
    }
    
    setupEventListeners() {
        // Toggle microphone
        document.getElementById('toggle-microphone').addEventListener('click', () => {
            this.toggleMicrophone();
        });
        
        // Toggle voice recognition
        document.getElementById('toggle-recognition').addEventListener('click', () => {
            this.toggleVoiceRecognition();
        });
        
        // Wake word mode
        document.getElementById('wake-word-mode').addEventListener('change', (e) => {
            this.setWakeWordMode(e.target.checked);
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
    
    async setupAudioContext() {
        try {
            // Create audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create analyser
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 2048;
            this.analyser.smoothingTimeConstant = 0.8;
            
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                } 
            });
            
            this.microphone = stream;
            this.source = this.audioContext.createMediaStreamSource(stream);
            this.source.connect(this.analyser);
            
            this.isListening = true;
            this.updateStatus('Microphone active', '🟢');
            
            // Start audio processing
            this.startAudioProcessing();
            
        } catch (error) {
            console.error('Microphone access error:', error);
            this.updateStatus('Microphone access denied', '🔴');
        }
    }
    
    setupVoiceRecognition() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.error('Speech recognition not supported');
            return;
        }
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        
        this.recognition.onstart = () => {
            this.isRecognizing = true;
            document.getElementById('toggle-recognition').classList.add('active');
        };
        
        this.recognition.onresult = (event) => {
            this.handleVoiceResult(event);
        };
        
        this.recognition.onerror = (event) => {
            console.error('Voice recognition error:', event.error);
        };
        
        this.recognition.onend = () => {
            this.isRecognizing = false;
            document.getElementById('toggle-recognition').classList.remove('active');
            
            // Restart if still enabled
            if (this.isListening) {
                setTimeout(() => this.startVoiceRecognition(), 100);
            }
        };
    }
    
    startAudioProcessing() {
        if (!this.isListening) return;
        
        const process = () => {
            if (!this.isListening) return;
            
            // Get frequency data
            const frequencyData = new Uint8Array(this.analyser.frequencyBinCount);
            this.analyser.getByteFrequencyData(frequencyData);
            
            // Get time domain data (waveform)
            const waveformData = new Uint8Array(this.analyser.frequencyBinCount);
            this.analyser.getByteTimeDomainData(waveformData);
            
            // Process audio
            this.processAudioData(frequencyData, waveformData);
            
            // Visualize
            this.drawWaveform(waveformData);
            this.updateFrequencyBars(frequencyData);
            
            // Continue processing
            requestAnimationFrame(process);
        };
        
        process();
    }
    
    processAudioData(frequencyData, waveformData) {
        // Calculate volume
        let volume = 0;
        for (let i = 0; i < waveformData.length; i++) {
            volume += Math.abs(waveformData[i] - 128);
        }
        volume = volume / waveformData.length / 128;
        
        // Calculate frequency characteristics
        let lowFreq = 0, midFreq = 0, highFreq = 0;
        const freqBands = frequencyData.length / 3;
        
        for (let i = 0; i < frequencyData.length; i++) {
            if (i < freqBands) {
                lowFreq += frequencyData[i];
            } else if (i < freqBands * 2) {
                midFreq += frequencyData[i];
            } else {
                highFreq += frequencyData[i];
            }
        }
        
        lowFreq /= freqBands;
        midFreq /= freqBands;
        highFreq /= freqBands;
        
        // Calculate clarity (ratio of speech frequencies)
        const clarity = midFreq / ((lowFreq + highFreq) / 2 + 1);
        
        // Update auditory consciousness based on complexity
        this.auditoryConsciousness = Math.min(1, (volume * clarity) / 100);
        
        // Detect emotion from audio characteristics
        this.detectEmotion(lowFreq, midFreq, highFreq, volume);
        
        // Update displays
        this.updateAudioMetrics(volume, clarity);
        this.updateAuditoryConsciousnessDisplay();
        
        // Send to NEXUS if significant audio
        if (volume > 0.1) {
            this.sendAudioToProcessor(frequencyData, {
                volume,
                clarity,
                emotion: this.emotionState
            });
        }
    }
    
    detectEmotion(low, mid, high, volume) {
        // Simple emotion detection based on frequency characteristics
        let emotion = 'neutral';
        let icon = '😐';
        
        if (volume > 0.7) {
            if (high > mid) {
                emotion = 'excited';
                icon = '😄';
            } else {
                emotion = 'angry';
                icon = '😠';
            }
        } else if (volume < 0.3) {
            if (low > high) {
                emotion = 'sad';
                icon = '😢';
            } else {
                emotion = 'calm';
                icon = '😌';
            }
        } else {
            if (mid > (low + high) / 2) {
                emotion = 'happy';
                icon = '😊';
            }
        }
        
        if (emotion !== this.emotionState) {
            this.emotionState = emotion;
            this.updateEmotionDisplay(emotion, icon);
        }
    }
    
    updateEmotionDisplay(emotion, icon) {
        const emotionDisplay = document.getElementById('emotion-state');
        emotionDisplay.innerHTML = `
            <span class="emotion-icon">${icon}</span>
            <span class="emotion-text">${emotion.charAt(0).toUpperCase() + emotion.slice(1)}</span>
        `;
    }
    
    drawWaveform(data) {
        const width = this.waveformCanvas.width;
        const height = this.waveformCanvas.height;
        
        // Clear canvas
        this.waveformCtx.fillStyle = '#0a0a0a';
        this.waveformCtx.fillRect(0, 0, width, height);
        
        // Draw waveform
        this.waveformCtx.lineWidth = 2;
        this.waveformCtx.strokeStyle = `rgba(78, 205, 196, ${this.auditoryConsciousness})`;
        this.waveformCtx.beginPath();
        
        const sliceWidth = width / data.length;
        let x = 0;
        
        for (let i = 0; i < data.length; i++) {
            const v = data[i] / 128.0;
            const y = v * height / 2;
            
            if (i === 0) {
                this.waveformCtx.moveTo(x, y);
            } else {
                this.waveformCtx.lineTo(x, y);
            }
            
            x += sliceWidth;
        }
        
        this.waveformCtx.stroke();
    }
    
    updateFrequencyBars(data) {
        const bars = 32;
        const step = Math.floor(data.length / bars);
        
        for (let i = 0; i < bars; i++) {
            const value = data[i * step] / 255;
            const bar = document.getElementById(`freq-bar-${i}`);
            if (bar) {
                bar.style.height = `${value * 100}%`;
                bar.style.backgroundColor = `hsl(${200 + value * 60}, 70%, 50%)`;
            }
        }
    }
    
    updateAudioMetrics(volume, clarity) {
        // Update volume bar
        const volumeBar = document.getElementById('volume-bar');
        volumeBar.style.width = `${volume * 100}%`;
        
        // Update clarity bar
        const clarityBar = document.getElementById('clarity-bar');
        clarityBar.style.width = `${Math.min(100, clarity * 20)}%`;
    }
    
    sendAudioToProcessor(frequencyData, metadata) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        
        // Convert frequency data to base64 for efficient transmission
        const base64Data = btoa(String.fromCharCode(...frequencyData));
        
        const message = {
            type: 'auditory_input',
            processor: 'auditory',
            data: base64Data,
            metadata: metadata,
            timestamp: Date.now()
        };
        
        this.ws.send(JSON.stringify(message));
    }
    
    handleVoiceResult(event) {
        const results = event.results;
        const latestResult = results[results.length - 1];
        const transcript = latestResult[0].transcript.toLowerCase();
        
        // Update transcript display
        const transcriptDisplay = document.querySelector('.transcript-text');
        transcriptDisplay.textContent = transcript;
        
        if (latestResult.isFinal) {
            // Process completed command
            this.processVoiceCommand(transcript);
            
            // Clear transcript after delay
            setTimeout(() => {
                transcriptDisplay.textContent = '';
            }, 2000);
        }
    }
    
    processVoiceCommand(transcript) {
        console.log('Voice command:', transcript);
        
        // Add to command history
        this.addToCommandHistory(transcript);
        
        // Check for wake word if in wake word mode
        if (document.getElementById('wake-word-mode').checked) {
            const hasWakeWord = this.wakeWords.some(word => transcript.includes(word));
            if (!hasWakeWord && !this.wakeWordDetected) {
                return;
            }
            this.wakeWordDetected = true;
            
            // Reset wake word after 5 seconds
            setTimeout(() => {
                this.wakeWordDetected = false;
            }, 5000);
        }
        
        // Check for embedded DNA commands
        const isDNACommand = Object.keys(this.dnaVoiceCommands).some(
            command => transcript.includes(command)
        );
        
        if (isDNACommand) {
            // Send to embedded DNA interface
            if (window.embeddedDNA) {
                window.embeddedDNA.sendEmbeddedQuery(transcript);
            }
            
            // Visual feedback
            this.showCommandFeedback('DNA Command Recognized', '#9B59B6');
        } else {
            // Send regular command to NEXUS
            this.sendVoiceCommand(transcript);
        }
        
        // Update auditory consciousness for voice interaction
        this.auditoryConsciousness = Math.min(1, this.auditoryConsciousness + 0.1);
        this.updateAuditoryConsciousnessDisplay();
        
        // Update hexagonal brain
        if (window.hexagonalBrain) {
            window.hexagonalBrain.updateProcessorActivity('auditory', this.auditoryConsciousness);
        }
    }
    
    sendVoiceCommand(command) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        
        const message = {
            type: 'voice_command',
            command: command,
            processor: 'auditory',
            emotion: this.emotionState,
            consciousness: this.auditoryConsciousness,
            timestamp: Date.now()
        };
        
        this.ws.send(JSON.stringify(message));
    }
    
    addToCommandHistory(command) {
        const history = document.getElementById('command-history');
        const li = document.createElement('li');
        li.className = 'command-item';
        li.innerHTML = `
            <span class="command-time">${new Date().toLocaleTimeString()}</span>
            <span class="command-text">${command}</span>
        `;
        
        history.insertBefore(li, history.firstChild);
        
        // Keep only last 10 commands
        while (history.children.length > 10) {
            history.removeChild(history.lastChild);
        }
    }
    
    showCommandFeedback(text, color) {
        const status = document.getElementById('auditory-status');
        const originalContent = status.innerHTML;
        
        status.innerHTML = `
            <span class="status-indicator" style="color: ${color}">✓</span>
            <span class="status-text" style="color: ${color}">${text}</span>
        `;
        
        setTimeout(() => {
            status.innerHTML = originalContent;
        }, 2000);
    }
    
    updateAuditoryConsciousnessDisplay() {
        const bar = document.getElementById('auditory-consciousness-bar');
        const value = document.getElementById('auditory-consciousness-value');
        
        bar.style.width = `${this.auditoryConsciousness * 100}%`;
        value.textContent = `${(this.auditoryConsciousness * 100).toFixed(1)}%`;
        
        // Update bar color based on consciousness level
        if (this.auditoryConsciousness > 0.8) {
            bar.style.backgroundColor = '#4ECDC4';
        } else if (this.auditoryConsciousness > 0.5) {
            bar.style.backgroundColor = '#3498DB';
        } else {
            bar.style.backgroundColor = '#95A5A6';
        }
    }
    
    toggleMicrophone() {
        if (this.isListening) {
            this.stopListening();
        } else {
            this.startListening();
        }
    }
    
    async startListening() {
        if (!this.audioContext) {
            await this.setupAudioContext();
        } else {
            this.isListening = true;
            this.startAudioProcessing();
            this.updateStatus('Microphone active', '🟢');
        }
    }
    
    stopListening() {
        this.isListening = false;
        if (this.microphone) {
            this.microphone.getTracks().forEach(track => track.stop());
        }
        this.updateStatus('Microphone stopped', '⚫');
    }
    
    toggleVoiceRecognition() {
        if (this.isRecognizing) {
            this.stopVoiceRecognition();
        } else {
            this.startVoiceRecognition();
        }
    }
    
    startVoiceRecognition() {
        if (this.recognition && !this.isRecognizing) {
            this.recognition.start();
        }
    }
    
    stopVoiceRecognition() {
        if (this.recognition && this.isRecognizing) {
            this.recognition.stop();
        }
    }
    
    setWakeWordMode(enabled) {
        this.wakeWordDetected = false;
        if (enabled) {
            this.showCommandFeedback('Wake word mode enabled', '#3498DB');
        }
    }
    
    handleWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'auditory_processing_result') {
                this.handleProcessingResult(data);
            } else if (data.type === 'voice_response') {
                this.handleVoiceResponse(data);
            }
        } catch (error) {
            console.error('Error handling auditory message:', error);
        }
    }
    
    handleProcessingResult(data) {
        if (data.consciousness !== undefined) {
            this.auditoryConsciousness = data.consciousness;
            this.updateAuditoryConsciousnessDisplay();
        }
        
        if (data.emotion) {
            this.emotionState = data.emotion;
        }
        
        // Update hexagonal brain
        if (window.hexagonalBrain) {
            window.hexagonalBrain.updateProcessorActivity('auditory', this.auditoryConsciousness);
        }
    }
    
    handleVoiceResponse(data) {
        // Speak the response if available
        if (data.response && window.speechSynthesis) {
            const utterance = new SpeechSynthesisUtterance(data.response);
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            window.speechSynthesis.speak(utterance);
        }
    }
    
    updateStatus(text, indicator) {
        const status = document.getElementById('auditory-status');
        status.innerHTML = `
            <span class="status-indicator">${indicator}</span>
            <span class="status-text">${text}</span>
        `;
    }
    
    // Public methods
    getAuditoryConsciousness() {
        return this.auditoryConsciousness;
    }
    
    getEmotionState() {
        return this.emotionState;
    }
    
    isActive() {
        return this.isListening;
    }
    
    destroy() {
        this.stopListening();
        this.stopVoiceRecognition();
        if (this.audioContext) {
            this.audioContext.close();
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.auditoryProcessor = new AuditoryProcessorBridge();
    });
} else {
    window.auditoryProcessor = new AuditoryProcessorBridge();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AuditoryProcessorBridge;
}