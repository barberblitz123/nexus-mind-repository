#!/usr/bin/env python3
"""
NEXUS Self-Improvement Engine - Autonomous Learning and Optimization System
Tracks performance, recognizes patterns, generates optimized code, and creates new tools
"""

import os
import json
import time
import hashlib
import sqlite3
import asyncio
import inspect
import ast
import sys
import traceback
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
import numpy as np
from pathlib import Path
import networkx as nx
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import re

# Import NEXUS components
try:
    from nexus_memory_core import NexusMemoryCore
    from nexus_unified_tools import NexusUnifiedTools
except ImportError:
    print("Warning: Some NEXUS components not found. Running in standalone mode.")

@dataclass
class ActionMetric:
    """Metrics for tracking action performance"""
    action_id: str
    action_type: str
    timestamp: float
    duration: float
    success: bool
    error: Optional[str]
    input_hash: str
    output_hash: str
    memory_usage: int
    cpu_usage: float
    context: Dict[str, Any]

@dataclass
class Pattern:
    """Recognized pattern in action sequences"""
    pattern_id: str
    sequence: List[str]
    frequency: int
    avg_duration: float
    success_rate: float
    contexts: List[Dict[str, Any]]
    optimization_potential: float

@dataclass
class GeneratedTool:
    """Dynamically generated tool"""
    tool_id: str
    name: str
    code: str
    pattern_id: str
    performance_gain: float
    usage_count: int
    last_modified: float

class NexusSelfImprovement:
    """Self-Improvement Engine for NEXUS 2.0"""
    
    def __init__(self, db_path: str = "nexus_learning.db"):
        self.db_path = db_path
        self.memory_core = None
        self.unified_tools = None
        
        # Performance tracking
        self.action_buffer = []
        self.pattern_buffer = defaultdict(list)
        self.performance_history = []
        
        # Learning parameters
        self.learning_rate = 0.1
        self.min_pattern_frequency = 3
        self.optimization_threshold = 0.7
        self.safety_threshold = 0.95
        
        # Knowledge graph
        self.knowledge_graph = nx.DiGraph()
        
        # Initialize database
        self._init_database()
        
        # Load existing patterns and tools
        self._load_learned_data()
        
        # Start background learning tasks
        self._start_learning_loop()
    
    def _init_database(self):
        """Initialize SQLite database for learning storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Action metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS action_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_id TEXT UNIQUE,
                action_type TEXT,
                timestamp REAL,
                duration REAL,
                success INTEGER,
                error TEXT,
                input_hash TEXT,
                output_hash TEXT,
                memory_usage INTEGER,
                cpu_usage REAL,
                context TEXT
            )
        ''')
        
        # Patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                pattern_id TEXT PRIMARY KEY,
                sequence TEXT,
                frequency INTEGER,
                avg_duration REAL,
                success_rate REAL,
                contexts TEXT,
                optimization_potential REAL,
                created_at REAL,
                last_seen REAL
            )
        ''')
        
        # Generated tools table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generated_tools (
                tool_id TEXT PRIMARY KEY,
                name TEXT,
                code TEXT,
                pattern_id TEXT,
                performance_gain REAL,
                usage_count INTEGER,
                created_at REAL,
                last_modified REAL,
                FOREIGN KEY (pattern_id) REFERENCES patterns(pattern_id)
            )
        ''')
        
        # Knowledge graph nodes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_nodes (
                node_id TEXT PRIMARY KEY,
                node_type TEXT,
                data TEXT,
                created_at REAL
            )
        ''')
        
        # Knowledge graph edges
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_edges (
                edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT,
                target_id TEXT,
                edge_type TEXT,
                weight REAL,
                data TEXT,
                created_at REAL,
                FOREIGN KEY (source_id) REFERENCES knowledge_nodes(node_id),
                FOREIGN KEY (target_id) REFERENCES knowledge_nodes(node_id)
            )
        ''')
        
        # Learning parameters table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_params (
                param_name TEXT PRIMARY KEY,
                value REAL,
                updated_at REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def track_action(self, action_type: str, func: Callable, *args, **kwargs) -> Any:
        """Track and analyze action performance"""
        action_id = hashlib.md5(f"{action_type}_{time.time()}".encode()).hexdigest()
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        # Create input hash for pattern detection
        input_data = json.dumps({"args": str(args), "kwargs": str(kwargs)}, sort_keys=True)
        input_hash = hashlib.md5(input_data.encode()).hexdigest()[:16]
        
        success = False
        error = None
        result = None
        
        try:
            # Execute the action
            result = func(*args, **kwargs)
            success = True
            
            # Update knowledge graph
            self._update_knowledge_graph(action_type, args, kwargs, result)
            
        except Exception as e:
            error = str(e)
            traceback.print_exc()
        
        # Calculate metrics
        duration = time.time() - start_time
        memory_usage = self._get_memory_usage() - start_memory
        cpu_usage = self._estimate_cpu_usage(duration)
        
        # Create output hash
        output_hash = hashlib.md5(str(result).encode()).hexdigest()[:16] if result else ""
        
        # Create metric
        metric = ActionMetric(
            action_id=action_id,
            action_type=action_type,
            timestamp=start_time,
            duration=duration,
            success=success,
            error=error,
            input_hash=input_hash,
            output_hash=output_hash,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            context={"args": str(args)[:100], "kwargs": str(kwargs)[:100]}
        )
        
        # Store metric
        self._store_metric(metric)
        self.action_buffer.append(metric)
        
        # Trigger pattern analysis if buffer is large enough
        if len(self.action_buffer) >= 10:
            asyncio.create_task(self._analyze_patterns())
        
        # Adjust learning rate based on success
        self._adjust_learning_rate(success)
        
        return result
    
    def _store_metric(self, metric: ActionMetric):
        """Store action metric in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO action_metrics 
            (action_id, action_type, timestamp, duration, success, error, 
             input_hash, output_hash, memory_usage, cpu_usage, context)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metric.action_id, metric.action_type, metric.timestamp,
            metric.duration, int(metric.success), metric.error,
            metric.input_hash, metric.output_hash, metric.memory_usage,
            metric.cpu_usage, json.dumps(metric.context)
        ))
        
        conn.commit()
        conn.close()
    
    async def _analyze_patterns(self):
        """Analyze action buffer for patterns"""
        if len(self.action_buffer) < 2:
            return
        
        # Group actions by type
        action_sequences = defaultdict(list)
        for metric in self.action_buffer:
            action_sequences[metric.action_type].append(metric)
        
        # Find repeated sequences
        for action_type, metrics in action_sequences.items():
            if len(metrics) >= self.min_pattern_frequency:
                # Check for repeated input patterns
                input_patterns = Counter([m.input_hash for m in metrics])
                
                for input_hash, count in input_patterns.items():
                    if count >= self.min_pattern_frequency:
                        # Calculate pattern metrics
                        pattern_metrics = [m for m in metrics if m.input_hash == input_hash]
                        avg_duration = np.mean([m.duration for m in pattern_metrics])
                        success_rate = sum(1 for m in pattern_metrics if m.success) / len(pattern_metrics)
                        
                        # Calculate optimization potential
                        duration_variance = np.var([m.duration for m in pattern_metrics])
                        optimization_potential = min(1.0, duration_variance / (avg_duration + 1e-6))
                        
                        # Create pattern
                        pattern = Pattern(
                            pattern_id=f"{action_type}_{input_hash}",
                            sequence=[action_type],
                            frequency=count,
                            avg_duration=avg_duration,
                            success_rate=success_rate,
                            contexts=[m.context for m in pattern_metrics],
                            optimization_potential=optimization_potential
                        )
                        
                        # Store pattern
                        self._store_pattern(pattern)
                        
                        # Generate optimized tool if potential is high
                        if optimization_potential > self.optimization_threshold:
                            await self._generate_optimized_tool(pattern)
        
        # Clear old entries from buffer
        current_time = time.time()
        self.action_buffer = [m for m in self.action_buffer 
                             if current_time - m.timestamp < 3600]  # Keep last hour
    
    def _store_pattern(self, pattern: Pattern):
        """Store recognized pattern in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO patterns
            (pattern_id, sequence, frequency, avg_duration, success_rate,
             contexts, optimization_potential, created_at, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pattern.pattern_id,
            json.dumps(pattern.sequence),
            pattern.frequency,
            pattern.avg_duration,
            pattern.success_rate,
            json.dumps(pattern.contexts),
            pattern.optimization_potential,
            time.time(),
            time.time()
        ))
        
        conn.commit()
        conn.close()
    
    async def _generate_optimized_tool(self, pattern: Pattern):
        """Generate optimized tool for recognized pattern"""
        tool_name = f"optimized_{pattern.pattern_id}"
        
        # Analyze pattern contexts to understand parameters
        param_analysis = self._analyze_parameters(pattern.contexts)
        
        # Generate optimized code
        code = self._generate_tool_code(pattern, param_analysis)
        
        # Test generated code for safety
        if self._validate_generated_code(code):
            # Create tool
            tool = GeneratedTool(
                tool_id=hashlib.md5(f"{tool_name}_{time.time()}".encode()).hexdigest(),
                name=tool_name,
                code=code,
                pattern_id=pattern.pattern_id,
                performance_gain=0.0,  # Will be measured
                usage_count=0,
                last_modified=time.time()
            )
            
            # Store tool
            self._store_generated_tool(tool)
            
            # Dynamically load tool
            self._load_generated_tool(tool)
    
    def _analyze_parameters(self, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze contexts to understand common parameters"""
        param_analysis = {
            "common_args": [],
            "common_kwargs": {},
            "variations": []
        }
        
        # Extract common patterns from contexts
        all_args = []
        all_kwargs = []
        
        for context in contexts:
            if "args" in context:
                all_args.append(context["args"])
            if "kwargs" in context:
                all_kwargs.append(context["kwargs"])
        
        # Find most common values
        if all_args:
            param_analysis["common_args"] = Counter(all_args).most_common(1)[0][0]
        if all_kwargs:
            param_analysis["common_kwargs"] = Counter(all_kwargs).most_common(1)[0][0]
        
        return param_analysis
    
    def _generate_tool_code(self, pattern: Pattern, param_analysis: Dict[str, Any]) -> str:
        """Generate optimized Python code for pattern"""
        # Template for generated tool
        code_template = '''
def {func_name}(self, *args, **kwargs):
    """Auto-generated optimized function for pattern: {pattern_id}
    Average duration: {avg_duration:.3f}s
    Success rate: {success_rate:.2%}
    """
    # Pre-computed optimizations
    {optimizations}
    
    # Core logic
    try:
        {core_logic}
        return result
    except Exception as e:
        # Fallback to original implementation
        return self._original_{action_type}(*args, **kwargs)
'''
        
        # Generate optimizations based on pattern
        optimizations = self._generate_optimizations(pattern, param_analysis)
        core_logic = self._generate_core_logic(pattern, param_analysis)
        
        # Fill template
        code = code_template.format(
            func_name=f"optimized_{pattern.sequence[0]}",
            pattern_id=pattern.pattern_id,
            avg_duration=pattern.avg_duration,
            success_rate=pattern.success_rate,
            optimizations=optimizations,
            core_logic=core_logic,
            action_type=pattern.sequence[0]
        )
        
        return code
    
    def _generate_optimizations(self, pattern: Pattern, param_analysis: Dict[str, Any]) -> str:
        """Generate optimization code based on pattern analysis"""
        optimizations = []
        
        # Cache frequently used values
        if pattern.frequency > 10:
            optimizations.append("# Cache for frequent calls")
            optimizations.append("cache_key = hashlib.md5(str(args).encode()).hexdigest()")
            optimizations.append("if hasattr(self, '_cache') and cache_key in self._cache:")
            optimizations.append("    return self._cache[cache_key]")
        
        # Pre-compute common operations
        if pattern.avg_duration > 0.1:
            optimizations.append("\n# Pre-compute common operations")
            optimizations.append("# Based on pattern analysis")
        
        return "\n    ".join(optimizations)
    
    def _generate_core_logic(self, pattern: Pattern, param_analysis: Dict[str, Any]) -> str:
        """Generate core logic for optimized function"""
        # Basic implementation - can be enhanced with ML
        logic = []
        
        logic.append("# Optimized execution path")
        logic.append("result = None")
        
        # Add specific optimizations based on action type
        if "file" in pattern.sequence[0].lower():
            logic.append("# File operation optimization")
            logic.append("with open(args[0], 'r') as f:")
            logic.append("    result = f.read()")
        elif "network" in pattern.sequence[0].lower():
            logic.append("# Network operation optimization")
            logic.append("import aiohttp")
            logic.append("async with aiohttp.ClientSession() as session:")
            logic.append("    result = await session.get(args[0])")
        else:
            logic.append("# Generic optimization")
            logic.append("result = self._execute_optimized(*args, **kwargs)")
        
        return "\n        ".join(logic)
    
    def _validate_generated_code(self, code: str) -> bool:
        """Validate generated code for safety"""
        try:
            # Parse code to check syntax
            ast.parse(code)
            
            # Check for dangerous operations
            dangerous_patterns = [
                r'exec\s*\(', r'eval\s*\(', r'__import__',
                r'subprocess', r'os\.system', r'open\s*\(.+,\s*["\']w'
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, code):
                    return False
            
            # Additional safety checks
            if len(code) > 10000:  # Code too long
                return False
            
            return True
            
        except SyntaxError:
            return False
    
    def _store_generated_tool(self, tool: GeneratedTool):
        """Store generated tool in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO generated_tools
            (tool_id, name, code, pattern_id, performance_gain,
             usage_count, created_at, last_modified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tool.tool_id, tool.name, tool.code, tool.pattern_id,
            tool.performance_gain, tool.usage_count,
            time.time(), tool.last_modified
        ))
        
        conn.commit()
        conn.close()
    
    def _load_generated_tool(self, tool: GeneratedTool):
        """Dynamically load generated tool into runtime"""
        try:
            # Create a namespace for the tool
            namespace = {
                'self': self,
                'hashlib': hashlib,
                'time': time,
                'json': json,
                'np': np
            }
            
            # Execute the code in namespace
            exec(tool.code, namespace)
            
            # Find the function and bind it
            for name, obj in namespace.items():
                if callable(obj) and name.startswith('optimized_'):
                    setattr(self, name, obj)
                    print(f"Loaded optimized tool: {name}")
                    
        except Exception as e:
            print(f"Failed to load generated tool {tool.name}: {e}")
    
    def _update_knowledge_graph(self, action_type: str, args: tuple, kwargs: dict, result: Any):
        """Update knowledge graph with new relationships"""
        # Create nodes for action and result
        action_node = f"action_{action_type}_{time.time()}"
        result_node = f"result_{type(result).__name__}_{time.time()}"
        
        # Add nodes
        self.knowledge_graph.add_node(action_node, type="action", data=action_type)
        self.knowledge_graph.add_node(result_node, type="result", data=str(result)[:100])
        
        # Add edge
        self.knowledge_graph.add_edge(action_node, result_node, weight=1.0)
        
        # Store in database
        self._store_knowledge_node(action_node, "action", action_type)
        self._store_knowledge_node(result_node, "result", str(result)[:100])
        self._store_knowledge_edge(action_node, result_node, "produces", 1.0)
        
        # Analyze graph for insights
        if len(self.knowledge_graph) > 100:
            asyncio.create_task(self._analyze_knowledge_graph())
    
    def _store_knowledge_node(self, node_id: str, node_type: str, data: str):
        """Store knowledge node in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO knowledge_nodes
            (node_id, node_type, data, created_at)
            VALUES (?, ?, ?, ?)
        ''', (node_id, node_type, data, time.time()))
        
        conn.commit()
        conn.close()
    
    def _store_knowledge_edge(self, source: str, target: str, edge_type: str, weight: float):
        """Store knowledge edge in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO knowledge_edges
            (source_id, target_id, edge_type, weight, data, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (source, target, edge_type, weight, "{}", time.time()))
        
        conn.commit()
        conn.close()
    
    async def _analyze_knowledge_graph(self):
        """Analyze knowledge graph for insights"""
        # Find central nodes (most connected)
        centrality = nx.degree_centrality(self.knowledge_graph)
        top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Find clusters
        if len(self.knowledge_graph) > 20:
            communities = nx.community.louvain_communities(self.knowledge_graph.to_undirected())
            
            # Store insights
            insights = {
                "central_nodes": top_nodes,
                "communities": [list(c) for c in communities],
                "graph_density": nx.density(self.knowledge_graph)
            }
            
            # Use insights to improve performance
            self._apply_graph_insights(insights)
    
    def _apply_graph_insights(self, insights: Dict[str, Any]):
        """Apply insights from knowledge graph analysis"""
        # Adjust learning parameters based on graph density
        if insights["graph_density"] > 0.7:
            # Dense graph - increase learning rate
            self.learning_rate = min(0.5, self.learning_rate * 1.1)
        elif insights["graph_density"] < 0.3:
            # Sparse graph - decrease learning rate
            self.learning_rate = max(0.01, self.learning_rate * 0.9)
        
        # Update learning parameters in database
        self._update_learning_param("learning_rate", self.learning_rate)
    
    def _adjust_learning_rate(self, success: bool):
        """Adjust learning rate based on success/failure"""
        if success:
            # Increase learning rate slightly on success
            self.learning_rate = min(0.5, self.learning_rate * 1.01)
        else:
            # Decrease learning rate on failure
            self.learning_rate = max(0.01, self.learning_rate * 0.95)
        
        # Store update
        self._update_learning_param("learning_rate", self.learning_rate)
    
    def _update_learning_param(self, param_name: str, value: float):
        """Update learning parameter in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO learning_params
            (param_name, value, updated_at)
            VALUES (?, ?, ?)
        ''', (param_name, value, time.time()))
        
        conn.commit()
        conn.close()
    
    def self_modify(self, modification_type: str, target: str, new_code: str) -> bool:
        """Self-modify with safety checks"""
        # Validate modification
        if not self._validate_generated_code(new_code):
            print(f"Modification failed safety check: {modification_type}")
            return False
        
        # Check performance impact
        if not self._check_modification_safety(modification_type, target):
            print(f"Modification would degrade performance: {modification_type}")
            return False
        
        # Apply modification
        try:
            # Backup current state
            backup = getattr(self, target, None) if hasattr(self, target) else None
            
            # Execute modification
            namespace = {'self': self}
            exec(new_code, namespace)
            
            # Test modification
            if self._test_modification(target):
                print(f"Successfully applied modification: {modification_type}")
                return True
            else:
                # Rollback
                if backup:
                    setattr(self, target, backup)
                print(f"Modification test failed, rolled back: {modification_type}")
                return False
                
        except Exception as e:
            print(f"Modification error: {e}")
            return False
    
    def _check_modification_safety(self, modification_type: str, target: str) -> bool:
        """Check if modification is safe based on historical performance"""
        # Query recent performance metrics
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent success rate
        cursor.execute('''
            SELECT AVG(success) as success_rate
            FROM action_metrics
            WHERE timestamp > ?
        ''', (time.time() - 3600,))  # Last hour
        
        result = cursor.fetchone()
        conn.close()
        
        current_success_rate = result[0] if result and result[0] else 0.5
        
        # Only allow modifications if success rate is above threshold
        return current_success_rate >= self.safety_threshold
    
    def _test_modification(self, target: str) -> bool:
        """Test modification with synthetic workload"""
        try:
            # Run basic tests on modified component
            if hasattr(self, target) and callable(getattr(self, target)):
                # Call with test parameters
                test_func = getattr(self, target)
                test_func("test_input")
                return True
            return True
        except:
            return False
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Overall metrics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_actions,
                AVG(success) as success_rate,
                AVG(duration) as avg_duration,
                SUM(success) as successful_actions
            FROM action_metrics
            WHERE timestamp > ?
        ''', (time.time() - 86400,))  # Last 24 hours
        
        overall = cursor.fetchone()
        
        # Pattern metrics
        cursor.execute('''
            SELECT COUNT(*) as pattern_count,
                   AVG(optimization_potential) as avg_potential
            FROM patterns
        ''')
        
        patterns = cursor.fetchone()
        
        # Generated tools metrics
        cursor.execute('''
            SELECT COUNT(*) as tool_count,
                   SUM(usage_count) as total_usage,
                   AVG(performance_gain) as avg_gain
            FROM generated_tools
        ''')
        
        tools = cursor.fetchone()
        
        conn.close()
        
        report = {
            "overall_performance": {
                "total_actions": overall[0] if overall else 0,
                "success_rate": overall[1] if overall else 0,
                "avg_duration": overall[2] if overall else 0,
                "successful_actions": overall[3] if overall else 0
            },
            "pattern_recognition": {
                "patterns_found": patterns[0] if patterns else 0,
                "avg_optimization_potential": patterns[1] if patterns else 0
            },
            "generated_tools": {
                "tools_created": tools[0] if tools else 0,
                "total_usage": tools[1] if tools else 0,
                "avg_performance_gain": tools[2] if tools else 0
            },
            "learning_parameters": {
                "current_learning_rate": self.learning_rate,
                "optimization_threshold": self.optimization_threshold,
                "safety_threshold": self.safety_threshold
            },
            "knowledge_graph": {
                "total_nodes": len(self.knowledge_graph),
                "total_edges": self.knowledge_graph.number_of_edges(),
                "graph_density": nx.density(self.knowledge_graph) if len(self.knowledge_graph) > 0 else 0
            }
        }
        
        return report
    
    def visualize_knowledge_graph(self, output_path: str = "nexus_knowledge_graph.png"):
        """Visualize the knowledge graph"""
        if len(self.knowledge_graph) == 0:
            print("Knowledge graph is empty")
            return
        
        plt.figure(figsize=(15, 10))
        
        # Create layout
        pos = nx.spring_layout(self.knowledge_graph, k=2, iterations=50)
        
        # Draw nodes
        node_colors = []
        for node in self.knowledge_graph.nodes():
            if self.knowledge_graph.nodes[node].get('type') == 'action':
                node_colors.append('lightblue')
            else:
                node_colors.append('lightgreen')
        
        nx.draw_networkx_nodes(self.knowledge_graph, pos, 
                              node_color=node_colors, 
                              node_size=500, alpha=0.9)
        
        # Draw edges
        nx.draw_networkx_edges(self.knowledge_graph, pos, 
                              edge_color='gray', 
                              arrows=True, alpha=0.5)
        
        # Draw labels
        labels = {node: node.split('_')[0] for node in self.knowledge_graph.nodes()}
        nx.draw_networkx_labels(self.knowledge_graph, pos, labels, 
                               font_size=8)
        
        plt.title("NEXUS Knowledge Graph")
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Knowledge graph saved to {output_path}")
    
    def _load_learned_data(self):
        """Load previously learned patterns and tools"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Load generated tools
        cursor.execute('SELECT * FROM generated_tools')
        tools = cursor.fetchall()
        
        for tool_data in tools:
            tool = GeneratedTool(
                tool_id=tool_data[0],
                name=tool_data[1],
                code=tool_data[2],
                pattern_id=tool_data[3],
                performance_gain=tool_data[4],
                usage_count=tool_data[5],
                last_modified=tool_data[7]
            )
            self._load_generated_tool(tool)
        
        # Load learning parameters
        cursor.execute('SELECT * FROM learning_params')
        params = cursor.fetchall()
        
        for param in params:
            if param[0] == 'learning_rate':
                self.learning_rate = param[1]
            elif param[0] == 'optimization_threshold':
                self.optimization_threshold = param[1]
            elif param[0] == 'safety_threshold':
                self.safety_threshold = param[1]
        
        conn.close()
        
        print(f"Loaded {len(tools)} generated tools")
    
    def _start_learning_loop(self):
        """Start background learning tasks"""
        async def learning_loop():
            while True:
                try:
                    # Analyze patterns every 5 minutes
                    await asyncio.sleep(300)
                    await self._analyze_patterns()
                    
                    # Analyze knowledge graph every 15 minutes
                    await asyncio.sleep(600)
                    await self._analyze_knowledge_graph()
                    
                    # Generate performance report every hour
                    await asyncio.sleep(2700)
                    report = self.get_performance_report()
                    print(f"Performance Report: {json.dumps(report, indent=2)}")
                    
                except Exception as e:
                    print(f"Learning loop error: {e}")
                    await asyncio.sleep(60)
        
        # Start in background
        asyncio.create_task(learning_loop())
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        except:
            return 0
    
    def _estimate_cpu_usage(self, duration: float) -> float:
        """Estimate CPU usage based on duration"""
        # Simple estimation - can be improved with actual CPU monitoring
        return min(1.0, duration / 0.1)  # Normalize to 0-1 range
    
    def integrate_with_nexus(self, memory_core: Any, unified_tools: Any):
        """Integrate with existing NEXUS components"""
        self.memory_core = memory_core
        self.unified_tools = unified_tools
        
        # Wrap existing methods to track performance
        if self.unified_tools:
            for attr_name in dir(self.unified_tools):
                attr = getattr(self.unified_tools, attr_name)
                if callable(attr) and not attr_name.startswith('_'):
                    # Create tracked version
                    def make_tracked(func, name):
                        def tracked_func(*args, **kwargs):
                            return self.track_action(name, func, *args, **kwargs)
                        return tracked_func
                    
                    # Replace with tracked version
                    setattr(self.unified_tools, attr_name, 
                           make_tracked(attr, attr_name))
        
        print("Self-improvement engine integrated with NEXUS")


# Example usage and testing
if __name__ == "__main__":
    # Initialize self-improvement engine
    engine = NexusSelfImprovement()
    
    # Example: Track a simple action
    def example_action(x, y):
        """Example action to track"""
        time.sleep(0.1)  # Simulate work
        return x + y
    
    # Track multiple executions
    print("Testing self-improvement engine...")
    
    for i in range(5):
        result = engine.track_action("add_numbers", example_action, i, i+1)
        print(f"Result {i}: {result}")
    
    # Test pattern with same inputs
    for i in range(5):
        result = engine.track_action("add_numbers", example_action, 10, 20)
        print(f"Repeated result: {result}")
    
    # Generate report
    print("\nPerformance Report:")
    report = engine.get_performance_report()
    print(json.dumps(report, indent=2))
    
    # Visualize knowledge graph
    engine.visualize_knowledge_graph()
    
    print("\nSelf-improvement engine initialized and learning!")