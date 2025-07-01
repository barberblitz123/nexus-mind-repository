"""
NEXUS Database Production Layer
SQLAlchemy models, migrations, and optimized database operations
"""

import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Type, TypeVar
from contextlib import asynccontextmanager
import json
from decimal import Decimal

# Database dependencies
from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean, 
    DateTime, Text, JSON, ForeignKey, Index, UniqueConstraint,
    CheckConstraint, event, pool, MetaData, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    relationship, sessionmaker, scoped_session, Session,
    selectinload, joinedload, subqueryload, raiseload
)
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY, ENUM
from sqlalchemy.sql import func
from sqlalchemy.pool import NullPool, QueuePool, StaticPool
import asyncpg
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations
import uuid

# Monitoring
from prometheus_client import Counter, Histogram, Gauge
import time

# Type hints
T = TypeVar('T')

# Configure logging
logger = logging.getLogger(__name__)

# Metrics
db_query_duration = Histogram('nexus_db_query_duration_seconds', 'Database query duration', ['query_type'])
db_query_count = Counter('nexus_db_queries_total', 'Total database queries', ['query_type'])
db_error_count = Counter('nexus_db_errors_total', 'Database errors', ['error_type'])
db_connection_pool_size = Gauge('nexus_db_connection_pool_size', 'Database connection pool size')
db_active_connections = Gauge('nexus_db_active_connections', 'Active database connections')

# Base model
Base = declarative_base()

# Custom types
def generate_uuid():
    return str(uuid.uuid4())


class TimestampMixin:
    """Mixin for timestamp fields"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)


# Core Models
class User(Base, TimestampMixin, SoftDeleteMixin):
    """User model with comprehensive fields"""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(String(50), default='user', nullable=False)
    preferences = Column(JSONB, default={})
    metadata = Column(JSONB, default={})
    last_login_at = Column(DateTime(timezone=True))
    login_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    activities = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_users_email_active', 'email', 'is_active'),
        Index('idx_users_role', 'role'),
        CheckConstraint("email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$'", name='valid_email'),
    )


class Project(Base, TimestampMixin, SoftDeleteMixin):
    """Project model for NEXUS projects"""
    __tablename__ = 'projects'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    status = Column(String(50), default='active', nullable=False)
    visibility = Column(String(50), default='private', nullable=False)
    settings = Column(JSONB, default={})
    tags = Column(ARRAY(String), default=[])
    star_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    components = relationship("Component", back_populates="project", cascade="all, delete-orphan")
    deployments = relationship("Deployment", back_populates="project", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_projects_owner_status', 'owner_id', 'status'),
        Index('idx_projects_visibility', 'visibility'),
        Index('idx_projects_tags', 'tags', postgresql_using='gin'),
        UniqueConstraint('owner_id', 'name', name='unique_project_name_per_owner'),
    )


class Component(Base, TimestampMixin):
    """Component model for project components"""
    __tablename__ = 'components'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    version = Column(String(50), default='1.0.0', nullable=False)
    configuration = Column(JSONB, default={})
    dependencies = Column(JSONB, default=[])
    status = Column(String(50), default='active', nullable=False)
    metrics = Column(JSONB, default={})
    
    # Relationships
    project = relationship("Project", back_populates="components")
    
    # Indexes
    __table_args__ = (
        Index('idx_components_project_type', 'project_id', 'type'),
        Index('idx_components_status', 'status'),
        UniqueConstraint('project_id', 'name', name='unique_component_name_per_project'),
    )


class Deployment(Base, TimestampMixin):
    """Deployment model for tracking deployments"""
    __tablename__ = 'deployments'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    environment = Column(String(50), nullable=False)
    version = Column(String(50), nullable=False)
    status = Column(String(50), default='pending', nullable=False)
    deployed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    deployed_at = Column(DateTime(timezone=True))
    rollback_to = Column(UUID(as_uuid=True), ForeignKey('deployments.id'), nullable=True)
    configuration = Column(JSONB, default={})
    logs = Column(JSONB, default=[])
    
    # Relationships
    project = relationship("Project", back_populates="deployments")
    deployer = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_deployments_project_env', 'project_id', 'environment'),
        Index('idx_deployments_status', 'status'),
        Index('idx_deployments_deployed_at', 'deployed_at'),
    )


class ActivityLog(Base, TimestampMixin):
    """Activity logging for audit trail"""
    __tablename__ = 'activity_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(255), nullable=False)
    details = Column(JSONB, default={})
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="activities")
    
    # Indexes
    __table_args__ = (
        Index('idx_activity_logs_user_action', 'user_id', 'action'),
        Index('idx_activity_logs_resource', 'resource_type', 'resource_id'),
        Index('idx_activity_logs_created_at', 'created_at'),
    )


class UserSession(Base, TimestampMixin):
    """User session tracking"""
    __tablename__ = 'user_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_sessions_expires', 'expires_at'),
        Index('idx_user_sessions_active', 'is_active'),
    )


class CacheEntry(Base, TimestampMixin):
    """Database-backed cache for fallback"""
    __tablename__ = 'cache_entries'
    
    key = Column(String(255), primary_key=True)
    value = Column(JSONB, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    tags = Column(ARRAY(String), default=[])
    
    # Indexes
    __table_args__ = (
        Index('idx_cache_entries_tags', 'tags', postgresql_using='gin'),
    )


class DatabaseManager:
    """Production database manager with connection pooling and monitoring"""
    
    def __init__(self, config):
        self.config = config
        self.engine = None
        self.async_engine = None
        self.session_factory = None
        self.async_session_factory = None
        self._read_replicas = []
        self._connection_semaphore = asyncio.Semaphore(config.DB_MAX_CONNECTIONS)
    
    async def initialize(self):
        """Initialize database connections and run migrations"""
        # Create main engine
        self.async_engine = create_async_engine(
            self.config.DATABASE_URL,
            echo=self.config.DB_ECHO,
            pool_size=self.config.DB_POOL_SIZE,
            max_overflow=self.config.DB_MAX_OVERFLOW,
            pool_timeout=self.config.DB_POOL_TIMEOUT,
            pool_recycle=self.config.DB_POOL_RECYCLE,
            pool_pre_ping=True,
            connect_args={
                "server_settings": {
                    "application_name": "nexus-core",
                    "jit": "off"
                },
                "command_timeout": 60,
                "prepared_statement_cache_size": 0,
                "prepared_statement_name_func": lambda idx: f"__asyncpg_{idx}__"
            }
        )
        
        # Create session factory
        self.async_session_factory = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Initialize read replicas
        if self.config.DB_READ_REPLICAS:
            await self._init_read_replicas()
        
        # Run migrations
        await self.run_migrations()
        
        # Register event listeners
        self._register_event_listeners()
        
        logger.info("Database initialized successfully")
    
    async def _init_read_replicas(self):
        """Initialize read replica connections"""
        for replica_url in self.config.DB_READ_REPLICAS:
            try:
                replica_engine = create_async_engine(
                    replica_url,
                    echo=False,
                    pool_size=self.config.DB_POOL_SIZE // 2,
                    max_overflow=self.config.DB_MAX_OVERFLOW // 2,
                    pool_timeout=self.config.DB_POOL_TIMEOUT,
                    pool_recycle=self.config.DB_POOL_RECYCLE,
                    pool_pre_ping=True
                )
                self._read_replicas.append(replica_engine)
                logger.info(f"Read replica initialized: {replica_url}")
            except Exception as e:
                logger.error(f"Failed to initialize read replica {replica_url}: {e}")
    
    def _register_event_listeners(self):
        """Register SQLAlchemy event listeners for monitoring"""
        @event.listens_for(self.async_engine.sync_engine, "before_execute")
        def receive_before_execute(conn, clauseelement, multiparams, params, execution_options):
            conn.info.setdefault('query_start_time', []).append(time.time())
        
        @event.listens_for(self.async_engine.sync_engine, "after_execute")
        def receive_after_execute(conn, clauseelement, multiparams, params, execution_options, result):
            total_time = time.time() - conn.info['query_start_time'].pop(-1)
            db_query_duration.labels(query_type=type(clauseelement).__name__).observe(total_time)
            db_query_count.labels(query_type=type(clauseelement).__name__).inc()
    
    @asynccontextmanager
    async def get_session(self, read_only: bool = False) -> AsyncSession:
        """Get database session with connection management"""
        async with self._connection_semaphore:
            if read_only and self._read_replicas:
                # Use read replica for read-only queries
                engine = self._read_replicas[hash(asyncio.current_task()) % len(self._read_replicas)]
                async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as session:
                    yield session
            else:
                # Use main connection
                async with self.async_session_factory() as session:
                    yield session
    
    async def execute_query(self, query, params=None, read_only=True):
        """Execute raw SQL query with monitoring"""
        async with self.get_session(read_only=read_only) as session:
            try:
                result = await session.execute(query, params or {})
                if not read_only:
                    await session.commit()
                return result
            except Exception as e:
                db_error_count.labels(error_type=type(e).__name__).inc()
                if not read_only:
                    await session.rollback()
                raise
    
    async def bulk_insert(self, model: Type[T], records: List[Dict[str, Any]]) -> List[T]:
        """Bulk insert with optimizations"""
        async with self.get_session(read_only=False) as session:
            try:
                # Use PostgreSQL COPY for large datasets
                if len(records) > 1000:
                    return await self._bulk_copy(session, model, records)
                else:
                    # Use regular bulk insert
                    instances = [model(**record) for record in records]
                    session.add_all(instances)
                    await session.commit()
                    return instances
            except Exception as e:
                await session.rollback()
                db_error_count.labels(error_type='bulk_insert_error').inc()
                raise
    
    async def _bulk_copy(self, session: AsyncSession, model: Type[T], records: List[Dict[str, Any]]) -> List[T]:
        """Use PostgreSQL COPY for efficient bulk insert"""
        # Implementation of COPY command for bulk insert
        # This is a placeholder - actual implementation would use asyncpg's copy_records_to_table
        pass
    
    async def run_migrations(self):
        """Run Alembic migrations"""
        try:
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", self.config.DATABASE_URL)
            
            # Run migrations in a separate thread to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: command.upgrade(alembic_cfg, "head")
            )
            
            logger.info("Database migrations completed successfully")
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    async def backup_database(self, backup_path: str):
        """Create database backup"""
        try:
            # Use pg_dump for backup
            import subprocess
            
            # Parse database URL
            from urllib.parse import urlparse
            db_url = urlparse(self.config.DATABASE_URL)
            
            env = {
                'PGPASSWORD': db_url.password,
                'PGHOST': db_url.hostname,
                'PGPORT': str(db_url.port or 5432),
                'PGUSER': db_url.username,
                'PGDATABASE': db_url.path[1:]  # Remove leading slash
            }
            
            # Run pg_dump
            subprocess.run(
                ['pg_dump', '-Fc', '-f', backup_path],
                env={**os.environ, **env},
                check=True
            )
            
            logger.info(f"Database backup created: {backup_path}")
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise
    
    def get_pool_size(self) -> int:
        """Get current connection pool size"""
        if self.async_engine:
            return self.async_engine.pool.size()
        return 0
    
    async def close(self):
        """Close all database connections"""
        if self.async_engine:
            await self.async_engine.dispose()
        
        for replica in self._read_replicas:
            await replica.dispose()
        
        logger.info("Database connections closed")


# Query optimization helpers
class QueryOptimizer:
    """Helper class for query optimization"""
    
    @staticmethod
    def with_joined_load(query, *relationships):
        """Add joined loading for relationships"""
        for rel in relationships:
            query = query.options(joinedload(rel))
        return query
    
    @staticmethod
    def with_subquery_load(query, *relationships):
        """Add subquery loading for relationships"""
        for rel in relationships:
            query = query.options(subqueryload(rel))
        return query
    
    @staticmethod
    def paginate(query, page: int, per_page: int):
        """Add pagination to query"""
        return query.limit(per_page).offset((page - 1) * per_page)
    
    @staticmethod
    def add_search_filter(query, model, search_term: str, fields: List[str]):
        """Add full-text search filter"""
        from sqlalchemy import or_
        
        filters = []
        for field in fields:
            column = getattr(model, field)
            filters.append(column.ilike(f'%{search_term}%'))
        
        return query.filter(or_(*filters))


# Repository pattern for common operations
class BaseRepository:
    """Base repository with common database operations"""
    
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get entity by ID"""
        result = await self.session.get(self.model, id)
        return result
    
    async def get_all(self, filters: Dict[str, Any] = None, 
                     page: int = 1, per_page: int = 50) -> List[T]:
        """Get all entities with optional filters and pagination"""
        from sqlalchemy import select
        
        query = select(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        query = QueryOptimizer.paginate(query, page, per_page)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def create(self, **kwargs) -> T:
        """Create new entity"""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance
    
    async def update(self, id: str, **kwargs) -> Optional[T]:
        """Update entity"""
        instance = await self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            await self.session.commit()
            await self.session.refresh(instance)
        
        return instance
    
    async def delete(self, id: str, soft: bool = True) -> bool:
        """Delete entity (soft delete by default)"""
        instance = await self.get_by_id(id)
        if instance:
            if soft and hasattr(instance, 'is_deleted'):
                instance.is_deleted = True
                instance.deleted_at = datetime.now(timezone.utc)
            else:
                await self.session.delete(instance)
            
            await self.session.commit()
            return True
        
        return False
    
    async def count(self, filters: Dict[str, Any] = None) -> int:
        """Count entities"""
        from sqlalchemy import select, func
        
        query = select(func.count()).select_from(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(query)
        return result.scalar()


# Async context manager for database sessions
@asynccontextmanager
async def get_db_session(db_manager: DatabaseManager, read_only: bool = False):
    """Get database session context manager"""
    async with db_manager.get_session(read_only=read_only) as session:
        try:
            yield session
            if not read_only:
                await session.commit()
        except Exception:
            if not read_only:
                await session.rollback()
            raise
        finally:
            await session.close()