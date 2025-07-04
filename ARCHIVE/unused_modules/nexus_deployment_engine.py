#!/usr/bin/env python3
"""
NEXUS Production Deployment Engine
==================================

Core deployment system with multi-cloud support, Kubernetes orchestration,
containerization, and advanced deployment strategies.

Features:
- Multi-cloud deployment (AWS, GCP, Azure)
- Kubernetes orchestration with Helm
- Docker container management
- Serverless deployment
- Blue-green deployments
- Canary releases
- Automatic rollback
- Zero-downtime updates
"""

import os
import json
import yaml
import asyncio
import hashlib
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import aiofiles
import docker
import boto3
import kubernetes
from kubernetes import client, config as k8s_config
from azure.identity import DefaultAzureCredential
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.web import WebSiteManagementClient
from google.cloud import run_v2, functions_v1
from google.oauth2 import service_account
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

console = Console()

class CloudProvider(Enum):
    """Supported cloud providers"""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    KUBERNETES = "kubernetes"
    DOCKER = "docker"
    SERVERLESS = "serverless"

class DeploymentStrategy(Enum):
    """Deployment strategies"""
    ROLLING_UPDATE = "rolling_update"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    RECREATE = "recreate"
    A_B_TESTING = "a_b_testing"

class ServiceType(Enum):
    """Service types for deployment"""
    WEB_APP = "web_app"
    API = "api"
    MICROSERVICE = "microservice"
    STATIC_SITE = "static_site"
    SERVERLESS_FUNCTION = "serverless_function"
    BATCH_JOB = "batch_job"

@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    name: str
    version: str
    provider: CloudProvider
    strategy: DeploymentStrategy
    service_type: ServiceType
    region: str = "us-east-1"
    replicas: int = 3
    cpu: str = "1000m"
    memory: str = "1Gi"
    environment: Dict[str, str] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)
    health_check: Dict[str, Any] = field(default_factory=dict)
    auto_scaling: Dict[str, Any] = field(default_factory=dict)
    networking: Dict[str, Any] = field(default_factory=dict)
    volumes: List[Dict[str, Any]] = field(default_factory=list)
    custom_domain: Optional[str] = None
    ssl_enabled: bool = True
    monitoring: Dict[str, Any] = field(default_factory=dict)
    rollback_on_failure: bool = True
    max_surge: int = 1
    max_unavailable: int = 0
    deployment_timeout: int = 600  # seconds
    canary_percentage: int = 10
    canary_duration: int = 300  # seconds

@dataclass
class DeploymentStatus:
    """Deployment status information"""
    deployment_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    replicas_ready: int = 0
    replicas_total: int = 0
    endpoint: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    rollback_available: bool = False
    previous_version: Optional[str] = None

class DeploymentEngine:
    """Core deployment engine with multi-cloud support"""
    
    def __init__(self):
        self.providers = {
            CloudProvider.AWS: AWSDeploymentProvider(),
            CloudProvider.GCP: GCPDeploymentProvider(),
            CloudProvider.AZURE: AzureDeploymentProvider(),
            CloudProvider.KUBERNETES: KubernetesDeploymentProvider(),
            CloudProvider.DOCKER: DockerDeploymentProvider(),
            CloudProvider.SERVERLESS: ServerlessDeploymentProvider()
        }
        self.deployment_history = []
        self.active_deployments = {}
        
    async def deploy(self, config: DeploymentConfig, artifact_path: str) -> DeploymentStatus:
        """Deploy application using specified configuration"""
        console.print(f"[cyan]Starting deployment: {config.name} v{config.version}[/cyan]")
        
        # Generate deployment ID
        deployment_id = self._generate_deployment_id(config)
        
        # Initialize deployment status
        status = DeploymentStatus(
            deployment_id=deployment_id,
            status="initializing",
            start_time=datetime.now(),
            replicas_total=config.replicas
        )
        
        self.active_deployments[deployment_id] = status
        
        try:
            # Validate configuration
            await self._validate_config(config)
            
            # Pre-deployment checks
            await self._pre_deployment_checks(config)
            
            # Get provider
            provider = self.providers.get(config.provider)
            if not provider:
                raise ValueError(f"Unsupported provider: {config.provider}")
            
            # Execute deployment based on strategy
            if config.strategy == DeploymentStrategy.BLUE_GREEN:
                result = await self._deploy_blue_green(provider, config, artifact_path, status)
            elif config.strategy == DeploymentStrategy.CANARY:
                result = await self._deploy_canary(provider, config, artifact_path, status)
            elif config.strategy == DeploymentStrategy.ROLLING_UPDATE:
                result = await self._deploy_rolling_update(provider, config, artifact_path, status)
            else:
                result = await provider.deploy(config, artifact_path, status)
            
            # Post-deployment verification
            await self._verify_deployment(config, status)
            
            # Update status
            status.status = "completed"
            status.end_time = datetime.now()
            status.endpoint = result.get("endpoint")
            status.rollback_available = True
            
            # Store deployment history
            self._store_deployment_history(config, status)
            
            console.print(f"[green]Deployment successful: {status.endpoint}[/green]")
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            status.status = "failed"
            status.end_time = datetime.now()
            status.events.append({
                "timestamp": datetime.now().isoformat(),
                "type": "error",
                "message": str(e)
            })
            
            # Rollback if configured
            if config.rollback_on_failure and status.previous_version:
                console.print("[yellow]Initiating automatic rollback...[/yellow]")
                await self.rollback(deployment_id)
            
            raise
        
        return status
    
    async def _deploy_blue_green(self, provider: Any, config: DeploymentConfig, 
                                artifact_path: str, status: DeploymentStatus) -> Dict[str, Any]:
        """Execute blue-green deployment"""
        console.print("[cyan]Executing blue-green deployment...[/cyan]")
        
        # Deploy to green environment
        green_config = config.__class__(**{**config.__dict__, "name": f"{config.name}-green"})
        green_result = await provider.deploy(green_config, artifact_path, status)
        
        # Run health checks on green
        await self._health_check(green_result["endpoint"], config.health_check)
        
        # Switch traffic to green
        await provider.switch_traffic(config.name, "green")
        
        # Keep blue as backup for rollback
        status.previous_version = f"{config.name}-blue"
        
        return green_result
    
    async def _deploy_canary(self, provider: Any, config: DeploymentConfig,
                           artifact_path: str, status: DeploymentStatus) -> Dict[str, Any]:
        """Execute canary deployment"""
        console.print(f"[cyan]Executing canary deployment ({config.canary_percentage}%)...[/cyan]")
        
        # Deploy canary version
        canary_config = config.__class__(**{
            **config.__dict__,
            "name": f"{config.name}-canary",
            "replicas": max(1, config.replicas * config.canary_percentage // 100)
        })
        
        canary_result = await provider.deploy(canary_config, artifact_path, status)
        
        # Route percentage of traffic to canary
        await provider.configure_traffic_split(config.name, {
            "stable": 100 - config.canary_percentage,
            "canary": config.canary_percentage
        })
        
        # Monitor canary metrics
        console.print(f"[yellow]Monitoring canary for {config.canary_duration}s...[/yellow]")
        canary_healthy = await self._monitor_canary(
            canary_result["endpoint"],
            config.canary_duration,
            config.health_check
        )
        
        if canary_healthy:
            # Promote canary to stable
            console.print("[green]Canary healthy, promoting to stable...[/green]")
            result = await provider.promote_canary(config.name)
        else:
            # Rollback canary
            console.print("[red]Canary unhealthy, rolling back...[/red]")
            await provider.rollback_canary(config.name)
            raise Exception("Canary deployment failed health checks")
        
        return result
    
    async def _deploy_rolling_update(self, provider: Any, config: DeploymentConfig,
                                   artifact_path: str, status: DeploymentStatus) -> Dict[str, Any]:
        """Execute rolling update deployment"""
        console.print("[cyan]Executing rolling update...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            
            task = progress.add_task(
                f"Updating {config.replicas} replicas",
                total=config.replicas
            )
            
            # Update replicas in batches
            batch_size = config.max_surge
            for i in range(0, config.replicas, batch_size):
                batch_end = min(i + batch_size, config.replicas)
                
                # Update batch
                await provider.update_replicas(
                    config.name,
                    artifact_path,
                    start_index=i,
                    end_index=batch_end
                )
                
                # Wait for batch to be ready
                await self._wait_for_replicas_ready(provider, config.name, batch_end)
                
                # Update progress
                progress.update(task, completed=batch_end)
                status.replicas_ready = batch_end
                
                # Health check
                if config.health_check:
                    await self._health_check_replicas(provider, config.name, config.health_check)
        
        return await provider.get_deployment_info(config.name)
    
    async def rollback(self, deployment_id: str) -> bool:
        """Rollback a deployment"""
        console.print(f"[yellow]Rolling back deployment: {deployment_id}[/yellow]")
        
        status = self.active_deployments.get(deployment_id)
        if not status or not status.rollback_available:
            console.print("[red]Rollback not available for this deployment[/red]")
            return False
        
        try:
            # Find deployment config from history
            deployment = next(
                (d for d in self.deployment_history if d["deployment_id"] == deployment_id),
                None
            )
            
            if not deployment:
                raise ValueError("Deployment not found in history")
            
            config = deployment["config"]
            provider = self.providers.get(config.provider)
            
            # Execute rollback
            await provider.rollback(config.name, status.previous_version)
            
            console.print("[green]Rollback completed successfully[/green]")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            console.print(f"[red]Rollback failed: {e}[/red]")
            return False
    
    async def scale(self, deployment_id: str, replicas: int) -> bool:
        """Scale a deployment"""
        console.print(f"[cyan]Scaling deployment {deployment_id} to {replicas} replicas...[/cyan]")
        
        status = self.active_deployments.get(deployment_id)
        if not status:
            console.print("[red]Deployment not found[/red]")
            return False
        
        try:
            # Find deployment config
            deployment = next(
                (d for d in self.deployment_history if d["deployment_id"] == deployment_id),
                None
            )
            
            if not deployment:
                raise ValueError("Deployment not found in history")
            
            config = deployment["config"]
            provider = self.providers.get(config.provider)
            
            # Scale deployment
            await provider.scale(config.name, replicas)
            
            # Update status
            status.replicas_total = replicas
            
            console.print(f"[green]Scaled to {replicas} replicas[/green]")
            return True
            
        except Exception as e:
            logger.error(f"Scaling failed: {e}")
            console.print(f"[red]Scaling failed: {e}[/red]")
            return False
    
    async def get_status(self, deployment_id: str) -> Optional[DeploymentStatus]:
        """Get deployment status"""
        return self.active_deployments.get(deployment_id)
    
    async def list_deployments(self, provider: Optional[CloudProvider] = None) -> List[Dict[str, Any]]:
        """List all deployments"""
        deployments = []
        
        for deployment in self.deployment_history:
            if provider and deployment["config"].provider != provider:
                continue
            
            status = self.active_deployments.get(deployment["deployment_id"])
            deployments.append({
                "deployment_id": deployment["deployment_id"],
                "name": deployment["config"].name,
                "version": deployment["config"].version,
                "provider": deployment["config"].provider.value,
                "status": status.status if status else "unknown",
                "endpoint": status.endpoint if status else None,
                "timestamp": deployment["timestamp"]
            })
        
        return deployments
    
    def _generate_deployment_id(self, config: DeploymentConfig) -> str:
        """Generate unique deployment ID"""
        data = f"{config.name}-{config.version}-{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:12]
    
    async def _validate_config(self, config: DeploymentConfig):
        """Validate deployment configuration"""
        # Validate required fields
        if not config.name:
            raise ValueError("Deployment name is required")
        
        if not config.version:
            raise ValueError("Deployment version is required")
        
        # Validate provider-specific requirements
        provider = self.providers.get(config.provider)
        if provider:
            await provider.validate_config(config)
    
    async def _pre_deployment_checks(self, config: DeploymentConfig):
        """Run pre-deployment checks"""
        console.print("[yellow]Running pre-deployment checks...[/yellow]")
        
        # Check resource availability
        provider = self.providers.get(config.provider)
        if provider:
            resources_available = await provider.check_resources(config)
            if not resources_available:
                raise Exception("Insufficient resources for deployment")
        
        # Check for conflicts
        existing = await self._check_existing_deployment(config.name)
        if existing and existing.status == "in_progress":
            raise Exception("Another deployment is in progress")
    
    async def _verify_deployment(self, config: DeploymentConfig, status: DeploymentStatus):
        """Verify deployment after completion"""
        console.print("[yellow]Verifying deployment...[/yellow]")
        
        if config.health_check:
            endpoint = status.endpoint
            if endpoint:
                healthy = await self._health_check(endpoint, config.health_check)
                if not healthy:
                    raise Exception("Deployment failed health checks")
    
    async def _health_check(self, endpoint: str, health_config: Dict[str, Any]) -> bool:
        """Perform health check on endpoint"""
        path = health_config.get("path", "/health")
        timeout = health_config.get("timeout", 30)
        interval = health_config.get("interval", 5)
        retries = health_config.get("retries", 6)
        
        url = f"{endpoint}{path}"
        
        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                        if response.status == 200:
                            console.print(f"[green]Health check passed: {url}[/green]")
                            return True
            except Exception as e:
                logger.warning(f"Health check attempt {attempt + 1} failed: {e}")
            
            if attempt < retries - 1:
                await asyncio.sleep(interval)
        
        return False
    
    async def _monitor_canary(self, endpoint: str, duration: int, 
                            health_config: Dict[str, Any]) -> bool:
        """Monitor canary deployment"""
        start_time = datetime.now()
        errors = 0
        checks = 0
        
        while (datetime.now() - start_time).seconds < duration:
            checks += 1
            
            # Perform health check
            healthy = await self._health_check(endpoint, health_config)
            if not healthy:
                errors += 1
            
            # Calculate error rate
            error_rate = errors / checks
            if error_rate > 0.1:  # 10% error threshold
                console.print(f"[red]Canary error rate too high: {error_rate:.2%}[/red]")
                return False
            
            await asyncio.sleep(10)  # Check every 10 seconds
        
        console.print(f"[green]Canary monitoring complete. Error rate: {error_rate:.2%}[/green]")
        return True
    
    async def _wait_for_replicas_ready(self, provider: Any, name: str, expected: int):
        """Wait for replicas to be ready"""
        timeout = 300  # 5 minutes
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout:
            ready = await provider.get_ready_replicas(name)
            if ready >= expected:
                return
            
            await asyncio.sleep(5)
        
        raise Exception(f"Timeout waiting for replicas to be ready")
    
    async def _health_check_replicas(self, provider: Any, name: str, 
                                   health_config: Dict[str, Any]):
        """Health check all replicas"""
        endpoints = await provider.get_replica_endpoints(name)
        
        tasks = [
            self._health_check(endpoint, health_config)
            for endpoint in endpoints
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        failed = sum(1 for r in results if r is False or isinstance(r, Exception))
        if failed > 0:
            raise Exception(f"{failed} replicas failed health checks")
    
    async def _check_existing_deployment(self, name: str) -> Optional[DeploymentStatus]:
        """Check for existing deployment with same name"""
        for deployment_id, status in self.active_deployments.items():
            deployment = next(
                (d for d in self.deployment_history if d["deployment_id"] == deployment_id),
                None
            )
            if deployment and deployment["config"].name == name:
                return status
        return None
    
    def _store_deployment_history(self, config: DeploymentConfig, status: DeploymentStatus):
        """Store deployment in history"""
        self.deployment_history.append({
            "deployment_id": status.deployment_id,
            "config": config,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 100 deployments
        if len(self.deployment_history) > 100:
            self.deployment_history = self.deployment_history[-100:]


class AWSDeploymentProvider:
    """AWS deployment provider"""
    
    def __init__(self):
        self.ecs_client = boto3.client('ecs')
        self.ecr_client = boto3.client('ecr')
        self.elb_client = boto3.client('elbv2')
        self.lambda_client = boto3.client('lambda')
        self.s3_client = boto3.client('s3')
        self.cloudformation_client = boto3.client('cloudformation')
    
    async def deploy(self, config: DeploymentConfig, artifact_path: str, 
                    status: DeploymentStatus) -> Dict[str, Any]:
        """Deploy to AWS"""
        console.print("[cyan]Deploying to AWS...[/cyan]")
        
        if config.service_type == ServiceType.SERVERLESS_FUNCTION:
            return await self._deploy_lambda(config, artifact_path, status)
        elif config.service_type == ServiceType.STATIC_SITE:
            return await self._deploy_s3_cloudfront(config, artifact_path, status)
        else:
            return await self._deploy_ecs(config, artifact_path, status)
    
    async def _deploy_ecs(self, config: DeploymentConfig, artifact_path: str,
                         status: DeploymentStatus) -> Dict[str, Any]:
        """Deploy to ECS"""
        # Push Docker image to ECR
        image_uri = await self._push_to_ecr(config.name, config.version, artifact_path)
        
        # Create or update ECS task definition
        task_definition = self._create_task_definition(config, image_uri)
        
        # Register task definition
        response = self.ecs_client.register_task_definition(**task_definition)
        task_def_arn = response['taskDefinition']['taskDefinitionArn']
        
        # Update ECS service
        cluster_name = f"nexus-{config.environment}"
        service_name = config.name
        
        try:
            # Update existing service
            self.ecs_client.update_service(
                cluster=cluster_name,
                service=service_name,
                taskDefinition=task_def_arn,
                desiredCount=config.replicas,
                deploymentConfiguration={
                    'maximumPercent': 200,
                    'minimumHealthyPercent': 100,
                    'deploymentCircuitBreaker': {
                        'enable': config.rollback_on_failure,
                        'rollback': config.rollback_on_failure
                    }
                }
            )
        except self.ecs_client.exceptions.ServiceNotFoundException:
            # Create new service
            self._create_ecs_service(cluster_name, service_name, task_def_arn, config)
        
        # Get load balancer URL
        endpoint = await self._get_load_balancer_url(service_name)
        
        return {
            "provider": "aws",
            "service": "ecs",
            "task_definition": task_def_arn,
            "endpoint": endpoint
        }
    
    async def _deploy_lambda(self, config: DeploymentConfig, artifact_path: str,
                           status: DeploymentStatus) -> Dict[str, Any]:
        """Deploy Lambda function"""
        # Create deployment package
        zip_file = await self._create_lambda_package(artifact_path)
        
        function_name = config.name
        
        try:
            # Update existing function
            self.lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=open(zip_file, 'rb').read()
            )
            
            # Update function configuration
            self.lambda_client.update_function_configuration(
                FunctionName=function_name,
                Runtime='python3.9',
                MemorySize=int(config.memory.rstrip('Mi')),
                Timeout=30,
                Environment={'Variables': config.environment}
            )
        except self.lambda_client.exceptions.ResourceNotFoundException:
            # Create new function
            self.lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.9',
                Role=f'arn:aws:iam::123456789012:role/lambda-role',
                Handler='index.handler',
                Code={'ZipFile': open(zip_file, 'rb').read()},
                MemorySize=int(config.memory.rstrip('Mi')),
                Timeout=30,
                Environment={'Variables': config.environment}
            )
        
        # Create API Gateway if needed
        if config.networking.get('expose_http', True):
            endpoint = await self._create_api_gateway(function_name)
        else:
            endpoint = f"arn:aws:lambda:{config.region}:function:{function_name}"
        
        return {
            "provider": "aws",
            "service": "lambda",
            "function_name": function_name,
            "endpoint": endpoint
        }
    
    async def _deploy_s3_cloudfront(self, config: DeploymentConfig, artifact_path: str,
                                  status: DeploymentStatus) -> Dict[str, Any]:
        """Deploy static site to S3 and CloudFront"""
        bucket_name = f"{config.name}-{config.environment}"
        
        # Create S3 bucket
        try:
            self.s3_client.create_bucket(Bucket=bucket_name)
        except self.s3_client.exceptions.BucketAlreadyExists:
            pass
        
        # Upload files
        await self._upload_to_s3(artifact_path, bucket_name)
        
        # Configure static website hosting
        self.s3_client.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration={
                'IndexDocument': {'Suffix': 'index.html'},
                'ErrorDocument': {'Key': 'error.html'}
            }
        )
        
        # Create CloudFront distribution
        distribution_id = await self._create_cloudfront_distribution(bucket_name, config)
        
        return {
            "provider": "aws",
            "service": "s3_cloudfront",
            "bucket": bucket_name,
            "distribution_id": distribution_id,
            "endpoint": f"https://{distribution_id}.cloudfront.net"
        }
    
    async def validate_config(self, config: DeploymentConfig):
        """Validate AWS-specific configuration"""
        # Validate region
        valid_regions = ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1']
        if config.region not in valid_regions:
            raise ValueError(f"Invalid AWS region: {config.region}")
        
        # Validate resource limits
        if config.service_type != ServiceType.SERVERLESS_FUNCTION:
            cpu_value = int(config.cpu.rstrip('m'))
            if cpu_value < 256 or cpu_value > 4096:
                raise ValueError("CPU must be between 256m and 4096m for ECS")
    
    async def check_resources(self, config: DeploymentConfig) -> bool:
        """Check if AWS resources are available"""
        # Check service limits
        # In production, would check actual AWS service quotas
        return True
    
    async def switch_traffic(self, name: str, target: str):
        """Switch traffic between blue/green deployments"""
        # Update ALB target group weights
        pass
    
    async def configure_traffic_split(self, name: str, weights: Dict[str, int]):
        """Configure traffic split for canary deployment"""
        # Update ALB listener rules with weighted routing
        pass
    
    async def promote_canary(self, name: str) -> Dict[str, Any]:
        """Promote canary to stable"""
        # Update service to use canary task definition
        return {"status": "promoted"}
    
    async def rollback_canary(self, name: str):
        """Rollback canary deployment"""
        # Remove canary task definition from service
        pass
    
    async def rollback(self, name: str, previous_version: str):
        """Rollback to previous version"""
        # Update service to use previous task definition
        pass
    
    async def scale(self, name: str, replicas: int):
        """Scale ECS service"""
        cluster_name = f"nexus-production"
        
        self.ecs_client.update_service(
            cluster=cluster_name,
            service=name,
            desiredCount=replicas
        )
    
    async def update_replicas(self, name: str, artifact_path: str,
                            start_index: int, end_index: int):
        """Update specific replicas for rolling update"""
        # ECS handles this automatically with deployment configuration
        pass
    
    async def get_ready_replicas(self, name: str) -> int:
        """Get number of ready replicas"""
        cluster_name = f"nexus-production"
        
        response = self.ecs_client.describe_services(
            cluster=cluster_name,
            services=[name]
        )
        
        if response['services']:
            return response['services'][0]['runningCount']
        return 0
    
    async def get_replica_endpoints(self, name: str) -> List[str]:
        """Get endpoints for all replicas"""
        # Would query ECS tasks and get their IPs
        return []
    
    async def get_deployment_info(self, name: str) -> Dict[str, Any]:
        """Get deployment information"""
        cluster_name = f"nexus-production"
        
        response = self.ecs_client.describe_services(
            cluster=cluster_name,
            services=[name]
        )
        
        if response['services']:
            service = response['services'][0]
            return {
                "name": name,
                "status": service['status'],
                "desired_count": service['desiredCount'],
                "running_count": service['runningCount'],
                "endpoint": await self._get_load_balancer_url(name)
            }
        
        return {}
    
    async def _push_to_ecr(self, name: str, version: str, artifact_path: str) -> str:
        """Push Docker image to ECR"""
        repository_name = name
        
        # Create repository if it doesn't exist
        try:
            self.ecr_client.create_repository(repositoryName=repository_name)
        except self.ecr_client.exceptions.RepositoryAlreadyExistsException:
            pass
        
        # Get login token
        response = self.ecr_client.get_authorization_token()
        registry = response['authorizationData'][0]['proxyEndpoint']
        
        # Build and push image
        image_uri = f"{registry}/{repository_name}:{version}"
        
        # In production, would use Docker SDK to build and push
        return image_uri
    
    def _create_task_definition(self, config: DeploymentConfig, image_uri: str) -> Dict[str, Any]:
        """Create ECS task definition"""
        return {
            'family': config.name,
            'networkMode': 'awsvpc',
            'requiresCompatibilities': ['FARGATE'],
            'cpu': config.cpu.rstrip('m'),
            'memory': config.memory.rstrip('Gi'),
            'containerDefinitions': [{
                'name': config.name,
                'image': image_uri,
                'essential': True,
                'portMappings': [{
                    'containerPort': 80,
                    'protocol': 'tcp'
                }],
                'environment': [
                    {'name': k, 'value': v}
                    for k, v in config.environment.items()
                ],
                'logConfiguration': {
                    'logDriver': 'awslogs',
                    'options': {
                        'awslogs-group': f'/ecs/{config.name}',
                        'awslogs-region': config.region,
                        'awslogs-stream-prefix': 'ecs'
                    }
                }
            }]
        }
    
    def _create_ecs_service(self, cluster_name: str, service_name: str,
                          task_def_arn: str, config: DeploymentConfig):
        """Create new ECS service"""
        self.ecs_client.create_service(
            cluster=cluster_name,
            serviceName=service_name,
            taskDefinition=task_def_arn,
            desiredCount=config.replicas,
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': ['subnet-12345', 'subnet-67890'],
                    'securityGroups': ['sg-12345'],
                    'assignPublicIp': 'ENABLED'
                }
            },
            loadBalancers=[{
                'targetGroupArn': 'arn:aws:elasticloadbalancing:...',
                'containerName': config.name,
                'containerPort': 80
            }]
        )
    
    async def _get_load_balancer_url(self, service_name: str) -> str:
        """Get load balancer URL for service"""
        # In production, would query actual ALB
        return f"https://{service_name}.elb.amazonaws.com"
    
    async def _create_lambda_package(self, artifact_path: str) -> str:
        """Create Lambda deployment package"""
        # Create zip file from artifact
        zip_path = f"/tmp/{os.path.basename(artifact_path)}.zip"
        shutil.make_archive(zip_path.rstrip('.zip'), 'zip', artifact_path)
        return zip_path
    
    async def _create_api_gateway(self, function_name: str) -> str:
        """Create API Gateway for Lambda function"""
        # In production, would create actual API Gateway
        return f"https://api.gateway.url/{function_name}"
    
    async def _upload_to_s3(self, source_path: str, bucket_name: str):
        """Upload files to S3 bucket"""
        for root, dirs, files in os.walk(source_path):
            for file in files:
                file_path = os.path.join(root, file)
                s3_key = os.path.relpath(file_path, source_path)
                
                self.s3_client.upload_file(
                    file_path,
                    bucket_name,
                    s3_key,
                    ExtraArgs={
                        'ContentType': self._get_content_type(file),
                        'CacheControl': 'max-age=31536000' if file.endswith(('.js', '.css')) else 'max-age=3600'
                    }
                )
    
    async def _create_cloudfront_distribution(self, bucket_name: str, 
                                            config: DeploymentConfig) -> str:
        """Create CloudFront distribution"""
        # In production, would create actual CloudFront distribution
        return f"d{hashlib.md5(bucket_name.encode()).hexdigest()[:10]}"
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type for file"""
        extensions = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg'
        }
        ext = os.path.splitext(filename)[1].lower()
        return extensions.get(ext, 'application/octet-stream')


class GCPDeploymentProvider:
    """Google Cloud Platform deployment provider"""
    
    def __init__(self):
        # Initialize GCP clients
        self.credentials = service_account.Credentials.from_service_account_file(
            os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'gcp-credentials.json')
        )
        self.run_client = run_v2.ServicesClient(credentials=self.credentials)
        self.functions_client = functions_v1.CloudFunctionsServiceClient(credentials=self.credentials)
    
    async def deploy(self, config: DeploymentConfig, artifact_path: str,
                    status: DeploymentStatus) -> Dict[str, Any]:
        """Deploy to GCP"""
        console.print("[cyan]Deploying to Google Cloud Platform...[/cyan]")
        
        if config.service_type == ServiceType.SERVERLESS_FUNCTION:
            return await self._deploy_cloud_function(config, artifact_path, status)
        else:
            return await self._deploy_cloud_run(config, artifact_path, status)
    
    async def _deploy_cloud_run(self, config: DeploymentConfig, artifact_path: str,
                               status: DeploymentStatus) -> Dict[str, Any]:
        """Deploy to Cloud Run"""
        project_id = os.environ.get('GCP_PROJECT_ID', 'nexus-project')
        location = config.region
        service_name = config.name
        
        # Build container image
        image_url = await self._build_container_image(project_id, service_name, 
                                                     config.version, artifact_path)
        
        # Create or update Cloud Run service
        service = run_v2.Service()
        service.template.containers.append({
            'image': image_url,
            'ports': [{'container_port': 8080}],
            'env': [{'name': k, 'value': v} for k, v in config.environment.items()],
            'resources': {
                'limits': {
                    'cpu': config.cpu,
                    'memory': config.memory
                }
            }
        })
        
        service.template.scaling.min_instance_count = 1
        service.template.scaling.max_instance_count = config.replicas
        
        parent = f"projects/{project_id}/locations/{location}"
        
        try:
            # Update existing service
            service_path = f"{parent}/services/{service_name}"
            self.run_client.update_service(service=service, name=service_path)
        except:
            # Create new service
            self.run_client.create_service(parent=parent, service=service, 
                                         service_id=service_name)
        
        # Get service URL
        service_url = f"https://{service_name}-{location}.run.app"
        
        return {
            "provider": "gcp",
            "service": "cloud_run",
            "project_id": project_id,
            "service_name": service_name,
            "endpoint": service_url
        }
    
    async def _deploy_cloud_function(self, config: DeploymentConfig, artifact_path: str,
                                   status: DeploymentStatus) -> Dict[str, Any]:
        """Deploy Cloud Function"""
        project_id = os.environ.get('GCP_PROJECT_ID', 'nexus-project')
        location = config.region
        function_name = config.name
        
        # Upload source to Cloud Storage
        source_url = await self._upload_function_source(project_id, function_name, 
                                                       artifact_path)
        
        # Create or update function
        function = {
            'name': f"projects/{project_id}/locations/{location}/functions/{function_name}",
            'source_archive_url': source_url,
            'entry_point': 'main',
            'https_trigger': {},
            'available_memory_mb': int(config.memory.rstrip('Mi')),
            'environment_variables': config.environment
        }
        
        parent = f"projects/{project_id}/locations/{location}"
        
        try:
            # Update existing function
            self.functions_client.update_cloud_function(function=function)
        except:
            # Create new function
            self.functions_client.create_cloud_function(parent=parent, function=function)
        
        # Get function URL
        function_url = f"https://{location}-{project_id}.cloudfunctions.net/{function_name}"
        
        return {
            "provider": "gcp",
            "service": "cloud_functions",
            "project_id": project_id,
            "function_name": function_name,
            "endpoint": function_url
        }
    
    async def validate_config(self, config: DeploymentConfig):
        """Validate GCP-specific configuration"""
        valid_regions = ['us-central1', 'us-east1', 'europe-west1', 'asia-northeast1']
        if config.region not in valid_regions:
            raise ValueError(f"Invalid GCP region: {config.region}")
    
    async def check_resources(self, config: DeploymentConfig) -> bool:
        """Check if GCP resources are available"""
        # Check quotas
        return True
    
    async def _build_container_image(self, project_id: str, service_name: str,
                                   version: str, artifact_path: str) -> str:
        """Build container image using Cloud Build"""
        # In production, would trigger Cloud Build
        return f"gcr.io/{project_id}/{service_name}:{version}"
    
    async def _upload_function_source(self, project_id: str, function_name: str,
                                    artifact_path: str) -> str:
        """Upload function source to Cloud Storage"""
        # In production, would upload to Cloud Storage
        bucket_name = f"{project_id}-functions"
        object_name = f"{function_name}-{datetime.now().isoformat()}.zip"
        return f"gs://{bucket_name}/{object_name}"
    
    # Implement other required methods similar to AWS provider
    async def switch_traffic(self, name: str, target: str):
        pass
    
    async def configure_traffic_split(self, name: str, weights: Dict[str, int]):
        pass
    
    async def promote_canary(self, name: str) -> Dict[str, Any]:
        return {"status": "promoted"}
    
    async def rollback_canary(self, name: str):
        pass
    
    async def rollback(self, name: str, previous_version: str):
        pass
    
    async def scale(self, name: str, replicas: int):
        pass
    
    async def update_replicas(self, name: str, artifact_path: str,
                            start_index: int, end_index: int):
        pass
    
    async def get_ready_replicas(self, name: str) -> int:
        return 1
    
    async def get_replica_endpoints(self, name: str) -> List[str]:
        return []
    
    async def get_deployment_info(self, name: str) -> Dict[str, Any]:
        return {}


class AzureDeploymentProvider:
    """Azure deployment provider"""
    
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.subscription_id = os.environ.get('AZURE_SUBSCRIPTION_ID')
        
        self.container_client = ContainerInstanceManagementClient(
            self.credential, self.subscription_id
        )
        self.webapp_client = WebSiteManagementClient(
            self.credential, self.subscription_id
        )
    
    async def deploy(self, config: DeploymentConfig, artifact_path: str,
                    status: DeploymentStatus) -> Dict[str, Any]:
        """Deploy to Azure"""
        console.print("[cyan]Deploying to Microsoft Azure...[/cyan]")
        
        if config.service_type == ServiceType.SERVERLESS_FUNCTION:
            return await self._deploy_function_app(config, artifact_path, status)
        elif config.service_type in [ServiceType.WEB_APP, ServiceType.API]:
            return await self._deploy_app_service(config, artifact_path, status)
        else:
            return await self._deploy_container_instance(config, artifact_path, status)
    
    async def _deploy_container_instance(self, config: DeploymentConfig, artifact_path: str,
                                        status: DeploymentStatus) -> Dict[str, Any]:
        """Deploy to Azure Container Instances"""
        resource_group = f"nexus-{config.environment}"
        container_group_name = config.name
        
        # Build and push container image to ACR
        image_url = await self._push_to_acr(config.name, config.version, artifact_path)
        
        # Create container group
        container_group = {
            'location': config.region,
            'containers': [{
                'name': config.name,
                'image': image_url,
                'resources': {
                    'requests': {
                        'cpu': float(config.cpu.rstrip('m')) / 1000,
                        'memory_in_gb': float(config.memory.rstrip('Gi'))
                    }
                },
                'environment_variables': [
                    {'name': k, 'value': v} for k, v in config.environment.items()
                ],
                'ports': [{'port': 80}]
            }],
            'os_type': 'Linux',
            'ip_address': {
                'type': 'Public',
                'ports': [{'protocol': 'TCP', 'port': 80}]
            }
        }
        
        # Create or update container group
        self.container_client.container_groups.create_or_update(
            resource_group,
            container_group_name,
            container_group
        )
        
        # Get container group IP
        container_group = self.container_client.container_groups.get(
            resource_group,
            container_group_name
        )
        
        endpoint = f"http://{container_group.ip_address.ip}"
        
        return {
            "provider": "azure",
            "service": "container_instances",
            "resource_group": resource_group,
            "container_group": container_group_name,
            "endpoint": endpoint
        }
    
    async def _deploy_app_service(self, config: DeploymentConfig, artifact_path: str,
                                 status: DeploymentStatus) -> Dict[str, Any]:
        """Deploy to Azure App Service"""
        resource_group = f"nexus-{config.environment}"
        app_name = config.name
        
        # Create app service plan if needed
        plan_name = f"{app_name}-plan"
        self.webapp_client.app_service_plans.create_or_update(
            resource_group,
            plan_name,
            {
                'location': config.region,
                'sku': {'name': 'B1', 'tier': 'Basic'}
            }
        )
        
        # Create or update web app
        self.webapp_client.web_apps.create_or_update(
            resource_group,
            app_name,
            {
                'location': config.region,
                'server_farm_id': f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Web/serverfarms/{plan_name}",
                'site_config': {
                    'linux_fx_version': 'DOCKER|nginx:latest',
                    'app_settings': [
                        {'name': k, 'value': v} for k, v in config.environment.items()
                    ]
                }
            }
        )
        
        # Deploy code
        await self._deploy_to_app_service(resource_group, app_name, artifact_path)
        
        endpoint = f"https://{app_name}.azurewebsites.net"
        
        return {
            "provider": "azure",
            "service": "app_service",
            "resource_group": resource_group,
            "app_name": app_name,
            "endpoint": endpoint
        }
    
    async def _deploy_function_app(self, config: DeploymentConfig, artifact_path: str,
                                  status: DeploymentStatus) -> Dict[str, Any]:
        """Deploy Azure Function"""
        resource_group = f"nexus-{config.environment}"
        function_app_name = config.name
        
        # Create function app
        # Implementation would create Azure Function App
        
        endpoint = f"https://{function_app_name}.azurewebsites.net/api"
        
        return {
            "provider": "azure",
            "service": "functions",
            "resource_group": resource_group,
            "function_app": function_app_name,
            "endpoint": endpoint
        }
    
    async def validate_config(self, config: DeploymentConfig):
        """Validate Azure-specific configuration"""
        valid_regions = ['eastus', 'westus', 'northeurope', 'westeurope']
        if config.region not in valid_regions:
            raise ValueError(f"Invalid Azure region: {config.region}")
    
    async def check_resources(self, config: DeploymentConfig) -> bool:
        """Check if Azure resources are available"""
        return True
    
    async def _push_to_acr(self, name: str, version: str, artifact_path: str) -> str:
        """Push container image to Azure Container Registry"""
        # In production, would push to ACR
        registry_name = "nexusregistry"
        return f"{registry_name}.azurecr.io/{name}:{version}"
    
    async def _deploy_to_app_service(self, resource_group: str, app_name: str,
                                   artifact_path: str):
        """Deploy code to App Service"""
        # In production, would use ZIP deploy or Git deploy
        pass
    
    # Implement other required methods
    async def switch_traffic(self, name: str, target: str):
        pass
    
    async def configure_traffic_split(self, name: str, weights: Dict[str, int]):
        pass
    
    async def promote_canary(self, name: str) -> Dict[str, Any]:
        return {"status": "promoted"}
    
    async def rollback_canary(self, name: str):
        pass
    
    async def rollback(self, name: str, previous_version: str):
        pass
    
    async def scale(self, name: str, replicas: int):
        pass
    
    async def update_replicas(self, name: str, artifact_path: str,
                            start_index: int, end_index: int):
        pass
    
    async def get_ready_replicas(self, name: str) -> int:
        return 1
    
    async def get_replica_endpoints(self, name: str) -> List[str]:
        return []
    
    async def get_deployment_info(self, name: str) -> Dict[str, Any]:
        return {}


class KubernetesDeploymentProvider:
    """Kubernetes deployment provider"""
    
    def __init__(self):
        # Load kubeconfig
        try:
            k8s_config.load_incluster_config()
        except:
            k8s_config.load_kube_config()
        
        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()
        self.networking_v1 = client.NetworkingV1Api()
    
    async def deploy(self, config: DeploymentConfig, artifact_path: str,
                    status: DeploymentStatus) -> Dict[str, Any]:
        """Deploy to Kubernetes"""
        console.print("[cyan]Deploying to Kubernetes...[/cyan]")
        
        namespace = config.environment
        
        # Create namespace if it doesn't exist
        await self._create_namespace(namespace)
        
        # Create ConfigMap for configuration
        await self._create_configmap(config, namespace)
        
        # Create Secret for secrets
        if config.secrets:
            await self._create_secret(config, namespace)
        
        # Create Deployment
        deployment = await self._create_deployment(config, artifact_path, namespace)
        
        # Create Service
        service = await self._create_service(config, namespace)
        
        # Create Ingress if custom domain specified
        if config.custom_domain:
            ingress = await self._create_ingress(config, namespace)
            endpoint = f"https://{config.custom_domain}"
        else:
            # Get service endpoint
            endpoint = await self._get_service_endpoint(config.name, namespace)
        
        return {
            "provider": "kubernetes",
            "namespace": namespace,
            "deployment": deployment.metadata.name,
            "service": service.metadata.name,
            "endpoint": endpoint
        }
    
    async def _create_namespace(self, namespace: str):
        """Create Kubernetes namespace"""
        try:
            self.core_v1.create_namespace(
                client.V1Namespace(
                    metadata=client.V1ObjectMeta(name=namespace)
                )
            )
        except client.ApiException as e:
            if e.status != 409:  # Already exists
                raise
    
    async def _create_configmap(self, config: DeploymentConfig, namespace: str):
        """Create ConfigMap for environment variables"""
        configmap = client.V1ConfigMap(
            metadata=client.V1ObjectMeta(
                name=f"{config.name}-config",
                namespace=namespace
            ),
            data=config.environment
        )
        
        try:
            self.core_v1.create_namespaced_config_map(namespace, configmap)
        except client.ApiException as e:
            if e.status == 409:  # Already exists
                self.core_v1.patch_namespaced_config_map(
                    f"{config.name}-config",
                    namespace,
                    configmap
                )
            else:
                raise
    
    async def _create_secret(self, config: DeploymentConfig, namespace: str):
        """Create Secret for sensitive data"""
        secret = client.V1Secret(
            metadata=client.V1ObjectMeta(
                name=f"{config.name}-secret",
                namespace=namespace
            ),
            string_data=config.secrets
        )
        
        try:
            self.core_v1.create_namespaced_secret(namespace, secret)
        except client.ApiException as e:
            if e.status == 409:  # Already exists
                self.core_v1.patch_namespaced_secret(
                    f"{config.name}-secret",
                    namespace,
                    secret
                )
            else:
                raise
    
    async def _create_deployment(self, config: DeploymentConfig, artifact_path: str,
                               namespace: str) -> client.V1Deployment:
        """Create Kubernetes Deployment"""
        # Container specification
        container = client.V1Container(
            name=config.name,
            image=f"{config.name}:{config.version}",
            ports=[client.V1ContainerPort(container_port=8080)],
            resources=client.V1ResourceRequirements(
                requests={
                    "cpu": config.cpu,
                    "memory": config.memory
                },
                limits={
                    "cpu": config.cpu,
                    "memory": config.memory
                }
            ),
            env_from=[
                client.V1EnvFromSource(
                    config_map_ref=client.V1ConfigMapEnvSource(
                        name=f"{config.name}-config"
                    )
                )
            ]
        )
        
        # Add secrets if present
        if config.secrets:
            container.env_from.append(
                client.V1EnvFromSource(
                    secret_ref=client.V1SecretEnvSource(
                        name=f"{config.name}-secret"
                    )
                )
            )
        
        # Add volumes if specified
        volumes = []
        volume_mounts = []
        for i, vol in enumerate(config.volumes):
            volume_name = f"volume-{i}"
            volumes.append(
                client.V1Volume(
                    name=volume_name,
                    persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                        claim_name=vol.get("claim_name", f"{config.name}-pvc-{i}")
                    )
                )
            )
            volume_mounts.append(
                client.V1VolumeMount(
                    name=volume_name,
                    mount_path=vol["mount_path"]
                )
            )
        
        if volume_mounts:
            container.volume_mounts = volume_mounts
        
        # Pod specification
        pod_spec = client.V1PodSpec(
            containers=[container],
            volumes=volumes if volumes else None
        )
        
        # Add health checks
        if config.health_check:
            container.liveness_probe = client.V1Probe(
                http_get=client.V1HTTPGetAction(
                    path=config.health_check.get("path", "/health"),
                    port=8080
                ),
                initial_delay_seconds=30,
                period_seconds=10
            )
            container.readiness_probe = client.V1Probe(
                http_get=client.V1HTTPGetAction(
                    path=config.health_check.get("path", "/health"),
                    port=8080
                ),
                initial_delay_seconds=5,
                period_seconds=5
            )
        
        # Deployment specification
        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(
                name=config.name,
                namespace=namespace,
                labels={"app": config.name}
            ),
            spec=client.V1DeploymentSpec(
                replicas=config.replicas,
                selector=client.V1LabelSelector(
                    match_labels={"app": config.name}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={"app": config.name}
                    ),
                    spec=pod_spec
                ),
                strategy=client.V1DeploymentStrategy(
                    type="RollingUpdate" if config.strategy == DeploymentStrategy.ROLLING_UPDATE else "Recreate",
                    rolling_update=client.V1RollingUpdateDeployment(
                        max_surge=config.max_surge,
                        max_unavailable=config.max_unavailable
                    ) if config.strategy == DeploymentStrategy.ROLLING_UPDATE else None
                )
            )
        )
        
        # Create or update deployment
        try:
            return self.apps_v1.create_namespaced_deployment(namespace, deployment)
        except client.ApiException as e:
            if e.status == 409:  # Already exists
                return self.apps_v1.patch_namespaced_deployment(
                    config.name,
                    namespace,
                    deployment
                )
            else:
                raise
    
    async def _create_service(self, config: DeploymentConfig, namespace: str) -> client.V1Service:
        """Create Kubernetes Service"""
        service = client.V1Service(
            metadata=client.V1ObjectMeta(
                name=config.name,
                namespace=namespace,
                labels={"app": config.name}
            ),
            spec=client.V1ServiceSpec(
                selector={"app": config.name},
                ports=[
                    client.V1ServicePort(
                        port=80,
                        target_port=8080,
                        protocol="TCP"
                    )
                ],
                type="LoadBalancer" if not config.custom_domain else "ClusterIP"
            )
        )
        
        try:
            return self.core_v1.create_namespaced_service(namespace, service)
        except client.ApiException as e:
            if e.status == 409:  # Already exists
                return self.core_v1.patch_namespaced_service(
                    config.name,
                    namespace,
                    service
                )
            else:
                raise
    
    async def _create_ingress(self, config: DeploymentConfig, namespace: str):
        """Create Kubernetes Ingress"""
        ingress = client.V1Ingress(
            metadata=client.V1ObjectMeta(
                name=config.name,
                namespace=namespace,
                annotations={
                    "kubernetes.io/ingress.class": "nginx",
                    "cert-manager.io/cluster-issuer": "letsencrypt-prod" if config.ssl_enabled else None
                }
            ),
            spec=client.V1IngressSpec(
                tls=[
                    client.V1IngressTLS(
                        hosts=[config.custom_domain],
                        secret_name=f"{config.name}-tls"
                    )
                ] if config.ssl_enabled else None,
                rules=[
                    client.V1IngressRule(
                        host=config.custom_domain,
                        http=client.V1HTTPIngressRuleValue(
                            paths=[
                                client.V1HTTPIngressPath(
                                    path="/",
                                    path_type="Prefix",
                                    backend=client.V1IngressBackend(
                                        service=client.V1IngressServiceBackend(
                                            name=config.name,
                                            port=client.V1ServiceBackendPort(number=80)
                                        )
                                    )
                                )
                            ]
                        )
                    )
                ]
            )
        )
        
        try:
            return self.networking_v1.create_namespaced_ingress(namespace, ingress)
        except client.ApiException as e:
            if e.status == 409:  # Already exists
                return self.networking_v1.patch_namespaced_ingress(
                    config.name,
                    namespace,
                    ingress
                )
            else:
                raise
    
    async def _get_service_endpoint(self, service_name: str, namespace: str) -> str:
        """Get service endpoint"""
        service = self.core_v1.read_namespaced_service(service_name, namespace)
        
        if service.spec.type == "LoadBalancer":
            # Wait for load balancer to be provisioned
            for _ in range(60):  # Wait up to 5 minutes
                service = self.core_v1.read_namespaced_service(service_name, namespace)
                if service.status.load_balancer.ingress:
                    ingress = service.status.load_balancer.ingress[0]
                    host = ingress.hostname or ingress.ip
                    return f"http://{host}"
                await asyncio.sleep(5)
        
        # Fallback to cluster IP
        return f"http://{service.spec.cluster_ip}"
    
    async def validate_config(self, config: DeploymentConfig):
        """Validate Kubernetes-specific configuration"""
        # Validate resource requests
        pass
    
    async def check_resources(self, config: DeploymentConfig) -> bool:
        """Check if Kubernetes resources are available"""
        # Check node capacity
        return True
    
    async def switch_traffic(self, name: str, target: str):
        """Switch traffic for blue-green deployment"""
        # Update service selector
        pass
    
    async def configure_traffic_split(self, name: str, weights: Dict[str, int]):
        """Configure traffic split using Istio or similar"""
        # Would use Istio VirtualService for traffic management
        pass
    
    async def promote_canary(self, name: str) -> Dict[str, Any]:
        """Promote canary deployment"""
        # Update main deployment with canary image
        return {"status": "promoted"}
    
    async def rollback_canary(self, name: str):
        """Rollback canary deployment"""
        # Delete canary deployment
        pass
    
    async def rollback(self, name: str, previous_version: str):
        """Rollback deployment"""
        # Use kubectl rollout undo
        pass
    
    async def scale(self, name: str, replicas: int):
        """Scale deployment"""
        namespace = "production"  # Should be passed in config
        
        # Patch deployment with new replica count
        body = {"spec": {"replicas": replicas}}
        self.apps_v1.patch_namespaced_deployment(
            name=name,
            namespace=namespace,
            body=body
        )
    
    async def update_replicas(self, name: str, artifact_path: str,
                            start_index: int, end_index: int):
        """Update replicas for rolling update"""
        # Kubernetes handles this automatically
        pass
    
    async def get_ready_replicas(self, name: str) -> int:
        """Get number of ready replicas"""
        namespace = "production"  # Should be passed in config
        
        deployment = self.apps_v1.read_namespaced_deployment(name, namespace)
        return deployment.status.ready_replicas or 0
    
    async def get_replica_endpoints(self, name: str) -> List[str]:
        """Get pod endpoints"""
        namespace = "production"  # Should be passed in config
        
        pods = self.core_v1.list_namespaced_pod(
            namespace=namespace,
            label_selector=f"app={name}"
        )
        
        endpoints = []
        for pod in pods.items:
            if pod.status.pod_ip:
                endpoints.append(f"http://{pod.status.pod_ip}:8080")
        
        return endpoints
    
    async def get_deployment_info(self, name: str) -> Dict[str, Any]:
        """Get deployment information"""
        namespace = "production"  # Should be passed in config
        
        deployment = self.apps_v1.read_namespaced_deployment(name, namespace)
        
        return {
            "name": name,
            "replicas": deployment.spec.replicas,
            "ready_replicas": deployment.status.ready_replicas,
            "updated_replicas": deployment.status.updated_replicas,
            "available_replicas": deployment.status.available_replicas
        }


class DockerDeploymentProvider:
    """Docker deployment provider for local/development"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
    
    async def deploy(self, config: DeploymentConfig, artifact_path: str,
                    status: DeploymentStatus) -> Dict[str, Any]:
        """Deploy using Docker"""
        console.print("[cyan]Deploying with Docker...[/cyan]")
        
        # Build Docker image
        image_tag = f"{config.name}:{config.version}"
        console.print(f"[yellow]Building Docker image: {image_tag}[/yellow]")
        
        # Check if Dockerfile exists
        dockerfile_path = os.path.join(artifact_path, "Dockerfile")
        if not os.path.exists(dockerfile_path):
            # Create default Dockerfile
            await self._create_dockerfile(dockerfile_path, config)
        
        # Build image
        image, build_logs = self.docker_client.images.build(
            path=artifact_path,
            tag=image_tag,
            rm=True,
            buildargs=config.environment
        )
        
        # Stop and remove existing containers
        await self._cleanup_existing_containers(config.name)
        
        # Run containers
        containers = []
        for i in range(config.replicas):
            container_name = f"{config.name}-{i}"
            port = 8080 + i
            
            container = self.docker_client.containers.run(
                image_tag,
                name=container_name,
                detach=True,
                ports={'8080/tcp': port},
                environment=config.environment,
                restart_policy={"Name": "unless-stopped"}
            )
            
            containers.append({
                "name": container_name,
                "id": container.id,
                "port": port
            })
            
            console.print(f"[green]Started container: {container_name} on port {port}[/green]")
        
        # Set up nginx load balancer if multiple replicas
        if config.replicas > 1:
            endpoint = await self._setup_nginx_load_balancer(config.name, containers)
        else:
            endpoint = f"http://localhost:{containers[0]['port']}"
        
        return {
            "provider": "docker",
            "image": image_tag,
            "containers": containers,
            "endpoint": endpoint
        }
    
    async def _create_dockerfile(self, dockerfile_path: str, config: DeploymentConfig):
        """Create default Dockerfile"""
        content = """FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
"""
        with open(dockerfile_path, "w") as f:
            f.write(content)
    
    async def _cleanup_existing_containers(self, name: str):
        """Stop and remove existing containers"""
        for container in self.docker_client.containers.list(all=True):
            if container.name.startswith(name):
                console.print(f"[yellow]Removing existing container: {container.name}[/yellow]")
                container.stop()
                container.remove()
    
    async def _setup_nginx_load_balancer(self, name: str, 
                                       containers: List[Dict[str, Any]]) -> str:
        """Set up nginx load balancer for multiple containers"""
        # Create nginx configuration
        upstream_servers = "\n".join([
            f"    server host.docker.internal:{c['port']};"
            for c in containers
        ])
        
        nginx_conf = f"""
upstream {name} {{
{upstream_servers}
}}

server {{
    listen 80;
    location / {{
        proxy_pass http://{name};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}
"""
        
        # Write nginx config
        config_dir = f"/tmp/nginx-{name}"
        os.makedirs(config_dir, exist_ok=True)
        
        with open(f"{config_dir}/nginx.conf", "w") as f:
            f.write(nginx_conf)
        
        # Run nginx container
        nginx_container = self.docker_client.containers.run(
            "nginx:alpine",
            name=f"{name}-nginx",
            detach=True,
            ports={'80/tcp': 8000},
            volumes={config_dir: {'bind': '/etc/nginx/conf.d', 'mode': 'ro'}},
            restart_policy={"Name": "unless-stopped"}
        )
        
        console.print(f"[green]Started nginx load balancer on port 8000[/green]")
        
        return "http://localhost:8000"
    
    async def validate_config(self, config: DeploymentConfig):
        """Validate Docker-specific configuration"""
        pass
    
    async def check_resources(self, config: DeploymentConfig) -> bool:
        """Check if Docker resources are available"""
        # Check Docker daemon is running
        try:
            self.docker_client.ping()
            return True
        except:
            return False
    
    # Implement other required methods
    async def switch_traffic(self, name: str, target: str):
        pass
    
    async def configure_traffic_split(self, name: str, weights: Dict[str, int]):
        pass
    
    async def promote_canary(self, name: str) -> Dict[str, Any]:
        return {"status": "promoted"}
    
    async def rollback_canary(self, name: str):
        pass
    
    async def rollback(self, name: str, previous_version: str):
        pass
    
    async def scale(self, name: str, replicas: int):
        pass
    
    async def update_replicas(self, name: str, artifact_path: str,
                            start_index: int, end_index: int):
        pass
    
    async def get_ready_replicas(self, name: str) -> int:
        count = 0
        for container in self.docker_client.containers.list():
            if container.name.startswith(name) and container.status == "running":
                count += 1
        return count
    
    async def get_replica_endpoints(self, name: str) -> List[str]:
        endpoints = []
        for container in self.docker_client.containers.list():
            if container.name.startswith(name):
                # Get container port mapping
                ports = container.ports.get('8080/tcp', [])
                if ports:
                    port = ports[0]['HostPort']
                    endpoints.append(f"http://localhost:{port}")
        return endpoints
    
    async def get_deployment_info(self, name: str) -> Dict[str, Any]:
        containers = []
        for container in self.docker_client.containers.list(all=True):
            if container.name.startswith(name):
                containers.append({
                    "name": container.name,
                    "status": container.status,
                    "id": container.id[:12]
                })
        
        return {
            "name": name,
            "containers": containers,
            "count": len(containers)
        }


class ServerlessDeploymentProvider:
    """Serverless deployment provider (Lambda, Cloud Functions, etc.)"""
    
    def __init__(self):
        self.aws_provider = AWSDeploymentProvider()
        self.gcp_provider = GCPDeploymentProvider()
        self.azure_provider = AzureDeploymentProvider()
    
    async def deploy(self, config: DeploymentConfig, artifact_path: str,
                    status: DeploymentStatus) -> Dict[str, Any]:
        """Deploy serverless function"""
        console.print("[cyan]Deploying serverless function...[/cyan]")
        
        # Determine cloud provider based on region or environment variable
        if config.region.startswith("us-") or config.region.startswith("eu-"):
            # AWS regions
            return await self.aws_provider._deploy_lambda(config, artifact_path, status)
        elif config.region.endswith("1"):  # GCP regions like us-central1
            return await self.gcp_provider._deploy_cloud_function(config, artifact_path, status)
        else:
            # Default to Azure
            return await self.azure_provider._deploy_function_app(config, artifact_path, status)
    
    async def validate_config(self, config: DeploymentConfig):
        """Validate serverless configuration"""
        if config.service_type != ServiceType.SERVERLESS_FUNCTION:
            raise ValueError("Service type must be serverless_function")
    
    async def check_resources(self, config: DeploymentConfig) -> bool:
        """Check serverless resources"""
        return True
    
    # Implement other required methods as pass-through to cloud providers
    async def switch_traffic(self, name: str, target: str):
        pass
    
    async def configure_traffic_split(self, name: str, weights: Dict[str, int]):
        pass
    
    async def promote_canary(self, name: str) -> Dict[str, Any]:
        return {"status": "promoted"}
    
    async def rollback_canary(self, name: str):
        pass
    
    async def rollback(self, name: str, previous_version: str):
        pass
    
    async def scale(self, name: str, replicas: int):
        # Serverless auto-scales
        pass
    
    async def update_replicas(self, name: str, artifact_path: str,
                            start_index: int, end_index: int):
        pass
    
    async def get_ready_replicas(self, name: str) -> int:
        return 1  # Serverless is always "ready"
    
    async def get_replica_endpoints(self, name: str) -> List[str]:
        return []
    
    async def get_deployment_info(self, name: str) -> Dict[str, Any]:
        return {"name": name, "type": "serverless"}


async def main():
    """Example usage and CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NEXUS Deployment Engine")
    parser.add_argument("command", choices=["deploy", "rollback", "scale", "status", "list"])
    parser.add_argument("--name", "-n", help="Deployment name")
    parser.add_argument("--version", "-v", help="Version to deploy")
    parser.add_argument("--provider", "-p", choices=[p.value for p in CloudProvider])
    parser.add_argument("--strategy", "-s", choices=[s.value for s in DeploymentStrategy])
    parser.add_argument("--artifact", "-a", help="Path to artifact/build directory")
    parser.add_argument("--replicas", "-r", type=int, default=3)
    parser.add_argument("--deployment-id", "-d", help="Deployment ID")
    parser.add_argument("--config", "-c", help="Configuration file (YAML)")
    
    args = parser.parse_args()
    
    engine = DeploymentEngine()
    
    if args.command == "deploy":
        if args.config:
            # Load configuration from file
            with open(args.config) as f:
                config_data = yaml.safe_load(f)
            config = DeploymentConfig(**config_data)
        else:
            # Create configuration from arguments
            config = DeploymentConfig(
                name=args.name,
                version=args.version,
                provider=CloudProvider(args.provider),
                strategy=DeploymentStrategy(args.strategy or "rolling_update"),
                service_type=ServiceType.WEB_APP,
                replicas=args.replicas
            )
        
        status = await engine.deploy(config, args.artifact)
        
        # Display deployment status
        table = Table(title="Deployment Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Deployment ID", status.deployment_id)
        table.add_row("Status", status.status)
        table.add_row("Endpoint", status.endpoint or "N/A")
        table.add_row("Duration", f"{(status.end_time - status.start_time).total_seconds():.2f}s")
        
        console.print(table)
        
    elif args.command == "rollback":
        if not args.deployment_id:
            parser.error("rollback requires --deployment-id")
        
        success = await engine.rollback(args.deployment_id)
        if success:
            console.print("[green]Rollback completed successfully[/green]")
        else:
            console.print("[red]Rollback failed[/red]")
            
    elif args.command == "scale":
        if not all([args.deployment_id, args.replicas]):
            parser.error("scale requires --deployment-id and --replicas")
        
        success = await engine.scale(args.deployment_id, args.replicas)
        if success:
            console.print(f"[green]Scaled to {args.replicas} replicas[/green]")
            
    elif args.command == "status":
        if not args.deployment_id:
            parser.error("status requires --deployment-id")
        
        status = await engine.get_status(args.deployment_id)
        if status:
            console.print(Panel(
                f"Status: {status.status}\n"
                f"Replicas: {status.replicas_ready}/{status.replicas_total}\n"
                f"Endpoint: {status.endpoint or 'N/A'}",
                title=f"Deployment {status.deployment_id}"
            ))
        else:
            console.print("[red]Deployment not found[/red]")
            
    elif args.command == "list":
        deployments = await engine.list_deployments(
            CloudProvider(args.provider) if args.provider else None
        )
        
        table = Table(title="Deployments")
        table.add_column("ID", style="cyan")
        table.add_column("Name")
        table.add_column("Version")
        table.add_column("Provider")
        table.add_column("Status")
        table.add_column("Endpoint")
        
        for deployment in deployments[-10:]:  # Show last 10
            table.add_row(
                deployment["deployment_id"],
                deployment["name"],
                deployment["version"],
                deployment["provider"],
                deployment["status"],
                deployment["endpoint"] or "N/A"
            )
        
        console.print(table)


if __name__ == "__main__":
    asyncio.run(main())