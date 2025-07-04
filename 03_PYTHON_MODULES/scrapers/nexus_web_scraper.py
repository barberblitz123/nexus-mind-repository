#!/usr/bin/env python3
"""
NEXUS Web Scraper - Core Engine
High-level web scraping with multiple strategies and stealth capabilities
"""

import json
import asyncio
import hashlib
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urljoin
import aiofiles
import time

# Primary engine - Crawl4AI
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    # Try to import LLM extraction - multiple fallback paths
    LLMContentExtraction = None
    try:
        from crawl4ai.content_scraper import LLMContentExtraction
    except ImportError:
        try:
            from crawl4ai.extraction_strategy import LLMExtractionStrategy as LLMContentExtraction
        except ImportError:
            try:
                from crawl4ai.extraction import LLMExtractionStrategy as LLMContentExtraction
            except ImportError:
                # Create a mock class for compatibility
                class MockLLMExtraction:
                    def __init__(self, *args, **kwargs):
                        pass
                LLMContentExtraction = MockLLMExtraction
    CRAWL4AI_AVAILABLE = True
except ImportError:
    AsyncWebCrawler = BrowserConfig = CrawlerRunConfig = CacheMode = LLMContentExtraction = None
    CRAWL4AI_AVAILABLE = False

# Fallback engines
import httpx
from bs4 import BeautifulSoup
import cloudscraper
from fake_useragent import UserAgent

# Memory integration
from nexus_memory_core import NexusUnifiedMemory
from nexus_memory_types import MemoryEntry

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NexusWebScraper:
    """Advanced web scraper with multiple engines and stealth capabilities"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the web scraper with configuration"""
        self.config_path = config_path or "nexus_scraper_config.json"
        self.config = self._load_config()
        
        # Initialize components
        self.memory = NexusUnifiedMemory()
        self.ua = UserAgent()
        self.session_cache = {}
        self.rate_limiter = RateLimiter(
            self.config["scraper"]["rate_limit"]["requests_per_second"],
            self.config["scraper"]["rate_limit"]["burst_size"]
        )
        
        # Setup cache directory
        self.cache_dir = Path(self.config["caching"]["cache_dir"])
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize crawlers
        self._init_crawlers()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load config: {e}. Using defaults.")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            "scraper": {
                "primary_engine": "crawl4ai",
                "timeout": 30,
                "max_retries": 3,
                "rate_limit": {"requests_per_second": 2, "burst_size": 10}
            },
            "stealth": {"enabled": True},
            "caching": {"enabled": True, "cache_dir": "./nexus_scraper_cache"},
            "memory_integration": {"enabled": True, "importance_threshold": 0.6}
        }
    
    def _init_crawlers(self):
        """Initialize crawler instances"""
        # Browser config for Crawl4AI
        if BrowserConfig:
            self.browser_config = BrowserConfig(
                headless=True,
                browser_type="chromium",
                viewport={"width": 1920, "height": 1080},
                extra_args=["--disable-blink-features=AutomationControlled"]
            )
        else:
            self.browser_config = None
        
        # Cloudscraper for anti-bot protection
        self.cloudscraper = cloudscraper.create_scraper()
    
    async def scrape(self, url: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main scraping method with automatic strategy selection
        
        Args:
            url: URL to scrape
            options: Optional scraping options
            
        Returns:
            Dict containing scraped content and metadata
        """
        options = options or {}
        
        # Rate limiting
        await self.rate_limiter.acquire()
        
        # Check cache first
        if self.config["caching"]["enabled"]:
            cached = await self._get_cached(url)
            if cached:
                logger.info(f"Returning cached content for {url}")
                return cached
        
        # Try primary engine (Crawl4AI)
        try:
            result = await self._scrape_with_crawl4ai(url, options)
            if result and result.get("success"):
                await self._cache_result(url, result)
                await self._store_in_memory(url, result)
                return result
        except Exception as e:
            logger.warning(f"Crawl4AI failed for {url}: {e}")
        
        # Fallback to cloudscraper for anti-bot sites
        try:
            result = await self._scrape_with_cloudscraper(url, options)
            if result and result.get("success"):
                await self._cache_result(url, result)
                await self._store_in_memory(url, result)
                return result
        except Exception as e:
            logger.warning(f"Cloudscraper failed for {url}: {e}")
        
        # Final fallback to basic httpx + BeautifulSoup
        try:
            result = await self._scrape_with_httpx(url, options)
            if result and result.get("success"):
                await self._cache_result(url, result)
                await self._store_in_memory(url, result)
                return result
        except Exception as e:
            logger.error(f"All scraping methods failed for {url}: {e}")
            return self._error_result(url, str(e))
    
    async def _scrape_with_crawl4ai(self, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape using Crawl4AI with advanced features"""
        if not CRAWL4AI_AVAILABLE:
            raise ImportError("Crawl4AI not available")
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            # Configure run settings
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                word_count_threshold=10,
                exclude_external_links=True,
                remove_overlay_elements=True,
                timeout=self.config["scraper"]["timeout"] * 1000,  # ms
                wait_for="networkidle" if options.get("wait_for_js", True) else None,
                user_agent=self._get_user_agent() if self.config["stealth"]["enabled"] else None,
                headers=self.config["stealth"]["request_headers"] if self.config["stealth"]["enabled"] else None
            )
            
            # Add content extraction if needed
            if options.get("extract_content", True) and LLMContentExtraction:
                run_config.extraction_strategy = LLMContentExtraction(
                    provider="anthropic",
                    model="claude-3-haiku-20240307",
                    instruction="Extract the main content, removing navigation, ads, and boilerplate"
                )
            
            # Perform crawl
            result = await crawler.arun(url, config=run_config)
            
            if result.success:
                return {
                    "success": True,
                    "url": url,
                    "title": result.metadata.get("title", ""),
                    "content": result.markdown_v2 or result.cleaned_html,
                    "text": result.text,
                    "links": result.links,
                    "images": result.media.get("images", []),
                    "metadata": result.metadata,
                    "html": result.html if options.get("include_html", False) else None,
                    "screenshot": result.screenshot if options.get("screenshot", False) else None,
                    "engine": "crawl4ai",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise Exception(f"Crawl4AI failed: {result.error}")
    
    async def _scrape_with_cloudscraper(self, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape using cloudscraper for anti-bot protection"""
        headers = self.config["stealth"]["request_headers"].copy()
        if self.config["stealth"]["enabled"]:
            headers["User-Agent"] = self._get_user_agent()
        
        # Run in thread pool since cloudscraper is sync
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.cloudscraper.get(
                url,
                headers=headers,
                timeout=self.config["scraper"]["timeout"]
            )
        )
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract content
            content = self._extract_content_bs(soup, options)
            
            return {
                "success": True,
                "url": url,
                "title": soup.title.string if soup.title else "",
                "content": content["text"],
                "text": content["text"],
                "links": content["links"],
                "images": content["images"],
                "metadata": {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "encoding": response.encoding
                },
                "html": response.text if options.get("include_html", False) else None,
                "engine": "cloudscraper",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise Exception(f"HTTP {response.status_code}: {response.reason}")
    
    async def _scrape_with_httpx(self, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Basic scraping with httpx and BeautifulSoup"""
        headers = self.config["stealth"]["request_headers"].copy()
        if self.config["stealth"]["enabled"]:
            headers["User-Agent"] = self._get_user_agent()
        
        async with httpx.AsyncClient(timeout=self.config["scraper"]["timeout"]) as client:
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            content = self._extract_content_bs(soup, options)
            
            return {
                "success": True,
                "url": str(response.url),
                "title": soup.title.string if soup.title else "",
                "content": content["text"],
                "text": content["text"],
                "links": content["links"],
                "images": content["images"],
                "metadata": {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "encoding": response.encoding or "utf-8"
                },
                "html": response.text if options.get("include_html", False) else None,
                "engine": "httpx",
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_content_bs(self, soup: BeautifulSoup, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content using BeautifulSoup"""
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Find main content
        main_content = None
        for selector in self.config["content_extraction"]["selectors"]["content_patterns"]:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.body or soup
        
        # Extract text
        text = main_content.get_text(separator='\n', strip=True)
        
        # Extract links
        links = []
        if options.get("extract_links", True):
            base_url = options.get("base_url", "")
            for link in main_content.find_all('a', href=True):
                href = urljoin(base_url, link['href'])
                links.append({
                    "url": href,
                    "text": link.get_text(strip=True),
                    "title": link.get('title', '')
                })
        
        # Extract images
        images = []
        if options.get("extract_images", True):
            for img in main_content.find_all('img', src=True):
                images.append({
                    "url": urljoin(options.get("base_url", ""), img['src']),
                    "alt": img.get('alt', ''),
                    "title": img.get('title', '')
                })
        
        return {
            "text": text,
            "links": links,
            "images": images
        }
    
    def _get_user_agent(self) -> str:
        """Get a random user agent"""
        if self.config["stealth"]["rotate_user_agents"]:
            return self.ua.random
        else:
            import random
            return random.choice(self.config["stealth"]["user_agents"])
    
    async def _get_cached(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cached result if available"""
        cache_key = hashlib.md5(url.encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                async with aiofiles.open(cache_file, 'r') as f:
                    data = json.loads(await f.read())
                    
                # Check TTL
                cached_time = datetime.fromisoformat(data["timestamp"])
                age_hours = (datetime.now() - cached_time).total_seconds() / 3600
                
                if age_hours < self.config["caching"]["ttl_hours"]:
                    return data
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        
        return None
    
    async def _cache_result(self, url: str, result: Dict[str, Any]):
        """Cache scraping result"""
        if not self.config["caching"]["enabled"]:
            return
        
        cache_key = hashlib.md5(url.encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            # Remove large data from cache
            cache_data = result.copy()
            if "html" in cache_data:
                cache_data["html"] = None
            if "screenshot" in cache_data:
                cache_data["screenshot"] = None
            
            async with aiofiles.open(cache_file, 'w') as f:
                await f.write(json.dumps(cache_data, indent=2))
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")
    
    async def _store_in_memory(self, url: str, result: Dict[str, Any]):
        """Store scraping result in NEXUS memory"""
        if not self.config["memory_integration"]["enabled"]:
            return
        
        try:
            # Calculate importance based on content length and structure
            importance = min(0.5 + len(result.get("text", "")) / 10000, 1.0)
            
            # Create memory entry
            memory_data = {
                "url": url,
                "title": result.get("title", ""),
                "content": result.get("text", "")[:5000],  # Limit stored content
                "summary": result.get("content", "")[:1000],
                "links_count": len(result.get("links", [])),
                "images_count": len(result.get("images", [])),
                "engine": result.get("engine", "unknown"),
                "scraped_at": result.get("timestamp", datetime.now().isoformat())
            }
            
            # Store in memory with metadata
            await self.memory.store(
                content=memory_data,
                metadata={
                    "type": "web_scraping",
                    "url": url,
                    "domain": urlparse(url).netloc,
                    "engine": result.get("engine", "unknown")
                },
                importance=importance
            )
            
            logger.info(f"Stored scraping result in memory: {url}")
        except Exception as e:
            logger.error(f"Failed to store in memory: {e}")
    
    def _error_result(self, url: str, error: str) -> Dict[str, Any]:
        """Create error result"""
        return {
            "success": False,
            "url": url,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
    
    async def batch_scrape(self, urls: List[str], options: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Scrape multiple URLs concurrently"""
        options = options or {}
        max_concurrent = self.config["scraper"].get("concurrent_requests", 5)
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_semaphore(url: str) -> Dict[str, Any]:
            async with semaphore:
                return await self.scrape(url, options)
        
        # Scrape all URLs concurrently
        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        final_results = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                final_results.append(self._error_result(url, str(result)))
            else:
                final_results.append(result)
        
        return final_results


class RateLimiter:
    """Token bucket rate limiter for API calls"""
    
    def __init__(self, rate: float, burst: int):
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a token, waiting if necessary"""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens < 1:
                sleep_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(sleep_time)
                self.tokens = 1
            
            self.tokens -= 1


# CLI interface
async def main():
    """CLI interface for testing"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python nexus_web_scraper.py <url> [options]")
        sys.exit(1)
    
    url = sys.argv[1]
    
    # Initialize scraper
    scraper = NexusWebScraper()
    
    # Scrape URL
    print(f"Scraping {url}...")
    result = await scraper.scrape(url, {
        "extract_content": True,
        "extract_links": True,
        "extract_images": True,
        "wait_for_js": True
    })
    
    if result["success"]:
        print(f"\nTitle: {result['title']}")
        print(f"Engine: {result['engine']}")
        print(f"Content length: {len(result['text'])} chars")
        print(f"Links found: {len(result['links'])}")
        print(f"Images found: {len(result['images'])}")
        print(f"\nContent preview:\n{result['text'][:500]}...")
    else:
        print(f"Scraping failed: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())