#!/usr/bin/env python3
"""
NEXUS 2.0 Webinar Interface - Production-Grade Web Interface
Compatible with NEXUS 2.0 Production Build
Provides real-time collaboration, streaming, and system monitoring
"""

from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
import asyncio
import json
import uvicorn
from datetime import datetime
import uuid
import aiofiles
import os
import logging
from contextlib import asynccontextmanager
import aiohttp
import redis.asyncio as redis
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# NEXUS 2.0 Production imports
from nexus_core_production import (
    NexusProductionCore, ServiceHealthCheck, MetricsCollector,
    CircuitBreakerMixin, request_count, request_duration
)
from nexus_integration_core import (
    MessageBus, ServiceDiscovery, StateManager,
    DistributedTransactionManager, MessagePriority
)
from nexus_startup_manager import StartupManager, ServiceStatus
from nexus_config_production import ProductionConfig
from nexus_database_production import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Metrics
webinar_connections = Gauge('nexus_webinar_connections', 'Active webinar connections', ['room_id'])
webinar_messages = Counter('nexus_webinar_messages_total', 'Total webinar messages', ['type'])
webinar_latency = Histogram('nexus_webinar_latency_seconds', 'Webinar message latency')

# Pydantic models for Webinar API
class WebinarSession(BaseModel):
    """Webinar session configuration"""
    title: str
    description: Optional[str] = None
    host_id: str
    scheduled_start: Optional[datetime] = None
    max_participants: int = Field(default=100, ge=1, le=1000)
    features: Dict[str, bool] = Field(default_factory=lambda: {
        "chat": True,
        "video": True,
        "screen_share": True,
        "recording": False,
        "ai_assistance": True
    })
    access_control: Dict[str, Any] = Field(default_factory=dict)

class ParticipantJoin(BaseModel):
    """Participant join request"""
    session_id: str
    user_id: str
    display_name: str
    role: str = "participant"  # host, co-host, participant, viewer
    capabilities: Dict[str, bool] = Field(default_factory=lambda: {
        "video": True,
        "audio": True,
        "chat": True
    })

class ChatMessage(BaseModel):
    """Chat message in webinar"""
    session_id: str
    user_id: str
    message: str
    message_type: str = "text"  # text, system, ai_response
    attachments: Optional[List[str]] = None
    reply_to: Optional[str] = None

class SystemCommand(BaseModel):
    """System command for webinar control"""
    command: str  # start_recording, stop_recording, mute_all, etc.
    parameters: Dict[str, Any] = Field(default_factory=dict)
    authorization: Optional[str] = None

class AIAssistantQuery(BaseModel):
    """Query for AI assistant during webinar"""
    session_id: str
    query: str
    context: Dict[str, Any] = Field(default_factory=dict)
    response_format: str = "text"  # text, audio, visual

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting NEXUS Webinar Interface...")
    
    # Initialize core services
    app.state.config = ProductionConfig()
    app.state.message_bus = MessageBus()
    app.state.service_discovery = ServiceDiscovery()
    app.state.state_manager = StateManager()
    app.state.db_manager = DatabaseManager(app.state.config)
    
    # Initialize Redis connection
    app.state.redis = await redis.from_url(
        app.state.config.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    
    # Start background services
    asyncio.create_task(app.state.message_bus.start())
    asyncio.create_task(monitor_system_health(app))
    asyncio.create_task(cleanup_inactive_sessions(app))
    
    # Register with service discovery
    await app.state.service_discovery.register_service(
        "webinar_interface",
        f"http://localhost:{app.state.config.WEBINAR_PORT}",
        tags=["web", "api", "webinar"],
        health_check_url="/health"
    )
    
    yield
    
    # Shutdown
    logger.info("Shutting down NEXUS Webinar Interface...")
    await app.state.redis.close()
    await app.state.message_bus.stop()
    await app.state.service_discovery.deregister_service("webinar_interface")

# Create FastAPI app
app = FastAPI(
    title="NEXUS 2.0 Webinar Interface",
    description="Production-grade webinar and collaboration platform",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (use Redis in production)
webinar_sessions: Dict[str, Dict[str, Any]] = {}
active_connections: Dict[str, List[WebSocket]] = {}
participant_info: Dict[str, Dict[str, Any]] = {}

# Main UI Route
@app.get("/")
async def root():
    """Serve the NEXUS Webinar Interface"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>NEXUS 2.0 Webinar Platform</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            color: #fff;
            overflow: hidden;
            height: 100vh;
        }
        
        /* Layout */
        .container {
            display: grid;
            grid-template-rows: 60px 1fr;
            height: 100vh;
        }
        
        /* Header */
        .header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        
        .header h1 {
            font-size: 24px;
            font-weight: 600;
            letter-spacing: 1px;
        }
        
        .header .status {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #4ade80;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(1.2); }
        }
        
        /* Main Content */
        .main-content {
            display: grid;
            grid-template-columns: 1fr 350px;
            height: 100%;
        }
        
        /* Video Area */
        .video-area {
            background: #000;
            position: relative;
            display: grid;
            grid-template-rows: 1fr auto;
        }
        
        .video-grid {
            display: grid;
            gap: 10px;
            padding: 20px;
            overflow-y: auto;
        }
        
        .video-grid.single { grid-template-columns: 1fr; }
        .video-grid.dual { grid-template-columns: 1fr 1fr; }
        .video-grid.quad { grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; }
        .video-grid.many { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
        
        .video-container {
            background: #1a1a1a;
            border-radius: 12px;
            position: relative;
            aspect-ratio: 16/9;
            overflow: hidden;
            border: 2px solid transparent;
            transition: all 0.3s ease;
        }
        
        .video-container:hover {
            border-color: #3b82f6;
            transform: scale(1.02);
        }
        
        .video-container.speaking {
            border-color: #4ade80;
            box-shadow: 0 0 20px rgba(74, 222, 128, 0.4);
        }
        
        .video-placeholder {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        }
        
        .participant-avatar {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: #3b82f6;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            font-weight: 600;
            margin-bottom: 12px;
        }
        
        .participant-name {
            font-size: 16px;
            font-weight: 500;
            text-align: center;
        }
        
        .video-controls {
            position: absolute;
            bottom: 10px;
            left: 10px;
            right: 10px;
            display: flex;
            justify-content: center;
            gap: 10px;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .video-container:hover .video-controls {
            opacity: 1;
        }
        
        /* Controls Bar */
        .controls-bar {
            background: #1a1a1a;
            padding: 20px;
            display: flex;
            justify-content: center;
            gap: 20px;
            border-top: 1px solid #333;
        }
        
        .control-btn {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            border: none;
            background: #2a2a2a;
            color: #fff;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            transition: all 0.3s ease;
            position: relative;
        }
        
        .control-btn:hover {
            background: #3a3a3a;
            transform: scale(1.1);
        }
        
        .control-btn.active {
            background: #3b82f6;
        }
        
        .control-btn.danger {
            background: #ef4444;
        }
        
        /* Sidebar */
        .sidebar {
            background: #0f0f0f;
            border-left: 1px solid #333;
            display: flex;
            flex-direction: column;
        }
        
        .sidebar-tabs {
            display: flex;
            border-bottom: 1px solid #333;
        }
        
        .sidebar-tab {
            flex: 1;
            padding: 15px;
            background: none;
            border: none;
            color: #666;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
            position: relative;
        }
        
        .sidebar-tab:hover {
            color: #fff;
            background: rgba(255,255,255,0.05);
        }
        
        .sidebar-tab.active {
            color: #3b82f6;
        }
        
        .sidebar-tab.active::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: #3b82f6;
        }
        
        .sidebar-content {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
        }
        
        /* Chat */
        .chat-messages {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .chat-message {
            background: rgba(255,255,255,0.05);
            padding: 12px;
            border-radius: 8px;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .chat-message .author {
            font-weight: 600;
            color: #3b82f6;
            margin-bottom: 4px;
            font-size: 14px;
        }
        
        .chat-message .content {
            font-size: 14px;
            line-height: 1.5;
        }
        
        .chat-message .timestamp {
            font-size: 12px;
            color: #666;
            margin-top: 4px;
        }
        
        .chat-message.system {
            background: rgba(59, 130, 246, 0.1);
            border-left: 3px solid #3b82f6;
        }
        
        .chat-message.ai {
            background: rgba(74, 222, 128, 0.1);
            border-left: 3px solid #4ade80;
        }
        
        .chat-input-container {
            padding: 20px;
            border-top: 1px solid #333;
        }
        
        .chat-input {
            width: 100%;
            background: rgba(255,255,255,0.05);
            border: 1px solid #333;
            border-radius: 8px;
            padding: 12px;
            color: #fff;
            font-size: 14px;
            resize: none;
            min-height: 50px;
            max-height: 150px;
        }
        
        .chat-input:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
        }
        
        /* Participants List */
        .participants-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .participant-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        
        .participant-item:hover {
            background: rgba(255,255,255,0.08);
        }
        
        .participant-avatar-small {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: #3b82f6;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: 600;
        }
        
        .participant-info {
            flex: 1;
        }
        
        .participant-info .name {
            font-weight: 500;
            font-size: 14px;
        }
        
        .participant-info .role {
            font-size: 12px;
            color: #666;
        }
        
        .participant-status {
            display: flex;
            gap: 8px;
        }
        
        .status-icon {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: rgba(255,255,255,0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
        }
        
        .status-icon.active {
            background: #4ade80;
            color: #000;
        }
        
        /* AI Assistant */
        .ai-panel {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        
        .ai-suggestion {
            background: linear-gradient(135deg, rgba(74, 222, 128, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%);
            padding: 16px;
            border-radius: 8px;
            border: 1px solid rgba(74, 222, 128, 0.3);
        }
        
        .ai-suggestion h4 {
            color: #4ade80;
            margin-bottom: 8px;
            font-size: 14px;
        }
        
        .ai-suggestion p {
            font-size: 13px;
            line-height: 1.5;
            color: #ccc;
        }
        
        .ai-actions {
            display: flex;
            gap: 8px;
            margin-top: 12px;
        }
        
        .ai-action-btn {
            padding: 6px 12px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 6px;
            color: #fff;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .ai-action-btn:hover {
            background: rgba(255,255,255,0.2);
            transform: translateY(-1px);
        }
        
        /* Modals */
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.8);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .modal.active {
            display: flex;
        }
        
        .modal-content {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 30px;
            max-width: 500px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
            animation: modalSlideIn 0.3s ease;
        }
        
        @keyframes modalSlideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .modal-header {
            margin-bottom: 20px;
        }
        
        .modal-header h2 {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .modal-header p {
            color: #666;
            font-size: 14px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-size: 14px;
            font-weight: 500;
        }
        
        .form-input {
            width: 100%;
            background: rgba(255,255,255,0.05);
            border: 1px solid #333;
            border-radius: 8px;
            padding: 12px;
            color: #fff;
            font-size: 14px;
        }
        
        .form-input:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
        }
        
        .modal-actions {
            display: flex;
            gap: 12px;
            justify-content: flex-end;
            margin-top: 30px;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: #3b82f6;
            color: #fff;
        }
        
        .btn-primary:hover {
            background: #2563eb;
            transform: translateY(-1px);
        }
        
        .btn-secondary {
            background: rgba(255,255,255,0.1);
            color: #fff;
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .btn-secondary:hover {
            background: rgba(255,255,255,0.2);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .sidebar {
                position: fixed;
                right: -350px;
                top: 60px;
                bottom: 0;
                width: 350px;
                transition: right 0.3s ease;
                z-index: 100;
            }
            
            .sidebar.open {
                right: 0;
            }
            
            .video-grid {
                padding: 10px;
            }
            
            .controls-bar {
                padding: 15px;
                gap: 15px;
            }
            
            .control-btn {
                width: 40px;
                height: 40px;
                font-size: 18px;
            }
        }
        
        /* Loading Animation */
        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
        }
        
        .loading-spinner {
            width: 50px;
            height: 50px;
            border: 3px solid rgba(255,255,255,0.1);
            border-top-color: #3b82f6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Notifications */
        .notification {
            position: fixed;
            top: 80px;
            right: 20px;
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 16px 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            animation: notificationSlide 0.3s ease;
            z-index: 1000;
        }
        
        @keyframes notificationSlide {
            from { opacity: 0; transform: translateX(100%); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .notification.success {
            border-color: #4ade80;
            background: linear-gradient(135deg, rgba(74, 222, 128, 0.1) 0%, rgba(74, 222, 128, 0.05) 100%);
        }
        
        .notification.error {
            border-color: #ef4444;
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%);
        }
        
        .notification.info {
            border-color: #3b82f6;
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%);
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>NEXUS Webinar Platform</h1>
            <div class="status">
                <div class="status-indicator">
                    <div class="status-dot"></div>
                    <span id="connectionStatus">Connected</span>
                </div>
                <div class="status-indicator">
                    <span id="participantCount">0</span> Participants
                </div>
                <div class="status-indicator">
                    <span id="sessionTime">00:00</span>
                </div>
            </div>
        </div>
        
        <!-- Main Content -->
        <div class="main-content">
            <!-- Video Area -->
            <div class="video-area">
                <div class="video-grid single" id="videoGrid">
                    <div class="loading">
                        <div class="loading-spinner"></div>
                    </div>
                </div>
                
                <!-- Controls -->
                <div class="controls-bar">
                    <button class="control-btn" id="micBtn" title="Toggle Microphone">
                        🎤
                    </button>
                    <button class="control-btn" id="cameraBtn" title="Toggle Camera">
                        📹
                    </button>
                    <button class="control-btn" id="screenBtn" title="Share Screen">
                        🖥️
                    </button>
                    <button class="control-btn" id="recordBtn" title="Record Session">
                        ⏺️
                    </button>
                    <button class="control-btn" id="settingsBtn" title="Settings">
                        ⚙️
                    </button>
                    <button class="control-btn danger" id="leaveBtn" title="Leave Webinar">
                        📞
                    </button>
                </div>
            </div>
            
            <!-- Sidebar -->
            <div class="sidebar" id="sidebar">
                <div class="sidebar-tabs">
                    <button class="sidebar-tab active" data-tab="chat">Chat</button>
                    <button class="sidebar-tab" data-tab="participants">Participants</button>
                    <button class="sidebar-tab" data-tab="ai">AI Assistant</button>
                </div>
                
                <div class="sidebar-content">
                    <!-- Chat Tab -->
                    <div class="tab-content" id="chatTab">
                        <div class="chat-messages" id="chatMessages">
                            <div class="chat-message system">
                                <div class="content">Welcome to NEXUS Webinar Platform</div>
                                <div class="timestamp">System</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Participants Tab -->
                    <div class="tab-content" id="participantsTab" style="display: none;">
                        <div class="participants-list" id="participantsList">
                            <!-- Participants will be added here -->
                        </div>
                    </div>
                    
                    <!-- AI Assistant Tab -->
                    <div class="tab-content" id="aiTab" style="display: none;">
                        <div class="ai-panel">
                            <div class="ai-suggestion">
                                <h4>🤖 AI Meeting Assistant</h4>
                                <p>I'm here to help with transcription, summaries, and answering questions during your webinar.</p>
                            </div>
                            
                            <div class="form-group">
                                <textarea class="chat-input" placeholder="Ask the AI assistant..." id="aiQuery"></textarea>
                            </div>
                            
                            <button class="btn btn-primary" onclick="askAI()">Ask AI</button>
                            
                            <div id="aiResponses">
                                <!-- AI responses will appear here -->
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Chat Input (visible only in chat tab) -->
                <div class="chat-input-container" id="chatInputContainer">
                    <textarea class="chat-input" placeholder="Type a message..." id="chatInput"></textarea>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Join Modal -->
    <div class="modal active" id="joinModal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>Join Webinar</h2>
                <p>Enter your details to join the webinar session</p>
            </div>
            
            <div class="form-group">
                <label>Your Name</label>
                <input type="text" class="form-input" id="userName" placeholder="Enter your name">
            </div>
            
            <div class="form-group">
                <label>Session ID</label>
                <input type="text" class="form-input" id="sessionId" placeholder="Enter session ID or leave blank for demo">
            </div>
            
            <div class="form-group">
                <label>Role</label>
                <select class="form-input" id="userRole">
                    <option value="participant">Participant</option>
                    <option value="host">Host</option>
                    <option value="co-host">Co-Host</option>
                    <option value="viewer">Viewer</option>
                </select>
            </div>
            
            <div class="modal-actions">
                <button class="btn btn-primary" onclick="joinWebinar()">Join Webinar</button>
            </div>
        </div>
    </div>
    
    <script>
        // Global variables
        let ws = null;
        let localStream = null;
        let peerConnections = {};
        let sessionInfo = {};
        let userId = null;
        let sessionTimer = null;
        let startTime = null;
        
        // Initialize WebSocket connection
        function initWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws/webinar`);
            
            ws.onopen = () => {
                console.log('WebSocket connected');
                updateConnectionStatus('Connected');
            };
            
            ws.onmessage = async (event) => {
                const data = JSON.parse(event.data);
                await handleWebSocketMessage(data);
            };
            
            ws.onclose = () => {
                console.log('WebSocket disconnected');
                updateConnectionStatus('Disconnected');
                setTimeout(initWebSocket, 3000);
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                updateConnectionStatus('Error');
            };
        }
        
        // Handle incoming WebSocket messages
        async function handleWebSocketMessage(data) {
            switch (data.type) {
                case 'participant_joined':
                    addParticipant(data.participant);
                    showNotification(`${data.participant.display_name} joined`, 'info');
                    break;
                    
                case 'participant_left':
                    removeParticipant(data.user_id);
                    showNotification(`${data.display_name} left`, 'info');
                    break;
                    
                case 'chat_message':
                    addChatMessage(data.message);
                    break;
                    
                case 'ai_response':
                    addAIResponse(data.response);
                    break;
                    
                case 'webrtc_offer':
                    await handleWebRTCOffer(data);
                    break;
                    
                case 'webrtc_answer':
                    await handleWebRTCAnswer(data);
                    break;
                    
                case 'webrtc_ice_candidate':
                    await handleICECandidate(data);
                    break;
                    
                case 'session_update':
                    updateSessionInfo(data.session);
                    break;
                    
                case 'system_notification':
                    showNotification(data.message, data.level || 'info');
                    break;
            }
        }
        
        // Join webinar
        async function joinWebinar() {
            const userName = document.getElementById('userName').value.trim();
            const sessionId = document.getElementById('sessionId').value.trim() || 'demo';
            const userRole = document.getElementById('userRole').value;
            
            if (!userName) {
                showNotification('Please enter your name', 'error');
                return;
            }
            
            userId = generateUserId();
            
            // Initialize local media
            try {
                localStream = await navigator.mediaDevices.getUserMedia({
                    video: true,
                    audio: true
                });
                
                // Send join request
                const response = await fetch('/api/webinar/join', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: sessionId,
                        user_id: userId,
                        display_name: userName,
                        role: userRole
                    })
                });
                
                if (response.ok) {
                    const result = await response.json();
                    sessionInfo = result.session;
                    
                    // Close modal
                    document.getElementById('joinModal').classList.remove('active');
                    
                    // Initialize UI
                    initializeUI();
                    
                    // Connect WebSocket
                    initWebSocket();
                    
                    // Start session timer
                    startSessionTimer();
                    
                    showNotification('Successfully joined webinar', 'success');
                } else {
                    throw new Error('Failed to join webinar');
                }
            } catch (error) {
                console.error('Error joining webinar:', error);
                showNotification('Failed to join webinar: ' + error.message, 'error');
            }
        }
        
        // Initialize UI after joining
        function initializeUI() {
            // Clear loading
            document.getElementById('videoGrid').innerHTML = '';
            
            // Add local video
            addVideoStream(userId, localStream, true);
            
            // Setup controls
            setupControls();
            
            // Setup chat
            setupChat();
            
            // Setup tabs
            setupTabs();
        }
        
        // Add video stream to grid
        function addVideoStream(peerId, stream, isLocal = false) {
            const videoGrid = document.getElementById('videoGrid');
            
            const container = document.createElement('div');
            container.className = 'video-container';
            container.id = `video-${peerId}`;
            
            const video = document.createElement('video');
            video.srcObject = stream;
            video.autoplay = true;
            video.playsInline = true;
            if (isLocal) video.muted = true;
            
            container.appendChild(video);
            
            // Add controls overlay
            const controls = document.createElement('div');
            controls.className = 'video-controls';
            controls.innerHTML = `
                <button class="control-btn" onclick="togglePeerAudio('${peerId}')">🔇</button>
                <button class="control-btn" onclick="togglePeerVideo('${peerId}')">📹</button>
            `;
            container.appendChild(controls);
            
            videoGrid.appendChild(container);
            
            // Update grid layout
            updateVideoGrid();
        }
        
        // Update video grid layout based on participant count
        function updateVideoGrid() {
            const videoGrid = document.getElementById('videoGrid');
            const videoCount = videoGrid.children.length;
            
            videoGrid.className = 'video-grid';
            if (videoCount === 1) {
                videoGrid.classList.add('single');
            } else if (videoCount === 2) {
                videoGrid.classList.add('dual');
            } else if (videoCount <= 4) {
                videoGrid.classList.add('quad');
            } else {
                videoGrid.classList.add('many');
            }
        }
        
        // Setup control buttons
        function setupControls() {
            // Microphone toggle
            document.getElementById('micBtn').addEventListener('click', () => {
                const audioTrack = localStream.getAudioTracks()[0];
                if (audioTrack) {
                    audioTrack.enabled = !audioTrack.enabled;
                    document.getElementById('micBtn').classList.toggle('active', audioTrack.enabled);
                }
            });
            
            // Camera toggle
            document.getElementById('cameraBtn').addEventListener('click', () => {
                const videoTrack = localStream.getVideoTracks()[0];
                if (videoTrack) {
                    videoTrack.enabled = !videoTrack.enabled;
                    document.getElementById('cameraBtn').classList.toggle('active', videoTrack.enabled);
                }
            });
            
            // Screen share
            document.getElementById('screenBtn').addEventListener('click', async () => {
                try {
                    const screenStream = await navigator.mediaDevices.getDisplayMedia({
                        video: true,
                        audio: true
                    });
                    
                    // Replace video track
                    const videoTrack = screenStream.getVideoTracks()[0];
                    const sender = peerConnections[userId]?.getSenders().find(
                        s => s.track && s.track.kind === 'video'
                    );
                    
                    if (sender) {
                        sender.replaceTrack(videoTrack);
                    }
                    
                    videoTrack.onended = () => {
                        // Restore camera when screen share ends
                        const cameraTrack = localStream.getVideoTracks()[0];
                        if (sender && cameraTrack) {
                            sender.replaceTrack(cameraTrack);
                        }
                        document.getElementById('screenBtn').classList.remove('active');
                    };
                    
                    document.getElementById('screenBtn').classList.add('active');
                } catch (error) {
                    console.error('Error sharing screen:', error);
                    showNotification('Failed to share screen', 'error');
                }
            });
            
            // Recording
            document.getElementById('recordBtn').addEventListener('click', () => {
                const isRecording = document.getElementById('recordBtn').classList.contains('active');
                
                if (isRecording) {
                    stopRecording();
                } else {
                    startRecording();
                }
            });
            
            // Settings
            document.getElementById('settingsBtn').addEventListener('click', () => {
                showNotification('Settings panel coming soon', 'info');
            });
            
            // Leave
            document.getElementById('leaveBtn').addEventListener('click', () => {
                if (confirm('Are you sure you want to leave the webinar?')) {
                    leaveWebinar();
                }
            });
        }
        
        // Setup chat functionality
        function setupChat() {
            const chatInput = document.getElementById('chatInput');
            
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendChatMessage();
                }
            });
        }
        
        // Send chat message
        function sendChatMessage() {
            const chatInput = document.getElementById('chatInput');
            const message = chatInput.value.trim();
            
            if (!message) return;
            
            ws.send(JSON.stringify({
                type: 'chat_message',
                session_id: sessionInfo.id,
                user_id: userId,
                message: message
            }));
            
            chatInput.value = '';
        }
        
        // Add chat message to UI
        function addChatMessage(message) {
            const chatMessages = document.getElementById('chatMessages');
            
            const messageEl = document.createElement('div');
            messageEl.className = `chat-message ${message.message_type}`;
            messageEl.innerHTML = `
                <div class="author">${message.author}</div>
                <div class="content">${message.content}</div>
                <div class="timestamp">${new Date(message.timestamp).toLocaleTimeString()}</div>
            `;
            
            chatMessages.appendChild(messageEl);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        // Setup tab switching
        function setupTabs() {
            const tabs = document.querySelectorAll('.sidebar-tab');
            const chatInputContainer = document.getElementById('chatInputContainer');
            
            tabs.forEach(tab => {
                tab.addEventListener('click', () => {
                    // Update active tab
                    tabs.forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');
                    
                    // Show corresponding content
                    const tabName = tab.dataset.tab;
                    document.querySelectorAll('.tab-content').forEach(content => {
                        content.style.display = 'none';
                    });
                    document.getElementById(`${tabName}Tab`).style.display = 'block';
                    
                    // Show/hide chat input
                    chatInputContainer.style.display = tabName === 'chat' ? 'block' : 'none';
                });
            });
        }
        
        // AI Assistant
        async function askAI() {
            const query = document.getElementById('aiQuery').value.trim();
            if (!query) return;
            
            try {
                const response = await fetch('/api/webinar/ai-assist', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: sessionInfo.id,
                        query: query,
                        context: {
                            participant_count: Object.keys(peerConnections).length,
                            duration: getSessionDuration()
                        }
                    })
                });
                
                if (response.ok) {
                    const result = await response.json();
                    addAIResponse(result);
                    document.getElementById('aiQuery').value = '';
                }
            } catch (error) {
                console.error('Error querying AI:', error);
                showNotification('Failed to get AI response', 'error');
            }
        }
        
        // Add AI response to UI
        function addAIResponse(response) {
            const aiResponses = document.getElementById('aiResponses');
            
            const responseEl = document.createElement('div');
            responseEl.className = 'ai-suggestion';
            responseEl.innerHTML = `
                <h4>AI Response</h4>
                <p>${response.content}</p>
                <div class="ai-actions">
                    ${response.actions ? response.actions.map(action => 
                        `<button class="ai-action-btn" onclick="${action.callback}">${action.label}</button>`
                    ).join('') : ''}
                </div>
            `;
            
            aiResponses.insertBefore(responseEl, aiResponses.firstChild);
        }
        
        // Participant management
        function addParticipant(participant) {
            const participantsList = document.getElementById('participantsList');
            
            const participantEl = document.createElement('div');
            participantEl.className = 'participant-item';
            participantEl.id = `participant-${participant.user_id}`;
            participantEl.innerHTML = `
                <div class="participant-avatar-small">${participant.display_name[0].toUpperCase()}</div>
                <div class="participant-info">
                    <div class="name">${participant.display_name}</div>
                    <div class="role">${participant.role}</div>
                </div>
                <div class="participant-status">
                    <div class="status-icon ${participant.audio ? 'active' : ''}" title="Audio">🎤</div>
                    <div class="status-icon ${participant.video ? 'active' : ''}" title="Video">📹</div>
                </div>
            `;
            
            participantsList.appendChild(participantEl);
            updateParticipantCount();
        }
        
        function removeParticipant(userId) {
            const participantEl = document.getElementById(`participant-${userId}`);
            if (participantEl) {
                participantEl.remove();
            }
            
            const videoEl = document.getElementById(`video-${userId}`);
            if (videoEl) {
                videoEl.remove();
            }
            
            updateVideoGrid();
            updateParticipantCount();
        }
        
        function updateParticipantCount() {
            const count = document.querySelectorAll('.participant-item').length;
            document.getElementById('participantCount').textContent = count;
        }
        
        // Session timer
        function startSessionTimer() {
            startTime = Date.now();
            
            sessionTimer = setInterval(() => {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;
                document.getElementById('sessionTime').textContent = 
                    `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }, 1000);
        }
        
        function getSessionDuration() {
            if (!startTime) return 0;
            return Math.floor((Date.now() - startTime) / 1000);
        }
        
        // Leave webinar
        async function leaveWebinar() {
            // Stop all streams
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
            }
            
            // Close peer connections
            Object.values(peerConnections).forEach(pc => pc.close());
            
            // Close WebSocket
            if (ws) {
                ws.close();
            }
            
            // Clear timer
            if (sessionTimer) {
                clearInterval(sessionTimer);
            }
            
            // Redirect or show join modal
            window.location.reload();
        }
        
        // Utility functions
        function generateUserId() {
            return 'user_' + Math.random().toString(36).substr(2, 9);
        }
        
        function updateConnectionStatus(status) {
            document.getElementById('connectionStatus').textContent = status;
        }
        
        function showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.remove();
            }, 5000);
        }
        
        // Start/stop recording (placeholder)
        function startRecording() {
            ws.send(JSON.stringify({
                type: 'system_command',
                command: 'start_recording',
                session_id: sessionInfo.id
            }));
            
            document.getElementById('recordBtn').classList.add('active');
            showNotification('Recording started', 'success');
        }
        
        function stopRecording() {
            ws.send(JSON.stringify({
                type: 'system_command',
                command: 'stop_recording',
                session_id: sessionInfo.id
            }));
            
            document.getElementById('recordBtn').classList.remove('active');
            showNotification('Recording stopped', 'info');
        }
        
        // WebRTC handlers (simplified placeholders)
        async function handleWebRTCOffer(data) {
            // WebRTC implementation would go here
            console.log('Received WebRTC offer from', data.from_user);
        }
        
        async function handleWebRTCAnswer(data) {
            // WebRTC implementation would go here
            console.log('Received WebRTC answer from', data.from_user);
        }
        
        async function handleICECandidate(data) {
            // WebRTC implementation would go here
            console.log('Received ICE candidate from', data.from_user);
        }
        
        // Initialize on load
        window.addEventListener('load', () => {
            // Check for WebRTC support
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                showNotification('Your browser does not support WebRTC', 'error');
            }
            
            // Auto-focus name input
            document.getElementById('userName').focus();
        });
        
        // Handle page unload
        window.addEventListener('beforeunload', () => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'participant_leaving',
                    session_id: sessionInfo.id,
                    user_id: userId
                }));
            }
        });
    </script>
</body>
</html>
    """)

# API Endpoints

# Session Management
@app.post("/api/webinar/create")
async def create_webinar_session(session_data: WebinarSession):
    """Create a new webinar session"""
    session_id = str(uuid.uuid4())
    
    session = {
        "id": session_id,
        "title": session_data.title,
        "description": session_data.description,
        "host_id": session_data.host_id,
        "scheduled_start": session_data.scheduled_start,
        "max_participants": session_data.max_participants,
        "features": session_data.features,
        "access_control": session_data.access_control,
        "status": "created",
        "created_at": datetime.now().isoformat(),
        "participants": []
    }
    
    webinar_sessions[session_id] = session
    
    # Store in Redis for persistence
    await app.state.redis.setex(
        f"webinar:session:{session_id}",
        3600 * 24,  # 24 hour TTL
        json.dumps(session)
    )
    
    # Publish event
    await app.state.message_bus.publish(
        "webinar.session.created",
        {"session_id": session_id, "title": session_data.title}
    )
    
    return {"session_id": session_id, "status": "created"}

@app.post("/api/webinar/join")
async def join_webinar(join_data: ParticipantJoin):
    """Join a webinar session"""
    session_id = join_data.session_id
    
    # Get or create session
    if session_id not in webinar_sessions:
        # Try to load from Redis
        session_data = await app.state.redis.get(f"webinar:session:{session_id}")
        if session_data:
            webinar_sessions[session_id] = json.loads(session_data)
        else:
            # Create demo session
            webinar_sessions[session_id] = {
                "id": session_id,
                "title": "Demo Webinar Session",
                "host_id": join_data.user_id if join_data.role == "host" else "demo_host",
                "status": "active",
                "participants": []
            }
    
    session = webinar_sessions[session_id]
    
    # Add participant
    participant = {
        "user_id": join_data.user_id,
        "display_name": join_data.display_name,
        "role": join_data.role,
        "capabilities": join_data.capabilities,
        "joined_at": datetime.now().isoformat()
    }
    
    session["participants"].append(participant)
    participant_info[join_data.user_id] = participant
    
    # Update metrics
    webinar_connections.labels(room_id=session_id).inc()
    
    # Broadcast join event
    await broadcast_to_session(session_id, {
        "type": "participant_joined",
        "participant": participant
    })
    
    return {"status": "joined", "session": session}

@app.get("/api/webinar/sessions")
async def list_sessions(active_only: bool = True):
    """List webinar sessions"""
    sessions = list(webinar_sessions.values())
    
    if active_only:
        sessions = [s for s in sessions if s.get("status") == "active"]
    
    return sessions

# WebSocket endpoint for real-time communication
@app.websocket("/ws/webinar")
async def webinar_websocket(websocket: WebSocket):
    """WebSocket endpoint for webinar real-time features"""
    await websocket.accept()
    
    user_id = None
    session_id = None
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Track message metrics
            webinar_messages.labels(type=data.get("type", "unknown")).inc()
            
            # Process different message types
            if data["type"] == "authenticate":
                user_id = data["user_id"]
                session_id = data["session_id"]
                
                # Add to active connections
                if session_id not in active_connections:
                    active_connections[session_id] = []
                active_connections[session_id].append(websocket)
                
            elif data["type"] == "chat_message":
                # Process chat message
                message = {
                    "type": "chat_message",
                    "message": {
                        "author": participant_info.get(user_id, {}).get("display_name", "Unknown"),
                        "content": data["message"],
                        "message_type": "text",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                await broadcast_to_session(session_id, message)
                
            elif data["type"] == "system_command":
                # Handle system commands
                await handle_system_command(session_id, data["command"], data.get("parameters", {}))
                
            elif data["type"] == "ai_query":
                # Process AI query
                response = await process_ai_query(data["query"], data.get("context", {}))
                await websocket.send_json({
                    "type": "ai_response",
                    "response": response
                })
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Clean up on disconnect
        if session_id and session_id in active_connections:
            active_connections[session_id].remove(websocket)
            webinar_connections.labels(room_id=session_id).dec()
            
            # Broadcast leave event
            if user_id:
                await broadcast_to_session(session_id, {
                    "type": "participant_left",
                    "user_id": user_id,
                    "display_name": participant_info.get(user_id, {}).get("display_name", "Unknown")
                })

# AI Assistant endpoint
@app.post("/api/webinar/ai-assist")
async def ai_assist(query: AIAssistantQuery):
    """Process AI assistant query during webinar"""
    response = await process_ai_query(query.query, query.context)
    
    # Format response based on requested format
    if query.response_format == "audio":
        # Generate audio response (placeholder)
        return {"type": "audio", "content": "Audio generation not implemented"}
    elif query.response_format == "visual":
        # Generate visual response (placeholder)
        return {"type": "visual", "content": "Visual generation not implemented"}
    else:
        return {
            "type": "text",
            "content": response["content"],
            "actions": response.get("actions", [])
        }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for service discovery"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "services": {
            "redis": await check_redis_health(),
            "message_bus": app.state.message_bus.is_running if hasattr(app.state, 'message_bus') else False
        }
    }
    
    return health_status

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

# Helper functions
async def broadcast_to_session(session_id: str, message: dict):
    """Broadcast message to all participants in a session"""
    if session_id in active_connections:
        disconnected = []
        for websocket in active_connections[session_id]:
            try:
                await websocket.send_json(message)
            except:
                disconnected.append(websocket)
        
        # Remove disconnected websockets
        for ws in disconnected:
            active_connections[session_id].remove(ws)

async def handle_system_command(session_id: str, command: str, parameters: dict):
    """Handle system commands for webinar control"""
    if command == "start_recording":
        # Start recording logic
        await app.state.message_bus.publish(
            "webinar.recording.start",
            {"session_id": session_id}
        )
    elif command == "stop_recording":
        # Stop recording logic
        await app.state.message_bus.publish(
            "webinar.recording.stop",
            {"session_id": session_id}
        )
    elif command == "mute_all":
        # Mute all participants
        await broadcast_to_session(session_id, {
            "type": "system_notification",
            "message": "All participants have been muted",
            "level": "info"
        })

async def process_ai_query(query: str, context: dict) -> dict:
    """Process AI assistant query"""
    # Placeholder for AI processing
    # In production, this would integrate with NEXUS AI services
    
    response = {
        "content": f"I understand you're asking about: {query}. Based on the context, here's my response...",
        "actions": [
            {"label": "Generate Summary", "callback": "generateSummary()"},
            {"label": "Create Action Items", "callback": "createActionItems()"}
        ]
    }
    
    return response

async def check_redis_health() -> bool:
    """Check Redis connection health"""
    try:
        await app.state.redis.ping()
        return True
    except:
        return False

async def monitor_system_health(app):
    """Monitor system health and update metrics"""
    while True:
        try:
            # Update system metrics
            health_data = {
                "active_sessions": len(webinar_sessions),
                "total_participants": sum(len(s.get("participants", [])) for s in webinar_sessions.values()),
                "active_connections": sum(len(conns) for conns in active_connections.values())
            }
            
            # Publish health metrics
            await app.state.message_bus.publish(
                "webinar.health.update",
                health_data,
                priority=MessagePriority.LOW
            )
            
            await asyncio.sleep(30)  # Update every 30 seconds
        except Exception as e:
            logger.error(f"Health monitoring error: {e}")
            await asyncio.sleep(60)

async def cleanup_inactive_sessions(app):
    """Clean up inactive webinar sessions"""
    while True:
        try:
            current_time = datetime.now()
            
            for session_id, session in list(webinar_sessions.items()):
                # Check if session is inactive (no participants for 1 hour)
                if len(session.get("participants", [])) == 0:
                    created_at = datetime.fromisoformat(session.get("created_at", current_time.isoformat()))
                    if (current_time - created_at).total_seconds() > 3600:
                        # Remove inactive session
                        del webinar_sessions[session_id]
                        await app.state.redis.delete(f"webinar:session:{session_id}")
                        logger.info(f"Cleaned up inactive session: {session_id}")
            
            await asyncio.sleep(300)  # Run every 5 minutes
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")
            await asyncio.sleep(600)

if __name__ == "__main__":
    config = ProductionConfig()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.WEBINAR_PORT,
        log_level="info",
        access_log=True
    )