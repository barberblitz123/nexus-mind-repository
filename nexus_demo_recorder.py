#!/usr/bin/env python3
"""
NEXUS Demo Recorder - Capture impressive demos as video/GIF
"""

import subprocess
import sys
import os
import time
from pathlib import Path
from datetime import datetime

class DemoRecorder:
    """Record NEXUS demos for sharing"""
    
    def __init__(self):
        self.output_dir = Path("nexus_demo_output/recordings")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def check_dependencies(self):
        """Check if recording tools are available"""
        tools = {
            'asciinema': 'pip install asciinema',
            'ffmpeg': 'Please install ffmpeg from https://ffmpeg.org/',
            'imagemagick': 'Please install ImageMagick for GIF creation'
        }
        
        missing = []
        for tool, install_msg in tools.items():
            if not self.is_tool_available(tool):
                missing.append((tool, install_msg))
                
        if missing:
            print("📦 Missing dependencies for recording:")
            for tool, msg in missing:
                print(f"  - {tool}: {msg}")
            return False
        return True
        
    def is_tool_available(self, tool):
        """Check if a command-line tool is available"""
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=False)
            return True
        except FileNotFoundError:
            return False
            
    def record_asciinema(self):
        """Record terminal session with asciinema"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        recording_path = self.output_dir / f"nexus_demo_{timestamp}.cast"
        
        print("🎬 Starting asciinema recording...")
        print("📝 Press Ctrl+D when done recording")
        
        # Record the demo
        subprocess.run([
            "asciinema", "rec",
            "--title", "NEXUS Mind - Voice-Driven Development Demo",
            "--idle-time-limit", "2",
            str(recording_path)
        ])
        
        return recording_path
        
    def convert_to_gif(self, cast_file):
        """Convert asciinema recording to GIF"""
        gif_path = cast_file.with_suffix('.gif')
        svg_path = cast_file.with_suffix('.svg')
        
        print("🎨 Converting to GIF...")
        
        # First convert to SVG
        subprocess.run([
            "asciinema", "convert",
            str(cast_file),
            str(svg_path)
        ])
        
        # Then to GIF using ImageMagick
        if self.is_tool_available("convert"):
            subprocess.run([
                "convert",
                "-density", "200",
                "-delay", "10",
                "-loop", "0",
                str(svg_path),
                str(gif_path)
            ])
            
            print(f"✅ GIF created: {gif_path}")
            return gif_path
            
    def create_video_script(self):
        """Create a script for video recording with OBS or similar"""
        script_content = """# NEXUS Demo Video Recording Script

## Setup (Before Recording)
1. Set resolution to 1920x1080
2. Use dark terminal theme
3. Increase font size to 16-18pt
4. Clear terminal history

## Recording Steps

### 1. Introduction (0:00-0:30)
- Show NEXUS logo animation
- Brief explanation of voice-driven development

### 2. Voice Command Demo (0:30-1:00)
- Say: "Create a task management app with authentication"
- Show voice waveform visualization
- Display command recognition

### 3. Architecture Generation (1:00-1:30)
- Show project tree creation
- Highlight file structure

### 4. Code Generation (1:30-2:30)
- Display React components
- Show FastAPI backend
- Syntax highlighting animation

### 5. UI Preview (2:30-3:00)
- Show mockup visualization
- Highlight responsive design

### 6. Testing Suite (3:00-3:30)
- Run automated tests
- Show test results table

### 7. Deployment (3:30-4:00)
- One-click deployment animation
- Show live URL

### 8. Metrics & Comparison (4:00-4:30)
- Performance metrics
- Speed comparison table

### 9. Customization (4:30-5:00)
- Live theme change
- Feature additions

## Post-Production
- Add background music (optional)
- Include captions for voice commands
- Export as MP4 (H.264, 60fps)
"""
        
        script_path = self.output_dir / "video_recording_script.md"
        script_path.write_text(script_content)
        print(f"📋 Video script saved: {script_path}")
        
    def create_sharing_package(self):
        """Create a complete sharing package"""
        package_dir = self.output_dir / "sharing_package"
        package_dir.mkdir(exist_ok=True)
        
        # Social media templates
        social_content = {
            "twitter.txt": """🚀 Just witnessed the future of coding! 

NEXUS created a full-stack app in 5 seconds from a single voice command 🎤

✅ Authentication system
✅ Real-time updates  
✅ Beautiful UI
✅ Automated tests
✅ Instant deployment

See it in action 👇
#NEXUSMind #AI #VoiceCoding #Future""",
            
            "linkedin.txt": """Revolutionizing Software Development with NEXUS Mind

I'm excited to share a demonstration of NEXUS, an AI system that transforms voice commands into fully-functional applications.

Key Highlights:
• Voice-driven development: Speak your requirements naturally
• Full-stack generation: Frontend, backend, and database in seconds
• Automated testing: Comprehensive test suites generated instantly
• One-click deployment: From idea to production in under 5 minutes

This isn't just faster development - it's a fundamental shift in how we create software.

Watch the demo and see the future of development.

#AI #SoftwareDevelopment #Innovation #Technology #NEXUS""",
            
            "youtube_description.txt": """NEXUS Mind - Voice-Driven Full-Stack Development Demo

Watch NEXUS create a complete task management application from a single voice command!

Timestamps:
00:00 - Introduction
00:30 - Voice Command Recognition
01:00 - Project Architecture Generation
01:30 - Full-Stack Code Generation
02:30 - UI/UX Design Preview
03:00 - Automated Testing
03:30 - One-Click Deployment
04:00 - Performance Metrics
04:30 - Live Customization

Features Demonstrated:
✅ Natural language understanding
✅ Instant architecture design
✅ Full-stack code generation
✅ Beautiful UI creation
✅ Automated testing
✅ Cloud deployment

Try NEXUS yourself:
GitHub: https://github.com/nexus-mind/nexus
Documentation: https://nexus-mind.dev/docs

#NEXUS #AI #VoiceCoding #FullStack #Demo"""
        }
        
        for filename, content in social_content.items():
            (package_dir / filename).write_text(content)
            
        print(f"📦 Sharing package created: {package_dir}")
        
def main():
    """Main recording workflow"""
    recorder = DemoRecorder()
    
    print("🎥 NEXUS Demo Recorder")
    print("=" * 40)
    
    # Check dependencies
    if not recorder.check_dependencies():
        print("\n⚠️  Please install missing dependencies first")
        return
        
    print("\nOptions:")
    print("1. Record terminal demo (asciinema)")
    print("2. Create video recording script")
    print("3. Generate sharing package")
    print("4. All of the above")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice in ['1', '4']:
        # Record demo
        cast_file = recorder.record_asciinema()
        if cast_file and cast_file.exists():
            print(f"\n✅ Recording saved: {cast_file}")
            
            # Optionally convert to GIF
            if input("\nConvert to GIF? (y/n): ").lower() == 'y':
                recorder.convert_to_gif(cast_file)
                
    if choice in ['2', '4']:
        recorder.create_video_script()
        
    if choice in ['3', '4']:
        recorder.create_sharing_package()
        
    print("\n✨ Done! Check the output directory for your files.")
    print(f"📁 Output location: {recorder.output_dir.absolute()}")

if __name__ == "__main__":
    main()