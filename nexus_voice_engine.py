#!/usr/bin/env python3
"""
NEXUS Voice Engine - Core voice processing with real-time capabilities
"""

import asyncio
import numpy as np
import torch
import whisper
import webrtcvad
import pyaudio
import json
import time
from typing import Optional, Callable, Dict, Any, List, Tuple
from dataclasses import dataclass
from collections import deque
import threading
import queue
import logging
from concurrent.futures import ThreadPoolExecutor
import librosa
import soundfile as sf
from scipy import signal
import noisereduce as nr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    """Audio configuration settings"""
    sample_rate: int = 16000
    chunk_size: int = 480  # 30ms at 16kHz
    channels: int = 1
    format: int = pyaudio.paInt16
    vad_mode: int = 3  # 0-3, 3 being most aggressive
    silence_threshold: float = 0.01
    min_speech_duration: float = 0.5
    max_silence_duration: float = 1.0
    wake_word: str = "hey nexus"
    wake_word_threshold: float = 0.7


@dataclass
class VoiceSegment:
    """Represents a voice segment"""
    audio: np.ndarray
    start_time: float
    end_time: float
    speaker_id: Optional[int] = None
    language: Optional[str] = None
    confidence: float = 0.0


class WakeWordDetector:
    """Custom wake word detection using Whisper"""
    
    def __init__(self, wake_word: str, model_size: str = "tiny"):
        self.wake_word = wake_word.lower()
        self.model = whisper.load_model(model_size)
        self.buffer = deque(maxlen=int(16000 * 2))  # 2 seconds buffer
        
    def detect(self, audio_chunk: np.ndarray) -> Tuple[bool, float]:
        """Detect wake word in audio chunk"""
        self.buffer.extend(audio_chunk)
        
        if len(self.buffer) < 16000:  # Need at least 1 second
            return False, 0.0
            
        # Convert buffer to numpy array
        audio = np.array(self.buffer, dtype=np.float32)
        
        # Transcribe with Whisper
        result = self.model.transcribe(
            audio,
            language='en',
            fp16=torch.cuda.is_available()
        )
        
        text = result['text'].lower().strip()
        
        # Check for wake word
        if self.wake_word in text:
            # Calculate confidence based on position and clarity
            confidence = result['segments'][0]['confidence'] if result['segments'] else 0.5
            return True, confidence
            
        return False, 0.0


class VoiceActivityDetector:
    """Enhanced VAD with noise robustness"""
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.vad = webrtcvad.Vad(config.vad_mode)
        self.speech_buffer = deque(maxlen=int(config.sample_rate * 2))
        self.is_speaking = False
        self.silence_start = None
        
    def process_frame(self, frame: bytes) -> Tuple[bool, bool]:
        """
        Process audio frame and detect speech
        Returns: (is_speech, speech_complete)
        """
        is_speech = self.vad.is_speech(frame, self.config.sample_rate)
        
        current_time = time.time()
        speech_complete = False
        
        if is_speech:
            self.is_speaking = True
            self.silence_start = None
        else:
            if self.is_speaking and self.silence_start is None:
                self.silence_start = current_time
            elif self.is_speaking and self.silence_start:
                silence_duration = current_time - self.silence_start
                if silence_duration > self.config.max_silence_duration:
                    self.is_speaking = False
                    speech_complete = True
                    
        return is_speech, speech_complete


class AudioProcessor:
    """Advanced audio processing with noise cancellation"""
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.noise_profile = None
        self.echo_canceller = EchoCanceller(config)
        
    def process(self, audio: np.ndarray) -> np.ndarray:
        """Apply audio processing pipeline"""
        # Convert to float32
        audio = audio.astype(np.float32) / 32768.0
        
        # Apply automatic gain control
        audio = self.apply_agc(audio)
        
        # Noise reduction
        if self.noise_profile is not None:
            audio = nr.reduce_noise(
                y=audio,
                sr=self.config.sample_rate,
                noise_profile=self.noise_profile
            )
        
        # Echo cancellation
        audio = self.echo_canceller.process(audio)
        
        # Bandpass filter for voice frequencies
        audio = self.bandpass_filter(audio, 80, 8000)
        
        # Convert back to int16
        audio = np.clip(audio * 32768.0, -32768, 32767).astype(np.int16)
        
        return audio
        
    def apply_agc(self, audio: np.ndarray, target_level: float = 0.3) -> np.ndarray:
        """Apply automatic gain control"""
        rms = np.sqrt(np.mean(audio**2))
        if rms > 0:
            gain = target_level / rms
            audio = audio * min(gain, 10.0)  # Limit maximum gain
        return audio
        
    def bandpass_filter(self, audio: np.ndarray, low_freq: int, high_freq: int) -> np.ndarray:
        """Apply bandpass filter for voice frequencies"""
        nyquist = self.config.sample_rate / 2
        low = low_freq / nyquist
        high = high_freq / nyquist
        b, a = signal.butter(4, [low, high], btype='band')
        return signal.filtfilt(b, a, audio)
        
    def update_noise_profile(self, noise_sample: np.ndarray):
        """Update noise profile for better cancellation"""
        self.noise_profile = noise_sample


class EchoCanceller:
    """Simple echo cancellation using adaptive filtering"""
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.reference_buffer = deque(maxlen=int(config.sample_rate * 0.5))
        self.filter_length = 512
        self.step_size = 0.01
        self.weights = np.zeros(self.filter_length)
        
    def process(self, audio: np.ndarray) -> np.ndarray:
        """Apply echo cancellation"""
        # Simple implementation - in production, use more sophisticated algorithms
        return audio


class SpeakerDiarizer:
    """Speaker diarization for multi-speaker scenarios"""
    
    def __init__(self):
        self.speakers = {}
        self.current_speaker = 0
        
    def identify_speaker(self, audio_features: np.ndarray) -> int:
        """Identify speaker from audio features"""
        # Simplified implementation - in production, use neural speaker embeddings
        # This would typically use libraries like pyannote.audio
        return self.current_speaker


class NexusVoiceEngine:
    """Main voice engine orchestrating all components"""
    
    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_running = False
        
        # Initialize components
        self.vad = VoiceActivityDetector(self.config)
        self.processor = AudioProcessor(self.config)
        self.wake_detector = WakeWordDetector(self.config.wake_word)
        self.diarizer = SpeakerDiarizer()
        
        # Initialize Whisper model
        self.whisper_model = whisper.load_model("base")
        
        # Buffers and queues
        self.audio_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.audio_buffer = deque(maxlen=int(self.config.sample_rate * 30))  # 30s buffer
        
        # Threading
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.processing_thread = None
        
        # Callbacks
        self.on_transcription: Optional[Callable] = None
        self.on_wake_word: Optional[Callable] = None
        self.on_speech_start: Optional[Callable] = None
        self.on_speech_end: Optional[Callable] = None
        
        # State
        self.wake_word_active = False
        self.current_segment = None
        self.transcription_language = "en"
        
    def start(self):
        """Start the voice engine"""
        if self.is_running:
            return
            
        self.is_running = True
        
        # Open audio stream
        self.stream = self.audio.open(
            format=self.config.format,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            frames_per_buffer=self.config.chunk_size,
            stream_callback=self._audio_callback
        )
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._processing_loop)
        self.processing_thread.start()
        
        logger.info("Voice engine started")
        
    def stop(self):
        """Stop the voice engine"""
        self.is_running = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            
        if self.processing_thread:
            self.processing_thread.join()
            
        self.audio.terminate()
        self.executor.shutdown()
        
        logger.info("Voice engine stopped")
        
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio stream callback"""
        if status:
            logger.warning(f"Audio callback status: {status}")
            
        self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)
        
    def _processing_loop(self):
        """Main processing loop"""
        speech_frames = []
        speech_start_time = None
        
        while self.is_running:
            try:
                # Get audio data
                audio_data = self.audio_queue.get(timeout=0.1)
                
                # Convert to numpy
                audio_np = np.frombuffer(audio_data, dtype=np.int16)
                
                # Process audio
                processed_audio = self.processor.process(audio_np)
                
                # Add to buffer
                self.audio_buffer.extend(processed_audio)
                
                # Check for wake word if not active
                if not self.wake_word_active:
                    detected, confidence = self.wake_detector.detect(processed_audio)
                    if detected and confidence > self.config.wake_word_threshold:
                        self.wake_word_active = True
                        if self.on_wake_word:
                            self.on_wake_word(confidence)
                        continue
                
                # Skip processing if wake word not active
                if not self.wake_word_active:
                    continue
                
                # Voice activity detection
                is_speech, speech_complete = self.vad.process_frame(audio_data)
                
                if is_speech:
                    if speech_start_time is None:
                        speech_start_time = time.time()
                        if self.on_speech_start:
                            self.on_speech_start()
                    speech_frames.append(processed_audio)
                    
                if speech_complete and speech_frames:
                    # Create voice segment
                    segment_audio = np.concatenate(speech_frames)
                    segment = VoiceSegment(
                        audio=segment_audio,
                        start_time=speech_start_time,
                        end_time=time.time()
                    )
                    
                    # Process segment asynchronously
                    self.executor.submit(self._process_segment, segment)
                    
                    # Reset
                    speech_frames = []
                    speech_start_time = None
                    
                    if self.on_speech_end:
                        self.on_speech_end()
                        
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Processing error: {e}")
                
    def _process_segment(self, segment: VoiceSegment):
        """Process a voice segment"""
        try:
            # Identify speaker
            segment.speaker_id = self.diarizer.identify_speaker(segment.audio)
            
            # Detect language
            segment.language = self._detect_language(segment.audio)
            
            # Transcribe
            result = self.transcribe(segment.audio, language=segment.language)
            
            # Add metadata
            result['segment'] = segment
            result['timestamp'] = time.time()
            
            # Call callback
            if self.on_transcription:
                self.on_transcription(result)
                
            # Add to result queue
            self.result_queue.put(result)
            
        except Exception as e:
            logger.error(f"Segment processing error: {e}")
            
    def _detect_language(self, audio: np.ndarray) -> str:
        """Detect language from audio"""
        # Use Whisper's language detection
        audio_float = audio.astype(np.float32) / 32768.0
        
        # Pad or trim to 30 seconds
        audio_float = whisper.pad_or_trim(audio_float)
        
        # Make log-Mel spectrogram
        mel = whisper.log_mel_spectrogram(audio_float).to(self.whisper_model.device)
        
        # Detect language
        _, probs = self.whisper_model.detect_language(mel)
        
        # Get top language
        lang = max(probs, key=probs.get)
        
        return lang
        
    def transcribe(self, audio: np.ndarray, language: Optional[str] = None) -> Dict[str, Any]:
        """Transcribe audio to text"""
        # Convert to float32
        audio_float = audio.astype(np.float32) / 32768.0
        
        # Transcribe with Whisper
        result = self.whisper_model.transcribe(
            audio_float,
            language=language or self.transcription_language,
            fp16=torch.cuda.is_available(),
            verbose=False
        )
        
        return {
            'text': result['text'],
            'language': result['language'],
            'segments': result['segments'],
            'confidence': np.mean([s.get('confidence', 0.5) for s in result['segments']])
        }
        
    def set_wake_word(self, wake_word: str):
        """Update wake word"""
        self.config.wake_word = wake_word
        self.wake_detector = WakeWordDetector(wake_word)
        
    def reset_wake_word(self):
        """Reset wake word detection"""
        self.wake_word_active = False
        
    def get_audio_devices(self) -> List[Dict[str, Any]]:
        """Get available audio devices"""
        devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            devices.append({
                'index': i,
                'name': info['name'],
                'channels': info['maxInputChannels'],
                'sample_rate': info['defaultSampleRate']
            })
        return devices
        
    def calibrate_noise(self, duration: float = 2.0):
        """Calibrate noise profile"""
        logger.info(f"Calibrating noise for {duration} seconds...")
        
        noise_samples = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                audio_data = self.audio_queue.get(timeout=0.1)
                audio_np = np.frombuffer(audio_data, dtype=np.int16)
                noise_samples.append(audio_np)
            except queue.Empty:
                continue
                
        if noise_samples:
            noise_profile = np.concatenate(noise_samples)
            self.processor.update_noise_profile(noise_profile)
            logger.info("Noise calibration complete")
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get engine metrics"""
        return {
            'is_running': self.is_running,
            'wake_word_active': self.wake_word_active,
            'audio_queue_size': self.audio_queue.qsize(),
            'result_queue_size': self.result_queue.qsize(),
            'buffer_size': len(self.audio_buffer),
            'sample_rate': self.config.sample_rate
        }


# WebRTC integration for streaming
class WebRTCVoiceStreamer:
    """WebRTC integration for real-time streaming"""
    
    def __init__(self, voice_engine: NexusVoiceEngine):
        self.engine = voice_engine
        self.peer_connections = {}
        
    async def handle_offer(self, offer: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle WebRTC offer"""
        # Implementation would use aiortc or similar
        pass
        
    async def stream_audio(self, client_id: str):
        """Stream audio to client"""
        # Implementation for WebRTC audio streaming
        pass


if __name__ == "__main__":
    # Example usage
    engine = NexusVoiceEngine()
    
    # Set up callbacks
    def on_transcription(result):
        print(f"Transcription: {result['text']}")
        print(f"Language: {result['language']}")
        print(f"Confidence: {result['confidence']:.2f}")
        
    def on_wake_word(confidence):
        print(f"Wake word detected! Confidence: {confidence:.2f}")
        
    engine.on_transcription = on_transcription
    engine.on_wake_word = on_wake_word
    
    try:
        # Calibrate noise
        engine.calibrate_noise()
        
        # Start engine
        engine.start()
        
        # Keep running
        print("Voice engine running. Say 'Hey NEXUS' to activate...")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping voice engine...")
        engine.stop()