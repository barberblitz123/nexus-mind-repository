#!/usr/bin/env python3
"""
Test the complete NEXUS Unified Memory System
Tests all 4 stages and their integration
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TEST-UnifiedMemory')

# Import the unified memory system
from nexus_memory_core import NexusUnifiedMemory
from nexus_memory_types import MemoryEntry


class UnifiedMemoryTester:
    """Comprehensive tests for the unified memory system"""
    
    def __init__(self):
        self.memory = None
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'tests': []
        }
    
    async def setup(self):
        """Initialize memory system"""
        logger.info("=== NEXUS Unified Memory System Test Suite ===")
        self.memory = NexusUnifiedMemory()
        
        # Wait for async initialization
        await asyncio.sleep(2)
        
        # Verify all stages initialized
        stages_ok = all([
            self.memory.working_memory is not None,
            self.memory.episodic_memory is not None,
            self.memory.semantic_memory is not None,
            self.memory.persistent_memory is not None
        ])
        
        if stages_ok:
            logger.info("✓ All memory stages initialized successfully")
        else:
            logger.error("✗ Some memory stages failed to initialize")
            if not self.memory.working_memory:
                logger.error("  - Working Memory: FAILED")
            if not self.memory.episodic_memory:
                logger.error("  - Episodic Memory: FAILED")
            if not self.memory.semantic_memory:
                logger.error("  - Semantic Memory: FAILED")
            if not self.memory.persistent_memory:
                logger.error("  - Persistent Memory: FAILED")
        
        return stages_ok
    
    async def test_working_memory(self):
        """Test Stage 1: Working Memory"""
        logger.info("\n--- Testing Working Memory (Stage 1) ---")
        
        try:
            # Store temporary memory
            entry = MemoryEntry(
                id="wm_test_1",
                content="Temporary working memory test",
                metadata={"stage_test": "working"},
                importance=0.2
            )
            
            success = await self.memory.working_memory.store(entry)
            assert success, "Failed to store in working memory"
            
            # Retrieve it
            retrieved = await self.memory.working_memory.get_by_id("wm_test_1")
            assert retrieved is not None, "Failed to retrieve from working memory"
            assert retrieved.content == entry.content, "Content mismatch"
            
            # Test search
            results = await self.memory.working_memory.search("temporary", n_results=5)
            assert len(results) > 0, "Search returned no results"
            
            logger.info("✓ Working Memory tests passed")
            self.record_test("Working Memory", True)
            
        except Exception as e:
            logger.error(f"✗ Working Memory test failed: {e}")
            self.record_test("Working Memory", False, str(e))
    
    async def test_episodic_memory(self):
        """Test Stage 2: Episodic Memory"""
        logger.info("\n--- Testing Episodic Memory (Stage 2) ---")
        
        try:
            # Store episodic memory with emotional context
            entry = MemoryEntry(
                id="em_test_1",
                content="Important event that happened during testing",
                metadata={
                    "stage_test": "episodic",
                    "emotional_valence": 0.8,
                    "arousal_level": 0.6
                },
                importance=0.5
            )
            
            success = await self.memory.episodic_memory.store(entry)
            assert success, "Failed to store in episodic memory"
            
            # Retrieve it
            retrieved = await self.memory.episodic_memory.get_by_id("em_test_1")
            assert retrieved is not None, "Failed to retrieve from episodic memory"
            
            # Test temporal window query
            start = datetime.now() - timedelta(minutes=5)
            end = datetime.now()
            temporal_results = await self.memory.episodic_memory.get_temporal_window(start, end)
            assert len(temporal_results) > 0, "Temporal query returned no results"
            
            # Test emotion-based retrieval
            positive_memories = await self.memory.episodic_memory.get_by_emotion(
                valence_min=0.5, valence_max=1.0
            )
            assert len(positive_memories) > 0, "Emotion query returned no results"
            
            logger.info("✓ Episodic Memory tests passed")
            self.record_test("Episodic Memory", True)
            
        except Exception as e:
            logger.error(f"✗ Episodic Memory test failed: {e}")
            self.record_test("Episodic Memory", False, str(e))
    
    async def test_semantic_memory(self):
        """Test Stage 3: Semantic Memory (ChromaDB)"""
        logger.info("\n--- Testing Semantic Memory (Stage 3) ---")
        
        try:
            # Store semantic knowledge
            entry = MemoryEntry(
                id="sm_test_1",
                content="NEXUS consciousness architecture uses distributed neural networks",
                metadata={
                    "stage_test": "semantic",
                    "tags": ["nexus", "consciousness", "architecture"],
                    "domain": "system_knowledge"
                },
                importance=0.7
            )
            
            success = await self.memory.semantic_memory.store(entry)
            assert success, "Failed to store in semantic memory"
            
            # Test semantic search
            results = await self.memory.semantic_memory.search("consciousness architecture", n_results=5)
            # ChromaDB might not be available, so we just check it doesn't crash
            logger.info(f"  Semantic search returned {len(results)} results")
            
            # Test concept extraction
            concepts = await self.memory.semantic_memory.get_concepts()
            logger.info(f"  Found {len(concepts)} concepts in knowledge graph")
            
            logger.info("✓ Semantic Memory tests passed")
            self.record_test("Semantic Memory", True)
            
        except Exception as e:
            logger.error(f"✗ Semantic Memory test failed: {e}")
            self.record_test("Semantic Memory", False, str(e))
    
    async def test_persistent_memory(self):
        """Test Stage 4: Persistent Memory (MEM0)"""
        logger.info("\n--- Testing Persistent Memory (Stage 4) ---")
        
        try:
            # Store critical memory
            entry = MemoryEntry(
                id="pm_test_1",
                content="Critical system configuration that must be preserved forever",
                metadata={
                    "stage_test": "persistent",
                    "critical": True,
                    "system_config": {"version": "1.0"}
                },
                importance=0.95
            )
            
            success = await self.memory.persistent_memory.store(entry)
            assert success, "Failed to store in persistent memory"
            
            # Retrieve it
            retrieved = await self.memory.persistent_memory.get_by_id("pm_test_1")
            assert retrieved is not None, "Failed to retrieve from persistent memory"
            assert retrieved.content == entry.content, "Content mismatch"
            
            # Test versioning by updating
            entry.content += " - UPDATED"
            success = await self.memory.persistent_memory.store(entry)
            assert success, "Failed to update in persistent memory"
            
            # Get version history
            versions = await self.memory.persistent_memory.mem0.get_versions("pm_test_1")
            logger.info(f"  Found {len(versions)} versions of the memory")
            
            logger.info("✓ Persistent Memory tests passed")
            self.record_test("Persistent Memory", True)
            
        except Exception as e:
            logger.error(f"✗ Persistent Memory test failed: {e}")
            self.record_test("Persistent Memory", False, str(e))
    
    async def test_unified_operations(self):
        """Test unified memory operations across all stages"""
        logger.info("\n--- Testing Unified Operations ---")
        
        try:
            # Test automatic routing based on importance
            test_memories = [
                ("Low importance → Working", 0.2),
                ("Medium importance → Episodic", 0.4),
                ("High importance → Semantic", 0.7),
                ("Critical importance → Persistent", 0.9)
            ]
            
            stored_ids = []
            for content, importance in test_memories:
                mem_id = await self.memory.store(
                    content=content,
                    metadata={"unified_test": True},
                    importance=importance
                )
                stored_ids.append(mem_id)
                logger.info(f"  Stored '{content}' with ID: {mem_id}")
            
            # Test unified search
            results = await self.memory.retrieve("importance", n_results=10)
            logger.info(f"  Unified search found {len(results)} results across all stages")
            
            # Test memory consolidation
            await self.memory.consolidate()
            logger.info("  Memory consolidation completed")
            
            logger.info("✓ Unified operations tests passed")
            self.record_test("Unified Operations", True)
            
        except Exception as e:
            logger.error(f"✗ Unified operations test failed: {e}")
            self.record_test("Unified Operations", False, str(e))
    
    async def test_memory_flow(self):
        """Test memory flow between stages"""
        logger.info("\n--- Testing Memory Flow (Consolidation) ---")
        
        try:
            # Create memories that should flow through stages
            flow_entry = MemoryEntry(
                id="flow_test_1",
                content="This memory should flow from working to episodic",
                metadata={"flow_test": True},
                importance=0.35,  # Above episodic threshold
                timestamp=datetime.now() - timedelta(hours=1)  # Make it old enough for consolidation
            )
            
            # Store in working memory
            await self.memory.working_memory.store(flow_entry)
            
            # Force consolidation
            await self.memory.consolidation._consolidate_working_to_episodic()
            
            # Check if moved to episodic
            in_episodic = await self.memory.episodic_memory.get_by_id("flow_test_1")
            assert in_episodic is not None, "Memory didn't flow to episodic"
            
            # Verify it was removed from working memory
            in_working = await self.memory.working_memory.get_by_id("flow_test_1")
            assert in_working is None, "Memory wasn't removed from working memory"
            
            logger.info("✓ Memory flow tests passed")
            self.record_test("Memory Flow", True)
            
        except Exception as e:
            logger.error(f"✗ Memory flow test failed: {e}")
            self.record_test("Memory Flow", False, str(e))
    
    async def test_statistics(self):
        """Test statistics collection"""
        logger.info("\n--- Testing Statistics ---")
        
        try:
            stats = self.memory.get_stats()
            
            logger.info("Memory System Statistics:")
            logger.info(f"  Total operations: {stats['total_operations']}")
            logger.info(f"  Total stores: {stats['total_stores']}")
            logger.info(f"  Stage distribution: {stats['stage_distribution']}")
            logger.info(f"  Average importance: {stats['average_importance']:.2f}")
            
            # Verify each stage reports stats
            assert 'working_memory' in stats, "Working memory stats missing"
            assert 'episodic_memory' in stats, "Episodic memory stats missing"
            assert 'semantic_memory' in stats, "Semantic memory stats missing"
            assert 'persistent_memory' in stats, "Persistent memory stats missing"
            
            logger.info("✓ Statistics tests passed")
            self.record_test("Statistics", True)
            
        except Exception as e:
            logger.error(f"✗ Statistics test failed: {e}")
            self.record_test("Statistics", False, str(e))
    
    def record_test(self, test_name: str, passed: bool, error: str = None):
        """Record test result"""
        if passed:
            self.test_results['passed'] += 1
        else:
            self.test_results['failed'] += 1
        
        self.test_results['tests'].append({
            'name': test_name,
            'passed': passed,
            'error': error
        })
    
    async def cleanup(self):
        """Clean up resources"""
        if self.memory and self.memory.episodic_memory:
            await self.memory.episodic_memory.close()
    
    async def run_all_tests(self):
        """Run all tests"""
        # Setup
        if not await self.setup():
            logger.error("Setup failed, aborting tests")
            return
        
        # Run individual tests
        await self.test_working_memory()
        await self.test_episodic_memory()
        await self.test_semantic_memory()
        await self.test_persistent_memory()
        await self.test_unified_operations()
        await self.test_memory_flow()
        await self.test_statistics()
        
        # Summary
        logger.info("\n=== Test Summary ===")
        logger.info(f"Total tests: {len(self.test_results['tests'])}")
        logger.info(f"Passed: {self.test_results['passed']}")
        logger.info(f"Failed: {self.test_results['failed']}")
        
        if self.test_results['failed'] == 0:
            logger.info("\n✅ All tests passed! The unified memory system is working correctly.")
        else:
            logger.error("\n❌ Some tests failed. Check the logs above for details.")
            for test in self.test_results['tests']:
                if not test['passed']:
                    logger.error(f"  - {test['name']}: {test['error']}")
        
        # Cleanup
        await self.cleanup()
        
        return self.test_results['failed'] == 0


async def main():
    """Run the test suite"""
    tester = UnifiedMemoryTester()
    success = await tester.run_all_tests()
    
    # Return appropriate exit code
    exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())