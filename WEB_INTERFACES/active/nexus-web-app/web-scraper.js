/**
 * 🧬 NEXUS Web Scraper Integration
 * Unlimited Internet Search and Knowledge Acquisition
 * Using Firecrawl API for comprehensive web scraping
 */

class NexusWebScraper {
    constructor() {
        this.firecrawlApiKey = null;
        this.firecrawlBaseUrl = 'https://api.firecrawl.dev/v0';
        this.isInitialized = false;
        this.searchHistory = [];
        this.knowledgeBase = new Map();
        
        console.log('🧬 NEXUS Web Scraper initialized');
    }
    
    async initialize(apiKey = null) {
        try {
            // Try to use provided API key or check for environment variable
            this.firecrawlApiKey = apiKey || this.getApiKeyFromStorage() || 'demo-key';
            
            // Test connection
            const testResult = await this.testConnection();
            
            if (testResult.success) {
                this.isInitialized = true;
                console.log('🧬 Firecrawl API connected successfully');
                return true;
            } else {
                console.log('🧬 Firecrawl API not available - using fallback scraping');
                this.initializeFallbackScraper();
                return false;
            }
            
        } catch (error) {
            console.error('🧬 Web scraper initialization failed:', error);
            this.initializeFallbackScraper();
            return false;
        }
    }
    
    async testConnection() {
        try {
            // Test with a simple request
            const response = await fetch(`${this.firecrawlBaseUrl}/scrape`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.firecrawlApiKey}`
                },
                body: JSON.stringify({
                    url: 'https://example.com',
                    formats: ['markdown']
                })
            });
            
            return { success: response.ok };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    initializeFallbackScraper() {
        console.log('🧬 Initializing fallback web scraper...');
        this.isInitialized = true;
        
        // Use CORS proxy for fallback scraping
        this.corsProxy = 'https://api.allorigins.win/get?url=';
    }
    
    // Main search function
    async searchWeb(query, options = {}) {
        console.log('🧬 Searching web for:', query);
        
        const searchOptions = {
            maxResults: options.maxResults || 5,
            includeContent: options.includeContent !== false,
            formats: options.formats || ['markdown', 'text'],
            timeout: options.timeout || 30000
        };
        
        try {
            // First, get search results
            const searchResults = await this.getSearchResults(query, searchOptions.maxResults);
            
            // Then scrape content from each result
            const scrapedResults = [];
            
            for (const result of searchResults) {
                try {
                    const content = await this.scrapeUrl(result.url, searchOptions);
                    
                    if (content && content.text) {
                        scrapedResults.push({
                            ...result,
                            content: content.text,
                            markdown: content.markdown,
                            scrapedAt: Date.now()
                        });
                    }
                    
                    // Add delay to be respectful
                    await this.delay(1000);
                    
                } catch (error) {
                    console.warn('🧬 Failed to scrape:', result.url, error.message);
                    
                    // Add result without content
                    scrapedResults.push({
                        ...result,
                        content: result.snippet || '',
                        error: error.message
                    });
                }
            }
            
            // Store in knowledge base
            this.storeKnowledge(query, scrapedResults);
            
            // Add to search history
            this.searchHistory.push({
                query,
                timestamp: Date.now(),
                resultsCount: scrapedResults.length
            });
            
            console.log('🧬 Web search completed:', scrapedResults.length, 'results');
            
            return {
                query,
                results: scrapedResults,
                timestamp: Date.now(),
                totalResults: scrapedResults.length
            };
            
        } catch (error) {
            console.error('🧬 Web search failed:', error);
            throw error;
        }
    }
    
    // Get search results using multiple search engines
    async getSearchResults(query, maxResults = 5) {
        console.log('🧬 Getting search results for:', query);
        
        // Use multiple search approaches
        const results = [];
        
        try {
            // Try SerpAPI (free tier available)
            const serpResults = await this.searchWithSerpAPI(query, maxResults);
            results.push(...serpResults);
        } catch (error) {
            console.warn('🧬 SerpAPI failed:', error.message);
        }
        
        try {
            // Try DuckDuckGo Instant Answer API
            const ddgResults = await this.searchWithDuckDuckGo(query);
            results.push(...ddgResults);
        } catch (error) {
            console.warn('🧬 DuckDuckGo failed:', error.message);
        }
        
        // If we still don't have enough results, generate smart fallback URLs
        if (results.length < maxResults) {
            const fallbackUrls = await this.generateSmartFallbackUrls(query);
            results.push(...fallbackUrls.slice(0, maxResults - results.length));
        }
        
        // Remove duplicates and limit results
        const uniqueResults = this.removeDuplicateUrls(results);
        return uniqueResults.slice(0, maxResults);
    }
    
    async searchWithSerpAPI(query, maxResults) {
        // Use free SerpAPI alternative - SearchAPI.io (has free tier)
        const apiUrl = `https://www.searchapi.io/api/v1/search?engine=google&q=${encodeURIComponent(query)}&api_key=demo`;
        
        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('SearchAPI failed');
            
            const data = await response.json();
            const results = [];
            
            if (data.organic_results) {
                for (const result of data.organic_results.slice(0, maxResults)) {
                    results.push({
                        title: result.title || 'No title',
                        url: result.link || result.url,
                        snippet: result.snippet || result.description || '',
                        source: 'Google'
                    });
                }
            }
            
            return results;
        } catch (error) {
            console.warn('🧬 SearchAPI failed:', error.message);
            return [];
        }
    }
    
    async searchWithDuckDuckGo(query) {
        // Use DuckDuckGo Instant Answer API (CORS-friendly)
        const apiUrl = `https://api.duckduckgo.com/?q=${encodeURIComponent(query)}&format=json&no_html=1&skip_disambig=1`;
        
        try {
            const response = await fetch(apiUrl, {
                mode: 'cors',
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            if (!response.ok) throw new Error('DuckDuckGo API failed');
            
            const data = await response.json();
            const results = [];
            
            // Process RelatedTopics
            if (data.RelatedTopics && Array.isArray(data.RelatedTopics)) {
                for (const topic of data.RelatedTopics.slice(0, 3)) {
                    if (topic.FirstURL && topic.Text) {
                        results.push({
                            title: topic.Text.split(' - ')[0] || topic.Text.substring(0, 100),
                            url: topic.FirstURL,
                            snippet: topic.Text,
                            source: 'DuckDuckGo'
                        });
                    }
                }
            }
            
            // Process Answer if available
            if (data.Answer && data.AnswerType) {
                results.push({
                    title: `${data.AnswerType}: ${query}`,
                    url: data.AbstractURL || `https://duckduckgo.com/?q=${encodeURIComponent(query)}`,
                    snippet: data.Answer,
                    source: 'DuckDuckGo Answer'
                });
            }
            
            return results;
        } catch (error) {
            console.warn('🧬 DuckDuckGo search failed:', error.message);
            return [];
        }
    }
    
    async generateFallbackUrls(query) {
        // Generate some likely URLs based on the query
        const encodedQuery = encodeURIComponent(query);
        
        return [
            {
                title: `Wikipedia: ${query}`,
                url: `https://en.wikipedia.org/wiki/${encodedQuery.replace(/%20/g, '_')}`,
                snippet: `Wikipedia article about ${query}`,
                source: 'Wikipedia'
            },
            {
                title: `GitHub: ${query}`,
                url: `https://github.com/search?q=${encodedQuery}`,
                snippet: `GitHub repositories related to ${query}`,
                source: 'GitHub'
            },
            {
                title: `Stack Overflow: ${query}`,
                url: `https://stackoverflow.com/search?q=${encodedQuery}`,
                snippet: `Stack Overflow discussions about ${query}`,
                source: 'Stack Overflow'
            },
            {
                title: `Reddit: ${query}`,
                url: `https://www.reddit.com/search/?q=${encodedQuery}`,
                snippet: `Reddit discussions about ${query}`,
                source: 'Reddit'
            },
            {
                title: `ArXiv: ${query}`,
                url: `https://arxiv.org/search/?query=${encodedQuery}`,
                snippet: `Academic papers about ${query}`,
                source: 'ArXiv'
            }
        ];
    }
    
    // Scrape individual URL
    async scrapeUrl(url, options = {}) {
        try {
            if (this.firecrawlApiKey && this.firecrawlApiKey !== 'demo-key') {
                return await this.scrapeWithFirecrawl(url, options);
            } else {
                return await this.scrapeWithFallback(url, options);
            }
            
        } catch (error) {
            console.error('🧬 URL scraping failed:', url, error.message);
            throw error;
        }
    }
    
    async scrapeWithFirecrawl(url, options) {
        const response = await fetch(`${this.firecrawlBaseUrl}/scrape`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.firecrawlApiKey}`
            },
            body: JSON.stringify({
                url: url,
                formats: options.formats || ['markdown', 'text'],
                onlyMainContent: true,
                includeTags: ['title', 'meta'],
                excludeTags: ['nav', 'footer', 'aside', 'script', 'style'],
                waitFor: 2000
            })
        });
        
        if (!response.ok) {
            throw new Error(`Firecrawl API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        return {
            text: data.data?.text || '',
            markdown: data.data?.markdown || '',
            title: data.data?.metadata?.title || '',
            description: data.data?.metadata?.description || '',
            url: url
        };
    }
    
    async scrapeWithFallback(url, options) {
        // Use CORS proxy to fetch content
        const proxyUrl = `${this.corsProxy}${encodeURIComponent(url)}`;
        
        const response = await fetch(proxyUrl);
        const data = await response.json();
        
        if (!data.contents) {
            throw new Error('No content received from proxy');
        }
        
        // Parse HTML content
        const parser = new DOMParser();
        const doc = parser.parseFromString(data.contents, 'text/html');
        
        // Extract text content
        const title = doc.querySelector('title')?.textContent || '';
        const description = doc.querySelector('meta[name="description"]')?.getAttribute('content') || '';
        
        // Remove script and style elements
        const scripts = doc.querySelectorAll('script, style, nav, footer, aside');
        scripts.forEach(el => el.remove());
        
        // Get main content
        const mainContent = doc.querySelector('main, article, .content, #content, .post, .entry') || doc.body;
        const text = mainContent ? mainContent.textContent.trim() : '';
        
        // Convert to markdown (simple conversion)
        const markdown = this.htmlToMarkdown(mainContent?.innerHTML || '');
        
        return {
            text: text.substring(0, 10000), // Limit text length
            markdown: markdown.substring(0, 10000),
            title,
            description,
            url
        };
    }
    
    htmlToMarkdown(html) {
        // Simple HTML to Markdown conversion
        return html
            .replace(/<h1[^>]*>(.*?)<\/h1>/gi, '# $1\n\n')
            .replace(/<h2[^>]*>(.*?)<\/h2>/gi, '## $1\n\n')
            .replace(/<h3[^>]*>(.*?)<\/h3>/gi, '### $1\n\n')
            .replace(/<p[^>]*>(.*?)<\/p>/gi, '$1\n\n')
            .replace(/<strong[^>]*>(.*?)<\/strong>/gi, '**$1**')
            .replace(/<em[^>]*>(.*?)<\/em>/gi, '*$1*')
            .replace(/<a[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>/gi, '[$2]($1)')
            .replace(/<br[^>]*>/gi, '\n')
            .replace(/<[^>]*>/g, '') // Remove remaining HTML tags
            .replace(/\n\s*\n\s*\n/g, '\n\n') // Clean up extra newlines
            .trim();
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
    
    getStoredKnowledge(query) {
        const key = query.toLowerCase();
        return this.knowledgeBase.get(key) || [];
    }
    
    // Specialized search functions
    async searchNews(query) {
        return await this.searchWeb(`${query} news latest`, {
            maxResults: 10,
            formats: ['text']
        });
    }
    
    async searchAcademic(query) {
        return await this.searchWeb(`${query} research paper academic`, {
            maxResults: 5,
            formats: ['markdown', 'text']
        });
    }
    
    async searchTechnical(query) {
        return await this.searchWeb(`${query} documentation tutorial guide`, {
            maxResults: 8,
            formats: ['markdown']
        });
    }
    
    async searchCode(query) {
        return await this.searchWeb(`${query} github code example`, {
            maxResults: 6,
            formats: ['text']
        });
    }
    
    // Utility methods
    async delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    getApiKeyFromStorage() {
        try {
            return localStorage.getItem('firecrawl_api_key');
        } catch {
            return null;
        }
    }
    
    setApiKey(apiKey) {
        this.firecrawlApiKey = apiKey;
        try {
            localStorage.setItem('firecrawl_api_key', apiKey);
        } catch {
            console.warn('🧬 Could not store API key in localStorage');
        }
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
                content: result.content.substring(0, 500) + '...',
                relevance: this.calculateRelevance(query, result.content)
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
    // Helper functions for improved search
    async generateSmartFallbackUrls(query) {
        // Generate intelligent URLs based on query analysis
        const encodedQuery = encodeURIComponent(query);
        const lowerQuery = query.toLowerCase();
        const results = [];
        
        // Always include Wikipedia
        results.push({
            title: `Wikipedia: ${query}`,
            url: `https://en.wikipedia.org/wiki/${encodedQuery.replace(/%20/g, '_')}`,
            snippet: `Wikipedia article about ${query}`,
            source: 'Wikipedia'
        });
        
        // Programming/tech related
        if (lowerQuery.includes('code') || lowerQuery.includes('programming') || 
            lowerQuery.includes('javascript') || lowerQuery.includes('python') || 
            lowerQuery.includes('api') || lowerQuery.includes('tutorial')) {
            
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
            lowerQuery.includes('today') || lowerQuery.includes('current')) {
            
            results.push({
                title: `Google News: ${query}`,
                url: `https://news.google.com/search?q=${encodedQuery}`,
                snippet: `Latest news about ${query}`,
                source: 'Google News'
            });
        }
        
        // Academic/research
        if (lowerQuery.includes('research') || lowerQuery.includes('study') || 
            lowerQuery.includes('paper') || lowerQuery.includes('academic')) {
            
            results.push({
                title: `ArXiv: ${query}`,
                url: `https://arxiv.org/search/?query=${encodedQuery}`,
                snippet: `Academic papers about ${query}`,
                source: 'ArXiv'
            });
            
            results.push({
                title: `Google Scholar: ${query}`,
                url: `https://scholar.google.com/scholar?q=${encodedQuery}`,
                snippet: `Academic research about ${query}`,
                source: 'Google Scholar'
            });
        }
        
        // Social/discussion
        results.push({
            title: `Reddit: ${query}`,
            url: `https://www.reddit.com/search/?q=${encodedQuery}`,
            snippet: `Community discussions about ${query}`,
            source: 'Reddit'
        });
        
        // General search engines as fallback
        results.push({
            title: `Bing: ${query}`,
            url: `https://www.bing.com/search?q=${encodedQuery}`,
            snippet: `Bing search results for ${query}`,
            source: 'Bing'
        });
        
        return results;
    }
    
    removeDuplicateUrls(results) {
        const seen = new Set();
        return results.filter(result => {
            if (seen.has(result.url)) {
                return false;
            }
            seen.add(result.url);
            return true;
        });
    }