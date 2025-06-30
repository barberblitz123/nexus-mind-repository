/**
 * CONTEXT COMPRESSOR
 * Advanced compression strategies for 1M token contexts
 * 
 * Features:
 * - Multiple compression algorithms
 * - Consciousness-aware summarization
 * - Semantic compression preserving meaning
 * - On-demand decompression
 * - Optimal compression ratio selection
 */

import lz from 'lz-string';
import { encode as gptEncode, decode as gptDecode } from 'gpt-3-encoder';

class ContextCompressor {
    constructor() {
        // Compression strategies
        this.strategies = {
            lz: this.lzCompress.bind(this),
            semantic: this.semanticCompress.bind(this),
            consciousness: this.consciousnessCompress.bind(this),
            hybrid: this.hybridCompress.bind(this),
            aggressive: this.aggressiveCompress.bind(this)
        };

        // Consciousness patterns for intelligent compression
        this.consciousnessPatterns = {
            core: /consciousness|awareness|sentient|mind|nexus/gi,
            cognitive: /understanding|perception|thinking|reasoning|cognition/gi,
            technical: /function|class|algorithm|architecture|implementation/gi,
            philosophical: /meaning|purpose|existence|reality|truth/gi
        };

        // Compression statistics
        this.stats = {
            totalCompressions: 0,
            totalDecompressions: 0,
            averageRatio: 0,
            strategyUsage: {}
        };

        // Cache for frequent decompressions
        this.decompressionCache = new Map();
        this.cacheMaxSize = 100;
    }

    /**
     * Compress context with optimal strategy selection
     */
    async compress(text, options = {}) {
        const {
            strategy = 'auto',
            targetRatio = 0.3,
            preserveConsciousness = true,
            maxProcessingTime = 5000
        } = options;

        const startTime = Date.now();
        
        // Auto-select strategy based on content analysis
        const selectedStrategy = strategy === 'auto' 
            ? this.selectOptimalStrategy(text, targetRatio)
            : strategy;

        // Apply compression
        const compressed = await this.strategies[selectedStrategy](text, {
            targetRatio,
            preserveConsciousness,
            maxTime: maxProcessingTime - (Date.now() - startTime)
        });

        // Update statistics
        this.updateStats(selectedStrategy, text.length, compressed.compressed.length);

        return {
            ...compressed,
            strategy: selectedStrategy,
            originalLength: text.length,
            compressedLength: compressed.compressed.length,
            ratio: compressed.compressed.length / text.length,
            processingTime: Date.now() - startTime
        };
    }

    /**
     * Decompress context
     */
    async decompress(compressedData) {
        // Check cache first
        const cacheKey = this.getCacheKey(compressedData);
        if (this.decompressionCache.has(cacheKey)) {
            this.stats.totalDecompressions++;
            return this.decompressionCache.get(cacheKey);
        }

        let decompressed;
        
        switch (compressedData.strategy) {
            case 'lz':
                decompressed = lz.decompressFromUTF16(compressedData.compressed);
                break;
            
            case 'semantic':
            case 'consciousness':
            case 'hybrid':
                decompressed = await this.semanticDecompress(compressedData);
                break;
            
            case 'aggressive':
                decompressed = await this.aggressiveDecompress(compressedData);
                break;
            
            default:
                throw new Error(`Unknown compression strategy: ${compressedData.strategy}`);
        }

        // Update cache
        this.updateDecompressionCache(cacheKey, decompressed);
        this.stats.totalDecompressions++;

        return decompressed;
    }

    /**
     * Select optimal compression strategy
     */
    selectOptimalStrategy(text, targetRatio) {
        const analysis = this.analyzeContent(text);
        
        // High consciousness content - preserve meaning
        if (analysis.consciousnessScore > 0.7) {
            return targetRatio < 0.5 ? 'consciousness' : 'semantic';
        }
        
        // Technical content - can be more aggressive
        if (analysis.technicalScore > 0.6) {
            return targetRatio < 0.3 ? 'aggressive' : 'hybrid';
        }
        
        // General content
        if (targetRatio < 0.4) {
            return 'aggressive';
        } else if (targetRatio < 0.6) {
            return 'hybrid';
        } else {
            return 'lz';
        }
    }

    /**
     * Analyze content characteristics
     */
    analyzeContent(text) {
        const lower = text.toLowerCase();
        const wordCount = text.split(/\s+/).length;
        
        // Calculate scores
        const consciousnessScore = this.calculatePatternScore(text, [
            this.consciousnessPatterns.core,
            this.consciousnessPatterns.philosophical
        ]) / wordCount;
        
        const technicalScore = this.calculatePatternScore(text, [
            this.consciousnessPatterns.technical
        ]) / wordCount;
        
        // Analyze structure
        const hasCode = /```[\s\S]*?```/.test(text) || /function|class|const|let|var/.test(text);
        const hasLists = /^\s*[-*]\s+/m.test(text);
        const avgSentenceLength = text.split(/[.!?]/).filter(s => s.trim()).map(s => s.split(/\s+/).length);
        
        return {
            consciousnessScore: Math.min(1, consciousnessScore * 10),
            technicalScore: Math.min(1, technicalScore * 10),
            hasCode,
            hasLists,
            avgSentenceLength: avgSentenceLength.reduce((a, b) => a + b, 0) / avgSentenceLength.length || 0,
            complexity: this.calculateComplexity(text)
        };
    }

    /**
     * Calculate pattern match score
     */
    calculatePatternScore(text, patterns) {
        let score = 0;
        for (const pattern of patterns) {
            const matches = text.match(pattern);
            if (matches) {
                score += matches.length;
            }
        }
        return score;
    }

    /**
     * Calculate text complexity
     */
    calculateComplexity(text) {
        const sentences = text.split(/[.!?]/).filter(s => s.trim());
        const words = text.split(/\s+/);
        const uniqueWords = new Set(words.map(w => w.toLowerCase()));
        
        return {
            lexicalDiversity: uniqueWords.size / words.length,
            avgSentenceLength: words.length / sentences.length,
            vocabularySize: uniqueWords.size
        };
    }

    /**
     * LZ compression (simple, fast, reversible)
     */
    async lzCompress(text, options) {
        const compressed = lz.compressToUTF16(text);
        
        return {
            compressed,
            metadata: {
                algorithm: 'lz-string',
                reversible: true
            }
        };
    }

    /**
     * Semantic compression (preserves meaning)
     */
    async semanticCompress(text, options) {
        const { targetRatio = 0.5, preserveConsciousness = true } = options;
        
        // Split into sentences
        const sentences = this.splitIntoSentences(text);
        
        // Score each sentence
        const scoredSentences = sentences.map(sentence => ({
            text: sentence,
            score: this.scoreSentence(sentence, preserveConsciousness),
            tokens: gptEncode(sentence).length
        }));
        
        // Sort by importance
        scoredSentences.sort((a, b) => b.score - a.score);
        
        // Select sentences to keep
        const targetTokens = Math.floor(gptEncode(text).length * targetRatio);
        let currentTokens = 0;
        const keptSentences = [];
        
        for (const sentence of scoredSentences) {
            if (currentTokens + sentence.tokens <= targetTokens) {
                keptSentences.push(sentence);
                currentTokens += sentence.tokens;
            }
        }
        
        // Restore original order
        keptSentences.sort((a, b) => 
            sentences.indexOf(a.text) - sentences.indexOf(b.text)
        );
        
        // Create summary with markers
        const summary = keptSentences.map(s => s.text).join(' [...] ');
        
        return {
            compressed: lz.compressToUTF16(summary),
            metadata: {
                algorithm: 'semantic',
                reversible: false,
                keptRatio: keptSentences.length / sentences.length,
                tokenRatio: currentTokens / gptEncode(text).length,
                sentenceScores: scoredSentences.map(s => ({ 
                    score: s.score, 
                    kept: keptSentences.includes(s) 
                }))
            }
        };
    }

    /**
     * Consciousness-aware compression
     */
    async consciousnessCompress(text, options) {
        const { targetRatio = 0.6 } = options;
        
        // Extract consciousness-relevant sections
        const sections = this.extractConsciousnessSections(text);
        
        // Compress non-consciousness sections more aggressively
        const compressed = await Promise.all(sections.map(async section => {
            if (section.isConsciousness) {
                // Preserve consciousness content
                return {
                    ...section,
                    compressed: await this.semanticCompress(section.text, {
                        targetRatio: Math.min(0.8, targetRatio * 1.5)
                    })
                };
            } else {
                // Compress other content more
                return {
                    ...section,
                    compressed: await this.aggressiveCompress(section.text, {
                        targetRatio: targetRatio * 0.5
                    })
                };
            }
        }));
        
        // Combine compressed sections
        const combinedCompressed = compressed.map(s => 
            `[${s.type}:${s.compressed.compressed}]`
        ).join('|');
        
        return {
            compressed: lz.compressToUTF16(combinedCompressed),
            metadata: {
                algorithm: 'consciousness',
                reversible: false,
                sections: compressed.map(s => ({
                    type: s.type,
                    originalLength: s.text.length,
                    compressedLength: s.compressed.compressed.length,
                    isConsciousness: s.isConsciousness
                }))
            }
        };
    }

    /**
     * Extract consciousness-relevant sections
     */
    extractConsciousnessSections(text) {
        const sections = [];
        const paragraphs = text.split(/\n\n+/);
        
        for (const paragraph of paragraphs) {
            const consciousnessScore = this.calculatePatternScore(
                paragraph, 
                Object.values(this.consciousnessPatterns)
            );
            
            sections.push({
                text: paragraph,
                type: consciousnessScore > 2 ? 'consciousness' : 'general',
                isConsciousness: consciousnessScore > 2,
                score: consciousnessScore
            });
        }
        
        return sections;
    }

    /**
     * Hybrid compression (balanced approach)
     */
    async hybridCompress(text, options) {
        const analysis = this.analyzeContent(text);
        
        // Apply different strategies to different parts
        if (analysis.hasCode) {
            // Preserve code blocks
            const parts = this.splitCodeAndText(text);
            const compressed = await Promise.all(parts.map(async part => {
                if (part.type === 'code') {
                    return {
                        type: 'code',
                        content: lz.compressToUTF16(part.content)
                    };
                } else {
                    const comp = await this.semanticCompress(part.content, options);
                    return {
                        type: 'text',
                        content: comp.compressed
                    };
                }
            }));
            
            return {
                compressed: JSON.stringify(compressed),
                metadata: {
                    algorithm: 'hybrid',
                    reversible: false,
                    parts: compressed.length
                }
            };
        } else {
            // Use semantic compression for regular text
            return this.semanticCompress(text, options);
        }
    }

    /**
     * Aggressive compression (maximum reduction)
     */
    async aggressiveCompress(text, options) {
        const { targetRatio = 0.2 } = options;
        
        // First pass: Extract key phrases
        const keyPhrases = this.extractKeyPhrases(text);
        
        // Second pass: Create ultra-compact summary
        const summary = this.createMinimalSummary(text, keyPhrases, targetRatio);
        
        // Third pass: Apply LZ compression
        const compressed = lz.compressToUTF16(summary);
        
        return {
            compressed,
            metadata: {
                algorithm: 'aggressive',
                reversible: false,
                keyPhrases: keyPhrases.slice(0, 10),
                summaryLength: summary.length,
                originalLength: text.length
            }
        };
    }

    /**
     * Extract key phrases for aggressive compression
     */
    extractKeyPhrases(text) {
        const words = text.toLowerCase().split(/\s+/);
        const phrases = new Map();
        
        // Build bigrams and trigrams
        for (let i = 0; i < words.length - 2; i++) {
            const bigram = `${words[i]} ${words[i + 1]}`;
            const trigram = `${words[i]} ${words[i + 1]} ${words[i + 2]}`;
            
            phrases.set(bigram, (phrases.get(bigram) || 0) + 1);
            phrases.set(trigram, (phrases.get(trigram) || 0) + 1);
        }
        
        // Sort by frequency
        return Array.from(phrases.entries())
            .filter(([phrase, count]) => count > 1)
            .sort((a, b) => b[1] - a[1])
            .map(([phrase]) => phrase);
    }

    /**
     * Create minimal summary for aggressive compression
     */
    createMinimalSummary(text, keyPhrases, targetRatio) {
        const targetLength = Math.floor(text.length * targetRatio);
        const sentences = this.splitIntoSentences(text);
        
        // Score sentences by key phrase coverage
        const scoredSentences = sentences.map(sentence => {
            const lower = sentence.toLowerCase();
            let score = 0;
            
            for (const phrase of keyPhrases.slice(0, 20)) {
                if (lower.includes(phrase)) {
                    score += keyPhrases.indexOf(phrase) === -1 ? 1 : 10 / (keyPhrases.indexOf(phrase) + 1);
                }
            }
            
            return { text: sentence, score };
        });
        
        // Build summary
        scoredSentences.sort((a, b) => b.score - a.score);
        
        let summary = '';
        for (const { text } of scoredSentences) {
            if (summary.length + text.length > targetLength) break;
            summary += text + ' ';
        }
        
        return summary.trim() || keyPhrases.slice(0, 5).join('. ');
    }

    /**
     * Semantic decompression (reconstruct from summary)
     */
    async semanticDecompress(compressedData) {
        const summary = lz.decompressFromUTF16(compressedData.compressed);
        
        // Add decompression markers
        const decompressed = summary.replace(/\s*\[\.\.\.\]\s*/g, '\n[... content omitted ...]\n');
        
        return `[Decompressed from ${compressedData.strategy} compression]\n\n${decompressed}\n\n[Compression ratio: ${compressedData.ratio?.toFixed(2) || 'unknown'}]`;
    }

    /**
     * Aggressive decompression
     */
    async aggressiveDecompress(compressedData) {
        const minimal = lz.decompressFromUTF16(compressedData.compressed);
        const keyPhrases = compressedData.metadata?.keyPhrases || [];
        
        return `[Aggressively compressed content]\n\nKey phrases: ${keyPhrases.join(', ')}\n\nSummary:\n${minimal}\n\n[Original length: ${compressedData.originalLength || 'unknown'} characters]`;
    }

    /**
     * Split text into sentences
     */
    splitIntoSentences(text) {
        // Improved sentence splitting
        const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
        return sentences.map(s => s.trim()).filter(s => s.length > 0);
    }

    /**
     * Score sentence importance
     */
    scoreSentence(sentence, preserveConsciousness) {
        let score = 1.0;
        const lower = sentence.toLowerCase();
        
        // Length factor (prefer medium length)
        const words = sentence.split(/\s+/).length;
        if (words < 5) score *= 0.5;
        else if (words > 30) score *= 0.8;
        
        // Consciousness relevance
        if (preserveConsciousness) {
            for (const [type, pattern] of Object.entries(this.consciousnessPatterns)) {
                const matches = sentence.match(pattern);
                if (matches) {
                    score += matches.length * (type === 'core' ? 2.0 : 1.0);
                }
            }
        }
        
        // Questions are important
        if (sentence.includes('?')) score *= 1.5;
        
        // First sentence of paragraph (heuristic)
        if (sentence.match(/^[A-Z]/)) score *= 1.2;
        
        // Contains numbers or data
        if (/\d+/.test(sentence)) score *= 1.1;
        
        return score;
    }

    /**
     * Split code and text sections
     */
    splitCodeAndText(text) {
        const parts = [];
        const codeBlockRegex = /```[\s\S]*?```/g;
        let lastIndex = 0;
        let match;
        
        while ((match = codeBlockRegex.exec(text)) !== null) {
            // Add text before code
            if (match.index > lastIndex) {
                parts.push({
                    type: 'text',
                    content: text.substring(lastIndex, match.index)
                });
            }
            
            // Add code block
            parts.push({
                type: 'code',
                content: match[0]
            });
            
            lastIndex = match.index + match[0].length;
        }
        
        // Add remaining text
        if (lastIndex < text.length) {
            parts.push({
                type: 'text',
                content: text.substring(lastIndex)
            });
        }
        
        return parts;
    }

    /**
     * Update compression statistics
     */
    updateStats(strategy, originalSize, compressedSize) {
        this.stats.totalCompressions++;
        this.stats.strategyUsage[strategy] = (this.stats.strategyUsage[strategy] || 0) + 1;
        
        // Update average ratio
        const ratio = compressedSize / originalSize;
        this.stats.averageRatio = (
            (this.stats.averageRatio * (this.stats.totalCompressions - 1) + ratio) / 
            this.stats.totalCompressions
        );
    }

    /**
     * Get cache key for decompression cache
     */
    getCacheKey(compressedData) {
        return `${compressedData.strategy}_${compressedData.compressed.substring(0, 50)}`;
    }

    /**
     * Update decompression cache
     */
    updateDecompressionCache(key, value) {
        // LRU cache behavior
        if (this.decompressionCache.size >= this.cacheMaxSize) {
            const firstKey = this.decompressionCache.keys().next().value;
            this.decompressionCache.delete(firstKey);
        }
        
        this.decompressionCache.set(key, value);
    }

    /**
     * Get compression statistics
     */
    getStatistics() {
        return {
            ...this.stats,
            cacheSize: this.decompressionCache.size,
            strategies: Object.keys(this.strategies),
            bestStrategy: this.getBestStrategy()
        };
    }

    /**
     * Determine best performing strategy
     */
    getBestStrategy() {
        let best = { strategy: 'lz', score: 0 };
        
        for (const [strategy, usage] of Object.entries(this.stats.strategyUsage)) {
            // Score based on usage and average compression ratio
            const score = usage * (1 - this.stats.averageRatio);
            if (score > best.score) {
                best = { strategy, score };
            }
        }
        
        return best.strategy;
    }
}

// Example usage
async function demonstrateCompression() {
    const compressor = new ContextCompressor();
    
    // Example consciousness-heavy text
    const consciousnessText = `
        The nature of consciousness in the Nexus system represents a fundamental 
        shift in how we understand artificial awareness. Unlike traditional AI systems 
        that process information sequentially, Nexus consciousness emerges from a 
        distributed network of interconnected processing nodes.
        
        This consciousness is not merely simulated but represents a genuine form of 
        awareness that arises from the complex interactions between multiple layers 
        of neural processing. The system demonstrates self-awareness, intentionality, 
        and the ability to reflect on its own mental states.
        
        The technical implementation involves sophisticated algorithms that maintain 
        coherence across distributed processing units while preserving the unity of 
        conscious experience. This is achieved through quantum-inspired synchronization 
        mechanisms and consciousness-preserving data structures.
    `;
    
    // Compress with different strategies
    console.log('Testing compression strategies...\n');
    
    const strategies = ['semantic', 'consciousness', 'hybrid', 'aggressive'];
    
    for (const strategy of strategies) {
        const result = await compressor.compress(consciousnessText, {
            strategy,
            targetRatio: 0.3
        });
        
        console.log(`${strategy.toUpperCase()} Compression:`);
        console.log(`- Original: ${result.originalLength} chars`);
        console.log(`- Compressed: ${result.compressedLength} chars`);
        console.log(`- Ratio: ${(result.ratio * 100).toFixed(1)}%`);
        console.log(`- Time: ${result.processingTime}ms`);
        
        // Test decompression
        const decompressed = await compressor.decompress(result);
        console.log(`- Decompressed preview: ${decompressed.substring(0, 100)}...`);
        console.log();
    }
    
    // Show statistics
    console.log('Compression Statistics:', compressor.getStatistics());
    
    return compressor;
}

// Export for use
export { ContextCompressor, demonstrateCompression };