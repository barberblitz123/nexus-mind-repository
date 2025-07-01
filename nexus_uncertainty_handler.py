"""
NEXUS 2.0 Uncertainty Handler
Manages decision confidence, generates alternatives, and learns from feedback
"""

import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import hashlib
from collections import defaultdict
import sqlite3
import pickle

class ConfidenceLevel(Enum):
    """Confidence levels for decisions"""
    VERY_LOW = 0.2
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95

class UncertaintyType(Enum):
    """Types of uncertainty"""
    AMBIGUOUS_REQUIREMENT = "ambiguous_requirement"
    MULTIPLE_SOLUTIONS = "multiple_solutions"
    INCOMPLETE_INFORMATION = "incomplete_information"
    TECHNICAL_FEASIBILITY = "technical_feasibility"
    PERFORMANCE_TRADEOFF = "performance_tradeoff"
    SECURITY_CONCERN = "security_concern"
    COMPATIBILITY_ISSUE = "compatibility_issue"

@dataclass
class Decision:
    """Represents a decision with confidence"""
    id: str
    description: str
    confidence: float
    reasoning: List[str]
    alternatives: List['Decision'] = field(default_factory=list)
    uncertainty_types: Set[UncertaintyType] = field(default_factory=set)
    factors: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    outcome: Optional[str] = None
    feedback: Optional[Dict[str, Any]] = None

@dataclass
class Solution:
    """Represents a solution with trade-offs"""
    id: str
    name: str
    description: str
    confidence: float
    pros: List[str]
    cons: List[str]
    trade_offs: Dict[str, Any]
    implementation_complexity: float  # 0-1
    performance_impact: float  # -1 to 1
    security_score: float  # 0-1
    compatibility_score: float  # 0-1
    code_example: Optional[str] = None

@dataclass
class ClarificationRequest:
    """Request for clarification"""
    id: str
    uncertainty_type: UncertaintyType
    question: str
    context: str
    options: List[str]
    priority: int  # 1-5
    related_decisions: List[str]

class UncertaintyHandler:
    """Handles uncertainty in NEXUS decision making"""
    
    def __init__(self, learning_db: str = "nexus_uncertainty_learning.db"):
        self.learning_db = learning_db
        self.current_decisions: Dict[str, Decision] = {}
        self.decision_history: List[Decision] = []
        self.confidence_thresholds = {
            'require_clarification': 0.4,
            'suggest_alternatives': 0.6,
            'auto_proceed': 0.8
        }
        self.learning_weights = self._init_learning_weights()
        self._init_database()
        
    def _init_database(self):
        """Initialize learning database"""
        self.conn = sqlite3.connect(self.learning_db)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS decision_outcomes (
                decision_id TEXT PRIMARY KEY,
                decision_type TEXT,
                confidence REAL,
                factors TEXT,
                outcome TEXT,
                feedback TEXT,
                timestamp TIMESTAMP
            )
        ''')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS clarification_patterns (
                pattern_id TEXT PRIMARY KEY,
                uncertainty_type TEXT,
                question_template TEXT,
                success_rate REAL,
                usage_count INTEGER,
                last_used TIMESTAMP
            )
        ''')
        self.conn.commit()
        
    def _init_learning_weights(self) -> Dict[str, float]:
        """Initialize learning weights for confidence calculation"""
        return {
            'past_success': 0.3,
            'complexity': -0.2,
            'clarity': 0.25,
            'risk': -0.15,
            'alternatives': -0.1
        }
        
    def evaluate_decision(self, description: str, context: Dict[str, Any]) -> Decision:
        """Evaluate a decision with confidence scoring"""
        decision_id = self._generate_id(description)
        
        # Analyze the decision
        confidence, factors = self._calculate_confidence(description, context)
        uncertainty_types = self._identify_uncertainties(description, context)
        reasoning = self._generate_reasoning(factors, uncertainty_types)
        
        # Create decision
        decision = Decision(
            id=decision_id,
            description=description,
            confidence=confidence,
            reasoning=reasoning,
            uncertainty_types=uncertainty_types,
            factors=factors
        )
        
        # Generate alternatives if confidence is low
        if confidence < self.confidence_thresholds['suggest_alternatives']:
            alternatives = self._generate_alternatives(description, context)
            decision.alternatives = alternatives
            
        self.current_decisions[decision_id] = decision
        return decision
        
    def _calculate_confidence(self, description: str, context: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """Calculate confidence score with factors"""
        factors = {}
        
        # Clarity factor
        clarity = self._assess_clarity(description)
        factors['clarity'] = clarity
        
        # Complexity factor
        complexity = self._assess_complexity(context)
        factors['complexity'] = complexity
        
        # Risk factor
        risk = self._assess_risk(context)
        factors['risk'] = risk
        
        # Historical success factor
        past_success = self._check_past_success(description, context)
        factors['past_success'] = past_success
        
        # Information completeness
        completeness = self._assess_information_completeness(context)
        factors['completeness'] = completeness
        
        # Calculate weighted confidence
        confidence = 0.5  # Base confidence
        
        for factor, value in factors.items():
            if factor in self.learning_weights:
                confidence += self.learning_weights[factor] * value
                
        # Normalize to 0-1
        confidence = max(0.0, min(1.0, confidence))
        
        return confidence, factors
        
    def _identify_uncertainties(self, description: str, context: Dict[str, Any]) -> Set[UncertaintyType]:
        """Identify types of uncertainty in the decision"""
        uncertainties = set()
        
        # Check for ambiguous requirements
        ambiguous_words = ['maybe', 'possibly', 'might', 'could', 'should', 'probably']
        if any(word in description.lower() for word in ambiguous_words):
            uncertainties.add(UncertaintyType.AMBIGUOUS_REQUIREMENT)
            
        # Check for incomplete information
        if 'unknown' in context or 'missing' in context:
            uncertainties.add(UncertaintyType.INCOMPLETE_INFORMATION)
            
        # Check for multiple valid approaches
        if context.get('alternatives_count', 0) > 2:
            uncertainties.add(UncertaintyType.MULTIPLE_SOLUTIONS)
            
        # Check for performance concerns
        if 'performance' in context and context['performance'].get('uncertain', False):
            uncertainties.add(UncertaintyType.PERFORMANCE_TRADEOFF)
            
        # Check for security concerns
        if 'security' in context and context['security'].get('risks', []):
            uncertainties.add(UncertaintyType.SECURITY_CONCERN)
            
        return uncertainties
        
    def generate_solutions(self, problem: str, context: Dict[str, Any], 
                         max_solutions: int = 3) -> List[Solution]:
        """Generate multiple solutions with trade-offs"""
        solutions = []
        
        # Generate base solutions
        base_approaches = self._identify_approaches(problem, context)
        
        for i, approach in enumerate(base_approaches[:max_solutions]):
            solution = self._evaluate_solution(
                approach['name'],
                approach['description'],
                problem,
                context
            )
            solutions.append(solution)
            
        # Sort by confidence
        solutions.sort(key=lambda s: s.confidence, reverse=True)
        
        return solutions
        
    def _evaluate_solution(self, name: str, description: str, 
                         problem: str, context: Dict[str, Any]) -> Solution:
        """Evaluate a single solution"""
        solution_id = self._generate_id(f"{problem}_{name}")
        
        # Analyze pros and cons
        pros = self._identify_pros(name, description, context)
        cons = self._identify_cons(name, description, context)
        
        # Calculate metrics
        complexity = self._calculate_implementation_complexity(description, context)
        performance = self._calculate_performance_impact(description, context)
        security = self._calculate_security_score(description, context)
        compatibility = self._calculate_compatibility_score(description, context)
        
        # Calculate overall confidence
        confidence = (security * 0.3 + compatibility * 0.3 + 
                     (1 - complexity) * 0.2 + (1 + performance) / 2 * 0.2)
        
        # Identify trade-offs
        trade_offs = {
            'time_vs_quality': self._assess_time_quality_tradeoff(complexity, confidence),
            'performance_vs_maintainability': self._assess_perf_maint_tradeoff(
                performance, complexity
            ),
            'flexibility_vs_simplicity': self._assess_flex_simp_tradeoff(
                description, complexity
            )
        }
        
        # Generate code example if applicable
        code_example = None
        if context.get('include_code', False):
            code_example = self._generate_code_example(name, description)
            
        return Solution(
            id=solution_id,
            name=name,
            description=description,
            confidence=confidence,
            pros=pros,
            cons=cons,
            trade_offs=trade_offs,
            implementation_complexity=complexity,
            performance_impact=performance,
            security_score=security,
            compatibility_score=compatibility,
            code_example=code_example
        )
        
    def request_clarification(self, decision: Decision) -> List[ClarificationRequest]:
        """Generate clarification requests for uncertain decisions"""
        requests = []
        
        for uncertainty_type in decision.uncertainty_types:
            request = self._create_clarification_request(
                uncertainty_type,
                decision.description,
                decision.factors
            )
            if request:
                requests.append(request)
                
        # Prioritize requests
        requests.sort(key=lambda r: r.priority, reverse=True)
        
        return requests
        
    def _create_clarification_request(self, uncertainty_type: UncertaintyType,
                                    description: str, factors: Dict[str, float]) -> Optional[ClarificationRequest]:
        """Create a specific clarification request"""
        templates = {
            UncertaintyType.AMBIGUOUS_REQUIREMENT: {
                'question': "Could you clarify what you mean by '{}'?",
                'options': ["Specifically, I mean...", "Either option is fine", "Let me provide more context"]
            },
            UncertaintyType.INCOMPLETE_INFORMATION: {
                'question': "I need more information about {}. Can you provide:",
                'options': ["Here's the missing information...", "I don't have that information", "Use your best judgment"]
            },
            UncertaintyType.MULTIPLE_SOLUTIONS: {
                'question': "There are multiple ways to approach this. Which is more important:",
                'options': ["Performance", "Simplicity", "Flexibility", "Maintainability"]
            },
            UncertaintyType.PERFORMANCE_TRADEOFF: {
                'question': "This involves a performance trade-off. Would you prefer:",
                'options': ["Optimize for speed", "Optimize for memory", "Balanced approach"]
            }
        }
        
        if uncertainty_type not in templates:
            return None
            
        template = templates[uncertainty_type]
        
        # Extract the uncertain part from description
        uncertain_part = self._extract_uncertain_part(description, uncertainty_type)
        
        return ClarificationRequest(
            id=self._generate_id(f"clarify_{uncertainty_type.value}"),
            uncertainty_type=uncertainty_type,
            question=template['question'].format(uncertain_part),
            context=description,
            options=template['options'],
            priority=self._calculate_priority(uncertainty_type, factors),
            related_decisions=[d.id for d in self.current_decisions.values() 
                             if uncertainty_type in d.uncertainty_types]
        )
        
    def learn_from_outcome(self, decision_id: str, outcome: str, 
                         feedback: Dict[str, Any]):
        """Learn from decision outcomes"""
        if decision_id not in self.current_decisions:
            return
            
        decision = self.current_decisions[decision_id]
        decision.outcome = outcome
        decision.feedback = feedback
        
        # Store in database
        self.conn.execute('''
            INSERT OR REPLACE INTO decision_outcomes
            (decision_id, decision_type, confidence, factors, outcome, feedback, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            decision_id,
            str(list(decision.uncertainty_types)),
            decision.confidence,
            json.dumps(decision.factors),
            outcome,
            json.dumps(feedback),
            datetime.now()
        ))
        self.conn.commit()
        
        # Update learning weights
        self._update_learning_weights(decision, outcome, feedback)
        
        # Move to history
        self.decision_history.append(decision)
        del self.current_decisions[decision_id]
        
    def _update_learning_weights(self, decision: Decision, outcome: str, 
                               feedback: Dict[str, Any]):
        """Update learning weights based on outcome"""
        success = feedback.get('success', False)
        
        # Adjust weights based on success
        learning_rate = 0.1
        
        for factor, value in decision.factors.items():
            if factor in self.learning_weights:
                if success:
                    # Increase weight if factor contributed to success
                    if value > 0.5:
                        self.learning_weights[factor] += learning_rate * (1 - self.learning_weights[factor])
                else:
                    # Decrease weight if factor contributed to failure
                    if value > 0.5:
                        self.learning_weights[factor] -= learning_rate * self.learning_weights[factor]
                        
    def propagate_uncertainty(self, source_decision: Decision, 
                            related_decisions: List[Decision]) -> Dict[str, float]:
        """Propagate uncertainty through related decisions"""
        propagation_results = {}
        
        for related in related_decisions:
            # Calculate impact based on relationship strength
            impact = self._calculate_uncertainty_impact(source_decision, related)
            
            # Adjust confidence
            new_confidence = related.confidence * (1 - impact * (1 - source_decision.confidence))
            propagation_results[related.id] = new_confidence
            
            # Update the decision
            related.confidence = new_confidence
            related.reasoning.append(
                f"Confidence adjusted due to uncertainty in: {source_decision.description}"
            )
            
        return propagation_results
        
    def get_confidence_report(self) -> Dict[str, Any]:
        """Generate confidence report for all current decisions"""
        report = {
            'total_decisions': len(self.current_decisions),
            'confidence_distribution': {},
            'uncertainty_types': defaultdict(int),
            'requiring_clarification': [],
            'high_confidence': [],
            'low_confidence': []
        }
        
        # Analyze decisions
        for decision in self.current_decisions.values():
            # Categorize by confidence level
            level = self._get_confidence_level(decision.confidence)
            if level.name not in report['confidence_distribution']:
                report['confidence_distribution'][level.name] = 0
            report['confidence_distribution'][level.name] += 1
            
            # Count uncertainty types
            for u_type in decision.uncertainty_types:
                report['uncertainty_types'][u_type.value] += 1
                
            # Categorize decisions
            if decision.confidence < self.confidence_thresholds['require_clarification']:
                report['requiring_clarification'].append({
                    'id': decision.id,
                    'description': decision.description,
                    'confidence': decision.confidence
                })
            elif decision.confidence >= self.confidence_thresholds['auto_proceed']:
                report['high_confidence'].append({
                    'id': decision.id,
                    'description': decision.description,
                    'confidence': decision.confidence
                })
            else:
                report['low_confidence'].append({
                    'id': decision.id,
                    'description': decision.description,
                    'confidence': decision.confidence
                })
                
        return report
        
    # Helper methods
    def _generate_id(self, text: str) -> str:
        """Generate unique ID for decision/solution"""
        return hashlib.md5(f"{text}_{datetime.now()}".encode()).hexdigest()[:8]
        
    def _assess_clarity(self, description: str) -> float:
        """Assess clarity of description (0-1)"""
        # Simple heuristic based on specificity
        specific_words = ['exactly', 'specifically', 'must', 'require', 'need']
        vague_words = ['maybe', 'possibly', 'might', 'could', 'should']
        
        specific_count = sum(1 for word in specific_words if word in description.lower())
        vague_count = sum(1 for word in vague_words if word in description.lower())
        
        return min(1.0, max(0.0, 0.5 + specific_count * 0.1 - vague_count * 0.2))
        
    def _assess_complexity(self, context: Dict[str, Any]) -> float:
        """Assess complexity (0-1)"""
        complexity_factors = {
            'dependencies': len(context.get('dependencies', [])) / 10,
            'integration_points': len(context.get('integrations', [])) / 5,
            'async_operations': 0.3 if context.get('async', False) else 0,
            'external_services': len(context.get('external_services', [])) / 3
        }
        
        return min(1.0, sum(complexity_factors.values()) / len(complexity_factors))
        
    def _assess_risk(self, context: Dict[str, Any]) -> float:
        """Assess risk level (0-1)"""
        risk_factors = {
            'security_sensitive': 0.5 if context.get('security_sensitive', False) else 0,
            'data_loss_possible': 0.4 if context.get('data_loss_possible', False) else 0,
            'breaking_changes': 0.3 if context.get('breaking_changes', False) else 0,
            'performance_critical': 0.2 if context.get('performance_critical', False) else 0
        }
        
        return min(1.0, sum(risk_factors.values()))
        
    def _check_past_success(self, description: str, context: Dict[str, Any]) -> float:
        """Check historical success rate for similar decisions"""
        # Query database for similar decisions
        similar_decisions = self.conn.execute('''
            SELECT confidence, outcome, feedback
            FROM decision_outcomes
            WHERE decision_type LIKE ?
            ORDER BY timestamp DESC
            LIMIT 10
        ''', (f"%{context.get('type', 'general')}%",)).fetchall()
        
        if not similar_decisions:
            return 0.5  # Neutral if no history
            
        success_count = sum(1 for _, _, feedback in similar_decisions 
                          if json.loads(feedback).get('success', False))
        
        return success_count / len(similar_decisions)
        
    def _assess_information_completeness(self, context: Dict[str, Any]) -> float:
        """Assess how complete the information is"""
        required_fields = ['requirements', 'constraints', 'resources', 'timeline']
        present_fields = sum(1 for field in required_fields if field in context and context[field])
        
        return present_fields / len(required_fields)
        
    def _generate_reasoning(self, factors: Dict[str, float], 
                          uncertainties: Set[UncertaintyType]) -> List[str]:
        """Generate reasoning explanation"""
        reasoning = []
        
        # Factor-based reasoning
        for factor, value in factors.items():
            if value > 0.7:
                reasoning.append(f"High {factor} ({value:.2f}) increases confidence")
            elif value < 0.3:
                reasoning.append(f"Low {factor} ({value:.2f}) reduces confidence")
                
        # Uncertainty-based reasoning
        for uncertainty in uncertainties:
            reasoning.append(f"Uncertainty: {uncertainty.value.replace('_', ' ')}")
            
        return reasoning
        
    def _generate_alternatives(self, description: str, 
                             context: Dict[str, Any]) -> List[Decision]:
        """Generate alternative decisions"""
        alternatives = []
        
        # Generate variations based on different priorities
        priorities = ['performance', 'simplicity', 'security', 'compatibility']
        
        for priority in priorities:
            alt_context = context.copy()
            alt_context['priority'] = priority
            
            alt_description = f"{description} (optimized for {priority})"
            alt_decision = self.evaluate_decision(alt_description, alt_context)
            
            alternatives.append(alt_decision)
            
        return alternatives
        
    def _identify_approaches(self, problem: str, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify different approaches to solve a problem"""
        approaches = []
        
        # Common software engineering approaches
        if 'implementation' in problem.lower():
            approaches.extend([
                {'name': 'Simple Direct', 'description': 'Straightforward implementation with minimal abstraction'},
                {'name': 'Pattern-Based', 'description': 'Using established design patterns'},
                {'name': 'Framework-Integrated', 'description': 'Leveraging existing framework capabilities'}
            ])
            
        if 'optimization' in problem.lower():
            approaches.extend([
                {'name': 'Algorithm Optimization', 'description': 'Improve algorithmic complexity'},
                {'name': 'Caching Strategy', 'description': 'Implement strategic caching'},
                {'name': 'Parallel Processing', 'description': 'Utilize concurrent execution'}
            ])
            
        if not approaches:
            # Generic approaches
            approaches = [
                {'name': 'Conservative', 'description': 'Safe, well-tested approach'},
                {'name': 'Innovative', 'description': 'Modern, cutting-edge solution'},
                {'name': 'Balanced', 'description': 'Middle-ground approach'}
            ]
            
        return approaches
        
    def _identify_pros(self, name: str, description: str, context: Dict[str, Any]) -> List[str]:
        """Identify pros of a solution"""
        pros = []
        
        if 'simple' in name.lower() or 'direct' in name.lower():
            pros.extend(['Easy to understand', 'Quick to implement', 'Low complexity'])
            
        if 'pattern' in name.lower():
            pros.extend(['Well-established approach', 'Maintainable', 'Follows best practices'])
            
        if 'optimize' in name.lower():
            pros.extend(['Better performance', 'Resource efficient', 'Scalable'])
            
        return pros
        
    def _identify_cons(self, name: str, description: str, context: Dict[str, Any]) -> List[str]:
        """Identify cons of a solution"""
        cons = []
        
        if 'simple' in name.lower():
            cons.extend(['May not scale well', 'Limited flexibility'])
            
        if 'pattern' in name.lower():
            cons.extend(['Can be over-engineered', 'Learning curve'])
            
        if 'optimize' in name.lower():
            cons.extend(['Increased complexity', 'Harder to debug'])
            
        return cons
        
    def _calculate_implementation_complexity(self, description: str, 
                                           context: Dict[str, Any]) -> float:
        """Calculate implementation complexity (0-1)"""
        complexity_keywords = ['complex', 'advanced', 'distributed', 'async', 'parallel']
        simplicity_keywords = ['simple', 'basic', 'straightforward', 'direct']
        
        complexity_score = sum(1 for k in complexity_keywords if k in description.lower())
        simplicity_score = sum(1 for k in simplicity_keywords if k in description.lower())
        
        base_complexity = 0.5
        return min(1.0, max(0.0, base_complexity + complexity_score * 0.1 - simplicity_score * 0.1))
        
    def _calculate_performance_impact(self, description: str, 
                                    context: Dict[str, Any]) -> float:
        """Calculate performance impact (-1 to 1)"""
        positive_keywords = ['optimize', 'fast', 'efficient', 'cache', 'parallel']
        negative_keywords = ['slow', 'blocking', 'synchronous', 'iterate', 'nested']
        
        positive_score = sum(1 for k in positive_keywords if k in description.lower())
        negative_score = sum(1 for k in negative_keywords if k in description.lower())
        
        return min(1.0, max(-1.0, (positive_score - negative_score) * 0.2))
        
    def _calculate_security_score(self, description: str, context: Dict[str, Any]) -> float:
        """Calculate security score (0-1)"""
        security_positive = ['secure', 'encrypted', 'authenticated', 'authorized', 'sanitized']
        security_negative = ['vulnerable', 'exposed', 'public', 'unencrypted', 'trust']
        
        positive = sum(1 for k in security_positive if k in description.lower())
        negative = sum(1 for k in security_negative if k in description.lower())
        
        base_score = 0.7  # Assume reasonable security by default
        return min(1.0, max(0.0, base_score + positive * 0.1 - negative * 0.2))
        
    def _calculate_compatibility_score(self, description: str, context: Dict[str, Any]) -> float:
        """Calculate compatibility score (0-1)"""
        if 'compatibility_requirements' in context:
            met_requirements = sum(1 for req in context['compatibility_requirements']
                                 if req.lower() in description.lower())
            return met_requirements / len(context['compatibility_requirements'])
            
        return 0.8  # Default good compatibility
        
    def _assess_time_quality_tradeoff(self, complexity: float, quality: float) -> Dict[str, Any]:
        """Assess time vs quality trade-off"""
        return {
            'time_to_implement': 'Low' if complexity < 0.3 else 'Medium' if complexity < 0.7 else 'High',
            'quality_score': quality,
            'recommendation': 'Quick win' if complexity < 0.3 and quality > 0.7 else 'Invest time' if quality > 0.8 else 'Balance needed'
        }
        
    def _assess_perf_maint_tradeoff(self, performance: float, complexity: float) -> Dict[str, Any]:
        """Assess performance vs maintainability trade-off"""
        maintainability = 1 - complexity
        
        return {
            'performance_gain': performance,
            'maintainability': maintainability,
            'recommendation': 'Optimize' if performance > 0.5 and maintainability > 0.3 else 'Keep simple'
        }
        
    def _assess_flex_simp_tradeoff(self, description: str, complexity: float) -> Dict[str, Any]:
        """Assess flexibility vs simplicity trade-off"""
        flexibility_keywords = ['extensible', 'configurable', 'modular', 'plugin']
        flexibility = sum(1 for k in flexibility_keywords if k in description.lower()) / len(flexibility_keywords)
        
        return {
            'flexibility': flexibility,
            'simplicity': 1 - complexity,
            'recommendation': 'Flexible' if flexibility > 0.5 else 'Simple'
        }
        
    def _generate_code_example(self, name: str, description: str) -> str:
        """Generate a simple code example"""
        # This is a simplified example generator
        if 'cache' in name.lower():
            return '''from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_operation(param):
    # Cached computation
    result = perform_complex_calculation(param)
    return result'''
    
        elif 'pattern' in name.lower():
            return '''class SingletonPattern:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance'''
        
        else:
            return '''def solution_implementation(data):
    # Process data
    processed = preprocess(data)
    
    # Apply solution logic
    result = apply_algorithm(processed)
    
    return result'''
            
    def _extract_uncertain_part(self, description: str, uncertainty_type: UncertaintyType) -> str:
        """Extract the uncertain part from description"""
        words = description.split()
        
        if uncertainty_type == UncertaintyType.AMBIGUOUS_REQUIREMENT:
            # Find ambiguous words and their context
            ambiguous = ['maybe', 'possibly', 'might', 'could', 'should']
            for i, word in enumerate(words):
                if word.lower() in ambiguous:
                    start = max(0, i - 2)
                    end = min(len(words), i + 3)
                    return ' '.join(words[start:end])
                    
        return description[:50] + '...' if len(description) > 50 else description
        
    def _calculate_priority(self, uncertainty_type: UncertaintyType, 
                          factors: Dict[str, float]) -> int:
        """Calculate priority for clarification request"""
        base_priorities = {
            UncertaintyType.AMBIGUOUS_REQUIREMENT: 3,
            UncertaintyType.INCOMPLETE_INFORMATION: 4,
            UncertaintyType.MULTIPLE_SOLUTIONS: 2,
            UncertaintyType.TECHNICAL_FEASIBILITY: 3,
            UncertaintyType.PERFORMANCE_TRADEOFF: 2,
            UncertaintyType.SECURITY_CONCERN: 5,
            UncertaintyType.COMPATIBILITY_ISSUE: 4
        }
        
        priority = base_priorities.get(uncertainty_type, 3)
        
        # Adjust based on risk
        if factors.get('risk', 0) > 0.7:
            priority = min(5, priority + 1)
            
        return priority
        
    def _calculate_uncertainty_impact(self, source: Decision, target: Decision) -> float:
        """Calculate how much uncertainty propagates between decisions"""
        # Check for shared factors
        shared_factors = set(source.factors.keys()) & set(target.factors.keys())
        
        if not shared_factors:
            return 0.1  # Minimal impact if no shared factors
            
        # Calculate impact based on shared uncertainties
        shared_uncertainties = source.uncertainty_types & target.uncertainty_types
        
        impact = len(shared_uncertainties) / max(len(source.uncertainty_types), 1)
        impact *= len(shared_factors) / max(len(source.factors), 1)
        
        return min(1.0, impact)
        
    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Get confidence level enum from float value"""
        for level in ConfidenceLevel:
            if confidence <= level.value:
                return level
        return ConfidenceLevel.VERY_HIGH