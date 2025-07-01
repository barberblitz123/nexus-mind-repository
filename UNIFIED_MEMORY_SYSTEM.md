# NEXUS Unified Memory System

## Overview

The NEXUS Unified Memory System is a sophisticated 4-stage memory architecture that provides intelligent, persistent memory capabilities for NEXUS and MANUS. It's designed to mimic human memory systems with automatic consolidation and intelligent routing.

## 4-Stage Architecture

### Stage 1: Working Memory (RAM)
- **Purpose**: Fast, temporary storage for active processing
- **Capacity**: 512MB default (configurable)
- **TTL**: 1 hour default
- **Features**:
  - LRU eviction policy
  - Sub-millisecond access
  - Thread-safe operations
  - Automatic cleanup

### Stage 2: Episodic Memory (SQLite)
- **Purpose**: Recent experiences with temporal context
- **Capacity**: 100,000 episodes default
- **Features**:
  - Temporal indexing
  - Emotional tagging
  - Experience replay
  - Significance scoring
  - Automatic consolidation

### Stage 3: Semantic Memory (ChromaDB)
- **Purpose**: Knowledge graphs and vector storage
- **Features**:
  - Semantic search
  - Consciousness-aware retrieval
  - Concept relationships
  - Clustering capabilities
  - Uses existing ChromaDB implementation

### Stage 4: Persistent Memory (MEM0)
- **Purpose**: Forever storage for critical memories
- **Features**:
  - Encryption at rest
  - Compression (zstd)
  - Versioning support
  - Redundant storage
  - Blockchain-inspired immutability

## Memory Flow

```
New Memory → Working Memory → Episodic Memory → Semantic Memory → Persistent Memory (MEM0)
           ↑                                                                         ↓
           ←───────────────────────── Retrieval ←────────────────────────────────←
```

### Automatic Routing
Memories are automatically routed based on importance:
- **0.0-0.3**: Working memory only
- **0.3-0.6**: Promoted to episodic memory
- **0.6-0.8**: Consolidated to semantic memory
- **0.8-1.0**: Archived to persistent memory (MEM0)

## Installation

### Prerequisites
```bash
pip install aiosqlite chromadb sentence-transformers zstandard cryptography
```

### Quick Start
```python
from nexus_memory_core import NexusUnifiedMemory

# Initialize
memory = NexusUnifiedMemory()

# Store a memory
memory_id = await memory.store(
    content="Important system configuration",
    metadata={"type": "config", "critical": True},
    importance=0.9  # Will go to persistent storage
)

# Retrieve memories
results = await memory.retrieve("system configuration", n_results=5)
```

## Configuration

Edit `nexus_memory_config.json` to customize:

```json
{
    "working_memory": {
        "max_size_mb": 512,
        "ttl_seconds": 3600
    },
    "episodic_memory": {
        "max_episodes": 100000
    },
    "semantic_memory": {
        "chromadb_path": "./nexus_vectors"
    },
    "mem0": {
        "encryption": true,
        "compression": "zstd"
    }
}
```

## MANUS Integration

The unified memory system is fully integrated with MANUS:

```python
from manus_nexus_integration import NEXUSPoweredMANUS

# Create MANUS with unified memory
nexus_manus = NEXUSPoweredMANUS()
await nexus_manus.start()

# Tasks are automatically stored in memory
result = await nexus_manus.think_and_execute("Analyze system performance")

# Retrieve task memories
memories = await nexus_manus.retrieve_task_memories("performance analysis")
```

## Web Interface

The MANUS web interface displays real-time memory statistics:
- Total operations and average importance
- Memory distribution across stages
- Stage-specific metrics
- Storage utilization

Access at: http://localhost:8001

## API Endpoints

### Memory Statistics
```
GET /api/memory/unified-stats
```

Returns comprehensive memory system statistics.

### Legacy Support
The system maintains backward compatibility with:
- `/api/nexus/memory-dna` - Original NEXUS memory DNA
- Existing ChromaDB implementations

## Advanced Features

### Memory Consolidation
Automatic consolidation runs every 5 minutes (configurable):
- Moves old working memories to episodic
- Extracts patterns from episodic to semantic
- Archives critical semantic memories to MEM0

### Versioning
MEM0 supports memory versioning:
```python
# Update existing memory
await memory.store(updated_content, importance=0.9)

# Retrieve specific version
old_version = await memory.persistent_memory.mem0.retrieve(memory_id, version=1)
```

### Search Capabilities
Unified search across all stages:
```python
# Searches all memory stages in parallel
results = await memory.retrieve("consciousness", n_results=10)
```

## Performance

- **Working Memory**: < 1ms access time
- **Episodic Memory**: < 10ms for most queries
- **Semantic Memory**: < 100ms with vector search
- **Persistent Memory**: < 50ms with caching

## Troubleshooting

### ChromaDB Not Available
If ChromaDB is not installed, semantic memory runs in fallback mode with limited functionality.

### Memory Not Persisting
Check that:
1. Importance scores are set correctly
2. Consolidation is enabled in config
3. Database paths are writable

### High Memory Usage
Adjust `working_memory.max_size_mb` in configuration.

## Architecture Benefits

1. **Human-like Memory**: Mimics human memory consolidation
2. **Intelligent Routing**: Automatic importance-based storage
3. **Fault Tolerance**: Redundant storage in MEM0
4. **Scalability**: Can handle millions of memories
5. **Security**: Encryption for sensitive memories
6. **Performance**: Optimized for different access patterns

## Future Enhancements

- Distributed MEM0 storage
- Neural network-based importance scoring
- Cross-instance memory synchronization
- Advanced emotion modeling
- Quantum memory entanglement

## Contributing

The unified memory system is part of the NEXUS ecosystem. Contributions should maintain:
- The 4-stage architecture
- Backward compatibility
- Performance characteristics
- Security features

---

For more information, see the NEXUS Core Technical Specification.