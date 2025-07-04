"""
NEXUS Application Firewall
Comprehensive firewall with request filtering, anomaly detection, DDoS protection, and geo-blocking
"""

import re
import time
import json
import hmac
import hashlib
import ipaddress
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Tuple, Any, Union, Pattern
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict, deque
import logging
from functools import lru_cache
import asyncio
from urllib.parse import urlparse, parse_qs, unquote
import geoip2.database
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
import aiohttp
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat severity levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class AttackType(Enum):
    """Types of attacks"""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    XXE = "xxe"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    LDAP_INJECTION = "ldap_injection"
    CSRF = "csrf"
    DDOS = "ddos"
    BRUTE_FORCE = "brute_force"
    BOT = "bot"
    SCANNER = "scanner"
    MALICIOUS_FILE = "malicious_file"
    ANOMALY = "anomaly"


class Action(Enum):
    """Firewall actions"""
    ALLOW = "allow"
    BLOCK = "block"
    CHALLENGE = "challenge"
    LOG = "log"
    RATE_LIMIT = "rate_limit"


@dataclass
class FirewallRule:
    """Firewall rule definition"""
    id: str
    name: str
    description: str
    pattern: Optional[Pattern] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    action: Action = Action.BLOCK
    threat_level: ThreatLevel = ThreatLevel.MEDIUM
    attack_type: Optional[AttackType] = None
    priority: int = 0
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class GeoRule:
    """Geographic blocking rule"""
    id: str
    name: str
    action: Action
    countries: List[str] = field(default_factory=list)  # ISO country codes
    regions: List[str] = field(default_factory=list)
    cities: List[str] = field(default_factory=list)
    allow_list: bool = False  # If True, only allow these locations
    enabled: bool = True


@dataclass
class RateLimitRule:
    """Rate limiting rule"""
    id: str
    name: str
    path_pattern: str
    max_requests: int
    window_seconds: int
    burst_size: int = 0
    action: Action = Action.RATE_LIMIT
    by_ip: bool = True
    by_user: bool = False
    enabled: bool = True


@dataclass
class Request:
    """HTTP request representation"""
    method: str
    path: str
    headers: Dict[str, str]
    params: Dict[str, List[str]]
    body: Optional[str] = None
    ip_address: str = ""
    user_agent: str = ""
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ThreatInfo:
    """Information about detected threat"""
    attack_type: AttackType
    threat_level: ThreatLevel
    confidence: float
    rule_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    recommended_action: Action = Action.BLOCK


class ApplicationFirewall:
    """Production-grade application firewall"""
    
    def __init__(self, geoip_db_path: Optional[str] = None, ml_model_path: Optional[str] = None):
        self.rules: Dict[str, FirewallRule] = {}
        self.geo_rules: Dict[str, GeoRule] = {}
        self.rate_limit_rules: Dict[str, RateLimitRule] = {}
        
        # Attack pattern detection
        self.attack_patterns = self._init_attack_patterns()
        
        # Rate limiting state
        self.rate_limit_buckets: Dict[str, deque] = defaultdict(deque)
        
        # DDoS protection
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.blocked_ips: Set[str] = set()
        self.suspicious_ips: Dict[str, int] = defaultdict(int)
        
        # Anomaly detection
        self.ml_model = self._load_ml_model(ml_model_path)
        self.baseline_features: Dict[str, List[float]] = {}
        
        # GeoIP database
        self.geoip_reader = None
        if geoip_db_path:
            try:
                self.geoip_reader = geoip2.database.Reader(geoip_db_path)
            except Exception as e:
                logger.warning(f"Failed to load GeoIP database: {e}")
                
        # Initialize default rules
        self._init_default_rules()
        
        # Statistics
        self.stats = {
            "requests_analyzed": 0,
            "threats_detected": 0,
            "requests_blocked": 0,
            "attacks_by_type": defaultdict(int)
        }
        
    def _init_attack_patterns(self) -> Dict[AttackType, List[Pattern]]:
        """Initialize attack detection patterns"""
        return {
            AttackType.SQL_INJECTION: [
                re.compile(r"(\bunion\b.*\bselect\b|\bselect\b.*\bfrom\b|\binsert\b.*\binto\b)", re.IGNORECASE),
                re.compile(r"(--|\#|\/\*|\*\/|@@|@)", re.IGNORECASE),
                re.compile(r"(\bdrop\b|\bcreate\b|\balter\b)\s+(\btable\b|\bdatabase\b)", re.IGNORECASE),
                re.compile(r"(\bexec\b|\bexecute\b)\s*\(", re.IGNORECASE),
                re.compile(r"(\'|\")(\s*)(or|and)(\s*)(\'|\")?(\s*)=(\'|\")?(\s*)(\'|\")", re.IGNORECASE),
                re.compile(r"\b(sleep|benchmark|waitfor)\s*\(", re.IGNORECASE)
            ],
            AttackType.XSS: [
                re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
                re.compile(r"javascript\s*:", re.IGNORECASE),
                re.compile(r"on\w+\s*=", re.IGNORECASE),
                re.compile(r"<iframe[^>]*>", re.IGNORECASE),
                re.compile(r"<object[^>]*>", re.IGNORECASE),
                re.compile(r"<embed[^>]*>", re.IGNORECASE),
                re.compile(r"<img[^>]+src[\\s]*=[\\s]*[\"\'](javascript|data):", re.IGNORECASE)
            ],
            AttackType.COMMAND_INJECTION: [
                re.compile(r"[;&|]\s*(ls|cat|rm|mv|cp|wget|curl|nc|netcat)", re.IGNORECASE),
                re.compile(r"\$\(.*\)|\`.*\`"),
                re.compile(r"(system|exec|passthru|shell_exec|eval|assert)\s*\(", re.IGNORECASE),
                re.compile(r"\b(bash|sh|cmd|powershell)\b", re.IGNORECASE)
            ],
            AttackType.PATH_TRAVERSAL: [
                re.compile(r"\.\.\/|\.\.\\"),
                re.compile(r"(\/etc\/passwd|\/etc\/shadow|\/windows\/system32)"),
                re.compile(r"%2e%2e%2f|%252e%252e%252f", re.IGNORECASE),
                re.compile(r"\.\.%c0%af|\.\.%c1%9c", re.IGNORECASE)
            ],
            AttackType.XXE: [
                re.compile(r"<!ENTITY.*>", re.IGNORECASE),
                re.compile(r"SYSTEM\s+[\"']file:", re.IGNORECASE),
                re.compile(r"<!DOCTYPE[^>]*\[[^]]*\]>", re.IGNORECASE | re.DOTALL)
            ],
            AttackType.LDAP_INJECTION: [
                re.compile(r"\(\w*=\*\)|\(\w*=\w*\*\)", re.IGNORECASE),
                re.compile(r"[)(].*[)(]", re.IGNORECASE)
            ]
        }
        
    def _init_default_rules(self):
        """Initialize default security rules"""
        # SQL Injection rules
        self.add_rule(FirewallRule(
            id="sql_injection_basic",
            name="Basic SQL Injection",
            description="Detect basic SQL injection attempts",
            pattern=self.attack_patterns[AttackType.SQL_INJECTION][0],
            attack_type=AttackType.SQL_INJECTION,
            threat_level=ThreatLevel.HIGH,
            priority=100
        ))
        
        # XSS rules
        self.add_rule(FirewallRule(
            id="xss_script_tag",
            name="XSS Script Tag",
            description="Detect script tag injection",
            pattern=self.attack_patterns[AttackType.XSS][0],
            attack_type=AttackType.XSS,
            threat_level=ThreatLevel.HIGH,
            priority=100
        ))
        
        # Path traversal rules
        self.add_rule(FirewallRule(
            id="path_traversal_basic",
            name="Path Traversal",
            description="Detect path traversal attempts",
            pattern=self.attack_patterns[AttackType.PATH_TRAVERSAL][0],
            attack_type=AttackType.PATH_TRAVERSAL,
            threat_level=ThreatLevel.MEDIUM,
            priority=90
        ))
        
        # Command injection rules
        self.add_rule(FirewallRule(
            id="command_injection_basic",
            name="Command Injection",
            description="Detect command injection attempts",
            pattern=self.attack_patterns[AttackType.COMMAND_INJECTION][0],
            attack_type=AttackType.COMMAND_INJECTION,
            threat_level=ThreatLevel.CRITICAL,
            priority=110
        ))
        
        # Rate limiting rules
        self.add_rate_limit_rule(RateLimitRule(
            id="api_rate_limit",
            name="API Rate Limit",
            path_pattern="/api/*",
            max_requests=100,
            window_seconds=60,
            burst_size=20
        ))
        
        self.add_rate_limit_rule(RateLimitRule(
            id="auth_rate_limit",
            name="Authentication Rate Limit",
            path_pattern="/auth/*",
            max_requests=5,
            window_seconds=60,
            action=Action.BLOCK
        ))
        
    def _load_ml_model(self, model_path: Optional[str]) -> Optional[IsolationForest]:
        """Load ML model for anomaly detection"""
        if model_path:
            try:
                return joblib.load(model_path)
            except Exception as e:
                logger.warning(f"Failed to load ML model: {e}")
                
        # Create default model if none provided
        return IsolationForest(contamination=0.1, random_state=42)
    
    # Rule Management
    def add_rule(self, rule: FirewallRule):
        """Add firewall rule"""
        self.rules[rule.id] = rule
        logger.info(f"Added firewall rule: {rule.name}")
        
    def remove_rule(self, rule_id: str):
        """Remove firewall rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed firewall rule: {rule_id}")
            
    def add_geo_rule(self, rule: GeoRule):
        """Add geographic rule"""
        self.geo_rules[rule.id] = rule
        logger.info(f"Added geo rule: {rule.name}")
        
    def add_rate_limit_rule(self, rule: RateLimitRule):
        """Add rate limiting rule"""
        self.rate_limit_rules[rule.id] = rule
        logger.info(f"Added rate limit rule: {rule.name}")
    
    # Request Analysis
    async def analyze_request(self, request: Request) -> Tuple[Action, Optional[ThreatInfo]]:
        """Analyze request and determine action"""
        self.stats["requests_analyzed"] += 1
        
        # Check if IP is blocked
        if request.ip_address in self.blocked_ips:
            return Action.BLOCK, ThreatInfo(
                attack_type=AttackType.DDOS,
                threat_level=ThreatLevel.CRITICAL,
                confidence=1.0,
                details={"reason": "IP blocked"}
            )
        
        # Check geo-blocking rules
        geo_action = await self._check_geo_rules(request)
        if geo_action != Action.ALLOW:
            return geo_action, ThreatInfo(
                attack_type=AttackType.BOT,
                threat_level=ThreatLevel.MEDIUM,
                confidence=1.0,
                details={"reason": "Geographic restriction"}
            )
        
        # Check rate limiting
        rate_limit_action = self._check_rate_limits(request)
        if rate_limit_action != Action.ALLOW:
            return rate_limit_action, ThreatInfo(
                attack_type=AttackType.DDOS,
                threat_level=ThreatLevel.MEDIUM,
                confidence=0.8,
                details={"reason": "Rate limit exceeded"}
            )
        
        # Check for attacks
        threat_info = await self._detect_attacks(request)
        if threat_info:
            self.stats["threats_detected"] += 1
            self.stats["attacks_by_type"][threat_info.attack_type.value] += 1
            
            # Update suspicious IP tracking
            self.suspicious_ips[request.ip_address] += 1
            
            # Auto-block after multiple violations
            if self.suspicious_ips[request.ip_address] >= 10:
                self.blocked_ips.add(request.ip_address)
                logger.warning(f"Auto-blocked IP after multiple violations: {request.ip_address}")
                
            if threat_info.recommended_action == Action.BLOCK:
                self.stats["requests_blocked"] += 1
                
            return threat_info.recommended_action, threat_info
        
        # Anomaly detection
        if await self._is_anomalous(request):
            return Action.LOG, ThreatInfo(
                attack_type=AttackType.ANOMALY,
                threat_level=ThreatLevel.LOW,
                confidence=0.7,
                details={"reason": "Anomalous behavior detected"}
            )
        
        # Update request history for DDoS detection
        self._update_request_history(request)
        
        return Action.ALLOW, None
    
    async def _detect_attacks(self, request: Request) -> Optional[ThreatInfo]:
        """Detect various attack patterns"""
        # Combine all request data for analysis
        request_data = self._serialize_request(request)
        
        # Check each attack type
        for attack_type, patterns in self.attack_patterns.items():
            for pattern in patterns:
                if pattern.search(request_data):
                    # Match found, check specific rules
                    for rule in sorted(self.rules.values(), key=lambda r: r.priority, reverse=True):
                        if not rule.enabled:
                            continue
                            
                        if rule.attack_type == attack_type:
                            if rule.pattern and rule.pattern.search(request_data):
                                return ThreatInfo(
                                    attack_type=attack_type,
                                    threat_level=rule.threat_level,
                                    confidence=0.95,
                                    rule_id=rule.id,
                                    recommended_action=rule.action
                                )
                                
                    # No specific rule matched, use default
                    return ThreatInfo(
                        attack_type=attack_type,
                        threat_level=ThreatLevel.MEDIUM,
                        confidence=0.85,
                        recommended_action=Action.BLOCK
                    )
        
        # Check for bot/scanner patterns
        if self._is_bot_scanner(request):
            return ThreatInfo(
                attack_type=AttackType.SCANNER,
                threat_level=ThreatLevel.LOW,
                confidence=0.8,
                recommended_action=Action.CHALLENGE
            )
        
        return None
    
    def _serialize_request(self, request: Request) -> str:
        """Serialize request for pattern matching"""
        parts = [
            request.method,
            request.path,
            str(request.params),
            request.body or "",
            request.user_agent
        ]
        
        # Add relevant headers
        for header, value in request.headers.items():
            if header.lower() in ['referer', 'cookie', 'authorization']:
                parts.append(f"{header}: {value}")
                
        return " ".join(parts)
    
    def _is_bot_scanner(self, request: Request) -> bool:
        """Detect bot/scanner behavior"""
        suspicious_paths = [
            '/wp-admin', '/wp-login.php', '/admin', '/.env',
            '/config.php', '/phpmyadmin', '/.git', '/backup'
        ]
        
        # Check for suspicious paths
        if any(path in request.path.lower() for path in suspicious_paths):
            return True
            
        # Check user agent
        bot_patterns = [
            'bot', 'crawler', 'spider', 'scraper', 'scan',
            'nikto', 'sqlmap', 'havij', 'acunetix'
        ]
        
        if request.user_agent:
            ua_lower = request.user_agent.lower()
            if any(pattern in ua_lower for pattern in bot_patterns):
                return True
                
        return False
    
    # Rate Limiting
    def _check_rate_limits(self, request: Request) -> Action:
        """Check rate limiting rules"""
        for rule in self.rate_limit_rules.values():
            if not rule.enabled:
                continue
                
            # Check if path matches
            if not self._path_matches_pattern(request.path, rule.path_pattern):
                continue
                
            # Determine bucket key
            bucket_keys = []
            if rule.by_ip:
                bucket_keys.append(f"ip:{request.ip_address}")
            if rule.by_user and request.user_id:
                bucket_keys.append(f"user:{request.user_id}")
                
            for bucket_key in bucket_keys:
                bucket = self.rate_limit_buckets[bucket_key]
                
                # Remove old entries
                cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=rule.window_seconds)
                while bucket and bucket[0] < cutoff_time:
                    bucket.popleft()
                    
                # Check limit
                if len(bucket) >= rule.max_requests:
                    return rule.action
                    
                # Add current request
                bucket.append(datetime.now(timezone.utc))
                
        return Action.ALLOW
    
    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches pattern with wildcards"""
        # Convert pattern to regex
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        regex_pattern = f"^{regex_pattern}$"
        
        return bool(re.match(regex_pattern, path))
    
    # Geographic Blocking
    async def _check_geo_rules(self, request: Request) -> Action:
        """Check geographic blocking rules"""
        if not self.geoip_reader:
            return Action.ALLOW
            
        try:
            response = self.geoip_reader.city(request.ip_address)
            country = response.country.iso_code
            region = response.subdivisions.most_specific.iso_code if response.subdivisions else None
            city = response.city.name
            
            for rule in self.geo_rules.values():
                if not rule.enabled:
                    continue
                    
                matched = False
                
                # Check country
                if rule.countries and country in rule.countries:
                    matched = True
                    
                # Check region
                if rule.regions and region and region in rule.regions:
                    matched = True
                    
                # Check city
                if rule.cities and city and city in rule.cities:
                    matched = True
                    
                # Apply rule based on allow_list flag
                if rule.allow_list:
                    # Allow list: block if NOT matched
                    if not matched:
                        return rule.action
                else:
                    # Block list: block if matched
                    if matched:
                        return rule.action
                        
        except Exception as e:
            logger.debug(f"GeoIP lookup failed for {request.ip_address}: {e}")
            
        return Action.ALLOW
    
    # DDoS Protection
    def _update_request_history(self, request: Request):
        """Update request history for DDoS detection"""
        self.request_history[request.ip_address].append(request.timestamp)
        
        # Check for DDoS patterns
        if self._detect_ddos(request.ip_address):
            self.blocked_ips.add(request.ip_address)
            logger.warning(f"DDoS detected from IP: {request.ip_address}")
            
    def _detect_ddos(self, ip_address: str) -> bool:
        """Detect DDoS attack patterns"""
        history = self.request_history[ip_address]
        
        if len(history) < 100:
            return False
            
        # Calculate request rate
        time_span = (history[-1] - history[0]).total_seconds()
        if time_span > 0:
            rate = len(history) / time_span
            
            # Threshold: more than 10 requests per second sustained
            if rate > 10:
                return True
                
        # Check for request bursts
        burst_window = 5  # seconds
        burst_threshold = 50  # requests
        
        for i in range(len(history) - burst_threshold):
            if (history[i + burst_threshold - 1] - history[i]).total_seconds() < burst_window:
                return True
                
        return False
    
    # Anomaly Detection
    async def _is_anomalous(self, request: Request) -> bool:
        """Detect anomalous requests using ML"""
        if not self.ml_model:
            return False
            
        try:
            # Extract features
            features = self._extract_features(request)
            
            # Predict
            prediction = self.ml_model.predict([features])[0]
            
            # -1 indicates anomaly in IsolationForest
            return prediction == -1
            
        except Exception as e:
            logger.debug(f"Anomaly detection failed: {e}")
            return False
            
    def _extract_features(self, request: Request) -> List[float]:
        """Extract numerical features from request"""
        features = []
        
        # Request characteristics
        features.append(len(request.path))
        features.append(len(str(request.params)))
        features.append(len(request.body) if request.body else 0)
        features.append(len(request.headers))
        features.append(len(request.user_agent))
        
        # Time-based features
        hour = request.timestamp.hour
        day_of_week = request.timestamp.weekday()
        features.append(hour)
        features.append(day_of_week)
        
        # Method encoding
        method_map = {'GET': 0, 'POST': 1, 'PUT': 2, 'DELETE': 3, 'HEAD': 4, 'OPTIONS': 5}
        features.append(method_map.get(request.method, 6))
        
        # Path depth
        features.append(request.path.count('/'))
        
        # Query parameter count
        features.append(sum(len(v) for v in request.params.values()))
        
        return features
    
    # Webhook Signature Verification
    def verify_webhook_signature(self, payload: bytes, signature: str, 
                                secret: str, algorithm: str = 'sha256') -> bool:
        """Verify webhook signature"""
        try:
            # Calculate expected signature
            if algorithm == 'sha256':
                expected = hmac.new(
                    secret.encode(),
                    payload,
                    hashlib.sha256
                ).hexdigest()
            elif algorithm == 'sha1':
                expected = hmac.new(
                    secret.encode(),
                    payload,
                    hashlib.sha1
                ).hexdigest()
            else:
                logger.warning(f"Unsupported signature algorithm: {algorithm}")
                return False
                
            # Compare signatures
            return hmac.compare_digest(signature, expected)
            
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return False
    
    # Security Headers Validation
    def get_required_headers(self) -> Dict[str, str]:
        """Get required security headers"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
    
    # Statistics and Monitoring
    def get_statistics(self) -> Dict[str, Any]:
        """Get firewall statistics"""
        return {
            **self.stats,
            "blocked_ips": len(self.blocked_ips),
            "suspicious_ips": len(self.suspicious_ips),
            "active_rules": sum(1 for r in self.rules.values() if r.enabled),
            "active_geo_rules": sum(1 for r in self.geo_rules.values() if r.enabled),
            "active_rate_limits": sum(1 for r in self.rate_limit_rules.values() if r.enabled)
        }
    
    def reset_statistics(self):
        """Reset statistics"""
        self.stats = {
            "requests_analyzed": 0,
            "threats_detected": 0,
            "requests_blocked": 0,
            "attacks_by_type": defaultdict(int)
        }
        
    # Threat Intelligence Integration
    async def check_threat_intelligence(self, ip_address: str) -> Optional[ThreatInfo]:
        """Check IP against threat intelligence feeds"""
        # This would integrate with services like:
        # - AbuseIPDB
        # - Shodan
        # - VirusTotal
        # - Custom threat feeds
        
        # Placeholder implementation
        known_bad_ips = {'192.168.1.100', '10.0.0.1'}  # Example
        
        if ip_address in known_bad_ips:
            return ThreatInfo(
                attack_type=AttackType.BOT,
                threat_level=ThreatLevel.HIGH,
                confidence=1.0,
                details={"source": "threat_intelligence"}
            )
            
        return None
    
    # Export/Import Configuration
    def export_rules(self) -> Dict[str, Any]:
        """Export firewall rules"""
        return {
            "firewall_rules": [
                {
                    "id": rule.id,
                    "name": rule.name,
                    "description": rule.description,
                    "pattern": rule.pattern.pattern if rule.pattern else None,
                    "conditions": rule.conditions,
                    "action": rule.action.value,
                    "threat_level": rule.threat_level.value,
                    "attack_type": rule.attack_type.value if rule.attack_type else None,
                    "priority": rule.priority,
                    "enabled": rule.enabled
                }
                for rule in self.rules.values()
            ],
            "geo_rules": [
                {
                    "id": rule.id,
                    "name": rule.name,
                    "action": rule.action.value,
                    "countries": rule.countries,
                    "regions": rule.regions,
                    "cities": rule.cities,
                    "allow_list": rule.allow_list,
                    "enabled": rule.enabled
                }
                for rule in self.geo_rules.values()
            ],
            "rate_limit_rules": [
                {
                    "id": rule.id,
                    "name": rule.name,
                    "path_pattern": rule.path_pattern,
                    "max_requests": rule.max_requests,
                    "window_seconds": rule.window_seconds,
                    "burst_size": rule.burst_size,
                    "action": rule.action.value,
                    "by_ip": rule.by_ip,
                    "by_user": rule.by_user,
                    "enabled": rule.enabled
                }
                for rule in self.rate_limit_rules.values()
            ]
        }


# Example usage
if __name__ == "__main__":
    # Initialize firewall
    firewall = ApplicationFirewall()
    
    # Add custom rule
    firewall.add_rule(FirewallRule(
        id="custom_api_protection",
        name="API Endpoint Protection",
        description="Protect sensitive API endpoints",
        pattern=re.compile(r"/api/v1/admin/.*"),
        conditions={"require_auth": True},
        action=Action.BLOCK,
        threat_level=ThreatLevel.HIGH,
        priority=200
    ))
    
    # Add geo-blocking rule
    firewall.add_geo_rule(GeoRule(
        id="block_countries",
        name="Block High-Risk Countries",
        action=Action.BLOCK,
        countries=["XX", "YY"],  # Example country codes
        allow_list=False
    ))
    
    # Test request analysis
    async def test_firewall():
        # Normal request
        normal_request = Request(
            method="GET",
            path="/api/v1/users",
            headers={"User-Agent": "Mozilla/5.0"},
            params={},
            ip_address="1.2.3.4"
        )
        
        action, threat = await firewall.analyze_request(normal_request)
        print(f"Normal request: {action.value}")
        
        # SQL injection attempt
        sql_request = Request(
            method="GET",
            path="/api/v1/users",
            headers={"User-Agent": "Mozilla/5.0"},
            params={"id": ["1' OR '1'='1"]},
            ip_address="1.2.3.5"
        )
        
        action, threat = await firewall.analyze_request(sql_request)
        print(f"SQL injection: {action.value}, threat: {threat.attack_type.value if threat else 'None'}")
        
        # XSS attempt
        xss_request = Request(
            method="POST",
            path="/api/v1/comment",
            headers={"User-Agent": "Mozilla/5.0"},
            params={},
            body="<script>alert('xss')</script>",
            ip_address="1.2.3.6"
        )
        
        action, threat = await firewall.analyze_request(xss_request)
        print(f"XSS attempt: {action.value}, threat: {threat.attack_type.value if threat else 'None'}")
        
        # Get statistics
        stats = firewall.get_statistics()
        print(f"Firewall stats: {stats}")
        
    # Run test
    asyncio.run(test_firewall())
    
    # Export rules
    exported = firewall.export_rules()
    print(f"Exported {len(exported['firewall_rules'])} firewall rules")