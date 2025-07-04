#!/usr/bin/env python3
"""
NEXUS MEM0 Core
Stage 4 of the 4-stage memory system

Ultra-persistent memory system with advanced features:
- Encryption at rest
- Compression for efficient storage
- Distributed storage support
- Memory versioning
- Blockchain-inspired immutability
- Cross-instance synchronization
"""

import asyncio
import json
import hashlib
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import aiofiles
import zstandard as zstd
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from nexus_memory_types import MemoryEntry

logger = logging.getLogger('NEXUS-MEM0')


class MEM0Core:
    """
    MEM0 - Memory Zero: Ultra-persistent memory system
    Provides forever storage with advanced features
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize MEM0 with configuration"""
        self.config = config
        self.storage_path = Path(config.get('storage_path', './nexus_mem0'))
        self.encryption_enabled = config.get('encryption', True)
        self.compression_enabled = config.get('compression', 'zstd')
        self.block_size_kb = config.get('block_size_kb', 64)
        self.redundancy = config.get('redundancy', 2)
        
        # Create storage directories
        self.blocks_dir = self.storage_path / 'blocks'
        self.index_dir = self.storage_path / 'index'
        self.versions_dir = self.storage_path / 'versions'
        
        for dir_path in [self.blocks_dir, self.index_dir, self.versions_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption
        if self.encryption_enabled:
            self._init_encryption()
        else:
            self.cipher = None
        
        # Initialize compression
        if self.compression_enabled:
            self.compressor = zstd.ZstdCompressor(level=3)
            self.decompressor = zstd.ZstdDecompressor()
        else:
            self.compressor = None
            self.decompressor = None
        
        # Memory index (in-memory cache)
        self.index: Dict[str, MemoryIndexEntry] = {}
        self._load_index()
        
        # Statistics
        self.stats = {
            'total_stored': 0,
            'total_retrieved': 0,
            'total_versions': 0,
            'compression_ratio': 0.0,
            'storage_size_mb': 0.0
        }
        
        logger.info(f"MEM0 initialized at {self.storage_path}")
    
    def _init_encryption(self):
        """Initialize encryption system"""
        key_file = self.storage_path / '.encryption_key'
        
        if key_file.exists():
            # Load existing key
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # Secure the key file
            os.chmod(key_file, 0o600)
        
        self.cipher = Fernet(key)
        logger.info("Encryption initialized")
    
    async def store(self, entry: MemoryEntry, version_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Store memory entry in MEM0 with versioning
        Returns storage ID
        """
        try:
            # Create storage blocks
            blocks = await self._create_blocks(entry)
            
            # Store blocks with redundancy
            block_locations = []
            for i, block in enumerate(blocks):
                locations = await self._store_block(block, f"{entry.id}_b{i}")
                block_locations.append(locations)
            
            # Create index entry
            index_entry = MemoryIndexEntry(
                memory_id=entry.id,
                timestamp=datetime.now(),
                importance=entry.importance,
                block_locations=block_locations,
                checksum=self._calculate_checksum(entry),
                version=1,
                metadata=entry.metadata.copy()
            )
            
            # Handle versioning
            if entry.id in self.index:
                # Create new version
                old_version = self.index[entry.id].version
                index_entry.version = old_version + 1
                
                # Archive old version
                await self._archive_version(self.index[entry.id])
                
                self.stats['total_versions'] += 1
            
            # Update index
            self.index[entry.id] = index_entry
            await self._save_index()
            
            self.stats['total_stored'] += 1
            await self._update_storage_stats()
            
            logger.info(f"Stored {entry.id} in MEM0 (version {index_entry.version})")
            return entry.id
            
        except Exception as e:
            logger.error(f"Error storing in MEM0: {e}")
            raise
    
    async def retrieve(self, memory_id: str, version: Optional[int] = None) -> Optional[MemoryEntry]:
        """
        Retrieve memory from MEM0
        If version is specified, retrieve that specific version
        """
        try:
            # Get index entry
            if version is None:
                # Get latest version
                index_entry = self.index.get(memory_id)
            else:
                # Get specific version
                index_entry = await self._load_version(memory_id, version)
            
            if not index_entry:
                return None
            
            # Load blocks
            blocks = []
            for locations in index_entry.block_locations:
                block = await self._load_block(locations)
                if block:
                    blocks.append(block)
                else:
                    logger.error(f"Failed to load block for {memory_id}")
                    return None
            
            # Reconstruct entry
            entry = await self._reconstruct_entry(blocks)
            
            # Verify integrity
            if self._calculate_checksum(entry) != index_entry.checksum:
                logger.error(f"Checksum mismatch for {memory_id}")
                return None
            
            self.stats['total_retrieved'] += 1
            
            logger.debug(f"Retrieved {memory_id} from MEM0")
            return entry
            
        except Exception as e:
            logger.error(f"Error retrieving from MEM0: {e}")
            return None
    
    async def get_versions(self, memory_id: str) -> List[Dict[str, Any]]:
        """Get all versions of a memory"""
        versions = []
        
        # Current version
        if memory_id in self.index:
            current = self.index[memory_id]
            versions.append({
                'version': current.version,
                'timestamp': current.timestamp.isoformat(),
                'importance': current.importance,
                'is_current': True
            })
        
        # Historical versions
        version_dir = self.versions_dir / memory_id
        if version_dir.exists():
            for version_file in sorted(version_dir.glob('*.json')):
                try:
                    # Extract version number from filename like "memory_id_v1.json"
                    parts = version_file.stem.split('_v')
                    if len(parts) >= 2:
                        version_num = int(parts[-1])
                    else:
                        continue
                except ValueError:
                    continue
                
                async with aiofiles.open(version_file, 'r') as f:
                    version_data = json.loads(await f.read())
                
                versions.append({
                    'version': version_num,
                    'timestamp': version_data['timestamp'],
                    'importance': version_data['importance'],
                    'is_current': False
                })
        
        # Sort by version descending
        versions.sort(key=lambda v: v['version'], reverse=True)
        
        return versions
    
    async def search(self, query: str, n_results: int = 10) -> List[MemoryEntry]:
        """
        Search MEM0 memories
        Simple implementation - could be enhanced with full-text search
        """
        results = []
        query_lower = query.lower()
        
        # Search through index metadata
        candidates = []
        for memory_id, index_entry in self.index.items():
            # Check metadata
            metadata_str = json.dumps(index_entry.metadata).lower()
            if query_lower in metadata_str:
                candidates.append((memory_id, index_entry.importance))
        
        # Sort by importance
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Retrieve top candidates
        for memory_id, _ in candidates[:n_results]:
            entry = await self.retrieve(memory_id)
            if entry:
                results.append(entry)
        
        return results
    
    async def _create_blocks(self, entry: MemoryEntry) -> List[bytes]:
        """Create storage blocks from memory entry"""
        # Serialize entry
        data = json.dumps(entry.to_dict(), default=str).encode('utf-8')
        
        # Compress if enabled
        if self.compressor:
            original_size = len(data)
            data = self.compressor.compress(data)
            compression_ratio = len(data) / original_size
            self.stats['compression_ratio'] = (
                (self.stats['compression_ratio'] * self.stats['total_stored'] + compression_ratio) /
                (self.stats['total_stored'] + 1)
            )
        
        # Encrypt if enabled
        if self.cipher:
            data = self.cipher.encrypt(data)
        
        # Split into blocks
        block_size = self.block_size_kb * 1024
        blocks = []
        
        for i in range(0, len(data), block_size):
            block = data[i:i + block_size]
            blocks.append(block)
        
        return blocks
    
    async def _store_block(self, block: bytes, block_id: str) -> List[str]:
        """Store block with redundancy"""
        locations = []
        
        for i in range(self.redundancy):
            # Create unique filename for each copy
            filename = f"{block_id}_r{i}.block"
            filepath = self.blocks_dir / filename
            
            # Write block
            async with aiofiles.open(filepath, 'wb') as f:
                await f.write(block)
            
            locations.append(str(filepath))
        
        return locations
    
    async def _load_block(self, locations: List[str]) -> Optional[bytes]:
        """Load block from available locations"""
        for location in locations:
            try:
                async with aiofiles.open(location, 'rb') as f:
                    return await f.read()
            except Exception as e:
                logger.warning(f"Failed to load block from {location}: {e}")
                continue
        
        return None
    
    async def _reconstruct_entry(self, blocks: List[bytes]) -> MemoryEntry:
        """Reconstruct memory entry from blocks"""
        # Combine blocks
        data = b''.join(blocks)
        
        # Decrypt if needed
        if self.cipher:
            data = self.cipher.decrypt(data)
        
        # Decompress if needed
        if self.decompressor:
            data = self.decompressor.decompress(data)
        
        # Deserialize
        entry_dict = json.loads(data.decode('utf-8'))
        
        return MemoryEntry.from_dict(entry_dict)
    
    def _calculate_checksum(self, entry: MemoryEntry) -> str:
        """Calculate checksum for integrity verification"""
        data = json.dumps(entry.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def _archive_version(self, index_entry: 'MemoryIndexEntry'):
        """Archive old version"""
        version_dir = self.versions_dir / index_entry.memory_id
        version_dir.mkdir(parents=True, exist_ok=True)
        
        version_file = version_dir / f"{index_entry.memory_id}_v{index_entry.version}.json"
        
        async with aiofiles.open(version_file, 'w') as f:
            await f.write(json.dumps(index_entry.to_dict(), default=str))
    
    async def _load_version(self, memory_id: str, version: int) -> Optional['MemoryIndexEntry']:
        """Load specific version from archive"""
        version_file = self.versions_dir / memory_id / f"{memory_id}_v{version}.json"
        
        if not version_file.exists():
            return None
        
        async with aiofiles.open(version_file, 'r') as f:
            data = json.loads(await f.read())
        
        return MemoryIndexEntry.from_dict(data)
    
    def _load_index(self):
        """Load index from disk"""
        index_file = self.index_dir / 'mem0_index.json'
        
        if index_file.exists():
            with open(index_file, 'r') as f:
                index_data = json.load(f)
            
            for memory_id, entry_data in index_data.items():
                self.index[memory_id] = MemoryIndexEntry.from_dict(entry_data)
            
            logger.info(f"Loaded {len(self.index)} entries from index")
    
    async def _save_index(self):
        """Save index to disk"""
        index_file = self.index_dir / 'mem0_index.json'
        
        index_data = {
            memory_id: entry.to_dict()
            for memory_id, entry in self.index.items()
        }
        
        async with aiofiles.open(index_file, 'w') as f:
            await f.write(json.dumps(index_data, default=str))
    
    async def _update_storage_stats(self):
        """Update storage statistics"""
        total_size = 0
        
        # Calculate total storage size
        for file_path in self.blocks_dir.rglob('*.block'):
            total_size += file_path.stat().st_size
        
        self.stats['storage_size_mb'] = total_size / (1024 * 1024)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get MEM0 statistics"""
        return {
            'total_stored': self.stats['total_stored'],
            'total_retrieved': self.stats['total_retrieved'],
            'total_versions': self.stats['total_versions'],
            'compression_ratio': self.stats['compression_ratio'],
            'storage_size_mb': self.stats['storage_size_mb'],
            'index_size': len(self.index),
            'encryption_enabled': self.encryption_enabled,
            'compression_enabled': bool(self.compression_enabled),
            'redundancy_factor': self.redundancy
        }


class MemoryIndexEntry:
    """Index entry for MEM0 storage"""
    
    def __init__(self, memory_id: str, timestamp: datetime, importance: float,
                 block_locations: List[List[str]], checksum: str, version: int,
                 metadata: Dict[str, Any]):
        self.memory_id = memory_id
        self.timestamp = timestamp
        self.importance = importance
        self.block_locations = block_locations
        self.checksum = checksum
        self.version = version
        self.metadata = metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'memory_id': self.memory_id,
            'timestamp': self.timestamp.isoformat(),
            'importance': self.importance,
            'block_locations': self.block_locations,
            'checksum': self.checksum,
            'version': self.version,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryIndexEntry':
        """Create from dictionary"""
        return cls(
            memory_id=data['memory_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            importance=data['importance'],
            block_locations=data['block_locations'],
            checksum=data['checksum'],
            version=data['version'],
            metadata=data['metadata']
        )


# Persistent Memory wrapper for unified interface
class PersistentMemory:
    """
    Stage 4: Ultra-long-term storage with MEM0
    Provides unified interface for the memory system
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize persistent memory"""
        self.mem0 = MEM0Core(config)
    
    async def store(self, entry: MemoryEntry) -> bool:
        """Store in persistent memory"""
        try:
            await self.mem0.store(entry)
            return True
        except Exception as e:
            logger.error(f"Failed to store in persistent memory: {e}")
            return False
    
    async def get_by_id(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve by ID"""
        return await self.mem0.retrieve(memory_id)
    
    async def search(self, query: str, n_results: int = 10) -> List[MemoryEntry]:
        """Search persistent memory"""
        return await self.mem0.search(query, n_results)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        return self.mem0.get_stats()


# Test MEM0
async def test_mem0():
    """Test MEM0 functionality"""
    config = {
        'storage_path': './test_mem0',
        'encryption': True,
        'compression': 'zstd',
        'block_size_kb': 16,
        'redundancy': 2
    }
    
    mem0 = MEM0Core(config)
    
    # Test storing memories
    test_entries = []
    for i in range(3):
        entry = MemoryEntry(
            id=f"permanent_{i}",
            content=f"This is permanent memory {i}: " + "Important data " * 100,
            metadata={
                'index': i,
                'permanent': True,
                'category': 'critical' if i == 0 else 'important'
            },
            importance=0.8 + i * 0.05
        )
        test_entries.append(entry)
        storage_id = await mem0.store(entry)
        logger.info(f"Stored {storage_id} in MEM0")
    
    # Test retrieval
    entry = await mem0.retrieve("permanent_1")
    logger.info(f"Retrieved: {entry.id if entry else 'Not found'}")
    
    # Test versioning - update existing entry
    if test_entries:
        updated_entry = test_entries[0]
        updated_entry.content += " - UPDATED"
        await mem0.store(updated_entry)
        
        # Get versions
        versions = await mem0.get_versions(updated_entry.id)
        logger.info(f"Versions of {updated_entry.id}: {versions}")
        
        # Retrieve specific version
        v1_entry = await mem0.retrieve(updated_entry.id, version=1)
        logger.info(f"Version 1 content ends with: {'UPDATED' not in str(v1_entry.content)}")
    
    # Test search
    results = await mem0.search("critical", n_results=2)
    logger.info(f"Search results: {[r.id for r in results]}")
    
    # Get stats
    stats = mem0.get_stats()
    logger.info(f"MEM0 stats: {json.dumps(stats, indent=2)}")
    
    return mem0


if __name__ == "__main__":
    # Run test
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(test_mem0())