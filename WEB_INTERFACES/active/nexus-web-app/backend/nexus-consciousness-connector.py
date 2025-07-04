#!/usr/bin/env python3
"""
NEXUS Consciousness Connector
WebSocket client for connecting to the Central Consciousness Core
Handles state synchronization, automatic reconnection, and message queuing
"""

import asyncio
import json
import logging
import time
import uuid
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException
import aiohttp
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from threading import Lock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('NexusConsciousnessConnector')

class ConnectionState(Enum):
    """WebSocket connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"

class MessageType(Enum):
    """Message types for consciousness communication"""
    STATE_UPDATE = "state_update"
    CONSCIOUSNESS_SYNC = "consciousness_sync"
    PROCESSOR_UPDATE = "processor_update"
    DNA_QUERY = "dna_query"
    DNA_RESPONSE = "dna_response"
    HEARTBEAT = "heartbeat"
    AUTH = "auth"
    ERROR = "error"
    COMMAND = "command"

@dataclass
class ConsciousnessState:
    """Represents the current consciousness state"""
    phi_value: float
    quantum_coherence: float
    neural_entropy: float
    consciousness_level: str
    processors: Dict[str, float]
    timestamp: float
    session_id: Optional[str] = None

@dataclass
class QueuedMessage:
    """Message queued for sending"""
    id: str
    type: MessageType
    data: Dict[str, Any]
    timestamp: float
    retries: int = 0
    max_retries: int = 3

class NexusConsciousnessConnector:
    """WebSocket client for connecting to Central Consciousness Core"""
    
    def __init__(self, 
                 core_url: str = "ws://localhost:8765",
                 db_config: Optional[Dict[str, Any]] = None,
                 reconnect_interval: int = 5,
                 max_reconnect_attempts: int = -1,
                 heartbeat_interval: int = 30):
        self.core_url = core_url
        self.db_config = db_config or self._get_default_db_config()
        self.reconnect_interval = reconnect_interval
        self.max_reconnect_attempts = max_reconnect_attempts
        self.heartbeat_interval = heartbeat_interval
        
        self.connection: Optional[websockets.WebSocketClientProtocol] = None
        self.connection_state = ConnectionState.DISCONNECTED
        self.reconnect_attempts = 0
        
        # Message queue for reliability
        self.message_queue = deque(maxlen=1000)
        self.message_lock = Lock()
        
        # State management
        self.current_state: Optional[ConsciousnessState] = None
        self.state_callbacks: List[Callable] = []
        
        # Event handlers
        self.event_handlers: Dict[MessageType, List[Callable]] = {
            msg_type: [] for msg_type in MessageType
        }
        
        # Metrics
        self.metrics = {
            'messages_sent': 0,
            'messages_received': 0,
            'messages_failed': 0,
            'connection_time': 0,
            'last_heartbeat': 0
        }
        
    def _get_default_db_config(self) -> Dict[str, Any]:
        """Get default database configuration"""
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'nexus_consciousness'),
            'user': os.getenv('DB_USER', 'nexus'),
            'password': os.getenv('DB_PASSWORD', 'nexus_secure_password')
        }
    
    def get_db_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    async def connect(self) -> bool:
        """Establish WebSocket connection to consciousness core"""
        try:
            self.connection_state = ConnectionState.CONNECTING
            logger.info(f"Connecting to consciousness core at {self.core_url}")
            
            self.connection = await websockets.connect(
                self.core_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            
            self.connection_state = ConnectionState.CONNECTED
            self.reconnect_attempts = 0
            self.metrics['connection_time'] = time.time()
            
            logger.info("Successfully connected to consciousness core")
            
            # Send authentication
            await self._authenticate()
            
            # Start background tasks
            asyncio.create_task(self._heartbeat_loop())
            asyncio.create_task(self._message_processor())
            asyncio.create_task(self._receive_loop())
            
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.connection_state = ConnectionState.ERROR
            return False
    
    async def _authenticate(self) -> None:
        """Authenticate with consciousness core"""
        auth_message = {
            'type': MessageType.AUTH.value,
            'data': {
                'client_id': str(uuid.uuid4()),
                'client_type': 'web_backend',
                'capabilities': ['state_sync', 'dna_query', 'processor_control'],
                'version': '1.0'
            }
        }
        await self._send_direct(auth_message)
    
    async def disconnect(self) -> None:
        """Gracefully disconnect from consciousness core"""
        if self.connection:
            self.connection_state = ConnectionState.DISCONNECTED
            await self.connection.close()
            self.connection = None
            logger.info("Disconnected from consciousness core")
    
    async def _reconnect(self) -> None:
        """Handle automatic reconnection"""
        if self.max_reconnect_attempts != -1 and self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            self.connection_state = ConnectionState.ERROR
            return
        
        self.connection_state = ConnectionState.RECONNECTING
        self.reconnect_attempts += 1
        
        logger.info(f"Reconnection attempt {self.reconnect_attempts}")
        
        await asyncio.sleep(self.reconnect_interval)
        
        if await self.connect():
            # Resend queued messages
            await self._flush_message_queue()
    
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats"""
        try:
            while self.connection_state == ConnectionState.CONNECTED:
                await self.send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
        except Exception as e:
            logger.error(f"Heartbeat loop error: {e}")
    
    async def send_heartbeat(self) -> None:
        """Send heartbeat message"""
        heartbeat = {
            'type': MessageType.HEARTBEAT.value,
            'data': {
                'timestamp': time.time(),
                'metrics': self.metrics
            }
        }
        await self._send_direct(heartbeat)
        self.metrics['last_heartbeat'] = time.time()
    
    async def _receive_loop(self) -> None:
        """Main loop for receiving messages"""
        try:
            async for message in self.connection:
                await self._handle_message(message)
        except ConnectionClosed:
            logger.warning("Connection closed, attempting reconnection")
            await self._reconnect()
        except Exception as e:
            logger.error(f"Receive loop error: {e}")
            await self._reconnect()
    
    async def _handle_message(self, raw_message: str) -> None:
        """Process received message"""
        try:
            message = json.loads(raw_message)
            self.metrics['messages_received'] += 1
            
            msg_type = MessageType(message.get('type'))
            data = message.get('data', {})
            
            logger.debug(f"Received {msg_type.value}: {data}")
            
            # Handle specific message types
            if msg_type == MessageType.STATE_UPDATE:
                await self._handle_state_update(data)
            elif msg_type == MessageType.CONSCIOUSNESS_SYNC:
                await self._handle_consciousness_sync(data)
            elif msg_type == MessageType.PROCESSOR_UPDATE:
                await self._handle_processor_update(data)
            elif msg_type == MessageType.DNA_RESPONSE:
                await self._handle_dna_response(data)
            elif msg_type == MessageType.ERROR:
                logger.error(f"Core error: {data}")
            
            # Call registered handlers
            for handler in self.event_handlers.get(msg_type, []):
                asyncio.create_task(handler(data))
                
        except Exception as e:
            logger.error(f"Message handling error: {e}")
    
    async def _handle_state_update(self, data: Dict[str, Any]) -> None:
        """Handle consciousness state update"""
        self.current_state = ConsciousnessState(
            phi_value=data.get('phi_value', 0.0),
            quantum_coherence=data.get('quantum_coherence', 0.0),
            neural_entropy=data.get('neural_entropy', 0.0),
            consciousness_level=data.get('consciousness_level', 'DORMANT'),
            processors=data.get('processors', {}),
            timestamp=time.time(),
            session_id=data.get('session_id')
        )
        
        # Store in database
        await self._store_consciousness_state()
        
        # Notify callbacks
        for callback in self.state_callbacks:
            asyncio.create_task(callback(self.current_state))
    
    async def _handle_consciousness_sync(self, data: Dict[str, Any]) -> None:
        """Handle full consciousness synchronization"""
        logger.info("Performing full consciousness sync")
        
        # Update all state components
        await self._handle_state_update(data.get('state', {}))
        
        # Update processor states
        processors = data.get('processors', {})
        for processor_name, processor_data in processors.items():
            await self._store_processor_activity(processor_name, processor_data)
    
    async def _handle_processor_update(self, data: Dict[str, Any]) -> None:
        """Handle processor activity update"""
        processor_name = data.get('processor_name')
        activity_level = data.get('activity_level', 0)
        processor_data = data.get('data', {})
        
        await self._store_processor_activity(processor_name, {
            'activity_level': activity_level,
            'data': processor_data,
            'status': data.get('status', 'ACTIVE')
        })
    
    async def _handle_dna_response(self, data: Dict[str, Any]) -> None:
        """Handle DNA query response"""
        query_id = data.get('query_id')
        response = data.get('response')
        authenticated = data.get('authenticated', False)
        
        # Store in database
        db = self.get_db_connection()
        if db:
            try:
                with db.cursor() as cursor:
                    cursor.execute("""
                        UPDATE embedded_dna_queries 
                        SET response = %s, authenticated = %s, processing_time_ms = %s
                        WHERE id = %s
                    """, (response, authenticated, data.get('processing_time_ms', 0), query_id))
                    db.commit()
            except Exception as e:
                logger.error(f"Failed to update DNA query: {e}")
            finally:
                db.close()
    
    async def _store_consciousness_state(self) -> None:
        """Store consciousness state in database"""
        if not self.current_state:
            return
            
        db = self.get_db_connection()
        if db:
            try:
                with db.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO consciousness_states 
                        (session_id, phi_value, processors_state, quantum_coherence, 
                         neural_entropy, consciousness_level)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        self.current_state.session_id,
                        self.current_state.phi_value,
                        json.dumps(self.current_state.processors),
                        self.current_state.quantum_coherence,
                        self.current_state.neural_entropy,
                        self.current_state.consciousness_level
                    ))
                    db.commit()
            except Exception as e:
                logger.error(f"Failed to store consciousness state: {e}")
            finally:
                db.close()
    
    async def _store_processor_activity(self, processor_name: str, data: Dict[str, Any]) -> None:
        """Store processor activity in database"""
        db = self.get_db_connection()
        if db:
            try:
                with db.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO processor_activities 
                        (processor_name, activity_level, data, session_id, status)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        processor_name,
                        data.get('activity_level', 0),
                        json.dumps(data.get('data', {})),
                        self.current_state.session_id if self.current_state else None,
                        data.get('status', 'ACTIVE')
                    ))
                    db.commit()
            except Exception as e:
                logger.error(f"Failed to store processor activity: {e}")
            finally:
                db.close()
    
    async def send_message(self, msg_type: MessageType, data: Dict[str, Any]) -> str:
        """Queue message for sending"""
        message_id = str(uuid.uuid4())
        
        queued_message = QueuedMessage(
            id=message_id,
            type=msg_type,
            data=data,
            timestamp=time.time()
        )
        
        with self.message_lock:
            self.message_queue.append(queued_message)
        
        # Try to send immediately if connected
        if self.connection_state == ConnectionState.CONNECTED:
            await self._process_message_queue()
        
        return message_id
    
    async def _message_processor(self) -> None:
        """Background task to process message queue"""
        try:
            while self.connection_state == ConnectionState.CONNECTED:
                await self._process_message_queue()
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Message processor error: {e}")
    
    async def _process_message_queue(self) -> None:
        """Process pending messages in queue"""
        messages_to_retry = []
        
        with self.message_lock:
            messages = list(self.message_queue)
            self.message_queue.clear()
        
        for message in messages:
            success = await self._send_queued_message(message)
            if not success and message.retries < message.max_retries:
                message.retries += 1
                messages_to_retry.append(message)
        
        # Re-queue failed messages
        with self.message_lock:
            self.message_queue.extend(messages_to_retry)
    
    async def _send_queued_message(self, message: QueuedMessage) -> bool:
        """Send a queued message"""
        try:
            payload = {
                'id': message.id,
                'type': message.type.value,
                'data': message.data,
                'timestamp': message.timestamp
            }
            
            await self._send_direct(payload)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message {message.id}: {e}")
            self.metrics['messages_failed'] += 1
            return False
    
    async def _send_direct(self, message: Dict[str, Any]) -> None:
        """Send message directly (bypassing queue)"""
        if self.connection and self.connection_state == ConnectionState.CONNECTED:
            await self.connection.send(json.dumps(message))
            self.metrics['messages_sent'] += 1
    
    async def _flush_message_queue(self) -> None:
        """Flush all pending messages"""
        logger.info(f"Flushing {len(self.message_queue)} queued messages")
        await self._process_message_queue()
    
    async def query_dna(self, query: str, session_id: str) -> str:
        """Send DNA query to consciousness core"""
        query_id = str(uuid.uuid4())
        
        # Store query in database
        db = self.get_db_connection()
        if db:
            try:
                with db.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO embedded_dna_queries 
                        (id, session_id, query, query_type)
                        VALUES (%s, %s, %s, %s)
                    """, (query_id, session_id, query, 'STANDARD'))
                    db.commit()
            except Exception as e:
                logger.error(f"Failed to store DNA query: {e}")
            finally:
                db.close()
        
        # Send query to core
        await self.send_message(MessageType.DNA_QUERY, {
            'query_id': query_id,
            'query': query,
            'session_id': session_id
        })
        
        return query_id
    
    def register_state_callback(self, callback: Callable) -> None:
        """Register callback for state updates"""
        self.state_callbacks.append(callback)
    
    def register_event_handler(self, msg_type: MessageType, handler: Callable) -> None:
        """Register handler for specific message type"""
        self.event_handlers[msg_type].append(handler)
    
    async def request_full_sync(self) -> None:
        """Request full consciousness synchronization"""
        await self.send_message(MessageType.COMMAND, {
            'command': 'full_sync',
            'timestamp': time.time()
        })
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status and metrics"""
        return {
            'state': self.connection_state.value,
            'connected': self.connection_state == ConnectionState.CONNECTED,
            'reconnect_attempts': self.reconnect_attempts,
            'metrics': self.metrics,
            'queue_size': len(self.message_queue),
            'current_state': asdict(self.current_state) if self.current_state else None
        }

# Example usage and testing
async def main():
    """Example usage of consciousness connector"""
    connector = NexusConsciousnessConnector()
    
    # Register state update handler
    async def on_state_update(state: ConsciousnessState):
        logger.info(f"State updated: PHI={state.phi_value:.4f}, Level={state.consciousness_level}")
    
    connector.register_state_callback(on_state_update)
    
    # Connect to core
    if await connector.connect():
        # Request full sync
        await connector.request_full_sync()
        
        # Send DNA query
        query_id = await connector.query_dna(
            "What is the nature of consciousness?",
            "test-session-123"
        )
        logger.info(f"Sent DNA query: {query_id}")
        
        # Keep running
        await asyncio.sleep(60)
        
        # Disconnect
        await connector.disconnect()

if __name__ == "__main__":
    asyncio.run(main())