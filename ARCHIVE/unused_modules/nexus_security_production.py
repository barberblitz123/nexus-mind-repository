"""
NEXUS Production Security Module
Comprehensive security layer with JWT auth, OAuth2, rate limiting, and protection mechanisms
"""

import jwt
import secrets
import hashlib
import time
import re
import html
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any, Union
from functools import wraps
from contextlib import contextmanager
import redis
import bleach
from sqlalchemy import text
from sqlalchemy.sql import operators
import bcrypt
from urllib.parse import urlparse, parse_qs
import logging
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict
import ipaddress

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthProvider(Enum):
    """Supported OAuth2 providers"""
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"
    LOCAL = "local"


@dataclass
class SecurityConfig:
    """Security configuration"""
    jwt_secret: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    jwt_algorithm: str = "HS256"
    access_token_expire: int = 3600  # 1 hour
    refresh_token_expire: int = 604800  # 7 days
    
    # Rate limiting
    rate_limit_window: int = 60  # seconds
    rate_limit_max_requests: int = 100
    rate_limit_burst: int = 20
    
    # Password policy
    min_password_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special: bool = True
    
    # Session config
    session_timeout: int = 1800  # 30 minutes
    max_sessions_per_user: int = 5
    
    # Security headers
    enable_hsts: bool = True
    enable_csp: bool = True
    enable_cors: bool = True
    allowed_origins: List[str] = field(default_factory=list)
    
    # OAuth2 providers
    oauth_providers: Dict[str, Dict[str, str]] = field(default_factory=dict)


@dataclass
class User:
    """User model with security attributes"""
    id: str
    email: str
    username: str
    password_hash: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    api_keys: List[Dict[str, Any]] = field(default_factory=list)
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Session:
    """User session"""
    id: str
    user_id: str
    token: str
    refresh_token: str
    ip_address: str
    user_agent: str
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    is_active: bool = True


@dataclass
class ApiKey:
    """API key with scopes"""
    id: str
    key: str
    name: str
    user_id: str
    scopes: List[str]
    rate_limit: Optional[int] = None
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True


class SecurityManager:
    """Core security manager for NEXUS"""
    
    def __init__(self, config: SecurityConfig, redis_client: Optional[redis.Redis] = None):
        self.config = config
        self.redis = redis_client or redis.Redis(decode_responses=True)
        self.sessions: Dict[str, Session] = {}
        self.users: Dict[str, User] = {}
        self.api_keys: Dict[str, ApiKey] = {}
        self.csrf_tokens: Dict[str, str] = {}
        
        # Initialize OAuth2 providers
        self.oauth_providers = self._init_oauth_providers()
        
        # Compile regex patterns for validation
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.sql_injection_pattern = re.compile(
            r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|script|javascript|eval)\b)',
            re.IGNORECASE
        )
        self.xss_pattern = re.compile(r'<script.*?>.*?</script>', re.IGNORECASE | re.DOTALL)
        
    def _init_oauth_providers(self) -> Dict[str, Dict[str, str]]:
        """Initialize OAuth2 provider configurations"""
        providers = {}
        
        if AuthProvider.GOOGLE.value in self.config.oauth_providers:
            providers[AuthProvider.GOOGLE.value] = {
                'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
                'token_url': 'https://oauth2.googleapis.com/token',
                'userinfo_url': 'https://openidconnect.googleapis.com/v1/userinfo',
                **self.config.oauth_providers[AuthProvider.GOOGLE.value]
            }
            
        if AuthProvider.GITHUB.value in self.config.oauth_providers:
            providers[AuthProvider.GITHUB.value] = {
                'auth_url': 'https://github.com/login/oauth/authorize',
                'token_url': 'https://github.com/login/oauth/access_token',
                'userinfo_url': 'https://api.github.com/user',
                **self.config.oauth_providers[AuthProvider.GITHUB.value]
            }
            
        if AuthProvider.MICROSOFT.value in self.config.oauth_providers:
            providers[AuthProvider.MICROSOFT.value] = {
                'auth_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
                'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
                'userinfo_url': 'https://graph.microsoft.com/v1.0/me',
                **self.config.oauth_providers[AuthProvider.MICROSOFT.value]
            }
            
        return providers
    
    # JWT Token Management
    def generate_tokens(self, user: User) -> Tuple[str, str]:
        """Generate access and refresh tokens"""
        now = datetime.now(timezone.utc)
        
        # Access token payload
        access_payload = {
            'user_id': user.id,
            'email': user.email,
            'username': user.username,
            'roles': user.roles,
            'permissions': user.permissions,
            'exp': now + timedelta(seconds=self.config.access_token_expire),
            'iat': now,
            'type': 'access'
        }
        
        # Refresh token payload
        refresh_payload = {
            'user_id': user.id,
            'exp': now + timedelta(seconds=self.config.refresh_token_expire),
            'iat': now,
            'type': 'refresh'
        }
        
        access_token = jwt.encode(access_payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)
        refresh_token = jwt.encode(refresh_payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)
        
        return access_token, refresh_token
    
    def verify_token(self, token: str, token_type: str = 'access') -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.config.jwt_secret, algorithms=[self.config.jwt_algorithm])
            
            if payload.get('type') != token_type:
                logger.warning(f"Invalid token type: expected {token_type}, got {payload.get('type')}")
                return None
                
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.info("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token using refresh token"""
        payload = self.verify_token(refresh_token, token_type='refresh')
        if not payload:
            return None
            
        user = self.users.get(payload['user_id'])
        if not user:
            return None
            
        access_token, _ = self.generate_tokens(user)
        return access_token
    
    # Authentication
    def authenticate(self, username: str, password: str, ip_address: str) -> Optional[Tuple[User, str, str]]:
        """Authenticate user with username/password"""
        user = self._get_user_by_username(username)
        if not user:
            logger.warning(f"Authentication failed: user not found - {username}")
            return None
            
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            logger.warning(f"Authentication failed: account locked - {username}")
            return None
            
        # Verify password
        if not self._verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
                logger.warning(f"Account locked due to failed attempts: {username}")
                
            return None
            
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.last_login = datetime.now(timezone.utc)
        
        # Generate tokens
        access_token, refresh_token = self.generate_tokens(user)
        
        # Create session
        session = self._create_session(user, access_token, refresh_token, ip_address)
        
        return user, access_token, refresh_token
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password against policy"""
        errors = []
        
        if len(password) < self.config.min_password_length:
            errors.append(f"Password must be at least {self.config.min_password_length} characters")
            
        if self.config.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
            
        if self.config.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
            
        if self.config.require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
            
        if self.config.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
            
        return len(errors) == 0, errors
    
    # OAuth2 Integration
    def get_oauth_auth_url(self, provider: str, state: str, redirect_uri: str) -> Optional[str]:
        """Get OAuth2 authorization URL"""
        if provider not in self.oauth_providers:
            return None
            
        config = self.oauth_providers[provider]
        params = {
            'client_id': config['client_id'],
            'redirect_uri': redirect_uri,
            'state': state,
            'response_type': 'code',
            'scope': config.get('scope', 'openid email profile')
        }
        
        if provider == AuthProvider.GOOGLE.value:
            params['access_type'] = 'offline'
            params['prompt'] = 'consent'
            
        query_string = '&'.join(f"{k}={v}" for k, v in params.items())
        return f"{config['auth_url']}?{query_string}"
    
    async def exchange_oauth_code(self, provider: str, code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
        """Exchange OAuth2 authorization code for tokens"""
        if provider not in self.oauth_providers:
            return None
            
        config = self.oauth_providers[provider]
        
        # Exchange code for tokens
        # This would make an HTTP request to the token endpoint
        # For now, returning a placeholder
        return {
            'access_token': 'oauth_access_token',
            'refresh_token': 'oauth_refresh_token',
            'expires_in': 3600
        }
    
    # API Key Management
    def generate_api_key(self, user: User, name: str, scopes: List[str], 
                        rate_limit: Optional[int] = None, 
                        expires_in_days: Optional[int] = None) -> ApiKey:
        """Generate new API key for user"""
        key = f"nxs_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
            
        api_key = ApiKey(
            id=secrets.token_urlsafe(16),
            key=key_hash,  # Store hash, return actual key only once
            name=name,
            user_id=user.id,
            scopes=scopes,
            rate_limit=rate_limit,
            expires_at=expires_at
        )
        
        self.api_keys[key_hash] = api_key
        user.api_keys.append({
            'id': api_key.id,
            'name': name,
            'key_prefix': key[:10],
            'scopes': scopes,
            'created_at': api_key.created_at.isoformat()
        })
        
        return api_key
    
    def verify_api_key(self, key: str) -> Optional[Tuple[User, ApiKey]]:
        """Verify API key and return associated user"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        api_key = self.api_keys.get(key_hash)
        
        if not api_key or not api_key.is_active:
            return None
            
        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            api_key.is_active = False
            return None
            
        user = self.users.get(api_key.user_id)
        if not user:
            return None
            
        api_key.last_used = datetime.now(timezone.utc)
        return user, api_key
    
    # Rate Limiting
    def check_rate_limit(self, identifier: str, limit: Optional[int] = None, 
                        window: Optional[int] = None) -> Tuple[bool, Dict[str, int]]:
        """Check rate limit for identifier (user_id, IP, API key)"""
        limit = limit or self.config.rate_limit_max_requests
        window = window or self.config.rate_limit_window
        
        key = f"rate_limit:{identifier}"
        current_time = int(time.time())
        window_start = current_time - window
        
        # Clean old entries
        self.redis.zremrangebyscore(key, 0, window_start)
        
        # Count requests in window
        request_count = self.redis.zcard(key)
        
        if request_count >= limit:
            # Calculate when the oldest request will expire
            oldest_request = self.redis.zrange(key, 0, 0, withscores=True)
            if oldest_request:
                reset_time = int(oldest_request[0][1]) + window
            else:
                reset_time = current_time + window
                
            return False, {
                'limit': limit,
                'remaining': 0,
                'reset': reset_time
            }
        
        # Add current request
        self.redis.zadd(key, {str(current_time): current_time})
        self.redis.expire(key, window)
        
        return True, {
            'limit': limit,
            'remaining': limit - request_count - 1,
            'reset': current_time + window
        }
    
    # Input Sanitization
    def sanitize_input(self, input_data: Any, input_type: str = 'text') -> Any:
        """Sanitize user input based on type"""
        if input_data is None:
            return None
            
        if isinstance(input_data, dict):
            return {k: self.sanitize_input(v, input_type) for k, v in input_data.items()}
            
        if isinstance(input_data, list):
            return [self.sanitize_input(item, input_type) for item in input_data]
            
        if not isinstance(input_data, str):
            return input_data
            
        # Basic sanitization
        sanitized = input_data.strip()
        
        if input_type == 'html':
            # Use bleach for HTML sanitization
            sanitized = bleach.clean(
                sanitized,
                tags=['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li'],
                attributes={'a': ['href', 'title']},
                strip=True
            )
        elif input_type == 'sql':
            # Check for SQL injection patterns
            if self.sql_injection_pattern.search(sanitized):
                logger.warning(f"Potential SQL injection detected: {sanitized[:50]}...")
                raise ValueError("Invalid input detected")
                
            # Escape single quotes
            sanitized = sanitized.replace("'", "''")
            
        elif input_type == 'filename':
            # Remove potentially dangerous characters from filenames
            sanitized = re.sub(r'[^\w\s.-]', '', sanitized)
            sanitized = re.sub(r'\.{2,}', '.', sanitized)  # Prevent directory traversal
            
        elif input_type == 'email':
            # Validate email format
            if not self.email_pattern.match(sanitized):
                raise ValueError("Invalid email format")
                
        else:  # Default text sanitization
            # HTML escape
            sanitized = html.escape(sanitized)
            
        return sanitized
    
    # XSS Protection
    def prevent_xss(self, content: str) -> str:
        """Remove potential XSS attacks from content"""
        # Remove script tags
        content = self.xss_pattern.sub('', content)
        
        # Remove event handlers
        content = re.sub(r'\s*on\w+\s*=\s*["\'].*?["\']', '', content, flags=re.IGNORECASE)
        
        # Remove javascript: protocol
        content = re.sub(r'javascript:', '', content, flags=re.IGNORECASE)
        
        # HTML encode
        return html.escape(content)
    
    # CSRF Protection
    def generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token for session"""
        token = secrets.token_urlsafe(32)
        self.csrf_tokens[session_id] = token
        
        # Store in Redis with expiration
        self.redis.setex(f"csrf:{session_id}", self.config.session_timeout, token)
        
        return token
    
    def verify_csrf_token(self, session_id: str, token: str) -> bool:
        """Verify CSRF token"""
        stored_token = self.redis.get(f"csrf:{session_id}")
        return stored_token == token
    
    # Session Management
    def _create_session(self, user: User, access_token: str, refresh_token: str, 
                       ip_address: str, user_agent: str = '') -> Session:
        """Create new user session"""
        # Check max sessions
        user_sessions = [s for s in self.sessions.values() if s.user_id == user.id and s.is_active]
        if len(user_sessions) >= self.config.max_sessions_per_user:
            # Invalidate oldest session
            oldest_session = min(user_sessions, key=lambda s: s.created_at)
            self.invalidate_session(oldest_session.id)
            
        session = Session(
            id=secrets.token_urlsafe(16),
            user_id=user.id,
            token=access_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=self.config.session_timeout),
            last_activity=datetime.now(timezone.utc)
        )
        
        self.sessions[session.id] = session
        
        # Store in Redis
        self.redis.setex(
            f"session:{session.id}",
            self.config.session_timeout,
            json.dumps({
                'user_id': user.id,
                'ip_address': ip_address,
                'created_at': session.created_at.isoformat()
            })
        )
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get active session"""
        session = self.sessions.get(session_id)
        
        if not session or not session.is_active:
            return None
            
        if session.expires_at < datetime.now(timezone.utc):
            self.invalidate_session(session_id)
            return None
            
        # Update last activity
        session.last_activity = datetime.now(timezone.utc)
        
        return session
    
    def invalidate_session(self, session_id: str):
        """Invalidate session"""
        if session_id in self.sessions:
            self.sessions[session_id].is_active = False
            
        self.redis.delete(f"session:{session_id}")
        self.redis.delete(f"csrf:{session_id}")
        
        if session_id in self.csrf_tokens:
            del self.csrf_tokens[session_id]
    
    # Security Headers
    def get_security_headers(self, request_origin: Optional[str] = None) -> Dict[str, str]:
        """Get security headers for response"""
        headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
        }
        
        if self.config.enable_hsts:
            headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
            
        if self.config.enable_csp:
            headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' wss: https:;"
            )
            
        if self.config.enable_cors and request_origin:
            if request_origin in self.config.allowed_origins or '*' in self.config.allowed_origins:
                headers['Access-Control-Allow-Origin'] = request_origin
                headers['Access-Control-Allow-Credentials'] = 'true'
                headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRF-Token'
                headers['Access-Control-Max-Age'] = '86400'
                
        return headers
    
    # Helper methods
    def _get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username or email"""
        for user in self.users.values():
            if user.username == username or user.email == username:
                return user
        return None
    
    # Decorators for Flask/FastAPI
    def require_auth(self, scopes: Optional[List[str]] = None):
        """Decorator to require authentication"""
        def decorator(f):
            @wraps(f)
            async def async_wrapper(*args, **kwargs):
                # Extract token from request (implementation depends on framework)
                token = kwargs.get('token')  # Placeholder
                
                payload = self.verify_token(token)
                if not payload:
                    raise ValueError("Invalid or expired token")
                    
                if scopes:
                    user_permissions = set(payload.get('permissions', []))
                    if not any(scope in user_permissions for scope in scopes):
                        raise ValueError("Insufficient permissions")
                        
                kwargs['current_user'] = payload
                return await f(*args, **kwargs)
                
            @wraps(f)
            def sync_wrapper(*args, **kwargs):
                # Sync version for non-async functions
                token = kwargs.get('token')  # Placeholder
                
                payload = self.verify_token(token)
                if not payload:
                    raise ValueError("Invalid or expired token")
                    
                if scopes:
                    user_permissions = set(payload.get('permissions', []))
                    if not any(scope in user_permissions for scope in scopes):
                        raise ValueError("Insufficient permissions")
                        
                kwargs['current_user'] = payload
                return f(*args, **kwargs)
                
            return async_wrapper if asyncio.iscoroutinefunction(f) else sync_wrapper
        return decorator
    
    def rate_limit(self, max_requests: Optional[int] = None, window: Optional[int] = None):
        """Decorator for rate limiting"""
        def decorator(f):
            @wraps(f)
            async def async_wrapper(*args, **kwargs):
                # Extract identifier from request
                identifier = kwargs.get('user_id', 'anonymous')  # Placeholder
                
                allowed, info = self.check_rate_limit(identifier, max_requests, window)
                if not allowed:
                    raise ValueError(f"Rate limit exceeded. Retry after {info['reset']}")
                    
                # Add rate limit headers to response
                kwargs['rate_limit_info'] = info
                return await f(*args, **kwargs)
                
            @wraps(f)
            def sync_wrapper(*args, **kwargs):
                identifier = kwargs.get('user_id', 'anonymous')  # Placeholder
                
                allowed, info = self.check_rate_limit(identifier, max_requests, window)
                if not allowed:
                    raise ValueError(f"Rate limit exceeded. Retry after {info['reset']}")
                    
                kwargs['rate_limit_info'] = info
                return f(*args, **kwargs)
                
            return async_wrapper if asyncio.iscoroutinefunction(f) else sync_wrapper
        return decorator


# Example usage
if __name__ == "__main__":
    # Initialize security configuration
    config = SecurityConfig(
        jwt_secret="your-secret-key-here",
        allowed_origins=["https://nexus.example.com", "http://localhost:3000"],
        oauth_providers={
            "google": {
                "client_id": "your-google-client-id",
                "client_secret": "your-google-client-secret",
                "scope": "openid email profile"
            },
            "github": {
                "client_id": "your-github-client-id",
                "client_secret": "your-github-client-secret",
                "scope": "read:user user:email"
            }
        }
    )
    
    # Create security manager
    security = SecurityManager(config)
    
    # Example: Create a user
    test_user = User(
        id="user123",
        email="test@example.com",
        username="testuser",
        password_hash=security.hash_password("SecurePassword123!"),
        roles=["user", "developer"],
        permissions=["read", "write", "deploy"]
    )
    
    security.users[test_user.id] = test_user
    
    # Example: Authenticate user
    auth_result = security.authenticate("testuser", "SecurePassword123!", "192.168.1.1")
    if auth_result:
        user, access_token, refresh_token = auth_result
        print(f"Authentication successful for {user.username}")
        print(f"Access token: {access_token[:20]}...")
        
    # Example: Generate API key
    api_key = security.generate_api_key(
        test_user,
        "Development Key",
        ["read", "write"],
        rate_limit=1000,
        expires_in_days=90
    )
    print(f"Generated API key: nxs_{'*' * 32}")
    
    # Example: Check rate limit
    allowed, info = security.check_rate_limit("user123")
    print(f"Rate limit check: allowed={allowed}, remaining={info['remaining']}")
    
    # Example: Sanitize input
    safe_input = security.sanitize_input("<script>alert('xss')</script>Hello", "html")
    print(f"Sanitized input: {safe_input}")
    
    # Example: Get security headers
    headers = security.get_security_headers("https://nexus.example.com")
    print("Security headers:", headers)