#!/usr/bin/env python3
"""
NEXUS Screen Capture System - Cross-platform screen capture with advanced features
Provides screen recording, annotation, and privacy protection
"""

import asyncio
import io
import json
import logging
import os
import platform
import subprocess
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import mss
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk
import pyautogui

# Platform-specific imports
if platform.system() == "Windows":
    import win32gui
    import win32con
elif platform.system() == "Darwin":
    import Quartz
    from AppKit import NSWorkspace

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CaptureRegion:
    """Screen capture region"""
    x: int
    y: int
    width: int
    height: int
    monitor: Optional[int] = None
    window_id: Optional[str] = None

@dataclass
class PrivacyRule:
    """Privacy protection rule"""
    rule_type: str  # blur, blackout, pixelate
    pattern: Optional[str] = None  # regex pattern
    regions: Optional[List[Tuple[int, int, int, int]]] = None
    strength: float = 0.8

@dataclass
class Annotation:
    """Screen annotation"""
    annotation_type: str  # text, arrow, rectangle, circle, highlight
    position: Tuple[int, int]
    properties: Dict[str, Any]
    timestamp: Optional[datetime] = None

class NexusScreenCapture:
    """Advanced screen capture system with recording and annotation"""
    
    def __init__(self):
        """Initialize screen capture system"""
        self.screen_capture = mss.mss()
        self.platform = platform.system()
        self.recording = False
        self.recording_thread = None
        self.capture_dir = Path("captures")
        self.capture_dir.mkdir(exist_ok=True)
        self.privacy_rules = []
        self.annotations = []
        self.video_writer = None
        self.fps = 30
        self.quality = 85
        
        # Font for annotations
        try:
            if self.platform == "Windows":
                self.font_path = "C:/Windows/Fonts/Arial.ttf"
            elif self.platform == "Darwin":
                self.font_path = "/System/Library/Fonts/Helvetica.ttc"
            else:
                self.font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        except:
            self.font_path = None
    
    def get_monitors(self) -> List[Dict[str, Any]]:
        """Get information about all monitors"""
        monitors = []
        for i, monitor in enumerate(self.screen_capture.monitors[1:], 1):
            monitors.append({
                'id': i,
                'name': f'Monitor {i}',
                'x': monitor['left'],
                'y': monitor['top'],
                'width': monitor['width'],
                'height': monitor['height']
            })
        return monitors
    
    def get_windows(self) -> List[Dict[str, Any]]:
        """Get list of all windows"""
        windows = []
        
        if self.platform == "Windows":
            def enum_handler(hwnd, windows_list):
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    if window_title:
                        rect = win32gui.GetWindowRect(hwnd)
                        windows_list.append({
                            'id': hwnd,
                            'title': window_title,
                            'x': rect[0],
                            'y': rect[1],
                            'width': rect[2] - rect[0],
                            'height': rect[3] - rect[1]
                        })
                return True
            
            win32gui.EnumWindows(enum_handler, windows)
            
        elif self.platform == "Darwin":
            # Use Quartz to get window list
            window_list = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionAll,
                Quartz.kCGNullWindowID
            )
            
            for window in window_list:
                if window.get('kCGWindowLayer', 0) == 0:
                    bounds = window.get('kCGWindowBounds', {})
                    windows.append({
                        'id': window.get('kCGWindowNumber'),
                        'title': window.get('kCGWindowOwnerName', 'Unknown'),
                        'x': int(bounds.get('X', 0)),
                        'y': int(bounds.get('Y', 0)),
                        'width': int(bounds.get('Width', 0)),
                        'height': int(bounds.get('Height', 0))
                    })
                    
        elif self.platform == "Linux":
            # Use xwininfo
            try:
                result = subprocess.run(['wmctrl', '-l', '-G'], 
                                      capture_output=True, text=True)
                for line in result.stdout.strip().split('\n'):
                    parts = line.split(None, 7)
                    if len(parts) >= 8:
                        windows.append({
                            'id': parts[0],
                            'title': parts[7],
                            'x': int(parts[2]),
                            'y': int(parts[3]),
                            'width': int(parts[4]),
                            'height': int(parts[5])
                        })
            except:
                logger.warning("wmctrl not found. Window listing unavailable.")
        
        return windows
    
    async def capture_screen(self, region: Optional[CaptureRegion] = None,
                           output_path: Optional[str] = None) -> str:
        """Capture screen or specific region"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not output_path:
            output_path = self.capture_dir / f"screenshot_{timestamp}.png"
        
        try:
            if region:
                # Capture specific region
                monitor = {
                    "left": region.x,
                    "top": region.y,
                    "width": region.width,
                    "height": region.height
                }
            else:
                # Capture primary monitor
                monitor = self.screen_capture.monitors[1]
            
            # Capture
            screenshot = self.screen_capture.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # Apply privacy rules
            img = self._apply_privacy_rules(img, monitor)
            
            # Apply annotations
            if self.annotations:
                img = self._apply_annotations(img)
            
            # Optimize and save
            img = self._optimize_image(img)
            img.save(output_path, quality=self.quality, optimize=True)
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Screen capture error: {e}")
            raise
    
    async def capture_window(self, window_title: str, output_path: Optional[str] = None) -> str:
        """Capture specific window by title"""
        windows = self.get_windows()
        
        # Find window
        target_window = None
        for window in windows:
            if window_title.lower() in window['title'].lower():
                target_window = window
                break
        
        if not target_window:
            raise ValueError(f"Window '{window_title}' not found")
        
        # Create region from window bounds
        region = CaptureRegion(
            x=target_window['x'],
            y=target_window['y'],
            width=target_window['width'],
            height=target_window['height'],
            window_id=target_window['id']
        )
        
        return await self.capture_screen(region, output_path)
    
    async def select_region(self) -> CaptureRegion:
        """Interactive region selection"""
        # Create transparent overlay window
        root = tk.Tk()
        root.attributes('-alpha', 0.3)
        root.attributes('-fullscreen', True)
        root.attributes('-topmost', True)
        
        if self.platform == "Darwin":
            root.attributes('-transparent', True)
        
        canvas = tk.Canvas(root, highlightthickness=0)
        canvas.pack(fill='both', expand=True)
        
        # Variables for selection
        start_x = start_y = end_x = end_y = 0
        rect = None
        
        def on_mouse_down(event):
            nonlocal start_x, start_y, rect
            start_x, start_y = event.x, event.y
            if rect:
                canvas.delete(rect)
            rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, 
                                         outline='red', width=2)
        
        def on_mouse_drag(event):
            nonlocal end_x, end_y
            end_x, end_y = event.x, event.y
            canvas.coords(rect, start_x, start_y, end_x, end_y)
        
        def on_mouse_up(event):
            root.quit()
        
        canvas.bind('<ButtonPress-1>', on_mouse_down)
        canvas.bind('<B1-Motion>', on_mouse_drag)
        canvas.bind('<ButtonRelease-1>', on_mouse_up)
        
        # Add escape key binding
        root.bind('<Escape>', lambda e: root.quit())
        
        root.mainloop()
        root.destroy()
        
        # Calculate region
        x = min(start_x, end_x)
        y = min(start_y, end_y)
        width = abs(end_x - start_x)
        height = abs(end_y - start_y)
        
        return CaptureRegion(x, y, width, height)
    
    async def start_recording(self, region: Optional[CaptureRegion] = None,
                            output_path: Optional[str] = None,
                            fps: int = 30) -> str:
        """Start video recording"""
        if self.recording:
            raise RuntimeError("Recording already in progress")
        
        self.fps = fps
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not output_path:
            output_path = self.capture_dir / f"recording_{timestamp}.mp4"
        
        # Determine capture region
        if region:
            monitor = {
                "left": region.x,
                "top": region.y,
                "width": region.width,
                "height": region.height
            }
        else:
            monitor = self.screen_capture.monitors[1]
        
        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(
            str(output_path),
            fourcc,
            fps,
            (monitor['width'], monitor['height'])
        )
        
        # Start recording thread
        self.recording = True
        self.recording_thread = threading.Thread(
            target=self._recording_loop,
            args=(monitor, output_path)
        )
        self.recording_thread.start()
        
        return str(output_path)
    
    def _recording_loop(self, monitor: Dict[str, Any], output_path: str):
        """Recording loop thread"""
        frame_duration = 1.0 / self.fps
        
        while self.recording:
            start_time = time.time()
            
            try:
                # Capture frame
                screenshot = self.screen_capture.grab(monitor)
                
                # Convert to numpy array
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                # Apply privacy rules
                img = self._apply_privacy_rules(img, monitor)
                
                # Apply annotations
                if self.annotations:
                    img = self._apply_annotations(img)
                
                # Convert to OpenCV format
                frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                
                # Write frame
                self.video_writer.write(frame)
                
            except Exception as e:
                logger.error(f"Recording frame error: {e}")
            
            # Maintain FPS
            elapsed = time.time() - start_time
            if elapsed < frame_duration:
                time.sleep(frame_duration - elapsed)
    
    async def stop_recording(self) -> None:
        """Stop video recording"""
        if not self.recording:
            raise RuntimeError("No recording in progress")
        
        self.recording = False
        
        # Wait for thread to finish
        if self.recording_thread:
            self.recording_thread.join()
        
        # Release video writer
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
    
    def add_annotation(self, annotation: Annotation) -> None:
        """Add annotation to captures"""
        annotation.timestamp = datetime.now()
        self.annotations.append(annotation)
    
    def clear_annotations(self) -> None:
        """Clear all annotations"""
        self.annotations = []
    
    def add_privacy_rule(self, rule: PrivacyRule) -> None:
        """Add privacy protection rule"""
        self.privacy_rules.append(rule)
    
    def clear_privacy_rules(self) -> None:
        """Clear all privacy rules"""
        self.privacy_rules = []
    
    def _apply_privacy_rules(self, img: Image.Image, monitor: Dict[str, Any]) -> Image.Image:
        """Apply privacy protection to image"""
        img_array = np.array(img)
        
        for rule in self.privacy_rules:
            if rule.rule_type == 'blur':
                img_array = self._apply_blur(img_array, rule)
            elif rule.rule_type == 'blackout':
                img_array = self._apply_blackout(img_array, rule)
            elif rule.rule_type == 'pixelate':
                img_array = self._apply_pixelate(img_array, rule)
        
        # Detect and blur sensitive content
        img_array = self._auto_detect_sensitive(img_array)
        
        return Image.fromarray(img_array)
    
    def _apply_blur(self, img_array: np.ndarray, rule: PrivacyRule) -> np.ndarray:
        """Apply blur effect"""
        if rule.regions:
            for region in rule.regions:
                x, y, w, h = region
                roi = img_array[y:y+h, x:x+w]
                
                # Apply Gaussian blur
                blur_strength = int(50 * rule.strength)
                if blur_strength % 2 == 0:
                    blur_strength += 1
                
                blurred = cv2.GaussianBlur(roi, (blur_strength, blur_strength), 0)
                img_array[y:y+h, x:x+w] = blurred
        
        return img_array
    
    def _apply_blackout(self, img_array: np.ndarray, rule: PrivacyRule) -> np.ndarray:
        """Apply blackout effect"""
        if rule.regions:
            for region in rule.regions:
                x, y, w, h = region
                img_array[y:y+h, x:x+w] = 0  # Black
        
        return img_array
    
    def _apply_pixelate(self, img_array: np.ndarray, rule: PrivacyRule) -> np.ndarray:
        """Apply pixelate effect"""
        if rule.regions:
            for region in rule.regions:
                x, y, w, h = region
                roi = img_array[y:y+h, x:x+w]
                
                # Pixelate by downsampling and upsampling
                pixel_size = int(20 * rule.strength)
                small = cv2.resize(roi, (w//pixel_size, h//pixel_size), 
                                 interpolation=cv2.INTER_NEAREST)
                pixelated = cv2.resize(small, (w, h), 
                                     interpolation=cv2.INTER_NEAREST)
                
                img_array[y:y+h, x:x+w] = pixelated
        
        return img_array
    
    def _auto_detect_sensitive(self, img_array: np.ndarray) -> np.ndarray:
        """Auto-detect and blur sensitive content"""
        # This is a placeholder for more sophisticated detection
        # In production, you might use OCR to detect sensitive text patterns
        
        # Example: Blur regions that might contain passwords
        # (This would need actual implementation with OCR)
        
        return img_array
    
    def _apply_annotations(self, img: Image.Image) -> Image.Image:
        """Apply annotations to image"""
        draw = ImageDraw.Draw(img)
        
        # Load font
        font = None
        if self.font_path:
            try:
                font = ImageFont.truetype(self.font_path, 16)
            except:
                font = None
        
        for annotation in self.annotations:
            if annotation.annotation_type == 'text':
                self._draw_text(draw, annotation, font)
            elif annotation.annotation_type == 'arrow':
                self._draw_arrow(draw, annotation)
            elif annotation.annotation_type == 'rectangle':
                self._draw_rectangle(draw, annotation)
            elif annotation.annotation_type == 'circle':
                self._draw_circle(draw, annotation)
            elif annotation.annotation_type == 'highlight':
                self._draw_highlight(img, annotation)
        
        return img
    
    def _draw_text(self, draw: ImageDraw.Draw, annotation: Annotation, 
                  font: Optional[ImageFont.FreeTypeFont]):
        """Draw text annotation"""
        text = annotation.properties.get('text', '')
        color = annotation.properties.get('color', 'red')
        bg_color = annotation.properties.get('bg_color', None)
        
        x, y = annotation.position
        
        if bg_color and font:
            # Get text bbox
            bbox = draw.textbbox((x, y), text, font=font)
            # Draw background
            draw.rectangle(bbox, fill=bg_color)
        
        draw.text((x, y), text, fill=color, font=font)
    
    def _draw_arrow(self, draw: ImageDraw.Draw, annotation: Annotation):
        """Draw arrow annotation"""
        start = annotation.position
        end = tuple(annotation.properties.get('end', (start[0] + 50, start[1] + 50)))
        color = annotation.properties.get('color', 'red')
        width = annotation.properties.get('width', 3)
        
        # Draw line
        draw.line([start, end], fill=color, width=width)
        
        # Draw arrowhead
        angle = np.arctan2(end[1] - start[1], end[0] - start[0])
        arrow_length = 15
        arrow_angle = np.pi / 6
        
        # Calculate arrowhead points
        x1 = end[0] - arrow_length * np.cos(angle - arrow_angle)
        y1 = end[1] - arrow_length * np.sin(angle - arrow_angle)
        x2 = end[0] - arrow_length * np.cos(angle + arrow_angle)
        y2 = end[1] - arrow_length * np.sin(angle + arrow_angle)
        
        draw.polygon([end, (int(x1), int(y1)), (int(x2), int(y2))], fill=color)
    
    def _draw_rectangle(self, draw: ImageDraw.Draw, annotation: Annotation):
        """Draw rectangle annotation"""
        x, y = annotation.position
        width = annotation.properties.get('width', 100)
        height = annotation.properties.get('height', 100)
        color = annotation.properties.get('color', 'red')
        fill = annotation.properties.get('fill', None)
        line_width = annotation.properties.get('width', 3)
        
        draw.rectangle(
            [(x, y), (x + width, y + height)],
            outline=color,
            fill=fill,
            width=line_width
        )
    
    def _draw_circle(self, draw: ImageDraw.Draw, annotation: Annotation):
        """Draw circle annotation"""
        center = annotation.position
        radius = annotation.properties.get('radius', 50)
        color = annotation.properties.get('color', 'red')
        fill = annotation.properties.get('fill', None)
        line_width = annotation.properties.get('width', 3)
        
        bbox = [
            center[0] - radius,
            center[1] - radius,
            center[0] + radius,
            center[1] + radius
        ]
        
        draw.ellipse(bbox, outline=color, fill=fill, width=line_width)
    
    def _draw_highlight(self, img: Image.Image, annotation: Annotation):
        """Draw highlight annotation"""
        x, y = annotation.position
        width = annotation.properties.get('width', 100)
        height = annotation.properties.get('height', 50)
        color = annotation.properties.get('color', 'yellow')
        opacity = annotation.properties.get('opacity', 0.3)
        
        # Create overlay
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Parse color and add alpha
        if isinstance(color, str):
            if color.startswith('#'):
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
            else:
                # Use predefined colors
                colors = {
                    'yellow': (255, 255, 0),
                    'red': (255, 0, 0),
                    'green': (0, 255, 0),
                    'blue': (0, 0, 255)
                }
                r, g, b = colors.get(color, (255, 255, 0))
        else:
            r, g, b = color
        
        alpha = int(255 * opacity)
        
        draw.rectangle(
            [(x, y), (x + width, y + height)],
            fill=(r, g, b, alpha)
        )
        
        # Composite
        img.paste(overlay, (0, 0), overlay)
    
    def _optimize_image(self, img: Image.Image) -> Image.Image:
        """Optimize image for size and quality"""
        # Convert RGBA to RGB if needed
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        
        # Resize if too large
        max_dimension = 3840  # 4K max
        if img.width > max_dimension or img.height > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        
        return img
    
    async def capture_scrolling_screenshot(self, region: Optional[CaptureRegion] = None,
                                         scroll_pause: float = 0.5) -> str:
        """Capture scrolling screenshot of entire page"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.capture_dir / f"scrolling_{timestamp}.png"
        
        screenshots = []
        last_height = 0
        
        # Initial capture
        screenshot_path = await self.capture_screen(region)
        screenshots.append(Image.open(screenshot_path))
        
        # Scroll and capture
        while True:
            # Scroll down
            pyautogui.scroll(-5)  # Scroll down 5 "clicks"
            await asyncio.sleep(scroll_pause)
            
            # Capture
            screenshot_path = await self.capture_screen(region)
            current_screenshot = Image.open(screenshot_path)
            
            # Check if we've reached the bottom
            # (This is simplified - real implementation would be more sophisticated)
            if len(screenshots) > 20:  # Safety limit
                break
            
            screenshots.append(current_screenshot)
        
        # Stitch screenshots together
        total_height = sum(img.height for img in screenshots)
        stitched = Image.new('RGB', (screenshots[0].width, total_height))
        
        y_offset = 0
        for img in screenshots:
            stitched.paste(img, (0, y_offset))
            y_offset += img.height
        
        # Save stitched image
        stitched.save(output_path, quality=self.quality, optimize=True)
        
        # Clean up temporary screenshots
        for i in range(len(screenshots)):
            os.remove(screenshot_path)
        
        return str(output_path)
    
    async def create_gif_from_captures(self, image_paths: List[str], 
                                     output_path: Optional[str] = None,
                                     duration: int = 500) -> str:
        """Create animated GIF from multiple captures"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not output_path:
            output_path = self.capture_dir / f"animation_{timestamp}.gif"
        
        images = []
        for path in image_paths:
            img = Image.open(path)
            # Resize for smaller file size
            img.thumbnail((800, 600), Image.Resampling.LANCZOS)
            images.append(img)
        
        # Save as GIF
        images[0].save(
            output_path,
            save_all=True,
            append_images=images[1:],
            duration=duration,
            loop=0,
            optimize=True
        )
        
        return str(output_path)
    
    def compress_video(self, input_path: str, output_path: Optional[str] = None,
                      quality: str = 'medium') -> str:
        """Compress video file"""
        if not output_path:
            base_path = Path(input_path)
            output_path = base_path.parent / f"{base_path.stem}_compressed{base_path.suffix}"
        
        # Quality presets
        presets = {
            'low': {'crf': 35, 'preset': 'faster'},
            'medium': {'crf': 28, 'preset': 'fast'},
            'high': {'crf': 23, 'preset': 'medium'}
        }
        
        settings = presets.get(quality, presets['medium'])
        
        # Use ffmpeg for compression
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', 'libx264',
            '-crf', str(settings['crf']),
            '-preset', settings['preset'],
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            '-y',
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return str(output_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"Video compression failed: {e}")
            # Fallback to simple copy if ffmpeg fails
            shutil.copy2(input_path, output_path)
            return str(output_path)


class ScreenCaptureUI:
    """GUI for screen capture"""
    
    def __init__(self, capture_system: NexusScreenCapture):
        """Initialize UI"""
        self.capture = capture_system
        self.root = tk.Tk()
        self.root.title("NEXUS Screen Capture")
        self.root.geometry("400x500")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI components"""
        # Title
        title = ttk.Label(self.root, text="NEXUS Screen Capture", 
                         font=('Arial', 16, 'bold'))
        title.pack(pady=10)
        
        # Capture buttons frame
        capture_frame = ttk.LabelFrame(self.root, text="Capture", padding=10)
        capture_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(capture_frame, text="Capture Full Screen",
                  command=self._capture_fullscreen).pack(fill='x', pady=2)
        
        ttk.Button(capture_frame, text="Select Region",
                  command=self._capture_region).pack(fill='x', pady=2)
        
        ttk.Button(capture_frame, text="Capture Window",
                  command=self._capture_window).pack(fill='x', pady=2)
        
        # Recording frame
        record_frame = ttk.LabelFrame(self.root, text="Recording", padding=10)
        record_frame.pack(fill='x', padx=20, pady=10)
        
        self.record_button = ttk.Button(record_frame, text="Start Recording",
                                       command=self._toggle_recording)
        self.record_button.pack(fill='x', pady=2)
        
        # Annotation frame
        anno_frame = ttk.LabelFrame(self.root, text="Annotations", padding=10)
        anno_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(anno_frame, text="Add Text",
                  command=self._add_text_annotation).pack(fill='x', pady=2)
        
        ttk.Button(anno_frame, text="Add Arrow",
                  command=self._add_arrow_annotation).pack(fill='x', pady=2)
        
        ttk.Button(anno_frame, text="Clear Annotations",
                  command=self.capture.clear_annotations).pack(fill='x', pady=2)
        
        # Privacy frame
        privacy_frame = ttk.LabelFrame(self.root, text="Privacy", padding=10)
        privacy_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(privacy_frame, text="Add Blur Region",
                  command=self._add_blur_region).pack(fill='x', pady=2)
        
        ttk.Button(privacy_frame, text="Clear Privacy Rules",
                  command=self.capture.clear_privacy_rules).pack(fill='x', pady=2)
        
        # Status
        self.status_label = ttk.Label(self.root, text="Ready", 
                                     relief='sunken', anchor='w')
        self.status_label.pack(fill='x', side='bottom', padx=5, pady=5)
    
    def _capture_fullscreen(self):
        """Capture full screen"""
        asyncio.run(self._async_capture_fullscreen())
    
    async def _async_capture_fullscreen(self):
        """Async capture full screen"""
        self.status_label.config(text="Capturing...")
        path = await self.capture.capture_screen()
        self.status_label.config(text=f"Saved: {Path(path).name}")
    
    def _capture_region(self):
        """Capture selected region"""
        asyncio.run(self._async_capture_region())
    
    async def _async_capture_region(self):
        """Async capture region"""
        self.root.withdraw()
        region = await self.capture.select_region()
        self.root.deiconify()
        
        self.status_label.config(text="Capturing...")
        path = await self.capture.capture_screen(region)
        self.status_label.config(text=f"Saved: {Path(path).name}")
    
    def _capture_window(self):
        """Capture window"""
        # Get window list
        windows = self.capture.get_windows()
        
        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Window")
        dialog.geometry("400x300")
        
        # Listbox
        listbox = tk.Listbox(dialog)
        listbox.pack(fill='both', expand=True, padx=10, pady=10)
        
        for window in windows:
            listbox.insert(tk.END, window['title'])
        
        def on_select():
            selection = listbox.curselection()
            if selection:
                window = windows[selection[0]]
                dialog.destroy()
                asyncio.run(self._async_capture_window(window['title']))
        
        ttk.Button(dialog, text="Capture", command=on_select).pack(pady=5)
    
    async def _async_capture_window(self, window_title: str):
        """Async capture window"""
        self.status_label.config(text="Capturing...")
        path = await self.capture.capture_window(window_title)
        self.status_label.config(text=f"Saved: {Path(path).name}")
    
    def _toggle_recording(self):
        """Toggle recording"""
        if not self.capture.recording:
            asyncio.run(self._start_recording())
        else:
            asyncio.run(self._stop_recording())
    
    async def _start_recording(self):
        """Start recording"""
        self.status_label.config(text="Recording...")
        self.record_button.config(text="Stop Recording")
        await self.capture.start_recording()
    
    async def _stop_recording(self):
        """Stop recording"""
        await self.capture.stop_recording()
        self.record_button.config(text="Start Recording")
        self.status_label.config(text="Recording saved")
    
    def _add_text_annotation(self):
        """Add text annotation"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Text")
        dialog.geometry("300x150")
        
        ttk.Label(dialog, text="Text:").grid(row=0, column=0, padx=5, pady=5)
        text_entry = ttk.Entry(dialog, width=30)
        text_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="X:").grid(row=1, column=0, padx=5, pady=5)
        x_entry = ttk.Entry(dialog, width=10)
        x_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        ttk.Label(dialog, text="Y:").grid(row=2, column=0, padx=5, pady=5)
        y_entry = ttk.Entry(dialog, width=10)
        y_entry.grid(row=2, column=1, sticky='w', padx=5, pady=5)
        
        def add():
            annotation = Annotation(
                annotation_type='text',
                position=(int(x_entry.get()), int(y_entry.get())),
                properties={'text': text_entry.get(), 'color': 'red'}
            )
            self.capture.add_annotation(annotation)
            dialog.destroy()
            self.status_label.config(text="Text annotation added")
        
        ttk.Button(dialog, text="Add", command=add).grid(row=3, column=1, pady=10)
    
    def _add_arrow_annotation(self):
        """Add arrow annotation"""
        # Similar to text annotation dialog
        pass
    
    def _add_blur_region(self):
        """Add blur region"""
        self.root.withdraw()
        asyncio.run(self._async_add_blur_region())
    
    async def _async_add_blur_region(self):
        """Async add blur region"""
        region = await self.capture.select_region()
        self.root.deiconify()
        
        rule = PrivacyRule(
            rule_type='blur',
            regions=[(region.x, region.y, region.width, region.height)]
        )
        self.capture.add_privacy_rule(rule)
        self.status_label.config(text="Blur region added")
    
    def run(self):
        """Run UI"""
        self.root.mainloop()


if __name__ == "__main__":
    # Example usage
    capture = NexusScreenCapture()
    
    # CLI mode
    if len(sys.argv) > 1:
        import sys
        
        async def main():
            if sys.argv[1] == "capture":
                path = await capture.capture_screen()
                print(f"Screenshot saved: {path}")
            elif sys.argv[1] == "record":
                print("Recording started. Press Ctrl+C to stop.")
                path = await capture.start_recording()
                try:
                    await asyncio.sleep(3600)  # Max 1 hour
                except KeyboardInterrupt:
                    await capture.stop_recording()
                    print(f"Recording saved: {path}")
        
        asyncio.run(main())
    else:
        # GUI mode
        ui = ScreenCaptureUI(capture)
        ui.run()