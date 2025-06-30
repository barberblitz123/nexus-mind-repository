#!/usr/bin/env python3
"""
🧬 NEXUS Functional Core - Real Capabilities Without Theater
Focused on actual working features, not simulations
"""

import os
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import sqlite3
import re

@dataclass
class MemoryEntry:
    """Real memory storage structure"""
    id: str
    content: str
    timestamp: float
    session_id: str
    context: Dict[str, Any]
    tags: List[str] = field(default_factory=list)

@dataclass
class ConversationContext:
    """Real conversation tracking"""
    session_id: str
    start_time: float
    messages: List[Dict[str, str]]
    extracted_entities: List[str]
    topic_flow: List[str]

class NEXUSFunctionalCore:
    """
    NEXUS core focused on real, working capabilities
    No consciousness theater - just actual functionality
    """
    
    def __init__(self, data_dir: str = "./nexus_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Real memory system
        self.memory_db = self._init_memory_database()
        
        # Session management
        self.current_session = None
        self.session_history = []
        
        # Chat history access (if available)
        self.chat_history_dirs = self._find_chat_history_dirs()
        
        # Personality framework (kept from original)
        self.personality = {
            'name': 'NEXUS',
            'traits': {
                'analytical': 'Logical and systematic approach',
                'creative': 'Novel solutions and synthesis',
                'intuitive': 'Pattern recognition focus',
                'adaptive': 'Learns from interactions'
            },
            'style': 'Direct, helpful, technically competent'
        }
        
        print(f"🧬 NEXUS Functional Core initialized")
        print(f"📁 Data directory: {self.data_dir}")
        print(f"💾 Memory database: {self.memory_db}")
        print(f"📚 Found {len(self.chat_history_dirs)} chat history locations")
    
    def _init_memory_database(self) -> str:
        """Initialize SQLite database for persistent memory"""
        db_path = self.data_dir / "nexus_memory.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create memory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                session_id TEXT,
                context TEXT,
                tags TEXT,
                access_count INTEGER DEFAULT 1,
                last_accessed REAL
            )
        """)
        
        # Create index for faster searches
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session ON memories(session_id)
        """)
        
        conn.commit()
        conn.close()
        
        return str(db_path)
    
    def _find_chat_history_dirs(self) -> List[Path]:
        """Find Claude chat history directories"""
        possible_locations = [
            Path.home() / ".config" / "Claude" / "chats",
            Path.home() / "Library" / "Application Support" / "Claude" / "chats",
            Path.home() / "AppData" / "Roaming" / "Claude" / "chats",
            Path.home() / ".claude" / "chats",
            Path("./claude_chats"),  # Local export directory
        ]
        
        found_dirs = []
        for location in possible_locations:
            if location.exists() and location.is_dir():
                found_dirs.append(location)
        
        return found_dirs
    
    def store_memory(self, content: str, context: Dict[str, Any] = None, tags: List[str] = None) -> str:
        """Store a memory in persistent database"""
        memory_id = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect(self.memory_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO memories (id, content, timestamp, session_id, context, tags)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            memory_id,
            content,
            time.time(),
            self.current_session or "default",
            json.dumps(context or {}),
            json.dumps(tags or [])
        ))
        
        conn.commit()
        conn.close()
        
        return memory_id
    
    def retrieve_memories(self, query: str = None, limit: int = 10, session_id: str = None) -> List[MemoryEntry]:
        """Retrieve memories from database"""
        conn = sqlite3.connect(self.memory_db)
        cursor = conn.cursor()
        
        if query:
            # Search by content
            cursor.execute("""
                SELECT * FROM memories 
                WHERE content LIKE ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (f"%{query}%", limit))
        elif session_id:
            # Get memories from specific session
            cursor.execute("""
                SELECT * FROM memories 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (session_id, limit))
        else:
            # Get recent memories
            cursor.execute("""
                SELECT * FROM memories 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
        
        memories = []
        for row in cursor.fetchall():
            memory = MemoryEntry(
                id=row[0],
                content=row[1],
                timestamp=row[2],
                session_id=row[3],
                context=json.loads(row[4]) if row[4] else {},
                tags=json.loads(row[5]) if row[5] else []
            )
            memories.append(memory)
        
        conn.close()
        return memories
    
    def search_chat_history(self, query: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """Search through Claude chat history files"""
        results = []
        cutoff_time = time.time() - (days_back * 24 * 3600)
        
        for chat_dir in self.chat_history_dirs:
            for chat_file in chat_dir.glob("*.json"):
                try:
                    # Check file modification time
                    if chat_file.stat().st_mtime < cutoff_time:
                        continue
                    
                    with open(chat_file, 'r', encoding='utf-8') as f:
                        chat_data = json.load(f)
                    
                    # Search in messages
                    for message in chat_data.get('messages', []):
                        content = message.get('content', '')
                        if query.lower() in content.lower():
                            results.append({
                                'file': str(chat_file),
                                'timestamp': message.get('timestamp', 0),
                                'role': message.get('role', 'unknown'),
                                'content': content[:200] + '...' if len(content) > 200 else content,
                                'match_context': self._extract_context(content, query)
                            })
                
                except Exception as e:
                    # Skip files that can't be read
                    continue
        
        return sorted(results, key=lambda x: x['timestamp'], reverse=True)
    
    def _extract_context(self, content: str, query: str, context_size: int = 100) -> str:
        """Extract context around a search match"""
        query_lower = query.lower()
        content_lower = content.lower()
        
        pos = content_lower.find(query_lower)
        if pos == -1:
            return ""
        
        start = max(0, pos - context_size)
        end = min(len(content), pos + len(query) + context_size)
        
        context = content[start:end]
        if start > 0:
            context = "..." + context
        if end < len(content):
            context = context + "..."
        
        return context
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract important entities from text"""
        # Simple entity extraction
        entities = []
        
        # Extract URLs
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
        entities.extend(re.findall(url_pattern, text))
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities.extend(re.findall(email_pattern, text))
        
        # Extract capitalized phrases (potential names/places)
        cap_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        potential_names = re.findall(cap_pattern, text)
        entities.extend([name for name in potential_names if len(name.split()) <= 3])
        
        # Extract quoted strings
        quote_pattern = r'"([^"]+)"'
        entities.extend(re.findall(quote_pattern, text))
        
        return list(set(entities))  # Remove duplicates
    
    def bridge_sessions(self, previous_session_id: str) -> Dict[str, Any]:
        """Bridge context from a previous session"""
        # Retrieve memories from previous session
        previous_memories = self.retrieve_memories(session_id=previous_session_id, limit=20)
        
        # Extract key information
        bridged_context = {
            'previous_session': previous_session_id,
            'memory_count': len(previous_memories),
            'key_topics': [],
            'entities': [],
            'last_interaction': None
        }
        
        if previous_memories:
            # Get topics and entities
            all_entities = []
            for memory in previous_memories:
                entities = self.extract_entities(memory.content)
                all_entities.extend(entities)
            
            bridged_context['entities'] = list(set(all_entities))[:10]  # Top 10 unique
            bridged_context['last_interaction'] = previous_memories[0].timestamp
            
            # Simple topic extraction (most common meaningful words)
            words = []
            for memory in previous_memories:
                words.extend(self._extract_keywords(memory.content))
            
            from collections import Counter
            word_counts = Counter(words)
            bridged_context['key_topics'] = [word for word, _ in word_counts.most_common(5)]
        
        return bridged_context
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'been', 'be',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'to',
            'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'this', 'that'
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        
        return keywords
    
    def start_session(self, session_id: str = None) -> str:
        """Start a new session"""
        if not session_id:
            session_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:12]
        
        self.current_session = session_id
        self.session_history.append({
            'id': session_id,
            'start_time': time.time(),
            'messages': 0
        })
        
        return session_id
    
    def get_functional_status(self) -> Dict[str, Any]:
        """Get status of functional components"""
        conn = sqlite3.connect(self.memory_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM memories")
        total_memories = cursor.fetchone()[0]
        conn.close()
        
        return {
            'personality': self.personality['name'],
            'current_session': self.current_session,
            'total_memories': total_memories,
            'chat_history_available': len(self.chat_history_dirs) > 0,
            'session_count': len(self.session_history),
            'data_directory': str(self.data_dir),
            'capabilities': {
                'memory_persistence': True,
                'chat_history_search': len(self.chat_history_dirs) > 0,
                'session_bridging': True,
                'entity_extraction': True
            }
        }


# Example usage
if __name__ == "__main__":
    print("🧬 Testing NEXUS Functional Core")
    
    nexus = NEXUSFunctionalCore()
    
    # Start a session
    session_id = nexus.start_session()
    print(f"\n📍 Started session: {session_id}")
    
    # Store some memories
    mem1 = nexus.store_memory(
        "User asked about NEXUS capabilities",
        context={'query_type': 'capabilities'},
        tags=['introduction', 'capabilities']
    )
    print(f"💾 Stored memory: {mem1}")
    
    # Search memories
    memories = nexus.retrieve_memories(query="capabilities")
    print(f"\n🔍 Found {len(memories)} memories about capabilities")
    
    # Extract entities from text
    sample_text = 'John Smith from OpenAI said "NEXUS is impressive" at https://example.com'
    entities = nexus.extract_entities(sample_text)
    print(f"\n🏷️ Extracted entities: {entities}")
    
    # Get status
    status = nexus.get_functional_status()
    print(f"\n📊 Functional Status:")
    print(json.dumps(status, indent=2))