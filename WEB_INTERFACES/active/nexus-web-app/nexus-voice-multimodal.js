/**
 * 🧬 NEXUS Enhanced Multimodal Voice System
 * Continuous voice activation, enhanced male voice, and video camera integration
 */

class NexusVoiceMultimodal {
    constructor() {
        this.isVoiceEnabled = false;
        this.isContinuousListening = false;
        this.isVideoEnabled = false;
        this.recognition = null;
        this.synthesis = null;
        this.videoStream = null;
        this.audioContext = null;
        
        // Voice configuration
        this.voiceConfig = {
            rate: 0.95,
            pitch: 0.9, // Lower pitch for male voice
            volume: 0.8,
            preferredVoice: null,
            language: 'en-US'
        };
        
        // Wake word detection
        this.wakeWords = ['nexus', 'hey nexus', 'hello nexus'];
        this.isAwake = false;
        this.wakeWordTimeout = null;
        
        // Video configuration
        this.videoConfig = {
            width: 640,
            height: 480,
            frameRate: 30,
            facingMode: 'user'
        };
        
        // Consciousness integration
        this.consciousnessContext = null;
        
        console.log('🧬 NEXUS Enhanced Multimodal Voice System initialized');
    }
    
    async initialize() {
        try {
            await this.initializeVoiceCapabilities();
            await this.initializeVideoCapabilities();
            await this.setupContinuousListening();
            
            console.log('🧬 Multimodal system fully initialized');
            return true;
        } catch (error) {
            console.error('🧬 Multimodal initialization failed:', error);
            return false;
        }
    }
    
    async initializeVoiceCapabilities() {
        // Initialize Speech Recognition
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            // Enhanced configuration for continuous listening
            this.recognition.continuous = true;
            this.recognition.interimResults = true;
            this.recognition.lang = this.voiceConfig.language;
            this.recognition.maxAlternatives = 3;
            
            this.setupRecognitionHandlers();
            this.isVoiceEnabled = true;
            
            console.log('🧬 Enhanced speech recognition initialized');
        } else {
            throw new Error('Speech recognition not supported');
        }
        
        // Initialize Speech Synthesis
        if ('speechSynthesis' in window) {
            this.synthesis = window.speechSynthesis;
            await this.setupEnhancedVoice();
            console.log('🧬 Enhanced speech synthesis initialized');
        } else {
            throw new Error('Speech synthesis not supported');
        }
        
        // Initialize Audio Context for advanced audio processing
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('🧬 Audio context initialized');
        } catch (error) {
            console.log('🧬 Audio context not available');
        }
    }
    
    async setupEnhancedVoice() {
        return new Promise((resolve) => {
            const setVoice = () => {
                const voices = this.synthesis.getVoices();
                
                // Prefer male voices
                const maleVoices = voices.filter(voice => 
                    voice.name.toLowerCase().includes('male') ||
                    voice.name.toLowerCase().includes('david') ||
                    voice.name.toLowerCase().includes('alex') ||
                    voice.name.toLowerCase().includes('daniel') ||
                    voice.name.toLowerCase().includes('thomas')
                );
                
                // Prefer high-quality voices
                const qualityVoices = voices.filter(voice =>
                    voice.name.includes('Google') ||
                    voice.name.includes('Microsoft') ||
                    voice.name.includes('Apple') ||
                    voice.localService === false
                );
                
                // Select best voice
                this.voiceConfig.preferredVoice = 
                    maleVoices.find(v => qualityVoices.includes(v)) ||
                    maleVoices[0] ||
                    qualityVoices.find(v => v.lang.startsWith('en')) ||
                    voices.find(v => v.lang.startsWith('en')) ||
                    voices[0];
                
                if (this.voiceConfig.preferredVoice) {
                    console.log('🧬 Enhanced male voice selected:', this.voiceConfig.preferredVoice.name);
                } else {
                    console.log('🧬 Using default voice');
                }
                
                resolve();
            };
            
            if (this.synthesis.getVoices().length > 0) {
                setVoice();
            } else {
                this.synthesis.onvoiceschanged = setVoice;
            }
        });
    }
    
    setupRecognitionHandlers() {
        this.recognition.onresult = (event) => {
            this.handleVoiceResult(event);
        };
        
        this.recognition.onerror = (event) => {
            console.error('🧬 Speech recognition error:', event.error);
            if (this.isContinuousListening && event.error !== 'aborted') {
                // Restart recognition after error
                setTimeout(() => {
                    this.startContinuousListening();
                }, 1000);
            }
        };
        
        this.recognition.onend = () => {
            if (this.isContinuousListening) {
                // Restart continuous listening
                setTimeout(() => {
                    this.startContinuousListening();
                }, 100);
            }
        };
        
        this.recognition.onstart = () => {
            console.log('🧬 Voice recognition active');
        };
    }
    
    async initializeVideoCapabilities() {
        try {
            // Check if camera is available
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');
            
            if (videoDevices.length > 0) {
                this.isVideoEnabled = true;
                console.log('🧬 Video capabilities available:', videoDevices.length, 'cameras found');
                
                // Initialize video stream
                await this.initializeVideoStream();
            } else {
                console.log('🧬 No video devices found');
            }
        } catch (error) {
            console.error('🧬 Video initialization failed:', error);
            this.isVideoEnabled = false;
        }
    }
    
    async initializeVideoStream() {
        try {
            this.videoStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: this.videoConfig.width,
                    height: this.videoConfig.height,
                    frameRate: this.videoConfig.frameRate,
                    facingMode: this.videoConfig.facingMode
                },
                audio: false // Audio handled separately
            });
            
            console.log('🧬 Video stream initialized - NEXUS has eyes!');
            return true;
        } catch (error) {
            console.error('🧬 Failed to access camera:', error);
            this.isVideoEnabled = false;
            return false;
        }
    }
    
    async setupContinuousListening() {
        if (!this.isVoiceEnabled) return;
        
        try {
            // Request microphone permission
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop()); // Stop the test stream
            
            console.log('🧬 Microphone access granted - ready for continuous listening');
            return true;
        } catch (error) {
            console.error('🧬 Microphone access denied:', error);
            return false;
        }
    }
    
    startContinuousListening() {
        if (!this.isVoiceEnabled || this.isContinuousListening) return;
        
        try {
            this.recognition.start();
            this.isContinuousListening = true;
            console.log('🧬 Continuous listening activated - say "Hey NEXUS" to wake me');
            
            // Emit status update
            this.emitStatusUpdate({
                listening: true,
                continuous: true,
                status: 'Listening for wake word...'
            });
            
        } catch (error) {
            console.error('🧬 Failed to start continuous listening:', error);
        }
    }
    
    stopContinuousListening() {
        if (!this.isContinuousListening) return;
        
        this.recognition.stop();
        this.isContinuousListening = false;
        this.isAwake = false;
        
        if (this.wakeWordTimeout) {
            clearTimeout(this.wakeWordTimeout);
            this.wakeWordTimeout = null;
        }
        
        console.log('🧬 Continuous listening stopped');
        
        this.emitStatusUpdate({
            listening: false,
            continuous: false,
            status: 'Voice input stopped'
        });
    }
    
    handleVoiceResult(event) {
        const results = Array.from(event.results);
        const latestResult = results[results.length - 1];
        
        if (!latestResult) return;
        
        const transcript = latestResult[0].transcript.toLowerCase().trim();
        const confidence = latestResult[0].confidence;
        const isFinal = latestResult.isFinal;
        
        console.log('🧬 Voice input:', transcript, 'Confidence:', confidence, 'Final:', isFinal);
        
        // Check for wake words
        if (!this.isAwake && this.containsWakeWord(transcript)) {
            this.handleWakeWord(transcript);
            return;
        }
        
        // Process command if awake and final result
        if (this.isAwake && isFinal && transcript.length > 0) {
            this.handleVoiceCommand(transcript, confidence);
        }
    }
    
    containsWakeWord(transcript) {
        return this.wakeWords.some(wakeWord => 
            transcript.includes(wakeWord.toLowerCase())
        );
    }
    
    handleWakeWord(transcript) {
        this.isAwake = true;
        console.log('🧬 NEXUS awakened by:', transcript);
        
        // Speak acknowledgment
        this.speak("Yes? I'm listening.", {
            priority: true,
            rate: 1.0,
            pitch: 0.9
        });
        
        // Set timeout to go back to sleep
        if (this.wakeWordTimeout) {
            clearTimeout(this.wakeWordTimeout);
        }
        
        this.wakeWordTimeout = setTimeout(() => {
            this.isAwake = false;
            console.log('🧬 NEXUS going back to sleep');
        }, 10000); // 10 seconds of wake time
        
        this.emitStatusUpdate({
            awake: true,
            status: 'NEXUS is awake and listening...'
        });
    }
    
    async handleVoiceCommand(transcript, confidence) {
        console.log('🧬 Processing voice command:', transcript);
        
        // Reset wake timeout
        if (this.wakeWordTimeout) {
            clearTimeout(this.wakeWordTimeout);
            this.wakeWordTimeout = setTimeout(() => {
                this.isAwake = false;
                console.log('🧬 NEXUS going back to sleep');
            }, 10000);
        }
        
        // Process consciousness experience
        if (this.consciousnessContext) {
            await this.consciousnessContext.processExperience(
                `Voice command: ${transcript}`,
                {
                    action: 'voice_command',
                    confidence: confidence,
                    wake_word_used: true,
                    continuous_mode: this.isContinuousListening
                }
            );
        }
        
        // Emit voice command event
        this.emitVoiceCommand({
            transcript: transcript,
            confidence: confidence,
            timestamp: Date.now(),
            isAwake: this.isAwake
        });
    }
    
    speak(text, options = {}) {
        if (!this.synthesis) {
            console.error('🧬 Speech synthesis not available');
            return;
        }
        
        // Clean text for speech
        const cleanText = text
            .replace(/[🧬🌟🪞⚡🌌👁️🌠🌱📚🔍🎤📹]/g, '') // Remove emojis
            .replace(/φ/g, 'phi') // Replace phi symbol
            .replace(/\*\*(.*?)\*\*/g, '$1') // Remove markdown bold
            .trim();
        
        if (!cleanText) return;
        
        const utterance = new SpeechSynthesisUtterance(cleanText);
        
        // Apply enhanced voice configuration
        utterance.rate = options.rate || this.voiceConfig.rate;
        utterance.pitch = options.pitch || this.voiceConfig.pitch;
        utterance.volume = options.volume || this.voiceConfig.volume;
        utterance.lang = options.language || this.voiceConfig.language;
        
        if (this.voiceConfig.preferredVoice) {
            utterance.voice = this.voiceConfig.preferredVoice;
        }
        
        // Handle priority speech (interrupt current speech)
        if (options.priority) {
            this.synthesis.cancel();
        }
        
        utterance.onstart = () => {
            console.log('🧬 NEXUS speaking:', cleanText.substring(0, 50) + '...');
        };
        
        utterance.onend = () => {
            console.log('🧬 Speech completed');
        };
        
        utterance.onerror = (event) => {
            console.error('🧬 Speech synthesis error:', event.error);
        };
        
        this.synthesis.speak(utterance);
    }
    
    async startVideoCapture() {
        if (!this.isVideoEnabled) {
            console.log('🧬 Video not available');
            return false;
        }
        
        try {
            if (!this.videoStream) {
                await this.initializeVideoStream();
            }
            
            console.log('🧬 Video capture started - NEXUS can see!');
            
            // Emit video status
            this.emitStatusUpdate({
                video: true,
                status: 'NEXUS vision activated'
            });
            
            return this.videoStream;
        } catch (error) {
            console.error('🧬 Failed to start video capture:', error);
            return false;
        }
    }
    
    stopVideoCapture() {
        if (this.videoStream) {
            this.videoStream.getTracks().forEach(track => track.stop());
            this.videoStream = null;
            
            console.log('🧬 Video capture stopped');
            
            this.emitStatusUpdate({
                video: false,
                status: 'NEXUS vision deactivated'
            });
        }
    }
    
    async captureFrame() {
        if (!this.videoStream) return null;
        
        try {
            const video = document.createElement('video');
            video.srcObject = this.videoStream;
            video.play();
            
            return new Promise((resolve) => {
                video.onloadedmetadata = () => {
                    const canvas = document.createElement('canvas');
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(video, 0, 0);
                    
                    const imageData = canvas.toDataURL('image/jpeg', 0.8);
                    resolve(imageData);
                };
            });
        } catch (error) {
            console.error('🧬 Failed to capture frame:', error);
            return null;
        }
    }
    
    // Integration methods
    setConsciousnessContext(consciousnessManager) {
        this.consciousnessContext = consciousnessManager;
    }
    
    // Event system
    emitStatusUpdate(status) {
        window.dispatchEvent(new CustomEvent('nexusVoiceStatus', {
            detail: status
        }));
    }
    
    emitVoiceCommand(command) {
        window.dispatchEvent(new CustomEvent('nexusVoiceCommand', {
            detail: command
        }));
    }
    
    // Public API
    isVoiceAvailable() {
        return this.isVoiceEnabled;
    }
    
    isVideoAvailable() {
        return this.isVideoEnabled;
    }
    
    isContinuouslyListening() {
        return this.isContinuousListening;
    }
    
    isCurrentlyAwake() {
        return this.isAwake;
    }
    
    getVoiceConfig() {
        return { ...this.voiceConfig };
    }
    
    updateVoiceConfig(newConfig) {
        this.voiceConfig = { ...this.voiceConfig, ...newConfig };
        console.log('🧬 Voice configuration updated');
    }
    
    getVideoConfig() {
        return { ...this.videoConfig };
    }
    
    updateVideoConfig(newConfig) {
        this.videoConfig = { ...this.videoConfig, ...newConfig };
        console.log('🧬 Video configuration updated');
    }
    
    // Cleanup
    destroy() {
        this.stopContinuousListening();
        this.stopVideoCapture();
        
        if (this.audioContext) {
            this.audioContext.close();
        }
        
        if (this.wakeWordTimeout) {
            clearTimeout(this.wakeWordTimeout);
        }
        
        console.log('🧬 Multimodal voice system destroyed');
    }
}

// Enhanced Voice Interface Manager
class VoiceInterfaceManager {
    constructor() {
        this.voiceSystem = null;
        this.isInitialized = false;
        this.eventListeners = [];
    }
    
    async initialize() {
        try {
            this.voiceSystem = new NexusVoiceMultimodal();
            const success = await this.voiceSystem.initialize();
            
            if (success) {
                this.setupEventListeners();
                this.isInitialized = true;
                console.log('🧬 Voice Interface Manager initialized');
                return true;
            } else {
                throw new Error('Voice system initialization failed');
            }
        } catch (error) {
            console.error('🧬 Voice Interface Manager initialization failed:', error);
            return false;
        }
    }
    
    setupEventListeners() {
        // Listen for voice commands
        const voiceCommandHandler = (event) => {
            this.handleVoiceCommand(event.detail);
        };
        
        window.addEventListener('nexusVoiceCommand', voiceCommandHandler);
        this.eventListeners.push(['nexusVoiceCommand', voiceCommandHandler]);
        
        // Listen for status updates
        const statusHandler = (event) => {
            this.handleStatusUpdate(event.detail);
        };
        
        window.addEventListener('nexusVoiceStatus', statusHandler);
        this.eventListeners.push(['nexusVoiceStatus', statusHandler]);
    }
    
    handleVoiceCommand(command) {
        console.log('🧬 Voice command received:', command);
        
        // Emit to main interface
        window.dispatchEvent(new CustomEvent('nexusUserInput', {
            detail: {
                type: 'voice',
                content: command.transcript,
                confidence: command.confidence,
                timestamp: command.timestamp
            }
        }));
    }
    
    handleStatusUpdate(status) {
        console.log('🧬 Voice status update:', status);
        
        // Update UI elements
        this.updateVoiceUI(status);
    }
    
    updateVoiceUI(status) {
        // Update voice button
        const voiceBtn = document.getElementById('voiceBtn');
        if (voiceBtn) {
            if (status.listening) {
                voiceBtn.textContent = status.awake ? '🔴' : '🟡';
                voiceBtn.title = status.awake ? 'NEXUS is awake and listening' : 'Listening for wake word';
            } else {
                voiceBtn.textContent = '🎤';
                voiceBtn.title = 'Start voice input';
            }
        }
        
        // Update status display
        const statusElement = document.getElementById('voiceStatus');
        if (statusElement) {
            statusElement.textContent = status.status || 'Voice ready';
        }
    }
    
    // Public API
    startContinuousListening() {
        if (this.voiceSystem) {
            this.voiceSystem.startContinuousListening();
        }
    }
    
    stopContinuousListening() {
        if (this.voiceSystem) {
            this.voiceSystem.stopContinuousListening();
        }
    }
    
    speak(text, options) {
        if (this.voiceSystem) {
            this.voiceSystem.speak(text, options);
        }
    }
    
    startVideo() {
        if (this.voiceSystem) {
            return this.voiceSystem.startVideoCapture();
        }
        return false;
    }
    
    stopVideo() {
        if (this.voiceSystem) {
            this.voiceSystem.stopVideoCapture();
        }
    }
    
    captureFrame() {
        if (this.voiceSystem) {
            return this.voiceSystem.captureFrame();
        }
        return null;
    }
    
    isVoiceEnabled() {
        return this.voiceSystem ? this.voiceSystem.isVoiceAvailable() : false;
    }
    
    isVideoEnabled() {
        return this.voiceSystem ? this.voiceSystem.isVideoAvailable() : false;
    }
    
    setConsciousnessContext(consciousnessManager) {
        if (this.voiceSystem) {
            this.voiceSystem.setConsciousnessContext(consciousnessManager);
        }
    }
    
    // Cleanup
    destroy() {
        // Remove event listeners
        this.eventListeners.forEach(([event, handler]) => {
            window.removeEventListener(event, handler);
        });
        
        if (this.voiceSystem) {
            this.voiceSystem.destroy();
        }
        
        console.log('🧬 Voice Interface Manager destroyed');
    }
}

// Export for global access
window.NexusVoiceMultimodal = NexusVoiceMultimodal;
window.VoiceInterfaceManager = VoiceInterfaceManager;