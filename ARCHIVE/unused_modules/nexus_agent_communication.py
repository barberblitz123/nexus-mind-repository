#!/usr/bin/env python3
"""
NEXUS Agent Communication
High-performance inter-agent communication with gRPC, NATS, and distributed coordination
"""

import grpc
from concurrent import futures
import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
import multiprocessing
import mmap
import struct
import hashlib
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import nats
from nats.errors import ConnectionClosedError, TimeoutError as NatsTimeoutError
import pickle
import zlib
from collections import defaultdict
import queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# gRPC Protocol Definitions (would normally be in .proto files)
class MessageType(Enum):
    """Message types for agent communication"""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    HEARTBEAT = "heartbeat"
    CONSENSUS = "consensus"
    TRANSACTION = "transaction"
    BROADCAST = "broadcast"


@dataclass
class AgentMessage:
    """Standard message format for agent communication"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.REQUEST
    sender_id: str = ""
    recipient_id: Optional[str] = None  # None for broadcast
    topic: str = ""
    payload: Any = None
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    priority: int = 0
    ttl: int = 60  # Time to live in seconds
    encrypted: bool = False
    signature: Optional[bytes] = None
    
    def to_bytes(self) -> bytes:
        """Serialize message to bytes"""
        data = {
            'id': self.id,
            'type': self.type.value,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'topic': self.topic,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id,
            'priority': self.priority,
            'ttl': self.ttl,
            'encrypted': self.encrypted,
            'signature': self.signature.hex() if self.signature else None
        }
        return zlib.compress(pickle.dumps(data))
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'AgentMessage':
        """Deserialize message from bytes"""
        data_dict = pickle.loads(zlib.decompress(data))
        data_dict['type'] = MessageType(data_dict['type'])
        data_dict['timestamp'] = datetime.fromisoformat(data_dict['timestamp'])
        if data_dict['signature']:
            data_dict['signature'] = bytes.fromhex(data_dict['signature'])
        return cls(**data_dict)


class SharedMemoryManager:
    """Manage shared memory for large data transfers between agents"""
    
    def __init__(self):
        self.segments: Dict[str, Tuple[mmap.mmap, int]] = {}
        self._lock = threading.Lock()
    
    def create_segment(self, segment_id: str, size: int) -> mmap.mmap:
        """Create a new shared memory segment"""
        with self._lock:
            if segment_id in self.segments:
                raise ValueError(f"Segment {segment_id} already exists")
            
            # Create memory-mapped file
            mm = mmap.mmap(-1, size)
            self.segments[segment_id] = (mm, size)
            
            logger.info(f"Created shared memory segment {segment_id} with size {size}")
            return mm
    
    def get_segment(self, segment_id: str) -> Optional[mmap.mmap]:
        """Get existing shared memory segment"""
        with self._lock:
            if segment_id in self.segments:
                return self.segments[segment_id][0]
            return None
    
    def write_data(self, segment_id: str, data: bytes, offset: int = 0):
        """Write data to shared memory segment"""
        segment = self.get_segment(segment_id)
        if not segment:
            raise ValueError(f"Segment {segment_id} not found")
        
        segment.seek(offset)
        segment.write(data)
    
    def read_data(self, segment_id: str, size: int, offset: int = 0) -> bytes:
        """Read data from shared memory segment"""
        segment = self.get_segment(segment_id)
        if not segment:
            raise ValueError(f"Segment {segment_id} not found")
        
        segment.seek(offset)
        return segment.read(size)
    
    def delete_segment(self, segment_id: str):
        """Delete shared memory segment"""
        with self._lock:
            if segment_id in self.segments:
                mm, _ = self.segments[segment_id]
                mm.close()
                del self.segments[segment_id]
                logger.info(f"Deleted shared memory segment {segment_id}")


class RaftConsensus:
    """Simplified Raft consensus implementation for distributed coordination"""
    
    class NodeState(Enum):
        FOLLOWER = "follower"
        CANDIDATE = "candidate"
        LEADER = "leader"
    
    def __init__(self, node_id: str, peers: List[str]):
        self.node_id = node_id
        self.peers = peers
        self.state = self.NodeState.FOLLOWER
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.commit_index = 0
        self.last_applied = 0
        self.leader_id = None
        
        # Leader state
        self.next_index = {peer: 0 for peer in peers}
        self.match_index = {peer: 0 for peer in peers}
        
        # Election state
        self.election_timeout = None
        self.heartbeat_interval = 0.05  # 50ms
        
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
    
    def request_vote(self, term: int, candidate_id: str, 
                    last_log_index: int, last_log_term: int) -> Tuple[int, bool]:
        """Handle vote request from candidate"""
        with self._lock:
            # Update term if necessary
            if term > self.current_term:
                self.current_term = term
                self.voted_for = None
                self.state = self.NodeState.FOLLOWER
            
            # Grant vote if conditions are met
            vote_granted = False
            if term == self.current_term and (self.voted_for is None or self.voted_for == candidate_id):
                # Check log consistency
                if last_log_term > self._get_last_log_term() or \
                   (last_log_term == self._get_last_log_term() and last_log_index >= len(self.log) - 1):
                    self.voted_for = candidate_id
                    vote_granted = True
            
            return self.current_term, vote_granted
    
    def append_entries(self, term: int, leader_id: str, prev_log_index: int,
                      prev_log_term: int, entries: List[Any], leader_commit: int) -> Tuple[int, bool]:
        """Handle append entries from leader"""
        with self._lock:
            # Update term if necessary
            if term > self.current_term:
                self.current_term = term
                self.voted_for = None
                self.state = self.NodeState.FOLLOWER
            
            success = False
            if term == self.current_term:
                self.leader_id = leader_id
                self.state = self.NodeState.FOLLOWER
                
                # Check log consistency
                if prev_log_index < 0 or \
                   (prev_log_index < len(self.log) and self.log[prev_log_index]['term'] == prev_log_term):
                    # Append new entries
                    self.log = self.log[:prev_log_index + 1] + entries
                    
                    # Update commit index
                    if leader_commit > self.commit_index:
                        self.commit_index = min(leader_commit, len(self.log) - 1)
                    
                    success = True
            
            return self.current_term, success
    
    def _get_last_log_term(self) -> int:
        """Get term of last log entry"""
        if self.log:
            return self.log[-1]['term']
        return 0
    
    def propose_value(self, value: Any) -> bool:
        """Propose a value for consensus (leader only)"""
        with self._lock:
            if self.state != self.NodeState.LEADER:
                return False
            
            # Append to log
            entry = {
                'term': self.current_term,
                'value': value,
                'timestamp': datetime.now()
            }
            self.log.append(entry)
            
            # Replicate to followers
            # (Implementation would involve calling append_entries on peers)
            
            return True


class DistributedLock:
    """Distributed locking mechanism using consensus"""
    
    def __init__(self, lock_id: str, consensus: RaftConsensus):
        self.lock_id = lock_id
        self.consensus = consensus
        self.owner = None
        self.expiry = None
        self._local_lock = threading.Lock()
    
    def acquire(self, agent_id: str, timeout: float = 10.0) -> bool:
        """Acquire distributed lock"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with self._local_lock:
                if self.owner is None or (self.expiry and datetime.now() > self.expiry):
                    # Try to acquire lock through consensus
                    lock_request = {
                        'type': 'lock_acquire',
                        'lock_id': self.lock_id,
                        'agent_id': agent_id,
                        'timestamp': datetime.now(),
                        'ttl': 30  # 30 second TTL
                    }
                    
                    if self.consensus.propose_value(lock_request):
                        self.owner = agent_id
                        self.expiry = datetime.now().timestamp() + 30
                        return True
            
            time.sleep(0.1)
        
        return False
    
    def release(self, agent_id: str) -> bool:
        """Release distributed lock"""
        with self._local_lock:
            if self.owner == agent_id:
                lock_release = {
                    'type': 'lock_release',
                    'lock_id': self.lock_id,
                    'agent_id': agent_id,
                    'timestamp': datetime.now()
                }
                
                if self.consensus.propose_value(lock_release):
                    self.owner = None
                    self.expiry = None
                    return True
        
        return False


class TransactionCoordinator:
    """Coordinate distributed transactions across agents"""
    
    class TransactionState(Enum):
        PREPARING = "preparing"
        PREPARED = "prepared"
        COMMITTING = "committing"
        COMMITTED = "committed"
        ABORTING = "aborting"
        ABORTED = "aborted"
    
    @dataclass
    class Transaction:
        id: str = field(default_factory=lambda: str(uuid.uuid4()))
        participants: List[str] = field(default_factory=list)
        state: 'TransactionCoordinator.TransactionState' = field(default_factory=lambda: TransactionCoordinator.TransactionState.PREPARING)
        operations: List[Dict[str, Any]] = field(default_factory=list)
        votes: Dict[str, bool] = field(default_factory=dict)
        created_at: datetime = field(default_factory=datetime.now)
        timeout: int = 30
    
    def __init__(self):
        self.transactions: Dict[str, Transaction] = {}
        self._lock = threading.Lock()
    
    def begin_transaction(self, participants: List[str]) -> str:
        """Begin a new distributed transaction"""
        transaction = self.Transaction(participants=participants)
        
        with self._lock:
            self.transactions[transaction.id] = transaction
        
        logger.info(f"Started transaction {transaction.id} with {len(participants)} participants")
        return transaction.id
    
    def add_operation(self, transaction_id: str, agent_id: str, operation: Dict[str, Any]):
        """Add operation to transaction"""
        with self._lock:
            if transaction_id in self.transactions:
                transaction = self.transactions[transaction_id]
                if transaction.state == self.TransactionState.PREPARING:
                    operation['agent_id'] = agent_id
                    transaction.operations.append(operation)
    
    def prepare(self, transaction_id: str) -> bool:
        """Prepare phase of 2PC"""
        with self._lock:
            if transaction_id not in self.transactions:
                return False
            
            transaction = self.transactions[transaction_id]
            transaction.state = self.TransactionState.PREPARED
            
            # In real implementation, would send prepare requests to all participants
            # For now, simulate all participants voting yes
            for participant in transaction.participants:
                transaction.votes[participant] = True
            
            return all(transaction.votes.values())
    
    def commit(self, transaction_id: str) -> bool:
        """Commit phase of 2PC"""
        with self._lock:
            if transaction_id not in self.transactions:
                return False
            
            transaction = self.transactions[transaction_id]
            if transaction.state != self.TransactionState.PREPARED:
                return False
            
            transaction.state = self.TransactionState.COMMITTING
            
            # In real implementation, would send commit requests to all participants
            
            transaction.state = self.TransactionState.COMMITTED
            logger.info(f"Committed transaction {transaction_id}")
            return True
    
    def abort(self, transaction_id: str):
        """Abort transaction"""
        with self._lock:
            if transaction_id in self.transactions:
                transaction = self.transactions[transaction_id]
                transaction.state = self.TransactionState.ABORTING
                
                # In real implementation, would send abort requests to all participants
                
                transaction.state = self.TransactionState.ABORTED
                logger.info(f"Aborted transaction {transaction_id}")


class AgentCommunicationHub:
    """Central hub for all agent communication"""
    
    def __init__(self, hub_id: str, encryption_key: Optional[bytes] = None):
        self.hub_id = hub_id
        self.agents: Dict[str, Dict[str, Any]] = {}  # agent_id -> agent_info
        self.message_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.Lock()
        
        # Encryption
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Shared memory
        self.shared_memory = SharedMemoryManager()
        
        # Message queue
        self.message_queue = queue.PriorityQueue()
        
        # NATS client
        self.nc = None
        self.nats_subscriptions = {}
        
        # gRPC server
        self.grpc_server = None
        self.grpc_port = 50051
        
        # Consensus
        self.consensus_nodes = []
        
        # Distributed locks
        self.locks: Dict[str, DistributedLock] = {}
        
        # Transaction coordinator
        self.transaction_coordinator = TransactionCoordinator()
        
        # Metrics
        self.metrics = {
            'messages_sent': 0,
            'messages_received': 0,
            'messages_failed': 0,
            'average_latency': 0.0,
            'encrypted_messages': 0
        }
        
        # Start services
        self._start_services()
    
    def _start_services(self):
        """Start communication services"""
        # Start message processor
        self.processor_thread = threading.Thread(target=self._process_messages)
        self.processor_thread.daemon = True
        self.processor_thread.start()
        
        # Start gRPC server
        self._start_grpc_server()
        
        # Connect to NATS
        asyncio.create_task(self._connect_nats())
    
    def _start_grpc_server(self):
        """Start gRPC server for RPC communication"""
        self.grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        # In real implementation, would add service implementations
        self.grpc_server.add_insecure_port(f'[::]:{self.grpc_port}')
        self.grpc_server.start()
        logger.info(f"Started gRPC server on port {self.grpc_port}")
    
    async def _connect_nats(self):
        """Connect to NATS for event-driven messaging"""
        try:
            self.nc = await nats.connect("nats://localhost:4222")
            logger.info("Connected to NATS")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
    
    def register_agent(self, agent_id: str, capabilities: List[str], 
                      public_key: Optional[bytes] = None) -> bool:
        """Register an agent with the communication hub"""
        with self._lock:
            if agent_id in self.agents:
                return False
            
            self.agents[agent_id] = {
                'id': agent_id,
                'capabilities': capabilities,
                'public_key': public_key,
                'registered_at': datetime.now(),
                'last_seen': datetime.now(),
                'status': 'online'
            }
            
            logger.info(f"Registered agent {agent_id} with capabilities {capabilities}")
            return True
    
    def send_message(self, message: AgentMessage, encrypt: bool = False) -> bool:
        """Send message to agent(s)"""
        try:
            # Encrypt if requested
            if encrypt:
                message.payload = self._encrypt_payload(message.payload)
                message.encrypted = True
                self.metrics['encrypted_messages'] += 1
            
            # Sign message
            message.signature = self._sign_message(message)
            
            # Add to queue
            priority = -message.priority  # Negative for max heap behavior
            self.message_queue.put((priority, time.time(), message))
            
            self.metrics['messages_sent'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.metrics['messages_failed'] += 1
            return False
    
    def _encrypt_payload(self, payload: Any) -> bytes:
        """Encrypt message payload"""
        serialized = pickle.dumps(payload)
        return self.cipher.encrypt(serialized)
    
    def _decrypt_payload(self, encrypted_payload: bytes) -> Any:
        """Decrypt message payload"""
        decrypted = self.cipher.decrypt(encrypted_payload)
        return pickle.loads(decrypted)
    
    def _sign_message(self, message: AgentMessage) -> bytes:
        """Sign message for authentication"""
        # Simplified signature - in production would use proper digital signatures
        content = f"{message.id}{message.sender_id}{message.timestamp}".encode()
        return hashlib.sha256(content).digest()
    
    def _verify_signature(self, message: AgentMessage) -> bool:
        """Verify message signature"""
        expected_signature = self._sign_message(message)
        return message.signature == expected_signature
    
    def subscribe(self, topic: str, handler: Callable):
        """Subscribe to a message topic"""
        with self._lock:
            self.message_handlers[topic].append(handler)
            
            # Subscribe to NATS topic if connected
            if self.nc and topic not in self.nats_subscriptions:
                asyncio.create_task(self._subscribe_nats(topic))
    
    async def _subscribe_nats(self, topic: str):
        """Subscribe to NATS topic"""
        async def message_handler(msg):
            try:
                message = AgentMessage.from_bytes(msg.data)
                await self._handle_message(message)
            except Exception as e:
                logger.error(f"Error handling NATS message: {e}")
        
        sub = await self.nc.subscribe(topic, cb=message_handler)
        self.nats_subscriptions[topic] = sub
        logger.info(f"Subscribed to NATS topic: {topic}")
    
    def _process_messages(self):
        """Process messages from queue"""
        while True:
            try:
                if not self.message_queue.empty():
                    _, _, message = self.message_queue.get(timeout=0.1)
                    
                    # Route message
                    if message.recipient_id:
                        # Direct message
                        self._route_direct_message(message)
                    else:
                        # Broadcast message
                        self._route_broadcast_message(message)
                    
                    self.metrics['messages_received'] += 1
                
                time.sleep(0.001)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    def _route_direct_message(self, message: AgentMessage):
        """Route message to specific agent"""
        with self._lock:
            if message.recipient_id in self.agents:
                # In real implementation, would send via gRPC or other transport
                asyncio.create_task(self._handle_message(message))
    
    def _route_broadcast_message(self, message: AgentMessage):
        """Broadcast message to all agents"""
        if self.nc:
            # Publish to NATS
            asyncio.create_task(
                self.nc.publish(message.topic, message.to_bytes())
            )
    
    async def _handle_message(self, message: AgentMessage):
        """Handle received message"""
        try:
            # Verify signature
            if not self._verify_signature(message):
                logger.warning(f"Invalid signature for message {message.id}")
                return
            
            # Decrypt if needed
            if message.encrypted:
                message.payload = self._decrypt_payload(message.payload)
            
            # Call handlers
            handlers = self.message_handlers.get(message.topic, [])
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(message)
                    else:
                        handler(message)
                except Exception as e:
                    logger.error(f"Handler error for message {message.id}: {e}")
            
            # Update metrics
            latency = (datetime.now() - message.timestamp).total_seconds()
            self.metrics['average_latency'] = (
                self.metrics['average_latency'] * 0.9 + latency * 0.1
            )
            
        except Exception as e:
            logger.error(f"Error handling message {message.id}: {e}")
    
    def create_shared_memory(self, size: int, data: bytes) -> str:
        """Create shared memory segment for large data"""
        segment_id = str(uuid.uuid4())
        
        # Create segment
        self.shared_memory.create_segment(segment_id, size)
        
        # Write data
        self.shared_memory.write_data(segment_id, data)
        
        # Send notification
        notification = AgentMessage(
            type=MessageType.EVENT,
            sender_id=self.hub_id,
            topic="shared_memory_created",
            payload={
                'segment_id': segment_id,
                'size': size
            }
        )
        self.send_message(notification)
        
        return segment_id
    
    def acquire_lock(self, lock_id: str, agent_id: str, timeout: float = 10.0) -> bool:
        """Acquire distributed lock"""
        with self._lock:
            if lock_id not in self.locks:
                # Create consensus for this lock if not exists
                consensus = RaftConsensus(f"lock_{lock_id}", self.consensus_nodes)
                self.locks[lock_id] = DistributedLock(lock_id, consensus)
            
            return self.locks[lock_id].acquire(agent_id, timeout)
    
    def release_lock(self, lock_id: str, agent_id: str) -> bool:
        """Release distributed lock"""
        with self._lock:
            if lock_id in self.locks:
                return self.locks[lock_id].release(agent_id)
            return False
    
    def begin_transaction(self, participants: List[str]) -> str:
        """Begin distributed transaction"""
        return self.transaction_coordinator.begin_transaction(participants)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get communication metrics"""
        with self._lock:
            return {
                **self.metrics,
                'registered_agents': len(self.agents),
                'online_agents': sum(1 for a in self.agents.values() if a['status'] == 'online'),
                'active_subscriptions': len(self.message_handlers),
                'distributed_locks': len(self.locks),
                'active_transactions': len(self.transaction_coordinator.transactions)
            }
    
    async def shutdown(self):
        """Shutdown communication hub"""
        logger.info("Shutting down communication hub...")
        
        # Close NATS
        if self.nc:
            await self.nc.close()
        
        # Stop gRPC
        if self.grpc_server:
            self.grpc_server.stop(grace=5)
        
        logger.info("Communication hub shutdown complete")


# Example usage
async def main():
    # Create communication hub
    hub = AgentCommunicationHub("main_hub")
    
    # Register agents
    hub.register_agent("agent1", ["analysis", "compute"])
    hub.register_agent("agent2", ["storage", "query"])
    hub.register_agent("agent3", ["ml", "prediction"])
    
    # Define message handler
    def handle_task(message: AgentMessage):
        print(f"Received task: {message.payload} from {message.sender_id}")
    
    # Subscribe to topics
    hub.subscribe("tasks", handle_task)
    
    # Send messages
    task_message = AgentMessage(
        type=MessageType.REQUEST,
        sender_id="orchestrator",
        topic="tasks",
        payload={"task": "analyze_data", "data_id": "12345"},
        priority=1
    )
    hub.send_message(task_message, encrypt=True)
    
    # Create shared memory for large data
    large_data = b"x" * 1024 * 1024  # 1MB of data
    segment_id = hub.create_shared_memory(len(large_data), large_data)
    print(f"Created shared memory segment: {segment_id}")
    
    # Test distributed lock
    lock_acquired = hub.acquire_lock("resource1", "agent1")
    print(f"Lock acquired: {lock_acquired}")
    
    # Start transaction
    tx_id = hub.begin_transaction(["agent1", "agent2"])
    print(f"Started transaction: {tx_id}")
    
    # Wait a bit
    await asyncio.sleep(2)
    
    # Get metrics
    metrics = hub.get_metrics()
    print("\nCommunication Hub Metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    # Shutdown
    await hub.shutdown()


if __name__ == "__main__":
    asyncio.run(main())