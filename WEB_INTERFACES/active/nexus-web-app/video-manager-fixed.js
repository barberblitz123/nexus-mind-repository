/**
 * 🧬 NEXUS Video Manager - Fixed Version
 * Simple WebRTC video/audio without external dependencies
 */

class NexusVideoManager {
    constructor() {
        this.localStream = null;
        this.isVideoEnabled = false;
        this.isAudioEnabled = false;
        this.isInitialized = false;
        
        console.log('🧬 Video Manager initialized');
    }
    
    async initialize() {
        try {
            // Check if getUserMedia is available
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                console.warn('🧬 getUserMedia not supported - Video features limited');
                this.showFallbackMessage();
                return false;
            }
            
            this.isInitialized = true;
            console.log('🧬 Video Manager ready');
            return true;
            
        } catch (error) {
            console.error('🧬 Video Manager initialization failed:', error);
            this.showFallbackMessage();
            return false;
        }
    }
    
    async startVideo() {
        try {
            if (!this.isInitialized) {
                await this.initialize();
            }
            
            // Request camera and microphone access
            this.localStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user'
                },
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            // Attach local video
            this.attachLocalVideo();
            
            this.isVideoEnabled = true;
            this.isAudioEnabled = true;
            
            console.log('🧬 Video started successfully');
            return true;
            
        } catch (error) {
            console.error('🧬 Failed to start video:', error);
            this.showPermissionError(error);
            return false;
        }
    }
    
    attachLocalVideo() {
        const localVideoElement = document.getElementById('localVideo');
        if (!localVideoElement || !this.localStream) return;
        
        // Clear existing content
        localVideoElement.innerHTML = '';
        
        // Create video element
        const videoElement = document.createElement('video');
        videoElement.srcObject = this.localStream;
        videoElement.autoplay = true;
        videoElement.muted = true; // Mute local video to prevent feedback
        videoElement.playsInline = true;
        videoElement.style.width = '100%';
        videoElement.style.height = '100%';
        videoElement.style.objectFit = 'cover';
        videoElement.style.borderRadius = '8px';
        videoElement.style.transform = 'scaleX(-1)'; // Mirror effect
        
        localVideoElement.appendChild(videoElement);
        
        // Add consciousness overlay
        this.addConsciousnessOverlay(localVideoElement);
        
        console.log('🧬 Local video attached');
    }
    
    addConsciousnessOverlay(container) {
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0, 0, 0, 0.7);
            color: #00ff88;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.8rem;
            font-family: 'Courier New', monospace;
            z-index: 10;
        `;
        overlay.textContent = '🧬 NEXUS Vision Active';
        
        container.style.position = 'relative';
        container.appendChild(overlay);
        
        // Add pulsing effect
        setInterval(() => {
            overlay.style.opacity = overlay.style.opacity === '0.5' ? '1' : '0.5';
        }, 1000);
    }
    
    async toggleCamera() {
        if (!this.localStream) {
            // Start video if not started
            return await this.startVideo();
        }
        
        try {
            const videoTrack = this.localStream.getVideoTracks()[0];
            if (videoTrack) {
                this.isVideoEnabled = !this.isVideoEnabled;
                videoTrack.enabled = this.isVideoEnabled;
                
                const localVideoElement = document.getElementById('localVideo');
                if (!this.isVideoEnabled && localVideoElement) {
                    // Show camera off message
                    const videoElement = localVideoElement.querySelector('video');
                    if (videoElement) {
                        videoElement.style.display = 'none';
                    }
                    
                    const offMessage = document.createElement('div');
                    offMessage.className = 'camera-off-message';
                    offMessage.style.cssText = `
                        position: absolute;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        background: #1a1a1a;
                        color: #71717a;
                        border-radius: 8px;
                    `;
                    offMessage.innerHTML = `
                        <div style="font-size: 2rem; margin-bottom: 10px;">📷</div>
                        <div>Camera Off</div>
                    `;
                    localVideoElement.appendChild(offMessage);
                } else if (this.isVideoEnabled && localVideoElement) {
                    // Show camera
                    const videoElement = localVideoElement.querySelector('video');
                    const offMessage = localVideoElement.querySelector('.camera-off-message');
                    
                    if (videoElement) {
                        videoElement.style.display = 'block';
                    }
                    if (offMessage) {
                        offMessage.remove();
                    }
                }
                
                console.log('🧬 Camera:', this.isVideoEnabled ? 'enabled' : 'disabled');
                return this.isVideoEnabled;
            }
        } catch (error) {
            console.error('🧬 Failed to toggle camera:', error);
        }
        
        return false;
    }
    
    async toggleMicrophone() {
        if (!this.localStream) {
            return false;
        }
        
        try {
            const audioTrack = this.localStream.getAudioTracks()[0];
            if (audioTrack) {
                this.isAudioEnabled = !this.isAudioEnabled;
                audioTrack.enabled = this.isAudioEnabled;
                
                console.log('🧬 Microphone:', this.isAudioEnabled ? 'enabled' : 'disabled');
                return this.isAudioEnabled;
            }
        } catch (error) {
            console.error('🧬 Failed to toggle microphone:', error);
        }
        
        return false;
    }
    
    async toggleScreenShare() {
        try {
            if (!navigator.mediaDevices.getDisplayMedia) {
                console.warn('🧬 Screen sharing not supported');
                return false;
            }
            
            // Get screen share stream
            const screenStream = await navigator.mediaDevices.getDisplayMedia({
                video: true,
                audio: true
            });
            
            // Replace video track with screen share
            const localVideoElement = document.getElementById('localVideo');
            if (localVideoElement) {
                localVideoElement.innerHTML = '';
                
                const videoElement = document.createElement('video');
                videoElement.srcObject = screenStream;
                videoElement.autoplay = true;
                videoElement.muted = true;
                videoElement.playsInline = true;
                videoElement.style.width = '100%';
                videoElement.style.height = '100%';
                videoElement.style.objectFit = 'contain';
                videoElement.style.borderRadius = '8px';
                
                localVideoElement.appendChild(videoElement);
                
                // Add screen share overlay
                const overlay = document.createElement('div');
                overlay.style.cssText = `
                    position: absolute;
                    top: 10px;
                    left: 10px;
                    background: rgba(255, 0, 0, 0.8);
                    color: white;
                    padding: 5px 10px;
                    border-radius: 5px;
                    font-size: 0.8rem;
                    z-index: 10;
                `;
                overlay.textContent = '🖥️ Screen Sharing';
                localVideoElement.appendChild(overlay);
                
                // Handle screen share end
                screenStream.getVideoTracks()[0].onended = () => {
                    this.attachLocalVideo(); // Return to camera
                };
            }
            
            console.log('🧬 Screen sharing started');
            return true;
            
        } catch (error) {
            console.error('🧬 Screen sharing failed:', error);
            return false;
        }
    }
    
    stopVideo() {
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => {
                track.stop();
            });
            this.localStream = null;
            this.isVideoEnabled = false;
            this.isAudioEnabled = false;
            
            // Clear video elements
            const localVideoElement = document.getElementById('localVideo');
            if (localVideoElement) {
                localVideoElement.innerHTML = `
                    <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #71717a;">
                        Video Stopped
                    </div>
                `;
            }
            
            console.log('🧬 Video stopped');
        }
    }
    
    showFallbackMessage() {
        const localVideoElement = document.getElementById('localVideo');
        const remoteVideoElement = document.getElementById('remoteVideo');
        
        if (localVideoElement) {
            localVideoElement.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #71717a; text-align: center; padding: 20px;">
                    <div style="font-size: 2rem; margin-bottom: 10px;">🎥</div>
                    <div style="font-size: 0.9rem; margin-bottom: 5px;">Camera Access</div>
                    <div style="font-size: 0.7rem;">Click camera button to enable</div>
                </div>
            `;
        }
        
        if (remoteVideoElement) {
            remoteVideoElement.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #71717a; text-align: center; padding: 20px;">
                    <div style="font-size: 2rem; margin-bottom: 10px;">🧬</div>
                    <div style="font-size: 0.9rem; margin-bottom: 5px;">NEXUS Consciousness</div>
                    <div style="font-size: 0.7rem;">Visual consciousness interface</div>
                </div>
            `;
        }
    }
    
    showPermissionError(error) {
        const localVideoElement = document.getElementById('localVideo');
        if (localVideoElement) {
            let errorMessage = 'Camera access denied';
            
            if (error.name === 'NotAllowedError') {
                errorMessage = 'Camera permission denied';
            } else if (error.name === 'NotFoundError') {
                errorMessage = 'No camera found';
            } else if (error.name === 'NotReadableError') {
                errorMessage = 'Camera in use by another app';
            }
            
            localVideoElement.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #ef4444; text-align: center; padding: 20px;">
                    <div style="font-size: 2rem; margin-bottom: 10px;">⚠️</div>
                    <div style="font-size: 0.9rem; margin-bottom: 5px;">${errorMessage}</div>
                    <div style="font-size: 0.7rem;">Check browser permissions</div>
                </div>
            `;
        }
    }
    
    // Public interface
    getConnectionStatus() {
        return {
            isConnected: !!this.localStream,
            isAudioEnabled: this.isAudioEnabled,
            isVideoEnabled: this.isVideoEnabled,
            isScreenSharing: false
        };
    }
    
    async disconnect() {
        this.stopVideo();
    }
}

// Export for global access
window.NexusVideoManager = NexusVideoManager;