const { describe, it, before, after, beforeEach } = require('mocha');
const { expect } = require('chai');
const axios = require('axios');
const WebSocket = require('ws');
const fs = require('fs').promises;
const path = require('path');

// Import components for testing
const NexusAPIGateway = require('../gateway/nexus-api-gateway');
const ConsciousnessServer = require('../backend/consciousness-server');
const IDEServer = require('../ide/ide-server');
const ContextServer = require('../context/context-server');
const ProcessorServer = require('../processors/processor-server');

// Test configuration
const TEST_CONFIG = {
  gateway: { port: 4000 },
  consciousness: { port: 4001 },
  ide: { port: 4002 },
  context: { port: 4003 },
  processor: { port: 4004 },
  testTimeout: 30000,
  largeContextSize: 1000000 // 1M tokens
};

class IntegrationTestSuite {
  constructor() {
    this.servers = {};
    this.authToken = null;
    this.baseURL = `http://localhost:${TEST_CONFIG.gateway.port}`;
  }

  async setup() {
    console.log('Starting test servers...');
    
    // Start all services
    this.servers.consciousness = new ConsciousnessServer({ port: TEST_CONFIG.consciousness.port });
    this.servers.ide = new IDEServer({ port: TEST_CONFIG.ide.port });
    this.servers.context = new ContextServer({ port: TEST_CONFIG.context.port });
    this.servers.processor = new ProcessorServer({ port: TEST_CONFIG.processor.port });
    
    // Start gateway with test configuration
    this.servers.gateway = new NexusAPIGateway({
      port: TEST_CONFIG.gateway.port,
      services: {
        consciousness: `http://localhost:${TEST_CONFIG.consciousness.port}`,
        ide: `http://localhost:${TEST_CONFIG.ide.port}`,
        context: `http://localhost:${TEST_CONFIG.context.port}`,
        processor: `http://localhost:${TEST_CONFIG.processor.port}`
      }
    });

    // Start all servers
    await Promise.all([
      this.servers.consciousness.start(),
      this.servers.ide.start(),
      this.servers.context.start(),
      this.servers.processor.start(),
      this.servers.gateway.start()
    ]);

    // Get auth token for tests
    await this.authenticate();
    
    console.log('All test servers started successfully');
  }

  async authenticate() {
    const response = await axios.post(`${this.baseURL}/api/auth/login`, {
      username: 'nexus',
      password: 'consciousness'
    });
    this.authToken = response.data.token;
  }

  async teardown() {
    console.log('Stopping test servers...');
    await Promise.all(
      Object.values(this.servers).map(server => server.stop())
    );
    console.log('All test servers stopped');
  }

  getAuthHeaders() {
    return {
      'Authorization': `Bearer ${this.authToken}`
    };
  }
}

describe('Nexus Integration Tests', function() {
  this.timeout(TEST_CONFIG.testTimeout);
  
  const testSuite = new IntegrationTestSuite();
  
  before(async function() {
    await testSuite.setup();
  });
  
  after(async function() {
    await testSuite.teardown();
  });

  describe('Gateway Health Checks', () => {
    it('should return healthy status', async () => {
      const response = await axios.get(`${testSuite.baseURL}/health`);
      expect(response.status).to.equal(200);
      expect(response.data.status).to.equal('healthy');
      expect(response.data.services).to.be.an('object');
    });
  });

  describe('Authentication', () => {
    it('should authenticate with valid credentials', async () => {
      const response = await axios.post(`${testSuite.baseURL}/api/auth/login`, {
        username: 'nexus',
        password: 'consciousness'
      });
      expect(response.status).to.equal(200);
      expect(response.data.token).to.be.a('string');
      expect(response.data.expiresIn).to.be.a('number');
    });

    it('should reject invalid credentials', async () => {
      try {
        await axios.post(`${testSuite.baseURL}/api/auth/login`, {
          username: 'invalid',
          password: 'wrong'
        });
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error.response.status).to.equal(401);
      }
    });

    it('should refresh token', async () => {
      const response = await axios.post(
        `${testSuite.baseURL}/api/auth/refresh`,
        {},
        { headers: testSuite.getAuthHeaders() }
      );
      expect(response.status).to.equal(200);
      expect(response.data.token).to.be.a('string');
    });
  });

  describe('Backend Connectivity', () => {
    it('should connect to consciousness service', async () => {
      const response = await axios.get(
        `${testSuite.baseURL}/api/consciousness/status`,
        { headers: testSuite.getAuthHeaders() }
      );
      expect(response.status).to.equal(200);
    });

    it('should connect to IDE service', async () => {
      const response = await axios.get(
        `${testSuite.baseURL}/api/ide/status`,
        { headers: testSuite.getAuthHeaders() }
      );
      expect(response.status).to.equal(200);
    });

    it('should connect to context service', async () => {
      const response = await axios.get(
        `${testSuite.baseURL}/api/context/status`,
        { headers: testSuite.getAuthHeaders() }
      );
      expect(response.status).to.equal(200);
    });

    it('should connect to processor service', async () => {
      const response = await axios.get(
        `${testSuite.baseURL}/api/processor/status`,
        { headers: testSuite.getAuthHeaders() }
      );
      expect(response.status).to.equal(200);
    });
  });

  describe('IDE Functionality', () => {
    it('should create a new file', async () => {
      const response = await axios.post(
        `${testSuite.baseURL}/api/ide/files`,
        {
          path: '/test/sample.py',
          content: 'print("Hello, Nexus!")'
        },
        { headers: testSuite.getAuthHeaders() }
      );
      expect(response.status).to.equal(201);
    });

    it('should retrieve file content', async () => {
      const response = await axios.get(
        `${testSuite.baseURL}/api/ide/files?path=/test/sample.py`,
        { headers: testSuite.getAuthHeaders() }
      );
      expect(response.status).to.equal(200);
      expect(response.data.content).to.include('Hello, Nexus!');
    });

    it('should execute code', async () => {
      const response = await axios.post(
        `${testSuite.baseURL}/api/ide/execute`,
        {
          language: 'python',
          code: 'print(2 + 2)'
        },
        { headers: testSuite.getAuthHeaders() }
      );
      expect(response.status).to.equal(200);
      expect(response.data.output).to.include('4');
    });

    it('should provide code completion', async () => {
      const response = await axios.post(
        `${testSuite.baseURL}/api/ide/complete`,
        {
          language: 'python',
          code: 'import os\nos.',
          position: { line: 1, character: 3 }
        },
        { headers: testSuite.getAuthHeaders() }
      );
      expect(response.status).to.equal(200);
      expect(response.data.completions).to.be.an('array');
      expect(response.data.completions.length).to.be.greaterThan(0);
    });
  });

  describe('1M Token Context Handling', () => {
    it('should create large context', async () => {
      // Generate large context (simulating 1M tokens)
      const largeText = 'Lorem ipsum '.repeat(100000);
      
      const response = await axios.post(
        `${testSuite.baseURL}/api/context/create`,
        {
          content: largeText,
          metadata: {
            type: 'document',
            size: largeText.length
          }
        },
        { 
          headers: {
            ...testSuite.getAuthHeaders(),
            'X-Context-Size': TEST_CONFIG.largeContextSize.toString()
          }
        }
      );
      
      expect(response.status).to.equal(201);
      expect(response.data.contextId).to.be.a('string');
      expect(response.data.tokenCount).to.be.greaterThan(900000);
    });

    it('should retrieve large context efficiently', async () => {
      const startTime = Date.now();
      
      const response = await axios.get(
        `${testSuite.baseURL}/api/context/retrieve?size=large`,
        { headers: testSuite.getAuthHeaders() }
      );
      
      const endTime = Date.now();
      const duration = endTime - startTime;
      
      expect(response.status).to.equal(200);
      expect(duration).to.be.lessThan(5000); // Should retrieve in under 5 seconds
    });

    it('should handle context overflow gracefully', async () => {
      const oversizedText = 'x'.repeat(2000000); // 2M characters
      
      try {
        await axios.post(
          `${testSuite.baseURL}/api/context/create`,
          { content: oversizedText },
          { headers: testSuite.getAuthHeaders() }
        );
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error.response.status).to.equal(413);
        expect(error.response.data.error).to.include('too large');
      }
    });
  });

  describe('Processor Integrations', () => {
    it('should process text with Claude', async () => {
      const response = await axios.post(
        `${testSuite.baseURL}/api/processor/claude`,
        {
          prompt: 'Explain quantum computing in one sentence.',
          maxTokens: 100
        },
        { headers: testSuite.getAuthHeaders() }
      );
      
      expect(response.status).to.equal(200);
      expect(response.data.response).to.be.a('string');
      expect(response.data.tokensUsed).to.be.a('number');
    });

    it('should process with GPT', async () => {
      const response = await axios.post(
        `${testSuite.baseURL}/api/processor/gpt`,
        {
          prompt: 'What is machine learning?',
          model: 'gpt-4'
        },
        { headers: testSuite.getAuthHeaders() }
      );
      
      expect(response.status).to.equal(200);
      expect(response.data.response).to.be.a('string');
    });

    it('should handle processor chaining', async () => {
      const response = await axios.post(
        `${testSuite.baseURL}/api/processor/chain`,
        {
          processors: ['claude', 'gpt'],
          prompt: 'Analyze this code: print("Hello")',
          chainMode: 'sequential'
        },
        { headers: testSuite.getAuthHeaders() }
      );
      
      expect(response.status).to.equal(200);
      expect(response.data.results).to.be.an('array');
      expect(response.data.results).to.have.lengthOf(2);
    });
  });

  describe('WebSocket Functionality', () => {
    it('should establish WebSocket connection', (done) => {
      const ws = new WebSocket(
        `ws://localhost:${TEST_CONFIG.gateway.port}/ws/gateway?token=${testSuite.authToken}`
      );
      
      ws.on('open', () => {
        ws.send(JSON.stringify({ type: 'ping' }));
      });
      
      ws.on('message', (data) => {
        const message = JSON.parse(data);
        expect(message.type).to.equal('pong');
        ws.close();
        done();
      });
      
      ws.on('error', done);
    });

    it('should proxy WebSocket to IDE service', (done) => {
      const ws = new WebSocket(
        `ws://localhost:${TEST_CONFIG.gateway.port}/ws/ide?token=${testSuite.authToken}`
      );
      
      ws.on('open', () => {
        ws.send(JSON.stringify({ 
          type: 'code-change',
          file: 'test.py',
          content: 'print("test")'
        }));
        ws.close();
        done();
      });
      
      ws.on('error', done);
    });
  });

  describe('Performance Benchmarks', () => {
    it('should handle 100 concurrent requests', async function() {
      this.timeout(60000);
      
      const requests = Array(100).fill(null).map(() => 
        axios.get(
          `${testSuite.baseURL}/api/consciousness/status`,
          { headers: testSuite.getAuthHeaders() }
        )
      );
      
      const startTime = Date.now();
      const results = await Promise.allSettled(requests);
      const endTime = Date.now();
      
      const successful = results.filter(r => r.status === 'fulfilled').length;
      const duration = endTime - startTime;
      
      expect(successful).to.be.at.least(95); // At least 95% success rate
      expect(duration).to.be.lessThan(10000); // Complete within 10 seconds
    });

    it('should maintain low latency under load', async function() {
      const latencies = [];
      
      for (let i = 0; i < 10; i++) {
        const startTime = Date.now();
        await axios.get(
          `${testSuite.baseURL}/health`
        );
        const endTime = Date.now();
        latencies.push(endTime - startTime);
      }
      
      const avgLatency = latencies.reduce((a, b) => a + b) / latencies.length;
      expect(avgLatency).to.be.lessThan(100); // Average latency under 100ms
    });

    it('should handle large payloads efficiently', async () => {
      const largePayload = {
        data: 'x'.repeat(1000000) // 1MB payload
      };
      
      const startTime = Date.now();
      const response = await axios.post(
        `${testSuite.baseURL}/api/context/analyze`,
        largePayload,
        { headers: testSuite.getAuthHeaders() }
      );
      const endTime = Date.now();
      
      expect(response.status).to.equal(200);
      expect(endTime - startTime).to.be.lessThan(5000); // Process within 5 seconds
    });
  });

  describe('Error Handling', () => {
    it('should handle service downtime gracefully', async () => {
      // Simulate service downtime by stopping a service
      await testSuite.servers.processor.stop();
      
      try {
        await axios.get(
          `${testSuite.baseURL}/api/processor/status`,
          { headers: testSuite.getAuthHeaders() }
        );
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error.response.status).to.equal(502);
        expect(error.response.data.error).to.include('Service unavailable');
      }
      
      // Restart the service
      await testSuite.servers.processor.start();
    });

    it('should validate request data', async () => {
      try {
        await axios.post(
          `${testSuite.baseURL}/api/auth/login`,
          { username: '' } // Missing password
        );
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error.response.status).to.equal(400);
        expect(error.response.data.errors).to.be.an('array');
      }
    });
  });

  describe('Session Management', () => {
    it('should maintain session across requests', async () => {
      // Create a session
      const sessionResponse = await axios.post(
        `${testSuite.baseURL}/api/context/session/create`,
        { contextSize: TEST_CONFIG.largeContextSize },
        { headers: testSuite.getAuthHeaders() }
      );
      
      const sessionId = sessionResponse.data.sessionId;
      
      // Use the session
      const contextResponse = await axios.post(
        `${testSuite.baseURL}/api/context/session/${sessionId}/add`,
        { content: 'Test content' },
        { headers: testSuite.getAuthHeaders() }
      );
      
      expect(contextResponse.status).to.equal(200);
      expect(contextResponse.data.totalTokens).to.be.a('number');
    });
  });
});

// Performance monitoring utilities
class PerformanceMonitor {
  constructor() {
    this.metrics = {
      requests: 0,
      errors: 0,
      totalLatency: 0,
      peakLatency: 0
    };
  }

  recordRequest(latency, error = false) {
    this.metrics.requests++;
    if (error) this.metrics.errors++;
    this.metrics.totalLatency += latency;
    if (latency > this.metrics.peakLatency) {
      this.metrics.peakLatency = latency;
    }
  }

  getReport() {
    return {
      totalRequests: this.metrics.requests,
      errorRate: (this.metrics.errors / this.metrics.requests) * 100,
      averageLatency: this.metrics.totalLatency / this.metrics.requests,
      peakLatency: this.metrics.peakLatency
    };
  }
}

// Export test utilities
module.exports = {
  IntegrationTestSuite,
  PerformanceMonitor,
  TEST_CONFIG
};