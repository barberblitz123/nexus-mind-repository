#!/usr/bin/env python3
"""
NEXUS UI Project Tab Component
Provides project overview with file tree, statistics, goals, and visual mapping
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path


class ProjectTab:
    """Project overview tab for NEXUS terminal UI"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.file_tree_cache = {}
        self.project_stats = {}
        self.goals = []
        self.issues = []
        
    def render(self, width: int = 80, height: int = 24) -> List[str]:
        """Render the project tab view"""
        lines = []
        
        # Header
        lines.append("╔" + "═" * (width - 2) + "╗")
        lines.append("║" + " PROJECT OVERVIEW ".center(width - 2) + "║")
        lines.append("╠" + "═" * (width - 2) + "╣")
        
        # Layout: Left side (file tree), Right side (stats/goals)
        content_height = height - 4
        left_width = int(width * 0.5)
        right_width = width - left_width - 3
        
        # Generate content
        file_tree = self._render_file_tree(left_width - 2, content_height)
        right_panel = self._render_right_panel(right_width - 2, content_height)
        
        # Merge panels
        for i in range(content_height):
            left = file_tree[i] if i < len(file_tree) else " " * (left_width - 2)
            right = right_panel[i] if i < len(right_panel) else " " * (right_width - 2)
            lines.append(f"║ {left} │ {right} ║")
        
        # Footer
        lines.append("╚" + "═" * (width - 2) + "╝")
        
        return lines
    
    def _render_file_tree(self, width: int, height: int) -> List[str]:
        """Render file tree view"""
        lines = []
        lines.append("📁 File Explorer".ljust(width))
        lines.append("─" * width)
        
        # Build tree structure
        tree_lines = self._build_tree_lines(self.project_root, "", width - 4)
        
        # Fit to available height
        available = height - 2
        if len(tree_lines) > available:
            tree_lines = tree_lines[:available-1] + ["  ..."]
        
        lines.extend(tree_lines)
        return lines
    
    def _build_tree_lines(self, path: Path, prefix: str, max_width: int) -> List[str]:
        """Build file tree lines recursively"""
        lines = []
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            
            for i, item in enumerate(items[:20]):  # Limit items
                is_last = i == len(items) - 1
                
                # Skip hidden and cache directories
                if item.name.startswith('.') or item.name in ['__pycache__', 'node_modules']:
                    continue
                
                # Build line
                connector = "└── " if is_last else "├── "
                icon = "📁" if item.is_dir() else self._get_file_icon(item.name)
                line = f"{prefix}{connector}{icon} {item.name}"
                
                if len(line) > max_width:
                    line = line[:max_width-3] + "..."
                
                lines.append(line)
                
                # Recurse for directories
                if item.is_dir() and len(lines) < 50:
                    extension = "    " if is_last else "│   "
                    lines.extend(self._build_tree_lines(
                        item, prefix + extension, max_width
                    ))
                    
        except PermissionError:
            lines.append(f"{prefix}[Permission Denied]")
            
        return lines
    
    def _get_file_icon(self, filename: str) -> str:
        """Get icon for file type"""
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        
        icons = {
            'py': '🐍', 'js': '📜', 'ts': '📘', 'jsx': '⚛️', 'tsx': '⚛️',
            'html': '🌐', 'css': '🎨', 'json': '📋', 'md': '📝',
            'txt': '📄', 'yaml': '⚙️', 'yml': '⚙️', 'sh': '🔧',
            'sql': '🗃️', 'db': '🗄️', 'png': '🖼️', 'jpg': '🖼️',
            'gif': '🖼️', 'svg': '🎨', 'mp3': '🎵', 'mp4': '🎬'
        }
        
        return icons.get(ext, '📄')
    
    def _render_right_panel(self, width: int, height: int) -> List[str]:
        """Render right panel with stats, goals, and issues"""
        lines = []
        
        # Project Statistics
        lines.append("📊 Project Statistics".ljust(width))
        lines.append("─" * width)
        
        stats = self._calculate_stats()
        lines.append(f"Files: {stats['total_files']:,}")
        lines.append(f"Lines: {stats['total_lines']:,}")
        lines.append(f"Size: {self._format_size(stats['total_size'])}")
        lines.append("")
        
        # Active Goals
        lines.append("🎯 Active Goals".ljust(width))
        lines.append("─" * width)
        
        if self.goals:
            for goal in self.goals[:3]:
                status = "✅" if goal.get('completed') else "⏳"
                lines.append(f"{status} {goal['title'][:width-3]}")
        else:
            lines.append("No active goals")
        lines.append("")
        
        # Recent Issues
        lines.append("⚠️  Recent Issues".ljust(width))
        lines.append("─" * width)
        
        if self.issues:
            for issue in self.issues[:3]:
                severity = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(
                    issue.get('severity', 'info'), "⚪"
                )
                lines.append(f"{severity} {issue['message'][:width-3]}")
        else:
            lines.append("No issues detected")
        
        # Visual Map
        remaining = height - len(lines) - 2
        if remaining > 5:
            lines.append("")
            lines.append("🗺️  Project Map".ljust(width))
            lines.append("─" * width)
            lines.extend(self._render_project_map(width, remaining - 3))
        
        return lines
    
    def _calculate_stats(self) -> Dict[str, int]:
        """Calculate project statistics"""
        stats = {
            'total_files': 0,
            'total_lines': 0,
            'total_size': 0
        }
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip hidden and cache directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                if not file.startswith('.'):
                    stats['total_files'] += 1
                    filepath = os.path.join(root, file)
                    
                    try:
                        stats['total_size'] += os.path.getsize(filepath)
                        
                        # Count lines for text files
                        if file.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.md')):
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                stats['total_lines'] += sum(1 for _ in f)
                    except:
                        pass
        
        return stats
    
    def _format_size(self, size: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def _render_project_map(self, width: int, height: int) -> List[str]:
        """Render ASCII art project structure map"""
        lines = []
        
        # Simple module map
        map_data = [
            "┌─────────┐     ┌─────────┐",
            "│  Core   │────▶│   API   │",
            "└────┬────┘     └────┬────┘",
            "     │               │     ",
            "     ▼               ▼     ",
            "┌─────────┐     ┌─────────┐",
            "│   UI    │◀────│  Data   │",
            "└─────────┘     └─────────┘"
        ]
        
        # Center the map
        for line in map_data[:height]:
            lines.append(line.center(width))
        
        return lines
    
    def update_goals(self, goals: List[Dict[str, Any]]):
        """Update project goals"""
        self.goals = goals
    
    def update_issues(self, issues: List[Dict[str, Any]]):
        """Update project issues"""
        self.issues = issues
    
    def add_goal(self, title: str, description: str = ""):
        """Add a new goal"""
        self.goals.append({
            'id': len(self.goals) + 1,
            'title': title,
            'description': description,
            'completed': False,
            'created_at': datetime.now().isoformat()
        })
    
    def complete_goal(self, goal_id: int):
        """Mark a goal as completed"""
        for goal in self.goals:
            if goal['id'] == goal_id:
                goal['completed'] = True
                goal['completed_at'] = datetime.now().isoformat()
                break
    
    def add_issue(self, message: str, severity: str = "info", file: str = ""):
        """Add a new issue"""
        self.issues.append({
            'id': len(self.issues) + 1,
            'message': message,
            'severity': severity,
            'file': file,
            'timestamp': datetime.now().isoformat()
        })
    
    def clear_issues(self):
        """Clear all issues"""
        self.issues = []
    
    def refresh(self):
        """Refresh project data"""
        self.file_tree_cache.clear()
        self.project_stats = self._calculate_stats()


if __name__ == "__main__":
    # Demo the project tab
    tab = ProjectTab()
    
    # Add sample data
    tab.add_goal("Implement authentication system")
    tab.add_goal("Add unit tests for core modules")
    tab.add_goal("Optimize database queries")
    tab.complete_goal(2)
    
    tab.add_issue("Unused import in main.py", "warning", "main.py")
    tab.add_issue("Missing error handling in API", "error", "api/handlers.py")
    
    # Render
    for line in tab.render(100, 40):
        print(line)