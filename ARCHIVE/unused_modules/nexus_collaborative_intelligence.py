#!/usr/bin/env python3
"""
NEXUS Collaborative Intelligence System
A multi-agent collaboration framework enabling unified intelligence through
real-time communication, shared memory, and emergent problem-solving.
"""

import asyncio
import json
import uuid
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import websockets
import logging
from collections import defaultdict, Counter
import numpy as np
from threading import Lock
import hashlib
import pickle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages in the collaborative system"""
    REGISTER = "register"
    BROADCAST = "broadcast"
    DIRECT = "direct"
    MEMORY_WRITE = "memory_write"
    MEMORY_READ = "memory_read"
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    KNOWLEDGE_SHARE = "knowledge_share"
    CONSENSUS_REQUEST = "consensus_request"
    CONSENSUS_VOTE = "consensus_vote"
    CAPABILITY_UPDATE = "capability_update"
    TEACHING_REQUEST = "teaching_request"
    TEACHING_RESPONSE = "teaching_response"
    CONFLICT_RESOLUTION = "conflict_resolution"
    HEARTBEAT = "heartbeat"
    PERFORMANCE_UPDATE = "performance_update"


class ConsensusType(Enum):
    """Types of consensus mechanisms"""
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_VOTE = "weighted_vote"
    UNANIMOUS = "unanimous"
    QUORUM = "quorum"
    EXPERTISE_BASED = "expertise_based"


@dataclass
class AgentCapability:
    """Represents a capability of an agent"""
    name: str
    domain: str
    proficiency: float  # 0.0 to 1.0
    experience_count: int = 0
    success_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class AgentProfile:
    """Profile of a collaborative agent"""
    agent_id: str
    name: str
    type: str
    capabilities: Dict[str, AgentCapability] = field(default_factory=dict)
    performance_score: float = 0.5
    trust_score: float = 0.5
    active_tasks: Set[str] = field(default_factory=set)
    knowledge_domains: Set[str] = field(default_factory=set)
    teaching_history: List[Dict] = field(default_factory=list)
    learning_history: List[Dict] = field(default_factory=list)
    last_seen: datetime = field(default_factory=datetime.now)


@dataclass
class CollaborativeTask:
    """Represents a collaborative task"""
    task_id: str
    description: str
    required_capabilities: List[str]
    assigned_agents: List[str] = field(default_factory=list)
    status: str = "pending"
    priority: float = 0.5
    deadline: Optional[datetime] = None
    results: Dict[str, Any] = field(default_factory=dict)
    consensus_required: bool = False
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class MemoryEntry:
    """Entry in collective memory"""
    key: str
    value: Any
    agent_id: str
    timestamp: datetime
    confidence: float = 1.0
    access_count: int = 0
    tags: Set[str] = field(default_factory=set)
    expiry: Optional[datetime] = None


class CollectiveMemory:
    """Shared memory system for all agents"""
    
    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.memory: Dict[str, List[MemoryEntry]] = defaultdict(list)
        self.access_log: List[Dict] = []
        self.lock = Lock()
        self.indices: Dict[str, Set[str]] = defaultdict(set)  # tag -> keys
        
    def write(self, key: str, value: Any, agent_id: str, 
              confidence: float = 1.0, tags: Set[str] = None) -> bool:
        """Write to collective memory"""
        with self.lock:
            entry = MemoryEntry(
                key=key,
                value=value,
                agent_id=agent_id,
                timestamp=datetime.now(),
                confidence=confidence,
                tags=tags or set()
            )
            
            # Update indices
            for tag in entry.tags:
                self.indices[tag].add(key)
            
            # Add to memory
            self.memory[key].append(entry)
            
            # Enforce capacity limits
            if len(self.memory) > self.capacity:
                self._evict_oldest()
            
            # Log access
            self.access_log.append({
                'action': 'write',
                'key': key,
                'agent_id': agent_id,
                'timestamp': datetime.now()
            })
            
            return True
    
    def read(self, key: str, agent_id: str) -> Optional[Any]:
        """Read from collective memory"""
        with self.lock:
            if key not in self.memory:
                return None
            
            # Get most recent entry with highest confidence
            entries = sorted(self.memory[key], 
                           key=lambda x: (x.confidence, x.timestamp), 
                           reverse=True)
            
            if not entries:
                return None
            
            # Update access count
            entries[0].access_count += 1
            
            # Log access
            self.access_log.append({
                'action': 'read',
                'key': key,
                'agent_id': agent_id,
                'timestamp': datetime.now()
            })
            
            return entries[0].value
    
    def query_by_tags(self, tags: Set[str]) -> Dict[str, Any]:
        """Query memory by tags"""
        with self.lock:
            relevant_keys = set()
            for tag in tags:
                relevant_keys.update(self.indices.get(tag, set()))
            
            results = {}
            for key in relevant_keys:
                if key in self.memory and self.memory[key]:
                    latest = max(self.memory[key], key=lambda x: x.timestamp)
                    results[key] = latest.value
            
            return results
    
    def get_consensus_value(self, key: str, consensus_type: ConsensusType) -> Optional[Any]:
        """Get consensus value from multiple entries"""
        with self.lock:
            if key not in self.memory:
                return None
            
            entries = self.memory[key]
            if not entries:
                return None
            
            if consensus_type == ConsensusType.MAJORITY_VOTE:
                # Count occurrences of each value
                value_counts = Counter(e.value for e in entries)
                return value_counts.most_common(1)[0][0]
            
            elif consensus_type == ConsensusType.WEIGHTED_VOTE:
                # Weight by confidence
                value_weights = defaultdict(float)
                for entry in entries:
                    value_weights[str(entry.value)] += entry.confidence
                return max(value_weights.items(), key=lambda x: x[1])[0]
            
            elif consensus_type == ConsensusType.EXPERTISE_BASED:
                # Return value from highest confidence source
                return max(entries, key=lambda x: x.confidence).value
            
            else:
                # Default to most recent
                return max(entries, key=lambda x: x.timestamp).value
    
    def _evict_oldest(self):
        """Evict oldest, least accessed entries"""
        all_entries = []
        for key, entries in self.memory.items():
            for entry in entries:
                all_entries.append((key, entry))
        
        # Sort by access count and timestamp
        all_entries.sort(key=lambda x: (x[1].access_count, x[1].timestamp))
        
        # Remove oldest 10%
        to_remove = len(all_entries) // 10
        for key, entry in all_entries[:to_remove]:
            self.memory[key].remove(entry)
            if not self.memory[key]:
                del self.memory[key]
                # Update indices
                for tag in entry.tags:
                    self.indices[tag].discard(key)


class ConsensusEngine:
    """Handles consensus mechanisms for group decisions"""
    
    def __init__(self):
        self.active_decisions: Dict[str, Dict] = {}
        self.decision_history: List[Dict] = []
        self.lock = Lock()
    
    def create_decision(self, decision_id: str, question: str, 
                       options: List[Any], consensus_type: ConsensusType,
                       required_agents: Optional[List[str]] = None,
                       timeout: float = 30.0) -> Dict:
        """Create a new consensus decision"""
        with self.lock:
            self.active_decisions[decision_id] = {
                'id': decision_id,
                'question': question,
                'options': options,
                'consensus_type': consensus_type,
                'required_agents': required_agents or [],
                'votes': {},
                'started_at': time.time(),
                'timeout': timeout,
                'status': 'active'
            }
            return self.active_decisions[decision_id]
    
    def cast_vote(self, decision_id: str, agent_id: str, 
                  vote: Any, confidence: float = 1.0) -> bool:
        """Cast a vote for a decision"""
        with self.lock:
            if decision_id not in self.active_decisions:
                return False
            
            decision = self.active_decisions[decision_id]
            if decision['status'] != 'active':
                return False
            
            # Check timeout
            if time.time() - decision['started_at'] > decision['timeout']:
                decision['status'] = 'timeout'
                return False
            
            # Record vote
            decision['votes'][agent_id] = {
                'choice': vote,
                'confidence': confidence,
                'timestamp': time.time()
            }
            
            # Check if we have enough votes
            if self._check_consensus_reached(decision):
                decision['status'] = 'completed'
                decision['result'] = self._calculate_result(decision)
                self.decision_history.append(decision)
            
            return True
    
    def get_result(self, decision_id: str) -> Optional[Any]:
        """Get the result of a consensus decision"""
        with self.lock:
            if decision_id in self.active_decisions:
                decision = self.active_decisions[decision_id]
                if decision['status'] == 'completed':
                    return decision.get('result')
            
            # Check history
            for d in self.decision_history:
                if d['id'] == decision_id:
                    return d.get('result')
            
            return None
    
    def _check_consensus_reached(self, decision: Dict) -> bool:
        """Check if consensus has been reached"""
        consensus_type = decision['consensus_type']
        required_agents = decision['required_agents']
        votes = decision['votes']
        
        if required_agents:
            # Check if all required agents have voted
            if not all(agent in votes for agent in required_agents):
                return False
        
        if consensus_type == ConsensusType.UNANIMOUS:
            # Need all votes to agree
            if not votes:
                return False
            vote_values = [v['choice'] for v in votes.values()]
            return len(set(vote_values)) == 1
        
        elif consensus_type == ConsensusType.QUORUM:
            # Need at least 2/3 of required agents
            if required_agents:
                return len(votes) >= len(required_agents) * 2 / 3
            else:
                return len(votes) >= 3  # Default minimum
        
        else:
            # For other types, we can calculate once we have enough votes
            return len(votes) >= max(3, len(required_agents) // 2)
    
    def _calculate_result(self, decision: Dict) -> Any:
        """Calculate the final result based on consensus type"""
        consensus_type = decision['consensus_type']
        votes = decision['votes']
        
        if not votes:
            return None
        
        if consensus_type == ConsensusType.MAJORITY_VOTE:
            vote_counts = Counter(v['choice'] for v in votes.values())
            return vote_counts.most_common(1)[0][0]
        
        elif consensus_type == ConsensusType.WEIGHTED_VOTE:
            weighted_votes = defaultdict(float)
            for v in votes.values():
                weighted_votes[v['choice']] += v['confidence']
            return max(weighted_votes.items(), key=lambda x: x[1])[0]
        
        elif consensus_type == ConsensusType.EXPERTISE_BASED:
            # Would need agent profiles to determine expertise
            # For now, use confidence as proxy
            best_vote = max(votes.values(), key=lambda x: x['confidence'])
            return best_vote['choice']
        
        else:
            # Default to majority
            vote_counts = Counter(v['choice'] for v in votes.values())
            return vote_counts.most_common(1)[0][0]


class TaskDistributor:
    """Distributes tasks based on agent capabilities and performance"""
    
    def __init__(self):
        self.task_queue: List[CollaborativeTask] = []
        self.agent_profiles: Dict[str, AgentProfile] = {}
        self.task_history: List[Dict] = []
        self.lock = Lock()
    
    def register_agent(self, profile: AgentProfile):
        """Register an agent with the distributor"""
        with self.lock:
            self.agent_profiles[profile.agent_id] = profile
    
    def submit_task(self, task: CollaborativeTask) -> str:
        """Submit a task for distribution"""
        with self.lock:
            self.task_queue.append(task)
            self._distribute_tasks()
            return task.task_id
    
    def _distribute_tasks(self):
        """Distribute pending tasks to suitable agents"""
        pending_tasks = [t for t in self.task_queue if t.status == 'pending']
        
        for task in pending_tasks:
            # Find suitable agents
            suitable_agents = self._find_suitable_agents(task)
            
            if suitable_agents:
                # Assign task to best agents
                assigned = suitable_agents[:min(3, len(suitable_agents))]
                task.assigned_agents = [a.agent_id for a in assigned]
                task.status = 'assigned'
                
                # Update agent profiles
                for agent in assigned:
                    self.agent_profiles[agent.agent_id].active_tasks.add(task.task_id)
                
                logger.info(f"Task {task.task_id} assigned to {task.assigned_agents}")
    
    def _find_suitable_agents(self, task: CollaborativeTask) -> List[AgentProfile]:
        """Find agents suitable for a task"""
        suitable = []
        
        for agent in self.agent_profiles.values():
            # Check if agent has required capabilities
            capability_match = 0
            for req_cap in task.required_capabilities:
                for cap in agent.capabilities.values():
                    if req_cap.lower() in cap.name.lower() or req_cap.lower() in cap.domain.lower():
                        capability_match += cap.proficiency
                        break
            
            if capability_match > 0:
                # Calculate suitability score
                score = (
                    capability_match * 0.4 +
                    agent.performance_score * 0.3 +
                    agent.trust_score * 0.2 +
                    (1.0 - len(agent.active_tasks) / 10) * 0.1
                )
                suitable.append((agent, score))
        
        # Sort by suitability score
        suitable.sort(key=lambda x: x[1], reverse=True)
        return [agent for agent, _ in suitable]
    
    def complete_task(self, task_id: str, agent_id: str, 
                     result: Any, success: bool = True):
        """Mark a task as completed by an agent"""
        with self.lock:
            task = next((t for t in self.task_queue if t.task_id == task_id), None)
            if not task:
                return
            
            # Update task results
            task.results[agent_id] = {
                'result': result,
                'success': success,
                'timestamp': datetime.now()
            }
            
            # Update agent profile
            if agent_id in self.agent_profiles:
                profile = self.agent_profiles[agent_id]
                profile.active_tasks.discard(task_id)
                
                # Update performance score
                if success:
                    profile.performance_score = min(1.0, profile.performance_score * 1.1)
                else:
                    profile.performance_score = max(0.0, profile.performance_score * 0.9)
            
            # Check if task is fully completed
            if len(task.results) >= len(task.assigned_agents):
                task.status = 'completed'
                self.task_history.append({
                    'task': task,
                    'completed_at': datetime.now()
                })


class KnowledgeTransferProtocol:
    """Handles knowledge transfer between agents"""
    
    def __init__(self):
        self.teaching_sessions: Dict[str, Dict] = {}
        self.knowledge_base: Dict[str, Dict] = {}
        self.transfer_history: List[Dict] = []
        self.lock = Lock()
    
    def request_teaching(self, student_id: str, teacher_id: str,
                        topic: str, context: Dict = None) -> str:
        """Request teaching from one agent to another"""
        with self.lock:
            session_id = str(uuid.uuid4())
            self.teaching_sessions[session_id] = {
                'id': session_id,
                'student_id': student_id,
                'teacher_id': teacher_id,
                'topic': topic,
                'context': context or {},
                'status': 'requested',
                'started_at': datetime.now(),
                'knowledge_transferred': []
            }
            return session_id
    
    def transfer_knowledge(self, session_id: str, knowledge: Dict) -> bool:
        """Transfer knowledge in a teaching session"""
        with self.lock:
            if session_id not in self.teaching_sessions:
                return False
            
            session = self.teaching_sessions[session_id]
            if session['status'] != 'requested':
                return False
            
            # Store knowledge
            knowledge_id = str(uuid.uuid4())
            self.knowledge_base[knowledge_id] = {
                'id': knowledge_id,
                'content': knowledge,
                'teacher_id': session['teacher_id'],
                'topic': session['topic'],
                'created_at': datetime.now(),
                'access_count': 0
            }
            
            # Update session
            session['knowledge_transferred'].append(knowledge_id)
            session['status'] = 'active'
            
            return True
    
    def complete_teaching(self, session_id: str, success: bool = True) -> bool:
        """Complete a teaching session"""
        with self.lock:
            if session_id not in self.teaching_sessions:
                return False
            
            session = self.teaching_sessions[session_id]
            session['status'] = 'completed' if success else 'failed'
            session['completed_at'] = datetime.now()
            
            # Record in history
            self.transfer_history.append(session)
            
            return True
    
    def get_knowledge(self, topic: str, limit: int = 10) -> List[Dict]:
        """Retrieve knowledge on a topic"""
        with self.lock:
            relevant = []
            for k_id, knowledge in self.knowledge_base.items():
                if topic.lower() in knowledge['topic'].lower():
                    knowledge['access_count'] += 1
                    relevant.append(knowledge)
            
            # Sort by relevance and recency
            relevant.sort(key=lambda x: (x['access_count'], x['created_at']), 
                         reverse=True)
            
            return relevant[:limit]


class ConflictResolver:
    """Resolves conflicts between agent findings"""
    
    def __init__(self):
        self.conflicts: Dict[str, Dict] = {}
        self.resolutions: Dict[str, Dict] = {}
        self.lock = Lock()
    
    def report_conflict(self, agent_id: str, topic: str, 
                       finding: Any, conflicting_with: Dict) -> str:
        """Report a conflict in findings"""
        with self.lock:
            conflict_id = str(uuid.uuid4())
            self.conflicts[conflict_id] = {
                'id': conflict_id,
                'reporter': agent_id,
                'topic': topic,
                'findings': {
                    agent_id: finding
                },
                'conflicting_with': conflicting_with,
                'status': 'open',
                'created_at': datetime.now()
            }
            return conflict_id
    
    def add_perspective(self, conflict_id: str, agent_id: str, finding: Any):
        """Add another perspective to a conflict"""
        with self.lock:
            if conflict_id in self.conflicts:
                self.conflicts[conflict_id]['findings'][agent_id] = finding
    
    def resolve_conflict(self, conflict_id: str, method: str = 'weighted_consensus') -> Any:
        """Resolve a conflict using specified method"""
        with self.lock:
            if conflict_id not in self.conflicts:
                return None
            
            conflict = self.conflicts[conflict_id]
            findings = conflict['findings']
            
            if method == 'weighted_consensus':
                # Weight by agent trust scores (would need agent profiles)
                # For now, use simple majority
                finding_counts = Counter(str(f) for f in findings.values())
                resolution = finding_counts.most_common(1)[0][0]
            
            elif method == 'expert_opinion':
                # Would need to identify expert in the topic
                # For now, return most recent
                resolution = list(findings.values())[-1]
            
            elif method == 'synthesis':
                # Attempt to synthesize findings
                resolution = {
                    'synthesized': True,
                    'components': list(findings.values()),
                    'method': 'combined perspectives'
                }
            
            else:
                # Default to first finding
                resolution = list(findings.values())[0]
            
            # Record resolution
            self.resolutions[conflict_id] = {
                'conflict_id': conflict_id,
                'resolution': resolution,
                'method': method,
                'resolved_at': datetime.now()
            }
            
            conflict['status'] = 'resolved'
            return resolution


class CollaborativeIntelligenceServer:
    """WebSocket server for agent collaboration"""
    
    def __init__(self, host: str = 'localhost', port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.agent_profiles: Dict[str, AgentProfile] = {}
        
        # Initialize subsystems
        self.memory = CollectiveMemory()
        self.consensus = ConsensusEngine()
        self.distributor = TaskDistributor()
        self.knowledge_transfer = KnowledgeTransferProtocol()
        self.conflict_resolver = ConflictResolver()
        
        # Message handlers
        self.handlers: Dict[MessageType, Callable] = {
            MessageType.REGISTER: self._handle_register,
            MessageType.BROADCAST: self._handle_broadcast,
            MessageType.DIRECT: self._handle_direct,
            MessageType.MEMORY_WRITE: self._handle_memory_write,
            MessageType.MEMORY_READ: self._handle_memory_read,
            MessageType.TASK_REQUEST: self._handle_task_request,
            MessageType.TASK_RESPONSE: self._handle_task_response,
            MessageType.KNOWLEDGE_SHARE: self._handle_knowledge_share,
            MessageType.CONSENSUS_REQUEST: self._handle_consensus_request,
            MessageType.CONSENSUS_VOTE: self._handle_consensus_vote,
            MessageType.CAPABILITY_UPDATE: self._handle_capability_update,
            MessageType.TEACHING_REQUEST: self._handle_teaching_request,
            MessageType.TEACHING_RESPONSE: self._handle_teaching_response,
            MessageType.CONFLICT_RESOLUTION: self._handle_conflict_resolution,
            MessageType.HEARTBEAT: self._handle_heartbeat,
            MessageType.PERFORMANCE_UPDATE: self._handle_performance_update
        }
    
    async def start(self):
        """Start the collaboration server"""
        logger.info(f"Starting Collaborative Intelligence Server on {self.host}:{self.port}")
        async with websockets.serve(self._handle_client, self.host, self.port):
            await asyncio.Future()  # Run forever
    
    async def _handle_client(self, websocket, path):
        """Handle a client connection"""
        agent_id = None
        try:
            # Wait for registration
            message = await websocket.recv()
            data = json.loads(message)
            
            if data.get('type') != MessageType.REGISTER.value:
                await websocket.send(json.dumps({
                    'error': 'Must register first'
                }))
                return
            
            agent_id = data.get('agent_id', str(uuid.uuid4()))
            self.clients[agent_id] = websocket
            
            # Send registration confirmation
            await websocket.send(json.dumps({
                'type': 'registration_confirmed',
                'agent_id': agent_id
            }))
            
            logger.info(f"Agent {agent_id} connected")
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_type = MessageType(data.get('type'))
                    
                    if message_type in self.handlers:
                        response = await self.handlers[message_type](agent_id, data)
                        if response:
                            await websocket.send(json.dumps(response))
                
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'error': 'Invalid JSON'
                    }))
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await websocket.send(json.dumps({
                        'error': str(e)
                    }))
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Agent {agent_id} disconnected")
        finally:
            if agent_id and agent_id in self.clients:
                del self.clients[agent_id]
    
    async def _handle_register(self, agent_id: str, data: Dict) -> Dict:
        """Handle agent registration"""
        profile = AgentProfile(
            agent_id=agent_id,
            name=data.get('name', f'Agent_{agent_id[:8]}'),
            type=data.get('agent_type', 'generic')
        )
        
        # Register capabilities
        for cap_data in data.get('capabilities', []):
            capability = AgentCapability(
                name=cap_data['name'],
                domain=cap_data.get('domain', 'general'),
                proficiency=cap_data.get('proficiency', 0.5)
            )
            profile.capabilities[capability.name] = capability
        
        self.agent_profiles[agent_id] = profile
        self.distributor.register_agent(profile)
        
        return {
            'type': 'registration_complete',
            'profile': {
                'agent_id': profile.agent_id,
                'name': profile.name,
                'capabilities': list(profile.capabilities.keys())
            }
        }
    
    async def _handle_broadcast(self, agent_id: str, data: Dict) -> None:
        """Handle broadcast message"""
        message = {
            'type': 'broadcast',
            'from': agent_id,
            'content': data.get('content'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to all other connected agents
        tasks = []
        for client_id, websocket in self.clients.items():
            if client_id != agent_id:
                tasks.append(websocket.send(json.dumps(message)))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _handle_direct(self, agent_id: str, data: Dict) -> Dict:
        """Handle direct message"""
        target_id = data.get('target_id')
        if target_id not in self.clients:
            return {'error': 'Target agent not connected'}
        
        message = {
            'type': 'direct_message',
            'from': agent_id,
            'content': data.get('content'),
            'timestamp': datetime.now().isoformat()
        }
        
        await self.clients[target_id].send(json.dumps(message))
        return {'status': 'sent'}
    
    async def _handle_memory_write(self, agent_id: str, data: Dict) -> Dict:
        """Handle memory write request"""
        success = self.memory.write(
            key=data.get('key'),
            value=data.get('value'),
            agent_id=agent_id,
            confidence=data.get('confidence', 1.0),
            tags=set(data.get('tags', []))
        )
        
        return {
            'type': 'memory_write_response',
            'success': success
        }
    
    async def _handle_memory_read(self, agent_id: str, data: Dict) -> Dict:
        """Handle memory read request"""
        key = data.get('key')
        
        if data.get('by_tags'):
            result = self.memory.query_by_tags(set(data.get('tags', [])))
        else:
            result = self.memory.read(key, agent_id)
        
        return {
            'type': 'memory_read_response',
            'key': key,
            'value': result
        }
    
    async def _handle_task_request(self, agent_id: str, data: Dict) -> Dict:
        """Handle task submission request"""
        task = CollaborativeTask(
            task_id=str(uuid.uuid4()),
            description=data.get('description'),
            required_capabilities=data.get('required_capabilities', []),
            priority=data.get('priority', 0.5),
            consensus_required=data.get('consensus_required', False)
        )
        
        task_id = self.distributor.submit_task(task)
        
        # Notify assigned agents
        for assigned_id in task.assigned_agents:
            if assigned_id in self.clients:
                await self.clients[assigned_id].send(json.dumps({
                    'type': 'task_assignment',
                    'task': {
                        'task_id': task.task_id,
                        'description': task.description,
                        'priority': task.priority
                    }
                }))
        
        return {
            'type': 'task_submitted',
            'task_id': task_id,
            'assigned_agents': task.assigned_agents
        }
    
    async def _handle_task_response(self, agent_id: str, data: Dict) -> Dict:
        """Handle task completion response"""
        task_id = data.get('task_id')
        result = data.get('result')
        success = data.get('success', True)
        
        self.distributor.complete_task(task_id, agent_id, result, success)
        
        return {
            'type': 'task_response_acknowledged'
        }
    
    async def _handle_knowledge_share(self, agent_id: str, data: Dict) -> Dict:
        """Handle knowledge sharing"""
        # Store in collective memory with knowledge tag
        self.memory.write(
            key=f"knowledge_{data.get('topic')}_{agent_id}_{time.time()}",
            value=data.get('knowledge'),
            agent_id=agent_id,
            tags={'knowledge', data.get('topic')}
        )
        
        # Broadcast to interested agents
        await self._broadcast_to_domain(data.get('topic'), {
            'type': 'new_knowledge',
            'topic': data.get('topic'),
            'from': agent_id,
            'summary': data.get('summary')
        })
        
        return {
            'type': 'knowledge_shared'
        }
    
    async def _handle_consensus_request(self, agent_id: str, data: Dict) -> Dict:
        """Handle consensus request"""
        decision_id = str(uuid.uuid4())
        
        decision = self.consensus.create_decision(
            decision_id=decision_id,
            question=data.get('question'),
            options=data.get('options', []),
            consensus_type=ConsensusType(data.get('consensus_type', 'majority_vote')),
            required_agents=data.get('required_agents'),
            timeout=data.get('timeout', 30.0)
        )
        
        # Notify relevant agents
        agents_to_notify = decision['required_agents'] or list(self.clients.keys())
        for notify_id in agents_to_notify:
            if notify_id in self.clients and notify_id != agent_id:
                await self.clients[notify_id].send(json.dumps({
                    'type': 'consensus_request',
                    'decision_id': decision_id,
                    'question': decision['question'],
                    'options': decision['options']
                }))
        
        return {
            'type': 'consensus_initiated',
            'decision_id': decision_id
        }
    
    async def _handle_consensus_vote(self, agent_id: str, data: Dict) -> Dict:
        """Handle consensus vote"""
        decision_id = data.get('decision_id')
        vote = data.get('vote')
        confidence = data.get('confidence', 1.0)
        
        success = self.consensus.cast_vote(decision_id, agent_id, vote, confidence)
        
        if success:
            result = self.consensus.get_result(decision_id)
            if result is not None:
                # Consensus reached, notify all participants
                decision = self.consensus.active_decisions.get(decision_id)
                if decision:
                    for voter_id in decision['votes'].keys():
                        if voter_id in self.clients:
                            await self.clients[voter_id].send(json.dumps({
                                'type': 'consensus_reached',
                                'decision_id': decision_id,
                                'result': result
                            }))
        
        return {
            'type': 'vote_recorded',
            'success': success
        }
    
    async def _handle_capability_update(self, agent_id: str, data: Dict) -> Dict:
        """Handle capability update"""
        if agent_id not in self.agent_profiles:
            return {'error': 'Agent not registered'}
        
        profile = self.agent_profiles[agent_id]
        capability_name = data.get('capability')
        
        if capability_name in profile.capabilities:
            cap = profile.capabilities[capability_name]
            cap.proficiency = data.get('proficiency', cap.proficiency)
            cap.experience_count = data.get('experience_count', cap.experience_count)
            cap.success_rate = data.get('success_rate', cap.success_rate)
            cap.last_updated = datetime.now()
        else:
            # Add new capability
            profile.capabilities[capability_name] = AgentCapability(
                name=capability_name,
                domain=data.get('domain', 'general'),
                proficiency=data.get('proficiency', 0.5)
            )
        
        return {
            'type': 'capability_updated'
        }
    
    async def _handle_teaching_request(self, agent_id: str, data: Dict) -> Dict:
        """Handle teaching request"""
        teacher_id = data.get('teacher_id')
        topic = data.get('topic')
        
        if teacher_id not in self.clients:
            return {'error': 'Teacher not available'}
        
        session_id = self.knowledge_transfer.request_teaching(
            student_id=agent_id,
            teacher_id=teacher_id,
            topic=topic,
            context=data.get('context')
        )
        
        # Notify teacher
        await self.clients[teacher_id].send(json.dumps({
            'type': 'teaching_request',
            'session_id': session_id,
            'student_id': agent_id,
            'topic': topic
        }))
        
        return {
            'type': 'teaching_requested',
            'session_id': session_id
        }
    
    async def _handle_teaching_response(self, agent_id: str, data: Dict) -> Dict:
        """Handle teaching response"""
        session_id = data.get('session_id')
        knowledge = data.get('knowledge')
        
        success = self.knowledge_transfer.transfer_knowledge(session_id, knowledge)
        
        if success:
            # Notify student
            session = self.knowledge_transfer.teaching_sessions.get(session_id)
            if session and session['student_id'] in self.clients:
                await self.clients[session['student_id']].send(json.dumps({
                    'type': 'knowledge_received',
                    'session_id': session_id,
                    'knowledge': knowledge
                }))
        
        return {
            'type': 'teaching_delivered',
            'success': success
        }
    
    async def _handle_conflict_resolution(self, agent_id: str, data: Dict) -> Dict:
        """Handle conflict resolution"""
        action = data.get('action')
        
        if action == 'report':
            conflict_id = self.conflict_resolver.report_conflict(
                agent_id=agent_id,
                topic=data.get('topic'),
                finding=data.get('finding'),
                conflicting_with=data.get('conflicting_with', {})
            )
            
            # Notify other agents about the conflict
            await self._broadcast_to_domain(data.get('topic'), {
                'type': 'conflict_reported',
                'conflict_id': conflict_id,
                'topic': data.get('topic')
            })
            
            return {
                'type': 'conflict_reported',
                'conflict_id': conflict_id
            }
        
        elif action == 'add_perspective':
            self.conflict_resolver.add_perspective(
                conflict_id=data.get('conflict_id'),
                agent_id=agent_id,
                finding=data.get('finding')
            )
            return {'type': 'perspective_added'}
        
        elif action == 'request_resolution':
            result = self.conflict_resolver.resolve_conflict(
                conflict_id=data.get('conflict_id'),
                method=data.get('method', 'weighted_consensus')
            )
            return {
                'type': 'conflict_resolved',
                'resolution': result
            }
        
        return {'error': 'Unknown conflict action'}
    
    async def _handle_heartbeat(self, agent_id: str, data: Dict) -> Dict:
        """Handle agent heartbeat"""
        if agent_id in self.agent_profiles:
            self.agent_profiles[agent_id].last_seen = datetime.now()
        
        return {
            'type': 'heartbeat_ack',
            'timestamp': datetime.now().isoformat()
        }
    
    async def _handle_performance_update(self, agent_id: str, data: Dict) -> Dict:
        """Handle performance update"""
        if agent_id not in self.agent_profiles:
            return {'error': 'Agent not registered'}
        
        profile = self.agent_profiles[agent_id]
        profile.performance_score = data.get('performance_score', profile.performance_score)
        profile.trust_score = data.get('trust_score', profile.trust_score)
        
        return {
            'type': 'performance_updated'
        }
    
    async def _broadcast_to_domain(self, domain: str, message: Dict):
        """Broadcast message to agents interested in a domain"""
        tasks = []
        for agent_id, profile in self.agent_profiles.items():
            if domain in profile.knowledge_domains and agent_id in self.clients:
                tasks.append(self.clients[agent_id].send(json.dumps(message)))
        
        await asyncio.gather(*tasks, return_exceptions=True)


class CollaborativeAgentClient:
    """Client for agents to connect to the collaborative intelligence system"""
    
    def __init__(self, agent_id: str, name: str, agent_type: str,
                 capabilities: List[Dict], server_url: str = 'ws://localhost:8765'):
        self.agent_id = agent_id
        self.name = name
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.server_url = server_url
        self.websocket = None
        self.running = False
        self.message_handlers: Dict[str, Callable] = {}
    
    async def connect(self):
        """Connect to the collaboration server"""
        self.websocket = await websockets.connect(self.server_url)
        
        # Register with server
        await self.websocket.send(json.dumps({
            'type': MessageType.REGISTER.value,
            'agent_id': self.agent_id,
            'name': self.name,
            'agent_type': self.agent_type,
            'capabilities': self.capabilities
        }))
        
        # Wait for confirmation
        response = await self.websocket.recv()
        data = json.loads(response)
        
        if data.get('type') == 'registration_confirmed':
            logger.info(f"Agent {self.agent_id} registered successfully")
            self.running = True
            
            # Start message handling loop
            asyncio.create_task(self._message_loop())
        else:
            raise Exception("Registration failed")
    
    async def _message_loop(self):
        """Handle incoming messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type')
                    
                    if message_type in self.message_handlers:
                        await self.message_handlers[message_type](data)
                    else:
                        logger.debug(f"Unhandled message type: {message_type}")
                
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")
            self.running = False
    
    async def broadcast(self, content: Any):
        """Broadcast message to all agents"""
        await self.websocket.send(json.dumps({
            'type': MessageType.BROADCAST.value,
            'content': content
        }))
    
    async def send_direct(self, target_id: str, content: Any):
        """Send direct message to another agent"""
        await self.websocket.send(json.dumps({
            'type': MessageType.DIRECT.value,
            'target_id': target_id,
            'content': content
        }))
    
    async def write_memory(self, key: str, value: Any, 
                          confidence: float = 1.0, tags: List[str] = None):
        """Write to collective memory"""
        await self.websocket.send(json.dumps({
            'type': MessageType.MEMORY_WRITE.value,
            'key': key,
            'value': value,
            'confidence': confidence,
            'tags': tags or []
        }))
    
    async def read_memory(self, key: str) -> Any:
        """Read from collective memory"""
        await self.websocket.send(json.dumps({
            'type': MessageType.MEMORY_READ.value,
            'key': key
        }))
        
        # Wait for response
        # In production, implement proper response correlation
        response = await self.websocket.recv()
        data = json.loads(response)
        return data.get('value')
    
    async def submit_task(self, description: str, required_capabilities: List[str],
                         priority: float = 0.5, consensus_required: bool = False):
        """Submit a collaborative task"""
        await self.websocket.send(json.dumps({
            'type': MessageType.TASK_REQUEST.value,
            'description': description,
            'required_capabilities': required_capabilities,
            'priority': priority,
            'consensus_required': consensus_required
        }))
    
    async def complete_task(self, task_id: str, result: Any, success: bool = True):
        """Report task completion"""
        await self.websocket.send(json.dumps({
            'type': MessageType.TASK_RESPONSE.value,
            'task_id': task_id,
            'result': result,
            'success': success
        }))
    
    async def share_knowledge(self, topic: str, knowledge: Any, summary: str = None):
        """Share knowledge with other agents"""
        await self.websocket.send(json.dumps({
            'type': MessageType.KNOWLEDGE_SHARE.value,
            'topic': topic,
            'knowledge': knowledge,
            'summary': summary
        }))
    
    async def request_consensus(self, question: str, options: List[Any],
                               consensus_type: str = 'majority_vote',
                               required_agents: List[str] = None):
        """Request consensus from other agents"""
        await self.websocket.send(json.dumps({
            'type': MessageType.CONSENSUS_REQUEST.value,
            'question': question,
            'options': options,
            'consensus_type': consensus_type,
            'required_agents': required_agents
        }))
    
    async def vote(self, decision_id: str, vote: Any, confidence: float = 1.0):
        """Cast a vote in a consensus decision"""
        await self.websocket.send(json.dumps({
            'type': MessageType.CONSENSUS_VOTE.value,
            'decision_id': decision_id,
            'vote': vote,
            'confidence': confidence
        }))
    
    async def request_teaching(self, teacher_id: str, topic: str, context: Dict = None):
        """Request teaching from another agent"""
        await self.websocket.send(json.dumps({
            'type': MessageType.TEACHING_REQUEST.value,
            'teacher_id': teacher_id,
            'topic': topic,
            'context': context or {}
        }))
    
    async def teach(self, session_id: str, knowledge: Dict):
        """Provide teaching to another agent"""
        await self.websocket.send(json.dumps({
            'type': MessageType.TEACHING_RESPONSE.value,
            'session_id': session_id,
            'knowledge': knowledge
        }))
    
    async def report_conflict(self, topic: str, finding: Any, conflicting_with: Dict):
        """Report a conflict in findings"""
        await self.websocket.send(json.dumps({
            'type': MessageType.CONFLICT_RESOLUTION.value,
            'action': 'report',
            'topic': topic,
            'finding': finding,
            'conflicting_with': conflicting_with
        }))
    
    async def update_capability(self, capability: str, proficiency: float,
                               experience_count: int = None, success_rate: float = None):
        """Update agent capability"""
        await self.websocket.send(json.dumps({
            'type': MessageType.CAPABILITY_UPDATE.value,
            'capability': capability,
            'proficiency': proficiency,
            'experience_count': experience_count,
            'success_rate': success_rate
        }))
    
    async def send_heartbeat(self):
        """Send heartbeat to server"""
        await self.websocket.send(json.dumps({
            'type': MessageType.HEARTBEAT.value
        }))
    
    async def update_performance(self, performance_score: float, trust_score: float):
        """Update performance metrics"""
        await self.websocket.send(json.dumps({
            'type': MessageType.PERFORMANCE_UPDATE.value,
            'performance_score': performance_score,
            'trust_score': trust_score
        }))
    
    def on_message(self, message_type: str):
        """Decorator for registering message handlers"""
        def decorator(func):
            self.message_handlers[message_type] = func
            return func
        return decorator
    
    async def disconnect(self):
        """Disconnect from server"""
        self.running = False
        if self.websocket:
            await self.websocket.close()


# Example usage
async def example_agent():
    """Example of an agent using the collaborative system"""
    
    # Create agent client
    agent = CollaborativeAgentClient(
        agent_id="example_agent_1",
        name="Example Agent",
        agent_type="research",
        capabilities=[
            {'name': 'web_search', 'domain': 'information', 'proficiency': 0.8},
            {'name': 'text_analysis', 'domain': 'nlp', 'proficiency': 0.9}
        ]
    )
    
    # Register message handlers
    @agent.on_message('task_assignment')
    async def handle_task(data):
        task = data['task']
        logger.info(f"Received task: {task['description']}")
        
        # Simulate task completion
        await asyncio.sleep(2)
        await agent.complete_task(
            task_id=task['task_id'],
            result={'answer': 'Task completed successfully'},
            success=True
        )
    
    @agent.on_message('consensus_request')
    async def handle_consensus(data):
        logger.info(f"Consensus requested: {data['question']}")
        
        # Simulate decision making
        await asyncio.sleep(1)
        await agent.vote(
            decision_id=data['decision_id'],
            vote=data['options'][0],  # Vote for first option
            confidence=0.8
        )
    
    @agent.on_message('teaching_request')
    async def handle_teaching_request(data):
        logger.info(f"Teaching requested on: {data['topic']}")
        
        # Share knowledge
        await agent.teach(
            session_id=data['session_id'],
            knowledge={
                'topic': data['topic'],
                'content': 'Here is what I know about this topic...',
                'examples': ['example1', 'example2']
            }
        )
    
    # Connect to server
    await agent.connect()
    
    # Example operations
    await agent.write_memory('test_key', 'test_value', tags=['test'])
    await agent.share_knowledge('python', {'tip': 'Use async/await for concurrency'})
    await agent.submit_task('Analyze website content', ['web_search', 'text_analysis'])
    
    # Keep running
    while agent.running:
        await agent.send_heartbeat()
        await asyncio.sleep(30)


async def run_server():
    """Run the collaborative intelligence server"""
    server = CollaborativeIntelligenceServer()
    await server.start()


if __name__ == "__main__":
    # Run the server
    asyncio.run(run_server())
    
    # Or run an example agent
    # asyncio.run(example_agent())