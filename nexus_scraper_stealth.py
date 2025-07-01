#!/usr/bin/env python3
"""
NEXUS Scraper Stealth Module
Advanced anti-detection features for web scraping
"""

import random
import asyncio
import json
from typing import Dict, List, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Stealth libraries
try:
    from tf_playwright_stealth import stealth_async
except ImportError:
    try:
        from playwright_stealth import stealth_async
    except ImportError:
        stealth_async = None
from fake_useragent import UserAgent
try:
    from playwright.async_api import Browser, BrowserContext, Page
except ImportError:
    Browser = BrowserContext = Page = None

logger = logging.getLogger(__name__)


class StealthConfig:
    """Configuration for stealth features"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.ua = UserAgent()
        self._fingerprint_cache = {}
    
    def _default_config(self) -> Dict[str, Any]:
        return {
            "rotate_user_agents": True,
            "browser_fingerprinting": {
                "randomize_canvas": True,
                "randomize_webgl": True,
                "randomize_audio": True,
                "randomize_fonts": True,
                "randomize_plugins": True,
                "randomize_screen": True,
                "randomize_timezone": True,
                "randomize_language": True
            },
            "behavior_simulation": {
                "random_delays": True,
                "mouse_movements": True,
                "scroll_behavior": True,
                "typing_simulation": True
            },
            "detection_evasion": {
                "hide_webdriver": True,
                "disable_automation_flags": True,
                "modify_navigator": True,
                "bypass_csp": True
            }
        }
    
    def get_random_user_agent(self, browser_type: str = "chrome") -> str:
        """Get a random user agent for the specified browser"""
        if browser_type == "chrome":
            return self.ua.chrome
        elif browser_type == "firefox":
            return self.ua.firefox
        elif browser_type == "safari":
            return self.ua.safari
        else:
            return self.ua.random
    
    def get_random_viewport(self) -> Dict[str, int]:
        """Get random viewport dimensions"""
        viewports = [
            {"width": 1920, "height": 1080},  # Full HD
            {"width": 1366, "height": 768},   # Common laptop
            {"width": 1440, "height": 900},   # MacBook
            {"width": 1536, "height": 864},   # Surface
            {"width": 1600, "height": 900},   # HD+
            {"width": 1280, "height": 720},   # HD
            {"width": 1680, "height": 1050},  # WSXGA+
            {"width": 2560, "height": 1440},  # QHD
        ]
        return random.choice(viewports)
    
    def get_random_timezone(self) -> str:
        """Get random timezone"""
        timezones = [
            "America/New_York",
            "America/Chicago",
            "America/Denver",
            "America/Los_Angeles",
            "Europe/London",
            "Europe/Paris",
            "Europe/Berlin",
            "Asia/Tokyo",
            "Asia/Shanghai",
            "Australia/Sydney"
        ]
        return random.choice(timezones)
    
    def get_random_locale(self) -> str:
        """Get random locale"""
        locales = [
            "en-US", "en-GB", "en-CA", "en-AU",
            "es-ES", "es-MX", "fr-FR", "de-DE",
            "it-IT", "pt-BR", "ja-JP", "ko-KR"
        ]
        return random.choice(locales)


class BrowserStealth:
    """Apply stealth techniques to browser instances"""
    
    def __init__(self, stealth_config: StealthConfig):
        self.config = stealth_config
    
    async def apply_stealth(self, page: 'Page'):
        """Apply all stealth techniques to a page"""
        # Apply playwright-stealth
        if stealth_async:
            await stealth_async(page)
        
        # Additional stealth measures
        await self._modify_navigator_properties(page)
        await self._inject_stealth_scripts(page)
        await self._setup_request_interception(page)
    
    async def _modify_navigator_properties(self, page: 'Page'):
        """Modify navigator properties to avoid detection"""
        await page.add_init_script("""
            // Override navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Override navigator.plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    },
                    {
                        0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format", 
                        filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                        length: 1,
                        name: "Chrome PDF Viewer"
                    }
                ]
            });
            
            // Override navigator.languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Override navigator.permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Remove automation indicators
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """)
    
    async def _inject_stealth_scripts(self, page: Page):
        """Inject additional stealth scripts"""
        # Canvas fingerprinting protection
        if self.config.config["browser_fingerprinting"]["randomize_canvas"]:
            await page.add_init_script("""
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function(type) {
                    const context = this.getContext('2d');
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] = imageData.data[i] ^ (Math.random() * 0.1);
                    }
                    context.putImageData(imageData, 0, 0);
                    return originalToDataURL.apply(this, arguments);
                };
            """)
        
        # WebGL fingerprinting protection
        if self.config.config["browser_fingerprinting"]["randomize_webgl"]:
            await page.add_init_script("""
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) {
                        return 'Intel Iris OpenGL Engine';
                    }
                    return getParameter.apply(this, arguments);
                };
            """)
        
        # Audio fingerprinting protection
        if self.config.config["browser_fingerprinting"]["randomize_audio"]:
            await page.add_init_script("""
                const audioContext = window.AudioContext || window.webkitAudioContext;
                if (audioContext) {
                    const originalCreateOscillator = audioContext.prototype.createOscillator;
                    audioContext.prototype.createOscillator = function() {
                        const oscillator = originalCreateOscillator.apply(this, arguments);
                        const originalConnect = oscillator.connect;
                        oscillator.connect = function() {
                            arguments[0].gain.value = arguments[0].gain.value * (0.99 + Math.random() * 0.02);
                            return originalConnect.apply(this, arguments);
                        };
                        return oscillator;
                    };
                }
            """)
    
    async def _setup_request_interception(self, page: Page):
        """Setup request interception for additional stealth"""
        # Modify headers to remove automation indicators
        async def handle_route(route):
            headers = route.request.headers
            
            # Remove or modify suspicious headers
            headers_to_remove = [
                'sec-ch-ua-platform',
                'sec-fetch-user',
                'x-requested-with'
            ]
            
            for header in headers_to_remove:
                headers.pop(header.lower(), None)
            
            # Add realistic headers
            headers.update({
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'accept-language': 'en-US,en;q=0.9',
                'cache-control': 'max-age=0',
                'upgrade-insecure-requests': '1'
            })
            
            await route.continue_(headers=headers)
        
        await page.route('**/*', handle_route)


class BehaviorSimulator:
    """Simulate human-like behavior"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    async def simulate_human_behavior(self, page: Page):
        """Simulate various human behaviors"""
        if self.config.get("random_delays", True):
            await self._random_delay()
        
        if self.config.get("mouse_movements", True):
            await self._simulate_mouse_movement(page)
        
        if self.config.get("scroll_behavior", True):
            await self._simulate_scrolling(page)
    
    async def _random_delay(self, min_ms: int = 100, max_ms: int = 2000):
        """Add random delay between actions"""
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
    
    async def _simulate_mouse_movement(self, page: Page):
        """Simulate realistic mouse movements"""
        viewport = page.viewport_size
        if not viewport:
            return
        
        # Generate random bezier curve for mouse movement
        steps = random.randint(10, 20)
        for i in range(steps):
            x = random.randint(0, viewport["width"])
            y = random.randint(0, viewport["height"])
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.01, 0.05))
    
    async def _simulate_scrolling(self, page: Page):
        """Simulate human-like scrolling"""
        # Scroll down in chunks
        scroll_attempts = random.randint(3, 7)
        for _ in range(scroll_attempts):
            scroll_distance = random.randint(100, 500)
            await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Sometimes scroll back up a bit
        if random.random() < 0.3:
            scroll_up = random.randint(50, 200)
            await page.evaluate(f"window.scrollBy(0, -{scroll_up})")
    
    async def simulate_typing(self, page: Page, selector: str, text: str):
        """Simulate human-like typing"""
        await page.click(selector)
        
        for char in text:
            await page.type(selector, char)
            # Variable typing speed
            delay = random.uniform(0.05, 0.2)
            
            # Occasional longer pauses
            if random.random() < 0.1:
                delay = random.uniform(0.5, 1.0)
            
            await asyncio.sleep(delay)


class DetectionBypass:
    """Bypass common bot detection mechanisms"""
    
    def __init__(self):
        self.challenge_solvers = {
            "cloudflare": self._bypass_cloudflare,
            "datadome": self._bypass_datadome,
            "perimeter_x": self._bypass_perimeter_x,
            "recaptcha": self._handle_recaptcha
        }
    
    async def detect_and_bypass(self, page: Page) -> bool:
        """Detect and bypass protection if present"""
        # Check for common protection indicators
        protection_type = await self._detect_protection(page)
        
        if protection_type and protection_type in self.challenge_solvers:
            logger.info(f"Detected {protection_type} protection, attempting bypass...")
            return await self.challenge_solvers[protection_type](page)
        
        return True
    
    async def _detect_protection(self, page: Page) -> Optional[str]:
        """Detect type of bot protection"""
        # Check page content for protection indicators
        content = await page.content()
        
        if "cf-browser-verification" in content or "Cloudflare" in content:
            return "cloudflare"
        elif "datadome" in content.lower():
            return "datadome"
        elif "px-captcha" in content or "_px" in content:
            return "perimeter_x"
        elif "g-recaptcha" in content or "grecaptcha" in content:
            return "recaptcha"
        
        return None
    
    async def _bypass_cloudflare(self, page: Page) -> bool:
        """Attempt to bypass Cloudflare protection"""
        try:
            # Wait for challenge to complete
            await page.wait_for_timeout(5000)
            
            # Check if challenge was solved
            if "cf-browser-verification" not in await page.content():
                logger.info("Cloudflare challenge bypassed")
                return True
            
            # Try clicking the checkbox if present
            checkbox = await page.query_selector('input[type="checkbox"]')
            if checkbox:
                await checkbox.click()
                await page.wait_for_timeout(3000)
            
            return "cf-browser-verification" not in await page.content()
        except Exception as e:
            logger.error(f"Failed to bypass Cloudflare: {e}")
            return False
    
    async def _bypass_datadome(self, page: Page) -> bool:
        """Attempt to bypass DataDome protection"""
        # DataDome often uses behavioral analysis
        behavior_sim = BehaviorSimulator()
        await behavior_sim.simulate_human_behavior(page)
        
        # Wait and check if we're through
        await page.wait_for_timeout(3000)
        return "datadome" not in (await page.content()).lower()
    
    async def _bypass_perimeter_x(self, page: Page) -> bool:
        """Attempt to bypass PerimeterX protection"""
        # PerimeterX uses advanced fingerprinting
        # Best approach is prevention through proper stealth setup
        await page.wait_for_timeout(5000)
        return "_px" not in await page.content()
    
    async def _handle_recaptcha(self, page: Page) -> bool:
        """Handle reCAPTCHA (note: cannot automatically solve)"""
        logger.warning("reCAPTCHA detected. Manual solving or third-party service required.")
        return False


class StealthManager:
    """Main class for managing all stealth features"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.stealth_config = StealthConfig(self.config["stealth"])
        self.browser_stealth = BrowserStealth(self.stealth_config)
        self.behavior_sim = BehaviorSimulator(self.config["stealth"]["behavior_simulation"])
        self.detection_bypass = DetectionBypass()
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load stealth configuration"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        
        # Return default config
        return {
            "stealth": {
                "enabled": True,
                "rotate_user_agents": True,
                "browser_fingerprinting": {
                    "randomize_canvas": True,
                    "randomize_webgl": True,
                    "randomize_audio": True
                },
                "behavior_simulation": {
                    "random_delays": True,
                    "mouse_movements": True,
                    "scroll_behavior": True
                }
            }
        }
    
    async def create_stealth_context(self, browser: Browser) -> BrowserContext:
        """Create a browser context with stealth features"""
        # Get random configuration
        user_agent = self.stealth_config.get_random_user_agent()
        viewport = self.stealth_config.get_random_viewport()
        timezone = self.stealth_config.get_random_timezone()
        locale = self.stealth_config.get_random_locale()
        
        # Create context with stealth settings
        context = await browser.new_context(
            user_agent=user_agent,
            viewport=viewport,
            timezone_id=timezone,
            locale=locale,
            ignore_https_errors=True,
            java_script_enabled=True,
            bypass_csp=True,
            extra_http_headers={
                'Accept-Language': f'{locale},en;q=0.9',
            }
        )
        
        return context
    
    async def prepare_page(self, page: Page):
        """Prepare a page with all stealth features"""
        # Apply browser stealth
        await self.browser_stealth.apply_stealth(page)
        
        # Setup detection monitoring
        page.on('response', self._monitor_responses)
        
        # Initial behavior simulation
        await self.behavior_sim.simulate_human_behavior(page)
    
    async def _monitor_responses(self, response):
        """Monitor responses for detection indicators"""
        if response.status in [403, 429]:
            logger.warning(f"Possible bot detection: {response.status} on {response.url}")
    
    async def navigate_with_stealth(self, page: Page, url: str) -> bool:
        """Navigate to URL with full stealth measures"""
        try:
            # Pre-navigation setup
            await self.prepare_page(page)
            
            # Navigate with timeout
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Post-navigation behavior
            await self.behavior_sim.simulate_human_behavior(page)
            
            # Check for and bypass protection
            return await self.detection_bypass.detect_and_bypass(page)
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False


# Export main components
__all__ = ['StealthConfig', 'BrowserStealth', 'BehaviorSimulator', 'DetectionBypass', 'StealthManager']