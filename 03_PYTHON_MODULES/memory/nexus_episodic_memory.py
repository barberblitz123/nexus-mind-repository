#!/usr/bin/env python3
"""
NEXUS Episodic Memory
Stage 2 of the 4-stage memory system

Recent experiences stored in SQLite with temporal context
- Temporal indexing for time-based queries
- Experience replay capability
- Emotion and significance tagging
- Automatic consolidation to semantic memory
"""

import aiosqlite
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from nexus_memory_types import MemoryEntry

logger = logging.getLogger('NEXUS-EpisodicMemory')


class EpisodicMemory:
    """
    Stage 2: Experience-based temporal memory
    Stores recent experiences with rich temporal and emotional context
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize episodic memory with configuration"""
        self.config = config
        self.db_path = Path(config.get('db_path', './nexus_episodic.db'))
        self.max_episodes = config.get('max_episodes', 100000)
        self.consolidation_interval = config.get('consolidation_interval', 3600)
        
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Database connection (will be initialized in setup)
        self.db: Optional[aiosqlite.Connection] = None
        
        # Statistics
        self.stats = {
            'total_episodes': 0,
            'total_replays': 0,
            'consolidations': 0,
            'queries': 0
        }
        
        logger.info(f"Episodic Memory initialized: {self.db_path}")
    
    async def setup(self):
        """Setup database connection and schema"""
        self.db = await aiosqlite.connect(str(self.db_path))
        
        # Enable WAL mode for better concurrency
        await self.db.execute("PRAGMA journal_mode=WAL")
        
        # Create schema
        await self._create_schema()
        
        # Load statistics
        await self._load_stats()
        
        logger.info("Episodic Memory database setup complete")
    
    async def _create_schema(self):
        """Create database schema for episodic memories"""
        schema = """
        CREATE TABLE IF NOT EXISTS episodic_memories (
            id TEXT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            content TEXT NOT NULL,
            metadata TEXT,
            importance REAL DEFAULT 0.5,
            emotional_valence REAL DEFAULT 0.0,
            arousal_level REAL DEFAULT 0.5,
            significance_score REAL DEFAULT 0.5,
            temporal_context TEXT,
            replay_count INTEGER DEFAULT 0,
            last_replayed DATETIME,
            consolidation_status TEXT DEFAULT 'pending',
            working_memory_ref TEXT,
            semantic_memory_ref TEXT,
            access_count INTEGER DEFAULT 0,
            last_accessed DATETIME,
            stage TEXT DEFAULT 'episodic'
        );
        
        CREATE INDEX IF NOT EXISTS idx_temporal ON episodic_memories(timestamp);
        CREATE INDEX IF NOT EXISTS idx_significance ON episodic_memories(significance_score);
        CREATE INDEX IF NOT EXISTS idx_importance ON episodic_memories(importance);
        CREATE INDEX IF NOT EXISTS idx_consolidation ON episodic_memories(consolidation_status);
        
        CREATE TABLE IF NOT EXISTS episodic_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memory_id_1 TEXT NOT NULL,
            memory_id_2 TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            strength REAL DEFAULT 0.5,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (memory_id_1) REFERENCES episodic_memories(id),
            FOREIGN KEY (memory_id_2) REFERENCES episodic_memories(id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_relationships ON episodic_relationships(memory_id_1, memory_id_2);
        
        CREATE TABLE IF NOT EXISTS episodic_stats (
            key TEXT PRIMARY KEY,
            value INTEGER DEFAULT 0
        );
        """
        
        await self.db.executescript(schema)
        await self.db.commit()
    
    async def store(self, entry: MemoryEntry) -> bool:
        """Store memory entry in episodic memory"""
        try:
            # Extract or calculate emotional context
            emotional_valence = entry.metadata.get('emotional_valence', 0.0)
            arousal_level = entry.metadata.get('arousal_level', 0.5)
            
            # Calculate significance score
            significance = self._calculate_significance(entry, emotional_valence, arousal_level)
            
            # Create temporal context
            temporal_context = self._create_temporal_context(entry)
            
            # Store in database
            await self.db.execute("""
                INSERT INTO episodic_memories (
                    id, timestamp, content, metadata, importance,
                    emotional_valence, arousal_level, significance_score,
                    temporal_context, working_memory_ref, stage
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id,
                entry.timestamp.isoformat(),
                json.dumps(entry.content) if not isinstance(entry.content, str) else entry.content,
                json.dumps(entry.metadata),
                entry.importance,
                emotional_valence,
                arousal_level,
                significance,
                json.dumps(temporal_context),
                entry.metadata.get('working_memory_ref', ''),
                entry.stage
            ))
            
            await self.db.commit()
            
            # Update relationships if similar memories exist
            await self._update_relationships(entry)
            
            # Check if we need to prune old memories
            await self._prune_if_needed()
            
            self.stats['total_episodes'] += 1
            await self._save_stats()
            
            logger.debug(f"Stored episode {entry.id} with significance {significance:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing episode {entry.id}: {e}")
            return False
    
    async def get_by_id(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve specific episode by ID"""
        cursor = await self.db.execute("""
            SELECT * FROM episodic_memories WHERE id = ?
        """, (memory_id,))
        
        row = await cursor.fetchone()
        if not row:
            return None
        
        # Update access statistics
        await self.db.execute("""
            UPDATE episodic_memories 
            SET access_count = access_count + 1,
                last_accessed = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), memory_id))
        await self.db.commit()
        
        # Convert row to MemoryEntry
        return self._row_to_memory_entry(row)
    
    async def search(self, query: str, n_results: int = 10) -> List[MemoryEntry]:
        """Search episodic memories with temporal and emotional context"""
        self.stats['queries'] += 1
        
        # Search in content and metadata
        cursor = await self.db.execute("""
            SELECT * FROM episodic_memories
            WHERE content LIKE ? OR metadata LIKE ?
            ORDER BY significance_score DESC, timestamp DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", n_results * 2))
        
        rows = await cursor.fetchall()
        
        # Convert to MemoryEntry objects
        entries = []
        for row in rows:
            entry = self._row_to_memory_entry(row)
            if entry:
                entries.append(entry)
        
        # Sort by relevance to query
        entries = self._rank_by_relevance(entries, query)
        
        return entries[:n_results]
    
    async def get_temporal_window(self, start: datetime, end: datetime) -> List[MemoryEntry]:
        """Get all memories within a time window"""
        cursor = await self.db.execute("""
            SELECT * FROM episodic_memories
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
        """, (start.isoformat(), end.isoformat()))
        
        rows = await cursor.fetchall()
        return [self._row_to_memory_entry(row) for row in rows if row]
    
    async def get_by_emotion(self, valence_min: float = -1.0, valence_max: float = 1.0,
                           arousal_min: float = 0.0, arousal_max: float = 1.0,
                           n_results: int = 10) -> List[MemoryEntry]:
        """Get memories by emotional state"""
        cursor = await self.db.execute("""
            SELECT * FROM episodic_memories
            WHERE emotional_valence BETWEEN ? AND ?
              AND arousal_level BETWEEN ? AND ?
            ORDER BY significance_score DESC
            LIMIT ?
        """, (valence_min, valence_max, arousal_min, arousal_max, n_results))
        
        rows = await cursor.fetchall()
        return [self._row_to_memory_entry(row) for row in rows if row]
    
    async def replay_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """
        Replay a memory, strengthening it
        Returns the memory with updated replay count
        """
        entry = await self.get_by_id(memory_id)
        if not entry:
            return None
        
        # Update replay statistics
        await self.db.execute("""
            UPDATE episodic_memories
            SET replay_count = replay_count + 1,
                last_replayed = ?,
                significance_score = MIN(significance_score * 1.1, 1.0)
            WHERE id = ?
        """, (datetime.now().isoformat(), memory_id))
        await self.db.commit()
        
        self.stats['total_replays'] += 1
        
        # Return updated entry
        return await self.get_by_id(memory_id)
    
    async def get_for_consolidation(self, limit: int = 100) -> List[MemoryEntry]:
        """Get memories ready for consolidation to semantic memory"""
        # Get old, significant memories that haven't been consolidated
        min_age = datetime.now() - timedelta(seconds=self.consolidation_interval)
        
        cursor = await self.db.execute("""
            SELECT * FROM episodic_memories
            WHERE consolidation_status = 'pending'
              AND timestamp < ?
              AND (significance_score > 0.6 OR replay_count > 3 OR importance > 0.7)
            ORDER BY significance_score DESC, importance DESC
            LIMIT ?
        """, (min_age.isoformat(), limit))
        
        rows = await cursor.fetchall()
        return [self._row_to_memory_entry(row) for row in rows if row]
    
    async def mark_consolidated(self, memory_id: str, semantic_ref: str):
        """Mark memory as consolidated to semantic memory"""
        await self.db.execute("""
            UPDATE episodic_memories
            SET consolidation_status = 'consolidated',
                semantic_memory_ref = ?
            WHERE id = ?
        """, (semantic_ref, memory_id))
        await self.db.commit()
        
        self.stats['consolidations'] += 1
    
    def _calculate_significance(self, entry: MemoryEntry, 
                              emotional_valence: float, 
                              arousal_level: float) -> float:
        """
        Calculate significance score based on multiple factors
        Higher significance = more likely to be remembered long-term
        """
        # Base significance from importance
        significance = entry.importance * 0.4
        
        # Emotional impact (strong emotions = more significant)
        emotional_impact = abs(emotional_valence) * arousal_level
        significance += emotional_impact * 0.3
        
        # Metadata factors
        if entry.metadata.get('task_result') == 'success':
            significance += 0.1
        if entry.metadata.get('error'):
            significance += 0.2  # Errors are significant for learning
        if entry.metadata.get('user_interaction'):
            significance += 0.15
        
        # Content-based factors
        content_str = str(entry.content)
        if any(word in content_str.lower() for word in ['error', 'success', 'important', 'critical']):
            significance += 0.1
        
        return min(significance, 1.0)
    
    def _create_temporal_context(self, entry: MemoryEntry) -> Dict[str, Any]:
        """Create temporal context for the memory"""
        now = datetime.now()
        
        return {
            'time_of_day': now.strftime('%H:%M:%S'),
            'day_of_week': now.strftime('%A'),
            'date': now.strftime('%Y-%m-%d'),
            'timestamp': now.isoformat(),
            'session_time': entry.metadata.get('session_time', 0),
            'previous_memory': entry.metadata.get('previous_memory_id', '')
        }
    
    async def _update_relationships(self, entry: MemoryEntry):
        """Find and store relationships between memories"""
        # Find recent similar memories
        time_window = datetime.now() - timedelta(hours=1)
        
        cursor = await self.db.execute("""
            SELECT id, content FROM episodic_memories
            WHERE timestamp > ? AND id != ?
            ORDER BY timestamp DESC
            LIMIT 20
        """, (time_window.isoformat(), entry.id))
        
        recent_memories = await cursor.fetchall()
        
        # Simple similarity check (could be enhanced with embeddings)
        content_str = str(entry.content).lower()
        
        for mem_id, mem_content in recent_memories:
            mem_content_str = str(mem_content).lower()
            
            # Check for common keywords
            content_words = set(content_str.split())
            mem_words = set(mem_content_str.split())
            
            common_words = content_words.intersection(mem_words)
            if len(common_words) > 3:  # Arbitrary threshold
                strength = len(common_words) / max(len(content_words), len(mem_words))
                
                await self.db.execute("""
                    INSERT INTO episodic_relationships 
                    (memory_id_1, memory_id_2, relationship_type, strength)
                    VALUES (?, ?, ?, ?)
                """, (entry.id, mem_id, 'similarity', strength))
    
    async def _prune_if_needed(self):
        """Remove old memories if we exceed max_episodes"""
        cursor = await self.db.execute(
            "SELECT COUNT(*) FROM episodic_memories"
        )
        count = (await cursor.fetchone())[0]
        
        if count > self.max_episodes:
            # Remove oldest, least significant memories
            to_remove = count - int(self.max_episodes * 0.9)  # Keep 90% after pruning
            
            await self.db.execute("""
                DELETE FROM episodic_memories
                WHERE id IN (
                    SELECT id FROM episodic_memories
                    WHERE consolidation_status = 'consolidated'
                    ORDER BY significance_score ASC, timestamp ASC
                    LIMIT ?
                )
            """, (to_remove,))
            await self.db.commit()
            
            logger.info(f"Pruned {to_remove} old episodic memories")
    
    def _row_to_memory_entry(self, row) -> Optional[MemoryEntry]:
        """Convert database row to MemoryEntry"""
        if not row:
            return None
        
        try:
            # Convert row to dictionary if it's a tuple
            if isinstance(row, (tuple, list)):
                # Get column names from cursor description or use defaults
                columns = [
                    'id', 'timestamp', 'content', 'metadata', 'importance',
                    'emotional_valence', 'arousal_level', 'significance_score',
                    'temporal_context', 'replay_count', 'last_replayed',
                    'consolidation_status', 'working_memory_ref', 'semantic_memory_ref',
                    'access_count', 'last_accessed', 'stage'
                ]
                row_dict = dict(zip(columns[:len(row)], row))
            else:
                row_dict = dict(row)
            
            # Parse JSON fields
            content = json.loads(row_dict['content']) if isinstance(row_dict['content'], str) and row_dict['content'].startswith('{') else row_dict['content']
            metadata = json.loads(row_dict['metadata']) if row_dict.get('metadata') else {}
            
            # Add episodic-specific metadata
            metadata.update({
                'emotional_valence': row_dict.get('emotional_valence', 0.0),
                'arousal_level': row_dict.get('arousal_level', 0.5),
                'significance_score': row_dict.get('significance_score', 0.5),
                'replay_count': row_dict.get('replay_count', 0),
                'consolidation_status': row_dict.get('consolidation_status', 'pending')
            })
            
            return MemoryEntry(
                id=row_dict['id'],
                content=content,
                metadata=metadata,
                importance=row_dict.get('importance', 0.5),
                timestamp=datetime.fromisoformat(row_dict['timestamp']) if isinstance(row_dict['timestamp'], str) else row_dict['timestamp'],
                access_count=row_dict.get('access_count', 0),
                last_accessed=datetime.fromisoformat(row_dict['last_accessed']) if row_dict.get('last_accessed') else None,
                stage=row_dict.get('stage', 'episodic')
            )
        except Exception as e:
            logger.error(f"Error converting row to MemoryEntry: {e}")
            logger.error(f"Row type: {type(row)}, Row content: {row}")
            return None
    
    def _rank_by_relevance(self, entries: List[MemoryEntry], query: str) -> List[MemoryEntry]:
        """Rank entries by relevance to query"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for entry in entries:
            content_str = str(entry.content).lower()
            content_words = set(content_str.split())
            
            # Calculate relevance score
            common_words = query_words.intersection(content_words)
            relevance = len(common_words) / len(query_words) if query_words else 0
            
            # Boost by significance and recency
            recency_boost = 1.0 / (1 + (datetime.now() - entry.timestamp).days)
            
            entry.metadata['search_relevance'] = (
                relevance * 0.5 +
                entry.metadata.get('significance_score', 0.5) * 0.3 +
                recency_boost * 0.2
            )
        
        # Sort by relevance
        entries.sort(key=lambda e: e.metadata.get('search_relevance', 0), reverse=True)
        
        return entries
    
    async def _load_stats(self):
        """Load statistics from database"""
        cursor = await self.db.execute("SELECT key, value FROM episodic_stats")
        rows = await cursor.fetchall()
        
        for key, value in rows:
            if key in self.stats:
                self.stats[key] = value
    
    async def _save_stats(self):
        """Save statistics to database"""
        for key, value in self.stats.items():
            await self.db.execute("""
                INSERT OR REPLACE INTO episodic_stats (key, value)
                VALUES (?, ?)
            """, (key, value))
        await self.db.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get episodic memory statistics"""
        return {
            'total_episodes': self.stats['total_episodes'],
            'total_replays': self.stats['total_replays'],
            'consolidations': self.stats['consolidations'],
            'queries': self.stats['queries'],
            'database_path': str(self.db_path),
            'max_episodes': self.max_episodes
        }
    
    async def close(self):
        """Close database connection"""
        if self.db:
            await self._save_stats()
            await self.db.close()
            logger.info("Episodic Memory database closed")


# Test episodic memory
async def test_episodic_memory():
    """Test episodic memory functionality"""
    config = {
        'db_path': './test_episodic.db',
        'max_episodes': 1000
    }
    
    em = EpisodicMemory(config)
    await em.setup()
    
    # Test storing episodes
    test_entries = []
    for i in range(5):
        entry = MemoryEntry(
            id=f"episode_{i}",
            content=f"Test episode {i}: Something {'important' if i % 2 == 0 else 'normal'} happened",
            metadata={
                'index': i,
                'emotional_valence': (i - 2) / 2,  # -1 to 1
                'arousal_level': 0.3 + i * 0.15,   # 0.3 to 0.9
                'type': 'test'
            },
            importance=0.4 + i * 0.12
        )
        test_entries.append(entry)
        success = await em.store(entry)
        logger.info(f"Stored episode_{i}: {success}")
    
    # Test retrieval
    entry = await em.get_by_id("episode_2")
    logger.info(f"Retrieved: {entry.id if entry else 'Not found'}")
    
    # Test search
    results = await em.search("important", n_results=3)
    logger.info(f"Search results: {[r.id for r in results]}")
    
    # Test temporal window
    start = datetime.now() - timedelta(minutes=5)
    end = datetime.now()
    temporal_results = await em.get_temporal_window(start, end)
    logger.info(f"Temporal window results: {[r.id for r in temporal_results]}")
    
    # Test emotion-based retrieval
    positive_memories = await em.get_by_emotion(valence_min=0.0, valence_max=1.0)
    logger.info(f"Positive memories: {[r.id for r in positive_memories]}")
    
    # Test replay
    replayed = await em.replay_memory("episode_1")
    if replayed:
        logger.info(f"Replayed {replayed.id}, replay count: {replayed.metadata.get('replay_count')}")
    
    # Test consolidation candidates
    consolidation_ready = await em.get_for_consolidation()
    logger.info(f"Ready for consolidation: {[e.id for e in consolidation_ready]}")
    
    # Get stats
    stats = em.get_stats()
    logger.info(f"Episodic memory stats: {stats}")
    
    await em.close()
    return em


if __name__ == "__main__":
    # Run test
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(test_episodic_memory())