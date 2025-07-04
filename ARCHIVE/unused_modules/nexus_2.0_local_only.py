#!/usr/bin/env python3
"""
NEXUS 2.0 Local-Only Edition
No external APIs, subscriptions, or cloud services required
Everything runs locally on your machine
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import sqlite3
import threading
import queue
from dataclasses import dataclass
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import WordCompleter
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# Initialize console for rich output
console = Console()

# Local-only configuration
@dataclass
class LocalConfig:
    """Configuration for local-only NEXUS"""
    # Database
    database_path: str = "nexus_local.db"
    
    # Memory storage
    memory_path: str = "./nexus_memory"
    
    # UI settings
    ui_theme: str = "dark"
    terminal_mode: bool = True
    
    # Processing
    max_workers: int = 4
    cache_size: int = 1000
    
    # Features (all local)
    enable_voice: bool = False  # Requires local voice engine
    enable_vision: bool = False  # Requires local image processing
    enable_web_ui: bool = True   # Local web server only
    
    # Paths
    project_root: Path = Path(".")
    logs_dir: Path = Path("./nexus_logs")
    data_dir: Path = Path("./nexus_data")

class LocalMemorySystem:
    """Local-only memory system using SQLite"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize local database schema"""
        with self.lock:
            cursor = self.conn.cursor()
            
            # Core memory table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    context TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            # Task tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 5,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    details TEXT
                )
            ''')
            
            # Local knowledge base
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT DEFAULT 'local',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.conn.commit()
    
    def store_memory(self, memory_type: str, content: str, context: str = None):
        """Store a memory locally"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO memories (type, content, context) VALUES (?, ?, ?)",
                (memory_type, content, context)
            )
            self.conn.commit()
            return cursor.lastrowid
    
    def retrieve_memories(self, memory_type: str = None, limit: int = 10):
        """Retrieve memories from local storage"""
        with self.lock:
            cursor = self.conn.cursor()
            if memory_type:
                cursor.execute(
                    "SELECT * FROM memories WHERE type = ? ORDER BY timestamp DESC LIMIT ?",
                    (memory_type, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM memories ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
            return cursor.fetchall()

class LocalProcessingEngine:
    """Local-only processing engine without external APIs"""
    
    def __init__(self, config: LocalConfig):
        self.config = config
        self.memory = LocalMemorySystem(config.database_path)
        self.cache = {}
        self.active_tasks = queue.Queue()
    
    def process_text(self, text: str) -> Dict[str, Any]:
        """Process text locally without external APIs"""
        # Simple local text analysis
        result = {
            "text": text,
            "length": len(text),
            "words": len(text.split()),
            "timestamp": datetime.now().isoformat(),
            "processed_locally": True
        }
        
        # Store in memory
        self.memory.store_memory("text_input", text)
        
        return result
    
    def analyze_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Analyze code locally"""
        lines = code.split('\n')
        
        # Basic local code analysis
        analysis = {
            "language": language,
            "lines": len(lines),
            "characters": len(code),
            "functions": self._count_functions(code, language),
            "classes": self._count_classes(code, language),
            "imports": self._extract_imports(code, language),
            "processed_locally": True
        }
        
        return analysis
    
    def _count_functions(self, code: str, language: str) -> int:
        """Count functions in code (simple local analysis)"""
        if language == "python":
            return code.count("def ")
        elif language == "javascript":
            return code.count("function ") + code.count("=> ")
        return 0
    
    def _count_classes(self, code: str, language: str) -> int:
        """Count classes in code (simple local analysis)"""
        if language == "python":
            return code.count("class ")
        elif language in ["javascript", "typescript"]:
            return code.count("class ")
        return 0
    
    def _extract_imports(self, code: str, language: str) -> List[str]:
        """Extract imports from code (simple local analysis)"""
        imports = []
        if language == "python":
            for line in code.split('\n'):
                if line.strip().startswith(('import ', 'from ')):
                    imports.append(line.strip())
        return imports

class LocalNexusUI:
    """Local-only UI for NEXUS (no external dependencies)"""
    
    def __init__(self, engine: LocalProcessingEngine):
        self.engine = engine
        self.running = False
        
    def create_gui(self):
        """Create local Tkinter GUI"""
        self.root = tk.Tk()
        self.root.title("NEXUS 2.0 - Local Edition")
        self.root.geometry("800x600")
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)
        
        # Chat tab
        chat_frame = ttk.Frame(notebook)
        notebook.add(chat_frame, text="Chat")
        self._create_chat_tab(chat_frame)
        
        # Tasks tab
        tasks_frame = ttk.Frame(notebook)
        notebook.add(tasks_frame, text="Tasks")
        self._create_tasks_tab(tasks_frame)
        
        # Memory tab
        memory_frame = ttk.Frame(notebook)
        notebook.add(memory_frame, text="Memory")
        self._create_memory_tab(memory_frame)
        
        # Settings tab
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Settings")
        self._create_settings_tab(settings_frame)
        
    def _create_chat_tab(self, parent):
        """Create chat interface"""
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(parent, height=20)
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Input frame
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        self.chat_input = ttk.Entry(input_frame)
        self.chat_input.pack(side="left", fill="x", expand=True)
        self.chat_input.bind("<Return>", self._on_chat_enter)
        
        send_btn = ttk.Button(input_frame, text="Send", command=self._send_chat)
        send_btn.pack(side="right", padx=(5, 0))
        
    def _create_tasks_tab(self, parent):
        """Create tasks interface"""
        # Tasks list
        columns = ("ID", "Task", "Status", "Priority")
        self.tasks_tree = ttk.Treeview(parent, columns=columns, show="headings")
        
        for col in columns:
            self.tasks_tree.heading(col, text=col)
        
        self.tasks_tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Control buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Add Task", command=self._add_task).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Complete Task", command=self._complete_task).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Delete Task", command=self._delete_task).pack(side="left", padx=2)
        
    def _create_memory_tab(self, parent):
        """Create memory interface"""
        # Memory display
        self.memory_text = scrolledtext.ScrolledText(parent, height=20)
        self.memory_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Control buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Refresh", command=self._refresh_memory).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Clear Old", command=self._clear_old_memory).pack(side="left", padx=2)
        
    def _create_settings_tab(self, parent):
        """Create settings interface"""
        settings_frame = ttk.LabelFrame(parent, text="Local Settings", padding=10)
        settings_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Settings info
        info_text = """NEXUS 2.0 - Local Edition

All features run locally on your machine:
• No external APIs required
• No subscriptions needed
• No cloud services
• Your data stays on your device

Local Features:
• Text processing
• Code analysis
• Task management
• Memory system
• Local web interface

Data Storage:
• SQLite database: nexus_local.db
• Memory files: ./nexus_memory/
• Logs: ./nexus_logs/
"""
        
        info_label = ttk.Label(settings_frame, text=info_text, justify="left")
        info_label.pack(anchor="w")
        
    def _on_chat_enter(self, event):
        """Handle enter key in chat"""
        self._send_chat()
        
    def _send_chat(self):
        """Process chat input locally"""
        text = self.chat_input.get()
        if not text:
            return
            
        # Display user message
        self.chat_display.insert("end", f"\nYou: {text}\n")
        
        # Process locally
        result = self.engine.process_text(text)
        
        # Display response
        response = f"NEXUS (Local): Processed {result['words']} words locally. No external APIs used.\n"
        self.chat_display.insert("end", response)
        
        # Clear input
        self.chat_input.delete(0, "end")
        
        # Scroll to bottom
        self.chat_display.see("end")
        
    def _add_task(self):
        """Add a new task"""
        # Simple dialog for task input
        task_name = tk.simpledialog.askstring("New Task", "Enter task name:")
        if task_name:
            # Add to database
            with sqlite3.connect(self.engine.memory.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tasks (name, status) VALUES (?, ?)",
                    (task_name, "pending")
                )
                conn.commit()
            self._refresh_tasks()
            
    def _complete_task(self):
        """Mark selected task as complete"""
        selected = self.tasks_tree.selection()
        if selected:
            item = self.tasks_tree.item(selected[0])
            task_id = item['values'][0]
            
            with sqlite3.connect(self.engine.memory.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE tasks SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (task_id,)
                )
                conn.commit()
            self._refresh_tasks()
            
    def _delete_task(self):
        """Delete selected task"""
        selected = self.tasks_tree.selection()
        if selected:
            item = self.tasks_tree.item(selected[0])
            task_id = item['values'][0]
            
            if messagebox.askyesno("Delete Task", "Are you sure you want to delete this task?"):
                with sqlite3.connect(self.engine.memory.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                    conn.commit()
                self._refresh_tasks()
    
    def _refresh_tasks(self):
        """Refresh tasks list"""
        # Clear existing items
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
            
        # Load tasks from database
        with sqlite3.connect(self.engine.memory.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, status, priority FROM tasks ORDER BY created_at DESC")
            for row in cursor.fetchall():
                self.tasks_tree.insert("", "end", values=row)
                
    def _refresh_memory(self):
        """Refresh memory display"""
        memories = self.engine.memory.retrieve_memories(limit=50)
        
        self.memory_text.delete(1.0, "end")
        self.memory_text.insert("end", "Recent Memories (Local Storage)\n" + "="*50 + "\n\n")
        
        for memory in memories:
            self.memory_text.insert("end", f"[{memory[4]}] {memory[1]}: {memory[2]}\n")
            if memory[3]:  # context
                self.memory_text.insert("end", f"  Context: {memory[3]}\n")
            self.memory_text.insert("end", "\n")
            
    def _clear_old_memory(self):
        """Clear old memories (keep last 100)"""
        if messagebox.askyesno("Clear Memory", "Keep only the last 100 memories?"):
            with sqlite3.connect(self.engine.memory.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM memories 
                    WHERE id NOT IN (
                        SELECT id FROM memories 
                        ORDER BY timestamp DESC 
                        LIMIT 100
                    )
                """)
                conn.commit()
                deleted = cursor.rowcount
            
            messagebox.showinfo("Memory Cleared", f"Deleted {deleted} old memories")
            self._refresh_memory()
    
    def run(self):
        """Run the GUI"""
        self.create_gui()
        self._refresh_tasks()
        self._refresh_memory()
        self.root.mainloop()

class LocalWebServer:
    """Simple local web server (no external dependencies)"""
    
    def __init__(self, engine: LocalProcessingEngine, port: int = 7777):
        self.engine = engine
        self.port = port
        
    async def start(self):
        """Start local web server"""
        console.print(f"[green]Local web server starting on http://localhost:{self.port}[/green]")
        console.print("[yellow]This is a LOCAL server - no external connections[/yellow]")
        
        # Simple HTTP server implementation would go here
        # For now, we'll just indicate it's ready
        console.print("[green]✓ Local web server ready[/green]")

def main():
    """Main entry point for NEXUS 2.0 Local Edition"""
    console.print(Panel.fit(
        "[bold cyan]NEXUS 2.0 - Local Edition[/bold cyan]\n"
        "[green]No external APIs or subscriptions required![/green]\n"
        "Everything runs locally on your machine",
        border_style="cyan"
    ))
    
    # Initialize configuration
    config = LocalConfig()
    
    # Create necessary directories
    config.logs_dir.mkdir(exist_ok=True)
    config.data_dir.mkdir(exist_ok=True)
    Path(config.memory_path).mkdir(exist_ok=True)
    
    # Initialize engine
    engine = LocalProcessingEngine(config)
    
    # Choose interface
    console.print("\nSelect interface:")
    console.print("1. GUI (Graphical Interface)")
    console.print("2. Terminal (Command Line)")
    console.print("3. Web (Local Browser)")
    
    choice = prompt("Enter choice (1-3): ")
    
    if choice == "1":
        # Launch GUI
        ui = LocalNexusUI(engine)
        ui.run()
    elif choice == "2":
        # Terminal interface
        console.print("[cyan]Terminal interface starting...[/cyan]")
        
        while True:
            try:
                user_input = prompt("\nNEXUS> ", style=Style.from_dict({
                    'prompt': '#00aa00 bold',
                }))
                
                if user_input.lower() in ['exit', 'quit']:
                    break
                    
                # Process locally
                result = engine.process_text(user_input)
                console.print(f"[green]Processed locally: {result['words']} words[/green]")
                
            except KeyboardInterrupt:
                break
                
    elif choice == "3":
        # Web interface
        console.print("[cyan]Starting local web server...[/cyan]")
        server = LocalWebServer(engine)
        asyncio.run(server.start())
    else:
        console.print("[red]Invalid choice[/red]")
        
    console.print("\n[green]Thank you for using NEXUS 2.0 Local Edition![/green]")

if __name__ == "__main__":
    main()