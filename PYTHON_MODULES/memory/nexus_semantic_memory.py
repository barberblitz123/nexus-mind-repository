#!/usr/bin/env python3
"""
NEXUS Semantic Memory
Stage 3 of the 4-stage memory system

Knowledge graphs and vector storage using existing ChromaDB implementation
- Wraps the existing NexusVectorStore
- Adds unified memory interface
- Provides knowledge graph capabilities
- Enables cross-modal search
"""

import logging
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import numpy as np
from pathlib import Path

# Add the nexus-web-app directory to path to import NexusVectorStore
sys.path.append(os.path.join(os.path.dirname(__file__), 'nexus-web-app', 'context'))

from nexus_memory_types import MemoryEntry

logger = logging.getLogger('NEXUS-SemanticMemory')

# Try to import the existing ChromaDB implementation
try:
    from nexus_web_app.context.nexus_vector_store import NexusVectorStore
    CHROMADB_AVAILABLE = True
except ImportError:
    logger.warning("ChromaDB implementation not found. Semantic memory will use fallback mode.")
    CHROMADB_AVAILABLE = False
    NexusVectorStore = None


class SemanticMemory:
    """
    Stage 3: Knowledge graph and vector storage
    Wraps existing ChromaDB implementation with unified interface
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize semantic memory with configuration"""
        self.config = config
        self.chromadb_path = config.get('chromadb_path', './nexus_vectors')
        self.use_existing = config.get('use_existing', True)
        
        # Statistics
        self.stats = {
            'total_stored': 0,
            'total_searches': 0,
            'clusters_created': 0,
            'relationships_found': 0
        }
        
        # Initialize vector store if available
        if CHROMADB_AVAILABLE and self.use_existing:
            try:
                self.vector_store = NexusVectorStore(persist_directory=self.chromadb_path)
                logger.info(f"Semantic Memory initialized with ChromaDB at {self.chromadb_path}")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {e}")
                self.vector_store = None
        else:
            self.vector_store = None
            logger.warning("Semantic Memory running without ChromaDB backend")
        
        # Knowledge graph storage (simple in-memory for now)
        self.knowledge_graph = KnowledgeGraph()
    
    async def store(self, entry: MemoryEntry) -> bool:
        """Store memory entry in semantic memory"""
        try:
            # Convert MemoryEntry to format expected by ChromaDB
            text = self._entry_to_text(entry)
            metadata = self._prepare_metadata(entry)
            
            if self.vector_store:
                # Store in ChromaDB
                chunk_id = self.vector_store.add_conversation_chunk(
                    text=text,
                    metadata=metadata,
                    chunk_id=entry.id
                )
                
                # Extract and store concepts in knowledge graph
                concepts = self._extract_concepts(entry)
                for concept in concepts:
                    self.knowledge_graph.add_concept(concept, entry.id)
                
                # Find relationships between concepts
                self._update_concept_relationships(concepts)
                
                logger.debug(f"Stored {entry.id} in semantic memory")
            else:
                # Fallback storage
                logger.warning(f"ChromaDB not available, using fallback for {entry.id}")
            
            self.stats['total_stored'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error storing in semantic memory: {e}")
            return False
    
    async def get_by_id(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve specific memory by ID"""
        if not self.vector_store:
            return None
        
        try:
            # ChromaDB doesn't have direct ID lookup, so we search for exact match
            results = self.vector_store.semantic_search(
                query=f"id:{memory_id}",
                n_results=1
            )
            
            if results and results[0]['metadata'].get('memory_id') == memory_id:
                return self._chromadb_result_to_entry(results[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving from semantic memory: {e}")
            return None
    
    async def search(self, query: str, n_results: int = 10) -> List[MemoryEntry]:
        """Search semantic memory using vector similarity"""
        self.stats['total_searches'] += 1
        
        if not self.vector_store:
            return []
        
        try:
            # Use ChromaDB's semantic search
            results = self.vector_store.semantic_search(
                query=query,
                n_results=n_results,
                consciousness_boost=1.5  # Boost consciousness-related results
            )
            
            # Convert ChromaDB results to MemoryEntry objects
            entries = []
            for result in results:
                entry = self._chromadb_result_to_entry(result)
                if entry:
                    entries.append(entry)
            
            # Enhance with knowledge graph context
            entries = self._enhance_with_knowledge_graph(entries, query)
            
            return entries
            
        except Exception as e:
            logger.error(f"Error searching semantic memory: {e}")
            return []
    
    async def find_related(self, memory_id: str, n_results: int = 5) -> List[MemoryEntry]:
        """Find memories related to a given memory"""
        # Get the original memory
        original = await self.get_by_id(memory_id)
        if not original:
            return []
        
        # Search for similar content
        text = self._entry_to_text(original)
        related = await self.search(text, n_results + 1)
        
        # Remove the original from results
        related = [e for e in related if e.id != memory_id]
        
        return related[:n_results]
    
    async def get_concepts(self) -> Dict[str, List[str]]:
        """Get all concepts in the knowledge graph"""
        return self.knowledge_graph.get_all_concepts()
    
    async def get_concept_memories(self, concept: str, n_results: int = 10) -> List[MemoryEntry]:
        """Get memories associated with a specific concept"""
        memory_ids = self.knowledge_graph.get_concept_memories(concept, n_results)
        
        # Retrieve the actual memories
        memories = []
        for memory_id in memory_ids:
            entry = await self.get_by_id(memory_id)
            if entry:
                memories.append(entry)
        
        return memories
    
    async def cluster_memories(self) -> Dict[str, List[MemoryEntry]]:
        """Cluster similar memories"""
        if not self.vector_store:
            return {}
        
        try:
            # Use ChromaDB's clustering
            clusters = self.vector_store.cluster_conversations(min_samples=5)
            
            # Convert to MemoryEntry format
            result = {}
            for cluster_name, items in clusters.items():
                entries = []
                for item in items:
                    entry = self._chromadb_item_to_entry(item)
                    if entry:
                        entries.append(entry)
                
                if entries:
                    result[cluster_name] = entries
            
            self.stats['clusters_created'] = len(result)
            return result
            
        except Exception as e:
            logger.error(f"Error clustering memories: {e}")
            return {}
    
    def _entry_to_text(self, entry: MemoryEntry) -> str:
        """Convert MemoryEntry to text for ChromaDB"""
        # Combine content and important metadata into searchable text
        text_parts = []
        
        # Add content
        if isinstance(entry.content, str):
            text_parts.append(entry.content)
        else:
            text_parts.append(json.dumps(entry.content))
        
        # Add important metadata
        if entry.metadata.get('description'):
            text_parts.append(f"Description: {entry.metadata['description']}")
        
        if entry.metadata.get('tags'):
            text_parts.append(f"Tags: {', '.join(entry.metadata['tags'])}")
        
        return ' '.join(text_parts)
    
    def _prepare_metadata(self, entry: MemoryEntry) -> Dict[str, Any]:
        """Prepare metadata for ChromaDB storage"""
        metadata = entry.metadata.copy()
        
        # Add standard fields
        metadata.update({
            'memory_id': entry.id,
            'importance': entry.importance,
            'timestamp': entry.timestamp.isoformat(),
            'stage': 'semantic',
            'access_count': entry.access_count
        })
        
        # Ensure all values are JSON-serializable
        for key, value in metadata.items():
            if isinstance(value, datetime):
                metadata[key] = value.isoformat()
            elif not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                metadata[key] = str(value)
        
        return metadata
    
    def _chromadb_result_to_entry(self, result: Dict[str, Any]) -> Optional[MemoryEntry]:
        """Convert ChromaDB search result to MemoryEntry"""
        try:
            metadata = result['metadata']
            
            # Parse content
            content = result['text']
            try:
                # Try to parse as JSON first
                content = json.loads(content)
            except:
                # Keep as string if not JSON
                pass
            
            # Create MemoryEntry
            return MemoryEntry(
                id=metadata.get('memory_id', result.get('id', '')),
                content=content,
                metadata=metadata,
                importance=metadata.get('importance', 0.5),
                timestamp=datetime.fromisoformat(metadata['timestamp']) if 'timestamp' in metadata else datetime.now(),
                access_count=metadata.get('access_count', 0),
                stage='semantic'
            )
            
        except Exception as e:
            logger.error(f"Error converting ChromaDB result: {e}")
            return None
    
    def _chromadb_item_to_entry(self, item: Dict[str, Any]) -> Optional[MemoryEntry]:
        """Convert ChromaDB cluster item to MemoryEntry"""
        try:
            return MemoryEntry(
                id=item['id'],
                content=item['text'],
                metadata=item.get('metadata', {}),
                importance=item.get('metadata', {}).get('importance', 0.5),
                timestamp=datetime.fromisoformat(item['metadata']['timestamp']) if 'timestamp' in item.get('metadata', {}) else datetime.now(),
                stage='semantic'
            )
        except Exception as e:
            logger.error(f"Error converting ChromaDB item: {e}")
            return None
    
    def _extract_concepts(self, entry: MemoryEntry) -> List[str]:
        """Extract key concepts from memory entry"""
        concepts = []
        
        # Extract from content
        content_str = str(entry.content).lower()
        
        # Simple keyword extraction (could be enhanced with NLP)
        keywords = [
            'consciousness', 'memory', 'nexus', 'system', 'task',
            'error', 'success', 'learning', 'pattern', 'concept',
            'knowledge', 'understanding', 'intelligence', 'processing'
        ]
        
        for keyword in keywords:
            if keyword in content_str:
                concepts.append(keyword)
        
        # Extract from metadata tags
        if entry.metadata.get('tags'):
            concepts.extend(entry.metadata['tags'])
        
        # Extract from task type
        if entry.metadata.get('task_type'):
            concepts.append(f"task_{entry.metadata['task_type']}")
        
        return list(set(concepts))  # Remove duplicates
    
    def _update_concept_relationships(self, concepts: List[str]):
        """Update relationships between concepts"""
        # Create relationships between co-occurring concepts
        for i, concept1 in enumerate(concepts):
            for concept2 in concepts[i+1:]:
                self.knowledge_graph.add_relationship(concept1, concept2)
                self.stats['relationships_found'] += 1
    
    def _enhance_with_knowledge_graph(self, entries: List[MemoryEntry], query: str) -> List[MemoryEntry]:
        """Enhance search results with knowledge graph context"""
        # Extract concepts from query
        query_concepts = []
        for concept in self.knowledge_graph.concepts.keys():
            if concept in query.lower():
                query_concepts.append(concept)
        
        # Boost entries that share concepts with the query
        for entry in entries:
            entry_concepts = self._extract_concepts(entry)
            
            # Calculate concept overlap
            overlap = len(set(query_concepts).intersection(set(entry_concepts)))
            if overlap > 0:
                # Boost the relevance score
                entry.metadata['concept_boost'] = overlap * 0.1
                if 'combined_score' in entry.metadata:
                    entry.metadata['combined_score'] *= (1 + entry.metadata['concept_boost'])
        
        # Re-sort by updated scores
        entries.sort(key=lambda e: e.metadata.get('combined_score', 0), reverse=True)
        
        return entries
    
    def get_stats(self) -> Dict[str, Any]:
        """Get semantic memory statistics"""
        stats = {
            'total_stored': self.stats['total_stored'],
            'total_searches': self.stats['total_searches'],
            'clusters_created': self.stats['clusters_created'],
            'relationships_found': self.stats['relationships_found'],
            'total_concepts': len(self.knowledge_graph.concepts),
            'chromadb_available': CHROMADB_AVAILABLE and self.vector_store is not None
        }
        
        # Add ChromaDB stats if available
        if self.vector_store:
            try:
                chromadb_stats = self.vector_store.get_statistics()
                stats['chromadb_stats'] = chromadb_stats
            except:
                pass
        
        return stats


class KnowledgeGraph:
    """Simple knowledge graph for concept relationships"""
    
    def __init__(self):
        self.concepts: Dict[str, List[str]] = {}  # concept -> memory_ids
        self.relationships: Dict[Tuple[str, str], int] = {}  # (concept1, concept2) -> strength
    
    def add_concept(self, concept: str, memory_id: str):
        """Add a concept-memory association"""
        if concept not in self.concepts:
            self.concepts[concept] = []
        if memory_id not in self.concepts[concept]:
            self.concepts[concept].append(memory_id)
    
    def add_relationship(self, concept1: str, concept2: str, strength: int = 1):
        """Add or strengthen relationship between concepts"""
        # Ensure consistent ordering
        key = tuple(sorted([concept1, concept2]))
        
        if key in self.relationships:
            self.relationships[key] += strength
        else:
            self.relationships[key] = strength
    
    def get_concept_memories(self, concept: str, limit: int = 10) -> List[str]:
        """Get memory IDs associated with a concept"""
        return self.concepts.get(concept, [])[:limit]
    
    def get_related_concepts(self, concept: str, limit: int = 5) -> List[Tuple[str, int]]:
        """Get concepts related to the given concept"""
        related = []
        
        for (c1, c2), strength in self.relationships.items():
            if c1 == concept:
                related.append((c2, strength))
            elif c2 == concept:
                related.append((c1, strength))
        
        # Sort by strength
        related.sort(key=lambda x: x[1], reverse=True)
        
        return related[:limit]
    
    def get_all_concepts(self) -> Dict[str, List[str]]:
        """Get all concepts and their associated memories"""
        return self.concepts.copy()


# Test semantic memory
async def test_semantic_memory():
    """Test semantic memory functionality"""
    config = {
        'chromadb_path': './test_semantic_vectors',
        'use_existing': True
    }
    
    sm = SemanticMemory(config)
    
    # Test storing memories
    test_entries = []
    for i in range(5):
        entry = MemoryEntry(
            id=f"semantic_{i}",
            content=f"Test semantic memory {i}: This is about {'consciousness' if i % 2 == 0 else 'intelligence'} and {'nexus' if i % 3 == 0 else 'system'}",
            metadata={
                'index': i,
                'tags': ['test', 'semantic'],
                'task_type': 'analysis' if i % 2 == 0 else 'processing'
            },
            importance=0.5 + i * 0.1
        )
        test_entries.append(entry)
        success = await sm.store(entry)
        logger.info(f"Stored semantic_{i}: {success}")
    
    # Test search
    results = await sm.search("consciousness nexus", n_results=3)
    logger.info(f"Search results: {[r.id for r in results]}")
    
    # Test find related
    if test_entries:
        related = await sm.find_related(test_entries[0].id, n_results=2)
        logger.info(f"Related to {test_entries[0].id}: {[r.id for r in related]}")
    
    # Test concepts
    concepts = await sm.get_concepts()
    logger.info(f"Concepts in knowledge graph: {list(concepts.keys())}")
    
    # Test concept memories
    if concepts:
        concept = list(concepts.keys())[0]
        concept_memories = await sm.get_concept_memories(concept, n_results=3)
        logger.info(f"Memories for concept '{concept}': {[m.id for m in concept_memories]}")
    
    # Test clustering
    clusters = await sm.cluster_memories()
    logger.info(f"Found {len(clusters)} clusters")
    for cluster_name, memories in clusters.items():
        logger.info(f"  {cluster_name}: {len(memories)} memories")
    
    # Get stats
    stats = sm.get_stats()
    logger.info(f"Semantic memory stats: {json.dumps(stats, indent=2)}")
    
    return sm


if __name__ == "__main__":
    # Run test
    logging.basicConfig(level=logging.DEBUG)
    import asyncio
    asyncio.run(test_semantic_memory())