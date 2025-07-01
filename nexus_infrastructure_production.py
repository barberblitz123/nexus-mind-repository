"""
NEXUS Infrastructure as Code - Production infrastructure management
Supports Terraform, CloudFormation, Pulumi with multi-cloud provisioning
"""

import asyncio
import json
import yaml
import subprocess
import os
import shutil
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import hashlib
import boto3
from google.cloud import compute_v1, storage
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.identity import DefaultAzureCredential
import pulumi
from pulumi import automation as auto
import jinja2

class CloudProvider(Enum):
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    MULTI_CLOUD = "multi_cloud"

class IaCTool(Enum):
    TERRAFORM = "terraform"
    CLOUDFORMATION = "cloudformation"
    PULUMI = "pulumi"
    CDK = "cdk"
    ARM = "arm"

class ResourceType(Enum):
    COMPUTE = "compute"
    NETWORK = "network"
    STORAGE = "storage"
    DATABASE = "database"
    KUBERNETES = "kubernetes"
    SERVERLESS = "serverless"
    CDN = "cdn"
    DNS = "dns"
    SECURITY = "security"
    MONITORING = "monitoring"

@dataclass
class ResourceConfig:
    """Configuration for a cloud resource"""
    name: str
    type: ResourceType
    provider: CloudProvider
    region: str
    specifications: Dict[str, Any]
    tags: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    outputs: Dict[str, str] = field(default_factory=dict)

@dataclass
class InfrastructureStack:
    """Infrastructure stack configuration"""
    name: str
    environment: str
    provider: CloudProvider
    tool: IaCTool
    resources: List[ResourceConfig]
    variables: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, str] = field(default_factory=dict)
    backend_config: Dict[str, str] = field(default_factory=dict)

@dataclass
class DeploymentResult:
    """Result of infrastructure deployment"""
    stack_name: str
    status: str
    outputs: Dict[str, Any]
    resources_created: List[str]
    duration: float
    errors: List[str] = field(default_factory=list)

class TerraformProvider:
    """Manages Terraform infrastructure"""
    
    def __init__(self, working_dir: str = "./terraform"):
        self.working_dir = Path(working_dir)
        self.working_dir.mkdir(parents=True, exist_ok=True)
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader("./terraform_templates")
        )
    
    async def generate_configuration(self, stack: InfrastructureStack) -> str:
        """Generate Terraform configuration"""
        # Main configuration
        main_tf = self._generate_main_tf(stack)
        
        # Variables
        variables_tf = self._generate_variables_tf(stack)
        
        # Outputs
        outputs_tf = self._generate_outputs_tf(stack)
        
        # Provider configuration
        provider_tf = self._generate_provider_tf(stack)
        
        # Save configurations
        stack_dir = self.working_dir / stack.name
        stack_dir.mkdir(parents=True, exist_ok=True)
        
        with open(stack_dir / "main.tf", "w") as f:
            f.write(main_tf)
        
        with open(stack_dir / "variables.tf", "w") as f:
            f.write(variables_tf)
        
        with open(stack_dir / "outputs.tf", "w") as f:
            f.write(outputs_tf)
        
        with open(stack_dir / "provider.tf", "w") as f:
            f.write(provider_tf)
        
        # Generate terraform.tfvars
        tfvars = self._generate_tfvars(stack)
        with open(stack_dir / "terraform.tfvars", "w") as f:
            f.write(tfvars)
        
        return str(stack_dir)
    
    def _generate_provider_tf(self, stack: InfrastructureStack) -> str:
        """Generate provider configuration"""
        provider_configs = {
            CloudProvider.AWS: """
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "{backend_bucket}"
    key    = "{stack_name}/terraform.tfstate"
    region = "{backend_region}"
    encrypt = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = var.region
  
  default_tags {
    tags = var.default_tags
  }
}
""",
            CloudProvider.GCP: """
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  
  backend "gcs" {
    bucket = "{backend_bucket}"
    prefix = "{stack_name}"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
""",
            CloudProvider.AZURE: """
terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  
  backend "azurerm" {
    resource_group_name  = "{backend_rg}"
    storage_account_name = "{backend_storage}"
    container_name       = "tfstate"
    key                  = "{stack_name}.tfstate"
  }
}

provider "azurerm" {
  features {}
}
"""
        }
        
        template = provider_configs.get(stack.provider, provider_configs[CloudProvider.AWS])
        return template.format(
            backend_bucket=stack.backend_config.get("bucket", "nexus-terraform-state"),
            backend_region=stack.backend_config.get("region", "us-east-1"),
            backend_rg=stack.backend_config.get("resource_group", "nexus-terraform"),
            backend_storage=stack.backend_config.get("storage_account", "nexustfstate"),
            stack_name=stack.name
        )
    
    def _generate_main_tf(self, stack: InfrastructureStack) -> str:
        """Generate main Terraform configuration"""
        resources = []
        
        for resource in stack.resources:
            if resource.type == ResourceType.COMPUTE:
                resources.append(self._generate_compute_resource(resource, stack.provider))
            elif resource.type == ResourceType.NETWORK:
                resources.append(self._generate_network_resource(resource, stack.provider))
            elif resource.type == ResourceType.DATABASE:
                resources.append(self._generate_database_resource(resource, stack.provider))
            elif resource.type == ResourceType.KUBERNETES:
                resources.append(self._generate_kubernetes_resource(resource, stack.provider))
            elif resource.type == ResourceType.STORAGE:
                resources.append(self._generate_storage_resource(resource, stack.provider))
            elif resource.type == ResourceType.CDN:
                resources.append(self._generate_cdn_resource(resource, stack.provider))
        
        return "\n\n".join(resources)
    
    def _generate_compute_resource(self, resource: ResourceConfig, provider: CloudProvider) -> str:
        """Generate compute resource configuration"""
        if provider == CloudProvider.AWS:
            return f"""
# EC2 Instance: {resource.name}
resource "aws_instance" "{resource.name}" {{
  ami           = "{resource.specifications.get('ami', 'ami-0c02fb55956c7d316')}"
  instance_type = "{resource.specifications.get('instance_type', 't3.medium')}"
  key_name      = var.key_name
  
  vpc_security_group_ids = [aws_security_group.{resource.name}_sg.id]
  subnet_id              = aws_subnet.main.id
  
  root_block_device {{
    volume_type = "gp3"
    volume_size = {resource.specifications.get('disk_size', 30)}
    encrypted   = true
  }}
  
  user_data = file("${{path.module}}/user_data/{resource.name}.sh")
  
  tags = merge(
    var.default_tags,
    {{
      Name = "{resource.name}"
      Type = "compute"
    }}
  )
}}

# Security Group for {resource.name}
resource "aws_security_group" "{resource.name}_sg" {{
  name        = "{resource.name}-sg"
  description = "Security group for {resource.name}"
  vpc_id      = aws_vpc.main.id
  
  ingress {{
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidr_blocks
  }}
  
  ingress {{
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}
  
  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}
  
  tags = var.default_tags
}}
"""
        elif provider == CloudProvider.GCP:
            return f"""
# Compute Instance: {resource.name}
resource "google_compute_instance" "{resource.name}" {{
  name         = "{resource.name}"
  machine_type = "{resource.specifications.get('machine_type', 'n1-standard-2')}"
  zone         = "${{var.region}}-a"
  
  boot_disk {{
    initialize_params {{
      image = "{resource.specifications.get('image', 'debian-cloud/debian-11')}"
      size  = {resource.specifications.get('disk_size', 30)}
      type  = "pd-ssd"
    }}
  }}
  
  network_interface {{
    network = google_compute_network.main.id
    
    access_config {{
      // Ephemeral public IP
    }}
  }}
  
  metadata_startup_script = file("${{path.module}}/startup_scripts/{resource.name}.sh")
  
  labels = var.default_labels
}}
"""
        else:  # Azure
            return f"""
# Virtual Machine: {resource.name}
resource "azurerm_linux_virtual_machine" "{resource.name}" {{
  name                = "{resource.name}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  size                = "{resource.specifications.get('vm_size', 'Standard_D2s_v3')}"
  
  admin_username = "nexusadmin"
  
  admin_ssh_key {{
    username   = "nexusadmin"
    public_key = file("${{path.module}}/ssh_keys/nexus.pub")
  }}
  
  os_disk {{
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
  }}
  
  source_image_reference {{
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-focal"
    sku       = "20_04-lts-gen2"
    version   = "latest"
  }}
  
  network_interface_ids = [
    azurerm_network_interface.{resource.name}_nic.id,
  ]
  
  tags = var.default_tags
}}
"""
    
    def _generate_network_resource(self, resource: ResourceConfig, provider: CloudProvider) -> str:
        """Generate network resource configuration"""
        if provider == CloudProvider.AWS:
            return f"""
# VPC: {resource.name}
resource "aws_vpc" "{resource.name}" {{
  cidr_block           = "{resource.specifications.get('cidr', '10.0.0.0/16')}"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = merge(
    var.default_tags,
    {{
      Name = "{resource.name}"
    }}
  )
}}

# Internet Gateway
resource "aws_internet_gateway" "{resource.name}_igw" {{
  vpc_id = aws_vpc.{resource.name}.id
  
  tags = var.default_tags
}}

# Public Subnet
resource "aws_subnet" "{resource.name}_public" {{
  vpc_id                  = aws_vpc.{resource.name}.id
  cidr_block              = cidrsubnet(aws_vpc.{resource.name}.cidr_block, 8, 1)
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true
  
  tags = merge(
    var.default_tags,
    {{
      Name = "{resource.name}-public"
      Type = "public"
    }}
  )
}}

# Private Subnet
resource "aws_subnet" "{resource.name}_private" {{
  vpc_id            = aws_vpc.{resource.name}.id
  cidr_block        = cidrsubnet(aws_vpc.{resource.name}.cidr_block, 8, 10)
  availability_zone = data.aws_availability_zones.available.names[1]
  
  tags = merge(
    var.default_tags,
    {{
      Name = "{resource.name}-private"
      Type = "private"
    }}
  )
}}

# NAT Gateway
resource "aws_eip" "{resource.name}_nat_eip" {{
  domain = "vpc"
  tags   = var.default_tags
}}

resource "aws_nat_gateway" "{resource.name}_nat" {{
  allocation_id = aws_eip.{resource.name}_nat_eip.id
  subnet_id     = aws_subnet.{resource.name}_public.id
  
  tags = var.default_tags
}}

# Route Tables
resource "aws_route_table" "{resource.name}_public" {{
  vpc_id = aws_vpc.{resource.name}.id
  
  route {{
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.{resource.name}_igw.id
  }}
  
  tags = var.default_tags
}}

resource "aws_route_table" "{resource.name}_private" {{
  vpc_id = aws_vpc.{resource.name}.id
  
  route {{
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.{resource.name}_nat.id
  }}
  
  tags = var.default_tags
}}
"""
        # Add GCP and Azure network configurations as needed
        return ""
    
    def _generate_database_resource(self, resource: ResourceConfig, provider: CloudProvider) -> str:
        """Generate database resource configuration"""
        if provider == CloudProvider.AWS:
            return f"""
# RDS Database: {resource.name}
resource "aws_db_instance" "{resource.name}" {{
  identifier     = "{resource.name}"
  engine         = "{resource.specifications.get('engine', 'postgres')}"
  engine_version = "{resource.specifications.get('engine_version', '14.7')}"
  instance_class = "{resource.specifications.get('instance_class', 'db.t3.medium')}"
  
  allocated_storage     = {resource.specifications.get('storage', 100)}
  storage_encrypted     = true
  storage_type          = "gp3"
  
  db_name  = "{resource.specifications.get('database_name', 'nexus')}"
  username = "nexusadmin"
  password = random_password.{resource.name}_password.result
  
  vpc_security_group_ids = [aws_security_group.{resource.name}_db_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.{resource.name}.name
  
  backup_retention_period = {resource.specifications.get('backup_retention', 7)}
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = false
  final_snapshot_identifier = "${{var.environment}}-{resource.name}-final-snapshot-${{formatdate("YYYY-MM-DD-hhmm", timestamp())}}"
  
  enabled_cloudwatch_logs_exports = ["postgresql"]
  
  tags = var.default_tags
}}

# Random password for database
resource "random_password" "{resource.name}_password" {{
  length  = 32
  special = true
}}

# Store password in Secrets Manager
resource "aws_secretsmanager_secret" "{resource.name}_password" {{
  name = "{resource.name}-db-password"
  tags = var.default_tags
}}

resource "aws_secretsmanager_secret_version" "{resource.name}_password" {{
  secret_id     = aws_secretsmanager_secret.{resource.name}_password.id
  secret_string = random_password.{resource.name}_password.result
}}

# DB Subnet Group
resource "aws_db_subnet_group" "{resource.name}" {{
  name       = "{resource.name}-subnet-group"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  
  tags = var.default_tags
}}

# Security Group for Database
resource "aws_security_group" "{resource.name}_db_sg" {{
  name        = "{resource.name}-db-sg"
  description = "Security group for {resource.name} database"
  vpc_id      = aws_vpc.main.id
  
  ingress {{
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }}
  
  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}
  
  tags = var.default_tags
}}
"""
        # Add GCP and Azure database configurations as needed
        return ""
    
    def _generate_kubernetes_resource(self, resource: ResourceConfig, provider: CloudProvider) -> str:
        """Generate Kubernetes cluster configuration"""
        if provider == CloudProvider.AWS:
            return f"""
# EKS Cluster: {resource.name}
module "eks" {{
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  
  cluster_name    = "{resource.name}"
  cluster_version = "{resource.specifications.get('k8s_version', '1.27')}"
  
  cluster_endpoint_public_access = true
  
  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.private[*].id
  
  # EKS Managed Node Group(s)
  eks_managed_node_groups = {{
    main = {{
      desired_size = {resource.specifications.get('node_count', 3)}
      min_size     = {resource.specifications.get('min_nodes', 2)}
      max_size     = {resource.specifications.get('max_nodes', 10)}
      
      instance_types = ["{resource.specifications.get('node_type', 't3.medium')}"]
      
      k8s_labels = {{
        Environment = var.environment
        ManagedBy   = "terraform"
      }}
    }}
  }}
  
  # aws-auth configmap
  manage_aws_auth_configmap = true
  
  # Extend cluster security group rules
  cluster_security_group_additional_rules = {{
    egress_nodes_ephemeral_ports_tcp = {{
      description                = "To node 1025-65535"
      protocol                   = "tcp"
      from_port                  = 1025
      to_port                    = 65535
      type                       = "egress"
      source_node_security_group = true
    }}
  }}
  
  # Add-ons
  cluster_addons = {{
    coredns = {{
      most_recent = true
    }}
    kube-proxy = {{
      most_recent = true
    }}
    vpc-cni = {{
      most_recent = true
    }}
    aws-ebs-csi-driver = {{
      most_recent = true
    }}
  }}
  
  tags = var.default_tags
}}

# OIDC Provider for IRSA
data "tls_certificate" "eks" {{
  url = module.eks.cluster_oidc_issuer_url
}}

resource "aws_iam_openid_connect_provider" "eks" {{
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = module.eks.cluster_oidc_issuer_url
  
  tags = var.default_tags
}}
"""
        elif provider == CloudProvider.GCP:
            return f"""
# GKE Cluster: {resource.name}
resource "google_container_cluster" "{resource.name}" {{
  name     = "{resource.name}"
  location = var.region
  
  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1
  
  network    = google_compute_network.main.name
  subnetwork = google_compute_subnetwork.main.name
  
  # Enable Workload Identity
  workload_identity_config {{
    workload_pool = "${{var.project_id}}.svc.id.goog"
  }}
  
  # Enable network policy
  network_policy {{
    enabled = true
  }}
  
  # Enable binary authorization
  binary_authorization {{
    evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
  }}
  
  # Configure cluster autoscaling
  cluster_autoscaling {{
    enabled = true
    resource_limits {{
      resource_type = "cpu"
      minimum       = 2
      maximum       = 100
    }}
    resource_limits {{
      resource_type = "memory"
      minimum       = 8
      maximum       = 1000
    }}
  }}
}}

# Separately Managed Node Pool
resource "google_container_node_pool" "{resource.name}_nodes" {{
  name       = "${{google_container_cluster.{resource.name}.name}}-node-pool"
  location   = var.region
  cluster    = google_container_cluster.{resource.name}.name
  node_count = {resource.specifications.get('node_count', 3)}
  
  autoscaling {{
    min_node_count = {resource.specifications.get('min_nodes', 2)}
    max_node_count = {resource.specifications.get('max_nodes', 10)}
  }}
  
  node_config {{
    preemptible  = false
    machine_type = "{resource.specifications.get('node_type', 'n1-standard-2')}"
    
    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    service_account = google_service_account.kubernetes.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    
    workload_metadata_config {{
      mode = "GKE_METADATA"
    }}
  }}
}}
"""
        # Add Azure AKS configuration as needed
        return ""
    
    def _generate_storage_resource(self, resource: ResourceConfig, provider: CloudProvider) -> str:
        """Generate storage resource configuration"""
        if provider == CloudProvider.AWS:
            return f"""
# S3 Bucket: {resource.name}
resource "aws_s3_bucket" "{resource.name}" {{
  bucket = "{resource.name}-${{var.environment}}-${{data.aws_caller_identity.current.account_id}}"
  
  tags = var.default_tags
}}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "{resource.name}" {{
  bucket = aws_s3_bucket.{resource.name}.id
  versioning_configuration {{
    status = "Enabled"
  }}
}}

# S3 Bucket Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "{resource.name}" {{
  bucket = aws_s3_bucket.{resource.name}.id
  
  rule {{
    apply_server_side_encryption_by_default {{
      sse_algorithm = "AES256"
    }}
  }}
}}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "{resource.name}" {{
  bucket = aws_s3_bucket.{resource.name}.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}}

# S3 Bucket Lifecycle Configuration
resource "aws_s3_bucket_lifecycle_configuration" "{resource.name}" {{
  bucket = aws_s3_bucket.{resource.name}.id
  
  rule {{
    id     = "archive-old-objects"
    status = "Enabled"
    
    transition {{
      days          = 30
      storage_class = "STANDARD_IA"
    }}
    
    transition {{
      days          = 90
      storage_class = "GLACIER"
    }}
    
    expiration {{
      days = 365
    }}
  }}
}}
"""
        # Add GCP and Azure storage configurations as needed
        return ""
    
    def _generate_cdn_resource(self, resource: ResourceConfig, provider: CloudProvider) -> str:
        """Generate CDN resource configuration"""
        if provider == CloudProvider.AWS:
            return f"""
# CloudFront Distribution: {resource.name}
resource "aws_cloudfront_distribution" "{resource.name}" {{
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "{resource.name} CDN"
  default_root_object = "index.html"
  
  origin {{
    domain_name = aws_s3_bucket.{resource.specifications.get('origin_bucket', 'static')}.bucket_regional_domain_name
    origin_id   = "S3-${{aws_s3_bucket.{resource.specifications.get('origin_bucket', 'static')}.id}}"
    
    s3_origin_config {{
      origin_access_identity = aws_cloudfront_origin_access_identity.{resource.name}.cloudfront_access_identity_path
    }}
  }}
  
  default_cache_behavior {{
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${{aws_s3_bucket.{resource.specifications.get('origin_bucket', 'static')}.id}}"
    
    forwarded_values {{
      query_string = false
      cookies {{
        forward = "none"
      }}
    }}
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }}
  
  price_class = "{resource.specifications.get('price_class', 'PriceClass_100')}"
  
  restrictions {{
    geo_restriction {{
      restriction_type = "none"
    }}
  }}
  
  viewer_certificate {{
    cloudfront_default_certificate = true
  }}
  
  tags = var.default_tags
}}

# CloudFront Origin Access Identity
resource "aws_cloudfront_origin_access_identity" "{resource.name}" {{
  comment = "OAI for {resource.name}"
}}

# Update S3 bucket policy to allow CloudFront access
resource "aws_s3_bucket_policy" "{resource.name}_cdn_policy" {{
  bucket = aws_s3_bucket.{resource.specifications.get('origin_bucket', 'static')}.id
  
  policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Sid    = "AllowCloudFrontAccess"
        Effect = "Allow"
        Principal = {{
          AWS = aws_cloudfront_origin_access_identity.{resource.name}.iam_arn
        }}
        Action   = "s3:GetObject"
        Resource = "${{aws_s3_bucket.{resource.specifications.get('origin_bucket', 'static')}.arn}}/*"
      }}
    ]
  }})
}}
"""
        # Add GCP and Azure CDN configurations as needed
        return ""
    
    def _generate_variables_tf(self, stack: InfrastructureStack) -> str:
        """Generate variables.tf file"""
        variables = f"""
variable "environment" {{
  description = "Environment name"
  type        = string
  default     = "{stack.environment}"
}}

variable "region" {{
  description = "Cloud region"
  type        = string
  default     = "{stack.resources[0].region if stack.resources else 'us-east-1'}"
}}

variable "project_name" {{
  description = "Project name"
  type        = string
  default     = "nexus"
}}

variable "default_tags" {{
  description = "Default tags to apply to all resources"
  type        = map(string)
  default = {{
    Environment = "{stack.environment}"
    ManagedBy   = "terraform"
    Project     = "nexus"
  }}
}}
"""
        
        # Add custom variables
        for var_name, var_config in stack.variables.items():
            variables += f"""
variable "{var_name}" {{
  description = "{var_config.get('description', '')}"
  type        = {var_config.get('type', 'string')}
  default     = {json.dumps(var_config.get('default'))}
}}
"""
        
        return variables
    
    def _generate_outputs_tf(self, stack: InfrastructureStack) -> str:
        """Generate outputs.tf file"""
        outputs = ""
        
        for resource in stack.resources:
            if resource.type == ResourceType.COMPUTE:
                outputs += f"""
output "{resource.name}_instance_id" {{
  description = "Instance ID of {resource.name}"
  value       = aws_instance.{resource.name}.id
}}

output "{resource.name}_public_ip" {{
  description = "Public IP of {resource.name}"
  value       = aws_instance.{resource.name}.public_ip
}}
"""
            elif resource.type == ResourceType.DATABASE:
                outputs += f"""
output "{resource.name}_endpoint" {{
  description = "Database endpoint for {resource.name}"
  value       = aws_db_instance.{resource.name}.endpoint
  sensitive   = true
}}

output "{resource.name}_password_secret_arn" {{
  description = "ARN of the secret containing database password"
  value       = aws_secretsmanager_secret.{resource.name}_password.arn
}}
"""
            elif resource.type == ResourceType.KUBERNETES:
                outputs += f"""
output "{resource.name}_cluster_endpoint" {{
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
  sensitive   = true
}}

output "{resource.name}_cluster_name" {{
  description = "Kubernetes Cluster Name"
  value       = module.eks.cluster_name
}}

output "{resource.name}_cluster_security_group_id" {{
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}}
"""
        
        return outputs
    
    def _generate_tfvars(self, stack: InfrastructureStack) -> str:
        """Generate terraform.tfvars file"""
        tfvars = f"""
# Auto-generated terraform.tfvars for {stack.name}
environment = "{stack.environment}"
"""
        
        for var_name, var_value in stack.variables.items():
            if isinstance(var_value, dict) and 'value' in var_value:
                tfvars += f'{var_name} = {json.dumps(var_value["value"])}\n'
        
        return tfvars
    
    async def init(self, stack_dir: str) -> Tuple[bool, str]:
        """Initialize Terraform"""
        try:
            process = await asyncio.create_subprocess_exec(
                "terraform", "init", "-no-color",
                cwd=stack_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return True, stdout.decode()
            else:
                return False, stderr.decode()
        except Exception as e:
            return False, str(e)
    
    async def plan(self, stack_dir: str, var_file: Optional[str] = None) -> Tuple[bool, str]:
        """Create Terraform plan"""
        cmd = ["terraform", "plan", "-no-color", "-out=tfplan"]
        if var_file:
            cmd.extend(["-var-file", var_file])
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=stack_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return True, stdout.decode()
            else:
                return False, stderr.decode()
        except Exception as e:
            return False, str(e)
    
    async def apply(self, stack_dir: str, auto_approve: bool = False) -> Tuple[bool, str]:
        """Apply Terraform configuration"""
        cmd = ["terraform", "apply", "-no-color"]
        if auto_approve:
            cmd.append("-auto-approve")
        cmd.append("tfplan")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=stack_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return True, stdout.decode()
            else:
                return False, stderr.decode()
        except Exception as e:
            return False, str(e)
    
    async def destroy(self, stack_dir: str, auto_approve: bool = False) -> Tuple[bool, str]:
        """Destroy Terraform infrastructure"""
        cmd = ["terraform", "destroy", "-no-color"]
        if auto_approve:
            cmd.append("-auto-approve")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=stack_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return True, stdout.decode()
            else:
                return False, stderr.decode()
        except Exception as e:
            return False, str(e)
    
    async def get_outputs(self, stack_dir: str) -> Dict[str, Any]:
        """Get Terraform outputs"""
        try:
            process = await asyncio.create_subprocess_exec(
                "terraform", "output", "-json",
                cwd=stack_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                outputs = json.loads(stdout.decode())
                return {k: v["value"] for k, v in outputs.items()}
            else:
                return {}
        except Exception as e:
            return {}

class CloudFormationProvider:
    """Manages CloudFormation infrastructure"""
    
    def __init__(self):
        self.cf_client = boto3.client('cloudformation')
        self.s3_client = boto3.client('s3')
    
    async def generate_template(self, stack: InfrastructureStack) -> Dict[str, Any]:
        """Generate CloudFormation template"""
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": f"NEXUS Infrastructure Stack: {stack.name}",
            "Parameters": {},
            "Resources": {},
            "Outputs": {}
        }
        
        # Add parameters
        for var_name, var_config in stack.variables.items():
            template["Parameters"][var_name] = {
                "Type": "String",
                "Description": var_config.get("description", ""),
                "Default": str(var_config.get("default", ""))
            }
        
        # Add resources
        for resource in stack.resources:
            if resource.type == ResourceType.COMPUTE:
                self._add_compute_resource(template, resource)
            elif resource.type == ResourceType.NETWORK:
                self._add_network_resource(template, resource)
            elif resource.type == ResourceType.DATABASE:
                self._add_database_resource(template, resource)
            elif resource.type == ResourceType.STORAGE:
                self._add_storage_resource(template, resource)
        
        return template
    
    def _add_compute_resource(self, template: Dict[str, Any], resource: ResourceConfig):
        """Add compute resource to CloudFormation template"""
        template["Resources"][resource.name] = {
            "Type": "AWS::EC2::Instance",
            "Properties": {
                "ImageId": resource.specifications.get("ami", "ami-0c02fb55956c7d316"),
                "InstanceType": resource.specifications.get("instance_type", "t3.medium"),
                "KeyName": {"Ref": "KeyName"},
                "SecurityGroupIds": [{"Ref": f"{resource.name}SecurityGroup"}],
                "SubnetId": {"Ref": "PublicSubnet"},
                "BlockDeviceMappings": [{
                    "DeviceName": "/dev/xvda",
                    "Ebs": {
                        "VolumeSize": resource.specifications.get("disk_size", 30),
                        "VolumeType": "gp3",
                        "Encrypted": True
                    }
                }],
                "Tags": [
                    {"Key": "Name", "Value": resource.name},
                    {"Key": "Environment", "Value": {"Ref": "Environment"}}
                ]
            }
        }
        
        # Add security group
        template["Resources"][f"{resource.name}SecurityGroup"] = {
            "Type": "AWS::EC2::SecurityGroup",
            "Properties": {
                "GroupDescription": f"Security group for {resource.name}",
                "VpcId": {"Ref": "VPC"},
                "SecurityGroupIngress": [
                    {
                        "IpProtocol": "tcp",
                        "FromPort": 22,
                        "ToPort": 22,
                        "CidrIp": "10.0.0.0/8"
                    },
                    {
                        "IpProtocol": "tcp",
                        "FromPort": 443,
                        "ToPort": 443,
                        "CidrIp": "0.0.0.0/0"
                    }
                ],
                "SecurityGroupEgress": [{
                    "IpProtocol": "-1",
                    "CidrIp": "0.0.0.0/0"
                }],
                "Tags": [
                    {"Key": "Name", "Value": f"{resource.name}-sg"}
                ]
            }
        }
        
        # Add outputs
        template["Outputs"][f"{resource.name}InstanceId"] = {
            "Description": f"Instance ID of {resource.name}",
            "Value": {"Ref": resource.name}
        }
        template["Outputs"][f"{resource.name}PublicIP"] = {
            "Description": f"Public IP of {resource.name}",
            "Value": {"Fn::GetAtt": [resource.name, "PublicIp"]}
        }
    
    def _add_network_resource(self, template: Dict[str, Any], resource: ResourceConfig):
        """Add network resources to CloudFormation template"""
        # VPC
        template["Resources"]["VPC"] = {
            "Type": "AWS::EC2::VPC",
            "Properties": {
                "CidrBlock": resource.specifications.get("cidr", "10.0.0.0/16"),
                "EnableDnsHostnames": True,
                "EnableDnsSupport": True,
                "Tags": [{"Key": "Name", "Value": resource.name}]
            }
        }
        
        # Internet Gateway
        template["Resources"]["InternetGateway"] = {
            "Type": "AWS::EC2::InternetGateway",
            "Properties": {
                "Tags": [{"Key": "Name", "Value": f"{resource.name}-igw"}]
            }
        }
        
        template["Resources"]["AttachGateway"] = {
            "Type": "AWS::EC2::VPCGatewayAttachment",
            "Properties": {
                "VpcId": {"Ref": "VPC"},
                "InternetGatewayId": {"Ref": "InternetGateway"}
            }
        }
        
        # Subnets
        template["Resources"]["PublicSubnet"] = {
            "Type": "AWS::EC2::Subnet",
            "Properties": {
                "VpcId": {"Ref": "VPC"},
                "CidrBlock": "10.0.1.0/24",
                "AvailabilityZone": {"Fn::Select": ["0", {"Fn::GetAZs": ""}]},
                "MapPublicIpOnLaunch": True,
                "Tags": [{"Key": "Name", "Value": f"{resource.name}-public"}]
            }
        }
        
        template["Resources"]["PrivateSubnet"] = {
            "Type": "AWS::EC2::Subnet",
            "Properties": {
                "VpcId": {"Ref": "VPC"},
                "CidrBlock": "10.0.10.0/24",
                "AvailabilityZone": {"Fn::Select": ["1", {"Fn::GetAZs": ""}]},
                "Tags": [{"Key": "Name", "Value": f"{resource.name}-private"}]
            }
        }
    
    def _add_database_resource(self, template: Dict[str, Any], resource: ResourceConfig):
        """Add database resource to CloudFormation template"""
        template["Resources"][resource.name] = {
            "Type": "AWS::RDS::DBInstance",
            "Properties": {
                "DBInstanceIdentifier": resource.name,
                "Engine": resource.specifications.get("engine", "postgres"),
                "EngineVersion": resource.specifications.get("engine_version", "14.7"),
                "DBInstanceClass": resource.specifications.get("instance_class", "db.t3.medium"),
                "AllocatedStorage": str(resource.specifications.get("storage", 100)),
                "StorageType": "gp3",
                "StorageEncrypted": True,
                "MasterUsername": "nexusadmin",
                "MasterUserPassword": {"Ref": f"{resource.name}Password"},
                "VPCSecurityGroups": [{"Ref": f"{resource.name}SecurityGroup"}],
                "DBSubnetGroupName": {"Ref": f"{resource.name}SubnetGroup"},
                "BackupRetentionPeriod": resource.specifications.get("backup_retention", 7),
                "PreferredBackupWindow": "03:00-04:00",
                "PreferredMaintenanceWindow": "sun:04:00-sun:05:00",
                "Tags": [
                    {"Key": "Name", "Value": resource.name},
                    {"Key": "Environment", "Value": {"Ref": "Environment"}}
                ]
            }
        }
        
        # Generate random password
        template["Resources"][f"{resource.name}Password"] = {
            "Type": "AWS::SecretsManager::Secret",
            "Properties": {
                "Description": f"Database password for {resource.name}",
                "GenerateSecretString": {
                    "SecretStringTemplate": '{"username": "nexusadmin"}',
                    "GenerateStringKey": "password",
                    "PasswordLength": 32,
                    "ExcludeCharacters": '"@/\\'
                }
            }
        }
    
    def _add_storage_resource(self, template: Dict[str, Any], resource: ResourceConfig):
        """Add storage resource to CloudFormation template"""
        template["Resources"][resource.name] = {
            "Type": "AWS::S3::Bucket",
            "Properties": {
                "BucketName": {"Fn::Sub": f"{resource.name}-${{Environment}}-${{AWS::AccountId}}"},
                "VersioningConfiguration": {
                    "Status": "Enabled"
                },
                "BucketEncryption": {
                    "ServerSideEncryptionConfiguration": [{
                        "ServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "AES256"
                        }
                    }]
                },
                "PublicAccessBlockConfiguration": {
                    "BlockPublicAcls": True,
                    "BlockPublicPolicy": True,
                    "IgnorePublicAcls": True,
                    "RestrictPublicBuckets": True
                },
                "LifecycleConfiguration": {
                    "Rules": [{
                        "Id": "ArchiveOldObjects",
                        "Status": "Enabled",
                        "Transitions": [
                            {
                                "StorageClass": "STANDARD_IA",
                                "TransitionInDays": 30
                            },
                            {
                                "StorageClass": "GLACIER",
                                "TransitionInDays": 90
                            }
                        ],
                        "ExpirationInDays": 365
                    }]
                },
                "Tags": [
                    {"Key": "Name", "Value": resource.name},
                    {"Key": "Environment", "Value": {"Ref": "Environment"}}
                ]
            }
        }
    
    async def deploy_stack(self, stack_name: str, template: Dict[str, Any], 
                          parameters: Dict[str, str] = None) -> DeploymentResult:
        """Deploy CloudFormation stack"""
        start_time = datetime.now()
        result = DeploymentResult(
            stack_name=stack_name,
            status="IN_PROGRESS",
            outputs={},
            resources_created=[],
            duration=0
        )
        
        try:
            # Upload template to S3 if it's too large
            template_body = json.dumps(template)
            
            if len(template_body) > 51200:  # 50KB limit
                # Upload to S3
                bucket_name = f"nexus-cf-templates-{boto3.client('sts').get_caller_identity()['Account']}"
                key = f"{stack_name}/template-{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
                
                self.s3_client.put_object(
                    Bucket=bucket_name,
                    Key=key,
                    Body=template_body
                )
                
                template_url = f"https://{bucket_name}.s3.amazonaws.com/{key}"
                
                # Create or update stack
                response = self.cf_client.create_stack(
                    StackName=stack_name,
                    TemplateURL=template_url,
                    Parameters=[
                        {"ParameterKey": k, "ParameterValue": v}
                        for k, v in (parameters or {}).items()
                    ],
                    Capabilities=["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"],
                    Tags=[
                        {"Key": "ManagedBy", "Value": "NEXUS"},
                        {"Key": "Tool", "Value": "CloudFormation"}
                    ]
                )
            else:
                # Create or update stack with inline template
                response = self.cf_client.create_stack(
                    StackName=stack_name,
                    TemplateBody=template_body,
                    Parameters=[
                        {"ParameterKey": k, "ParameterValue": v}
                        for k, v in (parameters or {}).items()
                    ],
                    Capabilities=["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"],
                    Tags=[
                        {"Key": "ManagedBy", "Value": "NEXUS"},
                        {"Key": "Tool", "Value": "CloudFormation"}
                    ]
                )
            
            # Wait for stack to complete
            waiter = self.cf_client.get_waiter('stack_create_complete')
            waiter.wait(
                StackName=stack_name,
                WaiterConfig={
                    'Delay': 30,
                    'MaxAttempts': 120  # 60 minutes max
                }
            )
            
            # Get stack outputs
            stack_info = self.cf_client.describe_stacks(StackName=stack_name)['Stacks'][0]
            
            result.status = "COMPLETED"
            result.outputs = {
                output['OutputKey']: output.get('OutputValue', '')
                for output in stack_info.get('Outputs', [])
            }
            
            # Get created resources
            resources = self.cf_client.list_stack_resources(StackName=stack_name)
            result.resources_created = [
                f"{r['ResourceType']}:{r['LogicalResourceId']}"
                for r in resources['StackResourceSummaries']
            ]
            
        except Exception as e:
            result.status = "FAILED"
            result.errors.append(str(e))
        
        result.duration = (datetime.now() - start_time).total_seconds()
        return result
    
    async def delete_stack(self, stack_name: str) -> bool:
        """Delete CloudFormation stack"""
        try:
            self.cf_client.delete_stack(StackName=stack_name)
            
            # Wait for deletion
            waiter = self.cf_client.get_waiter('stack_delete_complete')
            waiter.wait(
                StackName=stack_name,
                WaiterConfig={
                    'Delay': 30,
                    'MaxAttempts': 60  # 30 minutes max
                }
            )
            
            return True
        except Exception as e:
            print(f"Error deleting stack: {e}")
            return False

class PulumiProvider:
    """Manages Pulumi infrastructure"""
    
    def __init__(self, work_dir: str = "./pulumi"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_program(self, stack: InfrastructureStack) -> auto.Stack:
        """Create Pulumi program"""
        stack_name = f"{stack.name}-{stack.environment}"
        project_name = "nexus-infrastructure"
        
        # Define the Pulumi program
        def pulumi_program():
            if stack.provider == CloudProvider.AWS:
                self._create_aws_resources(stack)
            elif stack.provider == CloudProvider.GCP:
                self._create_gcp_resources(stack)
            elif stack.provider == CloudProvider.AZURE:
                self._create_azure_resources(stack)
        
        # Create or select stack
        stack_obj = auto.create_or_select_stack(
            stack_name=stack_name,
            project_name=project_name,
            program=pulumi_program,
            opts=auto.LocalWorkspaceOptions(
                work_dir=str(self.work_dir),
                env_vars={
                    "PULUMI_CONFIG_PASSPHRASE": os.getenv("PULUMI_CONFIG_PASSPHRASE", "")
                }
            )
        )
        
        # Set configuration
        for key, value in stack.variables.items():
            stack_obj.set_config(key, auto.ConfigValue(value=str(value)))
        
        return stack_obj
    
    def _create_aws_resources(self, stack: InfrastructureStack):
        """Create AWS resources using Pulumi"""
        import pulumi_aws as aws
        
        # Create resources based on stack configuration
        for resource in stack.resources:
            if resource.type == ResourceType.COMPUTE:
                # Create EC2 instance
                instance = aws.ec2.Instance(
                    resource.name,
                    instance_type=resource.specifications.get("instance_type", "t3.medium"),
                    ami=resource.specifications.get("ami", "ami-0c02fb55956c7d316"),
                    tags={
                        "Name": resource.name,
                        "Environment": stack.environment,
                        **resource.tags
                    }
                )
                
                pulumi.export(f"{resource.name}_id", instance.id)
                pulumi.export(f"{resource.name}_public_ip", instance.public_ip)
            
            elif resource.type == ResourceType.STORAGE:
                # Create S3 bucket
                bucket = aws.s3.Bucket(
                    resource.name,
                    bucket=f"{resource.name}-{stack.environment}",
                    versioning=aws.s3.BucketVersioningArgs(
                        enabled=True
                    ),
                    server_side_encryption_configuration=aws.s3.BucketServerSideEncryptionConfigurationArgs(
                        rule=aws.s3.BucketServerSideEncryptionConfigurationRuleArgs(
                            apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                                sse_algorithm="AES256"
                            )
                        )
                    ),
                    tags=resource.tags
                )
                
                # Block public access
                bucket_public_access = aws.s3.BucketPublicAccessBlock(
                    f"{resource.name}-public-access-block",
                    bucket=bucket.id,
                    block_public_acls=True,
                    block_public_policy=True,
                    ignore_public_acls=True,
                    restrict_public_buckets=True
                )
                
                pulumi.export(f"{resource.name}_bucket_name", bucket.id)
                pulumi.export(f"{resource.name}_bucket_arn", bucket.arn)
    
    def _create_gcp_resources(self, stack: InfrastructureStack):
        """Create GCP resources using Pulumi"""
        import pulumi_gcp as gcp
        
        # Implementation for GCP resources
        pass
    
    def _create_azure_resources(self, stack: InfrastructureStack):
        """Create Azure resources using Pulumi"""
        import pulumi_azure_native as azure
        
        # Implementation for Azure resources
        pass
    
    async def deploy(self, stack_obj: auto.Stack) -> DeploymentResult:
        """Deploy Pulumi stack"""
        start_time = datetime.now()
        result = DeploymentResult(
            stack_name=stack_obj.name,
            status="IN_PROGRESS",
            outputs={},
            resources_created=[],
            duration=0
        )
        
        try:
            # Install plugins
            await asyncio.to_thread(stack_obj.workspace.install_plugin, "aws", "v5.0.0")
            
            # Refresh state
            await asyncio.to_thread(stack_obj.refresh, on_output=print)
            
            # Deploy
            up_result = await asyncio.to_thread(stack_obj.up, on_output=print)
            
            result.status = "COMPLETED"
            result.outputs = up_result.outputs
            result.resources_created = [
                f"{r.urn}" for r in up_result.summary.resource_changes.values()
            ]
            
        except Exception as e:
            result.status = "FAILED"
            result.errors.append(str(e))
        
        result.duration = (datetime.now() - start_time).total_seconds()
        return result
    
    async def destroy(self, stack_obj: auto.Stack) -> bool:
        """Destroy Pulumi stack"""
        try:
            await asyncio.to_thread(stack_obj.destroy, on_output=print)
            return True
        except Exception as e:
            print(f"Error destroying stack: {e}")
            return False

class SSLCertificateManager:
    """Manages SSL/TLS certificates"""
    
    def __init__(self, provider: CloudProvider):
        self.provider = provider
        if provider == CloudProvider.AWS:
            self.acm_client = boto3.client('acm')
            self.route53_client = boto3.client('route53')
    
    async def request_certificate(self, domain: str, validation_method: str = "DNS") -> str:
        """Request SSL certificate"""
        if self.provider == CloudProvider.AWS:
            # Request certificate from ACM
            response = self.acm_client.request_certificate(
                DomainName=domain,
                SubjectAlternativeNames=[f"*.{domain}"],
                ValidationMethod=validation_method,
                Tags=[
                    {"Key": "Domain", "Value": domain},
                    {"Key": "ManagedBy", "Value": "NEXUS"}
                ]
            )
            
            certificate_arn = response['CertificateArn']
            
            # Wait for validation records
            waiter = self.acm_client.get_waiter('certificate_validated')
            
            if validation_method == "DNS":
                # Get validation records
                cert_details = self.acm_client.describe_certificate(
                    CertificateArn=certificate_arn
                )
                
                # Create DNS validation records
                for option in cert_details['Certificate']['DomainValidationOptions']:
                    if 'ResourceRecord' in option:
                        await self._create_validation_record(
                            domain,
                            option['ResourceRecord']
                        )
                
                # Wait for validation
                waiter.wait(
                    CertificateArn=certificate_arn,
                    WaiterConfig={
                        'Delay': 60,
                        'MaxAttempts': 60  # 1 hour max
                    }
                )
            
            return certificate_arn
        
        return ""
    
    async def _create_validation_record(self, domain: str, record: Dict[str, str]):
        """Create DNS validation record"""
        # Find hosted zone
        zones = self.route53_client.list_hosted_zones_by_name(
            DNSName=domain
        )
        
        if not zones['HostedZones']:
            raise Exception(f"No hosted zone found for {domain}")
        
        zone_id = zones['HostedZones'][0]['Id']
        
        # Create validation record
        self.route53_client.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch={
                'Changes': [{
                    'Action': 'CREATE',
                    'ResourceRecordSet': {
                        'Name': record['Name'],
                        'Type': record['Type'],
                        'TTL': 300,
                        'ResourceRecords': [{'Value': record['Value']}]
                    }
                }]
            }
        )

class DNSManager:
    """Manages DNS configuration"""
    
    def __init__(self, provider: CloudProvider):
        self.provider = provider
        if provider == CloudProvider.AWS:
            self.route53_client = boto3.client('route53')
    
    async def create_hosted_zone(self, domain: str) -> str:
        """Create DNS hosted zone"""
        if self.provider == CloudProvider.AWS:
            response = self.route53_client.create_hosted_zone(
                Name=domain,
                CallerReference=f"nexus-{datetime.now().timestamp()}",
                HostedZoneConfig={
                    'Comment': f'Managed by NEXUS for {domain}',
                    'PrivateZone': False
                }
            )
            
            return response['HostedZone']['Id']
        
        return ""
    
    async def create_record(self, zone_id: str, record_name: str, 
                          record_type: str, values: List[str], ttl: int = 300):
        """Create DNS record"""
        if self.provider == CloudProvider.AWS:
            self.route53_client.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch={
                    'Changes': [{
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': record_name,
                            'Type': record_type,
                            'TTL': ttl,
                            'ResourceRecords': [{'Value': v} for v in values]
                        }
                    }]
                }
            )

class NexusInfrastructureManager:
    """Main infrastructure management system"""
    
    def __init__(self):
        self.terraform = TerraformProvider()
        self.cloudformation = CloudFormationProvider()
        self.pulumi = PulumiProvider()
        self.deployments = {}
    
    async def deploy_infrastructure(self, stack: InfrastructureStack) -> DeploymentResult:
        """Deploy infrastructure stack"""
        print(f"Deploying infrastructure stack: {stack.name}")
        
        if stack.tool == IaCTool.TERRAFORM:
            # Generate Terraform configuration
            stack_dir = await self.terraform.generate_configuration(stack)
            
            # Initialize Terraform
            init_success, init_output = await self.terraform.init(stack_dir)
            if not init_success:
                return DeploymentResult(
                    stack_name=stack.name,
                    status="FAILED",
                    outputs={},
                    resources_created=[],
                    duration=0,
                    errors=[f"Terraform init failed: {init_output}"]
                )
            
            # Create plan
            plan_success, plan_output = await self.terraform.plan(stack_dir)
            if not plan_success:
                return DeploymentResult(
                    stack_name=stack.name,
                    status="FAILED",
                    outputs={},
                    resources_created=[],
                    duration=0,
                    errors=[f"Terraform plan failed: {plan_output}"]
                )
            
            # Apply
            apply_success, apply_output = await self.terraform.apply(stack_dir, auto_approve=True)
            if not apply_success:
                return DeploymentResult(
                    stack_name=stack.name,
                    status="FAILED",
                    outputs={},
                    resources_created=[],
                    duration=0,
                    errors=[f"Terraform apply failed: {apply_output}"]
                )
            
            # Get outputs
            outputs = await self.terraform.get_outputs(stack_dir)
            
            result = DeploymentResult(
                stack_name=stack.name,
                status="COMPLETED",
                outputs=outputs,
                resources_created=[],  # Would parse from apply output
                duration=0
            )
            
        elif stack.tool == IaCTool.CLOUDFORMATION:
            # Generate CloudFormation template
            template = await self.cloudformation.generate_template(stack)
            
            # Deploy stack
            result = await self.cloudformation.deploy_stack(
                stack.name,
                template,
                {k: str(v) for k, v in stack.variables.items()}
            )
            
        elif stack.tool == IaCTool.PULUMI:
            # Create Pulumi program
            pulumi_stack = await self.pulumi.create_program(stack)
            
            # Deploy
            result = await self.pulumi.deploy(pulumi_stack)
        
        else:
            result = DeploymentResult(
                stack_name=stack.name,
                status="FAILED",
                outputs={},
                resources_created=[],
                duration=0,
                errors=[f"Unsupported IaC tool: {stack.tool}"]
            )
        
        # Store deployment
        self.deployments[stack.name] = result
        
        return result
    
    async def destroy_infrastructure(self, stack_name: str, tool: IaCTool) -> bool:
        """Destroy infrastructure stack"""
        print(f"Destroying infrastructure stack: {stack_name}")
        
        if tool == IaCTool.TERRAFORM:
            stack_dir = self.terraform.working_dir / stack_name
            if stack_dir.exists():
                success, output = await self.terraform.destroy(str(stack_dir), auto_approve=True)
                return success
            
        elif tool == IaCTool.CLOUDFORMATION:
            return await self.cloudformation.delete_stack(stack_name)
            
        elif tool == IaCTool.PULUMI:
            # Would need to recreate stack object
            pass
        
        return False
    
    def get_deployment_status(self, stack_name: str) -> Optional[DeploymentResult]:
        """Get deployment status"""
        return self.deployments.get(stack_name)

# Example usage
async def main():
    manager = NexusInfrastructureManager()
    
    # Define infrastructure stack
    stack = InfrastructureStack(
        name="nexus-production",
        environment="production",
        provider=CloudProvider.AWS,
        tool=IaCTool.TERRAFORM,
        resources=[
            ResourceConfig(
                name="nexus-web",
                type=ResourceType.COMPUTE,
                provider=CloudProvider.AWS,
                region="us-east-1",
                specifications={
                    "instance_type": "t3.large",
                    "ami": "ami-0c02fb55956c7d316",
                    "disk_size": 100
                },
                tags={"Component": "WebServer"}
            ),
            ResourceConfig(
                name="nexus-vpc",
                type=ResourceType.NETWORK,
                provider=CloudProvider.AWS,
                region="us-east-1",
                specifications={
                    "cidr": "10.0.0.0/16"
                }
            ),
            ResourceConfig(
                name="nexus-db",
                type=ResourceType.DATABASE,
                provider=CloudProvider.AWS,
                region="us-east-1",
                specifications={
                    "engine": "postgres",
                    "engine_version": "14.7",
                    "instance_class": "db.r6g.large",
                    "storage": 500,
                    "backup_retention": 30
                },
                dependencies=["nexus-vpc"]
            ),
            ResourceConfig(
                name="nexus-cluster",
                type=ResourceType.KUBERNETES,
                provider=CloudProvider.AWS,
                region="us-east-1",
                specifications={
                    "k8s_version": "1.27",
                    "node_count": 5,
                    "node_type": "t3.xlarge",
                    "min_nodes": 3,
                    "max_nodes": 10
                },
                dependencies=["nexus-vpc"]
            ),
            ResourceConfig(
                name="nexus-static",
                type=ResourceType.STORAGE,
                provider=CloudProvider.AWS,
                region="us-east-1",
                specifications={}
            ),
            ResourceConfig(
                name="nexus-cdn",
                type=ResourceType.CDN,
                provider=CloudProvider.AWS,
                region="us-east-1",
                specifications={
                    "origin_bucket": "nexus-static",
                    "price_class": "PriceClass_100"
                },
                dependencies=["nexus-static"]
            )
        ],
        variables={
            "key_name": {
                "description": "SSH key pair name",
                "type": "string",
                "default": "nexus-prod-key"
            },
            "allowed_ssh_cidr_blocks": {
                "description": "CIDR blocks allowed for SSH",
                "type": "list(string)",
                "default": ["10.0.0.0/8"]
            }
        },
        backend_config={
            "bucket": "nexus-terraform-state",
            "region": "us-east-1"
        }
    )
    
    # Deploy infrastructure
    result = await manager.deploy_infrastructure(stack)
    
    print(f"Deployment status: {result.status}")
    if result.outputs:
        print("Outputs:")
        for key, value in result.outputs.items():
            print(f"  {key}: {value}")
    
    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")

if __name__ == "__main__":
    asyncio.run(main())