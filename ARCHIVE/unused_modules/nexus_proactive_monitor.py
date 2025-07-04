#!/usr/bin/env python3
"""
NEXUS Proactive Monitoring System
================================
Real-time monitoring with automatic issue detection and suggestion engine.
"""

import asyncio
import aiohttp
import json
import logging
import os
import psutil
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from pathlib import Path
import subprocess
import re
import yaml
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from sklearn.ensemble import IsolationForest
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MonitoringEvent:
    """Represents a monitoring event"""
    timestamp: datetime
    source: str
    event_type: str
    severity: str  # info, warning, error, critical
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class SystemMetrics:
    """System resource metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    process_count: int
    open_files: int


@dataclass
class DependencyInfo:
    """Dependency information"""
    name: str
    current_version: str
    latest_version: str
    has_security_update: bool
    vulnerabilities: List[str] = field(default_factory=list)


class GitHubMonitor:
    """Monitors GitHub repositories for issues, PRs, and commits"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {self.token}' if self.token else ''
        }
        self.monitored_repos: Set[str] = set()
        self.last_check: Dict[str, datetime] = {}
        
    async def add_repository(self, repo: str):
        """Add a repository to monitor"""
        self.monitored_repos.add(repo)
        self.last_check[repo] = datetime.now()
        
    async def check_issues(self, repo: str) -> List[MonitoringEvent]:
        """Check for new issues"""
        events = []
        url = f"{self.base_url}/repos/{repo}/issues"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        issues = await response.json()
                        
                        for issue in issues[:10]:  # Check last 10 issues
                            created_at = datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00'))
                            
                            if created_at > self.last_check.get(repo, datetime.min):
                                event = MonitoringEvent(
                                    timestamp=datetime.now(),
                                    source=f"github:{repo}",
                                    event_type="new_issue",
                                    severity="warning" if 'bug' in str(issue.get('labels', [])).lower() else "info",
                                    message=f"New issue: {issue['title']}",
                                    data={
                                        'issue_number': issue['number'],
                                        'author': issue['user']['login'],
                                        'labels': [l['name'] for l in issue.get('labels', [])],
                                        'url': issue['html_url']
                                    },
                                    suggestions=self._generate_issue_suggestions(issue)
                                )
                                events.append(event)
                                
        except Exception as e:
            logger.error(f"Error checking GitHub issues: {e}")
            
        return events
    
    async def check_pull_requests(self, repo: str) -> List[MonitoringEvent]:
        """Check for new pull requests"""
        events = []
        url = f"{self.base_url}/repos/{repo}/pulls"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        prs = await response.json()
                        
                        for pr in prs[:10]:
                            created_at = datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00'))
                            
                            if created_at > self.last_check.get(repo, datetime.min):
                                event = MonitoringEvent(
                                    timestamp=datetime.now(),
                                    source=f"github:{repo}",
                                    event_type="new_pr",
                                    severity="info",
                                    message=f"New PR: {pr['title']}",
                                    data={
                                        'pr_number': pr['number'],
                                        'author': pr['user']['login'],
                                        'base': pr['base']['ref'],
                                        'head': pr['head']['ref'],
                                        'url': pr['html_url']
                                    },
                                    suggestions=self._generate_pr_suggestions(pr)
                                )
                                events.append(event)
                                
        except Exception as e:
            logger.error(f"Error checking GitHub PRs: {e}")
            
        return events
    
    async def check_commits(self, repo: str) -> List[MonitoringEvent]:
        """Check for new commits"""
        events = []
        url = f"{self.base_url}/repos/{repo}/commits"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        commits = await response.json()
                        
                        for commit in commits[:5]:
                            commit_date = datetime.fromisoformat(
                                commit['commit']['author']['date'].replace('Z', '+00:00')
                            )
                            
                            if commit_date > self.last_check.get(repo, datetime.min):
                                # Analyze commit for potential issues
                                issues = self._analyze_commit(commit)
                                
                                if issues:
                                    event = MonitoringEvent(
                                        timestamp=datetime.now(),
                                        source=f"github:{repo}",
                                        event_type="problematic_commit",
                                        severity="warning",
                                        message=f"Potential issues in commit: {commit['sha'][:7]}",
                                        data={
                                            'sha': commit['sha'],
                                            'author': commit['commit']['author']['name'],
                                            'message': commit['commit']['message'],
                                            'issues': issues
                                        },
                                        suggestions=self._generate_commit_suggestions(commit, issues)
                                    )
                                    events.append(event)
                                    
        except Exception as e:
            logger.error(f"Error checking GitHub commits: {e}")
            
        return events
    
    def _generate_issue_suggestions(self, issue: Dict) -> List[str]:
        """Generate suggestions for an issue"""
        suggestions = []
        
        # Check for missing labels
        if not issue.get('labels'):
            suggestions.append("Add appropriate labels to categorize this issue")
            
        # Check for bug reports without reproduction steps
        if 'bug' in str(issue.get('labels', [])).lower():
            body = issue.get('body', '').lower()
            if 'steps to reproduce' not in body and 'reproduction' not in body:
                suggestions.append("Request reproduction steps from the reporter")
                
        # Check for feature requests
        if 'enhancement' in str(issue.get('labels', [])).lower():
            suggestions.append("Consider creating a design document before implementation")
            
        return suggestions
    
    def _generate_pr_suggestions(self, pr: Dict) -> List[str]:
        """Generate suggestions for a pull request"""
        suggestions = []
        
        # Check PR size
        if pr.get('additions', 0) + pr.get('deletions', 0) > 500:
            suggestions.append("Large PR detected - consider breaking into smaller PRs")
            
        # Check for missing description
        if len(pr.get('body', '')) < 50:
            suggestions.append("PR description is too brief - add more context")
            
        # Check for tests
        if 'test' not in pr.get('title', '').lower() and 'test' not in pr.get('body', '').lower():
            suggestions.append("Ensure tests are included with this PR")
            
        return suggestions
    
    def _analyze_commit(self, commit: Dict) -> List[str]:
        """Analyze commit for potential issues"""
        issues = []
        message = commit['commit']['message']
        
        # Check for large commits
        if commit.get('stats', {}).get('total', 0) > 1000:
            issues.append("Very large commit - may be difficult to review")
            
        # Check for common issues in commit message
        if len(message) < 10:
            issues.append("Commit message too short")
        elif 'fix' in message.lower() and not re.search(r'#\d+', message):
            issues.append("Fix commit without issue reference")
            
        # Check for potential secrets
        secret_patterns = [
            r'api[_-]?key',
            r'secret',
            r'password',
            r'token',
            r'private[_-]?key'
        ]
        
        for pattern in secret_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                issues.append(f"Potential secret in commit message: {pattern}")
                
        return issues
    
    def _generate_commit_suggestions(self, commit: Dict, issues: List[str]) -> List[str]:
        """Generate suggestions for problematic commits"""
        suggestions = []
        
        for issue in issues:
            if "large commit" in issue:
                suggestions.append("Consider using feature branches for large changes")
            elif "message too short" in issue:
                suggestions.append("Use descriptive commit messages following conventional commits")
            elif "secret" in issue:
                suggestions.append("Review commit for secrets and rotate any exposed credentials")
                
        return suggestions


class SystemResourceMonitor:
    """Monitors system resources with anomaly detection"""
    
    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.metrics_history: deque = deque(maxlen=history_size)
        self.anomaly_detector = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        self.is_trained = False
        
    async def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Network I/O
        net_io = psutil.net_io_counters()
        network_io = {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv
        }
        
        # Process count
        process_count = len(psutil.pids())
        
        # Open files
        try:
            open_files = len(psutil.Process().open_files())
        except:
            open_files = 0
            
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_percent=disk_percent,
            network_io=network_io,
            process_count=process_count,
            open_files=open_files
        )
    
    async def analyze_metrics(self, metrics: SystemMetrics) -> List[MonitoringEvent]:
        """Analyze metrics for anomalies and issues"""
        events = []
        
        # Add to history
        self.metrics_history.append(metrics)
        
        # Check thresholds
        if metrics.cpu_percent > 90:
            events.append(MonitoringEvent(
                timestamp=datetime.now(),
                source="system",
                event_type="high_cpu",
                severity="warning",
                message=f"High CPU usage: {metrics.cpu_percent}%",
                data={'cpu_percent': metrics.cpu_percent},
                suggestions=[
                    "Check for CPU-intensive processes",
                    "Consider scaling horizontally",
                    "Profile application for performance bottlenecks"
                ]
            ))
            
        if metrics.memory_percent > 85:
            events.append(MonitoringEvent(
                timestamp=datetime.now(),
                source="system",
                event_type="high_memory",
                severity="warning",
                message=f"High memory usage: {metrics.memory_percent}%",
                data={'memory_percent': metrics.memory_percent},
                suggestions=[
                    "Check for memory leaks",
                    "Optimize memory-intensive operations",
                    "Consider increasing system memory"
                ]
            ))
            
        if metrics.disk_percent > 90:
            events.append(MonitoringEvent(
                timestamp=datetime.now(),
                source="system",
                event_type="low_disk_space",
                severity="critical",
                message=f"Low disk space: {100 - metrics.disk_percent}% free",
                data={'disk_percent': metrics.disk_percent},
                suggestions=[
                    "Clean up temporary files",
                    "Archive old logs",
                    "Remove unused Docker images and containers"
                ]
            ))
            
        # Anomaly detection
        if len(self.metrics_history) >= 100:
            anomalies = await self._detect_anomalies(metrics)
            events.extend(anomalies)
            
        return events
    
    async def _detect_anomalies(self, current_metrics: SystemMetrics) -> List[MonitoringEvent]:
        """Detect anomalies using machine learning"""
        events = []
        
        # Prepare data for anomaly detection
        if len(self.metrics_history) >= 100:
            data = []
            for m in self.metrics_history:
                data.append([
                    m.cpu_percent,
                    m.memory_percent,
                    m.disk_percent,
                    m.process_count,
                    m.open_files
                ])
                
            X = np.array(data)
            
            # Train or update model
            if not self.is_trained:
                self.anomaly_detector.fit(X[:-1])
                self.is_trained = True
                
            # Predict anomaly
            current_data = np.array([[
                current_metrics.cpu_percent,
                current_metrics.memory_percent,
                current_metrics.disk_percent,
                current_metrics.process_count,
                current_metrics.open_files
            ]])
            
            prediction = self.anomaly_detector.predict(current_data)
            
            if prediction[0] == -1:  # Anomaly detected
                events.append(MonitoringEvent(
                    timestamp=datetime.now(),
                    source="system",
                    event_type="resource_anomaly",
                    severity="warning",
                    message="Unusual system resource pattern detected",
                    data={
                        'cpu': current_metrics.cpu_percent,
                        'memory': current_metrics.memory_percent,
                        'disk': current_metrics.disk_percent
                    },
                    suggestions=[
                        "Investigate recent system changes",
                        "Check for unusual process activity",
                        "Review application logs for errors"
                    ]
                ))
                
        return events


class DependencyScanner:
    """Scans for dependency updates and security vulnerabilities"""
    
    def __init__(self):
        self.package_managers = {
            'pip': self._scan_pip,
            'npm': self._scan_npm,
            'cargo': self._scan_cargo,
            'go': self._scan_go
        }
        
    async def scan_all(self) -> List[MonitoringEvent]:
        """Scan all dependency managers"""
        events = []
        
        for manager, scanner in self.package_managers.items():
            try:
                manager_events = await scanner()
                events.extend(manager_events)
            except Exception as e:
                logger.error(f"Error scanning {manager}: {e}")
                
        return events
    
    async def _scan_pip(self) -> List[MonitoringEvent]:
        """Scan Python dependencies"""
        events = []
        
        try:
            # Check for outdated packages
            result = subprocess.run(
                ['pip', 'list', '--outdated', '--format=json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                outdated = json.loads(result.stdout)
                
                for pkg in outdated:
                    # Check if it's a security update
                    is_security = await self._check_security_advisory('pypi', pkg['name'])
                    
                    severity = "critical" if is_security else "info"
                    
                    events.append(MonitoringEvent(
                        timestamp=datetime.now(),
                        source="dependencies:pip",
                        event_type="outdated_package",
                        severity=severity,
                        message=f"Package {pkg['name']} has update: {pkg['version']} → {pkg['latest_version']}",
                        data={
                            'package': pkg['name'],
                            'current': pkg['version'],
                            'latest': pkg['latest_version'],
                            'is_security': is_security
                        },
                        suggestions=[
                            f"Update {pkg['name']} to {pkg['latest_version']}",
                            "Test update in development environment first" if is_security else None
                        ]
                    ))
                    
            # Run safety check for vulnerabilities
            try:
                safety_result = subprocess.run(
                    ['safety', 'check', '--json'],
                    capture_output=True,
                    text=True
                )
                
                if safety_result.returncode != 0 and safety_result.stdout:
                    vulnerabilities = json.loads(safety_result.stdout)
                    
                    for vuln in vulnerabilities:
                        events.append(MonitoringEvent(
                            timestamp=datetime.now(),
                            source="dependencies:pip",
                            event_type="security_vulnerability",
                            severity="critical",
                            message=f"Security vulnerability in {vuln['package']}: {vuln['vulnerability']}",
                            data=vuln,
                            suggestions=[
                                f"Update {vuln['package']} immediately",
                                "Review security advisory for impact assessment"
                            ]
                        ))
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error scanning pip dependencies: {e}")
            
        return events
    
    async def _scan_npm(self) -> List[MonitoringEvent]:
        """Scan Node.js dependencies"""
        events = []
        
        try:
            # Check for outdated packages
            result = subprocess.run(
                ['npm', 'outdated', '--json'],
                capture_output=True,
                text=True,
                cwd='.'
            )
            
            if result.stdout:
                outdated = json.loads(result.stdout)
                
                for name, info in outdated.items():
                    events.append(MonitoringEvent(
                        timestamp=datetime.now(),
                        source="dependencies:npm",
                        event_type="outdated_package",
                        severity="info",
                        message=f"Package {name} has update: {info.get('current')} → {info.get('latest')}",
                        data={
                            'package': name,
                            'current': info.get('current'),
                            'latest': info.get('latest'),
                            'wanted': info.get('wanted')
                        },
                        suggestions=[
                            f"Update {name} to {info.get('latest')}",
                            "Run npm update to apply compatible updates"
                        ]
                    ))
                    
            # Run npm audit
            audit_result = subprocess.run(
                ['npm', 'audit', '--json'],
                capture_output=True,
                text=True,
                cwd='.'
            )
            
            if audit_result.stdout:
                audit_data = json.loads(audit_result.stdout)
                
                if audit_data.get('vulnerabilities'):
                    for severity, count in audit_data['vulnerabilities'].items():
                        if count > 0:
                            events.append(MonitoringEvent(
                                timestamp=datetime.now(),
                                source="dependencies:npm",
                                event_type="security_audit",
                                severity="critical" if severity in ['high', 'critical'] else "warning",
                                message=f"npm audit found {count} {severity} vulnerabilities",
                                data={'severity': severity, 'count': count},
                                suggestions=[
                                    "Run 'npm audit fix' to auto-fix vulnerabilities",
                                    "Review npm audit report for manual fixes"
                                ]
                            ))
                            
        except Exception as e:
            logger.error(f"Error scanning npm dependencies: {e}")
            
        return events
    
    async def _scan_cargo(self) -> List[MonitoringEvent]:
        """Scan Rust dependencies"""
        events = []
        
        try:
            # Check for outdated crates
            result = subprocess.run(
                ['cargo', 'outdated', '--format', 'json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout:
                outdated = json.loads(result.stdout)
                
                for crate in outdated.get('crates', []):
                    events.append(MonitoringEvent(
                        timestamp=datetime.now(),
                        source="dependencies:cargo",
                        event_type="outdated_crate",
                        severity="info",
                        message=f"Crate {crate['name']} has update: {crate['version']} → {crate['latest']}",
                        data=crate,
                        suggestions=[
                            f"Update {crate['name']} in Cargo.toml",
                            "Run 'cargo update' after changing version"
                        ]
                    ))
                    
        except Exception as e:
            logger.error(f"Error scanning cargo dependencies: {e}")
            
        return events
    
    async def _scan_go(self) -> List[MonitoringEvent]:
        """Scan Go dependencies"""
        events = []
        
        try:
            # Check for available updates
            result = subprocess.run(
                ['go', 'list', '-u', '-m', '-json', 'all'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        module = json.loads(line)
                        
                        if module.get('Update'):
                            events.append(MonitoringEvent(
                                timestamp=datetime.now(),
                                source="dependencies:go",
                                event_type="outdated_module",
                                severity="info",
                                message=f"Module {module['Path']} has update: {module.get('Version')} → {module['Update']['Version']}",
                                data=module,
                                suggestions=[
                                    f"Update {module['Path']} to {module['Update']['Version']}",
                                    "Run 'go mod tidy' after updating"
                                ]
                            ))
                            
        except Exception as e:
            logger.error(f"Error scanning go dependencies: {e}")
            
        return events
    
    async def _check_security_advisory(self, ecosystem: str, package: str) -> bool:
        """Check if package has security advisory"""
        # This would integrate with security databases
        # For now, return based on common security-related keywords
        security_keywords = ['security', 'vulnerability', 'cve', 'patch']
        return any(keyword in package.lower() for keyword in security_keywords)


class LogMonitor:
    """Monitors application logs for errors and patterns"""
    
    def __init__(self, log_paths: List[str] = None):
        self.log_paths = log_paths or []
        self.last_positions: Dict[str, int] = {}
        self.error_patterns = [
            (re.compile(r'ERROR|CRITICAL|FATAL', re.I), 'error'),
            (re.compile(r'WARNING|WARN', re.I), 'warning'),
            (re.compile(r'Exception|Traceback', re.I), 'exception'),
            (re.compile(r'timeout|timed out', re.I), 'timeout'),
            (re.compile(r'connection refused|connection error', re.I), 'connection'),
            (re.compile(r'out of memory|OOM', re.I), 'memory'),
            (re.compile(r'disk full|no space left', re.I), 'disk'),
            (re.compile(r'permission denied|access denied', re.I), 'permission')
        ]
        
    async def scan_logs(self) -> List[MonitoringEvent]:
        """Scan logs for new errors and patterns"""
        events = []
        
        for log_path in self.log_paths:
            if os.path.exists(log_path):
                events.extend(await self._scan_log_file(log_path))
                
        return events
    
    async def _scan_log_file(self, log_path: str) -> List[MonitoringEvent]:
        """Scan individual log file"""
        events = []
        
        try:
            with open(log_path, 'r') as f:
                # Seek to last position
                last_pos = self.last_positions.get(log_path, 0)
                f.seek(last_pos)
                
                # Read new content
                new_content = f.read()
                
                # Update position
                self.last_positions[log_path] = f.tell()
                
                # Analyze content
                for line in new_content.split('\n'):
                    if line.strip():
                        for pattern, error_type in self.error_patterns:
                            if pattern.search(line):
                                events.append(self._create_log_event(log_path, line, error_type))
                                break
                                
        except Exception as e:
            logger.error(f"Error scanning log {log_path}: {e}")
            
        return events
    
    def _create_log_event(self, log_path: str, line: str, error_type: str) -> MonitoringEvent:
        """Create monitoring event from log line"""
        severity_map = {
            'error': 'error',
            'exception': 'critical',
            'warning': 'warning',
            'timeout': 'warning',
            'connection': 'error',
            'memory': 'critical',
            'disk': 'critical',
            'permission': 'error'
        }
        
        suggestions_map = {
            'error': ["Review error logs for root cause", "Check recent deployments"],
            'exception': ["Analyze stack trace", "Add error handling", "Check for edge cases"],
            'timeout': ["Increase timeout values", "Optimize slow operations", "Check network latency"],
            'connection': ["Verify service availability", "Check network configuration", "Review firewall rules"],
            'memory': ["Analyze memory usage", "Check for memory leaks", "Scale up resources"],
            'disk': ["Free up disk space", "Archive old files", "Increase disk capacity"],
            'permission': ["Review file permissions", "Check user access rights", "Update security policies"]
        }
        
        return MonitoringEvent(
            timestamp=datetime.now(),
            source=f"logs:{os.path.basename(log_path)}",
            event_type=f"log_{error_type}",
            severity=severity_map.get(error_type, 'warning'),
            message=f"{error_type.capitalize()} detected in logs",
            data={
                'log_file': log_path,
                'line': line[:200],  # Truncate long lines
                'pattern': error_type
            },
            suggestions=suggestions_map.get(error_type, ["Review log entry"])
        )


class SuggestionEngine:
    """Generates intelligent suggestions based on monitoring data"""
    
    def __init__(self):
        self.event_history: deque = deque(maxlen=1000)
        self.pattern_cache: Dict[str, List[str]] = {}
        
    async def analyze_events(self, events: List[MonitoringEvent]) -> List[str]:
        """Analyze events and generate proactive suggestions"""
        suggestions = []
        
        # Add events to history
        self.event_history.extend(events)
        
        # Analyze patterns
        patterns = self._detect_patterns()
        
        # Generate suggestions based on patterns
        if patterns.get('high_error_rate'):
            suggestions.append("High error rate detected - consider implementing circuit breakers")
            
        if patterns.get('memory_growth'):
            suggestions.append("Memory usage trending upward - schedule memory profiling session")
            
        if patterns.get('repeated_timeouts'):
            suggestions.append("Frequent timeouts detected - review service dependencies and network configuration")
            
        if patterns.get('security_backlog'):
            suggestions.append("Multiple security updates pending - schedule security patch window")
            
        if patterns.get('performance_degradation'):
            suggestions.append("Performance degrading over time - consider database optimization or caching strategy")
            
        # Check for correlated events
        correlations = self._find_correlations()
        
        for correlation in correlations:
            suggestions.append(f"Correlation detected: {correlation['event1']} often followed by {correlation['event2']}")
            
        return suggestions
    
    def _detect_patterns(self) -> Dict[str, bool]:
        """Detect patterns in event history"""
        patterns = {}
        
        if not self.event_history:
            return patterns
            
        # Count events by type in last hour
        recent_events = [e for e in self.event_history 
                        if e.timestamp > datetime.now() - timedelta(hours=1)]
        
        error_count = sum(1 for e in recent_events if e.severity in ['error', 'critical'])
        patterns['high_error_rate'] = error_count > 10
        
        # Check for memory growth
        memory_events = [e for e in recent_events if e.event_type == 'high_memory']
        if len(memory_events) >= 3:
            # Check if memory is increasing
            memory_values = [e.data.get('memory_percent', 0) for e in memory_events]
            patterns['memory_growth'] = all(memory_values[i] <= memory_values[i+1] 
                                          for i in range(len(memory_values)-1))
        
        # Check for repeated timeouts
        timeout_count = sum(1 for e in recent_events if 'timeout' in e.event_type)
        patterns['repeated_timeouts'] = timeout_count > 5
        
        # Check for security updates
        security_count = sum(1 for e in recent_events 
                           if e.event_type in ['security_vulnerability', 'security_audit'])
        patterns['security_backlog'] = security_count > 3
        
        # Check for performance degradation
        perf_events = [e for e in recent_events if e.event_type == 'high_cpu']
        patterns['performance_degradation'] = len(perf_events) > 5
        
        return patterns
    
    def _find_correlations(self) -> List[Dict[str, str]]:
        """Find correlated events"""
        correlations = []
        
        # Simple correlation: events that often happen together
        event_pairs = defaultdict(int)
        
        events = list(self.event_history)
        for i in range(len(events) - 1):
            if events[i+1].timestamp - events[i].timestamp < timedelta(minutes=5):
                pair = (events[i].event_type, events[i+1].event_type)
                event_pairs[pair] += 1
                
        # Report frequent pairs
        for (event1, event2), count in event_pairs.items():
            if count >= 3:
                correlations.append({
                    'event1': event1,
                    'event2': event2,
                    'count': count
                })
                
        return correlations


class ProactiveMonitor:
    """Main proactive monitoring system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize components
        self.github_monitor = GitHubMonitor()
        self.system_monitor = SystemResourceMonitor()
        self.dependency_scanner = DependencyScanner()
        self.log_monitor = LogMonitor(self.config.get('log_paths', []))
        self.suggestion_engine = SuggestionEngine()
        
        # Event storage
        self.events: List[MonitoringEvent] = []
        self.event_handlers: List[callable] = []
        
        # Background tasks
        self.monitoring_tasks: List[asyncio.Task] = []
        self.is_running = False
        
    async def start(self):
        """Start monitoring system"""
        logger.info("Starting NEXUS Proactive Monitor")
        self.is_running = True
        
        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._monitor_github()),
            asyncio.create_task(self._monitor_system()),
            asyncio.create_task(self._monitor_dependencies()),
            asyncio.create_task(self._monitor_logs()),
            asyncio.create_task(self._process_suggestions())
        ]
        
        # Wait for tasks
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
    async def stop(self):
        """Stop monitoring system"""
        logger.info("Stopping NEXUS Proactive Monitor")
        self.is_running = False
        
        # Cancel tasks
        for task in self.monitoring_tasks:
            task.cancel()
            
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
    async def add_github_repo(self, repo: str):
        """Add GitHub repository to monitor"""
        await self.github_monitor.add_repository(repo)
        
    def add_event_handler(self, handler: callable):
        """Add event handler"""
        self.event_handlers.append(handler)
        
    async def _monitor_github(self):
        """Monitor GitHub repositories"""
        while self.is_running:
            try:
                for repo in self.github_monitor.monitored_repos:
                    # Check various GitHub events
                    events = []
                    events.extend(await self.github_monitor.check_issues(repo))
                    events.extend(await self.github_monitor.check_pull_requests(repo))
                    events.extend(await self.github_monitor.check_commits(repo))
                    
                    # Process events
                    for event in events:
                        await self._handle_event(event)
                        
                    # Update last check time
                    self.github_monitor.last_check[repo] = datetime.now()
                    
            except Exception as e:
                logger.error(f"Error in GitHub monitoring: {e}")
                
            # Wait before next check
            await asyncio.sleep(300)  # 5 minutes
            
    async def _monitor_system(self):
        """Monitor system resources"""
        while self.is_running:
            try:
                # Collect metrics
                metrics = await self.system_monitor.collect_metrics()
                
                # Analyze for issues
                events = await self.system_monitor.analyze_metrics(metrics)
                
                # Process events
                for event in events:
                    await self._handle_event(event)
                    
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                
            # Wait before next check
            await asyncio.sleep(60)  # 1 minute
            
    async def _monitor_dependencies(self):
        """Monitor dependencies for updates"""
        while self.is_running:
            try:
                # Scan all dependencies
                events = await self.dependency_scanner.scan_all()
                
                # Process events
                for event in events:
                    await self._handle_event(event)
                    
            except Exception as e:
                logger.error(f"Error in dependency monitoring: {e}")
                
            # Wait before next check
            await asyncio.sleep(3600)  # 1 hour
            
    async def _monitor_logs(self):
        """Monitor application logs"""
        while self.is_running:
            try:
                # Scan logs
                events = await self.log_monitor.scan_logs()
                
                # Process events
                for event in events:
                    await self._handle_event(event)
                    
            except Exception as e:
                logger.error(f"Error in log monitoring: {e}")
                
            # Wait before next check
            await asyncio.sleep(30)  # 30 seconds
            
    async def _process_suggestions(self):
        """Process events and generate suggestions"""
        while self.is_running:
            try:
                # Get recent events
                recent_events = [e for e in self.events 
                               if e.timestamp > datetime.now() - timedelta(hours=1)]
                
                if recent_events:
                    # Generate suggestions
                    suggestions = await self.suggestion_engine.analyze_events(recent_events)
                    
                    if suggestions:
                        # Create suggestion event
                        event = MonitoringEvent(
                            timestamp=datetime.now(),
                            source="suggestion_engine",
                            event_type="proactive_suggestions",
                            severity="info",
                            message="Proactive suggestions based on monitoring data",
                            data={'suggestion_count': len(suggestions)},
                            suggestions=suggestions
                        )
                        
                        await self._handle_event(event)
                        
            except Exception as e:
                logger.error(f"Error in suggestion processing: {e}")
                
            # Wait before next analysis
            await asyncio.sleep(600)  # 10 minutes
            
    async def _handle_event(self, event: MonitoringEvent):
        """Handle monitoring event"""
        # Store event
        self.events.append(event)
        
        # Log event
        logger.info(f"[{event.severity.upper()}] {event.source}: {event.message}")
        
        if event.suggestions:
            logger.info(f"Suggestions: {', '.join(event.suggestions)}")
            
        # Call handlers
        for handler in self.event_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
                
    def get_recent_events(self, hours: int = 24) -> List[MonitoringEvent]:
        """Get recent events"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [e for e in self.events if e.timestamp > cutoff]
        
    def get_events_by_severity(self, severity: str) -> List[MonitoringEvent]:
        """Get events by severity"""
        return [e for e in self.events if e.severity == severity]
        
    def get_suggestions(self) -> List[str]:
        """Get all suggestions from recent events"""
        suggestions = []
        
        for event in self.get_recent_events():
            suggestions.extend(event.suggestions)
            
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        
        for suggestion in suggestions:
            if suggestion and suggestion not in seen:
                seen.add(suggestion)
                unique_suggestions.append(suggestion)
                
        return unique_suggestions


# Webhook server for external integrations
from aiohttp import web


class WebhookServer:
    """Webhook server for external integrations"""
    
    def __init__(self, monitor: ProactiveMonitor, port: int = 8888):
        self.monitor = monitor
        self.port = port
        self.app = web.Application()
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup webhook routes"""
        self.app.router.add_post('/webhook/github', self.handle_github_webhook)
        self.app.router.add_post('/webhook/gitlab', self.handle_gitlab_webhook)
        self.app.router.add_post('/webhook/custom', self.handle_custom_webhook)
        self.app.router.add_get('/events', self.get_events)
        self.app.router.add_get('/suggestions', self.get_suggestions)
        self.app.router.add_get('/health', self.health_check)
        
    async def handle_github_webhook(self, request):
        """Handle GitHub webhook"""
        try:
            data = await request.json()
            event_type = request.headers.get('X-GitHub-Event')
            
            # Process webhook data
            event = MonitoringEvent(
                timestamp=datetime.now(),
                source="webhook:github",
                event_type=f"github_{event_type}",
                severity="info",
                message=f"GitHub webhook: {event_type}",
                data=data
            )
            
            await self.monitor._handle_event(event)
            
            return web.json_response({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"Error handling GitHub webhook: {e}")
            return web.json_response({'error': str(e)}, status=500)
            
    async def handle_gitlab_webhook(self, request):
        """Handle GitLab webhook"""
        try:
            data = await request.json()
            event_type = data.get('object_kind', 'unknown')
            
            # Process webhook data
            event = MonitoringEvent(
                timestamp=datetime.now(),
                source="webhook:gitlab",
                event_type=f"gitlab_{event_type}",
                severity="info",
                message=f"GitLab webhook: {event_type}",
                data=data
            )
            
            await self.monitor._handle_event(event)
            
            return web.json_response({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"Error handling GitLab webhook: {e}")
            return web.json_response({'error': str(e)}, status=500)
            
    async def handle_custom_webhook(self, request):
        """Handle custom webhook"""
        try:
            data = await request.json()
            
            # Process webhook data
            event = MonitoringEvent(
                timestamp=datetime.now(),
                source="webhook:custom",
                event_type=data.get('type', 'custom'),
                severity=data.get('severity', 'info'),
                message=data.get('message', 'Custom webhook event'),
                data=data.get('data', {}),
                suggestions=data.get('suggestions', [])
            )
            
            await self.monitor._handle_event(event)
            
            return web.json_response({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"Error handling custom webhook: {e}")
            return web.json_response({'error': str(e)}, status=500)
            
    async def get_events(self, request):
        """Get recent events"""
        hours = int(request.query.get('hours', 24))
        severity = request.query.get('severity')
        
        if severity:
            events = self.monitor.get_events_by_severity(severity)
        else:
            events = self.monitor.get_recent_events(hours)
            
        # Convert to JSON-serializable format
        events_data = []
        for event in events:
            events_data.append({
                'timestamp': event.timestamp.isoformat(),
                'source': event.source,
                'event_type': event.event_type,
                'severity': event.severity,
                'message': event.message,
                'data': event.data,
                'suggestions': event.suggestions
            })
            
        return web.json_response(events_data)
        
    async def get_suggestions(self, request):
        """Get suggestions"""
        suggestions = self.monitor.get_suggestions()
        return web.json_response({'suggestions': suggestions})
        
    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            'status': 'healthy',
            'is_running': self.monitor.is_running,
            'monitored_repos': list(self.monitor.github_monitor.monitored_repos),
            'event_count': len(self.monitor.events)
        })
        
    async def start(self):
        """Start webhook server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        logger.info(f"Webhook server started on port {self.port}")


# Example usage and main entry point
async def main():
    """Main entry point"""
    # Configuration
    config = {
        'log_paths': [
            '/var/log/nexus/app.log',
            '/var/log/nexus/error.log',
            './nexus.log'
        ],
        'github_repos': [
            'nexus-project/nexus-core',
            'nexus-project/nexus-ui'
        ]
    }
    
    # Create monitor
    monitor = ProactiveMonitor(config)
    
    # Add GitHub repositories
    for repo in config.get('github_repos', []):
        await monitor.add_github_repo(repo)
        
    # Create webhook server
    webhook_server = WebhookServer(monitor)
    
    # Add custom event handler
    async def custom_handler(event: MonitoringEvent):
        if event.severity in ['critical', 'error']:
            print(f"ALERT: {event.message}")
            # Here you could send notifications, create tickets, etc.
            
    monitor.add_event_handler(custom_handler)
    
    # Start services
    await asyncio.gather(
        monitor.start(),
        webhook_server.start()
    )


if __name__ == "__main__":
    asyncio.run(main())