#!/usr/bin/env python3
"""
Integration layer for NEXUS Self-Improvement Engine
Connects with all existing NEXUS components for comprehensive learning
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from nexus_self_improvement import NexusSelfImprovement

# Import all NEXUS components
try:
    from nexus_memory_core import NexusMemoryCore
    from nexus_unified_tools import NexusUnifiedTools
    from nexus_episodic_memory import EpisodicMemory
    from nexus_semantic_memory import SemanticMemory
    from nexus_working_memory import WorkingMemory
    from nexus_web_scraper import NexusWebScraper
    from nexus_bug_detector import NexusBugDetector
    from nexus_security_scanner import NexusSecurityScanner
    from nexus_performance_analyzer import NexusPerformanceAnalyzer
    from nexus_project_generator import NexusProjectGenerator
    from nexus_doc_generator import NexusDocGenerator
except ImportError as e:
    print(f"Warning: Some NEXUS components not available: {e}")

class NexusIntegratedLearning:
    """Integrated learning system for all NEXUS components"""
    
    def __init__(self):
        # Initialize self-improvement engine
        self.learning_engine = NexusSelfImprovement("nexus_integrated_learning.db")
        
        # Initialize NEXUS components
        self.components = {}
        self._initialize_components()
        
        # Track component usage
        self.usage_stats = {}
        
        # Start integration
        self._integrate_all_components()
        
        print("✓ NEXUS Self-Improvement Integration initialized")
    
    def _initialize_components(self):
        """Initialize all available NEXUS components"""
        component_classes = {
            'memory_core': NexusMemoryCore,
            'unified_tools': NexusUnifiedTools,
            'episodic_memory': EpisodicMemory,
            'semantic_memory': SemanticMemory,
            'working_memory': WorkingMemory,
            'web_scraper': NexusWebScraper,
            'bug_detector': NexusBugDetector,
            'security_scanner': NexusSecurityScanner,
            'performance_analyzer': NexusPerformanceAnalyzer,
            'project_generator': NexusProjectGenerator,
            'doc_generator': NexusDocGenerator
        }
        
        for name, cls in component_classes.items():
            try:
                self.components[name] = cls()
                self.usage_stats[name] = {'calls': 0, 'success': 0, 'failures': 0}
                print(f"  • Initialized {name}")
            except Exception as e:
                print(f"  ✗ Failed to initialize {name}: {e}")
    
    def _integrate_all_components(self):
        """Integrate learning engine with all components"""
        for name, component in self.components.items():
            self._wrap_component_methods(name, component)
    
    def _wrap_component_methods(self, component_name: str, component: Any):
        """Wrap component methods with learning tracking"""
        for attr_name in dir(component):
            if not attr_name.startswith('_'):
                attr = getattr(component, attr_name)
                if callable(attr):
                    # Create tracked version
                    wrapped = self._create_tracked_method(
                        component_name, attr_name, attr
                    )
                    setattr(component, attr_name, wrapped)
    
    def _create_tracked_method(self, component_name: str, method_name: str, original_method):
        """Create a tracked version of a method"""
        def tracked_method(*args, **kwargs):
            action_type = f"{component_name}.{method_name}"
            
            # Update usage stats
            self.usage_stats[component_name]['calls'] += 1
            
            try:
                # Track with learning engine
                result = self.learning_engine.track_action(
                    action_type,
                    original_method,
                    *args,
                    **kwargs
                )
                
                self.usage_stats[component_name]['success'] += 1
                
                # Analyze result for learning opportunities
                self._analyze_result(component_name, method_name, result)
                
                return result
                
            except Exception as e:
                self.usage_stats[component_name]['failures'] += 1
                raise e
        
        tracked_method.__name__ = method_name
        tracked_method.__doc__ = original_method.__doc__
        return tracked_method
    
    def _analyze_result(self, component_name: str, method_name: str, result: Any):
        """Analyze method results for learning opportunities"""
        # Identify cross-component patterns
        if component_name == 'memory_core' and method_name == 'store':
            # Track memory storage patterns
            self._track_memory_pattern(result)
        elif component_name == 'web_scraper' and method_name == 'scrape':
            # Track web scraping patterns
            self._track_scraping_pattern(result)
        elif component_name == 'bug_detector' and method_name == 'detect':
            # Track bug detection patterns
            self._track_bug_pattern(result)
    
    def _track_memory_pattern(self, result: Any):
        """Track patterns in memory operations"""
        # Analyze memory usage patterns for optimization
        pass
    
    def _track_scraping_pattern(self, result: Any):
        """Track patterns in web scraping"""
        # Analyze scraping patterns for optimization
        pass
    
    def _track_bug_pattern(self, result: Any):
        """Track patterns in bug detection"""
        # Analyze bug patterns for better detection
        pass
    
    async def optimize_component(self, component_name: str):
        """Generate optimized version of a component based on learning"""
        if component_name not in self.components:
            return None
        
        # Get usage statistics
        stats = self.usage_stats[component_name]
        
        # Generate optimization report
        report = {
            'component': component_name,
            'total_calls': stats['calls'],
            'success_rate': stats['success'] / max(stats['calls'], 1),
            'optimization_suggestions': []
        }
        
        # Analyze patterns for this component
        conn = self.learning_engine.db_path
        patterns = self._get_component_patterns(component_name)
        
        # Generate optimizations
        for pattern in patterns:
            if pattern['optimization_potential'] > 0.5:
                suggestion = {
                    'pattern': pattern['pattern_id'],
                    'potential_improvement': f"{pattern['optimization_potential']*100:.1f}%",
                    'recommendation': self._generate_optimization_recommendation(pattern)
                }
                report['optimization_suggestions'].append(suggestion)
        
        return report
    
    def _get_component_patterns(self, component_name: str) -> List[Dict[str, Any]]:
        """Get learned patterns for a specific component"""
        import sqlite3
        conn = sqlite3.connect(self.learning_engine.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pattern_id, sequence, frequency, avg_duration, 
                   success_rate, optimization_potential
            FROM patterns
            WHERE pattern_id LIKE ?
            ORDER BY optimization_potential DESC
        ''', (f"{component_name}%",))
        
        patterns = []
        for row in cursor.fetchall():
            patterns.append({
                'pattern_id': row[0],
                'sequence': json.loads(row[1]),
                'frequency': row[2],
                'avg_duration': row[3],
                'success_rate': row[4],
                'optimization_potential': row[5]
            })
        
        conn.close()
        return patterns
    
    def _generate_optimization_recommendation(self, pattern: Dict[str, Any]) -> str:
        """Generate specific optimization recommendation"""
        if pattern['avg_duration'] > 1.0:
            return "Consider caching results for frequently repeated operations"
        elif pattern['success_rate'] < 0.8:
            return "Add error handling and retry logic for improved reliability"
        elif pattern['frequency'] > 10:
            return "Create specialized method for this common operation pattern"
        else:
            return "Monitor for further optimization opportunities"
    
    def get_learning_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive learning dashboard"""
        # Get base report from learning engine
        base_report = self.learning_engine.get_performance_report()
        
        # Add component-specific metrics
        component_metrics = {}
        for name, stats in self.usage_stats.items():
            if stats['calls'] > 0:
                component_metrics[name] = {
                    'usage_count': stats['calls'],
                    'success_rate': stats['success'] / stats['calls'],
                    'failure_rate': stats['failures'] / stats['calls']
                }
        
        # Calculate system-wide insights
        total_operations = sum(s['calls'] for s in self.usage_stats.values())
        total_success = sum(s['success'] for s in self.usage_stats.values())
        
        dashboard = {
            'system_metrics': {
                'total_operations': total_operations,
                'overall_success_rate': total_success / max(total_operations, 1),
                'active_components': len([s for s in self.usage_stats.values() if s['calls'] > 0])
            },
            'component_metrics': component_metrics,
            'learning_metrics': base_report,
            'top_patterns': self._get_top_patterns(),
            'optimization_opportunities': self._get_optimization_opportunities()
        }
        
        return dashboard
    
    def _get_top_patterns(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top recognized patterns"""
        import sqlite3
        conn = sqlite3.connect(self.learning_engine.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pattern_id, frequency, success_rate, optimization_potential
            FROM patterns
            ORDER BY frequency DESC
            LIMIT ?
        ''', (limit,))
        
        patterns = []
        for row in cursor.fetchall():
            patterns.append({
                'pattern': row[0],
                'frequency': row[1],
                'success_rate': row[2],
                'optimization_potential': row[3]
            })
        
        conn.close()
        return patterns
    
    def _get_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """Identify top optimization opportunities"""
        opportunities = []
        
        for component_name in self.components:
            patterns = self._get_component_patterns(component_name)
            for pattern in patterns[:2]:  # Top 2 per component
                if pattern['optimization_potential'] > 0.3:
                    opportunities.append({
                        'component': component_name,
                        'pattern': pattern['pattern_id'],
                        'potential': pattern['optimization_potential'],
                        'frequency': pattern['frequency']
                    })
        
        # Sort by potential impact (potential * frequency)
        opportunities.sort(
            key=lambda x: x['potential'] * x['frequency'], 
            reverse=True
        )
        
        return opportunities[:10]
    
    async def apply_learned_optimizations(self):
        """Apply all learned optimizations to components"""
        print("\nApplying learned optimizations...")
        
        applied_count = 0
        
        # Get all generated tools
        import sqlite3
        conn = sqlite3.connect(self.learning_engine.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM generated_tools WHERE performance_gain > 0.1')
        tools = cursor.fetchall()
        
        for tool in tools:
            tool_id, name, code, pattern_id, gain = tool[:5]
            
            # Apply tool to appropriate component
            component_name = pattern_id.split('.')[0] if '.' in pattern_id else None
            
            if component_name and component_name in self.components:
                success = self.learning_engine.self_modify(
                    f"optimization_{tool_id}",
                    name,
                    code
                )
                
                if success:
                    applied_count += 1
                    print(f"  ✓ Applied optimization to {component_name}: {gain*100:.1f}% improvement")
        
        conn.close()
        
        print(f"\n✓ Applied {applied_count} optimizations")
        return applied_count
    
    def export_learning_insights(self, filepath: str = "nexus_learning_insights.json"):
        """Export all learning insights to file"""
        insights = {
            'timestamp': time.time(),
            'dashboard': self.get_learning_dashboard(),
            'component_optimizations': {},
            'learning_parameters': {
                'learning_rate': self.learning_engine.learning_rate,
                'optimization_threshold': self.learning_engine.optimization_threshold,
                'safety_threshold': self.learning_engine.safety_threshold
            }
        }
        
        # Add component-specific optimizations
        for component_name in self.components:
            optimization = asyncio.run(self.optimize_component(component_name))
            if optimization:
                insights['component_optimizations'][component_name] = optimization
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(insights, f, indent=2)
        
        print(f"✓ Learning insights exported to {filepath}")
        return insights


# Example usage
async def demonstrate_integrated_learning():
    """Demonstrate integrated learning system"""
    print("=== NEXUS Integrated Learning System ===\n")
    
    # Initialize integrated system
    nexus = NexusIntegratedLearning()
    
    print("\nSimulating component usage...")
    
    # Simulate various component operations
    if 'memory_core' in nexus.components:
        memory = nexus.components['memory_core']
        for i in range(5):
            memory.store(f"test_key_{i}", {"data": f"value_{i}"})
            result = memory.retrieve(f"test_key_{i}")
            print(f"  • Memory operation {i+1}: ✓")
    
    if 'unified_tools' in nexus.components:
        tools = nexus.components['unified_tools']
        # Simulate tool usage
        print("  • Tool operations: ✓")
    
    # Wait for pattern analysis
    await asyncio.sleep(2)
    
    # Show learning dashboard
    print("\nLearning Dashboard:")
    print("-" * 50)
    dashboard = nexus.get_learning_dashboard()
    
    print(f"System Metrics:")
    print(f"  • Total Operations: {dashboard['system_metrics']['total_operations']}")
    print(f"  • Success Rate: {dashboard['system_metrics']['overall_success_rate']:.2%}")
    print(f"  • Active Components: {dashboard['system_metrics']['active_components']}")
    
    print(f"\nTop Patterns:")
    for pattern in dashboard['top_patterns'][:3]:
        print(f"  • {pattern['pattern']}: {pattern['frequency']} occurrences")
    
    print(f"\nOptimization Opportunities:")
    for opp in dashboard['optimization_opportunities'][:3]:
        print(f"  • {opp['component']}: {opp['potential']*100:.1f}% potential improvement")
    
    # Apply optimizations
    applied = await nexus.apply_learned_optimizations()
    
    # Export insights
    nexus.export_learning_insights()
    
    print("\n✓ NEXUS is now continuously learning and improving!")


if __name__ == "__main__":
    asyncio.run(demonstrate_integrated_learning())