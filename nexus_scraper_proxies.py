#!/usr/bin/env python3
"""
NEXUS Scraper Proxy Management
Free proxy discovery, validation, and rotation
"""

import asyncio
import aiohttp
import json
import random
import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class Proxy:
    """Proxy information and statistics"""
    host: str
    port: int
    protocol: str = "http"
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None
    speed_ms: Optional[int] = None
    last_check: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    consecutive_failures: int = 0
    is_active: bool = True
    
    @property
    def url(self) -> str:
        """Get proxy URL"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0
    
    @property
    def score(self) -> float:
        """Calculate proxy quality score"""
        # Factors: success rate, speed, recent failures
        score = self.success_rate * 100
        
        # Penalize slow proxies
        if self.speed_ms:
            if self.speed_ms < 1000:
                score += 20
            elif self.speed_ms < 3000:
                score += 10
            else:
                score -= 10
        
        # Penalize consecutive failures
        score -= self.consecutive_failures * 10
        
        return max(0, min(100, score))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol,
            "country": self.country,
            "speed_ms": self.speed_ms,
            "success_rate": self.success_rate,
            "score": self.score,
            "is_active": self.is_active
        }


class ProxyProvider:
    """Base class for proxy providers"""
    
    async def fetch_proxies(self) -> List[Proxy]:
        """Fetch proxies from provider"""
        raise NotImplementedError


class FreeProxyListProvider(ProxyProvider):
    """Fetch from free-proxy-list.net API"""
    
    async def fetch_proxies(self) -> List[Proxy]:
        proxies = []
        urls = [
            "https://www.proxy-list.download/api/v1/get?type=https",
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all&simplified=true"
        ]
        
        async with aiohttp.ClientSession() as session:
            for url in urls:
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            text = await response.text()
                            # Parse proxy list (usually IP:PORT format)
                            for line in text.strip().split('\n'):
                                if ':' in line:
                                    parts = line.strip().split(':')
                                    if len(parts) == 2:
                                        try:
                                            proxies.append(Proxy(
                                                host=parts[0],
                                                port=int(parts[1]),
                                                protocol="http"
                                            ))
                                        except ValueError:
                                            continue
                except Exception as e:
                    logger.warning(f"Failed to fetch from {url}: {e}")
        
        return proxies


class ProxyScrapeScraper(ProxyProvider):
    """Scrape proxies from ProxyScrape"""
    
    async def fetch_proxies(self) -> List[Proxy]:
        proxies = []
        
        async with aiohttp.ClientSession() as session:
            try:
                # Multiple endpoints for redundancy
                endpoints = [
                    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
                    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
                    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
                    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
                ]
                
                for url in endpoints:
                    try:
                        async with session.get(url, timeout=10) as response:
                            if response.status == 200:
                                text = await response.text()
                                for line in text.strip().split('\n'):
                                    match = re.match(r'(\d+\.\d+\.\d+\.\d+):(\d+)', line.strip())
                                    if match:
                                        proxies.append(Proxy(
                                            host=match.group(1),
                                            port=int(match.group(2)),
                                            protocol="http"
                                        ))
                    except Exception as e:
                        logger.debug(f"Failed to fetch from {url}: {e}")
                        
            except Exception as e:
                logger.error(f"ProxyScrape scraper error: {e}")
        
        return proxies


class ProxyManager:
    """Manage proxy pool with validation and rotation"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.proxies: Dict[str, Proxy] = {}
        self.providers = [
            FreeProxyListProvider(),
            ProxyScrapeScraper()
        ]
        self.validation_url = self.config.get("validation", {}).get("test_url", "https://httpbin.org/ip")
        self.min_proxies = 10
        self.max_consecutive_failures = 3
        self._lock = asyncio.Lock()
        self._last_fetch = None
        self._fetch_interval = timedelta(hours=1)
    
    async def initialize(self):
        """Initialize proxy pool"""
        await self.fetch_new_proxies()
        asyncio.create_task(self._background_validator())
        asyncio.create_task(self._background_fetcher())
    
    async def fetch_new_proxies(self):
        """Fetch proxies from all providers"""
        logger.info("Fetching new proxies...")
        all_proxies = []
        
        # Fetch from all providers concurrently
        tasks = [provider.fetch_proxies() for provider in self.providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_proxies.extend(result)
        
        # Add unique proxies to pool
        async with self._lock:
            for proxy in all_proxies:
                key = f"{proxy.host}:{proxy.port}"
                if key not in self.proxies:
                    self.proxies[key] = proxy
        
        logger.info(f"Fetched {len(all_proxies)} proxies, total pool size: {len(self.proxies)}")
        
        # Validate new proxies
        await self.validate_all_proxies()
    
    async def validate_proxy(self, proxy: Proxy) -> bool:
        """Validate a single proxy"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            async with aiohttp.ClientSession() as session:
                proxy_url = proxy.url
                async with session.get(
                    self.validation_url,
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=10),
                    ssl=False
                ) as response:
                    if response.status == 200:
                        elapsed_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
                        
                        # Update proxy stats
                        proxy.speed_ms = elapsed_ms
                        proxy.last_check = datetime.now()
                        proxy.success_count += 1
                        proxy.consecutive_failures = 0
                        proxy.is_active = True
                        
                        # Try to get country from response
                        try:
                            data = await response.json()
                            if 'origin' in data:
                                # Could enhance with GeoIP lookup
                                pass
                        except:
                            pass
                        
                        return True
                    else:
                        raise Exception(f"HTTP {response.status}")
                        
        except Exception as e:
            # Update failure stats
            proxy.failure_count += 1
            proxy.consecutive_failures += 1
            proxy.last_check = datetime.now()
            
            # Deactivate if too many failures
            if proxy.consecutive_failures >= self.max_consecutive_failures:
                proxy.is_active = False
                logger.debug(f"Deactivated proxy {proxy.host}:{proxy.port} after {proxy.consecutive_failures} failures")
            
            return False
    
    async def validate_all_proxies(self):
        """Validate all proxies in pool"""
        if not self.proxies:
            return
        
        logger.info(f"Validating {len(self.proxies)} proxies...")
        
        # Create validation tasks with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(50)  # Max 50 concurrent validations
        
        async def validate_with_semaphore(proxy: Proxy):
            async with semaphore:
                return await self.validate_proxy(proxy), proxy
        
        # Validate all proxies
        proxies_list = list(self.proxies.values())
        tasks = [validate_with_semaphore(proxy) for proxy in proxies_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count results
        valid_count = sum(1 for r in results if isinstance(r, tuple) and r[0])
        logger.info(f"Validation complete: {valid_count}/{len(proxies_list)} proxies are valid")
    
    async def get_proxy(self, retry_count: int = 0) -> Optional[Proxy]:
        """Get a working proxy using smart selection"""
        async with self._lock:
            # Get active proxies sorted by score
            active_proxies = [p for p in self.proxies.values() if p.is_active]
            
            if not active_proxies:
                # Try to fetch new proxies if none available
                if retry_count < 3:
                    await self.fetch_new_proxies()
                    return await self.get_proxy(retry_count + 1)
                return None
            
            # Sort by score (higher is better)
            active_proxies.sort(key=lambda p: p.score, reverse=True)
            
            # Use weighted random selection favoring better proxies
            if len(active_proxies) > 1:
                # Top 20% have higher chance
                top_count = max(1, len(active_proxies) // 5)
                weights = [3 if i < top_count else 1 for i in range(len(active_proxies))]
                
                selected = random.choices(active_proxies, weights=weights, k=1)[0]
            else:
                selected = active_proxies[0]
            
            return selected
    
    async def report_proxy_result(self, proxy: Proxy, success: bool, response_time_ms: Optional[int] = None):
        """Report proxy usage result"""
        async with self._lock:
            if success:
                proxy.success_count += 1
                proxy.consecutive_failures = 0
                if response_time_ms:
                    # Update speed with moving average
                    if proxy.speed_ms:
                        proxy.speed_ms = int((proxy.speed_ms + response_time_ms) / 2)
                    else:
                        proxy.speed_ms = response_time_ms
            else:
                proxy.failure_count += 1
                proxy.consecutive_failures += 1
                
                # Deactivate if too many failures
                if proxy.consecutive_failures >= self.max_consecutive_failures:
                    proxy.is_active = False
                    logger.info(f"Deactivated proxy {proxy.host}:{proxy.port} after failures")
    
    async def _background_validator(self):
        """Periodically validate proxies"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Re-validate inactive proxies occasionally
                async with self._lock:
                    inactive_proxies = [p for p in self.proxies.values() if not p.is_active]
                    
                if inactive_proxies:
                    # Test a sample of inactive proxies
                    sample_size = min(10, len(inactive_proxies))
                    sample = random.sample(inactive_proxies, sample_size)
                    
                    for proxy in sample:
                        if await self.validate_proxy(proxy):
                            logger.info(f"Reactivated proxy {proxy.host}:{proxy.port}")
                
                # Remove very old failed proxies
                async with self._lock:
                    cutoff_time = datetime.now() - timedelta(hours=24)
                    keys_to_remove = []
                    
                    for key, proxy in self.proxies.items():
                        if (not proxy.is_active and 
                            proxy.last_check and 
                            proxy.last_check < cutoff_time and
                            proxy.success_rate < 0.1):
                            keys_to_remove.append(key)
                    
                    for key in keys_to_remove:
                        del self.proxies[key]
                    
                    if keys_to_remove:
                        logger.info(f"Removed {len(keys_to_remove)} old failed proxies")
                        
            except Exception as e:
                logger.error(f"Background validator error: {e}")
    
    async def _background_fetcher(self):
        """Periodically fetch new proxies"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                
                # Fetch new proxies if pool is low
                active_count = sum(1 for p in self.proxies.values() if p.is_active)
                
                if active_count < self.min_proxies:
                    logger.info(f"Active proxy count low ({active_count}), fetching new proxies...")
                    await self.fetch_new_proxies()
                    
            except Exception as e:
                logger.error(f"Background fetcher error: {e}")
    
    def get_stats(self) -> Dict:
        """Get proxy pool statistics"""
        total = len(self.proxies)
        active = sum(1 for p in self.proxies.values() if p.is_active)
        
        # Group by country if available
        by_country = defaultdict(int)
        speed_distribution = {"fast": 0, "medium": 0, "slow": 0}
        
        for proxy in self.proxies.values():
            if proxy.country:
                by_country[proxy.country] += 1
            
            if proxy.speed_ms:
                if proxy.speed_ms < 1000:
                    speed_distribution["fast"] += 1
                elif proxy.speed_ms < 3000:
                    speed_distribution["medium"] += 1
                else:
                    speed_distribution["slow"] += 1
        
        return {
            "total_proxies": total,
            "active_proxies": active,
            "inactive_proxies": total - active,
            "by_country": dict(by_country),
            "speed_distribution": speed_distribution,
            "average_success_rate": sum(p.success_rate for p in self.proxies.values()) / total if total > 0 else 0
        }
    
    async def export_proxies(self, only_active: bool = True) -> List[Dict]:
        """Export proxy list"""
        proxies = []
        
        for proxy in self.proxies.values():
            if only_active and not proxy.is_active:
                continue
            
            proxies.append(proxy.to_dict())
        
        # Sort by score
        proxies.sort(key=lambda p: p["score"], reverse=True)
        
        return proxies


class ProxyRotator:
    """Handle proxy rotation for scraping sessions"""
    
    def __init__(self, proxy_manager: ProxyManager):
        self.proxy_manager = proxy_manager
        self.session_proxies: Dict[str, Proxy] = {}
        self.failed_proxies: Set[str] = set()
    
    async def get_proxy_for_session(self, session_id: str, force_new: bool = False) -> Optional[Proxy]:
        """Get proxy for a session with sticky assignment"""
        # Return existing proxy if not forcing new
        if not force_new and session_id in self.session_proxies:
            proxy = self.session_proxies[session_id]
            if proxy.is_active and proxy.url not in self.failed_proxies:
                return proxy
        
        # Get new proxy
        proxy = await self.proxy_manager.get_proxy()
        if proxy:
            self.session_proxies[session_id] = proxy
            
        return proxy
    
    async def report_failure(self, session_id: str, proxy: Proxy):
        """Report proxy failure and rotate"""
        self.failed_proxies.add(proxy.url)
        await self.proxy_manager.report_proxy_result(proxy, False)
        
        # Remove from session
        if session_id in self.session_proxies:
            del self.session_proxies[session_id]
    
    async def report_success(self, proxy: Proxy, response_time_ms: Optional[int] = None):
        """Report successful proxy usage"""
        await self.proxy_manager.report_proxy_result(proxy, True, response_time_ms)
        
        # Remove from failed set if present
        self.failed_proxies.discard(proxy.url)
    
    def clear_session(self, session_id: str):
        """Clear proxy assignment for session"""
        if session_id in self.session_proxies:
            del self.session_proxies[session_id]


# Standalone proxy utilities
async def test_proxy_manager():
    """Test proxy manager functionality"""
    config = {
        "validation": {
            "test_url": "https://httpbin.org/ip"
        }
    }
    
    manager = ProxyManager(config)
    await manager.initialize()
    
    # Wait for initial fetch and validation
    await asyncio.sleep(5)
    
    # Get stats
    stats = manager.get_stats()
    print(f"Proxy Pool Stats: {json.dumps(stats, indent=2)}")
    
    # Test getting proxies
    for i in range(5):
        proxy = await manager.get_proxy()
        if proxy:
            print(f"Got proxy: {proxy.host}:{proxy.port} (score: {proxy.score:.1f})")
        else:
            print("No proxy available")
    
    # Export active proxies
    active_proxies = await manager.export_proxies(only_active=True)
    print(f"\nActive proxies: {len(active_proxies)}")
    for p in active_proxies[:5]:
        print(f"  {p['host']}:{p['port']} - Score: {p['score']:.1f}, Success: {p['success_rate']:.2%}")


if __name__ == "__main__":
    asyncio.run(test_proxy_manager())