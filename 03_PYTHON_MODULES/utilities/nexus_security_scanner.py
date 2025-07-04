#!/usr/bin/env python3
"""
NEXUS Security Scanner - Omnipotent Security Analysis Tool
Detects vulnerabilities, suggests fixes, and ensures code security
"""

import os
import re
import json
import hashlib
import ast
from typing import Dict, List, Tuple, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import subprocess
from pathlib import Path

from nexus_unified_tools import NEXUSToolBase


class VulnerabilityType(Enum):
    """Types of vulnerabilities the scanner can detect"""
    SQL_INJECTION = "SQL Injection"
    XSS = "Cross-Site Scripting (XSS)"
    CSRF = "Cross-Site Request Forgery (CSRF)"
    INSECURE_DESERIALIZATION = "Insecure Deserialization"
    HARDCODED_CREDENTIALS = "Hardcoded Credentials"
    PATH_TRAVERSAL = "Path Traversal"
    COMMAND_INJECTION = "Command Injection"
    WEAK_CRYPTOGRAPHY = "Weak Cryptography"
    SENSITIVE_DATA_EXPOSURE = "Sensitive Data Exposure"
    BROKEN_ACCESS_CONTROL = "Broken Access Control"
    SECURITY_MISCONFIGURATION = "Security Misconfiguration"
    VULNERABLE_DEPENDENCIES = "Vulnerable Dependencies"


class Severity(Enum):
    """Vulnerability severity levels"""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFO = "Informational"


@dataclass
class Vulnerability:
    """Represents a detected vulnerability"""
    type: VulnerabilityType
    severity: Severity
    file_path: str
    line_number: int
    code_snippet: str
    description: str
    fix_suggestion: str
    cve_id: Optional[str] = None
    owasp_category: Optional[str] = None
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert vulnerability to dictionary"""
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "description": self.description,
            "fix_suggestion": self.fix_suggestion,
            "cve_id": self.cve_id,
            "owasp_category": self.owasp_category,
            "confidence": self.confidence
        }


@dataclass
class SecurityReport:
    """Comprehensive security scan report"""
    scan_id: str
    scan_date: datetime
    target_directory: str
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    risk_score: float = 0.0
    files_scanned: int = 0
    total_lines: int = 0
    scan_duration: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary"""
        return {
            "scan_id": self.scan_id,
            "scan_date": self.scan_date.isoformat(),
            "target_directory": self.target_directory,
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "risk_score": self.risk_score,
            "files_scanned": self.files_scanned,
            "total_lines": self.total_lines,
            "scan_duration": self.scan_duration,
            "summary": self.get_summary()
        }
    
    def get_summary(self) -> Dict[str, int]:
        """Get vulnerability count by severity"""
        summary = {s.value: 0 for s in Severity}
        for vuln in self.vulnerabilities:
            summary[vuln.severity.value] += 1
        return summary


class SecurityScannerOmnipotent(NEXUSToolBase):
    """Omnipotent Security Scanner for NEXUS"""
    
    def __init__(self):
        super().__init__(
            name="SecurityScanner",
            description="Comprehensive security vulnerability scanner",
            capabilities=[
                "vulnerability_detection",
                "dependency_scanning",
                "security_reporting",
                "fix_suggestions",
                "risk_assessment"
            ]
        )
        
        # Initialize patterns for vulnerability detection
        self._init_vulnerability_patterns()
        
        # Mock CVE database
        self._init_cve_database()
        
        # OWASP Top 10 mapping
        self._init_owasp_mapping()
    
    def _init_vulnerability_patterns(self):
        """Initialize regex patterns for vulnerability detection"""
        self.patterns = {
            VulnerabilityType.SQL_INJECTION: [
                # Direct SQL concatenation
                (r'(query|execute|cursor\.execute)\s*\(\s*["\'].*?\+.*?["\']', Severity.CRITICAL),
                (r'(query|execute)\s*\(\s*f["\'].*?\{.*?\}', Severity.HIGH),
                (r'(SELECT|INSERT|UPDATE|DELETE).*?\+.*?["\']', Severity.HIGH),
                # String formatting in SQL
                (r'\.format\s*\(.*?\).*?(SELECT|INSERT|UPDATE|DELETE)', Severity.HIGH),
                (r'%\s*\(.*?\).*?(SELECT|INSERT|UPDATE|DELETE)', Severity.HIGH),
            ],
            
            VulnerabilityType.XSS: [
                # Direct HTML output without escaping
                (r'innerHTML\s*=\s*[^;]*?(request|user|input)', Severity.HIGH),
                (r'document\.write\s*\([^)]*?(request|user|input)', Severity.HIGH),
                (r'\.html\s*\([^)]*?(request|user|input)', Severity.MEDIUM),
                # Unescaped template rendering
                (r'\{\{\s*[^}]*?\|\s*safe\s*\}\}', Severity.HIGH),
                (r'autoescape\s*=\s*False', Severity.HIGH),
            ],
            
            VulnerabilityType.CSRF: [
                # Missing CSRF protection
                (r'@app\.route.*?methods\s*=\s*\[[^\]]*?POST[^\]]*?\](?!.*?csrf)', Severity.MEDIUM),
                (r'csrf_exempt', Severity.MEDIUM),
                (r'verify_csrf_token\s*=\s*False', Severity.HIGH),
            ],
            
            VulnerabilityType.INSECURE_DESERIALIZATION: [
                # Dangerous deserialization
                (r'pickle\.loads?\s*\([^)]*?(request|user|input)', Severity.CRITICAL),
                (r'yaml\.load\s*\([^)]*?Loader\s*=\s*yaml\.FullLoader', Severity.HIGH),
                (r'eval\s*\([^)]*?(request|user|input)', Severity.CRITICAL),
                (r'exec\s*\([^)]*?(request|user|input)', Severity.CRITICAL),
            ],
            
            VulnerabilityType.HARDCODED_CREDENTIALS: [
                # Hardcoded passwords/keys
                (r'(password|passwd|pwd)\s*=\s*["\'][^"\']{8,}["\']', Severity.CRITICAL),
                (r'(api_key|apikey|secret)\s*=\s*["\'][^"\']{16,}["\']', Severity.CRITICAL),
                (r'(token)\s*=\s*["\'][^"\']{20,}["\']', Severity.HIGH),
                # AWS/Azure/GCP credentials
                (r'AKIA[0-9A-Z]{16}', Severity.CRITICAL),  # AWS Access Key
                (r'[0-9a-zA-Z/+=]{40}', Severity.HIGH),  # Potential AWS Secret
            ],
            
            VulnerabilityType.PATH_TRAVERSAL: [
                # Path traversal patterns
                (r'open\s*\([^)]*?(request|user|input)', Severity.HIGH),
                (r'os\.path\.join\s*\([^)]*?(request|user|input)', Severity.MEDIUM),
                (r'\.\./', Severity.MEDIUM),
                (r'file:\/\/', Severity.HIGH),
            ],
            
            VulnerabilityType.COMMAND_INJECTION: [
                # Command execution with user input
                (r'os\.system\s*\([^)]*?(request|user|input)', Severity.CRITICAL),
                (r'subprocess\.(call|run|Popen)\s*\([^)]*?(request|user|input)', Severity.CRITICAL),
                (r'shell\s*=\s*True.*?(request|user|input)', Severity.CRITICAL),
                (r'`[^`]*?(request|user|input)', Severity.HIGH),
            ],
            
            VulnerabilityType.WEAK_CRYPTOGRAPHY: [
                # Weak hash algorithms
                (r'md5|MD5', Severity.HIGH),
                (r'sha1|SHA1', Severity.MEDIUM),
                # Weak encryption
                (r'DES\s*\(', Severity.HIGH),
                (r'ECB\s*mode', Severity.HIGH),
                # Insecure random
                (r'random\.random\s*\(\)', Severity.MEDIUM),
                (r'math\.random\s*\(\)', Severity.MEDIUM),
            ],
        }
    
    def _init_cve_database(self):
        """Initialize mock CVE database"""
        self.cve_database = {
            "pickle": {"CVE-2020-1234": "Insecure deserialization in pickle"},
            "yaml": {"CVE-2020-5678": "YAML deserialization vulnerability"},
            "requests": {
                "2.25.0": {"CVE-2021-1234": "SSRF vulnerability in requests < 2.25.1"}
            },
            "django": {
                "3.1.0": {"CVE-2021-5678": "SQL injection in Django < 3.1.1"}
            },
        }
    
    def _init_owasp_mapping(self):
        """Map vulnerability types to OWASP Top 10"""
        self.owasp_mapping = {
            VulnerabilityType.SQL_INJECTION: "A03:2021 - Injection",
            VulnerabilityType.BROKEN_ACCESS_CONTROL: "A01:2021 - Broken Access Control",
            VulnerabilityType.WEAK_CRYPTOGRAPHY: "A02:2021 - Cryptographic Failures",
            VulnerabilityType.INSECURE_DESERIALIZATION: "A08:2021 - Software and Data Integrity Failures",
            VulnerabilityType.SECURITY_MISCONFIGURATION: "A05:2021 - Security Misconfiguration",
            VulnerabilityType.VULNERABLE_DEPENDENCIES: "A06:2021 - Vulnerable and Outdated Components",
            VulnerabilityType.XSS: "A03:2021 - Injection",
            VulnerabilityType.CSRF: "A01:2021 - Broken Access Control",
            VulnerabilityType.HARDCODED_CREDENTIALS: "A07:2021 - Identification and Authentication Failures",
            VulnerabilityType.PATH_TRAVERSAL: "A01:2021 - Broken Access Control",
            VulnerabilityType.COMMAND_INJECTION: "A03:2021 - Injection",
        }
    
    def scan_for_vulnerabilities(self, directory: str) -> SecurityReport:
        """Perform comprehensive security scan on directory"""
        start_time = datetime.now()
        scan_id = hashlib.sha256(f"{directory}{start_time}".encode()).hexdigest()[:16]
        
        report = SecurityReport(
            scan_id=scan_id,
            scan_date=start_time,
            target_directory=directory
        )
        
        # Scan all supported files
        for root, _, files in os.walk(directory):
            for file in files:
                if self._should_scan_file(file):
                    file_path = os.path.join(root, file)
                    self._scan_file(file_path, report)
        
        # Check dependencies
        dep_vulns = self.check_dependencies(directory)
        report.vulnerabilities.extend(dep_vulns)
        
        # Calculate risk score
        report.risk_score = self.calculate_risk_score(report.vulnerabilities)
        
        # Set scan duration
        report.scan_duration = (datetime.now() - start_time).total_seconds()
        
        return report
    
    def _should_scan_file(self, filename: str) -> bool:
        """Check if file should be scanned"""
        extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.php', '.rb', '.go'}
        return any(filename.endswith(ext) for ext in extensions)
    
    def _scan_file(self, file_path: str, report: SecurityReport):
        """Scan individual file for vulnerabilities"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
            
            report.files_scanned += 1
            report.total_lines += len(lines)
            
            # Check each vulnerability pattern
            for vuln_type, patterns in self.patterns.items():
                for pattern, severity in patterns:
                    for i, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            vuln = self._create_vulnerability(
                                vuln_type, severity, file_path, i, line
                            )
                            report.vulnerabilities.append(vuln)
            
            # Additional AST-based analysis for Python files
            if file_path.endswith('.py'):
                self._ast_analysis(file_path, content, report)
                
        except Exception as e:
            self.logger.error(f"Error scanning {file_path}: {e}")
    
    def _ast_analysis(self, file_path: str, content: str, report: SecurityReport):
        """Perform AST-based analysis for Python files"""
        try:
            tree = ast.parse(content)
            
            # Check for dangerous function calls
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['eval', 'exec', '__import__']:
                            vuln = Vulnerability(
                                type=VulnerabilityType.INSECURE_DESERIALIZATION,
                                severity=Severity.CRITICAL,
                                file_path=file_path,
                                line_number=node.lineno,
                                code_snippet=f"Dangerous function: {node.func.id}",
                                description=f"Use of dangerous function {node.func.id}",
                                fix_suggestion="Avoid using eval/exec with user input. Use ast.literal_eval for safe evaluation.",
                                owasp_category=self.owasp_mapping.get(VulnerabilityType.INSECURE_DESERIALIZATION)
                            )
                            report.vulnerabilities.append(vuln)
        except:
            pass  # Skip AST analysis if parsing fails
    
    def _create_vulnerability(self, vuln_type: VulnerabilityType, severity: Severity,
                            file_path: str, line_number: int, code_snippet: str) -> Vulnerability:
        """Create vulnerability object with fix suggestions"""
        fix_suggestions = {
            VulnerabilityType.SQL_INJECTION: 
                "Use parameterized queries or prepared statements. Example:\n"
                "cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
            
            VulnerabilityType.XSS:
                "Escape all user input before rendering. Use framework-specific escaping:\n"
                "- Django: Use |escape filter or autoescape\n"
                "- React: JSX automatically escapes\n"
                "- Manual: html.escape(user_input)",
            
            VulnerabilityType.CSRF:
                "Implement CSRF protection:\n"
                "- Django: Use {% csrf_token %} in forms\n"
                "- Flask: Use Flask-WTF CSRF protection\n"
                "- Add CSRF tokens to all state-changing requests",
            
            VulnerabilityType.INSECURE_DESERIALIZATION:
                "Avoid deserializing untrusted data:\n"
                "- Use JSON instead of pickle\n"
                "- If YAML needed, use yaml.safe_load()\n"
                "- Never use eval() or exec() with user input",
            
            VulnerabilityType.HARDCODED_CREDENTIALS:
                "Store credentials securely:\n"
                "- Use environment variables: os.environ.get('API_KEY')\n"
                "- Use secrets management: AWS Secrets Manager, HashiCorp Vault\n"
                "- Use .env files (add to .gitignore)",
            
            VulnerabilityType.PATH_TRAVERSAL:
                "Validate and sanitize file paths:\n"
                "- Use os.path.basename() to get filename only\n"
                "- Validate against whitelist of allowed paths\n"
                "- Use pathlib for safe path operations",
            
            VulnerabilityType.COMMAND_INJECTION:
                "Avoid shell execution with user input:\n"
                "- Use subprocess with shell=False\n"
                "- Pass arguments as list: subprocess.run(['cmd', 'arg1'])\n"
                "- Validate/escape all user input",
            
            VulnerabilityType.WEAK_CRYPTOGRAPHY:
                "Use strong cryptography:\n"
                "- Replace MD5/SHA1 with SHA256 or SHA3\n"
                "- Use bcrypt/scrypt/argon2 for passwords\n"
                "- Use secrets.token_urlsafe() for tokens\n"
                "- Use AES-GCM or ChaCha20-Poly1305 for encryption",
        }
        
        return Vulnerability(
            type=vuln_type,
            severity=severity,
            file_path=file_path,
            line_number=line_number,
            code_snippet=code_snippet.strip(),
            description=f"{vuln_type.value} vulnerability detected",
            fix_suggestion=fix_suggestions.get(vuln_type, "Review and fix this security issue"),
            owasp_category=self.owasp_mapping.get(vuln_type)
        )
    
    def check_dependencies(self, directory: str) -> List[Vulnerability]:
        """Check for vulnerable dependencies"""
        vulnerabilities = []
        
        # Check Python dependencies
        requirements_files = ['requirements.txt', 'Pipfile', 'pyproject.toml']
        for req_file in requirements_files:
            req_path = os.path.join(directory, req_file)
            if os.path.exists(req_path):
                vulns = self._check_python_dependencies(req_path)
                vulnerabilities.extend(vulns)
        
        # Check Node.js dependencies
        package_json = os.path.join(directory, 'package.json')
        if os.path.exists(package_json):
            vulns = self._check_node_dependencies(package_json)
            vulnerabilities.extend(vulns)
        
        return vulnerabilities
    
    def _check_python_dependencies(self, req_file: str) -> List[Vulnerability]:
        """Check Python dependencies for vulnerabilities"""
        vulnerabilities = []
        
        try:
            with open(req_file, 'r') as f:
                content = f.read()
            
            # Simple pattern matching for demo (real implementation would use pip-audit)
            for package, cves in self.cve_database.items():
                if package in content:
                    for cve_id, description in cves.items():
                        if isinstance(cves[cve_id], dict):
                            continue  # Skip version-specific CVEs for simplicity
                        
                        vuln = Vulnerability(
                            type=VulnerabilityType.VULNERABLE_DEPENDENCIES,
                            severity=Severity.HIGH,
                            file_path=req_file,
                            line_number=1,
                            code_snippet=f"{package} in {req_file}",
                            description=f"Vulnerable dependency: {description}",
                            fix_suggestion=f"Update {package} to latest secure version",
                            cve_id=cve_id,
                            owasp_category=self.owasp_mapping.get(VulnerabilityType.VULNERABLE_DEPENDENCIES)
                        )
                        vulnerabilities.append(vuln)
        
        except Exception as e:
            self.logger.error(f"Error checking Python dependencies: {e}")
        
        return vulnerabilities
    
    def _check_node_dependencies(self, package_json: str) -> List[Vulnerability]:
        """Check Node.js dependencies for vulnerabilities"""
        vulnerabilities = []
        
        try:
            with open(package_json, 'r') as f:
                data = json.load(f)
            
            # In real implementation, would use npm audit or similar
            # For demo, just check for outdated packages
            deps = data.get('dependencies', {})
            dev_deps = data.get('devDependencies', {})
            
            all_deps = {**deps, **dev_deps}
            
            for pkg, version in all_deps.items():
                # Simple check for very old versions (starting with 0. or 1.)
                if version.startswith(('0.', '1.')):
                    vuln = Vulnerability(
                        type=VulnerabilityType.VULNERABLE_DEPENDENCIES,
                        severity=Severity.MEDIUM,
                        file_path=package_json,
                        line_number=1,
                        code_snippet=f'"{pkg}": "{version}"',
                        description=f"Potentially outdated dependency: {pkg}@{version}",
                        fix_suggestion=f"Update {pkg} to latest stable version",
                        owasp_category=self.owasp_mapping.get(VulnerabilityType.VULNERABLE_DEPENDENCIES)
                    )
                    vulnerabilities.append(vuln)
        
        except Exception as e:
            self.logger.error(f"Error checking Node dependencies: {e}")
        
        return vulnerabilities
    
    def generate_security_report(self, report: SecurityReport, output_format: str = "json") -> str:
        """Generate detailed security report"""
        if output_format == "json":
            return json.dumps(report.to_dict(), indent=2)
        
        elif output_format == "markdown":
            md = f"# Security Scan Report\n\n"
            md += f"**Scan ID:** {report.scan_id}\n"
            md += f"**Date:** {report.scan_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
            md += f"**Target:** {report.target_directory}\n"
            md += f"**Risk Score:** {report.risk_score:.2f}/10\n\n"
            
            md += "## Summary\n\n"
            summary = report.get_summary()
            for severity, count in summary.items():
                if count > 0:
                    md += f"- **{severity}:** {count}\n"
            
            md += f"\n**Total Vulnerabilities:** {len(report.vulnerabilities)}\n"
            md += f"**Files Scanned:** {report.files_scanned}\n"
            md += f"**Lines Analyzed:** {report.total_lines}\n"
            md += f"**Scan Duration:** {report.scan_duration:.2f}s\n\n"
            
            if report.vulnerabilities:
                md += "## Vulnerabilities\n\n"
                
                # Group by severity
                by_severity = {}
                for vuln in report.vulnerabilities:
                    if vuln.severity not in by_severity:
                        by_severity[vuln.severity] = []
                    by_severity[vuln.severity].append(vuln)
                
                for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]:
                    if severity in by_severity:
                        md += f"### {severity.value} Severity\n\n"
                        for vuln in by_severity[severity]:
                            md += f"#### {vuln.type.value}\n"
                            md += f"- **File:** `{vuln.file_path}`\n"
                            md += f"- **Line:** {vuln.line_number}\n"
                            md += f"- **Code:** `{vuln.code_snippet}`\n"
                            md += f"- **Description:** {vuln.description}\n"
                            if vuln.cve_id:
                                md += f"- **CVE:** {vuln.cve_id}\n"
                            if vuln.owasp_category:
                                md += f"- **OWASP:** {vuln.owasp_category}\n"
                            md += f"- **Fix:** {vuln.fix_suggestion}\n\n"
            
            md += "## Recommendations\n\n"
            md += self._generate_recommendations(report)
            
            return md
        
        else:
            raise ValueError(f"Unsupported format: {output_format}")
    
    def _generate_recommendations(self, report: SecurityReport) -> str:
        """Generate security recommendations based on findings"""
        recommendations = []
        
        # Count vulnerability types
        vuln_types = {}
        for vuln in report.vulnerabilities:
            vuln_types[vuln.type] = vuln_types.get(vuln.type, 0) + 1
        
        # Generate specific recommendations
        if VulnerabilityType.SQL_INJECTION in vuln_types:
            recommendations.append(
                "1. **Implement Parameterized Queries**: Replace all string concatenation "
                "in SQL queries with parameterized statements to prevent SQL injection."
            )
        
        if VulnerabilityType.XSS in vuln_types:
            recommendations.append(
                "2. **Enable Output Encoding**: Ensure all user input is properly escaped "
                "before rendering in HTML. Enable auto-escaping in your template engine."
            )
        
        if VulnerabilityType.HARDCODED_CREDENTIALS in vuln_types:
            recommendations.append(
                "3. **Secure Credential Storage**: Move all hardcoded credentials to "
                "environment variables or a secure secrets management system."
            )
        
        if VulnerabilityType.VULNERABLE_DEPENDENCIES in vuln_types:
            recommendations.append(
                "4. **Update Dependencies**: Run dependency audit tools regularly and "
                "update all vulnerable packages to their latest secure versions."
            )
        
        if VulnerabilityType.WEAK_CRYPTOGRAPHY in vuln_types:
            recommendations.append(
                "5. **Upgrade Cryptography**: Replace weak algorithms (MD5, SHA1, DES) "
                "with modern alternatives (SHA256, bcrypt, AES-GCM)."
            )
        
        # General recommendations
        recommendations.extend([
            "- Implement a Security Development Lifecycle (SDL)",
            "- Conduct regular security training for developers",
            "- Set up automated security scanning in CI/CD pipeline",
            "- Perform periodic penetration testing",
            "- Implement security headers (CSP, HSTS, X-Frame-Options)",
            "- Enable logging and monitoring for security events"
        ])
        
        return "\n".join(recommendations)
    
    def suggest_fixes(self, vulnerability: Vulnerability) -> Dict[str, Any]:
        """Generate detailed fix suggestions for a vulnerability"""
        fixes = {
            "vulnerability": vulnerability.to_dict(),
            "fixes": []
        }
        
        if vulnerability.type == VulnerabilityType.SQL_INJECTION:
            fixes["fixes"] = [
                {
                    "title": "Use Parameterized Queries",
                    "code": """# Instead of:
query = f"SELECT * FROM users WHERE id = {user_id}"

# Use:
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))""",
                    "explanation": "Parameterized queries separate SQL logic from data"
                },
                {
                    "title": "Use ORM",
                    "code": """# Using SQLAlchemy
user = User.query.filter_by(id=user_id).first()

# Using Django ORM
user = User.objects.get(id=user_id)""",
                    "explanation": "ORMs provide built-in protection against SQL injection"
                }
            ]
        
        elif vulnerability.type == VulnerabilityType.XSS:
            fixes["fixes"] = [
                {
                    "title": "HTML Escape User Input",
                    "code": """# Python
import html
safe_output = html.escape(user_input)

# JavaScript
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}""",
                    "explanation": "Escaping converts dangerous characters to safe entities"
                },
                {
                    "title": "Use Content Security Policy",
                    "code": """# Add to HTTP headers
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'""",
                    "explanation": "CSP helps prevent XSS by controlling resource loading"
                }
            ]
        
        elif vulnerability.type == VulnerabilityType.HARDCODED_CREDENTIALS:
            fixes["fixes"] = [
                {
                    "title": "Use Environment Variables",
                    "code": """# Instead of:
api_key = "sk-1234567890abcdef"

# Use:
import os
api_key = os.environ.get('API_KEY')

# .env file (add to .gitignore)
API_KEY=sk-1234567890abcdef""",
                    "explanation": "Environment variables keep secrets out of code"
                },
                {
                    "title": "Use Secrets Manager",
                    "code": """# AWS Secrets Manager
import boto3
client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='api-key')
api_key = response['SecretString']""",
                    "explanation": "Dedicated secrets management provides better security"
                }
            ]
        
        return fixes
    
    def calculate_risk_score(self, vulnerabilities: List[Vulnerability]) -> float:
        """Calculate overall security risk score (0-10)"""
        if not vulnerabilities:
            return 0.0
        
        # Weight by severity
        severity_weights = {
            Severity.CRITICAL: 10.0,
            Severity.HIGH: 7.5,
            Severity.MEDIUM: 5.0,
            Severity.LOW: 2.5,
            Severity.INFO: 1.0
        }
        
        total_weight = 0
        for vuln in vulnerabilities:
            total_weight += severity_weights.get(vuln.severity, 0) * vuln.confidence
        
        # Normalize to 0-10 scale
        # Assuming 5 critical vulnerabilities would max out the score
        normalized_score = min(total_weight / 50.0 * 10.0, 10.0)
        
        return round(normalized_score, 2)
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute security scan based on parameters"""
        action = kwargs.get('action', 'scan')
        
        if action == 'scan':
            directory = kwargs.get('directory', '.')
            report = self.scan_for_vulnerabilities(directory)
            return {
                "success": True,
                "report": report.to_dict(),
                "markdown": self.generate_security_report(report, "markdown")
            }
        
        elif action == 'check_dependencies':
            directory = kwargs.get('directory', '.')
            vulns = self.check_dependencies(directory)
            return {
                "success": True,
                "vulnerabilities": [v.to_dict() for v in vulns]
            }
        
        elif action == 'suggest_fix':
            vuln_data = kwargs.get('vulnerability')
            if vuln_data:
                vuln = Vulnerability(**vuln_data)
                fixes = self.suggest_fixes(vuln)
                return {"success": True, "fixes": fixes}
        
        return {"success": False, "error": "Unknown action"}
    
    def execute_specialty(self, **kwargs) -> Dict[str, Any]:
        """Execute security scanning specialty - Enhanced MANUS integration"""
        action = kwargs.get('action', 'scan')
        directory = kwargs.get('directory', '.')
        
        try:
            if action == 'scan':
                # Perform comprehensive security scan
                report = self.scan_for_vulnerabilities(directory)
                return {
                    "success": True,
                    "action": "security_scan",
                    "report": report.to_dict(),
                    "summary": {
                        "total_vulnerabilities": len(report.vulnerabilities),
                        "risk_score": report.risk_score,
                        "files_scanned": report.files_scanned,
                        "critical_issues": len([v for v in report.vulnerabilities if v.severity == Severity.CRITICAL])
                    },
                    "markdown_report": self.generate_security_report(report, "markdown")
                }
            
            elif action == 'quick_scan':
                # Quick dependency check
                vulns = self.check_dependencies(directory)
                return {
                    "success": True,
                    "action": "quick_security_scan",
                    "vulnerabilities": [v.to_dict() for v in vulns],
                    "summary": f"Found {len(vulns)} dependency vulnerabilities"
                }
            
            elif action == 'suggest_fixes':
                # Get fix suggestions for vulnerabilities
                report = self.scan_for_vulnerabilities(directory)
                fixes = []
                for vuln in report.vulnerabilities[:5]:  # Top 5 vulnerabilities
                    fix_suggestion = self.suggest_fixes(vuln)
                    fixes.append(fix_suggestion)
                
                return {
                    "success": True,
                    "action": "security_fix_suggestions",
                    "fixes": fixes,
                    "summary": f"Generated fix suggestions for {len(fixes)} vulnerabilities"
                }
            
            else:
                return self.execute(**kwargs)
                
        except Exception as e:
            self.logger.error(f"Security scanner specialty execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": action
            }


def main():
    """Demo the security scanner"""
    scanner = SecurityScannerOmnipotent()
    
    # Scan current directory
    print("🔒 NEXUS Security Scanner Demo")
    print("=" * 50)
    
    # Create test vulnerable file
    test_file = "test_vulnerable.py"
    with open(test_file, 'w') as f:
        f.write('''
# Vulnerable code for testing
import pickle
import os

# SQL Injection vulnerability
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return execute_query(query)

# Hardcoded credentials
API_KEY = "sk-1234567890abcdef"
password = "supersecret123"

# Command injection
def run_command(user_input):
    os.system(f"echo {user_input}")

# Insecure deserialization
def load_data(data):
    return pickle.loads(data)

# Weak cryptography
import md5
def hash_password(pwd):
    return md5.new(pwd).hexdigest()
''')
    
    # Run scan
    report = scanner.scan_for_vulnerabilities('.')
    
    # Display report
    print(scanner.generate_security_report(report, "markdown"))
    
    # Show fix suggestions for first vulnerability
    if report.vulnerabilities:
        print("\n\n🔧 Fix Suggestions for First Vulnerability:")
        print("=" * 50)
        fixes = scanner.suggest_fixes(report.vulnerabilities[0])
        for fix in fixes["fixes"]:
            print(f"\n### {fix['title']}")
            print(f"```python\n{fix['code']}\n```")
            print(f"Explanation: {fix['explanation']}")
    
    # Cleanup
    os.remove(test_file)


if __name__ == "__main__":
    main()