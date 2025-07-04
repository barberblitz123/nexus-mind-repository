#!/usr/bin/env python3
"""
NEXUS YouTube Scraper with Self-Enhancement Capability
Recognizes limitations and identifies what it needs to accomplish tasks
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import re
import traceback

# Core dependencies
try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SelfEnhancementCapability:
    """Tracks missing capabilities and requirements"""
    
    def __init__(self):
        self.missing_capabilities = []
        self.required_packages = []
        self.suggested_solutions = []
        self.enhancement_log = []
    
    def add_missing_capability(self, capability: str, package: str = None, solution: str = None):
        """Record a missing capability"""
        entry = {
            "capability": capability,
            "package": package,
            "solution": solution,
            "timestamp": datetime.now().isoformat()
        }
        self.missing_capabilities.append(entry)
        
        if package and package not in self.required_packages:
            self.required_packages.append(package)
        
        if solution and solution not in self.suggested_solutions:
            self.suggested_solutions.append(solution)
        
        self.enhancement_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Missing: {capability}")
    
    def get_enhancement_report(self) -> Dict[str, Any]:
        """Generate a report of what's needed for enhancement"""
        return {
            "status": "enhancement_needed",
            "missing_capabilities": self.missing_capabilities,
            "required_packages": self.required_packages,
            "suggested_solutions": self.suggested_solutions,
            "installation_commands": self._generate_install_commands(),
            "enhancement_log": self.enhancement_log
        }
    
    def _generate_install_commands(self) -> List[str]:
        """Generate installation commands for missing packages"""
        commands = []
        
        if self.required_packages:
            # Basic pip install
            commands.append(f"pip install {' '.join(self.required_packages)}")
            
            # Individual installs with specific versions if needed
            for package in self.required_packages:
                if package == "yt-dlp":
                    commands.append("pip install yt-dlp[default]")
                elif package == "playwright":
                    commands.append("pip install playwright && playwright install chromium")
                elif package == "selenium":
                    commands.append("pip install selenium webdriver-manager")
        
        return commands


class NexusYouTubeScraper:
    """YouTube scraper with self-enhancement awareness"""
    
    def __init__(self):
        self.enhancement = SelfEnhancementCapability()
        self.capabilities = self._check_capabilities()
        self._init_components()
    
    def _check_capabilities(self) -> Dict[str, bool]:
        """Check available capabilities"""
        capabilities = {
            "yt_dlp": YTDLP_AVAILABLE,
            "httpx": HTTPX_AVAILABLE,
            "beautifulsoup": BS4_AVAILABLE,
            "transcript_extraction": False,
            "comment_extraction": False,
            "playlist_support": False,
            "live_stream_support": False
        }
        
        # Check for transcript capability
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            capabilities["transcript_extraction"] = True
        except ImportError:
            pass
        
        # Check for advanced features
        if YTDLP_AVAILABLE:
            capabilities["playlist_support"] = True
            capabilities["comment_extraction"] = True
            capabilities["live_stream_support"] = True
        
        return capabilities
    
    def _init_components(self):
        """Initialize available components"""
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'force_generic_extractor': False,
        } if YTDLP_AVAILABLE else None
    
    async def scrape_video(self, url: str, extract_options: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
        """
        Scrape YouTube video with self-enhancement awareness
        
        Args:
            url: YouTube video URL
            extract_options: What to extract (transcript, comments, etc.)
        
        Returns:
            Result dict with data or enhancement requirements
        """
        extract_options = extract_options or {
            "transcript": True,
            "comments": False,
            "related_videos": True,
            "metadata": True
        }
        
        # Validate URL
        if not self._is_youtube_url(url):
            return {
                "success": False,
                "error": "Invalid YouTube URL",
                "url": url
            }
        
        # Check if we can handle the request
        can_proceed, requirements = self._can_handle_request(extract_options)
        
        if not can_proceed:
            # Return enhancement requirements
            report = self.enhancement.get_enhancement_report()
            report["original_request"] = {
                "url": url,
                "options": extract_options
            }
            report["message"] = "I need additional capabilities to complete this task. Here's what I need:"
            return report
        
        # Proceed with scraping
        try:
            result = await self._perform_scraping(url, extract_options)
            return result
        except Exception as e:
            # Analyze the error and suggest enhancements
            return self._handle_scraping_error(e, url, extract_options)
    
    def _is_youtube_url(self, url: str) -> bool:
        """Validate YouTube URL"""
        youtube_patterns = [
            r'(https?://)?(www\.)?(youtube\.com/(watch\?v=|embed/|v/)|youtu\.be/)',
            r'(https?://)?(www\.)?(youtube\.com/playlist\?list=)',
            r'(https?://)?(www\.)?(youtube\.com/channel/)',
            r'(https?://)?(www\.)?(youtube\.com/c/)',
        ]
        
        return any(re.match(pattern, url) for pattern in youtube_patterns)
    
    def _can_handle_request(self, options: Dict[str, bool]) -> Tuple[bool, List[str]]:
        """Check if we can handle the requested extraction"""
        missing = []
        
        # Basic video metadata - always possible with yt-dlp
        if not self.capabilities["yt_dlp"]:
            self.enhancement.add_missing_capability(
                "Basic video metadata extraction",
                "yt-dlp",
                "Install yt-dlp for video metadata extraction"
            )
            missing.append("yt-dlp")
        
        # Transcript extraction
        if options.get("transcript", False) and not self.capabilities["transcript_extraction"]:
            self.enhancement.add_missing_capability(
                "Transcript/subtitle extraction",
                "youtube-transcript-api",
                "Install youtube-transcript-api for transcript extraction"
            )
            missing.append("youtube-transcript-api")
        
        # Comments extraction
        if options.get("comments", False) and not self.capabilities["comment_extraction"]:
            self.enhancement.add_missing_capability(
                "Comment extraction",
                "yt-dlp",
                "yt-dlp supports comment extraction with --write-comments flag"
            )
            if not self.capabilities["yt_dlp"]:
                missing.append("yt-dlp")
        
        # Advanced scraping fallback
        if not self.capabilities["httpx"] or not self.capabilities["beautifulsoup"]:
            self.enhancement.add_missing_capability(
                "Fallback web scraping",
                "httpx beautifulsoup4 lxml",
                "Install httpx and beautifulsoup4 for fallback scraping"
            )
            missing.extend(["httpx", "beautifulsoup4", "lxml"])
        
        return len(missing) == 0, missing
    
    async def _perform_scraping(self, url: str, options: Dict[str, bool]) -> Dict[str, Any]:
        """Perform the actual scraping"""
        result = {
            "success": True,
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "data": {}
        }
        
        # Extract video ID
        video_id = self._extract_video_id(url)
        if video_id:
            result["video_id"] = video_id
        
        # Get metadata using yt-dlp
        if self.capabilities["yt_dlp"] and options.get("metadata", True):
            try:
                metadata = await self._get_video_metadata(url)
                result["data"]["metadata"] = metadata
            except Exception as e:
                logger.warning(f"Metadata extraction failed: {e}")
                result["warnings"] = result.get("warnings", [])
                result["warnings"].append(f"Metadata extraction failed: {str(e)}")
        
        # Get transcript
        if options.get("transcript", False):
            if self.capabilities["transcript_extraction"]:
                try:
                    transcript = await self._get_transcript(video_id)
                    result["data"]["transcript"] = transcript
                except Exception as e:
                    logger.warning(f"Transcript extraction failed: {e}")
                    result["warnings"] = result.get("warnings", [])
                    result["warnings"].append(f"Transcript extraction failed: {str(e)}")
            else:
                result["data"]["transcript"] = {
                    "available": False,
                    "reason": "youtube-transcript-api not installed"
                }
        
        # Get comments (if requested)
        if options.get("comments", False):
            if self.capabilities["yt_dlp"]:
                try:
                    comments = await self._get_comments(url)
                    result["data"]["comments"] = comments
                except Exception as e:
                    logger.warning(f"Comment extraction failed: {e}")
                    result["warnings"] = result.get("warnings", [])
                    result["warnings"].append(f"Comment extraction failed: {str(e)}")
            else:
                result["data"]["comments"] = {
                    "available": False,
                    "reason": "yt-dlp not installed or comments disabled"
                }
        
        return result
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def _get_video_metadata(self, url: str) -> Dict[str, Any]:
        """Get video metadata using yt-dlp"""
        if not YTDLP_AVAILABLE:
            raise ImportError("yt-dlp not available")
        
        # Run in thread pool since yt-dlp is sync
        loop = asyncio.get_event_loop()
        
        def extract_info():
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        
        info = await loop.run_in_executor(None, extract_info)
        
        # Extract relevant metadata
        return {
            "title": info.get("title", ""),
            "description": info.get("description", ""),
            "duration": info.get("duration", 0),
            "upload_date": info.get("upload_date", ""),
            "uploader": info.get("uploader", ""),
            "view_count": info.get("view_count", 0),
            "like_count": info.get("like_count", 0),
            "thumbnail": info.get("thumbnail", ""),
            "tags": info.get("tags", []),
            "categories": info.get("categories", []),
        }
    
    async def _get_transcript(self, video_id: str) -> Dict[str, Any]:
        """Get video transcript"""
        from youtube_transcript_api import YouTubeTranscriptApi
        
        try:
            # Get available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try to get English transcript first
            try:
                transcript = transcript_list.find_transcript(['en'])
                data = transcript.fetch()
            except:
                # Get any available transcript
                transcript = transcript_list.find_manually_created_transcript()
                if not transcript:
                    transcript = transcript_list.find_generated_transcript()
                data = transcript.fetch() if transcript else []
            
            # Format transcript
            full_text = " ".join([entry['text'] for entry in data])
            
            return {
                "available": True,
                "language": transcript.language if transcript else "unknown",
                "full_text": full_text,
                "segments": data[:10],  # First 10 segments as sample
                "total_segments": len(data)
            }
        except Exception as e:
            logger.error(f"Transcript extraction error: {e}")
            return {
                "available": False,
                "error": str(e)
            }
    
    async def _get_comments(self, url: str) -> Dict[str, Any]:
        """Get video comments using yt-dlp"""
        if not YTDLP_AVAILABLE:
            return {"available": False, "reason": "yt-dlp not available"}
        
        # Configure yt-dlp for comment extraction
        opts = self.ydl_opts.copy()
        opts['getcomments'] = True
        opts['skip_download'] = True
        
        loop = asyncio.get_event_loop()
        
        def extract_comments():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get('comments', [])
        
        try:
            comments = await loop.run_in_executor(None, extract_comments)
            
            # Process and limit comments
            processed_comments = []
            for comment in comments[:50]:  # Limit to first 50
                processed_comments.append({
                    "author": comment.get("author", ""),
                    "text": comment.get("text", ""),
                    "likes": comment.get("like_count", 0),
                    "time": comment.get("timestamp", 0)
                })
            
            return {
                "available": True,
                "count": len(comments),
                "sample": processed_comments
            }
        except Exception as e:
            logger.error(f"Comment extraction error: {e}")
            return {
                "available": False,
                "error": str(e)
            }
    
    def _handle_scraping_error(self, error: Exception, url: str, options: Dict[str, bool]) -> Dict[str, Any]:
        """Analyze error and suggest enhancements"""
        error_str = str(error)
        error_type = type(error).__name__
        
        # Common error patterns and solutions
        if "HTTPSConnectionPool" in error_str or "SSL" in error_str:
            self.enhancement.add_missing_capability(
                "SSL/HTTPS handling",
                "certifi",
                "Install certifi for SSL certificate handling"
            )
        
        elif "403" in error_str or "429" in error_str:
            self.enhancement.add_missing_capability(
                "Rate limiting and authentication",
                "yt-dlp",
                "Use yt-dlp with cookies or authentication for better access"
            )
        
        elif "AttributeError" in error_str and "NoneType" in error_str:
            self.enhancement.add_missing_capability(
                "Robust HTML parsing",
                "beautifulsoup4 lxml",
                "Install beautifulsoup4 and lxml for better HTML parsing"
            )
        
        elif "ImportError" in error_str:
            # Extract package name from error
            import_match = re.search(r"No module named '([^']+)'", error_str)
            if import_match:
                package = import_match.group(1)
                self.enhancement.add_missing_capability(
                    f"Missing module: {package}",
                    package,
                    f"Install {package} to enable this functionality"
                )
        
        # Generate enhancement report
        report = self.enhancement.get_enhancement_report()
        report["error_details"] = {
            "type": error_type,
            "message": error_str,
            "traceback": traceback.format_exc(),
            "url": url,
            "requested_options": options
        }
        
        return report
    
    async def analyze_capabilities(self) -> Dict[str, Any]:
        """Analyze current capabilities and potential enhancements"""
        analysis = {
            "current_capabilities": self.capabilities,
            "enhancement_opportunities": [],
            "recommended_packages": [],
            "capability_matrix": {
                "basic_metadata": {
                    "status": "available" if self.capabilities["yt_dlp"] else "requires_installation",
                    "package": "yt-dlp",
                    "features": ["title", "description", "views", "likes", "duration"]
                },
                "transcripts": {
                    "status": "available" if self.capabilities["transcript_extraction"] else "requires_installation",
                    "package": "youtube-transcript-api",
                    "features": ["auto-captions", "manual-captions", "multi-language"]
                },
                "comments": {
                    "status": "available" if self.capabilities["yt_dlp"] else "requires_installation",
                    "package": "yt-dlp",
                    "features": ["comment-text", "author", "likes", "replies"]
                },
                "playlists": {
                    "status": "available" if self.capabilities["playlist_support"] else "requires_installation",
                    "package": "yt-dlp",
                    "features": ["playlist-videos", "playlist-metadata"]
                },
                "advanced_scraping": {
                    "status": "partial",
                    "packages": ["selenium", "playwright"],
                    "features": ["dynamic-content", "javascript-rendering", "interaction"]
                }
            }
        }
        
        # Add enhancement opportunities
        if not self.capabilities["yt_dlp"]:
            analysis["enhancement_opportunities"].append({
                "capability": "Core YouTube data extraction",
                "impact": "high",
                "effort": "low",
                "command": "pip install yt-dlp"
            })
        
        if not self.capabilities["transcript_extraction"]:
            analysis["enhancement_opportunities"].append({
                "capability": "Transcript and subtitle extraction",
                "impact": "high",
                "effort": "low",
                "command": "pip install youtube-transcript-api"
            })
        
        # Check for advanced capabilities
        try:
            import selenium
            analysis["capability_matrix"]["advanced_scraping"]["selenium"] = True
        except ImportError:
            analysis["enhancement_opportunities"].append({
                "capability": "Browser automation for complex scraping",
                "impact": "medium",
                "effort": "medium",
                "command": "pip install selenium webdriver-manager"
            })
        
        try:
            import playwright
            analysis["capability_matrix"]["advanced_scraping"]["playwright"] = True
        except ImportError:
            analysis["enhancement_opportunities"].append({
                "capability": "Modern browser automation",
                "impact": "medium",
                "effort": "medium",
                "command": "pip install playwright && playwright install"
            })
        
        return analysis


# Integration with NEXUS Agent System
class NexusYouTubeAgent:
    """NEXUS Agent wrapper for YouTube scraping with self-enhancement"""
    
    def __init__(self, agent_id: str = "youtube_scraper"):
        self.agent_id = agent_id
        self.scraper = NexusYouTubeScraper()
        self.task_queue = asyncio.Queue()
        self.results = {}
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a YouTube scraping task"""
        task_id = task.get("id", datetime.now().isoformat())
        task_type = task.get("type", "scrape_video")
        
        logger.info(f"Processing task {task_id}: {task_type}")
        
        try:
            if task_type == "scrape_video":
                result = await self.scraper.scrape_video(
                    task["url"],
                    task.get("options", {})
                )
            elif task_type == "analyze_capabilities":
                result = await self.scraper.analyze_capabilities()
            elif task_type == "batch_scrape":
                results = []
                for url in task["urls"]:
                    video_result = await self.scraper.scrape_video(url, task.get("options", {}))
                    results.append(video_result)
                result = {"batch_results": results}
            else:
                result = {
                    "success": False,
                    "error": f"Unknown task type: {task_type}"
                }
            
            # Store result
            self.results[task_id] = result
            
            # Check if enhancement is needed
            if result.get("status") == "enhancement_needed":
                logger.warning(f"Task {task_id} requires enhancements: {result['required_packages']}")
                # Could trigger an enhancement workflow here
            
            return result
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "task_id": task_id,
                "traceback": traceback.format_exc()
            }
            self.results[task_id] = error_result
            return error_result
    
    async def suggest_enhancement(self) -> Dict[str, Any]:
        """Suggest enhancements based on failed tasks"""
        enhancement_report = self.scraper.enhancement.get_enhancement_report()
        
        # Analyze failed tasks
        failed_tasks = []
        for task_id, result in self.results.items():
            if not result.get("success", True) or result.get("status") == "enhancement_needed":
                failed_tasks.append({
                    "task_id": task_id,
                    "reason": result.get("error", "Enhancement needed"),
                    "missing": result.get("required_packages", [])
                })
        
        enhancement_report["failed_tasks"] = failed_tasks
        enhancement_report["success_rate"] = len([r for r in self.results.values() if r.get("success", False)]) / max(len(self.results), 1)
        
        return enhancement_report


# CLI Testing Interface
async def main():
    """Test the YouTube scraper with self-enhancement"""
    import sys
    
    agent = NexusYouTubeAgent()
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
        
        # Test scraping
        print(f"🎥 Scraping YouTube video: {url}")
        result = await agent.process_task({
            "type": "scrape_video",
            "url": url,
            "options": {
                "transcript": True,
                "comments": True,
                "metadata": True
            }
        })
        
        if result.get("status") == "enhancement_needed":
            print("\n🔧 Enhancement Required!")
            print(f"Message: {result['message']}")
            print(f"\nMissing capabilities:")
            for cap in result["missing_capabilities"]:
                print(f"  - {cap['capability']}")
            
            print(f"\nRequired packages: {', '.join(result['required_packages'])}")
            print(f"\nInstallation commands:")
            for cmd in result["installation_commands"]:
                print(f"  $ {cmd}")
        else:
            print(f"\n✅ Scraping successful!")
            if "data" in result:
                if "metadata" in result["data"]:
                    meta = result["data"]["metadata"]
                    print(f"Title: {meta.get('title', 'N/A')}")
                    print(f"Duration: {meta.get('duration', 0)} seconds")
                    print(f"Views: {meta.get('view_count', 0)}")
    else:
        # Run capability analysis
        print("🔍 Analyzing YouTube scraping capabilities...")
        analysis = await agent.scraper.analyze_capabilities()
        
        print("\n📊 Current Capabilities:")
        for cap, status in analysis["current_capabilities"].items():
            print(f"  {cap}: {'✅' if status else '❌'}")
        
        print("\n🚀 Enhancement Opportunities:")
        for opp in analysis["enhancement_opportunities"]:
            print(f"\n  {opp['capability']}")
            print(f"  Impact: {opp['impact']}, Effort: {opp['effort']}")
            print(f"  Install: {opp['command']}")


if __name__ == "__main__":
    asyncio.run(main())