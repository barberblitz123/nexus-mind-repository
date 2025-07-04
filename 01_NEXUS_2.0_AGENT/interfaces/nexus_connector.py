#!/usr/bin/env python3
"""
NEXUS 2.0 Connector
Bridges the web interface to REAL agent execution

This replaces simulation with actual Python subprocess execution,
file operations, and real agent capabilities.
"""

import os
import sys
import asyncio
import subprocess
import tempfile
import json
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.nexus_logger import get_logger


@dataclass
class AgentCapabilities:
    """Defines what an agent can actually do"""
    can_execute_code: bool = True
    can_run_shell: bool = True
    can_write_files: bool = True
    can_read_files: bool = True
    can_access_network: bool = True
    can_spawn_subagents: bool = True
    memory_enabled: bool = True
    learning_enabled: bool = True


@dataclass
class ExecutionResult:
    """Result of executing a real action"""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    files_created: List[str] = None
    files_modified: List[str] = None
    metadata: Dict[str, Any] = None


class RealAgentExecutor:
    """Executes REAL agent actions - not simulations"""
    
    def __init__(self, agent_id: str, capabilities: AgentCapabilities = None):
        self.agent_id = agent_id
        self.capabilities = capabilities or AgentCapabilities()
        self.logger = get_logger()
        self.working_dir = Path(f"/tmp/nexus_agents/{agent_id}")
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        # Agent memory (persistent across tasks)
        self.memory = {
            "created_at": datetime.now().isoformat(),
            "tasks_completed": 0,
            "learned_patterns": {},
            "error_history": [],
            "success_history": []
        }
        
        self.logger.info(f"Real Agent Executor initialized", agent_id=agent_id)
    
    async def execute_task(self, task_description: str) -> ExecutionResult:
        """Execute a real task based on natural language description"""
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        self.logger.log_system_event(f"Task started: {task_description}", {"task_id": task_id})
        
        start_time = time.time()
        
        try:
            # Parse task into actionable steps
            steps = self._parse_task(task_description)
            
            results = []
            for step in steps:
                self.logger.log_agent_activity(self.agent_id, f"Executing: {step['action']}")
                
                if step['type'] == 'code':
                    result = await self._execute_code(step['content'])
                elif step['type'] == 'shell':
                    result = await self._execute_shell(step['content'])
                elif step['type'] == 'file_write':
                    result = await self._write_file(step['path'], step['content'])
                elif step['type'] == 'file_read':
                    result = await self._read_file(step['path'])
                else:
                    result = ExecutionResult(False, "", f"Unknown step type: {step['type']}")
                
                results.append(result)
                
                if not result.success:
                    # Learn from error
                    self._learn_from_error(task_description, step, result.error)
                    break
            
            # Aggregate results
            all_success = all(r.success for r in results)
            combined_output = "\n".join(r.output for r in results if r.output)
            combined_errors = "\n".join(r.error for r in results if r.error)
            
            execution_time = time.time() - start_time
            
            if all_success:
                self.logger.log_system_event(f"Task completed in {execution_time:.2f}s", {
                    "task_id": task_id,
                    "execution_time": execution_time,
                    "success": True
                })
                self.memory["tasks_completed"] += 1
                self.memory["success_history"].append({
                    "task": task_description,
                    "timestamp": datetime.now().isoformat(),
                    "execution_time": execution_time
                })
            else:
                self.logger.log_error(Exception(combined_errors), f"Task {task_id} failed")
                
            return ExecutionResult(
                success=all_success,
                output=combined_output,
                error=combined_errors if not all_success else None,
                execution_time=execution_time,
                metadata={"task_id": task_id, "steps_completed": len(results)}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.log_error(e, f"Task {task_id} failed")
            
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                execution_time=execution_time,
                metadata={"task_id": task_id, "exception": type(e).__name__}
            )
    
    def _parse_task(self, task_description: str) -> List[Dict[str, Any]]:
        """Parse natural language task into executable steps"""
        steps = []
        
        # Simple pattern matching for now
        # TODO: Replace with LLM-based parsing for complex tasks
        
        task_lower = task_description.lower()
        
        if "analyze" in task_lower and "code" in task_lower:
            steps.append({
                "type": "shell",
                "action": "List Python files",
                "content": "find . -name '*.py' -type f | head -20"
            })
            steps.append({
                "type": "code",
                "action": "Analyze code structure",
                "content": '''
import os
import ast

files = [f for f in os.listdir('.') if f.endswith('.py')][:5]
for file in files:
    try:
        with open(file, 'r') as f:
            tree = ast.parse(f.read())
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        print(f"\n{file}:")
        print(f"  Classes: {classes}")
        print(f"  Functions: {functions[:5]}..." if len(functions) > 5 else f"  Functions: {functions}")
    except:
        pass
'''
            })
            
        elif "create" in task_lower and "file" in task_lower:
            # Extract filename if provided
            import re
            filename_match = re.search(r'file[\s:]+([\w.-]+)', task_description, re.I)
            filename = filename_match.group(1) if filename_match else "new_file.txt"
            
            steps.append({
                "type": "file_write",
                "action": f"Create file {filename}",
                "path": filename,
                "content": f"# File created by NEXUS Agent\n# Task: {task_description}\n# Created: {datetime.now()}\n"
            })
            
        elif "run" in task_lower and "test" in task_lower:
            steps.append({
                "type": "shell",
                "action": "Run tests",
                "content": "python -m pytest -v --tb=short 2>/dev/null || echo 'No tests found or pytest not installed'"
            })
            
        elif "install" in task_lower:
            package_match = re.search(r'install\s+([\w.-]+)', task_description, re.I)
            package = package_match.group(1) if package_match else "requests"
            
            steps.append({
                "type": "shell",
                "action": f"Install package {package}",
                "content": f"pip install {package}"
            })
            
        else:
            # Default: try to execute as shell command
            steps.append({
                "type": "shell",
                "action": "Execute command",
                "content": task_description
            })
        
        return steps
    
    async def _execute_code(self, code: str) -> ExecutionResult:
        """Execute Python code in a subprocess"""
        if not self.capabilities.can_execute_code:
            return ExecutionResult(False, "", "Code execution disabled")
        
        try:
            # Write code to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute in subprocess
            process = await asyncio.create_subprocess_exec(
                sys.executable, temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.working_dir)
            )
            
            stdout, stderr = await process.communicate()
            
            # Clean up
            os.unlink(temp_file)
            
            if process.returncode == 0:
                return ExecutionResult(
                    success=True,
                    output=stdout.decode('utf-8'),
                    execution_time=0  # TODO: measure actual time
                )
            else:
                return ExecutionResult(
                    success=False,
                    output=stdout.decode('utf-8'),
                    error=stderr.decode('utf-8')
                )
                
        except Exception as e:
            return ExecutionResult(False, "", str(e))
    
    async def _execute_shell(self, command: str) -> ExecutionResult:
        """Execute shell command"""
        if not self.capabilities.can_run_shell:
            return ExecutionResult(False, "", "Shell execution disabled")
        
        try:
            # Security: Basic command filtering
            dangerous_commands = ['rm -rf /', 'sudo', 'chmod 777', 'curl | sh']
            if any(danger in command for danger in dangerous_commands):
                return ExecutionResult(False, "", "Command blocked for security")
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.working_dir)
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return ExecutionResult(
                    success=True,
                    output=stdout.decode('utf-8')
                )
            else:
                return ExecutionResult(
                    success=False,
                    output=stdout.decode('utf-8'),
                    error=stderr.decode('utf-8')
                )
                
        except Exception as e:
            return ExecutionResult(False, "", str(e))
    
    async def _write_file(self, path: str, content: str) -> ExecutionResult:
        """Write content to file"""
        if not self.capabilities.can_write_files:
            return ExecutionResult(False, "", "File writing disabled")
        
        try:
            file_path = self.working_dir / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            return ExecutionResult(
                success=True,
                output=f"File written: {file_path}",
                files_created=[str(file_path)]
            )
            
        except Exception as e:
            return ExecutionResult(False, "", str(e))
    
    async def _read_file(self, path: str) -> ExecutionResult:
        """Read file content"""
        if not self.capabilities.can_read_files:
            return ExecutionResult(False, "", "File reading disabled")
        
        try:
            file_path = self.working_dir / path
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            return ExecutionResult(
                success=True,
                output=content
            )
            
        except Exception as e:
            return ExecutionResult(False, "", str(e))
    
    def _learn_from_error(self, task: str, step: Dict, error: str):
        """Learn from execution errors to improve future performance"""
        if not self.capabilities.learning_enabled:
            return
        
        # Store error pattern
        error_pattern = {
            "task": task,
            "step": step,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        self.memory["error_history"].append(error_pattern)
        
        # Simple pattern recognition
        if "command not found" in error:
            self.memory["learned_patterns"]["missing_commands"] = \
                self.memory["learned_patterns"].get("missing_commands", []) + [step['content']]
        elif "permission denied" in error:
            self.memory["learned_patterns"]["permission_issues"] = \
                self.memory["learned_patterns"].get("permission_issues", []) + [step['content']]
        
        # Limit memory size
        if len(self.memory["error_history"]) > 100:
            self.memory["error_history"] = self.memory["error_history"][-50:]


class NEXUSConnector:
    """Main connector between web interface and real agent system"""
    
    def __init__(self):
        self.logger = get_logger()
        self.agents: Dict[str, RealAgentExecutor] = {}
        self.logger.info("NEXUS Connector initialized - Real execution enabled")
    
    async def create_agent(self, agent_id: str, name: str, agent_type: str) -> Dict[str, Any]:
        """Create a real agent executor"""
        # Define capabilities based on agent type
        capabilities = AgentCapabilities()
        
        if agent_type == "developer":
            capabilities.can_execute_code = True
            capabilities.can_write_files = True
        elif agent_type == "analyst":
            capabilities.can_execute_code = True
            capabilities.can_read_files = True
            capabilities.can_run_shell = False  # Limited shell access
        elif agent_type == "devops":
            capabilities.can_run_shell = True
            capabilities.can_access_network = True
        
        # Create real executor
        executor = RealAgentExecutor(agent_id, capabilities)
        self.agents[agent_id] = executor
        
        self.logger.info(f"Created real agent: {name} ({agent_type})", agent_id=agent_id, audit=True)
        
        return {
            "agent_id": agent_id,
            "name": name,
            "type": agent_type,
            "capabilities": asdict(capabilities),
            "status": "ready"
        }
    
    async def execute_agent_task(self, agent_id: str, task: str) -> Dict[str, Any]:
        """Execute a real task on an agent"""
        if agent_id not in self.agents:
            return {
                "success": False,
                "error": f"Agent {agent_id} not found"
            }
        
        executor = self.agents[agent_id]
        result = await executor.execute_task(task)
        
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "execution_time": result.execution_time,
            "metadata": result.metadata
        }
    
    async def get_agent_memory(self, agent_id: str) -> Dict[str, Any]:
        """Get agent's memory/learning state"""
        if agent_id not in self.agents:
            return {}
        
        return self.agents[agent_id].memory
    
    async def export_logs(self) -> str:
        """Export system logs"""
        export_path = self.logger.export_logs(format='json')
        return str(export_path)
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        metrics = self.logger.get_metrics_summary()
        
        # Add agent metrics
        metrics["agents"] = {
            "total": len(self.agents),
            "active": len([a for a in self.agents.values() if a.memory["tasks_completed"] > 0]),
            "total_tasks_completed": sum(a.memory["tasks_completed"] for a in self.agents.values())
        }
        
        return metrics


# Global connector instance
_connector = None

def get_connector() -> NEXUSConnector:
    """Get or create the global connector instance"""
    global _connector
    if _connector is None:
        _connector = NEXUSConnector()
    return _connector


if __name__ == "__main__":
    # Test the connector
    async def test():
        connector = get_connector()
        
        # Create an agent
        agent = await connector.create_agent("test-001", "Test Agent", "developer")
        print(f"Created agent: {agent}")
        
        # Execute some tasks
        tasks = [
            "analyze code in current directory",
            "create file test_output.py with hello world",
            "list files in current directory"
        ]
        
        for task in tasks:
            print(f"\nExecuting: {task}")
            result = await connector.execute_agent_task(agent['agent_id'], task)
            print(f"Success: {result['success']}")
            print(f"Output: {result['output'][:200]}..." if len(result['output']) > 200 else f"Output: {result['output']}")
            if result['error']:
                print(f"Error: {result['error']}")
        
        # Check memory
        memory = await connector.get_agent_memory(agent['agent_id'])
        print(f"\nAgent memory: {json.dumps(memory, indent=2)}")
        
        # Export logs
        log_path = await connector.export_logs()
        print(f"\nLogs exported to: {log_path}")
    
    # Run test
    asyncio.run(test())