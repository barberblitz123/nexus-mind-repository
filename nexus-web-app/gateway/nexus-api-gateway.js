const express = require('express');
const httpProxy = require('http-proxy-middleware');
const WebSocket = require('ws');
const jwt = require('jsonwebtoken');
const rateLimit = require('express-rate-limit');
const { body, validationResult } = require('express-validator');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const winston = require('winston');

// Initialize logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

class NexusAPIGateway {
  constructor(config = {}) {
    this.app = express();
    this.server = null;
    this.wss = null;
    this.config = {
      port: config.port || 3000,
      jwtSecret: config.jwtSecret || process.env.JWT_SECRET || 'nexus-consciousness-secret',
      services: {
        consciousness: config.consciousnessService || 'http://localhost:5001',
        ide: config.ideService || 'http://localhost:5002',
        context: config.contextService || 'http://localhost:5003',
        processor: config.processorService || 'http://localhost:5004',
        knowledge: config.knowledgeService || 'http://localhost:5005',
        mcp: config.mcpService || 'http://localhost:3001'
      },
      rateLimits: {
        general: { windowMs: 15 * 60 * 1000, max: 100 },
        api: { windowMs: 15 * 60 * 1000, max: 1000 },
        auth: { windowMs: 15 * 60 * 1000, max: 5 }
      },
      ...config
    };
    
    this.setupMiddleware();
    this.setupRoutes();
    this.setupWebSocketProxy();
  }

  setupMiddleware() {
    // Security middleware
    this.app.use(helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          scriptSrc: ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          imgSrc: ["'self'", "data:", "https:"],
          connectSrc: ["'self'", "ws:", "wss:"],
        },
      },
    }));
    
    // CORS configuration
    this.app.use(cors({
      origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
      credentials: true
    }));
    
    // Compression
    this.app.use(compression());
    
    // Body parsing
    this.app.use(express.json({ limit: '50mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '50mb' }));
    
    // Request logging
    this.app.use((req, res, next) => {
      logger.info(`${req.method} ${req.path}`, {
        ip: req.ip,
        userAgent: req.get('user-agent')
      });
      next();
    });
  }

  setupRoutes() {
    // Health check endpoint
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        services: this.config.services
      });
    });

    // Authentication routes
    this.setupAuthRoutes();
    
    // Service proxy routes
    this.setupServiceProxies();
    
    // Error handling
    this.app.use((err, req, res, next) => {
      logger.error('Gateway error:', err);
      res.status(err.status || 500).json({
        error: 'Internal gateway error',
        message: process.env.NODE_ENV === 'development' ? err.message : undefined
      });
    });
  }

  setupAuthRoutes() {
    const authLimiter = rateLimit(this.config.rateLimits.auth);
    
    // Login endpoint
    this.app.post('/api/auth/login', 
      authLimiter,
      [
        body('username').notEmpty().trim(),
        body('password').notEmpty()
      ],
      async (req, res) => {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
          return res.status(400).json({ errors: errors.array() });
        }

        try {
          // Here you would validate credentials against your user store
          const { username, password } = req.body;
          
          // For demo purposes - replace with real authentication
          if (username === 'nexus' && password === 'consciousness') {
            const token = jwt.sign(
              { 
                username, 
                role: 'admin',
                timestamp: Date.now()
              },
              this.config.jwtSecret,
              { expiresIn: '24h' }
            );
            
            res.json({
              token,
              expiresIn: 86400,
              role: 'admin'
            });
          } else {
            res.status(401).json({ error: 'Invalid credentials' });
          }
        } catch (error) {
          logger.error('Authentication error:', error);
          res.status(500).json({ error: 'Authentication failed' });
        }
      }
    );

    // Token refresh endpoint
    this.app.post('/api/auth/refresh', this.authenticateToken, (req, res) => {
      const token = jwt.sign(
        { 
          username: req.user.username, 
          role: req.user.role,
          timestamp: Date.now()
        },
        this.config.jwtSecret,
        { expiresIn: '24h' }
      );
      
      res.json({ token, expiresIn: 86400 });
    });
  }

  setupServiceProxies() {
    const apiLimiter = rateLimit(this.config.rateLimits.api);
    
    // Consciousness service proxy
    this.app.use('/api/consciousness',
      apiLimiter,
      this.authenticateToken,
      this.createProxy(this.config.services.consciousness, {
        pathRewrite: { '^/api/consciousness': '' }
      })
    );
    
    // IDE service proxy
    this.app.use('/api/ide',
      apiLimiter,
      this.authenticateToken,
      this.createProxy(this.config.services.ide, {
        pathRewrite: { '^/api/ide': '' }
      })
    );
    
    // Context service proxy (handles 1M token contexts)
    this.app.use('/api/context',
      apiLimiter,
      this.authenticateToken,
      this.createProxy(this.config.services.context, {
        pathRewrite: { '^/api/context': '' },
        onProxyReq: (proxyReq, req, res) => {
          // Add context-specific headers
          proxyReq.setHeader('X-Context-Size', req.get('X-Context-Size') || '1000000');
          proxyReq.setHeader('X-Context-Type', req.get('X-Context-Type') || 'full');
        }
      })
    );
    
    // Processor service proxy
    this.app.use('/api/processor',
      apiLimiter,
      this.authenticateToken,
      this.createProxy(this.config.services.processor, {
        pathRewrite: { '^/api/processor': '' }
      })
    );
    
    // Knowledge service proxy
    this.app.use('/api/knowledge',
      apiLimiter,
      this.authenticateToken,
      this.createProxy(this.config.services.knowledge, {
        pathRewrite: { '^/api/knowledge': '' }
      })
    );
    
    // MCP service proxy
    this.app.use('/api/mcp',
      apiLimiter,
      this.authenticateToken,
      this.createProxy(this.config.services.mcp, {
        pathRewrite: { '^/api/mcp': '' }
      })
    );
  }

  createProxy(target, options = {}) {
    return httpProxy.createProxyMiddleware({
      target,
      changeOrigin: true,
      timeout: 300000, // 5 minutes for large context operations
      proxyTimeout: 300000,
      onError: (err, req, res) => {
        logger.error(`Proxy error for ${target}:`, err);
        res.status(502).json({
          error: 'Service unavailable',
          service: target
        });
      },
      ...options
    });
  }

  setupWebSocketProxy() {
    // WebSocket proxy for real-time features
    const wsProxy = httpProxy.createProxyMiddleware({
      ws: true,
      changeOrigin: true
    });

    this.app.on('upgrade', (request, socket, head) => {
      const pathname = new URL(request.url, `http://${request.headers.host}`).pathname;
      
      // Authenticate WebSocket connections
      const token = this.extractTokenFromRequest(request);
      if (!token) {
        socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n');
        socket.destroy();
        return;
      }

      try {
        const decoded = jwt.verify(token, this.config.jwtSecret);
        request.user = decoded;
        
        // Route WebSocket connections to appropriate services
        let target;
        if (pathname.startsWith('/ws/consciousness')) {
          target = this.config.services.consciousness;
        } else if (pathname.startsWith('/ws/ide')) {
          target = this.config.services.ide;
        } else if (pathname.startsWith('/ws/context')) {
          target = this.config.services.context;
        } else if (pathname.startsWith('/ws/processor')) {
          target = this.config.services.processor;
        } else {
          socket.write('HTTP/1.1 404 Not Found\r\n\r\n');
          socket.destroy();
          return;
        }

        wsProxy.upgrade(request, socket, head, {
          target,
          ws: true
        });
      } catch (error) {
        logger.error('WebSocket authentication error:', error);
        socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n');
        socket.destroy();
      }
    });
  }

  authenticateToken(req, res, next) {
    const token = this.extractTokenFromRequest(req);
    
    if (!token) {
      return res.status(401).json({ error: 'No token provided' });
    }

    jwt.verify(token, this.config.jwtSecret, (err, user) => {
      if (err) {
        return res.status(403).json({ error: 'Invalid token' });
      }
      req.user = user;
      next();
    });
  }

  extractTokenFromRequest(req) {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    return token || req.query.token;
  }

  async start() {
    return new Promise((resolve, reject) => {
      this.server = this.app.listen(this.config.port, (err) => {
        if (err) {
          reject(err);
        } else {
          logger.info(`Nexus API Gateway running on port ${this.config.port}`);
          
          // Setup WebSocket server
          this.wss = new WebSocket.Server({ 
            server: this.server,
            path: '/ws/gateway'
          });
          
          this.wss.on('connection', (ws, req) => {
            logger.info('New WebSocket connection to gateway');
            
            ws.on('message', (message) => {
              // Handle gateway-specific WebSocket messages
              try {
                const data = JSON.parse(message);
                this.handleGatewayMessage(ws, data);
              } catch (error) {
                ws.send(JSON.stringify({ error: 'Invalid message format' }));
              }
            });
            
            ws.on('close', () => {
              logger.info('WebSocket connection closed');
            });
          });
          
          resolve(this.server);
        }
      });
    });
  }

  handleGatewayMessage(ws, data) {
    switch (data.type) {
      case 'ping':
        ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
        break;
      case 'service-status':
        this.checkServiceStatus().then(status => {
          ws.send(JSON.stringify({ type: 'status', data: status }));
        });
        break;
      case 'metrics':
        ws.send(JSON.stringify({ 
          type: 'metrics', 
          data: this.getMetrics() 
        }));
        break;
      default:
        ws.send(JSON.stringify({ error: 'Unknown message type' }));
    }
  }

  async checkServiceStatus() {
    const status = {};
    for (const [name, url] of Object.entries(this.config.services)) {
      try {
        const response = await fetch(`${url}/health`);
        status[name] = response.ok ? 'healthy' : 'unhealthy';
      } catch (error) {
        status[name] = 'unreachable';
      }
    }
    return status;
  }

  getMetrics() {
    return {
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      timestamp: Date.now()
    };
  }

  async stop() {
    return new Promise((resolve) => {
      if (this.wss) {
        this.wss.close(() => {
          logger.info('WebSocket server closed');
        });
      }
      
      if (this.server) {
        this.server.close(() => {
          logger.info('API Gateway stopped');
          resolve();
        });
      } else {
        resolve();
      }
    });
  }
}

// Export for use as module
module.exports = NexusAPIGateway;

// Run standalone if executed directly
if (require.main === module) {
  const gateway = new NexusAPIGateway({
    port: process.env.GATEWAY_PORT || 3000
  });
  
  gateway.start().catch(error => {
    logger.error('Failed to start gateway:', error);
    process.exit(1);
  });
  
  // Graceful shutdown
  process.on('SIGTERM', async () => {
    logger.info('SIGTERM received, shutting down gracefully');
    await gateway.stop();
    process.exit(0);
  });
  
  process.on('SIGINT', async () => {
    logger.info('SIGINT received, shutting down gracefully');
    await gateway.stop();
    process.exit(0);
  });
}