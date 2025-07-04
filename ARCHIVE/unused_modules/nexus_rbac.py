"""
NEXUS Role-Based Access Control (RBAC)
Comprehensive RBAC system with dynamic policies, audit logging, and compliance
"""

import json
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Tuple, Any, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from functools import wraps, lru_cache
import hashlib
import logging
from pathlib import Path
import asyncio
from collections import defaultdict
import yaml
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Permission(Enum):
    """System permissions"""
    # Resource permissions
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    
    # System permissions
    ADMIN = "admin"
    DEPLOY = "deploy"
    MONITOR = "monitor"
    AUDIT = "audit"
    
    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # API permissions
    API_CREATE = "api:create"
    API_READ = "api:read"
    API_UPDATE = "api:update"
    API_DELETE = "api:delete"
    
    # Project permissions
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_DEPLOY = "project:deploy"
    
    # Security permissions
    SECURITY_AUDIT = "security:audit"
    SECURITY_CONFIG = "security:config"
    SECURITY_SCAN = "security:scan"
    
    # AI/ML permissions
    AI_TRAIN = "ai:train"
    AI_PREDICT = "ai:predict"
    AI_CONFIG = "ai:config"


class ResourceType(Enum):
    """Resource types in the system"""
    USER = "user"
    PROJECT = "project"
    API = "api"
    DATABASE = "database"
    FILE = "file"
    SERVICE = "service"
    DEPLOYMENT = "deployment"
    MODEL = "model"
    SECRET = "secret"
    AUDIT_LOG = "audit_log"


class ComplianceFramework(Enum):
    """Supported compliance frameworks"""
    SOC2 = "soc2"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"
    CCPA = "ccpa"


class AuditEventType(Enum):
    """Types of audit events"""
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    RESOURCE_CREATED = "resource_created"
    RESOURCE_READ = "resource_read"
    RESOURCE_UPDATED = "resource_updated"
    RESOURCE_DELETED = "resource_deleted"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    POLICY_CREATED = "policy_created"
    POLICY_UPDATED = "policy_updated"
    POLICY_DELETED = "policy_deleted"
    AUTHENTICATION = "authentication"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_ALERT = "security_alert"


@dataclass
class Role:
    """Role definition"""
    id: str
    name: str
    description: str
    permissions: Set[Permission]
    inherits_from: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_system: bool = False
    is_active: bool = True


@dataclass
class Resource:
    """Resource definition"""
    id: str
    type: ResourceType
    name: str
    owner: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Policy:
    """Access control policy"""
    id: str
    name: str
    description: str
    effect: str  # "allow" or "deny"
    principals: List[str]  # Users or roles
    actions: List[Permission]
    resources: List[str]  # Resource patterns
    conditions: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    is_active: bool = True


@dataclass
class AuditEvent:
    """Audit event record"""
    id: str
    timestamp: datetime
    event_type: AuditEventType
    user_id: str
    resource_id: Optional[str] = None
    resource_type: Optional[ResourceType] = None
    action: Optional[Permission] = None
    result: str = "success"  # "success" or "failure"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    compliance_tags: List[ComplianceFramework] = field(default_factory=list)


@dataclass
class AccessContext:
    """Context for access control decisions"""
    user_id: str
    roles: List[str]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    request_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class RBACManager:
    """Role-Based Access Control Manager"""
    
    def __init__(self, audit_retention_days: int = 365):
        self.roles: Dict[str, Role] = {}
        self.resources: Dict[str, Resource] = {}
        self.policies: Dict[str, Policy] = {}
        self.user_roles: Dict[str, Set[str]] = defaultdict(set)
        self.audit_events: List[AuditEvent] = []
        self.audit_retention_days = audit_retention_days
        
        # Policy evaluation cache
        self._policy_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Initialize default roles
        self._init_default_roles()
        
        # Compliance mappings
        self.compliance_requirements = self._init_compliance_requirements()
        
    def _init_default_roles(self):
        """Initialize system default roles"""
        # Super Admin
        self.roles["super_admin"] = Role(
            id="super_admin",
            name="Super Administrator",
            description="Full system access",
            permissions=set(Permission),
            is_system=True
        )
        
        # Admin
        self.roles["admin"] = Role(
            id="admin",
            name="Administrator",
            description="Administrative access",
            permissions={
                Permission.ADMIN, Permission.USER_CREATE, Permission.USER_READ,
                Permission.USER_UPDATE, Permission.USER_DELETE, Permission.SECURITY_CONFIG,
                Permission.PROJECT_CREATE, Permission.PROJECT_UPDATE, Permission.PROJECT_DELETE
            },
            is_system=True
        )
        
        # Developer
        self.roles["developer"] = Role(
            id="developer",
            name="Developer",
            description="Development access",
            permissions={
                Permission.READ, Permission.WRITE, Permission.EXECUTE,
                Permission.PROJECT_CREATE, Permission.PROJECT_READ, Permission.PROJECT_UPDATE,
                Permission.API_CREATE, Permission.API_READ, Permission.API_UPDATE
            },
            is_system=True
        )
        
        # Viewer
        self.roles["viewer"] = Role(
            id="viewer",
            name="Viewer",
            description="Read-only access",
            permissions={
                Permission.READ, Permission.PROJECT_READ, Permission.API_READ
            },
            is_system=True
        )
        
        # Auditor
        self.roles["auditor"] = Role(
            id="auditor",
            name="Auditor",
            description="Audit and compliance access",
            permissions={
                Permission.AUDIT, Permission.SECURITY_AUDIT, Permission.READ
            },
            is_system=True
        )
        
    def _init_compliance_requirements(self) -> Dict[ComplianceFramework, Dict[str, Any]]:
        """Initialize compliance framework requirements"""
        return {
            ComplianceFramework.SOC2: {
                "required_audit_events": [
                    AuditEventType.ACCESS_GRANTED, AuditEventType.ACCESS_DENIED,
                    AuditEventType.AUTHENTICATION, AuditEventType.CONFIGURATION_CHANGE
                ],
                "retention_days": 365,
                "encryption_required": True
            },
            ComplianceFramework.GDPR: {
                "required_audit_events": [
                    AuditEventType.RESOURCE_READ, AuditEventType.RESOURCE_UPDATED,
                    AuditEventType.RESOURCE_DELETED
                ],
                "retention_days": 1095,  # 3 years
                "data_minimization": True,
                "right_to_erasure": True
            },
            ComplianceFramework.HIPAA: {
                "required_audit_events": list(AuditEventType),
                "retention_days": 2190,  # 6 years
                "encryption_required": True,
                "access_controls": True
            }
        }
    
    # Role Management
    def create_role(self, name: str, description: str, permissions: Set[Permission],
                   inherits_from: Optional[List[str]] = None) -> Role:
        """Create a new role"""
        role_id = f"role_{uuid.uuid4().hex[:8]}"
        
        # Collect inherited permissions
        all_permissions = set(permissions)
        if inherits_from:
            for parent_role_id in inherits_from:
                if parent_role := self.roles.get(parent_role_id):
                    all_permissions.update(parent_role.permissions)
                    
        role = Role(
            id=role_id,
            name=name,
            description=description,
            permissions=all_permissions,
            inherits_from=inherits_from or []
        )
        
        self.roles[role_id] = role
        
        # Audit event
        self._audit_event(
            AuditEventType.ROLE_ASSIGNED,
            "system",
            details={
                "role_id": role_id,
                "role_name": name,
                "permissions": [p.value for p in permissions]
            }
        )
        
        return role
    
    def assign_role(self, user_id: str, role_id: str, context: Optional[AccessContext] = None):
        """Assign role to user"""
        if role_id not in self.roles:
            raise ValueError(f"Role not found: {role_id}")
            
        self.user_roles[user_id].add(role_id)
        
        # Audit event
        self._audit_event(
            AuditEventType.ROLE_ASSIGNED,
            context.user_id if context else "system",
            details={
                "target_user": user_id,
                "role_id": role_id,
                "role_name": self.roles[role_id].name
            },
            context=context
        )
        
    def remove_role(self, user_id: str, role_id: str, context: Optional[AccessContext] = None):
        """Remove role from user"""
        if role_id in self.user_roles[user_id]:
            self.user_roles[user_id].remove(role_id)
            
            # Audit event
            self._audit_event(
                AuditEventType.ROLE_REMOVED,
                context.user_id if context else "system",
                details={
                    "target_user": user_id,
                    "role_id": role_id,
                    "role_name": self.roles[role_id].name if role_id in self.roles else "unknown"
                },
                context=context
            )
    
    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """Get all permissions for a user"""
        permissions = set()
        
        for role_id in self.user_roles.get(user_id, []):
            if role := self.roles.get(role_id):
                permissions.update(role.permissions)
                
        return permissions
    
    # Resource Management
    def create_resource(self, resource_type: ResourceType, name: str, owner: str,
                       attributes: Optional[Dict[str, Any]] = None) -> Resource:
        """Create a new resource"""
        resource_id = f"{resource_type.value}_{uuid.uuid4().hex[:8]}"
        
        resource = Resource(
            id=resource_id,
            type=resource_type,
            name=name,
            owner=owner,
            attributes=attributes or {}
        )
        
        self.resources[resource_id] = resource
        
        # Audit event
        self._audit_event(
            AuditEventType.RESOURCE_CREATED,
            owner,
            resource_id=resource_id,
            resource_type=resource_type,
            details={"resource_name": name}
        )
        
        return resource
    
    # Policy Management
    def create_policy(self, name: str, description: str, effect: str,
                     principals: List[str], actions: List[Permission],
                     resources: List[str], conditions: Optional[Dict[str, Any]] = None) -> Policy:
        """Create access control policy"""
        policy_id = f"policy_{uuid.uuid4().hex[:8]}"
        
        policy = Policy(
            id=policy_id,
            name=name,
            description=description,
            effect=effect,
            principals=principals,
            actions=actions,
            resources=resources,
            conditions=conditions or {}
        )
        
        self.policies[policy_id] = policy
        
        # Clear policy cache
        self._policy_cache.clear()
        
        # Audit event
        self._audit_event(
            AuditEventType.POLICY_CREATED,
            "system",
            details={
                "policy_id": policy_id,
                "policy_name": name,
                "effect": effect,
                "principals": principals,
                "actions": [a.value for a in actions]
            }
        )
        
        return policy
    
    # Access Control
    def check_permission(self, context: AccessContext, permission: Permission,
                        resource_id: Optional[str] = None) -> bool:
        """Check if user has permission"""
        # Check cache first
        cache_key = f"{context.user_id}:{permission.value}:{resource_id}"
        cached = self._get_cached_decision(cache_key)
        if cached is not None:
            return cached
            
        # Get user's permissions
        user_permissions = self.get_user_permissions(context.user_id)
        
        # Check if user has the required permission
        has_permission = permission in user_permissions
        
        # If resource is specified, check resource-based policies
        if resource_id and resource_id in self.resources:
            resource = self.resources[resource_id]
            has_permission = self._evaluate_resource_policies(
                context, permission, resource, has_permission
            )
            
        # Cache decision
        self._cache_decision(cache_key, has_permission)
        
        # Audit event
        self._audit_event(
            AuditEventType.ACCESS_GRANTED if has_permission else AuditEventType.ACCESS_DENIED,
            context.user_id,
            resource_id=resource_id,
            action=permission,
            details={
                "permission": permission.value,
                "resource_id": resource_id,
                "result": "granted" if has_permission else "denied"
            },
            context=context
        )
        
        return has_permission
    
    def _evaluate_resource_policies(self, context: AccessContext, permission: Permission,
                                  resource: Resource, default: bool) -> bool:
        """Evaluate resource-specific policies"""
        result = default
        
        # Get applicable policies
        applicable_policies = []
        
        for policy in self.policies.values():
            if not policy.is_active:
                continue
                
            # Check if policy applies to user
            if not self._policy_applies_to_principal(policy, context):
                continue
                
            # Check if policy applies to action
            if permission not in policy.actions:
                continue
                
            # Check if policy applies to resource
            if not self._policy_applies_to_resource(policy, resource):
                continue
                
            # Check conditions
            if not self._evaluate_conditions(policy.conditions, context, resource):
                continue
                
            applicable_policies.append(policy)
            
        # Sort by priority and evaluate
        applicable_policies.sort(key=lambda p: p.priority, reverse=True)
        
        for policy in applicable_policies:
            if policy.effect == "deny":
                return False
            elif policy.effect == "allow":
                result = True
                
        return result
    
    def _policy_applies_to_principal(self, policy: Policy, context: AccessContext) -> bool:
        """Check if policy applies to the principal"""
        for principal in policy.principals:
            if principal == context.user_id:
                return True
            if principal in context.roles:
                return True
            if principal == "*":  # Wildcard
                return True
        return False
    
    def _policy_applies_to_resource(self, policy: Policy, resource: Resource) -> bool:
        """Check if policy applies to the resource"""
        for resource_pattern in policy.resources:
            if resource_pattern == "*":  # Wildcard
                return True
            if resource_pattern == resource.id:
                return True
            if self._match_resource_pattern(resource_pattern, resource):
                return True
        return False
    
    def _match_resource_pattern(self, pattern: str, resource: Resource) -> bool:
        """Match resource against pattern (supports wildcards)"""
        # Convert pattern to regex
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        regex_pattern = f"^{regex_pattern}$"
        
        # Check against resource ID and type
        if re.match(regex_pattern, resource.id):
            return True
        if re.match(regex_pattern, f"{resource.type.value}/*"):
            return True
            
        return False
    
    def _evaluate_conditions(self, conditions: Dict[str, Any], context: AccessContext,
                           resource: Resource) -> bool:
        """Evaluate policy conditions"""
        if not conditions:
            return True
            
        for condition_type, condition_value in conditions.items():
            if condition_type == "ip_range":
                if not self._check_ip_range(context.ip_address, condition_value):
                    return False
                    
            elif condition_type == "time_range":
                if not self._check_time_range(context.request_time, condition_value):
                    return False
                    
            elif condition_type == "resource_tags":
                if not self._check_resource_tags(resource.tags, condition_value):
                    return False
                    
            elif condition_type == "user_attributes":
                if not self._check_user_attributes(context.attributes, condition_value):
                    return False
                    
        return True
    
    def _check_ip_range(self, ip_address: Optional[str], allowed_ranges: List[str]) -> bool:
        """Check if IP address is in allowed ranges"""
        if not ip_address:
            return False
            
        # Implementation would check IP against CIDR ranges
        return True  # Placeholder
    
    def _check_time_range(self, request_time: datetime, time_range: Dict[str, str]) -> bool:
        """Check if request time is within allowed range"""
        # Implementation would parse time range and compare
        return True  # Placeholder
    
    def _check_resource_tags(self, resource_tags: List[str], required_tags: List[str]) -> bool:
        """Check if resource has required tags"""
        return all(tag in resource_tags for tag in required_tags)
    
    def _check_user_attributes(self, user_attributes: Dict[str, Any],
                             required_attributes: Dict[str, Any]) -> bool:
        """Check if user has required attributes"""
        for key, value in required_attributes.items():
            if key not in user_attributes:
                return False
            if user_attributes[key] != value:
                return False
        return True
    
    # Audit and Compliance
    def _audit_event(self, event_type: AuditEventType, user_id: str,
                    resource_id: Optional[str] = None,
                    resource_type: Optional[ResourceType] = None,
                    action: Optional[Permission] = None,
                    details: Optional[Dict[str, Any]] = None,
                    context: Optional[AccessContext] = None):
        """Record audit event"""
        event = AuditEvent(
            id=f"audit_{uuid.uuid4().hex}",
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            user_id=user_id,
            resource_id=resource_id,
            resource_type=resource_type,
            action=action,
            result="success",
            ip_address=context.ip_address if context else None,
            user_agent=context.user_agent if context else None,
            details=details or {}
        )
        
        # Add compliance tags based on event type
        event.compliance_tags = self._get_compliance_tags(event_type)
        
        self.audit_events.append(event)
        
        # Clean old audit events
        self._clean_old_audit_events()
        
        logger.info(f"Audit event: {event_type.value} by {user_id}")
    
    def _get_compliance_tags(self, event_type: AuditEventType) -> List[ComplianceFramework]:
        """Get compliance frameworks that require this event type"""
        tags = []
        
        for framework, requirements in self.compliance_requirements.items():
            if event_type in requirements.get("required_audit_events", []):
                tags.append(framework)
                
        return tags
    
    def _clean_old_audit_events(self):
        """Remove audit events older than retention period"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.audit_retention_days)
        
        # Keep events required for compliance
        self.audit_events = [
            event for event in self.audit_events
            if event.timestamp > cutoff_date or self._is_required_for_compliance(event)
        ]
    
    def _is_required_for_compliance(self, event: AuditEvent) -> bool:
        """Check if event must be retained for compliance"""
        for framework in event.compliance_tags:
            requirements = self.compliance_requirements.get(framework, {})
            retention_days = requirements.get("retention_days", 0)
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
            if event.timestamp > cutoff_date:
                return True
                
        return False
    
    def get_audit_events(self, filters: Optional[Dict[str, Any]] = None,
                        limit: int = 100) -> List[AuditEvent]:
        """Retrieve audit events with optional filters"""
        events = self.audit_events
        
        if filters:
            if "user_id" in filters:
                events = [e for e in events if e.user_id == filters["user_id"]]
                
            if "resource_id" in filters:
                events = [e for e in events if e.resource_id == filters["resource_id"]]
                
            if "event_type" in filters:
                events = [e for e in events if e.event_type == filters["event_type"]]
                
            if "start_date" in filters:
                events = [e for e in events if e.timestamp >= filters["start_date"]]
                
            if "end_date" in filters:
                events = [e for e in events if e.timestamp <= filters["end_date"]]
                
            if "compliance_framework" in filters:
                framework = filters["compliance_framework"]
                events = [e for e in events if framework in e.compliance_tags]
                
        # Sort by timestamp descending and limit
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]
    
    def generate_compliance_report(self, framework: ComplianceFramework,
                                 start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate compliance report for specified framework"""
        requirements = self.compliance_requirements.get(framework, {})
        
        # Get relevant audit events
        events = self.get_audit_events({
            "start_date": start_date,
            "end_date": end_date,
            "compliance_framework": framework
        }, limit=10000)
        
        # Analyze events
        event_summary = defaultdict(int)
        user_activity = defaultdict(int)
        resource_access = defaultdict(int)
        
        for event in events:
            event_summary[event.event_type.value] += 1
            user_activity[event.user_id] += 1
            if event.resource_id:
                resource_access[event.resource_type.value if event.resource_type else "unknown"] += 1
                
        report = {
            "framework": framework.value,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_events": len(events),
            "event_summary": dict(event_summary),
            "unique_users": len(user_activity),
            "user_activity": dict(user_activity),
            "resource_access": dict(resource_access),
            "requirements_met": self._check_compliance_requirements(framework, events),
            "recommendations": self._get_compliance_recommendations(framework, events)
        }
        
        return report
    
    def _check_compliance_requirements(self, framework: ComplianceFramework,
                                     events: List[AuditEvent]) -> Dict[str, bool]:
        """Check if compliance requirements are met"""
        requirements = self.compliance_requirements.get(framework, {})
        results = {}
        
        # Check required event types
        required_events = set(requirements.get("required_audit_events", []))
        logged_events = set(event.event_type for event in events)
        results["required_events_logged"] = required_events.issubset(logged_events)
        
        # Check other requirements
        if "encryption_required" in requirements:
            results["encryption_enabled"] = True  # Would check actual encryption status
            
        if "access_controls" in requirements:
            results["access_controls_enforced"] = True  # Would check actual enforcement
            
        return results
    
    def _get_compliance_recommendations(self, framework: ComplianceFramework,
                                      events: List[AuditEvent]) -> List[str]:
        """Get recommendations for improving compliance"""
        recommendations = []
        
        # Analyze patterns and suggest improvements
        if framework == ComplianceFramework.SOC2:
            if len(events) < 1000:
                recommendations.append("Increase audit logging coverage")
                
        elif framework == ComplianceFramework.GDPR:
            # Check for data access patterns
            data_access_events = [e for e in events if e.event_type in [
                AuditEventType.RESOURCE_READ, AuditEventType.RESOURCE_UPDATED
            ]]
            if len(data_access_events) < 100:
                recommendations.append("Implement comprehensive data access logging")
                
        return recommendations
    
    # Caching
    def _get_cached_decision(self, cache_key: str) -> Optional[bool]:
        """Get cached access decision"""
        if cache_key in self._policy_cache:
            cached_time, decision = self._policy_cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                return decision
            else:
                del self._policy_cache[cache_key]
        return None
    
    def _cache_decision(self, cache_key: str, decision: bool):
        """Cache access decision"""
        self._policy_cache[cache_key] = (time.time(), decision)
    
    # Decorators
    def require_permission(self, permission: Permission, resource_id: Optional[str] = None):
        """Decorator to require permission for function execution"""
        def decorator(f):
            @wraps(f)
            async def async_wrapper(*args, **kwargs):
                context = kwargs.get('context')
                if not context:
                    raise ValueError("Access context required")
                    
                if not self.check_permission(context, permission, resource_id):
                    raise PermissionError(f"Permission denied: {permission.value}")
                    
                return await f(*args, **kwargs)
                
            @wraps(f)
            def sync_wrapper(*args, **kwargs):
                context = kwargs.get('context')
                if not context:
                    raise ValueError("Access context required")
                    
                if not self.check_permission(context, permission, resource_id):
                    raise PermissionError(f"Permission denied: {permission.value}")
                    
                return f(*args, **kwargs)
                
            return async_wrapper if asyncio.iscoroutinefunction(f) else sync_wrapper
        return decorator
    
    # Export/Import
    def export_configuration(self) -> Dict[str, Any]:
        """Export RBAC configuration"""
        return {
            "roles": {role_id: asdict(role) for role_id, role in self.roles.items()},
            "policies": {policy_id: asdict(policy) for policy_id, policy in self.policies.items()},
            "user_roles": {user_id: list(roles) for user_id, roles in self.user_roles.items()}
        }
    
    def import_configuration(self, config: Dict[str, Any]):
        """Import RBAC configuration"""
        # Import roles
        for role_id, role_data in config.get("roles", {}).items():
            self.roles[role_id] = Role(**role_data)
            
        # Import policies
        for policy_id, policy_data in config.get("policies", {}).items():
            self.policies[policy_id] = Policy(**policy_data)
            
        # Import user roles
        for user_id, roles in config.get("user_roles", {}).items():
            self.user_roles[user_id] = set(roles)


# Example usage
if __name__ == "__main__":
    # Initialize RBAC manager
    rbac = RBACManager()
    
    # Create custom role
    ml_engineer_role = rbac.create_role(
        "ML Engineer",
        "Machine Learning Engineer with model training permissions",
        {Permission.AI_TRAIN, Permission.AI_PREDICT, Permission.AI_CONFIG,
         Permission.READ, Permission.WRITE}
    )
    print(f"Created role: {ml_engineer_role.name}")
    
    # Create user context
    context = AccessContext(
        user_id="user123",
        roles=["developer"],
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0"
    )
    
    # Assign role to user
    rbac.assign_role("user123", "developer", context)
    rbac.assign_role("user123", ml_engineer_role.id, context)
    
    # Create a resource
    ml_model = rbac.create_resource(
        ResourceType.MODEL,
        "sentiment-analyzer-v1",
        "user123",
        attributes={"type": "nlp", "framework": "pytorch"}
    )
    
    # Create a policy
    ml_policy = rbac.create_policy(
        "ML Model Access",
        "Policy for ML model access",
        "allow",
        ["ml_engineer"],  # Role-based
        [Permission.AI_TRAIN, Permission.AI_PREDICT],
        ["model/*"],  # All models
        conditions={
            "time_range": {
                "start": "09:00",
                "end": "18:00"
            }
        }
    )
    
    # Check permissions
    has_read = rbac.check_permission(context, Permission.READ)
    print(f"User has READ permission: {has_read}")
    
    has_ai_train = rbac.check_permission(context, Permission.AI_TRAIN, ml_model.id)
    print(f"User has AI_TRAIN permission on model: {has_ai_train}")
    
    # Generate audit report
    audit_events = rbac.get_audit_events({"user_id": "user123"})
    print(f"Found {len(audit_events)} audit events for user123")
    
    # Generate compliance report
    report = rbac.generate_compliance_report(
        ComplianceFramework.SOC2,
        datetime.now(timezone.utc) - timedelta(days=30),
        datetime.now(timezone.utc)
    )
    print(f"SOC2 Compliance Report: {report['requirements_met']}")
    
    # Export configuration
    config = rbac.export_configuration()
    print(f"Exported {len(config['roles'])} roles and {len(config['policies'])} policies")