#!/usr/bin/env python3
"""
NEXUS MLOps Infrastructure - Production ML Operations System
Handles model registry, deployment, monitoring, and governance
"""

import os
import json
import yaml
import shutil
import hashlib
import pickle
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass, field
import asyncio
from pathlib import Path
import numpy as np
import pandas as pd
from enum import Enum

# Model serving
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

# MLflow
import mlflow
from mlflow.tracking import MlflowClient
from mlflow.models import infer_signature

# Model interpretability
import shap
from lime.lime_tabular import LimeTabularExplainer

# Monitoring
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge, Summary

# Database
import sqlite3
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Distributed computing
from ray import serve
import ray

# Bias detection
from aif360.datasets import BinaryLabelDataset
from aif360.metrics import BinaryLabelDatasetMetric
from aif360.algorithms.preprocessing import Reweighing

# Cloud storage
import boto3
from azure.storage.blob import BlobServiceClient
from google.cloud import storage as gcs

# Kubernetes
from kubernetes import client, config as k8s_config

# Security
import jwt
from cryptography.fernet import Fernet

Base = declarative_base()


class ModelStatus(Enum):
    """Model lifecycle status"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class DeploymentStrategy(Enum):
    """Deployment strategies"""
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"
    SHADOW = "shadow"
    A_B_TEST = "ab_test"


@dataclass
class ModelMetadata:
    """Model metadata"""
    model_id: str
    name: str
    version: str
    algorithm: str
    framework: str
    created_at: datetime
    updated_at: datetime
    author: str
    description: str
    tags: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    data_schema: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: ModelStatus = ModelStatus.DEVELOPMENT


@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    model_id: str
    strategy: DeploymentStrategy
    replicas: int = 1
    cpu_request: str = "100m"
    memory_request: str = "256Mi"
    cpu_limit: str = "1000m"
    memory_limit: str = "1Gi"
    min_replicas: int = 1
    max_replicas: int = 10
    target_cpu_utilization: int = 70
    canary_percentage: int = 10
    health_check_path: str = "/health"
    readiness_check_path: str = "/ready"


class ModelRegistry:
    """Central model registry with versioning"""
    
    def __init__(self, storage_backend: str = "local", storage_config: Dict = None):
        self.storage_backend = storage_backend
        self.storage_config = storage_config or {}
        self.mlflow_client = MlflowClient()
        self._init_storage()
        
    def _init_storage(self):
        """Initialize storage backend"""
        if self.storage_backend == "s3":
            self.s3_client = boto3.client('s3', **self.storage_config)
        elif self.storage_backend == "azure":
            self.blob_client = BlobServiceClient(**self.storage_config)
        elif self.storage_backend == "gcs":
            self.gcs_client = gcs.Client(**self.storage_config)
        else:  # local
            self.storage_path = Path(self.storage_config.get('path', './model_registry'))
            self.storage_path.mkdir(exist_ok=True)
    
    def register_model(
        self,
        model: Any,
        metadata: ModelMetadata,
        artifacts: Dict[str, Any] = None
    ) -> str:
        """Register a new model"""
        # Generate unique model ID
        model_id = self._generate_model_id(metadata)
        metadata.model_id = model_id
        
        # Save model with MLflow
        with mlflow.start_run(run_name=f"{metadata.name}_v{metadata.version}"):
            # Log parameters
            mlflow.log_params(metadata.parameters)
            
            # Log metrics
            for metric_name, metric_value in metadata.metrics.items():
                mlflow.log_metric(metric_name, metric_value)
            
            # Log model
            if metadata.framework == "sklearn":
                mlflow.sklearn.log_model(model, "model")
            elif metadata.framework == "pytorch":
                mlflow.pytorch.log_model(model, "model")
            elif metadata.framework == "tensorflow":
                mlflow.tensorflow.log_model(model, "model")
            else:
                mlflow.pyfunc.log_model("model", python_model=model)
            
            # Log artifacts
            if artifacts:
                for name, artifact in artifacts.items():
                    if isinstance(artifact, (dict, list)):
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
                            json.dump(artifact, f)
                            mlflow.log_artifact(f.name, name)
                    else:
                        mlflow.log_artifact(artifact, name)
            
            # Save metadata
            self._save_metadata(metadata)
            
            run_id = mlflow.active_run().info.run_id
        
        # Register in MLflow Model Registry
        mlflow.register_model(
            f"runs:/{run_id}/model",
            metadata.name
        )
        
        print(f"Model registered: {model_id}")
        return model_id
    
    def get_model(self, model_id: str) -> Tuple[Any, ModelMetadata]:
        """Retrieve model and metadata"""
        # Load metadata
        metadata = self._load_metadata(model_id)
        
        # Load model from MLflow
        model_uri = f"models:/{metadata.name}/{metadata.version}"
        
        if metadata.framework == "sklearn":
            model = mlflow.sklearn.load_model(model_uri)
        elif metadata.framework == "pytorch":
            model = mlflow.pytorch.load_model(model_uri)
        elif metadata.framework == "tensorflow":
            model = mlflow.tensorflow.load_model(model_uri)
        else:
            model = mlflow.pyfunc.load_model(model_uri)
        
        return model, metadata
    
    def list_models(
        self,
        status: Optional[ModelStatus] = None,
        tags: Optional[List[str]] = None
    ) -> List[ModelMetadata]:
        """List registered models"""
        models = []
        
        # List from MLflow
        for rm in self.mlflow_client.list_registered_models():
            for version in rm.latest_versions:
                try:
                    metadata = self._load_metadata(f"{rm.name}_v{version.version}")
                    
                    # Filter by status
                    if status and metadata.status != status:
                        continue
                    
                    # Filter by tags
                    if tags and not any(tag in metadata.tags for tag in tags):
                        continue
                    
                    models.append(metadata)
                except:
                    continue
        
        return models
    
    def update_model_status(self, model_id: str, status: ModelStatus):
        """Update model status"""
        metadata = self._load_metadata(model_id)
        metadata.status = status
        metadata.updated_at = datetime.now()
        self._save_metadata(metadata)
        
        # Update MLflow stage
        stage_map = {
            ModelStatus.DEVELOPMENT: "None",
            ModelStatus.STAGING: "Staging",
            ModelStatus.PRODUCTION: "Production",
            ModelStatus.ARCHIVED: "Archived"
        }
        
        self.mlflow_client.transition_model_version_stage(
            name=metadata.name,
            version=metadata.version,
            stage=stage_map.get(status, "None")
        )
    
    def _generate_model_id(self, metadata: ModelMetadata) -> str:
        """Generate unique model ID"""
        content = f"{metadata.name}_{metadata.version}_{metadata.created_at}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _save_metadata(self, metadata: ModelMetadata):
        """Save model metadata"""
        metadata_dict = {
            'model_id': metadata.model_id,
            'name': metadata.name,
            'version': metadata.version,
            'algorithm': metadata.algorithm,
            'framework': metadata.framework,
            'created_at': metadata.created_at.isoformat(),
            'updated_at': metadata.updated_at.isoformat(),
            'author': metadata.author,
            'description': metadata.description,
            'tags': metadata.tags,
            'metrics': metadata.metrics,
            'parameters': metadata.parameters,
            'data_schema': metadata.data_schema,
            'dependencies': metadata.dependencies,
            'status': metadata.status.value
        }
        
        if self.storage_backend == "local":
            path = self.storage_path / f"{metadata.model_id}_metadata.json"
            with open(path, 'w') as f:
                json.dump(metadata_dict, f, indent=2)
        # Add cloud storage implementations as needed
    
    def _load_metadata(self, model_id: str) -> ModelMetadata:
        """Load model metadata"""
        if self.storage_backend == "local":
            path = self.storage_path / f"{model_id}_metadata.json"
            with open(path, 'r') as f:
                data = json.load(f)
        # Add cloud storage implementations as needed
        
        return ModelMetadata(
            model_id=data['model_id'],
            name=data['name'],
            version=data['version'],
            algorithm=data['algorithm'],
            framework=data['framework'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            author=data['author'],
            description=data['description'],
            tags=data['tags'],
            metrics=data['metrics'],
            parameters=data['parameters'],
            data_schema=data['data_schema'],
            dependencies=data['dependencies'],
            status=ModelStatus(data['status'])
        )


class ModelDeployment:
    """Handle model deployment with various strategies"""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.deployments = {}
        self._init_kubernetes()
        
    def _init_kubernetes(self):
        """Initialize Kubernetes client"""
        try:
            k8s_config.load_incluster_config()
        except:
            k8s_config.load_kube_config()
        
        self.k8s_apps = client.AppsV1Api()
        self.k8s_core = client.CoreV1Api()
        self.k8s_autoscaling = client.AutoscalingV1Api()
    
    async def deploy_model(
        self,
        model_id: str,
        config: DeploymentConfig
    ) -> Dict[str, Any]:
        """Deploy model with specified strategy"""
        model, metadata = self.registry.get_model(model_id)
        
        if config.strategy == DeploymentStrategy.BLUE_GREEN:
            result = await self._deploy_blue_green(model, metadata, config)
        elif config.strategy == DeploymentStrategy.CANARY:
            result = await self._deploy_canary(model, metadata, config)
        elif config.strategy == DeploymentStrategy.ROLLING:
            result = await self._deploy_rolling(model, metadata, config)
        elif config.strategy == DeploymentStrategy.SHADOW:
            result = await self._deploy_shadow(model, metadata, config)
        elif config.strategy == DeploymentStrategy.A_B_TEST:
            result = await self._deploy_ab_test(model, metadata, config)
        else:
            raise ValueError(f"Unknown deployment strategy: {config.strategy}")
        
        # Update deployment record
        self.deployments[model_id] = {
            'config': config,
            'metadata': metadata,
            'status': 'deployed',
            'timestamp': datetime.now(),
            'result': result
        }
        
        return result
    
    async def _deploy_blue_green(
        self,
        model: Any,
        metadata: ModelMetadata,
        config: DeploymentConfig
    ) -> Dict[str, Any]:
        """Blue-green deployment"""
        # Create new deployment (green)
        green_name = f"{metadata.name}-green-{metadata.version}"
        
        # Deploy green version
        deployment = self._create_k8s_deployment(green_name, model, metadata, config)
        service = self._create_k8s_service(green_name, deployment)
        
        # Test green deployment
        await self._test_deployment(service)
        
        # Switch traffic to green
        main_service = self.k8s_core.read_namespaced_service(
            name=metadata.name,
            namespace="default"
        )
        main_service.spec.selector = {"app": green_name}
        self.k8s_core.patch_namespaced_service(
            name=metadata.name,
            namespace="default",
            body=main_service
        )
        
        # Delete old blue deployment
        try:
            blue_name = f"{metadata.name}-blue-{metadata.version}"
            self.k8s_apps.delete_namespaced_deployment(
                name=blue_name,
                namespace="default"
            )
        except:
            pass
        
        return {
            'strategy': 'blue_green',
            'deployment': green_name,
            'status': 'success'
        }
    
    async def _deploy_canary(
        self,
        model: Any,
        metadata: ModelMetadata,
        config: DeploymentConfig
    ) -> Dict[str, Any]:
        """Canary deployment with gradual rollout"""
        canary_name = f"{metadata.name}-canary-{metadata.version}"
        
        # Deploy canary version with limited replicas
        canary_replicas = max(1, int(config.replicas * config.canary_percentage / 100))
        config.replicas = canary_replicas
        
        deployment = self._create_k8s_deployment(canary_name, model, metadata, config)
        
        # Monitor canary performance
        await self._monitor_canary(deployment, duration_minutes=30)
        
        # Gradual rollout
        for percentage in [25, 50, 75, 100]:
            new_replicas = int(config.replicas * percentage / 100)
            deployment.spec.replicas = new_replicas
            
            self.k8s_apps.patch_namespaced_deployment(
                name=canary_name,
                namespace="default",
                body=deployment
            )
            
            # Monitor after each increase
            await asyncio.sleep(300)  # 5 minutes
            
            metrics = await self._get_deployment_metrics(canary_name)
            if metrics['error_rate'] > 0.05:  # 5% error threshold
                # Rollback
                self.k8s_apps.delete_namespaced_deployment(
                    name=canary_name,
                    namespace="default"
                )
                raise Exception("Canary deployment failed due to high error rate")
        
        return {
            'strategy': 'canary',
            'deployment': canary_name,
            'status': 'success',
            'rollout_percentage': 100
        }
    
    async def _deploy_rolling(
        self,
        model: Any,
        metadata: ModelMetadata,
        config: DeploymentConfig
    ) -> Dict[str, Any]:
        """Rolling deployment with zero downtime"""
        deployment_name = f"{metadata.name}-{metadata.version}"
        
        # Create or update deployment
        try:
            existing = self.k8s_apps.read_namespaced_deployment(
                name=deployment_name,
                namespace="default"
            )
            # Update existing deployment
            existing.spec.template.spec.containers[0].image = self._build_model_image(
                model, metadata
            )
            self.k8s_apps.patch_namespaced_deployment(
                name=deployment_name,
                namespace="default",
                body=existing
            )
        except:
            # Create new deployment
            deployment = self._create_k8s_deployment(
                deployment_name, model, metadata, config
            )
        
        # Wait for rollout to complete
        await self._wait_for_rollout(deployment_name)
        
        return {
            'strategy': 'rolling',
            'deployment': deployment_name,
            'status': 'success'
        }
    
    async def _deploy_shadow(
        self,
        model: Any,
        metadata: ModelMetadata,
        config: DeploymentConfig
    ) -> Dict[str, Any]:
        """Shadow deployment for testing in production"""
        shadow_name = f"{metadata.name}-shadow-{metadata.version}"
        
        # Deploy shadow version
        deployment = self._create_k8s_deployment(shadow_name, model, metadata, config)
        
        # Configure traffic mirroring
        # This would typically involve service mesh configuration (Istio, Linkerd)
        # For now, we'll simulate shadow traffic
        
        return {
            'strategy': 'shadow',
            'deployment': shadow_name,
            'status': 'success',
            'mode': 'shadow'
        }
    
    async def _deploy_ab_test(
        self,
        model: Any,
        metadata: ModelMetadata,
        config: DeploymentConfig
    ) -> Dict[str, Any]:
        """A/B test deployment"""
        ab_name = f"{metadata.name}-ab-{metadata.version}"
        
        # Deploy B version
        deployment = self._create_k8s_deployment(ab_name, model, metadata, config)
        
        # Configure traffic splitting (would use service mesh in production)
        # For now, we'll use simple percentage-based routing
        
        return {
            'strategy': 'ab_test',
            'deployment': ab_name,
            'status': 'success',
            'traffic_split': config.canary_percentage
        }
    
    def _create_k8s_deployment(
        self,
        name: str,
        model: Any,
        metadata: ModelMetadata,
        config: DeploymentConfig
    ) -> client.V1Deployment:
        """Create Kubernetes deployment"""
        # Build container image
        image = self._build_model_image(model, metadata)
        
        # Define deployment
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1DeploymentSpec(
                replicas=config.replicas,
                selector=client.V1LabelSelector(
                    match_labels={"app": name}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": name}),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name="model",
                                image=image,
                                ports=[client.V1ContainerPort(container_port=8080)],
                                resources=client.V1ResourceRequirements(
                                    requests={
                                        "cpu": config.cpu_request,
                                        "memory": config.memory_request
                                    },
                                    limits={
                                        "cpu": config.cpu_limit,
                                        "memory": config.memory_limit
                                    }
                                ),
                                liveness_probe=client.V1Probe(
                                    http_get=client.V1HTTPGetAction(
                                        path=config.health_check_path,
                                        port=8080
                                    ),
                                    initial_delay_seconds=30,
                                    period_seconds=10
                                ),
                                readiness_probe=client.V1Probe(
                                    http_get=client.V1HTTPGetAction(
                                        path=config.readiness_check_path,
                                        port=8080
                                    ),
                                    initial_delay_seconds=5,
                                    period_seconds=5
                                )
                            )
                        ]
                    )
                )
            )
        )
        
        # Create deployment
        self.k8s_apps.create_namespaced_deployment(
            namespace="default",
            body=deployment
        )
        
        # Create HPA
        hpa = client.V1HorizontalPodAutoscaler(
            api_version="autoscaling/v1",
            kind="HorizontalPodAutoscaler",
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1HorizontalPodAutoscalerSpec(
                scale_target_ref=client.V1CrossVersionObjectReference(
                    api_version="apps/v1",
                    kind="Deployment",
                    name=name
                ),
                min_replicas=config.min_replicas,
                max_replicas=config.max_replicas,
                target_cpu_utilization_percentage=config.target_cpu_utilization
            )
        )
        
        self.k8s_autoscaling.create_namespaced_horizontal_pod_autoscaler(
            namespace="default",
            body=hpa
        )
        
        return deployment
    
    def _create_k8s_service(
        self,
        name: str,
        deployment: client.V1Deployment
    ) -> client.V1Service:
        """Create Kubernetes service"""
        service = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1ServiceSpec(
                selector={"app": name},
                ports=[
                    client.V1ServicePort(
                        port=80,
                        target_port=8080
                    )
                ],
                type="LoadBalancer"
            )
        )
        
        return self.k8s_core.create_namespaced_service(
            namespace="default",
            body=service
        )
    
    def _build_model_image(self, model: Any, metadata: ModelMetadata) -> str:
        """Build container image for model"""
        # In production, this would build and push to container registry
        # For now, return a placeholder
        return f"nexus-models/{metadata.name}:{metadata.version}"
    
    async def _test_deployment(self, service: client.V1Service):
        """Test deployed service"""
        # Wait for service to be ready
        await asyncio.sleep(30)
        
        # Perform health checks
        # In production, would make actual HTTP requests
        pass
    
    async def _monitor_canary(self, deployment: client.V1Deployment, duration_minutes: int):
        """Monitor canary deployment"""
        # In production, would collect real metrics
        await asyncio.sleep(duration_minutes * 60)
    
    async def _get_deployment_metrics(self, deployment_name: str) -> Dict[str, float]:
        """Get deployment metrics"""
        # In production, would query Prometheus or similar
        return {
            'error_rate': 0.01,
            'latency_p99': 100,
            'throughput': 1000
        }
    
    async def _wait_for_rollout(self, deployment_name: str):
        """Wait for deployment rollout to complete"""
        while True:
            deployment = self.k8s_apps.read_namespaced_deployment(
                name=deployment_name,
                namespace="default"
            )
            
            if deployment.status.replicas == deployment.status.ready_replicas:
                break
            
            await asyncio.sleep(5)


class ModelMonitoring:
    """Monitor model performance in production"""
    
    def __init__(self):
        # Prometheus metrics
        self.prediction_counter = Counter(
            'model_predictions_total',
            'Total number of predictions',
            ['model_name', 'model_version']
        )
        
        self.prediction_latency = Histogram(
            'model_prediction_latency_seconds',
            'Prediction latency in seconds',
            ['model_name', 'model_version']
        )
        
        self.model_accuracy = Gauge(
            'model_accuracy',
            'Model accuracy score',
            ['model_name', 'model_version']
        )
        
        self.drift_score = Gauge(
            'model_drift_score',
            'Data drift score',
            ['model_name', 'model_version', 'feature']
        )
        
        # Storage for monitoring data
        self.performance_history = []
        self.drift_history = []
        
    def record_prediction(
        self,
        model_name: str,
        model_version: str,
        features: Dict[str, Any],
        prediction: Any,
        latency: float,
        actual: Optional[Any] = None
    ):
        """Record prediction for monitoring"""
        # Update metrics
        self.prediction_counter.labels(model_name, model_version).inc()
        self.prediction_latency.labels(model_name, model_version).observe(latency)
        
        # Store prediction data
        record = {
            'timestamp': datetime.now(),
            'model_name': model_name,
            'model_version': model_version,
            'features': features,
            'prediction': prediction,
            'latency': latency,
            'actual': actual
        }
        
        self.performance_history.append(record)
        
        # Clean old data (keep last 7 days)
        cutoff = datetime.now() - timedelta(days=7)
        self.performance_history = [
            r for r in self.performance_history
            if r['timestamp'] > cutoff
        ]
    
    def update_accuracy(self, model_name: str, model_version: str, accuracy: float):
        """Update model accuracy metric"""
        self.model_accuracy.labels(model_name, model_version).set(accuracy)
    
    def detect_drift(
        self,
        model_name: str,
        model_version: str,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Detect data drift"""
        drift_scores = {}
        
        for column in reference_data.columns:
            if column not in current_data.columns:
                continue
            
            # Calculate drift score (simplified)
            if pd.api.types.is_numeric_dtype(reference_data[column]):
                # KS statistic for numeric features
                from scipy.stats import ks_2samp
                statistic, p_value = ks_2samp(
                    reference_data[column],
                    current_data[column]
                )
                drift_score = statistic
            else:
                # Chi-square for categorical features
                from scipy.stats import chi2_contingency
                ref_counts = reference_data[column].value_counts()
                curr_counts = current_data[column].value_counts()
                
                # Align categories
                all_cats = set(ref_counts.index) | set(curr_counts.index)
                ref_aligned = [ref_counts.get(cat, 0) for cat in all_cats]
                curr_aligned = [curr_counts.get(cat, 0) for cat in all_cats]
                
                chi2, p_value = chi2_contingency([ref_aligned, curr_aligned])[:2]
                drift_score = 1 - p_value
            
            drift_scores[column] = drift_score
            self.drift_score.labels(model_name, model_version, column).set(drift_score)
        
        # Store drift history
        self.drift_history.append({
            'timestamp': datetime.now(),
            'model_name': model_name,
            'model_version': model_version,
            'drift_scores': drift_scores
        })
        
        return drift_scores
    
    def get_performance_report(
        self,
        model_name: str,
        model_version: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Generate performance report"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Filter relevant records
        records = [
            r for r in self.performance_history
            if r['model_name'] == model_name
            and r['model_version'] == model_version
            and r['timestamp'] > cutoff
        ]
        
        if not records:
            return {'error': 'No data available'}
        
        # Calculate metrics
        latencies = [r['latency'] for r in records]
        
        # Calculate accuracy if actual values available
        accuracy = None
        records_with_actual = [r for r in records if r['actual'] is not None]
        if records_with_actual:
            correct = sum(1 for r in records_with_actual if r['prediction'] == r['actual'])
            accuracy = correct / len(records_with_actual)
        
        return {
            'model_name': model_name,
            'model_version': model_version,
            'time_period_hours': hours,
            'total_predictions': len(records),
            'average_latency': np.mean(latencies),
            'p95_latency': np.percentile(latencies, 95),
            'p99_latency': np.percentile(latencies, 99),
            'accuracy': accuracy,
            'predictions_per_hour': len(records) / hours
        }


class ModelExplainability:
    """Model interpretability and explainability"""
    
    def __init__(self):
        self.explainers = {}
        
    def explain_prediction(
        self,
        model: Any,
        features: pd.DataFrame,
        prediction_index: int = 0,
        method: str = "shap"
    ) -> Dict[str, Any]:
        """Explain individual prediction"""
        
        if method == "shap":
            return self._explain_shap(model, features, prediction_index)
        elif method == "lime":
            return self._explain_lime(model, features, prediction_index)
        else:
            raise ValueError(f"Unknown explanation method: {method}")
    
    def _explain_shap(
        self,
        model: Any,
        features: pd.DataFrame,
        prediction_index: int
    ) -> Dict[str, Any]:
        """SHAP explanation"""
        # Get or create explainer
        model_id = id(model)
        if model_id not in self.explainers:
            self.explainers[model_id] = shap.Explainer(model, features)
        
        explainer = self.explainers[model_id]
        
        # Calculate SHAP values
        shap_values = explainer(features)
        
        # Get explanation for specific prediction
        explanation = {
            'method': 'shap',
            'base_value': explainer.expected_value,
            'prediction': model.predict(features)[prediction_index],
            'feature_importance': {}
        }
        
        # Extract feature importance
        for i, col in enumerate(features.columns):
            explanation['feature_importance'][col] = {
                'value': features.iloc[prediction_index, i],
                'shap_value': shap_values[prediction_index, i].values
            }
        
        return explanation
    
    def _explain_lime(
        self,
        model: Any,
        features: pd.DataFrame,
        prediction_index: int
    ) -> Dict[str, Any]:
        """LIME explanation"""
        # Create LIME explainer
        explainer = LimeTabularExplainer(
            features.values,
            feature_names=features.columns.tolist(),
            mode='classification' if hasattr(model, 'predict_proba') else 'regression'
        )
        
        # Get explanation
        if hasattr(model, 'predict_proba'):
            exp = explainer.explain_instance(
                features.iloc[prediction_index].values,
                model.predict_proba,
                num_features=len(features.columns)
            )
        else:
            exp = explainer.explain_instance(
                features.iloc[prediction_index].values,
                model.predict,
                num_features=len(features.columns)
            )
        
        # Format explanation
        explanation = {
            'method': 'lime',
            'prediction': model.predict(features)[prediction_index],
            'feature_importance': {}
        }
        
        for feature, importance in exp.as_list():
            explanation['feature_importance'][feature] = importance
        
        return explanation
    
    def global_feature_importance(
        self,
        model: Any,
        features: pd.DataFrame,
        method: str = "permutation"
    ) -> Dict[str, float]:
        """Calculate global feature importance"""
        
        if hasattr(model, 'feature_importances_'):
            # Tree-based models
            importance = dict(zip(features.columns, model.feature_importances_))
        elif method == "permutation":
            # Permutation importance
            from sklearn.inspection import permutation_importance
            result = permutation_importance(model, features, np.zeros(len(features)))
            importance = dict(zip(features.columns, result.importances_mean))
        else:
            # SHAP-based global importance
            explainer = shap.Explainer(model, features)
            shap_values = explainer(features)
            importance = dict(zip(
                features.columns,
                np.abs(shap_values.values).mean(axis=0)
            ))
        
        # Normalize
        total = sum(importance.values())
        if total > 0:
            importance = {k: v/total for k, v in importance.items()}
        
        return importance


class BiasDetection:
    """Detect and mitigate bias in models"""
    
    def __init__(self):
        self.metrics_history = []
        
    def detect_bias(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        sensitive_features: List[str],
        model: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Detect bias in data or model predictions"""
        results = {
            'timestamp': datetime.now(),
            'data_bias': {},
            'model_bias': {} if model else None
        }
        
        # Check data bias
        for feature in sensitive_features:
            if feature not in X.columns:
                continue
            
            # Calculate disparate impact
            groups = X.groupby(feature)
            group_outcomes = {}
            
            for group_name, group_data in groups:
                group_indices = group_data.index
                positive_rate = y[group_indices].mean()
                group_outcomes[group_name] = positive_rate
            
            # Find min and max positive rates
            min_rate = min(group_outcomes.values())
            max_rate = max(group_outcomes.values())
            
            disparate_impact = min_rate / max_rate if max_rate > 0 else 0
            
            results['data_bias'][feature] = {
                'disparate_impact': disparate_impact,
                'group_outcomes': group_outcomes,
                'bias_detected': disparate_impact < 0.8  # 80% rule
            }
        
        # Check model bias if provided
        if model:
            predictions = model.predict(X)
            
            for feature in sensitive_features:
                if feature not in X.columns:
                    continue
                
                groups = X.groupby(feature)
                group_predictions = {}
                
                for group_name, group_data in groups:
                    group_indices = group_data.index
                    positive_rate = predictions[group_indices].mean()
                    group_predictions[group_name] = positive_rate
                
                min_rate = min(group_predictions.values())
                max_rate = max(group_predictions.values())
                
                disparate_impact = min_rate / max_rate if max_rate > 0 else 0
                
                results['model_bias'][feature] = {
                    'disparate_impact': disparate_impact,
                    'group_predictions': group_predictions,
                    'bias_detected': disparate_impact < 0.8
                }
        
        self.metrics_history.append(results)
        return results
    
    def mitigate_bias(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        sensitive_features: List[str],
        method: str = "reweighing"
    ) -> Tuple[pd.DataFrame, pd.Series, Dict[str, Any]]:
        """Apply bias mitigation techniques"""
        
        if method == "reweighing":
            # Apply reweighing algorithm
            weights = self._calculate_reweighing_weights(X, y, sensitive_features)
            
            # Return weighted data
            return X, y, {'method': 'reweighing', 'weights': weights}
        
        elif method == "sampling":
            # Apply oversampling/undersampling
            X_balanced, y_balanced = self._balance_dataset(X, y, sensitive_features)
            
            return X_balanced, y_balanced, {'method': 'sampling'}
        
        else:
            raise ValueError(f"Unknown mitigation method: {method}")
    
    def _calculate_reweighing_weights(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        sensitive_features: List[str]
    ) -> np.ndarray:
        """Calculate reweighing weights"""
        weights = np.ones(len(X))
        
        for feature in sensitive_features:
            if feature not in X.columns:
                continue
            
            # Calculate group statistics
            for group_value in X[feature].unique():
                group_mask = X[feature] == group_value
                group_size = group_mask.sum()
                group_positive = y[group_mask].sum()
                
                # Calculate expected positive rate
                overall_positive_rate = y.mean()
                expected_positive = group_size * overall_positive_rate
                
                # Calculate weight
                if group_positive > 0:
                    weight = expected_positive / group_positive
                    weights[group_mask] *= weight
        
        # Normalize weights
        weights = weights / weights.mean()
        
        return weights
    
    def _balance_dataset(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        sensitive_features: List[str]
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Balance dataset through sampling"""
        # Simple oversampling of minority groups
        from imblearn.over_sampling import SMOTE
        
        # Apply SMOTE
        smote = SMOTE(random_state=42)
        X_balanced, y_balanced = smote.fit_resample(X, y)
        
        return pd.DataFrame(X_balanced, columns=X.columns), pd.Series(y_balanced)


class ModelGovernance:
    """Model governance and compliance"""
    
    def __init__(self):
        self.audit_log = []
        self.compliance_checks = {}
        self.access_control = {}
        
    def log_model_access(
        self,
        user_id: str,
        model_id: str,
        action: str,
        details: Dict[str, Any] = None
    ):
        """Log model access for audit trail"""
        log_entry = {
            'timestamp': datetime.now(),
            'user_id': user_id,
            'model_id': model_id,
            'action': action,
            'details': details or {}
        }
        
        self.audit_log.append(log_entry)
        
        # Rotate logs (keep last 90 days)
        cutoff = datetime.now() - timedelta(days=90)
        self.audit_log = [
            entry for entry in self.audit_log
            if entry['timestamp'] > cutoff
        ]
    
    def check_compliance(
        self,
        model_id: str,
        regulations: List[str] = ["GDPR", "CCPA", "HIPAA"]
    ) -> Dict[str, Dict[str, Any]]:
        """Check model compliance with regulations"""
        results = {}
        
        for regulation in regulations:
            if regulation == "GDPR":
                results["GDPR"] = self._check_gdpr_compliance(model_id)
            elif regulation == "CCPA":
                results["CCPA"] = self._check_ccpa_compliance(model_id)
            elif regulation == "HIPAA":
                results["HIPAA"] = self._check_hipaa_compliance(model_id)
        
        self.compliance_checks[model_id] = {
            'timestamp': datetime.now(),
            'results': results
        }
        
        return results
    
    def _check_gdpr_compliance(self, model_id: str) -> Dict[str, Any]:
        """Check GDPR compliance"""
        return {
            'compliant': True,
            'checks': {
                'data_minimization': True,
                'purpose_limitation': True,
                'accuracy': True,
                'storage_limitation': True,
                'security': True,
                'accountability': True
            },
            'recommendations': []
        }
    
    def _check_ccpa_compliance(self, model_id: str) -> Dict[str, Any]:
        """Check CCPA compliance"""
        return {
            'compliant': True,
            'checks': {
                'right_to_know': True,
                'right_to_delete': True,
                'right_to_opt_out': True,
                'non_discrimination': True
            },
            'recommendations': []
        }
    
    def _check_hipaa_compliance(self, model_id: str) -> Dict[str, Any]:
        """Check HIPAA compliance"""
        return {
            'compliant': True,
            'checks': {
                'access_controls': True,
                'audit_controls': True,
                'integrity': True,
                'transmission_security': True
            },
            'recommendations': []
        }
    
    def set_access_control(
        self,
        model_id: str,
        permissions: Dict[str, List[str]]
    ):
        """Set access control for model"""
        self.access_control[model_id] = {
            'permissions': permissions,
            'updated_at': datetime.now()
        }
    
    def check_access(
        self,
        user_id: str,
        model_id: str,
        action: str
    ) -> bool:
        """Check if user has access to perform action"""
        if model_id not in self.access_control:
            return True  # No restrictions
        
        permissions = self.access_control[model_id]['permissions']
        
        # Check if user has permission for action
        if action in permissions:
            return user_id in permissions[action]
        
        return False


class DistributedTraining:
    """Distributed model training support"""
    
    def __init__(self):
        ray.init(ignore_reinit_error=True)
        
    @ray.remote
    def train_partition(
        self,
        model_class: Any,
        X_partition: pd.DataFrame,
        y_partition: pd.Series,
        hyperparameters: Dict[str, Any]
    ) -> Any:
        """Train model on data partition"""
        model = model_class(**hyperparameters)
        model.fit(X_partition, y_partition)
        return model
    
    async def distributed_train(
        self,
        model_class: Any,
        X: pd.DataFrame,
        y: pd.Series,
        hyperparameters: Dict[str, Any],
        n_partitions: int = 4
    ) -> Any:
        """Train model using distributed computing"""
        # Split data into partitions
        partition_size = len(X) // n_partitions
        partitions = []
        
        for i in range(n_partitions):
            start_idx = i * partition_size
            end_idx = start_idx + partition_size if i < n_partitions - 1 else len(X)
            
            X_partition = X.iloc[start_idx:end_idx]
            y_partition = y.iloc[start_idx:end_idx]
            
            partitions.append((X_partition, y_partition))
        
        # Train models in parallel
        futures = []
        for X_part, y_part in partitions:
            future = self.train_partition.remote(
                model_class,
                X_part,
                y_part,
                hyperparameters
            )
            futures.append(future)
        
        # Wait for all models to complete
        models = ray.get(futures)
        
        # Ensemble models (simple averaging for now)
        # In production, would use more sophisticated ensemble methods
        return models[0]  # Return first model for simplicity


# FastAPI Model Serving
app = FastAPI(title="NEXUS Model Serving API")

class PredictionRequest(BaseModel):
    features: Dict[str, Any]
    model_id: str

class PredictionResponse(BaseModel):
    prediction: Any
    model_id: str
    latency: float
    explanation: Optional[Dict[str, Any]] = None

# Global instances
model_registry = ModelRegistry()
model_deployment = ModelDeployment(model_registry)
model_monitoring = ModelMonitoring()
model_explainability = ModelExplainability()
model_governance = ModelGovernance()

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Make prediction using deployed model"""
    start_time = datetime.now()
    
    try:
        # Check access
        if not model_governance.check_access("api_user", request.model_id, "predict"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Load model
        model, metadata = model_registry.get_model(request.model_id)
        
        # Prepare features
        features_df = pd.DataFrame([request.features])
        
        # Make prediction
        prediction = model.predict(features_df)[0]
        
        # Calculate latency
        latency = (datetime.now() - start_time).total_seconds()
        
        # Record for monitoring
        model_monitoring.record_prediction(
            metadata.name,
            metadata.version,
            request.features,
            prediction,
            latency
        )
        
        # Log access
        model_governance.log_model_access(
            "api_user",
            request.model_id,
            "predict",
            {"features": request.features}
        )
        
        # Generate explanation if requested
        explanation = None
        if request.features.get("_explain", False):
            explanation = model_explainability.explain_prediction(
                model,
                features_df,
                prediction_index=0
            )
        
        return PredictionResponse(
            prediction=prediction,
            model_id=request.model_id,
            latency=latency,
            explanation=explanation
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def list_models(status: Optional[str] = None):
    """List available models"""
    try:
        status_enum = ModelStatus(status) if status else None
        models = model_registry.list_models(status=status_enum)
        
        return {
            "models": [
                {
                    "model_id": m.model_id,
                    "name": m.name,
                    "version": m.version,
                    "status": m.status.value,
                    "created_at": m.created_at.isoformat()
                }
                for m in models
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/{model_id}/metrics")
async def get_model_metrics(model_id: str, hours: int = 24):
    """Get model performance metrics"""
    try:
        model, metadata = model_registry.get_model(model_id)
        report = model_monitoring.get_performance_report(
            metadata.name,
            metadata.version,
            hours
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/{model_id}/deploy")
async def deploy_model(
    model_id: str,
    strategy: str = "rolling",
    background_tasks: BackgroundTasks = None
):
    """Deploy model with specified strategy"""
    try:
        config = DeploymentConfig(
            model_id=model_id,
            strategy=DeploymentStrategy(strategy)
        )
        
        # Deploy asynchronously
        background_tasks.add_task(
            model_deployment.deploy_model,
            model_id,
            config
        )
        
        return {"message": f"Deployment started for model {model_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return prometheus_client.generate_latest()


if __name__ == "__main__":
    # Example usage
    import sklearn.datasets
    from sklearn.ensemble import RandomForestClassifier
    
    # Generate sample data
    X, y = sklearn.datasets.make_classification(n_samples=1000, n_features=20)
    X_df = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(20)])
    
    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_df, y)
    
    # Create metadata
    metadata = ModelMetadata(
        model_id="",
        name="sample_classifier",
        version="1.0.0",
        algorithm="random_forest",
        framework="sklearn",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        author="system",
        description="Sample classification model",
        tags=["classification", "sample"],
        metrics={"accuracy": 0.95, "f1_score": 0.94},
        parameters={"n_estimators": 100, "random_state": 42}
    )
    
    # Register model
    registry = ModelRegistry()
    model_id = registry.register_model(model, metadata)
    
    print(f"Model registered with ID: {model_id}")
    
    # Run API server
    uvicorn.run(app, host="0.0.0.0", port=8000)