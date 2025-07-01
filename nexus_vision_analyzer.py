#!/usr/bin/env python3
"""
NEXUS Vision Analyzer - Advanced visual analysis and pattern recognition
Provides UI/UX analysis, design extraction, and visual debugging
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageStat
from sklearn.cluster import KMeans
from collections import Counter, defaultdict
import colorsys
from dataclasses import dataclass
import webcolors

from nexus_vision_engine import NexusVisionEngine, VisionResult, UIElement

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DesignPattern:
    """Detected design pattern"""
    pattern_type: str
    confidence: float
    properties: Dict[str, Any]
    examples: List[Tuple[int, int, int, int]]  # Bounding boxes

@dataclass
class ColorPalette:
    """Extracted color palette"""
    primary: str
    secondary: List[str]
    accent: List[str]
    background: str
    text: str
    semantic: Dict[str, str]  # success, error, warning, info

@dataclass
class AccessibilityIssue:
    """Accessibility issue found"""
    issue_type: str
    severity: str  # low, medium, high, critical
    location: Tuple[int, int, int, int]
    description: str
    suggestion: str

class NexusVisionAnalyzer:
    """Advanced visual analysis for UI/UX and design systems"""
    
    def __init__(self, vision_engine: Optional[NexusVisionEngine] = None):
        """Initialize analyzer"""
        self.engine = vision_engine or NexusVisionEngine()
        self.patterns_db = self._load_patterns_db()
        self.cache_dir = Path("vision_analysis_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Common UI patterns
        self.ui_patterns = {
            'button': {
                'min_width': 60,
                'min_height': 30,
                'max_aspect_ratio': 5.0,
                'common_texts': ['submit', 'cancel', 'ok', 'save', 'delete', 'add', 'remove']
            },
            'input': {
                'min_width': 100,
                'min_height': 25,
                'max_height': 50,
                'aspect_ratio_range': (3.0, 10.0)
            },
            'card': {
                'min_width': 200,
                'min_height': 100,
                'has_shadow': True,
                'has_border': True
            },
            'navbar': {
                'position': 'top',
                'min_height': 40,
                'max_height': 100,
                'spans_width': True
            },
            'sidebar': {
                'position': 'left|right',
                'min_width': 150,
                'max_width': 350,
                'spans_height': True
            }
        }
    
    def _load_patterns_db(self) -> Dict[str, Any]:
        """Load design patterns database"""
        patterns_file = Path("design_patterns.json")
        if patterns_file.exists():
            with open(patterns_file, 'r') as f:
                return json.load(f)
        return {
            'material': {
                'elevation': [0, 1, 2, 3, 4, 6, 8, 12, 16, 24],
                'spacing': [4, 8, 12, 16, 20, 24, 32, 40, 48, 56, 64],
                'typography': {
                    'h1': {'size': 96, 'weight': 300},
                    'h2': {'size': 60, 'weight': 300},
                    'h3': {'size': 48, 'weight': 400},
                    'h4': {'size': 34, 'weight': 400},
                    'h5': {'size': 24, 'weight': 400},
                    'h6': {'size': 20, 'weight': 500}
                }
            }
        }
    
    async def analyze_ui_patterns(self, image_path: str) -> List[DesignPattern]:
        """Recognize UI/UX patterns in image"""
        patterns = []
        
        # Load image
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect edges and contours
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Analyze each contour
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            roi = image[y:y+h, x:x+w]
            
            # Check against known patterns
            pattern = self._identify_ui_element(roi, (x, y, w, h), image.shape)
            if pattern:
                patterns.append(pattern)
        
        # Group and refine patterns
        patterns = self._refine_patterns(patterns)
        
        # Use Vision API for additional insights
        if self.engine.client:
            vision_result = await self.engine.analyze_image(image_path, 
                "Identify UI components and patterns: buttons, forms, cards, navigation, etc.")
            patterns = self._merge_vision_patterns(patterns, vision_result)
        
        return patterns
    
    def _identify_ui_element(self, roi: np.ndarray, bounds: Tuple[int, int, int, int], 
                           image_shape: Tuple[int, int, int]) -> Optional[DesignPattern]:
        """Identify UI element type"""
        x, y, w, h = bounds
        img_h, img_w = image_shape[:2]
        
        # Calculate properties
        aspect_ratio = w / h if h > 0 else 0
        relative_pos = (x / img_w, y / img_h)
        relative_size = (w / img_w, h / img_h)
        
        # Check for button
        if (self.ui_patterns['button']['min_width'] <= w and 
            self.ui_patterns['button']['min_height'] <= h <= 80 and
            aspect_ratio <= self.ui_patterns['button']['max_aspect_ratio']):
            
            # Additional button checks
            if self._has_rounded_corners(roi) or self._has_solid_background(roi):
                return DesignPattern(
                    pattern_type='button',
                    confidence=0.8,
                    properties={
                        'style': 'solid' if self._has_solid_background(roi) else 'outlined',
                        'rounded': self._has_rounded_corners(roi)
                    },
                    examples=[(x, y, x+w, y+h)]
                )
        
        # Check for input field
        input_pattern = self.ui_patterns['input']
        if (input_pattern['min_width'] <= w and 
            input_pattern['min_height'] <= h <= input_pattern['max_height'] and
            input_pattern['aspect_ratio_range'][0] <= aspect_ratio <= input_pattern['aspect_ratio_range'][1]):
            
            if self._has_border(roi):
                return DesignPattern(
                    pattern_type='input',
                    confidence=0.75,
                    properties={'has_border': True},
                    examples=[(x, y, x+w, y+h)]
                )
        
        # Check for card
        if (w >= self.ui_patterns['card']['min_width'] and 
            h >= self.ui_patterns['card']['min_height']):
            
            if self._has_shadow(roi) or self._has_border(roi):
                return DesignPattern(
                    pattern_type='card',
                    confidence=0.7,
                    properties={
                        'has_shadow': self._has_shadow(roi),
                        'has_border': self._has_border(roi)
                    },
                    examples=[(x, y, x+w, y+h)]
                )
        
        # Check for navbar
        if (y < img_h * 0.2 and w > img_w * 0.8 and 
            self.ui_patterns['navbar']['min_height'] <= h <= self.ui_patterns['navbar']['max_height']):
            return DesignPattern(
                pattern_type='navbar',
                confidence=0.85,
                properties={'position': 'top'},
                examples=[(x, y, x+w, y+h)]
            )
        
        # Check for sidebar
        if (h > img_h * 0.7 and 
            self.ui_patterns['sidebar']['min_width'] <= w <= self.ui_patterns['sidebar']['max_width']):
            position = 'left' if x < img_w * 0.3 else 'right' if x > img_w * 0.7 else None
            if position:
                return DesignPattern(
                    pattern_type='sidebar',
                    confidence=0.8,
                    properties={'position': position},
                    examples=[(x, y, x+w, y+h)]
                )
        
        return None
    
    def _has_rounded_corners(self, roi: np.ndarray) -> bool:
        """Check if element has rounded corners"""
        h, w = roi.shape[:2]
        corners = [
            roi[0:5, 0:5],
            roi[0:5, w-5:w],
            roi[h-5:h, 0:5],
            roi[h-5:h, w-5:w]
        ]
        
        for corner in corners:
            if np.mean(corner) > 200:  # Mostly white
                return True
        return False
    
    def _has_solid_background(self, roi: np.ndarray) -> bool:
        """Check if element has solid background"""
        # Calculate color variance
        b, g, r = cv2.split(roi)
        variance = np.var(b) + np.var(g) + np.var(r)
        return variance < 1000
    
    def _has_border(self, roi: np.ndarray) -> bool:
        """Check if element has border"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # Check edges on perimeter
        h, w = edges.shape
        perimeter_edges = np.sum(edges[0, :]) + np.sum(edges[h-1, :]) + \
                         np.sum(edges[:, 0]) + np.sum(edges[:, w-1])
        
        return perimeter_edges > (2 * (w + h) * 0.5 * 255)
    
    def _has_shadow(self, roi: np.ndarray) -> bool:
        """Check if element has shadow"""
        # Look for gradient at edges
        h, w = roi.shape[:2]
        
        # Check bottom and right edges for shadow
        bottom_edge = roi[h-10:h, :]
        right_edge = roi[:, w-10:w]
        
        # Shadow typically darker
        bottom_mean = np.mean(bottom_edge)
        right_mean = np.mean(right_edge)
        center_mean = np.mean(roi[h//2-5:h//2+5, w//2-5:w//2+5])
        
        return bottom_mean < center_mean * 0.8 or right_mean < center_mean * 0.8
    
    def _refine_patterns(self, patterns: List[DesignPattern]) -> List[DesignPattern]:
        """Group and refine detected patterns"""
        # Group similar patterns
        grouped = defaultdict(list)
        for pattern in patterns:
            grouped[pattern.pattern_type].append(pattern)
        
        refined = []
        for pattern_type, group in grouped.items():
            if len(group) >= 2:
                # Multiple instances increase confidence
                avg_confidence = np.mean([p.confidence for p in group])
                merged = DesignPattern(
                    pattern_type=pattern_type,
                    confidence=min(avg_confidence * 1.2, 0.95),
                    properties=group[0].properties,
                    examples=[ex for p in group for ex in p.examples]
                )
                refined.append(merged)
            else:
                refined.extend(group)
        
        return refined
    
    def _merge_vision_patterns(self, cv_patterns: List[DesignPattern], 
                             vision_result: VisionResult) -> List[DesignPattern]:
        """Merge CV patterns with Vision API results"""
        # Extract patterns from vision result
        ui_elements = vision_result.content.get('ui_elements', [])
        
        # Merge logic here
        return cv_patterns
    
    async def extract_design_system(self, image_paths: List[str]) -> Dict[str, Any]:
        """Extract complete design system from multiple screenshots"""
        design_system = {
            'colors': None,
            'typography': {},
            'spacing': [],
            'components': {},
            'patterns': {},
            'grid': None
        }
        
        all_colors = []
        all_patterns = []
        
        for image_path in image_paths:
            # Extract colors
            palette = await self.analyze_color_palette(image_path)
            all_colors.append(palette)
            
            # Extract patterns
            patterns = await self.analyze_ui_patterns(image_path)
            all_patterns.extend(patterns)
            
            # Extract typography
            typography = await self._extract_typography(image_path)
            design_system['typography'].update(typography)
            
            # Detect grid system
            grid = self._detect_grid_system(image_path)
            if grid:
                design_system['grid'] = grid
        
        # Consolidate design system
        design_system['colors'] = self._consolidate_colors(all_colors)
        design_system['components'] = self._extract_components(all_patterns)
        design_system['spacing'] = self._extract_spacing_system(all_patterns)
        
        return design_system
    
    async def analyze_color_palette(self, image_path: str) -> ColorPalette:
        """Extract color palette from image"""
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Reshape to pixels
        pixels = image_rgb.reshape(-1, 3)
        
        # Use k-means to find dominant colors
        n_colors = 10
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
        kmeans.fit(pixels)
        
        # Get color frequencies
        labels = kmeans.labels_
        label_counts = Counter(labels)
        
        # Sort colors by frequency
        colors = []
        for label, count in label_counts.most_common():
            rgb = kmeans.cluster_centers_[label]
            hex_color = '#%02x%02x%02x' % tuple(int(c) for c in rgb)
            percentage = count / len(pixels)
            colors.append({
                'hex': hex_color,
                'rgb': rgb,
                'percentage': percentage,
                'usage': self._classify_color_usage(rgb, percentage)
            })
        
        # Classify colors
        palette = self._classify_palette(colors)
        
        # Detect semantic colors
        palette.semantic = self._detect_semantic_colors(colors)
        
        return palette
    
    def _classify_color_usage(self, rgb: np.ndarray, percentage: float) -> str:
        """Classify how a color is used"""
        r, g, b = rgb
        
        # Convert to HSV
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        
        # Background colors are usually light and dominant
        if percentage > 0.3 and v > 0.9:
            return 'background'
        
        # Text colors are usually dark and less dominant
        if percentage < 0.1 and v < 0.3:
            return 'text'
        
        # Accent colors are vibrant and rare
        if percentage < 0.05 and s > 0.5:
            return 'accent'
        
        return 'primary' if percentage > 0.1 else 'secondary'
    
    def _classify_palette(self, colors: List[Dict]) -> ColorPalette:
        """Classify colors into palette categories"""
        background = '#ffffff'
        text = '#000000'
        primary = None
        secondary = []
        accent = []
        
        for color in colors:
            usage = color['usage']
            if usage == 'background':
                background = color['hex']
            elif usage == 'text':
                text = color['hex']
            elif usage == 'primary' and not primary:
                primary = color['hex']
            elif usage == 'accent':
                accent.append(color['hex'])
            else:
                secondary.append(color['hex'])
        
        # Ensure we have a primary color
        if not primary and colors:
            primary = colors[0]['hex']
        
        return ColorPalette(
            primary=primary or '#000000',
            secondary=secondary[:3],
            accent=accent[:2],
            background=background,
            text=text,
            semantic={}
        )
    
    def _detect_semantic_colors(self, colors: List[Dict]) -> Dict[str, str]:
        """Detect semantic colors (success, error, warning, info)"""
        semantic = {}
        
        for color in colors:
            rgb = color['rgb']
            h, s, v = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
            
            # Green for success (h: 0.25-0.42)
            if 0.25 <= h <= 0.42 and s > 0.3:
                semantic['success'] = color['hex']
            
            # Red for error (h: 0-0.08 or 0.92-1)
            elif (h <= 0.08 or h >= 0.92) and s > 0.3:
                semantic['error'] = color['hex']
            
            # Yellow/Orange for warning (h: 0.08-0.17)
            elif 0.08 <= h <= 0.17 and s > 0.3:
                semantic['warning'] = color['hex']
            
            # Blue for info (h: 0.5-0.67)
            elif 0.5 <= h <= 0.67 and s > 0.3:
                semantic['info'] = color['hex']
        
        return semantic
    
    async def _extract_typography(self, image_path: str) -> Dict[str, Any]:
        """Extract typography information"""
        # Extract text regions
        text_data = await self.engine.extract_text_with_layout(image_path)
        
        typography = {}
        
        # Analyze text regions
        for block_num, block in text_data.get('blocks', {}).items():
            for par_num, paragraph in block.items():
                for item in paragraph:
                    # Estimate font size from height
                    height = item['height']
                    estimated_size = int(height * 0.75)  # Rough estimate
                    
                    # Classify text type
                    if estimated_size > 32:
                        text_type = 'heading1'
                    elif estimated_size > 24:
                        text_type = 'heading2'
                    elif estimated_size > 20:
                        text_type = 'heading3'
                    elif estimated_size > 16:
                        text_type = 'heading4'
                    else:
                        text_type = 'body'
                    
                    if text_type not in typography:
                        typography[text_type] = {
                            'size': estimated_size,
                            'examples': []
                        }
                    
                    typography[text_type]['examples'].append(item['text'])
        
        return typography
    
    def _detect_grid_system(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Detect grid system in layout"""
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect vertical lines
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
        
        if lines is None:
            return None
        
        # Group vertical lines
        vertical_lines = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(x2 - x1) < 10:  # Nearly vertical
                vertical_lines.append((x1 + x2) // 2)
        
        if len(vertical_lines) < 2:
            return None
        
        # Find regular spacing
        vertical_lines.sort()
        spacings = [vertical_lines[i+1] - vertical_lines[i] for i in range(len(vertical_lines)-1)]
        
        # Check for consistent spacing
        if spacings:
            common_spacing = Counter(spacings).most_common(1)[0][0]
            consistency = sum(1 for s in spacings if abs(s - common_spacing) < 10) / len(spacings)
            
            if consistency > 0.7:
                return {
                    'type': 'column',
                    'columns': len(vertical_lines),
                    'gutter': common_spacing,
                    'consistency': consistency
                }
        
        return None
    
    def _consolidate_colors(self, all_colors: List[ColorPalette]) -> ColorPalette:
        """Consolidate colors from multiple images"""
        if not all_colors:
            return ColorPalette(
                primary='#000000',
                secondary=[],
                accent=[],
                background='#ffffff',
                text='#000000',
                semantic={}
            )
        
        # Count occurrences
        primary_colors = Counter(p.primary for p in all_colors)
        background_colors = Counter(p.background for p in all_colors)
        text_colors = Counter(p.text for p in all_colors)
        
        # Merge semantic colors
        semantic = {}
        for palette in all_colors:
            semantic.update(palette.semantic)
        
        # Get most common
        return ColorPalette(
            primary=primary_colors.most_common(1)[0][0],
            secondary=list(set(c for p in all_colors for c in p.secondary))[:3],
            accent=list(set(c for p in all_colors for c in p.accent))[:2],
            background=background_colors.most_common(1)[0][0],
            text=text_colors.most_common(1)[0][0],
            semantic=semantic
        )
    
    def _extract_components(self, patterns: List[DesignPattern]) -> Dict[str, List[Dict]]:
        """Extract reusable components from patterns"""
        components = defaultdict(list)
        
        # Group by pattern type
        for pattern in patterns:
            component = {
                'confidence': pattern.confidence,
                'properties': pattern.properties,
                'instances': len(pattern.examples)
            }
            components[pattern.pattern_type].append(component)
        
        # Consolidate similar components
        for comp_type in components:
            components[comp_type] = self._consolidate_components(components[comp_type])
        
        return dict(components)
    
    def _consolidate_components(self, components: List[Dict]) -> List[Dict]:
        """Consolidate similar components"""
        # Group by properties
        grouped = defaultdict(list)
        for comp in components:
            prop_key = json.dumps(comp['properties'], sort_keys=True)
            grouped[prop_key].append(comp)
        
        # Merge groups
        consolidated = []
        for prop_key, group in grouped.items():
            merged = {
                'properties': group[0]['properties'],
                'confidence': np.mean([c['confidence'] for c in group]),
                'instances': sum(c['instances'] for c in group)
            }
            consolidated.append(merged)
        
        return consolidated
    
    def _extract_spacing_system(self, patterns: List[DesignPattern]) -> List[int]:
        """Extract spacing system from patterns"""
        spacings = []
        
        # Get all bounding boxes
        all_boxes = []
        for pattern in patterns:
            all_boxes.extend(pattern.examples)
        
        # Calculate spacings between elements
        for i, box1 in enumerate(all_boxes):
            for box2 in all_boxes[i+1:]:
                # Horizontal spacing
                h_space = min(abs(box1[0] - box2[2]), abs(box2[0] - box1[2]))
                if 4 <= h_space <= 64:
                    spacings.append(h_space)
                
                # Vertical spacing
                v_space = min(abs(box1[1] - box2[3]), abs(box2[1] - box1[3]))
                if 4 <= v_space <= 64:
                    spacings.append(v_space)
        
        # Find common spacings
        spacing_counts = Counter(spacings)
        common_spacings = [s for s, count in spacing_counts.most_common(10) if count > 2]
        
        # Round to common values
        standard_spacings = [4, 8, 12, 16, 20, 24, 32, 40, 48, 56, 64]
        final_spacings = []
        for spacing in common_spacings:
            closest = min(standard_spacings, key=lambda x: abs(x - spacing))
            if abs(closest - spacing) <= 2:
                final_spacings.append(closest)
        
        return sorted(set(final_spacings))
    
    async def analyze_accessibility(self, image_path: str) -> List[AccessibilityIssue]:
        """Analyze image for accessibility issues"""
        issues = []
        
        # Load image
        image = cv2.imread(image_path)
        pil_image = Image.open(image_path)
        
        # Extract colors
        palette = await self.analyze_color_palette(image_path)
        
        # Check color contrast
        contrast_issues = self._check_color_contrast(palette, image)
        issues.extend(contrast_issues)
        
        # Check text size
        text_issues = await self._check_text_size(image_path)
        issues.extend(text_issues)
        
        # Check touch targets
        touch_issues = await self._check_touch_targets(image_path)
        issues.extend(touch_issues)
        
        # Check for alt text indicators
        alt_text_issues = self._check_alt_text_indicators(image)
        issues.extend(alt_text_issues)
        
        return issues
    
    def _check_color_contrast(self, palette: ColorPalette, image: np.ndarray) -> List[AccessibilityIssue]:
        """Check color contrast ratios"""
        issues = []
        
        # Calculate contrast between text and background
        text_rgb = self._hex_to_rgb(palette.text)
        bg_rgb = self._hex_to_rgb(palette.background)
        contrast_ratio = self._calculate_contrast_ratio(text_rgb, bg_rgb)
        
        if contrast_ratio < 4.5:
            issues.append(AccessibilityIssue(
                issue_type='color_contrast',
                severity='high',
                location=(0, 0, image.shape[1], image.shape[0]),
                description=f'Text/background contrast ratio {contrast_ratio:.2f} is below WCAG AA standard (4.5:1)',
                suggestion='Increase contrast between text and background colors'
            ))
        
        return issues
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _calculate_contrast_ratio(self, rgb1: Tuple[int, int, int], 
                                 rgb2: Tuple[int, int, int]) -> float:
        """Calculate WCAG contrast ratio"""
        def relative_luminance(rgb):
            r, g, b = [x/255.0 for x in rgb]
            r = r/12.92 if r <= 0.03928 else ((r+0.055)/1.055)**2.4
            g = g/12.92 if g <= 0.03928 else ((g+0.055)/1.055)**2.4
            b = b/12.92 if b <= 0.03928 else ((b+0.055)/1.055)**2.4
            return 0.2126*r + 0.7152*g + 0.0722*b
        
        l1 = relative_luminance(rgb1)
        l2 = relative_luminance(rgb2)
        
        lighter = max(l1, l2)
        darker = min(l1, l2)
        
        return (lighter + 0.05) / (darker + 0.05)
    
    async def _check_text_size(self, image_path: str) -> List[AccessibilityIssue]:
        """Check text size for readability"""
        issues = []
        
        # Extract text regions
        text_data = await self.engine.extract_text_with_layout(image_path)
        
        for block_num, block in text_data.get('blocks', {}).items():
            for par_num, paragraph in block.items():
                for item in paragraph:
                    height = item['height']
                    
                    # Check minimum text size (roughly 12px)
                    if height < 16:  # Accounting for line height
                        issues.append(AccessibilityIssue(
                            issue_type='text_size',
                            severity='medium',
                            location=(item['left'], item['top'], 
                                    item['left'] + item['width'], 
                                    item['top'] + item['height']),
                            description=f'Text size (~{int(height*0.75)}px) may be too small',
                            suggestion='Use minimum 16px for body text'
                        ))
        
        return issues
    
    async def _check_touch_targets(self, image_path: str) -> List[AccessibilityIssue]:
        """Check touch target sizes"""
        issues = []
        
        # Get UI patterns
        patterns = await self.analyze_ui_patterns(image_path)
        
        for pattern in patterns:
            if pattern.pattern_type in ['button', 'input', 'checkbox', 'radio']:
                for bounds in pattern.examples:
                    x1, y1, x2, y2 = bounds
                    width = x2 - x1
                    height = y2 - y1
                    
                    # WCAG recommends 44x44 pixels minimum
                    if width < 44 or height < 44:
                        issues.append(AccessibilityIssue(
                            issue_type='touch_target',
                            severity='high',
                            location=bounds,
                            description=f'Touch target ({width}x{height}) is below 44x44 minimum',
                            suggestion='Increase touch target size to at least 44x44 pixels'
                        ))
        
        return issues
    
    def _check_alt_text_indicators(self, image: np.ndarray) -> List[AccessibilityIssue]:
        """Check for images that might need alt text"""
        issues = []
        
        # This is a placeholder - in reality, would need more sophisticated detection
        # Could use object detection to find images within the UI
        
        return issues
    
    async def analyze_performance_metrics(self, image_path: str) -> Dict[str, Any]:
        """Extract performance metrics from screenshots"""
        metrics = {
            'visual_complexity': 0,
            'element_count': 0,
            'text_density': 0,
            'image_optimization': {},
            'render_blocking_elements': []
        }
        
        # Load image
        image = cv2.imread(image_path)
        
        # Calculate visual complexity
        metrics['visual_complexity'] = self._calculate_visual_complexity(image)
        
        # Count UI elements
        patterns = await self.analyze_ui_patterns(image_path)
        metrics['element_count'] = sum(len(p.examples) for p in patterns)
        
        # Calculate text density
        text_data = await self.engine.extract_text_with_layout(image_path)
        metrics['text_density'] = self._calculate_text_density(text_data, image.shape)
        
        # Check for large images
        metrics['image_optimization'] = self._check_image_optimization(image)
        
        return metrics
    
    def _calculate_visual_complexity(self, image: np.ndarray) -> float:
        """Calculate visual complexity score"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate edges
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Calculate color variance
        b, g, r = cv2.split(image)
        color_variance = (np.var(b) + np.var(g) + np.var(r)) / 3
        
        # Normalize and combine
        complexity = (edge_density * 0.5 + min(color_variance / 10000, 1) * 0.5)
        
        return complexity
    
    def _calculate_text_density(self, text_data: Dict, image_shape: Tuple) -> float:
        """Calculate text density on page"""
        total_text_area = 0
        image_area = image_shape[0] * image_shape[1]
        
        for block_num, block in text_data.get('blocks', {}).items():
            for par_num, paragraph in block.items():
                for item in paragraph:
                    if item['text'].strip():
                        total_text_area += item['width'] * item['height']
        
        return total_text_area / image_area if image_area > 0 else 0
    
    def _check_image_optimization(self, image: np.ndarray) -> Dict[str, Any]:
        """Check for image optimization opportunities"""
        h, w = image.shape[:2]
        
        return {
            'dimensions': f'{w}x{h}',
            'estimated_size': w * h * 3 / 1024,  # KB estimate
            'optimization_suggestions': []
        }
    
    async def visual_diff(self, before_path: str, after_path: str) -> Dict[str, Any]:
        """Compare two images and highlight differences"""
        # Use vision engine for basic comparison
        diff_data = await self.engine.compare_images(before_path, after_path)
        
        # Load images for detailed analysis
        before = cv2.imread(before_path)
        after = cv2.imread(after_path)
        
        # Ensure same size
        if before.shape != after.shape:
            after = cv2.resize(after, (before.shape[1], before.shape[0]))
        
        # Calculate detailed diff
        diff = cv2.absdiff(before, after)
        
        # Create diff visualization
        diff_viz = self._create_diff_visualization(before, after, diff)
        
        # Save diff image
        diff_path = self.cache_dir / f"diff_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        cv2.imwrite(str(diff_path), diff_viz)
        
        # Analyze what changed
        changes = await self._analyze_changes(before_path, after_path, diff_data['differences'])
        
        return {
            'similarity': diff_data['similarity'],
            'differences_count': len(diff_data['differences']),
            'diff_image': str(diff_path),
            'changes': changes
        }
    
    def _create_diff_visualization(self, before: np.ndarray, after: np.ndarray, 
                                 diff: np.ndarray) -> np.ndarray:
        """Create visual diff with highlights"""
        # Create a copy of after image
        viz = after.copy()
        
        # Convert diff to grayscale and threshold
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)
        
        # Dilate to connect nearby changes
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=2)
        
        # Find contours of changes
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Draw rectangles around changes
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(viz, (x, y), (x+w, y+h), (0, 0, 255), 2)
        
        return viz
    
    async def _analyze_changes(self, before_path: str, after_path: str, 
                             differences: List[Dict]) -> List[Dict[str, str]]:
        """Analyze what changed between images"""
        changes = []
        
        # Get UI patterns before and after
        patterns_before = await self.analyze_ui_patterns(before_path)
        patterns_after = await self.analyze_ui_patterns(after_path)
        
        # Compare patterns
        before_types = Counter(p.pattern_type for p in patterns_before)
        after_types = Counter(p.pattern_type for p in patterns_after)
        
        # Find added/removed elements
        for pattern_type in set(before_types.keys()) | set(after_types.keys()):
            before_count = before_types.get(pattern_type, 0)
            after_count = after_types.get(pattern_type, 0)
            
            if after_count > before_count:
                changes.append({
                    'type': 'added',
                    'element': pattern_type,
                    'count': after_count - before_count
                })
            elif before_count > after_count:
                changes.append({
                    'type': 'removed',
                    'element': pattern_type,
                    'count': before_count - after_count
                })
        
        # Analyze color changes
        palette_before = await self.analyze_color_palette(before_path)
        palette_after = await self.analyze_color_palette(after_path)
        
        if palette_before.primary != palette_after.primary:
            changes.append({
                'type': 'color_change',
                'element': 'primary_color',
                'from': palette_before.primary,
                'to': palette_after.primary
            })
        
        return changes


if __name__ == "__main__":
    # Example usage
    async def main():
        analyzer = NexusVisionAnalyzer()
        
        # Test pattern detection
        patterns = await analyzer.analyze_ui_patterns("screenshot.png")
        print(f"Detected patterns: {[p.pattern_type for p in patterns]}")
        
        # Test color extraction
        palette = await analyzer.analyze_color_palette("screenshot.png")
        print(f"Color palette: Primary={palette.primary}, Background={palette.background}")
        
        # Test accessibility
        issues = await analyzer.analyze_accessibility("screenshot.png")
        print(f"Accessibility issues: {len(issues)}")
    
    asyncio.run(main())