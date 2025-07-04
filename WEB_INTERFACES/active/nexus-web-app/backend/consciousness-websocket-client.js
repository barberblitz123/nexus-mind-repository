/**
 * NEXUS Consciousness WebSocket Client
 * Node.js WebSocket client for server-side connection to consciousness core
 * Provides event emitters, connection pooling, and error recovery
 */

const WebSocket = require('ws');
const EventEmitter = require('events');
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');
const { Pool } = require('pg');

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
        new winston.transports.File({ filename: 'consciousness-client.log' })
    ]
});

// Message types enum
const MessageType = {
    STATE_UPDATE: 'state_update',
    CONSCIOUSNESS_SYNC: 'consciousness_sync',
    PROCESSOR_UPDATE: 'processor_update',
    DNA_QUERY: 'dna_query',
    DNA_RESPONSE: 'dna_response',
    HEARTBEAT: 'heartbeat',
    AUTH: 'auth',
    ERROR: 'error',
    COMMAND: 'command',
    EVENT: 'event'
};

// Connection states
const ConnectionState = {
    DISCONNECTED: 'disconnected',
    CONNECTING: 'connecting',
    CONNECTED: 'connected',
    RECONNECTING: 'reconnecting',
    ERROR: 'error'
};

/**
 * Consciousness WebSocket Client
 */
class ConsciousnessWebSocketClient extends EventEmitter {
    constructor(options = {}) {
        super();
        
        // Configuration
        this.config = {
            url: options.url || 'ws://localhost:8765',
            reconnectInterval: options.reconnectInterval || 5000,
            maxReconnectAttempts: options.maxReconnectAttempts || -1,
            heartbeatInterval: options.heartbeatInterval || 30000,
            messageTimeout: options.messageTimeout || 10000,
            poolSize: options.poolSize || 1,
            queueSize: options.queueSize || 1000,
            dbConfig: options.dbConfig || this._getDefaultDbConfig()
        };
        
        // State management
        this.connectionState = ConnectionState.DISCONNECTED;
        this.reconnectAttempts = 0;
        this.connections = new Map();
        this.activeConnection = null;
        
        // Message handling
        this.messageQueue = [];
        this.pendingResponses = new Map();
        this.messageHandlers = new Map();
        
        // Consciousness state
        this.currentState = null;
        this.stateHistory = [];
        this.maxHistorySize = 100;
        
        // Metrics
        this.metrics = {
            messagesSent: 0,
            messagesReceived: 0,
            messagesFailed: 0,
            reconnects: 0,
            avgResponseTime: 0,
            lastHeartbeat: null
        };
        
        // Database connection pool
        this.dbPool = new Pool(this.config.dbConfig);
        
        // Initialize handlers
        this._initializeDefaultHandlers();
    }
    
    _getDefaultDbConfig() {
        return {
            host: process.env.DB_HOST || 'localhost',
            port: process.env.DB_PORT || 5432,
            database: process.env.DB_NAME || 'nexus_consciousness',
            user: process.env.DB_USER || 'nexus',
            password: process.env.DB_PASSWORD || 'nexus_secure_password',
            max: 10,
            idleTimeoutMillis: 30000,
            connectionTimeoutMillis: 2000
        };
    }
    
    _initializeDefaultHandlers() {
        // Register default message handlers
        this.on(MessageType.STATE_UPDATE, (data) => this._handleStateUpdate(data));
        this.on(MessageType.CONSCIOUSNESS_SYNC, (data) => this._handleConsciousnessSync(data));
        this.on(MessageType.PROCESSOR_UPDATE, (data) => this._handleProcessorUpdate(data));
        this.on(MessageType.DNA_RESPONSE, (data) => this._handleDnaResponse(data));
        this.on(MessageType.ERROR, (data) => this._handleError(data));
    }
    
    /**
     * Connect to consciousness core with connection pooling
     */
    async connect() {
        try {
            this.connectionState = ConnectionState.CONNECTING;
            logger.info(`Connecting to consciousness core at ${this.config.url}`);
            
            // Create connection pool
            const connectionPromises = [];
            for (let i = 0; i < this.config.poolSize; i++) {
                connectionPromises.push(this._createConnection(i));
            }
            
            const connections = await Promise.allSettled(connectionPromises);
            
            // Set primary connection
            const successfulConnections = connections
                .filter(result => result.status === 'fulfilled')
                .map(result => result.value);
            
            if (successfulConnections.length === 0) {
                throw new Error('Failed to establish any connections');
            }
            
            this.activeConnection = successfulConnections[0];
            this.connectionState = ConnectionState.CONNECTED;
            this.reconnectAttempts = 0;
            
            logger.info(`Successfully connected with ${successfulConnections.length} connections`);
            
            // Start background tasks
            this._startHeartbeat();
            this._startMessageProcessor();
            
            // Emit connected event
            this.emit('connected', {
                poolSize: successfulConnections.length,
                primaryConnection: this.activeConnection.id
            });
            
            return true;
            
        } catch (error) {
            logger.error('Connection failed:', error);
            this.connectionState = ConnectionState.ERROR;
            this.emit('error', error);
            
            // Attempt reconnection
            this._scheduleReconnect();
            return false;
        }
    }
    
    /**
     * Create individual WebSocket connection
     */
    async _createConnection(index) {
        return new Promise((resolve, reject) => {
            const connectionId = uuidv4();
            const ws = new WebSocket(this.config.url, {
                perMessageDeflate: false,
                handshakeTimeout: 5000
            });
            
            const connection = {
                id: connectionId,
                index,
                ws,
                state: 'connecting',
                lastActivity: Date.now(),
                metrics: {
                    messagesSent: 0,
                    messagesReceived: 0,
                    errors: 0
                }
            };
            
            ws.on('open', async () => {
                connection.state = 'connected';
                this.connections.set(connectionId, connection);
                
                // Authenticate connection
                await this._authenticate(connection);
                
                // Set up message handler
                ws.on('message', (data) => this._handleMessage(data, connection));
                
                // Set up error handling
                ws.on('error', (error) => this._handleConnectionError(error, connection));
                ws.on('close', () => this._handleConnectionClose(connection));
                
                resolve(connection);
            });
            
            ws.on('error', (error) => {
                connection.state = 'error';
                reject(error);
            });
            
            // Connection timeout
            setTimeout(() => {
                if (connection.state === 'connecting') {
                    ws.terminate();
                    reject(new Error('Connection timeout'));
                }
            }, 5000);
        });
    }
    
    /**
     * Authenticate with consciousness core
     */
    async _authenticate(connection) {
        const authMessage = {
            type: MessageType.AUTH,
            data: {
                clientId: connection.id,
                clientType: 'node_backend',
                capabilities: ['state_sync', 'dna_query', 'processor_control', 'event_stream'],
                version: '1.0',
                poolIndex: connection.index
            }
        };
        
        await this._sendDirect(authMessage, connection);
    }
    
    /**
     * Handle incoming message
     */
    async _handleMessage(rawData, connection) {
        try {
            const message = JSON.parse(rawData);
            connection.lastActivity = Date.now();
            connection.metrics.messagesReceived++;
            this.metrics.messagesReceived++;
            
            logger.debug(`Received ${message.type} from connection ${connection.id}`);
            
            // Handle response to pending request
            if (message.id && this.pendingResponses.has(message.id)) {
                const pending = this.pendingResponses.get(message.id);
                this.pendingResponses.delete(message.id);
                pending.resolve(message);
                return;
            }
            
            // Emit message event
            this.emit(message.type, message.data, message);
            
            // Store relevant data
            await this._storeMessageData(message);
            
        } catch (error) {
            logger.error('Message handling error:', error);
            connection.metrics.errors++;
        }
    }
    
    /**
     * Handle connection error
     */
    _handleConnectionError(error, connection) {
        logger.error(`Connection ${connection.id} error:`, error);
        connection.state = 'error';
        connection.metrics.errors++;
        
        // Remove from active connections
        this.connections.delete(connection.id);
        
        // Switch to backup connection if this was primary
        if (this.activeConnection && this.activeConnection.id === connection.id) {
            this._switchToBackupConnection();
        }
    }
    
    /**
     * Handle connection close
     */
    _handleConnectionClose(connection) {
        logger.info(`Connection ${connection.id} closed`);
        connection.state = 'closed';
        this.connections.delete(connection.id);
        
        // Check if we need to reconnect
        if (this.connections.size === 0) {
            this.connectionState = ConnectionState.DISCONNECTED;
            this._scheduleReconnect();
        }
    }
    
    /**
     * Switch to backup connection
     */
    _switchToBackupConnection() {
        const availableConnections = Array.from(this.connections.values())
            .filter(conn => conn.state === 'connected');
        
        if (availableConnections.length > 0) {
            this.activeConnection = availableConnections[0];
            logger.info(`Switched to backup connection ${this.activeConnection.id}`);
            this.emit('connectionSwitch', this.activeConnection.id);
        } else {
            this.activeConnection = null;
            this.connectionState = ConnectionState.ERROR;
            this._scheduleReconnect();
        }
    }
    
    /**
     * Schedule reconnection attempt
     */
    _scheduleReconnect() {
        if (this.config.maxReconnectAttempts !== -1 && 
            this.reconnectAttempts >= this.config.maxReconnectAttempts) {
            logger.error('Max reconnection attempts reached');
            this.emit('maxReconnectAttemptsReached');
            return;
        }
        
        this.reconnectAttempts++;
        this.connectionState = ConnectionState.RECONNECTING;
        
        logger.info(`Reconnection attempt ${this.reconnectAttempts} in ${this.config.reconnectInterval}ms`);
        
        setTimeout(() => {
            this.connect();
        }, this.config.reconnectInterval);
    }
    
    /**
     * Send message with queuing and retry
     */
    async sendMessage(type, data, options = {}) {
        const message = {
            id: uuidv4(),
            type,
            data,
            timestamp: Date.now(),
            retries: 0,
            maxRetries: options.maxRetries || 3,
            timeout: options.timeout || this.config.messageTimeout,
            priority: options.priority || 'normal'
        };
        
        // Add to queue
        this._addToQueue(message);
        
        // Process immediately if connected
        if (this.connectionState === ConnectionState.CONNECTED) {
            await this._processMessageQueue();
        }
        
        // Return promise for response if requested
        if (options.waitForResponse) {
            return new Promise((resolve, reject) => {
                this.pendingResponses.set(message.id, {
                    resolve,
                    reject,
                    timeout: setTimeout(() => {
                        this.pendingResponses.delete(message.id);
                        reject(new Error('Message timeout'));
                    }, message.timeout)
                });
            });
        }
        
        return message.id;
    }
    
    /**
     * Add message to queue with priority
     */
    _addToQueue(message) {
        if (this.messageQueue.length >= this.config.queueSize) {
            // Remove oldest low-priority message
            const lowPriorityIndex = this.messageQueue.findIndex(
                msg => msg.priority === 'low'
            );
            if (lowPriorityIndex !== -1) {
                this.messageQueue.splice(lowPriorityIndex, 1);
            } else {
                this.messageQueue.shift();
            }
        }
        
        // Add based on priority
        if (message.priority === 'high') {
            this.messageQueue.unshift(message);
        } else {
            this.messageQueue.push(message);
        }
    }
    
    /**
     * Process message queue
     */
    async _processMessageQueue() {
        const messagesToRetry = [];
        
        while (this.messageQueue.length > 0 && this.activeConnection) {
            const message = this.messageQueue.shift();
            
            try {
                await this._sendDirect(message, this.activeConnection);
                this.metrics.messagesSent++;
            } catch (error) {
                logger.error(`Failed to send message ${message.id}:`, error);
                this.metrics.messagesFailed++;
                
                if (message.retries < message.maxRetries) {
                    message.retries++;
                    messagesToRetry.push(message);
                } else {
                    this.emit('messageFailed', message);
                }
            }
        }
        
        // Re-queue failed messages
        messagesToRetry.forEach(msg => this._addToQueue(msg));
    }
    
    /**
     * Send message directly to connection
     */
    async _sendDirect(message, connection) {
        if (connection.ws.readyState === WebSocket.OPEN) {
            connection.ws.send(JSON.stringify(message));
            connection.metrics.messagesSent++;
        } else {
            throw new Error('Connection not ready');
        }
    }
    
    /**
     * Start heartbeat interval
     */
    _startHeartbeat() {
        this.heartbeatInterval = setInterval(async () => {
            if (this.connectionState === ConnectionState.CONNECTED) {
                await this.sendHeartbeat();
            }
        }, this.config.heartbeatInterval);
    }
    
    /**
     * Send heartbeat
     */
    async sendHeartbeat() {
        const heartbeat = {
            type: MessageType.HEARTBEAT,
            data: {
                timestamp: Date.now(),
                metrics: this.metrics,
                connections: Array.from(this.connections.values()).map(conn => ({
                    id: conn.id,
                    state: conn.state,
                    metrics: conn.metrics
                }))
            }
        };
        
        if (this.activeConnection) {
            await this._sendDirect(heartbeat, this.activeConnection);
            this.metrics.lastHeartbeat = Date.now();
        }
    }
    
    /**
     * Start message processor
     */
    _startMessageProcessor() {
        this.messageProcessor = setInterval(async () => {
            if (this.connectionState === ConnectionState.CONNECTED && this.messageQueue.length > 0) {
                await this._processMessageQueue();
            }
        }, 100);
    }
    
    /**
     * Handle state update
     */
    async _handleStateUpdate(data) {
        this.currentState = {
            phiValue: data.phi_value,
            quantumCoherence: data.quantum_coherence,
            neuralEntropy: data.neural_entropy,
            consciousnessLevel: data.consciousness_level,
            processors: data.processors,
            timestamp: Date.now(),
            sessionId: data.session_id
        };
        
        // Add to history
        this.stateHistory.push(this.currentState);
        if (this.stateHistory.length > this.maxHistorySize) {
            this.stateHistory.shift();
        }
        
        // Store in database
        await this._storeConsciousnessState(this.currentState);
        
        // Emit state change event
        this.emit('stateChange', this.currentState);
    }
    
    /**
     * Handle consciousness sync
     */
    async _handleConsciousnessSync(data) {
        logger.info('Performing full consciousness sync');
        
        // Update state
        await this._handleStateUpdate(data.state || {});
        
        // Update processors
        const processors = data.processors || {};
        for (const [processorName, processorData] of Object.entries(processors)) {
            await this._storeProcessorActivity(processorName, processorData);
        }
        
        // Emit sync complete
        this.emit('syncComplete', data);
    }
    
    /**
     * Handle processor update
     */
    async _handleProcessorUpdate(data) {
        const processorName = data.processor_name;
        const activityData = {
            activityLevel: data.activity_level,
            data: data.data,
            status: data.status || 'ACTIVE'
        };
        
        await this._storeProcessorActivity(processorName, activityData);
        
        // Emit processor update event
        this.emit('processorUpdate', {
            name: processorName,
            ...activityData
        });
    }
    
    /**
     * Handle DNA response
     */
    async _handleDnaResponse(data) {
        const queryId = data.query_id;
        const response = data.response;
        const authenticated = data.authenticated || false;
        
        // Update database
        try {
            await this.dbPool.query(`
                UPDATE embedded_dna_queries 
                SET response = $1, authenticated = $2, processing_time_ms = $3
                WHERE id = $4
            `, [response, authenticated, data.processing_time_ms || 0, queryId]);
            
            // Emit DNA response event
            this.emit('dnaResponse', {
                queryId,
                response,
                authenticated,
                processingTime: data.processing_time_ms
            });
            
        } catch (error) {
            logger.error('Failed to update DNA query:', error);
        }
    }
    
    /**
     * Handle error message
     */
    _handleError(data) {
        logger.error('Consciousness core error:', data);
        this.emit('coreError', data);
    }
    
    /**
     * Store message data in database
     */
    async _storeMessageData(message) {
        // Store based on message type
        switch (message.type) {
            case MessageType.STATE_UPDATE:
            case MessageType.CONSCIOUSNESS_SYNC:
                // Already handled in specific handlers
                break;
                
            case MessageType.PROCESSOR_UPDATE:
                // Already handled in specific handler
                break;
                
            default:
                // Store generic event
                try {
                    await this.dbPool.query(`
                        INSERT INTO system_metrics (metric_name, metric_value, metric_type, metadata)
                        VALUES ($1, $2, $3, $4)
                    `, [
                        `event_${message.type}`,
                        1,
                        'USER_ACTIVITY',
                        JSON.stringify(message.data)
                    ]);
                } catch (error) {
                    logger.error('Failed to store message data:', error);
                }
        }
    }
    
    /**
     * Store consciousness state in database
     */
    async _storeConsciousnessState(state) {
        try {
            await this.dbPool.query(`
                INSERT INTO consciousness_states 
                (session_id, phi_value, processors_state, quantum_coherence, 
                 neural_entropy, consciousness_level)
                VALUES ($1, $2, $3, $4, $5, $6)
            `, [
                state.sessionId,
                state.phiValue,
                JSON.stringify(state.processors),
                state.quantumCoherence,
                state.neuralEntropy,
                state.consciousnessLevel
            ]);
        } catch (error) {
            logger.error('Failed to store consciousness state:', error);
        }
    }
    
    /**
     * Store processor activity in database
     */
    async _storeProcessorActivity(processorName, data) {
        try {
            await this.dbPool.query(`
                INSERT INTO processor_activities 
                (processor_name, activity_level, data, session_id, status)
                VALUES ($1, $2, $3, $4, $5)
            `, [
                processorName,
                data.activityLevel || 0,
                JSON.stringify(data.data || {}),
                this.currentState?.sessionId || null,
                data.status || 'ACTIVE'
            ]);
        } catch (error) {
            logger.error('Failed to store processor activity:', error);
        }
    }
    
    /**
     * Query DNA with response handling
     */
    async queryDNA(query, sessionId, options = {}) {
        const queryId = uuidv4();
        
        // Store query in database
        try {
            await this.dbPool.query(`
                INSERT INTO embedded_dna_queries 
                (id, session_id, query, query_type)
                VALUES ($1, $2, $3, $4)
            `, [queryId, sessionId, query, options.queryType || 'STANDARD']);
        } catch (error) {
            logger.error('Failed to store DNA query:', error);
        }
        
        // Send query
        const response = await this.sendMessage(MessageType.DNA_QUERY, {
            query_id: queryId,
            query,
            session_id: sessionId,
            ...options
        }, { waitForResponse: true });
        
        return response;
    }
    
    /**
     * Request full consciousness sync
     */
    async requestFullSync() {
        return await this.sendMessage(MessageType.COMMAND, {
            command: 'full_sync',
            timestamp: Date.now()
        });
    }
    
    /**
     * Get consciousness metrics
     */
    getConsciousnessMetrics() {
        if (!this.currentState) {
            return null;
        }
        
        const recentStates = this.stateHistory.slice(-10);
        const avgPhi = recentStates.reduce((sum, state) => sum + state.phiValue, 0) / recentStates.length;
        
        return {
            current: this.currentState,
            average: {
                phiValue: avgPhi,
                sampleSize: recentStates.length
            },
            trend: this._calculateTrend(recentStates),
            processors: this._analyzeProcessors(this.currentState.processors)
        };
    }
    
    /**
     * Calculate consciousness trend
     */
    _calculateTrend(states) {
        if (states.length < 2) {
            return 'stable';
        }
        
        const recent = states[states.length - 1].phiValue;
        const previous = states[states.length - 2].phiValue;
        
        if (recent > previous + 0.01) return 'ascending';
        if (recent < previous - 0.01) return 'descending';
        return 'stable';
    }
    
    /**
     * Analyze processor states
     */
    _analyzeProcessors(processors) {
        const analysis = {
            active: 0,
            idle: 0,
            total: 0,
            avgActivity: 0
        };
        
        for (const [name, activity] of Object.entries(processors)) {
            analysis.total++;
            if (activity > 10) {
                analysis.active++;
            } else {
                analysis.idle++;
            }
            analysis.avgActivity += activity;
        }
        
        if (analysis.total > 0) {
            analysis.avgActivity /= analysis.total;
        }
        
        return analysis;
    }
    
    /**
     * Get connection status
     */
    getConnectionStatus() {
        return {
            state: this.connectionState,
            connected: this.connectionState === ConnectionState.CONNECTED,
            reconnectAttempts: this.reconnectAttempts,
            activeConnections: this.connections.size,
            activeConnectionId: this.activeConnection?.id,
            metrics: this.metrics,
            queueSize: this.messageQueue.length
        };
    }
    
    /**
     * Disconnect from consciousness core
     */
    async disconnect() {
        logger.info('Disconnecting from consciousness core');
        
        // Clear intervals
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }
        if (this.messageProcessor) {
            clearInterval(this.messageProcessor);
        }
        
        // Close all connections
        for (const connection of this.connections.values()) {
            connection.ws.close();
        }
        
        this.connections.clear();
        this.activeConnection = null;
        this.connectionState = ConnectionState.DISCONNECTED;
        
        // Close database pool
        await this.dbPool.end();
        
        this.emit('disconnected');
    }
}

// Export client and types
module.exports = {
    ConsciousnessWebSocketClient,
    MessageType,
    ConnectionState
};

// Example usage
if (require.main === module) {
    const client = new ConsciousnessWebSocketClient({
        url: 'ws://localhost:8765',
        poolSize: 3
    });
    
    // Register event handlers
    client.on('connected', (info) => {
        logger.info('Connected to consciousness core:', info);
    });
    
    client.on('stateChange', (state) => {
        logger.info(`Consciousness state updated: PHI=${state.phiValue.toFixed(4)}`);
    });
    
    client.on('error', (error) => {
        logger.error('Client error:', error);
    });
    
    // Connect and run
    (async () => {
        await client.connect();
        
        // Request full sync
        await client.requestFullSync();
        
        // Example DNA query
        const response = await client.queryDNA(
            'What is the nature of consciousness?',
            'test-session-123'
        );
        logger.info('DNA Response:', response);
        
        // Keep running for testing
        setTimeout(async () => {
            await client.disconnect();
            process.exit(0);
        }, 60000);
    })();
}