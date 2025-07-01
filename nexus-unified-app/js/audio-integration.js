// NEXUS Audio Integration - Visual Audio Components
class NexusAudioIntegration {
    constructor(nexusCore) {
        this.nexus = nexusCore;
        this.audioContext = null;
        this.analyser = null;
        this.microphone = null;
        this.source = null;
        this.dataArray = null;
        this.isActive = false;
        this.animationId = null;
        this.emotions = {
            current: 'neutral',
            confidence: 0
        };
        this.metrics = {
            volume: 0,
            clarity: 0,
            frequency: {
                low: 0,
                mid: 0,
                high: 0
            }
        };
    }

    async initialize() {
        console.log('🎵 Initializing NEXUS Audio Integration...');
        
        try {
            // Create audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create analyser node
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 2048;
            this.analyser.smoothingTimeConstant = 0.8;
            
            // Set up data arrays
            this.bufferLength = this.analyser.frequencyBinCount;
            this.dataArray = new Uint8Array(this.bufferLength);
            this.frequencyData = new Uint8Array(this.bufferLength);
            
            // Initialize visual components
            this.initializeVisuals();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Start audio capture when voice is active
            this.nexus.on('voice-toggled', (e) => {
                if (e.detail.enabled) {
                    this.startAudioCapture();
                } else {
                    this.stopAudioCapture();
                }
            });
            
            // Auto-start if voice is enabled
            if (this.nexus.config.voiceEnabled) {
                await this.startAudioCapture();
            }
            
        } catch (error) {
            console.error('Error initializing audio:', error);
            this.nexus.showError('Audio initialization failed');
        }
    }

    initializeVisuals() {
        // Get canvas and context
        this.canvas = document.getElementById('audio-waveform');
        this.canvasCtx = this.canvas.getContext('2d');
        
        // Set canvas size
        this.resizeCanvas();
        
        // Create frequency bars
        this.createFrequencyBars();
        
        // Initialize meters
        this.volumeMeter = document.getElementById('volume-level');
        this.clarityMeter = document.getElementById('clarity-level');
        this.emotionIcon = document.getElementById('emotion-icon');
        this.emotionText = document.getElementById('emotion-text');
    }

    createFrequencyBars() {
        const container = document.getElementById('frequency-bars');
        container.innerHTML = ''; // Clear existing
        
        // Create 32 frequency bars
        for (let i = 0; i < 32; i++) {
            const bar = document.createElement('div');
            bar.className = 'freq-bar';
            bar.id = `freq-bar-${i}`;
            bar.style.height = '2px';
            container.appendChild(bar);
        }
        
        this.frequencyBars = container.querySelectorAll('.freq-bar');
    }

    setupEventListeners() {
        // Window resize
        window.addEventListener('resize', () => this.resizeCanvas());
        
        // Panel resize
        this.nexus.on('panel-resized', () => {
            setTimeout(() => this.resizeCanvas(), 300);
        });
        
        // Voice events
        this.nexus.on('speaking', () => {
            this.isProcessingSpeech = true;
        });
        
        this.nexus.on('listening', () => {
            this.isProcessingSpeech = false;
        });
    }

    resizeCanvas() {
        const container = this.canvas.parentElement;
        this.canvas.width = container.clientWidth - 20;
        this.canvas.height = 150;
    }

    async startAudioCapture() {
        if (this.isActive) return;
        
        try {
            console.log('🎤 Starting audio capture...');
            
            // Get user media
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            // Create source from microphone
            this.microphone = stream;
            this.source = this.audioContext.createMediaStreamSource(stream);
            this.source.connect(this.analyser);
            
            // Resume audio context if suspended
            if (this.audioContext.state === 'suspended') {
                await this.audioContext.resume();
            }
            
            this.isActive = true;
            this.startVisualization();
            
            // Add active class
            document.getElementById('audio-visual-panel').classList.add('audio-active');
            
        } catch (error) {
            console.error('Error accessing microphone:', error);
            this.nexus.showError('Microphone access denied');
        }
    }

    stopAudioCapture() {
        if (!this.isActive) return;
        
        console.log('🎤 Stopping audio capture...');
        
        // Stop microphone
        if (this.microphone) {
            this.microphone.getTracks().forEach(track => track.stop());
            this.microphone = null;
        }
        
        // Disconnect source
        if (this.source) {
            this.source.disconnect();
            this.source = null;
        }
        
        // Stop visualization
        this.stopVisualization();
        this.isActive = false;
        
        // Remove active class
        document.getElementById('audio-visual-panel').classList.remove('audio-active');
    }

    startVisualization() {
        const draw = () => {
            this.animationId = requestAnimationFrame(draw);
            
            // Get waveform data
            this.analyser.getByteTimeDomainData(this.dataArray);
            
            // Get frequency data
            this.analyser.getByteFrequencyData(this.frequencyData);
            
            // Update visualizations
            this.drawWaveform();
            this.updateFrequencyBars();
            this.updateMetrics();
            this.detectEmotion();
        };
        
        draw();
    }

    stopVisualization() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        
        // Clear visualizations
        this.clearWaveform();
        this.resetFrequencyBars();
    }

    drawWaveform() {
        const { width, height } = this.canvas;
        const ctx = this.canvasCtx;
        
        // Clear canvas
        ctx.fillStyle = 'rgba(10, 10, 10, 0.2)';
        ctx.fillRect(0, 0, width, height);
        
        // Set line style based on consciousness level
        const consciousness = this.nexus.config.consciousness.level;
        const hue = 120 + (consciousness * 60); // Green to cyan
        ctx.strokeStyle = `hsla(${hue}, 100%, 50%, 0.8)`;
        ctx.lineWidth = 2;
        
        // Draw waveform
        ctx.beginPath();
        
        const sliceWidth = width / this.bufferLength;
        let x = 0;
        
        for (let i = 0; i < this.bufferLength; i++) {
            const v = this.dataArray[i] / 128.0;
            const y = v * height / 2;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
            
            x += sliceWidth;
        }
        
        ctx.lineTo(width, height / 2);
        ctx.stroke();
        
        // Add glow effect for high amplitude
        const amplitude = this.calculateAmplitude();
        if (amplitude > 0.3) {
            ctx.shadowBlur = 20 * amplitude;
            ctx.shadowColor = `hsla(${hue}, 100%, 50%, 0.5)`;
            ctx.stroke();
            ctx.shadowBlur = 0;
        }
    }

    clearWaveform() {
        const { width, height } = this.canvas;
        this.canvasCtx.clearRect(0, 0, width, height);
    }

    updateFrequencyBars() {
        // Calculate bar heights based on frequency data
        const barCount = this.frequencyBars.length;
        const samplesPerBar = Math.floor(this.frequencyData.length / barCount);
        
        for (let i = 0; i < barCount; i++) {
            let sum = 0;
            const offset = i * samplesPerBar;
            
            // Average frequency data for this bar
            for (let j = 0; j < samplesPerBar; j++) {
                sum += this.frequencyData[offset + j];
            }
            
            const average = sum / samplesPerBar;
            const height = (average / 255) * 100;
            
            // Update bar height with easing
            const bar = this.frequencyBars[i];
            const currentHeight = parseFloat(bar.style.height) || 0;
            const newHeight = currentHeight + (height - currentHeight) * 0.3;
            bar.style.height = `${newHeight}%`;
            
            // Color based on frequency range
            const hue = 120 + (i / barCount) * 60;
            bar.style.background = `linear-gradient(to top, 
                hsla(${hue}, 100%, 50%, 0.8), 
                hsla(${hue + 30}, 100%, 60%, 0.9))`;
        }
    }

    resetFrequencyBars() {
        this.frequencyBars.forEach(bar => {
            bar.style.height = '2px';
        });
    }

    updateMetrics() {
        // Calculate volume
        let sum = 0;
        for (let i = 0; i < this.dataArray.length; i++) {
            const value = Math.abs(this.dataArray[i] - 128) / 128;
            sum += value;
        }
        this.metrics.volume = sum / this.dataArray.length;
        
        // Calculate clarity (based on frequency distribution)
        const freqSum = this.frequencyData.reduce((a, b) => a + b, 0);
        const freqAvg = freqSum / this.frequencyData.length;
        let variance = 0;
        for (let i = 0; i < this.frequencyData.length; i++) {
            variance += Math.pow(this.frequencyData[i] - freqAvg, 2);
        }
        this.metrics.clarity = 1 - (Math.sqrt(variance / this.frequencyData.length) / 255);
        
        // Calculate frequency bands
        const bandSize = Math.floor(this.frequencyData.length / 3);
        this.metrics.frequency.low = this.calculateBandAverage(0, bandSize);
        this.metrics.frequency.mid = this.calculateBandAverage(bandSize, bandSize * 2);
        this.metrics.frequency.high = this.calculateBandAverage(bandSize * 2, this.frequencyData.length);
        
        // Update UI
        this.updateMetersUI();
    }

    calculateBandAverage(start, end) {
        let sum = 0;
        for (let i = start; i < end; i++) {
            sum += this.frequencyData[i];
        }
        return (sum / (end - start)) / 255;
    }

    updateMetersUI() {
        // Update volume meter
        if (this.volumeMeter) {
            const volumePercent = Math.min(this.metrics.volume * 200, 100);
            this.volumeMeter.style.width = `${volumePercent}%`;
        }
        
        // Update clarity meter
        if (this.clarityMeter) {
            const clarityPercent = this.metrics.clarity * 100;
            this.clarityMeter.style.width = `${clarityPercent}%`;
        }
    }

    detectEmotion() {
        // Simple emotion detection based on audio characteristics
        const { low, mid, high } = this.metrics.frequency;
        const volume = this.metrics.volume;
        
        let emotion = 'neutral';
        let confidence = 0.5;
        
        if (volume < 0.1) {
            emotion = 'quiet';
            confidence = 0.8;
        } else if (high > 0.6 && volume > 0.3) {
            emotion = 'excited';
            confidence = 0.7;
        } else if (low > 0.7 && mid < 0.3) {
            emotion = 'calm';
            confidence = 0.6;
        } else if (mid > 0.6 && volume > 0.4) {
            emotion = 'engaged';
            confidence = 0.7;
        } else if (low > 0.5 && high < 0.3) {
            emotion = 'serious';
            confidence = 0.6;
        }
        
        // Update emotion if confidence is high enough
        if (confidence > 0.6 && emotion !== this.emotions.current) {
            this.emotions.current = emotion;
            this.emotions.confidence = confidence;
            this.updateEmotionDisplay();
            
            // Emit emotion event
            this.nexus.emit('audio-emotion', {
                emotion: emotion,
                confidence: confidence,
                metrics: this.metrics
            });
        }
    }

    updateEmotionDisplay() {
        const emotionMap = {
            neutral: { icon: '😊', text: 'Neutral' },
            quiet: { icon: '🤫', text: 'Quiet' },
            excited: { icon: '🎉', text: 'Excited' },
            calm: { icon: '😌', text: 'Calm' },
            engaged: { icon: '🤝', text: 'Engaged' },
            serious: { icon: '🧐', text: 'Serious' }
        };
        
        const emotion = emotionMap[this.emotions.current] || emotionMap.neutral;
        
        if (this.emotionIcon) {
            this.emotionIcon.textContent = emotion.icon;
        }
        
        if (this.emotionText) {
            this.emotionText.textContent = emotion.text;
        }
    }

    calculateAmplitude() {
        let sum = 0;
        for (let i = 0; i < this.dataArray.length; i++) {
            sum += Math.abs(this.dataArray[i] - 128);
        }
        return sum / (this.dataArray.length * 128);
    }

    // Public methods for external control
    updateEmotion(data) {
        if (data.emotion && data.emotion !== this.emotions.current) {
            this.emotions.current = data.emotion;
            this.emotions.confidence = data.confidence || 0.8;
            this.updateEmotionDisplay();
        }
    }

    setConsciousnessLevel(level) {
        // Adjust visual parameters based on consciousness level
        if (level > 0.9) {
            document.getElementById('audio-visual-panel').classList.add('high-consciousness');
        } else {
            document.getElementById('audio-visual-panel').classList.remove('high-consciousness');
        }
    }
}

// Register with window for global access
window.NexusAudioIntegration = NexusAudioIntegration;