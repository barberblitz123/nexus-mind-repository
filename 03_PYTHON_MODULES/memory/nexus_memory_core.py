#!/usr/bin/env python3
"""
NEXUS Unified Memory System
4-Stage Memory Architecture with MEM0

This implements a hierarchical memory system inspired by human cognition:
1. Working Memory - Active, immediate (RAM)
2. Episodic Memory - Recent experiences (SQLite)
3. Semantic Memory - Knowledge graphs (ChromaDB)
4. Persistent Memory - Forever storage (MEM0)
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import hashlib

# Import common types
from nexus_memory_types import MemoryEntry

# Import memory stage implementations
from nexus_working_memory import WorkingMemory
from nexus_episodic_memory import EpisodicMemory
from nexus_semantic_memory import SemanticMemory
from nexus_mem0_core import PersistentMemory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('NEXUS-Memory')


class NexusUnifiedMemory:
    """
    Unified 7-stage memory system integrating all memory types
    Provides single interface for all memory operations with enhanced capabilities
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize unified memory system"""
        logger.info("Initializing NEXUS Unified Memory System 2.0")
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize core memory stages
        self._initialize_memory_stages()
        
        # Initialize enhanced memory types
        self._initialize_enhanced_memories()
        
        # Memory consolidation system
        self.consolidation = MemoryConsolidation(self)
        
        # Unified retrieval system with fusion
        self.retrieval = UnifiedMemoryRetrieval(self)
        
        # Memory fusion engine
        self.fusion = MemoryFusionEngine(self)
        
        # Temporal decay manager
        self.decay_manager = TemporalDecayManager(self)
        
        # Statistics tracking
        self.stats = MemoryStatistics()
        
        # Start background processes
        asyncio.create_task(self._background_maintenance())
        
        logger.info("NEXUS Unified Memory System 2.0 initialized")
    
    def _initialize_memory_stages(self):
        """Initialize all memory stages with their configurations"""
        try:
            # Stage 1: Working Memory
            logger.info("Initializing Working Memory...")
            self.working_memory = WorkingMemory(self.config['working_memory'])
            
            # Stage 2: Episodic Memory
            logger.info("Initializing Episodic Memory...")
            self.episodic_memory = EpisodicMemory(self.config['episodic_memory'])
            # Setup async components
            asyncio.create_task(self.episodic_memory.setup())
            
            # Stage 3: Semantic Memory (ChromaDB)
            logger.info("Initializing Semantic Memory...")
            self.semantic_memory = SemanticMemory(self.config['semantic_memory'])
            
            # Stage 4: Persistent Memory (MEM0)
            logger.info("Initializing Persistent Memory (MEM0)...")
            self.persistent_memory = PersistentMemory(self.config['mem0'])
            
            logger.info("All core memory stages initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing memory stages: {e}")
            # Initialize with None for failed components
            if not hasattr(self, 'working_memory'):
                self.working_memory = None
            if not hasattr(self, 'episodic_memory'):
                self.episodic_memory = None
            if not hasattr(self, 'semantic_memory'):
                self.semantic_memory = None
            if not hasattr(self, 'persistent_memory'):
                self.persistent_memory = None
    
    def _initialize_enhanced_memories(self):
        """Initialize enhanced memory types"""
        try:
            # Stage 5: Learning Memory
            logger.info("Initializing Learning Memory...")
            self.learning_memory = LearningMemory(self.config.get('learning_memory', {}))
            
            # Stage 6: Goal Memory
            logger.info("Initializing Goal Memory...")
            self.goal_memory = GoalMemory(self.config.get('goal_memory', {}))
            
            # Stage 7: Context Memory
            logger.info("Initializing Context Memory...")
            self.context_memory = ContextMemory(self.config.get('context_memory', {}))
            
            # Stage 8: Collaborative Memory
            logger.info("Initializing Collaborative Memory...")
            self.collaborative_memory = CollaborativeMemory(self.config.get('collaborative_memory', {}))
            
            logger.info("All enhanced memory types initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing enhanced memories: {e}")
            # Initialize with None for failed components
            for memory_type in ['learning_memory', 'goal_memory', 'context_memory', 'collaborative_memory']:
                if not hasattr(self, memory_type):
                    setattr(self, memory_type, None)
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            "working_memory": {
                "max_size_mb": 512,
                "ttl_seconds": 3600,
                "eviction_policy": "lru"
            },
            "episodic_memory": {
                "db_path": "./nexus_episodic.db",
                "max_episodes": 100000,
                "consolidation_interval": 3600
            },
            "semantic_memory": {
                "chromadb_path": "./nexus_vectors",
                "use_existing": True,
                "embedding_model": "all-MiniLM-L6-v2"
            },
            "mem0": {
                "storage_path": "./nexus_mem0",
                "encryption": True,
                "compression": "zstd",
                "block_size_kb": 64,
                "redundancy": 2
            },
            "consolidation": {
                "to_episodic": 0.3,
                "to_semantic": 0.6,
                "to_persistent": 0.8,
                "auto_consolidate": True,
                "interval_seconds": 300
            }
        }
        
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    for key, value in loaded_config.items():
                        if key in default_config:
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
            except Exception as e:
                logger.warning(f"Could not load config from {config_path}: {e}")
        
        return default_config
    
    async def store(self, content: Any, metadata: Optional[Dict[str, Any]] = None, 
                   importance: Optional[float] = None) -> str:
        """
        Store content in unified memory system
        Automatically routes to appropriate memory stage based on importance
        """
        # Generate unique ID
        memory_id = self._generate_memory_id(content)
        
        # Create memory entry
        entry = MemoryEntry(
            id=memory_id,
            content=content,
            metadata=metadata or {},
            importance=importance or self._calculate_importance(content, metadata)
        )
        
        # Store in working memory first
        if self.working_memory:
            await self.working_memory.store(entry)
        
        # Route to appropriate stage based on importance
        if entry.importance >= self.config['consolidation']['to_persistent']:
            # Very important - store in MEM0 immediately
            if self.persistent_memory:
                await self.persistent_memory.store(entry)
            entry.stage = "persistent"
        elif entry.importance >= self.config['consolidation']['to_semantic']:
            # Important - store in semantic memory
            if self.semantic_memory:
                await self.semantic_memory.store(entry)
            entry.stage = "semantic"
        elif entry.importance >= self.config['consolidation']['to_episodic']:
            # Moderate importance - store in episodic memory
            if self.episodic_memory:
                await self.episodic_memory.store(entry)
            entry.stage = "episodic"
        
        # Update statistics
        self.stats.record_store(entry)
        
        logger.info(f"Stored memory {memory_id} in stage: {entry.stage}")
        return memory_id
    
    async def retrieve(self, query: str, n_results: int = 10) -> List[MemoryEntry]:
        """
        Retrieve memories using unified search across all stages
        """
        return await self.retrieval.search(query, n_results)
    
    async def get_by_id(self, memory_id: str) -> Optional[MemoryEntry]:
        """
        Retrieve specific memory by ID
        """
        # Check each stage in order of likelihood
        stages = [
            ('working', self.working_memory),
            ('episodic', self.episodic_memory),
            ('semantic', self.semantic_memory),
            ('persistent', self.persistent_memory)
        ]
        
        for stage_name, stage in stages:
            if stage:
                entry = await stage.get_by_id(memory_id)
                if entry:
                    entry.access_count += 1
                    entry.last_accessed = datetime.now()
                    self.stats.record_retrieval(entry)
                    return entry
        
        return None
    
    def _generate_memory_id(self, content: Any) -> str:
        """Generate unique ID for memory entry"""
        content_str = json.dumps(content, sort_keys=True, default=str)
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16]
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        return f"mem_{timestamp}_{content_hash}"
    
    def _calculate_importance(self, content: Any, metadata: Optional[Dict[str, Any]]) -> float:
        """
        Calculate importance score for memory entry
        Factors: content length, metadata tags, keywords, etc.
        """
        score = 0.5  # Base score
        
        # Content-based scoring
        content_str = str(content)
        
        # Length factor (longer = potentially more important)
        if len(content_str) > 1000:
            score += 0.1
        
        # Keyword detection
        important_keywords = [
            'critical', 'important', 'urgent', 'error', 'success',
            'nexus', 'consciousness', 'memory', 'core', 'system'
        ]
        
        for keyword in important_keywords:
            if keyword.lower() in content_str.lower():
                score += 0.05
        
        # Metadata factors
        if metadata:
            if metadata.get('priority') == 'high':
                score += 0.2
            if metadata.get('user_marked_important'):
                score += 0.3
            if metadata.get('task_result') == 'success':
                score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    async def consolidate(self):
        """Run memory consolidation process"""
        if self.config['consolidation']['auto_consolidate']:
            await self.consolidation.run()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        stats = {
            'total_operations': self.stats.total_stores + self.stats.total_retrievals,
            'total_stores': self.stats.total_stores,
            'total_retrievals': self.stats.total_retrievals,
            'stage_distribution': self.stats.stage_counts,
            'average_importance': self.stats.get_average_importance()
        }
        
        # Add stage-specific stats if available
        if self.working_memory:
            stats['working_memory'] = self.working_memory.get_stats()
        if self.episodic_memory:
            stats['episodic_memory'] = self.episodic_memory.get_stats()
        if self.semantic_memory:
            stats['semantic_memory'] = self.semantic_memory.get_stats()
        if self.persistent_memory:
            stats['persistent_memory'] = self.persistent_memory.get_stats()
        
        return stats


class MemoryConsolidation:
    """
    Manages memory flow between stages
    Working → Episodic → Semantic → Persistent
    """
    
    def __init__(self, unified_memory: NexusUnifiedMemory):
        self.memory = unified_memory
        self.last_consolidation = datetime.now()
        
    async def run(self):
        """
        Run consolidation process
        Moves memories between stages based on importance and age
        """
        logger.info("Running memory consolidation")
        
        # Check if it's time to consolidate
        interval = timedelta(seconds=self.memory.config['consolidation']['interval_seconds'])
        if datetime.now() - self.last_consolidation < interval:
            return
        
        # Consolidate from working to episodic
        if self.memory.working_memory and self.memory.episodic_memory:
            await self._consolidate_working_to_episodic()
        
        # Consolidate from episodic to semantic
        if self.memory.episodic_memory and self.memory.semantic_memory:
            await self._consolidate_episodic_to_semantic()
        
        # Consolidate from semantic to persistent
        if self.memory.semantic_memory and self.memory.persistent_memory:
            await self._consolidate_semantic_to_persistent()
        
        self.last_consolidation = datetime.now()
        logger.info("Memory consolidation completed")
    
    async def _consolidate_working_to_episodic(self):
        """Move eligible memories from working to episodic"""
        if not (self.memory.working_memory and self.memory.episodic_memory):
            return
        
        # Get memories ready for consolidation
        eligible = await self.memory.working_memory.get_all_for_consolidation()
        
        consolidated = 0
        for entry in eligible:
            # Check if memory meets threshold
            if entry.importance >= self.memory.config['consolidation']['to_episodic']:
                # Store in episodic memory
                success = await self.memory.episodic_memory.store(entry)
                
                if success:
                    # Remove from working memory
                    await self.memory.working_memory.remove(entry.id)
                    consolidated += 1
                    logger.debug(f"Consolidated {entry.id} to episodic memory")
        
        if consolidated > 0:
            logger.info(f"Consolidated {consolidated} memories from working to episodic")
    
    async def _consolidate_episodic_to_semantic(self):
        """Extract patterns and move to semantic memory"""
        if not (self.memory.episodic_memory and self.memory.semantic_memory):
            return
        
        # Get memories ready for semantic consolidation
        eligible = await self.memory.episodic_memory.get_for_consolidation(limit=50)
        
        consolidated = 0
        for entry in eligible:
            # Check if memory meets threshold
            if entry.importance >= self.memory.config['consolidation']['to_semantic']:
                # Store in semantic memory
                success = await self.memory.semantic_memory.store(entry)
                
                if success:
                    # Mark as consolidated in episodic
                    await self.memory.episodic_memory.mark_consolidated(
                        entry.id, 
                        f"semantic_{entry.id}"
                    )
                    consolidated += 1
                    logger.debug(f"Consolidated {entry.id} to semantic memory")
        
        if consolidated > 0:
            logger.info(f"Consolidated {consolidated} memories from episodic to semantic")
    
    async def _consolidate_semantic_to_persistent(self):
        """Archive important semantic memories to MEM0"""
        if not (self.memory.semantic_memory and self.memory.persistent_memory):
            return
        
        # Search for highly important memories in semantic
        important_memories = await self.memory.semantic_memory.search(
            "important critical core system",
            n_results=20
        )
        
        consolidated = 0
        for entry in important_memories:
            # Check if memory meets threshold and not already in persistent
            if (entry.importance >= self.memory.config['consolidation']['to_persistent'] and
                entry.stage != 'persistent'):
                
                # Store in persistent memory
                success = await self.memory.persistent_memory.store(entry)
                
                if success:
                    entry.stage = 'persistent'
                    consolidated += 1
                    logger.debug(f"Archived {entry.id} to persistent memory")
        
        if consolidated > 0:
            logger.info(f"Archived {consolidated} memories to persistent storage")


class UnifiedMemoryRetrieval:
    """
    Intelligent retrieval across all memory stages
    Implements parallel search with result fusion
    """
    
    def __init__(self, unified_memory: NexusUnifiedMemory):
        self.memory = unified_memory
        
    async def search(self, query: str, n_results: int = 10) -> List[MemoryEntry]:
        """
        Search across all memory stages in parallel
        """
        results = []
        
        # Search all stages in parallel
        search_tasks = []
        
        if self.memory.working_memory:
            search_tasks.append(self._search_stage('working', self.memory.working_memory, query, n_results))
        if self.memory.episodic_memory:
            search_tasks.append(self._search_stage('episodic', self.memory.episodic_memory, query, n_results))
        if self.memory.semantic_memory:
            search_tasks.append(self._search_stage('semantic', self.memory.semantic_memory, query, n_results * 2))
        if self.memory.persistent_memory:
            search_tasks.append(self._search_stage('persistent', self.memory.persistent_memory, query, n_results))
        
        # Execute searches in parallel
        if search_tasks:
            stage_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Combine results
            for stage_result in stage_results:
                if isinstance(stage_result, list):
                    results.extend(stage_result)
        
        # Rank and deduplicate results
        results = self._rank_results(results, query)
        
        # Return top N
        return results[:n_results]
    
    async def _search_stage(self, stage_name: str, stage, query: str, n_results: int) -> List[MemoryEntry]:
        """Search individual memory stage"""
        try:
            return await stage.search(query, n_results)
        except Exception as e:
            logger.error(f"Error searching {stage_name} memory: {e}")
            return []
    
    def _rank_results(self, results: List[MemoryEntry], query: str) -> List[MemoryEntry]:
        """
        Rank results by relevance and importance
        Remove duplicates
        """
        # Remove duplicates by ID
        seen = set()
        unique_results = []
        for entry in results:
            if entry.id not in seen:
                seen.add(entry.id)
                unique_results.append(entry)
        
        # Calculate relevance scores
        for entry in unique_results:
            # Simple relevance: keyword matching
            content_str = str(entry.content).lower()
            query_lower = query.lower()
            
            # Exact match bonus
            if query_lower in content_str:
                entry.metadata['relevance_score'] = 1.0
            else:
                # Partial match
                query_words = query_lower.split()
                matches = sum(1 for word in query_words if word in content_str)
                entry.metadata['relevance_score'] = matches / len(query_words)
            
            # Combined score: relevance * importance * recency
            recency_factor = 1.0 / (1 + (datetime.now() - entry.timestamp).days)
            entry.metadata['combined_score'] = (
                entry.metadata['relevance_score'] * 
                entry.importance * 
                recency_factor
            )
        
        # Sort by combined score
        unique_results.sort(key=lambda x: x.metadata.get('combined_score', 0), reverse=True)
        
        return unique_results


class MemoryStatistics:
    """Track memory system statistics"""
    
    def __init__(self):
        self.total_stores = 0
        self.total_retrievals = 0
        self.stage_counts = {
            'working': 0,
            'episodic': 0,
            'semantic': 0,
            'persistent': 0
        }
        self.importance_sum = 0.0
        self.importance_count = 0
        
    def record_store(self, entry: MemoryEntry):
        """Record a store operation"""
        self.total_stores += 1
        self.stage_counts[entry.stage] += 1
        self.importance_sum += entry.importance
        self.importance_count += 1
        
    def record_retrieval(self, entry: MemoryEntry):
        """Record a retrieval operation"""
        self.total_retrievals += 1
        
    def get_average_importance(self) -> float:
        """Get average importance of stored memories"""
        if self.importance_count == 0:
            return 0.0
        return self.importance_sum / self.importance_count


# Example usage and testing
async def test_unified_memory():
    """Test the unified memory system"""
    logger.info("Testing NEXUS Unified Memory System")
    
    # Initialize memory
    memory = NexusUnifiedMemory()
    
    # Wait a bit for async initialization
    await asyncio.sleep(1)
    
    # Store some test memories with different importance levels
    test_memories = [
        {
            "content": "This is a low importance test memory for working memory only",
            "metadata": {"type": "test", "category": "low"},
            "importance": 0.2
        },
        {
            "content": "This is a moderate importance task result for episodic memory",
            "metadata": {"type": "task", "task_id": "123", "result": "success"},
            "importance": 0.5
        },
        {
            "content": "This is an important semantic knowledge about NEXUS consciousness architecture",
            "metadata": {"type": "knowledge", "domain": "consciousness", "tags": ["nexus", "architecture"]},
            "importance": 0.7
        },
        {
            "content": "This is a critical system memory about NEXUS core consciousness protocols that must be preserved forever",
            "metadata": {"type": "system", "priority": "high", "critical": True},
            "importance": 0.95
        }
    ]
    
    stored_ids = []
    logger.info("\n--- Storing memories ---")
    for i, mem in enumerate(test_memories):
        mem_id = await memory.store(
            mem["content"], 
            mem["metadata"], 
            mem["importance"]
        )
        stored_ids.append(mem_id)
        logger.info(f"Stored {i+1}: {mem_id} (importance: {mem['importance']})")
    
    # Test retrieval by ID
    logger.info("\n--- Testing retrieval by ID ---")
    if stored_ids:
        test_id = stored_ids[1]
        retrieved = await memory.get_by_id(test_id)
        if retrieved:
            logger.info(f"Retrieved {test_id}: {retrieved.content[:50]}...")
    
    # Test search across all stages
    logger.info("\n--- Testing unified search ---")
    search_queries = [
        "consciousness",
        "task result",
        "critical system",
        "nexus"
    ]
    
    for query in search_queries:
        results = await memory.retrieve(query, n_results=3)
        logger.info(f"Search '{query}': {len(results)} results")
        for r in results:
            logger.info(f"  - {r.id} (stage: {r.stage}, relevance: {r.metadata.get('combined_score', 0):.2f})")
    
    # Test consolidation
    logger.info("\n--- Testing memory consolidation ---")
    await memory.consolidate()
    
    # Get comprehensive statistics
    logger.info("\n--- Memory System Statistics ---")
    stats = memory.get_stats()
    logger.info(f"Overall stats: {json.dumps(stats, indent=2)}")
    
    # Test memory pressure in working memory
    if memory.working_memory:
        pressure = await memory.working_memory.get_memory_pressure()
        logger.info(f"Working memory pressure: {pressure:.2%}")
    
    # Close database connections properly
    if memory.episodic_memory:
        await memory.episodic_memory.close()
    
    logger.info("\n--- Test completed successfully ---")
    return memory


class LearningMemory:
    """Memory system for learning patterns and improvements"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = config.get('db_path', './nexus_learning.db')
        self.learnings = {}
        self._init_db()
    
    def _init_db(self):
        """Initialize learning database"""
        import sqlite3
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS learnings (
                id TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                pattern TEXT NOT NULL,
                outcome TEXT NOT NULL,
                success_rate REAL DEFAULT 0.0,
                confidence REAL DEFAULT 0.0,
                application_count INTEGER DEFAULT 0,
                metadata TEXT
            )
        ''')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS learning_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learning_id TEXT NOT NULL,
                related_memory_id TEXT NOT NULL,
                relationship_type TEXT,
                strength REAL DEFAULT 0.5,
                FOREIGN KEY (learning_id) REFERENCES learnings(id)
            )
        ''')
        self.conn.commit()
    
    async def store(self, entry: MemoryEntry) -> bool:
        """Store learning pattern"""
        try:
            self.conn.execute(
                "INSERT INTO learnings (id, pattern, outcome, metadata) VALUES (?, ?, ?, ?)",
                (entry.id, str(entry.content), entry.metadata.get('outcome', ''), json.dumps(entry.metadata))
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error storing learning: {e}")
            return False
    
    async def search(self, query: str, n_results: int = 10) -> List[MemoryEntry]:
        """Search learning patterns"""
        cursor = self.conn.execute(
            "SELECT * FROM learnings WHERE pattern LIKE ? ORDER BY success_rate DESC LIMIT ?",
            (f'%{query}%', n_results)
        )
        results = []
        for row in cursor:
            entry = MemoryEntry(
                id=row[0],
                content={'pattern': row[2], 'outcome': row[3]},
                metadata=json.loads(row[7]) if row[7] else {},
                importance=row[4],  # Use success_rate as importance
                stage='learning'
            )
            results.append(entry)
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        cursor = self.conn.execute("SELECT COUNT(*), AVG(success_rate), AVG(confidence) FROM learnings")
        count, avg_success, avg_confidence = cursor.fetchone()
        return {
            'total_learnings': count or 0,
            'average_success_rate': avg_success or 0.0,
            'average_confidence': avg_confidence or 0.0
        }


class GoalMemory:
    """Memory system for goals and objectives"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = config.get('db_path', './nexus_goals.db')
        self._init_db()
    
    def _init_db(self):
        """Initialize goals database"""
        import sqlite3
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                goal_description TEXT NOT NULL,
                priority REAL DEFAULT 0.5,
                status TEXT DEFAULT 'active',
                progress REAL DEFAULT 0.0,
                deadline DATETIME,
                parent_goal_id TEXT,
                metadata TEXT
            )
        ''')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS goal_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id TEXT NOT NULL,
                step_description TEXT NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                order_index INTEGER,
                FOREIGN KEY (goal_id) REFERENCES goals(id)
            )
        ''')
        self.conn.commit()
    
    async def store(self, entry: MemoryEntry) -> bool:
        """Store goal"""
        try:
            self.conn.execute(
                "INSERT INTO goals (id, goal_description, priority, metadata) VALUES (?, ?, ?, ?)",
                (entry.id, str(entry.content), entry.importance, json.dumps(entry.metadata))
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error storing goal: {e}")
            return False
    
    async def search(self, query: str, n_results: int = 10) -> List[MemoryEntry]:
        """Search goals"""
        cursor = self.conn.execute(
            "SELECT * FROM goals WHERE goal_description LIKE ? AND status = 'active' ORDER BY priority DESC LIMIT ?",
            (f'%{query}%', n_results)
        )
        results = []
        for row in cursor:
            entry = MemoryEntry(
                id=row[0],
                content=row[2],
                metadata=json.loads(row[8]) if row[8] else {},
                importance=row[3],
                stage='goal'
            )
            results.append(entry)
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get goal statistics"""
        cursor = self.conn.execute("SELECT COUNT(*), AVG(progress) FROM goals WHERE status = 'active'")
        count, avg_progress = cursor.fetchone()
        return {
            'active_goals': count or 0,
            'average_progress': avg_progress or 0.0
        }


class ContextMemory:
    """Memory system for contextual information"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.contexts = {}
        self.current_context = {}
    
    async def store(self, entry: MemoryEntry) -> bool:
        """Store context"""
        context_type = entry.metadata.get('context_type', 'general')
        if context_type not in self.contexts:
            self.contexts[context_type] = []
        self.contexts[context_type].append(entry)
        return True
    
    async def search(self, query: str, n_results: int = 10) -> List[MemoryEntry]:
        """Search contexts"""
        results = []
        for context_type, entries in self.contexts.items():
            for entry in entries:
                if query.lower() in str(entry.content).lower():
                    results.append(entry)
        return results[:n_results]
    
    def get_current_context(self) -> Dict[str, Any]:
        """Get current active context"""
        return self.current_context
    
    def update_context(self, updates: Dict[str, Any]):
        """Update current context"""
        self.current_context.update(updates)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get context statistics"""
        total = sum(len(entries) for entries in self.contexts.values())
        return {
            'context_types': len(self.contexts),
            'total_contexts': total,
            'current_context_keys': len(self.current_context)
        }


class CollaborativeMemory:
    """Memory system for multi-agent collaboration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agent_memories = {}
        self.shared_knowledge = []
    
    async def store(self, entry: MemoryEntry) -> bool:
        """Store collaborative memory"""
        agent_id = entry.metadata.get('agent_id', 'default')
        if agent_id not in self.agent_memories:
            self.agent_memories[agent_id] = []
        self.agent_memories[agent_id].append(entry)
        
        # Share if marked as shared
        if entry.metadata.get('shared', False):
            self.shared_knowledge.append(entry)
        return True
    
    async def search(self, query: str, n_results: int = 10) -> List[MemoryEntry]:
        """Search collaborative memories"""
        results = []
        # Search shared knowledge first
        for entry in self.shared_knowledge:
            if query.lower() in str(entry.content).lower():
                results.append(entry)
        
        # Then search agent-specific memories
        for agent_id, memories in self.agent_memories.items():
            for entry in memories:
                if query.lower() in str(entry.content).lower() and entry not in results:
                    results.append(entry)
        
        return results[:n_results]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collaborative statistics"""
        total = sum(len(memories) for memories in self.agent_memories.values())
        return {
            'total_agents': len(self.agent_memories),
            'total_memories': total,
            'shared_knowledge': len(self.shared_knowledge)
        }


class MemoryFusionEngine:
    """Fuses insights from multiple memory types"""
    
    def __init__(self, unified_memory: NexusUnifiedMemory):
        self.memory = unified_memory
        self.fusion_patterns = {}
    
    async def fuse_memories(self, query: str, memory_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Fuse memories from multiple types to generate insights"""
        if not memory_types:
            memory_types = ['working', 'episodic', 'semantic', 'learning', 'goal', 'context']
        
        # Collect memories from each type
        all_memories = {}
        for mem_type in memory_types:
            memory_obj = getattr(self.memory, f'{mem_type}_memory', None)
            if memory_obj:
                results = await memory_obj.search(query, 5)
                all_memories[mem_type] = results
        
        # Analyze patterns across memory types
        insights = self._analyze_cross_memory_patterns(all_memories)
        
        # Generate fusion score
        fusion_score = self._calculate_fusion_score(all_memories)
        
        return {
            'query': query,
            'memories_by_type': {k: len(v) for k, v in all_memories.items()},
            'insights': insights,
            'fusion_score': fusion_score,
            'timestamp': datetime.now().isoformat()
        }
    
    def _analyze_cross_memory_patterns(self, memories: Dict[str, List[MemoryEntry]]) -> List[str]:
        """Analyze patterns across different memory types"""
        insights = []
        
        # Check for goal-learning alignment
        if 'goal' in memories and 'learning' in memories:
            goal_content = [str(m.content) for m in memories['goal']]
            learning_content = [str(m.content) for m in memories['learning']]
            if any(g in l for g in goal_content for l in learning_content):
                insights.append("Goals align with recent learnings")
        
        # Check for context-episodic correlation
        if 'context' in memories and 'episodic' in memories:
            if len(memories['context']) > 0 and len(memories['episodic']) > 2:
                insights.append("Rich contextual information available for recent episodes")
        
        # Check for semantic-learning connection
        if 'semantic' in memories and 'learning' in memories:
            if len(memories['semantic']) > 3 and len(memories['learning']) > 1:
                insights.append("Strong knowledge base supports recent learnings")
        
        return insights
    
    def _calculate_fusion_score(self, memories: Dict[str, List[MemoryEntry]]) -> float:
        """Calculate fusion score based on memory diversity and relevance"""
        if not memories:
            return 0.0
        
        # Diversity score (how many memory types have results)
        diversity = len([k for k, v in memories.items() if v]) / len(memories)
        
        # Relevance score (average importance across all memories)
        all_entries = [m for entries in memories.values() for m in entries]
        if all_entries:
            avg_importance = sum(m.importance for m in all_entries) / len(all_entries)
        else:
            avg_importance = 0.0
        
        # Combined fusion score
        return (diversity * 0.4 + avg_importance * 0.6)


class TemporalDecayManager:
    """Manages temporal decay of memories"""
    
    def __init__(self, unified_memory: NexusUnifiedMemory):
        self.memory = unified_memory
        self.decay_rates = {
            'working': 0.1,      # Fast decay
            'episodic': 0.01,    # Medium decay
            'semantic': 0.001,   # Slow decay
            'persistent': 0.0    # No decay
        }
    
    async def apply_decay(self):
        """Apply temporal decay to all memories"""
        for memory_type, decay_rate in self.decay_rates.items():
            if decay_rate > 0:
                memory_obj = getattr(self.memory, f'{memory_type}_memory', None)
                if memory_obj and hasattr(memory_obj, 'apply_decay'):
                    await memory_obj.apply_decay(decay_rate)
    
    def calculate_decay_factor(self, timestamp: datetime, memory_type: str) -> float:
        """Calculate decay factor for a memory based on age"""
        age_days = (datetime.now() - timestamp).days
        decay_rate = self.decay_rates.get(memory_type, 0.01)
        return max(0.1, 1.0 - (age_days * decay_rate))


# Add background maintenance method to NexusUnifiedMemory
async def _background_maintenance(self):
    """Background maintenance tasks"""
    while True:
        try:
            # Run consolidation every interval
            await asyncio.sleep(self.config['consolidation']['interval_seconds'])
            await self.consolidate()
            
            # Apply temporal decay
            await self.decay_manager.apply_decay()
            
            # Log statistics
            stats = self.get_stats()
            logger.info(f"Memory stats: {stats['total_operations']} operations, "
                       f"health: {stats.get('health_score', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Error in background maintenance: {e}")
            await asyncio.sleep(60)  # Wait before retrying

# Patch the method into the class
NexusUnifiedMemory._background_maintenance = _background_maintenance


if __name__ == "__main__":
    # Run test
    asyncio.run(test_unified_memory())