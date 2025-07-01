#!/usr/bin/env python3
"""
NEXUS Integrated Test Suite
Comprehensive testing for all NEXUS components working together
"""

import asyncio
import json
import os
import sys
import time
import tempfile
import shutil
import psutil
import pytest
from unittest.mock import Mock, patch, AsyncMock
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp
from pathlib import Path
import numpy as np
from typing import Dict, List, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import NEXUS components
from nexus_2.0_launcher import NexusLauncher
from nexus_omnipotent_core import OmnipotentNexusCore
from nexus_unified_tools import UnifiedToolInterface
from nexus_memory_core import MemoryCore
from nexus_web_scraper import WebScrapingService
from nexus_enhanced_manus import EnhancedManusThinker
from nexus_communication_engine import CommunicationEngine
from nexus_predictive_engine import PredictiveEngine
from nexus_context_engine import ContextEngine
from nexus_goal_reasoning import GoalReasoningEngine
from nexus_autonomous_agent import AutonomousAgent
from nexus_collaborative_intelligence import CollaborativeIntelligence
from nexus_integration_hub import IntegrationHub
from nexus_orchestrator import SystemOrchestrator
from nexus_proactive_monitor import ProactiveMonitor
from nexus_research_engine import ResearchEngine
from nexus_self_improvement import SelfImprovementEngine
from nexus_semantic_analyzer import SemanticAnalyzer
from nexus_tool_discovery import ToolDiscoveryEngine
from nexus_uncertainty_handler import UncertaintyHandler
from nexus_doc_generator import DocumentationGenerator
from nexus_bug_detector import BugDetector
from nexus_security_scanner import SecurityScanner
from nexus_performance_analyzer import PerformanceAnalyzer
from nexus_project_generator import ProjectGenerator


class NexusTestHarness:
    """Test harness for NEXUS integrated testing"""
    
    def __init__(self):
        self.nexus = None
        self.temp_dirs = []
        self.start_time = None
        self.metrics = {
            'startup_time': 0,
            'command_response_times': [],
            'memory_usage': [],
            'cpu_usage': [],
            'error_count': 0,
            'success_count': 0
        }
        
    async def setup(self):
        """Setup test environment"""
        self.start_time = time.time()
        
        # Create temporary directories for testing
        self.test_dir = tempfile.mkdtemp(prefix='nexus_test_')
        self.temp_dirs.append(self.test_dir)
        
        # Initialize NEXUS with test configuration
        self.nexus = NexusLauncher()
        await self.nexus.initialize()
        
        self.metrics['startup_time'] = time.time() - self.start_time
        
    async def teardown(self):
        """Cleanup test environment"""
        # Shutdown NEXUS
        if self.nexus:
            await self.nexus.shutdown()
            
        # Clean up temporary directories
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
    def record_metrics(self):
        """Record current system metrics"""
        process = psutil.Process()
        self.metrics['memory_usage'].append(process.memory_info().rss / 1024 / 1024)  # MB
        self.metrics['cpu_usage'].append(process.cpu_percent(interval=0.1))
        
    async def measure_command_time(self, command_fn, *args, **kwargs):
        """Measure command execution time"""
        start = time.time()
        try:
            result = await command_fn(*args, **kwargs)
            self.metrics['success_count'] += 1
            return result
        except Exception as e:
            self.metrics['error_count'] += 1
            raise e
        finally:
            elapsed = time.time() - start
            self.metrics['command_response_times'].append(elapsed)
            self.record_metrics()


class TestEndToEndFlows:
    """Test complete user workflows"""
    
    @pytest.fixture
    async def harness(self):
        """Setup test harness"""
        harness = NexusTestHarness()
        await harness.setup()
        yield harness
        await harness.teardown()
        
    @pytest.mark.asyncio
    async def test_voice_command_flow(self, harness):
        """Test: Launch → Voice command → Tab switch → Action → Result"""
        # Simulate voice command
        voice_input = "Create a new Python function to calculate fibonacci"
        
        # Process voice command
        result = await harness.measure_command_time(
            harness.nexus.process_voice_command,
            voice_input
        )
        
        assert result is not None
        assert 'fibonacci' in str(result).lower()
        
        # Verify tab switch
        assert harness.nexus.current_tab == 'code'
        
        # Verify action execution
        assert harness.nexus.last_action is not None
        assert harness.nexus.last_result is not None
        
    @pytest.mark.asyncio
    async def test_screenshot_analysis_flow(self, harness):
        """Test: Screenshot → Analysis → Code generation → Preview"""
        # Create mock screenshot
        mock_screenshot = {
            'type': 'screenshot',
            'content': 'Mock UI screenshot data',
            'metadata': {
                'width': 1920,
                'height': 1080,
                'format': 'png'
            }
        }
        
        # Analyze screenshot
        analysis = await harness.measure_command_time(
            harness.nexus.analyze_screenshot,
            mock_screenshot
        )
        
        assert analysis is not None
        assert 'ui_elements' in analysis
        
        # Generate code from analysis
        code = await harness.measure_command_time(
            harness.nexus.generate_code_from_analysis,
            analysis
        )
        
        assert code is not None
        assert len(code) > 0
        
        # Preview generated code
        preview = await harness.measure_command_time(
            harness.nexus.preview_code,
            code
        )
        
        assert preview is not None
        assert preview['status'] == 'success'
        
    @pytest.mark.asyncio
    async def test_goal_execution_flow(self, harness):
        """Test: Goal submission → Task creation → Execution → Deployment"""
        # Submit goal
        goal = {
            'objective': 'Create a REST API for user management',
            'requirements': [
                'CRUD operations',
                'Authentication',
                'Input validation'
            ]
        }
        
        # Create tasks from goal
        tasks = await harness.measure_command_time(
            harness.nexus.create_tasks_from_goal,
            goal
        )
        
        assert len(tasks) > 0
        assert all('task_id' in task for task in tasks)
        
        # Execute tasks
        results = []
        for task in tasks[:2]:  # Test first 2 tasks
            result = await harness.measure_command_time(
                harness.nexus.execute_task,
                task
            )
            results.append(result)
            
        assert all(r['status'] == 'completed' for r in results)
        
        # Deploy solution
        deployment = await harness.measure_command_time(
            harness.nexus.deploy_solution,
            results
        )
        
        assert deployment['status'] == 'deployed'


class TestMultiModalIntegration:
    """Test multi-modal capabilities"""
    
    @pytest.fixture
    async def harness(self):
        harness = NexusTestHarness()
        await harness.setup()
        yield harness
        await harness.teardown()
        
    @pytest.mark.asyncio
    async def test_voice_vision_integration(self, harness):
        """Test voice and vision working together"""
        # Voice command with visual context
        voice_input = "Make this button larger"
        visual_context = {
            'screenshot': 'mock_screenshot_data',
            'selected_element': {
                'type': 'button',
                'bounds': {'x': 100, 'y': 200, 'width': 80, 'height': 30}
            }
        }
        
        result = await harness.measure_command_time(
            harness.nexus.process_multimodal_input,
            voice_input,
            visual_context
        )
        
        assert result is not None
        assert 'modifications' in result
        assert result['modifications'][0]['property'] == 'size'
        
    @pytest.mark.asyncio
    async def test_tab_coordination(self, harness):
        """Test coordinated actions across tabs"""
        # Create project in project tab
        await harness.nexus.switch_tab('project')
        project = await harness.measure_command_time(
            harness.nexus.create_project,
            'test_app'
        )
        
        # Switch to code tab and generate code
        await harness.nexus.switch_tab('code')
        code = await harness.measure_command_time(
            harness.nexus.generate_boilerplate,
            project['id']
        )
        
        # Switch to deploy tab and prepare deployment
        await harness.nexus.switch_tab('deploy')
        deployment = await harness.measure_command_time(
            harness.nexus.prepare_deployment,
            project['id']
        )
        
        # Verify coordination
        assert project['id'] == code['project_id']
        assert project['id'] == deployment['project_id']
        assert harness.nexus.get_tab_state('project')['active_project'] == project['id']
        
    @pytest.mark.asyncio
    async def test_agent_collaboration(self, harness):
        """Test multiple agents working together"""
        # Create collaborative task
        task = {
            'type': 'collaborative',
            'objective': 'Build a dashboard with real-time data',
            'agents_required': ['ui_designer', 'backend_dev', 'data_analyst']
        }
        
        # Execute collaborative task
        result = await harness.measure_command_time(
            harness.nexus.execute_collaborative_task,
            task
        )
        
        # Verify collaboration
        assert result['status'] == 'completed'
        assert len(result['agent_contributions']) == 3
        assert all(c['status'] == 'success' for c in result['agent_contributions'])
        
    @pytest.mark.asyncio
    async def test_state_persistence(self, harness):
        """Test state persistence across sessions"""
        # Create some state
        test_state = {
            'project': 'test_project',
            'current_file': 'main.py',
            'cursor_position': {'line': 42, 'column': 15},
            'open_tabs': ['main.py', 'test.py', 'config.json']
        }
        
        # Save state
        await harness.nexus.save_state(test_state)
        
        # Simulate restart
        await harness.nexus.shutdown()
        await harness.nexus.initialize()
        
        # Restore state
        restored_state = await harness.nexus.get_state()
        
        assert restored_state['project'] == test_state['project']
        assert restored_state['current_file'] == test_state['current_file']
        assert restored_state['cursor_position'] == test_state['cursor_position']
        assert restored_state['open_tabs'] == test_state['open_tabs']


class TestPerformanceValidation:
    """Test performance characteristics"""
    
    @pytest.fixture
    async def harness(self):
        harness = NexusTestHarness()
        await harness.setup()
        yield harness
        await harness.teardown()
        
    @pytest.mark.asyncio
    async def test_startup_performance(self, harness):
        """Test startup time is within acceptable limits"""
        assert harness.metrics['startup_time'] < 5.0  # Should start in under 5 seconds
        
    @pytest.mark.asyncio
    async def test_command_response_time(self, harness):
        """Test command response times"""
        # Execute various commands
        commands = [
            ('voice', "Show me the file structure"),
            ('code', "Generate a function to sort a list"),
            ('search', "Find all TODO comments"),
            ('analyze', "Analyze code quality")
        ]
        
        for cmd_type, cmd in commands:
            start = time.time()
            await harness.nexus.execute_command(cmd_type, cmd)
            elapsed = time.time() - start
            harness.metrics['command_response_times'].append(elapsed)
            
        # Verify response times
        avg_response_time = np.mean(harness.metrics['command_response_times'])
        max_response_time = np.max(harness.metrics['command_response_times'])
        
        assert avg_response_time < 1.0  # Average under 1 second
        assert max_response_time < 3.0  # Max under 3 seconds
        
    @pytest.mark.asyncio
    async def test_memory_efficiency(self, harness):
        """Test memory usage remains reasonable"""
        initial_memory = harness.metrics['memory_usage'][0] if harness.metrics['memory_usage'] else 0
        
        # Perform memory-intensive operations
        for i in range(10):
            # Load large file
            large_content = "x" * (1024 * 1024)  # 1MB
            await harness.nexus.process_file_content(large_content)
            harness.record_metrics()
            
        # Check memory growth
        final_memory = harness.metrics['memory_usage'][-1]
        memory_growth = final_memory - initial_memory
        
        assert memory_growth < 500  # Less than 500MB growth
        
    @pytest.mark.asyncio
    async def test_cpu_optimization(self, harness):
        """Test CPU usage optimization"""
        # Run CPU-intensive tasks
        tasks = []
        for i in range(5):
            task = harness.nexus.analyze_codebase(f"project_{i}")
            tasks.append(task)
            
        # Execute concurrently
        await asyncio.gather(*tasks)
        
        # Check CPU usage
        avg_cpu = np.mean(harness.metrics['cpu_usage'])
        max_cpu = np.max(harness.metrics['cpu_usage'])
        
        assert avg_cpu < 80  # Average CPU under 80%
        assert max_cpu < 100  # Should not max out CPU


class TestStressScenarios:
    """Test system under stress conditions"""
    
    @pytest.fixture
    async def harness(self):
        harness = NexusTestHarness()
        await harness.setup()
        yield harness
        await harness.teardown()
        
    @pytest.mark.asyncio
    async def test_multiple_projects(self, harness):
        """Test handling multiple projects simultaneously"""
        projects = []
        
        # Create multiple projects
        for i in range(10):
            project = await harness.nexus.create_project(f"stress_test_{i}")
            projects.append(project)
            
        # Perform operations on each project
        tasks = []
        for project in projects:
            task = harness.nexus.analyze_project(project['id'])
            tasks.append(task)
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all completed successfully
        successful = sum(1 for r in results if not isinstance(r, Exception))
        assert successful >= 8  # At least 80% success rate
        
    @pytest.mark.asyncio
    async def test_large_codebase(self, harness):
        """Test with large codebase"""
        # Create large codebase structure
        large_project = harness.test_dir + '/large_project'
        os.makedirs(large_project)
        
        # Generate many files
        for i in range(100):
            dir_path = f"{large_project}/module_{i % 10}"
            os.makedirs(dir_path, exist_ok=True)
            
            for j in range(10):
                file_path = f"{dir_path}/file_{j}.py"
                with open(file_path, 'w') as f:
                    f.write(f"# Module {i} File {j}\n" * 100)
                    
        # Analyze large codebase
        start = time.time()
        result = await harness.nexus.analyze_codebase(large_project)
        elapsed = time.time() - start
        
        assert result['status'] == 'completed'
        assert result['files_analyzed'] == 1000
        assert elapsed < 30  # Should complete within 30 seconds
        
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, harness):
        """Test many concurrent operations"""
        operations = []
        
        # Queue many different operations
        for i in range(50):
            op_type = i % 5
            if op_type == 0:
                op = harness.nexus.execute_command('code', f"Generate function_{i}")
            elif op_type == 1:
                op = harness.nexus.analyze_file(f"file_{i}.py")
            elif op_type == 2:
                op = harness.nexus.search_codebase(f"pattern_{i}")
            elif op_type == 3:
                op = harness.nexus.refactor_code(f"function_{i}")
            else:
                op = harness.nexus.generate_tests(f"module_{i}")
                
            operations.append(op)
            
        # Execute all concurrently
        results = await asyncio.gather(*operations, return_exceptions=True)
        
        # Verify system stability
        successful = sum(1 for r in results if not isinstance(r, Exception))
        assert successful >= 40  # At least 80% success rate
        
    @pytest.mark.asyncio
    async def test_resource_limits(self, harness):
        """Test behavior at resource limits"""
        # Simulate low memory condition
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value.available = 100 * 1024 * 1024  # 100MB available
            
            # Try memory-intensive operation
            result = await harness.nexus.handle_low_memory_operation()
            
            assert result['status'] == 'degraded'
            assert 'memory_optimization' in result
            
        # Simulate high CPU load
        with patch('psutil.cpu_percent') as mock_cpu:
            mock_cpu.return_value = 95.0  # 95% CPU usage
            
            # Try CPU-intensive operation
            result = await harness.nexus.handle_high_cpu_operation()
            
            assert result['status'] == 'throttled'
            assert 'cpu_optimization' in result


class TestUserAcceptance:
    """Test common user workflows and scenarios"""
    
    @pytest.fixture
    async def harness(self):
        harness = NexusTestHarness()
        await harness.setup()
        yield harness
        await harness.teardown()
        
    @pytest.mark.asyncio
    async def test_common_developer_workflow(self, harness):
        """Test typical developer workflow"""
        # 1. Create new project
        project = await harness.nexus.create_project("my_app")
        
        # 2. Generate initial structure
        structure = await harness.nexus.generate_project_structure(project['id'], 'web_app')
        
        # 3. Write some code
        code = await harness.nexus.generate_code(
            project['id'],
            'Create a user authentication module'
        )
        
        # 4. Add tests
        tests = await harness.nexus.generate_tests(code['module_id'])
        
        # 5. Fix issues
        issues = await harness.nexus.analyze_code_issues(project['id'])
        fixes = await harness.nexus.fix_issues(issues)
        
        # 6. Deploy
        deployment = await harness.nexus.deploy_project(project['id'])
        
        # Verify workflow completed successfully
        assert project['status'] == 'active'
        assert structure['files_created'] > 0
        assert len(code['functions']) > 0
        assert len(tests['test_cases']) > 0
        assert len(fixes['fixed_issues']) == len(issues['issues'])
        assert deployment['status'] == 'deployed'
        
    @pytest.mark.asyncio
    async def test_error_recovery(self, harness):
        """Test error recovery mechanisms"""
        # Simulate various errors
        error_scenarios = [
            ('network_error', NetworkError("Connection timeout")),
            ('file_not_found', FileNotFoundError("main.py not found")),
            ('syntax_error', SyntaxError("Invalid Python syntax")),
            ('api_error', APIError("Rate limit exceeded"))
        ]
        
        for error_type, error in error_scenarios:
            # Trigger error
            with patch.object(harness.nexus, 'execute_operation') as mock_op:
                mock_op.side_effect = error
                
                # Attempt operation
                result = await harness.nexus.execute_with_recovery('test_operation')
                
                # Verify recovery
                assert result['recovered'] == True
                assert result['recovery_method'] in ['retry', 'fallback', 'graceful_degradation']
                assert result['error_handled'] == True
                
    @pytest.mark.asyncio
    async def test_edge_cases(self, harness):
        """Test edge cases and boundary conditions"""
        # Empty input
        result = await harness.nexus.process_command("")
        assert result['status'] == 'error'
        assert 'empty_input' in result['error']
        
        # Very long input
        long_input = "x" * 10000
        result = await harness.nexus.process_command(long_input)
        assert result['status'] == 'truncated'
        
        # Special characters
        special_input = "Create function $@#%^&*()"
        result = await harness.nexus.process_command(special_input)
        assert result['status'] == 'sanitized'
        
        # Circular dependencies
        circular_task = {
            'id': 'task1',
            'depends_on': ['task2'],
            'subtasks': [{
                'id': 'task2',
                'depends_on': ['task1']
            }]
        }
        result = await harness.nexus.execute_task(circular_task)
        assert result['status'] == 'error'
        assert 'circular_dependency' in result['error']
        
    @pytest.mark.asyncio
    async def test_accessibility_features(self, harness):
        """Test accessibility and usability features"""
        # Screen reader support
        screen_reader_mode = await harness.nexus.enable_accessibility('screen_reader')
        assert screen_reader_mode['enabled'] == True
        assert 'aria_labels' in screen_reader_mode
        
        # Keyboard navigation
        keyboard_nav = await harness.nexus.test_keyboard_navigation()
        assert keyboard_nav['all_elements_reachable'] == True
        assert keyboard_nav['tab_order_logical'] == True
        
        # High contrast mode
        high_contrast = await harness.nexus.enable_accessibility('high_contrast')
        assert high_contrast['enabled'] == True
        assert high_contrast['contrast_ratio'] >= 4.5
        
        # Voice control
        voice_control = await harness.nexus.enable_accessibility('voice_control')
        assert voice_control['enabled'] == True
        assert len(voice_control['available_commands']) > 50


class TestIntegrationMetrics:
    """Collect and validate integration metrics"""
    
    @pytest.mark.asyncio
    async def test_full_integration_suite(self):
        """Run complete integration test suite and collect metrics"""
        harness = NexusTestHarness()
        await harness.setup()
        
        try:
            # Run all test categories
            test_results = {
                'end_to_end': await self._run_end_to_end_tests(harness),
                'multi_modal': await self._run_multi_modal_tests(harness),
                'performance': await self._run_performance_tests(harness),
                'stress': await self._run_stress_tests(harness),
                'user_acceptance': await self._run_user_acceptance_tests(harness)
            }
            
            # Generate comprehensive report
            report = self._generate_integration_report(harness, test_results)
            
            # Save report
            with open('nexus_integration_report.json', 'w') as f:
                json.dump(report, f, indent=2)
                
            # Validate overall system health
            assert report['overall_status'] == 'healthy'
            assert report['test_pass_rate'] >= 0.95  # 95% pass rate
            assert report['performance_score'] >= 0.8  # 80% performance score
            
        finally:
            await harness.teardown()
            
    async def _run_end_to_end_tests(self, harness):
        """Run end-to-end test category"""
        results = []
        tests = [
            'test_voice_command_flow',
            'test_screenshot_analysis_flow',
            'test_goal_execution_flow'
        ]
        
        for test in tests:
            try:
                await getattr(TestEndToEndFlows(), test)(harness)
                results.append({'test': test, 'status': 'passed'})
            except Exception as e:
                results.append({'test': test, 'status': 'failed', 'error': str(e)})
                
        return results
        
    async def _run_multi_modal_tests(self, harness):
        """Run multi-modal test category"""
        # Similar implementation for other test categories
        pass
        
    async def _run_performance_tests(self, harness):
        """Run performance test category"""
        pass
        
    async def _run_stress_tests(self, harness):
        """Run stress test category"""
        pass
        
    async def _run_user_acceptance_tests(self, harness):
        """Run user acceptance test category"""
        pass
        
    def _generate_integration_report(self, harness, test_results):
        """Generate comprehensive integration report"""
        total_tests = sum(len(results) for results in test_results.values())
        passed_tests = sum(
            sum(1 for r in results if r.get('status') == 'passed')
            for results in test_results.values()
        )
        
        return {
            'timestamp': time.time(),
            'overall_status': 'healthy' if passed_tests / total_tests >= 0.95 else 'degraded',
            'test_pass_rate': passed_tests / total_tests,
            'performance_score': self._calculate_performance_score(harness.metrics),
            'metrics': harness.metrics,
            'test_results': test_results,
            'recommendations': self._generate_recommendations(harness.metrics, test_results)
        }
        
    def _calculate_performance_score(self, metrics):
        """Calculate overall performance score"""
        scores = []
        
        # Startup time score (5s = 100%, 10s = 0%)
        startup_score = max(0, min(1, (10 - metrics['startup_time']) / 5))
        scores.append(startup_score)
        
        # Response time score
        if metrics['command_response_times']:
            avg_response = np.mean(metrics['command_response_times'])
            response_score = max(0, min(1, (2 - avg_response) / 2))
            scores.append(response_score)
            
        # Memory efficiency score
        if metrics['memory_usage']:
            avg_memory = np.mean(metrics['memory_usage'])
            memory_score = max(0, min(1, (1000 - avg_memory) / 1000))
            scores.append(memory_score)
            
        # CPU efficiency score
        if metrics['cpu_usage']:
            avg_cpu = np.mean(metrics['cpu_usage'])
            cpu_score = max(0, min(1, (100 - avg_cpu) / 100))
            scores.append(cpu_score)
            
        return np.mean(scores) if scores else 0
        
    def _generate_recommendations(self, metrics, test_results):
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Performance recommendations
        if metrics['startup_time'] > 3:
            recommendations.append("Consider optimizing startup sequence")
            
        if metrics['command_response_times'] and np.mean(metrics['command_response_times']) > 1:
            recommendations.append("Optimize command processing pipeline")
            
        # Memory recommendations
        if metrics['memory_usage'] and np.max(metrics['memory_usage']) > 800:
            recommendations.append("Implement memory optimization strategies")
            
        # Test failure recommendations
        for category, results in test_results.items():
            failed = [r for r in results if r.get('status') == 'failed']
            if failed:
                recommendations.append(f"Address failures in {category}: {len(failed)} tests failed")
                
        return recommendations


# Mock classes for testing
class NetworkError(Exception):
    pass

class APIError(Exception):
    pass


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])