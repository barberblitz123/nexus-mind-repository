#!/usr/bin/env python3
"""
NEXUS Working Memory
Stage 1 of the 4-stage memory system

Fast, temporary storage for active consciousness processing
- In-memory storage with configurable size limits
- LRU (Least Recently Used) eviction policy
- TTL (Time To Live) support
- Thread-safe operations
"""

import asyncio
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import sys
from threading import Lock

from nexus_memory_types import MemoryEntry

logger = logging.getLogger('NEXUS-WorkingMemory')


class WorkingMemory:
    """
    Stage 1: Active consciousness processing
    Provides ultra-fast access to recent memories
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize working memory with configuration"""
        self.config = config
        self.max_size_bytes = config.get('max_size_mb', 512) * 1024 * 1024
        self.ttl_seconds = config.get('ttl_seconds', 3600)
        self.eviction_policy = config.get('eviction_policy', 'lru')
        
        # Storage structures
        self.memory_store: OrderedDict[str, MemoryEntry] = OrderedDict()
        self.memory_sizes: Dict[str, int] = {}
        self.total_size = 0
        
        # Thread safety
        self.lock = Lock()
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expired': 0,
            'total_stored': 0
        }
        
        logger.info(f"Working Memory initialized: {self.max_size_bytes / 1024 / 1024:.1f}MB, TTL: {self.ttl_seconds}s")
    
    async def store(self, entry: MemoryEntry) -> bool:
        """
        Store memory entry in working memory
        Returns True if stored successfully
        """
        with self.lock:
            # Calculate entry size
            entry_size = self._calculate_size(entry)
            
            # Check if entry is too large
            if entry_size > self.max_size_bytes:
                logger.warning(f"Entry {entry.id} too large ({entry_size} bytes)")
                return False
            
            # Make room if needed
            while self.total_size + entry_size > self.max_size_bytes:
                if not self._evict_one():
                    logger.error("Cannot make room for new entry")
                    return False
            
            # Store the entry
            self.memory_store[entry.id] = entry
            self.memory_sizes[entry.id] = entry_size
            self.total_size += entry_size
            
            # Move to end (most recently used)
            self.memory_store.move_to_end(entry.id)
            
            self.stats['total_stored'] += 1
            
            logger.debug(f"Stored {entry.id} in working memory ({entry_size} bytes)")
            return True
    
    async def get_by_id(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve memory by ID"""
        with self.lock:
            # Check if exists
            if memory_id not in self.memory_store:
                self.stats['misses'] += 1
                return None
            
            entry = self.memory_store[memory_id]
            
            # Check if expired
            if self._is_expired(entry):
                self._remove_entry(memory_id)
                self.stats['expired'] += 1
                self.stats['misses'] += 1
                return None
            
            # Update access time and move to end
            entry.last_accessed = datetime.now()
            entry.access_count += 1
            self.memory_store.move_to_end(memory_id)
            
            self.stats['hits'] += 1
            return entry
    
    async def search(self, query: str, n_results: int = 10) -> List[MemoryEntry]:
        """
        Search working memory for matching entries
        Simple keyword-based search
        """
        results = []
        query_lower = query.lower()
        
        with self.lock:
            # Search through all entries
            for memory_id, entry in list(self.memory_store.items()):
                # Skip expired entries
                if self._is_expired(entry):
                    self._remove_entry(memory_id)
                    continue
                
                # Simple content matching
                content_str = str(entry.content).lower()
                if query_lower in content_str:
                    results.append(entry)
                    
                    # Update access
                    entry.last_accessed = datetime.now()
                    entry.access_count += 1
                    self.memory_store.move_to_end(memory_id)
                    
                    if len(results) >= n_results:
                        break
            
            # Also check metadata
            if len(results) < n_results:
                for memory_id, entry in list(self.memory_store.items()):
                    if entry in results:
                        continue
                    
                    # Check metadata
                    metadata_str = str(entry.metadata).lower()
                    if query_lower in metadata_str:
                        results.append(entry)
                        
                        # Update access
                        entry.last_accessed = datetime.now()
                        entry.access_count += 1
                        self.memory_store.move_to_end(memory_id)
                        
                        if len(results) >= n_results:
                            break
        
        return results
    
    async def get_all_for_consolidation(self) -> List[MemoryEntry]:
        """
        Get all entries eligible for consolidation
        Returns entries that are old enough but not expired
        """
        eligible = []
        consolidation_age = timedelta(seconds=self.ttl_seconds / 3)  # 1/3 of TTL
        
        with self.lock:
            current_time = datetime.now()
            
            for memory_id, entry in list(self.memory_store.items()):
                # Skip if expired
                if self._is_expired(entry):
                    self._remove_entry(memory_id)
                    continue
                
                # Check if old enough for consolidation
                age = current_time - entry.timestamp
                if age > consolidation_age:
                    eligible.append(entry)
        
        return eligible
    
    async def remove(self, memory_id: str) -> bool:
        """Remove specific entry from working memory"""
        with self.lock:
            if memory_id in self.memory_store:
                self._remove_entry(memory_id)
                return True
            return False
    
    def _calculate_size(self, entry: MemoryEntry) -> int:
        """Calculate approximate size of memory entry in bytes"""
        # Rough estimation
        size = sys.getsizeof(entry.id)
        size += sys.getsizeof(entry.content)
        size += sys.getsizeof(entry.metadata)
        size += sys.getsizeof(entry.importance)
        size += sys.getsizeof(entry.timestamp)
        size += 100  # Overhead
        
        return size
    
    def _is_expired(self, entry: MemoryEntry) -> bool:
        """Check if entry has expired based on TTL"""
        age = datetime.now() - entry.timestamp
        return age.total_seconds() > self.ttl_seconds
    
    def _evict_one(self) -> bool:
        """
        Evict one entry based on eviction policy
        Returns True if an entry was evicted
        """
        if not self.memory_store:
            return False
        
        if self.eviction_policy == 'lru':
            # Remove least recently used (first in OrderedDict)
            memory_id = next(iter(self.memory_store))
        elif self.eviction_policy == 'lfu':
            # Remove least frequently used
            memory_id = min(
                self.memory_store.keys(),
                key=lambda k: self.memory_store[k].access_count
            )
        elif self.eviction_policy == 'fifo':
            # Remove oldest
            memory_id = min(
                self.memory_store.keys(),
                key=lambda k: self.memory_store[k].timestamp
            )
        else:
            # Default to LRU
            memory_id = next(iter(self.memory_store))
        
        self._remove_entry(memory_id)
        self.stats['evictions'] += 1
        logger.debug(f"Evicted {memory_id} from working memory")
        return True
    
    def _remove_entry(self, memory_id: str):
        """Remove entry and update size tracking"""
        if memory_id in self.memory_store:
            del self.memory_store[memory_id]
            
            if memory_id in self.memory_sizes:
                self.total_size -= self.memory_sizes[memory_id]
                del self.memory_sizes[memory_id]
    
    async def cleanup_expired(self):
        """Remove all expired entries"""
        with self.lock:
            expired_ids = []
            
            for memory_id, entry in self.memory_store.items():
                if self._is_expired(entry):
                    expired_ids.append(memory_id)
            
            for memory_id in expired_ids:
                self._remove_entry(memory_id)
                self.stats['expired'] += 1
            
            if expired_ids:
                logger.info(f"Cleaned up {len(expired_ids)} expired entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get working memory statistics"""
        with self.lock:
            total_entries = len(self.memory_store)
            
            # Calculate hit rate
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0
            
            # Get age distribution
            if self.memory_store:
                ages = [(datetime.now() - entry.timestamp).total_seconds() 
                       for entry in self.memory_store.values()]
                avg_age = sum(ages) / len(ages)
                oldest_age = max(ages)
            else:
                avg_age = 0
                oldest_age = 0
            
            return {
                'total_entries': total_entries,
                'total_size_mb': self.total_size / 1024 / 1024,
                'max_size_mb': self.max_size_bytes / 1024 / 1024,
                'utilization': self.total_size / self.max_size_bytes,
                'hit_rate': hit_rate,
                'stats': self.stats.copy(),
                'average_age_seconds': avg_age,
                'oldest_age_seconds': oldest_age,
                'ttl_seconds': self.ttl_seconds,
                'eviction_policy': self.eviction_policy
            }
    
    async def get_memory_pressure(self) -> float:
        """
        Get current memory pressure (0.0 to 1.0)
        Used for consolidation decisions
        """
        with self.lock:
            return self.total_size / self.max_size_bytes


# Cleanup task for expired entries
async def cleanup_task(working_memory: WorkingMemory, interval: int = 300):
    """Periodically clean up expired entries"""
    while True:
        await asyncio.sleep(interval)
        await working_memory.cleanup_expired()


# Test working memory
async def test_working_memory():
    """Test working memory functionality"""
    config = {
        'max_size_mb': 10,
        'ttl_seconds': 60,
        'eviction_policy': 'lru'
    }
    
    wm = WorkingMemory(config)
    
    # Test storing entries
    test_entries = []
    for i in range(5):
        entry = MemoryEntry(
            id=f"test_{i}",
            content=f"Test content {i}: " + "x" * 1000,
            metadata={'index': i},
            importance=0.5 + i * 0.1
        )
        test_entries.append(entry)
        success = await wm.store(entry)
        logger.info(f"Stored test_{i}: {success}")
    
    # Test retrieval
    entry = await wm.get_by_id("test_2")
    logger.info(f"Retrieved: {entry.id if entry else 'Not found'}")
    
    # Test search
    results = await wm.search("content", n_results=3)
    logger.info(f"Search results: {[r.id for r in results]}")
    
    # Test consolidation eligibility
    eligible = await wm.get_all_for_consolidation()
    logger.info(f"Eligible for consolidation: {[e.id for e in eligible]}")
    
    # Get stats
    stats = wm.get_stats()
    logger.info(f"Working memory stats: {stats}")
    
    # Test memory pressure
    pressure = await wm.get_memory_pressure()
    logger.info(f"Memory pressure: {pressure:.2%}")
    
    return wm


if __name__ == "__main__":
    # Run test
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(test_working_memory())