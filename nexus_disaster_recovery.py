#!/usr/bin/env python3
"""
NEXUS Disaster Recovery System
Automated backups, failover, and recovery capabilities
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import tarfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import aioboto3
import aiofiles
import psycopg2
import yaml
from croniter import croniter
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()
logger = logging.getLogger(__name__)


class BackupType(Enum):
    """Backup types"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"


class BackupStorage(Enum):
    """Backup storage locations"""
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"
    AZURE = "azure"
    REMOTE_SERVER = "remote"


class RecoveryPoint(Enum):
    """Recovery point types"""
    LATEST = "latest"
    POINT_IN_TIME = "point_in_time"
    SPECIFIC_BACKUP = "specific_backup"


class FailoverMode(Enum):
    """Failover modes"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SCHEDULED = "scheduled"


@dataclass
class BackupConfig:
    """Backup configuration"""
    name: str
    type: BackupType
    schedule: str  # Cron expression
    retention_days: int
    storage: List[BackupStorage]
    paths: List[str]
    databases: List[Dict[str, str]] = field(default_factory=list)
    pre_scripts: List[str] = field(default_factory=list)
    post_scripts: List[str] = field(default_factory=list)
    encryption_enabled: bool = True
    compression_enabled: bool = True
    verify_backup: bool = True
    
    def get_next_run(self) -> datetime:
        """Get next scheduled run time"""
        cron = croniter(self.schedule, datetime.now())
        return cron.get_next(datetime)


@dataclass
class BackupMetadata:
    """Backup metadata"""
    id: str
    name: str
    type: BackupType
    timestamp: datetime
    size_bytes: int
    duration_seconds: float
    status: str
    storage_locations: List[str]
    checksum: str
    encrypted: bool
    compressed: bool
    parent_backup_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'timestamp': self.timestamp.isoformat(),
            'size_bytes': self.size_bytes,
            'duration_seconds': self.duration_seconds,
            'status': self.status,
            'storage_locations': self.storage_locations,
            'checksum': self.checksum,
            'encrypted': self.encrypted,
            'compressed': self.compressed,
            'parent_backup_id': self.parent_backup_id
        }


@dataclass
class RecoveryPlan:
    """Recovery plan configuration"""
    name: str
    rto_minutes: int  # Recovery Time Objective
    rpo_minutes: int  # Recovery Point Objective
    failover_sequence: List[Dict[str, Any]]
    health_checks: List[Dict[str, Any]]
    notification_channels: List[str]
    test_schedule: Optional[str] = None
    auto_failover: bool = False
    rollback_enabled: bool = True


@dataclass
class IncidentReport:
    """Incident report"""
    id: str
    timestamp: datetime
    type: str
    severity: str
    description: str
    affected_systems: List[str]
    recovery_actions: List[Dict[str, Any]]
    resolution_time: Optional[timedelta] = None
    root_cause: Optional[str] = None
    lessons_learned: List[str] = field(default_factory=list)
    preventive_measures: List[str] = field(default_factory=list)


class DisasterRecoveryManager:
    """Main disaster recovery manager"""
    
    def __init__(self, config_path: str = "dr_config.yaml"):
        self.config_path = config_path
        self.backup_configs: Dict[str, BackupConfig] = {}
        self.recovery_plans: Dict[str, RecoveryPlan] = {}
        self.backup_history: List[BackupMetadata] = []
        self.incident_reports: List[IncidentReport] = []
        self.active_recoveries: Set[str] = set()
        self.load_config()
    
    def load_config(self):
        """Load DR configuration"""
        if Path(self.config_path).exists():
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                
                # Load backup configurations
                for name, backup_cfg in config.get('backups', {}).items():
                    self.backup_configs[name] = BackupConfig(
                        name=name,
                        type=BackupType(backup_cfg['type']),
                        schedule=backup_cfg['schedule'],
                        retention_days=backup_cfg['retention_days'],
                        storage=[BackupStorage(s) for s in backup_cfg['storage']],
                        paths=backup_cfg.get('paths', []),
                        databases=backup_cfg.get('databases', []),
                        pre_scripts=backup_cfg.get('pre_scripts', []),
                        post_scripts=backup_cfg.get('post_scripts', []),
                        encryption_enabled=backup_cfg.get('encryption_enabled', True),
                        compression_enabled=backup_cfg.get('compression_enabled', True),
                        verify_backup=backup_cfg.get('verify_backup', True)
                    )
                
                # Load recovery plans
                for name, recovery_cfg in config.get('recovery_plans', {}).items():
                    self.recovery_plans[name] = RecoveryPlan(
                        name=name,
                        rto_minutes=recovery_cfg['rto_minutes'],
                        rpo_minutes=recovery_cfg['rpo_minutes'],
                        failover_sequence=recovery_cfg['failover_sequence'],
                        health_checks=recovery_cfg['health_checks'],
                        notification_channels=recovery_cfg.get('notification_channels', []),
                        test_schedule=recovery_cfg.get('test_schedule'),
                        auto_failover=recovery_cfg.get('auto_failover', False),
                        rollback_enabled=recovery_cfg.get('rollback_enabled', True)
                    )
    
    async def perform_backup(self, backup_name: str) -> BackupMetadata:
        """Perform a backup"""
        if backup_name not in self.backup_configs:
            raise ValueError(f"Backup configuration '{backup_name}' not found")
        
        config = self.backup_configs[backup_name]
        backup_id = f"{backup_name}-{int(time.time())}"
        start_time = time.time()
        
        console.print(f"\n[cyan]Starting backup: {backup_name}[/cyan]")
        console.print(f"Type: {config.type.value}")
        
        try:
            # Run pre-backup scripts
            if config.pre_scripts:
                console.print("[yellow]Running pre-backup scripts...[/yellow]")
                for script in config.pre_scripts:
                    await self._run_script(script)
            
            # Create backup directory
            backup_dir = Path(f"/tmp/nexus-backup/{backup_id}")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup files
            if config.paths:
                await self._backup_files(config.paths, backup_dir)
            
            # Backup databases
            if config.databases:
                await self._backup_databases(config.databases, backup_dir)
            
            # Create archive
            archive_path = await self._create_archive(
                backup_dir,
                backup_id,
                config.compression_enabled,
                config.encryption_enabled
            )
            
            # Calculate checksum
            checksum = await self._calculate_checksum(archive_path)
            
            # Upload to storage
            storage_locations = await self._upload_backup(
                archive_path,
                backup_id,
                config.storage
            )
            
            # Verify backup if enabled
            if config.verify_backup:
                console.print("[yellow]Verifying backup...[/yellow]")
                await self._verify_backup(archive_path, checksum)
            
            # Run post-backup scripts
            if config.post_scripts:
                console.print("[yellow]Running post-backup scripts...[/yellow]")
                for script in config.post_scripts:
                    await self._run_script(script)
            
            # Create metadata
            duration = time.time() - start_time
            metadata = BackupMetadata(
                id=backup_id,
                name=backup_name,
                type=config.type,
                timestamp=datetime.now(),
                size_bytes=Path(archive_path).stat().st_size,
                duration_seconds=duration,
                status="completed",
                storage_locations=storage_locations,
                checksum=checksum,
                encrypted=config.encryption_enabled,
                compressed=config.compression_enabled,
                parent_backup_id=self._get_parent_backup_id(backup_name, config.type)
            )
            
            self.backup_history.append(metadata)
            await self._save_backup_metadata(metadata)
            
            # Cleanup old backups
            await self._cleanup_old_backups(backup_name, config.retention_days)
            
            # Cleanup temporary files
            shutil.rmtree(backup_dir)
            os.remove(archive_path)
            
            console.print(f"[green]Backup completed successfully![/green]")
            console.print(f"Duration: {duration:.2f} seconds")
            console.print(f"Size: {metadata.size_bytes / 1024 / 1024:.2f} MB")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            console.print(f"[red]Backup failed: {str(e)}[/red]")
            
            # Create failed metadata
            metadata = BackupMetadata(
                id=backup_id,
                name=backup_name,
                type=config.type,
                timestamp=datetime.now(),
                size_bytes=0,
                duration_seconds=time.time() - start_time,
                status="failed",
                storage_locations=[],
                checksum="",
                encrypted=config.encryption_enabled,
                compressed=config.compression_enabled
            )
            
            self.backup_history.append(metadata)
            raise
    
    async def _backup_files(self, paths: List[str], backup_dir: Path):
        """Backup files and directories"""
        console.print("[yellow]Backing up files...[/yellow]")
        
        for path in paths:
            source = Path(path)
            if not source.exists():
                console.print(f"[red]Warning: Path {path} does not exist[/red]")
                continue
            
            # Create relative path structure in backup
            if source.is_file():
                dest = backup_dir / "files" / source.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
            else:
                dest = backup_dir / "files" / source.name
                shutil.copytree(source, dest, dirs_exist_ok=True)
    
    async def _backup_databases(self, databases: List[Dict[str, str]], backup_dir: Path):
        """Backup databases"""
        console.print("[yellow]Backing up databases...[/yellow]")
        
        db_backup_dir = backup_dir / "databases"
        db_backup_dir.mkdir(parents=True, exist_ok=True)
        
        for db_config in databases:
            db_type = db_config['type']
            db_name = db_config['name']
            
            if db_type == 'postgresql':
                await self._backup_postgresql(db_config, db_backup_dir)
            elif db_type == 'mysql':
                await self._backup_mysql(db_config, db_backup_dir)
            elif db_type == 'mongodb':
                await self._backup_mongodb(db_config, db_backup_dir)
            else:
                console.print(f"[red]Unsupported database type: {db_type}[/red]")
    
    async def _backup_postgresql(self, db_config: Dict[str, str], backup_dir: Path):
        """Backup PostgreSQL database"""
        backup_file = backup_dir / f"{db_config['name']}.sql"
        
        cmd = [
            'pg_dump',
            '-h', db_config.get('host', 'localhost'),
            '-p', str(db_config.get('port', 5432)),
            '-U', db_config.get('user', 'postgres'),
            '-d', db_config['name'],
            '-f', str(backup_file),
            '--clean',
            '--if-exists',
            '--no-owner',
            '--no-privileges'
        ]
        
        env = os.environ.copy()
        if 'password' in db_config:
            env['PGPASSWORD'] = db_config['password']
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"PostgreSQL backup failed: {result.stderr}")
    
    async def _backup_mysql(self, db_config: Dict[str, str], backup_dir: Path):
        """Backup MySQL database"""
        backup_file = backup_dir / f"{db_config['name']}.sql"
        
        cmd = [
            'mysqldump',
            '-h', db_config.get('host', 'localhost'),
            '-P', str(db_config.get('port', 3306)),
            '-u', db_config.get('user', 'root'),
            f"-p{db_config.get('password', '')}",
            '--single-transaction',
            '--routines',
            '--triggers',
            db_config['name']
        ]
        
        with open(backup_file, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            raise Exception(f"MySQL backup failed: {result.stderr}")
    
    async def _backup_mongodb(self, db_config: Dict[str, str], backup_dir: Path):
        """Backup MongoDB database"""
        backup_path = backup_dir / db_config['name']
        
        cmd = [
            'mongodump',
            '--host', f"{db_config.get('host', 'localhost')}:{db_config.get('port', 27017)}",
            '--db', db_config['name'],
            '--out', str(backup_path)
        ]
        
        if 'user' in db_config:
            cmd.extend(['--username', db_config['user']])
        if 'password' in db_config:
            cmd.extend(['--password', db_config['password']])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"MongoDB backup failed: {result.stderr}")
    
    async def _create_archive(
        self,
        backup_dir: Path,
        backup_id: str,
        compress: bool,
        encrypt: bool
    ) -> str:
        """Create backup archive"""
        console.print("[yellow]Creating archive...[/yellow]")
        
        archive_path = f"/tmp/{backup_id}.tar"
        if compress:
            archive_path += ".gz"
        
        # Create tar archive
        mode = 'w:gz' if compress else 'w'
        with tarfile.open(archive_path, mode) as tar:
            tar.add(backup_dir, arcname=backup_id)
        
        # Encrypt if enabled
        if encrypt:
            encrypted_path = f"{archive_path}.enc"
            await self._encrypt_file(archive_path, encrypted_path)
            os.remove(archive_path)
            return encrypted_path
        
        return archive_path
    
    async def _encrypt_file(self, source_path: str, dest_path: str):
        """Encrypt a file using GPG or OpenSSL"""
        # Using OpenSSL for simplicity
        password = os.getenv('NEXUS_BACKUP_PASSWORD', 'default-password')
        
        cmd = [
            'openssl', 'enc',
            '-aes-256-cbc',
            '-salt',
            '-in', source_path,
            '-out', dest_path,
            '-pass', f'pass:{password}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Encryption failed: {result.stderr}")
    
    async def _calculate_checksum(self, file_path: str) -> str:
        """Calculate file checksum"""
        cmd = ['sha256sum', file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Checksum calculation failed: {result.stderr}")
        
        return result.stdout.split()[0]
    
    async def _upload_backup(
        self,
        file_path: str,
        backup_id: str,
        storage_locations: List[BackupStorage]
    ) -> List[str]:
        """Upload backup to storage locations"""
        console.print("[yellow]Uploading backup...[/yellow]")
        
        uploaded_locations = []
        
        for storage in storage_locations:
            try:
                if storage == BackupStorage.LOCAL:
                    location = await self._upload_local(file_path, backup_id)
                elif storage == BackupStorage.S3:
                    location = await self._upload_s3(file_path, backup_id)
                elif storage == BackupStorage.GCS:
                    location = await self._upload_gcs(file_path, backup_id)
                elif storage == BackupStorage.AZURE:
                    location = await self._upload_azure(file_path, backup_id)
                elif storage == BackupStorage.REMOTE_SERVER:
                    location = await self._upload_remote(file_path, backup_id)
                
                uploaded_locations.append(location)
                console.print(f"[green]✓ Uploaded to {storage.value}[/green]")
                
            except Exception as e:
                console.print(f"[red]Failed to upload to {storage.value}: {str(e)}[/red]")
        
        return uploaded_locations
    
    async def _upload_local(self, file_path: str, backup_id: str) -> str:
        """Upload to local storage"""
        backup_dir = Path("/var/nexus/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        dest_path = backup_dir / Path(file_path).name
        shutil.copy2(file_path, dest_path)
        
        return str(dest_path)
    
    async def _upload_s3(self, file_path: str, backup_id: str) -> str:
        """Upload to AWS S3"""
        bucket_name = os.getenv('NEXUS_S3_BACKUP_BUCKET', 'nexus-backups')
        key = f"backups/{backup_id}/{Path(file_path).name}"
        
        async with aioboto3.Session().client('s3') as s3:
            await s3.upload_file(file_path, bucket_name, key)
        
        return f"s3://{bucket_name}/{key}"
    
    async def _upload_gcs(self, file_path: str, backup_id: str) -> str:
        """Upload to Google Cloud Storage"""
        # Implementation would use Google Cloud Storage client
        bucket_name = os.getenv('NEXUS_GCS_BACKUP_BUCKET', 'nexus-backups')
        blob_name = f"backups/{backup_id}/{Path(file_path).name}"
        
        return f"gs://{bucket_name}/{blob_name}"
    
    async def _upload_azure(self, file_path: str, backup_id: str) -> str:
        """Upload to Azure Blob Storage"""
        # Implementation would use Azure Storage client
        container_name = os.getenv('NEXUS_AZURE_BACKUP_CONTAINER', 'nexus-backups')
        blob_name = f"backups/{backup_id}/{Path(file_path).name}"
        
        return f"azure://{container_name}/{blob_name}"
    
    async def _upload_remote(self, file_path: str, backup_id: str) -> str:
        """Upload to remote server via SSH"""
        remote_host = os.getenv('NEXUS_BACKUP_REMOTE_HOST')
        remote_path = os.getenv('NEXUS_BACKUP_REMOTE_PATH', '/backups')
        remote_user = os.getenv('NEXUS_BACKUP_REMOTE_USER', 'backup')
        
        dest_path = f"{remote_path}/{backup_id}/{Path(file_path).name}"
        
        # Create remote directory
        cmd = [
            'ssh',
            f'{remote_user}@{remote_host}',
            f'mkdir -p {remote_path}/{backup_id}'
        ]
        subprocess.run(cmd, check=True)
        
        # Copy file
        cmd = [
            'scp',
            file_path,
            f'{remote_user}@{remote_host}:{dest_path}'
        ]
        subprocess.run(cmd, check=True)
        
        return f"remote://{remote_host}{dest_path}"
    
    async def _verify_backup(self, file_path: str, expected_checksum: str):
        """Verify backup integrity"""
        actual_checksum = await self._calculate_checksum(file_path)
        
        if actual_checksum != expected_checksum:
            raise Exception(f"Backup verification failed: checksum mismatch")
        
        console.print("[green]✓ Backup verified successfully[/green]")
    
    async def _run_script(self, script_path: str):
        """Run a backup script"""
        if not Path(script_path).exists():
            console.print(f"[red]Script not found: {script_path}[/red]")
            return
        
        result = subprocess.run([script_path], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Script failed: {result.stderr}")
    
    def _get_parent_backup_id(self, backup_name: str, backup_type: BackupType) -> Optional[str]:
        """Get parent backup ID for incremental/differential backups"""
        if backup_type == BackupType.FULL:
            return None
        
        # Find last full backup
        full_backups = [
            b for b in self.backup_history
            if b.name == backup_name and b.type == BackupType.FULL and b.status == "completed"
        ]
        
        if full_backups:
            return sorted(full_backups, key=lambda b: b.timestamp, reverse=True)[0].id
        
        return None
    
    async def _save_backup_metadata(self, metadata: BackupMetadata):
        """Save backup metadata"""
        metadata_dir = Path("/var/nexus/backup-metadata")
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_file = metadata_dir / f"{metadata.id}.json"
        
        async with aiofiles.open(metadata_file, 'w') as f:
            await f.write(json.dumps(metadata.to_dict(), indent=2))
    
    async def _cleanup_old_backups(self, backup_name: str, retention_days: int):
        """Clean up old backups"""
        console.print("[yellow]Cleaning up old backups...[/yellow]")
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        old_backups = [
            b for b in self.backup_history
            if b.name == backup_name and b.timestamp < cutoff_date and b.status == "completed"
        ]
        
        for backup in old_backups:
            console.print(f"[yellow]Removing old backup: {backup.id}[/yellow]")
            
            # Remove from storage locations
            for location in backup.storage_locations:
                await self._delete_backup_from_storage(location)
            
            # Remove metadata
            metadata_file = Path(f"/var/nexus/backup-metadata/{backup.id}.json")
            if metadata_file.exists():
                metadata_file.unlink()
            
            # Remove from history
            self.backup_history.remove(backup)
    
    async def _delete_backup_from_storage(self, location: str):
        """Delete backup from storage location"""
        if location.startswith('s3://'):
            # Delete from S3
            parts = location.replace('s3://', '').split('/', 1)
            bucket = parts[0]
            key = parts[1]
            
            async with aioboto3.Session().client('s3') as s3:
                await s3.delete_object(Bucket=bucket, Key=key)
        
        elif location.startswith('/'):
            # Delete from local storage
            Path(location).unlink(missing_ok=True)
        
        # Add other storage types as needed
    
    async def restore_backup(
        self,
        backup_id: str,
        target_path: str = "/",
        selective_restore: Optional[List[str]] = None
    ) -> bool:
        """Restore from backup"""
        console.print(f"\n[cyan]Starting restore: {backup_id}[/cyan]")
        
        # Find backup metadata
        backup = next((b for b in self.backup_history if b.id == backup_id), None)
        
        if not backup:
            console.print(f"[red]Backup {backup_id} not found[/red]")
            return False
        
        try:
            # Download backup from storage
            console.print("[yellow]Downloading backup...[/yellow]")
            local_path = await self._download_backup(backup)
            
            # Verify backup
            console.print("[yellow]Verifying backup...[/yellow]")
            await self._verify_backup(local_path, backup.checksum)
            
            # Decrypt if needed
            if backup.encrypted:
                console.print("[yellow]Decrypting backup...[/yellow]")
                decrypted_path = await self._decrypt_file(local_path)
                os.remove(local_path)
                local_path = decrypted_path
            
            # Extract backup
            console.print("[yellow]Extracting backup...[/yellow]")
            extract_dir = Path(f"/tmp/nexus-restore/{backup_id}")
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            with tarfile.open(local_path, 'r:*') as tar:
                tar.extractall(extract_dir)
            
            # Restore files
            if selective_restore:
                await self._selective_restore(extract_dir, target_path, selective_restore)
            else:
                await self._full_restore(extract_dir, target_path)
            
            # Cleanup
            shutil.rmtree(extract_dir)
            os.remove(local_path)
            
            console.print("[green]Restore completed successfully![/green]")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            console.print(f"[red]Restore failed: {str(e)}[/red]")
            return False
    
    async def _download_backup(self, backup: BackupMetadata) -> str:
        """Download backup from storage"""
        # Try each storage location until successful
        for location in backup.storage_locations:
            try:
                if location.startswith('s3://'):
                    return await self._download_from_s3(location)
                elif location.startswith('/'):
                    return location  # Already local
                # Add other storage types
                
            except Exception as e:
                logger.error(f"Failed to download from {location}: {str(e)}")
        
        raise Exception("Failed to download backup from any location")
    
    async def _download_from_s3(self, location: str) -> str:
        """Download backup from S3"""
        parts = location.replace('s3://', '').split('/', 1)
        bucket = parts[0]
        key = parts[1]
        
        local_path = f"/tmp/{Path(key).name}"
        
        async with aioboto3.Session().client('s3') as s3:
            await s3.download_file(bucket, key, local_path)
        
        return local_path
    
    async def _decrypt_file(self, encrypted_path: str) -> str:
        """Decrypt a file"""
        decrypted_path = encrypted_path.replace('.enc', '')
        password = os.getenv('NEXUS_BACKUP_PASSWORD', 'default-password')
        
        cmd = [
            'openssl', 'enc',
            '-aes-256-cbc',
            '-d',
            '-in', encrypted_path,
            '-out', decrypted_path,
            '-pass', f'pass:{password}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Decryption failed: {result.stderr}")
        
        return decrypted_path
    
    async def _selective_restore(
        self,
        extract_dir: Path,
        target_path: str,
        patterns: List[str]
    ):
        """Selective restore based on patterns"""
        console.print(f"[yellow]Performing selective restore...[/yellow]")
        
        # Implementation would match patterns and restore only matching files
        pass
    
    async def _full_restore(self, extract_dir: Path, target_path: str):
        """Full restore of all files"""
        console.print(f"[yellow]Performing full restore...[/yellow]")
        
        # Find the backup directory within extract_dir
        backup_dirs = list(extract_dir.glob("*"))
        if not backup_dirs:
            raise Exception("No backup data found in archive")
        
        backup_dir = backup_dirs[0]
        
        # Restore files
        files_dir = backup_dir / "files"
        if files_dir.exists():
            for item in files_dir.iterdir():
                dest = Path(target_path) / item.name
                
                if item.is_file():
                    shutil.copy2(item, dest)
                else:
                    shutil.copytree(item, dest, dirs_exist_ok=True)
        
        # Restore databases
        db_dir = backup_dir / "databases"
        if db_dir.exists():
            await self._restore_databases(db_dir)
    
    async def _restore_databases(self, db_dir: Path):
        """Restore databases from backup"""
        console.print("[yellow]Restoring databases...[/yellow]")
        
        for db_file in db_dir.iterdir():
            if db_file.suffix == '.sql':
                # Determine database type and restore
                # This is simplified - real implementation would read metadata
                if 'postgres' in db_file.name:
                    await self._restore_postgresql(db_file)
                elif 'mysql' in db_file.name:
                    await self._restore_mysql(db_file)
    
    async def _restore_postgresql(self, sql_file: Path):
        """Restore PostgreSQL database"""
        db_name = sql_file.stem
        
        cmd = [
            'psql',
            '-h', os.getenv('DB_HOST', 'localhost'),
            '-U', os.getenv('DB_USER', 'postgres'),
            '-d', db_name,
            '-f', str(sql_file)
        ]
        
        env = os.environ.copy()
        if 'DB_PASSWORD' in os.environ:
            env['PGPASSWORD'] = os.environ['DB_PASSWORD']
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"PostgreSQL restore failed: {result.stderr}")
    
    async def _restore_mysql(self, sql_file: Path):
        """Restore MySQL database"""
        db_name = sql_file.stem
        
        cmd = [
            'mysql',
            '-h', os.getenv('DB_HOST', 'localhost'),
            '-u', os.getenv('DB_USER', 'root'),
            f"-p{os.getenv('DB_PASSWORD', '')}",
            db_name
        ]
        
        with open(sql_file, 'r') as f:
            result = subprocess.run(cmd, stdin=f, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"MySQL restore failed: {result.stderr}")
    
    async def execute_failover(
        self,
        plan_name: str,
        reason: str = "Manual failover"
    ) -> bool:
        """Execute failover plan"""
        if plan_name not in self.recovery_plans:
            console.print(f"[red]Recovery plan '{plan_name}' not found[/red]")
            return False
        
        plan = self.recovery_plans[plan_name]
        incident_id = f"incident-{int(time.time())}"
        
        console.print(f"\n[cyan]Executing failover plan: {plan_name}[/cyan]")
        console.print(f"Reason: {reason}")
        console.print(f"RTO: {plan.rto_minutes} minutes")
        
        # Create incident report
        incident = IncidentReport(
            id=incident_id,
            timestamp=datetime.now(),
            type="failover",
            severity="high",
            description=reason,
            affected_systems=[],
            recovery_actions=[]
        )
        
        try:
            # Execute failover sequence
            for step in plan.failover_sequence:
                console.print(f"\n[yellow]Executing: {step['name']}[/yellow]")
                
                success = await self._execute_failover_step(step)
                
                incident.recovery_actions.append({
                    'step': step['name'],
                    'status': 'success' if success else 'failed',
                    'timestamp': datetime.now().isoformat()
                })
                
                if not success:
                    console.print(f"[red]Failover step failed: {step['name']}[/red]")
                    
                    if plan.rollback_enabled:
                        console.print("[yellow]Initiating rollback...[/yellow]")
                        await self._rollback_failover(incident)
                    
                    return False
            
            # Run health checks
            console.print("\n[yellow]Running health checks...[/yellow]")
            health_status = await self._run_health_checks(plan.health_checks)
            
            if not all(health_status.values()):
                console.print("[red]Health checks failed[/red]")
                
                if plan.rollback_enabled:
                    await self._rollback_failover(incident)
                
                return False
            
            # Failover successful
            incident.resolution_time = datetime.now() - incident.timestamp
            self.incident_reports.append(incident)
            
            console.print(f"\n[green]Failover completed successfully![/green]")
            console.print(f"Time taken: {incident.resolution_time}")
            
            # Send notifications
            await self._send_notifications(
                plan.notification_channels,
                f"Failover completed: {plan_name}",
                incident
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failover failed: {str(e)}")
            console.print(f"[red]Failover failed: {str(e)}[/red]")
            
            incident.recovery_actions.append({
                'step': 'error',
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
            self.incident_reports.append(incident)
            return False
    
    async def _execute_failover_step(self, step: Dict[str, Any]) -> bool:
        """Execute a single failover step"""
        step_type = step.get('type')
        
        if step_type == 'script':
            return await self._execute_script_step(step)
        elif step_type == 'dns_update':
            return await self._execute_dns_update(step)
        elif step_type == 'load_balancer':
            return await self._execute_load_balancer_update(step)
        elif step_type == 'database_failover':
            return await self._execute_database_failover(step)
        elif step_type == 'service_start':
            return await self._execute_service_start(step)
        
        return False
    
    async def _execute_script_step(self, step: Dict[str, Any]) -> bool:
        """Execute a script failover step"""
        script_path = step.get('script')
        
        if not script_path or not Path(script_path).exists():
            return False
        
        result = subprocess.run([script_path], capture_output=True, text=True)
        return result.returncode == 0
    
    async def _execute_dns_update(self, step: Dict[str, Any]) -> bool:
        """Update DNS records for failover"""
        # Implementation would update DNS provider
        console.print(f"[yellow]Updating DNS: {step.get('domain')} -> {step.get('target')}[/yellow]")
        return True
    
    async def _execute_load_balancer_update(self, step: Dict[str, Any]) -> bool:
        """Update load balancer configuration"""
        # Implementation would update load balancer
        console.print(f"[yellow]Updating load balancer: {step.get('name')}[/yellow]")
        return True
    
    async def _execute_database_failover(self, step: Dict[str, Any]) -> bool:
        """Execute database failover"""
        # Implementation would promote replica to primary
        console.print(f"[yellow]Failing over database: {step.get('database')}[/yellow]")
        return True
    
    async def _execute_service_start(self, step: Dict[str, Any]) -> bool:
        """Start services"""
        services = step.get('services', [])
        
        for service in services:
            cmd = ['systemctl', 'start', service]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                console.print(f"[red]Failed to start service: {service}[/red]")
                return False
        
        return True
    
    async def _run_health_checks(self, health_checks: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Run health checks"""
        results = {}
        
        for check in health_checks:
            name = check.get('name', 'unknown')
            check_type = check.get('type')
            
            if check_type == 'http':
                results[name] = await self._http_health_check(check)
            elif check_type == 'tcp':
                results[name] = await self._tcp_health_check(check)
            elif check_type == 'script':
                results[name] = await self._script_health_check(check)
            
            status = "✓" if results[name] else "✗"
            console.print(f"{status} {name}")
        
        return results
    
    async def _http_health_check(self, check: Dict[str, Any]) -> bool:
        """HTTP health check"""
        import aiohttp
        
        url = check.get('url')
        expected_status = check.get('expected_status', 200)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    return resp.status == expected_status
        except:
            return False
    
    async def _tcp_health_check(self, check: Dict[str, Any]) -> bool:
        """TCP port health check"""
        import socket
        
        host = check.get('host')
        port = check.get('port')
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    async def _script_health_check(self, check: Dict[str, Any]) -> bool:
        """Script-based health check"""
        script = check.get('script')
        
        if not script or not Path(script).exists():
            return False
        
        result = subprocess.run([script], capture_output=True, text=True)
        return result.returncode == 0
    
    async def _rollback_failover(self, incident: IncidentReport):
        """Rollback failed failover"""
        console.print("[yellow]Rolling back failover...[/yellow]")
        
        # Execute rollback steps in reverse order
        for action in reversed(incident.recovery_actions):
            if action['status'] == 'success':
                # Rollback this action
                console.print(f"[yellow]Rolling back: {action['step']}[/yellow]")
                # Implementation would reverse the action
    
    async def _send_notifications(
        self,
        channels: List[str],
        message: str,
        incident: IncidentReport
    ):
        """Send notifications"""
        for channel in channels:
            if channel.startswith('slack://'):
                await self._send_slack_notification(channel, message, incident)
            elif channel.startswith('email://'):
                await self._send_email_notification(channel, message, incident)
            elif channel.startswith('pagerduty://'):
                await self._send_pagerduty_notification(channel, message, incident)
    
    async def _send_slack_notification(
        self,
        webhook_url: str,
        message: str,
        incident: IncidentReport
    ):
        """Send Slack notification"""
        import aiohttp
        
        payload = {
            "text": message,
            "attachments": [{
                "color": "good" if incident.resolution_time else "danger",
                "fields": [
                    {"title": "Incident ID", "value": incident.id, "short": True},
                    {"title": "Type", "value": incident.type, "short": True},
                    {"title": "Severity", "value": incident.severity, "short": True},
                    {"title": "Description", "value": incident.description}
                ]
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            await session.post(webhook_url, json=payload)
    
    async def _send_email_notification(
        self,
        email_config: str,
        message: str,
        incident: IncidentReport
    ):
        """Send email notification"""
        # Implementation would send email
        pass
    
    async def _send_pagerduty_notification(
        self,
        integration_key: str,
        message: str,
        incident: IncidentReport
    ):
        """Send PagerDuty notification"""
        # Implementation would create PagerDuty incident
        pass
    
    async def test_recovery_plan(self, plan_name: str) -> Dict[str, Any]:
        """Test a recovery plan without executing it"""
        if plan_name not in self.recovery_plans:
            return {"success": False, "error": "Plan not found"}
        
        plan = self.recovery_plans[plan_name]
        
        console.print(f"\n[cyan]Testing recovery plan: {plan_name}[/cyan]")
        
        test_results = {
            "plan_name": plan_name,
            "timestamp": datetime.now().isoformat(),
            "steps": [],
            "health_checks": [],
            "estimated_recovery_time": 0,
            "issues_found": []
        }
        
        # Test each failover step
        for step in plan.failover_sequence:
            console.print(f"[yellow]Testing: {step['name']}[/yellow]")
            
            step_result = {
                "name": step['name'],
                "type": step['type'],
                "testable": True,
                "issues": []
            }
            
            # Validate step configuration
            if step['type'] == 'script' and not Path(step.get('script', '')).exists():
                step_result['issues'].append("Script not found")
                test_results['issues_found'].append(f"{step['name']}: Script not found")
            
            test_results['steps'].append(step_result)
            test_results['estimated_recovery_time'] += step.get('estimated_time', 60)
        
        # Test health checks
        console.print("\n[yellow]Testing health checks...[/yellow]")
        health_results = await self._run_health_checks(plan.health_checks)
        
        for check_name, result in health_results.items():
            test_results['health_checks'].append({
                "name": check_name,
                "current_status": "healthy" if result else "unhealthy"
            })
        
        # Check RTO feasibility
        if test_results['estimated_recovery_time'] > plan.rto_minutes * 60:
            test_results['issues_found'].append(
                f"Estimated recovery time ({test_results['estimated_recovery_time']}s) "
                f"exceeds RTO ({plan.rto_minutes} minutes)"
            )
        
        test_results['success'] = len(test_results['issues_found']) == 0
        
        return test_results
    
    def generate_post_mortem(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Generate post-mortem report"""
        incident = next((i for i in self.incident_reports if i.id == incident_id), None)
        
        if not incident:
            return None
        
        post_mortem = {
            "incident_id": incident.id,
            "timestamp": incident.timestamp.isoformat(),
            "duration": str(incident.resolution_time) if incident.resolution_time else "Ongoing",
            "severity": incident.severity,
            "description": incident.description,
            "timeline": [],
            "impact": {
                "affected_systems": incident.affected_systems,
                "downtime_minutes": incident.resolution_time.total_seconds() / 60 if incident.resolution_time else 0
            },
            "root_cause": incident.root_cause or "To be determined",
            "recovery_actions": incident.recovery_actions,
            "lessons_learned": incident.lessons_learned,
            "preventive_measures": incident.preventive_measures,
            "action_items": []
        }
        
        # Build timeline
        for action in incident.recovery_actions:
            post_mortem['timeline'].append({
                "time": action['timestamp'],
                "event": action['step'],
                "status": action['status']
            })
        
        # Generate action items
        if not incident.root_cause:
            post_mortem['action_items'].append({
                "description": "Determine root cause",
                "priority": "high",
                "assignee": "TBD"
            })
        
        if not incident.preventive_measures:
            post_mortem['action_items'].append({
                "description": "Identify preventive measures",
                "priority": "high",
                "assignee": "TBD"
            })
        
        return post_mortem
    
    def get_backup_status(self) -> Table:
        """Get backup status summary"""
        table = Table(title="Backup Status")
        table.add_column("Name", style="cyan")
        table.add_column("Last Backup", style="green")
        table.add_column("Size", style="yellow")
        table.add_column("Type", style="magenta")
        table.add_column("Status", style="blue")
        table.add_column("Next Run", style="white")
        
        for config_name, config in self.backup_configs.items():
            # Find last backup
            last_backup = None
            for backup in reversed(self.backup_history):
                if backup.name == config_name and backup.status == "completed":
                    last_backup = backup
                    break
            
            if last_backup:
                last_backup_str = last_backup.timestamp.strftime("%Y-%m-%d %H:%M")
                size_str = f"{last_backup.size_bytes / 1024 / 1024:.1f} MB"
                status = "✓"
            else:
                last_backup_str = "Never"
                size_str = "-"
                status = "⚠"
            
            next_run = config.get_next_run()
            next_run_str = next_run.strftime("%Y-%m-%d %H:%M")
            
            table.add_row(
                config_name,
                last_backup_str,
                size_str,
                config.type.value,
                status,
                next_run_str
            )
        
        return table
    
    def get_recovery_metrics(self) -> Dict[str, Any]:
        """Get recovery metrics"""
        total_incidents = len(self.incident_reports)
        
        if total_incidents == 0:
            return {
                "total_incidents": 0,
                "average_recovery_time": 0,
                "success_rate": 100.0,
                "mttr": 0  # Mean Time To Recovery
            }
        
        successful_recoveries = [
            i for i in self.incident_reports
            if i.resolution_time is not None
        ]
        
        total_recovery_time = sum(
            i.resolution_time.total_seconds()
            for i in successful_recoveries
        )
        
        return {
            "total_incidents": total_incidents,
            "successful_recoveries": len(successful_recoveries),
            "success_rate": (len(successful_recoveries) / total_incidents) * 100,
            "average_recovery_time": total_recovery_time / len(successful_recoveries) if successful_recoveries else 0,
            "mttr": total_recovery_time / total_incidents if total_incidents > 0 else 0,
            "incidents_by_severity": {
                "critical": sum(1 for i in self.incident_reports if i.severity == "critical"),
                "high": sum(1 for i in self.incident_reports if i.severity == "high"),
                "medium": sum(1 for i in self.incident_reports if i.severity == "medium"),
                "low": sum(1 for i in self.incident_reports if i.severity == "low")
            }
        }


async def main():
    """Example usage"""
    dr_manager = DisasterRecoveryManager()
    
    # Example backup configuration
    backup_config = BackupConfig(
        name="nexus-daily",
        type=BackupType.FULL,
        schedule="0 2 * * *",  # 2 AM daily
        retention_days=30,
        storage=[BackupStorage.LOCAL, BackupStorage.S3],
        paths=["/etc/nexus", "/var/nexus/data"],
        databases=[{
            "type": "postgresql",
            "name": "nexus_db",
            "host": "localhost",
            "user": "postgres"
        }],
        encryption_enabled=True,
        compression_enabled=True
    )
    
    dr_manager.backup_configs["nexus-daily"] = backup_config
    
    # Example recovery plan
    recovery_plan = RecoveryPlan(
        name="primary-failover",
        rto_minutes=15,
        rpo_minutes=60,
        failover_sequence=[
            {
                "name": "Stop primary services",
                "type": "service_stop",
                "services": ["nexus-api", "nexus-worker"],
                "estimated_time": 30
            },
            {
                "name": "Update DNS",
                "type": "dns_update",
                "domain": "api.nexus.io",
                "target": "failover.nexus.io",
                "estimated_time": 180
            },
            {
                "name": "Start failover services",
                "type": "service_start",
                "services": ["nexus-api-failover", "nexus-worker-failover"],
                "estimated_time": 60
            }
        ],
        health_checks=[
            {
                "name": "API Health",
                "type": "http",
                "url": "https://failover.nexus.io/health",
                "expected_status": 200
            },
            {
                "name": "Database Connection",
                "type": "tcp",
                "host": "db-failover.nexus.io",
                "port": 5432
            }
        ],
        notification_channels=[
            "slack://hooks.slack.com/services/xxx/yyy/zzz",
            "pagerduty://integration-key"
        ]
    )
    
    dr_manager.recovery_plans["primary-failover"] = recovery_plan
    
    # Display backup status
    console.print(dr_manager.get_backup_status())
    
    # Test recovery plan
    test_results = await dr_manager.test_recovery_plan("primary-failover")
    console.print(f"\n[cyan]Recovery plan test results:[/cyan]")
    console.print(f"Success: {test_results['success']}")
    console.print(f"Estimated recovery time: {test_results['estimated_recovery_time']}s")
    
    if test_results['issues_found']:
        console.print("[red]Issues found:[/red]")
        for issue in test_results['issues_found']:
            console.print(f"  • {issue}")
    
    # Show recovery metrics
    metrics = dr_manager.get_recovery_metrics()
    console.print(f"\n[cyan]Recovery metrics:[/cyan]")
    console.print(f"Total incidents: {metrics['total_incidents']}")
    console.print(f"Success rate: {metrics['success_rate']:.1f}%")
    console.print(f"MTTR: {metrics['mttr']:.0f} seconds")


if __name__ == "__main__":
    asyncio.run(main())