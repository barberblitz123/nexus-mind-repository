"""
NEXUS 2.0 Context Engine
Captures and manages complete project context with advanced features
"""

import json
import sqlite3
import pickle
import hashlib
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict
import networkx as nx
import numpy as np
from dataclasses import dataclass, asdict
import ast
import git
import lz4.frame
import importlib.util

@dataclass
class ProjectContext:
    """Complete context for a project"""
    project_id: str
    name: str
    path: str
    files: Dict[str, Dict[str, Any]]  # filename -> {content, hash, last_modified, dependencies}
    dependencies: Dict[str, List[str]]  # file -> [dependencies]
    conversations: List[Dict[str, Any]]  # conversation history
    last_accessed: datetime
    metadata: Dict[str, Any]
    relationships: List[str]  # related project IDs
    git_history: List[Dict[str, Any]]  # recent commits
    temporal_index: Dict[str, List[Dict[str, Any]]]  # timestamp -> events

class ContextEngine:
    """Advanced context management for NEXUS 2.0"""
    
    def __init__(self, storage_path: str = "nexus_context.db"):
        self.storage_path = storage_path
        self.current_context: Optional[ProjectContext] = None
        self.context_cache: Dict[str, ProjectContext] = {}
        self.relationship_graph = nx.DiGraph()
        self.auto_save_interval = 60  # seconds
        self.compression_threshold = 1024 * 1024  # 1MB
        
        self._init_storage()
        self._start_auto_save()
        
    def _init_storage(self):
        """Initialize SQLite storage"""
        self.conn = sqlite3.connect(self.storage_path, check_same_thread=False)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS contexts (
                project_id TEXT PRIMARY KEY,
                name TEXT,
                path TEXT,
                data BLOB,
                compressed INTEGER DEFAULT 0,
                last_accessed TIMESTAMP,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS relationships (
                source_id TEXT,
                target_id TEXT,
                relationship_type TEXT,
                strength REAL DEFAULT 1.0,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (source_id, target_id)
            )
        ''')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS temporal_index (
                project_id TEXT,
                timestamp TIMESTAMP,
                event_type TEXT,
                event_data TEXT,
                PRIMARY KEY (project_id, timestamp, event_type)
            )
        ''')
        self.conn.commit()
        
    def capture_project_context(self, project_path: str, name: str = None) -> ProjectContext:
        """Capture complete context for a project"""
        project_path = Path(project_path).resolve()
        project_id = hashlib.md5(str(project_path).encode()).hexdigest()
        
        if not name:
            name = project_path.name
            
        # Gather files and dependencies
        files = {}
        dependencies = defaultdict(list)
        
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and not self._should_ignore(file_path):
                rel_path = str(file_path.relative_to(project_path))
                
                try:
                    content = file_path.read_text(encoding='utf-8')
                    file_hash = hashlib.md5(content.encode()).hexdigest()
                    
                    # Extract dependencies for Python files
                    if file_path.suffix == '.py':
                        deps = self._extract_dependencies(content, file_path)
                        dependencies[rel_path] = deps
                        
                    files[rel_path] = {
                        'content': content,
                        'hash': file_hash,
                        'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime),
                        'size': file_path.stat().st_size,
                        'type': file_path.suffix
                    }
                except Exception as e:
                    # Handle binary files or encoding issues
                    files[rel_path] = {
                        'content': None,
                        'hash': None,
                        'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime),
                        'size': file_path.stat().st_size,
                        'type': file_path.suffix,
                        'error': str(e)
                    }
                    
        # Extract git history if available
        git_history = self._extract_git_history(project_path)
        
        # Create context
        context = ProjectContext(
            project_id=project_id,
            name=name,
            path=str(project_path),
            files=files,
            dependencies=dict(dependencies),
            conversations=[],
            last_accessed=datetime.now(),
            metadata={
                'total_files': len(files),
                'total_size': sum(f.get('size', 0) for f in files.values()),
                'languages': self._detect_languages(files),
                'framework': self._detect_framework(files, dependencies)
            },
            relationships=[],
            git_history=git_history,
            temporal_index=defaultdict(list)
        )
        
        # Cache and save
        self.context_cache[project_id] = context
        self._save_context(context)
        self._add_temporal_event(project_id, 'context_captured', {'files': len(files)})
        
        return context
        
    def switch_context(self, project_id: str) -> Optional[ProjectContext]:
        """Switch to a different project context"""
        # Check cache first
        if project_id in self.context_cache:
            self.current_context = self.context_cache[project_id]
            self.current_context.last_accessed = datetime.now()
            self._add_temporal_event(project_id, 'context_switched', {})
            return self.current_context
            
        # Load from storage
        context = self._load_context(project_id)
        if context:
            self.current_context = context
            self.context_cache[project_id] = context
            self._add_temporal_event(project_id, 'context_loaded', {})
            return context
            
        return None
        
    def add_conversation(self, message: str, response: str, metadata: Dict[str, Any] = None):
        """Add conversation to current context"""
        if not self.current_context:
            return
            
        conversation = {
            'timestamp': datetime.now(),
            'message': message,
            'response': response,
            'metadata': metadata or {}
        }
        
        self.current_context.conversations.append(conversation)
        self._add_temporal_event(
            self.current_context.project_id,
            'conversation',
            {'message_preview': message[:100]}
        )
        
    def map_relationships(self, source_id: str, target_id: str, 
                         relationship_type: str = 'related', strength: float = 1.0):
        """Map relationships between projects"""
        self.relationship_graph.add_edge(
            source_id, target_id,
            type=relationship_type,
            strength=strength
        )
        
        # Update in database
        self.conn.execute('''
            INSERT OR REPLACE INTO relationships (source_id, target_id, relationship_type, strength)
            VALUES (?, ?, ?, ?)
        ''', (source_id, target_id, relationship_type, strength))
        self.conn.commit()
        
        # Update context objects
        if source_id in self.context_cache:
            if target_id not in self.context_cache[source_id].relationships:
                self.context_cache[source_id].relationships.append(target_id)
                
    def get_related_contexts(self, project_id: str, max_depth: int = 2) -> List[str]:
        """Get related project contexts"""
        if project_id not in self.relationship_graph:
            return []
            
        related = set()
        
        # BFS to find related projects
        queue = [(project_id, 0)]
        visited = set()
        
        while queue:
            current_id, depth = queue.pop(0)
            if current_id in visited or depth > max_depth:
                continue
                
            visited.add(current_id)
            if current_id != project_id:
                related.add(current_id)
                
            # Add neighbors
            for neighbor in self.relationship_graph.neighbors(current_id):
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1))
                    
        return list(related)
        
    def search_temporal(self, start_time: datetime, end_time: datetime, 
                       event_types: List[str] = None) -> List[Dict[str, Any]]:
        """Search events by time range"""
        query = '''
            SELECT project_id, timestamp, event_type, event_data
            FROM temporal_index
            WHERE timestamp BETWEEN ? AND ?
        '''
        params = [start_time, end_time]
        
        if event_types:
            placeholders = ','.join('?' * len(event_types))
            query += f' AND event_type IN ({placeholders})'
            params.extend(event_types)
            
        query += ' ORDER BY timestamp DESC'
        
        cursor = self.conn.execute(query, params)
        events = []
        
        for row in cursor:
            events.append({
                'project_id': row[0],
                'timestamp': datetime.fromisoformat(row[1]),
                'event_type': row[2],
                'event_data': json.loads(row[3])
            })
            
        return events
        
    def compress_context(self, context: ProjectContext) -> bytes:
        """Compress context for storage efficiency"""
        # Remove large content for compression
        compressed_files = {}
        for path, file_info in context.files.items():
            compressed_info = file_info.copy()
            if compressed_info.get('content') and len(compressed_info['content']) > 1000:
                # Store only hash for large files
                compressed_info['content_compressed'] = True
                compressed_info['content'] = None
            compressed_files[path] = compressed_info
            
        # Create compressed version
        compressed_context = ProjectContext(
            project_id=context.project_id,
            name=context.name,
            path=context.path,
            files=compressed_files,
            dependencies=context.dependencies,
            conversations=context.conversations[-100:],  # Keep last 100 conversations
            last_accessed=context.last_accessed,
            metadata=context.metadata,
            relationships=context.relationships,
            git_history=context.git_history[-50:],  # Keep last 50 commits
            temporal_index=dict(context.temporal_index)
        )
        
        # Serialize and compress
        serialized = pickle.dumps(asdict(compressed_context))
        compressed = lz4.frame.compress(serialized)
        
        return compressed
        
    def _extract_dependencies(self, content: str, file_path: Path) -> List[str]:
        """Extract dependencies from Python code"""
        dependencies = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.append(node.module)
                        
        except Exception:
            # Fallback to regex for invalid Python
            import re
            import_pattern = r'(?:from\s+(\S+)\s+)?import\s+(\S+)'
            for match in re.finditer(import_pattern, content):
                if match.group(1):
                    dependencies.append(match.group(1))
                if match.group(2):
                    dependencies.append(match.group(2))
                    
        return list(set(dependencies))
        
    def _extract_git_history(self, project_path: Path) -> List[Dict[str, Any]]:
        """Extract git history if available"""
        try:
            repo = git.Repo(project_path)
            commits = []
            
            for commit in repo.iter_commits(max_count=100):
                commits.append({
                    'hash': commit.hexsha,
                    'message': commit.message.strip(),
                    'author': str(commit.author),
                    'timestamp': datetime.fromtimestamp(commit.committed_date),
                    'files_changed': len(commit.stats.files)
                })
                
            return commits
        except Exception:
            return []
            
    def _detect_languages(self, files: Dict[str, Dict[str, Any]]) -> List[str]:
        """Detect programming languages used"""
        language_extensions = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.php': 'PHP',
            '.r': 'R',
            '.scala': 'Scala',
            '.m': 'Objective-C'
        }
        
        languages = set()
        for file_info in files.values():
            ext = file_info.get('type', '')
            if ext in language_extensions:
                languages.add(language_extensions[ext])
                
        return sorted(list(languages))
        
    def _detect_framework(self, files: Dict[str, Dict[str, Any]], 
                         dependencies: Dict[str, List[str]]) -> Optional[str]:
        """Detect framework or library used"""
        # Check for framework indicators
        if 'package.json' in files:
            content = files['package.json'].get('content', '')
            if 'react' in content:
                return 'React'
            elif 'vue' in content:
                return 'Vue'
            elif 'angular' in content:
                return 'Angular'
                
        if 'requirements.txt' in files or 'setup.py' in files:
            all_deps = set()
            for deps in dependencies.values():
                all_deps.update(deps)
                
            if 'django' in all_deps:
                return 'Django'
            elif 'flask' in all_deps:
                return 'Flask'
            elif 'fastapi' in all_deps:
                return 'FastAPI'
            elif 'tensorflow' in all_deps or 'torch' in all_deps:
                return 'ML/AI'
                
        return None
        
    def _should_ignore(self, path: Path) -> bool:
        """Check if file should be ignored"""
        ignore_patterns = [
            '__pycache__', '.git', 'node_modules', '.env',
            'venv', '.venv', 'env', '.idea', '.vscode',
            '*.pyc', '*.pyo', '*.pyd', '.DS_Store', '*.log'
        ]
        
        path_str = str(path)
        for pattern in ignore_patterns:
            if pattern in path_str:
                return True
                
        return False
        
    def _save_context(self, context: ProjectContext):
        """Save context to storage"""
        data = pickle.dumps(asdict(context))
        compressed = 0
        
        # Compress if large
        if len(data) > self.compression_threshold:
            data = self.compress_context(context)
            compressed = 1
            
        self.conn.execute('''
            INSERT OR REPLACE INTO contexts 
            (project_id, name, path, data, compressed, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (context.project_id, context.name, context.path, 
              data, compressed, context.last_accessed))
        self.conn.commit()
        
    def _load_context(self, project_id: str) -> Optional[ProjectContext]:
        """Load context from storage"""
        cursor = self.conn.execute(
            'SELECT data, compressed FROM contexts WHERE project_id = ?',
            (project_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            return None
            
        data, compressed = row
        
        if compressed:
            data = lz4.frame.decompress(data)
            
        context_dict = pickle.loads(data)
        return ProjectContext(**context_dict)
        
    def _add_temporal_event(self, project_id: str, event_type: str, event_data: Dict[str, Any]):
        """Add event to temporal index"""
        timestamp = datetime.now()
        
        self.conn.execute('''
            INSERT INTO temporal_index (project_id, timestamp, event_type, event_data)
            VALUES (?, ?, ?, ?)
        ''', (project_id, timestamp, event_type, json.dumps(event_data)))
        self.conn.commit()
        
        # Update in-memory index if context is loaded
        if project_id in self.context_cache:
            self.context_cache[project_id].temporal_index[str(timestamp)].append({
                'type': event_type,
                'data': event_data
            })
            
    def _start_auto_save(self):
        """Start auto-save thread"""
        def auto_save():
            while True:
                time.sleep(self.auto_save_interval)
                
                # Save all cached contexts
                for context in self.context_cache.values():
                    self._save_context(context)
                    
        thread = threading.Thread(target=auto_save, daemon=True)
        thread.start()
        
    def restore_session(self, project_id: str) -> Optional[ProjectContext]:
        """Restore a previous session"""
        context = self.switch_context(project_id)
        if context:
            self._add_temporal_event(project_id, 'session_restored', {
                'conversations': len(context.conversations)
            })
        return context
        
    def get_context_summary(self, project_id: str = None) -> Dict[str, Any]:
        """Get summary of context"""
        if project_id:
            context = self.context_cache.get(project_id) or self._load_context(project_id)
        else:
            context = self.current_context
            
        if not context:
            return {}
            
        return {
            'project_id': context.project_id,
            'name': context.name,
            'path': context.path,
            'total_files': len(context.files),
            'total_conversations': len(context.conversations),
            'languages': context.metadata.get('languages', []),
            'framework': context.metadata.get('framework'),
            'last_accessed': context.last_accessed.isoformat(),
            'relationships': len(context.relationships),
            'recent_commits': len(context.git_history)
        }