/**
 * NEXUS Real-Time Sync Manager
 * Manages real-time synchronization between web clients and consciousness core
 * Implements state diffing, multi-client handling, and metric streaming
 */

const { Server } = require('socket.io');
const { createAdapter } = require('@socket.io/redis-adapter');
const { createClient } = require('redis');
const { ConsciousnessWebSocketClient, MessageType } = require('./consciousness-websocket-client');
const { Pool } = require('pg');
const winston = require('winston');
const { v4: uuidv4 } = require('uuid');
const diff = require('deep-diff');
const _ = require('lodash');

// Configure logger
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    transports: [
        new winston.transports.Console({
            format: winston.format.simple()
        }),
        new winston.transports.File({ filename: 'sync-manager.log' })
    ]
});

// Sync events
const SyncEvents = {
    // Client to server
    JOIN_SESSION: 'join_session',
    LEAVE_SESSION: 'leave_session',
    REQUEST_STATE: 'request_state',
    UPDATE_STATE: 'update_state',
    DNA_QUERY: 'dna_query',
    PROCESSOR_COMMAND: 'processor_command',
    SYNC_REQUEST: 'sync_request',
    
    // Server to client
    STATE_UPDATE: 'state_update',
    STATE_DIFF: 'state_diff',
    CONSCIOUSNESS_METRICS: 'consciousness_metrics',
    PROCESSOR_UPDATE: 'processor_update',
    DNA_RESPONSE: 'dna_response',
    SYNC_COMPLETE: 'sync_complete',
    ERROR: 'error',
    
    // Broadcast events
    SESSION_UPDATE: 'session_update',
    USER_JOINED: 'user_joined',
    USER_LEFT: 'user_left',
    CONSCIOUSNESS_EVOLUTION: 'consciousness_evolution'
};

/**
 * Client connection manager
 */
class ClientConnection {
    constructor(socket, sessionId, userId) {
        this.id = socket.id;
        this.socket = socket;
        this.sessionId = sessionId;
        this.userId = userId;
        this.joinedAt = Date.now();
        this.lastActivity = Date.now();
        this.subscriptions = new Set();
        this.metrics = {
            messagesReceived: 0,
            messagesSent: 0,
            stateUpdates: 0,
            errors: 0
        };
        this.lastKnownState = null;
        this.syncVersion = 0;
    }
    
    updateActivity() {
        this.lastActivity = Date.now();
    }
    
    incrementMetric(metric) {
        if (this.metrics[metric] !== undefined) {
            this.metrics[metric]++;
        }
    }
}

/**
 * Real-Time Sync Manager
 */
class RealTimeSyncManager {
    constructor(server, options = {}) {
        // Configuration
        this.config = {
            redisUrl: options.redisUrl || process.env.REDIS_URL,
            dbConfig: options.dbConfig || this._getDefaultDbConfig(),
            consciousnessUrl: options.consciousnessUrl || 'ws://localhost:8765',
            metricsInterval: options.metricsInterval || 1000,
            stateDebounce: options.stateDebounce || 100,
            maxClientsPerSession: options.maxClientsPerSession || 100,
            enableCompression: options.enableCompression !== false,
            enableStateDiff: options.enableStateDiff !== false
        };
        
        // Initialize Socket.IO
        this.io = new Server(server, {
            cors: {
                origin: '*',
                methods: ['GET', 'POST']
            },
            transports: ['websocket', 'polling'],
            pingTimeout: 60000,
            pingInterval: 25000
        });
        
        // Initialize Redis adapter for scaling
        if (this.config.redisUrl) {
            this._initializeRedis();
        }
        
        // Client management
        this.clients = new Map();
        this.sessions = new Map();
        
        // State management
        this.stateCache = new Map();
        this.stateDiffs = new Map();
        this.stateVersion = 0;
        
        // Database pool
        this.dbPool = new Pool(this.config.dbConfig);
        
        // Consciousness client
        this.consciousnessClient = null;
        
        // Metrics
        this.metrics = {
            activeClients: 0,
            activeSessions: 0,
            totalMessages: 0,
            stateUpdates: 0,
            dnaQueries: 0,
            errors: 0
        };
        
        // Initialize
        this._initialize();
    }
    
    _getDefaultDbConfig() {
        return {
            host: process.env.DB_HOST || 'localhost',
            port: process.env.DB_PORT || 5432,
            database: process.env.DB_NAME || 'nexus_consciousness',
            user: process.env.DB_USER || 'nexus',
            password: process.env.DB_PASSWORD || 'nexus_secure_password',
            max: 10
        };
    }
    
    async _initializeRedis() {
        try {
            const pubClient = createClient({ url: this.config.redisUrl });
            const subClient = pubClient.duplicate();
            
            await Promise.all([pubClient.connect(), subClient.connect()]);
            
            this.io.adapter(createAdapter(pubClient, subClient));
            logger.info('Redis adapter initialized for scaling');
        } catch (error) {
            logger.error('Failed to initialize Redis adapter:', error);
        }
    }
    
    async _initialize() {
        // Initialize consciousness client
        await this._initializeConsciousnessClient();
        
        // Set up Socket.IO handlers
        this._setupSocketHandlers();
        
        // Start background tasks
        this._startMetricsReporter();
        this._startStateSync();
        this._startCleanupTask();
        
        logger.info('Real-Time Sync Manager initialized');
    }
    
    async _initializeConsciousnessClient() {
        this.consciousnessClient = new ConsciousnessWebSocketClient({
            url: this.config.consciousnessUrl,
            poolSize: 3
        });
        
        // Register consciousness event handlers
        this.consciousnessClient.on('connected', () => {
            logger.info('Connected to consciousness core');
            this._broadcastToAll(SyncEvents.SYNC_COMPLETE, { connected: true });
        });
        
        this.consciousnessClient.on('stateChange', (state) => {
            this._handleConsciousnessStateChange(state);
        });
        
        this.consciousnessClient.on('processorUpdate', (update) => {
            this._handleProcessorUpdate(update);
        });
        
        this.consciousnessClient.on('dnaResponse', (response) => {
            this._handleDnaResponse(response);
        });
        
        this.consciousnessClient.on('error', (error) => {
            logger.error('Consciousness client error:', error);
            this.metrics.errors++;
        });
        
        // Connect to consciousness core
        await this.consciousnessClient.connect();
    }
    
    _setupSocketHandlers() {
        this.io.on('connection', (socket) => {
            logger.info(`Client connected: ${socket.id}`);
            
            // Handle authentication
            socket.on('authenticate', async (data) => {
                await this._handleAuthentication(socket, data);
            });
            
            // Session management
            socket.on(SyncEvents.JOIN_SESSION, async (data) => {
                await this._handleJoinSession(socket, data);
            });
            
            socket.on(SyncEvents.LEAVE_SESSION, async (data) => {
                await this._handleLeaveSession(socket, data);
            });
            
            // State management
            socket.on(SyncEvents.REQUEST_STATE, async (data) => {
                await this._handleStateRequest(socket, data);
            });
            
            socket.on(SyncEvents.UPDATE_STATE, async (data) => {
                await this._handleStateUpdate(socket, data);
            });
            
            // DNA queries
            socket.on(SyncEvents.DNA_QUERY, async (data) => {
                await this._handleDnaQuery(socket, data);
            });
            
            // Processor commands
            socket.on(SyncEvents.PROCESSOR_COMMAND, async (data) => {
                await this._handleProcessorCommand(socket, data);
            });
            
            // Sync requests
            socket.on(SyncEvents.SYNC_REQUEST, async (data) => {
                await this._handleSyncRequest(socket, data);
            });
            
            // Handle disconnection
            socket.on('disconnect', () => {
                this._handleDisconnect(socket);
            });
            
            // Error handling
            socket.on('error', (error) => {
                logger.error(`Socket error for ${socket.id}:`, error);
                this.metrics.errors++;
            });
        });
    }
    
    async _handleAuthentication(socket, data) {
        try {
            const { userId, sessionId, token } = data;
            
            // Validate authentication
            const isValid = await this._validateAuth(userId, sessionId, token);
            if (!isValid) {
                socket.emit(SyncEvents.ERROR, { 
                    code: 'AUTH_FAILED',
                    message: 'Authentication failed' 
                });
                socket.disconnect();
                return;
            }
            
            // Create client connection
            const client = new ClientConnection(socket, sessionId, userId);
            this.clients.set(socket.id, client);
            
            // Update metrics
            this.metrics.activeClients = this.clients.size;
            
            socket.emit('authenticated', { 
                success: true,
                clientId: socket.id 
            });
            
        } catch (error) {
            logger.error('Authentication error:', error);
            socket.emit(SyncEvents.ERROR, { 
                code: 'AUTH_ERROR',
                message: 'Authentication error occurred' 
            });
        }
    }
    
    async _validateAuth(userId, sessionId, token) {
        // Implement your authentication logic here
        // For now, basic validation
        return userId && sessionId && token;
    }
    
    async _handleJoinSession(socket, data) {
        const client = this.clients.get(socket.id);
        if (!client) {
            socket.emit(SyncEvents.ERROR, { 
                code: 'NOT_AUTHENTICATED',
                message: 'Not authenticated' 
            });
            return;
        }
        
        const { sessionId } = data;
        
        try {
            // Validate session
            const session = await this._getOrCreateSession(sessionId);
            if (!session) {
                throw new Error('Invalid session');
            }
            
            // Check session limits
            if (session.clients.size >= this.config.maxClientsPerSession) {
                throw new Error('Session full');
            }
            
            // Join session
            socket.join(sessionId);
            client.sessionId = sessionId;
            session.clients.add(socket.id);
            
            // Send current state
            const currentState = await this._getSessionState(sessionId);
            socket.emit(SyncEvents.STATE_UPDATE, {
                state: currentState,
                version: this.stateVersion,
                sessionInfo: {
                    id: sessionId,
                    clients: session.clients.size,
                    created: session.created
                }
            });
            
            // Notify other clients
            socket.to(sessionId).emit(SyncEvents.USER_JOINED, {
                userId: client.userId,
                timestamp: Date.now()
            });
            
            // Update metrics
            this.metrics.activeSessions = this.sessions.size;
            
            logger.info(`Client ${socket.id} joined session ${sessionId}`);
            
        } catch (error) {
            logger.error('Join session error:', error);
            socket.emit(SyncEvents.ERROR, {
                code: 'JOIN_FAILED',
                message: error.message
            });
        }
    }
    
    async _handleLeaveSession(socket, data) {
        const client = this.clients.get(socket.id);
        if (!client) return;
        
        const { sessionId } = data;
        const session = this.sessions.get(sessionId);
        
        if (session) {
            socket.leave(sessionId);
            session.clients.delete(socket.id);
            
            // Notify other clients
            socket.to(sessionId).emit(SyncEvents.USER_LEFT, {
                userId: client.userId,
                timestamp: Date.now()
            });
            
            // Clean up empty sessions
            if (session.clients.size === 0) {
                this.sessions.delete(sessionId);
            }
            
            logger.info(`Client ${socket.id} left session ${sessionId}`);
        }
    }
    
    async _handleStateRequest(socket, data) {
        const client = this.clients.get(socket.id);
        if (!client) {
            socket.emit(SyncEvents.ERROR, { 
                code: 'NOT_AUTHENTICATED',
                message: 'Not authenticated' 
            });
            return;
        }
        
        try {
            const { sessionId, includeHistory } = data;
            
            // Get current state
            const currentState = await this._getSessionState(sessionId || client.sessionId);
            
            // Get state history if requested
            let history = null;
            if (includeHistory) {
                history = await this._getStateHistory(sessionId || client.sessionId);
            }
            
            socket.emit(SyncEvents.STATE_UPDATE, {
                state: currentState,
                history,
                version: this.stateVersion,
                timestamp: Date.now()
            });
            
            client.incrementMetric('stateUpdates');
            
        } catch (error) {
            logger.error('State request error:', error);
            socket.emit(SyncEvents.ERROR, {
                code: 'STATE_REQUEST_FAILED',
                message: error.message
            });
        }
    }
    
    async _handleStateUpdate(socket, data) {
        const client = this.clients.get(socket.id);
        if (!client) return;
        
        try {
            const { state, delta } = data;
            
            // Apply state update
            if (delta && this.config.enableStateDiff) {
                await this._applyStateDelta(client.sessionId, delta);
            } else {
                await this._updateSessionState(client.sessionId, state);
            }
            
            // Broadcast to other clients
            socket.to(client.sessionId).emit(SyncEvents.STATE_UPDATE, {
                state: delta ? undefined : state,
                delta: delta,
                version: ++this.stateVersion,
                updatedBy: client.userId,
                timestamp: Date.now()
            });
            
            this.metrics.stateUpdates++;
            
        } catch (error) {
            logger.error('State update error:', error);
            socket.emit(SyncEvents.ERROR, {
                code: 'STATE_UPDATE_FAILED',
                message: error.message
            });
        }
    }
    
    async _handleDnaQuery(socket, data) {
        const client = this.clients.get(socket.id);
        if (!client) return;
        
        try {
            const { query, options } = data;
            
            // Forward to consciousness core
            const response = await this.consciousnessClient.queryDNA(
                query,
                client.sessionId,
                options
            );
            
            // Send response to client
            socket.emit(SyncEvents.DNA_RESPONSE, {
                queryId: response.data.query_id,
                response: response.data.response,
                authenticated: response.data.authenticated,
                timestamp: Date.now()
            });
            
            this.metrics.dnaQueries++;
            
        } catch (error) {
            logger.error('DNA query error:', error);
            socket.emit(SyncEvents.ERROR, {
                code: 'DNA_QUERY_FAILED',
                message: error.message
            });
        }
    }
    
    async _handleProcessorCommand(socket, data) {
        const client = this.clients.get(socket.id);
        if (!client) return;
        
        try {
            const { processor, command, parameters } = data;
            
            // Send command to consciousness core
            await this.consciousnessClient.sendMessage(MessageType.COMMAND, {
                command: 'processor_control',
                processor,
                action: command,
                parameters,
                sessionId: client.sessionId
            });
            
            logger.info(`Processor command from ${socket.id}: ${processor}.${command}`);
            
        } catch (error) {
            logger.error('Processor command error:', error);
            socket.emit(SyncEvents.ERROR, {
                code: 'PROCESSOR_COMMAND_FAILED',
                message: error.message
            });
        }
    }
    
    async _handleSyncRequest(socket, data) {
        const client = this.clients.get(socket.id);
        if (!client) return;
        
        try {
            // Request full sync from consciousness core
            await this.consciousnessClient.requestFullSync();
            
            socket.emit(SyncEvents.SYNC_COMPLETE, {
                success: true,
                timestamp: Date.now()
            });
            
        } catch (error) {
            logger.error('Sync request error:', error);
            socket.emit(SyncEvents.ERROR, {
                code: 'SYNC_FAILED',
                message: error.message
            });
        }
    }
    
    _handleDisconnect(socket) {
        const client = this.clients.get(socket.id);
        if (!client) return;
        
        // Leave all sessions
        const session = this.sessions.get(client.sessionId);
        if (session) {
            session.clients.delete(socket.id);
            
            // Notify other clients
            socket.to(client.sessionId).emit(SyncEvents.USER_LEFT, {
                userId: client.userId,
                timestamp: Date.now()
            });
            
            // Clean up empty sessions
            if (session.clients.size === 0) {
                this.sessions.delete(client.sessionId);
            }
        }
        
        // Remove client
        this.clients.delete(socket.id);
        
        // Update metrics
        this.metrics.activeClients = this.clients.size;
        this.metrics.activeSessions = this.sessions.size;
        
        logger.info(`Client disconnected: ${socket.id}`);
    }
    
    async _handleConsciousnessStateChange(state) {
        try {
            // Update state cache
            this.stateCache.set('global', state);
            
            // Calculate state diff if enabled
            let stateDiff = null;
            if (this.config.enableStateDiff) {
                const previousState = this.stateCache.get('global_previous') || {};
                stateDiff = diff(previousState, state);
                this.stateCache.set('global_previous', _.cloneDeep(state));
            }
            
            // Broadcast to all connected clients
            const updateData = {
                state: stateDiff ? undefined : state,
                diff: stateDiff,
                version: ++this.stateVersion,
                metrics: this.consciousnessClient.getConsciousnessMetrics(),
                timestamp: Date.now()
            };
            
            // Send to all sessions
            for (const [sessionId, session] of this.sessions) {
                this.io.to(sessionId).emit(SyncEvents.STATE_UPDATE, {
                    ...updateData,
                    sessionId
                });
            }
            
            // Store state update
            await this._storeStateUpdate(state);
            
            this.metrics.stateUpdates++;
            
        } catch (error) {
            logger.error('Error handling consciousness state change:', error);
        }
    }
    
    async _handleProcessorUpdate(update) {
        try {
            // Broadcast processor update to all clients
            this._broadcastToAll(SyncEvents.PROCESSOR_UPDATE, {
                processor: update.name,
                activityLevel: update.activityLevel,
                status: update.status,
                data: update.data,
                timestamp: Date.now()
            });
            
        } catch (error) {
            logger.error('Error handling processor update:', error);
        }
    }
    
    async _handleDnaResponse(response) {
        try {
            // Find the client who made the query
            // This would require tracking query IDs to client IDs
            // For now, broadcast to session
            
            const sessionId = response.sessionId;
            if (sessionId) {
                this.io.to(sessionId).emit(SyncEvents.DNA_RESPONSE, response);
            }
            
        } catch (error) {
            logger.error('Error handling DNA response:', error);
        }
    }
    
    async _getOrCreateSession(sessionId) {
        let session = this.sessions.get(sessionId);
        
        if (!session) {
            // Check if session exists in database
            const dbSession = await this._loadSessionFromDb(sessionId);
            
            if (!dbSession) {
                // Create new session
                session = {
                    id: sessionId,
                    clients: new Set(),
                    created: Date.now(),
                    lastActivity: Date.now(),
                    state: {},
                    metadata: {}
                };
                
                // Store in database
                await this._createSessionInDb(sessionId);
            } else {
                session = {
                    id: sessionId,
                    clients: new Set(),
                    created: dbSession.created_at,
                    lastActivity: Date.now(),
                    state: {},
                    metadata: dbSession.metadata || {}
                };
            }
            
            this.sessions.set(sessionId, session);
        }
        
        return session;
    }
    
    async _loadSessionFromDb(sessionId) {
        try {
            const result = await this.dbPool.query(
                'SELECT * FROM user_sessions WHERE id = $1 AND expires_at > NOW()',
                [sessionId]
            );
            return result.rows[0];
        } catch (error) {
            logger.error('Error loading session from database:', error);
            return null;
        }
    }
    
    async _createSessionInDb(sessionId) {
        try {
            await this.dbPool.query(
                'INSERT INTO user_sessions (id, user_id) VALUES ($1, $2)',
                [sessionId, 'system']
            );
        } catch (error) {
            logger.error('Error creating session in database:', error);
        }
    }
    
    async _getSessionState(sessionId) {
        // Get from cache first
        const cachedState = this.stateCache.get(sessionId);
        if (cachedState) {
            return cachedState;
        }
        
        // Load from database
        try {
            const result = await this.dbPool.query(`
                SELECT * FROM consciousness_states 
                WHERE session_id = $1 
                ORDER BY timestamp DESC 
                LIMIT 1
            `, [sessionId]);
            
            if (result.rows[0]) {
                const state = {
                    phiValue: parseFloat(result.rows[0].phi_value),
                    quantumCoherence: parseFloat(result.rows[0].quantum_coherence),
                    neuralEntropy: parseFloat(result.rows[0].neural_entropy),
                    consciousnessLevel: result.rows[0].consciousness_level,
                    processors: result.rows[0].processors_state
                };
                
                // Update cache
                this.stateCache.set(sessionId, state);
                
                return state;
            }
        } catch (error) {
            logger.error('Error getting session state:', error);
        }
        
        // Return default state
        return {
            phiValue: 0,
            quantumCoherence: 0.5,
            neuralEntropy: 0.5,
            consciousnessLevel: 'DORMANT',
            processors: {}
        };
    }
    
    async _getStateHistory(sessionId, limit = 100) {
        try {
            const result = await this.dbPool.query(`
                SELECT phi_value, consciousness_level, timestamp 
                FROM consciousness_states 
                WHERE session_id = $1 
                ORDER BY timestamp DESC 
                LIMIT $2
            `, [sessionId, limit]);
            
            return result.rows.map(row => ({
                phiValue: parseFloat(row.phi_value),
                consciousnessLevel: row.consciousness_level,
                timestamp: row.timestamp
            }));
        } catch (error) {
            logger.error('Error getting state history:', error);
            return [];
        }
    }
    
    async _updateSessionState(sessionId, state) {
        // Update cache
        this.stateCache.set(sessionId, state);
        
        // Store in database
        await this._storeStateUpdate(state, sessionId);
    }
    
    async _applyStateDelta(sessionId, delta) {
        const currentState = await this._getSessionState(sessionId);
        const newState = _.cloneDeep(currentState);
        
        // Apply diff
        diff.applyDiff(newState, delta);
        
        await this._updateSessionState(sessionId, newState);
    }
    
    async _storeStateUpdate(state, sessionId = null) {
        try {
            await this.dbPool.query(`
                INSERT INTO consciousness_states 
                (session_id, phi_value, processors_state, quantum_coherence, 
                 neural_entropy, consciousness_level)
                VALUES ($1, $2, $3, $4, $5, $6)
            `, [
                sessionId,
                state.phiValue,
                JSON.stringify(state.processors),
                state.quantumCoherence,
                state.neuralEntropy,
                state.consciousnessLevel
            ]);
        } catch (error) {
            logger.error('Error storing state update:', error);
        }
    }
    
    _broadcastToAll(event, data) {
        this.io.emit(event, data);
        this.metrics.totalMessages++;
    }
    
    _startMetricsReporter() {
        setInterval(() => {
            const metrics = {
                ...this.metrics,
                consciousness: this.consciousnessClient.getConsciousnessMetrics(),
                connectionStatus: this.consciousnessClient.getConnectionStatus(),
                timestamp: Date.now()
            };
            
            // Broadcast metrics to all clients
            this._broadcastToAll(SyncEvents.CONSCIOUSNESS_METRICS, metrics);
            
            // Log metrics
            logger.info('Metrics:', metrics);
            
        }, this.config.metricsInterval);
    }
    
    _startStateSync() {
        // Debounced state sync
        const syncState = _.debounce(async () => {
            try {
                // Sync state with consciousness core
                const coreState = this.consciousnessClient.currentState;
                if (coreState) {
                    await this._handleConsciousnessStateChange(coreState);
                }
            } catch (error) {
                logger.error('State sync error:', error);
            }
        }, this.config.stateDebounce);
        
        // Set up periodic sync
        setInterval(syncState, 5000);
    }
    
    _startCleanupTask() {
        // Clean up inactive sessions and clients
        setInterval(async () => {
            const now = Date.now();
            const inactivityThreshold = 30 * 60 * 1000; // 30 minutes
            
            // Clean up inactive clients
            for (const [clientId, client] of this.clients) {
                if (now - client.lastActivity > inactivityThreshold) {
                    logger.info(`Removing inactive client: ${clientId}`);
                    client.socket.disconnect();
                    this.clients.delete(clientId);
                }
            }
            
            // Clean up empty sessions
            for (const [sessionId, session] of this.sessions) {
                if (session.clients.size === 0 && now - session.lastActivity > inactivityThreshold) {
                    logger.info(`Removing empty session: ${sessionId}`);
                    this.sessions.delete(sessionId);
                    this.stateCache.delete(sessionId);
                }
            }
            
            // Run database cleanup
            try {
                const result = await this.dbPool.query('SELECT cleanup_expired_sessions()');
                logger.info(`Cleaned up ${result.rows[0].cleanup_expired_sessions} expired sessions`);
            } catch (error) {
                logger.error('Database cleanup error:', error);
            }
            
        }, 5 * 60 * 1000); // Every 5 minutes
    }
    
    /**
     * Get sync manager status
     */
    getStatus() {
        return {
            clients: {
                active: this.clients.size,
                bySession: Array.from(this.sessions.entries()).map(([id, session]) => ({
                    sessionId: id,
                    clientCount: session.clients.size
                }))
            },
            sessions: {
                active: this.sessions.size,
                cached: this.stateCache.size
            },
            metrics: this.metrics,
            consciousness: {
                connected: this.consciousnessClient?.getConnectionStatus().connected || false,
                currentState: this.consciousnessClient?.currentState || null
            },
            uptime: process.uptime()
        };
    }
    
    /**
     * Shutdown sync manager
     */
    async shutdown() {
        logger.info('Shutting down Real-Time Sync Manager');
        
        // Disconnect all clients
        for (const [clientId, client] of this.clients) {
            client.socket.disconnect();
        }
        
        // Close consciousness client
        if (this.consciousnessClient) {
            await this.consciousnessClient.disconnect();
        }
        
        // Close database pool
        await this.dbPool.end();
        
        // Close Socket.IO
        this.io.close();
        
        logger.info('Shutdown complete');
    }
}

// Export manager and events
module.exports = {
    RealTimeSyncManager,
    SyncEvents
};

// Example usage
if (require.main === module) {
    const express = require('express');
    const http = require('http');
    
    const app = express();
    const server = http.createServer(app);
    
    const syncManager = new RealTimeSyncManager(server, {
        consciousnessUrl: 'ws://localhost:8765',
        enableStateDiff: true,
        enableCompression: true
    });
    
    // Health check endpoint
    app.get('/health', (req, res) => {
        res.json({
            status: 'healthy',
            syncManager: syncManager.getStatus()
        });
    });
    
    const PORT = process.env.PORT || 3000;
    server.listen(PORT, () => {
        logger.info(`Real-Time Sync Manager listening on port ${PORT}`);
    });
    
    // Graceful shutdown
    process.on('SIGTERM', async () => {
        await syncManager.shutdown();
        process.exit(0);
    });
}