#!/usr/bin/env python3
"""
NEXUS Live Preview System - Enhanced with HMR, multi-device, and advanced features
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
import threading
from concurrent.futures import ThreadPoolExecutor
import hashlib
import websockets
import aiohttp
from aiohttp import web
import socket

# Third-party imports
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    Observer = None
    FileSystemEventHandler = object


@dataclass
class PreviewServer:
    """Preview server configuration"""
    host: str = "localhost"
    port: int = 3000
    ssl: bool = False
    base_path: Path = Path.cwd()
    

@dataclass
class DevicePreview:
    """Device preview configuration"""
    name: str
    width: int
    height: int
    user_agent: str
    device_scale_factor: float = 1.0
    is_mobile: bool = False
    has_touch: bool = False
    

@dataclass
class NetworkProfile:
    """Network throttling profile"""
    name: str
    download_speed: int  # bytes/sec
    upload_speed: int    # bytes/sec
    latency: int        # milliseconds
    packet_loss: float  # percentage
    

@dataclass
class PerformanceMetrics:
    """Performance metrics"""
    timestamp: datetime
    page_load_time: float
    first_paint: float
    first_contentful_paint: float
    dom_interactive: float
    memory_usage: Dict[str, int]
    cpu_usage: float
    network_requests: int
    total_size: int
    

class FileWatcher(FileSystemEventHandler):
    """Watch files for changes"""
    
    def __init__(self, callback: Callable):
        self.callback = callback
        self.debounce_timers = {}
        self.debounce_delay = 0.5  # seconds
        
    def on_modified(self, event):
        if not event.is_directory:
            self._debounced_callback(event.src_path)
            
    def on_created(self, event):
        if not event.is_directory:
            self._debounced_callback(event.src_path)
            
    def _debounced_callback(self, file_path: str):
        """Debounce file changes"""
        if file_path in self.debounce_timers:
            self.debounce_timers[file_path].cancel()
            
        timer = threading.Timer(
            self.debounce_delay,
            lambda: self.callback(file_path)
        )
        self.debounce_timers[file_path] = timer
        timer.start()
        

class HotModuleReplacement:
    """Hot module replacement system"""
    
    def __init__(self):
        self.module_cache = {}
        self.dependency_graph = {}
        self.websocket_clients = set()
        
    def register_module(self, module_path: str, content: str):
        """Register module in HMR system"""
        module_hash = hashlib.md5(content.encode()).hexdigest()
        
        self.module_cache[module_path] = {
            "content": content,
            "hash": module_hash,
            "timestamp": time.time()
        }
        
        # Extract dependencies
        dependencies = self._extract_dependencies(content, module_path)
        self.dependency_graph[module_path] = dependencies
        
    def _extract_dependencies(self, content: str, module_path: str) -> List[str]:
        """Extract module dependencies"""
        dependencies = []
        
        # JavaScript/TypeScript imports
        import_patterns = [
            r'import\s+.*?\s+from\s+[\'"](.+?)[\'"]',
            r'import\s*\([\'"](.+?)[\'"]\)',
            r'require\s*\([\'"](.+?)[\'"]\)',
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # Resolve relative paths
                if match.startswith('.'):
                    base_dir = os.path.dirname(module_path)
                    resolved = os.path.normpath(os.path.join(base_dir, match))
                    dependencies.append(resolved)
                else:
                    dependencies.append(match)
                    
        return dependencies
        
    async def handle_change(self, file_path: str, content: str):
        """Handle file change for HMR"""
        # Update module
        old_hash = self.module_cache.get(file_path, {}).get("hash")
        self.register_module(file_path, content)
        new_hash = self.module_cache[file_path]["hash"]
        
        if old_hash != new_hash:
            # Find affected modules
            affected = self._find_affected_modules(file_path)
            
            # Create HMR update
            update = {
                "type": "hmr-update",
                "timestamp": time.time(),
                "modules": {
                    module: self.module_cache.get(module, {})
                    for module in affected
                }
            }
            
            # Send to all clients
            await self._broadcast_update(update)
            
    def _find_affected_modules(self, changed_module: str) -> Set[str]:
        """Find all modules affected by change"""
        affected = {changed_module}
        
        # Find modules that depend on changed module
        for module, deps in self.dependency_graph.items():
            if changed_module in deps:
                affected.add(module)
                # Recursively find dependents
                affected.update(self._find_affected_modules(module))
                
        return affected
        
    async def _broadcast_update(self, update: dict):
        """Broadcast HMR update to clients"""
        message = json.dumps(update)
        
        # Send to all connected clients
        disconnected = set()
        for client in self.websocket_clients:
            try:
                await client.send(message)
            except Exception:
                disconnected.add(client)
                
        # Remove disconnected clients
        self.websocket_clients -= disconnected
        

class ConsoleLogger:
    """Stream console logs from preview"""
    
    def __init__(self):
        self.logs = []
        self.max_logs = 1000
        self.listeners = []
        
    def log(self, level: str, message: str, source: str = "preview"):
        """Add log entry"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "source": source
        }
        
        self.logs.append(entry)
        
        # Limit log size
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
            
        # Notify listeners
        for listener in self.listeners:
            listener(entry)
            
    def get_logs(self, since: Optional[datetime] = None) -> List[dict]:
        """Get logs since timestamp"""
        if since:
            return [
                log for log in self.logs
                if datetime.fromisoformat(log["timestamp"]) > since
            ]
        return self.logs
        
    def clear(self):
        """Clear all logs"""
        self.logs.clear()
        

class ElementInspector:
    """Element inspection tools"""
    
    def __init__(self):
        self.inspection_script = """
        (function() {
            let selectedElement = null;
            let overlay = null;
            
            function createOverlay() {
                overlay = document.createElement('div');
                overlay.style.position = 'absolute';
                overlay.style.border = '2px solid #0080ff';
                overlay.style.backgroundColor = 'rgba(0, 128, 255, 0.1)';
                overlay.style.pointerEvents = 'none';
                overlay.style.zIndex = '999999';
                document.body.appendChild(overlay);
            }
            
            function updateOverlay(element) {
                const rect = element.getBoundingClientRect();
                overlay.style.left = rect.left + 'px';
                overlay.style.top = rect.top + 'px';
                overlay.style.width = rect.width + 'px';
                overlay.style.height = rect.height + 'px';
            }
            
            function getElementInfo(element) {
                const styles = window.getComputedStyle(element);
                const rect = element.getBoundingClientRect();
                
                return {
                    tagName: element.tagName.toLowerCase(),
                    id: element.id,
                    className: element.className,
                    attributes: Array.from(element.attributes).map(attr => ({
                        name: attr.name,
                        value: attr.value
                    })),
                    computedStyles: {
                        display: styles.display,
                        position: styles.position,
                        width: styles.width,
                        height: styles.height,
                        margin: styles.margin,
                        padding: styles.padding,
                        border: styles.border,
                        color: styles.color,
                        backgroundColor: styles.backgroundColor,
                        fontSize: styles.fontSize,
                        fontFamily: styles.fontFamily
                    },
                    rect: {
                        left: rect.left,
                        top: rect.top,
                        width: rect.width,
                        height: rect.height
                    },
                    textContent: element.textContent.trim().substring(0, 100)
                };
            }
            
            document.addEventListener('mouseover', function(e) {
                if (!overlay) createOverlay();
                selectedElement = e.target;
                updateOverlay(selectedElement);
            });
            
            document.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                if (selectedElement) {
                    const info = getElementInfo(selectedElement);
                    window.postMessage({
                        type: 'element-inspected',
                        data: info
                    }, '*');
                }
                
                return false;
            }, true);
            
            window.__nexusInspector = {
                enable: () => overlay.style.display = 'block',
                disable: () => overlay.style.display = 'none',
                inspect: (selector) => {
                    const element = document.querySelector(selector);
                    if (element) {
                        return getElementInfo(element);
                    }
                    return null;
                }
            };
        })();
        """
        
    def get_injection_script(self) -> str:
        """Get script to inject into preview"""
        return self.inspection_script
        

class PerformanceProfiler:
    """Performance profiling tools"""
    
    def __init__(self):
        self.metrics_history = []
        self.profiling_script = """
        (function() {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    window.postMessage({
                        type: 'performance-entry',
                        data: {
                            name: entry.name,
                            entryType: entry.entryType,
                            startTime: entry.startTime,
                            duration: entry.duration
                        }
                    }, '*');
                }
            });
            
            observer.observe({ entryTypes: ['navigation', 'resource', 'measure'] });
            
            // Collect metrics
            function collectMetrics() {
                const navigation = performance.getEntriesByType('navigation')[0];
                const memory = performance.memory || {};
                
                return {
                    timestamp: new Date().toISOString(),
                    pageLoadTime: navigation ? navigation.loadEventEnd - navigation.fetchStart : 0,
                    firstPaint: navigation ? navigation.responseEnd - navigation.fetchStart : 0,
                    firstContentfulPaint: 0, // Would need specific API
                    domInteractive: navigation ? navigation.domInteractive : 0,
                    memoryUsage: {
                        usedJSHeapSize: memory.usedJSHeapSize || 0,
                        totalJSHeapSize: memory.totalJSHeapSize || 0,
                        jsHeapSizeLimit: memory.jsHeapSizeLimit || 0
                    },
                    networkRequests: performance.getEntriesByType('resource').length,
                    totalSize: performance.getEntriesByType('resource').reduce(
                        (sum, entry) => sum + (entry.transferSize || 0), 0
                    )
                };
            }
            
            // Send metrics periodically
            setInterval(() => {
                window.postMessage({
                    type: 'performance-metrics',
                    data: collectMetrics()
                }, '*');
            }, 1000);
            
            window.__nexusProfiler = {
                measure: (name, startMark, endMark) => {
                    performance.measure(name, startMark, endMark);
                },
                mark: (name) => {
                    performance.mark(name);
                },
                getMetrics: collectMetrics
            };
        })();
        """
        
    def analyze_metrics(self, metrics: List[PerformanceMetrics]) -> Dict[str, Any]:
        """Analyze performance metrics"""
        if not metrics:
            return {}
            
        # Calculate averages
        avg_load_time = sum(m.page_load_time for m in metrics) / len(metrics)
        avg_memory = sum(
            m.memory_usage.get("usedJSHeapSize", 0) for m in metrics
        ) / len(metrics)
        
        # Find issues
        issues = []
        
        if avg_load_time > 3000:  # 3 seconds
            issues.append({
                "type": "slow_load",
                "message": f"Average page load time is {avg_load_time:.0f}ms",
                "severity": "warning"
            })
            
        if avg_memory > 50 * 1024 * 1024:  # 50MB
            issues.append({
                "type": "high_memory",
                "message": f"High memory usage: {avg_memory / 1024 / 1024:.1f}MB",
                "severity": "warning"
            })
            
        return {
            "summary": {
                "avgLoadTime": avg_load_time,
                "avgMemory": avg_memory,
                "totalRequests": sum(m.network_requests for m in metrics),
            },
            "issues": issues,
            "metrics": metrics
        }
        

class AccessibilityChecker:
    """Accessibility checking tools"""
    
    def __init__(self):
        self.rules = self._load_rules()
        self.checking_script = """
        (function() {
            function checkAccessibility() {
                const issues = [];
                
                // Check images for alt text
                document.querySelectorAll('img').forEach(img => {
                    if (!img.alt) {
                        issues.push({
                            type: 'missing_alt',
                            element: img.outerHTML.substring(0, 100),
                            message: 'Image missing alt text',
                            severity: 'error'
                        });
                    }
                });
                
                // Check form labels
                document.querySelectorAll('input, select, textarea').forEach(input => {
                    if (!input.labels || input.labels.length === 0) {
                        if (!input.getAttribute('aria-label')) {
                            issues.push({
                                type: 'missing_label',
                                element: input.outerHTML.substring(0, 100),
                                message: 'Form input missing label',
                                severity: 'error'
                            });
                        }
                    }
                });
                
                // Check heading hierarchy
                let lastLevel = 0;
                document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(heading => {
                    const level = parseInt(heading.tagName.charAt(1));
                    if (level > lastLevel + 1) {
                        issues.push({
                            type: 'heading_skip',
                            element: heading.outerHTML.substring(0, 100),
                            message: `Heading level skipped from H${lastLevel} to H${level}`,
                            severity: 'warning'
                        });
                    }
                    lastLevel = level;
                });
                
                // Check color contrast
                // This is simplified - real implementation would be more complex
                
                // Check ARIA attributes
                document.querySelectorAll('[role]').forEach(element => {
                    const role = element.getAttribute('role');
                    // Check for required ARIA properties based on role
                });
                
                return issues;
            }
            
            window.__nexusA11y = {
                check: checkAccessibility,
                highlight: (selector) => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        el.style.outline = '3px solid red';
                    });
                }
            };
            
            // Auto-check on load
            window.addEventListener('load', () => {
                const issues = checkAccessibility();
                window.postMessage({
                    type: 'a11y-check',
                    data: issues
                }, '*');
            });
        })();
        """
        
    def _load_rules(self) -> Dict[str, Any]:
        """Load accessibility rules"""
        return {
            "wcag_2_1": {
                "level_a": [
                    "images_alt_text",
                    "form_labels",
                    "heading_hierarchy",
                    "color_contrast_minimum",
                    "keyboard_accessible",
                    "focus_visible",
                ],
                "level_aa": [
                    "color_contrast_enhanced",
                    "resize_text",
                    "consistent_navigation",
                ],
                "level_aaa": [
                    "color_contrast_maximum",
                    "no_interruptions",
                    "reading_level",
                ]
            }
        }
        

class NexusLivePreview:
    """Live preview system with hot reload"""
    
    def __init__(self):
        self.server = PreviewServer()
        self.hmr = HotModuleReplacement()
        self.console = ConsoleLogger()
        self.inspector = ElementInspector()
        self.profiler = PerformanceProfiler()
        self.accessibility = AccessibilityChecker()
        
        # Network profiles
        self.network_profiles = {
            "3g_slow": NetworkProfile("3G Slow", 50_000, 20_000, 400, 0.05),
            "3g_fast": NetworkProfile("3G Fast", 200_000, 80_000, 100, 0.02),
            "4g": NetworkProfile("4G", 1_500_000, 750_000, 50, 0.01),
            "wifi": NetworkProfile("WiFi", 30_000_000, 15_000_000, 10, 0.0),
            "offline": NetworkProfile("Offline", 0, 0, 0, 1.0),
        }
        
        # Device presets
        self.device_presets = {
            "iphone_12": DevicePreview(
                "iPhone 12", 390, 844,
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
                3.0, True, True
            ),
            "ipad": DevicePreview(
                "iPad", 820, 1180,
                "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)",
                2.0, True, True
            ),
            "pixel_5": DevicePreview(
                "Pixel 5", 393, 851,
                "Mozilla/5.0 (Linux; Android 11; Pixel 5)",
                2.75, True, True
            ),
            "desktop_1080": DevicePreview(
                "Desktop 1080p", 1920, 1080,
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                1.0, False, False
            ),
        }
        
        self.active_device = None
        self.active_network = None
        self.app = None
        self.runner = None
        self.file_observer = None
        
    async def start(self, project_path: Path, port: Optional[int] = None):
        """Start preview server"""
        self.server.base_path = project_path
        if port:
            self.server.port = port
            
        # Find available port
        self.server.port = self._find_available_port(self.server.port)
        
        # Setup web server
        self.app = web.Application()
        self._setup_routes()
        
        # Start file watching
        if Observer:
            self._start_file_watching()
            
        # Start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        site = web.TCPSite(
            self.runner,
            self.server.host,
            self.server.port
        )
        await site.start()
        
        print(f"Preview server started at http://{self.server.host}:{self.server.port}")
        
    def _find_available_port(self, start_port: int) -> int:
        """Find available port"""
        port = start_port
        while port < start_port + 100:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind((self.server.host, port))
                    return port
                except OSError:
                    port += 1
        raise RuntimeError("No available ports")
        
    def _setup_routes(self):
        """Setup web server routes"""
        # Static files
        self.app.router.add_static(
            '/',
            self.server.base_path,
            show_index=True
        )
        
        # WebSocket for HMR
        self.app.router.add_get('/ws', self._handle_websocket)
        
        # API endpoints
        self.app.router.add_get('/api/console', self._handle_console)
        self.app.router.add_post('/api/inspect', self._handle_inspect)
        self.app.router.add_get('/api/performance', self._handle_performance)
        self.app.router.add_get('/api/accessibility', self._handle_accessibility)
        
        # Inject preview scripts
        self.app.middlewares.append(self._inject_scripts_middleware)
        
    async def _handle_websocket(self, request):
        """Handle WebSocket connections"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        # Add to HMR clients
        self.hmr.websocket_clients.add(ws)
        
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self._handle_ws_message(ws, data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f'WebSocket error: {ws.exception()}')
        finally:
            self.hmr.websocket_clients.discard(ws)
            
        return ws
        
    async def _handle_ws_message(self, ws, data: dict):
        """Handle WebSocket message"""
        msg_type = data.get("type")
        
        if msg_type == "console-log":
            self.console.log(
                data.get("level", "log"),
                data.get("message", ""),
                data.get("source", "preview")
            )
        elif msg_type == "performance-metrics":
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                **data.get("data", {})
            )
            self.profiler.metrics_history.append(metrics)
        elif msg_type == "element-inspected":
            # Handle element inspection data
            pass
        elif msg_type == "a11y-check":
            # Handle accessibility check results
            pass
            
    async def _handle_console(self, request):
        """Handle console API requests"""
        since = request.query.get("since")
        if since:
            since = datetime.fromisoformat(since)
            
        logs = self.console.get_logs(since)
        return web.json_response(logs)
        
    async def _handle_inspect(self, request):
        """Handle element inspection requests"""
        data = await request.json()
        selector = data.get("selector")
        
        # Would send command to preview to inspect element
        return web.json_response({"status": "ok"})
        
    async def _handle_performance(self, request):
        """Handle performance API requests"""
        analysis = self.profiler.analyze_metrics(
            self.profiler.metrics_history[-100:]  # Last 100 metrics
        )
        return web.json_response(analysis)
        
    async def _handle_accessibility(self, request):
        """Handle accessibility API requests"""
        # Would return accessibility check results
        return web.json_response({"issues": []})
        
    @web.middleware
    async def _inject_scripts_middleware(self, request, handler):
        """Inject preview scripts into HTML"""
        response = await handler(request)
        
        if (response.content_type == 'text/html' and
            hasattr(response, 'text')):
            
            # Read original HTML
            html = await response.text()
            
            # Inject scripts before </body>
            scripts = f"""
            <script>
                // HMR WebSocket connection
                const ws = new WebSocket('ws://{self.server.host}:{self.server.port}/ws');
                
                ws.onmessage = (event) => {{
                    const data = JSON.parse(event.data);
                    if (data.type === 'hmr-update') {{
                        // Handle HMR update
                        console.log('HMR update received', data);
                        window.location.reload(); // Simple reload for now
                    }}
                }};
                
                // Console logging
                const originalLog = console.log;
                console.log = function(...args) {{
                    originalLog.apply(console, args);
                    ws.send(JSON.stringify({{
                        type: 'console-log',
                        level: 'log',
                        message: args.join(' ')
                    }}));
                }};
                
                {self.inspector.get_injection_script()}
                {self.profiler.profiling_script}
                {self.accessibility.checking_script}
            </script>
            """
            
            # Inject before </body>
            html = html.replace('</body>', f'{scripts}</body>')
            
            # Create new response
            return web.Response(
                text=html,
                content_type='text/html',
                headers=response.headers
            )
            
        return response
        
    def _start_file_watching(self):
        """Start watching files for changes"""
        if not Observer:
            return
            
        self.file_observer = Observer()
        
        handler = FileWatcher(self._on_file_change)
        self.file_observer.schedule(
            handler,
            str(self.server.base_path),
            recursive=True
        )
        
        self.file_observer.start()
        
    def _on_file_change(self, file_path: str):
        """Handle file change"""
        path = Path(file_path)
        
        # Skip non-relevant files
        if path.suffix not in ['.html', '.js', '.jsx', '.ts', '.tsx', '.css', '.scss']:
            return
            
        # Read file content
        try:
            content = path.read_text()
        except Exception:
            return
            
        # Handle HMR update
        relative_path = path.relative_to(self.server.base_path)
        asyncio.create_task(
            self.hmr.handle_change(str(relative_path), content)
        )
        
    def set_device(self, device_name: str):
        """Set device preview mode"""
        if device_name in self.device_presets:
            self.active_device = self.device_presets[device_name]
            # Would apply device settings to preview
            
    def set_network_profile(self, profile_name: str):
        """Set network throttling profile"""
        if profile_name in self.network_profiles:
            self.active_network = self.network_profiles[profile_name]
            # Would apply network throttling
            
    async def stop(self):
        """Stop preview server"""
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()
            
        if self.runner:
            await self.runner.cleanup()
            
        print("Preview server stopped")


async def main():
    """Test live preview system"""
    preview = NexusLivePreview()
    
    # Create test project
    test_dir = Path("test_preview")
    test_dir.mkdir(exist_ok=True)
    
    # Create test HTML file
    (test_dir / "index.html").write_text("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Preview</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
        </style>
    </head>
    <body>
        <h1>Live Preview Test</h1>
        <p>Edit this file to see hot reload in action!</p>
        <button onclick="console.log('Button clicked!')">Click me</button>
        
        <script>
            console.log('Page loaded');
            
            // Test performance
            performance.mark('custom-start');
            setTimeout(() => {
                performance.mark('custom-end');
                performance.measure('custom-operation', 'custom-start', 'custom-end');
            }, 1000);
        </script>
    </body>
    </html>
    """)
    
    # Start preview
    await preview.start(test_dir)
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await preview.stop()
        
    # Cleanup
    import shutil
    shutil.rmtree(test_dir)


if __name__ == "__main__":
    asyncio.run(main())