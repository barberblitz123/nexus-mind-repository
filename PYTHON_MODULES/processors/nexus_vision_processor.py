#!/usr/bin/env python3
"""
NEXUS Vision Processor Module
Enables computer vision capabilities for NEXUS
"""

import asyncio
import json
import os
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime
import numpy as np
import cv2
from PIL import Image
import io
import aiohttp
from fastapi import FastAPI, UploadFile, File, WebSocket, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="NEXUS Vision Processor")

# NEXUS API endpoint
NEXUS_API = os.getenv("NEXUS_API_URL", "http://localhost:8002")

class VisionProcessor:
    def __init__(self):
        self.session = None
        self.screen_capture_enabled = False
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
    async def start(self):
        """Start vision processor"""
        self.session = aiohttp.ClientSession()
        
    async def process_image(self, image_data: bytes) -> Dict[str, Any]:
        """Process an image and extract information"""
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "dimensions": {"width": img.shape[1], "height": img.shape[0]},
            "analysis": {}
        }
        
        # Detect faces
        faces = self.detect_faces(img)
        results["analysis"]["faces"] = len(faces)
        
        # Detect text (OCR)
        text = self.detect_text(img)
        results["analysis"]["text"] = text
        
        # Detect objects
        objects = self.detect_objects(img)
        results["analysis"]["objects"] = objects
        
        # Analyze colors
        colors = self.analyze_colors(img)
        results["analysis"]["dominant_colors"] = colors
        
        return results
        
    def detect_faces(self, img: np.ndarray) -> List[Dict[str, int]]:
        """Detect faces in image"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        return [
            {"x": int(x), "y": int(y), "width": int(w), "height": int(h)}
            for (x, y, w, h) in faces
        ]
        
    def detect_text(self, img: np.ndarray) -> str:
        """Extract text from image using OCR"""
        try:
            import pytesseract
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            text = pytesseract.image_to_string(gray)
            return text.strip()
        except ImportError:
            return "OCR not available (install tesseract)"
        except Exception:
            return ""
            
    def detect_objects(self, img: np.ndarray) -> List[str]:
        """Detect objects in image"""
        # Simple edge detection for now
        # In production, this would use a proper object detection model
        edges = cv2.Canny(img, 100, 200)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        object_count = len([c for c in contours if cv2.contourArea(c) > 100])
        return [f"object_{i}" for i in range(min(object_count, 10))]
        
    def analyze_colors(self, img: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze dominant colors in image"""
        # Convert to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Reshape to list of pixels
        pixels = img_rgb.reshape(-1, 3)
        
        # Simple k-means clustering for dominant colors
        from sklearn.cluster import KMeans
        n_colors = 5
        
        try:
            kmeans = KMeans(n_clusters=n_colors, n_init=10)
            kmeans.fit(pixels)
            
            colors = []
            for color in kmeans.cluster_centers_:
                colors.append({
                    "rgb": [int(c) for c in color],
                    "hex": "#{:02x}{:02x}{:02x}".format(int(color[0]), int(color[1]), int(color[2]))
                })
            return colors
        except:
            # Fallback to average color
            avg_color = np.mean(pixels, axis=0)
            return [{
                "rgb": [int(c) for c in avg_color],
                "hex": "#{:02x}{:02x}{:02x}".format(int(avg_color[0]), int(avg_color[1]), int(avg_color[2]))
            }]
            
    async def capture_screen(self) -> Dict[str, Any]:
        """Capture and analyze screen"""
        try:
            import pyautogui
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            screenshot.save(img_buffer, format='PNG')
            img_data = img_buffer.getvalue()
            
            # Process image
            results = await self.process_image(img_data)
            
            # Add screen-specific info
            results["screen_info"] = {
                "resolution": pyautogui.size(),
                "mouse_position": pyautogui.position()
            }
            
            return results
            
        except ImportError:
            return {"error": "Screen capture not available (install pyautogui)"}
            
    async def process_webcam_frame(self) -> Dict[str, Any]:
        """Process a frame from webcam"""
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            # Convert frame to bytes
            _, buffer = cv2.imencode('.jpg', frame)
            img_data = buffer.tobytes()
            
            # Process image
            return await self.process_image(img_data)
        else:
            return {"error": "Could not capture webcam frame"}
            
    async def send_vision_data(self, vision_data: Dict[str, Any]):
        """Send vision data to NEXUS"""
        try:
            async with self.session.post(
                f"{NEXUS_API}/api/v2/vision/data",
                json=vision_data
            ) as resp:
                return resp.status == 200
        except:
            return False

# Global processor instance
processor = VisionProcessor()

@app.on_event("startup")
async def startup():
    """Start vision processor on app startup"""
    await processor.start()
    
@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    if processor.session:
        await processor.session.close()
        
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "vision_enabled": True}
    
@app.post("/api/vision/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """Analyze uploaded image"""
    contents = await file.read()
    results = await processor.process_image(contents)
    
    # Send to NEXUS if significant
    if results["analysis"].get("faces", 0) > 0 or results["analysis"].get("text"):
        await processor.send_vision_data(results)
        
    return results
    
@app.post("/api/vision/screen")
async def capture_screen():
    """Capture and analyze screen"""
    results = await processor.capture_screen()
    
    # Send to NEXUS
    await processor.send_vision_data(results)
    
    return results
    
@app.post("/api/vision/webcam")
async def capture_webcam():
    """Capture and analyze webcam frame"""
    results = await processor.process_webcam_frame()
    
    # Send to NEXUS
    await processor.send_vision_data(results)
    
    return results
    
@app.websocket("/ws/vision")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time vision streaming"""
    await websocket.accept()
    
    try:
        while True:
            # Receive image data
            data = await websocket.receive_bytes()
            
            # Process image
            results = await processor.process_image(data)
            
            # Send results back
            await websocket.send_json(results)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
        
@app.get("/api/vision/capabilities")
async def get_capabilities():
    """Get available vision capabilities"""
    capabilities = {
        "face_detection": True,
        "text_recognition": True,
        "object_detection": True,
        "color_analysis": True,
        "screen_capture": True,
        "webcam_capture": True,
        "real_time_streaming": True
    }
    
    # Check for optional dependencies
    try:
        import pytesseract
        capabilities["ocr_available"] = True
    except ImportError:
        capabilities["ocr_available"] = False
        
    try:
        import pyautogui
        capabilities["screen_capture_available"] = True
    except ImportError:
        capabilities["screen_capture_available"] = False
        
    return capabilities

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)