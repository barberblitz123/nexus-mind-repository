#!/usr/bin/env python3
"""
NEXUS Agent Registry
Dynamic agent discovery, capability management, and marketplace system
"""

import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading
import hashlib
import sqlite3
import pickle
import os
from packaging import version
import importlib.util
import inspect
import logging
from collections import defaultdict
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentVersion:
    """Semantic versioning for agents"""
    
    def __init__(self, version_str: str):
        self.version = version.parse(version_str)
        self.major = self.version.major
        self.minor = self.version.minor
        self.patch = self.version.micro
    
    def __str__(self):
        return str(self.version)
    
    def __lt__(self, other):
        return self.version < other.version
    
    def is_compatible(self, other: 'AgentVersion') -> bool:
        """Check if versions are compatible (same major version)"""
        return self.major == other.major


@dataclass
class AgentCapability:
    """Definition of an agent capability"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    required_resources: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class AgentImplementation:
    """Agent implementation details"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    capabilities: List[AgentCapability] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)
    source_path: Optional[str] = None
    container_image: Optional[str] = None
    entry_point: str = "main"
    configuration: Dict[str, Any] = field(default_factory=dict)
    performance_profile: Dict[str, float] = field(default_factory=dict)
    test_coverage: float = 0.0
    stability_score: float = 100.0
    usage_count: int = 0
    rating: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    deployment_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AgentDeployment:
    """Active agent deployment"""
    deployment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    implementation_id: str = ""
    instance_count: int = 1
    variant: str = "stable"  # stable, canary, experimental
    traffic_weight: float = 1.0
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    error_rate: float = 0.0
    success_rate: float = 100.0
    average_latency: float = 0.0
    deployed_at: datetime = field(default_factory=datetime.now)
    last_health_check: datetime = field(default_factory=datetime.now)


class AgentRegistry:
    """Central registry for agent management and discovery"""
    
    def __init__(self, db_path: str = "nexus_agent_registry.db"):
        self.db_path = db_path
        self.implementations: Dict[str, AgentImplementation] = {}
        self.deployments: Dict[str, List[AgentDeployment]] = defaultdict(list)
        self.capability_index: Dict[str, Set[str]] = defaultdict(set)  # capability -> implementation_ids
        self.version_history: Dict[str, List[AgentImplementation]] = defaultdict(list)
        self._lock = threading.RLock()
        
        # A/B testing configurations
        self.ab_tests: Dict[str, Dict[str, Any]] = {}
        
        # Performance benchmarks
        self.benchmarks: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Initialize database
        self._init_database()
        self._load_registry()
    
    def _init_database(self):
        """Initialize SQLite database for persistent storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS implementations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deployments (
                deployment_id TEXT PRIMARY KEY,
                implementation_id TEXT NOT NULL,
                data TEXT NOT NULL,
                deployed_at TIMESTAMP,
                FOREIGN KEY (implementation_id) REFERENCES implementations(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS benchmarks (
                implementation_id TEXT NOT NULL,
                capability TEXT NOT NULL,
                metric TEXT NOT NULL,
                value REAL NOT NULL,
                measured_at TIMESTAMP,
                PRIMARY KEY (implementation_id, capability, metric)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ab_tests (
                test_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                variants TEXT NOT NULL,
                config TEXT NOT NULL,
                created_at TIMESTAMP,
                status TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_registry(self):
        """Load registry from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Load implementations
        cursor.execute("SELECT id, data FROM implementations WHERE json_extract(data, '$.is_active') = 1")
        for row in cursor.fetchall():
            impl_data = json.loads(row[1])
            impl = self._dict_to_implementation(impl_data)
            self.implementations[impl.id] = impl
            self._index_implementation(impl)
        
        # Load deployments
        cursor.execute("SELECT deployment_id, implementation_id, data FROM deployments")
        for row in cursor.fetchall():
            deployment_data = json.loads(row[2])
            deployment = self._dict_to_deployment(deployment_data)
            self.deployments[row[1]].append(deployment)
        
        conn.close()
        logger.info(f"Loaded {len(self.implementations)} implementations from registry")
    
    def _dict_to_implementation(self, data: Dict) -> AgentImplementation:
        """Convert dictionary to AgentImplementation"""
        impl = AgentImplementation()
        for key, value in data.items():
            if hasattr(impl, key):
                if key in ['created_at', 'updated_at'] and isinstance(value, str):
                    value = datetime.fromisoformat(value)
                elif key == 'capabilities':
                    value = [AgentCapability(**cap) for cap in value]
                setattr(impl, key, value)
        return impl
    
    def _dict_to_deployment(self, data: Dict) -> AgentDeployment:
        """Convert dictionary to AgentDeployment"""
        deployment = AgentDeployment()
        for key, value in data.items():
            if hasattr(deployment, key):
                if key in ['deployed_at', 'last_health_check'] and isinstance(value, str):
                    value = datetime.fromisoformat(value)
                setattr(deployment, key, value)
        return deployment
    
    def _index_implementation(self, impl: AgentImplementation):
        """Index implementation for fast lookup"""
        for capability in impl.capabilities:
            self.capability_index[capability.name].add(impl.id)
        
        self.version_history[impl.name].append(impl)
        self.version_history[impl.name].sort(key=lambda x: AgentVersion(x.version), reverse=True)
    
    def register_implementation(self, impl: AgentImplementation) -> str:
        """Register a new agent implementation"""
        with self._lock:
            # Validate implementation
            if not self._validate_implementation(impl):
                raise ValueError("Invalid implementation")
            
            # Check for duplicate versions
            existing = self.get_implementation(impl.name, impl.version)
            if existing:
                raise ValueError(f"Implementation {impl.name} v{impl.version} already exists")
            
            # Store implementation
            impl.updated_at = datetime.now()
            self.implementations[impl.id] = impl
            self._index_implementation(impl)
            
            # Persist to database
            self._save_implementation(impl)
            
            logger.info(f"Registered implementation: {impl.name} v{impl.version}")
            return impl.id
    
    def _validate_implementation(self, impl: AgentImplementation) -> bool:
        """Validate agent implementation"""
        # Check required fields
        if not impl.name or not impl.version:
            return False
        
        # Validate version format
        try:
            AgentVersion(impl.version)
        except Exception:
            return False
        
        # Validate capabilities
        if not impl.capabilities:
            return False
        
        # Validate source or container
        if not impl.source_path and not impl.container_image:
            return False
        
        # If source path provided, validate it exists
        if impl.source_path and not os.path.exists(impl.source_path):
            return False
        
        return True
    
    def _save_implementation(self, impl: AgentImplementation):
        """Save implementation to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        impl_dict = asdict(impl)
        # Convert datetime objects to ISO format
        impl_dict['created_at'] = impl.created_at.isoformat()
        impl_dict['updated_at'] = impl.updated_at.isoformat()
        
        cursor.execute('''
            INSERT OR REPLACE INTO implementations (id, name, version, data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (impl.id, impl.name, impl.version, json.dumps(impl_dict), 
              impl.created_at, impl.updated_at))
        
        conn.commit()
        conn.close()
    
    def get_implementation(self, name: str, version: Optional[str] = None) -> Optional[AgentImplementation]:
        """Get specific implementation"""
        with self._lock:
            if version:
                # Get specific version
                for impl in self.version_history.get(name, []):
                    if impl.version == version and impl.is_active:
                        return impl
            else:
                # Get latest version
                versions = self.version_history.get(name, [])
                if versions:
                    return versions[0] if versions[0].is_active else None
            
            return None
    
    def discover_agents(self, capability: Optional[str] = None, 
                       tags: Optional[List[str]] = None) -> List[AgentImplementation]:
        """Discover agents by capability or tags"""
        with self._lock:
            results = []
            
            if capability:
                # Find by capability
                impl_ids = self.capability_index.get(capability, set())
                results = [self.implementations[impl_id] for impl_id in impl_ids 
                          if impl_id in self.implementations and self.implementations[impl_id].is_active]
            else:
                # Get all active implementations
                results = [impl for impl in self.implementations.values() if impl.is_active]
            
            # Filter by tags if specified
            if tags:
                results = [impl for impl in results 
                          if any(tag in sum([cap.tags for cap in impl.capabilities], []) 
                                for tag in tags)]
            
            # Sort by stability score and rating
            results.sort(key=lambda x: (x.stability_score * 0.7 + x.rating * 30), reverse=True)
            
            return results
    
    def deploy_agent(self, implementation_id: str, variant: str = "stable", 
                    instance_count: int = 1, traffic_weight: float = 1.0) -> str:
        """Deploy an agent implementation"""
        with self._lock:
            impl = self.implementations.get(implementation_id)
            if not impl:
                raise ValueError(f"Implementation {implementation_id} not found")
            
            deployment = AgentDeployment(
                implementation_id=implementation_id,
                instance_count=instance_count,
                variant=variant,
                traffic_weight=traffic_weight
            )
            
            self.deployments[implementation_id].append(deployment)
            self._save_deployment(deployment)
            
            # Update usage count
            impl.usage_count += 1
            self._save_implementation(impl)
            
            logger.info(f"Deployed {impl.name} v{impl.version} as {variant} with {instance_count} instances")
            return deployment.deployment_id
    
    def _save_deployment(self, deployment: AgentDeployment):
        """Save deployment to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        deployment_dict = asdict(deployment)
        deployment_dict['deployed_at'] = deployment.deployed_at.isoformat()
        deployment_dict['last_health_check'] = deployment.last_health_check.isoformat()
        
        cursor.execute('''
            INSERT OR REPLACE INTO deployments (deployment_id, implementation_id, data, deployed_at)
            VALUES (?, ?, ?, ?)
        ''', (deployment.deployment_id, deployment.implementation_id, 
              json.dumps(deployment_dict), deployment.deployed_at))
        
        conn.commit()
        conn.close()
    
    def create_ab_test(self, name: str, control_impl_id: str, 
                      variant_impl_ids: List[str], traffic_split: Dict[str, float]) -> str:
        """Create A/B test for agent algorithms"""
        with self._lock:
            test_id = str(uuid.uuid4())
            
            # Validate implementations exist
            all_impl_ids = [control_impl_id] + variant_impl_ids
            for impl_id in all_impl_ids:
                if impl_id not in self.implementations:
                    raise ValueError(f"Implementation {impl_id} not found")
            
            # Validate traffic split
            if abs(sum(traffic_split.values()) - 1.0) > 0.01:
                raise ValueError("Traffic split must sum to 1.0")
            
            ab_test = {
                'test_id': test_id,
                'name': name,
                'control': control_impl_id,
                'variants': variant_impl_ids,
                'traffic_split': traffic_split,
                'created_at': datetime.now(),
                'status': 'active',
                'metrics': defaultdict(lambda: defaultdict(float))
            }
            
            self.ab_tests[test_id] = ab_test
            self._save_ab_test(ab_test)
            
            # Deploy variants
            for impl_id, weight in traffic_split.items():
                self.deploy_agent(impl_id, variant='experimental', 
                                traffic_weight=weight)
            
            logger.info(f"Created A/B test '{name}' with {len(all_impl_ids)} variants")
            return test_id
    
    def _save_ab_test(self, ab_test: Dict):
        """Save A/B test to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO ab_tests (test_id, name, variants, config, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (ab_test['test_id'], ab_test['name'], 
              json.dumps(ab_test['variants']), json.dumps(ab_test),
              ab_test['created_at'], ab_test['status']))
        
        conn.commit()
        conn.close()
    
    def record_benchmark(self, implementation_id: str, capability: str, 
                        metrics: Dict[str, float]):
        """Record performance benchmark for an implementation"""
        with self._lock:
            impl = self.implementations.get(implementation_id)
            if not impl:
                raise ValueError(f"Implementation {implementation_id} not found")
            
            # Update benchmarks
            self.benchmarks[implementation_id][capability] = metrics
            
            # Update implementation performance profile
            impl.performance_profile.update(metrics)
            self._save_implementation(impl)
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for metric, value in metrics.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO benchmarks 
                    (implementation_id, capability, metric, value, measured_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (implementation_id, capability, metric, value, datetime.now()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded benchmark for {impl.name} - {capability}")
    
    def hot_swap_implementation(self, old_impl_id: str, new_impl_id: str, 
                               rollout_strategy: str = "gradual") -> bool:
        """Hot swap agent implementation without downtime"""
        with self._lock:
            old_impl = self.implementations.get(old_impl_id)
            new_impl = self.implementations.get(new_impl_id)
            
            if not old_impl or not new_impl:
                raise ValueError("Implementation not found")
            
            # Check compatibility
            old_version = AgentVersion(old_impl.version)
            new_version = AgentVersion(new_impl.version)
            
            if not new_version.is_compatible(old_version):
                logger.warning(f"Versions {old_version} and {new_version} may not be compatible")
            
            if rollout_strategy == "immediate":
                # Immediate swap
                self._perform_immediate_swap(old_impl_id, new_impl_id)
            elif rollout_strategy == "gradual":
                # Gradual rollout
                self._perform_gradual_swap(old_impl_id, new_impl_id)
            else:
                raise ValueError(f"Unknown rollout strategy: {rollout_strategy}")
            
            logger.info(f"Hot swapped {old_impl.name} v{old_impl.version} -> v{new_impl.version}")
            return True
    
    def _perform_immediate_swap(self, old_impl_id: str, new_impl_id: str):
        """Perform immediate implementation swap"""
        # Update all deployments
        old_deployments = self.deployments.get(old_impl_id, [])
        for deployment in old_deployments:
            # Create new deployment
            new_deployment = AgentDeployment(
                implementation_id=new_impl_id,
                instance_count=deployment.instance_count,
                variant=deployment.variant,
                traffic_weight=deployment.traffic_weight
            )
            self.deployments[new_impl_id].append(new_deployment)
            self._save_deployment(new_deployment)
        
        # Remove old deployments
        self.deployments[old_impl_id] = []
    
    def _perform_gradual_swap(self, old_impl_id: str, new_impl_id: str):
        """Perform gradual implementation swap"""
        # Start with 10% traffic to new implementation
        self.create_ab_test(
            name=f"swap_{old_impl_id}_to_{new_impl_id}",
            control_impl_id=old_impl_id,
            variant_impl_ids=[new_impl_id],
            traffic_split={old_impl_id: 0.9, new_impl_id: 0.1}
        )
    
    def get_marketplace_listings(self, category: Optional[str] = None,
                               sort_by: str = "rating") -> List[Dict[str, Any]]:
        """Get marketplace listings for agent extensions"""
        with self._lock:
            listings = []
            
            for impl in self.implementations.values():
                if not impl.is_active:
                    continue
                
                listing = {
                    'id': impl.id,
                    'name': impl.name,
                    'version': impl.version,
                    'author': impl.author,
                    'description': impl.description,
                    'rating': impl.rating,
                    'usage_count': impl.usage_count,
                    'stability_score': impl.stability_score,
                    'capabilities': [cap.name for cap in impl.capabilities],
                    'tags': sum([cap.tags for cap in impl.capabilities], []),
                    'created_at': impl.created_at.isoformat(),
                    'updated_at': impl.updated_at.isoformat()
                }
                
                listings.append(listing)
            
            # Sort listings
            if sort_by == "rating":
                listings.sort(key=lambda x: x['rating'], reverse=True)
            elif sort_by == "usage":
                listings.sort(key=lambda x: x['usage_count'], reverse=True)
            elif sort_by == "recent":
                listings.sort(key=lambda x: x['updated_at'], reverse=True)
            
            return listings
    
    def install_from_marketplace(self, listing_id: str) -> bool:
        """Install an agent from marketplace"""
        with self._lock:
            impl = self.implementations.get(listing_id)
            if not impl:
                raise ValueError(f"Listing {listing_id} not found")
            
            # Deploy the implementation
            deployment_id = self.deploy_agent(impl.id, variant="stable")
            
            logger.info(f"Installed {impl.name} v{impl.version} from marketplace")
            return True
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        with self._lock:
            total_implementations = len(self.implementations)
            active_implementations = sum(1 for impl in self.implementations.values() if impl.is_active)
            total_deployments = sum(len(deps) for deps in self.deployments.values())
            
            capability_counts = defaultdict(int)
            for impl_ids in self.capability_index.values():
                capability_counts[len(impl_ids)] += 1
            
            return {
                'total_implementations': total_implementations,
                'active_implementations': active_implementations,
                'total_deployments': total_deployments,
                'unique_agents': len(self.version_history),
                'active_ab_tests': sum(1 for test in self.ab_tests.values() if test['status'] == 'active'),
                'capability_coverage': len(self.capability_index),
                'average_stability_score': sum(impl.stability_score for impl in self.implementations.values()) / max(1, total_implementations),
                'average_rating': sum(impl.rating for impl in self.implementations.values()) / max(1, total_implementations)
            }


# Example usage
if __name__ == "__main__":
    # Create registry
    registry = AgentRegistry()
    
    # Create sample implementations
    analyzer_v1 = AgentImplementation(
        name="DataAnalyzer",
        version="1.0.0",
        author="NEXUS Team",
        description="Advanced data analysis agent",
        capabilities=[
            AgentCapability(
                name="statistical_analysis",
                description="Perform statistical analysis on datasets",
                input_schema={"data": "array", "method": "string"},
                output_schema={"results": "object", "confidence": "float"},
                tags=["analytics", "statistics"]
            ),
            AgentCapability(
                name="anomaly_detection",
                description="Detect anomalies in data",
                input_schema={"data": "array", "threshold": "float"},
                output_schema={"anomalies": "array", "score": "float"},
                tags=["analytics", "ml"]
            )
        ],
        source_path="/path/to/analyzer",
        performance_profile={"cpu_usage": 45.0, "memory_mb": 512},
        test_coverage=85.5,
        stability_score=95.0,
        rating=4.8
    )
    
    analyzer_v2 = AgentImplementation(
        name="DataAnalyzer",
        version="2.0.0",
        author="NEXUS Team",
        description="Advanced data analysis agent with ML capabilities",
        capabilities=[
            AgentCapability(
                name="statistical_analysis",
                description="Enhanced statistical analysis with ML",
                input_schema={"data": "array", "method": "string", "ml_enhanced": "boolean"},
                output_schema={"results": "object", "confidence": "float", "model_used": "string"},
                tags=["analytics", "statistics", "ml"]
            ),
            AgentCapability(
                name="predictive_modeling",
                description="Build predictive models",
                input_schema={"data": "array", "target": "string", "algorithm": "string"},
                output_schema={"model": "object", "accuracy": "float"},
                tags=["ml", "prediction"]
            )
        ],
        source_path="/path/to/analyzer_v2",
        performance_profile={"cpu_usage": 60.0, "memory_mb": 1024},
        test_coverage=92.0,
        stability_score=88.0,
        rating=4.5
    )
    
    # Register implementations
    impl1_id = registry.register_implementation(analyzer_v1)
    impl2_id = registry.register_implementation(analyzer_v2)
    
    # Discover agents
    print("\nDiscovering agents with 'statistical_analysis' capability:")
    agents = registry.discover_agents(capability="statistical_analysis")
    for agent in agents:
        print(f"  - {agent.name} v{agent.version} (stability: {agent.stability_score})")
    
    # Deploy agent
    deployment_id = registry.deploy_agent(impl1_id, variant="stable", instance_count=3)
    print(f"\nDeployed {analyzer_v1.name} with deployment ID: {deployment_id}")
    
    # Create A/B test
    ab_test_id = registry.create_ab_test(
        name="analyzer_ml_test",
        control_impl_id=impl1_id,
        variant_impl_ids=[impl2_id],
        traffic_split={impl1_id: 0.7, impl2_id: 0.3}
    )
    print(f"\nCreated A/B test: {ab_test_id}")
    
    # Record benchmarks
    registry.record_benchmark(impl1_id, "statistical_analysis", {
        "latency_ms": 125.5,
        "throughput_qps": 1000,
        "accuracy": 98.5
    })
    
    # Get marketplace listings
    print("\nMarketplace listings:")
    listings = registry.get_marketplace_listings(sort_by="rating")
    for listing in listings:
        print(f"  - {listing['name']} v{listing['version']} ⭐ {listing['rating']}")
    
    # Get registry stats
    stats = registry.get_registry_stats()
    print(f"\nRegistry Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")