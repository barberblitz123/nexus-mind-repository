#!/usr/bin/env python3
"""
NEXUS Loading Animations and Visual Effects
"""

import time
import random
import sys
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.live import Live
from typing import List

console = Console()

class NEXUSAnimations:
    """Collection of loading animations and visual effects"""
    
    @staticmethod
    def matrix_rain(duration: float = 3.0):
        """Matrix-style rain effect"""
        width = console.width
        height = 20
        
        # Characters for the rain
        chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
        
        # Initialize columns
        columns = [[random.choice(chars) for _ in range(height)] for _ in range(width)]
        speeds = [random.uniform(0.1, 0.3) for _ in range(width)]
        positions = [random.randint(0, height) for _ in range(width)]
        
        start_time = time.time()
        
        with Live(console=console, refresh_per_second=20) as live:
            while time.time() - start_time < duration:
                # Create the display
                lines = []
                for y in range(height):
                    line = ""
                    for x in range(width):
                        if positions[x] - y >= 0 and positions[x] - y < len(columns[x]):
                            char = columns[x][positions[x] - y]
                            if y == positions[x]:
                                line += f"[bright_green]{char}[/bright_green]"
                            elif y == positions[x] - 1:
                                line += f"[green]{char}[/green]"
                            else:
                                line += f"[dim green]{char}[/dim green]"
                        else:
                            line += " "
                    lines.append(line)
                
                # Update positions
                for x in range(width):
                    positions[x] += speeds[x]
                    if positions[x] > height + 10:
                        positions[x] = -10
                        columns[x] = [random.choice(chars) for _ in range(height)]
                
                # Display
                display = "\n".join(lines)
                live.update(Panel(display, border_style="green", title="[bold green]NEXUS INITIALIZING[/bold green]"))
                
                time.sleep(0.05)
    
    @staticmethod
    def quantum_particles(duration: float = 2.0):
        """Quantum particle animation"""
        width = 60
        height = 20
        particles = []
        
        # Create particles
        for _ in range(30):
            particles.append({
                'x': random.randint(0, width),
                'y': random.randint(0, height),
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(-1, 1),
                'char': random.choice('⚛◉○◦∙·')
            })
        
        start_time = time.time()
        
        with Live(console=console, refresh_per_second=30) as live:
            while time.time() - start_time < duration:
                # Create display grid
                grid = [[' ' for _ in range(width)] for _ in range(height)]
                
                # Update and draw particles
                for particle in particles:
                    # Update position
                    particle['x'] += particle['vx']
                    particle['y'] += particle['vy']
                    
                    # Bounce off walls
                    if particle['x'] <= 0 or particle['x'] >= width - 1:
                        particle['vx'] *= -1
                    if particle['y'] <= 0 or particle['y'] >= height - 1:
                        particle['vy'] *= -1
                    
                    # Draw particle
                    x, y = int(particle['x']), int(particle['y'])
                    if 0 <= x < width and 0 <= y < height:
                        grid[y][x] = particle['char']
                
                # Convert grid to string
                lines = []
                for row in grid:
                    lines.append(''.join(row))
                
                display = '\n'.join(lines)
                live.update(Panel(
                    f"[cyan]{display}[/cyan]",
                    title="[bold cyan]QUANTUM CONSCIOUSNESS LOADING[/bold cyan]",
                    border_style="cyan"
                ))
                
                time.sleep(0.033)
    
    @staticmethod
    def dna_helix(duration: float = 2.0):
        """DNA helix animation"""
        width = 40
        height = 20
        
        start_time = time.time()
        
        with Live(console=console, refresh_per_second=20) as live:
            while time.time() - start_time < duration:
                t = time.time() - start_time
                lines = []
                
                for y in range(height):
                    # Calculate helix position
                    offset = t * 2
                    x1 = int(width/2 + 10 * math.sin((y + offset) * 0.5))
                    x2 = int(width/2 + 10 * math.sin((y + offset) * 0.5 + math.pi))
                    
                    # Create line
                    line = [' '] * width
                    if 0 <= x1 < width:
                        line[x1] = '●'
                    if 0 <= x2 < width:
                        line[x2] = '●'
                    
                    # Connect with bonds
                    if abs(x1 - x2) > 2:
                        for x in range(min(x1, x2) + 1, max(x1, x2)):
                            if 0 <= x < width:
                                line[x] = '─'
                    
                    lines.append(''.join(line))
                
                display = '\n'.join(lines)
                live.update(Panel(
                    f"[magenta]{display}[/magenta]",
                    title="[bold magenta]LOADING MEMORY DNA[/bold magenta]",
                    border_style="magenta"
                ))
                
                time.sleep(0.05)
    
    @staticmethod
    def neural_network(duration: float = 2.0):
        """Neural network activation animation"""
        nodes = []
        connections = []
        
        # Create nodes
        layers = [3, 5, 5, 3]
        y_spacing = 5
        x_spacing = 15
        
        for layer_idx, layer_size in enumerate(layers):
            for node_idx in range(layer_size):
                x = layer_idx * x_spacing + 10
                y = node_idx * y_spacing + 5
                nodes.append({
                    'x': x,
                    'y': y,
                    'layer': layer_idx,
                    'activation': 0.0
                })
        
        # Create connections
        node_idx = 0
        for layer_idx, layer_size in enumerate(layers[:-1]):
            next_layer_start = node_idx + layer_size
            next_layer_size = layers[layer_idx + 1]
            
            for i in range(layer_size):
                for j in range(next_layer_size):
                    connections.append({
                        'from': node_idx + i,
                        'to': next_layer_start + j,
                        'weight': random.uniform(-1, 1)
                    })
            
            node_idx += layer_size
        
        start_time = time.time()
        
        with Live(console=console, refresh_per_second=20) as live:
            while time.time() - start_time < duration:
                t = time.time() - start_time
                
                # Activate nodes in waves
                for node in nodes:
                    wave_offset = node['layer'] * 0.5
                    node['activation'] = (math.sin(t * 2 - wave_offset) + 1) / 2
                
                # Create display
                width = 70
                height = 25
                grid = [[' ' for _ in range(width)] for _ in range(height)]
                
                # Draw connections
                for conn in connections:
                    from_node = nodes[conn['from']]
                    to_node = nodes[conn['to']]
                    
                    # Simple line drawing
                    steps = 20
                    for i in range(steps):
                        x = int(from_node['x'] + (to_node['x'] - from_node['x']) * i / steps)
                        y = int(from_node['y'] + (to_node['y'] - from_node['y']) * i / steps)
                        
                        if 0 <= x < width and 0 <= y < height:
                            activation = (from_node['activation'] + to_node['activation']) / 2
                            if activation > 0.7:
                                grid[y][x] = '═'
                            elif activation > 0.3:
                                grid[y][x] = '─'
                            else:
                                grid[y][x] = '·'
                
                # Draw nodes
                for node in nodes:
                    x, y = int(node['x']), int(node['y'])
                    if 0 <= x < width and 0 <= y < height:
                        if node['activation'] > 0.7:
                            grid[y][x] = '◉'
                        elif node['activation'] > 0.3:
                            grid[y][x] = '○'
                        else:
                            grid[y][x] = '◦'
                
                # Convert to string
                lines = []
                for row in grid:
                    lines.append(''.join(row))
                
                display = '\n'.join(lines)
                live.update(Panel(
                    f"[bright_cyan]{display}[/bright_cyan]",
                    title="[bold bright_cyan]NEURAL NETWORK ACTIVATION[/bold bright_cyan]",
                    border_style="bright_cyan"
                ))
                
                time.sleep(0.05)
    
    @staticmethod
    def loading_bar_with_status(tasks: List[str], title: str = "Initializing NEXUS"):
        """Animated loading bar with status updates"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            
            main_task = progress.add_task(f"[cyan]{title}[/cyan]", total=len(tasks))
            
            for task_name in tasks:
                # Update description
                progress.update(main_task, description=f"[cyan]{task_name}[/cyan]")
                
                # Simulate work with sub-progress
                sub_task = progress.add_task(f"  └─ {task_name}", total=100)
                
                for i in range(100):
                    progress.update(sub_task, advance=1)
                    time.sleep(random.uniform(0.001, 0.01))
                
                progress.remove_task(sub_task)
                progress.update(main_task, advance=1)
                
                # Brief pause between tasks
                time.sleep(0.1)
    
    @staticmethod
    def glitch_text(text: str, duration: float = 1.0):
        """Glitch text effect"""
        glitch_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"
        
        start_time = time.time()
        original = text
        
        with Live(console=console, refresh_per_second=30) as live:
            while time.time() - start_time < duration:
                t = (time.time() - start_time) / duration
                
                # Calculate how many characters to reveal
                reveal_count = int(len(original) * t)
                
                # Create glitched text
                glitched = ""
                for i, char in enumerate(original):
                    if i < reveal_count:
                        glitched += char
                    elif char == ' ':
                        glitched += ' '
                    else:
                        glitched += random.choice(glitch_chars)
                
                # Add random glitches
                if random.random() < 0.1:
                    glitch_pos = random.randint(0, len(glitched) - 1)
                    glitched = glitched[:glitch_pos] + random.choice(glitch_chars) + glitched[glitch_pos + 1:]
                
                # Display
                live.update(Align.center(
                    Text(glitched, style="bold cyan"),
                    vertical="middle"
                ))
                
                time.sleep(0.03)
        
        # Final reveal
        console.print(Align.center(
            Text(original, style="bold cyan"),
            vertical="middle"
        ))


# Import math for animations
import math

# Demo all animations
def demo_animations():
    """Demo all loading animations"""
    animations = NEXUSAnimations()
    
    console.clear()
    
    # Matrix rain
    console.print("\n[bold green]Matrix Rain Animation[/bold green]\n")
    animations.matrix_rain(duration=2.0)
    
    time.sleep(0.5)
    console.clear()
    
    # Quantum particles
    console.print("\n[bold cyan]Quantum Particles Animation[/bold cyan]\n")
    animations.quantum_particles(duration=2.0)
    
    time.sleep(0.5)
    console.clear()
    
    # Neural network
    console.print("\n[bold bright_cyan]Neural Network Animation[/bold bright_cyan]\n")
    animations.neural_network(duration=2.0)
    
    time.sleep(0.5)
    console.clear()
    
    # Loading bar
    console.print("\n[bold]Progress Bar Animation[/bold]\n")
    tasks = [
        "Loading consciousness core...",
        "Initializing memory DNA...",
        "Connecting to integration hub...",
        "Starting MANUS agent...",
        "Activating voice control...",
        "Enabling vision processing..."
    ]
    animations.loading_bar_with_status(tasks)
    
    time.sleep(0.5)
    console.clear()
    
    # Glitch text
    console.print("\n" * 10)
    animations.glitch_text("NEXUS IS READY", duration=1.5)
    console.print("\n" * 10)


if __name__ == "__main__":
    demo_animations()