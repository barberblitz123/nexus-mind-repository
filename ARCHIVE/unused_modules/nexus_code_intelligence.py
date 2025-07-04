#!/usr/bin/env python3
"""
NEXUS Code Intelligence ML
Machine learning for code understanding, bug prediction, and refactoring suggestions
"""

import os
import ast
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict, Counter
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

# ML frameworks
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor

# Code analysis
import astroid
from pylint import epylint as lint
import radon.complexity as radon_complexity
import radon.metrics as radon_metrics
from pyflakes.api import check as pyflakes_check
import autopep8
import black

# Code embeddings
from transformers import (
    RobertaTokenizer, RobertaModel, RobertaForSequenceClassification,
    CodeBERTModel, GPT2Model, GPT2Tokenizer
)
import code2vec
from gensim.models import Word2Vec
import networkx as nx

# AST processing
import tree_sitter
from tree_sitter import Language, Parser
import pygments
from pygments.lexers import get_lexer_by_name
from pygments.token import Token

# Model explanation
import shap
import lime
from captum.attr import IntegratedGradients

# API learning
from typing import Pattern
import re
from fuzzywuzzy import fuzz
import difflib

# Monitoring
from prometheus_client import Counter, Histogram, Gauge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
code_embeddings_generated = Counter('nexus_code_embeddings_total', 'Total code embeddings generated')
bugs_predicted = Counter('nexus_bugs_predicted_total', 'Total bugs predicted')
refactorings_suggested = Counter('nexus_refactorings_suggested_total', 'Total refactorings suggested')
api_patterns_learned = Counter('nexus_api_patterns_learned_total', 'API patterns learned')

@dataclass
class CodeFeatures:
    """Features extracted from code"""
    ast_features: Dict[str, float]
    complexity_metrics: Dict[str, float]
    code_embeddings: np.ndarray
    token_features: Dict[str, int]
    graph_features: Optional[Dict[str, float]] = None
    api_usage: Optional[List[str]] = None
    
@dataclass
class BugPrediction:
    """Bug prediction result"""
    file_path: str
    line_number: int
    bug_type: str
    confidence: float
    explanation: str
    suggested_fix: Optional[str] = None
    
@dataclass
class RefactoringsuggestionNode:
    """Refactoring suggestion"""
    file_path: str
    start_line: int
    end_line: int
    refactoring_type: str
    description: str
    new_code: str
    impact_score: float
    
@dataclass
class CodeSimilarity:
    """Code similarity result"""
    code1_path: str
    code2_path: str
    similarity_score: float
    similar_components: List[Tuple[str, str]]
    potential_duplication: bool

class ASTFeatureExtractor:
    """Extract features from Abstract Syntax Trees"""
    
    def __init__(self):
        self.feature_visitors = {
            'function_count': self._count_functions,
            'class_count': self._count_classes,
            'loop_count': self._count_loops,
            'conditional_count': self._count_conditionals,
            'max_depth': self._calculate_max_depth,
            'variable_count': self._count_variables,
            'import_count': self._count_imports,
            'comment_ratio': self._calculate_comment_ratio
        }
        
    def extract_features(self, code: str) -> Dict[str, float]:
        """Extract AST-based features from code"""
        try:
            tree = ast.parse(code)
            features = {}
            
            for feature_name, visitor_func in self.feature_visitors.items():
                features[feature_name] = visitor_func(tree, code)
                
            # Additional complex features
            features.update(self._extract_complexity_features(tree))
            features.update(self._extract_pattern_features(tree))
            
            return features
            
        except SyntaxError as e:
            logger.warning(f"Syntax error in code: {e}")
            return {name: 0.0 for name in self.feature_visitors.keys()}
            
    def _count_functions(self, tree: ast.AST, code: str) -> float:
        """Count function definitions"""
        return sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
        
    def _count_classes(self, tree: ast.AST, code: str) -> float:
        """Count class definitions"""
        return sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        
    def _count_loops(self, tree: ast.AST, code: str) -> float:
        """Count loop constructs"""
        loop_types = (ast.For, ast.While)
        return sum(1 for node in ast.walk(tree) if isinstance(node, loop_types))
        
    def _count_conditionals(self, tree: ast.AST, code: str) -> float:
        """Count conditional statements"""
        return sum(1 for node in ast.walk(tree) if isinstance(node, ast.If))
        
    def _calculate_max_depth(self, tree: ast.AST, code: str) -> float:
        """Calculate maximum nesting depth"""
        def get_depth(node, current_depth=0):
            max_child_depth = current_depth
            for child in ast.iter_child_nodes(node):
                child_depth = get_depth(child, current_depth + 1)
                max_child_depth = max(max_child_depth, child_depth)
            return max_child_depth
            
        return float(get_depth(tree))
        
    def _count_variables(self, tree: ast.AST, code: str) -> float:
        """Count variable assignments"""
        return sum(1 for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store))
        
    def _count_imports(self, tree: ast.AST, code: str) -> float:
        """Count import statements"""
        import_types = (ast.Import, ast.ImportFrom)
        return sum(1 for node in ast.walk(tree) if isinstance(node, import_types))
        
    def _calculate_comment_ratio(self, tree: ast.AST, code: str) -> float:
        """Calculate comment to code ratio"""
        lines = code.split('\n')
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        total_lines = len([line for line in lines if line.strip()])
        return comment_lines / max(total_lines, 1)
        
    def _extract_complexity_features(self, tree: ast.AST) -> Dict[str, float]:
        """Extract complexity-related features"""
        features = {}
        
        # Cyclomatic complexity for each function
        complexities = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_cyclomatic_complexity(node)
                complexities.append(complexity)
                
        if complexities:
            features['avg_cyclomatic_complexity'] = np.mean(complexities)
            features['max_cyclomatic_complexity'] = np.max(complexities)
        else:
            features['avg_cyclomatic_complexity'] = 0.0
            features['max_cyclomatic_complexity'] = 0.0
            
        return features
        
    def _calculate_cyclomatic_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
                
        return complexity
        
    def _extract_pattern_features(self, tree: ast.AST) -> Dict[str, float]:
        """Extract code pattern features"""
        features = {}
        
        # Exception handling patterns
        try_blocks = sum(1 for node in ast.walk(tree) if isinstance(node, ast.Try))
        features['exception_handling_ratio'] = try_blocks / max(len(list(ast.walk(tree))), 1)
        
        # List comprehensions vs loops
        list_comps = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ListComp))
        features['list_comprehension_usage'] = float(list_comps)
        
        # Decorator usage
        decorators = sum(len(node.decorator_list) for node in ast.walk(tree) 
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef)))
        features['decorator_count'] = float(decorators)
        
        return features

class Code2VecEmbedder:
    """Generate code embeddings using Code2Vec approach"""
    
    def __init__(self, embedding_size: int = 128):
        self.embedding_size = embedding_size
        self.path_vocab = {}
        self.token_vocab = {}
        self.model = None
        self._build_model()
        
    def _build_model(self):
        """Build Code2Vec neural network"""
        class Code2VecModel(nn.Module):
            def __init__(self, token_vocab_size, path_vocab_size, embedding_size):
                super().__init__()
                self.token_embed = nn.Embedding(token_vocab_size, embedding_size)
                self.path_embed = nn.Embedding(path_vocab_size, embedding_size)
                
                self.attention = nn.Sequential(
                    nn.Linear(embedding_size * 3, embedding_size),
                    nn.Tanh(),
                    nn.Linear(embedding_size, 1)
                )
                
                self.combine = nn.Linear(embedding_size * 3, embedding_size)
                
            def forward(self, contexts):
                # contexts: [(start_token, path, end_token), ...]
                context_vectors = []
                
                for start, path, end in contexts:
                    start_embed = self.token_embed(start)
                    path_embed = self.path_embed(path)
                    end_embed = self.token_embed(end)
                    
                    context = torch.cat([start_embed, path_embed, end_embed], dim=-1)
                    context_vectors.append(self.combine(context))
                    
                # Attention mechanism
                stacked = torch.stack(context_vectors)
                attention_scores = self.attention(torch.cat([s, p, e], dim=-1))
                attention_weights = torch.softmax(attention_scores, dim=0)
                
                # Weighted sum
                code_vector = torch.sum(attention_weights * stacked, dim=0)
                
                return code_vector
                
        # Initialize with dummy sizes, will be updated when vocabulary is built
        self.model = Code2VecModel(10000, 10000, self.embedding_size)
        
    def extract_paths(self, ast_node: ast.AST) -> List[Tuple[str, str, str]]:
        """Extract AST paths for Code2Vec"""
        paths = []
        
        def get_node_token(node):
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Num):
                return str(node.n)
            elif isinstance(node, ast.Str):
                return 'STRING'
            else:
                return node.__class__.__name__
                
        def extract_paths_recursive(node, current_path=[]):
            node_token = get_node_token(node)
            
            # If leaf node, create paths to other leaves
            if not list(ast.iter_child_nodes(node)):
                return [(current_path, node_token)]
                
            child_paths = []
            for child in ast.iter_child_nodes(node):
                child_results = extract_paths_recursive(child, current_path + [node.__class__.__name__])
                child_paths.extend(child_results)
                
            # Create paths between children
            for i in range(len(child_paths)):
                for j in range(i + 1, min(i + 5, len(child_paths))):  # Limit path combinations
                    path1, token1 = child_paths[i]
                    path2, token2 = child_paths[j]
                    
                    # Create path representation
                    path_str = '|'.join(path1 + ['UP'] + path2[::-1])
                    paths.append((token1, path_str, token2))
                    
            return child_paths
            
        try:
            if isinstance(ast_node, str):
                ast_node = ast.parse(ast_node)
            extract_paths_recursive(ast_node)
        except:
            pass
            
        return paths[:200]  # Limit number of paths
        
    def embed_code(self, code: str) -> np.ndarray:
        """Generate code embedding"""
        try:
            paths = self.extract_paths(code)
            
            if not paths:
                return np.zeros(self.embedding_size)
                
            # Convert to tensors (simplified - in practice, use proper vocabulary)
            context_tensors = []
            for start, path, end in paths:
                # Hash tokens to indices
                start_idx = hash(start) % 10000
                path_idx = hash(path) % 10000
                end_idx = hash(end) % 10000
                
                context_tensors.append((
                    torch.tensor(start_idx),
                    torch.tensor(path_idx),
                    torch.tensor(end_idx)
                ))
                
            # Get embedding
            with torch.no_grad():
                embedding = self.model(context_tensors)
                
            code_embeddings_generated.inc()
            return embedding.numpy()
            
        except Exception as e:
            logger.error(f"Error generating code embedding: {e}")
            return np.zeros(self.embedding_size)

class TransformerCodeEmbedder:
    """Generate code embeddings using transformer models"""
    
    def __init__(self, model_name: str = "microsoft/codebert-base"):
        self.tokenizer = RobertaTokenizer.from_pretrained(model_name)
        self.model = RobertaModel.from_pretrained(model_name)
        self.model.eval()
        
    def embed_code(self, code: str, max_length: int = 512) -> np.ndarray:
        """Generate code embedding using CodeBERT"""
        try:
            # Tokenize
            inputs = self.tokenizer(
                code,
                return_tensors="pt",
                max_length=max_length,
                truncation=True,
                padding=True
            )
            
            # Get embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use [CLS] token embedding
                embedding = outputs.last_hidden_state[:, 0, :].squeeze()
                
            code_embeddings_generated.inc()
            return embedding.numpy()
            
        except Exception as e:
            logger.error(f"Error with transformer embedding: {e}")
            return np.zeros(768)  # CodeBERT embedding size

class BugPredictor:
    """Predict bugs in code"""
    
    def __init__(self):
        self.ast_extractor = ASTFeatureExtractor()
        self.code_embedder = Code2VecEmbedder()
        self.model = None
        self.scaler = StandardScaler()
        self.bug_patterns = self._load_bug_patterns()
        
    def _load_bug_patterns(self) -> Dict[str, Pattern]:
        """Load common bug patterns"""
        return {
            'resource_leak': re.compile(r'open\([^)]+\)(?!.*\.close\(\))'),
            'null_reference': re.compile(r'(\w+)\.(\w+)(?!.*if\s+\1)'),
            'infinite_loop': re.compile(r'while\s+True:|while\s+1:'),
            'hardcoded_password': re.compile(r'password\s*=\s*["\'][^"\']+["\']'),
            'sql_injection': re.compile(r'execute\([^?]+%|execute\([^?]+\+'),
            'race_condition': re.compile(r'threading\.Thread.*(?!.*Lock\(\))')
        }
        
    def train(self, training_data: List[Tuple[str, List[BugPrediction]]]):
        """Train bug prediction model"""
        X = []
        y = []
        
        for code, bugs in training_data:
            features = self._extract_features(code)
            X.append(features)
            y.append(1 if bugs else 0)
            
        X = np.array(X)
        y = np.array(y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_scaled, y)
        
        logger.info(f"Bug predictor trained on {len(training_data)} samples")
        
    def predict(self, code: str, file_path: str = "unknown") -> List[BugPrediction]:
        """Predict bugs in code"""
        predictions = []
        
        # Pattern-based detection
        lines = code.split('\n')
        for i, line in enumerate(lines):
            for bug_type, pattern in self.bug_patterns.items():
                if pattern.search(line):
                    predictions.append(BugPrediction(
                        file_path=file_path,
                        line_number=i + 1,
                        bug_type=bug_type,
                        confidence=0.8,
                        explanation=f"Detected {bug_type} pattern",
                        suggested_fix=self._suggest_fix(bug_type, line)
                    ))
                    
        # ML-based detection
        if self.model:
            features = self._extract_features(code)
            X = self.scaler.transform([features])
            
            bug_probability = self.model.predict_proba(X)[0, 1]
            
            if bug_probability > 0.7:
                # Use SHAP to explain
                explainer = shap.TreeExplainer(self.model)
                shap_values = explainer.shap_values(X)
                
                # Find most important features
                feature_importance = np.abs(shap_values[0])
                top_features = np.argsort(feature_importance)[-3:]
                
                explanation = f"High bug probability ({bug_probability:.2f}) due to: "
                explanation += ", ".join([f"feature_{i}" for i in top_features])
                
                predictions.append(BugPrediction(
                    file_path=file_path,
                    line_number=0,
                    bug_type="general_bug_risk",
                    confidence=bug_probability,
                    explanation=explanation
                ))
                
        bugs_predicted.inc(len(predictions))
        return predictions
        
    def _extract_features(self, code: str) -> np.ndarray:
        """Extract features for bug prediction"""
        # AST features
        ast_features = self.ast_extractor.extract_features(code)
        
        # Code embeddings
        embeddings = self.code_embedder.embed_code(code)
        
        # Complexity metrics
        try:
            complexity = radon_complexity.cc_visit(code)
            avg_complexity = np.mean([c.complexity for c in complexity]) if complexity else 0
        except:
            avg_complexity = 0
            
        # Combine features
        features = list(ast_features.values())
        features.append(avg_complexity)
        features.extend(embeddings[:50])  # Use first 50 embedding dimensions
        
        return np.array(features)
        
    def _suggest_fix(self, bug_type: str, line: str) -> str:
        """Suggest fix for detected bug"""
        fixes = {
            'resource_leak': "Add proper resource cleanup: with open(...) as f:",
            'null_reference': "Add null check before accessing attribute",
            'infinite_loop': "Add break condition to loop",
            'hardcoded_password': "Use environment variables or secure credential storage",
            'sql_injection': "Use parameterized queries with ? placeholders",
            'race_condition': "Add proper thread synchronization with locks"
        }
        
        return fixes.get(bug_type, "Review and fix the identified issue")

class PerformancePredictor:
    """Predict code performance characteristics"""
    
    def __init__(self):
        self.ast_extractor = ASTFeatureExtractor()
        self.model = None
        self.scaler = StandardScaler()
        
    def train(self, training_data: List[Tuple[str, Dict[str, float]]]):
        """Train performance prediction model"""
        X = []
        y = []
        
        for code, metrics in training_data:
            features = self._extract_performance_features(code)
            X.append(features)
            # Predict execution time
            y.append(metrics.get('execution_time', 0))
            
        X = np.array(X)
        y = np.array(y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        self.model.fit(X_scaled, y)
        
        logger.info(f"Performance predictor trained on {len(training_data)} samples")
        
    def predict(self, code: str) -> Dict[str, float]:
        """Predict performance metrics"""
        features = self._extract_performance_features(code)
        
        if self.model:
            X = self.scaler.transform([features])
            execution_time = self.model.predict(X)[0]
        else:
            # Simple heuristic
            execution_time = len(code) * 0.001  # Rough estimate
            
        # Additional metrics
        metrics = {
            'predicted_execution_time': execution_time,
            'memory_complexity': self._estimate_memory_complexity(code),
            'time_complexity': self._estimate_time_complexity(code),
            'io_operations': self._count_io_operations(code),
            'database_queries': self._count_database_queries(code)
        }
        
        return metrics
        
    def _extract_performance_features(self, code: str) -> np.ndarray:
        """Extract performance-related features"""
        ast_features = self.ast_extractor.extract_features(code)
        
        # Loop nesting depth
        tree = ast.parse(code)
        max_loop_depth = self._calculate_max_loop_depth(tree)
        
        # Recursive calls
        recursive_calls = self._count_recursive_calls(tree)
        
        # Data structure usage
        list_ops = code.count('.append(') + code.count('.extend(')
        dict_ops = code.count('[') + code.count(']')
        
        features = list(ast_features.values())
        features.extend([max_loop_depth, recursive_calls, list_ops, dict_ops])
        
        return np.array(features)
        
    def _calculate_max_loop_depth(self, tree: ast.AST) -> int:
        """Calculate maximum loop nesting depth"""
        def get_loop_depth(node, current_depth=0):
            max_depth = current_depth
            
            if isinstance(node, (ast.For, ast.While)):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
                
            for child in ast.iter_child_nodes(node):
                child_depth = get_loop_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)
                
            return max_depth
            
        return get_loop_depth(tree)
        
    def _count_recursive_calls(self, tree: ast.AST) -> int:
        """Count potential recursive function calls"""
        function_names = set()
        recursive_count = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_names.add(node.name)
                
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and hasattr(node.func, 'id'):
                if node.func.id in function_names:
                    recursive_count += 1
                    
        return recursive_count
        
    def _estimate_memory_complexity(self, code: str) -> str:
        """Estimate memory complexity"""
        tree = ast.parse(code)
        
        # Look for data structure allocations
        has_nested_loops = self._calculate_max_loop_depth(tree) > 1
        has_recursion = self._count_recursive_calls(tree) > 0
        
        list_allocations = sum(1 for node in ast.walk(tree) 
                              if isinstance(node, ast.List) or isinstance(node, ast.Dict))
        
        if has_recursion:
            return "O(n) stack space due to recursion"
        elif has_nested_loops and list_allocations > 0:
            return "O(n²) possible due to nested data structures"
        elif list_allocations > 0:
            return "O(n) for data structures"
        else:
            return "O(1) constant space"
            
    def _estimate_time_complexity(self, code: str) -> str:
        """Estimate time complexity"""
        tree = ast.parse(code)
        
        loop_depth = self._calculate_max_loop_depth(tree)
        has_recursion = self._count_recursive_calls(tree) > 0
        
        # Look for common patterns
        has_sort = 'sort(' in code or 'sorted(' in code
        
        if has_sort:
            return "O(n log n) due to sorting"
        elif has_recursion:
            if 'fibonacci' in code.lower() or 'factorial' in code.lower():
                return "O(n!) or O(2^n) possible exponential"
            else:
                return "O(n) to O(n²) depending on recursion"
        elif loop_depth >= 3:
            return f"O(n^{loop_depth}) due to {loop_depth} nested loops"
        elif loop_depth == 2:
            return "O(n²) due to nested loops"
        elif loop_depth == 1:
            return "O(n) linear time"
        else:
            return "O(1) constant time"
            
    def _count_io_operations(self, code: str) -> int:
        """Count I/O operations"""
        io_patterns = [
            'open(', 'read(', 'write(', 'print(',
            'input(', 'requests.', 'urllib.'
        ]
        
        return sum(code.count(pattern) for pattern in io_patterns)
        
    def _count_database_queries(self, code: str) -> int:
        """Count database queries"""
        db_patterns = [
            '.execute(', '.query(', 'SELECT ', 'INSERT ',
            'UPDATE ', 'DELETE ', '.find(', '.aggregate('
        ]
        
        return sum(code.count(pattern) for pattern in db_patterns)

class RefactoringEngine:
    """Suggest code refactorings"""
    
    def __init__(self):
        self.ast_extractor = ASTFeatureExtractor()
        self.similarity_threshold = 0.8
        
    def suggest_refactorings(self, code: str, file_path: str = "unknown") -> List[RefactoringsuggestionNode]:
        """Suggest refactorings for code"""
        suggestions = []
        
        try:
            tree = ast.parse(code)
            
            # Check for various refactoring opportunities
            suggestions.extend(self._check_long_functions(tree, code, file_path))
            suggestions.extend(self._check_duplicate_code(tree, code, file_path))
            suggestions.extend(self._check_complex_conditionals(tree, code, file_path))
            suggestions.extend(self._check_code_smells(tree, code, file_path))
            
            refactorings_suggested.inc(len(suggestions))
            
        except SyntaxError:
            logger.warning(f"Syntax error in {file_path}, skipping refactoring analysis")
            
        return suggestions
        
    def _check_long_functions(self, tree: ast.AST, code: str, file_path: str) -> List[RefactoringsuggestionNode]:
        """Check for functions that are too long"""
        suggestions = []
        lines = code.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_lines = lines[node.lineno - 1:node.end_lineno]
                
                if len(func_lines) > 50:  # Function longer than 50 lines
                    suggestions.append(RefactoringsuggestionNode(
                        file_path=file_path,
                        start_line=node.lineno,
                        end_line=node.end_lineno,
                        refactoring_type="extract_function",
                        description=f"Function '{node.name}' is too long ({len(func_lines)} lines). Consider breaking it into smaller functions.",
                        new_code=self._suggest_function_extraction(node, func_lines),
                        impact_score=0.8
                    ))
                    
        return suggestions
        
    def _check_duplicate_code(self, tree: ast.AST, code: str, file_path: str) -> List[RefactoringsuggestionNode]:
        """Check for duplicate code blocks"""
        suggestions = []
        
        # Extract all function bodies
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_code = ast.unparse(node) if hasattr(ast, 'unparse') else str(node)
                functions.append((node, func_code))
                
        # Compare functions for similarity
        for i, (node1, code1) in enumerate(functions):
            for j, (node2, code2) in enumerate(functions[i+1:], i+1):
                similarity = fuzz.ratio(code1, code2) / 100.0
                
                if similarity > self.similarity_threshold:
                    suggestions.append(RefactoringsuggestionNode(
                        file_path=file_path,
                        start_line=node1.lineno,
                        end_line=node2.end_lineno,
                        refactoring_type="extract_common_code",
                        description=f"Functions '{node1.name}' and '{node2.name}' are {similarity:.0%} similar. Consider extracting common code.",
                        new_code=self._suggest_common_extraction(node1, node2),
                        impact_score=similarity
                    ))
                    
        return suggestions
        
    def _check_complex_conditionals(self, tree: ast.AST, code: str, file_path: str) -> List[RefactoringsuggestionNode]:
        """Check for complex conditional statements"""
        suggestions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                # Count conditions
                condition_count = self._count_conditions(node.test)
                
                if condition_count > 3:
                    suggestions.append(RefactoringsuggestionNode(
                        file_path=file_path,
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        refactoring_type="simplify_conditional",
                        description=f"Complex conditional with {condition_count} conditions. Consider extracting to a method or using guard clauses.",
                        new_code=self._suggest_conditional_simplification(node),
                        impact_score=0.6
                    ))
                    
        return suggestions
        
    def _check_code_smells(self, tree: ast.AST, code: str, file_path: str) -> List[RefactoringsuggestionNode]:
        """Check for common code smells"""
        suggestions = []
        
        # God class detection
        class_methods = defaultdict(int)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                method_count = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))
                if method_count > 20:
                    suggestions.append(RefactoringsuggestionNode(
                        file_path=file_path,
                        start_line=node.lineno,
                        end_line=node.end_lineno,
                        refactoring_type="split_class",
                        description=f"Class '{node.name}' has {method_count} methods. Consider splitting into smaller classes.",
                        new_code="# Split into multiple focused classes",
                        impact_score=0.9
                    ))
                    
        # Long parameter lists
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args)
                if param_count > 5:
                    suggestions.append(RefactoringsuggestionNode(
                        file_path=file_path,
                        start_line=node.lineno,
                        end_line=node.lineno,
                        refactoring_type="introduce_parameter_object",
                        description=f"Function '{node.name}' has {param_count} parameters. Consider using a parameter object.",
                        new_code=self._suggest_parameter_object(node),
                        impact_score=0.5
                    ))
                    
        return suggestions
        
    def _count_conditions(self, node: ast.AST) -> int:
        """Count number of conditions in a boolean expression"""
        if isinstance(node, ast.BoolOp):
            return sum(self._count_conditions(value) for value in node.values)
        elif isinstance(node, ast.Compare):
            return 1
        else:
            return 1
            
    def _suggest_function_extraction(self, func_node: ast.FunctionDef, func_lines: List[str]) -> str:
        """Suggest how to extract parts of a long function"""
        return f"""
# Extract logical sections into separate functions:
def {func_node.name}_part1(self, ...):
    # First logical section
    pass

def {func_node.name}_part2(self, ...):
    # Second logical section
    pass

def {func_node.name}(self, ...):
    result1 = self.{func_node.name}_part1(...)
    result2 = self.{func_node.name}_part2(...)
    return combine_results(result1, result2)
"""
        
    def _suggest_common_extraction(self, func1: ast.FunctionDef, func2: ast.FunctionDef) -> str:
        """Suggest extracting common code"""
        return f"""
# Extract common functionality:
def _common_logic(self, ...):
    # Common code from {func1.name} and {func2.name}
    pass

def {func1.name}(self, ...):
    common_result = self._common_logic(...)
    # Specific logic for {func1.name}
    
def {func2.name}(self, ...):
    common_result = self._common_logic(...)
    # Specific logic for {func2.name}
"""
        
    def _suggest_conditional_simplification(self, if_node: ast.If) -> str:
        """Suggest simplifying complex conditionals"""
        return """
# Extract complex condition to method:
def _check_complex_condition(self, ...):
    # Return True if all conditions are met
    return condition1 and condition2 and condition3

# Use guard clauses:
if not precondition:
    return early

# Main logic here
"""
        
    def _suggest_parameter_object(self, func_node: ast.FunctionDef) -> str:
        """Suggest using parameter object"""
        params = [arg.arg for arg in func_node.args.args if arg.arg != 'self']
        
        return f"""
# Create parameter object:
@dataclass
class {func_node.name.capitalize()}Params:
    {chr(10).join(f'    {param}: Any' for param in params)}

def {func_node.name}(self, params: {func_node.name.capitalize()}Params):
    # Use params.{params[0]}, params.{params[1]}, etc.
    pass
"""

class CodeSimilarityDetector:
    """Detect similar code fragments"""
    
    def __init__(self):
        self.embedder = TransformerCodeEmbedder()
        self.ast_extractor = ASTFeatureExtractor()
        
    def find_similar_code(self, code_base: Dict[str, str], 
                         query_code: str,
                         threshold: float = 0.8) -> List[CodeSimilarity]:
        """Find similar code in codebase"""
        similarities = []
        
        # Get query embedding
        query_embedding = self.embedder.embed_code(query_code)
        query_features = self.ast_extractor.extract_features(query_code)
        
        for file_path, code in code_base.items():
            # Get code embedding
            code_embedding = self.embedder.embed_code(code)
            code_features = self.ast_extractor.extract_features(code)
            
            # Calculate similarity
            embedding_sim = self._cosine_similarity(query_embedding, code_embedding)
            feature_sim = self._feature_similarity(query_features, code_features)
            
            combined_similarity = 0.7 * embedding_sim + 0.3 * feature_sim
            
            if combined_similarity > threshold:
                similar_components = self._find_similar_components(query_code, code)
                
                similarities.append(CodeSimilarity(
                    code1_path="query",
                    code2_path=file_path,
                    similarity_score=combined_similarity,
                    similar_components=similar_components,
                    potential_duplication=combined_similarity > 0.9
                ))
                
        return sorted(similarities, key=lambda x: x.similarity_score, reverse=True)
        
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
        
    def _feature_similarity(self, features1: Dict[str, float], 
                          features2: Dict[str, float]) -> float:
        """Calculate similarity based on AST features"""
        common_features = set(features1.keys()) & set(features2.keys())
        
        if not common_features:
            return 0.0
            
        diffs = []
        for feature in common_features:
            val1 = features1[feature]
            val2 = features2[feature]
            
            if val1 + val2 > 0:
                diff = abs(val1 - val2) / (val1 + val2)
                diffs.append(1 - diff)
            else:
                diffs.append(1.0)
                
        return np.mean(diffs)
        
    def _find_similar_components(self, code1: str, code2: str) -> List[Tuple[str, str]]:
        """Find similar components between two code fragments"""
        components = []
        
        try:
            tree1 = ast.parse(code1)
            tree2 = ast.parse(code2)
            
            # Compare functions
            funcs1 = {node.name: ast.unparse(node) if hasattr(ast, 'unparse') else str(node)
                     for node in ast.walk(tree1) if isinstance(node, ast.FunctionDef)}
            funcs2 = {node.name: ast.unparse(node) if hasattr(ast, 'unparse') else str(node)
                     for node in ast.walk(tree2) if isinstance(node, ast.FunctionDef)}
            
            for name1, code1 in funcs1.items():
                for name2, code2 in funcs2.items():
                    similarity = fuzz.ratio(code1, code2) / 100.0
                    if similarity > 0.7:
                        components.append((f"function:{name1}", f"function:{name2}"))
                        
        except:
            pass
            
        return components

class APIUsageLearner:
    """Learn API usage patterns"""
    
    def __init__(self):
        self.api_patterns = defaultdict(list)
        self.api_sequences = defaultdict(list)
        self.api_parameters = defaultdict(dict)
        
    def learn_from_code(self, code_base: Dict[str, str]):
        """Learn API usage patterns from codebase"""
        for file_path, code in code_base.items():
            try:
                tree = ast.parse(code)
                self._extract_api_calls(tree, code)
                self._extract_api_sequences(tree, code)
                self._extract_api_parameters(tree, code)
            except:
                continue
                
        api_patterns_learned.inc(len(self.api_patterns))
        logger.info(f"Learned {len(self.api_patterns)} API patterns")
        
    def suggest_api_usage(self, partial_code: str) -> List[Dict[str, Any]]:
        """Suggest API usage based on partial code"""
        suggestions = []
        
        try:
            tree = ast.parse(partial_code)
            
            # Find incomplete API calls
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and hasattr(node.func, 'attr'):
                    api_name = f"{node.func.value.id if hasattr(node.func.value, 'id') else 'obj'}.{node.func.attr}"
                    
                    if api_name in self.api_patterns:
                        # Suggest common patterns
                        patterns = Counter(self.api_patterns[api_name]).most_common(3)
                        
                        for pattern, count in patterns:
                            suggestions.append({
                                'api': api_name,
                                'pattern': pattern,
                                'confidence': count / len(self.api_patterns[api_name]),
                                'parameters': self.api_parameters.get(api_name, {}),
                                'next_calls': self._get_next_calls(api_name)
                            })
                            
        except:
            pass
            
        return suggestions
        
    def _extract_api_calls(self, tree: ast.AST, code: str):
        """Extract API call patterns"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                api_pattern = self._get_call_pattern(node)
                if api_pattern:
                    self.api_patterns[api_pattern['name']].append(api_pattern['pattern'])
                    
    def _extract_api_sequences(self, tree: ast.AST, code: str):
        """Extract sequences of API calls"""
        # Find sequences of calls within functions
        for func_node in ast.walk(tree):
            if isinstance(func_node, ast.FunctionDef):
                calls = []
                for node in ast.walk(func_node):
                    if isinstance(node, ast.Call) and node != func_node:
                        call_name = self._get_call_name(node)
                        if call_name:
                            calls.append(call_name)
                            
                # Store sequences
                for i in range(len(calls) - 1):
                    self.api_sequences[calls[i]].append(calls[i + 1])
                    
    def _extract_api_parameters(self, tree: ast.AST, code: str):
        """Extract common parameter patterns"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_name = self._get_call_name(node)
                if call_name:
                    # Extract keyword arguments
                    for keyword in node.keywords:
                        if keyword.arg:
                            if keyword.arg not in self.api_parameters[call_name]:
                                self.api_parameters[call_name][keyword.arg] = []
                                
                            # Store value type/pattern
                            value_type = type(keyword.value).__name__
                            self.api_parameters[call_name][keyword.arg].append(value_type)
                            
    def _get_call_pattern(self, node: ast.Call) -> Optional[Dict[str, str]]:
        """Get call pattern from AST node"""
        try:
            if hasattr(node.func, 'attr'):
                name = f"{node.func.value.id if hasattr(node.func.value, 'id') else 'obj'}.{node.func.attr}"
                
                # Create pattern representation
                args = f"args={len(node.args)}"
                kwargs = f"kwargs={','.join(sorted(kw.arg for kw in node.keywords if kw.arg))}"
                pattern = f"{name}({args},{kwargs})"
                
                return {'name': name, 'pattern': pattern}
        except:
            pass
            
        return None
        
    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        """Get call name from AST node"""
        try:
            if hasattr(node.func, 'id'):
                return node.func.id
            elif hasattr(node.func, 'attr'):
                return f"{node.func.value.id if hasattr(node.func.value, 'id') else 'obj'}.{node.func.attr}"
        except:
            pass
            
        return None
        
    def _get_next_calls(self, api_name: str) -> List[str]:
        """Get commonly following API calls"""
        if api_name not in self.api_sequences:
            return []
            
        next_calls = Counter(self.api_sequences[api_name]).most_common(3)
        return [call for call, _ in next_calls]

class NexusCodeIntelligence:
    """Main code intelligence system"""
    
    def __init__(self):
        self.ast_extractor = ASTFeatureExtractor()
        self.code2vec_embedder = Code2VecEmbedder()
        self.transformer_embedder = TransformerCodeEmbedder()
        self.bug_predictor = BugPredictor()
        self.performance_predictor = PerformancePredictor()
        self.refactoring_engine = RefactoringEngine()
        self.similarity_detector = CodeSimilarityDetector()
        self.api_learner = APIUsageLearner()
        
        logger.info("NEXUS Code Intelligence initialized")
        
    async def analyze_code(self, code: str, file_path: str = "unknown") -> Dict[str, Any]:
        """Comprehensive code analysis"""
        analysis = {
            'file_path': file_path,
            'timestamp': datetime.now().isoformat()
        }
        
        # Extract features
        features = CodeFeatures(
            ast_features=self.ast_extractor.extract_features(code),
            complexity_metrics=self._calculate_complexity_metrics(code),
            code_embeddings=self.transformer_embedder.embed_code(code),
            token_features=self._extract_token_features(code)
        )
        
        analysis['features'] = {
            'ast_features': features.ast_features,
            'complexity_metrics': features.complexity_metrics,
            'embedding_shape': features.code_embeddings.shape
        }
        
        # Predict bugs
        bugs = self.bug_predictor.predict(code, file_path)
        analysis['bugs'] = [
            {
                'line': bug.line_number,
                'type': bug.bug_type,
                'confidence': bug.confidence,
                'explanation': bug.explanation,
                'fix': bug.suggested_fix
            }
            for bug in bugs
        ]
        
        # Predict performance
        performance = self.performance_predictor.predict(code)
        analysis['performance'] = performance
        
        # Suggest refactorings
        refactorings = self.refactoring_engine.suggest_refactorings(code, file_path)
        analysis['refactorings'] = [
            {
                'type': ref.refactoring_type,
                'lines': f"{ref.start_line}-{ref.end_line}",
                'description': ref.description,
                'impact': ref.impact_score
            }
            for ref in refactorings
        ]
        
        return analysis
        
    async def find_similar_code(self, query_code: str, 
                              code_base: Dict[str, str]) -> List[Dict[str, Any]]:
        """Find similar code in codebase"""
        similarities = self.similarity_detector.find_similar_code(
            code_base, query_code
        )
        
        return [
            {
                'file': sim.code2_path,
                'similarity': sim.similarity_score,
                'components': sim.similar_components,
                'is_duplicate': sim.potential_duplication
            }
            for sim in similarities
        ]
        
    async def learn_from_codebase(self, code_base: Dict[str, str]):
        """Learn patterns from codebase"""
        # Learn API usage
        self.api_learner.learn_from_code(code_base)
        
        # Train bug predictor if we have labeled data
        # This would need actual bug data in practice
        
        # Train performance predictor if we have performance data
        # This would need actual performance measurements
        
        logger.info(f"Learned from {len(code_base)} files")
        
    async def suggest_code_completion(self, partial_code: str) -> List[Dict[str, Any]]:
        """Suggest code completions"""
        suggestions = []
        
        # API usage suggestions
        api_suggestions = self.api_learner.suggest_api_usage(partial_code)
        
        for api_sugg in api_suggestions:
            suggestions.append({
                'type': 'api_usage',
                'suggestion': api_sugg['pattern'],
                'confidence': api_sugg['confidence'],
                'next_calls': api_sugg.get('next_calls', [])
            })
            
        return suggestions
        
    def _calculate_complexity_metrics(self, code: str) -> Dict[str, float]:
        """Calculate code complexity metrics"""
        try:
            # Cyclomatic complexity
            cc_result = radon_complexity.cc_visit(code)
            avg_complexity = np.mean([block.complexity for block in cc_result]) if cc_result else 0
            
            # Halstead metrics
            h_visitor = radon_metrics.HalsteadVisitor.from_code(code)
            halstead = h_visitor.halstead
            
            # Maintainability index
            mi_score = radon_metrics.mi_visit(code, multi=True)
            
            return {
                'cyclomatic_complexity': avg_complexity,
                'halstead_volume': halstead.volume if halstead else 0,
                'halstead_difficulty': halstead.difficulty if halstead else 0,
                'maintainability_index': mi_score
            }
        except:
            return {
                'cyclomatic_complexity': 0,
                'halstead_volume': 0,
                'halstead_difficulty': 0,
                'maintainability_index': 0
            }
            
    def _extract_token_features(self, code: str) -> Dict[str, int]:
        """Extract token-level features"""
        lexer = get_lexer_by_name("python")
        tokens = list(pygments.lex(code, lexer))
        
        token_counts = Counter()
        for token_type, token_value in tokens:
            token_counts[str(token_type)] += 1
            
        return dict(token_counts)

# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize code intelligence
        code_intel = NexusCodeIntelligence()
        
        # Example code to analyze
        example_code = '''
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def process_data(data):
    result = []
    for i in range(len(data)):
        for j in range(len(data[i])):
            if data[i][j] > 0:
                result.append(data[i][j] * 2)
    return result

# Potential bug: file not closed
def read_file(filename):
    f = open(filename, 'r')
    content = f.read()
    return content
'''
        
        # Analyze code
        analysis = await code_intel.analyze_code(example_code, "example.py")
        
        print("Code Analysis Results:")
        print(f"Bugs found: {len(analysis['bugs'])}")
        for bug in analysis['bugs']:
            print(f"  - Line {bug['line']}: {bug['type']} ({bug['confidence']:.2f})")
            
        print(f"\nPerformance predictions:")
        for metric, value in analysis['performance'].items():
            print(f"  - {metric}: {value}")
            
        print(f"\nRefactoring suggestions: {len(analysis['refactorings'])}")
        for ref in analysis['refactorings']:
            print(f"  - {ref['type']} at lines {ref['lines']}: {ref['description']}")
            
        # Find similar code
        codebase = {
            'file1.py': example_code,
            'file2.py': '''
def fibonacci(num):
    if num <= 1:
        return num
    return fibonacci(num-1) + fibonacci(num-2)
'''
        }
        
        similar = await code_intel.find_similar_code(
            "def fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)",
            codebase
        )
        
        print(f"\nSimilar code found:")
        for sim in similar:
            print(f"  - {sim['file']}: {sim['similarity']:.2%} similar")
            
    asyncio.run(main())