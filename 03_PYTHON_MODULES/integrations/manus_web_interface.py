#!/usr/bin/env python3
"""
MANUS Web Interface - Task Management and Monitoring
Integrates with NEXUS core for unified experience
"""

from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
import json
import uvicorn
from datetime import datetime

from manus_continuous_agent import (
    MANUSContinuousAgent, Task, TaskStatus, TaskPriority
)
from nexus_enhanced_manus import EnhancedMANUSOmnipotent

# Pydantic models for API
class TaskCreate(BaseModel):
    name: str
    description: str = ""
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: str = "MEDIUM"
    dependencies: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    progress: Optional[float] = None

# Create FastAPI app
app = FastAPI(title="MANUS Continuous Work Agent")

# Global MANUS agent instance
manus_agent: Optional[MANUSContinuousAgent] = None
enhanced_manus: Optional[EnhancedMANUSOmnipotent] = None

# WebSocket connections for real-time updates
websocket_connections: List[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    """Start MANUS agent on app startup"""
    global manus_agent, enhanced_manus
    manus_agent = MANUSContinuousAgent()
    enhanced_manus = EnhancedMANUSOmnipotent()
    asyncio.create_task(manus_agent.start())
    asyncio.create_task(broadcast_status_updates())

@app.on_event("shutdown")
async def shutdown_event():
    """Stop MANUS agent on app shutdown"""
    if manus_agent:
        await manus_agent.stop()

# API Routes

@app.get("/")
async def root():
    """Serve the web interface"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>MANUS Continuous Work Agent</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #0a0a0a;
            color: #e0e0e0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: #00ff00;
            text-align: center;
            margin-bottom: 30px;
        }
        .stats {
            background: #1a1a1a;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        .stat-item {
            background: #2a2a2a;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #00ff00;
        }
        .stat-label {
            font-size: 0.9em;
            color: #888;
            margin-top: 5px;
        }
        .task-form {
            background: #1a1a1a;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .form-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        input, select, textarea {
            background: #2a2a2a;
            border: 1px solid #444;
            color: #e0e0e0;
            padding: 10px;
            border-radius: 5px;
            width: 100%;
        }
        button {
            background: #00ff00;
            color: #000;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            margin-top: 10px;
        }
        button:hover {
            background: #00cc00;
        }
        .tasks-container {
            background: #1a1a1a;
            padding: 20px;
            border-radius: 10px;
        }
        .task-item {
            background: #2a2a2a;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            display: grid;
            grid-template-columns: 1fr auto;
            align-items: center;
            gap: 10px;
        }
        .task-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }
        .task-name {
            font-weight: bold;
        }
        .task-status {
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.8em;
        }
        .status-pending { background: #666; }
        .status-in_progress { background: #0066cc; }
        .status-completed { background: #00cc00; }
        .status-failed { background: #cc0000; }
        .status-paused { background: #cc6600; }
        .progress-bar {
            height: 10px;
            background: #444;
            border-radius: 5px;
            overflow: hidden;
            margin-top: 5px;
        }
        .progress-fill {
            height: 100%;
            background: #00ff00;
            transition: width 0.3s ease;
        }
        .task-actions {
            display: flex;
            gap: 5px;
        }
        .task-actions button {
            padding: 5px 10px;
            font-size: 0.8em;
        }
        .logs-section {
            background: #1a1a1a;
            padding: 20px;
            border-radius: 10px;
            margin-top: 30px;
            max-height: 300px;
            overflow-y: auto;
        }
        .log-entry {
            font-family: monospace;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        .log-info { color: #00ff00; }
        .log-warning { color: #ffcc00; }
        .log-error { color: #ff3333; }
        
        /* Checkbox styling for web scraping options */
        input[type="checkbox"] {
            margin-right: 5px;
        }
        label input[type="checkbox"] {
            margin-right: 8px;
        }
        #parameterFields label {
            display: inline-block;
            margin-right: 15px;
            margin-bottom: 5px;
            color: #b0b0b0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 MANUS Continuous Work Agent</h1>
        
        <div class="stats" id="stats">
            <!-- Stats will be populated here -->
        </div>
        
        <div class="stats" id="memoryStats" style="margin-top: 20px; display: none;">
            <h3 style="color: #00ff00; margin-bottom: 15px;">🧬 NEXUS Memory DNA Status</h3>
            <div id="memoryStatsContent">
                <!-- Memory stats will be populated here -->
            </div>
        </div>
        
        <div class="task-form">
            <h2>Create New Task</h2>
            <form id="taskForm">
                <div class="form-grid">
                    <div>
                        <label>Task Name</label>
                        <input type="text" id="taskName" required>
                    </div>
                    <div>
                        <label>Priority</label>
                        <select id="taskPriority">
                            <option value="CRITICAL">Critical</option>
                            <option value="HIGH">High</option>
                            <option value="MEDIUM" selected>Medium</option>
                            <option value="LOW">Low</option>
                        </select>
                    </div>
                    <div>
                        <label>Action Type</label>
                        <select id="taskAction" onchange="updateParameterFields()">
                            <option value="shell_command">Shell Command</option>
                            <option value="python_script">Python Script</option>
                            <option value="http_request">HTTP Request</option>
                            <option value="file_operation">File Operation</option>
                            <option value="nexus_integration">NEXUS Integration</option>
                            <option value="web_scrape">Web Scraping</option>
                            <option value="batch_scrape">Batch Web Scraping</option>
                            <option value="scrape_with_analysis">Scrape & Analyze</option>
                        </select>
                    </div>
                    <div>
                        <label>Dependencies (comma-separated task IDs)</label>
                        <input type="text" id="taskDependencies">
                    </div>
                </div>
                <div style="margin-top: 15px;">
                    <label>Description</label>
                    <textarea id="taskDescription" rows="2"></textarea>
                </div>
                <div id="parameterFields" style="margin-top: 15px;">
                    <!-- Dynamic parameter fields -->
                </div>
                <button type="submit">Create Task</button>
            </form>
        </div>
        
        <div class="tasks-container">
            <h2>Active Tasks</h2>
            <div id="tasksList">
                <!-- Tasks will be populated here -->
            </div>
        </div>
        
        <div class="logs-section">
            <h2>System Logs</h2>
            <div id="logsContainer">
                <!-- Logs will be populated here -->
            </div>
        </div>
    </div>

    <script>
        let ws;
        
        // Connect to WebSocket for real-time updates
        function connectWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'stats') {
                    updateStats(data.data);
                } else if (data.type === 'tasks') {
                    updateTasksList(data.data);
                } else if (data.type === 'log') {
                    addLogEntry(data.data);
                }
            };
            
            ws.onclose = () => {
                setTimeout(connectWebSocket, 3000);
            };
        }
        
        // Update statistics display
        function updateStats(stats) {
            const statsHtml = `
                <div class="stat-item">
                    <div class="stat-value">${stats.total_tasks}</div>
                    <div class="stat-label">Total Tasks</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.pending}</div>
                    <div class="stat-label">Pending</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.in_progress}</div>
                    <div class="stat-label">In Progress</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.completed}</div>
                    <div class="stat-label">Completed</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.failed}</div>
                    <div class="stat-label">Failed</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.active_workers}</div>
                    <div class="stat-label">Active Workers</div>
                </div>
            `;
            document.getElementById('stats').innerHTML = statsHtml;
        }
        
        // Update tasks list
        function updateTasksList(tasks) {
            const tasksHtml = tasks.map(task => `
                <div class="task-item">
                    <div>
                        <div class="task-header">
                            <span class="task-name">${task.name}</span>
                            <span class="task-status status-${task.status}">${task.status}</span>
                        </div>
                        <div style="font-size: 0.9em; color: #888;">${task.description}</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${task.progress}%"></div>
                        </div>
                    </div>
                    <div class="task-actions">
                        ${getTaskActions(task)}
                    </div>
                </div>
            `).join('');
            document.getElementById('tasksList').innerHTML = tasksHtml;
        }
        
        // Get appropriate actions for task status
        function getTaskActions(task) {
            switch(task.status) {
                case 'pending':
                    return `<button onclick="cancelTask('${task.id}')">Cancel</button>`;
                case 'in_progress':
                    return `<button onclick="pauseTask('${task.id}')">Pause</button>`;
                case 'paused':
                    return `<button onclick="resumeTask('${task.id}')">Resume</button>`;
                default:
                    return '';
            }
        }
        
        // Add log entry
        function addLogEntry(log) {
            const logsContainer = document.getElementById('logsContainer');
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry log-${log.level.toLowerCase()}`;
            logEntry.textContent = `[${log.timestamp}] ${log.level}: ${log.message}`;
            logsContainer.appendChild(logEntry);
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }
        
        // Update parameter fields based on action type
        function updateParameterFields() {
            const action = document.getElementById('taskAction').value;
            const container = document.getElementById('parameterFields');
            
            let html = '<label>Parameters</label>';
            
            switch(action) {
                case 'shell_command':
                    html += `
                        <input type="text" id="param_command" placeholder="Command to execute" required>
                        <input type="number" id="param_timeout" placeholder="Timeout (seconds)" value="300">
                    `;
                    break;
                case 'python_script':
                    html += `
                        <textarea id="param_script" placeholder="Python script code" rows="5" required></textarea>
                    `;
                    break;
                case 'http_request':
                    html += `
                        <input type="text" id="param_url" placeholder="URL" required>
                        <select id="param_method">
                            <option value="GET">GET</option>
                            <option value="POST">POST</option>
                            <option value="PUT">PUT</option>
                            <option value="DELETE">DELETE</option>
                        </select>
                    `;
                    break;
                case 'file_operation':
                    html += `
                        <select id="param_operation">
                            <option value="read">Read</option>
                            <option value="write">Write</option>
                            <option value="delete">Delete</option>
                        </select>
                        <input type="text" id="param_path" placeholder="File path" required>
                        <textarea id="param_content" placeholder="Content (for write operation)" rows="3"></textarea>
                    `;
                    break;
                case 'nexus_integration':
                    html += `
                        <select id="param_type">
                            <option value="consciousness_sync">Consciousness Sync</option>
                            <option value="memory_store">Memory Store</option>
                        </select>
                    `;
                    break;
                case 'web_scrape':
                    html += `
                        <input type="text" id="param_url" placeholder="URL to scrape" required>
                        <div style="margin-top: 10px;">
                            <label><input type="checkbox" id="param_use_proxy"> Use Proxy</label>
                            <label><input type="checkbox" id="param_wait_for_js" checked> Wait for JavaScript</label>
                            <label><input type="checkbox" id="param_extract_links" checked> Extract Links</label>
                            <label><input type="checkbox" id="param_extract_images" checked> Extract Images</label>
                        </div>
                    `;
                    break;
                case 'batch_scrape':
                    html += `
                        <textarea id="param_urls" placeholder="URLs to scrape (one per line)" rows="5" required></textarea>
                        <div style="margin-top: 10px;">
                            <label><input type="checkbox" id="param_use_proxy"> Use Proxy</label>
                            <input type="number" id="param_concurrent" placeholder="Concurrent requests" value="5" min="1" max="20">
                        </div>
                    `;
                    break;
                case 'scrape_with_analysis':
                    html += `
                        <input type="text" id="param_url" placeholder="URL to scrape and analyze" required>
                        <textarea id="param_analysis_prompt" placeholder="Analysis instructions (e.g., 'Extract all product prices and reviews')" rows="3" required></textarea>
                        <div style="margin-top: 10px;">
                            <label><input type="checkbox" id="param_use_proxy"> Use Proxy</label>
                            <label><input type="checkbox" id="param_wait_for_js" checked> Wait for JavaScript</label>
                        </div>
                    `;
                    break;
            }
            
            container.innerHTML = html;
        }
        
        // Handle form submission
        document.getElementById('taskForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const action = document.getElementById('taskAction').value;
            const parameters = {};
            
            // Collect parameters based on action type
            document.querySelectorAll('[id^="param_"]').forEach(input => {
                const paramName = input.id.replace('param_', '');
                if (input.type === 'checkbox') {
                    parameters[paramName] = input.checked;
                } else if (input.value) {
                    // Special handling for URLs in batch_scrape
                    if (paramName === 'urls' && action === 'batch_scrape') {
                        parameters[paramName] = input.value.split('\n').map(url => url.trim()).filter(url => url);
                    } else {
                        parameters[paramName] = input.value;
                    }
                }
            });
            
            const taskData = {
                name: document.getElementById('taskName').value,
                description: document.getElementById('taskDescription').value,
                action: action,
                parameters: parameters,
                priority: document.getElementById('taskPriority').value,
                dependencies: document.getElementById('taskDependencies').value
                    .split(',')
                    .map(d => d.trim())
                    .filter(d => d)
            };
            
            try {
                const response = await fetch('/api/tasks', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(taskData)
                });
                
                if (response.ok) {
                    const result = await response.json();
                    addLogEntry({
                        timestamp: new Date().toISOString(),
                        level: 'INFO',
                        message: `Task created: ${taskData.name} (ID: ${result.task_id})`
                    });
                    document.getElementById('taskForm').reset();
                    updateParameterFields();
                }
            } catch (error) {
                console.error('Error creating task:', error);
            }
        });
        
        // Task control functions
        async function cancelTask(taskId) {
            await fetch(`/api/tasks/${taskId}/cancel`, { method: 'POST' });
        }
        
        async function pauseTask(taskId) {
            await fetch(`/api/tasks/${taskId}/pause`, { method: 'POST' });
        }
        
        async function resumeTask(taskId) {
            await fetch(`/api/tasks/${taskId}/resume`, { method: 'POST' });
        }
        
        // Initial load
        async function loadInitialData() {
            const statsResponse = await fetch('/api/stats');
            const stats = await statsResponse.json();
            updateStats(stats);
            
            const tasksResponse = await fetch('/api/tasks');
            const tasks = await tasksResponse.json();
            updateTasksList(tasks);
            
            // Load memory DNA stats if available
            loadMemoryStats();
        }
        
        // Load NEXUS Memory DNA statistics
        async function loadMemoryStats() {
            try {
                // First try unified memory stats
                let response = await fetch('/api/memory/unified-stats');
                let memoryStats = await response.json();
                
                if (!memoryStats.error) {
                    // We have unified memory stats
                    document.getElementById('memoryStats').style.display = 'block';
                    document.querySelector('#memoryStats h3').textContent = '🧬 Unified Memory System Status';
                    updateUnifiedMemoryStats(memoryStats);
                    return;
                }
                
                // Fall back to NEXUS memory DNA
                response = await fetch('/api/nexus/memory-dna');
                memoryStats = await response.json();
                
                if (memoryStats.status && memoryStats.status.includes('No NEXUS')) {
                    // No NEXUS integration
                    document.getElementById('memoryStats').style.display = 'none';
                } else {
                    // Display memory stats
                    document.getElementById('memoryStats').style.display = 'block';
                    updateMemoryStats(memoryStats);
                }
            } catch (error) {
                console.log('Memory stats not available');
                document.getElementById('memoryStats').style.display = 'none';
            }
        }
        
        // Update memory statistics display
        function updateMemoryStats(stats) {
            const memoryHtml = `
                <div class="stat-item">
                    <div class="stat-value">${stats.working_memory?.count || 0}</div>
                    <div class="stat-label">Working Memory</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.episodic_memory?.episodes || 0}</div>
                    <div class="stat-label">Episodic Memories</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.semantic_memory?.concepts || 0}</div>
                    <div class="stat-label">Semantic Concepts</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.persistent_memory?.mem0_blocks || 0}</div>
                    <div class="stat-label">MEM0 Blocks</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.persistent_memory?.immortal_memories || 0}</div>
                    <div class="stat-label">Immortal Memories</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.persistent_memory?.blockchain_height || 0}</div>
                    <div class="stat-label">Blockchain Height</div>
                </div>
            `;
            document.getElementById('memoryStatsContent').innerHTML = memoryHtml;
        }
        
        // Update unified memory statistics display
        function updateUnifiedMemoryStats(stats) {
            let memoryHtml = '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">';
            
            // Overall stats
            if (stats.total_operations !== undefined) {
                memoryHtml += `
                    <div class="stat-item">
                        <div class="stat-value">${stats.total_operations}</div>
                        <div class="stat-label">Total Operations</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.average_importance?.toFixed(2) || 0}</div>
                        <div class="stat-label">Avg Importance</div>
                    </div>
                `;
            }
            
            memoryHtml += '</div><div style="margin-top: 15px;">';
            
            // Stage-specific stats
            if (stats.stage_distribution) {
                memoryHtml += '<h4 style="color: #00cc00; margin-bottom: 10px;">Memory Distribution</h4>';
                memoryHtml += '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">';
                
                for (const [stage, count] of Object.entries(stats.stage_distribution)) {
                    memoryHtml += `
                        <div class="stat-item">
                            <div class="stat-value">${count}</div>
                            <div class="stat-label">${stage.charAt(0).toUpperCase() + stage.slice(1)}</div>
                        </div>
                    `;
                }
                memoryHtml += '</div>';
            }
            
            // Individual stage stats
            if (stats.working_memory || stats.episodic_memory || stats.semantic_memory || stats.persistent_memory) {
                memoryHtml += '<h4 style="color: #00cc00; margin: 15px 0 10px 0;">Stage Details</h4>';
                memoryHtml += '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">';
                
                // Working Memory
                if (stats.working_memory) {
                    memoryHtml += `
                        <div class="stat-item">
                            <div class="stat-value">${(stats.working_memory.utilization * 100).toFixed(1)}%</div>
                            <div class="stat-label">Working Memory Used</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${(stats.working_memory.hit_rate * 100).toFixed(1)}%</div>
                            <div class="stat-label">Cache Hit Rate</div>
                        </div>
                    `;
                }
                
                // Episodic Memory
                if (stats.episodic_memory) {
                    memoryHtml += `
                        <div class="stat-item">
                            <div class="stat-value">${stats.episodic_memory.total_episodes || 0}</div>
                            <div class="stat-label">Total Episodes</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${stats.episodic_memory.consolidations || 0}</div>
                            <div class="stat-label">Consolidations</div>
                        </div>
                    `;
                }
                
                // Semantic Memory
                if (stats.semantic_memory) {
                    memoryHtml += `
                        <div class="stat-item">
                            <div class="stat-value">${stats.semantic_memory.total_concepts || 0}</div>
                            <div class="stat-label">Concepts</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${stats.semantic_memory.chromadb_available ? '✓' : '✗'}</div>
                            <div class="stat-label">ChromaDB</div>
                        </div>
                    `;
                }
                
                // Persistent Memory (MEM0)
                if (stats.persistent_memory) {
                    memoryHtml += `
                        <div class="stat-item">
                            <div class="stat-value">${stats.persistent_memory.index_size || 0}</div>
                            <div class="stat-label">MEM0 Entries</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${stats.persistent_memory.storage_size_mb?.toFixed(1) || 0} MB</div>
                            <div class="stat-label">Storage Used</div>
                        </div>
                    `;
                }
                
                memoryHtml += '</div>';
            }
            
            document.getElementById('memoryStatsContent').innerHTML = memoryHtml;
        }
        
        // Refresh memory stats periodically
        setInterval(loadMemoryStats, 5000);
        
        // Initialize
        connectWebSocket();
        updateParameterFields();
        loadInitialData();
    </script>
</body>
</html>
    """)

@app.post("/api/tasks")
async def create_task(task_data: TaskCreate):
    """Create a new task"""
    if not manus_agent:
        raise HTTPException(status_code=503, detail="MANUS agent not initialized")
    
    task = Task(
        name=task_data.name,
        description=task_data.description,
        action=task_data.action,
        parameters=task_data.parameters,
        priority=TaskPriority[task_data.priority],
        dependencies=task_data.dependencies,
        context=task_data.context
    )
    
    task_id = await manus_agent.add_task(task)
    return {"task_id": task_id, "status": "created"}

@app.get("/api/tasks")
async def get_tasks():
    """Get all tasks"""
    if not manus_agent:
        raise HTTPException(status_code=503, detail="MANUS agent not initialized")
    
    all_tasks = manus_agent.persistence.load_all_tasks()
    return [
        {
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "status": task.status.value,
            "priority": task.priority.name,
            "progress": task.progress,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error": task.error
        }
        for task in all_tasks[:50]  # Limit to 50 most recent
    ]

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """Get a specific task"""
    if not manus_agent:
        raise HTTPException(status_code=503, detail="MANUS agent not initialized")
    
    task = await manus_agent.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "action": task.action,
        "parameters": task.parameters,
        "status": task.status.value,
        "priority": task.priority.name,
        "progress": task.progress,
        "created_at": task.created_at.isoformat(),
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "result": task.result,
        "error": task.error,
        "dependencies": task.dependencies,
        "context": task.context,
        "retry_count": task.retry_count
    }

@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a task"""
    if not manus_agent:
        raise HTTPException(status_code=503, detail="MANUS agent not initialized")
    
    success = await manus_agent.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel task")
    
    return {"status": "cancelled"}

@app.post("/api/tasks/{task_id}/pause")
async def pause_task(task_id: str):
    """Pause a task"""
    if not manus_agent:
        raise HTTPException(status_code=503, detail="MANUS agent not initialized")
    
    success = await manus_agent.pause_task(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot pause task")
    
    return {"status": "paused"}

@app.post("/api/tasks/{task_id}/resume")
async def resume_task(task_id: str):
    """Resume a task"""
    if not manus_agent:
        raise HTTPException(status_code=503, detail="MANUS agent not initialized")
    
    success = await manus_agent.resume_task(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot resume task")
    
    return {"status": "resumed"}

@app.get("/api/stats")
async def get_stats():
    """Get MANUS statistics"""
    if not manus_agent:
        raise HTTPException(status_code=503, detail="MANUS agent not initialized")
    
    return manus_agent.get_statistics()

@app.get("/api/nexus/memory-dna")
async def get_memory_dna_status():
    """Get NEXUS memory DNA status"""
    global manus_agent
    
    # Check if MANUS agent has NEXUS integration
    if not manus_agent:
        raise HTTPException(status_code=503, detail="MANUS agent not initialized")
    
    # Check if it's a NEXUSPoweredMANUS instance
    if hasattr(manus_agent, 'nexus_core'):
        # This is NEXUSPoweredMANUS with integrated memory
        nexus = manus_agent.nexus_core
        return {
            "working_memory": {
                "count": len(nexus.memory_dna['working']['storage']),
                "capacity": nexus.memory_dna['working']['capacity']
            },
            "episodic_memory": {
                "episodes": len(nexus.memory_dna['episodic']['experiences'])
            },
            "semantic_memory": {
                "concepts": len(nexus.memory_dna['semantic']['concept_graph']),
                "vector_store_status": "active" if nexus.memory_dna['semantic']['vector_store'] else "inactive"
            },
            "persistent_memory": {
                "mem0_blocks": len(nexus.memory_dna['persistent']['mem0_core']['index']),
                "immortal_memories": len(nexus.memory_dna['persistent']['immortal_memories']),
                "blockchain_height": len(nexus.memory_dna['persistent']['blockchain'])
            }
        }
    else:
        # Check if we're using NEXUSPoweredMANUS through integration
        try:
            from manus_nexus_integration import NEXUSPoweredMANUS
            # If manus_agent is wrapped in NEXUSPoweredMANUS
            if hasattr(manus_agent, 'get_memory_statistics'):
                return manus_agent.get_memory_statistics()
        except:
            pass
        
        # Fallback - no NEXUS memory DNA available
        return {
            "status": "No NEXUS memory DNA integration found",
            "hint": "Use NEXUSPoweredMANUS for integrated memory"
        }

@app.get("/api/memory/unified-stats")
async def get_unified_memory_stats():
    """Get unified memory system statistics"""
    if not manus_agent:
        raise HTTPException(status_code=503, detail="MANUS agent not initialized")
    
    # Check if using unified memory system
    from manus_nexus_integration import NEXUSPoweredMANUS
    
    if hasattr(manus_agent, 'unified_memory'):
        # Direct access to unified memory
        memory_stats = manus_agent.unified_memory.get_stats()
        return memory_stats
    elif hasattr(manus_agent, '__class__') and manus_agent.__class__.__name__ == 'NEXUSPoweredMANUS':
        # Access through NEXUSPoweredMANUS
        memory_stats = manus_agent.get_memory_statistics()
        return memory_stats
    else:
        return {
            "error": "Unified memory system not available",
            "description": "This MANUS instance is not enhanced with the unified memory system",
            "hint": "Use NEXUSPoweredMANUS with unified memory for full capabilities"
        }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except:
        websocket_connections.remove(websocket)

async def broadcast_status_updates():
    """Broadcast status updates to all connected clients"""
    while True:
        if manus_agent and websocket_connections:
            # Get current stats
            stats = manus_agent.get_statistics()
            
            # Get recent tasks
            tasks = manus_agent.persistence.load_all_tasks()
            recent_tasks = sorted(
                tasks, 
                key=lambda t: t.created_at, 
                reverse=True
            )[:20]
            
            # Broadcast to all connections
            for websocket in websocket_connections[:]:
                try:
                    await websocket.send_json({
                        "type": "stats",
                        "data": stats
                    })
                    
                    await websocket.send_json({
                        "type": "tasks",
                        "data": [
                            {
                                "id": task.id,
                                "name": task.name,
                                "description": task.description,
                                "status": task.status.value,
                                "priority": task.priority.name,
                                "progress": task.progress
                            }
                            for task in recent_tasks
                        ]
                    })
                except:
                    # Remove dead connections
                    websocket_connections.remove(websocket)
        
        await asyncio.sleep(2)  # Update every 2 seconds

# Enhanced MANUS API Endpoints

@app.post("/api/enhanced/generate-project")
async def generate_project(request: Dict[str, Any]):
    """Generate a complete project from description"""
    if not enhanced_manus:
        raise HTTPException(status_code=503, detail="Enhanced MANUS not initialized")
    
    result = await enhanced_manus.execute_specialty({
        'command': 'generate_project',
        'description': request.get('description'),
        'type': request.get('type', 'auto'),
        'output_dir': request.get('output_dir', './generated_project')
    })
    
    return result

@app.post("/api/enhanced/analyze-project")
async def analyze_project(request: Dict[str, Any]):
    """Analyze project for bugs, security, and performance issues"""
    if not enhanced_manus:
        raise HTTPException(status_code=503, detail="Enhanced MANUS not initialized")
    
    result = await enhanced_manus.execute_specialty({
        'command': 'analyze_project',
        'directory': request.get('directory', '.'),
        'include_security': request.get('include_security', True),
        'include_performance': request.get('include_performance', True)
    })
    
    return result

@app.post("/api/enhanced/full-analysis")
async def full_analysis(request: Dict[str, Any]):
    """Run comprehensive analysis on project"""
    if not enhanced_manus:
        raise HTTPException(status_code=503, detail="Enhanced MANUS not initialized")
    
    result = await enhanced_manus.execute_specialty({
        'command': 'full_analysis',
        'directory': request.get('directory', '.')
    })
    
    return result

@app.post("/api/enhanced/fix-all-issues")
async def fix_all_issues(request: Dict[str, Any]):
    """Automatically fix all detected issues"""
    if not enhanced_manus:
        raise HTTPException(status_code=503, detail="Enhanced MANUS not initialized")
    
    result = await enhanced_manus.execute_specialty({
        'command': 'fix_all_issues',
        'directory': request.get('directory', '.'),
        'auto_commit': request.get('auto_commit', False)
    })
    
    return result

@app.post("/api/enhanced/optimize-performance")
async def optimize_performance(request: Dict[str, Any]):
    """Optimize project performance"""
    if not enhanced_manus:
        raise HTTPException(status_code=503, detail="Enhanced MANUS not initialized")
    
    result = await enhanced_manus.execute_specialty({
        'command': 'optimize_performance',
        'directory': request.get('directory', '.'),
        'target_improvement': request.get('target_improvement', 0.5)
    })
    
    return result

# Individual tool endpoints

@app.post("/api/tools/generate-docs")
async def generate_documentation(request: Dict[str, Any]):
    """Generate documentation for project"""
    if not enhanced_manus:
        raise HTTPException(status_code=503, detail="Enhanced MANUS not initialized")
    
    result = await enhanced_manus.tools['doc_generator'].sync_documentation(
        request.get('directory', '.'),
        request.get('output_dir', './docs')
    )
    
    return result

@app.post("/api/tools/detect-bugs")
async def detect_bugs(request: Dict[str, Any]):
    """Detect bugs in project"""
    if not enhanced_manus:
        raise HTTPException(status_code=503, detail="Enhanced MANUS not initialized")
    
    bugs = await enhanced_manus.tools['bug_detector'].scan_project(
        request.get('directory', '.')
    )
    report = enhanced_manus.tools['bug_detector'].generate_report()
    
    return {
        'bugs': bugs,
        'report': enhanced_manus.tools['bug_detector'].export_report(report, 'json')
    }

@app.post("/api/tools/scan-security")
async def scan_security(request: Dict[str, Any]):
    """Scan for security vulnerabilities"""
    if not enhanced_manus:
        raise HTTPException(status_code=503, detail="Enhanced MANUS not initialized")
    
    report = enhanced_manus.tools['security_scanner'].scan_for_vulnerabilities(
        request.get('directory', '.')
    )
    risk_score = enhanced_manus.tools['security_scanner'].calculate_risk_score(report)
    
    return {
        'report': report.dict(),
        'risk_score': risk_score,
        'summary': enhanced_manus.tools['security_scanner'].generate_security_report(report, 'json')
    }

@app.post("/api/tools/analyze-performance")
async def analyze_performance(request: Dict[str, Any]):
    """Analyze code performance"""
    if not enhanced_manus:
        raise HTTPException(status_code=503, detail="Enhanced MANUS not initialized")
    
    code = request.get('code', '')
    file_path = request.get('file_path')
    
    if file_path:
        with open(file_path, 'r') as f:
            code = f.read()
    
    complexity = enhanced_manus.tools['performance_analyzer'].analyze_complexity(code)
    metrics = await enhanced_manus.tools['performance_analyzer'].profile_execution(code, {})
    suggestions = enhanced_manus.tools['performance_analyzer'].suggest_optimizations(code, metrics)
    
    return {
        'complexity': complexity.dict() if complexity else None,
        'metrics': metrics.dict() if metrics else None,
        'suggestions': [s.dict() for s in suggestions]
    }

@app.get("/api/enhanced/help")
async def get_enhanced_help():
    """Get help information for Enhanced MANUS"""
    if not enhanced_manus:
        raise HTTPException(status_code=503, detail="Enhanced MANUS not initialized")
    
    return await enhanced_manus.execute_specialty({'command': 'help'})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)