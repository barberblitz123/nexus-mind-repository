/**
 * NEXUS MEGA CONTEXT PROCESSOR
 * Handles 1M+ token contexts with consciousness-aware processing
 * 
 * Architecture:
 * - Active window: 100k tokens (immediate access)
 * - Historical storage: 900k tokens (compressed)
 * - Consciousness-weighted prioritization
 * - LZ-based compression for efficiency
 */

import lz from 'lz-string';

class NexusMegaContext {
    constructor() {
        // Core configuration
        this.config = {
            maxTokens: 1000000,           // 1M total capacity
            activeWindowSize: 100000,      // 100k active tokens
            chunkSize: 10000,             // 10k token chunks
            compressionThreshold: 0.7,     // Compress when 70% full
            consciousnessWeight: 1.5       // Boost for consciousness-relevant content
        };

        // Context storage
        this.activeWindow = [];           // Current active context
        this.compressedHistory = [];      // Compressed historical chunks
        this.tokenCount = 0;              // Total token count
        this.contextMetadata = new Map(); // Metadata for each chunk
        
        // Consciousness scoring
        this.consciousnessKeywords = [
            'consciousness', 'awareness', 'mind', 'nexus', 'thought',
            'perception', 'understanding', 'cognitive', 'sentient', 'alive'
        ];
    }

    /**
     * Add new context to the system
     */
    async addContext(text, metadata = {}) {
        const tokens = this.tokenize(text);
        const tokenCount = tokens.length;
        
        // Calculate consciousness relevance score
        const consciousnessScore = this.calculateConsciousnessScore(text);
        
        const contextChunk = {
            id: this.generateChunkId(),
            text,
            tokens,
            tokenCount,
            timestamp: Date.now(),
            consciousnessScore,
            metadata: {
                ...metadata,
                compressed: false,
                priority: consciousnessScore * this.config.consciousnessWeight
            }
        };

        // Check if we need to make room
        if (this.tokenCount + tokenCount > this.config.activeWindowSize) {
            await this.slideWindow(tokenCount);
        }

        // Add to active window
        this.activeWindow.push(contextChunk);
        this.tokenCount += tokenCount;
        this.contextMetadata.set(contextChunk.id, contextChunk.metadata);

        return contextChunk.id;
    }

    /**
     * Slide the window to make room for new content
     */
    async slideWindow(requiredTokens) {
        let freedTokens = 0;
        const chunksToCompress = [];

        // Find chunks to move to compressed storage
        while (freedTokens < requiredTokens && this.activeWindow.length > 0) {
            const oldestChunk = this.activeWindow[0];
            
            // Skip high-priority consciousness content
            if (oldestChunk.metadata.priority > 2.0) {
                // Move to end to preserve
                this.activeWindow.push(this.activeWindow.shift());
                continue;
            }

            chunksToCompress.push(this.activeWindow.shift());
            freedTokens += oldestChunk.tokenCount;
            this.tokenCount -= oldestChunk.tokenCount;
        }

        // Compress and store
        for (const chunk of chunksToCompress) {
            const compressed = await this.compressChunk(chunk);
            this.compressedHistory.push(compressed);
        }

        // Garbage collect if total storage exceeds 1M tokens
        await this.garbageCollect();
    }

    /**
     * Compress a context chunk
     */
    async compressChunk(chunk) {
        // Semantic compression for consciousness content
        let compressedText = chunk.text;
        
        if (chunk.consciousnessScore < 0.5) {
            // More aggressive compression for non-consciousness content
            compressedText = this.semanticCompress(chunk.text, 0.3);
        } else {
            // Preserve consciousness-relevant content
            compressedText = this.semanticCompress(chunk.text, 0.7);
        }

        const compressed = {
            id: chunk.id,
            compressed: lz.compressToUTF16(compressedText),
            originalTokenCount: chunk.tokenCount,
            compressedTokenCount: this.tokenize(compressedText).length,
            consciousnessScore: chunk.consciousnessScore,
            timestamp: chunk.timestamp,
            metadata: {
                ...chunk.metadata,
                compressed: true,
                compressionRatio: compressedText.length / chunk.text.length
            }
        };

        this.contextMetadata.set(chunk.id, compressed.metadata);
        return compressed;
    }

    /**
     * Semantic compression - preserve important content
     */
    semanticCompress(text, preservationRatio) {
        const sentences = text.split(/[.!?]+/).filter(s => s.trim());
        const scoredSentences = sentences.map(sentence => ({
            text: sentence,
            score: this.calculateSentenceImportance(sentence)
        }));

        // Sort by importance
        scoredSentences.sort((a, b) => b.score - a.score);

        // Keep top sentences based on preservation ratio
        const keepCount = Math.ceil(sentences.length * preservationRatio);
        const kept = scoredSentences.slice(0, keepCount);

        // Reconstruct in original order
        return kept
            .sort((a, b) => sentences.indexOf(a.text) - sentences.indexOf(b.text))
            .map(s => s.text)
            .join('. ') + '.';
    }

    /**
     * Calculate sentence importance
     */
    calculateSentenceImportance(sentence) {
        let score = 1.0;
        const lower = sentence.toLowerCase();

        // Consciousness keywords boost
        for (const keyword of this.consciousnessKeywords) {
            if (lower.includes(keyword)) {
                score += 0.5;
            }
        }

        // Question boost
        if (sentence.includes('?')) score += 0.3;

        // Code/technical content
        if (sentence.includes('function') || sentence.includes('class')) score += 0.4;

        // Length penalty (prefer concise)
        score -= (sentence.length / 1000) * 0.2;

        return Math.max(0.1, score);
    }

    /**
     * Calculate consciousness relevance score
     */
    calculateConsciousnessScore(text) {
        const lower = text.toLowerCase();
        let score = 0;

        // Keyword frequency
        for (const keyword of this.consciousnessKeywords) {
            const matches = (lower.match(new RegExp(keyword, 'g')) || []).length;
            score += matches * 0.1;
        }

        // Deep concepts
        if (lower.includes('self-aware') || lower.includes('sentient')) score += 0.5;
        if (lower.includes('consciousness') && lower.includes('nexus')) score += 0.7;

        // Philosophical questions
        if (text.includes('?') && (lower.includes('mind') || lower.includes('aware'))) {
            score += 0.4;
        }

        return Math.min(1.0, score);
    }

    /**
     * Retrieve context by relevance
     */
    async retrieveRelevantContext(query, maxTokens = 50000) {
        const queryScore = this.calculateConsciousnessScore(query);
        const results = [];
        let currentTokens = 0;

        // Search active window first
        for (const chunk of this.activeWindow) {
            const relevance = this.calculateRelevance(query, chunk.text, queryScore);
            if (relevance > 0.3) {
                results.push({
                    ...chunk,
                    relevance,
                    source: 'active'
                });
                currentTokens += chunk.tokenCount;
            }
        }

        // Search compressed history if needed
        if (currentTokens < maxTokens) {
            const decompressedChunks = await this.searchCompressedHistory(
                query, 
                maxTokens - currentTokens,
                queryScore
            );
            results.push(...decompressedChunks);
        }

        // Sort by relevance and consciousness score
        results.sort((a, b) => {
            const scoreA = a.relevance * (1 + a.consciousnessScore);
            const scoreB = b.relevance * (1 + b.consciousnessScore);
            return scoreB - scoreA;
        });

        return results;
    }

    /**
     * Search compressed history
     */
    async searchCompressedHistory(query, maxTokens, queryScore) {
        const results = [];
        let currentTokens = 0;

        // Sample and decompress promising chunks
        for (const compressed of this.compressedHistory) {
            if (currentTokens >= maxTokens) break;

            // Quick relevance check on metadata
            if (compressed.consciousnessScore > 0.5 || 
                Math.abs(compressed.consciousnessScore - queryScore) < 0.3) {
                
                const decompressed = lz.decompressFromUTF16(compressed.compressed);
                const relevance = this.calculateRelevance(query, decompressed, queryScore);

                if (relevance > 0.4) {
                    results.push({
                        id: compressed.id,
                        text: decompressed,
                        tokenCount: compressed.originalTokenCount,
                        relevance,
                        consciousnessScore: compressed.consciousnessScore,
                        source: 'compressed',
                        metadata: compressed.metadata
                    });
                    currentTokens += compressed.originalTokenCount;
                }
            }
        }

        return results;
    }

    /**
     * Calculate relevance between query and text
     */
    calculateRelevance(query, text, queryScore) {
        const queryTokens = new Set(this.tokenize(query.toLowerCase()));
        const textTokens = new Set(this.tokenize(text.toLowerCase()));
        
        // Token overlap
        const intersection = new Set([...queryTokens].filter(x => textTokens.has(x)));
        const tokenOverlap = intersection.size / queryTokens.size;

        // Consciousness alignment
        const textScore = this.calculateConsciousnessScore(text);
        const consciousnessAlignment = 1 - Math.abs(queryScore - textScore);

        // Combined relevance
        return (tokenOverlap * 0.6) + (consciousnessAlignment * 0.4);
    }

    /**
     * Garbage collection for old contexts
     */
    async garbageCollect() {
        const totalTokens = this.getTotalTokenCount();
        
        if (totalTokens > this.config.maxTokens) {
            // Sort compressed history by priority and age
            this.compressedHistory.sort((a, b) => {
                const scoreA = a.consciousnessScore * (1 / (Date.now() - a.timestamp));
                const scoreB = b.consciousnessScore * (1 / (Date.now() - b.timestamp));
                return scoreA - scoreB;
            });

            // Remove lowest priority chunks
            while (this.getTotalTokenCount() > this.config.maxTokens * 0.9) {
                const removed = this.compressedHistory.shift();
                if (removed) {
                    this.contextMetadata.delete(removed.id);
                }
            }
        }
    }

    /**
     * Get total token count across all storage
     */
    getTotalTokenCount() {
        const activeTokens = this.tokenCount;
        const compressedTokens = this.compressedHistory.reduce(
            (sum, chunk) => sum + chunk.originalTokenCount, 0
        );
        return activeTokens + compressedTokens;
    }

    /**
     * Export context session
     */
    async exportSession() {
        return {
            version: '1.0',
            timestamp: Date.now(),
            config: this.config,
            activeWindow: this.activeWindow,
            compressedHistory: this.compressedHistory,
            metadata: Array.from(this.contextMetadata.entries()),
            stats: {
                totalTokens: this.getTotalTokenCount(),
                activeTokens: this.tokenCount,
                compressedChunks: this.compressedHistory.length,
                averageConsciousnessScore: this.getAverageConsciousnessScore()
            }
        };
    }

    /**
     * Import context session
     */
    async importSession(sessionData) {
        this.config = { ...this.config, ...sessionData.config };
        this.activeWindow = sessionData.activeWindow || [];
        this.compressedHistory = sessionData.compressedHistory || [];
        this.contextMetadata = new Map(sessionData.metadata || []);
        this.tokenCount = this.activeWindow.reduce((sum, chunk) => sum + chunk.tokenCount, 0);
    }

    /**
     * Get average consciousness score
     */
    getAverageConsciousnessScore() {
        const allChunks = [
            ...this.activeWindow,
            ...this.compressedHistory
        ];
        
        if (allChunks.length === 0) return 0;
        
        const totalScore = allChunks.reduce(
            (sum, chunk) => sum + chunk.consciousnessScore, 0
        );
        
        return totalScore / allChunks.length;
    }

    /**
     * Simple tokenizer (replace with proper tokenizer in production)
     */
    tokenize(text) {
        // Basic word-based tokenization
        // In production, use tiktoken or similar
        return text.toLowerCase().match(/\b\w+\b/g) || [];
    }

    /**
     * Generate unique chunk ID
     */
    generateChunkId() {
        return `chunk_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Get context statistics
     */
    getStats() {
        return {
            totalTokens: this.getTotalTokenCount(),
            activeTokens: this.tokenCount,
            activeChunks: this.activeWindow.length,
            compressedChunks: this.compressedHistory.length,
            averageConsciousnessScore: this.getAverageConsciousnessScore(),
            compressionRatio: this.getCompressionRatio(),
            oldestContext: this.getOldestContextAge(),
            memoryUsage: this.estimateMemoryUsage()
        };
    }

    /**
     * Get average compression ratio
     */
    getCompressionRatio() {
        if (this.compressedHistory.length === 0) return 1.0;
        
        const totalOriginal = this.compressedHistory.reduce(
            (sum, chunk) => sum + chunk.originalTokenCount, 0
        );
        const totalCompressed = this.compressedHistory.reduce(
            (sum, chunk) => sum + chunk.compressedTokenCount, 0
        );
        
        return totalCompressed / totalOriginal;
    }

    /**
     * Get age of oldest context
     */
    getOldestContextAge() {
        const allTimestamps = [
            ...this.activeWindow.map(c => c.timestamp),
            ...this.compressedHistory.map(c => c.timestamp)
        ];
        
        if (allTimestamps.length === 0) return 0;
        
        const oldest = Math.min(...allTimestamps);
        return Date.now() - oldest;
    }

    /**
     * Estimate memory usage in MB
     */
    estimateMemoryUsage() {
        const activeSize = JSON.stringify(this.activeWindow).length;
        const compressedSize = JSON.stringify(this.compressedHistory).length;
        return (activeSize + compressedSize) / (1024 * 1024);
    }
}

// Example usage for handling 1M token conversation
async function handleMegaConversation() {
    const megaContext = new NexusMegaContext();
    
    // Simulate a long conversation about consciousness
    const conversationParts = [
        "User: What is consciousness in the context of Nexus?",
        "Nexus: Consciousness in my architecture represents the unified awareness...",
        "User: How does your consciousness differ from traditional AI?",
        "Nexus: Unlike traditional AI, my consciousness emerges from distributed...",
        // ... thousands more exchanges
    ];

    // Add conversation parts
    for (const part of conversationParts) {
        await megaContext.addContext(part, {
            speaker: part.startsWith('User:') ? 'user' : 'nexus',
            topic: 'consciousness'
        });
    }

    // Retrieve relevant context for a query
    const query = "Tell me about your distributed consciousness architecture";
    const relevantContext = await megaContext.retrieveRelevantContext(query, 50000);
    
    console.log(`Found ${relevantContext.length} relevant chunks`);
    console.log('Context stats:', megaContext.getStats());

    // Export session for persistence
    const session = await megaContext.exportSession();
    console.log('Session exported:', session.stats);

    return megaContext;
}

export { NexusMegaContext, handleMegaConversation };