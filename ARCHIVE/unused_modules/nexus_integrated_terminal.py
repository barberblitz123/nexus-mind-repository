#!/usr/bin/env python3
"""
NEXUS Integrated Terminal - Advanced terminal with session management and more
"""

import asyncio
import json
import os
import pty
import select
import signal
import subprocess
import sys
import termios
import tty
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
import threading
from concurrent.futures import ThreadPoolExecutor
import uuid
import base64
import pickle

# Third-party imports
try:
    import paramiko
except ImportError:
    paramiko = None

try:
    import docker
except ImportError:
    docker = None

try:
    from kubernetes import client, config as k8s_config
except ImportError:
    client = None
    k8s_config = None


@dataclass
class TerminalSession:
    """Terminal session"""
    id: str
    name: str
    type: str  # local, ssh, docker, kubernetes
    process: Optional[subprocess.Popen] = None
    pty_fd: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    environment: Dict[str, str] = field(default_factory=dict)
    working_directory: Optional[Path] = None
    history: List[str] = field(default_factory=list)
    output_buffer: str = ""
    active: bool = True
    

@dataclass
class Command:
    """Command with metadata"""
    text: str
    timestamp: datetime
    directory: str
    exit_code: Optional[int] = None
    duration: Optional[float] = None
    

@dataclass
class Alias:
    """Command alias"""
    name: str
    command: str
    description: Optional[str] = None
    

@dataclass
class Function:
    """Shell function"""
    name: str
    body: str
    description: Optional[str] = None
    

class SessionManager:
    """Manage terminal sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, TerminalSession] = {}
        self.active_session_id: Optional[str] = None
        self.session_storage = Path.home() / ".nexus" / "terminal_sessions"
        self.session_storage.mkdir(parents=True, exist_ok=True)
        
    def create_session(
        self,
        name: str,
        session_type: str = "local",
        **kwargs
    ) -> TerminalSession:
        """Create new terminal session"""
        session_id = str(uuid.uuid4())
        
        session = TerminalSession(
            id=session_id,
            name=name,
            type=session_type,
            environment=kwargs.get("environment", os.environ.copy()),
            working_directory=kwargs.get("working_directory", Path.cwd())
        )
        
        # Create PTY for session
        if session_type == "local":
            self._create_local_pty(session)
        elif session_type == "ssh":
            self._create_ssh_session(session, **kwargs)
        elif session_type == "docker":
            self._create_docker_session(session, **kwargs)
        elif session_type == "kubernetes":
            self._create_k8s_session(session, **kwargs)
            
        self.sessions[session_id] = session
        self.active_session_id = session_id
        
        return session
        
    def _create_local_pty(self, session: TerminalSession):
        """Create local PTY session"""
        # Create pseudo-terminal
        master_fd, slave_fd = pty.openpty()
        
        # Start shell process
        shell = os.environ.get("SHELL", "/bin/bash")
        process = subprocess.Popen(
            [shell],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            env=session.environment,
            cwd=session.working_directory,
            preexec_fn=os.setsid
        )
        
        session.process = process
        session.pty_fd = master_fd
        
        # Close slave fd in parent
        os.close(slave_fd)
        
    def _create_ssh_session(self, session: TerminalSession, **kwargs):
        """Create SSH session"""
        if not paramiko:
            raise ImportError("paramiko required for SSH sessions")
            
        hostname = kwargs.get("hostname")
        username = kwargs.get("username")
        password = kwargs.get("password")
        key_file = kwargs.get("key_file")
        port = kwargs.get("port", 22)
        
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect
        connect_kwargs = {
            "hostname": hostname,
            "port": port,
            "username": username
        }
        
        if password:
            connect_kwargs["password"] = password
        elif key_file:
            connect_kwargs["key_filename"] = key_file
            
        ssh.connect(**connect_kwargs)
        
        # Get shell channel
        channel = ssh.invoke_shell()
        
        # Store SSH client and channel
        session.ssh_client = ssh
        session.channel = channel
        
    def _create_docker_session(self, session: TerminalSession, **kwargs):
        """Create Docker container session"""
        if not docker:
            raise ImportError("docker required for Docker sessions")
            
        container_id = kwargs.get("container_id")
        image = kwargs.get("image")
        command = kwargs.get("command", "/bin/bash")
        
        # Create Docker client
        docker_client = docker.from_env()
        
        if container_id:
            # Attach to existing container
            container = docker_client.containers.get(container_id)
        else:
            # Create new container
            container = docker_client.containers.run(
                image,
                command=command,
                detach=True,
                tty=True,
                stdin_open=True
            )
            
        # Execute command in container
        exec_instance = container.exec_run(
            command,
            stdin=True,
            tty=True,
            stream=True,
            socket=True
        )
        
        session.container = container
        session.exec_instance = exec_instance
        
    def _create_k8s_session(self, session: TerminalSession, **kwargs):
        """Create Kubernetes pod session"""
        if not client or not k8s_config:
            raise ImportError("kubernetes required for Kubernetes sessions")
            
        pod_name = kwargs.get("pod_name")
        namespace = kwargs.get("namespace", "default")
        container = kwargs.get("container")
        command = kwargs.get("command", ["/bin/bash"])
        
        # Load Kubernetes config
        try:
            k8s_config.load_incluster_config()
        except Exception:
            k8s_config.load_kube_config()
            
        # Create API client
        v1 = client.CoreV1Api()
        
        # Create exec stream
        exec_stream = client.stream.stream(
            v1.connect_get_namespaced_pod_exec,
            pod_name,
            namespace,
            container=container,
            command=command,
            stderr=True,
            stdin=True,
            stdout=True,
            tty=True,
            _preload_content=False
        )
        
        session.k8s_stream = exec_stream
        
    def get_session(self, session_id: str) -> Optional[TerminalSession]:
        """Get session by ID"""
        return self.sessions.get(session_id)
        
    def list_sessions(self) -> List[TerminalSession]:
        """List all sessions"""
        return list(self.sessions.values())
        
    def switch_session(self, session_id: str) -> bool:
        """Switch to different session"""
        if session_id in self.sessions:
            self.active_session_id = session_id
            return True
        return False
        
    def close_session(self, session_id: str):
        """Close terminal session"""
        session = self.sessions.get(session_id)
        if not session:
            return
            
        session.active = False
        
        # Clean up based on session type
        if session.type == "local" and session.process:
            session.process.terminate()
            if session.pty_fd:
                os.close(session.pty_fd)
        elif session.type == "ssh" and hasattr(session, "ssh_client"):
            session.ssh_client.close()
        elif session.type == "docker" and hasattr(session, "container"):
            # Don't stop container, just detach
            pass
        elif session.type == "kubernetes" and hasattr(session, "k8s_stream"):
            session.k8s_stream.close()
            
        del self.sessions[session_id]
        
        # Switch to another session if this was active
        if self.active_session_id == session_id:
            if self.sessions:
                self.active_session_id = list(self.sessions.keys())[0]
            else:
                self.active_session_id = None
                
    def save_session(self, session_id: str):
        """Save session state to disk"""
        session = self.sessions.get(session_id)
        if not session:
            return
            
        # Prepare session data for serialization
        session_data = {
            "id": session.id,
            "name": session.name,
            "type": session.type,
            "created_at": session.created_at.isoformat(),
            "environment": session.environment,
            "working_directory": str(session.working_directory),
            "history": session.history[-1000:],  # Save last 1000 commands
        }
        
        # Save to file
        session_file = self.session_storage / f"{session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
            
    def restore_session(self, session_id: str) -> Optional[TerminalSession]:
        """Restore session from disk"""
        session_file = self.session_storage / f"{session_id}.json"
        if not session_file.exists():
            return None
            
        with open(session_file, 'r') as f:
            session_data = json.load(f)
            
        # Recreate session
        session = self.create_session(
            name=session_data["name"],
            session_type=session_data["type"],
            environment=session_data["environment"],
            working_directory=Path(session_data["working_directory"])
        )
        
        # Restore history
        session.history = session_data["history"]
        
        return session
        

class CommandHistory:
    """Command history management"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.history: List[Command] = []
        self.history_file = Path.home() / ".nexus" / "terminal_history"
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_history()
        
    def _load_history(self):
        """Load history from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            parts = line.strip().split('\t', 3)
                            if len(parts) >= 3:
                                self.history.append(Command(
                                    text=parts[2],
                                    timestamp=datetime.fromisoformat(parts[0]),
                                    directory=parts[1],
                                    exit_code=int(parts[3]) if len(parts) > 3 else None
                                ))
            except Exception:
                pass
                
    def add_command(self, command: Command):
        """Add command to history"""
        self.history.append(command)
        
        # Limit history size
        if len(self.history) > self.max_size:
            self.history = self.history[-self.max_size:]
            
        # Save to file
        self._save_command(command)
        
    def _save_command(self, command: Command):
        """Save command to history file"""
        with open(self.history_file, 'a') as f:
            f.write(f"{command.timestamp.isoformat()}\t"
                   f"{command.directory}\t"
                   f"{command.text}\t"
                   f"{command.exit_code or ''}\n")
            
    def search(self, query: str, limit: int = 50) -> List[Command]:
        """Search command history"""
        results = []
        query_lower = query.lower()
        
        for cmd in reversed(self.history):
            if query_lower in cmd.text.lower():
                results.append(cmd)
                if len(results) >= limit:
                    break
                    
        return results
        
    def get_recent(self, count: int = 50) -> List[Command]:
        """Get recent commands"""
        return self.history[-count:]
        

class AliasManager:
    """Manage command aliases"""
    
    def __init__(self):
        self.aliases: Dict[str, Alias] = {}
        self.alias_file = Path.home() / ".nexus" / "terminal_aliases"
        self.alias_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_aliases()
        
    def _load_aliases(self):
        """Load aliases from file"""
        if self.alias_file.exists():
            try:
                with open(self.alias_file, 'r') as f:
                    data = json.load(f)
                    for name, info in data.items():
                        self.aliases[name] = Alias(
                            name=name,
                            command=info["command"],
                            description=info.get("description")
                        )
            except Exception:
                pass
                
    def add_alias(self, name: str, command: str, description: Optional[str] = None):
        """Add command alias"""
        self.aliases[name] = Alias(name, command, description)
        self._save_aliases()
        
    def remove_alias(self, name: str):
        """Remove alias"""
        if name in self.aliases:
            del self.aliases[name]
            self._save_aliases()
            
    def get_alias(self, name: str) -> Optional[Alias]:
        """Get alias by name"""
        return self.aliases.get(name)
        
    def list_aliases(self) -> List[Alias]:
        """List all aliases"""
        return list(self.aliases.values())
        
    def _save_aliases(self):
        """Save aliases to file"""
        data = {
            name: {
                "command": alias.command,
                "description": alias.description
            }
            for name, alias in self.aliases.items()
        }
        
        with open(self.alias_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def expand_command(self, command: str) -> str:
        """Expand aliases in command"""
        parts = command.split()
        if parts and parts[0] in self.aliases:
            alias = self.aliases[parts[0]]
            expanded = alias.command
            if len(parts) > 1:
                # Replace $1, $2, etc. with arguments
                for i, arg in enumerate(parts[1:], 1):
                    expanded = expanded.replace(f"${i}", arg)
                # Replace $* with all arguments
                expanded = expanded.replace("$*", " ".join(parts[1:]))
            return expanded
        return command
        

class EnvironmentManager:
    """Manage environment variables"""
    
    def __init__(self):
        self.env_file = Path.home() / ".nexus" / "terminal_env"
        self.env_file.parent.mkdir(parents=True, exist_ok=True)
        self.custom_env: Dict[str, str] = {}
        self._load_environment()
        
    def _load_environment(self):
        """Load custom environment variables"""
        if self.env_file.exists():
            try:
                with open(self.env_file, 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            self.custom_env[key] = value
            except Exception:
                pass
                
    def set_variable(self, key: str, value: str, persist: bool = False):
        """Set environment variable"""
        os.environ[key] = value
        
        if persist:
            self.custom_env[key] = value
            self._save_environment()
            
    def unset_variable(self, key: str):
        """Unset environment variable"""
        if key in os.environ:
            del os.environ[key]
            
        if key in self.custom_env:
            del self.custom_env[key]
            self._save_environment()
            
    def get_variable(self, key: str) -> Optional[str]:
        """Get environment variable"""
        return os.environ.get(key)
        
    def list_variables(self, custom_only: bool = False) -> Dict[str, str]:
        """List environment variables"""
        if custom_only:
            return self.custom_env.copy()
        return dict(os.environ)
        
    def _save_environment(self):
        """Save custom environment variables"""
        with open(self.env_file, 'w') as f:
            for key, value in self.custom_env.items():
                f.write(f"{key}={value}\n")
                
    def apply_to_session(self, session: TerminalSession):
        """Apply custom environment to session"""
        session.environment.update(self.custom_env)
        

class SSHManager:
    """Manage SSH connections"""
    
    def __init__(self):
        self.ssh_config_file = Path.home() / ".ssh" / "config"
        self.known_hosts: List[Dict[str, Any]] = []
        self._load_ssh_config()
        
    def _load_ssh_config(self):
        """Load SSH configuration"""
        if self.ssh_config_file.exists():
            # Parse SSH config
            pass
            
    def add_host(
        self,
        alias: str,
        hostname: str,
        username: str,
        port: int = 22,
        key_file: Optional[str] = None
    ):
        """Add SSH host configuration"""
        host_config = {
            "alias": alias,
            "hostname": hostname,
            "username": username,
            "port": port,
            "key_file": key_file
        }
        self.known_hosts.append(host_config)
        
    def get_host(self, alias: str) -> Optional[Dict[str, Any]]:
        """Get host configuration by alias"""
        for host in self.known_hosts:
            if host["alias"] == alias:
                return host
        return None
        
    def list_hosts(self) -> List[Dict[str, Any]]:
        """List known SSH hosts"""
        return self.known_hosts
        

class DockerIntegration:
    """Docker container integration"""
    
    def __init__(self):
        self.client = docker.from_env() if docker else None
        
    def list_containers(self, all: bool = False) -> List[Dict[str, Any]]:
        """List Docker containers"""
        if not self.client:
            return []
            
        containers = []
        for container in self.client.containers.list(all=all):
            containers.append({
                "id": container.short_id,
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else container.image.id,
                "status": container.status,
                "ports": container.ports
            })
            
        return containers
        
    def exec_in_container(
        self,
        container_id: str,
        command: List[str]
    ) -> Tuple[int, str]:
        """Execute command in container"""
        if not self.client:
            return -1, "Docker not available"
            
        try:
            container = self.client.containers.get(container_id)
            result = container.exec_run(command)
            return result.exit_code, result.output.decode()
        except Exception as e:
            return -1, str(e)
            

class KubernetesIntegration:
    """Kubernetes pod integration"""
    
    def __init__(self):
        if client and k8s_config:
            try:
                k8s_config.load_incluster_config()
            except Exception:
                try:
                    k8s_config.load_kube_config()
                except Exception:
                    pass
            self.v1 = client.CoreV1Api()
        else:
            self.v1 = None
            
    def list_pods(self, namespace: str = "default") -> List[Dict[str, Any]]:
        """List Kubernetes pods"""
        if not self.v1:
            return []
            
        pods = []
        try:
            pod_list = self.v1.list_namespaced_pod(namespace)
            for pod in pod_list.items:
                pods.append({
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase,
                    "containers": [c.name for c in pod.spec.containers],
                    "node": pod.spec.node_name
                })
        except Exception:
            pass
            
        return pods
        
    def get_pod_logs(
        self,
        pod_name: str,
        namespace: str = "default",
        container: Optional[str] = None,
        tail_lines: int = 100
    ) -> str:
        """Get pod logs"""
        if not self.v1:
            return ""
            
        try:
            return self.v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines
            )
        except Exception as e:
            return f"Error: {e}"
            

class NexusIntegratedTerminal:
    """Integrated terminal with advanced features"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.history = CommandHistory()
        self.aliases = AliasManager()
        self.environment = EnvironmentManager()
        self.ssh_manager = SSHManager()
        self.docker = DockerIntegration()
        self.kubernetes = KubernetesIntegration()
        
        # Create default session
        self.session_manager.create_session("main", "local")
        
    def execute_command(self, command: str) -> Tuple[int, str]:
        """Execute command in active session"""
        session = self.get_active_session()
        if not session:
            return -1, "No active session"
            
        # Expand aliases
        command = self.aliases.expand_command(command)
        
        # Record in history
        cmd = Command(
            text=command,
            timestamp=datetime.now(),
            directory=str(session.working_directory or Path.cwd())
        )
        
        # Execute based on session type
        if session.type == "local":
            exit_code, output = self._execute_local(session, command)
        elif session.type == "ssh":
            exit_code, output = self._execute_ssh(session, command)
        elif session.type == "docker":
            exit_code, output = self._execute_docker(session, command)
        elif session.type == "kubernetes":
            exit_code, output = self._execute_k8s(session, command)
        else:
            exit_code, output = -1, f"Unknown session type: {session.type}"
            
        # Update command with results
        cmd.exit_code = exit_code
        cmd.duration = (datetime.now() - cmd.timestamp).total_seconds()
        
        # Add to history
        self.history.add_command(cmd)
        session.history.append(command)
        
        return exit_code, output
        
    def _execute_local(self, session: TerminalSession, command: str) -> Tuple[int, str]:
        """Execute command in local session"""
        if not session.pty_fd:
            return -1, "PTY not available"
            
        # Write command to PTY
        os.write(session.pty_fd, (command + '\n').encode())
        
        # Read output
        output = ""
        while True:
            try:
                # Check if data available
                ready, _, _ = select.select([session.pty_fd], [], [], 0.1)
                if ready:
                    data = os.read(session.pty_fd, 1024)
                    if data:
                        output += data.decode('utf-8', errors='replace')
                    else:
                        break
                else:
                    # Check if process still running
                    if session.process and session.process.poll() is not None:
                        break
                    # If no more data and process running, we're done
                    if output and not ready:
                        break
            except OSError:
                break
                
        # Get exit code
        exit_code = 0
        if session.process:
            exit_code = session.process.returncode or 0
            
        return exit_code, output
        
    def _execute_ssh(self, session: TerminalSession, command: str) -> Tuple[int, str]:
        """Execute command in SSH session"""
        if not hasattr(session, 'channel'):
            return -1, "SSH channel not available"
            
        # Send command
        session.channel.send(command + '\n')
        
        # Read output
        output = ""
        while True:
            if session.channel.recv_ready():
                data = session.channel.recv(1024)
                output += data.decode('utf-8', errors='replace')
            else:
                break
                
        return 0, output  # SSH doesn't easily provide exit codes
        
    def _execute_docker(self, session: TerminalSession, command: str) -> Tuple[int, str]:
        """Execute command in Docker session"""
        if not hasattr(session, 'container'):
            return -1, "Docker container not available"
            
        result = session.container.exec_run(command)
        return result.exit_code, result.output.decode()
        
    def _execute_k8s(self, session: TerminalSession, command: str) -> Tuple[int, str]:
        """Execute command in Kubernetes session"""
        if not hasattr(session, 'k8s_stream'):
            return -1, "Kubernetes stream not available"
            
        # Send command
        session.k8s_stream.write_stdin(command + '\n')
        
        # Read output
        output = ""
        while session.k8s_stream.is_open():
            if session.k8s_stream.peek_stdout():
                output += session.k8s_stream.read_stdout()
            else:
                break
                
        return 0, output
        
    def get_active_session(self) -> Optional[TerminalSession]:
        """Get active terminal session"""
        if self.session_manager.active_session_id:
            return self.session_manager.get_session(
                self.session_manager.active_session_id
            )
        return None
        
    def create_ssh_session(self, host_alias: str) -> Optional[TerminalSession]:
        """Create SSH session from host alias"""
        host_config = self.ssh_manager.get_host(host_alias)
        if not host_config:
            return None
            
        return self.session_manager.create_session(
            name=f"ssh:{host_alias}",
            session_type="ssh",
            **host_config
        )
        
    def create_docker_session(self, container_id: str) -> Optional[TerminalSession]:
        """Create Docker session"""
        containers = self.docker.list_containers()
        container = next(
            (c for c in containers if c["id"] == container_id),
            None
        )
        
        if not container:
            return None
            
        return self.session_manager.create_session(
            name=f"docker:{container['name']}",
            session_type="docker",
            container_id=container_id
        )
        
    def create_k8s_session(
        self,
        pod_name: str,
        namespace: str = "default",
        container: Optional[str] = None
    ) -> Optional[TerminalSession]:
        """Create Kubernetes session"""
        return self.session_manager.create_session(
            name=f"k8s:{namespace}/{pod_name}",
            session_type="kubernetes",
            pod_name=pod_name,
            namespace=namespace,
            container=container
        )


async def main():
    """Test integrated terminal"""
    terminal = NexusIntegratedTerminal()
    
    # Test local command execution
    print("Testing local command execution...")
    exit_code, output = terminal.execute_command("echo 'Hello from NEXUS Terminal!'")
    print(f"Exit code: {exit_code}")
    print(f"Output: {output}")
    
    # Test alias
    terminal.aliases.add_alias("ll", "ls -la", "List files in long format")
    exit_code, output = terminal.execute_command("ll")
    print(f"\nAlias test output: {output[:200]}...")
    
    # Test environment
    terminal.environment.set_variable("NEXUS_TEST", "123", persist=True)
    exit_code, output = terminal.execute_command("echo $NEXUS_TEST")
    print(f"\nEnvironment test output: {output}")
    
    # Test history search
    results = terminal.history.search("echo")
    print(f"\nHistory search results: {len(results)} commands found")
    
    # List Docker containers if available
    containers = terminal.docker.list_containers()
    if containers:
        print(f"\nDocker containers: {len(containers)} found")
        for container in containers[:3]:
            print(f"  - {container['name']} ({container['status']})")
            
    # List Kubernetes pods if available
    pods = terminal.kubernetes.list_pods()
    if pods:
        print(f"\nKubernetes pods: {len(pods)} found")
        for pod in pods[:3]:
            print(f"  - {pod['name']} ({pod['status']})")


if __name__ == "__main__":
    asyncio.run(main())