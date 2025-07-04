#!/usr/bin/env python3
"""
NEXUS Production Launcher - Single Binary Compilation & Management
Provides auto-update, dependency checking, and production deployment
"""

import asyncio
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import requests
import semver
import psutil
import yaml

# Try to import optional dependencies
try:
    import PyInstaller.__main__ as pyinstaller
    HAS_PYINSTALLER = True
except ImportError:
    HAS_PYINSTALLER = False

try:
    import nuitka
    HAS_NUITKA = True
except ImportError:
    HAS_NUITKA = False


class SystemRequirements:
    """System requirements validation"""
    
    MIN_PYTHON_VERSION = (3, 9)
    MIN_MEMORY_GB = 4
    MIN_DISK_GB = 10
    REQUIRED_PORTS = [8080, 5555, 9090]  # API, ZMQ, Metrics
    
    @classmethod
    def check_python_version(cls) -> Tuple[bool, str]:
        """Check Python version"""
        current = sys.version_info[:2]
        if current >= cls.MIN_PYTHON_VERSION:
            return True, f"Python {current[0]}.{current[1]} OK"
        return False, f"Python {cls.MIN_PYTHON_VERSION[0]}.{cls.MIN_PYTHON_VERSION[1]}+ required"
    
    @classmethod
    def check_memory(cls) -> Tuple[bool, str]:
        """Check available memory"""
        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb >= cls.MIN_MEMORY_GB:
            return True, f"Memory {memory_gb:.1f}GB OK"
        return False, f"At least {cls.MIN_MEMORY_GB}GB RAM required"
    
    @classmethod
    def check_disk_space(cls) -> Tuple[bool, str]:
        """Check available disk space"""
        disk_gb = psutil.disk_usage('.').free / (1024**3)
        if disk_gb >= cls.MIN_DISK_GB:
            return True, f"Disk space {disk_gb:.1f}GB OK"
        return False, f"At least {cls.MIN_DISK_GB}GB free space required"
    
    @classmethod
    def check_ports(cls) -> List[Tuple[bool, str]]:
        """Check if required ports are available"""
        results = []
        for port in cls.REQUIRED_PORTS:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('', port))
                sock.close()
                results.append((True, f"Port {port} available"))
            except OSError:
                results.append((False, f"Port {port} in use"))
        return results
    
    @classmethod
    def check_dependencies(cls) -> List[Tuple[bool, str]]:
        """Check external dependencies"""
        dependencies = {
            'redis-server': 'Redis',
            'consul': 'Consul',
            'etcd': 'etcd',
            'docker': 'Docker (optional)',
            'git': 'Git'
        }
        
        results = []
        for cmd, name in dependencies.items():
            if shutil.which(cmd):
                results.append((True, f"{name} found"))
            else:
                optional = "(optional)" in name
                results.append((not optional, f"{name} not found"))
        
        return results
    
    @classmethod
    def validate_all(cls) -> Tuple[bool, List[str]]:
        """Validate all system requirements"""
        errors = []
        warnings = []
        
        # Python version
        ok, msg = cls.check_python_version()
        if not ok:
            errors.append(msg)
        
        # Memory
        ok, msg = cls.check_memory()
        if not ok:
            warnings.append(msg)
        
        # Disk space
        ok, msg = cls.check_disk_space()
        if not ok:
            errors.append(msg)
        
        # Ports
        for ok, msg in cls.check_ports():
            if not ok:
                warnings.append(msg)
        
        # Dependencies
        for ok, msg in cls.check_dependencies():
            if not ok:
                if "optional" in msg.lower():
                    warnings.append(msg)
                else:
                    errors.append(msg)
        
        return len(errors) == 0, errors + warnings


class BinaryBuilder:
    """Build NEXUS as a single binary"""
    
    def __init__(self, source_dir: Path, output_dir: Path):
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def build_pyinstaller(self) -> Path:
        """Build using PyInstaller"""
        if not HAS_PYINSTALLER:
            raise RuntimeError("PyInstaller not installed")
        
        spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['{self.source_dir / "nexus_launcher.py"}'],
    pathex=['{self.source_dir}'],
    binaries=[],
    datas=[
        ('{self.source_dir / "nexus_production_config.yaml"}', '.'),
        ('{self.source_dir / "nexus_plugins"}', 'nexus_plugins'),
    ],
    hiddenimports=[
        'nexus_integration_core',
        'nexus_enhanced_manus',
        'nexus_unified_tools',
        'nexus_memory_core',
        'nexus_web_scraper',
        'nexus_voice_control',
        'nexus_vision_processor',
        'aiohttp',
        'graphene',
        'msgpack',
        'zmq',
        'redis',
        'consul',
        'etcd3',
        'prometheus_client',
        'opentelemetry',
        'grpc',
        'jwt',
        'yaml',
        'psutil'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='nexus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
        
        spec_file = self.output_dir / "nexus.spec"
        spec_file.write_text(spec_content)
        
        # Run PyInstaller
        pyinstaller.run([
            str(spec_file),
            '--distpath', str(self.output_dir),
            '--workpath', str(self.output_dir / 'build'),
            '--clean',
            '--noconfirm'
        ])
        
        binary_name = 'nexus.exe' if platform.system() == 'Windows' else 'nexus'
        return self.output_dir / binary_name
    
    def build_nuitka(self) -> Path:
        """Build using Nuitka (alternative)"""
        if not HAS_NUITKA:
            raise RuntimeError("Nuitka not installed")
        
        cmd = [
            sys.executable, '-m', 'nuitka',
            '--standalone',
            '--onefile',
            '--follow-imports',
            '--include-package=nexus_integration_core',
            '--include-package=nexus_enhanced_manus',
            '--include-package=nexus_unified_tools',
            '--include-data-files=nexus_production_config.yaml=.',
            '--include-data-dir=nexus_plugins=nexus_plugins',
            '--output-dir=' + str(self.output_dir),
            str(self.source_dir / 'nexus_launcher.py')
        ]
        
        subprocess.run(cmd, check=True)
        
        binary_name = 'nexus_launcher.exe' if platform.system() == 'Windows' else 'nexus_launcher'
        return self.output_dir / binary_name
    
    def create_archive(self, binary_path: Path, version: str) -> Path:
        """Create distribution archive"""
        system = platform.system().lower()
        arch = platform.machine().lower()
        
        archive_name = f"nexus-{version}-{system}-{arch}"
        
        # Create temporary directory for archive contents
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Copy binary
            shutil.copy2(binary_path, temp_path / binary_path.name)
            
            # Copy configuration
            shutil.copy2(
                self.source_dir / 'nexus_production_config.yaml',
                temp_path / 'nexus_production_config.yaml'
            )
            
            # Copy plugins directory
            if (self.source_dir / 'nexus_plugins').exists():
                shutil.copytree(
                    self.source_dir / 'nexus_plugins',
                    temp_path / 'nexus_plugins'
                )
            
            # Create README
            readme_content = f"""
NEXUS Mind Repository v{version}
================================

Installation:
1. Extract this archive
2. Run ./nexus (or nexus.exe on Windows)

First Run:
The setup wizard will guide you through initial configuration.

Requirements:
- Redis server (for state management)
- Consul or etcd (for service discovery)
- 4GB+ RAM
- 10GB+ free disk space

Documentation: https://nexus.dev/docs
Support: support@nexus.dev
"""
            (temp_path / 'README.txt').write_text(readme_content)
            
            # Create archive
            if system == 'windows':
                archive_path = self.output_dir / f"{archive_name}.zip"
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for file in temp_path.rglob('*'):
                        if file.is_file():
                            zf.write(file, file.relative_to(temp_path))
            else:
                archive_path = self.output_dir / f"{archive_name}.tar.gz"
                with tarfile.open(archive_path, 'w:gz') as tf:
                    tf.add(temp_path, arcname=archive_name)
            
            return archive_path


class AutoUpdater:
    """Auto-update system for NEXUS"""
    
    def __init__(self, current_version: str, update_url: str):
        self.current_version = current_version
        self.update_url = update_url
        self.update_dir = Path.home() / '.nexus' / 'updates'
        self.update_dir.mkdir(parents=True, exist_ok=True)
    
    async def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """Check for available updates"""
        try:
            response = requests.get(f"{self.update_url}/latest.json", timeout=10)
            response.raise_for_status()
            
            update_info = response.json()
            latest_version = update_info['version']
            
            if semver.compare(latest_version, self.current_version) > 0:
                return update_info
            
            return None
        except Exception as e:
            print(f"Update check failed: {e}")
            return None
    
    async def download_update(self, update_info: Dict[str, Any]) -> Path:
        """Download update package"""
        version = update_info['version']
        system = platform.system().lower()
        arch = platform.machine().lower()
        
        # Find matching download
        download_url = None
        for download in update_info['downloads']:
            if download['platform'] == system and download['arch'] == arch:
                download_url = download['url']
                expected_hash = download['sha256']
                break
        
        if not download_url:
            raise ValueError(f"No update available for {system}-{arch}")
        
        # Download file
        filename = download_url.split('/')[-1]
        download_path = self.update_dir / filename
        
        print(f"Downloading update {version}...")
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        # Download with progress
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        progress = (downloaded / total_size) * 100
                        print(f"\rProgress: {progress:.1f}%", end='', flush=True)
        
        print()  # New line after progress
        
        # Verify hash
        actual_hash = self._calculate_hash(download_path)
        if actual_hash != expected_hash:
            download_path.unlink()
            raise ValueError("Update verification failed")
        
        return download_path
    
    def _calculate_hash(self, filepath: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    async def apply_update(self, update_path: Path) -> bool:
        """Apply downloaded update"""
        try:
            # Extract update
            extract_dir = self.update_dir / 'extract'
            extract_dir.mkdir(exist_ok=True)
            
            if update_path.suffix == '.zip':
                with zipfile.ZipFile(update_path, 'r') as zf:
                    zf.extractall(extract_dir)
            else:
                with tarfile.open(update_path, 'r:gz') as tf:
                    tf.extractall(extract_dir)
            
            # Find binary
            binary_name = 'nexus.exe' if platform.system() == 'Windows' else 'nexus'
            new_binary = None
            
            for file in extract_dir.rglob(binary_name):
                new_binary = file
                break
            
            if not new_binary:
                raise ValueError("Binary not found in update package")
            
            # Replace current binary
            current_binary = Path(sys.argv[0]).resolve()
            backup_path = current_binary.with_suffix('.backup')
            
            # Backup current version
            shutil.copy2(current_binary, backup_path)
            
            # Copy new version
            shutil.copy2(new_binary, current_binary)
            
            # Make executable on Unix
            if platform.system() != 'Windows':
                os.chmod(current_binary, 0o755)
            
            # Cleanup
            shutil.rmtree(extract_dir)
            update_path.unlink()
            
            print("Update applied successfully. Please restart NEXUS.")
            return True
            
        except Exception as e:
            print(f"Update failed: {e}")
            return False


class SetupWizard:
    """First-run setup wizard"""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = {}
    
    async def run(self) -> Dict[str, Any]:
        """Run interactive setup wizard"""
        print("\n" + "="*60)
        print("NEXUS Mind Repository - Setup Wizard")
        print("="*60 + "\n")
        
        # Basic configuration
        print("Basic Configuration")
        print("-" * 20)
        
        self.config['nexus'] = {
            'version': '1.0.0',
            'mode': await self._prompt_choice(
                "Deployment mode",
                ['production', 'development'],
                'production'
            )
        }
        
        # API configuration
        print("\nAPI Configuration")
        print("-" * 20)
        
        self.config['nexus']['api'] = {
            'host': await self._prompt_string("API host", "0.0.0.0"),
            'port': await self._prompt_int("API port", 8080)
        }
        
        # Service discovery
        print("\nService Discovery")
        print("-" * 20)
        
        backend = await self._prompt_choice(
            "Service discovery backend",
            ['consul', 'etcd', 'memory'],
            'consul'
        )
        
        if backend == 'consul':
            self.config['nexus']['service_discovery'] = {
                'backend': 'consul',
                'host': await self._prompt_string("Consul host", "localhost"),
                'port': await self._prompt_int("Consul port", 8500)
            }
        elif backend == 'etcd':
            self.config['nexus']['service_discovery'] = {
                'backend': 'etcd',
                'host': await self._prompt_string("etcd host", "localhost"),
                'port': await self._prompt_int("etcd port", 2379)
            }
        else:
            self.config['nexus']['service_discovery'] = {'backend': 'memory'}
        
        # State management
        print("\nState Management")
        print("-" * 20)
        
        state_backend = await self._prompt_choice(
            "State backend",
            ['redis', 'etcd', 'memory'],
            'redis'
        )
        
        if state_backend == 'redis':
            self.config['nexus']['state'] = {
                'backend': 'redis',
                'url': await self._prompt_string(
                    "Redis URL",
                    "redis://localhost:6379"
                )
            }
        elif state_backend == 'etcd':
            self.config['nexus']['state'] = {
                'backend': 'etcd',
                'host': await self._prompt_string("etcd host", "localhost"),
                'port': await self._prompt_int("etcd port", 2379)
            }
        else:
            self.config['nexus']['state'] = {'backend': 'memory'}
        
        # Security
        print("\nSecurity Configuration")
        print("-" * 20)
        
        self.config['nexus']['security'] = {
            'auth_required': await self._prompt_bool("Enable authentication", True),
            'encryption': 'aes256',
            'tls_version': '1.3'
        }
        
        if self.config['nexus']['security']['auth_required']:
            secret = await self._prompt_string(
                "JWT secret (leave empty to generate)",
                ""
            )
            if not secret:
                import secrets
                secret = secrets.token_urlsafe(32)
                print(f"Generated secret: {secret}")
            self.config['nexus']['security']['jwt_secret'] = secret
        
        # Features
        print("\nFeature Configuration")
        print("-" * 20)
        
        self.config['nexus']['features'] = {
            'voice': 'enabled' if await self._prompt_bool("Enable voice control", True) else 'disabled',
            'vision': 'enabled' if await self._prompt_bool("Enable vision processing", True) else 'disabled',
            'learning': 'enabled' if await self._prompt_bool("Enable self-learning", True) else 'disabled'
        }
        
        # Monitoring
        print("\nMonitoring Configuration")
        print("-" * 20)
        
        enable_monitoring = await self._prompt_bool("Enable monitoring", True)
        
        if enable_monitoring:
            self.config['nexus']['monitoring'] = {
                'metrics': {
                    'enabled': True,
                    'port': await self._prompt_int("Metrics port", 9090)
                },
                'tracing': {
                    'enabled': await self._prompt_bool("Enable tracing", True),
                    'endpoint': await self._prompt_string(
                        "OpenTelemetry endpoint",
                        "localhost:4317"
                    )
                },
                'logs': {
                    'backend': await self._prompt_choice(
                        "Logs backend",
                        ['elasticsearch', 'file', 'console'],
                        'file'
                    )
                }
            }
        else:
            self.config['nexus']['monitoring'] = {
                'metrics': {'enabled': False},
                'tracing': {'enabled': False},
                'logs': {'backend': 'console'}
            }
        
        # Core settings
        self.config['nexus']['core'] = {
            'workers': 'auto',
            'max_memory': '16GB',
            'log_level': await self._prompt_choice(
                "Log level",
                ['debug', 'info', 'warning', 'error'],
                'info'
            )
        }
        
        # Save configuration
        print("\nSaving configuration...")
        self.save_config()
        
        print("\nSetup complete! Configuration saved to:", self.config_path)
        return self.config
    
    async def _prompt_string(self, prompt: str, default: str = "") -> str:
        """Prompt for string input"""
        if default:
            response = input(f"{prompt} [{default}]: ").strip()
            return response if response else default
        else:
            while True:
                response = input(f"{prompt}: ").strip()
                if response:
                    return response
                print("Value required")
    
    async def _prompt_int(self, prompt: str, default: int) -> int:
        """Prompt for integer input"""
        while True:
            response = input(f"{prompt} [{default}]: ").strip()
            if not response:
                return default
            try:
                return int(response)
            except ValueError:
                print("Please enter a valid number")
    
    async def _prompt_bool(self, prompt: str, default: bool) -> bool:
        """Prompt for boolean input"""
        default_str = "Y" if default else "N"
        while True:
            response = input(f"{prompt} [{default_str}]: ").strip().upper()
            if not response:
                return default
            if response in ['Y', 'YES']:
                return True
            elif response in ['N', 'NO']:
                return False
            print("Please enter Y or N")
    
    async def _prompt_choice(self, prompt: str, choices: List[str], default: str) -> str:
        """Prompt for choice selection"""
        print(f"\n{prompt}:")
        for i, choice in enumerate(choices, 1):
            marker = "*" if choice == default else " "
            print(f"  {marker} {i}. {choice}")
        
        while True:
            response = input(f"Select option [1-{len(choices)}]: ").strip()
            if not response:
                return default
            try:
                idx = int(response) - 1
                if 0 <= idx < len(choices):
                    return choices[idx]
            except ValueError:
                pass
            print(f"Please enter a number between 1 and {len(choices)}")
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)


class MigrationManager:
    """Handle migration from development to production"""
    
    def __init__(self, dev_dir: Path, prod_dir: Path):
        self.dev_dir = dev_dir
        self.prod_dir = prod_dir
        self.prod_dir.mkdir(parents=True, exist_ok=True)
    
    async def migrate(self) -> bool:
        """Migrate from development environment"""
        print("Migrating from development environment...")
        
        try:
            # Migrate configuration
            dev_config = self.dev_dir / 'nexus_config.yaml'
            if dev_config.exists():
                shutil.copy2(dev_config, self.prod_dir / 'nexus_production_config.yaml')
                print("✓ Configuration migrated")
            
            # Migrate state
            dev_state = self.dev_dir / 'nexus_state.json'
            if dev_state.exists():
                shutil.copy2(dev_state, self.prod_dir / 'nexus_state.json')
                print("✓ State migrated")
            
            # Migrate plugins
            dev_plugins = self.dev_dir / 'nexus_plugins'
            if dev_plugins.exists():
                shutil.copytree(
                    dev_plugins,
                    self.prod_dir / 'nexus_plugins',
                    dirs_exist_ok=True
                )
                print("✓ Plugins migrated")
            
            # Migrate databases
            for db_file in self.dev_dir.glob('*.db'):
                shutil.copy2(db_file, self.prod_dir / db_file.name)
                print(f"✓ Database {db_file.name} migrated")
            
            return True
            
        except Exception as e:
            print(f"Migration failed: {e}")
            return False


class BackupManager:
    """Backup and restore functionality"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.backup_dir = data_dir / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_backup(self, name: Optional[str] = None) -> Path:
        """Create a backup of current state"""
        if not name:
            name = datetime.now().strftime("backup_%Y%m%d_%H%M%S")
        
        backup_path = self.backup_dir / f"{name}.tar.gz"
        
        print(f"Creating backup: {name}")
        
        with tarfile.open(backup_path, 'w:gz') as tf:
            # Backup configuration
            config_file = self.data_dir / 'nexus_production_config.yaml'
            if config_file.exists():
                tf.add(config_file, arcname='nexus_production_config.yaml')
            
            # Backup state
            state_file = self.data_dir / 'nexus_state.json'
            if state_file.exists():
                tf.add(state_file, arcname='nexus_state.json')
            
            # Backup plugins
            plugins_dir = self.data_dir / 'nexus_plugins'
            if plugins_dir.exists():
                tf.add(plugins_dir, arcname='nexus_plugins')
            
            # Backup databases
            for db_file in self.data_dir.glob('*.db'):
                tf.add(db_file, arcname=db_file.name)
        
        print(f"Backup created: {backup_path}")
        return backup_path
    
    async def restore_backup(self, backup_path: Path) -> bool:
        """Restore from backup"""
        if not backup_path.exists():
            print(f"Backup not found: {backup_path}")
            return False
        
        print(f"Restoring from backup: {backup_path}")
        
        try:
            # Create restore directory
            restore_dir = self.data_dir / 'restore_temp'
            restore_dir.mkdir(exist_ok=True)
            
            # Extract backup
            with tarfile.open(backup_path, 'r:gz') as tf:
                tf.extractall(restore_dir)
            
            # Move files to data directory
            for item in restore_dir.iterdir():
                target = self.data_dir / item.name
                if target.exists():
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                shutil.move(str(item), str(target))
            
            # Cleanup
            restore_dir.rmdir()
            
            print("Restore completed successfully")
            return True
            
        except Exception as e:
            print(f"Restore failed: {e}")
            return False
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []
        
        for backup_file in self.backup_dir.glob('*.tar.gz'):
            stat = backup_file.stat()
            backups.append({
                'name': backup_file.stem,
                'path': backup_file,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_mtime)
            })
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)


class ProductionLauncher:
    """Main production launcher"""
    
    VERSION = "1.0.0"
    
    def __init__(self):
        self.data_dir = Path.home() / '.nexus'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.data_dir / 'nexus_production_config.yaml'
        self.update_url = os.environ.get('NEXUS_UPDATE_URL', 'https://updates.nexus.dev')
    
    async def run(self):
        """Main launcher entry point"""
        import argparse
        
        parser = argparse.ArgumentParser(
            description="NEXUS Mind Repository Production Launcher"
        )
        parser.add_argument(
            'command',
            choices=['start', 'setup', 'check', 'update', 'backup', 'restore', 'migrate', 'build'],
            help='Command to execute'
        )
        parser.add_argument('--config', help='Configuration file path')
        parser.add_argument('--backup-name', help='Backup name for restore')
        parser.add_argument('--dev-dir', help='Development directory for migration')
        parser.add_argument('--output-dir', help='Output directory for build')
        parser.add_argument('--no-update-check', action='store_true', help='Skip update check')
        
        args = parser.parse_args()
        
        # Override config path if provided
        if args.config:
            self.config_path = Path(args.config)
        
        # Execute command
        if args.command == 'check':
            await self.check_requirements()
        
        elif args.command == 'setup':
            await self.run_setup()
        
        elif args.command == 'start':
            await self.start_nexus(check_updates=not args.no_update_check)
        
        elif args.command == 'update':
            await self.check_and_apply_updates()
        
        elif args.command == 'backup':
            backup_manager = BackupManager(self.data_dir)
            await backup_manager.create_backup()
        
        elif args.command == 'restore':
            if not args.backup_name:
                print("Please specify --backup-name")
                return
            
            backup_manager = BackupManager(self.data_dir)
            backup_path = backup_manager.backup_dir / f"{args.backup_name}.tar.gz"
            await backup_manager.restore_backup(backup_path)
        
        elif args.command == 'migrate':
            if not args.dev_dir:
                print("Please specify --dev-dir")
                return
            
            migration_manager = MigrationManager(
                Path(args.dev_dir),
                self.data_dir
            )
            await migration_manager.migrate()
        
        elif args.command == 'build':
            output_dir = Path(args.output_dir) if args.output_dir else Path('dist')
            await self.build_binary(output_dir)
    
    async def check_requirements(self):
        """Check system requirements"""
        print("Checking system requirements...\n")
        
        ok, messages = SystemRequirements.validate_all()
        
        if ok:
            print("✓ All requirements satisfied")
        else:
            print("⚠ Some requirements not met:")
        
        for msg in messages:
            if "not found" in msg or "required" in msg:
                print(f"  ✗ {msg}")
            else:
                print(f"  ⚠ {msg}")
        
        return ok
    
    async def run_setup(self):
        """Run setup wizard"""
        wizard = SetupWizard(self.config_path)
        await wizard.run()
    
    async def start_nexus(self, check_updates: bool = True):
        """Start NEXUS with production configuration"""
        # Check if setup is needed
        if not self.config_path.exists():
            print("No configuration found. Running setup wizard...")
            await self.run_setup()
        
        # Check for updates
        if check_updates:
            await self.check_and_apply_updates()
        
        # Load configuration
        from nexus_integration_core import load_config, NexusIntegrationCore
        
        config = load_config(self.config_path)
        
        # Extract core config
        core_config = {
            'api_host': config['nexus']['api']['host'],
            'api_port': config['nexus']['api']['port'],
            'redis_url': config['nexus']['state'].get('url'),
            'state_file': str(self.data_dir / 'nexus_state.json'),
            'plugin_dir': str(self.data_dir / 'nexus_plugins'),
            'service_discovery': config['nexus']['service_discovery'],
            'state': config['nexus']['state'],
            'security': config['nexus']['security'],
            'monitoring': config['nexus']['monitoring']
        }
        
        # Create and start core
        print(f"\nStarting NEXUS v{self.VERSION} in production mode...")
        
        core = NexusIntegrationCore(core_config)
        
        try:
            await core.start()
            
            print("\nNEXUS is running!")
            print(f"API: http://{core_config['api_host']}:{core_config['api_port']}")
            print(f"Metrics: http://localhost:{config['nexus']['monitoring']['metrics']['port']}/metrics")
            print("\nPress Ctrl+C to stop")
            
            # Keep running
            await asyncio.Event().wait()
            
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            await core.stop()
    
    async def check_and_apply_updates(self):
        """Check for and apply updates"""
        updater = AutoUpdater(self.VERSION, self.update_url)
        
        print("Checking for updates...")
        update_info = await updater.check_for_updates()
        
        if not update_info:
            print("No updates available")
            return
        
        print(f"\nUpdate available: v{update_info['version']}")
        print(f"Current version: v{self.VERSION}")
        print(f"\nRelease notes:\n{update_info.get('release_notes', 'No release notes')}")
        
        response = input("\nApply update? [Y/n]: ").strip().upper()
        if response in ['', 'Y', 'YES']:
            try:
                update_path = await updater.download_update(update_info)
                await updater.apply_update(update_path)
            except Exception as e:
                print(f"Update failed: {e}")
    
    async def build_binary(self, output_dir: Path):
        """Build NEXUS as a single binary"""
        print("Building NEXUS binary...")
        
        builder = BinaryBuilder(Path.cwd(), output_dir)
        
        try:
            if HAS_PYINSTALLER:
                binary_path = builder.build_pyinstaller()
                print(f"Binary built with PyInstaller: {binary_path}")
            elif HAS_NUITKA:
                binary_path = builder.build_nuitka()
                print(f"Binary built with Nuitka: {binary_path}")
            else:
                print("No binary builder available. Install PyInstaller or Nuitka.")
                return
            
            # Create distribution archive
            archive_path = builder.create_archive(binary_path, self.VERSION)
            print(f"Distribution archive created: {archive_path}")
            
        except Exception as e:
            print(f"Build failed: {e}")


# Crash recovery handler
class CrashRecovery:
    """Handle crash recovery and diagnostics"""
    
    @staticmethod
    def setup_crash_handler():
        """Setup crash handler"""
        import signal
        import faulthandler
        
        # Enable fault handler
        faulthandler.enable()
        
        # Setup signal handlers
        def handle_crash(signum, frame):
            print(f"\nCrash detected (signal {signum})")
            
            # Create crash dump
            crash_dir = Path.home() / '.nexus' / 'crashes'
            crash_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            crash_file = crash_dir / f"crash_{timestamp}.txt"
            
            with open(crash_file, 'w') as f:
                f.write(f"NEXUS Crash Report\n")
                f.write(f"Time: {datetime.now()}\n")
                f.write(f"Signal: {signum}\n")
                f.write(f"Python: {sys.version}\n")
                f.write(f"Platform: {platform.platform()}\n\n")
                
                # Dump traceback
                import traceback
                traceback.print_exc(file=f)
                
                # Dump thread info
                faulthandler.dump_traceback(file=f, all_threads=True)
            
            print(f"Crash report saved to: {crash_file}")
            sys.exit(1)
        
        # Register handlers
        for sig in [signal.SIGSEGV, signal.SIGABRT]:
            if hasattr(signal, sig.name):
                signal.signal(sig, handle_crash)


async def main():
    """Main entry point"""
    # Setup crash handler
    CrashRecovery.setup_crash_handler()
    
    # Run launcher
    launcher = ProductionLauncher()
    await launcher.run()


if __name__ == "__main__":
    asyncio.run(main())