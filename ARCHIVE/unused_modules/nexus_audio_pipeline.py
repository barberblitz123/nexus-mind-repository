#!/usr/bin/env python3
"""
NEXUS Audio Pipeline - Complete audio processing pipeline with device management
"""

import asyncio
import numpy as np
import pyaudio
import sounddevice as sd
import soundfile as sf
from typing import Optional, List, Dict, Any, Callable, Tuple
from dataclasses import dataclass
import queue
import threading
import time
import logging
from enum import Enum
import json
from pathlib import Path
import wave
import struct
from scipy import signal
import websockets
import base64
from collections import deque
import audioop
import platform

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioFormat(Enum):
    """Supported audio formats"""
    INT16 = "int16"
    INT32 = "int32"
    FLOAT32 = "float32"
    FLOAT64 = "float64"


class DeviceType(Enum):
    """Audio device types"""
    INPUT = "input"
    OUTPUT = "output"
    DUPLEX = "duplex"


@dataclass
class AudioDevice:
    """Audio device information"""
    id: int
    name: str
    type: DeviceType
    channels: int
    sample_rate: float
    is_default: bool
    host_api: str
    latency: float


@dataclass
class AudioStreamConfig:
    """Audio stream configuration"""
    device_id: Optional[int] = None
    channels: int = 1
    sample_rate: int = 16000
    format: AudioFormat = AudioFormat.INT16
    chunk_size: int = 480  # 30ms at 16kHz
    buffer_size: int = 10  # Number of chunks to buffer
    echo_cancellation: bool = True
    noise_suppression: bool = True
    auto_gain_control: bool = True
    
    
class AudioDeviceManager:
    """Manage audio input/output devices"""
    
    def __init__(self):
        self.devices = self._enumerate_devices()
        self.current_input = None
        self.current_output = None
        self._monitor_thread = None
        self._monitoring = False
        
    def _enumerate_devices(self) -> Dict[int, AudioDevice]:
        """Get all available audio devices"""
        devices = {}
        
        # Use sounddevice for device enumeration
        device_list = sd.query_devices()
        
        for idx, device in enumerate(device_list):
            device_type = DeviceType.DUPLEX
            if device['max_input_channels'] > 0 and device['max_output_channels'] == 0:
                device_type = DeviceType.INPUT
            elif device['max_output_channels'] > 0 and device['max_input_channels'] == 0:
                device_type = DeviceType.OUTPUT
                
            devices[idx] = AudioDevice(
                id=idx,
                name=device['name'],
                type=device_type,
                channels=max(device['max_input_channels'], device['max_output_channels']),
                sample_rate=device['default_samplerate'],
                is_default=idx in [sd.default.device[0], sd.default.device[1]],
                host_api=sd.query_hostapis(device['hostapi'])['name'],
                latency=device['default_low_input_latency']
            )
            
        return devices
        
    def get_devices(self, device_type: Optional[DeviceType] = None) -> List[AudioDevice]:
        """Get devices by type"""
        if device_type is None:
            return list(self.devices.values())
            
        return [d for d in self.devices.values() if d.type == device_type or d.type == DeviceType.DUPLEX]
        
    def get_default_device(self, device_type: DeviceType) -> Optional[AudioDevice]:
        """Get default device for type"""
        devices = self.get_devices(device_type)
        
        for device in devices:
            if device.is_default:
                return device
                
        return devices[0] if devices else None
        
    def set_device(self, device_id: int, device_type: DeviceType):
        """Set active device"""
        if device_id not in self.devices:
            raise ValueError(f"Device {device_id} not found")
            
        device = self.devices[device_id]
        
        if device_type == DeviceType.INPUT:
            self.current_input = device
            sd.default.device[0] = device_id
        elif device_type == DeviceType.OUTPUT:
            self.current_output = device
            sd.default.device[1] = device_id
            
        logger.info(f"Set {device_type.value} device to: {device.name}")
        
    def start_monitoring(self, callback: Optional[Callable] = None):
        """Start monitoring for device changes"""
        if self._monitoring:
            return
            
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_devices,
            args=(callback,)
        )
        self._monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop device monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join()
            
    def _monitor_devices(self, callback: Optional[Callable]):
        """Monitor for device changes"""
        last_devices = set(self.devices.keys())
        
        while self._monitoring:
            try:
                current_devices = set(self._enumerate_devices().keys())
                
                if current_devices != last_devices:
                    self.devices = self._enumerate_devices()
                    
                    added = current_devices - last_devices
                    removed = last_devices - current_devices
                    
                    if callback:
                        callback({
                            'added': [self.devices[d] for d in added if d in self.devices],
                            'removed': list(removed)
                        })
                        
                    last_devices = current_devices
                    
            except Exception as e:
                logger.error(f"Device monitoring error: {e}")
                
            time.sleep(1.0)


class EchoCanceller:
    """Advanced echo cancellation using adaptive filtering"""
    
    def __init__(self, filter_length: int = 512, step_size: float = 0.5):
        self.filter_length = filter_length
        self.step_size = step_size
        self.weights = np.zeros(filter_length)
        self.reference_buffer = deque(maxlen=filter_length)
        self.error_buffer = deque(maxlen=1000)
        
    def process(self, input_signal: np.ndarray, reference_signal: np.ndarray) -> np.ndarray:
        """
        Cancel echo from input signal using reference signal
        
        Args:
            input_signal: Microphone input with echo
            reference_signal: Speaker output (echo source)
            
        Returns:
            Echo-cancelled signal
        """
        output = np.zeros_like(input_signal)
        
        # Ensure signals are same length
        min_len = min(len(input_signal), len(reference_signal))
        input_signal = input_signal[:min_len]
        reference_signal = reference_signal[:min_len]
        
        for i in range(len(input_signal)):
            # Update reference buffer
            self.reference_buffer.append(reference_signal[i])
            
            if len(self.reference_buffer) < self.filter_length:
                output[i] = input_signal[i]
                continue
                
            # Get reference vector
            ref_vector = np.array(self.reference_buffer)
            
            # Estimate echo
            echo_estimate = np.dot(self.weights, ref_vector)
            
            # Cancel echo
            error = input_signal[i] - echo_estimate
            output[i] = error
            
            # Update filter weights (NLMS algorithm)
            ref_power = np.dot(ref_vector, ref_vector) + 1e-10
            self.weights += (self.step_size * error * ref_vector) / ref_power
            
            # Track error for adaptation
            self.error_buffer.append(abs(error))
            
        return output
        
    def reset(self):
        """Reset echo canceller state"""
        self.weights.fill(0)
        self.reference_buffer.clear()
        self.error_buffer.clear()


class NoiseSupressor:
    """Advanced noise suppression using spectral subtraction"""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.frame_size = 512
        self.overlap = 0.5
        self.noise_profile = None
        self.alpha = 2.0  # Over-subtraction factor
        self.beta = 0.1   # Spectral floor
        
    def estimate_noise(self, signal: np.ndarray, duration: float = 1.0):
        """Estimate noise profile from signal"""
        # Use first 'duration' seconds as noise reference
        noise_samples = int(self.sample_rate * duration)
        noise_signal = signal[:noise_samples]
        
        # Compute noise spectrum
        _, _, Sxx = signal.spectrogram(
            noise_signal,
            fs=self.sample_rate,
            window='hann',
            nperseg=self.frame_size,
            noverlap=int(self.frame_size * self.overlap)
        )
        
        # Average noise spectrum
        self.noise_profile = np.mean(Sxx, axis=1)
        
    def process(self, signal: np.ndarray) -> np.ndarray:
        """Apply noise suppression to signal"""
        if self.noise_profile is None:
            # Auto-estimate noise from beginning
            self.estimate_noise(signal)
            
        # Compute signal spectrum
        f, t, Sxx = signal.spectrogram(
            signal,
            fs=self.sample_rate,
            window='hann',
            nperseg=self.frame_size,
            noverlap=int(self.frame_size * self.overlap)
        )
        
        # Spectral subtraction
        magnitude = np.sqrt(Sxx)
        phase = np.angle(Sxx)
        
        # Subtract noise with over-subtraction
        clean_magnitude = magnitude - self.alpha * self.noise_profile[:, np.newaxis]
        
        # Apply spectral floor
        clean_magnitude = np.maximum(clean_magnitude, self.beta * magnitude)
        
        # Reconstruct complex spectrum
        clean_spectrum = clean_magnitude * np.exp(1j * phase)
        
        # Inverse STFT
        _, clean_signal = signal.istft(
            clean_spectrum,
            fs=self.sample_rate,
            window='hann',
            nperseg=self.frame_size,
            noverlap=int(self.frame_size * self.overlap)
        )
        
        return clean_signal


class AutoGainControl:
    """Automatic Gain Control (AGC) for consistent audio levels"""
    
    def __init__(self, target_level: float = 0.3, attack_time: float = 0.01,
                 release_time: float = 0.1, sample_rate: int = 16000):
        self.target_level = target_level
        self.attack_time = attack_time
        self.release_time = release_time
        self.sample_rate = sample_rate
        
        # Calculate time constants
        self.attack_coeff = 1.0 - np.exp(-1.0 / (attack_time * sample_rate))
        self.release_coeff = 1.0 - np.exp(-1.0 / (release_time * sample_rate))
        
        self.current_gain = 1.0
        self.envelope = 0.0
        
    def process(self, signal: np.ndarray) -> np.ndarray:
        """Apply AGC to signal"""
        output = np.zeros_like(signal)
        
        for i in range(len(signal)):
            # Update envelope
            sample_abs = abs(signal[i])
            
            if sample_abs > self.envelope:
                # Attack
                self.envelope += self.attack_coeff * (sample_abs - self.envelope)
            else:
                # Release
                self.envelope += self.release_coeff * (sample_abs - self.envelope)
                
            # Calculate gain
            if self.envelope > 0:
                desired_gain = self.target_level / self.envelope
                
                # Smooth gain changes
                if desired_gain < self.current_gain:
                    self.current_gain += self.attack_coeff * (desired_gain - self.current_gain)
                else:
                    self.current_gain += self.release_coeff * (desired_gain - self.current_gain)
                    
                # Limit gain
                self.current_gain = np.clip(self.current_gain, 0.1, 10.0)
                
            # Apply gain
            output[i] = signal[i] * self.current_gain
            
        return np.clip(output, -1.0, 1.0)


class AudioFormatConverter:
    """Convert between different audio formats"""
    
    @staticmethod
    def convert(data: np.ndarray, from_format: AudioFormat, 
                to_format: AudioFormat) -> np.ndarray:
        """Convert audio data between formats"""
        if from_format == to_format:
            return data
            
        # First convert to float32 as intermediate
        if from_format == AudioFormat.INT16:
            float_data = data.astype(np.float32) / 32768.0
        elif from_format == AudioFormat.INT32:
            float_data = data.astype(np.float32) / 2147483648.0
        elif from_format == AudioFormat.FLOAT64:
            float_data = data.astype(np.float32)
        else:
            float_data = data
            
        # Then convert to target format
        if to_format == AudioFormat.INT16:
            return (float_data * 32768.0).astype(np.int16)
        elif to_format == AudioFormat.INT32:
            return (float_data * 2147483648.0).astype(np.int32)
        elif to_format == AudioFormat.FLOAT64:
            return float_data.astype(np.float64)
        else:
            return float_data
            
    @staticmethod
    def resample(data: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
        """Resample audio data"""
        if from_rate == to_rate:
            return data
            
        # Calculate resampling ratio
        ratio = to_rate / from_rate
        
        # Use scipy for resampling
        num_samples = int(len(data) * ratio)
        resampled = signal.resample(data, num_samples)
        
        return resampled


class AudioBuffer:
    """Thread-safe audio buffer with overflow handling"""
    
    def __init__(self, max_size: int, chunk_size: int):
        self.max_size = max_size
        self.chunk_size = chunk_size
        self.buffer = deque(maxlen=max_size // chunk_size)
        self.lock = threading.Lock()
        self.not_empty = threading.Condition(self.lock)
        self.stats = {
            'overflows': 0,
            'underflows': 0,
            'total_samples': 0
        }
        
    def put(self, data: np.ndarray):
        """Add data to buffer"""
        with self.lock:
            if len(self.buffer) >= self.buffer.maxlen:
                self.stats['overflows'] += 1
                # Remove oldest chunk
                self.buffer.popleft()
                
            self.buffer.append(data)
            self.stats['total_samples'] += len(data)
            self.not_empty.notify()
            
    def get(self, timeout: Optional[float] = None) -> Optional[np.ndarray]:
        """Get data from buffer"""
        with self.not_empty:
            if not self.buffer:
                if timeout is None:
                    return None
                    
                self.not_empty.wait(timeout)
                
                if not self.buffer:
                    self.stats['underflows'] += 1
                    return None
                    
            return self.buffer.popleft()
            
    def clear(self):
        """Clear buffer"""
        with self.lock:
            self.buffer.clear()
            
    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics"""
        with self.lock:
            return {
                **self.stats,
                'current_size': len(self.buffer),
                'fill_percentage': (len(self.buffer) / self.buffer.maxlen) * 100
            }


class NexusAudioPipeline:
    """Main audio processing pipeline"""
    
    def __init__(self, config: Optional[AudioStreamConfig] = None):
        self.config = config or AudioStreamConfig()
        self.device_manager = AudioDeviceManager()
        
        # Processing components
        self.echo_canceller = EchoCanceller()
        self.noise_suppressor = NoiseSupressor(self.config.sample_rate)
        self.agc = AutoGainControl(sample_rate=self.config.sample_rate)
        
        # Buffers
        self.input_buffer = AudioBuffer(
            max_size=self.config.sample_rate * 10,  # 10 seconds
            chunk_size=self.config.chunk_size
        )
        self.output_buffer = AudioBuffer(
            max_size=self.config.sample_rate * 10,
            chunk_size=self.config.chunk_size
        )
        
        # Streams
        self.input_stream = None
        self.output_stream = None
        self.duplex_stream = None
        
        # State
        self.is_running = False
        self.websocket_clients = set()
        
        # Callbacks
        self.on_audio_input: Optional[Callable] = None
        self.on_audio_output: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
    def start_input_stream(self):
        """Start audio input stream"""
        def audio_callback(indata, frames, time_info, status):
            if status:
                logger.warning(f"Input stream status: {status}")
                
            # Process audio
            processed = self._process_input(indata[:, 0])
            
            # Add to buffer
            self.input_buffer.put(processed)
            
            # Call callback
            if self.on_audio_input:
                self.on_audio_input(processed)
                
        self.input_stream = sd.InputStream(
            device=self.config.device_id,
            channels=self.config.channels,
            samplerate=self.config.sample_rate,
            blocksize=self.config.chunk_size,
            dtype='float32',
            callback=audio_callback
        )
        
        self.input_stream.start()
        logger.info("Input stream started")
        
    def start_output_stream(self):
        """Start audio output stream"""
        def audio_callback(outdata, frames, time_info, status):
            if status:
                logger.warning(f"Output stream status: {status}")
                
            # Get audio from buffer
            audio = self.output_buffer.get(timeout=0.01)
            
            if audio is not None:
                # Ensure correct size
                if len(audio) < frames:
                    audio = np.pad(audio, (0, frames - len(audio)))
                elif len(audio) > frames:
                    audio = audio[:frames]
                    
                outdata[:, 0] = audio
            else:
                # Output silence
                outdata.fill(0)
                
        self.output_stream = sd.OutputStream(
            device=self.config.device_id,
            channels=self.config.channels,
            samplerate=self.config.sample_rate,
            blocksize=self.config.chunk_size,
            dtype='float32',
            callback=audio_callback
        )
        
        self.output_stream.start()
        logger.info("Output stream started")
        
    def start_duplex_stream(self):
        """Start full-duplex stream for echo cancellation"""
        def audio_callback(indata, outdata, frames, time_info, status):
            if status:
                logger.warning(f"Duplex stream status: {status}")
                
            # Get output audio
            output_audio = self.output_buffer.get(timeout=0.001)
            
            if output_audio is not None:
                # Ensure correct size
                if len(output_audio) < frames:
                    output_audio = np.pad(output_audio, (0, frames - len(output_audio)))
                elif len(output_audio) > frames:
                    output_audio = output_audio[:frames]
                    
                outdata[:, 0] = output_audio
                
                # Process input with echo cancellation
                if self.config.echo_cancellation:
                    processed = self.echo_canceller.process(indata[:, 0], output_audio)
                else:
                    processed = indata[:, 0]
            else:
                outdata.fill(0)
                processed = indata[:, 0]
                
            # Further processing
            processed = self._process_input(processed)
            
            # Add to buffer
            self.input_buffer.put(processed)
            
            # Call callback
            if self.on_audio_input:
                self.on_audio_input(processed)
                
        self.duplex_stream = sd.Stream(
            device=(self.config.device_id, self.config.device_id),
            channels=self.config.channels,
            samplerate=self.config.sample_rate,
            blocksize=self.config.chunk_size,
            dtype='float32',
            callback=audio_callback
        )
        
        self.duplex_stream.start()
        logger.info("Duplex stream started")
        
    def _process_input(self, audio: np.ndarray) -> np.ndarray:
        """Apply input processing pipeline"""
        # Noise suppression
        if self.config.noise_suppression:
            audio = self.noise_suppressor.process(audio)
            
        # AGC
        if self.config.auto_gain_control:
            audio = self.agc.process(audio)
            
        return audio
        
    def start(self, duplex: bool = True):
        """Start audio pipeline"""
        if self.is_running:
            return
            
        self.is_running = True
        
        try:
            if duplex and self.config.echo_cancellation:
                self.start_duplex_stream()
            else:
                self.start_input_stream()
                self.start_output_stream()
                
            # Start device monitoring
            self.device_manager.start_monitoring(self._handle_device_change)
            
        except Exception as e:
            logger.error(f"Failed to start audio pipeline: {e}")
            if self.on_error:
                self.on_error(e)
            self.stop()
            
    def stop(self):
        """Stop audio pipeline"""
        self.is_running = False
        
        # Stop streams
        if self.input_stream:
            self.input_stream.stop()
            self.input_stream.close()
            
        if self.output_stream:
            self.output_stream.stop()
            self.output_stream.close()
            
        if self.duplex_stream:
            self.duplex_stream.stop()
            self.duplex_stream.close()
            
        # Stop device monitoring
        self.device_manager.stop_monitoring()
        
        # Clear buffers
        self.input_buffer.clear()
        self.output_buffer.clear()
        
        logger.info("Audio pipeline stopped")
        
    def _handle_device_change(self, changes: Dict[str, Any]):
        """Handle audio device changes"""
        logger.info(f"Audio device change: {changes}")
        
        if self.is_running:
            # Restart streams with new devices
            self.stop()
            self.start()
            
    def play_audio(self, audio: np.ndarray):
        """Play audio through output stream"""
        # Convert format if needed
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
            
        # Normalize if needed
        if np.max(np.abs(audio)) > 1.0:
            audio = audio / np.max(np.abs(audio))
            
        # Add to output buffer in chunks
        for i in range(0, len(audio), self.config.chunk_size):
            chunk = audio[i:i + self.config.chunk_size]
            self.output_buffer.put(chunk)
            
    def calibrate_noise(self, duration: float = 2.0):
        """Calibrate noise profile"""
        logger.info(f"Calibrating noise for {duration} seconds...")
        
        # Collect noise samples
        samples = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            audio = self.input_buffer.get(timeout=0.1)
            if audio is not None:
                samples.append(audio)
                
        if samples:
            noise_profile = np.concatenate(samples)
            self.noise_suppressor.estimate_noise(noise_profile)
            logger.info("Noise calibration complete")
            
    def get_audio_level(self) -> float:
        """Get current audio input level"""
        audio = self.input_buffer.get(timeout=0.01)
        
        if audio is not None:
            # Put it back
            self.input_buffer.put(audio)
            
            # Calculate RMS level
            rms = np.sqrt(np.mean(audio**2))
            return float(rms)
            
        return 0.0
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        return {
            'is_running': self.is_running,
            'input_buffer': self.input_buffer.get_stats(),
            'output_buffer': self.output_buffer.get_stats(),
            'current_level': self.get_audio_level(),
            'devices': {
                'input': self.device_manager.current_input.name if self.device_manager.current_input else None,
                'output': self.device_manager.current_output.name if self.device_manager.current_output else None
            }
        }
        
    async def start_websocket_server(self, host: str = 'localhost', port: int = 8765):
        """Start WebSocket server for audio streaming"""
        async def handle_client(websocket, path):
            """Handle WebSocket client"""
            self.websocket_clients.add(websocket)
            logger.info(f"WebSocket client connected: {websocket.remote_address}")
            
            try:
                # Send configuration
                await websocket.send(json.dumps({
                    'type': 'config',
                    'sample_rate': self.config.sample_rate,
                    'channels': self.config.channels,
                    'format': self.config.format.value
                }))
                
                # Handle messages
                async for message in websocket:
                    data = json.loads(message)
                    
                    if data['type'] == 'audio':
                        # Decode audio
                        audio_bytes = base64.b64decode(data['audio'])
                        audio = np.frombuffer(audio_bytes, dtype=np.float32)
                        
                        # Process and play
                        self.play_audio(audio)
                        
                    elif data['type'] == 'command':
                        # Handle commands
                        await self._handle_websocket_command(websocket, data)
                        
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                self.websocket_clients.remove(websocket)
                logger.info(f"WebSocket client disconnected: {websocket.remote_address}")
                
        # Start server
        server = await websockets.serve(handle_client, host, port)
        logger.info(f"WebSocket server started on ws://{host}:{port}")
        
        # Stream audio to clients
        asyncio.create_task(self._stream_to_websocket_clients())
        
        return server
        
    async def _stream_to_websocket_clients(self):
        """Stream audio to WebSocket clients"""
        while self.is_running:
            audio = self.input_buffer.get(timeout=0.1)
            
            if audio is not None and self.websocket_clients:
                # Encode audio
                audio_bytes = audio.astype(np.float32).tobytes()
                audio_b64 = base64.b64encode(audio_bytes).decode()
                
                # Send to all clients
                message = json.dumps({
                    'type': 'audio',
                    'audio': audio_b64,
                    'timestamp': time.time()
                })
                
                disconnected = set()
                
                for client in self.websocket_clients:
                    try:
                        await client.send(message)
                    except:
                        disconnected.add(client)
                        
                # Remove disconnected clients
                self.websocket_clients -= disconnected
                
            await asyncio.sleep(0.01)
            
    async def _handle_websocket_command(self, websocket, data: Dict[str, Any]):
        """Handle WebSocket command"""
        command = data.get('command')
        
        if command == 'get_devices':
            devices = [
                {
                    'id': d.id,
                    'name': d.name,
                    'type': d.type.value,
                    'channels': d.channels
                }
                for d in self.device_manager.get_devices()
            ]
            
            await websocket.send(json.dumps({
                'type': 'devices',
                'devices': devices
            }))
            
        elif command == 'set_device':
            device_id = data.get('device_id')
            device_type = DeviceType(data.get('device_type'))
            
            try:
                self.device_manager.set_device(device_id, device_type)
                await websocket.send(json.dumps({
                    'type': 'success',
                    'message': f'Device set to {device_id}'
                }))
            except Exception as e:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': str(e)
                }))
                
        elif command == 'get_stats':
            stats = self.get_statistics()
            await websocket.send(json.dumps({
                'type': 'stats',
                'stats': stats
            }))


# Fallback mechanisms
class FallbackAudioHandler:
    """Handle audio processing failures with fallbacks"""
    
    def __init__(self):
        self.fallback_chain = [
            self._try_sounddevice,
            self._try_pyaudio,
            self._try_file_based
        ]
        
    async def process_with_fallback(self, audio_processor: Callable, 
                                   audio_data: np.ndarray) -> Optional[np.ndarray]:
        """Process audio with fallback mechanisms"""
        for fallback in self.fallback_chain:
            try:
                result = await fallback(audio_processor, audio_data)
                if result is not None:
                    return result
            except Exception as e:
                logger.warning(f"Fallback failed: {e}")
                continue
                
        logger.error("All fallback mechanisms failed")
        return None
        
    async def _try_sounddevice(self, processor: Callable, data: np.ndarray) -> np.ndarray:
        """Try processing with sounddevice"""
        return processor(data)
        
    async def _try_pyaudio(self, processor: Callable, data: np.ndarray) -> np.ndarray:
        """Try processing with PyAudio"""
        # Convert to PyAudio format and process
        return processor(data)
        
    async def _try_file_based(self, processor: Callable, data: np.ndarray) -> np.ndarray:
        """Fallback to file-based processing"""
        # Save to temporary file, process, and load
        temp_file = Path("/tmp/nexus_audio_temp.wav")
        sf.write(temp_file, data, 16000)
        
        # Process file
        processed_data, _ = sf.read(temp_file)
        
        # Clean up
        temp_file.unlink()
        
        return processed_data


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Create audio pipeline
        config = AudioStreamConfig(
            sample_rate=16000,
            channels=1,
            echo_cancellation=True,
            noise_suppression=True,
            auto_gain_control=True
        )
        
        pipeline = NexusAudioPipeline(config)
        
        # Set up callbacks
        def on_audio_input(audio):
            level = np.sqrt(np.mean(audio**2))
            print(f"Audio level: {level:.3f}")
            
        pipeline.on_audio_input = on_audio_input
        
        # List devices
        print("Available audio devices:")
        for device in pipeline.device_manager.get_devices():
            print(f"  [{device.id}] {device.name} ({device.type.value})")
            
        # Start pipeline
        pipeline.start(duplex=True)
        
        # Calibrate noise
        pipeline.calibrate_noise()
        
        # Start WebSocket server
        server = await pipeline.start_websocket_server()
        
        print("Audio pipeline running. Press Ctrl+C to stop.")
        
        try:
            # Keep running
            while True:
                stats = pipeline.get_statistics()
                print(f"Stats: Level={stats['current_level']:.3f}, "
                      f"Input buffer={stats['input_buffer']['fill_percentage']:.1f}%")
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\nStopping...")
            
        finally:
            pipeline.stop()
            server.close()
            await server.wait_closed()
            
    # Run example
    asyncio.run(main())