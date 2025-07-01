#!/usr/bin/env python3
"""
NEXUS Vision Engine - Core vision processing with OpenAI Vision API
Provides real-time visual analysis and understanding capabilities
"""

import asyncio
import base64
import io
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from PIL import Image, ImageGrab, ImageDraw, ImageFont
import numpy as np
import cv2
import pytesseract
import mss
import openai
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import platform
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VisionResult:
    """Result from vision analysis"""
    analysis_type: str
    content: Dict[str, Any]
    confidence: float
    timestamp: datetime
    image_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class UIElement:
    """Detected UI element"""
    type: str
    bounds: Tuple[int, int, int, int]
    text: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    confidence: float = 0.0

class NexusVisionEngine:
    """Core vision processing engine with OpenAI Vision API integration"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize vision engine"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("No OpenAI API key found. Vision features will be limited.")
        
        self.client = openai.AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.screen_capture = mss.mss()
        self.cache_dir = Path("vision_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Platform-specific setup
        self.platform = platform.system().lower()
        self._setup_platform_specific()
    
    def _setup_platform_specific(self):
        """Setup platform-specific features"""
        if self.platform == "darwin":  # macOS
            # Check for screen recording permission
            try:
                subprocess.run(["tccutil", "check", "ScreenCapture"], check=True)
            except:
                logger.warning("Screen recording permission may be required on macOS")
        elif self.platform == "linux":
            # Check for required tools
            if not self._check_linux_tools():
                logger.warning("Some Linux tools may be missing for full functionality")
    
    def _check_linux_tools(self) -> bool:
        """Check if required Linux tools are available"""
        tools = ["xdotool", "xwininfo", "import"]
        for tool in tools:
            try:
                subprocess.run(["which", tool], check=True, capture_output=True)
            except:
                return False
        return True
    
    async def analyze_image(self, image_path: str, prompt: Optional[str] = None) -> VisionResult:
        """Analyze an image using OpenAI Vision API"""
        if not self.client:
            return await self._fallback_analysis(image_path)
        
        try:
            # Load and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
            
            # Prepare prompt
            if not prompt:
                prompt = """Analyze this image and provide:
                1. Description of what you see
                2. Any text or code visible
                3. UI elements and their layout
                4. Colors and design patterns
                5. Any issues or improvements suggested"""
            
            # Call Vision API
            response = await self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096
            )
            
            # Parse response
            content = response.choices[0].message.content
            analysis = self._parse_vision_response(content)
            
            return VisionResult(
                analysis_type="openai_vision",
                content=analysis,
                confidence=0.95,
                timestamp=datetime.now(),
                image_path=image_path
            )
            
        except Exception as e:
            logger.error(f"Vision API error: {e}")
            return await self._fallback_analysis(image_path)
    
    async def _fallback_analysis(self, image_path: str) -> VisionResult:
        """Fallback analysis using OCR and CV"""
        try:
            # Load image
            image = cv2.imread(image_path)
            pil_image = Image.open(image_path)
            
            # Perform OCR
            text = pytesseract.image_to_string(pil_image)
            data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)
            
            # Basic CV analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Extract UI elements
            ui_elements = self._extract_ui_elements(data, contours)
            
            # Color analysis
            colors = self._analyze_colors(image)
            
            return VisionResult(
                analysis_type="fallback_cv",
                content={
                    "text": text,
                    "ui_elements": ui_elements,
                    "colors": colors,
                    "contours": len(contours)
                },
                confidence=0.7,
                timestamp=datetime.now(),
                image_path=image_path
            )
            
        except Exception as e:
            logger.error(f"Fallback analysis error: {e}")
            return VisionResult(
                analysis_type="error",
                content={"error": str(e)},
                confidence=0.0,
                timestamp=datetime.now(),
                image_path=image_path
            )
    
    def _parse_vision_response(self, content: str) -> Dict[str, Any]:
        """Parse Vision API response into structured data"""
        result = {
            "description": "",
            "text_content": [],
            "code_blocks": [],
            "ui_elements": [],
            "colors": [],
            "suggestions": []
        }
        
        # Extract code blocks
        code_pattern = r"```(\w+)?\n(.*?)```"
        code_matches = re.findall(code_pattern, content, re.DOTALL)
        for lang, code in code_matches:
            result["code_blocks"].append({
                "language": lang or "unknown",
                "code": code.strip()
            })
        
        # Extract sections
        sections = content.split("\n\n")
        for section in sections:
            lower_section = section.lower()
            if "description" in lower_section or "what i see" in lower_section:
                result["description"] = section
            elif "text" in lower_section or "content" in lower_section:
                result["text_content"].append(section)
            elif "ui" in lower_section or "element" in lower_section:
                result["ui_elements"].append(section)
            elif "color" in lower_section or "design" in lower_section:
                result["colors"].append(section)
            elif "suggestion" in lower_section or "improvement" in lower_section:
                result["suggestions"].append(section)
        
        return result
    
    def _extract_ui_elements(self, ocr_data: Dict, contours: List) -> List[UIElement]:
        """Extract UI elements from OCR and contours"""
        elements = []
        
        # Extract text elements
        n_boxes = len(ocr_data['text'])
        for i in range(n_boxes):
            if int(ocr_data['conf'][i]) > 60:  # Confidence threshold
                x, y, w, h = (ocr_data['left'][i], ocr_data['top'][i], 
                             ocr_data['width'][i], ocr_data['height'][i])
                text = ocr_data['text'][i].strip()
                if text:
                    elements.append(UIElement(
                        type="text",
                        bounds=(x, y, x + w, y + h),
                        text=text,
                        confidence=ocr_data['conf'][i] / 100.0
                    ))
        
        # Extract button-like elements from contours
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            if area > 100:  # Filter small elements
                elements.append(UIElement(
                    type="unknown",
                    bounds=(x, y, x + w, y + h),
                    properties={"area": area},
                    confidence=0.5
                ))
        
        return elements
    
    def _analyze_colors(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze dominant colors in image"""
        # Convert to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Reshape to list of pixels
        pixels = rgb_image.reshape(-1, 3)
        
        # Use k-means to find dominant colors
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=5, random_state=42)
        kmeans.fit(pixels)
        
        colors = []
        for center in kmeans.cluster_centers_:
            rgb = tuple(int(c) for c in center)
            hex_color = '#%02x%02x%02x' % rgb
            colors.append({
                "rgb": rgb,
                "hex": hex_color,
                "percentage": 0  # Would need to calculate actual percentage
            })
        
        return colors
    
    async def capture_screen(self, monitor: Optional[int] = None, 
                           region: Optional[Tuple[int, int, int, int]] = None) -> str:
        """Capture screen or region"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.cache_dir / f"capture_{timestamp}.png"
        
        try:
            if region:
                # Capture specific region
                monitor_info = {
                    "left": region[0],
                    "top": region[1],
                    "width": region[2] - region[0],
                    "height": region[3] - region[1]
                }
            else:
                # Capture full monitor
                monitors = self.screen_capture.monitors
                monitor_info = monitors[monitor if monitor else 0]
            
            # Capture
            screenshot = self.screen_capture.grab(monitor_info)
            
            # Save to file
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            img.save(filename)
            
            return str(filename)
            
        except Exception as e:
            logger.error(f"Screen capture error: {e}")
            raise
    
    async def capture_window(self, window_title: str) -> str:
        """Capture specific window"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.cache_dir / f"window_{timestamp}.png"
        
        try:
            if self.platform == "darwin":  # macOS
                # Use screencapture with window ID
                script = f'''
                tell application "System Events"
                    set frontApp to name of first application process whose frontmost is true
                    set windowTitle to "{window_title}"
                    tell process frontApp
                        set windowID to id of window windowTitle
                    end tell
                end tell
                return windowID
                '''
                result = subprocess.run(["osascript", "-e", script], 
                                      capture_output=True, text=True)
                window_id = result.stdout.strip()
                subprocess.run(["screencapture", "-l", window_id, str(filename)])
                
            elif self.platform == "linux":
                # Use xwininfo and import
                result = subprocess.run(["xwininfo", "-name", window_title], 
                                      capture_output=True, text=True)
                window_id = re.search(r"Window id: (0x\w+)", result.stdout)
                if window_id:
                    subprocess.run(["import", "-window", window_id.group(1), str(filename)])
                    
            elif self.platform == "windows":
                # Use Win32 API through ctypes
                import ctypes
                from ctypes import wintypes
                
                # Find window
                hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
                if hwnd:
                    # Get window rect
                    rect = wintypes.RECT()
                    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    
                    # Capture region
                    region = (rect.left, rect.top, rect.right, rect.bottom)
                    return await self.capture_screen(region=region)
            
            return str(filename)
            
        except Exception as e:
            logger.error(f"Window capture error: {e}")
            # Fallback to full screen
            return await self.capture_screen()
    
    async def extract_text_with_layout(self, image_path: str) -> Dict[str, Any]:
        """Extract text while preserving layout"""
        try:
            # Use Tesseract with layout analysis
            image = Image.open(image_path)
            
            # Get detailed data
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Group by blocks and paragraphs
            blocks = {}
            current_block = 0
            current_par = 0
            
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                if int(data['conf'][i]) > 60:
                    block_num = data['block_num'][i]
                    par_num = data['par_num'][i]
                    
                    if block_num not in blocks:
                        blocks[block_num] = {}
                    if par_num not in blocks[block_num]:
                        blocks[block_num][par_num] = []
                    
                    blocks[block_num][par_num].append({
                        'text': data['text'][i],
                        'left': data['left'][i],
                        'top': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                        'conf': data['conf'][i]
                    })
            
            # Reconstruct text with layout
            layout_text = []
            for block_num in sorted(blocks.keys()):
                block_text = []
                for par_num in sorted(blocks[block_num].keys()):
                    par_text = ' '.join([item['text'] for item in blocks[block_num][par_num] 
                                       if item['text'].strip()])
                    if par_text:
                        block_text.append(par_text)
                if block_text:
                    layout_text.append('\n'.join(block_text))
            
            return {
                'full_text': '\n\n'.join(layout_text),
                'blocks': blocks,
                'raw_data': data
            }
            
        except Exception as e:
            logger.error(f"Text extraction error: {e}")
            return {'full_text': '', 'blocks': {}, 'error': str(e)}
    
    async def analyze_diagram(self, image_path: str) -> Dict[str, Any]:
        """Analyze diagrams and flowcharts"""
        # First use Vision API if available
        if self.client:
            prompt = """Analyze this diagram/flowchart:
            1. Identify the type of diagram
            2. Extract all nodes/components and their labels
            3. Identify connections and relationships
            4. Describe the flow or structure
            5. Suggest how to convert this to code or data structure"""
            
            result = await self.analyze_image(image_path, prompt)
            return result.content
        
        # Fallback to CV-based analysis
        try:
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect shapes
            shapes = self._detect_shapes(gray)
            
            # Extract text from shapes
            text_regions = self._extract_text_regions(image_path)
            
            # Detect connections (lines/arrows)
            connections = self._detect_connections(gray)
            
            return {
                'shapes': shapes,
                'text_regions': text_regions,
                'connections': connections,
                'type': 'unknown_diagram'
            }
            
        except Exception as e:
            logger.error(f"Diagram analysis error: {e}")
            return {'error': str(e)}
    
    def _detect_shapes(self, gray_image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect shapes in image"""
        shapes = []
        
        # Apply threshold
        _, thresh = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Approximate polygon
            epsilon = 0.04 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Get bounding rect
            x, y, w, h = cv2.boundingRect(contour)
            
            # Classify shape
            if len(approx) == 3:
                shape_type = "triangle"
            elif len(approx) == 4:
                aspect_ratio = float(w) / h
                if 0.95 <= aspect_ratio <= 1.05:
                    shape_type = "square"
                else:
                    shape_type = "rectangle"
            elif len(approx) > 6:
                shape_type = "circle"
            else:
                shape_type = "polygon"
            
            shapes.append({
                'type': shape_type,
                'bounds': (x, y, x + w, y + h),
                'vertices': len(approx),
                'area': cv2.contourArea(contour)
            })
        
        return shapes
    
    def _extract_text_regions(self, image_path: str) -> List[Dict[str, Any]]:
        """Extract text regions from image"""
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply morphological operations to find text regions
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(gray, kernel, iterations=3)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        text_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Extract region
            region = image[y:y+h, x:x+w]
            
            # OCR on region
            try:
                text = pytesseract.image_to_string(region).strip()
                if text:
                    text_regions.append({
                        'text': text,
                        'bounds': (x, y, x + w, y + h)
                    })
            except:
                pass
        
        return text_regions
    
    def _detect_connections(self, gray_image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect lines and arrows connecting shapes"""
        connections = []
        
        # Detect lines using Hough transform
        edges = cv2.Canny(gray_image, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=50, maxLineGap=10)
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                connections.append({
                    'type': 'line',
                    'start': (x1, y1),
                    'end': (x2, y2),
                    'length': np.sqrt((x2-x1)**2 + (y2-y1)**2)
                })
        
        return connections
    
    async def convert_code_screenshot(self, image_path: str) -> Dict[str, str]:
        """Convert code screenshot to actual code"""
        if self.client:
            prompt = """Extract the code from this screenshot:
            1. Preserve exact formatting and indentation
            2. Identify the programming language
            3. Include all visible code
            4. Note any syntax highlighting or comments
            5. Flag any partially visible or cut-off code"""
            
            result = await self.analyze_image(image_path, prompt)
            
            # Extract code blocks from response
            code_blocks = result.content.get('code_blocks', [])
            if code_blocks:
                return {
                    'language': code_blocks[0].get('language', 'unknown'),
                    'code': code_blocks[0].get('code', ''),
                    'confidence': result.confidence
                }
        
        # Fallback to OCR
        text_data = await self.extract_text_with_layout(image_path)
        code = text_data.get('full_text', '')
        
        # Try to detect language from content
        language = self._detect_language(code)
        
        return {
            'language': language,
            'code': code,
            'confidence': 0.6
        }
    
    def _detect_language(self, code: str) -> str:
        """Detect programming language from code text"""
        patterns = {
            'python': [r'def\s+\w+\s*\(', r'import\s+\w+', r'print\s*\(', r'class\s+\w+'],
            'javascript': [r'function\s+\w+', r'const\s+\w+', r'let\s+\w+', r'=>'],
            'java': [r'public\s+class', r'public\s+static', r'System\.out\.println'],
            'cpp': [r'#include\s*<', r'using\s+namespace', r'int\s+main\s*\('],
            'html': [r'<html', r'<body', r'<div', r'</\w+>'],
            'css': [r'\.\w+\s*{', r'#\w+\s*{', r':\s*\w+;']
        }
        
        for lang, patterns_list in patterns.items():
            for pattern in patterns_list:
                if re.search(pattern, code, re.IGNORECASE):
                    return lang
        
        return 'unknown'
    
    async def stream_analysis(self, callback, fps: int = 1):
        """Stream real-time screen analysis"""
        self.streaming = True
        
        try:
            while self.streaming:
                # Capture screen
                screenshot_path = await self.capture_screen()
                
                # Analyze in background
                result = await self.analyze_image(screenshot_path)
                
                # Callback with result
                await callback(result)
                
                # Clean up old screenshot
                os.remove(screenshot_path)
                
                # Wait for next frame
                await asyncio.sleep(1.0 / fps)
                
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            self.streaming = False
    
    def stop_streaming(self):
        """Stop streaming analysis"""
        self.streaming = False
    
    async def compare_images(self, image1_path: str, image2_path: str) -> Dict[str, Any]:
        """Compare two images for differences"""
        try:
            # Load images
            img1 = cv2.imread(image1_path)
            img2 = cv2.imread(image2_path)
            
            # Ensure same size
            if img1.shape != img2.shape:
                img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
            
            # Calculate difference
            diff = cv2.absdiff(img1, img2)
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            
            # Find contours of differences
            _, thresh = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            differences = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = cv2.contourArea(contour)
                if area > 100:  # Filter small differences
                    differences.append({
                        'bounds': (x, y, x + w, y + h),
                        'area': area
                    })
            
            # Calculate similarity score
            similarity = 1.0 - (np.sum(gray_diff > 30) / gray_diff.size)
            
            return {
                'similarity': similarity,
                'differences': differences,
                'total_differences': len(differences)
            }
            
        except Exception as e:
            logger.error(f"Image comparison error: {e}")
            return {'error': str(e)}


if __name__ == "__main__":
    # Example usage
    async def main():
        engine = NexusVisionEngine()
        
        # Capture screen
        screenshot = await engine.capture_screen()
        print(f"Screenshot saved: {screenshot}")
        
        # Analyze image
        result = await engine.analyze_image(screenshot)
        print(f"Analysis: {result.content}")
        
        # Extract text with layout
        text_data = await engine.extract_text_with_layout(screenshot)
        print(f"Extracted text: {text_data['full_text'][:200]}...")
    
    asyncio.run(main())