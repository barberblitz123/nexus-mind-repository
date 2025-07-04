#!/usr/bin/env python3
"""
NEXUS YouTube Scraper Module
Specialized for scraping YouTube video information and content
"""

import re
import json
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from urllib.parse import urlparse, parse_qs

class NexusYouTubeScraper:
    """YouTube-specific scraper for NEXUS 2.0"""
    
    def __init__(self):
        self.client = httpx.Client(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        self.async_client = httpx.AsyncClient(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n]+)',
            r'youtube\.com/embed/([^&\n]+)',
            r'youtube\.com/v/([^&\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
        
    async def scrape_video_basic(self, url: str) -> Dict[str, Any]:
        """Scrape basic video information without external dependencies"""
        video_id = self.extract_video_id(url)
        if not video_id:
            return {"error": "Invalid YouTube URL"}
            
        try:
            # Fetch the video page
            response = await self.async_client.get(url)
            html = response.text
            
            # Extract basic information using regex
            title_match = re.search(r'<title>(.+?)</title>', html)
            title = title_match.group(1).replace(' - YouTube', '') if title_match else 'Unknown'
            
            # Extract metadata from JSON-LD
            json_ld_match = re.search(r'<script type="application/ld\+json">(.+?)</script>', html, re.DOTALL)
            metadata = {}
            
            if json_ld_match:
                try:
                    json_data = json.loads(json_ld_match.group(1))
                    if isinstance(json_data, dict):
                        metadata = {
                            'name': json_data.get('name', title),
                            'description': json_data.get('description', ''),
                            'duration': json_data.get('duration', ''),
                            'uploadDate': json_data.get('uploadDate', ''),
                            'author': json_data.get('author', {}).get('name', '') if isinstance(json_data.get('author'), dict) else ''
                        }
                except:
                    pass
            
            # Extract view count
            views_match = re.search(r'"viewCount":"(\d+)"', html)
            views = int(views_match.group(1)) if views_match else 0
            
            # Extract likes (if available)
            likes_match = re.search(r'"label":"(\d+(?:,\d+)*) likes"', html)
            likes = likes_match.group(1) if likes_match else 'N/A'
            
            return {
                'success': True,
                'video_id': video_id,
                'url': url,
                'title': metadata.get('name', title),
                'description': metadata.get('description', '')[:500] + '...' if len(metadata.get('description', '')) > 500 else metadata.get('description', ''),
                'author': metadata.get('author', 'Unknown'),
                'views': f"{views:,}" if views else 'N/A',
                'likes': likes,
                'upload_date': metadata.get('uploadDate', 'Unknown'),
                'duration': metadata.get('duration', 'Unknown'),
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'video_id': video_id,
                'url': url
            }
    
    async def scrape_multiple_videos(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape multiple YouTube videos concurrently"""
        tasks = [self.scrape_video_basic(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results
    
    def scrape_video_sync(self, url: str) -> Dict[str, Any]:
        """Synchronous wrapper for video scraping"""
        return asyncio.run(self.scrape_video_basic(url))
    
    async def search_videos(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for YouTube videos (basic implementation)"""
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        
        try:
            response = await self.async_client.get(search_url)
            html = response.text
            
            # Extract video IDs from search results
            video_ids = re.findall(r'"videoId":"([^"]+)"', html)
            video_ids = list(set(video_ids))[:max_results]  # Remove duplicates and limit
            
            # Extract video titles
            titles = re.findall(r'"title":{"runs":\[{"text":"([^"]+)"\}\]', html)
            
            results = []
            for i, video_id in enumerate(video_ids):
                results.append({
                    'video_id': video_id,
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'title': titles[i] if i < len(titles) else 'Unknown',
                    'position': i + 1
                })
            
            return results
            
        except Exception as e:
            return [{'error': str(e), 'query': query}]
    
    def __del__(self):
        """Cleanup clients"""
        self.client.close()
        asyncio.run(self.async_client.aclose())


# Integration with NEXUS Agent System
class YouTubeScraperAgent:
    """YouTube Scraper Agent for NEXUS 2.0"""
    
    def __init__(self, agent_name: str = "YouTube Scraper"):
        self.name = agent_name
        self.scraper = NexusYouTubeScraper()
        self.history = []
        
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a YouTube scraping task"""
        task_type = task.get('type', 'scrape')
        
        if task_type == 'scrape':
            url = task.get('url')
            if url:
                result = await self.scraper.scrape_video_basic(url)
                self.history.append({
                    'timestamp': datetime.now().isoformat(),
                    'task': task,
                    'result': result
                })
                return result
                
        elif task_type == 'search':
            query = task.get('query', '')
            max_results = task.get('max_results', 5)
            results = await self.scraper.search_videos(query, max_results)
            self.history.append({
                'timestamp': datetime.now().isoformat(),
                'task': task,
                'results': results
            })
            return {'results': results}
            
        elif task_type == 'batch_scrape':
            urls = task.get('urls', [])
            results = await self.scraper.scrape_multiple_videos(urls)
            self.history.append({
                'timestamp': datetime.now().isoformat(),
                'task': task,
                'results': results
            })
            return {'results': results}
            
        return {'error': 'Unknown task type'}


# Demo function for testing
async def demo_youtube_scraper():
    """Demonstrate YouTube scraping capabilities"""
    print("🎥 NEXUS YouTube Scraper Demo")
    print("=" * 50)
    
    scraper = NexusYouTubeScraper()
    
    # Test 1: Scrape a single video
    print("\n1. Scraping a single video...")
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
    result = await scraper.scrape_video_basic(test_url)
    
    if result.get('success'):
        print(f"✅ Title: {result['title']}")
        print(f"✅ Author: {result['author']}")
        print(f"✅ Views: {result['views']}")
        print(f"✅ Upload Date: {result['upload_date']}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Test 2: Search for videos
    print("\n2. Searching for videos...")
    search_results = await scraper.search_videos("python programming tutorial", max_results=3)
    
    for i, video in enumerate(search_results):
        if 'error' not in video:
            print(f"\n   Video {i+1}:")
            print(f"   - Title: {video.get('title', 'Unknown')}")
            print(f"   - URL: {video.get('url', 'N/A')}")
    
    print("\n✅ YouTube scraper is working!")
    

if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_youtube_scraper())