"""
NEXUS Performance Analyzer - Omnipotent Performance Analysis and Optimization Engine
================================================================================
Advanced performance analysis system with complexity calculation, profiling,
and optimization suggestions.
"""

import ast
import time
import tracemalloc
import cProfile
import pstats
import io
import re
import sqlite3
from typing import Dict, List, Tuple, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
import threading
import psutil
import numpy as np
from datetime import datetime
import json

from nexus_unified_tools import NEXUSToolBase


@dataclass
class ComplexityResult:
    """Result of complexity analysis"""
    time_complexity: str
    space_complexity: str
    dominant_operations: List[str]
    nested_loops: int
    recursive_calls: bool
    confidence: float


@dataclass
class PerformanceMetrics:
    """Performance measurement results"""
    execution_time: float
    memory_usage: Dict[str, float]
    cpu_usage: float
    function_calls: Dict[str, int]
    hotspots: List[Tuple[str, float]]


@dataclass
class OptimizationSuggestion:
    """Optimization recommendation"""
    category: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    description: str
    code_location: Optional[str]
    expected_improvement: Optional[str]
    implementation_hint: Optional[str]


@dataclass
class QueryAnalysis:
    """Database query analysis result"""
    query_type: str
    table_names: List[str]
    has_joins: bool
    missing_indexes: List[str]
    is_n_plus_one: bool
    optimization_suggestions: List[str]


class ComplexityAnalyzer(ast.NodeVisitor):
    """AST visitor for analyzing code complexity"""
    
    def __init__(self):
        self.loop_depth = 0
        self.max_loop_depth = 0
        self.recursive_calls = False
        self.function_calls = defaultdict(int)
        self.operations = defaultdict(int)
        self.current_function = None
        self.space_usage = defaultdict(int)
        
    def visit_For(self, node):
        self.loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.loop_depth)
        self.operations['loop'] += 1
        self.generic_visit(node)
        self.loop_depth -= 1
        
    def visit_While(self, node):
        self.loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.loop_depth)
        self.operations['loop'] += 1
        self.generic_visit(node)
        self.loop_depth -= 1
        
    def visit_FunctionDef(self, node):
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
        
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            self.function_calls[func_name] += 1
            
            # Check for recursive calls
            if func_name == self.current_function:
                self.recursive_calls = True
                
            # Track specific operations
            if func_name in ['sorted', 'sort']:
                self.operations['sort'] += 1
            elif func_name in ['append', 'extend', 'insert']:
                self.operations['list_op'] += 1
            elif func_name in ['get', 'pop', 'setdefault']:
                self.operations['dict_op'] += 1
                
        self.generic_visit(node)
        
    def visit_ListComp(self, node):
        self.operations['comprehension'] += 1
        self.space_usage['list'] += 1
        self.generic_visit(node)
        
    def visit_DictComp(self, node):
        self.operations['comprehension'] += 1
        self.space_usage['dict'] += 1
        self.generic_visit(node)
        
    def visit_List(self, node):
        self.space_usage['list'] += 1
        self.generic_visit(node)
        
    def visit_Dict(self, node):
        self.space_usage['dict'] += 1
        self.generic_visit(node)


class PerformanceAnalyzerOmnipotent(NEXUSToolBase):
    """
    Omnipotent Performance Analysis Engine for NEXUS
    Provides comprehensive performance analysis and optimization
    """
    
    def __init__(self):
        super().__init__(
            name="Performance Analyzer",
            description="Advanced performance analysis and optimization engine",
            version="1.0.0"
        )
        self.profiler = cProfile.Profile()
        self.memory_snapshots = []
        self.execution_cache = {}
        self.query_patterns = self._load_query_patterns()
        
    def _load_query_patterns(self) -> Dict[str, re.Pattern]:
        """Load common database query patterns"""
        return {
            'select': re.compile(r'SELECT\s+.*?\s+FROM\s+(\w+)', re.IGNORECASE),
            'join': re.compile(r'JOIN\s+(\w+)', re.IGNORECASE),
            'where': re.compile(r'WHERE\s+(.*?)(?:ORDER|GROUP|LIMIT|$)', re.IGNORECASE),
            'n_plus_one': re.compile(r'SELECT.*?WHERE.*?id\s*=\s*\?', re.IGNORECASE),
            'missing_index': re.compile(r'WHERE\s+(\w+)\s*[=<>]', re.IGNORECASE)
        }
        
    def analyze_complexity(self, function_code: str) -> ComplexityResult:
        """
        Analyze the time and space complexity of a function
        """
        try:
            tree = ast.parse(function_code)
            analyzer = ComplexityAnalyzer()
            analyzer.visit(tree)
            
            # Determine time complexity
            time_complexity = self._calculate_time_complexity(analyzer)
            
            # Determine space complexity
            space_complexity = self._calculate_space_complexity(analyzer)
            
            # Identify dominant operations
            dominant_ops = self._get_dominant_operations(analyzer)
            
            # Calculate confidence based on code patterns
            confidence = self._calculate_confidence(analyzer, len(function_code))
            
            return ComplexityResult(
                time_complexity=time_complexity,
                space_complexity=space_complexity,
                dominant_operations=dominant_ops,
                nested_loops=analyzer.max_loop_depth,
                recursive_calls=analyzer.recursive_calls,
                confidence=confidence
            )
            
        except Exception as e:
            self.logger.error(f"Complexity analysis failed: {e}")
            return ComplexityResult(
                time_complexity="Unknown",
                space_complexity="Unknown",
                dominant_operations=[],
                nested_loops=0,
                recursive_calls=False,
                confidence=0.0
            )
            
    def _calculate_time_complexity(self, analyzer: ComplexityAnalyzer) -> str:
        """Calculate Big O time complexity"""
        if analyzer.recursive_calls:
            if analyzer.operations.get('loop', 0) > 0:
                return "O(n * recursive_depth)"
            return "O(recursive_depth)"
            
        loop_depth = analyzer.max_loop_depth
        has_sort = analyzer.operations.get('sort', 0) > 0
        
        if loop_depth == 0:
            if has_sort:
                return "O(n log n)"
            return "O(1)"
        elif loop_depth == 1:
            if has_sort:
                return "O(n² log n)"
            return "O(n)"
        elif loop_depth == 2:
            return "O(n²)"
        elif loop_depth == 3:
            return "O(n³)"
        else:
            return f"O(n^{loop_depth})"
            
    def _calculate_space_complexity(self, analyzer: ComplexityAnalyzer) -> str:
        """Calculate Big O space complexity"""
        lists = analyzer.space_usage.get('list', 0)
        dicts = analyzer.space_usage.get('dict', 0)
        
        if analyzer.recursive_calls:
            return "O(recursive_depth)"
            
        if lists + dicts == 0:
            return "O(1)"
        elif analyzer.max_loop_depth > 0:
            return "O(n)"
        else:
            return "O(1)"
            
    def _get_dominant_operations(self, analyzer: ComplexityAnalyzer) -> List[str]:
        """Identify the most significant operations"""
        ops = []
        
        if analyzer.operations.get('sort', 0) > 0:
            ops.append("Sorting")
        if analyzer.max_loop_depth >= 2:
            ops.append(f"Nested loops (depth: {analyzer.max_loop_depth})")
        if analyzer.recursive_calls:
            ops.append("Recursion")
        if analyzer.operations.get('comprehension', 0) > 2:
            ops.append("Multiple comprehensions")
            
        return ops
        
    def _calculate_confidence(self, analyzer: ComplexityAnalyzer, code_length: int) -> float:
        """Calculate confidence score for complexity analysis"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence for clear patterns
        if analyzer.max_loop_depth > 0:
            confidence += 0.2
        if analyzer.operations.get('sort', 0) > 0:
            confidence += 0.1
        if code_length > 100:
            confidence += 0.1
        if analyzer.recursive_calls:
            confidence += 0.1
            
        return min(confidence, 1.0)
        
    def profile_execution(self, code: str, globals_dict: Optional[Dict] = None) -> PerformanceMetrics:
        """
        Profile code execution with detailed metrics
        """
        if globals_dict is None:
            globals_dict = {}
            
        # Start memory tracking
        tracemalloc.start()
        initial_memory = tracemalloc.get_traced_memory()[0]
        
        # Start CPU tracking
        process = psutil.Process()
        initial_cpu = process.cpu_percent(interval=0.1)
        
        # Profile execution
        self.profiler.enable()
        start_time = time.perf_counter()
        
        try:
            exec(code, globals_dict)
        except Exception as e:
            self.logger.error(f"Execution failed: {e}")
            
        end_time = time.perf_counter()
        self.profiler.disable()
        
        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Get CPU usage
        final_cpu = process.cpu_percent(interval=0.1)
        
        # Analyze profiling results
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s).sort_stats('cumulative')
        ps.print_stats()
        
        # Extract function calls and hotspots
        function_calls = {}
        hotspots = []
        
        for line in s.getvalue().split('\n'):
            if line.strip() and not line.startswith(' '):
                parts = line.split()
                if len(parts) >= 6 and parts[0].isdigit():
                    calls = int(parts[0])
                    time_spent = float(parts[2])
                    func_name = parts[-1]
                    function_calls[func_name] = calls
                    if time_spent > 0.01:  # More than 10ms
                        hotspots.append((func_name, time_spent))
                        
        # Sort hotspots by time
        hotspots.sort(key=lambda x: x[1], reverse=True)
        
        return PerformanceMetrics(
            execution_time=end_time - start_time,
            memory_usage={
                'allocated': current - initial_memory,
                'peak': peak - initial_memory,
                'total': peak
            },
            cpu_usage=(final_cpu - initial_cpu) / 100.0,
            function_calls=function_calls,
            hotspots=hotspots[:10]  # Top 10 hotspots
        )
        
    def suggest_optimizations(self, code: str, metrics: Optional[PerformanceMetrics] = None) -> List[OptimizationSuggestion]:
        """
        Generate optimization suggestions based on code analysis
        """
        suggestions = []
        
        try:
            tree = ast.parse(code)
            
            # Analyze for common inefficiencies
            suggestions.extend(self._check_loop_inefficiencies(tree))
            suggestions.extend(self._check_data_structure_usage(tree))
            suggestions.extend(self._check_function_calls(tree))
            suggestions.extend(self._check_memory_patterns(tree))
            
            # Add metrics-based suggestions if available
            if metrics:
                suggestions.extend(self._analyze_metrics(metrics))
                
            # Check for parallelization opportunities
            suggestions.extend(self._check_parallelization(tree))
            
            # Sort by severity
            suggestions.sort(key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}[x.severity])
            
        except Exception as e:
            self.logger.error(f"Optimization analysis failed: {e}")
            
        return suggestions
        
    def _check_loop_inefficiencies(self, tree: ast.AST) -> List[OptimizationSuggestion]:
        """Check for inefficient loop patterns"""
        suggestions = []
        
        for node in ast.walk(tree):
            # Check for list append in loops
            if isinstance(node, ast.For):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                        if child.func.attr == 'append':
                            suggestions.append(OptimizationSuggestion(
                                category="Loop Efficiency",
                                severity="medium",
                                description="Consider using list comprehension instead of append in loop",
                                code_location=f"Line {node.lineno}",
                                expected_improvement="2-3x faster for large lists",
                                implementation_hint="result = [process(item) for item in items]"
                            ))
                            
            # Check for nested loops over same data
            if isinstance(node, ast.For) and any(isinstance(child, ast.For) for child in ast.walk(node)):
                suggestions.append(OptimizationSuggestion(
                    category="Algorithm",
                    severity="high",
                    description="Nested loops detected - consider using better algorithm",
                    code_location=f"Line {node.lineno}",
                    expected_improvement="O(n²) to O(n) or O(n log n)",
                    implementation_hint="Use sets/dicts for lookups or sorting-based approach"
                ))
                
        return suggestions
        
    def _check_data_structure_usage(self, tree: ast.AST) -> List[OptimizationSuggestion]:
        """Check for inefficient data structure usage"""
        suggestions = []
        
        for node in ast.walk(tree):
            # Check for list membership tests
            if isinstance(node, ast.Compare) and any(isinstance(op, ast.In) for op in node.ops):
                if isinstance(node.comparators[0], ast.Name):
                    suggestions.append(OptimizationSuggestion(
                        category="Data Structure",
                        severity="medium",
                        description="Consider using set for membership testing",
                        code_location=f"Line {node.lineno}",
                        expected_improvement="O(n) to O(1) lookup time",
                        implementation_hint="Use set() instead of list for 'in' operations"
                    ))
                    
        return suggestions
        
    def _check_function_calls(self, tree: ast.AST) -> List[OptimizationSuggestion]:
        """Check for expensive function calls"""
        suggestions = []
        call_counts = defaultdict(int)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                call_counts[node.func.id] += 1
                
        # Check for repeated expensive operations
        expensive_ops = ['sorted', 'len', 'sum', 'max', 'min']
        for op in expensive_ops:
            if call_counts[op] > 3:
                suggestions.append(OptimizationSuggestion(
                    category="Caching",
                    severity="medium",
                    description=f"Multiple calls to {op}() detected - consider caching result",
                    code_location=None,
                    expected_improvement="Eliminate redundant computations",
                    implementation_hint=f"{op}_result = {op}(data); # reuse {op}_result"
                ))
                
        return suggestions
        
    def _check_memory_patterns(self, tree: ast.AST) -> List[OptimizationSuggestion]:
        """Check for memory-inefficient patterns"""
        suggestions = []
        
        # Check for large intermediate lists
        list_comps = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ListComp))
        if list_comps > 3:
            suggestions.append(OptimizationSuggestion(
                category="Memory",
                severity="medium",
                description="Multiple list comprehensions - consider generators",
                code_location=None,
                expected_improvement="Reduce memory usage",
                implementation_hint="Use (expr for item in items) instead of [expr for item in items]"
            ))
            
        return suggestions
        
    def _check_parallelization(self, tree: ast.AST) -> List[OptimizationSuggestion]:
        """Check for parallelization opportunities"""
        suggestions = []
        
        # Look for independent loop iterations
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # Simple heuristic: if loop body doesn't modify shared state
                has_side_effects = any(
                    isinstance(child, (ast.Assign, ast.AugAssign))
                    for child in ast.walk(node)
                    if child != node
                )
                
                if not has_side_effects:
                    suggestions.append(OptimizationSuggestion(
                        category="Parallelization",
                        severity="medium",
                        description="Loop appears parallelizable",
                        code_location=f"Line {node.lineno}",
                        expected_improvement=f"Up to {multiprocessing.cpu_count()}x speedup",
                        implementation_hint="Use multiprocessing.Pool or concurrent.futures"
                    ))
                    
        return suggestions
        
    def _analyze_metrics(self, metrics: PerformanceMetrics) -> List[OptimizationSuggestion]:
        """Generate suggestions based on performance metrics"""
        suggestions = []
        
        # Check execution time
        if metrics.execution_time > 1.0:
            suggestions.append(OptimizationSuggestion(
                category="Performance",
                severity="high",
                description=f"Slow execution time: {metrics.execution_time:.2f}s",
                code_location=None,
                expected_improvement="Target sub-second execution",
                implementation_hint="Profile code to find bottlenecks"
            ))
            
        # Check memory usage
        if metrics.memory_usage['peak'] > 100 * 1024 * 1024:  # 100MB
            suggestions.append(OptimizationSuggestion(
                category="Memory",
                severity="high",
                description=f"High memory usage: {metrics.memory_usage['peak'] / 1024 / 1024:.1f}MB",
                code_location=None,
                expected_improvement="Reduce memory footprint",
                implementation_hint="Use generators or process data in chunks"
            ))
            
        # Check hotspots
        if metrics.hotspots:
            top_hotspot = metrics.hotspots[0]
            if top_hotspot[1] > 0.5:  # More than 500ms
                suggestions.append(OptimizationSuggestion(
                    category="Hotspot",
                    severity="critical",
                    description=f"Performance hotspot: {top_hotspot[0]} ({top_hotspot[1]:.2f}s)",
                    code_location=top_hotspot[0],
                    expected_improvement="Optimize or cache this function",
                    implementation_hint="Consider algorithmic improvements or memoization"
                ))
                
        return suggestions
        
    def compare_implementations(self, implementations: Dict[str, str], test_data: Optional[Any] = None) -> Dict[str, Any]:
        """
        Compare multiple implementations for performance
        """
        results = {}
        
        for name, code in implementations.items():
            # Analyze complexity
            complexity = self.analyze_complexity(code)
            
            # Profile execution if test data provided
            if test_data:
                metrics = self.profile_execution(code, {'test_data': test_data})
            else:
                metrics = None
                
            # Get optimization suggestions
            suggestions = self.suggest_optimizations(code, metrics)
            
            results[name] = {
                'complexity': complexity,
                'metrics': metrics,
                'suggestions': suggestions,
                'score': self._calculate_performance_score(complexity, metrics)
            }
            
        # Rank implementations
        ranked = sorted(results.items(), key=lambda x: x[1]['score'], reverse=True)
        
        return {
            'implementations': results,
            'ranking': [name for name, _ in ranked],
            'best': ranked[0][0] if ranked else None,
            'comparison': self._generate_comparison_summary(results)
        }
        
    def _calculate_performance_score(self, complexity: ComplexityResult, metrics: Optional[PerformanceMetrics]) -> float:
        """Calculate overall performance score"""
        score = 100.0
        
        # Penalize based on complexity
        complexity_penalties = {
            'O(1)': 0,
            'O(log n)': 5,
            'O(n)': 10,
            'O(n log n)': 20,
            'O(n²)': 40,
            'O(n³)': 60
        }
        
        for comp, penalty in complexity_penalties.items():
            if comp in complexity.time_complexity:
                score -= penalty
                break
                
        # Penalize nested loops
        score -= complexity.nested_loops * 10
        
        # Penalize based on metrics if available
        if metrics:
            if metrics.execution_time > 1.0:
                score -= min(20, metrics.execution_time * 10)
            if metrics.memory_usage['peak'] > 50 * 1024 * 1024:
                score -= 10
                
        return max(0, score)
        
    def _generate_comparison_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of implementation comparison"""
        summary = {
            'complexity_comparison': {},
            'performance_comparison': {},
            'recommendations': []
        }
        
        # Compare complexities
        for name, data in results.items():
            summary['complexity_comparison'][name] = {
                'time': data['complexity'].time_complexity,
                'space': data['complexity'].space_complexity
            }
            
        # Compare performance if metrics available
        for name, data in results.items():
            if data['metrics']:
                summary['performance_comparison'][name] = {
                    'execution_time': data['metrics'].execution_time,
                    'memory_usage': data['metrics'].memory_usage['peak']
                }
                
        # Generate recommendations
        best_score = max(data['score'] for data in results.values())
        for name, data in results.items():
            if data['score'] == best_score:
                summary['recommendations'].append(f"Use {name} for best overall performance")
            elif data['score'] > best_score * 0.8:
                summary['recommendations'].append(f"{name} is a viable alternative")
                
        return summary
        
    def analyze_database_queries(self, queries: List[str]) -> List[QueryAnalysis]:
        """
        Analyze database queries for performance issues
        """
        analyses = []
        query_cache = defaultdict(list)
        
        for query in queries:
            analysis = self._analyze_single_query(query)
            analyses.append(analysis)
            
            # Track for N+1 detection
            if analysis.query_type == 'SELECT':
                pattern = re.sub(r'\d+', '?', query)
                query_cache[pattern].append(query)
                
        # Detect N+1 queries
        for pattern, similar_queries in query_cache.items():
            if len(similar_queries) > 5:
                for analysis in analyses:
                    if any(q in similar_queries for q in queries):
                        analysis.is_n_plus_one = True
                        analysis.optimization_suggestions.append(
                            "N+1 query pattern detected - use JOIN or batch loading"
                        )
                        
        return analyses
        
    def _analyze_single_query(self, query: str) -> QueryAnalysis:
        """Analyze a single database query"""
        query_upper = query.upper()
        
        # Determine query type
        query_type = 'UNKNOWN'
        for qtype in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']:
            if query_upper.startswith(qtype):
                query_type = qtype
                break
                
        # Extract table names
        table_names = []
        if match := self.query_patterns['select'].search(query):
            table_names.append(match.group(1))
        for match in self.query_patterns['join'].finditer(query):
            table_names.append(match.group(1))
            
        # Check for joins
        has_joins = 'JOIN' in query_upper
        
        # Find potentially missing indexes
        missing_indexes = []
        if match := self.query_patterns['where'].search(query):
            where_clause = match.group(1)
            for column_match in self.query_patterns['missing_index'].finditer(where_clause):
                column = column_match.group(1)
                if column not in ['id', 'created_at', 'updated_at']:
                    missing_indexes.append(column)
                    
        # Generate optimization suggestions
        suggestions = []
        if missing_indexes:
            suggestions.append(f"Consider indexes on: {', '.join(missing_indexes)}")
        if has_joins and len(table_names) > 3:
            suggestions.append("Complex join - consider denormalization or materialized view")
        if 'SELECT *' in query_upper:
            suggestions.append("Avoid SELECT * - specify needed columns")
        if not any(keyword in query_upper for keyword in ['LIMIT', 'TOP']):
            suggestions.append("Consider adding LIMIT clause for large result sets")
            
        return QueryAnalysis(
            query_type=query_type,
            table_names=table_names,
            has_joins=has_joins,
            missing_indexes=missing_indexes,
            is_n_plus_one=False,  # Will be updated in batch analysis
            optimization_suggestions=suggestions
        )
        
    def identify_caching_opportunities(self, code: str, execution_traces: Optional[List[Dict]] = None) -> List[OptimizationSuggestion]:
        """
        Identify where caching would improve performance
        """
        suggestions = []
        
        try:
            tree = ast.parse(code)
            
            # Find repeated function calls
            call_locations = defaultdict(list)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    call_locations[node.func.id].append(node.lineno)
                    
            # Suggest caching for repeated calls
            for func_name, locations in call_locations.items():
                if len(locations) > 2:
                    suggestions.append(OptimizationSuggestion(
                        category="Caching",
                        severity="medium",
                        description=f"Function '{func_name}' called {len(locations)} times",
                        code_location=f"Lines: {locations}",
                        expected_improvement="Eliminate redundant computations",
                        implementation_hint=f"Use @functools.lru_cache or memoization for {func_name}"
                    ))
                    
            # Check for expensive operations in loops
            for node in ast.walk(tree):
                if isinstance(node, ast.For):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                            if child.func.id in ['sorted', 'max', 'min', 'sum']:
                                suggestions.append(OptimizationSuggestion(
                                    category="Caching",
                                    severity="high",
                                    description=f"Expensive operation '{child.func.id}' in loop",
                                    code_location=f"Line {child.lineno}",
                                    expected_improvement="Move computation outside loop",
                                    implementation_hint="Pre-compute before loop or cache result"
                                ))
                                
            # Analyze execution traces if provided
            if execution_traces:
                repeated_computations = self._analyze_execution_traces(execution_traces)
                for computation, count in repeated_computations.items():
                    if count > 10:
                        suggestions.append(OptimizationSuggestion(
                            category="Caching",
                            severity="high",
                            description=f"Computation repeated {count} times: {computation}",
                            code_location=None,
                            expected_improvement=f"Up to {count}x speedup",
                            implementation_hint="Implement result caching or memoization"
                        ))
                        
        except Exception as e:
            self.logger.error(f"Caching analysis failed: {e}")
            
        return suggestions
        
    def _analyze_execution_traces(self, traces: List[Dict]) -> Dict[str, int]:
        """Analyze execution traces for repeated computations"""
        computation_counts = defaultdict(int)
        
        for trace in traces:
            # Simple heuristic: count repeated function calls with same args
            key = f"{trace.get('function', 'unknown')}({trace.get('args', '')})"
            computation_counts[key] += 1
            
        return {k: v for k, v in computation_counts.items() if v > 1}
        
    def generate_performance_report(self, code: str, test_data: Optional[Any] = None) -> Dict[str, Any]:
        """
        Generate comprehensive performance analysis report
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'code_analysis': {},
            'performance_metrics': {},
            'optimization_suggestions': [],
            'summary': {}
        }
        
        # Analyze complexity
        complexity = self.analyze_complexity(code)
        report['code_analysis']['complexity'] = {
            'time': complexity.time_complexity,
            'space': complexity.space_complexity,
            'nested_loops': complexity.nested_loops,
            'recursive': complexity.recursive_calls,
            'confidence': complexity.confidence
        }
        
        # Profile execution if test data provided
        if test_data:
            metrics = self.profile_execution(code, {'test_data': test_data})
            report['performance_metrics'] = {
                'execution_time': f"{metrics.execution_time:.4f}s",
                'memory_usage': {
                    'allocated': f"{metrics.memory_usage['allocated'] / 1024:.2f}KB",
                    'peak': f"{metrics.memory_usage['peak'] / 1024:.2f}KB"
                },
                'cpu_usage': f"{metrics.cpu_usage * 100:.1f}%",
                'hotspots': [
                    {'function': name, 'time': f"{time:.4f}s"}
                    for name, time in metrics.hotspots[:5]
                ]
            }
        else:
            metrics = None
            
        # Get optimization suggestions
        suggestions = self.suggest_optimizations(code, metrics)
        caching_suggestions = self.identify_caching_opportunities(code)
        all_suggestions = suggestions + caching_suggestions
        
        # Group suggestions by category
        by_category = defaultdict(list)
        for suggestion in all_suggestions:
            by_category[suggestion.category].append({
                'severity': suggestion.severity,
                'description': suggestion.description,
                'location': suggestion.code_location,
                'improvement': suggestion.expected_improvement,
                'hint': suggestion.implementation_hint
            })
            
        report['optimization_suggestions'] = dict(by_category)
        
        # Generate summary
        report['summary'] = self._generate_report_summary(
            complexity, metrics, all_suggestions
        )
        
        return report
        
    def _generate_report_summary(self, complexity: ComplexityResult, 
                                metrics: Optional[PerformanceMetrics],
                                suggestions: List[OptimizationSuggestion]) -> Dict[str, Any]:
        """Generate executive summary of performance analysis"""
        summary = {
            'overall_rating': 'Good',
            'key_findings': [],
            'critical_issues': [],
            'quick_wins': []
        }
        
        # Rate based on complexity
        if 'n³' in complexity.time_complexity or 'n^4' in complexity.time_complexity:
            summary['overall_rating'] = 'Poor'
            summary['critical_issues'].append("Very high algorithmic complexity")
        elif 'n²' in complexity.time_complexity:
            summary['overall_rating'] = 'Fair'
            summary['key_findings'].append("Quadratic time complexity detected")
            
        # Add metrics-based findings
        if metrics:
            if metrics.execution_time > 1.0:
                summary['critical_issues'].append(f"Slow execution: {metrics.execution_time:.2f}s")
            if metrics.memory_usage['peak'] > 100 * 1024 * 1024:
                summary['critical_issues'].append(f"High memory usage: {metrics.memory_usage['peak'] / 1024 / 1024:.1f}MB")
                
        # Categorize suggestions
        for suggestion in suggestions:
            if suggestion.severity == 'critical':
                summary['critical_issues'].append(suggestion.description)
            elif suggestion.severity == 'low' and suggestion.expected_improvement:
                summary['quick_wins'].append({
                    'action': suggestion.description,
                    'benefit': suggestion.expected_improvement
                })
                
        # Overall rating adjustment
        if len(summary['critical_issues']) > 2:
            summary['overall_rating'] = 'Poor'
        elif len(summary['critical_issues']) > 0:
            summary['overall_rating'] = 'Fair'
            
        return summary
        
    def detect_memory_leaks(self, code: str, iterations: int = 10) -> Dict[str, Any]:
        """
        Detect potential memory leaks by running code multiple times
        """
        memory_usage = []
        
        for i in range(iterations):
            tracemalloc.start()
            
            try:
                exec(code)
            except Exception as e:
                self.logger.error(f"Execution failed in iteration {i}: {e}")
                
            current, peak = tracemalloc.get_traced_memory()
            memory_usage.append(current)
            tracemalloc.stop()
            
            # Small delay between iterations
            time.sleep(0.1)
            
        # Analyze memory trend
        memory_array = np.array(memory_usage)
        slope = np.polyfit(range(len(memory_array)), memory_array, 1)[0]
        
        # Detect leak if memory consistently increases
        has_leak = slope > 1024  # More than 1KB per iteration
        
        return {
            'has_leak': has_leak,
            'memory_trend': {
                'initial': memory_usage[0],
                'final': memory_usage[-1],
                'average_increase': slope,
                'measurements': memory_usage
            },
            'severity': 'high' if slope > 10240 else 'medium' if slope > 1024 else 'low',
            'recommendation': 'Check for unclosed resources or growing data structures' if has_leak else 'No memory leak detected'
        }
        
    def suggest_parallel_processing(self, code: str) -> List[OptimizationSuggestion]:
        """
        Identify opportunities for parallel processing
        """
        suggestions = []
        
        try:
            tree = ast.parse(code)
            
            # Look for map operations
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id == 'map':
                        suggestions.append(OptimizationSuggestion(
                            category="Parallelization",
                            severity="medium",
                            description="map() operation can be parallelized",
                            code_location=f"Line {node.lineno}",
                            expected_improvement=f"Up to {multiprocessing.cpu_count()}x speedup",
                            implementation_hint="Use multiprocessing.Pool().map() or concurrent.futures"
                        ))
                        
            # Look for independent list comprehensions
            list_comps = [node for node in ast.walk(tree) if isinstance(node, ast.ListComp)]
            if len(list_comps) > 2:
                suggestions.append(OptimizationSuggestion(
                    category="Parallelization",
                    severity="low",
                    description="Multiple list comprehensions could be parallelized",
                    code_location=None,
                    expected_improvement="Process multiple comprehensions concurrently",
                    implementation_hint="Use asyncio.gather() or ThreadPoolExecutor"
                ))
                
            # Look for file I/O operations
            io_operations = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in ['open', 'read', 'write']:
                        io_operations.append(node)
                        
            if len(io_operations) > 3:
                suggestions.append(OptimizationSuggestion(
                    category="Parallelization",
                    severity="medium",
                    description="Multiple I/O operations detected",
                    code_location=None,
                    expected_improvement="Concurrent I/O can improve throughput",
                    implementation_hint="Use asyncio for concurrent file operations"
                ))
                
        except Exception as e:
            self.logger.error(f"Parallel processing analysis failed: {e}")
            
        return suggestions
    
    def execute_specialty(self, **kwargs) -> Dict[str, Any]:
        """Execute performance analysis specialty - Enhanced MANUS integration"""
        action = kwargs.get('action', 'analyze')
        code = kwargs.get('code', '')
        directory = kwargs.get('directory', '.')
        
        try:
            if action == 'analyze':
                # Comprehensive performance analysis
                if not code:
                    return {"success": False, "error": "No code provided for analysis"}
                
                report = self.generate_performance_report(code)
                return {
                    "success": True,
                    "action": "performance_analysis",
                    "report": report,
                    "summary": {
                        "overall_rating": report['summary']['overall_rating'],
                        "critical_issues": len(report['summary']['critical_issues']),
                        "quick_wins": len(report['summary']['quick_wins']),
                        "complexity": report['code_analysis']['complexity']
                    }
                }
            
            elif action == 'complexity':
                # Just complexity analysis
                if not code:
                    return {"success": False, "error": "No code provided for complexity analysis"}
                
                complexity = self.analyze_complexity(code)
                return {
                    "success": True,
                    "action": "complexity_analysis",
                    "complexity": {
                        "time": complexity.time_complexity,
                        "space": complexity.space_complexity,
                        "nested_loops": complexity.nested_loops,
                        "recursive": complexity.recursive_calls,
                        "confidence": complexity.confidence
                    },
                    "summary": f"Time: {complexity.time_complexity}, Space: {complexity.space_complexity}"
                }
            
            elif action == 'optimize':
                # Get optimization suggestions
                if not code:
                    return {"success": False, "error": "No code provided for optimization"}
                
                suggestions = self.suggest_optimizations(code)
                caching_suggestions = self.identify_caching_opportunities(code)
                parallel_suggestions = self.suggest_parallel_processing(code)
                
                all_suggestions = suggestions + caching_suggestions + parallel_suggestions
                
                # Group by severity
                by_severity = {'critical': [], 'high': [], 'medium': [], 'low': []}
                for suggestion in all_suggestions:
                    by_severity[suggestion.severity].append({
                        'category': suggestion.category,
                        'description': suggestion.description,
                        'improvement': suggestion.expected_improvement,
                        'hint': suggestion.implementation_hint
                    })
                
                return {
                    "success": True,
                    "action": "optimization_suggestions",
                    "suggestions": by_severity,
                    "summary": f"Found {len(all_suggestions)} optimization opportunities"
                }
            
            elif action == 'compare':
                # Compare multiple implementations
                implementations = kwargs.get('implementations', {})
                if not implementations:
                    return {"success": False, "error": "No implementations provided for comparison"}
                
                comparison = self.compare_implementations(implementations)
                return {
                    "success": True,
                    "action": "implementation_comparison",
                    "comparison": comparison,
                    "summary": f"Best implementation: {comparison['best']}"
                }
            
            elif action == 'memory_leak':
                # Check for memory leaks
                if not code:
                    return {"success": False, "error": "No code provided for memory leak detection"}
                
                leak_analysis = self.detect_memory_leaks(code)
                return {
                    "success": True,
                    "action": "memory_leak_detection",
                    "analysis": leak_analysis,
                    "summary": f"Memory leak: {'Yes' if leak_analysis['has_leak'] else 'No'}"
                }
            
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            self.logger.error(f"Performance analyzer specialty execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": action
            }


# Example usage and testing
if __name__ == "__main__":
    analyzer = PerformanceAnalyzerOmnipotent()
    
    # Example 1: Analyze complexity
    code1 = """
def find_duplicates(arr):
    duplicates = []
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] == arr[j] and arr[i] not in duplicates:
                duplicates.append(arr[i])
    return duplicates
"""
    
    complexity = analyzer.analyze_complexity(code1)
    print("Complexity Analysis:")
    print(f"Time: {complexity.time_complexity}")
    print(f"Space: {complexity.space_complexity}")
    print(f"Nested loops: {complexity.nested_loops}")
    
    # Example 2: Compare implementations
    implementations = {
        "nested_loop": code1,
        "optimized": """
def find_duplicates(arr):
    seen = set()
    duplicates = set()
    for item in arr:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return list(duplicates)
"""
    }
    
    comparison = analyzer.compare_implementations(implementations)
    print(f"\nBest implementation: {comparison['best']}")
    
    # Example 3: Generate performance report
    report = analyzer.generate_performance_report(code1)
    print(f"\nPerformance Report Summary:")
    print(f"Rating: {report['summary']['overall_rating']}")
    print(f"Critical issues: {len(report['summary']['critical_issues'])}")