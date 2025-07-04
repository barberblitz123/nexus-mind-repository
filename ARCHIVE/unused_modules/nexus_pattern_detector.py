#!/usr/bin/env python3
"""
NEXUS Pattern Detector - Advanced pattern detection system
AST-based analysis, ML-powered pattern recognition, and refactoring suggestions
"""

import ast
import os
import re
import json
import hashlib
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor
import threading
import logging

# AST and code analysis
import astroid
from rope.base.project import Project
from rope.refactor.extract import ExtractMethod, ExtractVariable
from rope.refactor.rename import Rename
from rope.refactor.inline import InlineVariable
import autopep8
import black
import isort

# ML and pattern matching
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.decomposition import PCA
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel

# Sequence mining
from prefixspan import PrefixSpan
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

# Graph analysis
import networkx as nx
from pyvis.network import Network

# Monitoring
from prometheus_client import Counter, Histogram, Gauge
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
patterns_detected = Counter('nexus_patterns_detected_total', 'Total patterns detected')
pattern_detection_time = Histogram('nexus_pattern_detection_seconds', 'Pattern detection time')
active_patterns = Gauge('nexus_active_patterns', 'Number of active patterns')
refactoring_suggestions = Counter('nexus_refactoring_suggestions_total', 'Total refactoring suggestions')


@dataclass
class PatternConfig:
    """Pattern detection configuration"""
    min_similarity_threshold: float = 0.85
    min_pattern_length: int = 3
    max_pattern_complexity: int = 100
    clustering_eps: float = 0.3
    min_cluster_size: int = 2
    sequence_mining_support: float = 0.1
    enable_ml_detection: bool = True
    enable_ast_analysis: bool = True
    enable_security_patterns: bool = True
    cache_embeddings: bool = True
    pattern_language: str = "DSL"  # Domain Specific Language for patterns
    max_cache_size: int = 10000


@dataclass
class CodePattern:
    """Detected code pattern"""
    pattern_id: str
    pattern_type: str
    occurrences: List[Dict[str, Any]]
    confidence: float
    complexity: int
    description: str
    ast_signature: Optional[str] = None
    embeddings: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RefactoringOpportunity:
    """Refactoring suggestion"""
    opportunity_id: str
    pattern_id: str
    refactoring_type: str
    location: Dict[str, Any]
    impact_score: float
    effort_estimate: int  # in minutes
    description: str
    code_before: str
    code_after: str
    benefits: List[str]
    risks: List[str]


class PatternDSL:
    """Domain Specific Language for pattern definition"""
    
    def __init__(self):
        self.patterns = {}
        self.compiled_patterns = {}
    
    def define_pattern(self, name: str, pattern: str):
        """Define a custom pattern using DSL"""
        # Pattern DSL syntax:
        # $var = variable name
        # @type = type constraint
        # * = zero or more
        # + = one or more
        # ? = optional
        # {...} = code block
        
        self.patterns[name] = pattern
        self.compiled_patterns[name] = self._compile_pattern(pattern)
    
    def _compile_pattern(self, pattern: str) -> Any:
        """Compile DSL pattern to AST matcher"""
        # Simple pattern compiler (extend as needed)
        tokens = self._tokenize_pattern(pattern)
        return self._build_matcher(tokens)
    
    def _tokenize_pattern(self, pattern: str) -> List[str]:
        """Tokenize pattern string"""
        # Basic tokenizer
        tokens = re.findall(r'\$\w+|\@\w+|\*|\+|\?|\{[^}]+\}|\w+', pattern)
        return tokens
    
    def _build_matcher(self, tokens: List[str]) -> Any:
        """Build AST matcher from tokens"""
        # Build matcher logic (simplified)
        class PatternMatcher:
            def __init__(self, tokens):
                self.tokens = tokens
            
            def match(self, node):
                # Implement matching logic
                return True  # Simplified
        
        return PatternMatcher(tokens)
    
    def match(self, name: str, code: str) -> bool:
        """Check if code matches pattern"""
        if name not in self.compiled_patterns:
            return False
        
        try:
            tree = ast.parse(code)
            matcher = self.compiled_patterns[name]
            return matcher.match(tree)
        except:
            return False


class ASTPatternAnalyzer:
    """AST-based pattern analysis"""
    
    def __init__(self):
        self.pattern_cache = {}
        self.ast_signatures = {}
    
    def analyze_ast(self, code: str) -> Dict[str, Any]:
        """Analyze code AST for patterns"""
        try:
            tree = ast.parse(code)
            
            # Extract various patterns
            patterns = {
                'functions': self._extract_functions(tree),
                'classes': self._extract_classes(tree),
                'loops': self._extract_loops(tree),
                'conditionals': self._extract_conditionals(tree),
                'error_handling': self._extract_error_handling(tree),
                'decorators': self._extract_decorators(tree),
                'comprehensions': self._extract_comprehensions(tree),
                'imports': self._extract_imports(tree)
            }
            
            # Calculate complexity metrics
            complexity = self._calculate_complexity(tree)
            
            # Generate AST signature
            signature = self._generate_ast_signature(tree)
            
            return {
                'patterns': patterns,
                'complexity': complexity,
                'signature': signature,
                'metrics': self._calculate_metrics(tree)
            }
            
        except Exception as e:
            logger.error(f"AST analysis error: {e}")
            return {}
    
    def _extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract function patterns"""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'args': len(node.args.args),
                    'decorators': [d.id for d in node.decorator_list if isinstance(d, ast.Name)],
                    'returns': node.returns is not None,
                    'docstring': ast.get_docstring(node) is not None,
                    'lines': node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0,
                    'complexity': self._calculate_cyclomatic_complexity(node)
                })
        
        return functions
    
    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract class patterns"""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                classes.append({
                    'name': node.name,
                    'bases': [b.id for b in node.bases if isinstance(b, ast.Name)],
                    'decorators': [d.id for d in node.decorator_list if isinstance(d, ast.Name)],
                    'methods': methods,
                    'has_init': '__init__' in methods,
                    'lines': node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
                })
        
        return classes
    
    def _extract_loops(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract loop patterns"""
        loops = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                loop_type = 'for' if isinstance(node, ast.For) else 'while'
                loops.append({
                    'type': loop_type,
                    'nested': self._is_nested_loop(node),
                    'has_break': any(isinstance(n, ast.Break) for n in ast.walk(node)),
                    'has_continue': any(isinstance(n, ast.Continue) for n in ast.walk(node)),
                    'complexity': len(list(ast.walk(node)))
                })
        
        return loops
    
    def _extract_conditionals(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract conditional patterns"""
        conditionals = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                conditionals.append({
                    'has_else': node.orelse != [],
                    'elif_count': sum(1 for n in node.orelse if isinstance(n, ast.If)),
                    'complexity': self._calculate_conditional_complexity(node),
                    'nested_depth': self._calculate_nesting_depth(node)
                })
        
        return conditionals
    
    def _extract_error_handling(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract error handling patterns"""
        error_patterns = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                error_patterns.append({
                    'except_count': len(node.handlers),
                    'has_else': node.orelse != [],
                    'has_finally': node.finalbody != [],
                    'caught_exceptions': [
                        h.type.id if isinstance(h.type, ast.Name) else 'generic'
                        for h in node.handlers
                    ],
                    'is_bare_except': any(h.type is None for h in node.handlers)
                })
        
        return error_patterns
    
    def _extract_decorators(self, tree: ast.AST) -> List[str]:
        """Extract decorator usage"""
        decorators = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        decorators.append(decorator.id)
                    elif isinstance(decorator, ast.Attribute):
                        decorators.append(f"{decorator.value.id}.{decorator.attr}")
        
        return decorators
    
    def _extract_comprehensions(self, tree: ast.AST) -> Dict[str, int]:
        """Extract comprehension patterns"""
        return {
            'list_comp': sum(1 for n in ast.walk(tree) if isinstance(n, ast.ListComp)),
            'dict_comp': sum(1 for n in ast.walk(tree) if isinstance(n, ast.DictComp)),
            'set_comp': sum(1 for n in ast.walk(tree) if isinstance(n, ast.SetComp)),
            'generator': sum(1 for n in ast.walk(tree) if isinstance(n, ast.GeneratorExp))
        }
    
    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract import patterns"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'module': alias.name,
                        'alias': alias.asname,
                        'type': 'import'
                    })
            elif isinstance(node, ast.ImportFrom):
                imports.append({
                    'module': node.module,
                    'names': [alias.name for alias in node.names],
                    'level': node.level,
                    'type': 'from_import'
                })
        
        return imports
    
    def _calculate_complexity(self, tree: ast.AST) -> Dict[str, Any]:
        """Calculate code complexity metrics"""
        return {
            'cyclomatic': self._calculate_cyclomatic_complexity(tree),
            'cognitive': self._calculate_cognitive_complexity(tree),
            'halstead': self._calculate_halstead_metrics(tree),
            'maintainability_index': self._calculate_maintainability_index(tree)
        }
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _calculate_cognitive_complexity(self, node: ast.AST) -> int:
        """Calculate cognitive complexity"""
        # Simplified cognitive complexity
        complexity = 0
        nesting_level = 0
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1 + nesting_level
                nesting_level += 1
            elif isinstance(child, ast.BoolOp):
                complexity += 1
        
        return complexity
    
    def _calculate_halstead_metrics(self, node: ast.AST) -> Dict[str, float]:
        """Calculate Halstead complexity metrics"""
        operators = []
        operands = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.operator):
                operators.append(type(child).__name__)
            elif isinstance(child, (ast.Name, ast.Constant)):
                operands.append(str(child))
        
        n1 = len(set(operators))  # unique operators
        n2 = len(set(operands))   # unique operands
        N1 = len(operators)       # total operators
        N2 = len(operands)        # total operands
        
        # Halstead metrics
        n = n1 + n2  # vocabulary
        N = N1 + N2  # length
        V = N * np.log2(n) if n > 0 else 0  # volume
        D = (n1 / 2) * (N2 / n2) if n2 > 0 else 0  # difficulty
        E = D * V  # effort
        
        return {
            'vocabulary': n,
            'length': N,
            'volume': V,
            'difficulty': D,
            'effort': E
        }
    
    def _calculate_maintainability_index(self, node: ast.AST) -> float:
        """Calculate maintainability index"""
        halstead = self._calculate_halstead_metrics(node)
        cyclomatic = self._calculate_cyclomatic_complexity(node)
        lines = len(node.body) if hasattr(node, 'body') else 1
        
        # Maintainability Index formula
        mi = 171 - 5.2 * np.log(halstead['volume']) - 0.23 * cyclomatic - 16.2 * np.log(lines)
        return max(0, min(100, mi))
    
    def _is_nested_loop(self, node: ast.AST) -> bool:
        """Check if loop is nested"""
        for child in ast.walk(node):
            if child != node and isinstance(child, (ast.For, ast.While)):
                return True
        return False
    
    def _calculate_nesting_depth(self, node: ast.AST, depth: int = 0) -> int:
        """Calculate maximum nesting depth"""
        max_depth = depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With)):
                child_depth = self._calculate_nesting_depth(child, depth + 1)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def _calculate_conditional_complexity(self, node: ast.If) -> int:
        """Calculate conditional complexity"""
        complexity = 1
        
        # Count boolean operators in condition
        for child in ast.walk(node.test):
            if isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        # Add complexity for elif/else
        if node.orelse:
            complexity += 1
        
        return complexity
    
    def _generate_ast_signature(self, tree: ast.AST) -> str:
        """Generate unique AST signature"""
        # Create a simplified AST representation
        sig_parts = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                sig_parts.append(f"{type(node).__name__}:{node.name}")
            elif isinstance(node, (ast.For, ast.While, ast.If)):
                sig_parts.append(type(node).__name__)
        
        signature = "|".join(sig_parts)
        return hashlib.md5(signature.encode()).hexdigest()[:16]
    
    def _calculate_metrics(self, tree: ast.AST) -> Dict[str, Any]:
        """Calculate various code metrics"""
        return {
            'loc': len(ast.unparse(tree).split('\n')),
            'functions': sum(1 for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)),
            'classes': sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef)),
            'imports': sum(1 for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))),
            'comments': 0,  # Would need source code to count comments
            'docstrings': sum(1 for n in ast.walk(tree) if ast.get_docstring(n))
        }


class MLPatternDetector:
    """Machine learning based pattern detection"""
    
    def __init__(self, config: PatternConfig):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Code embedding model
        self.tokenizer = AutoTokenizer.from_pretrained('microsoft/codebert-base')
        self.model = AutoModel.from_pretrained('microsoft/codebert-base').to(self.device)
        
        # Clustering models
        self.dbscan = DBSCAN(eps=config.clustering_eps, min_samples=config.min_cluster_size)
        self.hierarchical = AgglomerativeClustering(n_clusters=None, distance_threshold=0.5)
        
        # Vectorizers
        self.tfidf = TfidfVectorizer(max_features=1000, ngram_range=(1, 3))
        
        # Caches
        self.embedding_cache = {}
        self.similarity_cache = {}
    
    def detect_similar_patterns(self, code_snippets: List[str]) -> List[CodePattern]:
        """Detect similar code patterns using ML"""
        patterns = []
        
        # Generate embeddings
        embeddings = self._generate_embeddings(code_snippets)
        
        # Cluster similar code
        clusters = self._cluster_embeddings(embeddings)
        
        # Extract patterns from clusters
        for cluster_id, indices in clusters.items():
            if len(indices) >= self.config.min_cluster_size:
                pattern = self._extract_pattern_from_cluster(
                    [code_snippets[i] for i in indices],
                    embeddings[indices]
                )
                patterns.append(pattern)
        
        return patterns
    
    def _generate_embeddings(self, code_snippets: List[str]) -> np.ndarray:
        """Generate code embeddings using CodeBERT"""
        embeddings = []
        
        for code in code_snippets:
            # Check cache
            code_hash = hashlib.md5(code.encode()).hexdigest()
            if code_hash in self.embedding_cache:
                embeddings.append(self.embedding_cache[code_hash])
                continue
            
            # Generate embedding
            inputs = self.tokenizer(
                code,
                return_tensors='pt',
                truncation=True,
                padding='max_length',
                max_length=512
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
            
            embeddings.append(embedding[0])
            
            # Cache embedding
            if self.config.cache_embeddings:
                self.embedding_cache[code_hash] = embedding[0]
        
        return np.array(embeddings)
    
    def _cluster_embeddings(self, embeddings: np.ndarray) -> Dict[int, List[int]]:
        """Cluster embeddings to find patterns"""
        # Normalize embeddings
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # DBSCAN clustering
        labels = self.dbscan.fit_predict(embeddings)
        
        # Group by cluster
        clusters = defaultdict(list)
        for idx, label in enumerate(labels):
            if label != -1:  # Ignore noise
                clusters[label].append(idx)
        
        return clusters
    
    def _extract_pattern_from_cluster(self, code_snippets: List[str], embeddings: np.ndarray) -> CodePattern:
        """Extract pattern from code cluster"""
        # Calculate centroid
        centroid = embeddings.mean(axis=0)
        
        # Find most representative code
        distances = np.linalg.norm(embeddings - centroid, axis=1)
        representative_idx = np.argmin(distances)
        
        # Analyze pattern
        ast_analyzer = ASTPatternAnalyzer()
        ast_analysis = ast_analyzer.analyze_ast(code_snippets[representative_idx])
        
        pattern = CodePattern(
            pattern_id=hashlib.md5(str(code_snippets).encode()).hexdigest()[:8],
            pattern_type=self._infer_pattern_type(ast_analysis),
            occurrences=[{'code': code, 'index': i} for i, code in enumerate(code_snippets)],
            confidence=self._calculate_pattern_confidence(embeddings),
            complexity=ast_analysis.get('complexity', {}).get('cyclomatic', 0),
            description=self._generate_pattern_description(code_snippets),
            ast_signature=ast_analysis.get('signature'),
            embeddings=centroid,
            metadata={
                'cluster_size': len(code_snippets),
                'avg_distance': float(distances.mean()),
                'ast_analysis': ast_analysis
            }
        )
        
        return pattern
    
    def _infer_pattern_type(self, ast_analysis: Dict[str, Any]) -> str:
        """Infer pattern type from AST analysis"""
        patterns = ast_analysis.get('patterns', {})
        
        # Simple heuristic for pattern type
        if patterns.get('error_handling'):
            return 'error_handling'
        elif patterns.get('loops') and any(l['nested'] for l in patterns['loops']):
            return 'nested_loop'
        elif patterns.get('functions') and any(f['decorators'] for f in patterns['functions']):
            return 'decorated_function'
        elif patterns.get('classes'):
            return 'class_pattern'
        else:
            return 'generic'
    
    def _calculate_pattern_confidence(self, embeddings: np.ndarray) -> float:
        """Calculate pattern confidence based on embedding similarity"""
        # Calculate pairwise similarities
        similarities = cosine_similarity(embeddings)
        
        # Average similarity (excluding diagonal)
        n = len(embeddings)
        if n <= 1:
            return 1.0
        
        avg_similarity = (similarities.sum() - n) / (n * (n - 1))
        return float(avg_similarity)
    
    def _generate_pattern_description(self, code_snippets: List[str]) -> str:
        """Generate pattern description"""
        # Simple description based on common tokens
        all_tokens = []
        for code in code_snippets[:5]:  # Sample first 5
            tokens = re.findall(r'\w+', code)
            all_tokens.extend(tokens)
        
        # Find most common tokens
        token_counts = Counter(all_tokens)
        common_tokens = [token for token, _ in token_counts.most_common(5)]
        
        return f"Pattern with common elements: {', '.join(common_tokens)}"


class SequencePatternMiner:
    """Mine sequential patterns in code workflows"""
    
    def __init__(self, min_support: float = 0.1):
        self.min_support = min_support
        self.patterns = []
    
    def mine_workflow_patterns(self, sequences: List[List[str]]) -> List[Dict[str, Any]]:
        """Mine frequent sequential patterns"""
        # Use PrefixSpan algorithm
        ps = PrefixSpan(sequences)
        ps.minlen = 2
        ps.maxlen = 10
        
        frequent_patterns = ps.frequent(int(len(sequences) * self.min_support))
        
        patterns = []
        for support, pattern in frequent_patterns:
            patterns.append({
                'pattern': pattern,
                'support': support / len(sequences),
                'confidence': self._calculate_confidence(pattern, sequences),
                'lift': self._calculate_lift(pattern, sequences)
            })
        
        return sorted(patterns, key=lambda p: p['support'], reverse=True)
    
    def _calculate_confidence(self, pattern: List[str], sequences: List[List[str]]) -> float:
        """Calculate pattern confidence"""
        if len(pattern) < 2:
            return 1.0
        
        antecedent = pattern[:-1]
        consequent = pattern[-1]
        
        antecedent_count = sum(1 for seq in sequences if self._contains_subsequence(seq, antecedent))
        pattern_count = sum(1 for seq in sequences if self._contains_subsequence(seq, pattern))
        
        return pattern_count / antecedent_count if antecedent_count > 0 else 0
    
    def _calculate_lift(self, pattern: List[str], sequences: List[List[str]]) -> float:
        """Calculate pattern lift"""
        if len(pattern) < 2:
            return 1.0
        
        pattern_support = sum(1 for seq in sequences if self._contains_subsequence(seq, pattern)) / len(sequences)
        
        # Calculate individual supports
        individual_supports = []
        for item in pattern:
            support = sum(1 for seq in sequences if item in seq) / len(sequences)
            individual_supports.append(support)
        
        expected_support = np.prod(individual_supports)
        
        return pattern_support / expected_support if expected_support > 0 else 1.0
    
    def _contains_subsequence(self, sequence: List[str], subsequence: List[str]) -> bool:
        """Check if sequence contains subsequence"""
        it = iter(sequence)
        return all(item in it for item in subsequence)


class NexusPatternDetector:
    """Main pattern detection system"""
    
    def __init__(self, config: Optional[PatternConfig] = None):
        self.config = config or PatternConfig()
        
        # Components
        self.ast_analyzer = ASTPatternAnalyzer()
        self.ml_detector = MLPatternDetector(self.config)
        self.sequence_miner = SequencePatternMiner(self.config.sequence_mining_support)
        self.pattern_dsl = PatternDSL()
        
        # Pattern storage
        self.detected_patterns: Dict[str, CodePattern] = {}
        self.refactoring_opportunities: List[RefactoringOpportunity] = []
        
        # Performance tracking
        self.pattern_graph = nx.DiGraph()
        self.execution_sequences = []
        
        # Threading
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Define common patterns
        self._define_common_patterns()
    
    def _define_common_patterns(self):
        """Define common code patterns using DSL"""
        # Define some common patterns
        self.pattern_dsl.define_pattern(
            'singleton',
            'class $name { @instance = None; def __new__($cls) { ... } }'
        )
        
        self.pattern_dsl.define_pattern(
            'factory',
            'class $Factory { def create_$product(@type) { ... } }'
        )
        
        self.pattern_dsl.define_pattern(
            'null_check',
            'if $var is None { $action }'
        )
        
        self.pattern_dsl.define_pattern(
            'resource_management',
            'with $resource as $var { $body }'
        )
    
    @pattern_detection_time.time()
    def detect_patterns(self, codebase_path: str) -> Dict[str, Any]:
        """Detect all patterns in codebase"""
        patterns_detected.inc()
        
        results = {
            'code_patterns': [],
            'workflow_patterns': [],
            'refactoring_opportunities': [],
            'security_issues': [],
            'performance_issues': [],
            'best_practice_violations': []
        }
        
        try:
            # Collect code files
            code_files = self._collect_code_files(codebase_path)
            
            # AST-based pattern detection
            if self.config.enable_ast_analysis:
                ast_patterns = self._detect_ast_patterns(code_files)
                results['code_patterns'].extend(ast_patterns)
            
            # ML-based similarity detection
            if self.config.enable_ml_detection:
                ml_patterns = self._detect_ml_patterns(code_files)
                results['code_patterns'].extend(ml_patterns)
            
            # Workflow pattern mining
            workflow_patterns = self._mine_workflow_patterns()
            results['workflow_patterns'] = workflow_patterns
            
            # Security pattern detection
            if self.config.enable_security_patterns:
                security_issues = self._detect_security_patterns(code_files)
                results['security_issues'] = security_issues
            
            # Performance pattern detection
            performance_issues = self._detect_performance_patterns(code_files)
            results['performance_issues'] = performance_issues
            
            # Best practice violations
            violations = self._detect_best_practice_violations(code_files)
            results['best_practice_violations'] = violations
            
            # Generate refactoring suggestions
            refactoring_opps = self._generate_refactoring_suggestions(results['code_patterns'])
            results['refactoring_opportunities'] = refactoring_opps
            
            # Update metrics
            active_patterns.set(len(results['code_patterns']))
            
            return results
            
        except Exception as e:
            logger.error(f"Pattern detection error: {e}")
            return results
    
    def _collect_code_files(self, path: str) -> List[Dict[str, str]]:
        """Collect all code files from path"""
        code_files = []
        
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(('.py', '.js', '.java', '.cpp', '.go')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        code_files.append({
                            'path': file_path,
                            'content': content,
                            'language': self._detect_language(file)
                        })
                    except Exception as e:
                        logger.warning(f"Failed to read {file_path}: {e}")
        
        return code_files
    
    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.go': 'go'
        }
        
        ext = os.path.splitext(filename)[1]
        return ext_map.get(ext, 'unknown')
    
    def _detect_ast_patterns(self, code_files: List[Dict[str, str]]) -> List[CodePattern]:
        """Detect patterns using AST analysis"""
        patterns = []
        pattern_groups = defaultdict(list)
        
        for file_info in code_files:
            if file_info['language'] == 'python':
                analysis = self.ast_analyzer.analyze_ast(file_info['content'])
                
                # Group by AST signature
                signature = analysis.get('signature')
                if signature:
                    pattern_groups[signature].append({
                        'file': file_info['path'],
                        'analysis': analysis,
                        'content': file_info['content']
                    })
        
        # Create patterns from groups
        for signature, occurrences in pattern_groups.items():
            if len(occurrences) >= self.config.min_cluster_size:
                pattern = CodePattern(
                    pattern_id=signature[:8],
                    pattern_type='ast_pattern',
                    occurrences=occurrences,
                    confidence=1.0,
                    complexity=occurrences[0]['analysis']['complexity']['cyclomatic'],
                    description=f"AST pattern found in {len(occurrences)} files",
                    ast_signature=signature
                )
                patterns.append(pattern)
        
        return patterns
    
    def _detect_ml_patterns(self, code_files: List[Dict[str, str]]) -> List[CodePattern]:
        """Detect patterns using ML"""
        # Extract code snippets
        code_snippets = []
        snippet_info = []
        
        for file_info in code_files:
            # Extract functions/methods as snippets
            if file_info['language'] == 'python':
                snippets = self._extract_code_snippets(file_info['content'])
                for snippet in snippets:
                    code_snippets.append(snippet['code'])
                    snippet_info.append({
                        'file': file_info['path'],
                        'snippet': snippet
                    })
        
        # Detect similar patterns
        if len(code_snippets) >= self.config.min_cluster_size:
            patterns = self.ml_detector.detect_similar_patterns(code_snippets)
            
            # Enhance patterns with file information
            for pattern in patterns:
                for i, occurrence in enumerate(pattern.occurrences):
                    occurrence['file'] = snippet_info[occurrence['index']]['file']
                    occurrence['snippet_info'] = snippet_info[occurrence['index']]['snippet']
            
            return patterns
        
        return []
    
    def _extract_code_snippets(self, code: str) -> List[Dict[str, Any]]:
        """Extract code snippets (functions, classes) from code"""
        snippets = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    snippet_code = ast.unparse(node)
                    snippets.append({
                        'type': type(node).__name__,
                        'name': node.name,
                        'code': snippet_code,
                        'line': node.lineno
                    })
        except:
            pass
        
        return snippets
    
    def _mine_workflow_patterns(self) -> List[Dict[str, Any]]:
        """Mine workflow patterns from execution sequences"""
        if not self.execution_sequences:
            return []
        
        return self.sequence_miner.mine_workflow_patterns(self.execution_sequences)
    
    def _detect_security_patterns(self, code_files: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Detect security vulnerability patterns"""
        security_patterns = []
        
        # Common security patterns
        patterns = {
            'sql_injection': r'(execute|query)\s*\(\s*["\'].*%[s|d].*["\'].*%',
            'hardcoded_password': r'(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']',
            'eval_usage': r'eval\s*\(',
            'pickle_load': r'pickle\.load\s*\(',
            'weak_random': r'random\.\w+\s*\(',
            'no_input_validation': r'request\.(GET|POST)\[.*\](?!.*validate)',
            'open_redirect': r'redirect\(request\.',
            'path_traversal': r'\.\./',
            'command_injection': r'(os\.system|subprocess\.call)\s*\([^)]*\+',
            'xxe_vulnerability': r'XMLParser.*resolve_entities\s*=\s*True'
        }
        
        for file_info in code_files:
            content = file_info['content']
            
            for pattern_name, pattern_regex in patterns.items():
                matches = re.finditer(pattern_regex, content, re.IGNORECASE)
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    
                    security_patterns.append({
                        'type': pattern_name,
                        'file': file_info['path'],
                        'line': line_num,
                        'match': match.group(),
                        'severity': self._get_security_severity(pattern_name),
                        'recommendation': self._get_security_recommendation(pattern_name)
                    })
        
        return security_patterns
    
    def _detect_performance_patterns(self, code_files: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Detect performance anti-patterns"""
        performance_issues = []
        
        for file_info in code_files:
            if file_info['language'] == 'python':
                try:
                    tree = ast.parse(file_info['content'])
                    
                    # Detect nested loops
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.For, ast.While)):
                            if self.ast_analyzer._is_nested_loop(node):
                                complexity = self.ast_analyzer._calculate_cyclomatic_complexity(node)
                                if complexity > 10:
                                    performance_issues.append({
                                        'type': 'complex_nested_loop',
                                        'file': file_info['path'],
                                        'line': node.lineno,
                                        'complexity': complexity,
                                        'impact': 'high',
                                        'suggestion': 'Consider refactoring to reduce nesting'
                                    })
                    
                    # Detect repeated operations
                    function_calls = defaultdict(list)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                            function_calls[node.func.id].append(node.lineno)
                    
                    for func_name, lines in function_calls.items():
                        if len(lines) > 5 and max(lines) - min(lines) < 20:
                            performance_issues.append({
                                'type': 'repeated_function_calls',
                                'file': file_info['path'],
                                'function': func_name,
                                'occurrences': len(lines),
                                'lines': lines[:5],  # First 5 occurrences
                                'impact': 'medium',
                                'suggestion': f'Consider caching results of {func_name}()'
                            })
                
                except:
                    pass
        
        return performance_issues
    
    def _detect_best_practice_violations(self, code_files: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Detect violations of coding best practices"""
        violations = []
        
        for file_info in code_files:
            if file_info['language'] == 'python':
                try:
                    tree = ast.parse(file_info['content'])
                    
                    for node in ast.walk(tree):
                        # Check for missing docstrings
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                            if not ast.get_docstring(node):
                                violations.append({
                                    'type': 'missing_docstring',
                                    'file': file_info['path'],
                                    'line': node.lineno,
                                    'entity': node.name,
                                    'severity': 'low',
                                    'fix': 'Add descriptive docstring'
                                })
                        
                        # Check for bare except
                        if isinstance(node, ast.ExceptHandler) and node.type is None:
                            violations.append({
                                'type': 'bare_except',
                                'file': file_info['path'],
                                'line': node.lineno,
                                'severity': 'medium',
                                'fix': 'Specify exception type'
                            })
                        
                        # Check for mutable default arguments
                        if isinstance(node, ast.FunctionDef):
                            for default in node.args.defaults:
                                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                                    violations.append({
                                        'type': 'mutable_default_argument',
                                        'file': file_info['path'],
                                        'line': node.lineno,
                                        'function': node.name,
                                        'severity': 'high',
                                        'fix': 'Use None as default and create mutable in function'
                                    })
                
                except:
                    pass
        
        return violations
    
    def _generate_refactoring_suggestions(self, patterns: List[CodePattern]) -> List[RefactoringOpportunity]:
        """Generate refactoring suggestions from patterns"""
        suggestions = []
        
        for pattern in patterns:
            if len(pattern.occurrences) >= 3:  # Pattern appears 3+ times
                # Suggest extract method
                suggestion = RefactoringOpportunity(
                    opportunity_id=hashlib.md5(f"{pattern.pattern_id}_extract".encode()).hexdigest()[:8],
                    pattern_id=pattern.pattern_id,
                    refactoring_type='extract_method',
                    location={'files': [occ.get('file') for occ in pattern.occurrences[:3]]},
                    impact_score=len(pattern.occurrences) * pattern.complexity / 10,
                    effort_estimate=15 * len(pattern.occurrences),  # 15 min per occurrence
                    description=f"Extract repeated pattern into reusable method",
                    code_before=pattern.occurrences[0].get('code', '')[:200] + '...',
                    code_after=f"def extracted_pattern(...):\n    # Extracted logic\n    pass",
                    benefits=[
                        f"Eliminate {len(pattern.occurrences)} duplications",
                        "Improve maintainability",
                        "Reduce code complexity"
                    ],
                    risks=[
                        "May require parameter adjustments",
                        "Could affect performance if not inlined"
                    ]
                )
                suggestions.append(suggestion)
                refactoring_suggestions.inc()
        
        return suggestions
    
    def _get_security_severity(self, pattern_type: str) -> str:
        """Get security issue severity"""
        severity_map = {
            'sql_injection': 'critical',
            'command_injection': 'critical',
            'eval_usage': 'high',
            'hardcoded_password': 'high',
            'pickle_load': 'medium',
            'weak_random': 'medium',
            'no_input_validation': 'high',
            'open_redirect': 'medium',
            'path_traversal': 'high',
            'xxe_vulnerability': 'high'
        }
        return severity_map.get(pattern_type, 'medium')
    
    def _get_security_recommendation(self, pattern_type: str) -> str:
        """Get security recommendation"""
        recommendations = {
            'sql_injection': 'Use parameterized queries or prepared statements',
            'command_injection': 'Use subprocess with list arguments, avoid shell=True',
            'eval_usage': 'Use ast.literal_eval() or avoid eval entirely',
            'hardcoded_password': 'Use environment variables or secure key management',
            'pickle_load': 'Use JSON or other safe serialization formats',
            'weak_random': 'Use secrets module for cryptographic randomness',
            'no_input_validation': 'Validate and sanitize all user inputs',
            'open_redirect': 'Validate redirect URLs against whitelist',
            'path_traversal': 'Sanitize file paths and use os.path.join()',
            'xxe_vulnerability': 'Disable XML external entity processing'
        }
        return recommendations.get(pattern_type, 'Review and fix security issue')
    
    def record_execution_sequence(self, sequence: List[str]):
        """Record execution sequence for pattern mining"""
        self.execution_sequences.append(sequence)
        
        # Limit stored sequences
        if len(self.execution_sequences) > 1000:
            self.execution_sequences.pop(0)
    
    def visualize_patterns(self, output_file: str = 'patterns.html'):
        """Visualize detected patterns as graph"""
        net = Network(height='750px', width='100%', directed=True)
        
        # Add pattern nodes
        for pattern_id, pattern in self.detected_patterns.items():
            size = len(pattern.occurrences) * 5
            net.add_node(
                pattern_id,
                label=pattern.pattern_type,
                size=size,
                title=pattern.description,
                color='#FF6B6B' if pattern.complexity > 10 else '#4ECDC4'
            )
        
        # Add relationships between patterns
        for pattern_id, pattern in self.detected_patterns.items():
            # Find related patterns (simplified)
            for other_id, other_pattern in self.detected_patterns.items():
                if pattern_id != other_id:
                    # Check if patterns appear in same files
                    pattern_files = {occ.get('file') for occ in pattern.occurrences}
                    other_files = {occ.get('file') for occ in other_pattern.occurrences}
                    
                    overlap = len(pattern_files & other_files)
                    if overlap > 0:
                        net.add_edge(pattern_id, other_id, value=overlap)
        
        net.save_graph(output_file)
        logger.info(f"Pattern visualization saved to {output_file}")
    
    def export_patterns(self, format: str = 'json') -> str:
        """Export detected patterns"""
        data = {
            'patterns': [
                {
                    'id': p.pattern_id,
                    'type': p.pattern_type,
                    'occurrences': len(p.occurrences),
                    'confidence': p.confidence,
                    'complexity': p.complexity,
                    'description': p.description,
                    'files': list({occ.get('file') for occ in p.occurrences})
                }
                for p in self.detected_patterns.values()
            ],
            'refactoring_opportunities': [
                {
                    'id': r.opportunity_id,
                    'type': r.refactoring_type,
                    'impact': r.impact_score,
                    'effort': r.effort_estimate,
                    'description': r.description
                }
                for r in self.refactoring_opportunities
            ]
        }
        
        if format == 'json':
            return json.dumps(data, indent=2)
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=['id', 'type', 'occurrences', 'confidence', 'complexity'])
            writer.writeheader()
            
            for pattern in data['patterns']:
                writer.writerow({
                    'id': pattern['id'],
                    'type': pattern['type'],
                    'occurrences': pattern['occurrences'],
                    'confidence': pattern['confidence'],
                    'complexity': pattern['complexity']
                })
            
            return output.getvalue()
        
        return str(data)


# Example usage
if __name__ == "__main__":
    # Initialize pattern detector
    config = PatternConfig(
        min_similarity_threshold=0.8,
        min_cluster_size=2,
        enable_ml_detection=True,
        enable_security_patterns=True
    )
    
    detector = NexusPatternDetector(config)
    
    # Detect patterns in current directory
    results = detector.detect_patterns(".")
    
    print(f"Detected {len(results['code_patterns'])} code patterns")
    print(f"Found {len(results['security_issues'])} security issues")
    print(f"Found {len(results['performance_issues'])} performance issues")
    print(f"Generated {len(results['refactoring_opportunities'])} refactoring suggestions")
    
    # Visualize patterns
    detector.visualize_patterns()
    
    # Export results
    print("\nPattern Summary:")
    print(detector.export_patterns('json'))