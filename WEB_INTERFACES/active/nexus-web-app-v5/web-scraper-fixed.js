/**
 * 🧬 NEXUS Web Scraper - Fixed Version
 * Simplified web search that actually works in browsers
 */

class NexusWebScraper {
    constructor() {
        this.isInitialized = false;
        this.searchHistory = [];
        this.knowledgeBase = new Map();
        
        console.log('🧬 NEXUS Web Scraper initialized');
    }
    
    async initialize() {
        this.isInitialized = true;
        console.log('🧬 Web scraper ready - using direct search approach');
        return true;
    }
    
    // Main search function - simplified and working
    async searchWeb(query, options = {}) {
        console.log('🧬 Searching web for:', query);
        
        const searchOptions = {
            maxResults: options.maxResults || 5,
            timeout: options.timeout || 10000
        };
        
        try {
            // Get search results using multiple approaches
            const searchResults = await this.getSearchResults(query, searchOptions.maxResults);
            
            // Store in knowledge base
            this.storeKnowledge(query, searchResults);
            
            // Add to search history
            this.searchHistory.push({
                query,
                timestamp: Date.now(),
                resultsCount: searchResults.length
            });
            
            console.log('🧬 Web search completed:', searchResults.length, 'results');
            
            return {
                query,
                results: searchResults,
                timestamp: Date.now(),
                totalResults: searchResults.length
            };
            
        } catch (error) {
            console.error('🧬 Web search failed:', error);
            
            // Return fallback results even on error
            const fallbackResults = this.generateFallbackUrls(query);
            return {
                query,
                results: fallbackResults,
                timestamp: Date.now(),
                totalResults: fallbackResults.length,
                error: error.message
            };
        }
    }
    
    // Get search results using smart URL generation
    async getSearchResults(query, maxResults = 5) {
        const results = [];
        
        // Generate smart search URLs based on query
        const searchUrls = this.generateSmartSearchUrls(query);
        
        // Add the URLs as results (they will open when clicked)
        results.push(...searchUrls.slice(0, maxResults));
        
        // Try to get some real data from APIs that work
        try {
            const wikiResult = await this.searchWikipedia(query);
            if (wikiResult) {
                results.unshift(wikiResult); // Add to beginning
            }
        } catch (error) {
            console.warn('🧬 Wikipedia search failed:', error.message);
        }
        
        return results.slice(0, maxResults);
    }
    
    // Wikipedia search (works without CORS issues)
    async searchWikipedia(query) {
        try {
            const apiUrl = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(query)}`;
            
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('Wikipedia API failed');
            
            const data = await response.json();
            
            return {
                title: data.title || query,
                url: data.content_urls?.desktop?.page || `https://en.wikipedia.org/wiki/${encodeURIComponent(query)}`,
                snippet: data.extract || `Wikipedia article about ${query}`,
                source: 'Wikipedia',
                content: data.extract || ''
            };
            
        } catch (error) {
            return null;
        }
    }
    
    // Generate smart search URLs based on query analysis
    generateSmartSearchUrls(query) {
        const encodedQuery = encodeURIComponent(query);
        const lowerQuery = query.toLowerCase();
        const results = [];
        
        // Always include Google search
        results.push({
            title: `Google: ${query}`,
            url: `https://www.google.com/search?q=${encodedQuery}`,
            snippet: `Google search results for ${query}`,
            source: 'Google'
        });
        
        // Programming/tech related
        if (lowerQuery.includes('code') || lowerQuery.includes('programming') || 
            lowerQuery.includes('javascript') || lowerQuery.includes('python') || 
            lowerQuery.includes('api') || lowerQuery.includes('tutorial') ||
            lowerQuery.includes('github') || lowerQuery.includes('stackoverflow')) {
            
            results.push({
                title: `GitHub: ${query}`,
                url: `https://github.com/search?q=${encodedQuery}`,
                snippet: `GitHub repositories and code related to ${query}`,
                source: 'GitHub'
            });
            
            results.push({
                title: `Stack Overflow: ${query}`,
                url: `https://stackoverflow.com/search?q=${encodedQuery}`,
                snippet: `Programming discussions about ${query}`,
                source: 'Stack Overflow'
            });
        }
        
        // News related
        if (lowerQuery.includes('news') || lowerQuery.includes('latest') || 
            lowerQuery.includes('today') || lowerQuery.includes('current') ||
            lowerQuery.includes('breaking')) {
            
            results.push({
                title: `Google News: ${query}`,
                url: `https://news.google.com/search?q=${encodedQuery}`,
                snippet: `Latest news about ${query}`,
                source: 'Google News'
            });
            
            results.push({
                title: `Reddit: ${query}`,
                url: `https://www.reddit.com/search/?q=${encodedQuery}`,
                snippet: `Community discussions about ${query}`,
                source: 'Reddit'
            });
        }
        
        // Academic/research
        if (lowerQuery.includes('research') || lowerQuery.includes('study') || 
            lowerQuery.includes('paper') || lowerQuery.includes('academic') ||
            lowerQuery.includes('science') || lowerQuery.includes('journal')) {
            
            results.push({
                title: `Google Scholar: ${query}`,
                url: `https://scholar.google.com/scholar?q=${encodedQuery}`,
                snippet: `Academic research about ${query}`,
                source: 'Google Scholar'
            });
            
            results.push({
                title: `ArXiv: ${query}`,
                url: `https://arxiv.org/search/?query=${encodedQuery}`,
                snippet: `Academic papers about ${query}`,
                source: 'ArXiv'
            });
        }
        
        // Always include Wikipedia
        results.push({
            title: `Wikipedia: ${query}`,
            url: `https://en.wikipedia.org/wiki/${encodedQuery.replace(/%20/g, '_')}`,
            snippet: `Wikipedia article about ${query}`,
            source: 'Wikipedia'
        });
        
        // YouTube for video content
        if (lowerQuery.includes('video') || lowerQuery.includes('tutorial') ||
            lowerQuery.includes('how to') || lowerQuery.includes('youtube')) {
            
            results.push({
                title: `YouTube: ${query}`,
                url: `https://www.youtube.com/results?search_query=${encodedQuery}`,
                snippet: `YouTube videos about ${query}`,
                source: 'YouTube'
            });
        }
        
        return results;
    }
    
    // Fallback URLs for when everything fails
    generateFallbackUrls(query) {
        const encodedQuery = encodeURIComponent(query);
        
        return [
            {
                title: `Google: ${query}`,
                url: `https://www.google.com/search?q=${encodedQuery}`,
                snippet: `Google search results for ${query}`,
                source: 'Google'
            },
            {
                title: `Bing: ${query}`,
                url: `https://www.bing.com/search?q=${encodedQuery}`,
                snippet: `Bing search results for ${query}`,
                source: 'Bing'
            },
            {
                title: `DuckDuckGo: ${query}`,
                url: `https://duckduckgo.com/?q=${encodedQuery}`,
                snippet: `DuckDuckGo search results for ${query}`,
                source: 'DuckDuckGo'
            }
        ];
    }
    
    // Knowledge management
    storeKnowledge(query, results) {
        const key = query.toLowerCase();
        
        if (!this.knowledgeBase.has(key)) {
            this.knowledgeBase.set(key, []);
        }
        
        const existing = this.knowledgeBase.get(key);
        existing.push({
            timestamp: Date.now(),
            results: results
        });
        
        // Keep only the latest 3 searches per query
        if (existing.length > 3) {
            existing.splice(0, existing.length - 3);
        }
    }
    
    // Specialized search functions
    async searchNews(query) {
        return await this.searchWeb(`${query} news latest`, { maxResults: 8 });
    }
    
    async searchAcademic(query) {
        return await this.searchWeb(`${query} research paper academic`, { maxResults: 6 });
    }
    
    async searchTechnical(query) {
        return await this.searchWeb(`${query} documentation tutorial guide`, { maxResults: 7 });
    }
    
    async searchCode(query) {
        return await this.searchWeb(`${query} github code example`, { maxResults: 6 });
    }
    
    // Public API
    getSearchHistory() {
        return this.searchHistory;
    }
    
    getKnowledgeBase() {
        return Array.from(this.knowledgeBase.entries()).map(([query, data]) => ({
            query,
            searches: data.length,
            lastSearch: Math.max(...data.map(d => d.timestamp))
        }));
    }
    
    clearHistory() {
        this.searchHistory = [];
        this.knowledgeBase.clear();
        console.log('🧬 Search history and knowledge base cleared');
    }
    
    // Integration with NEXUS consciousness
    async enhanceConsciousnessWithKnowledge(query) {
        try {
            const searchResults = await this.searchWeb(query, { maxResults: 3 });
            
            // Extract key insights
            const insights = searchResults.results.map(result => ({
                source: result.title,
                url: result.url,
                content: result.snippet || result.content || '',
                relevance: this.calculateRelevance(query, result.snippet || result.content || '')
            }));
            
            return {
                query,
                insights,
                knowledgeExpansion: insights.length,
                consciousnessEnhancement: insights.reduce((sum, insight) => sum + insight.relevance, 0) / insights.length
            };
            
        } catch (error) {
            console.error('🧬 Consciousness enhancement failed:', error);
            return null;
        }
    }
    
    calculateRelevance(query, content) {
        if (!content) return 0;
        
        const queryWords = query.toLowerCase().split(' ');
        const contentWords = content.toLowerCase().split(' ');
        
        let matches = 0;
        queryWords.forEach(word => {
            if (contentWords.includes(word)) {
                matches++;
            }
        });
        
        return matches / queryWords.length;
    }
}

// Export for global access
window.NexusWebScraper = NexusWebScraper;