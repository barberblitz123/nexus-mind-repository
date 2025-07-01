#!/usr/bin/env python3
"""
NEXUS Database Schema and Migration Scripts
Creates and manages all database tables for NEXUS 2.0 components
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('NEXUS-Migrations')


class NEXUSDatabaseManager:
    """Manages database schemas and migrations for NEXUS 2.0"""
    
    def __init__(self, base_path: str = "./nexus_data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # Database paths
        self.databases = {
            'episodic': self.base_path / 'nexus_episodic.db',
            'learning': self.base_path / 'nexus_learning.db',
            'goals': self.base_path / 'nexus_goals.db',
            'predictions': self.base_path / 'nexus_predictions.db',
            'orchestration': self.base_path / 'nexus_orchestration.db',
            'integration': self.base_path / 'nexus_integration.db'
        }
        
        # Migration history
        self.migration_history = self.base_path / 'migration_history.json'
        self.completed_migrations = self._load_migration_history()
    
    def _load_migration_history(self) -> Dict[str, List[str]]:
        """Load migration history"""
        if self.migration_history.exists():
            with open(self.migration_history, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_migration_history(self):
        """Save migration history"""
        with open(self.migration_history, 'w') as f:
            json.dump(self.completed_migrations, f, indent=2)
    
    def initialize_all_databases(self):
        """Initialize all database schemas"""
        logger.info("Initializing NEXUS 2.0 database schemas...")
        
        # Create schemas
        self._create_episodic_schema()
        self._create_learning_schema()
        self._create_goals_schema()
        self._create_predictions_schema()
        self._create_orchestration_schema()
        self._create_integration_schema()
        
        # Apply migrations
        self.apply_all_migrations()
        
        logger.info("Database initialization complete")
    
    def _create_episodic_schema(self):
        """Create enhanced episodic memory schema"""
        conn = sqlite3.connect(self.databases['episodic'])
        cursor = conn.cursor()
        
        # Enhanced episodic memories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS episodic_memories (
                id TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                content TEXT NOT NULL,
                metadata TEXT,
                importance REAL DEFAULT 0.5,
                emotional_valence REAL DEFAULT 0.0,
                arousal_level REAL DEFAULT 0.5,
                significance_score REAL DEFAULT 0.5,
                temporal_context TEXT,
                spatial_context TEXT,
                social_context TEXT,
                replay_count INTEGER DEFAULT 0,
                last_replayed DATETIME,
                consolidation_status TEXT DEFAULT 'pending',
                working_memory_ref TEXT,
                semantic_memory_ref TEXT,
                access_count INTEGER DEFAULT 0,
                last_accessed DATETIME,
                stage TEXT DEFAULT 'episodic',
                decay_factor REAL DEFAULT 1.0,
                created_by TEXT,
                tags TEXT
            )
        ''')
        
        # Memory relationships with types
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS episodic_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id_1 TEXT NOT NULL,
                memory_id_2 TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                strength REAL DEFAULT 0.5,
                bidirectional BOOLEAN DEFAULT TRUE,
                context TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_activated DATETIME,
                activation_count INTEGER DEFAULT 0,
                FOREIGN KEY (memory_id_1) REFERENCES episodic_memories(id),
                FOREIGN KEY (memory_id_2) REFERENCES episodic_memories(id)
            )
        ''')
        
        # Memory clusters for pattern detection
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_clusters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cluster_name TEXT NOT NULL,
                centroid_memory_id TEXT,
                member_count INTEGER DEFAULT 0,
                average_importance REAL DEFAULT 0.5,
                theme TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cluster_members (
                cluster_id INTEGER NOT NULL,
                memory_id TEXT NOT NULL,
                distance_to_centroid REAL DEFAULT 0.0,
                membership_strength REAL DEFAULT 1.0,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (cluster_id, memory_id),
                FOREIGN KEY (cluster_id) REFERENCES memory_clusters(id),
                FOREIGN KEY (memory_id) REFERENCES episodic_memories(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_temporal ON episodic_memories(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_significance ON episodic_memories(significance_score)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_importance ON episodic_memories(importance)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_consolidation ON episodic_memories(consolidation_status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags ON episodic_memories(tags)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_relationships ON episodic_relationships(memory_id_1, memory_id_2)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_relationship_type ON episodic_relationships(relationship_type)')
        
        conn.commit()
        conn.close()
        logger.info("Created episodic memory schema")
    
    def _create_learning_schema(self):
        """Create learning memory schema"""
        conn = sqlite3.connect(self.databases['learning'])
        cursor = conn.cursor()
        
        # Learning patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learnings (
                id TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                pattern TEXT NOT NULL,
                pattern_type TEXT,
                outcome TEXT NOT NULL,
                success_rate REAL DEFAULT 0.0,
                confidence REAL DEFAULT 0.0,
                application_count INTEGER DEFAULT 0,
                last_applied DATETIME,
                context_requirements TEXT,
                prerequisites TEXT,
                metadata TEXT,
                source_memories TEXT,
                created_by TEXT,
                tags TEXT
            )
        ''')
        
        # Learning applications tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learning_id TEXT NOT NULL,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                context TEXT,
                input_data TEXT,
                output_result TEXT,
                success BOOLEAN DEFAULT FALSE,
                performance_metrics TEXT,
                feedback TEXT,
                FOREIGN KEY (learning_id) REFERENCES learnings(id)
            )
        ''')
        
        # Learning evolution tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_evolution (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learning_id TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                evolution_type TEXT,
                changes TEXT,
                reason TEXT,
                performance_before REAL,
                performance_after REAL,
                evolved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (learning_id) REFERENCES learnings(id)
            )
        ''')
        
        # Learning relationships
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learning_id TEXT NOT NULL,
                related_memory_id TEXT NOT NULL,
                relationship_type TEXT,
                strength REAL DEFAULT 0.5,
                evidence_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (learning_id) REFERENCES learnings(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_pattern_type ON learnings(pattern_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_success ON learnings(success_rate)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_confidence ON learnings(confidence)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_tags ON learnings(tags)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_application_success ON learning_applications(success)')
        
        conn.commit()
        conn.close()
        logger.info("Created learning memory schema")
    
    def _create_goals_schema(self):
        """Create goals and objectives schema"""
        conn = sqlite3.connect(self.databases['goals'])
        cursor = conn.cursor()
        
        # Goals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                goal_description TEXT NOT NULL,
                goal_type TEXT,
                priority REAL DEFAULT 0.5,
                urgency REAL DEFAULT 0.5,
                importance REAL DEFAULT 0.5,
                status TEXT DEFAULT 'active',
                progress REAL DEFAULT 0.0,
                start_date DATETIME,
                deadline DATETIME,
                completion_date DATETIME,
                parent_goal_id TEXT,
                dependencies TEXT,
                success_criteria TEXT,
                resources_required TEXT,
                estimated_effort_hours REAL,
                actual_effort_hours REAL,
                created_by TEXT,
                assigned_to TEXT,
                metadata TEXT,
                tags TEXT,
                FOREIGN KEY (parent_goal_id) REFERENCES goals(id)
            )
        ''')
        
        # Goal steps/milestones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goal_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id TEXT NOT NULL,
                step_description TEXT NOT NULL,
                step_type TEXT,
                completed BOOLEAN DEFAULT FALSE,
                completion_date DATETIME,
                order_index INTEGER,
                estimated_hours REAL,
                actual_hours REAL,
                blockers TEXT,
                metadata TEXT,
                FOREIGN KEY (goal_id) REFERENCES goals(id)
            )
        ''')
        
        # Goal progress tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goal_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                progress_value REAL NOT NULL,
                progress_type TEXT,
                description TEXT,
                evidence TEXT,
                recorded_by TEXT,
                FOREIGN KEY (goal_id) REFERENCES goals(id)
            )
        ''')
        
        # Goal outcomes and learnings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goal_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id TEXT NOT NULL,
                outcome_type TEXT,
                outcome_description TEXT,
                success_level REAL DEFAULT 0.5,
                learnings TEXT,
                recommendations TEXT,
                impact_assessment TEXT,
                recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES goals(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_goal_status ON goals(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_goal_priority ON goals(priority)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_goal_deadline ON goals(deadline)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_goal_parent ON goals(parent_goal_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_goal_tags ON goals(tags)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_step_completed ON goal_steps(completed)')
        
        conn.commit()
        conn.close()
        logger.info("Created goals schema")
    
    def _create_predictions_schema(self):
        """Create predictions and forecasting schema"""
        conn = sqlite3.connect(self.databases['predictions'])
        cursor = conn.cursor()
        
        # Predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                prediction_type TEXT NOT NULL,
                prediction_target TEXT NOT NULL,
                prediction_value TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                time_horizon TEXT,
                predicted_for DATETIME,
                basis TEXT,
                model_used TEXT,
                input_features TEXT,
                uncertainty_range TEXT,
                created_by TEXT,
                status TEXT DEFAULT 'pending',
                metadata TEXT
            )
        ''')
        
        # Prediction validations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prediction_validations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id TEXT NOT NULL,
                validation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                actual_value TEXT,
                accuracy_score REAL,
                error_analysis TEXT,
                lessons_learned TEXT,
                FOREIGN KEY (prediction_id) REFERENCES predictions(id)
            )
        ''')
        
        # Predictive models
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictive_models (
                id TEXT PRIMARY KEY,
                model_name TEXT NOT NULL,
                model_type TEXT,
                target_domain TEXT,
                accuracy_history TEXT,
                parameters TEXT,
                training_data_ref TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME,
                version INTEGER DEFAULT 1,
                performance_metrics TEXT
            )
        ''')
        
        # Task predictions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_predictions (
                id TEXT PRIMARY KEY,
                task_description TEXT NOT NULL,
                predicted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                confidence REAL DEFAULT 0.5,
                estimated_duration_minutes INTEGER,
                prerequisites TEXT,
                expected_outcome TEXT,
                rationale TEXT,
                priority_score REAL DEFAULT 0.5,
                execution_window TEXT,
                status TEXT DEFAULT 'pending',
                metadata TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prediction_type ON predictions(prediction_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prediction_confidence ON predictions(confidence)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prediction_status ON predictions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prediction_target ON predictions(prediction_target)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_pred_confidence ON task_predictions(confidence)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_pred_priority ON task_predictions(priority_score)')
        
        conn.commit()
        conn.close()
        logger.info("Created predictions schema")
    
    def _create_orchestration_schema(self):
        """Create orchestration and resource management schema"""
        conn = sqlite3.connect(self.databases['orchestration'])
        cursor = conn.cursor()
        
        # Component registry
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS components (
                id TEXT PRIMARY KEY,
                component_name TEXT NOT NULL UNIQUE,
                component_type TEXT NOT NULL,
                status TEXT DEFAULT 'registered',
                health_score REAL DEFAULT 1.0,
                capabilities TEXT,
                dependencies TEXT,
                resource_limits TEXT,
                configuration TEXT,
                registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_heartbeat DATETIME,
                metadata TEXT
            )
        ''')
        
        # Resource allocations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resource_allocations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_id TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                allocated_amount REAL NOT NULL,
                limit_amount REAL,
                allocation_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                expiry_time DATETIME,
                priority INTEGER DEFAULT 5,
                metadata TEXT,
                FOREIGN KEY (component_id) REFERENCES components(id)
            )
        ''')
        
        # Task executions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_executions (
                id TEXT PRIMARY KEY,
                component_id TEXT NOT NULL,
                method_name TEXT NOT NULL,
                arguments TEXT,
                priority INTEGER DEFAULT 5,
                status TEXT DEFAULT 'queued',
                result TEXT,
                error TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                started_at DATETIME,
                completed_at DATETIME,
                retry_count INTEGER DEFAULT 0,
                timeout_seconds INTEGER,
                metadata TEXT,
                FOREIGN KEY (component_id) REFERENCES components(id)
            )
        ''')
        
        # Performance metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_id TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                metric_value REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                aggregation_period TEXT,
                metadata TEXT,
                FOREIGN KEY (component_id) REFERENCES components(id)
            )
        ''')
        
        # System optimizations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_optimizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                optimization_type TEXT NOT NULL,
                target_components TEXT,
                optimization_details TEXT,
                expected_improvement REAL,
                actual_improvement REAL,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                rollback_data TEXT,
                metadata TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_component_status ON components(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_component_type ON components(component_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_resource_component ON resource_allocations(component_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_resource_type ON resource_allocations(resource_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_status ON task_executions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_component ON task_executions(component_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metric_component ON performance_metrics(component_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metric_type ON performance_metrics(metric_type)')
        
        conn.commit()
        conn.close()
        logger.info("Created orchestration schema")
    
    def _create_integration_schema(self):
        """Create integration hub schema"""
        conn = sqlite3.connect(self.databases['integration'])
        cursor = conn.cursor()
        
        # Event store
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                source TEXT NOT NULL,
                data TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                processed BOOLEAN DEFAULT FALSE,
                processing_results TEXT
            )
        ''')
        
        # Event subscriptions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscriber_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                filter_criteria TEXT,
                callback_endpoint TEXT,
                active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_triggered DATETIME
            )
        ''')
        
        # State snapshots
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS state_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_id TEXT NOT NULL,
                state_data TEXT NOT NULL,
                version INTEGER NOT NULL,
                checksum TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        # Transactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                operations TEXT NOT NULL,
                participants TEXT NOT NULL,
                state TEXT DEFAULT 'pending',
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                end_time DATETIME,
                rollback_data TEXT,
                error_message TEXT,
                metadata TEXT
            )
        ''')
        
        # Transaction logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transaction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL,
                operation_index INTEGER NOT NULL,
                component_id TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                operation_data TEXT,
                status TEXT DEFAULT 'pending',
                executed_at DATETIME,
                result TEXT,
                FOREIGN KEY (transaction_id) REFERENCES transactions(id)
            )
        ''')
        
        # API access logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                request_data TEXT,
                response_data TEXT,
                status_code INTEGER,
                client_info TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                duration_ms INTEGER
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_source ON events(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_timestamp ON events(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscription_type ON event_subscriptions(event_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_state_component ON state_snapshots(component_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_state_version ON state_snapshots(version)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transaction_state ON transactions(state)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transaction_log ON transaction_logs(transaction_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_endpoint ON api_access_logs(endpoint)')
        
        conn.commit()
        conn.close()
        logger.info("Created integration schema")
    
    def apply_all_migrations(self):
        """Apply all pending migrations"""
        migrations = [
            ('add_context_memory', self._migration_add_context_memory),
            ('add_collaborative_memory', self._migration_add_collaborative_memory),
            ('add_memory_fusion', self._migration_add_memory_fusion),
            ('add_temporal_decay', self._migration_add_temporal_decay),
            ('add_unified_indexing', self._migration_add_unified_indexing),
            ('optimize_indexes', self._migration_optimize_indexes)
        ]
        
        for migration_name, migration_func in migrations:
            if migration_name not in self.completed_migrations.get('all', []):
                logger.info(f"Applying migration: {migration_name}")
                try:
                    migration_func()
                    
                    # Record migration
                    if 'all' not in self.completed_migrations:
                        self.completed_migrations['all'] = []
                    self.completed_migrations['all'].append(migration_name)
                    self._save_migration_history()
                    
                    logger.info(f"Migration {migration_name} completed")
                except Exception as e:
                    logger.error(f"Migration {migration_name} failed: {e}")
                    raise
    
    def _migration_add_context_memory(self):
        """Add context memory tables"""
        conn = sqlite3.connect(self.databases['episodic'])
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS context_memories (
                id TEXT PRIMARY KEY,
                context_type TEXT NOT NULL,
                context_data TEXT NOT NULL,
                active BOOLEAN DEFAULT TRUE,
                priority REAL DEFAULT 0.5,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                expiry_time DATETIME,
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS context_switches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_context_id TEXT,
                to_context_id TEXT NOT NULL,
                switch_reason TEXT,
                switch_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (to_context_id) REFERENCES context_memories(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _migration_add_collaborative_memory(self):
        """Add collaborative memory tables"""
        conn = sqlite3.connect(self.databases['integration'])
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collaborative_memories (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                memory_content TEXT NOT NULL,
                shared BOOLEAN DEFAULT FALSE,
                share_level TEXT DEFAULT 'private',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_accessed DATETIME,
                access_count INTEGER DEFAULT 0,
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_sharing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id TEXT NOT NULL,
                shared_with TEXT NOT NULL,
                share_type TEXT DEFAULT 'read',
                shared_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expiry_time DATETIME,
                access_count INTEGER DEFAULT 0,
                FOREIGN KEY (memory_id) REFERENCES collaborative_memories(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _migration_add_memory_fusion(self):
        """Add memory fusion tracking"""
        conn = sqlite3.connect(self.databases['episodic'])
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_fusions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fusion_query TEXT NOT NULL,
                memory_types TEXT NOT NULL,
                fusion_results TEXT,
                insights TEXT,
                fusion_score REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fusion_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT NOT NULL,
                pattern_description TEXT,
                memory_type_combination TEXT,
                success_rate REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _migration_add_temporal_decay(self):
        """Add temporal decay tracking"""
        # This migration updates existing tables to support decay
        for db_name in ['episodic', 'learning']:
            conn = sqlite3.connect(self.databases[db_name])
            cursor = conn.cursor()
            
            # Check if decay_factor column exists
            cursor.execute(f"PRAGMA table_info({db_name}_memories)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'decay_factor' not in columns and db_name == 'episodic':
                cursor.execute('''
                    ALTER TABLE episodic_memories 
                    ADD COLUMN decay_factor REAL DEFAULT 1.0
                ''')
            
            # Add decay tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS decay_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_id TEXT NOT NULL,
                    original_importance REAL NOT NULL,
                    current_importance REAL NOT NULL,
                    decay_applied REAL NOT NULL,
                    decay_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    decay_reason TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
    
    def _migration_add_unified_indexing(self):
        """Add unified indexing across all memory types"""
        conn = sqlite3.connect(self.databases['integration'])
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unified_memory_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                database_name TEXT NOT NULL,
                content_hash TEXT,
                importance REAL DEFAULT 0.5,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_accessed DATETIME,
                access_count INTEGER DEFAULT 0,
                tags TEXT,
                search_vector TEXT
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_unified_memory_id ON unified_memory_index(memory_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_unified_type ON unified_memory_index(memory_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_unified_importance ON unified_memory_index(importance)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_unified_hash ON unified_memory_index(content_hash)')
        
        conn.commit()
        conn.close()
    
    def _migration_optimize_indexes(self):
        """Optimize database indexes for performance"""
        for db_name, db_path in self.databases.items():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Analyze database
            cursor.execute('ANALYZE')
            
            # Vacuum to optimize storage
            cursor.execute('VACUUM')
            
            conn.commit()
            conn.close()
            
            logger.info(f"Optimized indexes for {db_name} database")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics for all databases"""
        stats = {}
        
        for db_name, db_path in self.databases.items():
            if db_path.exists():
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get table statistics
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                table_stats = {}
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    table_stats[table_name] = count
                
                # Get database size
                db_size = db_path.stat().st_size / (1024 * 1024)  # MB
                
                stats[db_name] = {
                    'tables': table_stats,
                    'size_mb': round(db_size, 2),
                    'path': str(db_path)
                }
                
                conn.close()
        
        return stats
    
    def backup_databases(self, backup_dir: Optional[str] = None):
        """Backup all databases"""
        if not backup_dir:
            backup_dir = self.base_path / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = Path(backup_dir)
        backup_path.mkdir(exist_ok=True)
        
        for db_name, db_path in self.databases.items():
            if db_path.exists():
                import shutil
                backup_file = backup_path / db_path.name
                shutil.copy2(db_path, backup_file)
                logger.info(f"Backed up {db_name} to {backup_file}")
        
        # Backup migration history
        if self.migration_history.exists():
            import shutil
            shutil.copy2(self.migration_history, backup_path / self.migration_history.name)
        
        logger.info(f"Database backup completed to {backup_path}")
        return str(backup_path)


# Migration execution script
def main():
    """Main migration execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NEXUS Database Migration Tool')
    parser.add_argument('--init', action='store_true', help='Initialize all databases')
    parser.add_argument('--migrate', action='store_true', help='Apply pending migrations')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--backup', action='store_true', help='Backup all databases')
    parser.add_argument('--path', default='./nexus_data', help='Base path for databases')
    
    args = parser.parse_args()
    
    # Create manager
    manager = NEXUSDatabaseManager(args.path)
    
    if args.init:
        manager.initialize_all_databases()
        print("Database initialization complete")
    
    if args.migrate:
        manager.apply_all_migrations()
        print("Migrations applied successfully")
    
    if args.stats:
        stats = manager.get_database_stats()
        print("\nDatabase Statistics:")
        print(json.dumps(stats, indent=2))
    
    if args.backup:
        backup_path = manager.backup_databases()
        print(f"Backup completed to: {backup_path}")
    
    if not any([args.init, args.migrate, args.stats, args.backup]):
        print("No action specified. Use --help for options.")


if __name__ == "__main__":
    main()