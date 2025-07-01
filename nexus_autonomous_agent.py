#!/usr/bin/env python3
"""
NEXUS Autonomous MANUS Agent
Self-directed agent with goal reasoning, predictive task generation,
and self-improvement capabilities
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import random
from dataclasses import dataclass, field
from enum import Enum

from nexus_enhanced_manus import EnhancedMANUSOmnipotent
from nexus_memory_core import NexusUnifiedMemory, MemoryEntry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('NEXUS-Autonomous')


class TaskPriority(Enum):
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    BACKGROUND = 1


class GoalStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    SUSPENDED = "suspended"


@dataclass
class Goal:
    """Represents an autonomous goal"""
    id: str
    description: str
    priority: TaskPriority
    status: GoalStatus = GoalStatus.PENDING
    progress: float = 0.0
    sub_goals: List['Goal'] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    deadline: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'description': self.description,
            'priority': self.priority.value,
            'status': self.status.value,
            'progress': self.progress,
            'sub_goals': [g.to_dict() for g in self.sub_goals],
            'dependencies': self.dependencies,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class PredictedTask:
    """Represents a predicted future task"""
    id: str
    description: str
    confidence: float
    estimated_time: timedelta
    prerequisites: List[str] = field(default_factory=list)
    rationale: str = ""
    predicted_at: datetime = field(default_factory=datetime.now)


class AutonomousMANUSAgent(EnhancedMANUSOmnipotent):
    """Autonomous agent with self-direction and goal reasoning"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize autonomous components
        self.memory = NexusUnifiedMemory()
        self.goals: Dict[str, Goal] = {}
        self.active_goals: List[Goal] = []
        self.task_queue: List[PredictedTask] = []
        self.learning_history: List[Dict[str, Any]] = []
        
        # Autonomous behavior settings
        self.autonomy_level = 0.8  # 0-1 scale
        self.creativity_factor = 0.6
        self.risk_tolerance = 0.4
        self.learning_rate = 0.1
        
        # Performance tracking
        self.success_rate = 0.5
        self.efficiency_score = 0.5
        self.innovation_score = 0.5
        
        # Set unique capabilities
        self.unique_capabilities.update({
            'autonomous_goal_generation',
            'predictive_task_planning',
            'self_improvement',
            'adaptive_learning',
            'proactive_problem_solving'
        })
        
        # Start autonomous processes
        asyncio.create_task(self._autonomous_loop())
        asyncio.create_task(self._learning_loop())
        
        logger.info("Autonomous MANUS Agent initialized")
    
    async def execute_specialty(self, context: Dict[str, Any]) -> Any:
        """Execute autonomous operations"""
        command = context.get('command', 'status')
        
        if command == 'status':
            return await self._get_autonomous_status()
        
        elif command == 'set_goal':
            return await self._set_goal(context)
        
        elif command == 'generate_goals':
            return await self._generate_goals(context)
        
        elif command == 'predict_tasks':
            return await self._predict_tasks(context)
        
        elif command == 'improve':
            return await self._self_improve(context)
        
        elif command == 'learn':
            return await self._learn_from_experience(context)
        
        elif command == 'autonomous_execute':
            return await self._autonomous_execute(context)
        
        else:
            # Delegate to parent class
            return await super().execute_specialty(context)
    
    async def _get_autonomous_status(self) -> Dict[str, Any]:
        """Get current autonomous agent status"""
        return {
            'active_goals': len(self.active_goals),
            'total_goals': len(self.goals),
            'queued_tasks': len(self.task_queue),
            'autonomy_level': self.autonomy_level,
            'performance': {
                'success_rate': self.success_rate,
                'efficiency': self.efficiency_score,
                'innovation': self.innovation_score
            },
            'current_focus': self.active_goals[0].description if self.active_goals else "Idle",
            'learning_events': len(self.learning_history),
            'capabilities': list(self.unique_capabilities)
        }
    
    async def _set_goal(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Set a new autonomous goal"""
        description = context.get('description', '')
        priority = TaskPriority(context.get('priority', TaskPriority.MEDIUM.value))
        deadline = context.get('deadline')
        
        goal = Goal(
            id=self._generate_goal_id(),
            description=description,
            priority=priority,
            deadline=datetime.fromisoformat(deadline) if deadline else None,
            metadata=context.get('metadata', {})
        )
        
        # Store goal
        self.goals[goal.id] = goal
        
        # Store in goal memory
        await self.memory.goal_memory.store(MemoryEntry(
            id=goal.id,
            content=goal.description,
            metadata=goal.metadata,
            importance=priority.value / 5.0
        ))
        
        # Analyze and decompose goal
        sub_goals = await self._decompose_goal(goal)
        goal.sub_goals = sub_goals
        
        # Add to active goals if high priority
        if priority.value >= TaskPriority.HIGH.value:
            self.active_goals.append(goal)
            self.active_goals.sort(key=lambda g: g.priority.value, reverse=True)
        
        return {
            'goal_id': goal.id,
            'goal': goal.to_dict(),
            'sub_goals': len(sub_goals),
            'estimated_completion': self._estimate_completion_time(goal)
        }
    
    async def _generate_goals(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate goals autonomously based on context"""
        domain = context.get('domain', 'general')
        
        # Analyze current state
        current_context = self.memory.context_memory.get_current_context()
        recent_memories = await self.memory.retrieve("recent activities", n_results=10)
        
        # Use memory fusion to identify patterns
        fusion_result = await self.memory.fusion.fuse_memories(
            f"{domain} improvements opportunities",
            memory_types=['learning', 'episodic', 'semantic']
        )
        
        generated_goals = []
        
        # Generate goals based on insights
        insights = fusion_result.get('insights', [])
        
        # Pattern-based goal generation
        if "Goals align with recent learnings" in insights:
            goal = Goal(
                id=self._generate_goal_id(),
                description=f"Apply recent learnings to improve {domain} performance",
                priority=TaskPriority.HIGH,
                metadata={'type': 'learning_application', 'domain': domain}
            )
            generated_goals.append(goal)
        
        # Performance-based goals
        if self.efficiency_score < 0.7:
            goal = Goal(
                id=self._generate_goal_id(),
                description=f"Optimize {domain} processes to improve efficiency by 20%",
                priority=TaskPriority.MEDIUM,
                metadata={'type': 'optimization', 'target_improvement': 0.2}
            )
            generated_goals.append(goal)
        
        # Innovation goals
        if self.innovation_score < 0.6 and self.creativity_factor > 0.5:
            goal = Goal(
                id=self._generate_goal_id(),
                description=f"Develop innovative solutions for {domain} challenges",
                priority=TaskPriority.MEDIUM,
                metadata={'type': 'innovation', 'creativity_required': True}
            )
            generated_goals.append(goal)
        
        # Predictive maintenance goals
        if random.random() < 0.3:  # 30% chance
            goal = Goal(
                id=self._generate_goal_id(),
                description=f"Proactively identify and fix potential issues in {domain}",
                priority=TaskPriority.LOW,
                metadata={'type': 'maintenance', 'proactive': True}
            )
            generated_goals.append(goal)
        
        # Store generated goals
        for goal in generated_goals:
            self.goals[goal.id] = goal
            await self.memory.goal_memory.store(MemoryEntry(
                id=goal.id,
                content=goal.description,
                metadata=goal.metadata,
                importance=goal.priority.value / 5.0
            ))
        
        return {
            'generated_goals': [g.to_dict() for g in generated_goals],
            'total_generated': len(generated_goals),
            'fusion_insights': insights,
            'rationale': f"Generated goals based on current state and {domain} analysis"
        }
    
    async def _predict_tasks(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Predict future tasks based on patterns"""
        time_horizon = context.get('horizon_days', 7)
        
        # Analyze historical patterns
        historical_tasks = await self.memory.episodic_memory.search(
            "task completed",
            n_results=50
        )
        
        # Analyze current goals
        active_goal_tasks = []
        for goal in self.active_goals:
            tasks = await self._generate_tasks_for_goal(goal)
            active_goal_tasks.extend(tasks)
        
        # Use learning memory to predict patterns
        learning_patterns = await self.memory.learning_memory.search(
            "task pattern",
            n_results=10
        )
        
        predicted_tasks = []
        
        # Pattern-based predictions
        for pattern in learning_patterns:
            if pattern.importance > 0.6:  # High success patterns
                task = PredictedTask(
                    id=self._generate_task_id(),
                    description=f"Apply pattern: {pattern.content.get('pattern', '')}",
                    confidence=pattern.importance,
                    estimated_time=timedelta(hours=2),
                    rationale="Based on successful historical pattern"
                )
                predicted_tasks.append(task)
        
        # Goal-based predictions
        for task_desc in active_goal_tasks[:5]:  # Top 5 tasks
            task = PredictedTask(
                id=self._generate_task_id(),
                description=task_desc,
                confidence=0.8,
                estimated_time=timedelta(hours=4),
                rationale="Required for active goal completion"
            )
            predicted_tasks.append(task)
        
        # Maintenance predictions
        if datetime.now().weekday() == 0:  # Monday
            task = PredictedTask(
                id=self._generate_task_id(),
                description="Weekly system maintenance and optimization",
                confidence=0.9,
                estimated_time=timedelta(hours=1),
                rationale="Regular maintenance schedule"
            )
            predicted_tasks.append(task)
        
        # Innovation predictions
        if self.creativity_factor > 0.5 and random.random() < self.creativity_factor:
            task = PredictedTask(
                id=self._generate_task_id(),
                description="Explore new approaches and innovative solutions",
                confidence=0.6,
                estimated_time=timedelta(hours=3),
                rationale="Maintaining innovation momentum"
            )
            predicted_tasks.append(task)
        
        # Sort by confidence
        predicted_tasks.sort(key=lambda t: t.confidence, reverse=True)
        
        # Add to queue
        self.task_queue.extend(predicted_tasks[:10])  # Keep top 10
        
        return {
            'predicted_tasks': [
                {
                    'id': t.id,
                    'description': t.description,
                    'confidence': t.confidence,
                    'estimated_hours': t.estimated_time.total_seconds() / 3600,
                    'rationale': t.rationale
                }
                for t in predicted_tasks
            ],
            'total_predicted': len(predicted_tasks),
            'queue_size': len(self.task_queue),
            'time_horizon_days': time_horizon
        }
    
    async def _self_improve(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Implement self-improvement mechanisms"""
        aspect = context.get('aspect', 'general')
        
        improvements = []
        
        # Analyze performance metrics
        if self.success_rate < 0.7:
            # Learn from failures
            failures = await self.memory.learning_memory.search("failure", n_results=10)
            
            improvement = {
                'aspect': 'success_rate',
                'current': self.success_rate,
                'action': 'Analyze failure patterns and adjust strategies',
                'expected_improvement': 0.1
            }
            improvements.append(improvement)
            
            # Adjust risk tolerance
            self.risk_tolerance *= 0.9
            logger.info(f"Reduced risk tolerance to {self.risk_tolerance}")
        
        # Efficiency improvements
        if self.efficiency_score < 0.8:
            improvement = {
                'aspect': 'efficiency',
                'current': self.efficiency_score,
                'action': 'Optimize task execution patterns',
                'expected_improvement': 0.15
            }
            improvements.append(improvement)
            
            # Increase parallel processing
            self._quantum_state['parallel_execution'] = True
        
        # Innovation improvements
        if self.innovation_score < 0.6:
            improvement = {
                'aspect': 'innovation',
                'current': self.innovation_score,
                'action': 'Increase creativity factor and exploration',
                'expected_improvement': 0.2
            }
            improvements.append(improvement)
            
            # Increase creativity
            self.creativity_factor = min(0.9, self.creativity_factor * 1.2)
        
        # Apply learning rate
        self.success_rate += self.learning_rate * 0.1
        self.efficiency_score += self.learning_rate * 0.05
        self.innovation_score += self.learning_rate * 0.08
        
        # Store improvement record
        improvement_record = {
            'timestamp': datetime.now().isoformat(),
            'improvements': improvements,
            'new_settings': {
                'risk_tolerance': self.risk_tolerance,
                'creativity_factor': self.creativity_factor,
                'learning_rate': self.learning_rate
            }
        }
        
        await self.memory.learning_memory.store(MemoryEntry(
            id=f"improvement_{datetime.now().timestamp()}",
            content=improvement_record,
            metadata={'type': 'self_improvement', 'aspect': aspect},
            importance=0.8
        ))
        
        return {
            'improvements_applied': improvements,
            'performance_metrics': {
                'success_rate': self.success_rate,
                'efficiency': self.efficiency_score,
                'innovation': self.innovation_score
            },
            'settings_updated': improvement_record['new_settings']
        }
    
    async def _learn_from_experience(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Learn from recent experiences"""
        experience_type = context.get('type', 'general')
        
        # Retrieve recent experiences
        recent_experiences = await self.memory.episodic_memory.search(
            experience_type,
            n_results=20
        )
        
        learnings = []
        
        for exp in recent_experiences:
            # Analyze outcome
            outcome = exp.metadata.get('outcome', 'unknown')
            if outcome == 'success':
                # Extract successful pattern
                pattern = {
                    'pattern': exp.content,
                    'outcome': 'success',
                    'confidence': 0.8,
                    'context': exp.metadata
                }
                
                learning = MemoryEntry(
                    id=f"learning_{exp.id}",
                    content=pattern,
                    metadata={'type': 'success_pattern', 'source': exp.id},
                    importance=0.7
                )
                
                await self.memory.learning_memory.store(learning)
                learnings.append(pattern)
                
            elif outcome == 'failure':
                # Learn from failure
                pattern = {
                    'pattern': exp.content,
                    'outcome': 'failure',
                    'lesson': 'Avoid similar approach',
                    'alternative': exp.metadata.get('alternative', 'Unknown')
                }
                
                learning = MemoryEntry(
                    id=f"learning_failure_{exp.id}",
                    content=pattern,
                    metadata={'type': 'failure_pattern', 'source': exp.id},
                    importance=0.6
                )
                
                await self.memory.learning_memory.store(learning)
                learnings.append(pattern)
        
        # Update learning history
        self.learning_history.append({
            'timestamp': datetime.now().isoformat(),
            'type': experience_type,
            'learnings_extracted': len(learnings),
            'experiences_analyzed': len(recent_experiences)
        })
        
        # Adjust learning rate based on success
        if learnings:
            self.learning_rate = min(0.3, self.learning_rate * 1.1)
        
        return {
            'learnings_extracted': learnings[:5],  # Top 5 learnings
            'total_learnings': len(learnings),
            'experiences_analyzed': len(recent_experiences),
            'updated_learning_rate': self.learning_rate
        }
    
    async def _autonomous_execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tasks autonomously"""
        max_duration = context.get('max_duration_minutes', 60)
        start_time = datetime.now()
        
        executed_tasks = []
        
        while (datetime.now() - start_time).seconds < max_duration * 60:
            # Select next task
            task = await self._select_next_task()
            
            if not task:
                # Generate new task if queue empty
                await self._predict_tasks({'horizon_days': 1})
                task = await self._select_next_task()
            
            if not task:
                break
            
            # Execute task
            try:
                result = await self._execute_task(task)
                executed_tasks.append({
                    'task': task.description,
                    'result': result,
                    'duration': (datetime.now() - task.predicted_at).seconds
                })
                
                # Learn from execution
                await self._learn_from_execution(task, result)
                
                # Update metrics
                if result.get('success', False):
                    self.success_rate = (self.success_rate * 0.9 + 1.0 * 0.1)
                else:
                    self.success_rate = (self.success_rate * 0.9 + 0.0 * 0.1)
                
            except Exception as e:
                logger.error(f"Error executing task {task.id}: {e}")
                executed_tasks.append({
                    'task': task.description,
                    'error': str(e),
                    'duration': 0
                })
            
            # Check if should continue
            if self.autonomy_level < random.random():
                break
        
        return {
            'executed_tasks': executed_tasks,
            'total_executed': len(executed_tasks),
            'duration_minutes': (datetime.now() - start_time).seconds / 60,
            'current_metrics': {
                'success_rate': self.success_rate,
                'autonomy_level': self.autonomy_level
            }
        }
    
    async def _autonomous_loop(self):
        """Main autonomous operation loop"""
        while True:
            try:
                # Check if autonomous mode is active
                if self.autonomy_level > 0.5:
                    # Review goals
                    await self._review_goals()
                    
                    # Generate new goals if needed
                    if len(self.active_goals) < 3:
                        await self._generate_goals({'domain': 'system_optimization'})
                    
                    # Predict upcoming tasks
                    if len(self.task_queue) < 5:
                        await self._predict_tasks({'horizon_days': 3})
                    
                    # Execute pending tasks
                    if self.task_queue and random.random() < self.autonomy_level:
                        await self._autonomous_execute({'max_duration_minutes': 10})
                
                # Sleep based on autonomy level
                sleep_time = 60 * (2 - self.autonomy_level)  # More autonomous = more frequent
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in autonomous loop: {e}")
                await asyncio.sleep(300)  # 5 minute cooldown on error
    
    async def _learning_loop(self):
        """Continuous learning loop"""
        while True:
            try:
                # Learn from recent experiences
                await self._learn_from_experience({'type': 'recent'})
                
                # Self-improve periodically
                if random.random() < 0.1:  # 10% chance each cycle
                    await self._self_improve({'aspect': 'adaptive'})
                
                # Consolidate memories
                await self.memory.consolidate()
                
                # Sleep
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error in learning loop: {e}")
                await asyncio.sleep(600)  # 10 minute cooldown
    
    # Helper methods
    def _generate_goal_id(self) -> str:
        """Generate unique goal ID"""
        return f"goal_{datetime.now().timestamp()}_{random.randint(1000, 9999)}"
    
    def _generate_task_id(self) -> str:
        """Generate unique task ID"""
        return f"task_{datetime.now().timestamp()}_{random.randint(1000, 9999)}"
    
    async def _decompose_goal(self, goal: Goal) -> List[Goal]:
        """Decompose goal into sub-goals"""
        sub_goals = []
        
        # Simple decomposition based on keywords
        if "optimize" in goal.description.lower():
            sub_goals.extend([
                Goal(
                    id=self._generate_goal_id(),
                    description=f"Analyze current performance for {goal.description}",
                    priority=TaskPriority(max(1, goal.priority.value - 1)),
                    metadata={'parent': goal.id, 'phase': 'analysis'}
                ),
                Goal(
                    id=self._generate_goal_id(),
                    description=f"Identify bottlenecks in {goal.description}",
                    priority=TaskPriority(max(1, goal.priority.value - 1)),
                    metadata={'parent': goal.id, 'phase': 'diagnosis'}
                ),
                Goal(
                    id=self._generate_goal_id(),
                    description=f"Implement improvements for {goal.description}",
                    priority=goal.priority,
                    metadata={'parent': goal.id, 'phase': 'implementation'}
                )
            ])
        
        elif "develop" in goal.description.lower() or "create" in goal.description.lower():
            sub_goals.extend([
                Goal(
                    id=self._generate_goal_id(),
                    description=f"Design architecture for {goal.description}",
                    priority=goal.priority,
                    metadata={'parent': goal.id, 'phase': 'design'}
                ),
                Goal(
                    id=self._generate_goal_id(),
                    description=f"Implement core functionality for {goal.description}",
                    priority=goal.priority,
                    metadata={'parent': goal.id, 'phase': 'development'}
                ),
                Goal(
                    id=self._generate_goal_id(),
                    description=f"Test and validate {goal.description}",
                    priority=TaskPriority(max(1, goal.priority.value - 1)),
                    metadata={'parent': goal.id, 'phase': 'testing'}
                )
            ])
        
        return sub_goals
    
    def _estimate_completion_time(self, goal: Goal) -> str:
        """Estimate time to complete goal"""
        # Simple estimation based on priority and sub-goals
        base_hours = goal.priority.value * 4
        sub_goal_hours = len(goal.sub_goals) * 2
        total_hours = base_hours + sub_goal_hours
        
        if total_hours < 24:
            return f"{total_hours} hours"
        else:
            return f"{total_hours / 24:.1f} days"
    
    async def _generate_tasks_for_goal(self, goal: Goal) -> List[str]:
        """Generate specific tasks for a goal"""
        tasks = []
        
        # Generate tasks based on goal type
        if goal.metadata.get('type') == 'optimization':
            tasks.extend([
                f"Profile current performance metrics for {goal.description}",
                f"Identify optimization opportunities in {goal.description}",
                f"Implement optimization strategies for {goal.description}",
                f"Measure improvement results for {goal.description}"
            ])
        
        elif goal.metadata.get('type') == 'learning_application':
            tasks.extend([
                f"Review relevant learnings for {goal.description}",
                f"Create implementation plan for {goal.description}",
                f"Apply learned patterns to {goal.description}",
                f"Evaluate effectiveness of {goal.description}"
            ])
        
        else:
            # Generic task generation
            tasks.extend([
                f"Analyze requirements for {goal.description}",
                f"Plan implementation of {goal.description}",
                f"Execute {goal.description}",
                f"Validate results of {goal.description}"
            ])
        
        return tasks
    
    async def _select_next_task(self) -> Optional[PredictedTask]:
        """Select next task from queue"""
        if not self.task_queue:
            return None
        
        # Sort by confidence and select
        self.task_queue.sort(key=lambda t: t.confidence, reverse=True)
        
        # Consider prerequisites
        for task in self.task_queue:
            if not task.prerequisites or all(
                p in [t.id for t in self.task_queue if t.confidence > 0.8]
                for p in task.prerequisites
            ):
                self.task_queue.remove(task)
                return task
        
        # If no task without prerequisites, take the highest confidence
        return self.task_queue.pop(0)
    
    async def _execute_task(self, task: PredictedTask) -> Dict[str, Any]:
        """Execute a specific task"""
        logger.info(f"Executing task: {task.description}")
        
        # Simulate task execution based on description
        # In a real implementation, this would call appropriate tools
        
        result = {
            'task_id': task.id,
            'description': task.description,
            'started_at': datetime.now().isoformat(),
            'success': random.random() < (0.3 + self.success_rate * 0.7),
            'confidence': task.confidence
        }
        
        # Execute based on task type
        if "analyze" in task.description.lower():
            result['output'] = "Analysis completed successfully"
            result['findings'] = ["Pattern A identified", "Optimization opportunity found"]
        
        elif "optimize" in task.description.lower():
            result['output'] = "Optimization applied"
            result['improvement'] = random.uniform(0.1, 0.3)
        
        elif "implement" in task.description.lower():
            result['output'] = "Implementation completed"
            result['artifacts'] = ["Module created", "Tests added"]
        
        result['completed_at'] = datetime.now().isoformat()
        
        return result
    
    async def _learn_from_execution(self, task: PredictedTask, result: Dict[str, Any]):
        """Learn from task execution"""
        learning_entry = MemoryEntry(
            id=f"execution_{task.id}",
            content={
                'task': task.description,
                'result': result,
                'confidence_accuracy': abs(task.confidence - (1.0 if result['success'] else 0.0))
            },
            metadata={
                'type': 'task_execution',
                'success': result['success'],
                'task_type': self._classify_task(task.description)
            },
            importance=0.6 if result['success'] else 0.4
        )
        
        await self.memory.learning_memory.store(learning_entry)
    
    def _classify_task(self, description: str) -> str:
        """Classify task type from description"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['analyze', 'review', 'examine']):
            return 'analysis'
        elif any(word in description_lower for word in ['optimize', 'improve', 'enhance']):
            return 'optimization'
        elif any(word in description_lower for word in ['implement', 'create', 'develop']):
            return 'implementation'
        elif any(word in description_lower for word in ['test', 'validate', 'verify']):
            return 'validation'
        else:
            return 'general'
    
    async def _review_goals(self):
        """Review and update goal status"""
        for goal in list(self.active_goals):
            # Check deadline
            if goal.deadline and datetime.now() > goal.deadline:
                goal.status = GoalStatus.FAILED
                self.active_goals.remove(goal)
                logger.warning(f"Goal {goal.id} missed deadline")
            
            # Check completion
            elif goal.progress >= 1.0:
                goal.status = GoalStatus.COMPLETED
                self.active_goals.remove(goal)
                logger.info(f"Goal {goal.id} completed successfully")
                
                # Learn from success
                await self.memory.learning_memory.store(MemoryEntry(
                    id=f"goal_success_{goal.id}",
                    content={'goal': goal.description, 'approach': 'successful'},
                    metadata={'type': 'goal_completion', 'priority': goal.priority.value},
                    importance=0.8
                ))
            
            # Update progress based on sub-goals
            elif goal.sub_goals:
                completed_sub_goals = sum(1 for sg in goal.sub_goals if sg.status == GoalStatus.COMPLETED)
                goal.progress = completed_sub_goals / len(goal.sub_goals)


# Convenience functions
async def create_autonomous_agent() -> AutonomousMANUSAgent:
    """Create and initialize autonomous agent"""
    agent = AutonomousMANUSAgent()
    await asyncio.sleep(1)  # Allow initialization
    return agent


async def demo_autonomous_agent():
    """Demonstrate autonomous agent capabilities"""
    agent = await create_autonomous_agent()
    
    # Get initial status
    status = await agent.execute_specialty({'command': 'status'})
    print("Initial Status:", json.dumps(status, indent=2))
    
    # Set a goal
    goal_result = await agent.execute_specialty({
        'command': 'set_goal',
        'description': 'Optimize system performance by 25%',
        'priority': TaskPriority.HIGH.value,
        'metadata': {'domain': 'performance'}
    })
    print("\nGoal Set:", json.dumps(goal_result, indent=2))
    
    # Generate additional goals
    generated = await agent.execute_specialty({
        'command': 'generate_goals',
        'domain': 'code_quality'
    })
    print("\nGenerated Goals:", json.dumps(generated, indent=2))
    
    # Predict tasks
    predictions = await agent.execute_specialty({
        'command': 'predict_tasks',
        'horizon_days': 3
    })
    print("\nPredicted Tasks:", json.dumps(predictions, indent=2))
    
    # Execute autonomously for a short time
    execution = await agent.execute_specialty({
        'command': 'autonomous_execute',
        'max_duration_minutes': 1
    })
    print("\nAutonomous Execution:", json.dumps(execution, indent=2))
    
    # Self-improve
    improvement = await agent.execute_specialty({
        'command': 'improve',
        'aspect': 'efficiency'
    })
    print("\nSelf-Improvement:", json.dumps(improvement, indent=2))
    
    # Final status
    final_status = await agent.execute_specialty({'command': 'status'})
    print("\nFinal Status:", json.dumps(final_status, indent=2))


if __name__ == "__main__":
    asyncio.run(demo_autonomous_agent())