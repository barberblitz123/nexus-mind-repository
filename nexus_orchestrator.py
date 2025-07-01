#!/usr/bin/env python3
"""
NEXUS Orchestration Engine
Coordinates all subsystems, manages resources, monitors health,
and optimizes performance across the entire NEXUS ecosystem
"""

import asyncio
import json
import logging
import psutil
import time
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('NEXUS-Orchestrator')


class ComponentStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    STARTING = "starting"
    STOPPING = "stopping"


class ResourceType(Enum):
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"


@dataclass
class Component:
    """Represents a NEXUS component"""
    name: str
    component_type: str
    instance: Any
    status: ComponentStatus = ComponentStatus.STARTING
    health_score: float = 1.0
    last_heartbeat: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    resource_usage: Dict[ResourceType, float] = field(default_factory=dict)


@dataclass
class Task:
    """Represents an orchestrated task"""
    id: str
    component: str
    method: str
    args: Dict[str, Any]
    priority: int = 5
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    result: Optional[Any] = None
    status: str = "pending"
    retries: int = 0
    max_retries: int = 3


class NEXUSOrchestrator:
    """Central orchestration engine for NEXUS 2.0"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        
        # Component registry
        self.components: Dict[str, Component] = {}
        self.component_lock = threading.Lock()
        
        # Task management
        self.task_queue: List[Task] = []
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.task_lock = threading.Lock()
        
        # Resource management
        self.resource_limits = self.config['resource_limits']
        self.resource_allocations: Dict[str, Dict[ResourceType, float]] = defaultdict(dict)
        
        # Performance tracking
        self.performance_metrics: Dict[str, List[float]] = defaultdict(list)
        self.optimization_history: List[Dict[str, Any]] = []
        
        # Executors for parallel processing
        self.thread_executor = ThreadPoolExecutor(max_workers=self.config['max_threads'])
        self.process_executor = ProcessPoolExecutor(max_workers=self.config['max_processes'])
        
        # System state
        self.is_running = False
        self.optimization_enabled = True
        self.auto_scaling_enabled = True
        
        # Start background tasks
        self._start_background_tasks()
        
        logger.info("NEXUS Orchestrator initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default orchestrator configuration"""
        return {
            'max_threads': 10,
            'max_processes': 4,
            'health_check_interval': 30,  # seconds
            'optimization_interval': 300,  # 5 minutes
            'resource_check_interval': 10,
            'task_timeout': 300,  # 5 minutes
            'resource_limits': {
                ResourceType.CPU: 80.0,      # 80% max CPU
                ResourceType.MEMORY: 75.0,   # 75% max memory
                ResourceType.DISK: 90.0,     # 90% max disk
                ResourceType.NETWORK: 100.0, # No network limit
                ResourceType.GPU: 95.0       # 95% max GPU if available
            },
            'degradation_thresholds': {
                'health_score': 0.7,
                'resource_usage': 0.8,
                'task_failure_rate': 0.2
            }
        }
    
    def register_component(self, name: str, component: Any, 
                          component_type: str, dependencies: Optional[List[str]] = None) -> bool:
        """Register a new component with the orchestrator"""
        with self.component_lock:
            if name in self.components:
                logger.warning(f"Component {name} already registered")
                return False
            
            comp = Component(
                name=name,
                component_type=component_type,
                instance=component,
                dependencies=dependencies or []
            )
            
            # Validate dependencies
            for dep in comp.dependencies:
                if dep not in self.components:
                    logger.error(f"Dependency {dep} not found for component {name}")
                    return False
            
            self.components[name] = comp
            logger.info(f"Registered component: {name} ({component_type})")
            
            # Start health monitoring
            asyncio.create_task(self._monitor_component_health(name))
            
            return True
    
    def unregister_component(self, name: str) -> bool:
        """Unregister a component"""
        with self.component_lock:
            if name not in self.components:
                return False
            
            # Check for dependencies
            dependent_components = [
                comp_name for comp_name, comp in self.components.items()
                if name in comp.dependencies
            ]
            
            if dependent_components:
                logger.error(f"Cannot unregister {name}, required by: {dependent_components}")
                return False
            
            # Stop any active tasks for this component
            self._cancel_component_tasks(name)
            
            del self.components[name]
            logger.info(f"Unregistered component: {name}")
            return True
    
    async def execute_task(self, component: str, method: str, 
                          args: Optional[Dict[str, Any]] = None,
                          priority: int = 5,
                          deadline: Optional[datetime] = None) -> str:
        """Execute a task on a component"""
        task = Task(
            id=f"task_{datetime.now().timestamp()}_{component}_{method}",
            component=component,
            method=method,
            args=args or {},
            priority=priority,
            deadline=deadline
        )
        
        with self.task_lock:
            # Add to queue sorted by priority
            self.task_queue.append(task)
            self.task_queue.sort(key=lambda t: t.priority, reverse=True)
        
        logger.info(f"Queued task {task.id} for {component}.{method}")
        
        # Trigger task processing
        asyncio.create_task(self._process_tasks())
        
        return task.id
    
    async def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """Get result of a task (blocking until complete)"""
        start_time = time.time()
        
        while True:
            # Check completed tasks
            if task_id in self.completed_tasks:
                task = self.completed_tasks[task_id]
                if task.status == 'completed':
                    return task.result
                else:
                    raise Exception(f"Task {task_id} failed: {task.result}")
            
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Task {task_id} timed out")
            
            await asyncio.sleep(0.1)
    
    def get_component_status(self, component: Optional[str] = None) -> Dict[str, Any]:
        """Get status of one or all components"""
        with self.component_lock:
            if component:
                if component not in self.components:
                    return {'error': f'Component {component} not found'}
                
                comp = self.components[component]
                return self._get_component_info(comp)
            else:
                # Return all component statuses
                return {
                    name: self._get_component_info(comp)
                    for name, comp in self.components.items()
                }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        with self.component_lock:
            total_components = len(self.components)
            healthy_components = sum(
                1 for comp in self.components.values()
                if comp.status == ComponentStatus.HEALTHY
            )
            
            # Calculate system health score
            if total_components > 0:
                component_health = healthy_components / total_components
            else:
                component_health = 0.0
            
            # Get resource usage
            resource_usage = self._get_system_resource_usage()
            
            # Calculate resource health
            resource_health = 1.0
            for resource_type, usage in resource_usage.items():
                limit = self.resource_limits.get(resource_type, 100.0)
                if usage > limit:
                    resource_health *= (limit / usage)
            
            # Get task metrics
            task_metrics = self._get_task_metrics()
            
            # Overall health score
            overall_health = (
                component_health * 0.4 +
                resource_health * 0.3 +
                task_metrics['success_rate'] * 0.3
            )
            
            return {
                'overall_health': overall_health,
                'component_health': component_health,
                'resource_health': resource_health,
                'task_health': task_metrics['success_rate'],
                'total_components': total_components,
                'healthy_components': healthy_components,
                'resource_usage': resource_usage,
                'task_metrics': task_metrics,
                'timestamp': datetime.now().isoformat()
            }
    
    async def optimize_performance(self) -> Dict[str, Any]:
        """Optimize system performance"""
        logger.info("Starting performance optimization...")
        
        optimizations = []
        
        # 1. Resource reallocation
        resource_opt = await self._optimize_resource_allocation()
        if resource_opt:
            optimizations.append(resource_opt)
        
        # 2. Task scheduling optimization
        task_opt = self._optimize_task_scheduling()
        if task_opt:
            optimizations.append(task_opt)
        
        # 3. Component scaling
        if self.auto_scaling_enabled:
            scaling_opt = await self._optimize_component_scaling()
            if scaling_opt:
                optimizations.append(scaling_opt)
        
        # 4. Cache optimization
        cache_opt = self._optimize_caches()
        if cache_opt:
            optimizations.append(cache_opt)
        
        # Record optimization
        optimization_record = {
            'timestamp': datetime.now().isoformat(),
            'optimizations': optimizations,
            'health_before': self.get_system_health()['overall_health']
        }
        
        # Apply optimizations
        for opt in optimizations:
            await self._apply_optimization(opt)
        
        # Measure improvement
        optimization_record['health_after'] = self.get_system_health()['overall_health']
        optimization_record['improvement'] = (
            optimization_record['health_after'] - optimization_record['health_before']
        )
        
        self.optimization_history.append(optimization_record)
        
        logger.info(f"Optimization complete. Improvement: {optimization_record['improvement']:.2%}")
        
        return optimization_record
    
    async def handle_degradation(self, component: str, reason: str) -> Dict[str, Any]:
        """Handle component degradation"""
        logger.warning(f"Handling degradation for {component}: {reason}")
        
        actions = []
        
        with self.component_lock:
            if component not in self.components:
                return {'error': f'Component {component} not found'}
            
            comp = self.components[component]
            comp.status = ComponentStatus.DEGRADED
            
            # 1. Reduce load on degraded component
            load_reduction = self._reduce_component_load(component)
            if load_reduction:
                actions.append(load_reduction)
            
            # 2. Redirect tasks to healthy components
            task_redirect = await self._redirect_tasks(component)
            if task_redirect:
                actions.append(task_redirect)
            
            # 3. Attempt recovery
            recovery = await self._attempt_recovery(component)
            if recovery:
                actions.append(recovery)
            
            # 4. Notify dependent components
            notification = self._notify_dependents(component, reason)
            if notification:
                actions.append(notification)
        
        return {
            'component': component,
            'reason': reason,
            'actions_taken': actions,
            'timestamp': datetime.now().isoformat()
        }
    
    # Background tasks
    def _start_background_tasks(self):
        """Start all background monitoring and optimization tasks"""
        self.is_running = True
        
        # Health monitoring
        asyncio.create_task(self._health_monitor_loop())
        
        # Resource monitoring
        asyncio.create_task(self._resource_monitor_loop())
        
        # Performance optimization
        asyncio.create_task(self._optimization_loop())
        
        # Task processing
        asyncio.create_task(self._task_processor_loop())
        
        logger.info("Background tasks started")
    
    async def _health_monitor_loop(self):
        """Monitor component health"""
        while self.is_running:
            try:
                interval = self.config['health_check_interval']
                await asyncio.sleep(interval)
                
                with self.component_lock:
                    for name, comp in self.components.items():
                        # Check heartbeat
                        time_since_heartbeat = (datetime.now() - comp.last_heartbeat).seconds
                        
                        if time_since_heartbeat > interval * 2:
                            # Component unresponsive
                            if comp.status != ComponentStatus.FAILED:
                                logger.error(f"Component {name} unresponsive")
                                comp.status = ComponentStatus.FAILED
                                await self.handle_degradation(name, "Unresponsive")
                        
                        # Check health score
                        elif comp.health_score < self.config['degradation_thresholds']['health_score']:
                            if comp.status == ComponentStatus.HEALTHY:
                                await self.handle_degradation(name, f"Low health score: {comp.health_score}")
                
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
    
    async def _resource_monitor_loop(self):
        """Monitor system resources"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config['resource_check_interval'])
                
                # Get current resource usage
                usage = self._get_system_resource_usage()
                
                # Check against limits
                for resource_type, current_usage in usage.items():
                    limit = self.resource_limits.get(resource_type, 100.0)
                    
                    if current_usage > limit:
                        logger.warning(f"{resource_type.value} usage ({current_usage:.1f}%) exceeds limit ({limit:.1f}%)")
                        
                        # Trigger resource optimization
                        if self.optimization_enabled:
                            await self._optimize_resource_allocation()
                
                # Update component resource usage
                self._update_component_resources()
                
            except Exception as e:
                logger.error(f"Error in resource monitor: {e}")
    
    async def _optimization_loop(self):
        """Periodic performance optimization"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config['optimization_interval'])
                
                if self.optimization_enabled:
                    await self.optimize_performance()
                
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
    
    async def _task_processor_loop(self):
        """Process queued tasks"""
        while self.is_running:
            try:
                await self._process_tasks()
                await asyncio.sleep(0.1)  # Small delay to prevent busy loop
                
            except Exception as e:
                logger.error(f"Error in task processor: {e}")
    
    async def _process_tasks(self):
        """Process pending tasks from queue"""
        with self.task_lock:
            if not self.task_queue:
                return
            
            # Get tasks that can be executed
            executable_tasks = []
            
            for task in self.task_queue[:]:
                # Check dependencies
                if all(dep in self.completed_tasks for dep in task.dependencies):
                    # Check if component is healthy
                    if task.component in self.components:
                        comp = self.components[task.component]
                        if comp.status in [ComponentStatus.HEALTHY, ComponentStatus.DEGRADED]:
                            executable_tasks.append(task)
                            self.task_queue.remove(task)
            
            # Execute tasks in parallel
            for task in executable_tasks:
                self.active_tasks[task.id] = task
                asyncio.create_task(self._execute_single_task(task))
    
    async def _execute_single_task(self, task: Task):
        """Execute a single task"""
        try:
            # Get component
            comp = self.components.get(task.component)
            if not comp:
                raise Exception(f"Component {task.component} not found")
            
            # Get method
            method = getattr(comp.instance, task.method, None)
            if not method:
                raise Exception(f"Method {task.method} not found on {task.component}")
            
            # Set timeout
            timeout = self.config['task_timeout']
            if task.deadline:
                timeout = min(timeout, (task.deadline - datetime.now()).seconds)
            
            # Execute with timeout
            task.status = 'executing'
            
            if asyncio.iscoroutinefunction(method):
                result = await asyncio.wait_for(method(**task.args), timeout=timeout)
            else:
                # Run in thread executor for blocking calls
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        self.thread_executor, method, **task.args
                    ),
                    timeout=timeout
                )
            
            # Success
            task.status = 'completed'
            task.result = result
            
            # Update metrics
            self._record_task_success(task)
            
        except asyncio.TimeoutError:
            task.status = 'timeout'
            task.result = f"Task timed out after {timeout} seconds"
            self._record_task_failure(task)
            
        except Exception as e:
            task.status = 'failed'
            task.result = str(e)
            self._record_task_failure(task)
            
            # Retry logic
            if task.retries < task.max_retries:
                task.retries += 1
                task.status = 'pending'
                with self.task_lock:
                    self.task_queue.append(task)
                logger.info(f"Retrying task {task.id} (attempt {task.retries})")
                return
        
        finally:
            # Move to completed
            with self.task_lock:
                if task.id in self.active_tasks:
                    del self.active_tasks[task.id]
                self.completed_tasks[task.id] = task
    
    # Helper methods
    def _get_component_info(self, comp: Component) -> Dict[str, Any]:
        """Get detailed component information"""
        return {
            'name': comp.name,
            'type': comp.component_type,
            'status': comp.status.value,
            'health_score': comp.health_score,
            'last_heartbeat': comp.last_heartbeat.isoformat(),
            'dependencies': comp.dependencies,
            'resource_usage': {
                rt.value: usage for rt, usage in comp.resource_usage.items()
            },
            'metadata': comp.metadata
        }
    
    def _get_system_resource_usage(self) -> Dict[ResourceType, float]:
        """Get current system resource usage"""
        usage = {}
        
        # CPU usage
        usage[ResourceType.CPU] = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        usage[ResourceType.MEMORY] = psutil.virtual_memory().percent
        
        # Disk usage
        usage[ResourceType.DISK] = psutil.disk_usage('/').percent
        
        # Network usage (simplified - just checking if network is available)
        usage[ResourceType.NETWORK] = 0.0  # Would need more complex monitoring
        
        # GPU usage (if available)
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            info = pynvml.nvmlDeviceGetUtilizationRates(handle)
            usage[ResourceType.GPU] = float(info.gpu)
        except:
            usage[ResourceType.GPU] = 0.0
        
        return usage
    
    def _get_task_metrics(self) -> Dict[str, Any]:
        """Get task execution metrics"""
        total_tasks = len(self.completed_tasks)
        if total_tasks == 0:
            return {
                'total_tasks': 0,
                'success_rate': 1.0,
                'average_execution_time': 0.0,
                'pending_tasks': len(self.task_queue),
                'active_tasks': len(self.active_tasks)
            }
        
        successful_tasks = sum(
            1 for task in self.completed_tasks.values()
            if task.status == 'completed'
        )
        
        execution_times = []
        for task in self.completed_tasks.values():
            if hasattr(task, 'completed_at'):
                exec_time = (task.completed_at - task.created_at).seconds
                execution_times.append(exec_time)
        
        return {
            'total_tasks': total_tasks,
            'success_rate': successful_tasks / total_tasks,
            'average_execution_time': sum(execution_times) / len(execution_times) if execution_times else 0.0,
            'pending_tasks': len(self.task_queue),
            'active_tasks': len(self.active_tasks)
        }
    
    async def _monitor_component_health(self, component_name: str):
        """Monitor individual component health"""
        while component_name in self.components:
            try:
                comp = self.components[component_name]
                
                # Check if component has health check method
                if hasattr(comp.instance, 'health_check'):
                    health = await comp.instance.health_check()
                    comp.health_score = health.get('score', 1.0)
                    comp.last_heartbeat = datetime.now()
                    
                    # Update status based on health
                    if comp.health_score >= 0.8:
                        comp.status = ComponentStatus.HEALTHY
                    elif comp.health_score >= 0.5:
                        comp.status = ComponentStatus.DEGRADED
                    else:
                        comp.status = ComponentStatus.FAILED
                
                await asyncio.sleep(self.config['health_check_interval'])
                
            except Exception as e:
                logger.error(f"Error monitoring {component_name}: {e}")
                await asyncio.sleep(60)  # Longer wait on error
    
    def _cancel_component_tasks(self, component: str):
        """Cancel all tasks for a component"""
        with self.task_lock:
            # Remove from queue
            self.task_queue = [
                task for task in self.task_queue
                if task.component != component
            ]
            
            # Mark active tasks as cancelled
            for task_id, task in self.active_tasks.items():
                if task.component == component:
                    task.status = 'cancelled'
                    task.result = 'Component unregistered'
    
    async def _optimize_resource_allocation(self) -> Optional[Dict[str, Any]]:
        """Optimize resource allocation across components"""
        current_usage = self._get_system_resource_usage()
        
        optimizations = []
        
        # Check for over-utilized resources
        for resource_type, usage in current_usage.items():
            limit = self.resource_limits.get(resource_type, 100.0)
            
            if usage > limit * 0.9:  # 90% of limit
                # Find components using most of this resource
                heavy_users = self._find_heavy_resource_users(resource_type)
                
                for component_name, component_usage in heavy_users[:3]:  # Top 3
                    if component_usage > 20.0:  # Using more than 20%
                        optimizations.append({
                            'type': 'resource_reduction',
                            'component': component_name,
                            'resource': resource_type.value,
                            'current_usage': component_usage,
                            'target_usage': component_usage * 0.8  # Reduce by 20%
                        })
        
        if optimizations:
            return {
                'optimization_type': 'resource_allocation',
                'optimizations': optimizations
            }
        
        return None
    
    def _optimize_task_scheduling(self) -> Optional[Dict[str, Any]]:
        """Optimize task scheduling"""
        with self.task_lock:
            if len(self.task_queue) < 10:
                return None
            
            # Reorder tasks based on:
            # 1. Priority
            # 2. Component health
            # 3. Resource availability
            
            def task_score(task: Task) -> float:
                score = task.priority * 10
                
                # Boost score for healthy components
                if task.component in self.components:
                    comp = self.components[task.component]
                    score *= comp.health_score
                
                # Penalize tasks with many dependencies
                score -= len(task.dependencies) * 2
                
                # Boost urgent tasks
                if task.deadline:
                    time_remaining = (task.deadline - datetime.now()).seconds
                    if time_remaining < 300:  # Less than 5 minutes
                        score *= 2
                
                return score
            
            # Re-sort queue
            self.task_queue.sort(key=task_score, reverse=True)
            
            return {
                'optimization_type': 'task_scheduling',
                'reordered_tasks': len(self.task_queue)
            }
    
    async def _optimize_component_scaling(self) -> Optional[Dict[str, Any]]:
        """Optimize component scaling"""
        scaling_actions = []
        
        # Check for components that need scaling
        for name, comp in self.components.items():
            if hasattr(comp.instance, 'get_load'):
                load = await comp.instance.get_load()
                
                # Scale up if overloaded
                if load > 0.8 and hasattr(comp.instance, 'scale_up'):
                    scaling_actions.append({
                        'component': name,
                        'action': 'scale_up',
                        'current_load': load,
                        'reason': 'High load'
                    })
                
                # Scale down if underutilized
                elif load < 0.2 and hasattr(comp.instance, 'scale_down'):
                    scaling_actions.append({
                        'component': name,
                        'action': 'scale_down',
                        'current_load': load,
                        'reason': 'Low utilization'
                    })
        
        if scaling_actions:
            return {
                'optimization_type': 'component_scaling',
                'scaling_actions': scaling_actions
            }
        
        return None
    
    def _optimize_caches(self) -> Optional[Dict[str, Any]]:
        """Optimize component caches"""
        cache_optimizations = []
        
        for name, comp in self.components.items():
            if hasattr(comp.instance, 'optimize_cache'):
                cache_optimizations.append({
                    'component': name,
                    'action': 'optimize_cache'
                })
        
        if cache_optimizations:
            return {
                'optimization_type': 'cache_optimization',
                'components': cache_optimizations
            }
        
        return None
    
    async def _apply_optimization(self, optimization: Dict[str, Any]):
        """Apply a specific optimization"""
        opt_type = optimization['optimization_type']
        
        if opt_type == 'resource_allocation':
            for opt in optimization['optimizations']:
                component = opt['component']
                if component in self.components:
                    comp = self.components[component]
                    if hasattr(comp.instance, 'set_resource_limit'):
                        await comp.instance.set_resource_limit(
                            opt['resource'],
                            opt['target_usage']
                        )
        
        elif opt_type == 'component_scaling':
            for action in optimization['scaling_actions']:
                component = action['component']
                if component in self.components:
                    comp = self.components[component]
                    if action['action'] == 'scale_up':
                        await comp.instance.scale_up()
                    elif action['action'] == 'scale_down':
                        await comp.instance.scale_down()
        
        elif opt_type == 'cache_optimization':
            for comp_info in optimization['components']:
                component = comp_info['component']
                if component in self.components:
                    comp = self.components[component]
                    await comp.instance.optimize_cache()
    
    def _reduce_component_load(self, component: str) -> Optional[Dict[str, Any]]:
        """Reduce load on a specific component"""
        # Throttle incoming tasks
        with self.task_lock:
            # Reduce priority of tasks for this component
            for task in self.task_queue:
                if task.component == component:
                    task.priority = max(1, task.priority - 2)
            
            # Re-sort queue
            self.task_queue.sort(key=lambda t: t.priority, reverse=True)
        
        return {
            'action': 'load_reduction',
            'component': component,
            'method': 'task_priority_reduction'
        }
    
    async def _redirect_tasks(self, component: str) -> Optional[Dict[str, Any]]:
        """Redirect tasks from degraded component"""
        redirected = 0
        
        with self.task_lock:
            # Find alternative components
            comp = self.components.get(component)
            if not comp:
                return None
            
            alternatives = [
                name for name, c in self.components.items()
                if c.component_type == comp.component_type 
                and c.status == ComponentStatus.HEALTHY
                and name != component
            ]
            
            if alternatives:
                # Redirect pending tasks
                for task in self.task_queue[:]:
                    if task.component == component:
                        # Assign to least loaded alternative
                        task.component = alternatives[0]  # Simple selection
                        redirected += 1
        
        if redirected > 0:
            return {
                'action': 'task_redirection',
                'from_component': component,
                'redirected_tasks': redirected
            }
        
        return None
    
    async def _attempt_recovery(self, component: str) -> Optional[Dict[str, Any]]:
        """Attempt to recover a degraded component"""
        comp = self.components.get(component)
        if not comp:
            return None
        
        recovery_actions = []
        
        # Try restart if available
        if hasattr(comp.instance, 'restart'):
            try:
                await comp.instance.restart()
                recovery_actions.append('restart')
            except Exception as e:
                logger.error(f"Failed to restart {component}: {e}")
        
        # Clear caches if available
        if hasattr(comp.instance, 'clear_cache'):
            try:
                await comp.instance.clear_cache()
                recovery_actions.append('cache_clear')
            except Exception as e:
                logger.error(f"Failed to clear cache for {component}: {e}")
        
        if recovery_actions:
            return {
                'action': 'recovery_attempt',
                'component': component,
                'recovery_actions': recovery_actions
            }
        
        return None
    
    def _notify_dependents(self, component: str, reason: str) -> Optional[Dict[str, Any]]:
        """Notify dependent components of degradation"""
        notifications = []
        
        for name, comp in self.components.items():
            if component in comp.dependencies:
                if hasattr(comp.instance, 'handle_dependency_degradation'):
                    try:
                        comp.instance.handle_dependency_degradation(component, reason)
                        notifications.append(name)
                    except Exception as e:
                        logger.error(f"Failed to notify {name}: {e}")
        
        if notifications:
            return {
                'action': 'dependency_notification',
                'degraded_component': component,
                'notified_components': notifications
            }
        
        return None
    
    def _find_heavy_resource_users(self, resource_type: ResourceType) -> List[Tuple[str, float]]:
        """Find components using most of a resource type"""
        users = []
        
        for name, comp in self.components.items():
            usage = comp.resource_usage.get(resource_type, 0.0)
            if usage > 0:
                users.append((name, usage))
        
        # Sort by usage descending
        users.sort(key=lambda x: x[1], reverse=True)
        
        return users
    
    def _update_component_resources(self):
        """Update resource usage for each component"""
        # This would need component-specific monitoring
        # For now, simulate with random values
        import random
        
        for comp in self.components.values():
            comp.resource_usage[ResourceType.CPU] = random.uniform(5, 30)
            comp.resource_usage[ResourceType.MEMORY] = random.uniform(10, 40)
    
    def _record_task_success(self, task: Task):
        """Record successful task execution"""
        component = task.component
        if component not in self.performance_metrics:
            self.performance_metrics[component] = []
        
        self.performance_metrics[component].append(1.0)
        
        # Keep only recent metrics
        if len(self.performance_metrics[component]) > 100:
            self.performance_metrics[component] = self.performance_metrics[component][-100:]
    
    def _record_task_failure(self, task: Task):
        """Record failed task execution"""
        component = task.component
        if component not in self.performance_metrics:
            self.performance_metrics[component] = []
        
        self.performance_metrics[component].append(0.0)
        
        # Keep only recent metrics
        if len(self.performance_metrics[component]) > 100:
            self.performance_metrics[component] = self.performance_metrics[component][-100:]
    
    async def shutdown(self):
        """Gracefully shutdown the orchestrator"""
        logger.info("Shutting down NEXUS Orchestrator...")
        
        self.is_running = False
        
        # Cancel all pending tasks
        with self.task_lock:
            for task in self.task_queue:
                task.status = 'cancelled'
                task.result = 'Orchestrator shutdown'
        
        # Shutdown executors
        self.thread_executor.shutdown(wait=True)
        self.process_executor.shutdown(wait=True)
        
        logger.info("NEXUS Orchestrator shutdown complete")


# Demo function
async def demo_orchestrator():
    """Demonstrate orchestrator capabilities"""
    
    # Create orchestrator
    orchestrator = NEXUSOrchestrator()
    
    # Create mock components
    class MockComponent:
        def __init__(self, name):
            self.name = name
            self.load = 0.5
        
        async def health_check(self):
            return {'score': 0.9, 'status': 'healthy'}
        
        async def process(self, data):
            await asyncio.sleep(0.1)  # Simulate work
            return f"Processed by {self.name}: {data}"
        
        async def get_load(self):
            return self.load
    
    # Register components
    comp1 = MockComponent("processor1")
    comp2 = MockComponent("processor2")
    comp3 = MockComponent("analyzer")
    
    orchestrator.register_component("processor1", comp1, "processor")
    orchestrator.register_component("processor2", comp2, "processor")
    orchestrator.register_component("analyzer", comp3, "analyzer", dependencies=["processor1"])
    
    # Get system status
    print("System Health:", json.dumps(orchestrator.get_system_health(), indent=2))
    
    # Execute some tasks
    task1_id = await orchestrator.execute_task("processor1", "process", {"data": "test1"}, priority=8)
    task2_id = await orchestrator.execute_task("processor2", "process", {"data": "test2"}, priority=5)
    task3_id = await orchestrator.execute_task("analyzer", "process", {"data": "analyze"}, priority=10)
    
    # Wait for results
    result1 = await orchestrator.get_task_result(task1_id, timeout=5)
    print(f"Task 1 result: {result1}")
    
    # Get component status
    status = orchestrator.get_component_status()
    print("Component Status:", json.dumps(status, indent=2))
    
    # Trigger optimization
    opt_result = await orchestrator.optimize_performance()
    print("Optimization Result:", json.dumps(opt_result, indent=2))
    
    # Simulate degradation
    comp1.load = 0.9
    degradation_result = await orchestrator.handle_degradation("processor1", "High load detected")
    print("Degradation Handling:", json.dumps(degradation_result, indent=2))
    
    # Final health check
    final_health = orchestrator.get_system_health()
    print("Final System Health:", json.dumps(final_health, indent=2))
    
    # Shutdown
    await orchestrator.shutdown()


if __name__ == "__main__":
    asyncio.run(demo_orchestrator())