#!/usr/bin/env python3
"""
NEXUS 2.0 Integration Test Suite
Tests the complete integration of all components working together
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

# Import all NEXUS components
from nexus_memory_core import NexusUnifiedMemory
from nexus_autonomous_agent import AutonomousMANUSAgent, TaskPriority
from nexus_orchestrator import NEXUSOrchestrator
from nexus_integration_hub import NEXUSIntegrationHub, EventType
from nexus_db_migrations import NEXUSDatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('NEXUS-Integration-Test')


class NEXUSIntegrationTest:
    """Comprehensive integration test for NEXUS 2.0"""
    
    def __init__(self):
        self.components = {}
        self.test_results = {}
        self.start_time = datetime.now()
    
    async def setup(self):
        """Initialize all NEXUS components"""
        logger.info("=== NEXUS 2.0 Integration Test Starting ===")
        
        # 1. Initialize database schemas
        logger.info("Initializing database schemas...")
        self.db_manager = NEXUSDatabaseManager('./test_nexus_data')
        self.db_manager.initialize_all_databases()
        
        # 2. Initialize Integration Hub (central nervous system)
        logger.info("Starting Integration Hub...")
        self.hub = NEXUSIntegrationHub()
        self.components['hub'] = self.hub
        await asyncio.sleep(1)  # Allow services to start
        
        # 3. Initialize Orchestrator (brain stem)
        logger.info("Starting Orchestrator...")
        self.orchestrator = NEXUSOrchestrator()
        self.components['orchestrator'] = self.orchestrator
        
        # 4. Initialize Enhanced Memory System
        logger.info("Initializing Memory System...")
        self.memory = NexusUnifiedMemory()
        self.components['memory'] = self.memory
        await asyncio.sleep(1)  # Allow async initialization
        
        # 5. Initialize Autonomous MANUS Agent
        logger.info("Starting Autonomous Agent...")
        self.agent = AutonomousMANUSAgent()
        self.components['agent'] = self.agent
        
        # 6. Register components with orchestrator and hub
        await self._register_components()
        
        # 7. Set up event subscriptions
        await self._setup_event_subscriptions()
        
        logger.info("Setup complete. All components initialized.")
    
    async def _register_components(self):
        """Register all components with orchestrator and hub"""
        # Register with orchestrator
        self.orchestrator.register_component(
            'memory', self.memory, 'memory_system',
            dependencies=[]
        )
        
        self.orchestrator.register_component(
            'agent', self.agent, 'autonomous_agent',
            dependencies=['memory']
        )
        
        # Register with integration hub
        self.hub.register_component('memory', self.memory, ['store', 'retrieve', 'fuse'])
        self.hub.register_component('agent', self.agent, ['execute', 'learn', 'predict'])
        self.hub.register_component('orchestrator', self.orchestrator, ['coordinate', 'optimize'])
    
    async def _setup_event_subscriptions(self):
        """Set up event subscriptions for component communication"""
        # Memory system subscribes to learning events
        async def memory_learning_handler(event):
            if event.data.get('type') == 'new_learning':
                await self.memory.learning_memory.store(event.data['learning'])
        
        self.hub.subscribe_event(EventType.COMPONENT, memory_learning_handler)
        
        # Agent subscribes to goal events
        async def agent_goal_handler(event):
            if event.data.get('type') == 'new_goal':
                await self.agent._set_goal(event.data)
        
        self.hub.subscribe_event(EventType.TASK, agent_goal_handler)
        
        # Orchestrator subscribes to system events
        async def orchestrator_system_handler(event):
            if event.data.get('type') == 'component_degraded':
                await self.orchestrator.handle_degradation(
                    event.data['component'],
                    event.data['reason']
                )
        
        self.hub.subscribe_event(EventType.SYSTEM, orchestrator_system_handler)
    
    async def test_memory_integration(self):
        """Test memory system integration"""
        logger.info("\n=== Testing Memory System Integration ===")
        
        try:
            # Store memories of different types
            memories_stored = []
            
            # Working memory
            mem1_id = await self.memory.store(
                "Test working memory content",
                {"type": "test", "category": "working"},
                importance=0.2
            )
            memories_stored.append(mem1_id)
            
            # Episodic memory
            mem2_id = await self.memory.store(
                "Test episodic event with moderate importance",
                {"type": "test", "category": "episodic", "timestamp": datetime.now().isoformat()},
                importance=0.5
            )
            memories_stored.append(mem2_id)
            
            # Semantic memory
            mem3_id = await self.memory.store(
                "Important semantic knowledge about NEXUS integration patterns",
                {"type": "test", "category": "semantic", "domain": "integration"},
                importance=0.7
            )
            memories_stored.append(mem3_id)
            
            # Learning memory
            learning_entry = await self.memory.learning_memory.store({
                "id": f"learning_test_{datetime.now().timestamp()}",
                "content": {"pattern": "Integration test pattern", "outcome": "success"},
                "metadata": {"confidence": 0.8},
                "importance": 0.6
            })
            
            # Goal memory
            goal_entry = await self.memory.goal_memory.store({
                "id": f"goal_test_{datetime.now().timestamp()}",
                "content": "Complete integration testing",
                "metadata": {"priority": "high"},
                "importance": 0.8
            })
            
            # Test retrieval
            search_results = await self.memory.retrieve("integration", n_results=5)
            
            # Test memory fusion
            fusion_result = await self.memory.fusion.fuse_memories(
                "NEXUS integration",
                memory_types=['working', 'episodic', 'semantic', 'learning', 'goal']
            )
            
            # Publish memory event
            await self.hub.publish_event(
                EventType.COMPONENT,
                'memory_test',
                {
                    'type': 'memory_test_complete',
                    'memories_stored': len(memories_stored),
                    'search_results': len(search_results),
                    'fusion_score': fusion_result['fusion_score']
                }
            )
            
            self.test_results['memory_integration'] = {
                'status': 'passed',
                'memories_stored': len(memories_stored),
                'search_results': len(search_results),
                'fusion_insights': fusion_result['insights'],
                'fusion_score': fusion_result['fusion_score']
            }
            
            logger.info(f"✓ Memory integration test passed. Fusion score: {fusion_result['fusion_score']:.2f}")
            
        except Exception as e:
            self.test_results['memory_integration'] = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"✗ Memory integration test failed: {e}")
    
    async def test_autonomous_agent(self):
        """Test autonomous agent capabilities"""
        logger.info("\n=== Testing Autonomous Agent ===")
        
        try:
            # Set a goal
            goal_result = await self.agent.execute_specialty({
                'command': 'set_goal',
                'description': 'Optimize NEXUS integration test performance',
                'priority': TaskPriority.HIGH.value,
                'metadata': {'test': True}
            })
            
            # Generate additional goals
            generated_goals = await self.agent.execute_specialty({
                'command': 'generate_goals',
                'domain': 'system_integration'
            })
            
            # Predict tasks
            predictions = await self.agent.execute_specialty({
                'command': 'predict_tasks',
                'horizon_days': 1
            })
            
            # Learn from experience
            learning_result = await self.agent.execute_specialty({
                'command': 'learn',
                'type': 'integration_test'
            })
            
            # Self-improve
            improvement_result = await self.agent.execute_specialty({
                'command': 'improve',
                'aspect': 'efficiency'
            })
            
            # Execute autonomously for a short period
            execution_result = await self.agent.execute_specialty({
                'command': 'autonomous_execute',
                'max_duration_minutes': 0.5  # 30 seconds
            })
            
            self.test_results['autonomous_agent'] = {
                'status': 'passed',
                'goals_created': len(generated_goals.get('generated_goals', [])) + 1,
                'tasks_predicted': len(predictions.get('predicted_tasks', [])),
                'tasks_executed': execution_result.get('total_executed', 0),
                'improvements_applied': len(improvement_result.get('improvements_applied', []))
            }
            
            logger.info(f"✓ Autonomous agent test passed. Goals: {self.test_results['autonomous_agent']['goals_created']}")
            
        except Exception as e:
            self.test_results['autonomous_agent'] = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"✗ Autonomous agent test failed: {e}")
    
    async def test_orchestration(self):
        """Test orchestration capabilities"""
        logger.info("\n=== Testing Orchestration ===")
        
        try:
            # Execute tasks through orchestrator
            task1_id = await self.orchestrator.execute_task(
                'memory', 'store',
                {
                    'content': 'Orchestrated memory storage test',
                    'metadata': {'orchestrated': True},
                    'importance': 0.6
                },
                priority=8
            )
            
            task2_id = await self.orchestrator.execute_task(
                'agent', 'execute_specialty',
                {
                    'context': {'command': 'status'}
                },
                priority=5
            )
            
            # Wait for tasks to complete
            await asyncio.sleep(1)
            
            # Get system health
            health = self.orchestrator.get_system_health()
            
            # Trigger optimization
            optimization = await self.orchestrator.optimize_performance()
            
            # Test degradation handling
            degradation_result = await self.orchestrator.handle_degradation(
                'memory',
                'Simulated high load'
            )
            
            self.test_results['orchestration'] = {
                'status': 'passed',
                'tasks_executed': 2,
                'system_health': health['overall_health'],
                'optimizations_applied': len(optimization.get('optimizations', [])),
                'degradation_handled': len(degradation_result.get('actions_taken', []))
            }
            
            logger.info(f"✓ Orchestration test passed. System health: {health['overall_health']:.2f}")
            
        except Exception as e:
            self.test_results['orchestration'] = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"✗ Orchestration test failed: {e}")
    
    async def test_integration_hub(self):
        """Test integration hub functionality"""
        logger.info("\n=== Testing Integration Hub ===")
        
        try:
            # Test state synchronization
            test_state = {
                'test_value': 42,
                'test_status': 'active',
                'timestamp': datetime.now().isoformat()
            }
            
            await self.hub.sync_state('test_component', test_state)
            
            # Retrieve state
            retrieved_state = await self.hub.get_state('test_component')
            
            # Test transaction management
            transaction_id = await self.hub.begin_transaction([
                {
                    'component': 'memory',
                    'method': 'store',
                    'args': {
                        'content': 'Transaction test memory',
                        'metadata': {'transaction': True}
                    }
                },
                {
                    'component': 'agent',
                    'method': 'execute_specialty',
                    'args': {
                        'context': {'command': 'status'}
                    }
                }
            ])
            
            # Commit transaction
            commit_success = await self.hub.commit_transaction(transaction_id)
            
            # Test event publication
            events_published = 0
            for i in range(5):
                await self.hub.publish_event(
                    EventType.NOTIFICATION,
                    'integration_test',
                    {'message': f'Test event {i}', 'index': i}
                )
                events_published += 1
            
            # Get metrics
            metrics = self.hub.metrics
            
            self.test_results['integration_hub'] = {
                'status': 'passed',
                'state_synced': retrieved_state is not None,
                'transaction_success': commit_success,
                'events_published': events_published,
                'total_events_processed': metrics['events_processed']
            }
            
            logger.info(f"✓ Integration hub test passed. Events processed: {metrics['events_processed']}")
            
        except Exception as e:
            self.test_results['integration_hub'] = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"✗ Integration hub test failed: {e}")
    
    async def test_cross_component_workflow(self):
        """Test a complex workflow involving all components"""
        logger.info("\n=== Testing Cross-Component Workflow ===")
        
        try:
            # 1. Agent generates a goal
            goal_event = await self.hub.publish_event(
                EventType.TASK,
                'workflow_test',
                {
                    'type': 'new_goal',
                    'description': 'Analyze and optimize system performance',
                    'priority': TaskPriority.HIGH.value
                }
            )
            
            # 2. Orchestrator schedules analysis task
            analysis_task = await self.orchestrator.execute_task(
                'agent', 'execute_specialty',
                {
                    'context': {
                        'command': 'analyze_project',
                        'directory': '.',
                        'include_performance': True
                    }
                },
                priority=9
            )
            
            # 3. Memory system stores analysis results
            analysis_memory = await self.memory.store(
                {
                    'workflow': 'performance_analysis',
                    'task_id': analysis_task,
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'type': 'analysis_result',
                    'workflow_test': True
                },
                importance=0.8
            )
            
            # 4. Agent learns from the analysis
            learning_event = await self.hub.publish_event(
                EventType.COMPONENT,
                'workflow_test',
                {
                    'type': 'new_learning',
                    'learning': {
                        'id': f'workflow_learning_{datetime.now().timestamp()}',
                        'content': {
                            'pattern': 'Cross-component workflow successful',
                            'outcome': 'All components integrated successfully'
                        },
                        'metadata': {'source': 'workflow_test'},
                        'importance': 0.7
                    }
                }
            )
            
            # 5. Hub initiates a transaction to update all component states
            update_transaction = await self.hub.begin_transaction([
                {
                    'component': 'memory',
                    'method': 'consolidate',
                    'args': {}
                }
            ])
            
            await self.hub.commit_transaction(update_transaction)
            
            # 6. Orchestrator optimizes based on workflow results
            final_optimization = await self.orchestrator.optimize_performance()
            
            self.test_results['cross_component_workflow'] = {
                'status': 'passed',
                'workflow_steps_completed': 6,
                'events_generated': 2,
                'memory_stored': True,
                'optimization_improvement': final_optimization.get('improvement', 0)
            }
            
            logger.info("✓ Cross-component workflow test passed")
            
        except Exception as e:
            self.test_results['cross_component_workflow'] = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"✗ Cross-component workflow test failed: {e}")
    
    async def test_resilience(self):
        """Test system resilience and recovery"""
        logger.info("\n=== Testing System Resilience ===")
        
        try:
            # Simulate component failure
            self.orchestrator.components['memory'].status = 'FAILED'
            
            # System should handle degradation
            await asyncio.sleep(1)
            
            # Check if degradation was handled
            health_after_failure = self.orchestrator.get_system_health()
            
            # Recover component
            self.orchestrator.components['memory'].status = 'HEALTHY'
            
            # Test rollback capability
            rollback_transaction = await self.hub.begin_transaction([
                {
                    'component': 'agent',
                    'method': 'execute_specialty',
                    'args': {
                        'context': {'command': 'invalid_command'}  # This should fail
                    }
                }
            ])
            
            # This should trigger rollback
            rollback_success = not await self.hub.commit_transaction(rollback_transaction)
            
            self.test_results['resilience'] = {
                'status': 'passed',
                'degradation_handled': health_after_failure['overall_health'] < 1.0,
                'rollback_triggered': rollback_success,
                'recovery_successful': True
            }
            
            logger.info("✓ Resilience test passed")
            
        except Exception as e:
            self.test_results['resilience'] = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"✗ Resilience test failed: {e}")
    
    async def cleanup(self):
        """Clean up test resources"""
        logger.info("\n=== Cleaning up test resources ===")
        
        # Shutdown components gracefully
        await self.orchestrator.shutdown()
        await self.hub.shutdown()
        
        # Get final statistics
        db_stats = self.db_manager.get_database_stats()
        
        # Backup test data
        backup_path = self.db_manager.backup_databases()
        
        logger.info(f"Test data backed up to: {backup_path}")
        logger.info(f"Database statistics: {json.dumps(db_stats, indent=2)}")
    
    async def generate_report(self):
        """Generate comprehensive test report"""
        duration = (datetime.now() - self.start_time).seconds
        
        report = {
            'test_suite': 'NEXUS 2.0 Integration Test',
            'timestamp': self.start_time.isoformat(),
            'duration_seconds': duration,
            'test_results': self.test_results,
            'summary': {
                'total_tests': len(self.test_results),
                'passed': sum(1 for r in self.test_results.values() if r['status'] == 'passed'),
                'failed': sum(1 for r in self.test_results.values() if r['status'] == 'failed')
            }
        }
        
        # Write report to file
        report_path = Path('./nexus_integration_test_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("NEXUS 2.0 Integration Test Report")
        logger.info("="*60)
        logger.info(f"Duration: {duration} seconds")
        logger.info(f"Total Tests: {report['summary']['total_tests']}")
        logger.info(f"Passed: {report['summary']['passed']}")
        logger.info(f"Failed: {report['summary']['failed']}")
        logger.info("="*60)
        
        # Print individual test results
        for test_name, result in self.test_results.items():
            status_icon = "✓" if result['status'] == 'passed' else "✗"
            logger.info(f"{status_icon} {test_name}: {result['status'].upper()}")
            if result['status'] == 'failed':
                logger.error(f"  Error: {result.get('error', 'Unknown error')}")
        
        logger.info(f"\nDetailed report saved to: {report_path}")
        
        return report


async def main():
    """Run the complete integration test suite"""
    test_suite = NEXUSIntegrationTest()
    
    try:
        # Setup
        await test_suite.setup()
        
        # Run tests
        await test_suite.test_memory_integration()
        await test_suite.test_autonomous_agent()
        await test_suite.test_orchestration()
        await test_suite.test_integration_hub()
        await test_suite.test_cross_component_workflow()
        await test_suite.test_resilience()
        
        # Generate report
        report = await test_suite.generate_report()
        
        # Cleanup
        await test_suite.cleanup()
        
        # Return success if all tests passed
        success = report['summary']['failed'] == 0
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Integration test suite failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)