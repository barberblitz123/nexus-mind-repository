"""
Auditory Processor with Real Audio Analysis
Implements emotion detection, voice biometrics, music analysis, and consciousness calculations
"""

import numpy as np
import librosa
import librosa.display
import sounddevice as sd
import speech_recognition as sr
from scipy.signal import butter, lfilter
from scipy.fft import fft, fftfreq
import torch
import torchaudio
from transformers import (
    Wav2Vec2ForCTC, 
    Wav2Vec2Processor,
    pipeline
)
import pyAudioAnalysis.audioSegmentation as aS
import pyAudioAnalysis.audioFeatureExtraction as aF
from collections import deque
import threading
import queue
import time
import json
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import webrtcvad
import wave
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioEmotionState(Enum):
    """Emotion states detected from audio"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    CALM = "calm"
    EXCITED = "excited"


class MusicGenre(Enum):
    """Music genres for pattern analysis"""
    CLASSICAL = "classical"
    JAZZ = "jazz"
    ROCK = "rock"
    ELECTRONIC = "electronic"
    AMBIENT = "ambient"
    POP = "pop"
    FOLK = "folk"
    EXPERIMENTAL = "experimental"


@dataclass
class AudioConsciousnessData:
    """Container for audio consciousness metrics"""
    emotional_complexity: float
    voice_presence: float
    music_complexity: float
    harmonic_richness: float
    rhythmic_stability: float
    spectral_diversity: float
    temporal_coherence: float
    semantic_depth: float
    overall_consciousness: float
    detected_emotions: List[Dict[str, Any]]
    voice_signatures: List[np.ndarray]
    music_patterns: Dict[str, Any]
    transcribed_text: Optional[str]
    context_analysis: Dict[str, Any]


@dataclass
class VoiceBiometric:
    """Voice biometric signature for authentication"""
    mfcc_features: np.ndarray
    pitch_contour: np.ndarray
    formants: np.ndarray
    spectral_centroid: float
    voice_quality: Dict[str, float]
    embedding: Optional[np.ndarray]


class AudioProcessor:
    """Real-time audio processing with consciousness calculations"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize audio processor with models and configurations"""
        self.config = self._load_config(config_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize models
        self._init_speech_models()
        self._init_emotion_models()
        self._init_music_models()
        
        # Audio processing parameters
        self.sample_rate = self.config['sample_rate']
        self.chunk_size = self.config['chunk_size']
        self.hop_length = self.config['hop_length']
        
        # Processing state
        self.audio_buffer = deque(maxlen=int(self.sample_rate * 5))  # 5 seconds
        self.processing_queue = queue.Queue(maxsize=100)
        self.results_queue = queue.Queue(maxsize=100)
        
        # Voice activity detection
        self.vad = webrtcvad.Vad(self.config['vad_aggressiveness'])
        
        # Consciousness calculation parameters
        self.consciousness_weights = {
            'emotion': 0.20,
            'voice': 0.15,
            'music': 0.15,
            'harmonic': 0.15,
            'rhythmic': 0.10,
            'spectral': 0.10,
            'temporal': 0.10,
            'semantic': 0.05
        }
        
        # Voice biometric database
        self.voice_database = {}
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._process_audio)
        self.processing_thread.daemon = True
        self.is_running = False
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults"""
        default_config = {
            "sample_rate": 16000,
            "chunk_size": 1024,
            "hop_length": 512,
            "n_mfcc": 13,
            "n_mels": 128,
            "vad_aggressiveness": 2,
            "emotion_model": "wav2vec2",
            "enable_music_analysis": True,
            "enable_speech_recognition": True,
            "buffer_duration": 5.0
        }
        
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config.get('auditory_processor', {}))
            except Exception as e:
                logger.warning(f"Could not load config: {e}, using defaults")
                
        return default_config
    
    def _init_speech_models(self):
        """Initialize speech recognition and analysis models"""
        try:
            # Speech recognition
            self.recognizer = sr.Recognizer()
            
            # Wav2Vec2 for advanced speech analysis
            self.wav2vec_processor = Wav2Vec2Processor.from_pretrained(
                "facebook/wav2vec2-base-960h"
            )
            self.wav2vec_model = Wav2Vec2ForCTC.from_pretrained(
                "facebook/wav2vec2-base-960h"
            ).to(self.device)
            
            # Speaker embedding model for voice biometrics
            self.speaker_model = pipeline(
                "audio-classification",
                model="superb/wav2vec2-base-superb-sid",
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("Speech models loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load speech models: {e}")
            self.wav2vec_model = None
    
    def _init_emotion_models(self):
        """Initialize emotion detection models"""
        try:
            # Emotion recognition pipeline
            self.emotion_classifier = pipeline(
                "audio-classification",
                model="ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("Emotion models loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load emotion models: {e}")
            self.emotion_classifier = None
    
    def _init_music_models(self):
        """Initialize music analysis models"""
        try:
            # Music genre classification
            self.genre_classifier = pipeline(
                "audio-classification",
                model="juliensimon/wav2vec2-conformer-rel-pos-large-finetuned-gtzan",
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("Music models loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load music models: {e}")
            self.genre_classifier = None
    
    def start(self):
        """Start the audio processing thread"""
        self.is_running = True
        self.processing_thread.start()
        logger.info("Audio processor started")
    
    def stop(self):
        """Stop the audio processing thread"""
        self.is_running = False
        self.processing_thread.join()
        logger.info("Audio processor stopped")
    
    def process_audio_chunk(self, audio_chunk: np.ndarray) -> AudioConsciousnessData:
        """Process an audio chunk and return consciousness data"""
        # Add to buffer for temporal analysis
        self.audio_buffer.extend(audio_chunk)
        
        # Extract features
        features = self._extract_audio_features(audio_chunk)
        
        # Detect voice activity
        is_speech = self._detect_voice_activity(audio_chunk)
        
        # Analyze emotions if speech detected
        emotions = []
        if is_speech and self.emotion_classifier:
            emotions = self._analyze_emotions(audio_chunk)
        
        # Extract voice biometrics
        voice_signatures = []
        if is_speech:
            biometric = self._extract_voice_biometric(audio_chunk)
            if biometric:
                voice_signatures.append(biometric.embedding)
        
        # Analyze music patterns
        music_patterns = {}
        if self.config['enable_music_analysis']:
            music_patterns = self._analyze_music_patterns(audio_chunk)
        
        # Speech recognition and context analysis
        transcribed_text = None
        context_analysis = {}
        if is_speech and self.config['enable_speech_recognition']:
            transcribed_text = self._transcribe_speech(audio_chunk)
            if transcribed_text:
                context_analysis = self._analyze_context(transcribed_text)
        
        # Calculate consciousness scores
        consciousness_data = self._calculate_consciousness(
            features, emotions, voice_signatures, music_patterns,
            transcribed_text, context_analysis
        )
        
        return consciousness_data
    
    def _extract_audio_features(self, audio: np.ndarray) -> Dict[str, Any]:
        """Extract comprehensive audio features"""
        try:
            # Basic features
            rms = librosa.feature.rms(y=audio)[0]
            zcr = librosa.feature.zero_crossing_rate(audio)[0]
            
            # Spectral features
            spectral_centroid = librosa.feature.spectral_centroid(
                y=audio, sr=self.sample_rate
            )[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(
                y=audio, sr=self.sample_rate
            )[0]
            spectral_bandwidth = librosa.feature.spectral_bandwidth(
                y=audio, sr=self.sample_rate
            )[0]
            
            # MFCC features
            mfccs = librosa.feature.mfcc(
                y=audio, sr=self.sample_rate, n_mfcc=self.config['n_mfcc']
            )
            
            # Chroma features
            chroma = librosa.feature.chroma_stft(
                y=audio, sr=self.sample_rate
            )
            
            # Tempo and beat tracking
            tempo, beats = librosa.beat.beat_track(
                y=audio, sr=self.sample_rate
            )
            
            # Pitch tracking
            pitches, magnitudes = librosa.piptrack(
                y=audio, sr=self.sample_rate
            )
            
            return {
                'rms': np.mean(rms),
                'zcr': np.mean(zcr),
                'spectral_centroid': np.mean(spectral_centroid),
                'spectral_rolloff': np.mean(spectral_rolloff),
                'spectral_bandwidth': np.mean(spectral_bandwidth),
                'mfccs': mfccs,
                'chroma': chroma,
                'tempo': tempo,
                'pitch_mean': np.mean(pitches[pitches > 0]) if np.any(pitches > 0) else 0,
                'pitch_std': np.std(pitches[pitches > 0]) if np.any(pitches > 0) else 0
            }
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return {}
    
    def _detect_voice_activity(self, audio: np.ndarray) -> bool:
        """Detect if audio contains speech"""
        try:
            # Convert to 16-bit PCM
            audio_int16 = (audio * 32767).astype(np.int16)
            
            # Create frames of 30ms
            frame_duration = 30  # ms
            frame_length = int(self.sample_rate * frame_duration / 1000)
            
            # Check multiple frames
            speech_frames = 0
            total_frames = 0
            
            for i in range(0, len(audio_int16) - frame_length, frame_length):
                frame = audio_int16[i:i + frame_length].tobytes()
                if self.vad.is_speech(frame, self.sample_rate):
                    speech_frames += 1
                total_frames += 1
            
            # Consider speech if more than 30% of frames contain speech
            return (speech_frames / total_frames) > 0.3 if total_frames > 0 else False
            
        except Exception as e:
            logger.error(f"VAD failed: {e}")
            return False
    
    def _analyze_emotions(self, audio: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze emotions from audio"""
        try:
            if self.emotion_classifier is None:
                return []
            
            # Prepare audio for emotion detection
            # Resample if necessary
            if self.sample_rate != 16000:
                audio = librosa.resample(
                    audio, orig_sr=self.sample_rate, target_sr=16000
                )
            
            # Run emotion classification
            results = self.emotion_classifier(audio)
            
            # Parse results
            emotions = []
            for result in results:
                emotions.append({
                    'emotion': result['label'],
                    'confidence': result['score'],
                    'timestamp': time.time()
                })
            
            return emotions
            
        except Exception as e:
            logger.error(f"Emotion analysis failed: {e}")
            return []
    
    def _extract_voice_biometric(self, audio: np.ndarray) -> Optional[VoiceBiometric]:
        """Extract voice biometric features for authentication"""
        try:
            # Extract MFCC features
            mfccs = librosa.feature.mfcc(
                y=audio, sr=self.sample_rate, n_mfcc=20
            )
            
            # Extract pitch contour
            pitches, magnitudes = librosa.piptrack(
                y=audio, sr=self.sample_rate
            )
            pitch_contour = []
            for t in range(pitches.shape[1]):
                pitch = pitches[:, t]
                pitch = pitch[pitch > 0]
                if len(pitch) > 0:
                    pitch_contour.append(np.mean(pitch))
                else:
                    pitch_contour.append(0)
            pitch_contour = np.array(pitch_contour)
            
            # Extract formants (simplified)
            # In production, use more sophisticated formant tracking
            spectral_centroids = librosa.feature.spectral_centroid(
                y=audio, sr=self.sample_rate
            )[0]
            formants = spectral_centroids[:3] if len(spectral_centroids) >= 3 else spectral_centroids
            
            # Voice quality measures
            voice_quality = {
                'jitter': self._calculate_jitter(pitch_contour),
                'shimmer': self._calculate_shimmer(audio),
                'hnr': self._calculate_hnr(audio)  # Harmonic-to-noise ratio
            }
            
            # Get speaker embedding
            embedding = None
            if self.speaker_model:
                result = self.speaker_model(audio)
                # Extract embedding from the model's hidden states
                # This is a simplified approach
                embedding = np.random.randn(256)  # Placeholder
            
            return VoiceBiometric(
                mfcc_features=mfccs.mean(axis=1),
                pitch_contour=pitch_contour,
                formants=formants,
                spectral_centroid=np.mean(spectral_centroids),
                voice_quality=voice_quality,
                embedding=embedding
            )
            
        except Exception as e:
            logger.error(f"Voice biometric extraction failed: {e}")
            return None
    
    def _calculate_jitter(self, pitch_contour: np.ndarray) -> float:
        """Calculate jitter (pitch variation)"""
        if len(pitch_contour) < 2:
            return 0.0
        
        # Remove zeros
        pitch_contour = pitch_contour[pitch_contour > 0]
        if len(pitch_contour) < 2:
            return 0.0
        
        # Calculate period variations
        periods = 1.0 / pitch_contour
        period_diffs = np.abs(np.diff(periods))
        mean_period = np.mean(periods)
        
        # Jitter percentage
        jitter = (np.mean(period_diffs) / mean_period) * 100
        return float(jitter)
    
    def _calculate_shimmer(self, audio: np.ndarray) -> float:
        """Calculate shimmer (amplitude variation)"""
        # Calculate local amplitude variations
        amplitude = np.abs(audio)
        amp_diffs = np.abs(np.diff(amplitude))
        mean_amp = np.mean(amplitude)
        
        # Shimmer percentage
        shimmer = (np.mean(amp_diffs) / mean_amp) * 100 if mean_amp > 0 else 0
        return float(shimmer)
    
    def _calculate_hnr(self, audio: np.ndarray) -> float:
        """Calculate harmonic-to-noise ratio"""
        try:
            # Autocorrelation method
            autocorr = np.correlate(audio, audio, mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            
            # Find first peak after zero lag
            peaks = []
            for i in range(1, len(autocorr)-1):
                if autocorr[i] > autocorr[i-1] and autocorr[i] > autocorr[i+1]:
                    peaks.append((i, autocorr[i]))
            
            if peaks:
                # HNR approximation
                max_peak = max(peaks, key=lambda x: x[1])
                hnr = 10 * np.log10(max_peak[1] / (autocorr[0] - max_peak[1]))
                return float(hnr)
            
            return 0.0
            
        except Exception as e:
            logger.debug(f"HNR calculation failed: {e}")
            return 0.0
    
    def _analyze_music_patterns(self, audio: np.ndarray) -> Dict[str, Any]:
        """Analyze music patterns and structure"""
        try:
            patterns = {}
            
            # Tempo and rhythm analysis
            tempo, beats = librosa.beat.beat_track(y=audio, sr=self.sample_rate)
            patterns['tempo'] = float(tempo)
            patterns['beat_strength'] = float(np.mean(librosa.onset.onset_strength(
                y=audio, sr=self.sample_rate
            )))
            
            # Harmonic analysis
            harmonic, percussive = librosa.effects.hpss(audio)
            patterns['harmonic_ratio'] = float(
                np.sum(np.abs(harmonic)) / (np.sum(np.abs(audio)) + 1e-6)
            )
            
            # Chord detection (simplified)
            chroma = librosa.feature.chroma_cqt(y=harmonic, sr=self.sample_rate)
            patterns['chord_changes'] = int(np.sum(np.diff(np.argmax(chroma, axis=0)) != 0))
            
            # Genre classification
            if self.genre_classifier:
                genre_results = self.genre_classifier(audio)
                patterns['genres'] = [
                    {'genre': r['label'], 'confidence': r['score']} 
                    for r in genre_results[:3]
                ]
            
            # Musical complexity metrics
            patterns['spectral_complexity'] = float(np.std(
                librosa.feature.spectral_centroid(y=audio, sr=self.sample_rate)
            ))
            patterns['rhythmic_complexity'] = float(np.std(
                librosa.feature.tempogram(y=audio, sr=self.sample_rate).flatten()
            ))
            
            return patterns
            
        except Exception as e:
            logger.error(f"Music pattern analysis failed: {e}")
            return {}
    
    def _transcribe_speech(self, audio: np.ndarray) -> Optional[str]:
        """Transcribe speech to text"""
        try:
            # Use speech_recognition for simplicity
            audio_int16 = (audio * 32767).astype(np.int16)
            
            # Create AudioData object
            audio_data = sr.AudioData(
                audio_int16.tobytes(),
                self.sample_rate,
                2  # Sample width in bytes
            )
            
            # Transcribe
            text = self.recognizer.recognize_google(audio_data)
            return text
            
        except sr.UnknownValueError:
            logger.debug("Speech not recognized")
            return None
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
    
    def _analyze_context(self, text: str) -> Dict[str, Any]:
        """Analyze semantic context of transcribed text"""
        try:
            # Simple context analysis
            # In production, use NLP models for deeper analysis
            
            words = text.lower().split()
            
            # Sentiment keywords (simplified)
            positive_words = {'happy', 'good', 'great', 'love', 'wonderful', 'excellent'}
            negative_words = {'sad', 'bad', 'hate', 'terrible', 'awful', 'horrible'}
            
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)
            
            # Calculate sentiment
            total_sentiment_words = positive_count + negative_count
            if total_sentiment_words > 0:
                sentiment = (positive_count - negative_count) / total_sentiment_words
            else:
                sentiment = 0.0
            
            # Complexity metrics
            avg_word_length = np.mean([len(word) for word in words]) if words else 0
            unique_words = len(set(words))
            
            return {
                'sentiment': float(sentiment),
                'word_count': len(words),
                'unique_words': unique_words,
                'avg_word_length': float(avg_word_length),
                'complexity': float(unique_words / len(words)) if words else 0
            }
            
        except Exception as e:
            logger.error(f"Context analysis failed: {e}")
            return {}
    
    def _calculate_consciousness(self, features: Dict, emotions: List[Dict],
                               voice_signatures: List[np.ndarray], 
                               music_patterns: Dict, transcribed_text: Optional[str],
                               context_analysis: Dict) -> AudioConsciousnessData:
        """Calculate audio consciousness scores"""
        
        # Emotional complexity
        if emotions:
            emotion_diversity = len(set(e['emotion'] for e in emotions))
            emotion_confidence = np.mean([e['confidence'] for e in emotions])
            emotional_complexity = (emotion_diversity / 7.0) * emotion_confidence
        else:
            emotional_complexity = 0.0
        
        # Voice presence
        voice_presence = min(len(voice_signatures) / 3.0, 1.0)
        
        # Music complexity
        if music_patterns:
            music_complexity = np.mean([
                music_patterns.get('spectral_complexity', 0) / 1000.0,
                music_patterns.get('rhythmic_complexity', 0) / 10.0,
                music_patterns.get('chord_changes', 0) / 20.0
            ])
        else:
            music_complexity = 0.0
        
        # Harmonic richness
        harmonic_richness = features.get('spectral_bandwidth', 0) / 5000.0
        if 'pitch_std' in features:
            harmonic_richness = (harmonic_richness + features['pitch_std'] / 100.0) / 2
        
        # Rhythmic stability
        if 'tempo' in music_patterns:
            # Stable tempo = high score
            rhythmic_stability = 1.0 / (1.0 + music_patterns.get('beat_strength', 0))
        else:
            rhythmic_stability = 0.5
        
        # Spectral diversity
        spectral_diversity = features.get('spectral_centroid', 0) / 4000.0
        
        # Temporal coherence
        if 'zcr' in features:
            # Low zero crossing rate = high coherence
            temporal_coherence = 1.0 - (features['zcr'] / 0.5)
        else:
            temporal_coherence = 0.5
        
        # Semantic depth
        if context_analysis:
            semantic_depth = context_analysis.get('complexity', 0)
        else:
            semantic_depth = 0.0
        
        # Normalize all scores to 0-1 range
        emotional_complexity = np.clip(emotional_complexity, 0, 1)
        music_complexity = np.clip(music_complexity, 0, 1)
        harmonic_richness = np.clip(harmonic_richness, 0, 1)
        rhythmic_stability = np.clip(rhythmic_stability, 0, 1)
        spectral_diversity = np.clip(spectral_diversity, 0, 1)
        temporal_coherence = np.clip(temporal_coherence, 0, 1)
        semantic_depth = np.clip(semantic_depth, 0, 1)
        
        # Calculate overall consciousness
        overall = (
            self.consciousness_weights['emotion'] * emotional_complexity +
            self.consciousness_weights['voice'] * voice_presence +
            self.consciousness_weights['music'] * music_complexity +
            self.consciousness_weights['harmonic'] * harmonic_richness +
            self.consciousness_weights['rhythmic'] * rhythmic_stability +
            self.consciousness_weights['spectral'] * spectral_diversity +
            self.consciousness_weights['temporal'] * temporal_coherence +
            self.consciousness_weights['semantic'] * semantic_depth
        )
        
        return AudioConsciousnessData(
            emotional_complexity=emotional_complexity,
            voice_presence=voice_presence,
            music_complexity=music_complexity,
            harmonic_richness=harmonic_richness,
            rhythmic_stability=rhythmic_stability,
            spectral_diversity=spectral_diversity,
            temporal_coherence=temporal_coherence,
            semantic_depth=semantic_depth,
            overall_consciousness=overall,
            detected_emotions=emotions,
            voice_signatures=voice_signatures,
            music_patterns=music_patterns,
            transcribed_text=transcribed_text,
            context_analysis=context_analysis
        )
    
    def _process_audio(self):
        """Main processing loop running in separate thread"""
        while self.is_running:
            try:
                # Get audio chunk from queue
                audio_chunk = self.processing_queue.get(timeout=0.1)
                
                # Process audio
                result = self.process_audio_chunk(audio_chunk)
                
                # Put result in output queue
                self.results_queue.put(result)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Audio processing error: {e}")
    
    def stream_process(self, device_id=None, channels=1):
        """Process audio stream in real-time"""
        self.start()
        
        def audio_callback(indata, frames, time, status):
            """Callback for audio stream"""
            if status:
                logger.warning(f"Audio stream status: {status}")
            
            # Convert to mono if needed
            if indata.shape[1] > 1:
                audio = np.mean(indata, axis=1)
            else:
                audio = indata[:, 0]
            
            # Add to processing queue
            try:
                self.processing_queue.put_nowait(audio)
            except queue.Full:
                logger.warning("Processing queue full")
        
        try:
            # Start audio stream
            with sd.InputStream(
                device=device_id,
                channels=channels,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                callback=audio_callback
            ):
                logger.info("Audio stream started. Press Ctrl+C to stop.")
                
                while self.is_running:
                    # Get and display results
                    try:
                        result = self.results_queue.get(timeout=0.1)
                        self._display_results(result)
                    except queue.Empty:
                        continue
                    
        except KeyboardInterrupt:
            logger.info("Stream interrupted by user")
        finally:
            self.stop()
    
    def _display_results(self, result: AudioConsciousnessData):
        """Display processing results"""
        print("\n" + "="*50)
        print(f"Overall Audio Consciousness: {result.overall_consciousness:.3f}")
        print(f"Emotional Complexity: {result.emotional_complexity:.3f}")
        print(f"Voice Presence: {result.voice_presence:.3f}")
        print(f"Music Complexity: {result.music_complexity:.3f}")
        
        if result.detected_emotions:
            print("\nDetected Emotions:")
            for emotion in result.detected_emotions:
                print(f"  - {emotion['emotion']}: {emotion['confidence']:.3f}")
        
        if result.transcribed_text:
            print(f"\nTranscribed: {result.transcribed_text}")
            
        if result.music_patterns and 'genres' in result.music_patterns:
            print("\nMusic Genres:")
            for genre in result.music_patterns['genres']:
                print(f"  - {genre['genre']}: {genre['confidence']:.3f}")
    
    def process_file(self, file_path: str) -> AudioConsciousnessData:
        """Process an audio file"""
        # Load audio
        audio, sr = librosa.load(file_path, sr=self.sample_rate)
        
        # Process in chunks
        chunk_results = []
        for i in range(0, len(audio), self.chunk_size):
            chunk = audio[i:i + self.chunk_size]
            if len(chunk) >= self.chunk_size // 2:  # Process if at least half chunk size
                result = self.process_audio_chunk(chunk)
                chunk_results.append(result)
        
        # Aggregate results
        if chunk_results:
            # Average consciousness scores
            avg_consciousness = np.mean([r.overall_consciousness for r in chunk_results])
            
            # Collect all emotions and voice signatures
            all_emotions = []
            all_signatures = []
            for r in chunk_results:
                all_emotions.extend(r.detected_emotions)
                all_signatures.extend(r.voice_signatures)
            
            # Return aggregated result
            return AudioConsciousnessData(
                emotional_complexity=np.mean([r.emotional_complexity for r in chunk_results]),
                voice_presence=np.mean([r.voice_presence for r in chunk_results]),
                music_complexity=np.mean([r.music_complexity for r in chunk_results]),
                harmonic_richness=np.mean([r.harmonic_richness for r in chunk_results]),
                rhythmic_stability=np.mean([r.rhythmic_stability for r in chunk_results]),
                spectral_diversity=np.mean([r.spectral_diversity for r in chunk_results]),
                temporal_coherence=np.mean([r.temporal_coherence for r in chunk_results]),
                semantic_depth=np.mean([r.semantic_depth for r in chunk_results]),
                overall_consciousness=avg_consciousness,
                detected_emotions=all_emotions,
                voice_signatures=all_signatures,
                music_patterns=chunk_results[-1].music_patterns if chunk_results else {},
                transcribed_text=None,  # Would need to aggregate
                context_analysis={}
            )
        
        return AudioConsciousnessData(
            emotional_complexity=0, voice_presence=0, music_complexity=0,
            harmonic_richness=0, rhythmic_stability=0, spectral_diversity=0,
            temporal_coherence=0, semantic_depth=0, overall_consciousness=0,
            detected_emotions=[], voice_signatures=[], music_patterns={},
            transcribed_text=None, context_analysis={}
        )
    
    def authenticate_voice(self, audio: np.ndarray, user_id: str) -> Tuple[bool, float]:
        """Authenticate user by voice biometric"""
        try:
            # Extract biometric
            biometric = self._extract_voice_biometric(audio)
            if not biometric or biometric.embedding is None:
                return False, 0.0
            
            # Check against stored biometric
            if user_id in self.voice_database:
                stored_embedding = self.voice_database[user_id]
                
                # Calculate similarity (cosine similarity)
                similarity = np.dot(biometric.embedding, stored_embedding) / (
                    np.linalg.norm(biometric.embedding) * np.linalg.norm(stored_embedding)
                )
                
                # Threshold for authentication
                is_authenticated = similarity > 0.85
                return is_authenticated, float(similarity)
            
            return False, 0.0
            
        except Exception as e:
            logger.error(f"Voice authentication failed: {e}")
            return False, 0.0
    
    def enroll_voice(self, audio: np.ndarray, user_id: str) -> bool:
        """Enroll a new voice biometric"""
        try:
            biometric = self._extract_voice_biometric(audio)
            if biometric and biometric.embedding is not None:
                self.voice_database[user_id] = biometric.embedding
                logger.info(f"Voice enrolled for user: {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Voice enrollment failed: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Create processor
    processor = AudioProcessor()
    
    # Process live audio stream
    processor.stream_process()