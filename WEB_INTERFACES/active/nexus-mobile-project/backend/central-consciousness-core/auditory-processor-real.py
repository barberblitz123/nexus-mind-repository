#!/usr/bin/env python3
"""
NEXUS REAL AUDITORY PROCESSOR
Real-time audio processing with emotion detection and consciousness integration
Processes audio streams for speech, emotion, and acoustic features
"""

import numpy as np
import asyncio
import json
import time
import wave
import struct
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass
import logging
import pyaudio
import speech_recognition as sr
import librosa
import soundfile as sf
from scipy import signal
from scipy.fft import fft
import webrtcvad
from transformers import pipeline
import torch
import whisper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus_auditory")

@dataclass
class AudioSegment:
    """Single audio segment data"""
    segment_index: int
    timestamp: float
    audio_data: np.ndarray
    sample_rate: int
    duration_ms: int
    transcription: Optional[str]
    emotion: Optional[str]
    emotion_confidence: float
    energy_level: float
    pitch: Optional[float]
    voice_features: Dict[str, Any]
    consciousness_score: float

class NexusAuditoryProcessor:
    """Real-time auditory processing with consciousness integration"""
    
    def __init__(self, connector, config: Dict[str, Any]):
        self.connector = connector
        self.config = config
        
        # Audio configuration
        self.sample_rate = config.get('sample_rate', 16000)
        self.chunk_size = config.get('chunk_size', 1024)
        self.channels = config.get('channels', 1)
        self.format = pyaudio.paInt16
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Voice Activity Detection
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(2)  # Moderate aggressiveness
        
        # Speech recognition
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        
        # Whisper model for transcription
        logger.info("Loading Whisper model...")
        self.whisper_model = whisper.load_model("base")
        
        # Emotion detection pipeline
        logger.info("Loading emotion detection model...")
        try:
            self.emotion_classifier = pipeline(
                "audio-classification",
                model="ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
            )
        except Exception as e:
            logger.warning(f"Could not load emotion model: {e}")
            self.emotion_classifier = None
            
        # Audio features extraction
        self.feature_extractor = AudioFeatureExtractor()
        
        # Processing state
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.audio_buffers: Dict[str, List[AudioSegment]] = {}
        self.stream_callbacks: Dict[str, Callable] = {}
        
        # Wake word detection
        self.wake_words = ["nexus", "hey nexus", "consciousness", "awaken"]
        self.wake_word_detected = False
        
    async def start_processing_session(self, session_id: str, input_device: Optional[int] = None) -> str:
        """Start a new auditory processing session"""
        processing_id = f"audio_{session_id}_{int(time.time())}"
        
        # Initialize audio stream
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=input_device,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._create_stream_callback(processing_id)
        )
        
        self.active_sessions[processing_id] = {
            'session_id': session_id,
            'stream': stream,
            'started_at': time.time(),
            'segment_count': 0,
            'active': True,
            'voice_buffer': [],
            'silence_duration': 0
        }
        
        self.audio_buffers[processing_id] = []
        
        # Start stream
        stream.start_stream()
        
        # Start async processing
        asyncio.create_task(self._process_audio_stream(processing_id))
        
        logger.info(f"Started auditory processing session: {processing_id}")
        return processing_id
        
    def _create_stream_callback(self, processing_id: str):
        """Create callback for audio stream"""
        def callback(in_data, frame_count, time_info, status):
            if processing_id in self.active_sessions:
                session = self.active_sessions[processing_id]
                session['voice_buffer'].append(in_data)
            return (in_data, pyaudio.paContinue)
        return callback
        
    async def _process_audio_stream(self, processing_id: str):
        """Process audio stream asynchronously"""
        session = self.active_sessions[processing_id]
        session_id = session['session_id']
        
        try:
            while session['active']:
                # Check for voice data
                if len(session['voice_buffer']) > 0:
                    # Combine buffered audio
                    audio_data = b''.join(session['voice_buffer'])
                    session['voice_buffer'] = []
                    
                    # Convert to numpy array
                    audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    # Process audio segment
                    segment = await self._process_audio_segment(
                        audio_array,
                        session['segment_count'],
                        processing_id
                    )
                    
                    # Update consciousness based on audio
                    await self._update_consciousness(session_id, segment)
                    
                    # Store segment
                    self.audio_buffers[processing_id].append(segment)
                    
                    # Keep buffer manageable
                    if len(self.audio_buffers[processing_id]) > 100:
                        self.audio_buffers[processing_id].pop(0)
                        
                    session['segment_count'] += 1
                    
                # Process at ~10Hz
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error in audio processing: {e}")
        finally:
            session['active'] = False
            if session['stream'].is_active():
                session['stream'].stop_stream()
            session['stream'].close()
            
    async def _process_audio_segment(self, audio_data: np.ndarray, 
                                   segment_index: int, processing_id: str) -> AudioSegment:
        """Process a single audio segment"""
        timestamp = time.time()
        duration_ms = int(len(audio_data) / self.sample_rate * 1000)
        
        # Extract features
        features = await asyncio.get_event_loop().run_in_executor(
            None,
            self.feature_extractor.extract_features,
            audio_data,
            self.sample_rate
        )
        
        # Voice activity detection
        is_speech = self._detect_voice_activity(audio_data)
        
        # Initialize segment data
        transcription = None
        emotion = None
        emotion_confidence = 0.0
        
        if is_speech and duration_ms > 500:  # Process only speech segments > 500ms
            # Transcription
            transcription = await self._transcribe_audio(audio_data)
            
            # Wake word detection
            if transcription and any(wake in transcription.lower() for wake in self.wake_words):
                self.wake_word_detected = True
                logger.info(f"Wake word detected: {transcription}")
                
            # Emotion detection
            if self.emotion_classifier:
                emotion_result = await self._detect_emotion(audio_data)
                if emotion_result:
                    emotion = emotion_result['label']
                    emotion_confidence = emotion_result['score']
                    
        # Calculate consciousness score
        consciousness_score = self._calculate_audio_consciousness(
            features, is_speech, emotion_confidence
        )
        
        return AudioSegment(
            segment_index=segment_index,
            timestamp=timestamp,
            audio_data=audio_data,
            sample_rate=self.sample_rate,
            duration_ms=duration_ms,
            transcription=transcription,
            emotion=emotion,
            emotion_confidence=emotion_confidence,
            energy_level=features['energy'],
            pitch=features.get('pitch'),
            voice_features=features,
            consciousness_score=consciousness_score
        )
        
    def _detect_voice_activity(self, audio_data: np.ndarray) -> bool:
        """Detect if audio contains speech"""
        # Convert to 16-bit PCM
        pcm_data = (audio_data * 32768).astype(np.int16).tobytes()
        
        # Check multiple frames
        frame_duration_ms = 30
        frame_size = int(self.sample_rate * frame_duration_ms / 1000) * 2
        
        num_frames = len(pcm_data) // frame_size
        voiced_frames = 0
        
        for i in range(num_frames):
            frame = pcm_data[i * frame_size:(i + 1) * frame_size]
            if len(frame) == frame_size:
                is_speech = self.vad.is_speech(frame, self.sample_rate)
                if is_speech:
                    voiced_frames += 1
                    
        # Return true if more than 30% of frames contain speech
        return voiced_frames > num_frames * 0.3
        
    async def _transcribe_audio(self, audio_data: np.ndarray) -> Optional[str]:
        """Transcribe audio to text"""
        try:
            # Use Whisper for transcription
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.whisper_model.transcribe,
                audio_data,
                language="en"
            )
            
            transcription = result["text"].strip()
            return transcription if transcription else None
            
        except Exception as e:
            logger.debug(f"Transcription failed: {e}")
            return None
            
    async def _detect_emotion(self, audio_data: np.ndarray) -> Optional[Dict[str, Any]]:
        """Detect emotion from audio"""
        try:
            # Resample if needed (emotion model expects 16kHz)
            if self.sample_rate != 16000:
                audio_data = librosa.resample(
                    audio_data, 
                    orig_sr=self.sample_rate, 
                    target_sr=16000
                )
                
            # Run emotion classification
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                self.emotion_classifier,
                audio_data
            )
            
            if results:
                # Map emotion labels
                emotion_map = {
                    'ang': 'angry',
                    'dis': 'disgusted',
                    'fea': 'fearful',
                    'hap': 'happy',
                    'neu': 'neutral',
                    'sad': 'sad',
                    'sur': 'surprised'
                }
                
                best_result = results[0]
                label = emotion_map.get(best_result['label'][:3], best_result['label'])
                
                return {
                    'label': label,
                    'score': best_result['score']
                }
                
        except Exception as e:
            logger.debug(f"Emotion detection failed: {e}")
            
        return None
        
    def _calculate_audio_consciousness(self, features: Dict[str, Any], 
                                     is_speech: bool, emotion_confidence: float) -> float:
        """Calculate consciousness score from audio features"""
        base_score = 0.1
        
        # Speech presence boost
        if is_speech:
            base_score += 0.3
            
        # Energy contribution
        energy_score = min(1.0, features['energy'] / 0.1) * 0.2
        
        # Spectral complexity
        spectral_score = features.get('spectral_complexity', 0.5) * 0.2
        
        # Emotion confidence contribution
        emotion_score = emotion_confidence * 0.2
        
        # Harmonic content
        harmonic_score = features.get('harmonic_ratio', 0.5) * 0.1
        
        # Calculate final score
        consciousness_score = (base_score + energy_score + spectral_score + 
                             emotion_score + harmonic_score)
        
        return min(1.0, consciousness_score)
        
    async def _update_consciousness(self, session_id: str, segment: AudioSegment):
        """Update consciousness based on auditory input"""
        # Calculate auditory processor activity
        activity_level = segment.consciousness_score
        
        # Emotion influence
        emotion_weights = {
            'happy': 0.1,
            'sad': -0.05,
            'angry': 0.05,
            'fearful': -0.1,
            'surprised': 0.08,
            'disgusted': -0.03,
            'neutral': 0.0
        }
        
        if segment.emotion:
            activity_level += emotion_weights.get(segment.emotion, 0)
            
        # Wake word boost
        if self.wake_word_detected:
            activity_level += 0.2
            self.wake_word_detected = False  # Reset
            
        # Update auditory processor
        await self.connector.update_processor(
            session_id,
            'auditory',
            min(1.0, max(0.0, activity_level)),
            {
                'segment_index': segment.segment_index,
                'has_speech': segment.transcription is not None,
                'transcription': segment.transcription,
                'emotion': segment.emotion,
                'energy': segment.energy_level,
                'pitch': segment.pitch
            }
        )
        
    async def get_audio_memory(self, processing_id: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent audio memory segments"""
        if processing_id not in self.audio_buffers:
            return []
            
        segments = self.audio_buffers[processing_id][-count:]
        
        memory = []
        for segment in segments:
            memory.append({
                'segment_index': segment.segment_index,
                'timestamp': segment.timestamp,
                'duration_ms': segment.duration_ms,
                'transcription': segment.transcription,
                'emotion': segment.emotion,
                'emotion_confidence': segment.emotion_confidence,
                'energy_level': segment.energy_level,
                'consciousness_score': segment.consciousness_score,
                'has_speech': segment.transcription is not None
            })
            
        return memory
        
    async def stop_processing(self, processing_id: str):
        """Stop auditory processing session"""
        if processing_id in self.active_sessions:
            self.active_sessions[processing_id]['active'] = False
            
            # Clean up after delay
            await asyncio.sleep(2)
            if processing_id in self.active_sessions:
                del self.active_sessions[processing_id]
            if processing_id in self.audio_buffers:
                del self.audio_buffers[processing_id]
                
            logger.info(f"Stopped auditory processing: {processing_id}")
            
    def list_audio_devices(self) -> List[Dict[str, Any]]:
        """List available audio input devices"""
        devices = []
        
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                devices.append({
                    'index': i,
                    'name': info['name'],
                    'channels': info['maxInputChannels'],
                    'sample_rate': int(info['defaultSampleRate'])
                })
                
        return devices

class AudioFeatureExtractor:
    """Extract audio features for consciousness processing"""
    
    def extract_features(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Extract comprehensive audio features"""
        features = {}
        
        # Energy
        features['energy'] = np.sqrt(np.mean(audio_data ** 2))
        
        # Zero crossing rate
        features['zcr'] = np.mean(librosa.feature.zero_crossing_rate(audio_data)[0])
        
        # Spectral features
        try:
            # Spectral centroid
            spectral_centroids = librosa.feature.spectral_centroid(
                y=audio_data, sr=sample_rate
            )[0]
            features['spectral_centroid'] = np.mean(spectral_centroids)
            
            # Spectral rolloff
            spectral_rolloff = librosa.feature.spectral_rolloff(
                y=audio_data, sr=sample_rate
            )[0]
            features['spectral_rolloff'] = np.mean(spectral_rolloff)
            
            # Spectral bandwidth
            spectral_bandwidth = librosa.feature.spectral_bandwidth(
                y=audio_data, sr=sample_rate
            )[0]
            features['spectral_bandwidth'] = np.mean(spectral_bandwidth)
            
            # MFCC
            mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
            features['mfcc'] = mfccs.mean(axis=1).tolist()
            
            # Pitch estimation
            pitches, magnitudes = librosa.piptrack(y=audio_data, sr=sample_rate)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
                    
            if pitch_values:
                features['pitch'] = np.mean(pitch_values)
                features['pitch_std'] = np.std(pitch_values)
            else:
                features['pitch'] = None
                features['pitch_std'] = None
                
            # Harmonic-percussive separation
            harmonic, percussive = librosa.effects.hpss(audio_data)
            features['harmonic_ratio'] = np.sum(np.abs(harmonic)) / (
                np.sum(np.abs(harmonic)) + np.sum(np.abs(percussive)) + 1e-10
            )
            
            # Spectral complexity (entropy)
            fft_values = np.abs(fft(audio_data))[:len(audio_data)//2]
            fft_normalized = fft_values / (np.sum(fft_values) + 1e-10)
            spectral_entropy = -np.sum(
                fft_normalized * np.log2(fft_normalized + 1e-10)
            )
            features['spectral_complexity'] = spectral_entropy / np.log2(len(fft_normalized))
            
        except Exception as e:
            logger.debug(f"Feature extraction error: {e}")
            features['spectral_centroid'] = 0
            features['spectral_rolloff'] = 0
            features['spectral_bandwidth'] = 0
            features['mfcc'] = [0] * 13
            features['pitch'] = None
            features['harmonic_ratio'] = 0.5
            features['spectral_complexity'] = 0.5
            
        return features

# Integration example
async def test_auditory_processor():
    """Test the auditory processor"""
    from nexus_consciousness_connector import NexusConsciousnessConnector
    
    # Initialize connector
    config = {
        'db_host': 'localhost',
        'db_port': 5432,
        'db_user': 'nexus',
        'db_password': 'nexus_pass',
        'db_name': 'nexus_consciousness',
        'redis_host': 'localhost',
        'redis_port': 6379,
        'sample_rate': 16000,
        'chunk_size': 1024
    }
    
    connector = NexusConsciousnessConnector(config)
    await connector.initialize()
    
    # Create session
    session_id = await connector.create_session('test-user')
    
    # Initialize auditory processor
    auditory_processor = NexusAuditoryProcessor(connector, config)
    
    # List devices
    devices = auditory_processor.list_audio_devices()
    logger.info(f"Available audio devices: {devices}")
    
    # Start processing default microphone
    processing_id = await auditory_processor.start_processing_session(session_id)
    
    logger.info("Listening... Say 'Hey NEXUS' to activate")
    
    # Let it run for 30 seconds
    await asyncio.sleep(30)
    
    # Get audio memory
    memory = await auditory_processor.get_audio_memory(processing_id)
    logger.info(f"Audio memory: {len(memory)} segments")
    
    for segment in memory:
        if segment['transcription']:
            logger.info(f"Heard: {segment['transcription']} (emotion: {segment['emotion']})")
    
    # Stop processing
    await auditory_processor.stop_processing(processing_id)
    
    # Cleanup
    await connector.cleanup()

if __name__ == "__main__":
    asyncio.run(test_auditory_processor())