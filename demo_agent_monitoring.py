#!/usr/bin/env python3
"""
Demo script showing integration of NEXUS monitoring with actual agents
"""

import asyncio
import random
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Import the monitoring system
from nexus_agent_monitor import (
    NexusAgentMonitor, Agent, Task, PerformanceMetrics, 
    LearningMetrics, TaskStatus, AgentStatus
)


class MonitoredNexusAgent:
    """Base class for monitored NEXUS agents"""
    
    def __init__(self, agent_id: str, name: str, monitor: NexusAgentMonitor):
        self.agent_id = agent_id
        self.name = name
        self.monitor = monitor
        self.current_task: Optional[Task] = None
        
        # Register agent with monitor
        self.agent = Agent(
            id=agent_id,
            name=name,
            status=AgentStatus.IDLE
        )
        monitor.agents[agent_id] = self.agent
    
    async def execute_task(self, task: Task):
        """Execute a task with monitoring"""
        self.current_task = task
        self.agent.status = AgentStatus.WORKING
        self.agent.current_task = task.id
        
        # Add task to monitor
        self.monitor.add_task(task)
        
        try:
            # Simulate task execution
            start_time = time.time()
            
            for progress in range(0, 101, 10):
                # Update progress
                self.monitor.update_task_progress(task.id, float(progress))
                
                # Update performance metrics
                perf_metrics = PerformanceMetrics(
                    response_time_ms=(time.time() - start_time) * 1000,
                    memory_mb=random.uniform(200, 400),
                    cpu_percent=random.uniform(30, 70),
                    network_kb_s=random.uniform(1, 5)
                )
                self.monitor.update_agent_performance(self.agent_id, perf_metrics)
                
                # Simulate work
                await asyncio.sleep(0.5)
            
            # Task completed
            self.monitor.update_task_progress(task.id, 100.0, TaskStatus.COMPLETED)
            
            # Update learning metrics
            learn_metrics = LearningMetrics(
                patterns_recognized=self.agent.learning.patterns_recognized + random.randint(1, 5),
                optimizations_made=self.agent.learning.optimizations_made + 1,
                success_rate=random.uniform(85, 95),
                knowledge_nodes=self.agent.learning.knowledge_nodes + random.randint(2, 8)
            )
            self.monitor.update_agent_learning(self.agent_id, learn_metrics)
            
        except Exception as e:
            # Task failed
            self.monitor.update_task_progress(task.id, task.progress, TaskStatus.FAILED)
            raise e
        finally:
            self.agent.status = AgentStatus.IDLE
            self.agent.current_task = None
            self.current_task = None


class DataProcessorAgent(MonitoredNexusAgent):
    """Agent specialized in data processing"""
    
    async def process_data_batch(self, batch_id: int):
        """Process a batch of data"""
        task = Task(
            id=f"data-batch-{batch_id}",
            name=f"Process Data Batch {batch_id}",
            agent_id=self.agent_id,
            status=TaskStatus.PENDING,
            estimated_time=30.0
        )
        
        await self.execute_task(task)


class LearningEngineAgent(MonitoredNexusAgent):
    """Agent specialized in pattern learning"""
    
    async def learn_patterns(self, dataset_id: str):
        """Learn patterns from dataset"""
        task = Task(
            id=f"learn-{dataset_id}",
            name=f"Learn Patterns from {dataset_id}",
            agent_id=self.agent_id,
            status=TaskStatus.PENDING,
            estimated_time=45.0
        )
        
        # Simulate learning phase
        self.agent.status = AgentStatus.LEARNING
        await self.execute_task(task)


class OptimizationAgent(MonitoredNexusAgent):
    """Agent specialized in system optimization"""
    
    async def optimize_system(self, target: str):
        """Optimize system component"""
        task = Task(
            id=f"optimize-{target}",
            name=f"Optimize {target}",
            agent_id=self.agent_id,
            status=TaskStatus.PENDING,
            estimated_time=60.0
        )
        
        # Simulate optimization phase
        self.agent.status = AgentStatus.OPTIMIZING
        await self.execute_task(task)


class MonitoringDemo:
    """Demo application showing monitoring in action"""
    
    def __init__(self):
        self.monitor = NexusAgentMonitor()
        self.agents = []
        
        # Create agents
        self.data_processor = DataProcessorAgent(
            "data-proc-01", "Data Processor", self.monitor
        )
        self.agents.append(self.data_processor)
        
        self.learner = LearningEngineAgent(
            "learner-01", "Learning Engine", self.monitor
        )
        self.agents.append(self.learner)
        
        self.optimizer = OptimizationAgent(
            "optimizer-01", "System Optimizer", self.monitor
        )
        self.agents.append(self.optimizer)
        
        # Set up collaborations
        self.monitor.add_collaboration("data-proc-01", "learner-01")
        self.monitor.add_collaboration("learner-01", "optimizer-01")
    
    async def run_demo_tasks(self):
        """Run demonstration tasks"""
        batch_counter = 0
        dataset_counter = 0
        
        while True:
            # Data processing tasks
            if random.random() < 0.4:
                batch_counter += 1
                asyncio.create_task(
                    self.data_processor.process_data_batch(batch_counter)
                )
            
            # Learning tasks
            if random.random() < 0.3:
                dataset_counter += 1
                asyncio.create_task(
                    self.learner.learn_patterns(f"dataset-{dataset_counter}")
                )
            
            # Optimization tasks
            if random.random() < 0.2:
                targets = ["memory", "cpu", "network", "storage"]
                target = random.choice(targets)
                asyncio.create_task(
                    self.optimizer.optimize_system(target)
                )
            
            await asyncio.sleep(2)
    
    async def run(self):
        """Run the monitoring demo"""
        # Start task generation
        task_generator = asyncio.create_task(self.run_demo_tasks())
        
        # Run dashboard
        try:
            await self.monitor.run_dashboard()
        finally:
            task_generator.cancel()


async def main():
    """Main entry point"""
    print("NEXUS Agent Monitoring Demo")
    print("=" * 50)
    print("This demo shows real-time monitoring of NEXUS agents")
    print("Press Ctrl+C to exit")
    print("=" * 50)
    
    await asyncio.sleep(2)
    
    demo = MonitoringDemo()
    await demo.run()


if __name__ == "__main__":
    asyncio.run(main())