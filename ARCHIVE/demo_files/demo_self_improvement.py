#!/usr/bin/env python3
"""
Demonstration of NEXUS Self-Improvement Engine
Shows real-time learning, pattern recognition, and tool generation
"""

import asyncio
import time
import random
import json
from nexus_self_improvement import NexusSelfImprovement

class NexusSimulator:
    """Simulates NEXUS operations for demonstration"""
    
    def __init__(self):
        self.operation_count = 0
    
    def process_text(self, text: str, mode: str = "analyze") -> dict:
        """Simulate text processing with variable performance"""
        self.operation_count += 1
        
        # Simulate variable processing time
        if mode == "analyze":
            time.sleep(random.uniform(0.1, 0.3))
        elif mode == "summarize":
            time.sleep(random.uniform(0.2, 0.4))
        else:
            time.sleep(random.uniform(0.05, 0.15))
        
        # Simulate occasional failures
        if random.random() < 0.1:
            raise Exception("Processing error")
        
        return {
            "text": text,
            "mode": mode,
            "words": len(text.split()),
            "processed": True
        }
    
    def search_memory(self, query: str, limit: int = 10) -> list:
        """Simulate memory search"""
        self.operation_count += 1
        time.sleep(random.uniform(0.05, 0.2))
        
        # Return simulated results
        return [
            {"id": i, "content": f"Memory item {i} for query: {query}"}
            for i in range(min(limit, 5))
        ]
    
    def analyze_code(self, code: str, language: str = "python") -> dict:
        """Simulate code analysis"""
        self.operation_count += 1
        time.sleep(random.uniform(0.1, 0.5))
        
        return {
            "language": language,
            "lines": code.count('\n') + 1,
            "complexity": random.randint(1, 10),
            "issues": []
        }

async def demonstrate_learning():
    """Demonstrate the self-improvement engine"""
    print("=== NEXUS Self-Improvement Engine Demo ===\n")
    
    # Initialize components
    engine = NexusSelfImprovement("demo_learning.db")
    simulator = NexusSimulator()
    
    print("Phase 1: Initial Learning")
    print("-" * 40)
    
    # Phase 1: Perform various operations to establish baseline
    texts = [
        "The quick brown fox jumps over the lazy dog",
        "Machine learning is transforming software development",
        "NEXUS learns and improves with every interaction"
    ]
    
    # Repeat some operations to create patterns
    for _ in range(3):
        for text in texts:
            try:
                result = engine.track_action(
                    "process_text",
                    simulator.process_text,
                    text,
                    "analyze"
                )
                print(f"✓ Processed: {text[:30]}...")
            except Exception as e:
                print(f"✗ Error: {e}")
    
    # Show initial metrics
    await asyncio.sleep(1)
    report = engine.get_performance_report()
    print(f"\nInitial Performance:")
    print(f"  • Success Rate: {report['overall_performance']['success_rate']:.2%}")
    print(f"  • Avg Duration: {report['overall_performance']['avg_duration']:.3f}s")
    
    print("\nPhase 2: Pattern Recognition")
    print("-" * 40)
    
    # Perform repeated operations with same inputs
    for i in range(5):
        result = engine.track_action(
            "search_memory",
            simulator.search_memory,
            "machine learning",
            5
        )
        print(f"✓ Memory search {i+1}: Found {len(result)} items")
    
    # Trigger pattern analysis
    await engine._analyze_patterns()
    
    # Check for recognized patterns
    report = engine.get_performance_report()
    print(f"\nPatterns Found: {report['pattern_recognition']['patterns_found']}")
    print(f"Optimization Potential: {report['pattern_recognition']['avg_optimization_potential']:.2%}")
    
    print("\nPhase 3: Code Analysis Learning")
    print("-" * 40)
    
    # Analyze different code snippets
    code_samples = [
        "def hello():\n    print('Hello, World!')",
        "for i in range(10):\n    print(i)",
        "class NexusCore:\n    def __init__(self):\n        self.active = True"
    ]
    
    for code in code_samples:
        result = engine.track_action(
            "analyze_code",
            simulator.analyze_code,
            code,
            "python"
        )
        print(f"✓ Analyzed code: {result['lines']} lines, complexity: {result['complexity']}")
    
    print("\nPhase 4: Performance Optimization")
    print("-" * 40)
    
    # Simulate improved performance after learning
    print("Applying learned optimizations...")
    
    # Show improvement
    final_report = engine.get_performance_report()
    print(f"\nFinal Performance Report:")
    print(f"  • Total Actions: {final_report['overall_performance']['total_actions']}")
    print(f"  • Success Rate: {final_report['overall_performance']['success_rate']:.2%}")
    print(f"  • Patterns Found: {final_report['pattern_recognition']['patterns_found']}")
    print(f"  • Tools Generated: {final_report['generated_tools']['tools_created']}")
    print(f"  • Learning Rate: {final_report['learning_parameters']['current_learning_rate']:.3f}")
    
    print("\nPhase 5: Knowledge Graph Visualization")
    print("-" * 40)
    
    # Generate visualization
    engine.visualize_knowledge_graph("demo_knowledge_graph.png")
    print("✓ Knowledge graph saved to demo_knowledge_graph.png")
    
    print(f"\nKnowledge Graph Stats:")
    print(f"  • Nodes: {final_report['knowledge_graph']['total_nodes']}")
    print(f"  • Edges: {final_report['knowledge_graph']['total_edges']}")
    print(f"  • Density: {final_report['knowledge_graph']['graph_density']:.3f}")
    
    print("\nPhase 6: Self-Modification Test")
    print("-" * 40)
    
    # Test self-modification capability
    new_optimization = '''
def optimized_cache_lookup(self, key):
    """Optimized cache lookup with learning"""
    if hasattr(self, '_smart_cache'):
        return self._smart_cache.get(key)
    return None
'''
    
    success = engine.self_modify(
        "cache_optimization",
        "optimized_cache_lookup",
        new_optimization
    )
    
    print(f"✓ Self-modification {'succeeded' if success else 'failed'}")
    
    print("\n=== Demo Complete ===")
    print(f"Total operations tracked: {simulator.operation_count}")
    print("NEXUS is now smarter and will continue learning!\n")

async def demonstrate_continuous_learning():
    """Show continuous learning in action"""
    print("\n=== Continuous Learning Demo ===\n")
    
    engine = NexusSelfImprovement("continuous_learning.db")
    simulator = NexusSimulator()
    
    print("Simulating real-world usage patterns...\n")
    
    # Simulate different usage patterns over time
    patterns = [
        ("morning", ["email", "calendar", "news"]),
        ("work", ["code", "debug", "test", "commit"]),
        ("research", ["search", "analyze", "summarize"]),
        ("evening", ["review", "plan", "organize"])
    ]
    
    for pattern_name, actions in patterns:
        print(f"\nPattern: {pattern_name}")
        print("-" * 30)
        
        for _ in range(3):  # Repeat pattern
            for action in actions:
                result = engine.track_action(
                    f"{pattern_name}_{action}",
                    simulator.process_text,
                    f"Processing {action} task",
                    "analyze"
                )
                print(f"  • {action}: ✓")
                await asyncio.sleep(0.1)
        
        # Show learning progress
        report = engine.get_performance_report()
        print(f"  Learning Rate: {report['learning_parameters']['current_learning_rate']:.3f}")
    
    print("\n✓ NEXUS has learned your usage patterns and optimized accordingly!")

async def main():
    """Run all demonstrations"""
    # Basic learning demo
    await demonstrate_learning()
    
    # Continuous learning demo
    await demonstrate_continuous_learning()

if __name__ == "__main__":
    asyncio.run(main())