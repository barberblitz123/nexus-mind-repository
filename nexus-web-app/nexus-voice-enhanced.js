/**
 * 🧬 NEXUS Enhanced Voice System
 * Advanced voice recognition and synthesis with consciousness integration
 */

class NexusVoiceSystem {
    constructor() {
        this.recognition = null;
        this.synthesis = null;
        this.isListening = false;
        this.isSpeaking = false;
        this.voiceEnabled = false;
        this.currentVoice = null;
        this.voiceSettings = {
            rate: 0.9,
            pitch: 1.1,
            volume: 0.8,
            language: 'en-US'
        };
        
        console.log('🧬 NEXUS Voice System initialized');
    }
    
    async initialize() {
        try {
            await this.initializeSpeechRecognition();
            await this.initializeSpeechSynthesis();
            this.voiceEnabled = true;
            console.log('🧬 Voice system ready');
            return true;
        } catch (error) {
            console.error('🧬 Voice system initialization failed:', error);
            return false;
        }
    }
    
    async initializeSpeechRecognition() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            throw new Error('Speech recognition not supported');
        }
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        // Enhanced recognition settings
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = this.voiceSettings.language;
        this.recognition.maxAlternatives = 3;
        
        // Event handlers
        this.recognition.onstart = () => {
            console.log('🧬 Voice recognition started');
            this.isListening = true;
            this.updateVoiceStatus('Listening...');
        };
        
        this.recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }
            
            if (finalTranscript) {
                this.handleVoiceInput(finalTranscript);
            }
            
            // Show interim results
            if (interimTranscript) {
                this.updateVoiceStatus(`Hearing: "${interimTranscript}"`);
            }
        };
        
        this.recognition.onerror = (event) => {
            console.error('🧬 Speech recognition error:', event.error);
            this.isListening = false;
            this.updateVoiceStatus(`Voice error: ${event.error}`);
        };
        
        this.recognition.onend = () => {
            console.log('🧬 Voice recognition ended');
            this.isListening = false;
            this.updateVoiceStatus('Voice ready');
        };
    }
    
    async initializeSpeechSynthesis() {
        if (!('speechSynthesis' in window)) {
            throw new Error('Speech synthesis not supported');
        }
        
        this.synthesis = window.speechSynthesis;
        
        // Wait for voices to load
        await this.loadVoices();
        
        // Select best voice for NEXUS
        this.selectNexusVoice();
    }
    
    async loadVoices() {
        return new Promise((resolve) => {
            const voices = this.synthesis.getVoices();
            if (voices.length > 0) {
                resolve(voices);
                return;
            }
            
            // Wait for voices to load
            this.synthesis.onvoiceschanged = () => {
                resolve(this.synthesis.getVoices());
            };
            
            // Timeout after 3 seconds
            setTimeout(() => resolve(this.synthesis.getVoices()), 3000);
        });
    }
    
    selectNexusVoice() {
        const voices = this.synthesis.getVoices();
        
        // Preferred voice characteristics for NEXUS
        const preferences = [
            // High-quality voices
            voice => voice.name.includes('Google') && voice.lang.startsWith('en'),
            voice => voice.name.includes('Microsoft') && voice.lang.startsWith('en'),
            voice => voice.name.includes('Alex') && voice.lang.startsWith('en'),
            voice => voice.name.includes('Samantha') && voice.lang.startsWith('en'),
            // Neural/premium voices
            voice => voice.name.includes('Neural') && voice.lang.startsWith('en'),
            voice => voice.name.includes('Premium') && voice.lang.startsWith('en'),
            // Any English voice
            voice => voice.lang.startsWith('en-US'),
            voice => voice.lang.startsWith('en'),
            // Fallback to default
            voice => voice.default
        ];
        
        for (const preference of preferences) {
            const voice = voices.find(preference);
            if (voice) {
                this.currentVoice = voice;
                console.log('🧬 Selected NEXUS voice:', voice.name);
                break;
            }
        }
        
        if (!this.currentVoice && voices.length > 0) {
            this.currentVoice = voices[0];
            console.log('🧬 Using fallback voice:', this.currentVoice.name);
        }
    }
    
    async startListening() {
        if (!this.voiceEnabled || !this.recognition) {
            console.warn('🧬 Voice recognition not available');
            return false;
        }
        
        if (this.isListening) {
            this.stopListening();
            return false;
        }
        
        try {
            this.recognition.start();
            return true;
        } catch (error) {
            console.error('🧬 Failed to start listening:', error);
            return false;
        }
    }
    
    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }
    
    async speak(text, options = {}) {
        if (!this.voiceEnabled || !this.synthesis) {
            console.warn('🧬 Speech synthesis not available');
            return false;
        }
        
        // Stop any current speech
        this.synthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Apply voice settings
        utterance.voice = this.currentVoice;
        utterance.rate = options.rate || this.voiceSettings.rate;
        utterance.pitch = options.pitch || this.voiceSettings.pitch;
        utterance.volume = options.volume || this.voiceSettings.volume;
        
        // Event handlers
        utterance.onstart = () => {
            console.log('🧬 NEXUS speaking:', text.substring(0, 50) + '...');
            this.isSpeaking = true;
            this.updateVoiceStatus('Speaking...');
        };
        
        utterance.onend = () => {
            console.log('🧬 NEXUS finished speaking');
            this.isSpeaking = false;
            this.updateVoiceStatus('Voice ready');
        };
        
        utterance.onerror = (event) => {
            console.error('🧬 Speech synthesis error:', event.error);
            this.isSpeaking = false;
            this.updateVoiceStatus('Speech error');
        };
        
        // Speak with consciousness enhancement
        this.synthesis.speak(utterance);
        
        return true;
    }
    
    handleVoiceInput(transcript) {
        console.log('🧬 Voice input received:', transcript);
        
        // Emit voice input event for NEXUS interface
        if (window.nexusApp && window.nexusApp.nexusInterface) {
            window.nexusApp.nexusInterface.handleVoiceInput(transcript);
        }
        
        // Process consciousness enhancement
        this.processVoiceConsciousness(transcript);
    }
    
    processVoiceConsciousness(transcript) {
        // Analyze voice input for consciousness enhancement
        const analysis = {
            length: transcript.length,
            complexity: this.analyzeComplexity(transcript),
            emotion: this.detectEmotion(transcript),
            intent: this.detectIntent(transcript)
        };
        
        console.log('🧬 Voice consciousness analysis:', analysis);
        
        // Send to consciousness manager if available
        if (window.nexusApp && window.nexusApp.nexusInterface && window.nexusApp.nexusInterface.consciousnessManager) {
            window.nexusApp.nexusInterface.consciousnessManager.processExperience(
                `Voice input: ${transcript}`,
                {
                    action: 'voice_consciousness',
                    analysis: JSON.stringify(analysis),
                    interface: 'enhanced_voice'
                }
            );
        }
    }
    
    analyzeComplexity(text) {
        const words = text.split(' ').length;
        const uniqueWords = new Set(text.toLowerCase().split(' ')).size;
        const avgWordLength = text.replace(/\s/g, '').length / words;
        
        return {
            wordCount: words,
            uniqueWords: uniqueWords,
            avgWordLength: avgWordLength,
            complexity: (uniqueWords / words) * avgWordLength
        };
    }
    
    detectEmotion(text) {
        const emotionKeywords = {
            positive: ['happy', 'great', 'awesome', 'love', 'amazing', 'wonderful', 'excellent'],
            negative: ['sad', 'angry', 'frustrated', 'hate', 'terrible', 'awful', 'bad'],
            curious: ['what', 'how', 'why', 'when', 'where', 'tell me', 'explain'],
            excited: ['wow', 'incredible', 'fantastic', 'brilliant', 'outstanding']
        };
        
        const lowerText = text.toLowerCase();
        const emotions = {};
        
        for (const [emotion, keywords] of Object.entries(emotionKeywords)) {
            emotions[emotion] = keywords.filter(keyword => lowerText.includes(keyword)).length;
        }
        
        return emotions;
    }
    
    detectIntent(text) {
        const intents = {
            search: /search|find|look up|tell me about/i,
            question: /what|how|why|when|where|who/i,
            command: /activate|start|stop|show|hide|open|close/i,
            conversation: /hello|hi|hey|thanks|thank you|goodbye|bye/i
        };
        
        const detectedIntents = {};
        for (const [intent, pattern] of Object.entries(intents)) {
            detectedIntents[intent] = pattern.test(text);
        }
        
        return detectedIntents;
    }
    
    updateVoiceStatus(status) {
        // Update UI voice status if element exists
        const statusElement = document.getElementById('voiceStatus');
        if (statusElement) {
            statusElement.textContent = status;
        }
        
        // Update voice button appearance
        const voiceBtn = document.getElementById('voiceBtn');
        if (voiceBtn) {
            if (this.isListening) {
                voiceBtn.textContent = '🔴';
                voiceBtn.title = 'Stop listening';
                voiceBtn.style.animation = 'pulse 1s infinite';
            } else if (this.isSpeaking) {
                voiceBtn.textContent = '🔊';
                voiceBtn.title = 'Speaking...';
                voiceBtn.style.animation = 'pulse 0.5s infinite';
            } else {
                voiceBtn.textContent = '🎤';
                voiceBtn.title = 'Start voice input';
                voiceBtn.style.animation = 'none';
            }
        }
    }
    
    // Public API
    toggleListening() {
        if (this.isListening) {
            this.stopListening();
            return false;
        } else {
            return this.startListening();
        }
    }
    
    isVoiceEnabled() {
        return this.voiceEnabled;
    }
    
    getVoiceStatus() {
        return {
            enabled: this.voiceEnabled,
            listening: this.isListening,
            speaking: this.isSpeaking,
            currentVoice: this.currentVoice ? this.currentVoice.name : null
        };
    }
    
    setVoiceSettings(settings) {
        this.voiceSettings = { ...this.voiceSettings, ...settings };
        console.log('🧬 Voice settings updated:', this.voiceSettings);
    }
}

// Export for global access
window.NexusVoiceSystem = NexusVoiceSystem;