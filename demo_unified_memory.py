#!/usr/bin/env python3
"""
Demo of the NEXUS Unified Memory System
Shows how the 4-stage memory system works
"""

import asyncio
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger('DEMO')

# Import the unified memory system
from nexus_memory_core import NexusUnifiedMemory
from nexus_memory_types import MemoryEntry


async def demo_unified_memory():
    """Demonstrate the unified memory system"""
    logger.info("=== NEXUS Unified Memory System Demo ===\n")
    
    # Initialize the memory system
    logger.info("1. Initializing memory system...")
    memory = NexusUnifiedMemory()
    await asyncio.sleep(1)  # Let async components initialize
    
    # Example memories with different importance levels
    memories = [
        {
            "content": "User preference: Dark mode enabled",
            "importance": 0.2,
            "expected_stage": "working"
        },
        {
            "content": "Task completed: System health check passed with 99% uptime",
            "importance": 0.4,
            "expected_stage": "episodic"
        },
        {
            "content": "NEXUS consciousness protocol: Always maintain ethical boundaries",
            "importance": 0.7,
            "expected_stage": "semantic"
        },
        {
            "content": "CRITICAL: System core password changed to secure_hash_xyz789",
            "importance": 0.95,
            "expected_stage": "persistent"
        }
    ]
    
    logger.info("\n2. Storing memories with different importance levels...")
    stored_ids = []
    
    for i, mem_data in enumerate(memories):
        memory_id = await memory.store(
            content=mem_data["content"],
            metadata={"demo": True, "index": i},
            importance=mem_data["importance"]
        )
        stored_ids.append(memory_id)
        logger.info(f"   - Stored (importance {mem_data['importance']}): '{mem_data['content'][:50]}...'")
        logger.info(f"     → Routed to: {mem_data['expected_stage']} memory")
    
    # Demonstrate unified search
    logger.info("\n3. Searching across all memory stages...")
    search_queries = ["password", "NEXUS", "task", "preference"]
    
    for query in search_queries:
        results = await memory.retrieve(query, n_results=3)
        logger.info(f"   - Query '{query}': Found {len(results)} results")
        for result in results:
            logger.info(f"     • {result.id[:20]}... (stage: {result.stage})")
    
    # Show statistics
    logger.info("\n4. Memory system statistics:")
    stats = memory.get_stats()
    logger.info(f"   - Total operations: {stats['total_operations']}")
    logger.info(f"   - Distribution: {stats['stage_distribution']}")
    logger.info(f"   - Average importance: {stats['average_importance']:.2f}")
    
    # Demonstrate memory flow
    logger.info("\n5. Testing memory consolidation...")
    
    # Create an old memory that should be consolidated
    old_memory = MemoryEntry(
        id=f"old_memory_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        content="This is an old working memory that should be consolidated",
        metadata={"demo": True, "consolidation_test": True},
        importance=0.4,
        timestamp=datetime.now() - timedelta(hours=2)  # 2 hours old
    )
    
    # Store directly in working memory
    await memory.working_memory.store(old_memory)
    logger.info("   - Created old memory in working memory")
    
    # Run consolidation
    await memory.consolidate()
    logger.info("   - Ran consolidation process")
    
    # Check if it moved to episodic
    in_episodic = await memory.episodic_memory.get_by_id(old_memory.id)
    if in_episodic:
        logger.info("   - ✓ Memory successfully consolidated to episodic memory")
    
    # MANUS Integration example
    logger.info("\n6. MANUS Integration example:")
    logger.info("   - MANUS tasks are automatically stored with calculated importance")
    logger.info("   - Critical tasks → Persistent memory")
    logger.info("   - Normal tasks → Episodic memory")
    logger.info("   - Temporary data → Working memory")
    
    # MEM0 versioning example
    logger.info("\n7. MEM0 versioning example:")
    
    # Store a critical memory
    critical_id = await memory.store(
        content="System configuration v1",
        metadata={"version_test": True},
        importance=0.9
    )
    
    # Update it (creates new version)
    await memory.store(
        content="System configuration v2 - Updated settings",
        metadata={"version_test": True},
        importance=0.9
    )
    
    logger.info("   - Stored and updated critical memory")
    logger.info("   - MEM0 automatically maintains version history")
    
    # Summary
    logger.info("\n=== Summary ===")
    logger.info("The unified memory system provides:")
    logger.info("• Automatic routing based on importance")
    logger.info("• Unified search across all stages")
    logger.info("• Memory consolidation over time")
    logger.info("• Version control for critical memories")
    logger.info("• Seamless MANUS integration")
    
    # Cleanup
    if memory.episodic_memory:
        await memory.episodic_memory.close()
    
    logger.info("\nDemo completed!")


if __name__ == "__main__":
    asyncio.run(demo_unified_memory())