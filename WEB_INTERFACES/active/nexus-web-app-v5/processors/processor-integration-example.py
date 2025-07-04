"""
Processor Integration Example
Shows how to use visual and auditory processors together for consciousness analysis
"""

import asyncio
import numpy as np
from pathlib import Path
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import cv2
import sounddevice as sd

# Import our processors
from visual_processor_real import VisualProcessor, VisualConsciousnessData
from auditory_processor_real import AudioProcessor, AudioConsciousnessData
from ml_model_loader import get_model_loader, ModelPriority

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CombinedConsciousnessData:
    """Combined consciousness data from all sensors"""
    visual: Optional[VisualConsciousnessData]
    auditory: Optional[AudioConsciousnessData]
    combined_score: float
    timestamp: float
    biometric_match: Optional[Dict[str, Any]]
    succession_ready: bool


class ConsciousnessIntegrator:
    """Integrates visual and auditory processors for unified consciousness analysis"""
    
    def __init__(self, config_path: str = "processor-config.json"):
        """Initialize the integrator with processors"""
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Initialize model loader
        self.model_loader = get_model_loader(config_path=config_path)
        
        # Pre-load essential models
        logger.info("Pre-loading models...")
        essential_models = ["yolov5s", "wav2vec2_base", "deepface_emotion"]
        self.model_loader.preload_models(essential_models)
        
        # Initialize processors
        self.visual_processor = VisualProcessor(config_path)
        self.audio_processor = AudioProcessor(config_path)
        
        # Consciousness fusion weights
        self.fusion_config = self.config['integration']['consciousness_aggregation']
        
        # Biometric database for succession
        self.biometric_database = {}
        
        # Results storage
        self.consciousness_history = []
        
    async def start(self):
        """Start all processors"""
        logger.info("Starting consciousness integration system...")
        
        # Start processors in their threads
        self.visual_processor.start()
        self.audio_processor.start()
        
        logger.info("All processors started successfully")
    
    async def stop(self):
        """Stop all processors"""
        logger.info("Stopping consciousness integration system...")
        
        self.visual_processor.stop()
        self.audio_processor.stop()
        
        logger.info("All processors stopped")
    
    def process_multimodal(self, video_frame: np.ndarray, 
                          audio_chunk: np.ndarray) -> CombinedConsciousnessData:
        """Process visual and audio data simultaneously"""
        import time
        
        # Process visual data
        visual_result = None
        if video_frame is not None and self.config['integration']['enable_visual']:
            visual_result = self.visual_processor.process_frame(video_frame)
        
        # Process audio data
        audio_result = None
        if audio_chunk is not None and self.config['integration']['enable_auditory']:
            audio_result = self.audio_processor.process_audio_chunk(audio_chunk)
        
        # Calculate combined consciousness
        combined_score = self._calculate_combined_consciousness(visual_result, audio_result)
        
        # Check biometric authentication for succession
        biometric_match = None
        succession_ready = False
        
        if visual_result and visual_result.detected_faces:
            # Extract face biometric
            face_biometric = self._extract_face_biometric(video_frame, visual_result)
            
            if audio_result and audio_result.voice_signatures:
                # Combined biometric check
                biometric_match = self._check_biometric_match(
                    face_biometric, 
                    audio_result.voice_signatures[0]
                )
                
                succession_ready = self._check_succession_readiness(biometric_match)
        
        # Create combined result
        result = CombinedConsciousnessData(
            visual=visual_result,
            auditory=audio_result,
            combined_score=combined_score,
            timestamp=time.time(),
            biometric_match=biometric_match,
            succession_ready=succession_ready
        )
        
        # Store in history
        self.consciousness_history.append(result)
        
        return result
    
    def _calculate_combined_consciousness(self, 
                                        visual: Optional[VisualConsciousnessData],
                                        auditory: Optional[AudioConsciousnessData]) -> float:
        """Calculate combined consciousness score"""
        scores = []
        weights = []
        
        if visual:
            scores.append(visual.overall_consciousness)
            weights.append(self.fusion_config['visual_weight'])
        
        if auditory:
            scores.append(auditory.overall_consciousness)
            weights.append(self.fusion_config['auditory_weight'])
        
        if not scores:
            return 0.0
        
        # Normalize weights
        total_weight = sum(weights)
        weights = [w/total_weight for w in weights]
        
        # Weighted average
        combined = sum(s * w for s, w in zip(scores, weights))
        
        # Apply temporal smoothing if we have history
        if len(self.consciousness_history) > 0:
            # Get recent scores
            window_size = int(self.fusion_config['temporal_window'])
            recent_scores = [
                h.combined_score for h in self.consciousness_history[-window_size:]
            ]
            
            # Exponential moving average
            alpha = 0.3
            smoothed = combined
            for score in reversed(recent_scores):
                smoothed = alpha * smoothed + (1 - alpha) * score
            
            combined = smoothed
        
        return combined
    
    def _extract_face_biometric(self, frame: np.ndarray, 
                               visual_result: VisualConsciousnessData) -> Optional[np.ndarray]:
        """Extract face biometric from detected faces"""
        if not visual_result.detected_faces:
            return None
        
        # Get the most prominent face
        face = max(visual_result.detected_faces, 
                  key=lambda f: f.get('attention_score', 0))
        
        # Extract biometric signature
        x, y, w, h = face['bbox']
        face_image = frame[y:y+h, x:x+w]
        
        return self.visual_processor.get_biometric_signature(face_image)
    
    def _check_biometric_match(self, face_signature: Optional[np.ndarray],
                              voice_signature: Optional[np.ndarray]) -> Dict[str, Any]:
        """Check biometric match for succession protocol"""
        if face_signature is None or voice_signature is None:
            return {"matched": False, "confidence": 0.0}
        
        # Check against enrolled biometrics
        best_match = None
        best_score = 0.0
        
        for user_id, bio_data in self.biometric_database.items():
            # Face matching
            face_score = 0.0
            if 'face_signature' in bio_data and face_signature is not None:
                face_similarity = np.dot(face_signature, bio_data['face_signature']) / (
                    np.linalg.norm(face_signature) * np.linalg.norm(bio_data['face_signature'])
                )
                face_score = max(0, face_similarity)
            
            # Voice matching
            voice_score = 0.0
            if 'voice_signature' in bio_data and voice_signature is not None:
                voice_similarity = np.dot(voice_signature, bio_data['voice_signature']) / (
                    np.linalg.norm(voice_signature) * np.linalg.norm(bio_data['voice_signature'])
                )
                voice_score = max(0, voice_similarity)
            
            # Combined score
            combined_score = (face_score + voice_score) / 2
            
            if combined_score > best_score:
                best_score = combined_score
                best_match = user_id
        
        threshold = self.config['succession_protocol']['biometric_requirements']['min_confidence']
        
        return {
            "matched": best_score > threshold,
            "confidence": float(best_score),
            "user_id": best_match,
            "face_confidence": float(face_score) if 'face_score' in locals() else 0.0,
            "voice_confidence": float(voice_score) if 'voice_score' in locals() else 0.0
        }
    
    def _check_succession_readiness(self, biometric_match: Dict[str, Any]) -> bool:
        """Check if succession protocol requirements are met"""
        if not biometric_match['matched']:
            return False
        
        # Check confidence levels
        min_confidence = self.config['succession_protocol']['biometric_requirements']['min_confidence']
        
        return (biometric_match['confidence'] >= min_confidence and
                biometric_match['face_confidence'] >= min_confidence * 0.9 and
                biometric_match['voice_confidence'] >= min_confidence * 0.9)
    
    def enroll_biometric(self, user_id: str, video_frames: list, audio_samples: list):
        """Enroll a new user for succession protocol"""
        logger.info(f"Enrolling biometric for user: {user_id}")
        
        # Process multiple samples for robust enrollment
        face_signatures = []
        voice_signatures = []
        
        # Extract face signatures
        for frame in video_frames[:self.config['succession_protocol']['biometric_requirements']['face_samples']]:
            result = self.visual_processor.process_frame(frame)
            if result.detected_faces:
                face_sig = self._extract_face_biometric(frame, result)
                if face_sig is not None:
                    face_signatures.append(face_sig)
        
        # Extract voice signatures
        for audio in audio_samples[:self.config['succession_protocol']['biometric_requirements']['voice_samples']]:
            result = self.audio_processor.process_audio_chunk(audio)
            if result.voice_signatures:
                voice_signatures.extend(result.voice_signatures)
        
        if face_signatures and voice_signatures:
            # Average signatures for robustness
            avg_face_sig = np.mean(face_signatures, axis=0)
            avg_voice_sig = np.mean(voice_signatures, axis=0)
            
            self.biometric_database[user_id] = {
                'face_signature': avg_face_sig,
                'voice_signature': avg_voice_sig,
                'enrollment_time': time.time(),
                'samples_count': {
                    'face': len(face_signatures),
                    'voice': len(voice_signatures)
                }
            }
            
            logger.info(f"Successfully enrolled {user_id}")
            return True
        
        logger.error(f"Failed to enroll {user_id} - insufficient biometric data")
        return False
    
    async def stream_consciousness(self, video_source=0, audio_device=None):
        """Stream consciousness analysis in real-time"""
        await self.start()
        
        # Open video capture
        cap = cv2.VideoCapture(video_source)
        
        # Audio stream parameters
        audio_sample_rate = self.config['auditory_processor']['sample_rate']
        audio_chunk_size = self.config['auditory_processor']['chunk_size']
        
        # Audio buffer
        audio_buffer = []
        
        def audio_callback(indata, frames, time, status):
            """Audio stream callback"""
            if status:
                logger.warning(f"Audio status: {status}")
            audio_buffer.append(indata.copy())
        
        # Start audio stream
        audio_stream = sd.InputStream(
            device=audio_device,
            channels=1,
            samplerate=audio_sample_rate,
            blocksize=audio_chunk_size,
            callback=audio_callback
        )
        
        try:
            audio_stream.start()
            
            while True:
                # Read video frame
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Get audio chunk
                audio_chunk = None
                if audio_buffer:
                    audio_chunk = audio_buffer.pop(0)[:, 0]  # Convert to mono
                
                # Process multimodal data
                result = self.process_multimodal(frame, audio_chunk)
                
                # Visualize results
                vis_frame = self._visualize_consciousness(frame, result)
                cv2.imshow('Nexus Consciousness Integration', vis_frame)
                
                # Display consciousness metrics
                self._display_metrics(result)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                # Small delay to prevent CPU overload
                await asyncio.sleep(0.01)
                
        finally:
            audio_stream.stop()
            cap.release()
            cv2.destroyAllWindows()
            await self.stop()
    
    def _visualize_consciousness(self, frame: np.ndarray, 
                                result: CombinedConsciousnessData) -> np.ndarray:
        """Visualize consciousness data on frame"""
        vis_frame = frame.copy()
        
        # Draw consciousness meter
        meter_height = 200
        meter_width = 30
        meter_x = frame.shape[1] - 50
        meter_y = 50
        
        # Background
        cv2.rectangle(vis_frame, (meter_x, meter_y), 
                     (meter_x + meter_width, meter_y + meter_height),
                     (255, 255, 255), 2)
        
        # Fill based on consciousness level
        fill_height = int(meter_height * result.combined_score)
        fill_y = meter_y + meter_height - fill_height
        
        # Color based on level
        if result.combined_score > 0.7:
            color = (0, 255, 0)  # Green
        elif result.combined_score > 0.4:
            color = (0, 255, 255)  # Yellow
        else:
            color = (0, 0, 255)  # Red
        
        cv2.rectangle(vis_frame, (meter_x, fill_y),
                     (meter_x + meter_width, meter_y + meter_height),
                     color, -1)
        
        # Draw text
        cv2.putText(vis_frame, f"Consciousness: {result.combined_score:.2%}",
                   (meter_x - 200, meter_y - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Succession status
        if result.succession_ready:
            cv2.putText(vis_frame, "SUCCESSION READY",
                       (10, frame.shape[0] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Biometric status
        if result.biometric_match and result.biometric_match['matched']:
            cv2.putText(vis_frame, f"User: {result.biometric_match['user_id']}",
                       (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        return vis_frame
    
    def _display_metrics(self, result: CombinedConsciousnessData):
        """Display detailed metrics"""
        print("\n" + "="*60)
        print(f"Combined Consciousness: {result.combined_score:.3f}")
        
        if result.visual:
            print(f"Visual Consciousness: {result.visual.overall_consciousness:.3f}")
            print(f"  - Objects: {len(result.visual.detected_objects)}")
            print(f"  - Faces: {len(result.visual.detected_faces)}")
        
        if result.auditory:
            print(f"Auditory Consciousness: {result.auditory.overall_consciousness:.3f}")
            print(f"  - Emotions: {len(result.auditory.detected_emotions)}")
            if result.auditory.transcribed_text:
                print(f"  - Speech: {result.auditory.transcribed_text}")
        
        if result.biometric_match:
            print(f"Biometric Match: {result.biometric_match['matched']} "
                  f"(confidence: {result.biometric_match['confidence']:.3f})")
        
        print(f"Succession Ready: {result.succession_ready}")


# Example usage
async def main():
    # Create integrator
    integrator = ConsciousnessIntegrator()
    
    # Example: Enroll a user (would use real video/audio in practice)
    # integrator.enroll_biometric("user_001", video_frames, audio_samples)
    
    # Stream consciousness analysis
    await integrator.stream_consciousness()


if __name__ == "__main__":
    asyncio.run(main())