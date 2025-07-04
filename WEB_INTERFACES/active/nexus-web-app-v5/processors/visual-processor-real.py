"""
Visual Processor with Real Computer Vision
Implements YOLO, face detection, emotion recognition, and consciousness calculations
"""

import cv2
import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image
import face_recognition
from deepface import DeepFace
import mediapipe as mp
from collections import deque
import threading
import queue
import time
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmotionState(Enum):
    """Emotion states detected from facial analysis"""
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEAR = "fear"
    SURPRISE = "surprise"
    NEUTRAL = "neutral"
    DISGUST = "disgust"


@dataclass
class VisualConsciousnessData:
    """Container for visual consciousness metrics"""
    complexity_score: float
    object_diversity: float
    face_presence: float
    emotion_intensity: float
    motion_dynamics: float
    color_richness: float
    spatial_coherence: float
    temporal_stability: float
    overall_consciousness: float
    detected_objects: List[Dict[str, Any]]
    detected_faces: List[Dict[str, Any]]
    scene_attributes: Dict[str, Any]


class VisualProcessor:
    """Real-time visual processing with consciousness calculations"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize visual processor with models and configurations"""
        self.config = self._load_config(config_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize models
        self._init_yolo()
        self._init_face_detection()
        self._init_pose_detection()
        
        # Processing state
        self.frame_buffer = deque(maxlen=30)  # 1 second at 30fps
        self.processing_queue = queue.Queue(maxsize=100)
        self.results_queue = queue.Queue(maxsize=100)
        
        # Consciousness calculation parameters
        self.consciousness_weights = {
            'complexity': 0.20,
            'diversity': 0.15,
            'faces': 0.20,
            'emotion': 0.15,
            'motion': 0.10,
            'color': 0.10,
            'spatial': 0.05,
            'temporal': 0.05
        }
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._process_frames)
        self.processing_thread.daemon = True
        self.is_running = False
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults"""
        default_config = {
            "yolo_model": "yolov5s",
            "confidence_threshold": 0.5,
            "nms_threshold": 0.4,
            "max_faces": 10,
            "emotion_model": "deepface",
            "enable_pose": True,
            "frame_skip": 2,
            "buffer_size": 30
        }
        
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config.get('visual_processor', {}))
            except Exception as e:
                logger.warning(f"Could not load config: {e}, using defaults")
                
        return default_config
    
    def _init_yolo(self):
        """Initialize YOLO object detection model"""
        try:
            # Use YOLOv5 from ultralytics
            self.yolo_model = torch.hub.load('ultralytics/yolov5', 
                                           self.config['yolo_model'], 
                                           pretrained=True)
            self.yolo_model.to(self.device)
            self.yolo_model.eval()
            
            # Get class names
            self.class_names = self.yolo_model.names
            logger.info("YOLO model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.yolo_model = None
    
    def _init_face_detection(self):
        """Initialize face detection and emotion recognition"""
        try:
            # MediaPipe face detection for real-time performance
            self.mp_face_detection = mp.solutions.face_detection
            self.face_detector = self.mp_face_detection.FaceDetection(
                model_selection=1, 
                min_detection_confidence=0.5
            )
            
            # Face mesh for detailed facial landmarks
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=self.config['max_faces'],
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            logger.info("Face detection models loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load face detection: {e}")
            self.face_detector = None
    
    def _init_pose_detection(self):
        """Initialize pose detection for body language analysis"""
        if not self.config['enable_pose']:
            self.pose_detector = None
            return
            
        try:
            self.mp_pose = mp.solutions.pose
            self.pose_detector = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                enable_segmentation=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            logger.info("Pose detection model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load pose detection: {e}")
            self.pose_detector = None
    
    def start(self):
        """Start the visual processing thread"""
        self.is_running = True
        self.processing_thread.start()
        logger.info("Visual processor started")
    
    def stop(self):
        """Stop the visual processing thread"""
        self.is_running = False
        self.processing_thread.join()
        logger.info("Visual processor stopped")
    
    def process_frame(self, frame: np.ndarray) -> VisualConsciousnessData:
        """Process a single frame and return consciousness data"""
        # Add frame to buffer for temporal analysis
        self.frame_buffer.append(frame)
        
        # Detect objects
        objects = self._detect_objects(frame)
        
        # Detect and analyze faces
        faces = self._detect_faces(frame)
        
        # Analyze scene attributes
        scene_attrs = self._analyze_scene(frame)
        
        # Calculate motion dynamics
        motion_score = self._calculate_motion()
        
        # Calculate consciousness scores
        consciousness_data = self._calculate_consciousness(
            objects, faces, scene_attrs, motion_score
        )
        
        return consciousness_data
    
    def _detect_objects(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect objects using YOLO"""
        if self.yolo_model is None:
            return []
        
        try:
            # Run inference
            results = self.yolo_model(frame)
            
            # Parse detections
            detections = []
            for *box, conf, cls in results.xyxy[0]:
                if conf > self.config['confidence_threshold']:
                    x1, y1, x2, y2 = [int(x) for x in box]
                    detections.append({
                        'class': self.class_names[int(cls)],
                        'confidence': float(conf),
                        'bbox': [x1, y1, x2, y2],
                        'center': [(x1+x2)//2, (y1+y2)//2],
                        'area': (x2-x1) * (y2-y1)
                    })
            
            return detections
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return []
    
    def _detect_faces(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect faces and analyze emotions"""
        if self.face_detector is None:
            return []
        
        faces_data = []
        
        try:
            # Convert to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect faces with MediaPipe
            results = self.face_detector.process(rgb_frame)
            
            if results.detections:
                for detection in results.detections:
                    # Get bounding box
                    bbox = detection.location_data.relative_bounding_box
                    h, w = frame.shape[:2]
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)
                    
                    # Crop face for emotion analysis
                    face_roi = frame[y:y+height, x:x+width]
                    
                    # Analyze emotion
                    emotion_data = self._analyze_emotion(face_roi)
                    
                    # Get facial landmarks
                    landmarks = self._get_facial_landmarks(rgb_frame, [x, y, width, height])
                    
                    faces_data.append({
                        'bbox': [x, y, width, height],
                        'confidence': detection.score[0],
                        'emotion': emotion_data,
                        'landmarks': landmarks,
                        'attention_score': self._calculate_attention_score(detection)
                    })
            
            return faces_data
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            return []
    
    def _analyze_emotion(self, face_roi: np.ndarray) -> Dict[str, Any]:
        """Analyze emotion from face ROI"""
        try:
            if face_roi.size == 0:
                return {'dominant': 'neutral', 'scores': {}}
            
            # Use DeepFace for emotion analysis
            result = DeepFace.analyze(
                face_roi, 
                actions=['emotion'], 
                enforce_detection=False
            )
            
            if isinstance(result, list):
                result = result[0]
            
            return {
                'dominant': result.get('dominant_emotion', 'neutral'),
                'scores': result.get('emotion', {}),
                'intensity': max(result.get('emotion', {}).values()) if result.get('emotion') else 0
            }
        except Exception as e:
            logger.debug(f"Emotion analysis failed: {e}")
            return {'dominant': 'neutral', 'scores': {}, 'intensity': 0}
    
    def _get_facial_landmarks(self, frame: np.ndarray, bbox: List[int]) -> Dict[str, Any]:
        """Extract facial landmarks for detailed analysis"""
        try:
            results = self.face_mesh.process(frame)
            
            if results.multi_face_landmarks:
                # Get landmarks for the face closest to bbox
                landmarks = results.multi_face_landmarks[0]
                
                # Extract key points
                key_points = {
                    'left_eye': self._get_landmark_coords(landmarks, 33),
                    'right_eye': self._get_landmark_coords(landmarks, 133),
                    'nose_tip': self._get_landmark_coords(landmarks, 1),
                    'mouth_center': self._get_landmark_coords(landmarks, 13),
                    'chin': self._get_landmark_coords(landmarks, 152)
                }
                
                return key_points
            
            return {}
        except Exception as e:
            logger.debug(f"Landmark extraction failed: {e}")
            return {}
    
    def _get_landmark_coords(self, landmarks, idx: int) -> Tuple[int, int]:
        """Get normalized landmark coordinates"""
        landmark = landmarks.landmark[idx]
        return (landmark.x, landmark.y)
    
    def _analyze_scene(self, frame: np.ndarray) -> Dict[str, Any]:
        """Analyze overall scene attributes"""
        # Color analysis
        color_stats = self._analyze_colors(frame)
        
        # Edge detection for complexity
        edges = cv2.Canny(frame, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Brightness and contrast
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        contrast = np.std(gray)
        
        # Detect dominant scene type
        scene_type = self._classify_scene(frame)
        
        return {
            'color_stats': color_stats,
            'edge_density': edge_density,
            'brightness': brightness,
            'contrast': contrast,
            'scene_type': scene_type,
            'complexity': edge_density * contrast / 255
        }
    
    def _analyze_colors(self, frame: np.ndarray) -> Dict[str, Any]:
        """Analyze color distribution and richness"""
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Calculate color histogram
        hist_h = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [256], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], None, [256], [0, 256])
        
        # Color diversity (entropy)
        hist_h_norm = hist_h / np.sum(hist_h)
        color_entropy = -np.sum(hist_h_norm * np.log2(hist_h_norm + 1e-7))
        
        # Dominant colors
        dominant_hue = np.argmax(hist_h)
        saturation_mean = np.mean(hsv[:, :, 1])
        value_mean = np.mean(hsv[:, :, 2])
        
        return {
            'color_entropy': float(color_entropy),
            'dominant_hue': int(dominant_hue),
            'saturation': float(saturation_mean),
            'brightness': float(value_mean),
            'vibrancy': float(saturation_mean * value_mean / 255)
        }
    
    def _classify_scene(self, frame: np.ndarray) -> str:
        """Classify the type of scene"""
        # Simple scene classification based on detected objects
        # In a real implementation, you'd use a scene classification model
        
        if hasattr(self, '_last_objects'):
            object_classes = [obj['class'] for obj in self._last_objects]
            
            # Simple heuristics
            if any(cls in ['person', 'face'] for cls in object_classes):
                return 'people'
            elif any(cls in ['car', 'truck', 'bus'] for cls in object_classes):
                return 'street'
            elif any(cls in ['cat', 'dog', 'bird'] for cls in object_classes):
                return 'animals'
            elif any(cls in ['tree', 'plant'] for cls in object_classes):
                return 'nature'
        
        return 'general'
    
    def _calculate_motion(self) -> float:
        """Calculate motion dynamics from frame buffer"""
        if len(self.frame_buffer) < 2:
            return 0.0
        
        try:
            # Calculate optical flow between recent frames
            prev_gray = cv2.cvtColor(self.frame_buffer[-2], cv2.COLOR_BGR2GRAY)
            curr_gray = cv2.cvtColor(self.frame_buffer[-1], cv2.COLOR_BGR2GRAY)
            
            # Dense optical flow
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, curr_gray, None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )
            
            # Calculate motion magnitude
            magnitude = np.sqrt(flow[:, :, 0]**2 + flow[:, :, 1]**2)
            motion_score = np.mean(magnitude)
            
            # Normalize to 0-1 range
            return min(motion_score / 10.0, 1.0)
        except Exception as e:
            logger.debug(f"Motion calculation failed: {e}")
            return 0.0
    
    def _calculate_attention_score(self, detection) -> float:
        """Calculate attention score for a face detection"""
        # Based on face size, position, and confidence
        bbox = detection.location_data.relative_bounding_box
        
        # Larger faces get higher scores
        size_score = bbox.width * bbox.height
        
        # Centered faces get higher scores
        center_x = bbox.xmin + bbox.width / 2
        center_y = bbox.ymin + bbox.height / 2
        center_distance = np.sqrt((center_x - 0.5)**2 + (center_y - 0.5)**2)
        position_score = 1 - center_distance
        
        # Combine with confidence
        confidence = detection.score[0]
        
        return (size_score * 0.4 + position_score * 0.3 + confidence * 0.3)
    
    def _calculate_consciousness(self, objects: List[Dict], faces: List[Dict], 
                               scene_attrs: Dict, motion_score: float) -> VisualConsciousnessData:
        """Calculate visual consciousness scores"""
        # Store objects for scene classification
        self._last_objects = objects
        
        # Complexity score based on scene attributes
        complexity_score = scene_attrs['complexity']
        
        # Object diversity
        unique_classes = len(set(obj['class'] for obj in objects))
        diversity_score = min(unique_classes / 10.0, 1.0)
        
        # Face presence and engagement
        face_score = min(len(faces) / 3.0, 1.0) if faces else 0.0
        
        # Emotion intensity
        emotion_scores = []
        for face in faces:
            if 'emotion' in face and 'intensity' in face['emotion']:
                emotion_scores.append(face['emotion']['intensity'])
        emotion_intensity = np.mean(emotion_scores) if emotion_scores else 0.0
        
        # Color richness
        color_richness = scene_attrs['color_stats']['color_entropy'] / 7.0  # Normalize
        
        # Spatial coherence (based on object arrangement)
        spatial_score = self._calculate_spatial_coherence(objects)
        
        # Temporal stability (low motion = high stability)
        temporal_score = 1.0 - motion_score
        
        # Calculate overall consciousness
        overall = (
            self.consciousness_weights['complexity'] * complexity_score +
            self.consciousness_weights['diversity'] * diversity_score +
            self.consciousness_weights['faces'] * face_score +
            self.consciousness_weights['emotion'] * emotion_intensity +
            self.consciousness_weights['motion'] * motion_score +
            self.consciousness_weights['color'] * color_richness +
            self.consciousness_weights['spatial'] * spatial_score +
            self.consciousness_weights['temporal'] * temporal_score
        )
        
        return VisualConsciousnessData(
            complexity_score=complexity_score,
            object_diversity=diversity_score,
            face_presence=face_score,
            emotion_intensity=emotion_intensity,
            motion_dynamics=motion_score,
            color_richness=color_richness,
            spatial_coherence=spatial_score,
            temporal_stability=temporal_score,
            overall_consciousness=overall,
            detected_objects=objects,
            detected_faces=faces,
            scene_attributes=scene_attrs
        )
    
    def _calculate_spatial_coherence(self, objects: List[Dict]) -> float:
        """Calculate how coherently objects are arranged in space"""
        if len(objects) < 2:
            return 1.0
        
        # Calculate pairwise distances between objects
        distances = []
        for i in range(len(objects)):
            for j in range(i + 1, len(objects)):
                center1 = objects[i]['center']
                center2 = objects[j]['center']
                dist = np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)
                distances.append(dist)
        
        if not distances:
            return 1.0
        
        # Lower variance in distances = higher coherence
        variance = np.var(distances)
        max_variance = 1000  # Empirical max
        coherence = 1.0 - min(variance / max_variance, 1.0)
        
        return coherence
    
    def _process_frames(self):
        """Main processing loop running in separate thread"""
        while self.is_running:
            try:
                # Get frame from queue with timeout
                frame = self.processing_queue.get(timeout=0.1)
                
                # Process frame
                result = self.process_frame(frame)
                
                # Put result in output queue
                self.results_queue.put(result)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Frame processing error: {e}")
    
    def stream_process(self, video_source=0):
        """Process video stream in real-time"""
        cap = cv2.VideoCapture(video_source)
        
        if not cap.isOpened():
            logger.error("Failed to open video source")
            return
        
        self.start()
        frame_count = 0
        
        try:
            while self.is_running:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Skip frames based on config
                if frame_count % self.config['frame_skip'] == 0:
                    # Add frame to processing queue
                    try:
                        self.processing_queue.put_nowait(frame)
                    except queue.Full:
                        logger.warning("Processing queue full, skipping frame")
                
                # Get latest results
                try:
                    result = self.results_queue.get_nowait()
                    # Visualize results
                    vis_frame = self._visualize_results(frame, result)
                    cv2.imshow('Nexus Visual Processor', vis_frame)
                except queue.Empty:
                    cv2.imshow('Nexus Visual Processor', frame)
                
                frame_count += 1
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.stop()
    
    def _visualize_results(self, frame: np.ndarray, 
                          result: VisualConsciousnessData) -> np.ndarray:
        """Visualize processing results on frame"""
        vis_frame = frame.copy()
        
        # Draw object detections
        for obj in result.detected_objects:
            x1, y1, x2, y2 = obj['bbox']
            cv2.rectangle(vis_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{obj['class']}: {obj['confidence']:.2f}"
            cv2.putText(vis_frame, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Draw face detections with emotions
        for face in result.detected_faces:
            x, y, w, h = face['bbox']
            cv2.rectangle(vis_frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            if 'emotion' in face:
                emotion = face['emotion']['dominant']
                cv2.putText(vis_frame, emotion, (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        # Draw consciousness metrics
        metrics_text = [
            f"Overall Consciousness: {result.overall_consciousness:.2f}",
            f"Complexity: {result.complexity_score:.2f}",
            f"Diversity: {result.object_diversity:.2f}",
            f"Emotion: {result.emotion_intensity:.2f}",
            f"Motion: {result.motion_dynamics:.2f}"
        ]
        
        y_offset = 30
        for text in metrics_text:
            cv2.putText(vis_frame, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_offset += 20
        
        return vis_frame
    
    def process_image(self, image_path: str) -> VisualConsciousnessData:
        """Process a single image file"""
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        return self.process_frame(image)
    
    def get_biometric_signature(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """Extract biometric signature from face for authentication"""
        try:
            # Get face encoding using face_recognition
            face_encodings = face_recognition.face_encodings(face_image)
            
            if face_encodings:
                return face_encodings[0]
            
            return None
        except Exception as e:
            logger.error(f"Biometric extraction failed: {e}")
            return None


# Example usage
if __name__ == "__main__":
    # Create processor
    processor = VisualProcessor()
    
    # Process video stream
    processor.stream_process(0)  # Use webcam