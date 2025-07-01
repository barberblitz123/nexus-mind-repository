#!/usr/bin/env python3
"""
NEXUS 2.0 CLI - Natural Language Command Interface
Provides quick access to all NEXUS capabilities through the command line
"""

import argparse
import asyncio
import json
import sys
import os
from typing import Optional, Dict, Any
from datetime import datetime
import requests
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
import aiohttp

# Initialize Rich console
console = Console()

# NEXUS API base URL
API_BASE = os.getenv("NEXUS_API_URL", "http://localhost:8002")

class NEXUSCLI:
    def __init__(self):
        self.console = console
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    def print_banner(self):
        """Print NEXUS CLI banner"""
        banner = """
[bold green]╔═══════════════════════════════════════════════╗
║             NEXUS 2.0 CLI Interface           ║
║        Omnipotent AI System Controller        ║
╚═══════════════════════════════════════════════╝[/bold green]
        """
        self.console.print(banner)
        
    async def submit_goal(self, goal: str, priority: str = "MEDIUM"):
        """Submit a natural language goal"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Submitting goal...", total=None)
            
            async with self.session.post(
                f"{API_BASE}/api/v2/goals",
                json={
                    "goal": goal,
                    "priority": priority
                }
            ) as resp:
                result = await resp.json()
                
        self.console.print(f"\n[green]✓[/green] Goal submitted successfully!")
        self.console.print(f"Goal ID: [cyan]{result['goal_id']}[/cyan]")
        
        if result.get('sub_goals'):
            self.console.print("\n[bold]Decomposed into sub-goals:[/bold]")
            for i, sub_goal in enumerate(result['sub_goals'], 1):
                self.console.print(f"  {i}. {sub_goal}")
                
    async def list_goals(self, status: Optional[str] = None):
        """List all goals"""
        params = {}
        if status:
            params['status'] = status
            
        async with self.session.get(
            f"{API_BASE}/api/v2/goals",
            params=params
        ) as resp:
            goals = await resp.json()
            
        if not goals:
            self.console.print("[yellow]No goals found[/yellow]")
            return
            
        table = Table(title="Active Goals")
        table.add_column("ID", style="cyan", width=12)
        table.add_column("Goal", style="white")
        table.add_column("Status", style="green")
        table.add_column("Progress", style="blue")
        table.add_column("Created", style="yellow")
        
        for goal in goals[:10]:  # Show top 10
            table.add_row(
                goal['id'][:8] + "...",
                goal['goal'][:50] + "..." if len(goal['goal']) > 50 else goal['goal'],
                goal['status'],
                f"{goal['progress']:.1f}%",
                datetime.fromisoformat(goal['created_at']).strftime("%Y-%m-%d %H:%M")
            )
            
        self.console.print(table)
        
    async def get_predictions(self, query: str):
        """Get system predictions"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Analyzing...", total=None)
            
            async with self.session.post(
                f"{API_BASE}/api/v2/predictions",
                json={"query": query}
            ) as resp:
                result = await resp.json()
                
        panel = Panel(
            f"[bold]{result['prediction']}[/bold]\n\n"
            f"Confidence: [green]{result['confidence']*100:.1f}%[/green]\n\n"
            f"[bold]Key Factors:[/bold]\n" +
            "\n".join(f"• {factor}" for factor in result.get('factors', [])),
            title=f"Prediction: {query}",
            border_style="green"
        )
        self.console.print(panel)
        
    async def show_learning_metrics(self):
        """Display learning metrics"""
        async with self.session.get(f"{API_BASE}/api/v2/learning/metrics") as resp:
            metrics = await resp.json()
            
        table = Table(title="Learning Metrics", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Goals", str(metrics['total_goals']))
        table.add_row("Completed Goals", str(metrics['completed_goals']))
        table.add_row("Accuracy Rate", f"{metrics['accuracy_rate']*100:.1f}%")
        table.add_row("Learning Rate", f"{metrics['learning_rate']:.4f}")
        table.add_row("Adaptations", str(metrics['adaptations']))
        table.add_row("Knowledge Nodes", f"{metrics['knowledge_nodes']:,}")
        table.add_row("Active Patterns", str(metrics['active_patterns']))
        
        self.console.print(table)
        
    async def conduct_research(self, topic: str, depth: str = "standard"):
        """Conduct research on a topic"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"Researching {topic}...", total=None)
            
            async with self.session.post(
                f"{API_BASE}/api/v2/research",
                json={
                    "topic": topic,
                    "depth": depth
                }
            ) as resp:
                result = await resp.json()
                
        self.console.print(f"\n[bold green]Research Results: {topic}[/bold green]\n")
        
        for finding in result.get('findings', []):
            panel = Panel(
                f"[bold]{finding['title']}[/bold]\n\n"
                f"{finding['summary']}\n\n"
                f"Confidence: [green]{finding['confidence']*100:.0f}%[/green]",
                border_style="blue"
            )
            self.console.print(panel)
            
    async def system_status(self):
        """Show system status"""
        # Get multiple status endpoints
        endpoints = [
            ("/api/stats", "MANUS Status"),
            ("/api/v2/learning/metrics", "Learning Metrics"),
        ]
        
        for endpoint, title in endpoints:
            try:
                async with self.session.get(f"{API_BASE}{endpoint}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.console.print(f"\n[bold cyan]{title}:[/bold cyan]")
                        self.console.print(json.dumps(data, indent=2))
            except:
                pass
                
    async def interactive_mode(self):
        """Start interactive CLI mode"""
        self.print_banner()
        self.console.print("\nType 'help' for available commands or 'exit' to quit.\n")
        
        commands = {
            'goal': 'Submit a natural language goal',
            'goals': 'List all goals',
            'predict': 'Get system predictions',
            'research': 'Conduct research on a topic',
            'learning': 'Show learning metrics',
            'status': 'Show system status',
            'help': 'Show this help message',
            'exit': 'Exit the CLI'
        }
        
        while True:
            try:
                command = Prompt.ask("\n[bold green]nexus>[/bold green]").strip().lower()
                
                if command == 'exit':
                    if Confirm.ask("Are you sure you want to exit?"):
                        break
                        
                elif command == 'help':
                    table = Table(title="Available Commands")
                    table.add_column("Command", style="cyan")
                    table.add_column("Description", style="white")
                    
                    for cmd, desc in commands.items():
                        table.add_row(cmd, desc)
                    self.console.print(table)
                    
                elif command == 'goal':
                    goal = Prompt.ask("Enter your goal")
                    priority = Prompt.ask(
                        "Priority",
                        choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                        default="MEDIUM"
                    )
                    await self.submit_goal(goal, priority)
                    
                elif command == 'goals':
                    status = Prompt.ask(
                        "Filter by status (optional)",
                        default="",
                        show_default=False
                    )
                    await self.list_goals(status if status else None)
                    
                elif command == 'predict':
                    query = Prompt.ask("What would you like to predict?")
                    await self.get_predictions(query)
                    
                elif command == 'research':
                    topic = Prompt.ask("Research topic")
                    depth = Prompt.ask(
                        "Depth",
                        choices=["quick", "standard", "deep"],
                        default="standard"
                    )
                    await self.conduct_research(topic, depth)
                    
                elif command == 'learning':
                    await self.show_learning_metrics()
                    
                elif command == 'status':
                    await self.system_status()
                    
                else:
                    self.console.print(f"[red]Unknown command: {command}[/red]")
                    self.console.print("Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'exit' command to quit properly.[/yellow]")
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")

async def main():
    parser = argparse.ArgumentParser(
        description="NEXUS 2.0 CLI - Natural Language Command Interface"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Goal command
    goal_parser = subparsers.add_parser('goal', help='Submit a goal')
    goal_parser.add_argument('goal', help='Natural language goal description')
    goal_parser.add_argument('-p', '--priority', 
                           choices=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
                           default='MEDIUM',
                           help='Goal priority')
    
    # Goals list command
    goals_parser = subparsers.add_parser('goals', help='List goals')
    goals_parser.add_argument('-s', '--status', help='Filter by status')
    
    # Predict command
    predict_parser = subparsers.add_parser('predict', help='Get predictions')
    predict_parser.add_argument('query', help='Prediction query')
    
    # Research command
    research_parser = subparsers.add_parser('research', help='Conduct research')
    research_parser.add_argument('topic', help='Research topic')
    research_parser.add_argument('-d', '--depth',
                               choices=['quick', 'standard', 'deep'],
                               default='standard',
                               help='Research depth')
    
    # Learning command
    learning_parser = subparsers.add_parser('learning', help='Show learning metrics')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    # Interactive mode
    interactive_parser = subparsers.add_parser('interactive', help='Start interactive mode')
    
    args = parser.parse_args()
    
    async with NEXUSCLI() as cli:
        if args.command == 'goal':
            await cli.submit_goal(args.goal, args.priority)
        elif args.command == 'goals':
            await cli.list_goals(args.status)
        elif args.command == 'predict':
            await cli.get_predictions(args.query)
        elif args.command == 'research':
            await cli.conduct_research(args.topic, args.depth)
        elif args.command == 'learning':
            await cli.show_learning_metrics()
        elif args.command == 'status':
            await cli.system_status()
        elif args.command == 'interactive' or not args.command:
            await cli.interactive_mode()
        else:
            parser.print_help()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)