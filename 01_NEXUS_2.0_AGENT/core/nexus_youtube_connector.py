#!/usr/bin/env python3
"""
NEXUS YouTube Connector
Bridges the enhanced YouTube scraper with the NEXUS 2.0 agent system
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the enhanced YouTube scraper
from agents.nexus_youtube_scraper_enhanced import NexusYouTubeAgent, NexusYouTubeScraper

# Import NEXUS components
try:
    from nexus_connector import NexusConnector
    from nexus_logger import NexusLogger
    NEXUS_AVAILABLE = True
except ImportError:
    NEXUS_AVAILABLE = False
    print("Warning: NEXUS core components not found. Running in standalone mode.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YouTubeAgentConnector:
    """Connects YouTube scraping to NEXUS agent system"""
    
    def __init__(self):
        self.youtube_agent = NexusYouTubeAgent("youtube_scraper_001")
        self.logger = NexusLogger() if NEXUS_AVAILABLE else None
        self.active_tasks = {}
    
    async def handle_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle commands from NEXUS system"""
        params = params or {}
        
        # Log the command
        if self.logger:
            self.logger.log_info(f"YouTube Agent received command: {command}", "YOUTUBE_AGENT")
        
        # Route commands
        if command == "scrape_video":
            return await self._handle_scrape_video(params)
        
        elif command == "analyze_capabilities":
            return await self._handle_analyze_capabilities()
        
        elif command == "batch_scrape":
            return await self._handle_batch_scrape(params)
        
        elif command == "check_enhancement":
            return await self._handle_check_enhancement()
        
        elif command == "help":
            return self._get_help()
        
        else:
            return {
                "success": False,
                "error": f"Unknown command: {command}",
                "available_commands": ["scrape_video", "analyze_capabilities", "batch_scrape", "check_enhancement", "help"]
            }
    
    async def _handle_scrape_video(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle video scraping request"""
        url = params.get("url")
        if not url:
            return {"success": False, "error": "No URL provided"}
        
        # Parse options
        options = {
            "transcript": params.get("transcript", True),
            "comments": params.get("comments", False),
            "metadata": params.get("metadata", True),
            "related_videos": params.get("related_videos", False)
        }
        
        # Create task
        task = {
            "id": f"yt_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "type": "scrape_video",
            "url": url,
            "options": options
        }
        
        # Log task start
        if self.logger:
            self.logger.log_info(f"Starting YouTube scrape: {url}", "YOUTUBE_AGENT")
        
        # Execute task
        result = await self.youtube_agent.process_task(task)
        
        # Handle self-enhancement response
        if result.get("status") == "enhancement_needed":
            # Log enhancement need
            if self.logger:
                self.logger.log_warning(
                    f"Enhancement needed: {', '.join(result.get('required_packages', []))}",
                    "YOUTUBE_AGENT"
                )
            
            # Format user-friendly response
            result["user_message"] = self._format_enhancement_message(result)
        
        return result
    
    async def _handle_analyze_capabilities(self) -> Dict[str, Any]:
        """Analyze current capabilities"""
        analysis = await self.youtube_agent.scraper.analyze_capabilities()
        
        # Add summary
        total_caps = len(analysis["current_capabilities"])
        active_caps = sum(1 for v in analysis["current_capabilities"].values() if v)
        
        analysis["summary"] = {
            "total_capabilities": total_caps,
            "active_capabilities": active_caps,
            "capability_percentage": (active_caps / total_caps * 100) if total_caps > 0 else 0,
            "enhancement_count": len(analysis["enhancement_opportunities"])
        }
        
        if self.logger:
            self.logger.log_info(
                f"Capability analysis: {active_caps}/{total_caps} active",
                "YOUTUBE_AGENT"
            )
        
        return analysis
    
    async def _handle_batch_scrape(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle batch scraping"""
        urls = params.get("urls", [])
        if not urls:
            return {"success": False, "error": "No URLs provided"}
        
        task = {
            "id": f"yt_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "type": "batch_scrape",
            "urls": urls,
            "options": params.get("options", {})
        }
        
        if self.logger:
            self.logger.log_info(f"Starting batch scrape of {len(urls)} videos", "YOUTUBE_AGENT")
        
        result = await self.youtube_agent.process_task(task)
        
        # Summarize results
        if "batch_results" in result:
            success_count = sum(1 for r in result["batch_results"] if r.get("success", False))
            enhancement_count = sum(1 for r in result["batch_results"] if r.get("status") == "enhancement_needed")
            
            result["summary"] = {
                "total": len(urls),
                "successful": success_count,
                "failed": len(urls) - success_count - enhancement_count,
                "enhancement_needed": enhancement_count
            }
        
        return result
    
    async def _handle_check_enhancement(self) -> Dict[str, Any]:
        """Check enhancement suggestions based on past failures"""
        enhancement_report = await self.youtube_agent.suggest_enhancement()
        
        if self.logger:
            packages = enhancement_report.get("required_packages", [])
            if packages:
                self.logger.log_info(
                    f"Enhancement check: {len(packages)} packages needed",
                    "YOUTUBE_AGENT"
                )
        
        return enhancement_report
    
    def _format_enhancement_message(self, result: Dict[str, Any]) -> str:
        """Format enhancement message for users"""
        msg = "I need additional capabilities to complete this task:\n\n"
        
        # List missing capabilities
        for cap in result.get("missing_capabilities", []):
            msg += f"• {cap['capability']}\n"
        
        msg += "\nTo enable these features, install:\n"
        for cmd in result.get("installation_commands", []):
            msg += f"  {cmd}\n"
        
        msg += "\nOnce installed, I'll be able to extract transcripts, comments, and more!"
        
        return msg
    
    def _get_help(self) -> Dict[str, Any]:
        """Get help information"""
        return {
            "success": True,
            "commands": {
                "scrape_video": {
                    "description": "Scrape a YouTube video",
                    "params": {
                        "url": "YouTube video URL (required)",
                        "transcript": "Extract transcript (default: true)",
                        "comments": "Extract comments (default: false)",
                        "metadata": "Extract metadata (default: true)"
                    },
                    "example": {
                        "command": "scrape_video",
                        "params": {"url": "https://youtube.com/watch?v=...", "transcript": True}
                    }
                },
                "analyze_capabilities": {
                    "description": "Check what YouTube scraping features are available",
                    "params": {},
                    "example": {"command": "analyze_capabilities"}
                },
                "batch_scrape": {
                    "description": "Scrape multiple YouTube videos",
                    "params": {
                        "urls": "List of YouTube URLs (required)",
                        "options": "Extraction options for all videos"
                    },
                    "example": {
                        "command": "batch_scrape",
                        "params": {
                            "urls": ["url1", "url2"],
                            "options": {"transcript": True}
                        }
                    }
                },
                "check_enhancement": {
                    "description": "Get enhancement suggestions based on past tasks",
                    "params": {},
                    "example": {"command": "check_enhancement"}
                }
            }
        }


# Integration with NEXUS Chat
async def process_chat_message(message: str) -> Dict[str, Any]:
    """Process natural language chat messages about YouTube"""
    connector = YouTubeAgentConnector()
    
    # Simple pattern matching for commands
    message_lower = message.lower()
    
    # Check for YouTube URLs
    import re
    youtube_url_pattern = r'(https?://)?(www\.)?(youtube\.com/(watch\?v=|embed/|v/)|youtu\.be/)[\w-]+'
    urls = re.findall(youtube_url_pattern, message)
    
    if urls:
        # Found YouTube URL(s)
        url = urls[0] if isinstance(urls[0], str) else ''.join(urls[0])
        
        # Determine what to extract based on message
        options = {
            "transcript": "transcript" in message_lower or "captions" in message_lower or "subtitles" in message_lower,
            "comments": "comment" in message_lower,
            "metadata": True  # Always get metadata
        }
        
        if "conversation" in message_lower or "discussion" in message_lower:
            options["transcript"] = True
            options["comments"] = True
        
        return await connector.handle_command("scrape_video", {"url": url, **options})
    
    elif "capabilit" in message_lower or "can you" in message_lower or "what can" in message_lower:
        return await connector.handle_command("analyze_capabilities")
    
    elif "help" in message_lower:
        return await connector.handle_command("help")
    
    else:
        return {
            "success": False,
            "message": "I can help you scrape YouTube videos. Just send me a YouTube URL!",
            "hint": "Try: 'Scrape this video: https://youtube.com/watch?v=...'"
        }


# Standalone testing
async def main():
    """Test the YouTube connector"""
    connector = YouTubeAgentConnector()
    
    print("🎥 NEXUS YouTube Agent Connector")
    print("================================\n")
    
    # Test capability analysis
    print("📊 Analyzing capabilities...")
    capabilities = await connector.handle_command("analyze_capabilities")
    
    if capabilities.get("success", True):
        summary = capabilities.get("summary", {})
        print(f"✅ Active: {summary.get('active_capabilities', 0)}/{summary.get('total_capabilities', 0)}")
        print(f"🔧 Enhancements available: {summary.get('enhancement_count', 0)}")
    
    # Test with a sample video (if URL provided)
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
        print(f"\n🎬 Testing with video: {url}")
        
        result = await connector.handle_command("scrape_video", {
            "url": url,
            "transcript": True,
            "comments": True
        })
        
        if result.get("status") == "enhancement_needed":
            print(f"\n{result.get('user_message', 'Enhancement needed')}")
        elif result.get("success"):
            print("\n✅ Scraping successful!")
            if "data" in result and "metadata" in result["data"]:
                meta = result["data"]["metadata"]
                print(f"Title: {meta.get('title', 'N/A')}")
                print(f"Duration: {meta.get('duration', 0)} seconds")
        else:
            print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
    
    # Show help
    print("\n📚 Available commands:")
    help_info = connector._get_help()
    for cmd, info in help_info["commands"].items():
        print(f"  • {cmd}: {info['description']}")


if __name__ == "__main__":
    asyncio.run(main())