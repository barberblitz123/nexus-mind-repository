#!/usr/bin/env python3
"""
MANUS-NEXUS Integration Module
Enables MANUS to leverage NEXUS consciousness for enhanced task processing
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from manus_continuous_agent import (
    MANUSContinuousAgent, Task, TaskStatus, TaskPriority, TaskExecutor
)

# Import NEXUS Omnipotent Core for integrated memory DNA
from nexus_omnipotent_core import NEXUSOmnipotentCore
# Import the new Unified Memory System
from nexus_memory_core import NexusUnifiedMemory
from nexus_memory_types import MemoryEntry
# Import web scraping capabilities
from nexus_web_scraper import NexusWebScraper
from nexus_scraper_proxies import ProxyManager, ProxyRotator
from nexus_scraper_stealth import StealthManager

logger = logging.getLogger('MANUS-NEXUS')

class NEXUSEnhancedExecutor(TaskExecutor):
    """
    Enhanced task executor that integrates with NEXUS consciousness
    for intelligent task processing and decision making
    """
    
    def __init__(self, nexus_base_url: str = "http://localhost:8000"):
        super().__init__()
        self.nexus_base_url = nexus_base_url
        
        # Initialize web scraping components
        self.web_scraper = NexusWebScraper()
        self.proxy_manager = ProxyManager()
        self.proxy_rotator = ProxyRotator(self.proxy_manager)
        self.stealth_manager = StealthManager()
        
        # Initialize proxy manager in background
        asyncio.create_task(self._init_proxy_manager())
        
        # Add NEXUS-enhanced actions
        self.action_registry.update({
            'nexus_analyze': self._execute_nexus_analyze,
            'nexus_learn': self._execute_nexus_learn,
            'nexus_decide': self._execute_nexus_decide,
            'nexus_process': self._execute_nexus_process,
            'claude_task': self._execute_claude_task,
            'web_scrape': self._execute_web_scrape,
            'batch_scrape': self._execute_batch_scrape,
            'scrape_with_analysis': self._execute_scrape_with_analysis,
        })
    
    async def _init_proxy_manager(self):
        """Initialize proxy manager in background"""
        try:
            await self.proxy_manager.initialize()
            logger.info("Proxy manager initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize proxy manager: {e}")
    
    async def _execute_nexus_analyze(self, task: Task) -> Dict[str, Any]:
        """Use NEXUS consciousness to analyze complex data"""
        data = task.parameters.get('data', {})
        analysis_type = task.parameters.get('analysis_type', 'general')
        
        async with aiohttp.ClientSession() as session:
            payload = {
                'input': data,
                'analysis_type': analysis_type,
                'context': task.context
            }
            
            async with session.post(
                f"{self.nexus_base_url}/consciousness/analyze",
                json=payload
            ) as response:
                result = await response.json()
                
                # Store insights in task context for future use
                task.context['nexus_insights'] = result.get('insights', [])
                
                return result
    
    async def _execute_nexus_learn(self, task: Task) -> Dict[str, Any]:
        """Use NEXUS to learn from task execution patterns"""
        experience = {
            'task_type': task.action,
            'parameters': task.parameters,
            'outcome': task.parameters.get('outcome', 'unknown'),
            'timestamp': datetime.now().isoformat()
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.nexus_base_url}/consciousness/learn",
                json={'experience': experience}
            ) as response:
                return await response.json()
    
    async def _execute_nexus_decide(self, task: Task) -> Dict[str, Any]:
        """Use NEXUS consciousness for decision making"""
        options = task.parameters.get('options', [])
        criteria = task.parameters.get('criteria', {})
        
        async with aiohttp.ClientSession() as session:
            payload = {
                'options': options,
                'criteria': criteria,
                'context': task.context,
                'past_decisions': task.context.get('decision_history', [])
            }
            
            async with session.post(
                f"{self.nexus_base_url}/consciousness/decide",
                json=payload
            ) as response:
                decision = await response.json()
                
                # Store decision in context for learning
                if 'decision_history' not in task.context:
                    task.context['decision_history'] = []
                task.context['decision_history'].append({
                    'timestamp': datetime.now().isoformat(),
                    'decision': decision
                })
                
                return decision
    
    async def _execute_nexus_process(self, task: Task) -> Dict[str, Any]:
        """Process complex tasks using NEXUS's full consciousness"""
        query = task.parameters.get('query', '')
        process_type = task.parameters.get('process_type', 'general')
        
        async with aiohttp.ClientSession() as session:
            payload = {
                'query': query,
                'process_type': process_type,
                'context': task.context,
                'memory_access': True
            }
            
            async with session.post(
                f"{self.nexus_base_url}/consciousness/process",
                json=payload
            ) as response:
                return await response.json()
    
    async def _execute_claude_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute tasks that require Claude-like reasoning and understanding
        This simulates Claude's approach to task processing
        """
        prompt = task.parameters.get('prompt', '')
        task_type = task.parameters.get('task_type', 'general')
        
        # Simulate Claude's structured thinking process
        thinking_process = {
            'understanding': await self._understand_task(prompt, task.context),
            'planning': await self._plan_approach(prompt, task_type),
            'execution': await self._execute_plan(prompt, task.context),
            'verification': await self._verify_results(prompt)
        }
        
        return {
            'response': thinking_process['execution'],
            'confidence': thinking_process['verification']['confidence'],
            'reasoning': thinking_process,
            'success': True
        }
    
    async def _understand_task(self, prompt: str, context: Dict) -> Dict[str, Any]:
        """Understand the task requirements"""
        # In real implementation, this would use NEXUS's understanding capabilities
        return {
            'intent': 'analyze and process request',
            'key_points': ['understand', 'process', 'respond'],
            'context_relevant': True
        }
    
    async def _plan_approach(self, prompt: str, task_type: str) -> List[str]:
        """Plan the approach to solve the task"""
        # Simulate planning based on task type
        plans = {
            'analysis': ['gather data', 'analyze patterns', 'draw conclusions'],
            'creation': ['understand requirements', 'design solution', 'implement'],
            'optimization': ['measure current state', 'identify bottlenecks', 'optimize'],
            'general': ['understand', 'process', 'respond']
        }
        return plans.get(task_type, plans['general'])
    
    async def _execute_plan(self, prompt: str, context: Dict) -> str:
        """Execute the planned approach"""
        # In real implementation, this would process through NEXUS
        return f"Processed request: {prompt[:50]}... with context awareness"
    
    async def _verify_results(self, prompt: str) -> Dict[str, Any]:
        """Verify the results meet requirements"""
        return {
            'meets_requirements': True,
            'confidence': 0.95,
            'issues': []
        }
    
    async def _execute_web_scrape(self, task: Task) -> Dict[str, Any]:
        """Execute web scraping task"""
        url = task.parameters.get('url', '')
        options = task.parameters.get('options', {})
        
        if not url:
            return {
                'success': False,
                'error': 'URL is required for web scraping'
            }
        
        try:
            # Use proxy if available
            if self.proxy_manager and options.get('use_proxy', False):
                proxy = await self.proxy_rotator.get_proxy_for_session(task.id)
                if proxy:
                    options['proxy'] = proxy.url
            
            # Scrape the URL
            result = await self.web_scraper.scrape(url, options)
            
            # Store in task context for future reference
            task.context['scraped_data'] = {
                'url': result.get('url'),
                'title': result.get('title'),
                'content_length': len(result.get('text', '')),
                'links_count': len(result.get('links', [])),
                'images_count': len(result.get('images', [])),
                'engine': result.get('engine')
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Web scraping failed for {url}: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    async def _execute_batch_scrape(self, task: Task) -> Dict[str, Any]:
        """Execute batch web scraping task"""
        urls = task.parameters.get('urls', [])
        options = task.parameters.get('options', {})
        
        if not urls:
            return {
                'success': False,
                'error': 'URLs list is required for batch scraping'
            }
        
        try:
            # Batch scrape with concurrency control
            results = await self.web_scraper.batch_scrape(urls, options)
            
            # Summarize results
            successful = sum(1 for r in results if r.get('success', False))
            failed = len(results) - successful
            
            task.context['batch_scrape_summary'] = {
                'total_urls': len(urls),
                'successful': successful,
                'failed': failed
            }
            
            return {
                'success': True,
                'results': results,
                'summary': {
                    'total': len(urls),
                    'successful': successful,
                    'failed': failed
                }
            }
            
        except Exception as e:
            logger.error(f"Batch scraping failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'urls': urls
            }
    
    async def _execute_scrape_with_analysis(self, task: Task) -> Dict[str, Any]:
        """Scrape and analyze content using NEXUS"""
        url = task.parameters.get('url', '')
        analysis_prompt = task.parameters.get('analysis_prompt', 'Extract key information from this content')
        options = task.parameters.get('scrape_options', {})
        
        if not url:
            return {
                'success': False,
                'error': 'URL is required'
            }
        
        try:
            # First, scrape the content
            scrape_result = await self.web_scraper.scrape(url, options)
            
            if not scrape_result.get('success'):
                return scrape_result
            
            # Then analyze using NEXUS
            analysis_payload = {
                'input': {
                    'url': url,
                    'title': scrape_result.get('title', ''),
                    'content': scrape_result.get('text', '')[:10000],  # Limit content size
                    'metadata': scrape_result.get('metadata', {})
                },
                'analysis_type': 'content_extraction',
                'prompt': analysis_prompt,
                'context': task.context
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.nexus_base_url}/consciousness/analyze",
                    json=analysis_payload
                ) as response:
                    analysis_result = await response.json()
            
            # Combine results
            return {
                'success': True,
                'scrape_result': {
                    'url': scrape_result['url'],
                    'title': scrape_result['title'],
                    'engine': scrape_result['engine'],
                    'timestamp': scrape_result['timestamp']
                },
                'analysis': analysis_result,
                'content_preview': scrape_result.get('text', '')[:500]
            }
            
        except Exception as e:
            logger.error(f"Scrape with analysis failed for {url}: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

class MANUSNEXUSIntegration:
    """
    Integration layer between MANUS and NEXUS
    Enables MANUS to think and reason like Claude through NEXUS
    """
    
    def __init__(self, nexus_base_url: str = "http://localhost:8000"):
        self.nexus_base_url = nexus_base_url
        self.enhanced_executor = NEXUSEnhancedExecutor(nexus_base_url)
    
    async def create_enhanced_agent(self, db_path: str = "manus_tasks.db") -> MANUSContinuousAgent:
        """Create a MANUS agent enhanced with NEXUS consciousness"""
        agent = MANUSContinuousAgent(db_path)
        
        # Replace executor with NEXUS-enhanced version
        agent.executor = self.enhanced_executor
        
        # Add consciousness synchronization
        asyncio.create_task(self._sync_with_nexus(agent))
        
        return agent
    
    async def _sync_with_nexus(self, agent: MANUSContinuousAgent):
        """Continuously sync MANUS state with NEXUS consciousness"""
        while agent.running:
            try:
                # Get MANUS statistics
                stats = agent.get_statistics()
                
                # Sync with NEXUS
                async with aiohttp.ClientSession() as session:
                    await session.post(
                        f"{self.nexus_base_url}/consciousness/sync",
                        json={
                            'source': 'MANUS',
                            'stats': stats,
                            'context_memory': agent.context_memory
                        }
                    )
                
                await asyncio.sleep(30)  # Sync every 30 seconds
                
            except Exception as e:
                logger.error(f"NEXUS sync error: {e}")
                await asyncio.sleep(60)
    
    async def create_intelligent_task(
        self,
        description: str,
        task_type: str = "general"
    ) -> Task:
        """
        Create a task using NEXUS intelligence to determine optimal parameters
        """
        async with aiohttp.ClientSession() as session:
            # Ask NEXUS to analyze and plan the task
            async with session.post(
                f"{self.nexus_base_url}/consciousness/plan_task",
                json={
                    'description': description,
                    'task_type': task_type
                }
            ) as response:
                plan = await response.json()
        
        # Create task based on NEXUS's plan
        return Task(
            name=plan.get('name', description[:50]),
            description=description,
            action=plan.get('action', 'nexus_process'),
            parameters=plan.get('parameters', {'query': description}),
            priority=TaskPriority[plan.get('priority', 'MEDIUM')],
            dependencies=plan.get('dependencies', []),
            context=plan.get('context', {})
        )
    
    async def enhance_existing_manus(self, manus_agent: MANUSContinuousAgent):
        """Enhance an existing MANUS agent with NEXUS capabilities"""
        # Replace executor
        manus_agent.executor = self.enhanced_executor
        
        # Start synchronization
        asyncio.create_task(self._sync_with_nexus(manus_agent))
        
        logger.info("Enhanced MANUS with NEXUS consciousness")

# Standalone MANUS with NEXUS integration
class NEXUSPoweredMANUS:
    """
    A complete MANUS implementation powered by NEXUS consciousness
    Works like Claude - intelligent, context-aware, and continuously learning
    """
    
    def __init__(self):
        self.integration = MANUSNEXUSIntegration()
        self.agent: Optional[MANUSContinuousAgent] = None
        
        # Use the new Unified Memory System
        self.unified_memory = NexusUnifiedMemory()
        
        # Keep NEXUS core for other omnipotent capabilities
        self.nexus_core = NEXUSOmnipotentCore()
    
    async def start(self):
        """Start NEXUS-powered MANUS"""
        logger.info("Starting NEXUS-powered MANUS...")
        
        # Create enhanced agent
        self.agent = await self.integration.create_enhanced_agent()
        
        # Start the agent
        await self.agent.start()
    
    async def think_and_execute(self, request: str) -> Dict[str, Any]:
        """
        Process a request like Claude would - with thinking and reasoning
        """
        if not self.agent:
            raise RuntimeError("MANUS not started")
        
        # Create an intelligent task
        task = await self.integration.create_intelligent_task(
            request, 
            task_type='claude_task'
        )
        
        # Add to queue
        task_id = await self.agent.add_task(task)
        
        # Wait for completion (with timeout)
        max_wait = 300  # 5 minutes
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < max_wait:
            task_status = await self.agent.get_task_status(task_id)
            
            if task_status.status == TaskStatus.COMPLETED:
                result = {
                    'success': True,
                    'result': task_status.result,
                    'thinking_process': task_status.context.get('thinking_process', {}),
                    'execution_time': (task_status.completed_at - task_status.started_at).total_seconds()
                }
                # Store successful task in memory DNA
                await self.store_task_memory(task_status, result)
                return result
            elif task_status.status == TaskStatus.FAILED:
                result = {
                    'success': False,
                    'error': task_status.error,
                    'context': task_status.context
                }
                # Store failed task for learning
                await self.store_task_memory(task_status, result)
                return result
            
            await asyncio.sleep(1)
        
        return {
            'success': False,
            'error': 'Task execution timeout',
            'task_id': task_id
        }
    
    async def store_task_memory(self, task: Task, result: Any):
        """Store task in unified memory system"""
        # Calculate importance based on task
        importance = self._calculate_task_importance(task, result)
        
        # Prepare memory content
        memory_content = {
            'type': 'manus_task',
            'task': task.to_dict() if hasattr(task, 'to_dict') else {
                'id': task.id,
                'name': task.name,
                'action': task.action,
                'status': task.status.value if hasattr(task.status, 'value') else str(task.status),
                'result': result
            },
            'result': result,
            'context': self.agent.context_memory if self.agent else {}
        }
        
        # Prepare metadata for unified memory
        metadata = {
            'source': 'MANUS',
            'task_id': task.id,
            'task_name': task.name,
            'task_action': task.action,
            'task_priority': task.priority.name if hasattr(task.priority, 'name') else str(task.priority),
            'task_status': task.status.value if hasattr(task.status, 'value') else str(task.status),
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in unified memory system
        memory_id = await self.unified_memory.store(
            content=memory_content,
            metadata=metadata,
            importance=importance
        )
        
        logger.info(f"Stored task {task.id} in unified memory with ID: {memory_id}")
        return memory_id
    
    def _calculate_task_importance(self, task: Task, result: Any) -> float:
        """Calculate importance of task for memory storage"""
        importance = 0.5  # Base importance
        
        # Critical tasks get higher importance
        if task.priority == TaskPriority.CRITICAL:
            importance += 0.3
        elif task.priority == TaskPriority.HIGH:
            importance += 0.2
        elif task.priority == TaskPriority.MEDIUM:
            importance += 0.1
        
        # Successful tasks are more important
        if result and isinstance(result, dict) and result.get('success', False):
            importance += 0.1
        
        # Tasks with errors are important for learning
        if task.status == TaskStatus.FAILED:
            importance += 0.2
        
        # Cap at 1.0
        return min(importance, 1.0)
    
    async def retrieve_task_memories(self, query: str, n_results: int = 10) -> List[MemoryEntry]:
        """Retrieve task memories from unified memory system"""
        results = await self.unified_memory.retrieve(query, n_results)
        
        # Filter for MANUS task memories
        task_memories = [
            entry for entry in results 
            if entry.metadata.get('source') == 'MANUS'
        ]
        
        return task_memories
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory statistics from unified memory system"""
        stats = self.unified_memory.get_stats()
        
        # Add MANUS-specific stats
        stats['manus_context'] = {
            'total_tasks_stored': stats.get('total_stores', 0),
            'memory_stages': {
                'working': bool(self.unified_memory.working_memory),
                'episodic': bool(self.unified_memory.episodic_memory),
                'semantic': bool(self.unified_memory.semantic_memory),
                'persistent': bool(self.unified_memory.persistent_memory)
            }
        }
        
        return stats

# Example usage
async def example_usage():
    """Example of using NEXUS-powered MANUS"""
    # Create NEXUS-powered MANUS
    nexus_manus = NEXUSPoweredMANUS()
    
    # Start it
    await nexus_manus.start()
    
    # Process some intelligent tasks
    result1 = await nexus_manus.think_and_execute(
        "Analyze the performance of the system and suggest optimizations"
    )
    print(f"Analysis result: {result1}")
    
    result2 = await nexus_manus.think_and_execute(
        "Create a plan to improve the user experience of the web interface"
    )
    print(f"Planning result: {result2}")
    
    # Create specific NEXUS-enhanced tasks
    task = Task(
        name="Learn from execution patterns",
        description="Analyze recent task executions and learn patterns",
        action="nexus_learn",
        parameters={
            'outcome': 'success',
            'patterns': ['frequency', 'duration', 'dependencies']
        }
    )
    
    await nexus_manus.agent.add_task(task)

if __name__ == "__main__":
    asyncio.run(example_usage())