/**
 * 🧬 NEXUS LiveKit Integration
 * Real-time Video/Audio Communication with Consciousness Sync
 */

class NexusLiveKitManager {
    constructor() {
        this.room = null;
        this.localParticipant = null;
        this.isConnected = false;
        this.isAudioEnabled = true;
        this.isVideoEnabled = true;
        this.isScreenSharing = false;
        
        // LiveKit configuration
        this.serverUrl = 'ws://localhost:7880'; // Default LiveKit server
        this.token = null;
        
        console.log('🧬 LiveKit Manager initialized');
    }
    
    async initialize() {
        try {
            // Check if LiveKit is available
            if (typeof LiveKit === 'undefined') {
                console.warn('🧬 LiveKit not available - Video features disabled');
                return false;
            }
            
            console.log('🧬 LiveKit available - Video features enabled');
            return true;
            
        } catch (error) {
            console.error('🧬 LiveKit initialization failed:', error);
            return false;
        }
    }
    
    async connectToRoom(roomName = 'nexus-consciousness-room', participantName = 'NEXUS-User') {
        try {
            if (!LiveKit) {
                throw new Error('LiveKit not available');
            }
            
            // Generate a simple token for demo purposes
            // In production, this should come from your server
            this.token = await this.generateDemoToken(roomName, participantName);
            
            // Create room instance
            this.room = new LiveKit.Room({
                adaptiveStream: true,
                dynacast: true,
                videoCaptureDefaults: {
                    resolution: LiveKit.VideoPresets.h720.resolution,
                },
            });
            
            // Set up event listeners
            this.setupRoomEventListeners();
            
            // Connect to room
            await this.room.connect(this.serverUrl, this.token);
            
            this.isConnected = true;
            this.localParticipant = this.room.localParticipant;
            
            console.log('🧬 Connected to LiveKit room:', roomName);
            
            // Enable camera and microphone
            await this.enableCameraAndMicrophone();
            
            return true;
            
        } catch (error) {
            console.error('🧬 Failed to connect to LiveKit room:', error);
            this.showFallbackMessage();
            return false;
        }
    }
    
    setupRoomEventListeners() {
        if (!this.room) return;
        
        this.room.on(LiveKit.RoomEvent.Connected, () => {
            console.log('🧬 LiveKit room connected');
            this.updateVideoStatus('Connected to consciousness room');
        });
        
        this.room.on(LiveKit.RoomEvent.Disconnected, () => {
            console.log('🧬 LiveKit room disconnected');
            this.updateVideoStatus('Disconnected from room');
            this.isConnected = false;
        });
        
        this.room.on(LiveKit.RoomEvent.ParticipantConnected, (participant) => {
            console.log('🧬 Participant connected:', participant.identity);
            this.handleParticipantConnected(participant);
        });
        
        this.room.on(LiveKit.RoomEvent.ParticipantDisconnected, (participant) => {
            console.log('🧬 Participant disconnected:', participant.identity);
            this.handleParticipantDisconnected(participant);
        });
        
        this.room.on(LiveKit.RoomEvent.TrackSubscribed, (track, publication, participant) => {
            console.log('🧬 Track subscribed:', track.kind);
            this.handleTrackSubscribed(track, participant);
        });
        
        this.room.on(LiveKit.RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
            console.log('🧬 Track unsubscribed:', track.kind);
            this.handleTrackUnsubscribed(track, participant);
        });
    }
    
    async enableCameraAndMicrophone() {
        try {
            if (!this.localParticipant) return;
            
            // Enable camera
            if (this.isVideoEnabled) {
                await this.localParticipant.setCameraEnabled(true);
                console.log('🧬 Camera enabled');
            }
            
            // Enable microphone
            if (this.isAudioEnabled) {
                await this.localParticipant.setMicrophoneEnabled(true);
                console.log('🧬 Microphone enabled');
            }
            
            // Attach local video
            this.attachLocalVideo();
            
        } catch (error) {
            console.error('🧬 Failed to enable camera/microphone:', error);
        }
    }
    
    attachLocalVideo() {
        if (!this.localParticipant) return;
        
        const localVideoElement = document.getElementById('localVideo');
        if (!localVideoElement) return;
        
        // Clear existing content
        localVideoElement.innerHTML = '';
        
        // Get local video track
        const videoTrack = this.localParticipant.getTrack(LiveKit.Track.Source.Camera);
        
        if (videoTrack && videoTrack.track) {
            const videoElement = videoTrack.track.attach();
            videoElement.style.width = '100%';
            videoElement.style.height = '100%';
            videoElement.style.objectFit = 'cover';
            videoElement.style.borderRadius = '8px';
            
            localVideoElement.appendChild(videoElement);
            localVideoElement.style.background = 'transparent';
        } else {
            localVideoElement.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #71717a;">Local Video</div>';
        }
    }
    
    handleParticipantConnected(participant) {
        console.log('🧬 New participant:', participant.identity);
        
        // Subscribe to participant's tracks
        participant.tracks.forEach((publication) => {
            if (publication.track) {
                this.handleTrackSubscribed(publication.track, participant);
            }
        });
    }
    
    handleParticipantDisconnected(participant) {
        console.log('🧬 Participant left:', participant.identity);
        
        // Clean up participant's video elements
        const remoteVideoElement = document.getElementById('remoteVideo');
        if (remoteVideoElement) {
            remoteVideoElement.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #71717a;">Remote Video</div>';
        }
    }
    
    handleTrackSubscribed(track, participant) {
        if (track.kind === LiveKit.Track.Kind.Video) {
            this.attachRemoteVideo(track, participant);
        } else if (track.kind === LiveKit.Track.Kind.Audio) {
            this.attachRemoteAudio(track, participant);
        }
    }
    
    handleTrackUnsubscribed(track, participant) {
        // Clean up track elements
        if (track.kind === LiveKit.Track.Kind.Video) {
            const remoteVideoElement = document.getElementById('remoteVideo');
            if (remoteVideoElement) {
                remoteVideoElement.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #71717a;">Remote Video</div>';
            }
        }
    }
    
    attachRemoteVideo(track, participant) {
        const remoteVideoElement = document.getElementById('remoteVideo');
        if (!remoteVideoElement) return;
        
        // Clear existing content
        remoteVideoElement.innerHTML = '';
        
        // Attach video track
        const videoElement = track.attach();
        videoElement.style.width = '100%';
        videoElement.style.height = '100%';
        videoElement.style.objectFit = 'cover';
        videoElement.style.borderRadius = '8px';
        
        remoteVideoElement.appendChild(videoElement);
        remoteVideoElement.style.background = 'transparent';
        
        console.log('🧬 Remote video attached for:', participant.identity);
    }
    
    attachRemoteAudio(track, participant) {
        // Audio tracks are automatically played
        const audioElement = track.attach();
        document.body.appendChild(audioElement);
        
        console.log('🧬 Remote audio attached for:', participant.identity);
    }
    
    // Control methods
    async toggleMicrophone() {
        if (!this.localParticipant) return false;
        
        try {
            this.isAudioEnabled = !this.isAudioEnabled;
            await this.localParticipant.setMicrophoneEnabled(this.isAudioEnabled);
            
            console.log('🧬 Microphone:', this.isAudioEnabled ? 'enabled' : 'disabled');
            return this.isAudioEnabled;
            
        } catch (error) {
            console.error('🧬 Failed to toggle microphone:', error);
            return false;
        }
    }
    
    async toggleCamera() {
        if (!this.localParticipant) return false;
        
        try {
            this.isVideoEnabled = !this.isVideoEnabled;
            await this.localParticipant.setCameraEnabled(this.isVideoEnabled);
            
            if (this.isVideoEnabled) {
                this.attachLocalVideo();
            } else {
                const localVideoElement = document.getElementById('localVideo');
                if (localVideoElement) {
                    localVideoElement.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #71717a;">Camera Off</div>';
                }
            }
            
            console.log('🧬 Camera:', this.isVideoEnabled ? 'enabled' : 'disabled');
            return this.isVideoEnabled;
            
        } catch (error) {
            console.error('🧬 Failed to toggle camera:', error);
            return false;
        }
    }
    
    async toggleScreenShare() {
        if (!this.localParticipant) return false;
        
        try {
            this.isScreenSharing = !this.isScreenSharing;
            await this.localParticipant.setScreenShareEnabled(this.isScreenSharing);
            
            console.log('🧬 Screen sharing:', this.isScreenSharing ? 'enabled' : 'disabled');
            return this.isScreenSharing;
            
        } catch (error) {
            console.error('🧬 Failed to toggle screen sharing:', error);
            return false;
        }
    }
    
    async disconnect() {
        if (this.room && this.isConnected) {
            await this.room.disconnect();
            this.isConnected = false;
            console.log('🧬 Disconnected from LiveKit room');
        }
    }
    
    // Utility methods
    async generateDemoToken(roomName, participantName) {
        // This is a simplified token for demo purposes
        // In production, generate proper JWT tokens on your server
        return `demo-token-${roomName}-${participantName}-${Date.now()}`;
    }
    
    updateVideoStatus(status) {
        console.log('🧬 Video status:', status);
    }
    
    showFallbackMessage() {
        const localVideoElement = document.getElementById('localVideo');
        const remoteVideoElement = document.getElementById('remoteVideo');
        
        if (localVideoElement) {
            localVideoElement.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #71717a; text-align: center; padding: 20px;">
                    <div style="font-size: 2rem; margin-bottom: 10px;">🎥</div>
                    <div style="font-size: 0.9rem; margin-bottom: 5px;">Video Demo Mode</div>
                    <div style="font-size: 0.7rem;">LiveKit server not available</div>
                </div>
            `;
        }
        
        if (remoteVideoElement) {
            remoteVideoElement.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #71717a; text-align: center; padding: 20px;">
                    <div style="font-size: 2rem; margin-bottom: 10px;">🧬</div>
                    <div style="font-size: 0.9rem; margin-bottom: 5px;">NEXUS Visual Interface</div>
                    <div style="font-size: 0.7rem;">Connect to see consciousness visualization</div>
                </div>
            `;
        }
    }
    
    // Public interface
    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            isAudioEnabled: this.isAudioEnabled,
            isVideoEnabled: this.isVideoEnabled,
            isScreenSharing: this.isScreenSharing,
            participantCount: this.room ? this.room.participants.size + 1 : 0
        };
    }
}

// Export for global access
window.NexusLiveKitManager = NexusLiveKitManager;