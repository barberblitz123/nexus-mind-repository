#!/usr/bin/env python3
"""
NEXUS Launch Demo Script
Shows NEXUS creating a React dashboard in under 2 minutes
"""

import asyncio
import time
import sys
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.align import Align
from typing import List, Dict

console = Console()

# Import animations
from nexus_loading_animation import NEXUSAnimations

class NEXUSDemo:
    """Demo script showing NEXUS capabilities"""
    
    def __init__(self):
        self.console = console
        self.animations = NEXUSAnimations()
        self.start_time = None
        
    async def run_demo(self):
        """Run the complete demo"""
        self.console.clear()
        
        # 1. Show terminal opening
        await self.show_terminal_open()
        
        # 2. User types command with voice
        await self.simulate_voice_command()
        
        # 3. NEXUS processes and creates the app
        await self.nexus_creates_app()
        
        # 4. Show deployment
        await self.show_deployment()
        
        # 5. Final summary
        await self.show_summary()
    
    async def show_terminal_open(self):
        """Simulate terminal opening"""
        # Terminal prompt
        self.console.print("\n" * 5)
        self.console.print("[dim]user@nexus[/dim]:[blue]~[/blue]$ ", end="")
        await asyncio.sleep(0.5)
        
        # Type nexus command
        command = "nexus"
        for char in command:
            self.console.print(char, end="")
            sys.stdout.flush()
            await asyncio.sleep(0.1)
        
        self.console.print()
        await asyncio.sleep(0.5)
        
        # Show NEXUS starting
        self.console.clear()
        self.animations.matrix_rain(duration=1.5)
        
    async def simulate_voice_command(self):
        """Simulate voice command"""
        self.console.clear()
        
        # Show voice indicator
        voice_panel = Panel(
            "[bold cyan]🎤 Voice Control Active[/bold cyan]\n\n"
            "[dim]Say your command...[/dim]",
            border_style="cyan",
            width=50
        )
        
        self.console.print("\n" * 5)
        self.console.print(Align.center(voice_panel))
        await asyncio.sleep(1)
        
        # Simulate voice recognition
        self.console.clear()
        self.console.print("\n" * 5)
        
        voice_panel = Panel(
            "[bold cyan]🎤 Voice Control Active[/bold cyan]\n\n"
            "[green]Recognized:[/green]\n"
            "\"Create a React dashboard with real-time analytics,\n"
            "user authentication, and beautiful charts\"",
            border_style="cyan",
            width=60
        )
        
        self.console.print(Align.center(voice_panel))
        await asyncio.sleep(2)
        
        # Show processing
        self.console.print("\n")
        self.console.print(Align.center("[bold cyan]Processing request...[/bold cyan]"))
        await asyncio.sleep(1)
        
    async def nexus_creates_app(self):
        """Show NEXUS creating the application"""
        self.start_time = datetime.now()
        self.console.clear()
        
        # Show NEXUS thinking
        thinking_panel = Panel(
            "[bold cyan]🧠 NEXUS Consciousness Active[/bold cyan]\n\n"
            "• Analyzing requirements\n"
            "• Planning architecture\n"
            "• Selecting optimal technologies\n"
            "• Designing component structure",
            title="[bold]NEXUS Thinking[/bold]",
            border_style="cyan"
        )
        
        self.console.print("\n")
        self.console.print(thinking_panel)
        await asyncio.sleep(2)
        
        # Show creation progress
        self.console.clear()
        await self.show_creation_progress()
        
    async def show_creation_progress(self):
        """Show detailed creation progress"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        # Header
        layout["header"].update(
            Panel("[bold cyan]NEXUS Creating React Dashboard[/bold cyan]", border_style="cyan")
        )
        
        # Footer with timer
        start = datetime.now()
        
        # Tasks to complete
        tasks = [
            ("Setting up project structure", "create-react-app nexus-dashboard"),
            ("Installing dependencies", "npm install recharts axios react-router-dom"),
            ("Creating authentication system", "JWT-based auth with secure endpoints"),
            ("Building dashboard layout", "Responsive grid with sidebars"),
            ("Implementing real-time data", "WebSocket connections for live updates"),
            ("Adding analytics charts", "Line, bar, pie charts with Recharts"),
            ("Setting up state management", "Redux Toolkit for global state"),
            ("Creating API endpoints", "RESTful API with Express backend"),
            ("Adding user management", "User CRUD with role-based access"),
            ("Implementing dark mode", "Theme switching with CSS variables"),
            ("Writing unit tests", "Jest and React Testing Library"),
            ("Optimizing performance", "Code splitting and lazy loading"),
            ("Building production bundle", "npm run build"),
            ("Deploying to cloud", "Vercel deployment with CI/CD")
        ]
        
        # Code preview
        code_examples = [
            ("App.jsx", """import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <Dashboard />
      </Router>
    </ThemeProvider>
  );
}

export default App;"""),
            ("Dashboard.jsx", """import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';
import useWebSocket from './hooks/useWebSocket';

const Dashboard = () => {
  const [data, setData] = useState([]);
  const { messages } = useWebSocket('ws://localhost:8080');
  
  useEffect(() => {
    // Update charts with real-time data
    if (messages.length > 0) {
      setData(prev => [...prev, messages[messages.length - 1]]);
    }
  }, [messages]);
  
  return (
    <div className="dashboard">
      <h1>Real-Time Analytics</h1>
      <LineChart width={600} height={300} data={data}>
        <Line type="monotone" dataKey="value" stroke="#8884d8" />
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="time" />
        <YAxis />
      </LineChart>
    </div>
  );
};"""),
            ("auth.js", """import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';

export const authenticateUser = async (email, password) => {
  const user = await User.findOne({ email });
  
  if (!user || !await bcrypt.compare(password, user.password)) {
    throw new Error('Invalid credentials');
  }
  
  const token = jwt.sign(
    { userId: user.id, role: user.role },
    process.env.JWT_SECRET,
    { expiresIn: '24h' }
  );
  
  return { user, token };
};""")
        ]
        
        current_code_idx = 0
        
        with Live(layout, refresh_per_second=4, console=self.console) as live:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            ) as progress:
                
                main_task = progress.add_task("Creating application...", total=len(tasks))
                
                for i, (task_name, task_detail) in enumerate(tasks):
                    # Update progress
                    progress.update(main_task, description=f"[cyan]{task_name}[/cyan]")
                    
                    # Update main layout with split view
                    main_layout = Layout()
                    main_layout.split_row(
                        Layout(Panel(progress, title="Progress", border_style="green"), name="progress"),
                        Layout(name="code")
                    )
                    
                    # Show code
                    if i % 4 == 0 and current_code_idx < len(code_examples):
                        file_name, code = code_examples[current_code_idx]
                        code_panel = Panel(
                            Syntax(code, "javascript", theme="monokai", line_numbers=True),
                            title=f"[bold yellow]{file_name}[/bold yellow]",
                            border_style="yellow"
                        )
                        main_layout["code"].update(code_panel)
                        current_code_idx += 1
                    
                    layout["main"].update(main_layout)
                    
                    # Update footer with elapsed time
                    elapsed = (datetime.now() - start).total_seconds()
                    layout["footer"].update(
                        Panel(f"[bold green]Elapsed: {elapsed:.1f}s[/bold green]", border_style="green")
                    )
                    
                    # Simulate work
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    progress.update(main_task, advance=1)
        
        # Show completion
        self.console.clear()
        self.animations.glitch_text("APPLICATION CREATED SUCCESSFULLY", duration=1.0)
        await asyncio.sleep(1)
    
    async def show_deployment(self):
        """Show deployment process"""
        self.console.clear()
        
        deployment_panel = Panel(
            "[bold green]🚀 Deploying to Production[/bold green]\n\n"
            "• Building optimized bundle... ✓\n"
            "• Uploading to Vercel... ✓\n"
            "• Running health checks... ✓\n"
            "• Configuring CDN... ✓\n"
            "• SSL certificate provisioned... ✓\n\n"
            "[bold cyan]Live URL:[/bold cyan] https://nexus-dashboard.vercel.app\n\n"
            "[dim]Deployment completed in 23 seconds[/dim]",
            title="[bold]Deployment[/bold]",
            border_style="green",
            width=60
        )
        
        self.console.print("\n" * 3)
        self.console.print(Align.center(deployment_panel))
        await asyncio.sleep(3)
    
    async def show_summary(self):
        """Show final summary"""
        self.console.clear()
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        # Create summary table
        table = Table(title="NEXUS Performance Summary", box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")
        
        table.add_row("Total Time", f"{elapsed:.1f} seconds")
        table.add_row("Files Created", "47")
        table.add_row("Lines of Code", "3,284")
        table.add_row("Dependencies Installed", "23")
        table.add_row("Tests Written", "15")
        table.add_row("Components Built", "12")
        table.add_row("API Endpoints", "8")
        table.add_row("Lighthouse Score", "98/100")
        
        self.console.print("\n" * 3)
        self.console.print(Align.center(table))
        
        # Final message
        final_panel = Panel(
            "[bold cyan]✨ NEXUS has successfully created your React dashboard![/bold cyan]\n\n"
            f"From voice command to production deployment in [bold green]{elapsed:.0f} seconds[/bold green]\n\n"
            "[bold]What NEXUS created:[/bold]\n"
            "• Full-stack React application with TypeScript\n"
            "• Real-time analytics with WebSocket\n"
            "• JWT authentication system\n"
            "• Beautiful, responsive UI with dark mode\n"
            "• Complete test coverage\n"
            "• Production-ready deployment\n\n"
            "[bold yellow]This is NEXUS - Your AI pair programmer that lives in your terminal![/bold yellow]",
            border_style="cyan",
            width=70
        )
        
        self.console.print("\n")
        self.console.print(Align.center(final_panel))
        
        # Show command to install
        self.console.print("\n\n")
        self.console.print(Align.center(
            "[bold cyan]Get NEXUS:[/bold cyan] [green]curl -sSL https://nexus.ai/install | bash[/green]"
        ))
        self.console.print("\n")


# Import for random delays
import random

async def main():
    """Run the demo"""
    demo = NEXUSDemo()
    
    try:
        await demo.run_demo()
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted[/yellow]")


if __name__ == "__main__":
    asyncio.run(main())