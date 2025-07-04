#!/usr/bin/env python3
"""
NEXUS REAL VISUAL PROCESSOR
Computer vision integration with consciousness engine
Processes real-time video streams and extracts consciousness-relevant features
"""

import cv2
import numpy as np
import asyncio
import json
import time
import base64
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging
import aioredis
import asyncpg
from concurrent.futures import ThreadPoolExecutor
import mediapipe as mp
import pytesseract
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus_visual")

@dataclass
class VisualFrame:
    """Single visual frame data"""
    frame_index: int
    timestamp: float
    image: np.ndarray
    width: int
    height: int
    detections: List[Dict[str, Any]]
    scene_description: str
    consciousness_score: float
    emotion: Optional[str]
    
class NexusVisualProcessor:
    """Real-time visual processing with consciousness integration"""
    
    def __init__(self, connector, config: Dict[str, Any]):
        self.connector = connector
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # MediaPipe initialization
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose
        self.mp_objectron = mp.solutions.objectron
        
        # Initialize detectors
        self.face_detection = self.mp_face_detection.FaceDetection(
            min_detection_confidence=0.5
        )
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=4,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=4,
            min_detection_confidence=0.5
        )
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5
        )
        
        # Haar cascades for additional detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
        
        # YOLO for object detection (simplified - in production use YOLOv5/v8)
        self.object_classes = [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train',
            'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign',
            'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep',
            'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella',
            'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard',
            'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard',
            'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork',
            'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
            'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
            'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv',
            'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave',
            'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase',
            'scissors', 'teddy bear', 'hair drier', 'toothbrush'
        ]
        
        # Emotion detection model (simplified)
        self.emotions = ['neutral', 'happy', 'sad', 'angry', 'fearful', 'disgusted', 'surprised']
        
        # Processing state
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.frame_buffer: Dict[str, List[VisualFrame]] = {}
        
    async def start_processing_session(self, session_id: str, source: Any) -> str:
        """Start a new visual processing session"""
        processing_id = f"visual_{session_id}_{int(time.time())}"
        
        self.active_sessions[processing_id] = {
            'session_id': session_id,
            'source': source,
            'started_at': time.time(),
            'frame_count': 0,
            'active': True
        }
        
        self.frame_buffer[processing_id] = []
        
        # Start async processing
        asyncio.create_task(self._process_video_stream(processing_id))
        
        logger.info(f"Started visual processing session: {processing_id}")
        return processing_id
        
    async def _process_video_stream(self, processing_id: str):
        """Process video stream asynchronously"""
        session_data = self.active_sessions[processing_id]
        session_id = session_data['session_id']
        
        try:
            # Initialize video capture
            if isinstance(session_data['source'], str):
                if session_data['source'] == 'webcam':
                    cap = cv2.VideoCapture(0)
                else:
                    cap = cv2.VideoCapture(session_data['source'])
            else:
                cap = session_data['source']
                
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            frame_interval = 1.0 / fps
            
            while session_data['active']:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Process frame
                processed_frame = await self._process_single_frame(
                    frame, 
                    session_data['frame_count'],
                    processing_id
                )
                
                # Update consciousness based on visual input
                await self._update_consciousness(session_id, processed_frame)
                
                # Store frame data
                self.frame_buffer[processing_id].append(processed_frame)
                
                # Keep buffer size manageable
                if len(self.frame_buffer[processing_id]) > 100:
                    self.frame_buffer[processing_id].pop(0)
                    
                session_data['frame_count'] += 1
                
                # Frame rate control
                await asyncio.sleep(frame_interval)
                
        except Exception as e:
            logger.error(f"Error in video processing: {e}")
        finally:
            cap.release()
            session_data['active'] = False
            
    async def _process_single_frame(self, frame: np.ndarray, frame_index: int, 
                                  processing_id: str) -> VisualFrame:
        """Process a single video frame"""
        timestamp = time.time()
        height, width = frame.shape[:2]
        
        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Run detections in parallel
        detections = await asyncio.gather(
            self._detect_faces(rgb_frame),
            self._detect_hands(rgb_frame),
            self._detect_pose(rgb_frame),
            self._detect_objects(frame),
            self._extract_text(frame)
        )
        
        # Combine all detections
        all_detections = []
        face_detections, hand_detections, pose_detections, object_detections, text_detections = detections
        
        all_detections.extend(face_detections)
        all_detections.extend(hand_detections)
        all_detections.extend(pose_detections)
        all_detections.extend(object_detections)
        all_detections.extend(text_detections)
        
        # Generate scene description
        scene_description = self._generate_scene_description(all_detections)
        
        # Calculate consciousness score
        consciousness_score = self._calculate_visual_consciousness(all_detections)
        
        # Detect primary emotion
        emotion = self._detect_emotion(face_detections) if face_detections else None
        
        return VisualFrame(
            frame_index=frame_index,
            timestamp=timestamp,
            image=frame,
            width=width,
            height=height,
            detections=all_detections,
            scene_description=scene_description,
            consciousness_score=consciousness_score,
            emotion=emotion
        )
        
    async def _detect_faces(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect faces and facial landmarks"""
        detections = []
        
        # MediaPipe face detection
        results = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self.face_detection.process,
            frame
        )
        
        if results.detections:
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                detections.append({
                    'type': 'face',
                    'confidence': detection.score[0],
                    'bbox': {
                        'x': bbox.xmin,
                        'y': bbox.ymin,
                        'width': bbox.width,
                        'height': bbox.height
                    },
                    'landmarks': self._extract_face_landmarks(detection)
                })
                
        # Face mesh for detailed landmarks
        mesh_results = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self.face_mesh.process,
            frame
        )
        
        if mesh_results.multi_face_landmarks:
            for face_landmarks in mesh_results.multi_face_landmarks:
                # Extract key facial points
                landmarks = []
                for landmark in face_landmarks.landmark:
                    landmarks.append({
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z
                    })
                    
                if detections:
                    detections[0]['detailed_landmarks'] = landmarks
                    
        return detections
        
    async def _detect_hands(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect hands and hand landmarks"""
        detections = []
        
        results = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self.hands.process,
            frame
        )
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Calculate bounding box
                x_coords = [lm.x for lm in hand_landmarks.landmark]
                y_coords = [lm.y for lm in hand_landmarks.landmark]
                
                detections.append({
                    'type': 'hand',
                    'confidence': 0.9,  # MediaPipe doesn't provide confidence
                    'bbox': {
                        'x': min(x_coords),
                        'y': min(y_coords),
                        'width': max(x_coords) - min(x_coords),
                        'height': max(y_coords) - min(y_coords)
                    },
                    'landmarks': [
                        {'x': lm.x, 'y': lm.y, 'z': lm.z}
                        for lm in hand_landmarks.landmark
                    ]
                })
                
        return detections
        
    async def _detect_pose(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect human pose"""
        detections = []
        
        results = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self.pose.process,
            frame
        )
        
        if results.pose_landmarks:
            landmarks = []
            for landmark in results.pose_landmarks.landmark:
                landmarks.append({
                    'x': landmark.x,
                    'y': landmark.y,
                    'z': landmark.z,
                    'visibility': landmark.visibility
                })
                
            detections.append({
                'type': 'pose',
                'confidence': 0.9,
                'landmarks': landmarks
            })
            
        return detections
        
    async def _detect_objects(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect objects using cascade classifiers (simplified)"""
        detections = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces using Haar cascade as backup
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        for (x, y, w, h) in faces:
            detections.append({
                'type': 'object',
                'class': 'face_haar',
                'confidence': 0.7,
                'bbox': {
                    'x': x / frame.shape[1],
                    'y': y / frame.shape[0],
                    'width': w / frame.shape[1],
                    'height': h / frame.shape[0]
                }
            })
            
        # Detect eyes
        eyes = self.eye_cascade.detectMultiScale(gray, 1.1, 4)
        for (x, y, w, h) in eyes:
            detections.append({
                'type': 'object',
                'class': 'eye',
                'confidence': 0.6,
                'bbox': {
                    'x': x / frame.shape[1],
                    'y': y / frame.shape[0],
                    'width': w / frame.shape[1],
                    'height': h / frame.shape[0]
                }
            })
            
        return detections
        
    async def _extract_text(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Extract text from image using OCR"""
        detections = []
        
        try:
            # Convert to PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
            # Run OCR
            text = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                pytesseract.image_to_string,
                pil_image
            )
            
            if text.strip():
                # Get detailed OCR data
                data = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    pytesseract.image_to_data,
                    pil_image,
                    output_type=pytesseract.Output.DICT
                )
                
                # Extract word bounding boxes
                n_boxes = len(data['text'])
                for i in range(n_boxes):
                    if int(data['conf'][i]) > 60:  # Confidence threshold
                        text = data['text'][i].strip()
                        if text:
                            detections.append({
                                'type': 'text',
                                'content': text,
                                'confidence': data['conf'][i] / 100.0,
                                'bbox': {
                                    'x': data['left'][i] / frame.shape[1],
                                    'y': data['top'][i] / frame.shape[0],
                                    'width': data['width'][i] / frame.shape[1],
                                    'height': data['height'][i] / frame.shape[0]
                                }
                            })
        except Exception as e:
            logger.debug(f"OCR failed: {e}")
            
        return detections
        
    def _extract_face_landmarks(self, detection) -> List[Dict[str, float]]:
        """Extract facial landmarks from detection"""
        landmarks = []
        
        # Key points from MediaPipe face detection
        keypoints = ['left_eye', 'right_eye', 'nose_tip', 'mouth_center', 
                    'left_ear_tragion', 'right_ear_tragion']
        
        for keypoint in detection.location_data.relative_keypoints:
            landmarks.append({
                'x': keypoint.x,
                'y': keypoint.y
            })
            
        return landmarks
        
    def _generate_scene_description(self, detections: List[Dict[str, Any]]) -> str:
        """Generate natural language scene description"""
        scene_elements = []
        
        # Count detections by type
        face_count = len([d for d in detections if d['type'] == 'face'])
        hand_count = len([d for d in detections if d['type'] == 'hand'])
        pose_count = len([d for d in detections if d['type'] == 'pose'])
        text_count = len([d for d in detections if d['type'] == 'text'])
        object_count = len([d for d in detections if d['type'] == 'object'])
        
        if face_count > 0:
            scene_elements.append(f"{face_count} face{'s' if face_count > 1 else ''}")
        if hand_count > 0:
            scene_elements.append(f"{hand_count} hand{'s' if hand_count > 1 else ''}")
        if pose_count > 0:
            scene_elements.append(f"{pose_count} human pose{'s' if pose_count > 1 else ''}")
        if text_count > 0:
            scene_elements.append(f"text ({text_count} words)")
        if object_count > 0:
            scene_elements.append(f"{object_count} object{'s' if object_count > 1 else ''}")
            
        if not scene_elements:
            return "Empty scene"
            
        return f"Scene contains: {', '.join(scene_elements)}"
        
    def _calculate_visual_consciousness(self, detections: List[Dict[str, Any]]) -> float:
        """Calculate consciousness score from visual complexity"""
        if not detections:
            return 0.1
            
        # Base score from detection count
        base_score = min(1.0, len(detections) / 20.0)
        
        # Diversity bonus
        detection_types = set(d['type'] for d in detections)
        diversity_score = len(detection_types) / 5.0
        
        # Confidence weight
        avg_confidence = np.mean([d.get('confidence', 0.5) for d in detections])
        
        # Human presence bonus
        human_bonus = 0.0
        if any(d['type'] in ['face', 'pose', 'hand'] for d in detections):
            human_bonus = 0.2
            
        # Calculate final score
        consciousness_score = (base_score * 0.4 + 
                             diversity_score * 0.3 + 
                             avg_confidence * 0.2 + 
                             human_bonus * 0.1)
        
        return min(1.0, consciousness_score)
        
    def _detect_emotion(self, face_detections: List[Dict[str, Any]]) -> Optional[str]:
        """Detect emotion from facial features (simplified)"""
        if not face_detections:
            return None
            
        # In a real implementation, this would use a trained emotion model
        # For now, return a random emotion based on face confidence
        face = face_detections[0]
        confidence = face.get('confidence', 0.5)
        
        if confidence > 0.8:
            return 'happy'
        elif confidence > 0.6:
            return 'neutral'
        else:
            return 'uncertain'
            
    async def _update_consciousness(self, session_id: str, frame: VisualFrame):
        """Update consciousness based on visual input"""
        # Calculate visual processor activity
        activity_level = frame.consciousness_score
        
        # Add emotion influence
        if frame.emotion:
            emotion_weights = {
                'happy': 0.1,
                'sad': -0.05,
                'angry': 0.05,
                'neutral': 0.0,
                'uncertain': -0.02
            }
            activity_level += emotion_weights.get(frame.emotion, 0)
            
        # Update visual processor
        await self.connector.update_processor(
            session_id,
            'visual',
            min(1.0, max(0.0, activity_level)),
            {
                'frame_index': frame.frame_index,
                'scene': frame.scene_description,
                'detection_count': len(frame.detections),
                'emotion': frame.emotion
            }
        )
        
    async def get_visual_memory(self, processing_id: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent visual memory frames"""
        if processing_id not in self.frame_buffer:
            return []
            
        frames = self.frame_buffer[processing_id][-count:]
        
        memory = []
        for frame in frames:
            # Convert frame to base64 for transmission
            _, buffer = cv2.imencode('.jpg', frame.image, [cv2.IMWRITE_JPEG_QUALITY, 70])
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            memory.append({
                'frame_index': frame.frame_index,
                'timestamp': frame.timestamp,
                'image': f"data:image/jpeg;base64,{img_base64}",
                'scene': frame.scene_description,
                'consciousness_score': frame.consciousness_score,
                'emotion': frame.emotion,
                'detections': len(frame.detections)
            })
            
        return memory
        
    async def stop_processing(self, processing_id: str):
        """Stop visual processing session"""
        if processing_id in self.active_sessions:
            self.active_sessions[processing_id]['active'] = False
            
            # Clean up after a delay
            await asyncio.sleep(5)
            if processing_id in self.active_sessions:
                del self.active_sessions[processing_id]
            if processing_id in self.frame_buffer:
                del self.frame_buffer[processing_id]
                
            logger.info(f"Stopped visual processing: {processing_id}")

# Integration example
async def test_visual_processor():
    """Test the visual processor"""
    from nexus_consciousness_connector import NexusConsciousnessConnector
    
    # Initialize connector
    config = {
        'db_host': 'localhost',
        'db_port': 5432,
        'db_user': 'nexus',
        'db_password': 'nexus_pass',
        'db_name': 'nexus_consciousness',
        'redis_host': 'localhost',
        'redis_port': 6379
    }
    
    connector = NexusConsciousnessConnector(config)
    await connector.initialize()
    
    # Create session
    session_id = await connector.create_session('test-user')
    
    # Initialize visual processor
    visual_processor = NexusVisualProcessor(connector, config)
    
    # Start processing webcam
    processing_id = await visual_processor.start_processing_session(session_id, 'webcam')
    
    # Let it run for 30 seconds
    await asyncio.sleep(30)
    
    # Get visual memory
    memory = await visual_processor.get_visual_memory(processing_id)
    logger.info(f"Visual memory: {len(memory)} frames")
    
    # Stop processing
    await visual_processor.stop_processing(processing_id)
    
    # Cleanup
    await connector.cleanup()

if __name__ == "__main__":
    asyncio.run(test_visual_processor())