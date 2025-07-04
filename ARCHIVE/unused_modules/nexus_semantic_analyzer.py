"""
NEXUS Semantic Code Analyzer - Deep Understanding of Code Intent and Business Logic
"""

import ast
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import networkx as nx
from collections import defaultdict
import re
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CodeIntent:
    """Represents the semantic intent of code"""
    type: str  # function, class, module
    name: str
    purpose: str
    business_context: str
    inputs: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]
    side_effects: List[str]
    preconditions: List[str]
    postconditions: List[str]
    invariants: List[str]

@dataclass
class BusinessLogic:
    """Extracted business logic from code"""
    domain: str
    rules: List[Dict[str, Any]]
    workflows: List[Dict[str, Any]]
    entities: List[Dict[str, Any]]
    constraints: List[str]
    decisions: List[Dict[str, Any]]

@dataclass
class DataFlow:
    """Represents data flow through the system"""
    source: str
    destination: str
    data_type: str
    transformations: List[str]
    validation_points: List[str]
    security_checks: List[str]
    path: List[str]

@dataclass
class ArchitecturePattern:
    """Recognized architecture pattern"""
    name: str
    type: str  # mvc, microservices, layered, etc.
    components: List[str]
    relationships: List[Dict[str, Any]]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]

@dataclass
class RefactoringCandidate:
    """Suggested refactoring based on semantic analysis"""
    location: str
    issue_type: str
    current_implementation: str
    suggested_implementation: str
    semantic_improvement: str
    business_impact: str
    risk_level: str
    effort_estimate: str

@dataclass
class CodeQualityMetrics:
    """Semantic code quality metrics"""
    semantic_coherence: float
    business_alignment: float
    intent_clarity: float
    abstraction_level: float
    domain_consistency: float
    cognitive_complexity: float
    maintainability_index: float

class SemanticASTAnalyzer(ast.NodeVisitor):
    """AST visitor for semantic analysis"""
    
    def __init__(self):
        self.functions = []
        self.classes = []
        self.imports = []
        self.global_vars = []
        self.patterns = []
        self.comments = []
        
    def visit_FunctionDef(self, node):
        """Analyze function definitions"""
        func_info = {
            "name": node.name,
            "args": [arg.arg for arg in node.args.args],
            "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
            "docstring": ast.get_docstring(node),
            "complexity": self._calculate_complexity(node),
            "calls": self._extract_function_calls(node),
            "returns": self._analyze_returns(node),
            "raises": self._analyze_exceptions(node)
        }
        self.functions.append(func_info)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Analyze class definitions"""
        class_info = {
            "name": node.name,
            "bases": [self._get_base_name(base) for base in node.bases],
            "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
            "docstring": ast.get_docstring(node),
            "methods": [],
            "attributes": [],
            "properties": []
        }
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                class_info["methods"].append(item.name)
                if any(d.id == "property" for d in item.decorator_list if isinstance(d, ast.Name)):
                    class_info["properties"].append(item.name)
        
        self.classes.append(class_info)
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """Track imports"""
        for alias in node.names:
            self.imports.append({
                "module": alias.name,
                "alias": alias.asname
            })
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Track from imports"""
        for alias in node.names:
            self.imports.append({
                "module": f"{node.module}.{alias.name}" if node.module else alias.name,
                "alias": alias.asname,
                "from": node.module
            })
        self.generic_visit(node)
    
    def _get_decorator_name(self, decorator):
        """Extract decorator name"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
            return decorator.func.id
        return "unknown"
    
    def _get_base_name(self, base):
        """Extract base class name"""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return f"{base.value.id}.{base.attr}"
        return "unknown"
    
    def _calculate_complexity(self, node):
        """Calculate cyclomatic complexity"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    def _extract_function_calls(self, node):
        """Extract function calls from node"""
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(f"{child.func.attr}")
        return calls
    
    def _analyze_returns(self, node):
        """Analyze return statements"""
        returns = []
        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                if child.value:
                    returns.append(self._get_value_type(child.value))
        return returns
    
    def _analyze_exceptions(self, node):
        """Analyze raised exceptions"""
        exceptions = []
        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                if child.exc:
                    if isinstance(child.exc, ast.Call) and isinstance(child.exc.func, ast.Name):
                        exceptions.append(child.exc.func.id)
        return exceptions
    
    def _get_value_type(self, value):
        """Infer value type from AST node"""
        if isinstance(value, ast.Constant):
            return type(value.value).__name__
        elif isinstance(value, ast.Name):
            return value.id
        elif isinstance(value, ast.List):
            return "list"
        elif isinstance(value, ast.Dict):
            return "dict"
        elif isinstance(value, ast.Call):
            if isinstance(value.func, ast.Name):
                return value.func.id
        return "unknown"

class BusinessLogicExtractor:
    """Extracts business logic from code"""
    
    def __init__(self):
        self.business_terms = self._load_business_terms()
        self.domain_patterns = self._load_domain_patterns()
    
    def _load_business_terms(self) -> Set[str]:
        """Load common business terms"""
        return {
            "customer", "order", "payment", "invoice", "product",
            "inventory", "shipping", "discount", "tax", "revenue",
            "user", "account", "transaction", "balance", "report",
            "workflow", "approval", "notification", "audit", "compliance"
        }
    
    def _load_domain_patterns(self) -> Dict[str, List[str]]:
        """Load domain-specific patterns"""
        return {
            "e-commerce": ["cart", "checkout", "catalog", "sku"],
            "finance": ["ledger", "portfolio", "interest", "loan"],
            "healthcare": ["patient", "diagnosis", "prescription", "appointment"],
            "logistics": ["route", "delivery", "warehouse", "tracking"]
        }
    
    def extract_business_logic(self, ast_tree: ast.AST, code_text: str) -> BusinessLogic:
        """Extract business logic from AST"""
        analyzer = SemanticASTAnalyzer()
        analyzer.visit(ast_tree)
        
        # Identify domain
        domain = self._identify_domain(analyzer, code_text)
        
        # Extract business rules
        rules = self._extract_business_rules(analyzer, code_text)
        
        # Extract workflows
        workflows = self._extract_workflows(analyzer)
        
        # Extract entities
        entities = self._extract_entities(analyzer)
        
        # Extract constraints
        constraints = self._extract_constraints(analyzer, code_text)
        
        # Extract decision points
        decisions = self._extract_decisions(analyzer)
        
        return BusinessLogic(
            domain=domain,
            rules=rules,
            workflows=workflows,
            entities=entities,
            constraints=constraints,
            decisions=decisions
        )
    
    def _identify_domain(self, analyzer: SemanticASTAnalyzer, code_text: str) -> str:
        """Identify business domain"""
        code_lower = code_text.lower()
        
        # Count domain-specific terms
        domain_scores = {}
        for domain, terms in self.domain_patterns.items():
            score = sum(1 for term in terms if term in code_lower)
            domain_scores[domain] = score
        
        # Also check business terms
        business_score = sum(1 for term in self.business_terms if term in code_lower)
        
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            if domain_scores[best_domain] > 0:
                return best_domain
        
        return "general" if business_score > 0 else "technical"
    
    def _extract_business_rules(self, analyzer: SemanticASTAnalyzer, code_text: str) -> List[Dict[str, Any]]:
        """Extract business rules from code"""
        rules = []
        
        # Look for validation functions
        for func in analyzer.functions:
            if any(keyword in func["name"].lower() for keyword in ["validate", "check", "verify"]):
                rules.append({
                    "type": "validation",
                    "name": func["name"],
                    "description": self._extract_rule_description(func),
                    "conditions": self._extract_conditions(func)
                })
        
        # Look for business calculations
        for func in analyzer.functions:
            if any(keyword in func["name"].lower() for keyword in ["calculate", "compute", "total"]):
                rules.append({
                    "type": "calculation",
                    "name": func["name"],
                    "description": self._extract_rule_description(func),
                    "formula": self._extract_formula(func)
                })
        
        return rules
    
    def _extract_workflows(self, analyzer: SemanticASTAnalyzer) -> List[Dict[str, Any]]:
        """Extract business workflows"""
        workflows = []
        
        # Look for process-oriented functions
        for func in analyzer.functions:
            if any(keyword in func["name"].lower() for keyword in ["process", "handle", "flow", "pipeline"]):
                workflows.append({
                    "name": func["name"],
                    "steps": self._extract_workflow_steps(func),
                    "inputs": func["args"],
                    "outputs": func["returns"]
                })
        
        return workflows
    
    def _extract_entities(self, analyzer: SemanticASTAnalyzer) -> List[Dict[str, Any]]:
        """Extract business entities"""
        entities = []
        
        for cls in analyzer.classes:
            # Check if it's a business entity
            if any(term in cls["name"].lower() for term in self.business_terms):
                entities.append({
                    "name": cls["name"],
                    "type": "business_entity",
                    "attributes": cls["attributes"],
                    "methods": cls["methods"],
                    "relationships": self._extract_relationships(cls)
                })
        
        return entities
    
    def _extract_constraints(self, analyzer: SemanticASTAnalyzer, code_text: str) -> List[str]:
        """Extract business constraints"""
        constraints = []
        
        # Look for assert statements
        lines = code_text.split('\n')
        for line in lines:
            if 'assert' in line and not line.strip().startswith('#'):
                constraints.append(line.strip())
        
        # Look for constraint patterns in docstrings
        for func in analyzer.functions:
            if func["docstring"]:
                doc_lower = func["docstring"].lower()
                if any(word in doc_lower for word in ["must", "should", "require", "constraint"]):
                    constraints.append(f"{func['name']}: {func['docstring'][:100]}")
        
        return constraints
    
    def _extract_decisions(self, analyzer: SemanticASTAnalyzer) -> List[Dict[str, Any]]:
        """Extract decision points"""
        decisions = []
        
        for func in analyzer.functions:
            if func["complexity"] > 3:  # Functions with multiple branches
                decisions.append({
                    "function": func["name"],
                    "complexity": func["complexity"],
                    "type": "complex_decision",
                    "branches": func["complexity"] - 1
                })
        
        return decisions
    
    def _extract_rule_description(self, func: Dict) -> str:
        """Extract rule description from function"""
        if func["docstring"]:
            return func["docstring"].split('\n')[0]
        return f"Rule implemented in {func['name']}"
    
    def _extract_conditions(self, func: Dict) -> List[str]:
        """Extract conditions from function"""
        # Simplified - would need deeper AST analysis
        conditions = []
        if "validate" in func["name"].lower():
            conditions.append(f"Validation logic in {func['name']}")
        return conditions
    
    def _extract_formula(self, func: Dict) -> str:
        """Extract calculation formula"""
        # Simplified - would need deeper AST analysis
        return f"Calculation implemented in {func['name']}"
    
    def _extract_workflow_steps(self, func: Dict) -> List[str]:
        """Extract workflow steps"""
        steps = []
        for i, call in enumerate(func["calls"]):
            steps.append(f"Step {i+1}: {call}")
        return steps
    
    def _extract_relationships(self, cls: Dict) -> List[str]:
        """Extract entity relationships"""
        relationships = []
        for base in cls["bases"]:
            if base != "object":
                relationships.append(f"inherits from {base}")
        return relationships

class DataFlowTracer:
    """Traces data flow through the system"""
    
    def __init__(self):
        self.flow_graph = nx.DiGraph()
        self.data_sources = set()
        self.data_sinks = set()
        self.transformations = defaultdict(list)
    
    def trace_data_flow(self, ast_tree: ast.AST) -> List[DataFlow]:
        """Trace data flow through the code"""
        analyzer = SemanticASTAnalyzer()
        analyzer.visit(ast_tree)
        
        flows = []
        
        # Build flow graph
        self._build_flow_graph(analyzer)
        
        # Find data paths
        for source in self.data_sources:
            for sink in self.data_sinks:
                paths = self._find_paths(source, sink)
                for path in paths:
                    flow = self._create_data_flow(source, sink, path)
                    flows.append(flow)
        
        return flows
    
    def _build_flow_graph(self, analyzer: SemanticASTAnalyzer):
        """Build data flow graph"""
        # Simplified implementation
        for func in analyzer.functions:
            node_name = func["name"]
            self.flow_graph.add_node(node_name, type="function")
            
            # Connect based on calls
            for call in func["calls"]:
                self.flow_graph.add_edge(node_name, call)
            
            # Identify sources and sinks
            if any(keyword in node_name.lower() for keyword in ["read", "load", "get"]):
                self.data_sources.add(node_name)
            if any(keyword in node_name.lower() for keyword in ["write", "save", "put"]):
                self.data_sinks.add(node_name)
    
    def _find_paths(self, source: str, sink: str) -> List[List[str]]:
        """Find all paths from source to sink"""
        try:
            paths = list(nx.all_simple_paths(self.flow_graph, source, sink, cutoff=10))
            return paths[:5]  # Limit to 5 paths
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
    
    def _create_data_flow(self, source: str, sink: str, path: List[str]) -> DataFlow:
        """Create DataFlow object from path"""
        transformations = []
        for node in path[1:-1]:  # Exclude source and sink
            if "transform" in node.lower() or "process" in node.lower():
                transformations.append(node)
        
        return DataFlow(
            source=source,
            destination=sink,
            data_type="unknown",  # Would need type inference
            transformations=transformations,
            validation_points=[n for n in path if "validate" in n.lower()],
            security_checks=[n for n in path if "auth" in n.lower() or "security" in n.lower()],
            path=path
        )

class ArchitecturePatternRecognizer:
    """Recognizes architecture patterns in code"""
    
    def __init__(self):
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load architecture pattern definitions"""
        return {
            "mvc": {
                "indicators": ["model", "view", "controller"],
                "structure": ["separation of concerns", "user interface", "business logic"],
                "strengths": ["Clear separation", "Testability", "Reusability"],
                "weaknesses": ["Can be overkill for simple apps", "Tight coupling possible"]
            },
            "repository": {
                "indicators": ["repository", "dao", "data access"],
                "structure": ["abstraction over data source", "consistent interface"],
                "strengths": ["Decoupling", "Testability", "Flexibility"],
                "weaknesses": ["Additional complexity", "Performance overhead"]
            },
            "observer": {
                "indicators": ["observer", "listener", "event", "notify"],
                "structure": ["subject-observer relationship", "event-driven"],
                "strengths": ["Loose coupling", "Dynamic relationships"],
                "weaknesses": ["Memory leaks possible", "Debugging complexity"]
            },
            "factory": {
                "indicators": ["factory", "create", "builder"],
                "structure": ["object creation abstraction", "polymorphic instantiation"],
                "strengths": ["Flexibility", "Encapsulation"],
                "weaknesses": ["Code complexity", "Indirection"]
            }
        }
    
    def recognize_patterns(self, analyzer: SemanticASTAnalyzer) -> List[ArchitecturePattern]:
        """Recognize architecture patterns"""
        recognized_patterns = []
        
        # Check class and function names
        all_names = [cls["name"].lower() for cls in analyzer.classes]
        all_names.extend([func["name"].lower() for func in analyzer.functions])
        
        for pattern_name, pattern_def in self.patterns.items():
            score = sum(1 for indicator in pattern_def["indicators"] if any(indicator in name for name in all_names))
            
            if score >= 2:  # Threshold for pattern detection
                pattern = ArchitecturePattern(
                    name=pattern_name.upper(),
                    type=pattern_name,
                    components=self._find_pattern_components(analyzer, pattern_def["indicators"]),
                    relationships=self._analyze_relationships(analyzer),
                    strengths=pattern_def["strengths"],
                    weaknesses=pattern_def["weaknesses"],
                    recommendations=self._generate_recommendations(pattern_name)
                )
                recognized_patterns.append(pattern)
        
        return recognized_patterns
    
    def _find_pattern_components(self, analyzer: SemanticASTAnalyzer, indicators: List[str]) -> List[str]:
        """Find components matching pattern"""
        components = []
        
        for cls in analyzer.classes:
            if any(indicator in cls["name"].lower() for indicator in indicators):
                components.append(cls["name"])
        
        for func in analyzer.functions:
            if any(indicator in func["name"].lower() for indicator in indicators):
                components.append(func["name"])
        
        return components
    
    def _analyze_relationships(self, analyzer: SemanticASTAnalyzer) -> List[Dict[str, Any]]:
        """Analyze component relationships"""
        relationships = []
        
        # Analyze inheritance
        for cls in analyzer.classes:
            for base in cls["bases"]:
                relationships.append({
                    "type": "inheritance",
                    "from": cls["name"],
                    "to": base
                })
        
        return relationships
    
    def _generate_recommendations(self, pattern_name: str) -> List[str]:
        """Generate pattern-specific recommendations"""
        base_recommendations = [
            "Ensure consistent pattern implementation",
            "Document pattern usage for team members",
            "Consider pattern trade-offs for your use case"
        ]
        
        pattern_specific = {
            "mvc": ["Keep controllers thin", "Avoid business logic in views"],
            "repository": ["Use interfaces for repositories", "Implement unit of work pattern"],
            "observer": ["Implement proper cleanup", "Consider weak references"],
            "factory": ["Keep factory methods simple", "Use dependency injection"]
        }
        
        return base_recommendations + pattern_specific.get(pattern_name, [])

class SemanticRefactoringAnalyzer:
    """Analyzes code for semantic refactoring opportunities"""
    
    def __init__(self):
        self.code_smells = self._load_code_smells()
    
    def _load_code_smells(self) -> Dict[str, Dict[str, Any]]:
        """Load semantic code smell definitions"""
        return {
            "feature_envy": {
                "description": "Method uses another class more than its own",
                "impact": "Violates encapsulation",
                "solution": "Move method to the class it uses most"
            },
            "data_clump": {
                "description": "Same group of variables used together repeatedly",
                "impact": "Duplication and coupling",
                "solution": "Extract into a class"
            },
            "primitive_obsession": {
                "description": "Overuse of primitive types for domain concepts",
                "impact": "Lost domain meaning",
                "solution": "Create domain-specific types"
            },
            "inappropriate_intimacy": {
                "description": "Classes know too much about each other",
                "impact": "High coupling",
                "solution": "Use interfaces or mediator pattern"
            }
        }
    
    def analyze_refactoring_opportunities(
        self, 
        ast_tree: ast.AST, 
        business_logic: BusinessLogic
    ) -> List[RefactoringCandidate]:
        """Analyze code for refactoring opportunities"""
        candidates = []
        
        analyzer = SemanticASTAnalyzer()
        analyzer.visit(ast_tree)
        
        # Check for semantic code smells
        candidates.extend(self._check_feature_envy(analyzer))
        candidates.extend(self._check_data_clumps(analyzer))
        candidates.extend(self._check_primitive_obsession(analyzer, business_logic))
        candidates.extend(self._check_inappropriate_intimacy(analyzer))
        
        # Business logic alignment
        candidates.extend(self._check_business_alignment(analyzer, business_logic))
        
        return candidates
    
    def _check_feature_envy(self, analyzer: SemanticASTAnalyzer) -> List[RefactoringCandidate]:
        """Check for feature envy smell"""
        candidates = []
        
        for func in analyzer.functions:
            # Count external method calls
            external_calls = defaultdict(int)
            for call in func["calls"]:
                if "." in call:
                    class_name = call.split(".")[0]
                    external_calls[class_name] += 1
            
            if external_calls:
                most_used = max(external_calls, key=external_calls.get)
                if external_calls[most_used] > 3:  # Threshold
                    candidates.append(RefactoringCandidate(
                        location=func["name"],
                        issue_type="feature_envy",
                        current_implementation=f"Method in current class",
                        suggested_implementation=f"Move to {most_used} class",
                        semantic_improvement="Better encapsulation and cohesion",
                        business_impact="Clearer domain boundaries",
                        risk_level="medium",
                        effort_estimate="2-4 hours"
                    ))
        
        return candidates
    
    def _check_data_clumps(self, analyzer: SemanticASTAnalyzer) -> List[RefactoringCandidate]:
        """Check for data clumps"""
        candidates = []
        
        # Find functions with many parameters
        for func in analyzer.functions:
            if len(func["args"]) > 3:
                # Check if these parameters appear together elsewhere
                param_set = set(func["args"])
                
                for other_func in analyzer.functions:
                    if other_func["name"] != func["name"]:
                        other_params = set(other_func["args"])
                        common = param_set.intersection(other_params)
                        
                        if len(common) >= 3:
                            candidates.append(RefactoringCandidate(
                                location=f"{func['name']} and {other_func['name']}",
                                issue_type="data_clump",
                                current_implementation=f"Parameters: {', '.join(common)}",
                                suggested_implementation="Extract into a data class",
                                semantic_improvement="Explicit domain concept",
                                business_impact="Clearer data relationships",
                                risk_level="low",
                                effort_estimate="1-2 hours"
                            ))
                            break
        
        return candidates
    
    def _check_primitive_obsession(
        self, 
        analyzer: SemanticASTAnalyzer, 
        business_logic: BusinessLogic
    ) -> List[RefactoringCandidate]:
        """Check for primitive obsession"""
        candidates = []
        
        # Look for business terms used with primitive types
        for func in analyzer.functions:
            for arg in func["args"]:
                for entity in business_logic.entities:
                    if entity["name"].lower() in arg.lower() and "_id" in arg.lower():
                        candidates.append(RefactoringCandidate(
                            location=f"{func['name']}.{arg}",
                            issue_type="primitive_obsession",
                            current_implementation=f"String/int ID for {entity['name']}",
                            suggested_implementation=f"Use {entity['name']} value object",
                            semantic_improvement="Type safety and domain modeling",
                            business_impact="Prevent invalid data",
                            risk_level="low",
                            effort_estimate="2-3 hours"
                        ))
        
        return candidates
    
    def _check_inappropriate_intimacy(self, analyzer: SemanticASTAnalyzer) -> List[RefactoringCandidate]:
        """Check for inappropriate intimacy"""
        candidates = []
        
        # Look for classes that reference each other extensively
        class_dependencies = defaultdict(set)
        
        for cls in analyzer.classes:
            for method in cls["methods"]:
                # Find method in functions
                for func in analyzer.functions:
                    if func["name"] == method:
                        for call in func["calls"]:
                            if "." in call:
                                called_class = call.split(".")[0]
                                class_dependencies[cls["name"]].add(called_class)
        
        # Check for bidirectional dependencies
        for class1, deps1 in class_dependencies.items():
            for class2 in deps1:
                if class2 in class_dependencies and class1 in class_dependencies[class2]:
                    candidates.append(RefactoringCandidate(
                        location=f"{class1} <-> {class2}",
                        issue_type="inappropriate_intimacy",
                        current_implementation="Bidirectional dependency",
                        suggested_implementation="Introduce interface or mediator",
                        semantic_improvement="Reduced coupling",
                        business_impact="Easier to modify independently",
                        risk_level="high",
                        effort_estimate="4-8 hours"
                    ))
        
        return candidates
    
    def _check_business_alignment(
        self, 
        analyzer: SemanticASTAnalyzer, 
        business_logic: BusinessLogic
    ) -> List[RefactoringCandidate]:
        """Check alignment with business logic"""
        candidates = []
        
        # Check if technical names should use business terms
        for func in analyzer.functions:
            func_lower = func["name"].lower()
            
            # Skip obvious technical functions
            if any(tech in func_lower for tech in ["init", "str", "repr", "eq"]):
                continue
            
            # Check if function deals with business concepts but uses technical names
            for entity in business_logic.entities:
                entity_lower = entity["name"].lower()
                if entity_lower in str(func["calls"]).lower() and entity_lower not in func_lower:
                    candidates.append(RefactoringCandidate(
                        location=func["name"],
                        issue_type="business_alignment",
                        current_implementation=f"Technical name: {func['name']}",
                        suggested_implementation=f"Use business term related to {entity['name']}",
                        semantic_improvement="Better business-code alignment",
                        business_impact="Improved communication with stakeholders",
                        risk_level="low",
                        effort_estimate="1 hour"
                    ))
        
        return candidates

class NexusSemanticAnalyzer:
    """Main semantic analyzer combining all components"""
    
    def __init__(self, workspace_path: str = "./nexus_semantic"):
        self.workspace = Path(workspace_path)
        self.workspace.mkdir(exist_ok=True)
        
        # Analysis components
        self.business_extractor = BusinessLogicExtractor()
        self.flow_tracer = DataFlowTracer()
        self.pattern_recognizer = ArchitecturePatternRecognizer()
        self.refactoring_analyzer = SemanticRefactoringAnalyzer()
        
        # Analysis cache
        self.analysis_cache = {}
    
    async def analyze_code(self, file_path: str) -> Dict[str, Any]:
        """Perform comprehensive semantic analysis"""
        logger.info(f"Analyzing {file_path}")
        
        # Read code
        with open(file_path, 'r') as f:
            code_text = f.read()
        
        # Parse AST
        try:
            ast_tree = ast.parse(code_text)
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            return {"error": str(e)}
        
        # Extract code intent
        intent = await self._analyze_intent(ast_tree, code_text)
        
        # Extract business logic
        business_logic = self.business_extractor.extract_business_logic(ast_tree, code_text)
        
        # Trace data flow
        data_flows = self.flow_tracer.trace_data_flow(ast_tree)
        
        # Recognize patterns
        ast_analyzer = SemanticASTAnalyzer()
        ast_analyzer.visit(ast_tree)
        patterns = self.pattern_recognizer.recognize_patterns(ast_analyzer)
        
        # Find refactoring opportunities
        refactorings = self.refactoring_analyzer.analyze_refactoring_opportunities(
            ast_tree, business_logic
        )
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(
            intent, business_logic, data_flows, patterns, refactorings
        )
        
        # Compile results
        analysis = {
            "file": file_path,
            "intent": intent,
            "business_logic": asdict(business_logic),
            "data_flows": [asdict(flow) for flow in data_flows],
            "patterns": [asdict(pattern) for pattern in patterns],
            "refactoring_suggestions": [asdict(ref) for ref in refactorings],
            "quality_metrics": asdict(quality_metrics),
            "timestamp": datetime.now().isoformat()
        }
        
        # Cache results
        self.analysis_cache[file_path] = analysis
        
        # Save analysis
        self._save_analysis(file_path, analysis)
        
        return analysis
    
    async def _analyze_intent(self, ast_tree: ast.AST, code_text: str) -> Dict[str, Any]:
        """Analyze code intent"""
        # Get module docstring
        module_doc = ast.get_docstring(ast_tree)
        
        # Analyze main components
        analyzer = SemanticASTAnalyzer()
        analyzer.visit(ast_tree)
        
        # Determine primary purpose
        if analyzer.classes:
            if any("test" in cls["name"].lower() for cls in analyzer.classes):
                purpose = "testing"
            elif any("model" in cls["name"].lower() for cls in analyzer.classes):
                purpose = "data_modeling"
            else:
                purpose = "business_logic"
        elif analyzer.functions:
            if any("main" in func["name"] for func in analyzer.functions):
                purpose = "application_entry"
            else:
                purpose = "utility"
        else:
            purpose = "configuration"
        
        return {
            "module_purpose": purpose,
            "module_description": module_doc or "No description provided",
            "main_components": {
                "classes": len(analyzer.classes),
                "functions": len(analyzer.functions),
                "imports": len(analyzer.imports)
            }
        }
    
    def _calculate_quality_metrics(
        self,
        intent: Dict[str, Any],
        business_logic: BusinessLogic,
        data_flows: List[DataFlow],
        patterns: List[ArchitecturePattern],
        refactorings: List[RefactoringCandidate]
    ) -> CodeQualityMetrics:
        """Calculate semantic quality metrics"""
        # Semantic coherence - how well components work together
        semantic_coherence = 1.0
        if refactorings:
            semantic_coherence -= 0.1 * len(refactorings)
        semantic_coherence = max(0.0, semantic_coherence)
        
        # Business alignment - how well code matches business domain
        business_alignment = 0.5
        if business_logic.domain != "technical":
            business_alignment = 0.8
        if business_logic.entities:
            business_alignment += 0.1
        if business_logic.rules:
            business_alignment += 0.1
        business_alignment = min(1.0, business_alignment)
        
        # Intent clarity
        intent_clarity = 0.7
        if intent["module_description"] != "No description provided":
            intent_clarity = 0.9
        
        # Abstraction level
        abstraction_level = 0.5
        if patterns:
            abstraction_level = 0.8
        
        # Domain consistency
        domain_consistency = 0.8
        smell_count = sum(1 for r in refactorings if r.issue_type == "business_alignment")
        domain_consistency -= 0.1 * smell_count
        domain_consistency = max(0.0, domain_consistency)
        
        # Cognitive complexity
        avg_complexity = sum(f["complexity"] for f in intent.get("functions", [])) / max(1, len(intent.get("functions", [])))
        cognitive_complexity = 1.0 - min(avg_complexity / 20.0, 1.0)
        
        # Maintainability index
        maintainability_index = (
            semantic_coherence * 0.2 +
            business_alignment * 0.2 +
            intent_clarity * 0.2 +
            abstraction_level * 0.1 +
            domain_consistency * 0.2 +
            cognitive_complexity * 0.1
        )
        
        return CodeQualityMetrics(
            semantic_coherence=round(semantic_coherence, 2),
            business_alignment=round(business_alignment, 2),
            intent_clarity=round(intent_clarity, 2),
            abstraction_level=round(abstraction_level, 2),
            domain_consistency=round(domain_consistency, 2),
            cognitive_complexity=round(cognitive_complexity, 2),
            maintainability_index=round(maintainability_index, 2)
        )
    
    def _save_analysis(self, file_path: str, analysis: Dict[str, Any]):
        """Save analysis results"""
        # Create analysis file name
        file_name = Path(file_path).stem
        analysis_path = self.workspace / f"{file_name}_semantic_analysis.json"
        
        with open(analysis_path, 'w') as f:
            json.dump(analysis, f, indent=2)
    
    async def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Analyze entire project"""
        project_path = Path(project_path)
        
        if not project_path.exists():
            return {"error": "Project path not found"}
        
        # Find all Python files
        py_files = list(project_path.rglob("*.py"))
        
        logger.info(f"Analyzing {len(py_files)} files in {project_path}")
        
        # Analyze each file
        results = {}
        for py_file in py_files:
            if "__pycache__" not in str(py_file):
                try:
                    analysis = await self.analyze_code(str(py_file))
                    results[str(py_file)] = analysis
                except Exception as e:
                    logger.error(f"Error analyzing {py_file}: {e}")
                    results[str(py_file)] = {"error": str(e)}
        
        # Generate project summary
        summary = self._generate_project_summary(results)
        
        return {
            "project": str(project_path),
            "files_analyzed": len(results),
            "summary": summary,
            "file_analyses": results
        }
    
    def _generate_project_summary(self, results: Dict[str, Dict]) -> Dict[str, Any]:
        """Generate project-level summary"""
        total_files = len(results)
        successful_analyses = sum(1 for r in results.values() if "error" not in r)
        
        # Aggregate metrics
        avg_metrics = {
            "semantic_coherence": 0.0,
            "business_alignment": 0.0,
            "maintainability_index": 0.0
        }
        
        metric_count = 0
        total_patterns = 0
        total_refactorings = 0
        domains = defaultdict(int)
        
        for analysis in results.values():
            if "quality_metrics" in analysis:
                metrics = analysis["quality_metrics"]
                avg_metrics["semantic_coherence"] += metrics["semantic_coherence"]
                avg_metrics["business_alignment"] += metrics["business_alignment"]
                avg_metrics["maintainability_index"] += metrics["maintainability_index"]
                metric_count += 1
            
            if "patterns" in analysis:
                total_patterns += len(analysis["patterns"])
            
            if "refactoring_suggestions" in analysis:
                total_refactorings += len(analysis["refactoring_suggestions"])
            
            if "business_logic" in analysis:
                domain = analysis["business_logic"]["domain"]
                domains[domain] += 1
        
        # Calculate averages
        if metric_count > 0:
            for key in avg_metrics:
                avg_metrics[key] = round(avg_metrics[key] / metric_count, 2)
        
        return {
            "total_files": total_files,
            "successful_analyses": successful_analyses,
            "average_metrics": avg_metrics,
            "total_patterns_found": total_patterns,
            "total_refactoring_suggestions": total_refactorings,
            "domains": dict(domains),
            "primary_domain": max(domains, key=domains.get) if domains else "unknown"
        }

# Example usage
async def main():
    analyzer = NexusSemanticAnalyzer()
    
    # Create a sample file for analysis
    sample_code = '''"""
E-commerce order processing module
"""

class Order:
    """Represents a customer order"""
    
    def __init__(self, customer_id, items):
        self.customer_id = customer_id
        self.items = items
        self.status = "pending"
        self.total = 0.0
    
    def calculate_total(self):
        """Calculate order total with tax"""
        subtotal = sum(item.price * item.quantity for item in self.items)
        tax = subtotal * 0.08  # 8% tax
        self.total = subtotal + tax
        return self.total
    
    def validate_order(self):
        """Validate order before processing"""
        if not self.items:
            raise ValueError("Order must have at least one item")
        
        if self.customer_id is None:
            raise ValueError("Customer ID is required")
        
        for item in self.items:
            if item.quantity <= 0:
                raise ValueError("Item quantity must be positive")
        
        return True
    
    def process_payment(self, payment_method):
        """Process payment for the order"""
        self.validate_order()
        total = self.calculate_total()
        
        # Process payment
        if payment_method.charge(total):
            self.status = "paid"
            return True
        else:
            self.status = "payment_failed"
            return False

def ship_order(order):
    """Ship a paid order"""
    if order.status != "paid":
        raise ValueError("Only paid orders can be shipped")
    
    # Create shipping label
    label = create_shipping_label(order)
    
    # Update order status
    order.status = "shipped"
    
    return label

def create_shipping_label(order):
    """Create shipping label for order"""
    return {
        "order_id": order.id,
        "customer": order.customer_id,
        "items": len(order.items)
    }
'''
    
    # Save sample code
    sample_path = Path("./sample_order.py")
    with open(sample_path, 'w') as f:
        f.write(sample_code)
    
    # Analyze the code
    analysis = await analyzer.analyze_code(str(sample_path))
    
    print("Semantic Analysis Results:")
    print(f"Business Domain: {analysis['business_logic']['domain']}")
    print(f"Quality Metrics: {analysis['quality_metrics']}")
    print(f"Patterns Found: {len(analysis['patterns'])}")
    print(f"Refactoring Suggestions: {len(analysis['refactoring_suggestions'])}")
    
    # Clean up
    sample_path.unlink()

if __name__ == "__main__":
    asyncio.run(main())