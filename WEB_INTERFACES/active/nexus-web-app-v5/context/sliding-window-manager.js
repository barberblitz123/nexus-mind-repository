/**
 * SLIDING WINDOW MANAGER
 * Efficient management of 1M token contexts with sliding window architecture
 * 
 * Features:
 * - 10k token chunks for optimal processing
 * - Continuity preservation between chunks
 * - Memory-optimized data structures
 * - Automatic garbage collection
 * - Session export/import capabilities
 */

class SlidingWindowManager {
    constructor(config = {}) {
        this.config = {
            maxTokens: 1000000,              // 1M total capacity
            activeWindowSize: 100000,         // 100k active window
            chunkSize: 10000,                // 10k tokens per chunk
            overlapSize: 500,                // Overlap between chunks for continuity
            maxChunksInMemory: 20,           // Max chunks to keep in memory
            gcThreshold: 0.9,                // Trigger GC at 90% capacity
            ...config
        };

        // Core data structures
        this.chunks = new Map();              // chunk_id -> chunk data
        this.chunkOrder = [];                 // Ordered list of chunk IDs
        this.activeChunks = new Set();        // Currently active chunk IDs
        this.chunkIndex = new Map();          // token_position -> chunk_id
        this.continuityMap = new Map();       // chunk_id -> next_chunk_id
        
        // Statistics
        this.stats = {
            totalTokens: 0,
            activeTokens: 0,
            chunkCount: 0,
            gcRuns: 0,
            compressionRatio: 1.0
        };

        // Memory management
        this.memoryPressure = false;
        this.lastGC = Date.now();
        
        // Initialize garbage collector
        this.setupGarbageCollector();
    }

    /**
     * Add tokens to the sliding window
     */
    addTokens(tokens, metadata = {}) {
        const tokenCount = tokens.length;
        
        // Check if we need to slide the window
        if (this.stats.activeTokens + tokenCount > this.config.activeWindowSize) {
            this.slideWindow(tokenCount);
        }

        // Create chunks from tokens
        const chunks = this.createChunks(tokens, metadata);
        
        // Add chunks to the system
        for (const chunk of chunks) {
            this.addChunk(chunk);
        }

        // Update statistics
        this.stats.totalTokens += tokenCount;
        this.stats.activeTokens += tokenCount;

        // Check memory pressure
        this.checkMemoryPressure();

        return chunks.map(c => c.id);
    }

    /**
     * Create chunks from tokens with overlap for continuity
     */
    createChunks(tokens, metadata) {
        const chunks = [];
        const chunkSize = this.config.chunkSize;
        const overlapSize = this.config.overlapSize;
        
        for (let i = 0; i < tokens.length; i += chunkSize - overlapSize) {
            const chunkTokens = tokens.slice(i, i + chunkSize);
            const previousOverlap = i > 0 ? tokens.slice(i - overlapSize, i) : [];
            const nextOverlap = tokens.slice(i + chunkSize - overlapSize, i + chunkSize);
            
            const chunk = {
                id: this.generateChunkId(),
                tokens: chunkTokens,
                tokenCount: chunkTokens.length,
                position: this.stats.totalTokens + i,
                timestamp: Date.now(),
                metadata: {
                    ...metadata,
                    chunkIndex: chunks.length,
                    hasOverlap: previousOverlap.length > 0 || nextOverlap.length > 0
                },
                continuity: {
                    previousOverlap,
                    nextOverlap,
                    previousChunkId: chunks.length > 0 ? chunks[chunks.length - 1].id : null,
                    nextChunkId: null  // Will be set when next chunk is created
                }
            };

            // Update previous chunk's next reference
            if (chunks.length > 0) {
                chunks[chunks.length - 1].continuity.nextChunkId = chunk.id;
            }

            chunks.push(chunk);
        }

        return chunks;
    }

    /**
     * Add a chunk to the system
     */
    addChunk(chunk) {
        this.chunks.set(chunk.id, chunk);
        this.chunkOrder.push(chunk.id);
        this.activeChunks.add(chunk.id);
        
        // Update index
        for (let i = 0; i < chunk.tokenCount; i++) {
            this.chunkIndex.set(chunk.position + i, chunk.id);
        }

        // Update continuity map
        if (chunk.continuity.previousChunkId) {
            this.continuityMap.set(chunk.continuity.previousChunkId, chunk.id);
        }

        this.stats.chunkCount++;
    }

    /**
     * Slide the window to make room for new tokens
     */
    slideWindow(requiredTokens) {
        let freedTokens = 0;
        const chunksToDeactivate = [];

        // Find chunks to move out of active window
        for (const chunkId of this.chunkOrder) {
            if (!this.activeChunks.has(chunkId)) continue;
            
            const chunk = this.chunks.get(chunkId);
            if (freedTokens >= requiredTokens) break;

            // Preserve high-priority chunks
            if (chunk.metadata.priority > 0.8) continue;

            chunksToDeactivate.push(chunkId);
            freedTokens += chunk.tokenCount;
        }

        // Deactivate chunks
        for (const chunkId of chunksToDeactivate) {
            this.deactivateChunk(chunkId);
        }

        this.stats.activeTokens -= freedTokens;
    }

    /**
     * Deactivate a chunk (move to inactive storage)
     */
    deactivateChunk(chunkId) {
        this.activeChunks.delete(chunkId);
        
        const chunk = this.chunks.get(chunkId);
        if (chunk) {
            // Mark as inactive
            chunk.metadata.active = false;
            chunk.metadata.deactivatedAt = Date.now();
            
            // Optionally compress if memory pressure is high
            if (this.memoryPressure) {
                this.compressChunk(chunk);
            }
        }
    }

    /**
     * Compress a chunk to save memory
     */
    compressChunk(chunk) {
        // Simple compression: remove overlap data and convert to minimal format
        const compressed = {
            id: chunk.id,
            tokenCount: chunk.tokenCount,
            position: chunk.position,
            timestamp: chunk.timestamp,
            compressed: true,
            // Store only essential metadata
            metadata: {
                priority: chunk.metadata.priority || 0,
                deactivatedAt: chunk.metadata.deactivatedAt
            }
        };

        // Replace full chunk with compressed version
        this.chunks.set(chunk.id, compressed);
    }

    /**
     * Retrieve chunks by token range
     */
    getChunksByRange(startToken, endToken) {
        const relevantChunks = [];
        
        for (let pos = startToken; pos < endToken; pos += this.config.chunkSize) {
            const chunkId = this.chunkIndex.get(pos);
            if (chunkId && !relevantChunks.some(c => c.id === chunkId)) {
                const chunk = this.chunks.get(chunkId);
                if (chunk) {
                    relevantChunks.push(chunk);
                }
            }
        }

        return relevantChunks;
    }

    /**
     * Get chunks with continuity preservation
     */
    getChunksWithContinuity(chunkId, before = 1, after = 1) {
        const chunks = [];
        const centerChunk = this.chunks.get(chunkId);
        
        if (!centerChunk) return chunks;

        // Get previous chunks
        let currentId = chunkId;
        for (let i = 0; i < before; i++) {
            const chunk = this.chunks.get(currentId);
            if (chunk && chunk.continuity.previousChunkId) {
                currentId = chunk.continuity.previousChunkId;
                const prevChunk = this.chunks.get(currentId);
                if (prevChunk) chunks.unshift(prevChunk);
            }
        }

        // Add center chunk
        chunks.push(centerChunk);

        // Get next chunks
        currentId = chunkId;
        for (let i = 0; i < after; i++) {
            const nextId = this.continuityMap.get(currentId);
            if (nextId) {
                const nextChunk = this.chunks.get(nextId);
                if (nextChunk) {
                    chunks.push(nextChunk);
                    currentId = nextId;
                }
            }
        }

        return chunks;
    }

    /**
     * Setup automatic garbage collection
     */
    setupGarbageCollector() {
        // Run GC periodically
        setInterval(() => {
            if (this.shouldRunGC()) {
                this.runGarbageCollection();
            }
        }, 60000); // Check every minute
    }

    /**
     * Check if garbage collection should run
     */
    shouldRunGC() {
        const utilizationRatio = this.stats.totalTokens / this.config.maxTokens;
        const timeSinceLastGC = Date.now() - this.lastGC;
        
        return (
            utilizationRatio > this.config.gcThreshold ||
            (this.memoryPressure && timeSinceLastGC > 30000)
        );
    }

    /**
     * Run garbage collection
     */
    runGarbageCollection() {
        console.log('Running garbage collection...');
        const startTime = Date.now();
        
        // Sort chunks by importance
        const chunkScores = new Map();
        for (const [chunkId, chunk] of this.chunks) {
            const score = this.calculateChunkImportance(chunk);
            chunkScores.set(chunkId, score);
        }

        // Sort by score
        const sortedChunks = Array.from(chunkScores.entries())
            .sort((a, b) => a[1] - b[1]);

        // Remove lowest scoring chunks
        let removed = 0;
        const targetRemoval = Math.floor(this.chunks.size * 0.2); // Remove 20%

        for (const [chunkId, score] of sortedChunks) {
            if (removed >= targetRemoval) break;
            if (this.activeChunks.has(chunkId)) continue; // Don't remove active chunks

            this.removeChunk(chunkId);
            removed++;
        }

        // Update stats
        this.stats.gcRuns++;
        this.lastGC = Date.now();
        this.memoryPressure = false;

        console.log(`GC completed in ${Date.now() - startTime}ms, removed ${removed} chunks`);
    }

    /**
     * Calculate chunk importance for GC
     */
    calculateChunkImportance(chunk) {
        let score = 1.0;

        // Active chunks are most important
        if (this.activeChunks.has(chunk.id)) {
            score += 10.0;
        }

        // Recent chunks are important
        const age = Date.now() - chunk.timestamp;
        score += Math.max(0, 5 - (age / (1000 * 60 * 60))); // Decay over hours

        // High priority metadata
        if (chunk.metadata && chunk.metadata.priority) {
            score += chunk.metadata.priority * 5;
        }

        // Compressed chunks are less important
        if (chunk.compressed) {
            score *= 0.5;
        }

        return score;
    }

    /**
     * Remove a chunk completely
     */
    removeChunk(chunkId) {
        const chunk = this.chunks.get(chunkId);
        if (!chunk) return;

        // Remove from all data structures
        this.chunks.delete(chunkId);
        this.activeChunks.delete(chunkId);
        this.chunkOrder = this.chunkOrder.filter(id => id !== chunkId);

        // Update index
        for (let i = 0; i < chunk.tokenCount; i++) {
            this.chunkIndex.delete(chunk.position + i);
        }

        // Update continuity
        if (chunk.continuity) {
            const prevId = chunk.continuity.previousChunkId;
            const nextId = chunk.continuity.nextChunkId;
            
            if (prevId && nextId) {
                this.continuityMap.set(prevId, nextId);
            } else if (prevId) {
                this.continuityMap.delete(prevId);
            }
        }

        this.stats.chunkCount--;
        if (chunk.metadata && chunk.metadata.active !== false) {
            this.stats.activeTokens -= chunk.tokenCount;
        }
        this.stats.totalTokens -= chunk.tokenCount;
    }

    /**
     * Check memory pressure
     */
    checkMemoryPressure() {
        // Simple heuristic based on chunk count and size
        const estimatedMemoryMB = (this.chunks.size * 0.1); // Rough estimate
        const maxMemoryMB = 500; // 500MB limit

        this.memoryPressure = estimatedMemoryMB > maxMemoryMB * 0.8;

        if (this.memoryPressure) {
            console.warn('Memory pressure detected, enabling compression');
        }
    }

    /**
     * Export session data
     */
    exportSession() {
        const sessionData = {
            version: '1.0',
            timestamp: Date.now(),
            config: this.config,
            stats: this.stats,
            chunks: Array.from(this.chunks.entries()).map(([id, chunk]) => ({
                id,
                chunk: this.serializeChunk(chunk)
            })),
            chunkOrder: this.chunkOrder,
            activeChunks: Array.from(this.activeChunks),
            continuityMap: Array.from(this.continuityMap.entries())
        };

        return sessionData;
    }

    /**
     * Import session data
     */
    importSession(sessionData) {
        // Validate version
        if (sessionData.version !== '1.0') {
            throw new Error(`Unsupported session version: ${sessionData.version}`);
        }

        // Restore configuration
        this.config = { ...this.config, ...sessionData.config };
        this.stats = { ...sessionData.stats };

        // Clear existing data
        this.chunks.clear();
        this.chunkOrder = [];
        this.activeChunks.clear();
        this.chunkIndex.clear();
        this.continuityMap.clear();

        // Restore chunks
        for (const { id, chunk } of sessionData.chunks) {
            const deserializedChunk = this.deserializeChunk(chunk);
            this.chunks.set(id, deserializedChunk);
            
            // Rebuild index
            if (!chunk.compressed) {
                for (let i = 0; i < chunk.tokenCount; i++) {
                    this.chunkIndex.set(chunk.position + i, id);
                }
            }
        }

        // Restore other data structures
        this.chunkOrder = sessionData.chunkOrder;
        this.activeChunks = new Set(sessionData.activeChunks);
        this.continuityMap = new Map(sessionData.continuityMap);
    }

    /**
     * Serialize chunk for export
     */
    serializeChunk(chunk) {
        if (chunk.compressed) {
            return chunk; // Already minimal
        }

        // Remove tokens for space efficiency
        const { tokens, ...chunkData } = chunk;
        return {
            ...chunkData,
            tokenCount: chunk.tokenCount,
            hasTokens: false
        };
    }

    /**
     * Deserialize chunk from import
     */
    deserializeChunk(chunkData) {
        if (chunkData.hasTokens === false) {
            // Tokens were removed during export
            return {
                ...chunkData,
                tokens: null, // Will need to be regenerated if needed
                metadata: {
                    ...chunkData.metadata,
                    tokensRemoved: true
                }
            };
        }
        return chunkData;
    }

    /**
     * Generate unique chunk ID
     */
    generateChunkId() {
        return `chunk_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Get window statistics
     */
    getStatistics() {
        return {
            ...this.stats,
            activeChunkCount: this.activeChunks.size,
            inactiveChunkCount: this.chunks.size - this.activeChunks.size,
            memoryPressure: this.memoryPressure,
            utilizationRatio: this.stats.totalTokens / this.config.maxTokens,
            compressionRatio: this.calculateCompressionRatio()
        };
    }

    /**
     * Calculate compression ratio
     */
    calculateCompressionRatio() {
        let compressedCount = 0;
        for (const chunk of this.chunks.values()) {
            if (chunk.compressed) compressedCount++;
        }
        return this.chunks.size > 0 ? compressedCount / this.chunks.size : 0;
    }
}

// Example usage for 1M token conversation
async function demonstrateSlidingWindow() {
    const windowManager = new SlidingWindowManager({
        maxTokens: 1000000,
        activeWindowSize: 100000,
        chunkSize: 10000
    });

    // Simulate adding conversation tokens
    console.log('Adding conversation tokens...');
    
    // Add initial conversation
    const conversation1 = new Array(50000).fill('token'); // 50k tokens
    const chunkIds1 = windowManager.addTokens(conversation1, {
        type: 'conversation',
        topic: 'consciousness',
        priority: 0.8
    });

    console.log(`Added ${chunkIds1.length} chunks for conversation 1`);

    // Add more conversation
    const conversation2 = new Array(60000).fill('token'); // 60k tokens
    const chunkIds2 = windowManager.addTokens(conversation2, {
        type: 'conversation',
        topic: 'architecture',
        priority: 0.6
    });

    console.log(`Added ${chunkIds2.length} chunks for conversation 2`);
    console.log('Window stats:', windowManager.getStatistics());

    // Demonstrate continuity preservation
    const middleChunkId = chunkIds1[Math.floor(chunkIds1.length / 2)];
    const continuousChunks = windowManager.getChunksWithContinuity(middleChunkId, 2, 2);
    console.log(`Retrieved ${continuousChunks.length} continuous chunks`);

    // Export session
    const session = windowManager.exportSession();
    console.log(`Exported session with ${session.chunks.length} chunks`);

    // Simulate memory pressure
    windowManager.checkMemoryPressure();
    if (windowManager.memoryPressure) {
        windowManager.runGarbageCollection();
    }

    return windowManager;
}

// Export for use
export { SlidingWindowManager, demonstrateSlidingWindow };