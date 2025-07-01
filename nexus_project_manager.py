#!/usr/bin/env python3
"""
NEXUS Project Manager - Complete project management with templates, dependencies, and CI/CD
"""

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import yaml
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
import tempfile
import zipfile
import tarfile
from urllib.parse import urlparse
import requests

# Third-party imports
try:
    import toml
except ImportError:
    toml = None

try:
    import git
except ImportError:
    git = None


@dataclass
class ProjectTemplate:
    """Project template definition"""
    name: str
    description: str
    language: str
    framework: Optional[str] = None
    structure: Dict[str, Any] = field(default_factory=dict)
    dependencies: Dict[str, str] = field(default_factory=dict)
    dev_dependencies: Dict[str, str] = field(default_factory=dict)
    scripts: Dict[str, str] = field(default_factory=dict)
    config_files: Dict[str, str] = field(default_factory=dict)
    

@dataclass
class Dependency:
    """Project dependency"""
    name: str
    version: str
    type: str  # runtime, dev, peer, optional
    source: str  # npm, pip, cargo, maven, etc.
    

@dataclass
class BuildConfig:
    """Build configuration"""
    name: str
    command: str
    env: Dict[str, str] = field(default_factory=dict)
    pre_build: List[str] = field(default_factory=list)
    post_build: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    

@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    name: str
    provider: str  # aws, gcp, azure, heroku, vercel, netlify, docker
    environment: str  # dev, staging, prod
    config: Dict[str, Any] = field(default_factory=dict)
    secrets: List[str] = field(default_factory=list)
    

@dataclass
class CICDPipeline:
    """CI/CD pipeline configuration"""
    name: str
    provider: str  # github, gitlab, jenkins, circleci, travis
    triggers: List[str] = field(default_factory=list)
    stages: List[Dict[str, Any]] = field(default_factory=list)
    

class TemplateRegistry:
    """Registry of project templates"""
    
    def __init__(self):
        self.templates = self._load_builtin_templates()
        self.custom_templates_dir = Path.home() / ".nexus" / "project_templates"
        self.custom_templates_dir.mkdir(parents=True, exist_ok=True)
        self._load_custom_templates()
        
    def _load_builtin_templates(self) -> Dict[str, ProjectTemplate]:
        """Load built-in project templates"""
        return {
            "react-app": ProjectTemplate(
                name="react-app",
                description="React application with TypeScript",
                language="typescript",
                framework="react",
                structure={
                    "src": {
                        "components": {},
                        "pages": {},
                        "utils": {},
                        "App.tsx": "import React from 'react';\n\nfunction App() {\n  return <div>Hello NEXUS!</div>;\n}\n\nexport default App;",
                        "index.tsx": "import React from 'react';\nimport ReactDOM from 'react-dom';\nimport App from './App';\n\nReactDOM.render(<App />, document.getElementById('root'));",
                    },
                    "public": {
                        "index.html": '<!DOCTYPE html>\n<html>\n<head>\n  <title>NEXUS React App</title>\n</head>\n<body>\n  <div id="root"></div>\n</body>\n</html>'
                    },
                    "package.json": {},
                    "tsconfig.json": {},
                    ".gitignore": "node_modules/\nbuild/\n.env",
                },
                dependencies={
                    "react": "^18.0.0",
                    "react-dom": "^18.0.0",
                },
                dev_dependencies={
                    "@types/react": "^18.0.0",
                    "@types/react-dom": "^18.0.0",
                    "typescript": "^4.9.0",
                    "vite": "^4.0.0",
                    "@vitejs/plugin-react": "^3.0.0"
                },
                scripts={
                    "dev": "vite",
                    "build": "vite build",
                    "preview": "vite preview",
                    "test": "vitest"
                }
            ),
            
            "python-api": ProjectTemplate(
                name="python-api",
                description="Python REST API with FastAPI",
                language="python",
                framework="fastapi",
                structure={
                    "app": {
                        "__init__.py": "",
                        "main.py": 'from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get("/")\ndef read_root():\n    return {"Hello": "NEXUS"}',
                        "models.py": "from pydantic import BaseModel\n\n# Define your models here",
                        "routers": {
                            "__init__.py": "",
                        },
                        "services": {
                            "__init__.py": "",
                        },
                    },
                    "tests": {
                        "__init__.py": "",
                        "test_main.py": "def test_example():\n    assert True",
                    },
                    "requirements.txt": "fastapi\nuvicorn[standard]\npydantic\npytest",
                    ".env.example": "DATABASE_URL=postgresql://user:pass@localhost/db",
                    ".gitignore": "__pycache__/\n*.pyc\n.env\nvenv/",
                    "Dockerfile": "FROM python:3.11\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nCMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\"]"
                },
                scripts={
                    "dev": "uvicorn app.main:app --reload",
                    "test": "pytest",
                    "lint": "flake8 app tests",
                    "format": "black app tests"
                }
            ),
            
            "node-api": ProjectTemplate(
                name="node-api",
                description="Node.js REST API with Express",
                language="javascript",
                framework="express",
                structure={
                    "src": {
                        "index.js": "const express = require('express');\nconst app = express();\n\napp.get('/', (req, res) => {\n  res.json({ hello: 'NEXUS' });\n});\n\nconst PORT = process.env.PORT || 3000;\napp.listen(PORT, () => console.log(`Server running on port ${PORT}`));",
                        "routes": {
                            "index.js": "// Define routes here"
                        },
                        "models": {
                            "index.js": "// Define models here"
                        },
                        "middleware": {
                            "index.js": "// Define middleware here"
                        }
                    },
                    "tests": {
                        "index.test.js": "test('example test', () => {\n  expect(true).toBe(true);\n});"
                    },
                    "package.json": {},
                    ".gitignore": "node_modules/\n.env\ndist/",
                    ".env.example": "PORT=3000\nDATABASE_URL=mongodb://localhost:27017/nexus"
                },
                dependencies={
                    "express": "^4.18.0",
                    "dotenv": "^16.0.0",
                    "cors": "^2.8.5"
                },
                dev_dependencies={
                    "nodemon": "^2.0.0",
                    "jest": "^29.0.0",
                    "eslint": "^8.0.0"
                },
                scripts={
                    "start": "node src/index.js",
                    "dev": "nodemon src/index.js",
                    "test": "jest",
                    "lint": "eslint src"
                }
            ),
            
            "static-site": ProjectTemplate(
                name="static-site",
                description="Static website with modern build tools",
                language="html",
                framework=None,
                structure={
                    "src": {
                        "index.html": "<!DOCTYPE html>\n<html>\n<head>\n  <title>NEXUS Site</title>\n  <link rel=\"stylesheet\" href=\"styles/main.css\">\n</head>\n<body>\n  <h1>Welcome to NEXUS</h1>\n  <script src=\"scripts/main.js\"></script>\n</body>\n</html>",
                        "styles": {
                            "main.css": "body {\n  font-family: system-ui;\n  margin: 0;\n  padding: 20px;\n}"
                        },
                        "scripts": {
                            "main.js": "console.log('NEXUS loaded!');"
                        },
                        "images": {}
                    },
                    "dist": {},
                    ".gitignore": "dist/\nnode_modules/",
                    "package.json": {}
                },
                dev_dependencies={
                    "vite": "^4.0.0",
                    "sass": "^1.0.0"
                },
                scripts={
                    "dev": "vite",
                    "build": "vite build",
                    "preview": "vite preview"
                }
            )
        }
        
    def _load_custom_templates(self):
        """Load custom templates from disk"""
        for template_dir in self.custom_templates_dir.iterdir():
            if template_dir.is_dir():
                manifest_file = template_dir / "template.json"
                if manifest_file.exists():
                    with open(manifest_file) as f:
                        manifest = json.load(f)
                        template = ProjectTemplate(**manifest)
                        self.templates[template.name] = template
                        
    def get_template(self, name: str) -> Optional[ProjectTemplate]:
        """Get template by name"""
        return self.templates.get(name)
        
    def list_templates(self) -> List[ProjectTemplate]:
        """List all available templates"""
        return list(self.templates.values())
        
    def create_template(self, template: ProjectTemplate):
        """Create custom template"""
        template_dir = self.custom_templates_dir / template.name
        template_dir.mkdir(exist_ok=True)
        
        # Save manifest
        manifest = {
            "name": template.name,
            "description": template.description,
            "language": template.language,
            "framework": template.framework,
            "structure": template.structure,
            "dependencies": template.dependencies,
            "dev_dependencies": template.dev_dependencies,
            "scripts": template.scripts,
            "config_files": template.config_files
        }
        
        with open(template_dir / "template.json", 'w') as f:
            json.dump(manifest, f, indent=2)
            
        self.templates[template.name] = template
        

class DependencyManager:
    """Manage project dependencies across different package managers"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.package_managers = {
            "npm": NpmManager(project_path),
            "pip": PipManager(project_path),
            "cargo": CargoManager(project_path),
            "maven": MavenManager(project_path),
            "gradle": GradleManager(project_path),
            "composer": ComposerManager(project_path),
        }
        
    def detect_package_manager(self) -> Optional[str]:
        """Detect which package manager to use"""
        if (self.project_path / "package.json").exists():
            return "npm"
        elif (self.project_path / "requirements.txt").exists() or \
             (self.project_path / "setup.py").exists() or \
             (self.project_path / "pyproject.toml").exists():
            return "pip"
        elif (self.project_path / "Cargo.toml").exists():
            return "cargo"
        elif (self.project_path / "pom.xml").exists():
            return "maven"
        elif (self.project_path / "build.gradle").exists():
            return "gradle"
        elif (self.project_path / "composer.json").exists():
            return "composer"
        return None
        
    def install_dependencies(self, dev: bool = True) -> Tuple[bool, str]:
        """Install project dependencies"""
        pm_type = self.detect_package_manager()
        if not pm_type:
            return False, "No package manager detected"
            
        pm = self.package_managers.get(pm_type)
        if pm:
            return pm.install(dev)
        return False, f"Package manager {pm_type} not supported"
        
    def add_dependency(
        self,
        name: str,
        version: Optional[str] = None,
        dev: bool = False
    ) -> Tuple[bool, str]:
        """Add a dependency"""
        pm_type = self.detect_package_manager()
        if not pm_type:
            return False, "No package manager detected"
            
        pm = self.package_managers.get(pm_type)
        if pm:
            return pm.add(name, version, dev)
        return False, f"Package manager {pm_type} not supported"
        
    def update_dependencies(self) -> Tuple[bool, str]:
        """Update all dependencies"""
        pm_type = self.detect_package_manager()
        if not pm_type:
            return False, "No package manager detected"
            
        pm = self.package_managers.get(pm_type)
        if pm:
            return pm.update()
        return False, f"Package manager {pm_type} not supported"
        
    def audit_dependencies(self) -> Dict[str, Any]:
        """Audit dependencies for security vulnerabilities"""
        pm_type = self.detect_package_manager()
        if not pm_type:
            return {"error": "No package manager detected"}
            
        pm = self.package_managers.get(pm_type)
        if pm and hasattr(pm, 'audit'):
            return pm.audit()
        return {"error": f"Audit not supported for {pm_type}"}
        

class PackageManagerBase:
    """Base class for package managers"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        
    def install(self, dev: bool = True) -> Tuple[bool, str]:
        """Install dependencies"""
        raise NotImplementedError
        
    def add(self, name: str, version: Optional[str] = None, dev: bool = False) -> Tuple[bool, str]:
        """Add dependency"""
        raise NotImplementedError
        
    def update(self) -> Tuple[bool, str]:
        """Update dependencies"""
        raise NotImplementedError
        
    def run_command(self, cmd: List[str]) -> Tuple[bool, str]:
        """Run command and return success status and output"""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
            

class NpmManager(PackageManagerBase):
    """NPM package manager"""
    
    def install(self, dev: bool = True) -> Tuple[bool, str]:
        cmd = ["npm", "install"]
        if not dev:
            cmd.append("--production")
        return self.run_command(cmd)
        
    def add(self, name: str, version: Optional[str] = None, dev: bool = False) -> Tuple[bool, str]:
        pkg = f"{name}@{version}" if version else name
        cmd = ["npm", "install", pkg]
        if dev:
            cmd.append("--save-dev")
        return self.run_command(cmd)
        
    def update(self) -> Tuple[bool, str]:
        return self.run_command(["npm", "update"])
        
    def audit(self) -> Dict[str, Any]:
        success, output = self.run_command(["npm", "audit", "--json"])
        if success:
            try:
                return json.loads(output)
            except:
                pass
        return {"error": output}
        

class PipManager(PackageManagerBase):
    """Pip package manager"""
    
    def install(self, dev: bool = True) -> Tuple[bool, str]:
        requirements_file = self.project_path / "requirements.txt"
        if requirements_file.exists():
            return self.run_command([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
        
        # Try setup.py
        setup_file = self.project_path / "setup.py"
        if setup_file.exists():
            cmd = [sys.executable, "-m", "pip", "install", "-e", "."]
            if dev:
                cmd.append("[dev]")
            return self.run_command(cmd)
            
        # Try pyproject.toml
        pyproject_file = self.project_path / "pyproject.toml"
        if pyproject_file.exists():
            return self.run_command([sys.executable, "-m", "pip", "install", "-e", "."])
            
        return False, "No requirements file found"
        
    def add(self, name: str, version: Optional[str] = None, dev: bool = False) -> Tuple[bool, str]:
        pkg = f"{name}=={version}" if version else name
        success, output = self.run_command([sys.executable, "-m", "pip", "install", pkg])
        
        if success:
            # Update requirements.txt
            requirements_file = self.project_path / "requirements.txt"
            with open(requirements_file, 'a') as f:
                f.write(f"\n{pkg}")
                
        return success, output
        
    def update(self) -> Tuple[bool, str]:
        return self.run_command([sys.executable, "-m", "pip", "install", "--upgrade", "-r", "requirements.txt"])
        

class CargoManager(PackageManagerBase):
    """Cargo package manager for Rust"""
    
    def install(self, dev: bool = True) -> Tuple[bool, str]:
        return self.run_command(["cargo", "build"])
        
    def add(self, name: str, version: Optional[str] = None, dev: bool = False) -> Tuple[bool, str]:
        cmd = ["cargo", "add", name]
        if version:
            cmd.append(f"--vers={version}")
        if dev:
            cmd.append("--dev")
        return self.run_command(cmd)
        
    def update(self) -> Tuple[bool, str]:
        return self.run_command(["cargo", "update"])
        

class MavenManager(PackageManagerBase):
    """Maven package manager for Java"""
    
    def install(self, dev: bool = True) -> Tuple[bool, str]:
        return self.run_command(["mvn", "install"])
        
    def add(self, name: str, version: Optional[str] = None, dev: bool = False) -> Tuple[bool, str]:
        # Maven doesn't have a simple add command, would need to edit pom.xml
        return False, "Manual pom.xml editing required"
        
    def update(self) -> Tuple[bool, str]:
        return self.run_command(["mvn", "versions:use-latest-versions"])
        

class GradleManager(PackageManagerBase):
    """Gradle package manager"""
    
    def install(self, dev: bool = True) -> Tuple[bool, str]:
        return self.run_command(["gradle", "build"])
        
    def add(self, name: str, version: Optional[str] = None, dev: bool = False) -> Tuple[bool, str]:
        # Gradle doesn't have a simple add command
        return False, "Manual build.gradle editing required"
        
    def update(self) -> Tuple[bool, str]:
        return self.run_command(["gradle", "dependencies", "--refresh-dependencies"])
        

class ComposerManager(PackageManagerBase):
    """Composer package manager for PHP"""
    
    def install(self, dev: bool = True) -> Tuple[bool, str]:
        cmd = ["composer", "install"]
        if not dev:
            cmd.append("--no-dev")
        return self.run_command(cmd)
        
    def add(self, name: str, version: Optional[str] = None, dev: bool = False) -> Tuple[bool, str]:
        pkg = f"{name}:{version}" if version else name
        cmd = ["composer", "require", pkg]
        if dev:
            cmd.insert(2, "--dev")
        return self.run_command(cmd)
        
    def update(self) -> Tuple[bool, str]:
        return self.run_command(["composer", "update"])
        

class BuildSystem:
    """Build system management"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.build_configs: Dict[str, BuildConfig] = {}
        self._load_configs()
        
    def _load_configs(self):
        """Load build configurations"""
        # Check for common build config files
        nexus_config = self.project_path / ".nexus" / "build.json"
        if nexus_config.exists():
            with open(nexus_config) as f:
                data = json.load(f)
                for name, config in data.items():
                    self.build_configs[name] = BuildConfig(name=name, **config)
                    
    def add_config(self, config: BuildConfig):
        """Add build configuration"""
        self.build_configs[config.name] = config
        self._save_configs()
        
    def _save_configs(self):
        """Save build configurations"""
        nexus_dir = self.project_path / ".nexus"
        nexus_dir.mkdir(exist_ok=True)
        
        data = {}
        for name, config in self.build_configs.items():
            data[name] = {
                "command": config.command,
                "env": config.env,
                "pre_build": config.pre_build,
                "post_build": config.post_build,
                "artifacts": config.artifacts
            }
            
        with open(nexus_dir / "build.json", 'w') as f:
            json.dump(data, f, indent=2)
            
    async def build(self, config_name: str) -> Tuple[bool, str]:
        """Run build configuration"""
        config = self.build_configs.get(config_name)
        if not config:
            return False, f"Build config '{config_name}' not found"
            
        output = []
        
        # Set environment
        env = os.environ.copy()
        env.update(config.env)
        
        # Run pre-build commands
        for cmd in config.pre_build:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=self.project_path,
                env=env,
                capture_output=True,
                text=True
            )
            output.append(f"Pre-build: {cmd}")
            output.append(result.stdout)
            if result.returncode != 0:
                output.append(result.stderr)
                return False, "\n".join(output)
                
        # Run main build command
        result = subprocess.run(
            config.command,
            shell=True,
            cwd=self.project_path,
            env=env,
            capture_output=True,
            text=True
        )
        output.append(f"Build: {config.command}")
        output.append(result.stdout)
        
        if result.returncode != 0:
            output.append(result.stderr)
            return False, "\n".join(output)
            
        # Run post-build commands
        for cmd in config.post_build:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=self.project_path,
                env=env,
                capture_output=True,
                text=True
            )
            output.append(f"Post-build: {cmd}")
            output.append(result.stdout)
            if result.returncode != 0:
                output.append(result.stderr)
                
        # Collect artifacts
        artifacts = []
        for pattern in config.artifacts:
            artifacts.extend(self.project_path.glob(pattern))
            
        output.append(f"\nArtifacts: {len(artifacts)} files")
        
        return True, "\n".join(output)
        

class DeploymentManager:
    """Manage deployments to various platforms"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.deployments: Dict[str, DeploymentConfig] = {}
        self._load_deployments()
        
    def _load_deployments(self):
        """Load deployment configurations"""
        nexus_config = self.project_path / ".nexus" / "deploy.json"
        if nexus_config.exists():
            with open(nexus_config) as f:
                data = json.load(f)
                for name, config in data.items():
                    self.deployments[name] = DeploymentConfig(name=name, **config)
                    
    def add_deployment(self, deployment: DeploymentConfig):
        """Add deployment configuration"""
        self.deployments[deployment.name] = deployment
        self._save_deployments()
        
    def _save_deployments(self):
        """Save deployment configurations"""
        nexus_dir = self.project_path / ".nexus"
        nexus_dir.mkdir(exist_ok=True)
        
        data = {}
        for name, deployment in self.deployments.items():
            data[name] = {
                "provider": deployment.provider,
                "environment": deployment.environment,
                "config": deployment.config,
                "secrets": deployment.secrets
            }
            
        with open(nexus_dir / "deploy.json", 'w') as f:
            json.dump(data, f, indent=2)
            
    async def deploy(self, deployment_name: str) -> Tuple[bool, str]:
        """Deploy to specified target"""
        deployment = self.deployments.get(deployment_name)
        if not deployment:
            return False, f"Deployment '{deployment_name}' not found"
            
        # Route to appropriate deployer
        if deployment.provider == "docker":
            return await self._deploy_docker(deployment)
        elif deployment.provider == "aws":
            return await self._deploy_aws(deployment)
        elif deployment.provider == "vercel":
            return await self._deploy_vercel(deployment)
        elif deployment.provider == "netlify":
            return await self._deploy_netlify(deployment)
        elif deployment.provider == "heroku":
            return await self._deploy_heroku(deployment)
        else:
            return False, f"Provider '{deployment.provider}' not supported"
            
    async def _deploy_docker(self, deployment: DeploymentConfig) -> Tuple[bool, str]:
        """Deploy using Docker"""
        image_name = deployment.config.get("image_name", "nexus-app")
        registry = deployment.config.get("registry")
        
        # Build image
        result = subprocess.run(
            ["docker", "build", "-t", image_name, "."],
            cwd=self.project_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return False, f"Docker build failed: {result.stderr}"
            
        # Push to registry if specified
        if registry:
            tag = f"{registry}/{image_name}"
            subprocess.run(["docker", "tag", image_name, tag])
            result = subprocess.run(
                ["docker", "push", tag],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return False, f"Docker push failed: {result.stderr}"
                
        return True, f"Docker image {image_name} deployed"
        
    async def _deploy_vercel(self, deployment: DeploymentConfig) -> Tuple[bool, str]:
        """Deploy to Vercel"""
        # Would implement Vercel deployment
        return False, "Vercel deployment not yet implemented"
        
    async def _deploy_netlify(self, deployment: DeploymentConfig) -> Tuple[bool, str]:
        """Deploy to Netlify"""
        # Would implement Netlify deployment
        return False, "Netlify deployment not yet implemented"
        
    async def _deploy_heroku(self, deployment: DeploymentConfig) -> Tuple[bool, str]:
        """Deploy to Heroku"""
        # Would implement Heroku deployment
        return False, "Heroku deployment not yet implemented"
        
    async def _deploy_aws(self, deployment: DeploymentConfig) -> Tuple[bool, str]:
        """Deploy to AWS"""
        # Would implement AWS deployment
        return False, "AWS deployment not yet implemented"
        

class CICDManager:
    """Manage CI/CD pipelines"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.pipelines: Dict[str, CICDPipeline] = {}
        
    def generate_github_actions(self, pipeline: CICDPipeline) -> str:
        """Generate GitHub Actions workflow"""
        workflow = {
            "name": pipeline.name,
            "on": {},
            "jobs": {}
        }
        
        # Set triggers
        for trigger in pipeline.triggers:
            if trigger == "push":
                workflow["on"]["push"] = {"branches": ["main", "master"]}
            elif trigger == "pull_request":
                workflow["on"]["pull_request"] = {"branches": ["main", "master"]}
            elif trigger.startswith("schedule:"):
                cron = trigger.split(":", 1)[1]
                workflow["on"]["schedule"] = [{"cron": cron}]
                
        # Generate jobs from stages
        for i, stage in enumerate(pipeline.stages):
            job_name = stage.get("name", f"stage_{i}")
            job = {
                "runs-on": stage.get("runner", "ubuntu-latest"),
                "steps": []
            }
            
            # Checkout code
            job["steps"].append({
                "uses": "actions/checkout@v3"
            })
            
            # Setup environment
            if "setup" in stage:
                for setup in stage["setup"]:
                    job["steps"].append(setup)
                    
            # Run commands
            if "run" in stage:
                for cmd in stage["run"]:
                    job["steps"].append({
                        "name": f"Run: {cmd[:50]}",
                        "run": cmd
                    })
                    
            workflow["jobs"][job_name] = job
            
        return yaml.dump(workflow, default_flow_style=False)
        
    def generate_gitlab_ci(self, pipeline: CICDPipeline) -> str:
        """Generate GitLab CI configuration"""
        config = {
            "stages": [s.get("name", f"stage_{i}") for i, s in enumerate(pipeline.stages)]
        }
        
        for stage in pipeline.stages:
            job_name = stage.get("name", "job")
            config[job_name] = {
                "stage": job_name,
                "script": stage.get("run", [])
            }
            
            if "only" in stage:
                config[job_name]["only"] = stage["only"]
                
        return yaml.dump(config, default_flow_style=False)
        

class SecretManager:
    """Manage project secrets and environment variables"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.env_file = project_path / ".env"
        self.env_example_file = project_path / ".env.example"
        self.secrets: Dict[str, str] = {}
        self._load_secrets()
        
    def _load_secrets(self):
        """Load secrets from .env file"""
        if self.env_file.exists():
            with open(self.env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.secrets[key.strip()] = value.strip()
                        
    def set_secret(self, key: str, value: str):
        """Set a secret"""
        self.secrets[key] = value
        self._save_secrets()
        
        # Update .env.example with key only
        self._update_env_example(key)
        
    def _save_secrets(self):
        """Save secrets to .env file"""
        with open(self.env_file, 'w') as f:
            for key, value in sorted(self.secrets.items()):
                f.write(f"{key}={value}\n")
                
    def _update_env_example(self, key: str):
        """Update .env.example with new key"""
        example_keys = set()
        
        if self.env_example_file.exists():
            with open(self.env_example_file) as f:
                for line in f:
                    if '=' in line:
                        k = line.split('=', 1)[0].strip()
                        example_keys.add(k)
                        
        example_keys.add(key)
        
        with open(self.env_example_file, 'w') as f:
            for k in sorted(example_keys):
                f.write(f"{k}=\n")
                
    def get_secret(self, key: str) -> Optional[str]:
        """Get a secret value"""
        return self.secrets.get(key)
        
    def list_secrets(self) -> List[str]:
        """List secret keys (not values)"""
        return list(self.secrets.keys())
        

class NexusProjectManager:
    """Complete project management system"""
    
    def __init__(self):
        self.template_registry = TemplateRegistry()
        self.projects_dir = Path.home() / "nexus_projects"
        self.projects_dir.mkdir(exist_ok=True)
        
    def create_project(
        self,
        name: str,
        template_name: Optional[str] = None,
        path: Optional[Path] = None
    ) -> Tuple[bool, str, Optional[Path]]:
        """Create new project"""
        # Determine project path
        project_path = path or (self.projects_dir / name)
        
        if project_path.exists():
            return False, f"Path {project_path} already exists", None
            
        # Get template
        if template_name:
            template = self.template_registry.get_template(template_name)
            if not template:
                return False, f"Template '{template_name}' not found", None
        else:
            # Use static site as default
            template = self.template_registry.get_template("static-site")
            
        # Create project structure
        project_path.mkdir(parents=True)
        
        try:
            # Create directory structure
            self._create_structure(project_path, template.structure)
            
            # Initialize package.json for Node projects
            if template.language in ["javascript", "typescript"]:
                self._create_package_json(
                    project_path,
                    name,
                    template
                )
                
            # Initialize git repository
            if git:
                repo = git.Repo.init(project_path)
                
                # Create initial commit
                repo.index.add("*")
                repo.index.commit("Initial commit")
                
            # Install dependencies
            if template.dependencies or template.dev_dependencies:
                dep_manager = DependencyManager(project_path)
                dep_manager.install_dependencies()
                
            return True, f"Project '{name}' created successfully", project_path
            
        except Exception as e:
            # Cleanup on failure
            if project_path.exists():
                shutil.rmtree(project_path)
            return False, f"Failed to create project: {e}", None
            
    def _create_structure(self, base_path: Path, structure: Dict[str, Any]):
        """Create directory structure from template"""
        for name, content in structure.items():
            path = base_path / name
            
            if isinstance(content, dict):
                # It's a directory
                path.mkdir(exist_ok=True)
                self._create_structure(path, content)
            else:
                # It's a file
                path.write_text(content)
                
    def _create_package_json(self, project_path: Path, name: str, template: ProjectTemplate):
        """Create package.json file"""
        package_json = {
            "name": name,
            "version": "0.1.0",
            "description": template.description,
            "scripts": template.scripts,
            "dependencies": template.dependencies,
            "devDependencies": template.dev_dependencies
        }
        
        with open(project_path / "package.json", 'w') as f:
            json.dump(package_json, f, indent=2)
            
    def scaffold_component(
        self,
        project_path: Path,
        component_type: str,
        name: str
    ) -> Tuple[bool, str]:
        """Scaffold a new component in existing project"""
        # Detect project type
        if (project_path / "package.json").exists():
            with open(project_path / "package.json") as f:
                package = json.load(f)
                
            # Check for React
            if "react" in package.get("dependencies", {}):
                return self._scaffold_react_component(project_path, component_type, name)
                
        return False, "Component scaffolding not supported for this project type"
        
    def _scaffold_react_component(
        self,
        project_path: Path,
        component_type: str,
        name: str
    ) -> Tuple[bool, str]:
        """Scaffold React component"""
        components_dir = project_path / "src" / "components"
        components_dir.mkdir(parents=True, exist_ok=True)
        
        component_dir = components_dir / name
        component_dir.mkdir(exist_ok=True)
        
        # Create component file
        component_content = f"""import React from 'react';
import './{name}.css';

interface {name}Props {{
  // Define props here
}}

const {name}: React.FC<{name}Props> = (props) => {{
  return (
    <div className="{name.lower()}">
      <h2>{name}</h2>
      {{/* Component content */}}
    </div>
  );
}};

export default {name};
"""
        
        (component_dir / f"{name}.tsx").write_text(component_content)
        
        # Create CSS file
        css_content = f""".{name.lower()} {{
  /* Component styles */
}}
"""
        (component_dir / f"{name}.css").write_text(css_content)
        
        # Create test file
        test_content = f"""import React from 'react';
import {{ render, screen }} from '@testing-library/react';
import {name} from './{name}';

describe('{name}', () => {{
  it('renders without crashing', () => {{
    render(<{name} />);
    expect(screen.getByText('{name}')).toBeInTheDocument();
  }});
}});
"""
        (component_dir / f"{name}.test.tsx").write_text(test_content)
        
        # Create index file
        (component_dir / "index.ts").write_text(f"export {{ default }} from './{name}';\n")
        
        return True, f"React component '{name}' scaffolded successfully"


async def main():
    """Test project manager"""
    manager = NexusProjectManager()
    
    # List available templates
    print("Available templates:")
    for template in manager.template_registry.list_templates():
        print(f"  - {template.name}: {template.description}")
        
    # Create test project
    print("\nCreating test project...")
    success, message, project_path = manager.create_project(
        "test-nexus-app",
        "react-app"
    )
    
    print(f"Result: {message}")
    
    if success and project_path:
        # Test dependency manager
        dep_manager = DependencyManager(project_path)
        pm_type = dep_manager.detect_package_manager()
        print(f"\nDetected package manager: {pm_type}")
        
        # Test build system
        build_system = BuildSystem(project_path)
        build_system.add_config(BuildConfig(
            name="production",
            command="npm run build",
            env={"NODE_ENV": "production"},
            artifacts=["dist/**/*"]
        ))
        
        # Test secret manager
        secret_manager = SecretManager(project_path)
        secret_manager.set_secret("API_KEY", "test-key-123")
        print(f"\nSecrets configured: {secret_manager.list_secrets()}")
        
        # Cleanup
        shutil.rmtree(project_path)
        print("\nTest project cleaned up")


if __name__ == "__main__":
    asyncio.run(main())