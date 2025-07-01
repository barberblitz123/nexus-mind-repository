#!/usr/bin/env python3
"""
NEXUS Live Preview System - Real-time preview for web development
Supports React, Vue, vanilla JS, and static HTML with hot reload
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from urllib.parse import urlparse

# Web server imports
import aiohttp
from aiohttp import web
import aiofiles
import websockets

# Terminal rendering imports
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree
from rich.live import Live
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

# File watching
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# HTML/CSS parsing for terminal preview
from bs4 import BeautifulSoup
import cssutils
import pyfiglet

# Performance monitoring
import psutil


@dataclass
class PreviewConfig:
    """Configuration for preview server"""
    host: str = "localhost"
    port: int = 3000
    ws_port: int = 3001
    framework: str = "auto"  # auto, react, vue, vanilla, static
    root_dir: str = "."
    entry_file: str = "index.html"
    build_command: Optional[str] = None
    dev_command: Optional[str] = None
    terminal_preview: bool = True
    web_preview: bool = True
    hot_reload: bool = True
    performance_monitor: bool = True


class FileWatcher(FileSystemEventHandler):
    """Watch for file changes and trigger updates"""
    
    def __init__(self, callback, extensions=None):
        self.callback = callback
        self.extensions = extensions or ['.js', '.jsx', '.ts', '.tsx', '.vue', '.html', '.css']
        self.last_modified = {}
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Check file extension
        path = Path(event.src_path)
        if path.suffix not in self.extensions:
            return
            
        # Debounce rapid changes
        current_time = time.time()
        if path in self.last_modified:
            if current_time - self.last_modified[path] < 0.5:
                return
                
        self.last_modified[path] = current_time
        self.callback(event.src_path)


class TerminalRenderer:
    """Render web content in terminal using ASCII art"""
    
    def __init__(self, console: Console):
        self.console = console
        self.layout_cache = {}
        
    def render_html(self, html_content: str) -> Layout:
        """Convert HTML to terminal layout"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Create main layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Render header
        title = soup.find('title')
        if title:
            header_text = pyfiglet.figlet_format(title.text, font='small')
            layout["header"].update(Panel(header_text, style="bold blue"))
        
        # Render body content
        body_tree = self._build_component_tree(soup.body if soup.body else soup)
        layout["body"].update(Panel(body_tree, title="Component Hierarchy"))
        
        # Render footer with interaction hints
        footer_text = "[bold]Interactive Elements:[/bold] "
        buttons = soup.find_all('button')
        links = soup.find_all('a')
        forms = soup.find_all('form')
        
        interactions = []
        if buttons:
            interactions.append(f"{len(buttons)} buttons")
        if links:
            interactions.append(f"{len(links)} links")
        if forms:
            interactions.append(f"{len(forms)} forms")
            
        footer_text += ", ".join(interactions) if interactions else "None"
        layout["footer"].update(Panel(footer_text, style="dim"))
        
        return layout
        
    def _build_component_tree(self, element, max_depth=5, current_depth=0):
        """Build a tree representation of HTML elements"""
        if current_depth >= max_depth:
            return Tree("...")
            
        # Create tree node
        node_name = element.name if hasattr(element, 'name') else str(element)
        classes = element.get('class', []) if hasattr(element, 'get') else []
        id_attr = element.get('id', '') if hasattr(element, 'get') else ''
        
        # Format node label
        label = f"[bold cyan]{node_name}[/bold cyan]"
        if id_attr:
            label += f" [yellow]#{id_attr}[/yellow]"
        if classes:
            label += f" [green].{'.'.join(classes)}[/green]"
            
        tree = Tree(label)
        
        # Add children
        if hasattr(element, 'children'):
            for child in element.children:
                if hasattr(child, 'name'):
                    child_tree = self._build_component_tree(child, max_depth, current_depth + 1)
                    tree.add(child_tree)
                elif child.strip():  # Text content
                    text = child.strip()[:50]  # Truncate long text
                    if len(child.strip()) > 50:
                        text += "..."
                    tree.add(f'[dim]"{text}"[/dim]')
                    
        return tree
        
    def render_styles(self, css_content: str) -> Table:
        """Render CSS styles as a table"""
        table = Table(title="Styles", show_header=True)
        table.add_column("Selector", style="cyan")
        table.add_column("Properties", style="green")
        
        # Parse CSS
        sheet = cssutils.parseString(css_content)
        for rule in sheet:
            if rule.type == rule.STYLE_RULE:
                selector = rule.selectorText
                properties = []
                for prop in rule.style:
                    properties.append(f"{prop.name}: {prop.value}")
                    
                table.add_row(selector, "\n".join(properties[:5]))  # Show first 5 properties
                
        return table


class WebSocketHandler:
    """Handle WebSocket connections for hot reload"""
    
    def __init__(self):
        self.connections: Set[websockets.WebSocketServerProtocol] = set()
        self.state_cache = {}
        
    async def handler(self, websocket, path):
        """Handle WebSocket connection"""
        self.connections.add(websocket)
        try:
            await websocket.send(json.dumps({
                "type": "connected",
                "message": "Hot reload connected"
            }))
            
            async for message in websocket:
                data = json.loads(message)
                await self.handle_message(data, websocket)
                
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connections.remove(websocket)
            
    async def handle_message(self, data: dict, websocket):
        """Handle incoming WebSocket message"""
        msg_type = data.get("type")
        
        if msg_type == "state_update":
            # Cache component state
            component_id = data.get("componentId")
            if component_id:
                self.state_cache[component_id] = data.get("state")
                
        elif msg_type == "interaction":
            # Handle user interaction from preview
            await self.broadcast({
                "type": "interaction_event",
                "data": data
            })
            
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if self.connections:
            message_json = json.dumps(message)
            await asyncio.gather(
                *[ws.send(message_json) for ws in self.connections],
                return_exceptions=True
            )
            
    async def trigger_reload(self, file_path: str):
        """Trigger hot reload for file change"""
        await self.broadcast({
            "type": "reload",
            "file": file_path,
            "timestamp": datetime.now().isoformat()
        })


class PreviewServer:
    """Main preview server handling HTTP and WebSocket"""
    
    def __init__(self, config: PreviewConfig):
        self.config = config
        self.console = Console()
        self.terminal_renderer = TerminalRenderer(self.console)
        self.ws_handler = WebSocketHandler()
        self.framework_detector = FrameworkDetector()
        self.performance_monitor = PerformanceMonitor() if config.performance_monitor else None
        self.app = web.Application()
        self.setup_routes()
        
    def setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get('/', self.serve_index)
        self.app.router.add_get('/ws', self.websocket_endpoint)
        self.app.router.add_get('/api/performance', self.get_performance)
        self.app.router.add_get('/api/component/{component_id}', self.get_component)
        self.app.router.add_post('/api/interaction', self.handle_interaction)
        self.app.router.add_static('/', self.config.root_dir, show_index=True)
        
    async def serve_index(self, request):
        """Serve main index file with hot reload injection"""
        index_path = Path(self.config.root_dir) / self.config.entry_file
        
        if not index_path.exists():
            return web.Response(text="Index file not found", status=404)
            
        async with aiofiles.open(index_path, 'r') as f:
            content = await f.read()
            
        # Inject hot reload script
        if self.config.hot_reload:
            hot_reload_script = self._generate_hot_reload_script()
            content = content.replace('</body>', f'{hot_reload_script}</body>')
            
        # Update terminal preview if enabled
        if self.config.terminal_preview:
            asyncio.create_task(self._update_terminal_preview(content))
            
        return web.Response(text=content, content_type='text/html')
        
    def _generate_hot_reload_script(self) -> str:
        """Generate hot reload client script"""
        return f"""
        <script>
        (function() {{
            const ws = new WebSocket('ws://{self.config.host}:{self.config.ws_port}');
            let reconnectInterval = null;
            
            ws.onopen = () => {{
                console.log('🔥 Hot reload connected');
                if (reconnectInterval) {{
                    clearInterval(reconnectInterval);
                    reconnectInterval = null;
                }}
            }};
            
            ws.onmessage = (event) => {{
                const data = JSON.parse(event.data);
                
                if (data.type === 'reload') {{
                    console.log('🔄 Reloading:', data.file);
                    
                    // Framework-specific reload
                    if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {{
                        // React hot reload
                        window.location.reload();
                    }} else if (window.Vue) {{
                        // Vue hot reload
                        window.location.reload();
                    }} else {{
                        // Generic reload
                        window.location.reload();
                    }}
                }}
            }};
            
            ws.onclose = () => {{
                console.log('🔌 Hot reload disconnected');
                // Attempt to reconnect
                if (!reconnectInterval) {{
                    reconnectInterval = setInterval(() => {{
                        window.location.reload();
                    }}, 2000);
                }}
            }};
            
            // Capture component state
            window.__NEXUS_PREVIEW__ = {{
                captureState: function(componentId, state) {{
                    ws.send(JSON.stringify({{
                        type: 'state_update',
                        componentId: componentId,
                        state: state
                    }}));
                }},
                
                captureInteraction: function(event) {{
                    ws.send(JSON.stringify({{
                        type: 'interaction',
                        element: event.target.tagName,
                        id: event.target.id,
                        classes: event.target.className,
                        eventType: event.type
                    }}));
                }}
            }};
            
            // Auto-attach interaction listeners
            document.addEventListener('click', window.__NEXUS_PREVIEW__.captureInteraction);
            document.addEventListener('submit', window.__NEXUS_PREVIEW__.captureInteraction);
        }})();
        </script>
        """
        
    async def websocket_endpoint(self, request):
        """WebSocket endpoint for hot reload"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        # Handle WebSocket messages
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                await self.ws_handler.handle_message(data, ws)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                self.console.print(f'[red]WebSocket error: {ws.exception()}[/red]')
                
        return ws
        
    async def get_performance(self, request):
        """Get performance metrics"""
        if not self.performance_monitor:
            return web.json_response({"error": "Performance monitoring disabled"}, status=404)
            
        metrics = self.performance_monitor.get_metrics()
        return web.json_response(metrics)
        
    async def get_component(self, request):
        """Get component information"""
        component_id = request.match_info['component_id']
        
        # Get cached component state
        state = self.ws_handler.state_cache.get(component_id)
        
        return web.json_response({
            "componentId": component_id,
            "state": state,
            "timestamp": datetime.now().isoformat()
        })
        
    async def handle_interaction(self, request):
        """Handle interaction from preview"""
        data = await request.json()
        
        # Broadcast interaction to all clients
        await self.ws_handler.broadcast({
            "type": "interaction_received",
            "data": data
        })
        
        return web.json_response({"status": "ok"})
        
    async def _update_terminal_preview(self, html_content: str):
        """Update terminal preview with HTML content"""
        try:
            layout = self.terminal_renderer.render_html(html_content)
            self.console.clear()
            self.console.print(layout)
        except Exception as e:
            self.console.print(f"[red]Terminal preview error: {e}[/red]")
            
    async def start(self):
        """Start preview server"""
        # Start file watcher
        if self.config.hot_reload:
            self._start_file_watcher()
            
        # Start WebSocket server
        ws_server = await websockets.serve(
            self.ws_handler.handler,
            self.config.host,
            self.config.ws_port
        )
        
        # Start HTTP server
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.config.host, self.config.port)
        await site.start()
        
        self.console.print(f"""
[bold green]🚀 NEXUS Live Preview Started![/bold green]

[bold]Web Preview:[/bold] http://{self.config.host}:{self.config.port}
[bold]WebSocket:[/bold] ws://{self.config.host}:{self.config.ws_port}
[bold]Framework:[/bold] {self.config.framework}
[bold]Hot Reload:[/bold] {'✅ Enabled' if self.config.hot_reload else '❌ Disabled'}
[bold]Terminal Preview:[/bold] {'✅ Enabled' if self.config.terminal_preview else '❌ Disabled'}

Press Ctrl+C to stop
        """)
        
        # Keep server running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            pass
        finally:
            await ws_server.close()
            await runner.cleanup()
            
    def _start_file_watcher(self):
        """Start watching for file changes"""
        def on_file_change(file_path):
            asyncio.run(self.ws_handler.trigger_reload(file_path))
            self.console.print(f"[yellow]📝 File changed: {file_path}[/yellow]")
            
        watcher = FileWatcher(on_file_change)
        observer = Observer()
        observer.schedule(watcher, self.config.root_dir, recursive=True)
        observer.start()


class FrameworkDetector:
    """Detect web framework from project files"""
    
    def detect(self, root_dir: str) -> str:
        """Detect framework type"""
        root_path = Path(root_dir)
        
        # Check for package.json
        package_json = root_path / "package.json"
        if package_json.exists():
            with open(package_json) as f:
                data = json.load(f)
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                
                if "react" in deps or "react-dom" in deps:
                    return "react"
                elif "vue" in deps:
                    return "vue"
                elif "svelte" in deps:
                    return "svelte"
                    
        # Check for framework-specific files
        if (root_path / "vue.config.js").exists():
            return "vue"
        elif (root_path / "next.config.js").exists():
            return "react"
        elif any(root_path.glob("*.jsx")):
            return "react"
        elif any(root_path.glob("*.vue")):
            return "vue"
            
        # Check HTML files for framework hints
        for html_file in root_path.glob("**/*.html"):
            with open(html_file) as f:
                content = f.read()
                if '<div id="app">' in content and 'vue' in content.lower():
                    return "vue"
                elif '<div id="root">' in content:
                    return "react"
                    
        return "vanilla"


class PerformanceMonitor:
    """Monitor preview performance metrics"""
    
    def __init__(self):
        self.metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "response_times": [],
            "render_times": []
        }
        self.start_time = time.time()
        
    def record_metric(self, metric_type: str, value: float):
        """Record a performance metric"""
        if metric_type in self.metrics:
            self.metrics[metric_type].append({
                "value": value,
                "timestamp": time.time() - self.start_time
            })
            
            # Keep only last 100 entries
            if len(self.metrics[metric_type]) > 100:
                self.metrics[metric_type].pop(0)
                
    def get_metrics(self) -> dict:
        """Get current performance metrics"""
        # Add current system metrics
        self.record_metric("cpu_usage", psutil.cpu_percent())
        self.record_metric("memory_usage", psutil.virtual_memory().percent)
        
        return {
            "uptime": time.time() - self.start_time,
            "metrics": self.metrics,
            "summary": {
                "avg_cpu": self._calculate_average("cpu_usage"),
                "avg_memory": self._calculate_average("memory_usage"),
                "avg_response_time": self._calculate_average("response_times"),
                "avg_render_time": self._calculate_average("render_times")
            }
        }
        
    def _calculate_average(self, metric_type: str) -> float:
        """Calculate average for a metric"""
        values = [m["value"] for m in self.metrics.get(metric_type, [])]
        return sum(values) / len(values) if values else 0


class DeviceEmulator:
    """Emulate different devices for responsive testing"""
    
    DEVICES = {
        "iphone-12": {"width": 390, "height": 844, "ua": "iPhone"},
        "ipad": {"width": 810, "height": 1080, "ua": "iPad"},
        "desktop": {"width": 1920, "height": 1080, "ua": "Desktop"},
        "galaxy-s21": {"width": 360, "height": 800, "ua": "Android"}
    }
    
    @classmethod
    def get_viewport_script(cls, device: str) -> str:
        """Get viewport emulation script"""
        if device not in cls.DEVICES:
            device = "desktop"
            
        config = cls.DEVICES[device]
        return f"""
        <meta name="viewport" content="width={config['width']}, initial-scale=1">
        <style>
            @media (max-width: {config['width']}px) {{
                body {{ max-width: {config['width']}px; }}
            }}
        </style>
        """


class ComponentPlayground:
    """Interactive component playground"""
    
    def __init__(self, framework: str):
        self.framework = framework
        self.components = {}
        
    def register_component(self, name: str, props: dict):
        """Register a component for playground"""
        self.components[name] = {
            "props": props,
            "instances": []
        }
        
    def generate_playground_html(self) -> str:
        """Generate playground HTML"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Component Playground</title>
            <style>
                .playground {{
                    display: grid;
                    grid-template-columns: 300px 1fr;
                    height: 100vh;
                }}
                .controls {{
                    background: #f0f0f0;
                    padding: 20px;
                    overflow-y: auto;
                }}
                .preview {{
                    padding: 20px;
                    overflow-y: auto;
                }}
                .prop-control {{
                    margin-bottom: 15px;
                }}
                .prop-control label {{
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                }}
                .prop-control input, .prop-control select {{
                    width: 100%;
                    padding: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="playground">
                <div class="controls">
                    <h2>Props</h2>
                    <div id="prop-controls"></div>
                </div>
                <div class="preview">
                    <h2>Preview</h2>
                    <div id="component-preview"></div>
                </div>
            </div>
            <script>
                // Component playground logic
                const playground = {self._generate_playground_script()};
            </script>
        </body>
        </html>
        """
        
    def _generate_playground_script(self) -> str:
        """Generate playground JavaScript"""
        if self.framework == "react":
            return """
            {
                updateComponent: function(props) {
                    // React component update
                    ReactDOM.render(
                        React.createElement(CurrentComponent, props),
                        document.getElementById('component-preview')
                    );
                }
            }
            """
        elif self.framework == "vue":
            return """
            {
                updateComponent: function(props) {
                    // Vue component update
                    if (window.vueApp) {
                        window.vueApp.$data = props;
                    }
                }
            }
            """
        else:
            return """
            {
                updateComponent: function(props) {
                    // Vanilla JS update
                    const preview = document.getElementById('component-preview');
                    preview.innerHTML = JSON.stringify(props, null, 2);
                }
            }
            """


async def main():
    """Main entry point"""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="NEXUS Live Preview System")
    parser.add_argument("--port", type=int, default=3000, help="HTTP server port")
    parser.add_argument("--ws-port", type=int, default=3001, help="WebSocket port")
    parser.add_argument("--root", default=".", help="Root directory")
    parser.add_argument("--entry", default="index.html", help="Entry file")
    parser.add_argument("--framework", default="auto", help="Framework type")
    parser.add_argument("--no-terminal", action="store_true", help="Disable terminal preview")
    parser.add_argument("--no-hot-reload", action="store_true", help="Disable hot reload")
    parser.add_argument("--no-performance", action="store_true", help="Disable performance monitoring")
    
    args = parser.parse_args()
    
    # Create configuration
    config = PreviewConfig(
        port=args.port,
        ws_port=args.ws_port,
        root_dir=args.root,
        entry_file=args.entry,
        framework=args.framework,
        terminal_preview=not args.no_terminal,
        hot_reload=not args.no_hot_reload,
        performance_monitor=not args.no_performance
    )
    
    # Auto-detect framework if needed
    if config.framework == "auto":
        detector = FrameworkDetector()
        config.framework = detector.detect(config.root_dir)
    
    # Create and start server
    server = PreviewServer(config)
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())