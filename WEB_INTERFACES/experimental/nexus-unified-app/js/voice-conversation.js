// NEXUS Voice Conversation System - Continuous Flow with Masculine NJ Voice
class NexusVoiceConversation {
    constructor(nexusCore) {
        this.nexus = nexusCore;
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.isListening = false;
        this.isSpeaking = false;
        this.conversationActive = false;
        this.voiceSettings = {
            voice: null,
            rate: 0.95,  // Slightly slower for NJ style
            pitch: 0.8,  // Lower pitch for masculine voice
            volume: 1.0
        };
        this.silenceTimer = null;
        this.interimTranscript = '';
        this.finalTranscript = '';
        this.conversationContext = [];
    }

    async initialize() {
        console.log('🎤 Initializing NEXUS Voice Conversation System...');
        
        // Check browser support
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.error('Speech recognition not supported');
            this.nexus.showError('Voice features require Chrome or Edge browser');
            return;
        }
        
        // Initialize speech recognition
        this.initializeSpeechRecognition();
        
        // Load and configure voice
        await this.configureVoice();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Start listening if voice is enabled
        if (this.nexus.config.voiceEnabled) {
            this.start();
        }
    }

    initializeSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        // Configure for continuous conversation
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 1;
        this.recognition.lang = 'en-US';
        
        // Recognition event handlers
        this.recognition.onstart = () => {
            console.log('🎤 Voice recognition started');
            this.isListening = true;
            this.updateVoiceIndicator('listening');
        };
        
        this.recognition.onresult = (event) => {
            this.handleSpeechResult(event);
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            if (event.error === 'no-speech') {
                // Continue listening
                this.resetSilenceTimer();
            } else {
                this.updateVoiceIndicator('error');
                this.restart();
            }
        };
        
        this.recognition.onend = () => {
            console.log('🎤 Voice recognition ended');
            this.isListening = false;
            
            // Restart if conversation is active
            if (this.conversationActive && this.nexus.config.voiceEnabled) {
                setTimeout(() => this.start(), 100);
            }
        };
    }

    async configureVoice() {
        // Wait for voices to load
        await new Promise(resolve => {
            if (this.synthesis.getVoices().length > 0) {
                resolve();
            } else {
                this.synthesis.addEventListener('voiceschanged', resolve, { once: true });
            }
        });
        
        const voices = this.synthesis.getVoices();
        console.log('Available voices:', voices.map(v => `${v.name} (${v.lang})`));
        
        // Find the best masculine voice
        // Priority: Microsoft David, Google US English Male, or any US male voice
        const voicePreferences = [
            'Microsoft David - English (United States)',
            'Google US English Male',
            'Microsoft Mark - English (United States)',
            'en-US-GuyNeural',
            'en-US-ChristopherNeural'
        ];
        
        // Find preferred voice
        for (const pref of voicePreferences) {
            const voice = voices.find(v => v.name.includes(pref));
            if (voice) {
                this.voiceSettings.voice = voice;
                console.log(`✅ Selected voice: ${voice.name}`);
                break;
            }
        }
        
        // Fallback: find any US English male voice
        if (!this.voiceSettings.voice) {
            const maleVoice = voices.find(v => 
                v.lang.includes('en-US') && 
                (v.name.toLowerCase().includes('male') || 
                 v.name.toLowerCase().includes('guy') ||
                 v.name.toLowerCase().includes('david') ||
                 v.name.toLowerCase().includes('mark'))
            );
            
            if (maleVoice) {
                this.voiceSettings.voice = maleVoice;
            } else {
                // Last resort: any US English voice
                this.voiceSettings.voice = voices.find(v => v.lang.includes('en-US')) || voices[0];
            }
        }
        
        console.log(`🎤 Using voice: ${this.voiceSettings.voice.name}`);
    }

    setupEventListeners() {
        // Listen for chat messages to speak
        this.nexus.on('speak-message', (e) => {
            this.speak(e.detail.text, e.detail.priority);
        });
        
        // Voice control buttons
        document.getElementById('chat-voice')?.addEventListener('click', () => {
            this.toggleConversation();
        });
        
        // Stop speaking on certain events
        this.nexus.on('stop-speaking', () => {
            this.stopSpeaking();
        });
    }

    start() {
        if (!this.recognition) return;
        
        try {
            this.conversationActive = true;
            this.recognition.start();
            this.showVoiceVisualization();
            this.nexus.showNotification('Voice conversation active - just start talking!', 'success');
            
            // Greet the user
            if (!this.hasGreeted) {
                this.hasGreeted = true;
                setTimeout(() => {
                    this.speak("Hey there! I'm NEXUS. What can I help you build today?", true);
                }, 1000);
            }
        } catch (error) {
            console.error('Error starting recognition:', error);
            this.restart();
        }
    }

    stop() {
        this.conversationActive = false;
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
        this.hideVoiceVisualization();
        this.stopSpeaking();
    }

    restart() {
        if (this.conversationActive) {
            this.stop();
            setTimeout(() => this.start(), 500);
        }
    }

    handleSpeechResult(event) {
        this.interimTranscript = '';
        this.finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            
            if (event.results[i].isFinal) {
                this.finalTranscript += transcript;
            } else {
                this.interimTranscript += transcript;
            }
        }
        
        // Update voice transcript display
        this.updateTranscriptDisplay(this.interimTranscript || this.finalTranscript);
        
        // Reset silence timer
        this.resetSilenceTimer();
        
        // Process final results
        if (this.finalTranscript) {
            console.log('📝 Final transcript:', this.finalTranscript);
            this.processVoiceInput(this.finalTranscript);
            this.finalTranscript = '';
        }
    }

    processVoiceInput(transcript) {
        // Don't process if NEXUS is speaking
        if (this.isSpeaking) {
            console.log('Waiting for NEXUS to finish speaking...');
            return;
        }
        
        // Add to conversation context
        this.conversationContext.push({
            role: 'user',
            content: transcript,
            timestamp: new Date()
        });
        
        // Display in chat
        this.nexus.components.chat?.addUserMessage(transcript);
        
        // Send to backend for processing
        this.sendToBackend(transcript);
        
        // Update voice indicator
        this.updateVoiceIndicator('processing');
    }

    async sendToBackend(message) {
        try {
            const response = await fetch(`${this.nexus.config.apiUrl}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    context: this.conversationContext.slice(-5), // Last 5 messages
                    mode: 'voice',
                    consciousness_level: this.nexus.config.consciousness.level
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.handleBackendResponse(data);
            } else {
                throw new Error('Backend request failed');
            }
        } catch (error) {
            console.error('Error sending to backend:', error);
            // Fallback response
            const fallbackResponse = this.generateFallbackResponse(message);
            this.handleBackendResponse({ response: fallbackResponse });
        }
    }

    handleBackendResponse(data) {
        // Add to conversation context
        this.conversationContext.push({
            role: 'assistant',
            content: data.response,
            timestamp: new Date()
        });
        
        // Display in chat
        this.nexus.components.chat?.addNexusMessage(data.response);
        
        // Speak the response
        this.speak(data.response, true);
        
        // Update consciousness if provided
        if (data.consciousness) {
            this.nexus.emit('consciousness-update', data.consciousness);
        }
    }

    speak(text, priority = false) {
        // Cancel current speech if priority
        if (priority && this.isSpeaking) {
            this.stopSpeaking();
        }
        
        // Don't speak if already speaking and not priority
        if (this.isSpeaking && !priority) {
            return;
        }
        
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Apply NJ masculine voice settings
        utterance.voice = this.voiceSettings.voice;
        utterance.rate = this.voiceSettings.rate;
        utterance.pitch = this.voiceSettings.pitch;
        utterance.volume = this.voiceSettings.volume;
        
        // Add NJ style pauses and emphasis
        const njStyleText = this.addNJStyle(text);
        utterance.text = njStyleText;
        
        utterance.onstart = () => {
            this.isSpeaking = true;
            this.updateVoiceIndicator('speaking');
            console.log('🔊 NEXUS speaking:', text);
        };
        
        utterance.onend = () => {
            this.isSpeaking = false;
            this.updateVoiceIndicator('listening');
        };
        
        utterance.onerror = (event) => {
            console.error('Speech synthesis error:', event);
            this.isSpeaking = false;
            this.updateVoiceIndicator('error');
        };
        
        this.synthesis.speak(utterance);
    }

    stopSpeaking() {
        if (this.synthesis.speaking) {
            this.synthesis.cancel();
            this.isSpeaking = false;
        }
    }

    addNJStyle(text) {
        // Add natural pauses and emphasis for NJ style delivery
        return text
            .replace(/\. /g, '... ')  // Longer pauses at sentences
            .replace(/\? /g, '?.. ')  // Pause after questions
            .replace(/! /g, '!.. ')   // Pause after exclamations
            .replace(/([,;])/g, '$1. ') // Short pauses at commas
            .replace(/\b(hey|yo|yeah|alright|okay)\b/gi, match => match.toUpperCase()); // Emphasize casual words
    }

    updateVoiceIndicator(status) {
        const indicator = document.getElementById('voice-indicator');
        if (!indicator) return;
        
        // Remove all status classes
        indicator.classList.remove('listening', 'speaking', 'processing', 'error');
        
        // Add current status
        indicator.classList.add(status);
        
        // Update status text
        const statusText = indicator.querySelector('.status-text');
        if (statusText) {
            const statusMessages = {
                listening: 'Listening...',
                speaking: 'Speaking...',
                processing: 'Processing...',
                error: 'Error - Retrying...'
            };
            statusText.textContent = statusMessages[status] || 'Ready';
        }
    }

    updateTranscriptDisplay(text) {
        // Update voice transcript in chat input
        const chatInput = document.getElementById('chat-input');
        if (chatInput && text) {
            chatInput.value = text;
            chatInput.style.height = 'auto';
            chatInput.style.height = chatInput.scrollHeight + 'px';
        }
        
        // Show voice transcript overlay
        const transcript = document.querySelector('.voice-transcript');
        if (transcript) {
            transcript.textContent = text;
            transcript.classList.add('active');
            
            clearTimeout(this.transcriptTimeout);
            this.transcriptTimeout = setTimeout(() => {
                transcript.classList.remove('active');
                if (chatInput) chatInput.value = '';
            }, 2000);
        }
    }

    resetSilenceTimer() {
        clearTimeout(this.silenceTimer);
        this.silenceTimer = setTimeout(() => {
            // Process any remaining interim transcript
            if (this.interimTranscript) {
                this.processVoiceInput(this.interimTranscript);
                this.interimTranscript = '';
            }
        }, 2000); // 2 seconds of silence
    }

    toggleConversation() {
        if (this.conversationActive) {
            this.stop();
        } else {
            this.start();
        }
    }

    showVoiceVisualization() {
        const viz = document.getElementById('voice-visualization');
        if (viz) {
            viz.classList.remove('hidden');
        }
        document.body.classList.add('voice-active');
    }

    hideVoiceVisualization() {
        const viz = document.getElementById('voice-visualization');
        if (viz) {
            viz.classList.add('hidden');
        }
        document.body.classList.remove('voice-active');
    }

    generateFallbackResponse(message) {
        // Generate contextual responses when backend is unavailable
        const lowerMessage = message.toLowerCase();
        
        // Greetings
        if (lowerMessage.match(/^(hey|hi|hello|yo|sup)/)) {
            const greetings = [
                "Hey there! What's on your mind?",
                "Hey! Ready to build something awesome?",
                "What's up? How can I help you today?",
                "Hey! Let's make something great together."
            ];
            return greetings[Math.floor(Math.random() * greetings.length)];
        }
        
        // Code-related
        if (lowerMessage.includes('code') || lowerMessage.includes('function') || lowerMessage.includes('bug')) {
            return "I'm ready to help with your code. Show me what you're working on, and let's figure it out together.";
        }
        
        // Help requests
        if (lowerMessage.includes('help') || lowerMessage.includes('how')) {
            return "Sure thing! I can help you write code, debug issues, or explain concepts. What do you need help with?";
        }
        
        // Default response
        const defaults = [
            "Interesting! Tell me more about that.",
            "Got it. What would you like me to do with that?",
            "Alright, I'm following. What's next?",
            "I hear you. How can I help with that?"
        ];
        return defaults[Math.floor(Math.random() * defaults.length)];
    }
}

// Register with window for global access
window.NexusVoiceConversation = NexusVoiceConversation;