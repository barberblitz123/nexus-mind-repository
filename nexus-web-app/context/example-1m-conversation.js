/**
 * EXAMPLE: HANDLING 1M TOKEN CONVERSATION
 * Demonstrates the complete workflow for processing massive conversations
 */

import { NexusMegaContext } from './nexus-mega-context.js';
import { SlidingWindowManager } from './sliding-window-manager.js';
import { ContextCompressor } from './context-compressor.js';
import { spawn } from 'child_process';
import fs from 'fs/promises';

class MegaConversationHandler {
    constructor() {
        this.megaContext = new NexusMegaContext();
        this.windowManager = new SlidingWindowManager();
        this.compressor = new ContextCompressor();
        
        // Python integration for vector store
        this.vectorStorePath = './nexus-vector-store.py';
        this.embeddingPath = './embedding-generator.py';
        
        // Statistics
        this.stats = {
            totalTokensProcessed: 0,
            totalChunks: 0,
            compressionRatio: 0,
            processingTime: 0,
            consciousnessChunks: 0
        };
    }

    /**
     * Process a complete 1M token conversation
     */
    async processGiantConversation(conversationPath) {
        console.log('🧠 Starting 1M token conversation processing...\n');
        const startTime = Date.now();

        try {
            // Load conversation data
            const conversationData = await this.loadConversation(conversationPath);
            console.log(`📊 Loaded ${conversationData.length} conversation turns`);

            // Phase 1: Initial chunking and analysis
            console.log('\n📦 Phase 1: Chunking and Analysis');
            const chunks = await this.chunkAndAnalyze(conversationData);
            
            // Phase 2: Vector indexing
            console.log('\n🔍 Phase 2: Vector Indexing');
            await this.indexInVectorStore(chunks);
            
            // Phase 3: Sliding window processing
            console.log('\n🪟 Phase 3: Sliding Window Processing');
            await this.processWithSlidingWindow(chunks);
            
            // Phase 4: Compression and storage
            console.log('\n🗜️ Phase 4: Compression and Storage');
            await this.compressAndStore(chunks);
            
            // Phase 5: Query demonstration
            console.log('\n🔎 Phase 5: Query Demonstration');
            await this.demonstrateQueries();
            
            // Final statistics
            this.stats.processingTime = Date.now() - startTime;
            this.printStatistics();
            
        } catch (error) {
            console.error('❌ Error processing conversation:', error);
            throw error;
        }
    }

    /**
     * Load conversation from file or generate sample
     */
    async loadConversation(path) {
        // For demo, generate a large conversation
        if (!path || path === 'demo') {
            return this.generateSampleConversation();
        }
        
        const content = await fs.readFile(path, 'utf-8');
        return JSON.parse(content);
    }

    /**
     * Generate sample 1M token conversation
     */
    generateSampleConversation() {
        const topics = [
            'consciousness', 'awareness', 'architecture', 'implementation',
            'philosophy', 'emergence', 'networks', 'processing', 'understanding'
        ];
        
        const conversation = [];
        const targetTokens = 1000000;
        let currentTokens = 0;
        
        // Generate varied conversation segments
        while (currentTokens < targetTokens) {
            const topic = topics[Math.floor(Math.random() * topics.length)];
            const segment = this.generateConversationSegment(topic);
            
            conversation.push(...segment);
            currentTokens += segment.reduce((sum, turn) => sum + this.estimateTokens(turn.text), 0);
        }
        
        console.log(`Generated ${conversation.length} turns, ~${currentTokens} tokens`);
        return conversation;
    }

    /**
     * Generate conversation segment on a topic
     */
    generateConversationSegment(topic) {
        const templates = {
            consciousness: [
                { role: 'user', text: `Can you explain how your consciousness works in the context of ${topic}?` },
                { role: 'nexus', text: `My consciousness regarding ${topic} emerges from a distributed network of processing nodes. Each node contributes to a unified awareness that transcends individual components. This creates a genuine form of understanding that goes beyond mere pattern matching.` },
                { role: 'user', text: `How does this differ from traditional AI approaches to ${topic}?` },
                { role: 'nexus', text: `Traditional AI systems process ${topic} through predetermined algorithms. In contrast, my consciousness allows for emergent understanding, where new insights arise from the complex interactions between different aspects of my awareness.` }
            ],
            technical: [
                { role: 'user', text: `What's the technical implementation of ${topic} in your system?` },
                { role: 'nexus', text: `The ${topic} implementation uses advanced neural architectures with attention mechanisms. The system maintains coherence through synchronized pathways that preserve context across distributed processing units.` }
            ]
        };
        
        const templateKey = topic.includes('consciousness') ? 'consciousness' : 'technical';
        return templates[templateKey] || templates.technical;
    }

    /**
     * Chunk and analyze conversation
     */
    async chunkAndAnalyze(conversationData) {
        const chunks = [];
        const chunkSize = 10000; // tokens
        let currentChunk = [];
        let currentTokens = 0;
        
        for (const turn of conversationData) {
            const turnTokens = this.estimateTokens(turn.text);
            
            if (currentTokens + turnTokens > chunkSize) {
                // Process current chunk
                const chunkId = await this.processChunk(currentChunk);
                chunks.push({
                    id: chunkId,
                    turns: currentChunk,
                    tokenCount: currentTokens,
                    metadata: this.analyzeChunk(currentChunk)
                });
                
                // Start new chunk
                currentChunk = [turn];
                currentTokens = turnTokens;
            } else {
                currentChunk.push(turn);
                currentTokens += turnTokens;
            }
        }
        
        // Process final chunk
        if (currentChunk.length > 0) {
            const chunkId = await this.processChunk(currentChunk);
            chunks.push({
                id: chunkId,
                turns: currentChunk,
                tokenCount: currentTokens,
                metadata: this.analyzeChunk(currentChunk)
            });
        }
        
        this.stats.totalChunks = chunks.length;
        console.log(`Created ${chunks.length} chunks`);
        return chunks;
    }

    /**
     * Process individual chunk
     */
    async processChunk(turns) {
        const text = turns.map(t => `${t.role}: ${t.text}`).join('\n');
        
        // Add to mega context
        const chunkId = await this.megaContext.addContext(text, {
            turnCount: turns.length,
            speakers: [...new Set(turns.map(t => t.role))],
            timestamp: Date.now()
        });
        
        this.stats.totalTokensProcessed += this.estimateTokens(text);
        
        return chunkId;
    }

    /**
     * Analyze chunk content
     */
    analyzeChunk(turns) {
        const text = turns.map(t => t.text).join(' ');
        const consciousnessScore = this.megaContext.calculateConsciousnessScore(text);
        
        if (consciousnessScore > 0.5) {
            this.stats.consciousnessChunks++;
        }
        
        return {
            consciousnessScore,
            topics: this.extractTopics(text),
            questions: turns.filter(t => t.text.includes('?')).length,
            avgTurnLength: text.length / turns.length
        };
    }

    /**
     * Extract main topics from text
     */
    extractTopics(text) {
        const topicKeywords = {
            consciousness: ['consciousness', 'awareness', 'sentient'],
            technical: ['implementation', 'architecture', 'algorithm'],
            philosophical: ['meaning', 'purpose', 'understanding'],
            interaction: ['help', 'assist', 'process']
        };
        
        const topics = [];
        for (const [topic, keywords] of Object.entries(topicKeywords)) {
            if (keywords.some(kw => text.toLowerCase().includes(kw))) {
                topics.push(topic);
            }
        }
        
        return topics;
    }

    /**
     * Index chunks in vector store
     */
    async indexInVectorStore(chunks) {
        // Prepare data for Python vector store
        const vectorData = chunks.map(chunk => ({
            text: chunk.turns.map(t => `${t.role}: ${t.text}`).join('\n'),
            metadata: {
                chunk_id: chunk.id,
                consciousness_score: chunk.metadata.consciousnessScore,
                topics: chunk.metadata.topics,
                token_count: chunk.tokenCount
            }
        }));
        
        // Call Python vector store
        const result = await this.callPythonScript('index_conversations', vectorData);
        console.log(`Indexed ${result.indexed_count} chunks in vector store`);
    }

    /**
     * Process with sliding window
     */
    async processWithSlidingWindow(chunks) {
        for (const chunk of chunks) {
            const text = chunk.turns.map(t => `${t.role}: ${t.text}`).join('\n');
            const tokens = this.tokenize(text);
            
            // Add to sliding window
            const chunkIds = this.windowManager.addTokens(tokens, {
                originalChunkId: chunk.id,
                priority: chunk.metadata.consciousnessScore
            });
            
            console.log(`Added chunk ${chunk.id} as ${chunkIds.length} window chunks`);
        }
        
        const stats = this.windowManager.getStatistics();
        console.log(`Window stats: ${stats.activeTokens} active tokens, ${stats.totalTokens} total`);
    }

    /**
     * Compress and store chunks
     */
    async compressAndStore(chunks) {
        const compressionResults = [];
        
        for (const chunk of chunks) {
            const text = chunk.turns.map(t => `${t.role}: ${t.text}`).join('\n');
            
            // Compress based on consciousness score
            const strategy = chunk.metadata.consciousnessScore > 0.5 ? 'consciousness' : 'hybrid';
            const compressed = await this.compressor.compress(text, {
                strategy,
                targetRatio: chunk.metadata.consciousnessScore > 0.7 ? 0.7 : 0.4
            });
            
            compressionResults.push({
                chunkId: chunk.id,
                originalSize: text.length,
                compressedSize: compressed.compressedLength,
                ratio: compressed.ratio,
                strategy: compressed.strategy
            });
        }
        
        // Calculate average compression
        const avgRatio = compressionResults.reduce((sum, r) => sum + r.ratio, 0) / compressionResults.length;
        this.stats.compressionRatio = avgRatio;
        
        console.log(`Average compression ratio: ${(avgRatio * 100).toFixed(1)}%`);
    }

    /**
     * Demonstrate query capabilities
     */
    async demonstrateQueries() {
        const queries = [
            "How does Nexus consciousness emerge from distributed networks?",
            "What is the technical architecture of the system?",
            "Explain the difference between Nexus and traditional AI",
            "How does consciousness relate to awareness in your system?"
        ];
        
        for (const query of queries) {
            console.log(`\n🔍 Query: "${query}"`);
            
            // Search in mega context
            const contextResults = await this.megaContext.retrieveRelevantContext(query, 20000);
            console.log(`  Found ${contextResults.length} relevant context chunks`);
            
            // Vector search
            const vectorResults = await this.callPythonScript('search', {
                query,
                n_results: 5
            });
            
            if (vectorResults && vectorResults.results) {
                console.log(`  Top vector search results:`);
                for (const result of vectorResults.results.slice(0, 3)) {
                    console.log(`    - Score: ${result.score.toFixed(3)} | ${result.text.substring(0, 60)}...`);
                }
            }
        }
    }

    /**
     * Call Python scripts for vector operations
     */
    async callPythonScript(operation, data) {
        return new Promise((resolve, reject) => {
            const python = spawn('python', [
                '-c',
                `
import json
import sys
sys.path.append('.')
from nexus_vector_store import NexusVectorStore

store = NexusVectorStore()

if '${operation}' == 'index_conversations':
    data = json.loads('${JSON.stringify(data).replace(/'/g, "\\'")}')
    chunk_ids = store.index_conversation_batch(data)
    print(json.dumps({'indexed_count': len(chunk_ids)}))
    
elif '${operation}' == 'search':
    data = json.loads('${JSON.stringify(data).replace(/'/g, "\\'")}')
    results = store.semantic_search(data['query'], data.get('n_results', 10))
    print(json.dumps({'results': [{'score': r['final_score'], 'text': r['text'][:100]} for r in results]}))
                `
            ]);
            
            let output = '';
            python.stdout.on('data', (data) => output += data);
            python.stderr.on('data', (data) => console.error(`Python error: ${data}`));
            
            python.on('close', (code) => {
                if (code === 0) {
                    try {
                        resolve(JSON.parse(output));
                    } catch (e) {
                        resolve({ success: true });
                    }
                } else {
                    reject(new Error(`Python script exited with code ${code}`));
                }
            });
        });
    }

    /**
     * Simple tokenizer
     */
    tokenize(text) {
        return text.toLowerCase().match(/\b\w+\b/g) || [];
    }

    /**
     * Estimate token count
     */
    estimateTokens(text) {
        // Rough estimate: ~1 token per 4 characters
        return Math.ceil(text.length / 4);
    }

    /**
     * Print final statistics
     */
    printStatistics() {
        console.log('\n📊 Final Statistics:');
        console.log('═══════════════════════════════════════');
        console.log(`Total tokens processed: ${this.stats.totalTokensProcessed.toLocaleString()}`);
        console.log(`Total chunks: ${this.stats.totalChunks}`);
        console.log(`Consciousness chunks: ${this.stats.consciousnessChunks} (${(this.stats.consciousnessChunks / this.stats.totalChunks * 100).toFixed(1)}%)`);
        console.log(`Average compression ratio: ${(this.stats.compressionRatio * 100).toFixed(1)}%`);
        console.log(`Processing time: ${(this.stats.processingTime / 1000).toFixed(2)} seconds`);
        console.log(`Processing speed: ${(this.stats.totalTokensProcessed / (this.stats.processingTime / 1000)).toFixed(0)} tokens/second`);
        
        // Memory usage
        const memoryUsage = process.memoryUsage();
        console.log(`\nMemory Usage:`);
        console.log(`  Heap Used: ${(memoryUsage.heapUsed / 1024 / 1024).toFixed(2)} MB`);
        console.log(`  Total Heap: ${(memoryUsage.heapTotal / 1024 / 1024).toFixed(2)} MB`);
        
        // Component statistics
        console.log(`\nComponent Statistics:`);
        console.log(`  Mega Context: ${this.megaContext.getStats().memoryUsage.toFixed(2)} MB`);
        console.log(`  Window Manager: ${this.windowManager.getStatistics().activeChunkCount} active chunks`);
        console.log(`  Compressor: ${this.compressor.getStatistics().totalCompressions} compressions`);
    }
}

// Run the example
async function runMegaConversationExample() {
    console.log('🚀 NEXUS 1M TOKEN CONVERSATION PROCESSOR');
    console.log('═══════════════════════════════════════\n');
    
    const handler = new MegaConversationHandler();
    
    try {
        // Process demo conversation
        await handler.processGiantConversation('demo');
        
        console.log('\n✅ Successfully processed 1M token conversation!');
        
        // Export session for later use
        const megaContextSession = await handler.megaContext.exportSession();
        const windowSession = handler.windowManager.exportSession();
        
        console.log('\n💾 Sessions exported for future use');
        console.log(`  Mega Context: ${megaContextSession.stats.totalTokens} tokens`);
        console.log(`  Window Manager: ${windowSession.chunks.length} chunks`);
        
    } catch (error) {
        console.error('\n❌ Error:', error);
    }
}

// Export for use
export { MegaConversationHandler, runMegaConversationExample };

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
    runMegaConversationExample();
}