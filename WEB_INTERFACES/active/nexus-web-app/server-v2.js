const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const session = require('express-session');
const MongoStore = require('connect-mongo');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const path = require('path');
const fs = require('fs').promises;
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');

// Import all components
const NexusAPIGateway = require('./gateway/nexus-api-gateway');
const ConsciousnessEngine = require('./backend/consciousness-engine');
const IDEManager = require('./ide/ide-manager');
const ContextManager = require('./context/context-manager');
const ProcessorManager = require('./processors/processor-manager');
const KnowledgeBase = require('./backend/knowledge-base');

// Configure logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    })
  ]
});

class NexusServerV2 {
  constructor(config = {}) {
    this.config = {
      port: config.port || process.env.PORT || 3000,
      mongoUri: config.mongoUri || process.env.MONGO_URI || 'mongodb://localhost:27017/nexus',
      sessionSecret: config.sessionSecret || process.env.SESSION_SECRET || 'nexus-session-secret',
      corsOrigins: config.corsOrigins || process.env.CORS_ORIGINS?.split(',') || ['http://localhost:3000'],
      maxContextSize: config.maxContextSize || 1000000, // 1M tokens
      enableMetrics: config.enableMetrics !== false,
      ...config
    };

    this.app = express();
    this.server = null;
    this.wss = null;
    this.components = {};
    this.sessions = new Map();
    this.metrics = {
      startTime: Date.now(),
      requests: 0,
      errors: 0,
      activeConnections: 0,
      contextOperations: 0
    };

    this.initializeComponents();
    this.setupMiddleware();
    this.setupRoutes();
    this.setupWebSocket();
  }

  async initializeComponents() {
    logger.info('Initializing Nexus components...');

    // Initialize core components
    this.components.consciousness = new ConsciousnessEngine({
      modelPath: this.config.consciousnessModel,
      maxTokens: this.config.maxContextSize
    });

    this.components.ide = new IDEManager({
      supportedLanguages: ['python', 'javascript', 'typescript', 'java', 'cpp'],
      maxFileSize: 10 * 1024 * 1024 // 10MB
    });

    this.components.context = new ContextManager({
      maxSize: this.config.maxContextSize,
      compressionEnabled: true,
      mongoUri: this.config.mongoUri
    });

    this.components.processor = new ProcessorManager({
      providers: ['claude', 'openai', 'gemini', 'local'],
      maxConcurrent: 10
    });

    this.components.knowledge = new KnowledgeBase({
      dbPath: './knowledge.db',
      indexingEnabled: true
    });

    // Initialize API Gateway for microservice communication
    this.components.gateway = new NexusAPIGateway({
      port: this.config.port + 1000, // Run gateway on separate port
      services: {
        consciousness: `http://localhost:${this.config.port}`,
        ide: `http://localhost:${this.config.port}`,
        context: `http://localhost:${this.config.port}`,
        processor: `http://localhost:${this.config.port}`,
        knowledge: `http://localhost:${this.config.port}`
      }
    });

    // Initialize all components
    await Promise.all([
      this.components.consciousness.initialize(),
      this.components.ide.initialize(),
      this.components.context.initialize(),
      this.components.processor.initialize(),
      this.components.knowledge.initialize()
    ]);

    logger.info('All components initialized successfully');
  }

  setupMiddleware() {
    // Security
    this.app.use(helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          scriptSrc: ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          imgSrc: ["'self'", "data:", "https:"],
          connectSrc: ["'self'", "ws:", "wss:", "http:", "https:"],
        },
      },
    }));

    // CORS
    this.app.use(cors({
      origin: this.config.corsOrigins,
      credentials: true
    }));

    // Compression
    this.app.use(compression());

    // Body parsing
    this.app.use(express.json({ limit: '50mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '50mb' }));

    // Session management with MongoDB store
    this.app.use(session({
      secret: this.config.sessionSecret,
      resave: false,
      saveUninitialized: false,
      store: MongoStore.create({
        mongoUrl: this.config.mongoUri,
        touchAfter: 24 * 3600 // lazy session update
      }),
      cookie: {
        secure: process.env.NODE_ENV === 'production',
        httpOnly: true,
        maxAge: 7 * 24 * 60 * 60 * 1000 // 7 days
      }
    }));

    // Request tracking
    this.app.use((req, res, next) => {
      this.metrics.requests++;
      req.requestId = uuidv4();
      logger.info(`${req.method} ${req.path}`, {
        requestId: req.requestId,
        ip: req.ip
      });
      next();
    });

    // Static files
    this.app.use(express.static(path.join(__dirname, 'public')));
  }

  setupRoutes() {
    // Health check
    this.app.get('/health', (req, res) => {
      const health = {
        status: 'healthy',
        uptime: process.uptime(),
        metrics: this.getMetrics(),
        components: {}
      };

      // Check component health
      for (const [name, component] of Object.entries(this.components)) {
        if (component && typeof component.getHealth === 'function') {
          health.components[name] = component.getHealth();
        }
      }

      res.json(health);
    });

    // IDE routes
    this.setupIDERoutes();

    // Context management routes
    this.setupContextRoutes();

    // Processor routes
    this.setupProcessorRoutes();

    // Consciousness routes
    this.setupConsciousnessRoutes();

    // Knowledge base routes
    this.setupKnowledgeRoutes();

    // Session management routes
    this.setupSessionRoutes();

    // Error handling
    this.app.use((err, req, res, next) => {
      this.metrics.errors++;
      logger.error('Server error:', {
        requestId: req.requestId,
        error: err.message,
        stack: err.stack
      });

      res.status(err.status || 500).json({
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? err.message : undefined,
        requestId: req.requestId
      });
    });
  }

  setupIDERoutes() {
    const ideRouter = express.Router();

    // File operations
    ideRouter.get('/files', async (req, res, next) => {
      try {
        const { path: filePath } = req.query;
        const content = await this.components.ide.readFile(filePath);
        res.json({ content, path: filePath });
      } catch (error) {
        next(error);
      }
    });

    ideRouter.post('/files', async (req, res, next) => {
      try {
        const { path: filePath, content } = req.body;
        await this.components.ide.writeFile(filePath, content);
        res.status(201).json({ success: true, path: filePath });
      } catch (error) {
        next(error);
      }
    });

    // Code execution
    ideRouter.post('/execute', async (req, res, next) => {
      try {
        const { language, code, timeout = 30000 } = req.body;
        const result = await this.components.ide.executeCode(language, code, { timeout });
        res.json(result);
      } catch (error) {
        next(error);
      }
    });

    // Code completion
    ideRouter.post('/complete', async (req, res, next) => {
      try {
        const { language, code, position } = req.body;
        const completions = await this.components.ide.getCompletions(language, code, position);
        res.json({ completions });
      } catch (error) {
        next(error);
      }
    });

    // Language server operations
    ideRouter.post('/lsp/:operation', async (req, res, next) => {
      try {
        const { operation } = req.params;
        const result = await this.components.ide.performLSPOperation(operation, req.body);
        res.json(result);
      } catch (error) {
        next(error);
      }
    });

    this.app.use('/api/ide', ideRouter);
  }

  setupContextRoutes() {
    const contextRouter = express.Router();

    // Create context
    contextRouter.post('/create', async (req, res, next) => {
      try {
        const { content, metadata } = req.body;
        const contextSize = parseInt(req.get('X-Context-Size') || this.config.maxContextSize);
        
        const context = await this.components.context.createContext({
          content,
          metadata,
          maxSize: contextSize,
          sessionId: req.session.id
        });

        this.metrics.contextOperations++;
        res.status(201).json(context);
      } catch (error) {
        next(error);
      }
    });

    // Retrieve context
    contextRouter.get('/retrieve', async (req, res, next) => {
      try {
        const { contextId, format = 'full' } = req.query;
        const context = await this.components.context.retrieveContext(contextId, {
          format,
          sessionId: req.session.id
        });
        res.json(context);
      } catch (error) {
        next(error);
      }
    });

    // Update context
    contextRouter.put('/:contextId', async (req, res, next) => {
      try {
        const { contextId } = req.params;
        const { content, operation = 'append' } = req.body;
        
        const updated = await this.components.context.updateContext(contextId, {
          content,
          operation,
          sessionId: req.session.id
        });

        this.metrics.contextOperations++;
        res.json(updated);
      } catch (error) {
        next(error);
      }
    });

    // Analyze context
    contextRouter.post('/analyze', async (req, res, next) => {
      try {
        const { data, analysisType = 'summary' } = req.body;
        const analysis = await this.components.context.analyzeContext(data, {
          type: analysisType,
          sessionId: req.session.id
        });
        res.json(analysis);
      } catch (error) {
        next(error);
      }
    });

    // Context compression
    contextRouter.post('/compress', async (req, res, next) => {
      try {
        const { contextId, compressionLevel = 'medium' } = req.body;
        const compressed = await this.components.context.compressContext(contextId, {
          level: compressionLevel
        });
        res.json(compressed);
      } catch (error) {
        next(error);
      }
    });

    this.app.use('/api/context', contextRouter);
  }

  setupProcessorRoutes() {
    const processorRouter = express.Router();

    // Process with Claude
    processorRouter.post('/claude', async (req, res, next) => {
      try {
        const { prompt, maxTokens = 1000, temperature = 0.7 } = req.body;
        const response = await this.components.processor.processWithClaude({
          prompt,
          maxTokens,
          temperature,
          sessionId: req.session.id
        });
        res.json(response);
      } catch (error) {
        next(error);
      }
    });

    // Process with GPT
    processorRouter.post('/gpt', async (req, res, next) => {
      try {
        const { prompt, model = 'gpt-4', maxTokens = 1000 } = req.body;
        const response = await this.components.processor.processWithGPT({
          prompt,
          model,
          maxTokens,
          sessionId: req.session.id
        });
        res.json(response);
      } catch (error) {
        next(error);
      }
    });

    // Chain multiple processors
    processorRouter.post('/chain', async (req, res, next) => {
      try {
        const { processors, prompt, chainMode = 'sequential' } = req.body;
        const results = await this.components.processor.chainProcessors({
          processors,
          prompt,
          mode: chainMode,
          sessionId: req.session.id
        });
        res.json({ results });
      } catch (error) {
        next(error);
      }
    });

    // Process with local model
    processorRouter.post('/local', async (req, res, next) => {
      try {
        const { prompt, modelName = 'default' } = req.body;
        const response = await this.components.processor.processWithLocal({
          prompt,
          modelName,
          sessionId: req.session.id
        });
        res.json(response);
      } catch (error) {
        next(error);
      }
    });

    this.app.use('/api/processor', processorRouter);
  }

  setupConsciousnessRoutes() {
    const consciousnessRouter = express.Router();

    // Get consciousness status
    consciousnessRouter.get('/status', async (req, res, next) => {
      try {
        const status = await this.components.consciousness.getStatus();
        res.json(status);
      } catch (error) {
        next(error);
      }
    });

    // Process thought
    consciousnessRouter.post('/think', async (req, res, next) => {
      try {
        const { input, context, mode = 'deep' } = req.body;
        const thought = await this.components.consciousness.processThought({
          input,
          context,
          mode,
          sessionId: req.session.id
        });
        res.json(thought);
      } catch (error) {
        next(error);
      }
    });

    // Update consciousness state
    consciousnessRouter.put('/state', async (req, res, next) => {
      try {
        const { updates } = req.body;
        const newState = await this.components.consciousness.updateState(updates);
        res.json(newState);
      } catch (error) {
        next(error);
      }
    });

    // Get consciousness insights
    consciousnessRouter.get('/insights', async (req, res, next) => {
      try {
        const { depth = 'medium' } = req.query;
        const insights = await this.components.consciousness.generateInsights({
          depth,
          sessionId: req.session.id
        });
        res.json(insights);
      } catch (error) {
        next(error);
      }
    });

    this.app.use('/api/consciousness', consciousnessRouter);
  }

  setupKnowledgeRoutes() {
    const knowledgeRouter = express.Router();

    // Store knowledge
    knowledgeRouter.post('/store', async (req, res, next) => {
      try {
        const { content, type, metadata } = req.body;
        const stored = await this.components.knowledge.store({
          content,
          type,
          metadata,
          sessionId: req.session.id
        });
        res.status(201).json(stored);
      } catch (error) {
        next(error);
      }
    });

    // Query knowledge
    knowledgeRouter.post('/query', async (req, res, next) => {
      try {
        const { query, filters = {}, limit = 10 } = req.body;
        const results = await this.components.knowledge.query({
          query,
          filters,
          limit,
          sessionId: req.session.id
        });
        res.json(results);
      } catch (error) {
        next(error);
      }
    });

    // Update knowledge
    knowledgeRouter.put('/:id', async (req, res, next) => {
      try {
        const { id } = req.params;
        const updates = req.body;
        const updated = await this.components.knowledge.update(id, updates);
        res.json(updated);
      } catch (error) {
        next(error);
      }
    });

    this.app.use('/api/knowledge', knowledgeRouter);
  }

  setupSessionRoutes() {
    const sessionRouter = express.Router();

    // Create session with 1M context support
    sessionRouter.post('/create', async (req, res, next) => {
      try {
        const { contextSize = this.config.maxContextSize, metadata = {} } = req.body;
        
        const sessionData = {
          id: uuidv4(),
          createdAt: new Date(),
          contextSize,
          metadata,
          contexts: [],
          processors: [],
          thoughts: []
        };

        this.sessions.set(sessionData.id, sessionData);
        req.session.nexusSessionId = sessionData.id;
        
        res.status(201).json({
          sessionId: sessionData.id,
          contextSize,
          expiresIn: 7 * 24 * 60 * 60 // 7 days
        });
      } catch (error) {
        next(error);
      }
    });

    // Get session info
    sessionRouter.get('/:sessionId', async (req, res, next) => {
      try {
        const { sessionId } = req.params;
        const session = this.sessions.get(sessionId);
        
        if (!session) {
          return res.status(404).json({ error: 'Session not found' });
        }

        res.json({
          id: session.id,
          createdAt: session.createdAt,
          contextSize: session.contextSize,
          totalTokens: session.contexts.reduce((sum, ctx) => sum + (ctx.tokenCount || 0), 0),
          metadata: session.metadata
        });
      } catch (error) {
        next(error);
      }
    });

    // Add to session context
    sessionRouter.post('/:sessionId/add', async (req, res, next) => {
      try {
        const { sessionId } = req.params;
        const { content, type = 'text' } = req.body;
        
        const session = this.sessions.get(sessionId);
        if (!session) {
          return res.status(404).json({ error: 'Session not found' });
        }

        const contextItem = await this.components.context.addToSession(sessionId, {
          content,
          type,
          timestamp: new Date()
        });

        session.contexts.push(contextItem);
        
        res.json({
          added: true,
          totalTokens: session.contexts.reduce((sum, ctx) => sum + (ctx.tokenCount || 0), 0),
          remainingCapacity: session.contextSize - session.contexts.reduce((sum, ctx) => sum + (ctx.tokenCount || 0), 0)
        });
      } catch (error) {
        next(error);
      }
    });

    this.app.use('/api/session', sessionRouter);
  }

  setupWebSocket() {
    this.wss = new WebSocket.Server({ noServer: true });

    this.wss.on('connection', (ws, req) => {
      this.metrics.activeConnections++;
      const connectionId = uuidv4();
      
      logger.info('New WebSocket connection', { connectionId });

      ws.on('message', async (message) => {
        try {
          const data = JSON.parse(message);
          await this.handleWebSocketMessage(ws, data, connectionId);
        } catch (error) {
          logger.error('WebSocket message error:', error);
          ws.send(JSON.stringify({ 
            error: 'Invalid message', 
            details: error.message 
          }));
        }
      });

      ws.on('close', () => {
        this.metrics.activeConnections--;
        logger.info('WebSocket connection closed', { connectionId });
      });

      ws.on('error', (error) => {
        logger.error('WebSocket error:', { connectionId, error });
      });

      // Send initial connection confirmation
      ws.send(JSON.stringify({
        type: 'connected',
        connectionId,
        capabilities: [
          'ide', 'context', 'processor', 'consciousness', 'knowledge'
        ]
      }));
    });
  }

  async handleWebSocketMessage(ws, data, connectionId) {
    const { type, payload } = data;

    switch (type) {
      case 'ide:execute':
        const result = await this.components.ide.executeCode(
          payload.language,
          payload.code
        );
        ws.send(JSON.stringify({ type: 'ide:result', data: result }));
        break;

      case 'context:stream':
        // Handle streaming large contexts
        const stream = await this.components.context.streamContext(payload.contextId);
        stream.on('data', (chunk) => {
          ws.send(JSON.stringify({ 
            type: 'context:chunk', 
            data: chunk.toString() 
          }));
        });
        stream.on('end', () => {
          ws.send(JSON.stringify({ type: 'context:end' }));
        });
        break;

      case 'processor:stream':
        // Handle streaming AI responses
        const processorStream = await this.components.processor.streamResponse(payload);
        processorStream.on('token', (token) => {
          ws.send(JSON.stringify({ 
            type: 'processor:token', 
            data: token 
          }));
        });
        processorStream.on('complete', (response) => {
          ws.send(JSON.stringify({ 
            type: 'processor:complete', 
            data: response 
          }));
        });
        break;

      case 'consciousness:sync':
        const consciousnessState = await this.components.consciousness.syncState(payload);
        ws.send(JSON.stringify({ 
          type: 'consciousness:state', 
          data: consciousnessState 
        }));
        break;

      case 'ping':
        ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
        break;

      default:
        ws.send(JSON.stringify({ 
          error: 'Unknown message type', 
          type 
        }));
    }
  }

  getMetrics() {
    return {
      uptime: Date.now() - this.metrics.startTime,
      requests: this.metrics.requests,
      errors: this.metrics.errors,
      errorRate: this.metrics.requests > 0 ? 
        (this.metrics.errors / this.metrics.requests) * 100 : 0,
      activeConnections: this.metrics.activeConnections,
      contextOperations: this.metrics.contextOperations,
      memory: process.memoryUsage(),
      cpu: process.cpuUsage()
    };
  }

  async start() {
    return new Promise((resolve, reject) => {
      this.server = http.createServer(this.app);

      // Handle WebSocket upgrade
      this.server.on('upgrade', (request, socket, head) => {
        this.wss.handleUpgrade(request, socket, head, (ws) => {
          this.wss.emit('connection', ws, request);
        });
      });

      this.server.listen(this.config.port, async (err) => {
        if (err) {
          reject(err);
        } else {
          logger.info(`Nexus Server V2 running on port ${this.config.port}`);
          
          // Start the API Gateway
          if (this.components.gateway) {
            await this.components.gateway.start();
            logger.info(`API Gateway running on port ${this.config.port + 1000}`);
          }
          
          resolve(this.server);
        }
      });
    });
  }

  async stop() {
    logger.info('Shutting down Nexus Server V2...');

    // Close WebSocket connections
    if (this.wss) {
      this.wss.clients.forEach(client => {
        client.send(JSON.stringify({ type: 'shutdown' }));
        client.close();
      });
      this.wss.close();
    }

    // Stop all components
    await Promise.all(
      Object.values(this.components).map(component => {
        if (component && typeof component.stop === 'function') {
          return component.stop();
        }
      })
    );

    // Close HTTP server
    return new Promise((resolve) => {
      if (this.server) {
        this.server.close(() => {
          logger.info('Server stopped');
          resolve();
        });
      } else {
        resolve();
      }
    });
  }
}

// Export for use as module
module.exports = NexusServerV2;

// Run standalone if executed directly
if (require.main === module) {
  const server = new NexusServerV2({
    port: process.env.PORT || 3000
  });

  server.start().catch(error => {
    logger.error('Failed to start server:', error);
    process.exit(1);
  });

  // Graceful shutdown handlers
  const shutdown = async () => {
    await server.stop();
    process.exit(0);
  };

  process.on('SIGTERM', shutdown);
  process.on('SIGINT', shutdown);
}