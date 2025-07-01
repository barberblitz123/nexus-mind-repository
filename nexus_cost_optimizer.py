#!/usr/bin/env python3
"""
NEXUS Cost Optimizer - Cloud Cost Management
Real-time cost monitoring, optimization recommendations, and savings automation
"""

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union
import pandas as pd
import numpy as np
from collections import defaultdict

# Cloud provider SDKs
try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    from google.cloud import billing_v1, compute_v1
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False

try:
    from azure.mgmt.costmanagement import CostManagementClient
    from azure.identity import DefaultAzureCredential
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

# Monitoring and analytics
try:
    from prometheus_client import Counter, Gauge, Histogram
    import matplotlib.pyplot as plt
    import seaborn as sns
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CostCategory(Enum):
    """Cost categories"""
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    SERVERLESS = "serverless"
    CONTAINER = "container"
    AI_ML = "ai_ml"
    MONITORING = "monitoring"
    OTHER = "other"


class OptimizationType(Enum):
    """Optimization types"""
    RIGHTSIZING = "rightsizing"
    RESERVED_INSTANCES = "reserved_instances"
    SAVINGS_PLANS = "savings_plans"
    SPOT_INSTANCES = "spot_instances"
    LIFECYCLE_POLICIES = "lifecycle_policies"
    UNUSED_RESOURCES = "unused_resources"
    SCHEDULED_SCALING = "scheduled_scaling"
    REGION_OPTIMIZATION = "region_optimization"
    COMMITMENT_OPTIMIZATION = "commitment_optimization"


class ResourceType(Enum):
    """Resource types"""
    EC2_INSTANCE = "ec2_instance"
    RDS_INSTANCE = "rds_instance"
    LAMBDA_FUNCTION = "lambda_function"
    S3_BUCKET = "s3_bucket"
    EBS_VOLUME = "ebs_volume"
    LOAD_BALANCER = "load_balancer"
    NAT_GATEWAY = "nat_gateway"
    VPN_CONNECTION = "vpn_connection"
    KUBERNETES_CLUSTER = "kubernetes_cluster"


@dataclass
class CostData:
    """Cost data point"""
    timestamp: datetime
    provider: str
    service: str
    resource_id: str
    resource_type: ResourceType
    category: CostCategory
    amount: float
    currency: str = "USD"
    region: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    usage_quantity: float = 0.0
    usage_unit: str = ""


@dataclass
class CostAnomaly:
    """Cost anomaly detection"""
    id: str
    timestamp: datetime
    resource_id: str
    service: str
    expected_cost: float
    actual_cost: float
    variance_percent: float
    severity: str  # low, medium, high, critical
    description: str
    recommended_action: str


@dataclass
class OptimizationRecommendation:
    """Cost optimization recommendation"""
    id: str
    type: OptimizationType
    resource_id: str
    resource_type: ResourceType
    current_cost: float
    recommended_cost: float
    monthly_savings: float
    annual_savings: float
    effort_level: str  # low, medium, high
    risk_level: str  # low, medium, high
    description: str
    implementation_steps: List[str]
    automated: bool = False
    priority_score: float = 0.0


@dataclass
class CostBudget:
    """Cost budget configuration"""
    name: str
    amount: float
    period: str  # daily, weekly, monthly, quarterly, yearly
    services: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    alert_thresholds: List[float] = field(default_factory=lambda: [80, 90, 100])
    notification_channels: List[str] = field(default_factory=list)
    auto_actions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CostForecast:
    """Cost forecast"""
    period_start: datetime
    period_end: datetime
    predicted_cost: float
    confidence_interval: Tuple[float, float]
    trend: str  # increasing, decreasing, stable
    seasonality_factor: float
    recommendations: List[str] = field(default_factory=list)


class CostAnalyzer(ABC):
    """Abstract cost analyzer interface"""
    
    @abstractmethod
    async def get_current_costs(self, start_date: datetime, end_date: datetime) -> List[CostData]:
        pass
    
    @abstractmethod
    async def get_resource_utilization(self, resource_id: str) -> Dict[str, float]:
        pass
    
    @abstractmethod
    async def get_pricing_info(self, resource_type: ResourceType, region: str) -> Dict[str, float]:
        pass
    
    @abstractmethod
    async def get_reserved_instance_recommendations(self) -> List[OptimizationRecommendation]:
        pass


class AWSCostAnalyzer(CostAnalyzer):
    """AWS cost analyzer"""
    
    def __init__(self, access_key: str = None, secret_key: str = None, region: str = 'us-east-1'):
        if not AWS_AVAILABLE:
            raise ImportError("AWS SDK (boto3) not installed")
        
        if access_key and secret_key:
            self.session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
        else:
            self.session = boto3.Session(region_name=region)
        
        self.ce_client = self.session.client('ce')  # Cost Explorer
        self.cloudwatch = self.session.client('cloudwatch')
        self.ec2_client = self.session.client('ec2')
        self.pricing_client = self.session.client('pricing', region_name='us-east-1')
    
    async def get_current_costs(self, start_date: datetime, end_date: datetime) -> List[CostData]:
        """Get current AWS costs"""
        costs = []
        
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost', 'UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'},
                    {'Type': 'TAG', 'Key': 'Environment'}
                ],
                Filter={
                    'Not': {
                        'Dimensions': {
                            'Key': 'RECORD_TYPE',
                            'Values': ['Credit', 'Refund']
                        }
                    }
                }
            )
            
            for result in response['ResultsByTime']:
                timestamp = datetime.strptime(result['TimePeriod']['Start'], '%Y-%m-%d')
                
                for group in result['Groups']:
                    service = group['Keys'][0]
                    usage_type = group['Keys'][1]
                    environment = group['Keys'][2] if len(group['Keys']) > 2 else 'untagged'
                    
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    usage = float(group['Metrics']['UsageQuantity']['Amount'])
                    
                    if cost > 0:
                        costs.append(CostData(
                            timestamp=timestamp,
                            provider='AWS',
                            service=service,
                            resource_id=f"{service}_{usage_type}",
                            resource_type=self._map_service_to_resource_type(service),
                            category=self._map_service_to_category(service),
                            amount=cost,
                            currency='USD',
                            tags={'Environment': environment},
                            usage_quantity=usage,
                            usage_unit=self._extract_usage_unit(usage_type)
                        ))
            
        except ClientError as e:
            logger.error(f"Failed to get AWS costs: {e}")
        
        return costs
    
    async def get_resource_utilization(self, resource_id: str) -> Dict[str, float]:
        """Get resource utilization metrics"""
        utilization = {}
        
        try:
            # Get EC2 instance metrics
            if resource_id.startswith('i-'):
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(days=7)
                
                # CPU utilization
                cpu_response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    Dimensions=[{'Name': 'InstanceId', 'Value': resource_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Average', 'Maximum']
                )
                
                if cpu_response['Datapoints']:
                    utilization['cpu_average'] = np.mean([d['Average'] for d in cpu_response['Datapoints']])
                    utilization['cpu_maximum'] = max([d['Maximum'] for d in cpu_response['Datapoints']])
                
                # Network utilization
                network_in = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='NetworkIn',
                    Dimensions=[{'Name': 'InstanceId', 'Value': resource_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Sum']
                )
                
                if network_in['Datapoints']:
                    utilization['network_in_gb'] = sum([d['Sum'] for d in network_in['Datapoints']]) / (1024**3)
            
        except ClientError as e:
            logger.error(f"Failed to get utilization for {resource_id}: {e}")
        
        return utilization
    
    async def get_pricing_info(self, resource_type: ResourceType, region: str) -> Dict[str, float]:
        """Get AWS pricing information"""
        pricing = {}
        
        try:
            if resource_type == ResourceType.EC2_INSTANCE:
                # Get EC2 pricing
                response = self.pricing_client.get_products(
                    ServiceCode='AmazonEC2',
                    Filters=[
                        {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self._get_region_name(region)},
                        {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Compute Instance'},
                        {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                        {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'}
                    ],
                    MaxResults=100
                )
                
                for price_item in response['PriceList']:
                    price_data = json.loads(price_item)
                    instance_type = price_data['product']['attributes'].get('instanceType')
                    
                    if instance_type:
                        on_demand_pricing = self._extract_on_demand_price(price_data)
                        if on_demand_pricing:
                            pricing[instance_type] = on_demand_pricing
            
        except Exception as e:
            logger.error(f"Failed to get pricing info: {e}")
        
        return pricing
    
    async def get_reserved_instance_recommendations(self) -> List[OptimizationRecommendation]:
        """Get Reserved Instance recommendations"""
        recommendations = []
        
        try:
            response = self.ce_client.get_reservation_purchase_recommendation(
                Service='EC2',
                PaymentOption='ALL_UPFRONT',
                TermInYears='ONE_YEAR',
                LookbackPeriodInDays='SIXTY_DAYS'
            )
            
            for rec in response.get('Recommendations', []):
                for detail in rec.get('RecommendationDetails', []):
                    instance_details = detail['InstanceDetails']['EC2InstanceDetails']
                    
                    current_cost = float(detail['EstimatedMonthlySavingsAmount']) + float(detail['EstimatedMonthlyOnDemandCost'])
                    recommended_cost = float(detail['EstimatedMonthlyOnDemandCost'])
                    monthly_savings = float(detail['EstimatedMonthlySavingsAmount'])
                    
                    recommendations.append(OptimizationRecommendation(
                        id=f"ri_{instance_details['InstanceType']}_{instance_details['Region']}",
                        type=OptimizationType.RESERVED_INSTANCES,
                        resource_id=instance_details['InstanceType'],
                        resource_type=ResourceType.EC2_INSTANCE,
                        current_cost=current_cost,
                        recommended_cost=recommended_cost,
                        monthly_savings=monthly_savings,
                        annual_savings=monthly_savings * 12,
                        effort_level='low',
                        risk_level='low',
                        description=f"Purchase Reserved Instance for {instance_details['InstanceType']} in {instance_details['Region']}",
                        implementation_steps=[
                            f"Purchase {detail['RecommendedNumberOfInstancesToPurchase']} Reserved Instances",
                            f"Instance Type: {instance_details['InstanceType']}",
                            f"Region: {instance_details['Region']}",
                            "Payment Option: All Upfront for maximum savings"
                        ],
                        automated=True,
                        priority_score=monthly_savings / current_cost if current_cost > 0 else 0
                    ))
            
        except ClientError as e:
            logger.error(f"Failed to get RI recommendations: {e}")
        
        return recommendations
    
    def _map_service_to_resource_type(self, service: str) -> ResourceType:
        """Map AWS service to resource type"""
        mapping = {
            'Amazon Elastic Compute Cloud - Compute': ResourceType.EC2_INSTANCE,
            'Amazon Relational Database Service': ResourceType.RDS_INSTANCE,
            'AWS Lambda': ResourceType.LAMBDA_FUNCTION,
            'Amazon Simple Storage Service': ResourceType.S3_BUCKET,
            'Amazon Elastic Block Store': ResourceType.EBS_VOLUME,
            'Amazon Elastic Load Balancing': ResourceType.LOAD_BALANCER,
            'Amazon Virtual Private Cloud': ResourceType.NAT_GATEWAY
        }
        return mapping.get(service, ResourceType.EC2_INSTANCE)
    
    def _map_service_to_category(self, service: str) -> CostCategory:
        """Map AWS service to cost category"""
        if 'Compute' in service or 'EC2' in service:
            return CostCategory.COMPUTE
        elif 'Storage' in service or 'S3' in service or 'EBS' in service:
            return CostCategory.STORAGE
        elif 'Database' in service or 'RDS' in service:
            return CostCategory.DATABASE
        elif 'Lambda' in service:
            return CostCategory.SERVERLESS
        elif 'Network' in service or 'VPC' in service or 'CloudFront' in service:
            return CostCategory.NETWORK
        elif 'Container' in service or 'ECS' in service or 'EKS' in service:
            return CostCategory.CONTAINER
        else:
            return CostCategory.OTHER
    
    def _extract_usage_unit(self, usage_type: str) -> str:
        """Extract usage unit from usage type"""
        if 'Hours' in usage_type:
            return 'hours'
        elif 'GB-Month' in usage_type:
            return 'GB-months'
        elif 'Requests' in usage_type:
            return 'requests'
        elif 'GB' in usage_type:
            return 'GB'
        else:
            return 'units'
    
    def _get_region_name(self, region_code: str) -> str:
        """Convert region code to region name"""
        region_names = {
            'us-east-1': 'US East (N. Virginia)',
            'us-west-2': 'US West (Oregon)',
            'eu-west-1': 'EU (Ireland)',
            'ap-southeast-1': 'Asia Pacific (Singapore)'
        }
        return region_names.get(region_code, region_code)
    
    def _extract_on_demand_price(self, price_data: Dict) -> Optional[float]:
        """Extract on-demand price from pricing data"""
        try:
            terms = price_data.get('terms', {}).get('OnDemand', {})
            for term in terms.values():
                for price_dimension in term.get('priceDimensions', {}).values():
                    if price_dimension['unit'] == 'Hrs':
                        return float(price_dimension['pricePerUnit']['USD'])
        except Exception:
            pass
        return None


class CostOptimizer:
    """Main cost optimization engine"""
    
    def __init__(self):
        self.analyzers: Dict[str, CostAnalyzer] = {}
        self.cost_history: List[CostData] = []
        self.recommendations: List[OptimizationRecommendation] = []
        self.budgets: Dict[str, CostBudget] = {}
        self.anomalies: List[CostAnomaly] = []
        self._running = False
        
        # Initialize metrics
        if ANALYTICS_AVAILABLE:
            self.cost_gauge = Gauge(
                'cloud_cost_current',
                'Current cloud costs',
                ['provider', 'service', 'category']
            )
            self.savings_gauge = Gauge(
                'cloud_cost_savings_potential',
                'Potential cost savings',
                ['type', 'resource_type']
            )
            self.anomaly_counter = Counter(
                'cloud_cost_anomalies_total',
                'Total cost anomalies detected',
                ['severity', 'service']
            )
    
    def add_analyzer(self, provider: str, analyzer: CostAnalyzer):
        """Add cost analyzer for a provider"""
        self.analyzers[provider] = analyzer
        logger.info(f"Added cost analyzer for {provider}")
    
    def add_budget(self, budget: CostBudget):
        """Add cost budget"""
        self.budgets[budget.name] = budget
        logger.info(f"Added budget: {budget.name} (${budget.amount} {budget.period})")
    
    async def analyze_costs(self, days_back: int = 30) -> Dict[str, Any]:
        """Analyze costs across all providers"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        analysis_result = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_cost': 0.0,
            'costs_by_provider': {},
            'costs_by_category': defaultdict(float),
            'costs_by_service': defaultdict(float),
            'top_resources': [],
            'cost_trend': [],
            'recommendations': [],
            'anomalies': []
        }
        
        # Collect costs from all providers
        all_costs = []
        for provider_name, analyzer in self.analyzers.items():
            try:
                provider_costs = await analyzer.get_current_costs(start_date, end_date)
                all_costs.extend(provider_costs)
                
                provider_total = sum(cost.amount for cost in provider_costs)
                analysis_result['costs_by_provider'][provider_name] = provider_total
                analysis_result['total_cost'] += provider_total
                
                logger.info(f"Analyzed {len(provider_costs)} cost items from {provider_name}")
                
            except Exception as e:
                logger.error(f"Failed to analyze costs for {provider_name}: {e}")
        
        self.cost_history = all_costs
        
        # Aggregate costs by category and service
        for cost in all_costs:
            analysis_result['costs_by_category'][cost.category.value] += cost.amount
            analysis_result['costs_by_service'][cost.service] += cost.amount
        
        # Find top cost resources
        resource_costs = defaultdict(float)
        for cost in all_costs:
            resource_costs[cost.resource_id] += cost.amount
        
        top_resources = sorted(
            resource_costs.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        analysis_result['top_resources'] = [
            {'resource_id': res_id, 'cost': cost}
            for res_id, cost in top_resources
        ]
        
        # Calculate daily cost trend
        daily_costs = defaultdict(float)
        for cost in all_costs:
            day = cost.timestamp.date()
            daily_costs[day] += cost.amount
        
        analysis_result['cost_trend'] = [
            {'date': day.isoformat(), 'cost': cost}
            for day, cost in sorted(daily_costs.items())
        ]
        
        # Generate optimization recommendations
        analysis_result['recommendations'] = await self.generate_recommendations()
        
        # Detect anomalies
        analysis_result['anomalies'] = await self.detect_anomalies()
        
        # Update metrics
        if ANALYTICS_AVAILABLE:
            for provider, cost in analysis_result['costs_by_provider'].items():
                self.cost_gauge.labels(provider=provider, service='all', category='all').set(cost)
            
            for category, cost in analysis_result['costs_by_category'].items():
                self.cost_gauge.labels(provider='all', service='all', category=category).set(cost)
        
        return analysis_result
    
    async def generate_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        # Get recommendations from each analyzer
        for provider_name, analyzer in self.analyzers.items():
            try:
                # Reserved Instance recommendations
                ri_recommendations = await analyzer.get_reserved_instance_recommendations()
                recommendations.extend(ri_recommendations)
                
                # Rightsizing recommendations
                rightsizing_recs = await self._generate_rightsizing_recommendations(provider_name, analyzer)
                recommendations.extend(rightsizing_recs)
                
                # Unused resource recommendations
                unused_recs = await self._find_unused_resources(provider_name, analyzer)
                recommendations.extend(unused_recs)
                
            except Exception as e:
                logger.error(f"Failed to generate recommendations for {provider_name}: {e}")
        
        # Sort by priority score
        recommendations.sort(key=lambda r: r.priority_score, reverse=True)
        
        self.recommendations = recommendations
        
        # Update metrics
        if ANALYTICS_AVAILABLE:
            for rec in recommendations:
                self.savings_gauge.labels(
                    type=rec.type.value,
                    resource_type=rec.resource_type.value
                ).set(rec.monthly_savings)
        
        return recommendations[:20]  # Return top 20 recommendations
    
    async def _generate_rightsizing_recommendations(
        self,
        provider: str,
        analyzer: CostAnalyzer
    ) -> List[OptimizationRecommendation]:
        """Generate rightsizing recommendations"""
        recommendations = []
        
        # Analyze resource utilization
        resource_costs = defaultdict(lambda: {'cost': 0, 'service': '', 'type': None})
        
        for cost in self.cost_history:
            if cost.provider == provider and cost.resource_type == ResourceType.EC2_INSTANCE:
                resource_costs[cost.resource_id]['cost'] += cost.amount
                resource_costs[cost.resource_id]['service'] = cost.service
                resource_costs[cost.resource_id]['type'] = cost.resource_type
        
        for resource_id, info in resource_costs.items():
            if info['cost'] > 100:  # Only analyze resources costing > $100/month
                try:
                    utilization = await analyzer.get_resource_utilization(resource_id)
                    
                    if utilization:
                        avg_cpu = utilization.get('cpu_average', 0)
                        max_cpu = utilization.get('cpu_maximum', 0)
                        
                        # Check if underutilized
                        if avg_cpu < 20 and max_cpu < 50:
                            current_cost = info['cost']
                            recommended_cost = current_cost * 0.5  # Assume 50% savings
                            
                            recommendations.append(OptimizationRecommendation(
                                id=f"rightsize_{resource_id}",
                                type=OptimizationType.RIGHTSIZING,
                                resource_id=resource_id,
                                resource_type=info['type'],
                                current_cost=current_cost,
                                recommended_cost=recommended_cost,
                                monthly_savings=current_cost - recommended_cost,
                                annual_savings=(current_cost - recommended_cost) * 12,
                                effort_level='medium',
                                risk_level='low',
                                description=f"Rightsize underutilized instance {resource_id} (CPU avg: {avg_cpu:.1f}%)",
                                implementation_steps=[
                                    "Analyze workload patterns",
                                    "Select smaller instance type",
                                    "Schedule maintenance window",
                                    "Resize instance",
                                    "Monitor performance"
                                ],
                                automated=False,
                                priority_score=0.8
                            ))
                
                except Exception as e:
                    logger.error(f"Failed to analyze utilization for {resource_id}: {e}")
        
        return recommendations
    
    async def _find_unused_resources(
        self,
        provider: str,
        analyzer: CostAnalyzer
    ) -> List[OptimizationRecommendation]:
        """Find unused resources"""
        recommendations = []
        
        # Find resources with zero utilization
        for cost in self.cost_history:
            if cost.provider == provider and cost.usage_quantity == 0 and cost.amount > 0:
                recommendations.append(OptimizationRecommendation(
                    id=f"unused_{cost.resource_id}",
                    type=OptimizationType.UNUSED_RESOURCES,
                    resource_id=cost.resource_id,
                    resource_type=cost.resource_type,
                    current_cost=cost.amount * 30,  # Monthly cost
                    recommended_cost=0,
                    monthly_savings=cost.amount * 30,
                    annual_savings=cost.amount * 365,
                    effort_level='low',
                    risk_level='low',
                    description=f"Remove unused {cost.resource_type.value}: {cost.resource_id}",
                    implementation_steps=[
                        "Verify resource is not needed",
                        "Backup any important data",
                        "Delete or terminate resource",
                        "Update documentation"
                    ],
                    automated=True,
                    priority_score=1.0
                ))
        
        return recommendations
    
    async def detect_anomalies(self, threshold_percent: float = 25.0) -> List[CostAnomaly]:
        """Detect cost anomalies"""
        anomalies = []
        
        # Group costs by service and day
        daily_service_costs = defaultdict(lambda: defaultdict(float))
        
        for cost in self.cost_history:
            day = cost.timestamp.date()
            key = f"{cost.provider}_{cost.service}"
            daily_service_costs[key][day] += cost.amount
        
        # Detect anomalies
        for service_key, daily_costs in daily_service_costs.items():
            if len(daily_costs) < 7:
                continue
            
            costs_array = np.array(list(daily_costs.values()))
            mean_cost = np.mean(costs_array)
            std_cost = np.std(costs_array)
            
            # Find outliers (costs > mean + 2*std)
            for day, cost in daily_costs.items():
                if cost > mean_cost + 2 * std_cost:
                    variance_percent = ((cost - mean_cost) / mean_cost) * 100
                    
                    if variance_percent > threshold_percent:
                        anomaly = CostAnomaly(
                            id=f"anomaly_{service_key}_{day}",
                            timestamp=datetime.combine(day, datetime.min.time()),
                            resource_id=service_key,
                            service=service_key.split('_', 1)[1],
                            expected_cost=mean_cost,
                            actual_cost=cost,
                            variance_percent=variance_percent,
                            severity=self._get_anomaly_severity(variance_percent),
                            description=f"Unusual cost spike detected for {service_key}",
                            recommended_action="Investigate resource usage and recent changes"
                        )
                        
                        anomalies.append(anomaly)
                        
                        # Update metrics
                        if ANALYTICS_AVAILABLE:
                            self.anomaly_counter.labels(
                                severity=anomaly.severity,
                                service=anomaly.service
                            ).inc()
        
        self.anomalies = anomalies
        return anomalies
    
    def _get_anomaly_severity(self, variance_percent: float) -> str:
        """Determine anomaly severity"""
        if variance_percent > 100:
            return 'critical'
        elif variance_percent > 50:
            return 'high'
        elif variance_percent > 25:
            return 'medium'
        else:
            return 'low'
    
    async def check_budgets(self) -> List[Dict[str, Any]]:
        """Check budget status"""
        alerts = []
        
        for budget_name, budget in self.budgets.items():
            # Calculate actual spending
            actual_spend = 0.0
            
            # Filter costs based on budget criteria
            for cost in self.cost_history:
                # Check if cost matches budget criteria
                if budget.services and cost.service not in budget.services:
                    continue
                
                if budget.tags:
                    if not all(cost.tags.get(k) == v for k, v in budget.tags.items()):
                        continue
                
                actual_spend += cost.amount
            
            # Check against budget amount
            budget_usage_percent = (actual_spend / budget.amount) * 100
            
            # Check alert thresholds
            for threshold in budget.alert_thresholds:
                if budget_usage_percent >= threshold:
                    alert = {
                        'budget_name': budget_name,
                        'budget_amount': budget.amount,
                        'actual_spend': actual_spend,
                        'usage_percent': budget_usage_percent,
                        'threshold': threshold,
                        'period': budget.period,
                        'timestamp': datetime.utcnow()
                    }
                    
                    alerts.append(alert)
                    
                    # Send notifications
                    await self._send_budget_alert(budget, alert)
                    
                    # Execute auto actions
                    if budget.auto_actions and threshold >= 100:
                        await self._execute_budget_actions(budget, alert)
        
        return alerts
    
    async def _send_budget_alert(self, budget: CostBudget, alert: Dict[str, Any]):
        """Send budget alert notifications"""
        for channel in budget.notification_channels:
            try:
                if channel.startswith('email://'):
                    # Send email notification
                    logger.info(f"Sending budget alert email for {budget.name}")
                elif channel.startswith('slack://'):
                    # Send Slack notification
                    logger.info(f"Sending budget alert to Slack for {budget.name}")
                elif channel.startswith('sns://'):
                    # Send SNS notification
                    logger.info(f"Sending budget alert to SNS for {budget.name}")
            except Exception as e:
                logger.error(f"Failed to send budget alert: {e}")
    
    async def _execute_budget_actions(self, budget: CostBudget, alert: Dict[str, Any]):
        """Execute automated budget actions"""
        for action in budget.auto_actions:
            action_type = action.get('type')
            
            try:
                if action_type == 'stop_instances':
                    # Stop non-critical instances
                    logger.warning(f"Executing budget action: stopping instances for {budget.name}")
                elif action_type == 'disable_services':
                    # Disable non-essential services
                    logger.warning(f"Executing budget action: disabling services for {budget.name}")
                elif action_type == 'notify_owners':
                    # Notify resource owners
                    logger.warning(f"Executing budget action: notifying owners for {budget.name}")
            except Exception as e:
                logger.error(f"Failed to execute budget action: {e}")
    
    async def forecast_costs(self, days_ahead: int = 30) -> CostForecast:
        """Forecast future costs"""
        if len(self.cost_history) < 30:
            return CostForecast(
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow() + timedelta(days=days_ahead),
                predicted_cost=0.0,
                confidence_interval=(0.0, 0.0),
                trend='insufficient_data',
                seasonality_factor=1.0
            )
        
        # Prepare data for forecasting
        daily_costs = defaultdict(float)
        for cost in self.cost_history:
            day = cost.timestamp.date()
            daily_costs[day] += cost.amount
        
        # Convert to time series
        dates = sorted(daily_costs.keys())
        costs = [daily_costs[d] for d in dates]
        
        # Simple linear regression for trend
        x = np.arange(len(costs))
        y = np.array(costs)
        
        # Fit linear model
        coeffs = np.polyfit(x, y, 1)
        trend_line = np.poly1d(coeffs)
        
        # Predict future costs
        future_x = np.arange(len(costs), len(costs) + days_ahead)
        predicted_costs = trend_line(future_x)
        
        # Calculate confidence interval (simplified)
        std_error = np.std(y - trend_line(x))
        confidence_interval = (
            max(0, predicted_costs.sum() - 2 * std_error * days_ahead),
            predicted_costs.sum() + 2 * std_error * days_ahead
        )
        
        # Determine trend
        if coeffs[0] > 0.1:
            trend = 'increasing'
        elif coeffs[0] < -0.1:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        # Generate recommendations based on forecast
        recommendations = []
        if trend == 'increasing':
            recommendations.append("Consider implementing cost optimization recommendations")
            recommendations.append("Review and adjust budget allocations")
            recommendations.append("Evaluate reserved instance purchases")
        
        return CostForecast(
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow() + timedelta(days=days_ahead),
            predicted_cost=predicted_costs.sum(),
            confidence_interval=confidence_interval,
            trend=trend,
            seasonality_factor=1.0,  # Simplified - would use proper seasonality analysis
            recommendations=recommendations
        )
    
    async def generate_cost_report(self, output_path: Path) -> bool:
        """Generate comprehensive cost report"""
        try:
            # Analyze current costs
            analysis = await self.analyze_costs()
            
            # Create visualizations if available
            if ANALYTICS_AVAILABLE:
                plt.style.use('seaborn-v0_8-darkgrid')
                fig, axes = plt.subplots(2, 2, figsize=(15, 10))
                
                # Cost by provider
                providers = list(analysis['costs_by_provider'].keys())
                costs = list(analysis['costs_by_provider'].values())
                axes[0, 0].pie(costs, labels=providers, autopct='%1.1f%%')
                axes[0, 0].set_title('Costs by Provider')
                
                # Cost trend
                dates = [d['date'] for d in analysis['cost_trend']]
                daily_costs = [d['cost'] for d in analysis['cost_trend']]
                axes[0, 1].plot(dates, daily_costs, marker='o')
                axes[0, 1].set_title('Daily Cost Trend')
                axes[0, 1].tick_params(axis='x', rotation=45)
                
                # Top resources
                resources = [r['resource_id'][:20] for r in analysis['top_resources'][:5]]
                resource_costs = [r['cost'] for r in analysis['top_resources'][:5]]
                axes[1, 0].barh(resources, resource_costs)
                axes[1, 0].set_title('Top 5 Cost Resources')
                axes[1, 0].set_xlabel('Cost ($)')
                
                # Category breakdown
                categories = list(analysis['costs_by_category'].keys())
                category_costs = list(analysis['costs_by_category'].values())
                axes[1, 1].bar(categories, category_costs)
                axes[1, 1].set_title('Costs by Category')
                axes[1, 1].tick_params(axis='x', rotation=45)
                
                plt.tight_layout()
                plt.savefig(output_path / 'cost_analysis.png', dpi=300, bbox_inches='tight')
                plt.close()
            
            # Generate text report
            report_path = output_path / 'cost_report.txt'
            with open(report_path, 'w') as f:
                f.write("NEXUS Cloud Cost Report\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"Report Period: {analysis['period']['start']} to {analysis['period']['end']}\n")
                f.write(f"Total Cost: ${analysis['total_cost']:.2f}\n\n")
                
                f.write("Costs by Provider:\n")
                for provider, cost in analysis['costs_by_provider'].items():
                    f.write(f"  {provider}: ${cost:.2f}\n")
                
                f.write("\nTop Optimization Recommendations:\n")
                for i, rec in enumerate(analysis['recommendations'][:5], 1):
                    f.write(f"\n{i}. {rec.description}\n")
                    f.write(f"   Potential Savings: ${rec.monthly_savings:.2f}/month\n")
                    f.write(f"   Effort: {rec.effort_level}, Risk: {rec.risk_level}\n")
                
                if analysis['anomalies']:
                    f.write("\nCost Anomalies Detected:\n")
                    for anomaly in analysis['anomalies'][:5]:
                        f.write(f"  - {anomaly.service}: {anomaly.variance_percent:.1f}% increase\n")
            
            logger.info(f"Cost report generated at {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate cost report: {e}")
            return False
    
    async def implement_recommendation(self, recommendation_id: str) -> bool:
        """Automatically implement a recommendation"""
        recommendation = next(
            (r for r in self.recommendations if r.id == recommendation_id),
            None
        )
        
        if not recommendation:
            logger.error(f"Recommendation {recommendation_id} not found")
            return False
        
        if not recommendation.automated:
            logger.warning(f"Recommendation {recommendation_id} cannot be automated")
            return False
        
        try:
            logger.info(f"Implementing recommendation: {recommendation.description}")
            
            if recommendation.type == OptimizationType.UNUSED_RESOURCES:
                # Delete unused resources
                # Implementation would call cloud provider APIs
                logger.info(f"Would delete resource: {recommendation.resource_id}")
                return True
            
            elif recommendation.type == OptimizationType.RESERVED_INSTANCES:
                # Purchase reserved instances
                # Implementation would call cloud provider APIs
                logger.info(f"Would purchase RI for: {recommendation.resource_id}")
                return True
            
            elif recommendation.type == OptimizationType.SCHEDULED_SCALING:
                # Implement scheduled scaling
                # Implementation would configure auto-scaling
                logger.info(f"Would configure scheduled scaling for: {recommendation.resource_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to implement recommendation: {e}")
            return False


class MultiCloudCostManager:
    """Manage costs across multiple cloud providers"""
    
    def __init__(self):
        self.optimizer = CostOptimizer()
        self._setup_analyzers()
        self._setup_default_budgets()
    
    def _setup_analyzers(self):
        """Setup cost analyzers for each provider"""
        # AWS
        if AWS_AVAILABLE and os.getenv('AWS_ACCESS_KEY_ID'):
            aws_analyzer = AWSCostAnalyzer()
            self.optimizer.add_analyzer('AWS', aws_analyzer)
        
        # Add other providers as implemented
    
    def _setup_default_budgets(self):
        """Setup default budgets"""
        # Overall monthly budget
        overall_budget = CostBudget(
            name='overall_monthly',
            amount=10000.0,
            period='monthly',
            alert_thresholds=[80, 90, 100, 110],
            notification_channels=['email://admin@nexus.io'],
            auto_actions=[
                {'type': 'notify_owners', 'threshold': 100},
                {'type': 'stop_instances', 'threshold': 110, 'tag_filter': {'Critical': 'false'}}
            ]
        )
        self.optimizer.add_budget(overall_budget)
        
        # Development environment budget
        dev_budget = CostBudget(
            name='development_monthly',
            amount=2000.0,
            period='monthly',
            tags={'Environment': 'development'},
            alert_thresholds=[90, 100],
            notification_channels=['slack://dev-channel']
        )
        self.optimizer.add_budget(dev_budget)
    
    async def run_cost_optimization_cycle(self):
        """Run complete cost optimization cycle"""
        logger.info("Starting cost optimization cycle")
        
        # Analyze costs
        analysis = await self.optimizer.analyze_costs()
        logger.info(f"Total cost: ${analysis['total_cost']:.2f}")
        
        # Check budgets
        budget_alerts = await self.optimizer.check_budgets()
        if budget_alerts:
            logger.warning(f"Budget alerts: {len(budget_alerts)}")
        
        # Forecast costs
        forecast = await self.optimizer.forecast_costs()
        logger.info(f"30-day forecast: ${forecast.predicted_cost:.2f} ({forecast.trend})")
        
        # Generate report
        report_path = Path('/tmp/nexus_cost_reports')
        report_path.mkdir(exist_ok=True)
        await self.optimizer.generate_cost_report(report_path)
        
        # Auto-implement high-priority recommendations
        for rec in self.optimizer.recommendations[:3]:
            if rec.automated and rec.priority_score > 0.8:
                logger.info(f"Auto-implementing: {rec.description}")
                await self.optimizer.implement_recommendation(rec.id)
        
        return {
            'total_cost': analysis['total_cost'],
            'recommendations': len(analysis['recommendations']),
            'potential_savings': sum(r.monthly_savings for r in analysis['recommendations']),
            'anomalies': len(analysis['anomalies']),
            'budget_alerts': len(budget_alerts)
        }


# Example usage
async def example_usage():
    """Example cost optimization usage"""
    
    # Initialize cost manager
    manager = MultiCloudCostManager()
    
    # Run optimization cycle
    results = await manager.run_cost_optimization_cycle()
    
    print(f"Cost Optimization Results:")
    print(f"  Total Cost: ${results['total_cost']:.2f}")
    print(f"  Recommendations: {results['recommendations']}")
    print(f"  Potential Monthly Savings: ${results['potential_savings']:.2f}")
    print(f"  Anomalies Detected: {results['anomalies']}")
    print(f"  Budget Alerts: {results['budget_alerts']}")
    
    # Get specific recommendations
    analysis = await manager.optimizer.analyze_costs()
    
    print("\nTop 5 Recommendations:")
    for i, rec in enumerate(analysis['recommendations'][:5], 1):
        print(f"\n{i}. {rec.description}")
        print(f"   Type: {rec.type.value}")
        print(f"   Monthly Savings: ${rec.monthly_savings:.2f}")
        print(f"   Annual Savings: ${rec.annual_savings:.2f}")
        print(f"   Effort: {rec.effort_level}, Risk: {rec.risk_level}")
        print(f"   Automated: {'Yes' if rec.automated else 'No'}")


if __name__ == "__main__":
    asyncio.run(example_usage())