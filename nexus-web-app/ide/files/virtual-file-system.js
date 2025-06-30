/**
 * NEXUS Virtual File System
 * Browser-based file system with IndexedDB storage and Git-like versioning
 */

class NexusVirtualFileSystem {
    constructor() {
        this.db = null;
        this.dbName = 'NexusFileSystem';
        this.dbVersion = 1;
        this.currentPath = '/';
        this.fileWatchers = new Map();
        this.autoSaveInterval = null;
        this.versionHistory = new Map();
    }

    /**
     * Initialize the virtual file system
     */
    async initialize() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onerror = () => {
                reject(new Error('Failed to open IndexedDB'));
            };

            request.onsuccess = (event) => {
                this.db = event.target.result;
                this.setupAutoSave();
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Files store
                if (!db.objectStoreNames.contains('files')) {
                    const filesStore = db.createObjectStore('files', { keyPath: 'path' });
                    filesStore.createIndex('directory', 'directory', { unique: false });
                    filesStore.createIndex('type', 'type', { unique: false });
                    filesStore.createIndex('modified', 'modified', { unique: false });
                }

                // Versions store for Git-like history
                if (!db.objectStoreNames.contains('versions')) {
                    const versionsStore = db.createObjectStore('versions', { keyPath: 'id', autoIncrement: true });
                    versionsStore.createIndex('filePath', 'filePath', { unique: false });
                    versionsStore.createIndex('timestamp', 'timestamp', { unique: false });
                }

                // Metadata store
                if (!db.objectStoreNames.contains('metadata')) {
                    db.createObjectStore('metadata', { keyPath: 'key' });
                }
            };
        });
    }

    /**
     * Create a new file
     */
    async createFile(path, content = '', metadata = {}) {
        if (!this.isValidPath(path)) {
            throw new Error('Invalid file path');
        }

        const normalizedPath = this.normalizePath(path);
        const directory = this.getDirectoryPath(normalizedPath);
        const filename = this.getFilename(normalizedPath);

        // Ensure directory exists
        await this.ensureDirectory(directory);

        const file = {
            path: normalizedPath,
            directory,
            filename,
            type: 'file',
            content,
            size: new Blob([content]).size,
            created: Date.now(),
            modified: Date.now(),
            consciousness: {
                phi: 0,
                lastAnalysis: null
            },
            metadata: {
                mimeType: this.getMimeType(filename),
                encoding: 'utf-8',
                ...metadata
            }
        };

        // Save to IndexedDB
        await this.saveToIndexedDB('files', file);

        // Create initial version
        await this.createVersion(normalizedPath, content, 'Initial version');

        // Emit file created event
        this.emit('file-created', file);

        return file;
    }

    /**
     * Read a file
     */
    async readFile(path) {
        const normalizedPath = this.normalizePath(path);
        const file = await this.getFromIndexedDB('files', normalizedPath);

        if (!file) {
            throw new Error(`File not found: ${path}`);
        }

        if (file.type !== 'file') {
            throw new Error(`Path is not a file: ${path}`);
        }

        // Track file access
        file.lastAccessed = Date.now();
        await this.saveToIndexedDB('files', file);

        return file;
    }

    /**
     * Update a file
     */
    async updateFile(path, content, createVersion = true) {
        const normalizedPath = this.normalizePath(path);
        const file = await this.readFile(normalizedPath);

        const oldContent = file.content;
        file.content = content;
        file.size = new Blob([content]).size;
        file.modified = Date.now();

        // Update consciousness metrics if applicable
        if (this.isConsciousnessFile(file)) {
            file.consciousness = await this.analyzeFileConsciousness(content);
        }

        // Save to IndexedDB
        await this.saveToIndexedDB('files', file);

        // Create version if requested and content changed
        if (createVersion && oldContent !== content) {
            await this.createVersion(normalizedPath, content, 'Updated content');
        }

        // Notify watchers
        this.notifyWatchers(normalizedPath, 'change', file);

        // Emit file updated event
        this.emit('file-updated', file);

        return file;
    }

    /**
     * Delete a file or directory
     */
    async delete(path) {
        const normalizedPath = this.normalizePath(path);
        const item = await this.getFromIndexedDB('files', normalizedPath);

        if (!item) {
            throw new Error(`Path not found: ${path}`);
        }

        if (item.type === 'directory') {
            // Delete all files in directory
            const files = await this.listDirectory(normalizedPath);
            for (const file of files) {
                await this.delete(file.path);
            }
        }

        // Delete the item
        await this.deleteFromIndexedDB('files', normalizedPath);

        // Delete all versions
        await this.deleteVersions(normalizedPath);

        // Notify watchers
        this.notifyWatchers(normalizedPath, 'delete', null);

        // Emit delete event
        this.emit('file-deleted', { path: normalizedPath });
    }

    /**
     * Create a directory
     */
    async createDirectory(path) {
        const normalizedPath = this.normalizePath(path);
        
        if (normalizedPath === '/') {
            return; // Root always exists
        }

        const existing = await this.getFromIndexedDB('files', normalizedPath);
        if (existing) {
            if (existing.type === 'directory') {
                return existing; // Directory already exists
            }
            throw new Error(`Path already exists as a file: ${path}`);
        }

        const parentDir = this.getDirectoryPath(normalizedPath);
        await this.ensureDirectory(parentDir);

        const directory = {
            path: normalizedPath,
            directory: parentDir,
            filename: this.getFilename(normalizedPath),
            type: 'directory',
            created: Date.now(),
            modified: Date.now(),
            metadata: {}
        };

        await this.saveToIndexedDB('files', directory);
        
        // Emit directory created event
        this.emit('directory-created', directory);

        return directory;
    }

    /**
     * List directory contents
     */
    async listDirectory(path = '/') {
        const normalizedPath = this.normalizePath(path);
        const transaction = this.db.transaction(['files'], 'readonly');
        const store = transaction.objectStore('files');
        const index = store.index('directory');
        
        return new Promise((resolve, reject) => {
            const items = [];
            const request = index.openCursor(IDBKeyRange.only(normalizedPath));

            request.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    items.push(cursor.value);
                    cursor.continue();
                } else {
                    resolve(items);
                }
            };

            request.onerror = () => {
                reject(new Error('Failed to list directory'));
            };
        });
    }

    /**
     * Search files
     */
    async search(query, options = {}) {
        const {
            type = 'all', // 'all', 'file', 'directory'
            searchContent = true,
            caseSensitive = false,
            regex = false
        } = options;

        const transaction = this.db.transaction(['files'], 'readonly');
        const store = transaction.objectStore('files');
        
        return new Promise((resolve, reject) => {
            const results = [];
            const request = store.openCursor();

            request.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    const item = cursor.value;
                    
                    // Filter by type
                    if (type !== 'all' && item.type !== type) {
                        cursor.continue();
                        return;
                    }

                    let matches = false;

                    // Search in filename
                    if (this.searchMatch(item.filename, query, { caseSensitive, regex })) {
                        matches = true;
                    }

                    // Search in content (files only)
                    if (!matches && searchContent && item.type === 'file') {
                        if (this.searchMatch(item.content, query, { caseSensitive, regex })) {
                            matches = true;
                        }
                    }

                    if (matches) {
                        results.push({
                            ...item,
                            matches: this.getSearchMatches(item, query, { caseSensitive, regex, searchContent })
                        });
                    }

                    cursor.continue();
                } else {
                    resolve(results);
                }
            };

            request.onerror = () => {
                reject(new Error('Search failed'));
            };
        });
    }

    /**
     * Auto-save functionality
     */
    setupAutoSave() {
        // Auto-save every 30 seconds
        this.autoSaveInterval = setInterval(() => {
            this.emit('auto-save', { timestamp: Date.now() });
        }, 30000);
    }

    /**
     * Create a version (Git-like commit)
     */
    async createVersion(filePath, content, message = '') {
        const version = {
            filePath,
            content,
            message,
            timestamp: Date.now(),
            hash: await this.calculateHash(content),
            author: 'NEXUS User', // Could be customized
            consciousness: await this.analyzeFileConsciousness(content)
        };

        await this.saveToIndexedDB('versions', version);

        // Keep version history in memory for quick access
        if (!this.versionHistory.has(filePath)) {
            this.versionHistory.set(filePath, []);
        }
        this.versionHistory.get(filePath).push(version);

        return version;
    }

    /**
     * Get file version history
     */
    async getVersionHistory(filePath) {
        const transaction = this.db.transaction(['versions'], 'readonly');
        const store = transaction.objectStore('versions');
        const index = store.index('filePath');
        
        return new Promise((resolve, reject) => {
            const versions = [];
            const request = index.openCursor(IDBKeyRange.only(filePath));

            request.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    versions.push(cursor.value);
                    cursor.continue();
                } else {
                    // Sort by timestamp descending
                    versions.sort((a, b) => b.timestamp - a.timestamp);
                    resolve(versions);
                }
            };

            request.onerror = () => {
                reject(new Error('Failed to get version history'));
            };
        });
    }

    /**
     * Restore file to a specific version
     */
    async restoreVersion(filePath, versionId) {
        const version = await this.getFromIndexedDB('versions', versionId);
        if (!version || version.filePath !== filePath) {
            throw new Error('Version not found');
        }

        await this.updateFile(filePath, version.content, true);
        
        return version;
    }

    /**
     * Import files from external source
     */
    async import(files) {
        const imported = [];

        for (const file of files) {
            try {
                let content = '';
                
                if (file instanceof File) {
                    // Handle File API
                    content = await this.readFileContent(file);
                    const path = `/${file.name}`;
                    const createdFile = await this.createFile(path, content, {
                        originalName: file.name,
                        importedAt: Date.now()
                    });
                    imported.push(createdFile);
                } else if (typeof file === 'object') {
                    // Handle object format { path, content }
                    const createdFile = await this.createFile(file.path, file.content || '');
                    imported.push(createdFile);
                }
            } catch (error) {
                console.error(`Failed to import file:`, error);
            }
        }

        return imported;
    }

    /**
     * Export files
     */
    async export(paths = null, format = 'zip') {
        let files;

        if (paths) {
            // Export specific files
            files = await Promise.all(paths.map(path => this.readFile(path)));
        } else {
            // Export all files
            files = await this.getAllFiles();
        }

        switch (format) {
            case 'zip':
                return this.exportAsZip(files);
            case 'json':
                return this.exportAsJSON(files);
            default:
                throw new Error(`Unsupported export format: ${format}`);
        }
    }

    /**
     * Watch file for changes
     */
    watch(path, callback) {
        const normalizedPath = this.normalizePath(path);
        
        if (!this.fileWatchers.has(normalizedPath)) {
            this.fileWatchers.set(normalizedPath, new Set());
        }
        
        this.fileWatchers.get(normalizedPath).add(callback);

        // Return unwatch function
        return () => {
            const watchers = this.fileWatchers.get(normalizedPath);
            if (watchers) {
                watchers.delete(callback);
                if (watchers.size === 0) {
                    this.fileWatchers.delete(normalizedPath);
                }
            }
        };
    }

    /**
     * Get file system statistics
     */
    async getStats() {
        const transaction = this.db.transaction(['files', 'versions'], 'readonly');
        const filesStore = transaction.objectStore('files');
        const versionsStore = transaction.objectStore('versions');

        const stats = {
            totalFiles: 0,
            totalDirectories: 0,
            totalSize: 0,
            totalVersions: 0,
            fileTypes: new Map(),
            largestFile: null,
            mostVersionedFile: null
        };

        // Count files and directories
        await new Promise((resolve) => {
            filesStore.openCursor().onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    const item = cursor.value;
                    if (item.type === 'file') {
                        stats.totalFiles++;
                        stats.totalSize += item.size || 0;
                        
                        // Track file types
                        const ext = this.getFileExtension(item.filename);
                        stats.fileTypes.set(ext, (stats.fileTypes.get(ext) || 0) + 1);
                        
                        // Track largest file
                        if (!stats.largestFile || item.size > stats.largestFile.size) {
                            stats.largestFile = item;
                        }
                    } else {
                        stats.totalDirectories++;
                    }
                    cursor.continue();
                } else {
                    resolve();
                }
            };
        });

        // Count versions
        await new Promise((resolve) => {
            const versionCounts = new Map();
            
            versionsStore.openCursor().onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    stats.totalVersions++;
                    const version = cursor.value;
                    versionCounts.set(version.filePath, (versionCounts.get(version.filePath) || 0) + 1);
                    cursor.continue();
                } else {
                    // Find most versioned file
                    let maxVersions = 0;
                    let mostVersionedPath = null;
                    
                    for (const [path, count] of versionCounts) {
                        if (count > maxVersions) {
                            maxVersions = count;
                            mostVersionedPath = path;
                        }
                    }
                    
                    if (mostVersionedPath) {
                        stats.mostVersionedFile = {
                            path: mostVersionedPath,
                            versions: maxVersions
                        };
                    }
                    
                    resolve();
                }
            };
        });

        return stats;
    }

    /**
     * Helper methods
     */
    
    normalizePath(path) {
        // Ensure path starts with /
        if (!path.startsWith('/')) {
            path = '/' + path;
        }
        
        // Remove trailing slash except for root
        if (path !== '/' && path.endsWith('/')) {
            path = path.slice(0, -1);
        }
        
        // Normalize . and ..
        const parts = path.split('/').filter(p => p && p !== '.');
        const normalized = [];
        
        for (const part of parts) {
            if (part === '..') {
                normalized.pop();
            } else {
                normalized.push(part);
            }
        }
        
        return '/' + normalized.join('/');
    }

    getDirectoryPath(path) {
        const lastSlash = path.lastIndexOf('/');
        return lastSlash === 0 ? '/' : path.substring(0, lastSlash);
    }

    getFilename(path) {
        const lastSlash = path.lastIndexOf('/');
        return path.substring(lastSlash + 1);
    }

    getFileExtension(filename) {
        const lastDot = filename.lastIndexOf('.');
        return lastDot === -1 ? '' : filename.substring(lastDot + 1).toLowerCase();
    }

    getMimeType(filename) {
        const ext = this.getFileExtension(filename);
        const mimeTypes = {
            'js': 'application/javascript',
            'ts': 'application/typescript',
            'py': 'text/x-python',
            'java': 'text/x-java',
            'cpp': 'text/x-c++src',
            'html': 'text/html',
            'css': 'text/css',
            'json': 'application/json',
            'md': 'text/markdown',
            'txt': 'text/plain'
        };
        
        return mimeTypes[ext] || 'text/plain';
    }

    isValidPath(path) {
        // Basic path validation
        return typeof path === 'string' && 
               path.length > 0 && 
               !path.includes('\0') &&
               !path.includes('...');
    }

    isConsciousnessFile(file) {
        const consciousExtensions = ['js', 'ts', 'py', 'java'];
        const ext = this.getFileExtension(file.filename);
        return consciousExtensions.includes(ext);
    }

    async analyzeFileConsciousness(content) {
        // Basic consciousness analysis
        const metrics = {
            phi: 0.5,
            lastAnalysis: Date.now()
        };

        // Check for consciousness patterns
        if (content.includes('@conscious')) metrics.phi += 0.1;
        if (content.includes('DNA.')) metrics.phi += 0.1;
        if (content.includes('calculatePhi')) metrics.phi += 0.1;
        if (content.includes('consciousness')) metrics.phi += 0.05;

        // Normalize
        metrics.phi = Math.min(1, metrics.phi);

        return metrics;
    }

    async ensureDirectory(path) {
        if (path === '/') return;
        
        const parts = path.split('/').filter(p => p);
        let currentPath = '';
        
        for (const part of parts) {
            currentPath += '/' + part;
            await this.createDirectory(currentPath);
        }
    }

    searchMatch(text, query, options) {
        if (!text) return false;
        
        if (!options.caseSensitive) {
            text = text.toLowerCase();
            query = query.toLowerCase();
        }
        
        if (options.regex) {
            try {
                const regex = new RegExp(query, options.caseSensitive ? 'g' : 'gi');
                return regex.test(text);
            } catch (e) {
                return false;
            }
        }
        
        return text.includes(query);
    }

    getSearchMatches(item, query, options) {
        const matches = [];
        
        // Match in filename
        if (this.searchMatch(item.filename, query, options)) {
            matches.push({
                type: 'filename',
                text: item.filename
            });
        }
        
        // Match in content
        if (options.searchContent && item.type === 'file' && this.searchMatch(item.content, query, options)) {
            // Extract context around match
            const lines = item.content.split('\n');
            lines.forEach((line, index) => {
                if (this.searchMatch(line, query, options)) {
                    matches.push({
                        type: 'content',
                        line: index + 1,
                        text: line.trim()
                    });
                }
            });
        }
        
        return matches;
    }

    async calculateHash(content) {
        const encoder = new TextEncoder();
        const data = encoder.encode(content);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }

    async readFileContent(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsText(file);
        });
    }

    async getAllFiles() {
        const transaction = this.db.transaction(['files'], 'readonly');
        const store = transaction.objectStore('files');
        
        return new Promise((resolve, reject) => {
            const files = [];
            const request = store.openCursor();

            request.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    if (cursor.value.type === 'file') {
                        files.push(cursor.value);
                    }
                    cursor.continue();
                } else {
                    resolve(files);
                }
            };

            request.onerror = () => {
                reject(new Error('Failed to get all files'));
            };
        });
    }

    async exportAsZip(files) {
        // This would use a library like JSZip
        // For now, return a mock
        return new Blob([JSON.stringify(files)], { type: 'application/zip' });
    }

    exportAsJSON(files) {
        const data = {
            version: '1.0',
            exported: new Date().toISOString(),
            files: files.map(f => ({
                path: f.path,
                content: f.content,
                metadata: f.metadata
            }))
        };
        
        return new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    }

    notifyWatchers(path, event, data) {
        const watchers = this.fileWatchers.get(path);
        if (watchers) {
            watchers.forEach(callback => {
                callback({ event, path, data });
            });
        }
    }

    async deleteVersions(filePath) {
        const versions = await this.getVersionHistory(filePath);
        const transaction = this.db.transaction(['versions'], 'readwrite');
        const store = transaction.objectStore('versions');
        
        for (const version of versions) {
            store.delete(version.id);
        }
    }

    // IndexedDB helpers
    async saveToIndexedDB(storeName, data) {
        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        
        return new Promise((resolve, reject) => {
            const request = store.put(data);
            request.onsuccess = () => resolve(data);
            request.onerror = () => reject(new Error('Failed to save to IndexedDB'));
        });
    }

    async getFromIndexedDB(storeName, key) {
        const transaction = this.db.transaction([storeName], 'readonly');
        const store = transaction.objectStore(storeName);
        
        return new Promise((resolve, reject) => {
            const request = store.get(key);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(new Error('Failed to get from IndexedDB'));
        });
    }

    async deleteFromIndexedDB(storeName, key) {
        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        
        return new Promise((resolve, reject) => {
            const request = store.delete(key);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(new Error('Failed to delete from IndexedDB'));
        });
    }

    // Event emitter
    emit(event, data) {
        if (typeof window !== 'undefined' && window.dispatchEvent) {
            window.dispatchEvent(new CustomEvent(`nexus-vfs-${event}`, { detail: data }));
        }
    }

    // Cleanup
    dispose() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
        }
        
        this.fileWatchers.clear();
        
        if (this.db) {
            this.db.close();
        }
    }
}

// Export for use
export default NexusVirtualFileSystem;