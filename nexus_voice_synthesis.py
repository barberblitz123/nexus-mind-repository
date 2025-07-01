#!/usr/bin/env python3
"""
NEXUS Voice Synthesis - Advanced text-to-speech with emotion and voice cloning
"""

import asyncio
import numpy as np
import torch
import torchaudio
from typing import Optional, Dict, Any, List, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import json
import io
import wave
import logging
from pathlib import Path
import queue
import threading
from TTS.api import TTS
import pyttsx3
import edge_tts
import soundfile as sf
from pydub import AudioSegment
from pydub.effects import normalize
import xml.etree.ElementTree as ET
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceEmotion(Enum):
    """Available voice emotions"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    EXCITED = "excited"
    CALM = "calm"
    CONFUSED = "confused"
    CONFIDENT = "confident"
    FEARFUL = "fearful"
    SURPRISED = "surprised"


class VoiceStyle(Enum):
    """Voice speaking styles"""
    CONVERSATIONAL = "conversational"
    NARRATIVE = "narrative"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    DRAMATIC = "dramatic"
    WHISPER = "whisper"
    SHOUTING = "shouting"
    ROBOTIC = "robotic"


@dataclass
class VoiceProfile:
    """Voice profile configuration"""
    name: str
    gender: str = "neutral"
    age: str = "adult"
    language: str = "en-US"
    pitch: float = 1.0  # 0.5 to 2.0
    speed: float = 1.0  # 0.5 to 2.0
    volume: float = 1.0  # 0.0 to 1.0
    emotion: VoiceEmotion = VoiceEmotion.NEUTRAL
    style: VoiceStyle = VoiceStyle.CONVERSATIONAL
    voice_id: Optional[str] = None
    model_path: Optional[str] = None


@dataclass
class SynthesisRequest:
    """TTS synthesis request"""
    text: str
    voice_profile: VoiceProfile
    ssml: bool = False
    streaming: bool = True
    format: str = "wav"
    sample_rate: int = 22050
    emotion_intensity: float = 1.0
    prosody_variation: float = 1.0


class SSMLProcessor:
    """SSML (Speech Synthesis Markup Language) processor"""
    
    def __init__(self):
        self.ssml_pattern = re.compile(r'<speak>.*?</speak>', re.DOTALL)
        
    def parse(self, ssml_text: str) -> List[Dict[str, Any]]:
        """Parse SSML and extract speech instructions"""
        if not self.ssml_pattern.match(ssml_text.strip()):
            # Wrap in speak tags if not present
            ssml_text = f"<speak>{ssml_text}</speak>"
            
        try:
            root = ET.fromstring(ssml_text)
            return self._parse_element(root)
        except ET.ParseError as e:
            logger.error(f"SSML parse error: {e}")
            # Fallback to plain text
            return [{'type': 'text', 'content': ssml_text}]
            
    def _parse_element(self, element) -> List[Dict[str, Any]]:
        """Recursively parse SSML elements"""
        instructions = []
        
        # Handle text before any child elements
        if element.text:
            instructions.append({
                'type': 'text',
                'content': element.text.strip()
            })
            
        # Process child elements
        for child in element:
            tag = child.tag.lower()
            
            if tag == 'break':
                instructions.append({
                    'type': 'break',
                    'time': child.get('time', '500ms'),
                    'strength': child.get('strength', 'medium')
                })
            elif tag == 'emphasis':
                instructions.append({
                    'type': 'emphasis',
                    'level': child.get('level', 'moderate'),
                    'content': child.text
                })
            elif tag == 'prosody':
                instructions.append({
                    'type': 'prosody',
                    'rate': child.get('rate', '1.0'),
                    'pitch': child.get('pitch', '1.0'),
                    'volume': child.get('volume', '1.0'),
                    'content': child.text
                })
            elif tag == 'say-as':
                instructions.append({
                    'type': 'say-as',
                    'interpret-as': child.get('interpret-as'),
                    'format': child.get('format'),
                    'content': child.text
                })
            elif tag == 'audio':
                instructions.append({
                    'type': 'audio',
                    'src': child.get('src')
                })
            elif tag == 'mark':
                instructions.append({
                    'type': 'mark',
                    'name': child.get('name')
                })
                
            # Recursively process child elements
            instructions.extend(self._parse_element(child))
            
            # Handle text after child element
            if child.tail:
                instructions.append({
                    'type': 'text',
                    'content': child.tail.strip()
                })
                
        return instructions


class EmotionController:
    """Control emotion and prosody in synthesized speech"""
    
    def __init__(self):
        self.emotion_mappings = {
            VoiceEmotion.HAPPY: {
                'pitch_modifier': 1.1,
                'speed_modifier': 1.05,
                'energy_modifier': 1.2
            },
            VoiceEmotion.SAD: {
                'pitch_modifier': 0.9,
                'speed_modifier': 0.95,
                'energy_modifier': 0.8
            },
            VoiceEmotion.ANGRY: {
                'pitch_modifier': 1.15,
                'speed_modifier': 1.1,
                'energy_modifier': 1.3
            },
            VoiceEmotion.EXCITED: {
                'pitch_modifier': 1.2,
                'speed_modifier': 1.15,
                'energy_modifier': 1.4
            },
            VoiceEmotion.CALM: {
                'pitch_modifier': 0.95,
                'speed_modifier': 0.9,
                'energy_modifier': 0.9
            },
            VoiceEmotion.FEARFUL: {
                'pitch_modifier': 1.05,
                'speed_modifier': 1.2,
                'energy_modifier': 0.9,
                'tremolo': True
            }
        }
        
    def apply_emotion(self, audio: np.ndarray, emotion: VoiceEmotion, 
                     intensity: float = 1.0, sample_rate: int = 22050) -> np.ndarray:
        """Apply emotion to audio"""
        if emotion == VoiceEmotion.NEUTRAL:
            return audio
            
        params = self.emotion_mappings.get(emotion, {})
        
        # Apply pitch modification
        if 'pitch_modifier' in params:
            pitch_shift = (params['pitch_modifier'] - 1.0) * intensity
            audio = self._pitch_shift(audio, pitch_shift, sample_rate)
            
        # Apply speed modification
        if 'speed_modifier' in params:
            speed_factor = 1.0 + (params['speed_modifier'] - 1.0) * intensity
            audio = self._time_stretch(audio, speed_factor)
            
        # Apply energy modification
        if 'energy_modifier' in params:
            energy_factor = 1.0 + (params['energy_modifier'] - 1.0) * intensity
            audio = audio * energy_factor
            
        # Apply tremolo for fearful emotion
        if params.get('tremolo') and intensity > 0.5:
            audio = self._apply_tremolo(audio, sample_rate)
            
        return np.clip(audio, -1.0, 1.0)
        
    def _pitch_shift(self, audio: np.ndarray, shift: float, sample_rate: int) -> np.ndarray:
        """Shift pitch of audio"""
        # Simple pitch shifting using resampling
        # In production, use librosa.effects.pitch_shift or similar
        return audio
        
    def _time_stretch(self, audio: np.ndarray, factor: float) -> np.ndarray:
        """Time stretch audio"""
        # Simple time stretching
        # In production, use librosa.effects.time_stretch
        return audio
        
    def _apply_tremolo(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply tremolo effect"""
        tremolo_freq = 4.0  # Hz
        tremolo_depth = 0.2
        t = np.arange(len(audio)) / sample_rate
        tremolo = 1.0 + tremolo_depth * np.sin(2 * np.pi * tremolo_freq * t)
        return audio * tremolo


class VoiceCloner:
    """Voice cloning capabilities"""
    
    def __init__(self):
        self.embeddings = {}
        self.model = None  # Would load voice cloning model
        
    def create_embedding(self, audio_samples: List[np.ndarray], 
                        speaker_name: str) -> Dict[str, Any]:
        """Create voice embedding from audio samples"""
        # In production, use models like YourTTS or similar
        embedding = {
            'speaker_name': speaker_name,
            'embedding_vector': np.random.randn(256),  # Placeholder
            'sample_rate': 22050,
            'created_at': time.time()
        }
        
        self.embeddings[speaker_name] = embedding
        return embedding
        
    def synthesize_with_voice(self, text: str, speaker_name: str) -> np.ndarray:
        """Synthesize text with cloned voice"""
        if speaker_name not in self.embeddings:
            raise ValueError(f"Voice profile '{speaker_name}' not found")
            
        # In production, use the actual voice cloning model
        # This is a placeholder
        return np.random.randn(22050 * 3)  # 3 seconds of audio


class NexusVoiceSynthesizer:
    """Main voice synthesis engine"""
    
    def __init__(self):
        # Initialize TTS engines
        self.tts_engine = None
        self.edge_tts_voices = {}
        self.pyttsx_engine = None
        
        # Components
        self.ssml_processor = SSMLProcessor()
        self.emotion_controller = EmotionController()
        self.voice_cloner = VoiceCloner()
        
        # Voice profiles
        self.voice_profiles = self._load_default_profiles()
        self.current_profile = self.voice_profiles['default']
        
        # Audio queue for streaming
        self.audio_queue = queue.Queue()
        self.is_streaming = False
        
        # Initialize engines
        self._initialize_engines()
        
    def _initialize_engines(self):
        """Initialize TTS engines"""
        try:
            # Initialize Coqui TTS
            self.tts_engine = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
            logger.info("Coqui TTS initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Coqui TTS: {e}")
            
        try:
            # Initialize pyttsx3 as fallback
            self.pyttsx_engine = pyttsx3.init()
            self._configure_pyttsx()
            logger.info("pyttsx3 initialized")
        except Exception as e:
            logger.warning(f"Could not initialize pyttsx3: {e}")
            
        # Get Edge TTS voices
        asyncio.run(self._load_edge_voices())
        
    def _configure_pyttsx(self):
        """Configure pyttsx3 engine"""
        if not self.pyttsx_engine:
            return
            
        # Set properties
        self.pyttsx_engine.setProperty('rate', 150)
        self.pyttsx_engine.setProperty('volume', 1.0)
        
        # Get available voices
        voices = self.pyttsx_engine.getProperty('voices')
        if voices:
            self.pyttsx_engine.setProperty('voice', voices[0].id)
            
    async def _load_edge_voices(self):
        """Load available Edge TTS voices"""
        try:
            voices = await edge_tts.list_voices()
            for voice in voices:
                self.edge_tts_voices[voice['ShortName']] = voice
            logger.info(f"Loaded {len(self.edge_tts_voices)} Edge TTS voices")
        except Exception as e:
            logger.warning(f"Could not load Edge TTS voices: {e}")
            
    def _load_default_profiles(self) -> Dict[str, VoiceProfile]:
        """Load default voice profiles"""
        return {
            'default': VoiceProfile(
                name="NEXUS Default",
                gender="neutral",
                language="en-US"
            ),
            'assistant': VoiceProfile(
                name="NEXUS Assistant",
                gender="female",
                language="en-US",
                style=VoiceStyle.PROFESSIONAL,
                pitch=1.05,
                speed=1.0
            ),
            'narrator': VoiceProfile(
                name="NEXUS Narrator",
                gender="male",
                language="en-US",
                style=VoiceStyle.NARRATIVE,
                pitch=0.95,
                speed=0.95
            ),
            'excited': VoiceProfile(
                name="NEXUS Excited",
                gender="neutral",
                language="en-US",
                emotion=VoiceEmotion.EXCITED,
                pitch=1.1,
                speed=1.1
            )
        }
        
    async def synthesize(self, request: SynthesisRequest) -> Union[np.ndarray, asyncio.Queue]:
        """Synthesize speech from text"""
        if request.streaming:
            return await self._synthesize_streaming(request)
        else:
            return await self._synthesize_batch(request)
            
    async def _synthesize_batch(self, request: SynthesisRequest) -> np.ndarray:
        """Synthesize complete audio"""
        # Process SSML if needed
        if request.ssml:
            instructions = self.ssml_processor.parse(request.text)
            audio_segments = []
            
            for instruction in instructions:
                if instruction['type'] == 'text':
                    segment = await self._synthesize_text(
                        instruction['content'],
                        request.voice_profile
                    )
                    audio_segments.append(segment)
                elif instruction['type'] == 'break':
                    # Add silence
                    duration = self._parse_duration(instruction['time'])
                    silence = np.zeros(int(request.sample_rate * duration))
                    audio_segments.append(silence)
                    
            audio = np.concatenate(audio_segments)
        else:
            audio = await self._synthesize_text(request.text, request.voice_profile)
            
        # Apply emotion
        if request.voice_profile.emotion != VoiceEmotion.NEUTRAL:
            audio = self.emotion_controller.apply_emotion(
                audio,
                request.voice_profile.emotion,
                request.emotion_intensity,
                request.sample_rate
            )
            
        # Apply audio effects
        audio = self._apply_voice_effects(audio, request.voice_profile, request.sample_rate)
        
        return audio
        
    async def _synthesize_streaming(self, request: SynthesisRequest) -> asyncio.Queue:
        """Synthesize audio with streaming"""
        stream_queue = asyncio.Queue()
        
        # Start synthesis in background
        asyncio.create_task(self._streaming_synthesis_worker(request, stream_queue))
        
        return stream_queue
        
    async def _streaming_synthesis_worker(self, request: SynthesisRequest, 
                                        stream_queue: asyncio.Queue):
        """Worker for streaming synthesis"""
        try:
            # Split text into sentences for streaming
            sentences = self._split_into_sentences(request.text)
            
            for sentence in sentences:
                if not sentence.strip():
                    continue
                    
                # Synthesize sentence
                audio = await self._synthesize_text(sentence, request.voice_profile)
                
                # Apply effects
                if request.voice_profile.emotion != VoiceEmotion.NEUTRAL:
                    audio = self.emotion_controller.apply_emotion(
                        audio,
                        request.voice_profile.emotion,
                        request.emotion_intensity,
                        request.sample_rate
                    )
                    
                # Stream audio chunks
                chunk_size = int(request.sample_rate * 0.1)  # 100ms chunks
                for i in range(0, len(audio), chunk_size):
                    chunk = audio[i:i + chunk_size]
                    await stream_queue.put(chunk)
                    
            # Signal end of stream
            await stream_queue.put(None)
            
        except Exception as e:
            logger.error(f"Streaming synthesis error: {e}")
            await stream_queue.put(None)
            
    async def _synthesize_text(self, text: str, profile: VoiceProfile) -> np.ndarray:
        """Synthesize text using appropriate engine"""
        # Try Coqui TTS first
        if self.tts_engine:
            try:
                wav = self.tts_engine.tts(text)
                return np.array(wav)
            except Exception as e:
                logger.warning(f"Coqui TTS failed: {e}")
                
        # Try Edge TTS
        if self.edge_tts_voices:
            try:
                return await self._synthesize_edge_tts(text, profile)
            except Exception as e:
                logger.warning(f"Edge TTS failed: {e}")
                
        # Fallback to pyttsx3
        if self.pyttsx_engine:
            return self._synthesize_pyttsx(text, profile)
            
        # Last resort - generate silence
        logger.error("No TTS engine available")
        return np.zeros(int(22050 * len(text) * 0.1))  # Rough estimate
        
    async def _synthesize_edge_tts(self, text: str, profile: VoiceProfile) -> np.ndarray:
        """Synthesize using Edge TTS"""
        # Select appropriate voice
        voice_name = self._select_edge_voice(profile)
        
        # Create communication object
        communicate = edge_tts.Communicate(text, voice_name)
        
        # Generate audio
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
                
        # Convert to numpy array
        audio = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        samples = np.array(audio.get_array_of_samples())
        
        # Normalize to float32
        samples = samples.astype(np.float32) / 32768.0
        
        return samples
        
    def _synthesize_pyttsx(self, text: str, profile: VoiceProfile) -> np.ndarray:
        """Synthesize using pyttsx3"""
        # Save to temporary file
        temp_file = io.BytesIO()
        self.pyttsx_engine.save_to_file(text, temp_file)
        self.pyttsx_engine.runAndWait()
        
        # Load and convert
        temp_file.seek(0)
        audio, sr = sf.read(temp_file)
        
        return audio
        
    def _select_edge_voice(self, profile: VoiceProfile) -> str:
        """Select Edge TTS voice based on profile"""
        # Filter voices by language
        matching_voices = [
            v for v in self.edge_tts_voices.values()
            if v['Locale'].startswith(profile.language[:2])
        ]
        
        # Filter by gender if specified
        if profile.gender != "neutral":
            matching_voices = [
                v for v in matching_voices
                if v['Gender'].lower() == profile.gender.lower()
            ]
            
        # Select based on style
        style_keywords = {
            VoiceStyle.PROFESSIONAL: ["professional", "formal"],
            VoiceStyle.CASUAL: ["casual", "friendly"],
            VoiceStyle.NARRATIVE: ["narrator", "story"]
        }
        
        if profile.style in style_keywords:
            keywords = style_keywords[profile.style]
            for voice in matching_voices:
                if any(kw in voice['FriendlyName'].lower() for kw in keywords):
                    return voice['ShortName']
                    
        # Default to first matching voice
        return matching_voices[0]['ShortName'] if matching_voices else "en-US-JennyNeural"
        
    def _apply_voice_effects(self, audio: np.ndarray, profile: VoiceProfile, 
                           sample_rate: int) -> np.ndarray:
        """Apply voice effects based on profile"""
        # Apply pitch shifting
        if profile.pitch != 1.0:
            # In production, use proper pitch shifting
            pass
            
        # Apply speed adjustment
        if profile.speed != 1.0:
            # In production, use proper time stretching
            pass
            
        # Apply volume adjustment
        audio = audio * profile.volume
        
        # Apply style-specific effects
        if profile.style == VoiceStyle.WHISPER:
            # Add breathiness and reduce volume
            audio = audio * 0.3
            # Add noise for breathiness
            noise = np.random.normal(0, 0.01, len(audio))
            audio = audio + noise
        elif profile.style == VoiceStyle.ROBOTIC:
            # Apply vocoder-like effect
            # In production, use proper vocoder
            pass
            
        return np.clip(audio, -1.0, 1.0)
        
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for streaming"""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return sentences
        
    def _parse_duration(self, duration_str: str) -> float:
        """Parse duration string to seconds"""
        if duration_str.endswith('ms'):
            return float(duration_str[:-2]) / 1000
        elif duration_str.endswith('s'):
            return float(duration_str[:-1])
        else:
            return 0.5  # Default
            
    def create_voice_profile(self, name: str, **kwargs) -> VoiceProfile:
        """Create a new voice profile"""
        profile = VoiceProfile(name=name, **kwargs)
        self.voice_profiles[name] = profile
        return profile
        
    def clone_voice(self, audio_files: List[str], profile_name: str) -> VoiceProfile:
        """Clone a voice from audio samples"""
        # Load audio samples
        samples = []
        for file_path in audio_files:
            audio, sr = sf.read(file_path)
            # Resample if needed
            if sr != 22050:
                # In production, use proper resampling
                pass
            samples.append(audio)
            
        # Create voice embedding
        embedding = self.voice_cloner.create_embedding(samples, profile_name)
        
        # Create voice profile
        profile = VoiceProfile(
            name=profile_name,
            voice_id=embedding['speaker_name']
        )
        
        self.voice_profiles[profile_name] = profile
        return profile
        
    def get_available_voices(self) -> Dict[str, List[str]]:
        """Get all available voices"""
        voices = {
            'profiles': list(self.voice_profiles.keys()),
            'edge_tts': list(self.edge_tts_voices.keys()),
            'cloned': list(self.voice_cloner.embeddings.keys())
        }
        
        if self.pyttsx_engine:
            pyttsx_voices = [v.id for v in self.pyttsx_engine.getProperty('voices')]
            voices['pyttsx'] = pyttsx_voices
            
        return voices
        
    def export_audio(self, audio: np.ndarray, output_path: str, 
                    sample_rate: int = 22050, format: str = 'wav'):
        """Export audio to file"""
        sf.write(output_path, audio, sample_rate, format=format)
        logger.info(f"Audio exported to {output_path}")


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Initialize synthesizer
        synthesizer = NexusVoiceSynthesizer()
        
        # Create a custom voice profile
        profile = synthesizer.create_voice_profile(
            "friendly_assistant",
            gender="female",
            emotion=VoiceEmotion.HAPPY,
            style=VoiceStyle.CONVERSATIONAL,
            pitch=1.1,
            speed=1.05
        )
        
        # Simple synthesis
        request = SynthesisRequest(
            text="Hello! I'm NEXUS, your AI assistant. How can I help you today?",
            voice_profile=profile,
            streaming=False
        )
        
        audio = await synthesizer.synthesize(request)
        print(f"Generated audio: {len(audio)} samples")
        
        # SSML synthesis
        ssml_text = """
        <speak>
            Welcome to NEXUS! <break time="500ms"/>
            I can speak with <emphasis level="strong">emotion</emphasis> and
            <prosody rate="slow" pitch="low">vary my voice</prosody>.
            <break time="1s"/>
            What would you like me to help with?
        </speak>
        """
        
        ssml_request = SynthesisRequest(
            text=ssml_text,
            voice_profile=profile,
            ssml=True,
            streaming=False
        )
        
        ssml_audio = await synthesizer.synthesize(ssml_request)
        print(f"Generated SSML audio: {len(ssml_audio)} samples")
        
        # Export audio
        synthesizer.export_audio(audio, "nexus_greeting.wav")
        
        # Streaming synthesis
        stream_request = SynthesisRequest(
            text="This is a longer text that will be streamed. Each sentence will be synthesized and sent as it's ready.",
            voice_profile=profile,
            streaming=True
        )
        
        stream_queue = await synthesizer.synthesize(stream_request)
        
        print("Streaming audio...")
        while True:
            chunk = await stream_queue.get()
            if chunk is None:
                break
            print(f"Received chunk: {len(chunk)} samples")
            
    # Run example
    asyncio.run(main())