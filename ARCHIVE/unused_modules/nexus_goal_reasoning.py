#!/usr/bin/env python3
"""
NEXUS Goal Reasoning System
==========================
Advanced goal understanding, decomposition, and strategy generation system.
Transforms high-level natural language goals into executable task sequences.
"""

import json
import sqlite3
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import networkx as nx
import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np
from collections import defaultdict
import re
from pathlib import Path

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load NLP models
try:
    nlp = spacy.load("en_core_web_sm")
except:
    logger.warning("Spacy model not found. Install with: python -m spacy download en_core_web_sm")
    nlp = None

# Initialize transformers for goal understanding
try:
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    sentiment_analyzer = pipeline("sentiment-analysis")
except:
    logger.warning("Transformers models not available. Install transformers library.")
    classifier = None
    sentiment_analyzer = None


class GoalType(Enum):
    """Types of goals the system can handle"""
    PERFORMANCE = "performance"
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"
    RESEARCH = "research"


class GoalPriority(Enum):
    """Priority levels for goals"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    WISHLIST = 1


class GoalStatus(Enum):
    """Status of goal execution"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StrategyType(Enum):
    """Types of strategies for achieving goals"""
    QUICK_WIN = "quick_win"
    COMPREHENSIVE = "comprehensive"
    MINIMAL = "minimal"
    OPTIMAL = "optimal"
    EXPERIMENTAL = "experimental"


@dataclass
class Task:
    """Represents a concrete task"""
    id: str
    description: str
    goal_id: str
    dependencies: List[str] = field(default_factory=list)
    estimated_hours: float = 0.0
    complexity: int = 1  # 1-5 scale
    required_skills: List[str] = field(default_factory=list)
    status: str = "pending"
    progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Strategy:
    """Represents a strategy to achieve a goal"""
    id: str
    goal_id: str
    type: StrategyType
    description: str
    tasks: List[Task] = field(default_factory=list)
    estimated_duration: float = 0.0
    risk_level: int = 1  # 1-5 scale
    success_probability: float = 0.8
    trade_offs: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0


@dataclass
class Goal:
    """Represents a high-level goal"""
    id: str
    original_text: str
    parsed_intent: str
    type: GoalType
    priority: GoalPriority
    status: GoalStatus
    strategies: List[Strategy] = field(default_factory=list)
    selected_strategy_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completion_criteria: List[str] = field(default_factory=list)
    progress: float = 0.0


class GoalReasoningSystem:
    """Main goal reasoning and decomposition system"""
    
    def __init__(self, db_path: str = "nexus_goals.db"):
        self.db_path = db_path
        self.goals: Dict[str, Goal] = {}
        self.goal_graph = nx.DiGraph()
        self.domain_knowledge = self._load_domain_knowledge()
        self.task_patterns = self._load_task_patterns()
        self._init_database()
        self._load_goals_from_db()
        
    def _init_database(self):
        """Initialize the goals database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Goals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id TEXT PRIMARY KEY,
                original_text TEXT,
                parsed_intent TEXT,
                type TEXT,
                priority INTEGER,
                status TEXT,
                selected_strategy_id TEXT,
                context TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                progress REAL
            )
        ''')
        
        # Strategies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategies (
                id TEXT PRIMARY KEY,
                goal_id TEXT,
                type TEXT,
                description TEXT,
                estimated_duration REAL,
                risk_level INTEGER,
                success_probability REAL,
                trade_offs TEXT,
                score REAL,
                FOREIGN KEY (goal_id) REFERENCES goals(id)
            )
        ''')
        
        # Tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                description TEXT,
                goal_id TEXT,
                strategy_id TEXT,
                dependencies TEXT,
                estimated_hours REAL,
                complexity INTEGER,
                required_skills TEXT,
                status TEXT,
                progress REAL,
                metadata TEXT,
                FOREIGN KEY (goal_id) REFERENCES goals(id),
                FOREIGN KEY (strategy_id) REFERENCES strategies(id)
            )
        ''')
        
        # Goal dependencies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goal_dependencies (
                goal_id TEXT,
                dependency_id TEXT,
                FOREIGN KEY (goal_id) REFERENCES goals(id),
                FOREIGN KEY (dependency_id) REFERENCES goals(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_domain_knowledge(self) -> Dict[str, Any]:
        """Load domain-specific knowledge for goal understanding"""
        return {
            "performance_indicators": [
                "speed", "fast", "slow", "performance", "optimize", "latency",
                "throughput", "efficiency", "response time", "load time"
            ],
            "feature_indicators": [
                "add", "implement", "create", "build", "develop", "feature",
                "functionality", "capability", "support", "enable"
            ],
            "security_indicators": [
                "secure", "security", "vulnerability", "exploit", "protect",
                "authenticate", "authorize", "encrypt", "ssl", "https"
            ],
            "common_tasks": {
                "authentication": [
                    "Design authentication schema",
                    "Implement user model",
                    "Create login/logout endpoints",
                    "Add session management",
                    "Implement password hashing",
                    "Add JWT token generation",
                    "Create middleware for auth checks"
                ],
                "performance": [
                    "Profile current performance",
                    "Identify bottlenecks",
                    "Implement caching strategy",
                    "Optimize database queries",
                    "Add lazy loading",
                    "Implement pagination",
                    "Minimize bundle size"
                ],
                "api": [
                    "Design API schema",
                    "Implement endpoint handlers",
                    "Add input validation",
                    "Create API documentation",
                    "Implement rate limiting",
                    "Add API versioning",
                    "Create integration tests"
                ]
            }
        }
    
    def _load_task_patterns(self) -> Dict[str, List[str]]:
        """Load common task decomposition patterns"""
        return {
            "crud_operations": [
                "Design data model",
                "Create database schema",
                "Implement Create endpoint",
                "Implement Read endpoints",
                "Implement Update endpoint",
                "Implement Delete endpoint",
                "Add validation logic",
                "Create unit tests",
                "Add integration tests"
            ],
            "ui_component": [
                "Design component interface",
                "Create component structure",
                "Implement component logic",
                "Add styling",
                "Create props validation",
                "Add event handlers",
                "Implement accessibility features",
                "Create component tests",
                "Add documentation"
            ],
            "optimization": [
                "Measure current performance",
                "Identify performance bottlenecks",
                "Research optimization techniques",
                "Implement optimizations",
                "Measure improved performance",
                "Document changes",
                "Create performance tests"
            ]
        }
    
    async def process_goal(self, goal_text: str, context: Dict[str, Any] = None) -> Goal:
        """Process a natural language goal and create structured goal object"""
        logger.info(f"Processing goal: {goal_text}")
        
        # Parse the goal
        parsed_info = await self._parse_goal(goal_text)
        
        # Create goal object
        goal = Goal(
            id=self._generate_id("goal"),
            original_text=goal_text,
            parsed_intent=parsed_info["intent"],
            type=parsed_info["type"],
            priority=parsed_info["priority"],
            status=GoalStatus.ANALYZING,
            context=context or {},
            completion_criteria=parsed_info["criteria"]
        )
        
        # Analyze dependencies
        goal.dependencies = await self._analyze_dependencies(goal)
        
        # Generate strategies
        strategies = await self._generate_strategies(goal)
        goal.strategies = strategies
        
        # Score and rank strategies
        for strategy in goal.strategies:
            strategy.score = self._score_strategy(strategy, goal)
        
        # Sort strategies by score
        goal.strategies.sort(key=lambda s: s.score, reverse=True)
        
        # Select default strategy
        if goal.strategies:
            goal.selected_strategy_id = goal.strategies[0].id
        
        # Update status
        goal.status = GoalStatus.PLANNING
        
        # Save to database and memory
        self._save_goal(goal)
        self.goals[goal.id] = goal
        
        # Add to goal graph
        self._update_goal_graph(goal)
        
        return goal
    
    async def _parse_goal(self, goal_text: str) -> Dict[str, Any]:
        """Parse natural language goal into structured information"""
        result = {
            "intent": "",
            "type": GoalType.FEATURE,
            "priority": GoalPriority.MEDIUM,
            "criteria": [],
            "entities": [],
            "keywords": []
        }
        
        # Use spaCy for basic NLP
        if nlp:
            doc = nlp(goal_text)
            
            # Extract entities
            result["entities"] = [(ent.text, ent.label_) for ent in doc.ents]
            
            # Extract key verbs and nouns
            verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]
            nouns = [token.lemma_ for token in doc if token.pos_ == "NOUN"]
            result["keywords"] = verbs + nouns
        
        # Classify goal type
        if classifier:
            type_labels = [t.value for t in GoalType]
            classification = classifier(goal_text, candidate_labels=type_labels)
            result["type"] = GoalType(classification["labels"][0])
        else:
            # Fallback classification based on keywords
            text_lower = goal_text.lower()
            if any(ind in text_lower for ind in self.domain_knowledge["performance_indicators"]):
                result["type"] = GoalType.PERFORMANCE
            elif any(ind in text_lower for ind in self.domain_knowledge["security_indicators"]):
                result["type"] = GoalType.SECURITY
            elif "fix" in text_lower or "bug" in text_lower:
                result["type"] = GoalType.BUGFIX
            elif "test" in text_lower:
                result["type"] = GoalType.TESTING
            elif "document" in text_lower or "docs" in text_lower:
                result["type"] = GoalType.DOCUMENTATION
        
        # Determine priority based on keywords
        if any(word in goal_text.lower() for word in ["urgent", "critical", "asap", "immediately"]):
            result["priority"] = GoalPriority.CRITICAL
        elif any(word in goal_text.lower() for word in ["important", "high priority"]):
            result["priority"] = GoalPriority.HIGH
        elif any(word in goal_text.lower() for word in ["low priority", "when possible", "nice to have"]):
            result["priority"] = GoalPriority.LOW
        
        # Extract completion criteria
        result["criteria"] = self._extract_completion_criteria(goal_text, result["type"])
        
        # Generate intent summary
        result["intent"] = self._summarize_intent(goal_text, result)
        
        return result
    
    def _extract_completion_criteria(self, goal_text: str, goal_type: GoalType) -> List[str]:
        """Extract measurable completion criteria from goal"""
        criteria = []
        
        # Type-specific criteria
        if goal_type == GoalType.PERFORMANCE:
            criteria.extend([
                "Performance metrics improved by measurable amount",
                "No regression in other performance areas",
                "Performance tests passing"
            ])
        elif goal_type == GoalType.FEATURE:
            criteria.extend([
                "Feature fully implemented and functional",
                "Unit tests written and passing",
                "Integration tests passing",
                "Documentation updated"
            ])
        elif goal_type == GoalType.SECURITY:
            criteria.extend([
                "Security vulnerability addressed",
                "Security tests passing",
                "No new vulnerabilities introduced"
            ])
        
        # Extract specific criteria from text
        if "must" in goal_text.lower():
            must_match = re.search(r'must\s+(.+?)(?:\.|$)', goal_text, re.IGNORECASE)
            if must_match:
                criteria.append(f"Must {must_match.group(1)}")
        
        if "should" in goal_text.lower():
            should_match = re.search(r'should\s+(.+?)(?:\.|$)', goal_text, re.IGNORECASE)
            if should_match:
                criteria.append(f"Should {should_match.group(1)}")
        
        return criteria
    
    def _summarize_intent(self, goal_text: str, parsed_info: Dict[str, Any]) -> str:
        """Create a concise summary of the goal intent"""
        keywords = parsed_info.get("keywords", [])
        goal_type = parsed_info["type"].value
        
        # Simple template-based summarization
        if keywords:
            action = keywords[0] if keywords else "achieve"
            target = keywords[1] if len(keywords) > 1 else "goal"
            return f"{action.capitalize()} {target} ({goal_type})"
        
        return f"{goal_type.capitalize()} goal: {goal_text[:50]}..."
    
    async def _analyze_dependencies(self, goal: Goal) -> List[str]:
        """Analyze what other goals this goal depends on"""
        dependencies = []
        
        # Check for explicit dependencies in goal text
        dep_patterns = [
            r"after\s+(.+?)(?:\s+is|$)",
            r"requires\s+(.+?)(?:\s+to|$)",
            r"depends on\s+(.+?)(?:\.|$)",
            r"once\s+(.+?)(?:\s+is|$)"
        ]
        
        for pattern in dep_patterns:
            matches = re.findall(pattern, goal.original_text, re.IGNORECASE)
            for match in matches:
                # Try to find existing goals that match
                for existing_goal_id, existing_goal in self.goals.items():
                    if match.lower() in existing_goal.original_text.lower():
                        dependencies.append(existing_goal_id)
        
        # Infer dependencies based on goal type and content
        if goal.type == GoalType.DEPLOYMENT:
            # Deployment typically depends on testing
            for g_id, g in self.goals.items():
                if g.type == GoalType.TESTING and g.status != GoalStatus.COMPLETED:
                    dependencies.append(g_id)
        
        return list(set(dependencies))  # Remove duplicates
    
    async def _generate_strategies(self, goal: Goal) -> List[Strategy]:
        """Generate multiple strategies to achieve the goal"""
        strategies = []
        
        # Quick Win Strategy - Minimal viable solution
        quick_strategy = await self._generate_quick_win_strategy(goal)
        if quick_strategy:
            strategies.append(quick_strategy)
        
        # Comprehensive Strategy - Full solution with all bells and whistles
        comprehensive_strategy = await self._generate_comprehensive_strategy(goal)
        if comprehensive_strategy:
            strategies.append(comprehensive_strategy)
        
        # Optimal Strategy - Best balance of time, quality, and completeness
        optimal_strategy = await self._generate_optimal_strategy(goal)
        if optimal_strategy:
            strategies.append(optimal_strategy)
        
        # Experimental Strategy - Try new approaches
        if goal.type in [GoalType.PERFORMANCE, GoalType.FEATURE]:
            experimental_strategy = await self._generate_experimental_strategy(goal)
            if experimental_strategy:
                strategies.append(experimental_strategy)
        
        return strategies
    
    async def _generate_quick_win_strategy(self, goal: Goal) -> Optional[Strategy]:
        """Generate a minimal viable solution strategy"""
        strategy = Strategy(
            id=self._generate_id("strategy"),
            goal_id=goal.id,
            type=StrategyType.QUICK_WIN,
            description="Minimal implementation focusing on core functionality"
        )
        
        # Generate minimal task set
        if goal.type == GoalType.FEATURE:
            # Use simplified task pattern
            strategy.tasks = [
                Task(
                    id=self._generate_id("task"),
                    description="Implement core functionality only",
                    goal_id=goal.id,
                    estimated_hours=4,
                    complexity=2,
                    required_skills=["programming"]
                ),
                Task(
                    id=self._generate_id("task"),
                    description="Add basic tests",
                    goal_id=goal.id,
                    estimated_hours=2,
                    complexity=1,
                    required_skills=["testing"]
                )
            ]
        elif goal.type == GoalType.PERFORMANCE:
            strategy.tasks = [
                Task(
                    id=self._generate_id("task"),
                    description="Quick performance profiling",
                    goal_id=goal.id,
                    estimated_hours=1,
                    complexity=2,
                    required_skills=["profiling"]
                ),
                Task(
                    id=self._generate_id("task"),
                    description="Apply most impactful optimization",
                    goal_id=goal.id,
                    estimated_hours=3,
                    complexity=3,
                    required_skills=["optimization"]
                )
            ]
        
        # Calculate estimates
        strategy.estimated_duration = sum(task.estimated_hours for task in strategy.tasks)
        strategy.risk_level = 2  # Low risk due to minimal changes
        strategy.success_probability = 0.9
        strategy.trade_offs = {
            "pros": ["Fast implementation", "Low risk", "Quick feedback"],
            "cons": ["Limited functionality", "May need rework", "Technical debt"]
        }
        
        return strategy
    
    async def _generate_comprehensive_strategy(self, goal: Goal) -> Optional[Strategy]:
        """Generate a complete, thorough solution strategy"""
        strategy = Strategy(
            id=self._generate_id("strategy"),
            goal_id=goal.id,
            type=StrategyType.COMPREHENSIVE,
            description="Complete implementation with full testing, documentation, and polish"
        )
        
        # Generate comprehensive task set based on goal type and content
        tasks = []
        
        # Analyze phase
        tasks.append(Task(
            id=self._generate_id("task"),
            description=f"Comprehensive analysis of {goal.parsed_intent}",
            goal_id=goal.id,
            estimated_hours=4,
            complexity=3,
            required_skills=["analysis", "research"]
        ))
        
        # Design phase
        tasks.append(Task(
            id=self._generate_id("task"),
            description="Create detailed design and architecture",
            goal_id=goal.id,
            estimated_hours=6,
            complexity=4,
            required_skills=["architecture", "design"]
        ))
        
        # Implementation phase
        if goal.type == GoalType.FEATURE:
            # Check for matching patterns
            for pattern_name, pattern_tasks in self.task_patterns.items():
                if pattern_name in goal.original_text.lower():
                    for task_desc in pattern_tasks:
                        tasks.append(Task(
                            id=self._generate_id("task"),
                            description=task_desc,
                            goal_id=goal.id,
                            estimated_hours=4,
                            complexity=3,
                            required_skills=["programming"]
                        ))
                    break
            else:
                # Default feature tasks
                impl_tasks = self.domain_knowledge["common_tasks"].get("feature", [])
                for task_desc in impl_tasks[:5]:  # Limit to avoid too many tasks
                    tasks.append(Task(
                        id=self._generate_id("task"),
                        description=task_desc,
                        goal_id=goal.id,
                        estimated_hours=4,
                        complexity=3,
                        required_skills=["programming"]
                    ))
        
        # Testing phase
        tasks.extend([
            Task(
                id=self._generate_id("task"),
                description="Write comprehensive unit tests",
                goal_id=goal.id,
                estimated_hours=6,
                complexity=3,
                required_skills=["testing"]
            ),
            Task(
                id=self._generate_id("task"),
                description="Create integration tests",
                goal_id=goal.id,
                estimated_hours=4,
                complexity=3,
                required_skills=["testing"]
            ),
            Task(
                id=self._generate_id("task"),
                description="Perform end-to-end testing",
                goal_id=goal.id,
                estimated_hours=3,
                complexity=2,
                required_skills=["testing"]
            )
        ])
        
        # Documentation phase
        tasks.append(Task(
            id=self._generate_id("task"),
            description="Create comprehensive documentation",
            goal_id=goal.id,
            estimated_hours=4,
            complexity=2,
            required_skills=["documentation"]
        ))
        
        # Set task dependencies
        for i in range(1, len(tasks)):
            tasks[i].dependencies = [tasks[i-1].id]
        
        strategy.tasks = tasks
        strategy.estimated_duration = sum(task.estimated_hours for task in tasks)
        strategy.risk_level = 3  # Medium risk due to complexity
        strategy.success_probability = 0.85
        strategy.trade_offs = {
            "pros": ["Complete solution", "High quality", "Well tested", "Maintainable"],
            "cons": ["Time consuming", "Higher complexity", "More resources needed"]
        }
        
        return strategy
    
    async def _generate_optimal_strategy(self, goal: Goal) -> Optional[Strategy]:
        """Generate an optimal balance strategy"""
        strategy = Strategy(
            id=self._generate_id("strategy"),
            goal_id=goal.id,
            type=StrategyType.OPTIMAL,
            description="Balanced approach optimizing for value delivery and quality"
        )
        
        # Take best elements from quick and comprehensive
        tasks = []
        
        # Start with analysis but shorter
        tasks.append(Task(
            id=self._generate_id("task"),
            description=f"Focused analysis of {goal.parsed_intent}",
            goal_id=goal.id,
            estimated_hours=2,
            complexity=3,
            required_skills=["analysis"]
        ))
        
        # Core implementation
        if goal.type == GoalType.FEATURE:
            tasks.extend([
                Task(
                    id=self._generate_id("task"),
                    description="Design core architecture",
                    goal_id=goal.id,
                    estimated_hours=3,
                    complexity=3,
                    required_skills=["architecture"]
                ),
                Task(
                    id=self._generate_id("task"),
                    description="Implement core features with extensibility",
                    goal_id=goal.id,
                    estimated_hours=8,
                    complexity=3,
                    required_skills=["programming"]
                ),
                Task(
                    id=self._generate_id("task"),
                    description="Add essential tests (80% coverage)",
                    goal_id=goal.id,
                    estimated_hours=4,
                    complexity=2,
                    required_skills=["testing"]
                ),
                Task(
                    id=self._generate_id("task"),
                    description="Create essential documentation",
                    goal_id=goal.id,
                    estimated_hours=2,
                    complexity=2,
                    required_skills=["documentation"]
                )
            ])
        elif goal.type == GoalType.PERFORMANCE:
            tasks.extend([
                Task(
                    id=self._generate_id("task"),
                    description="Profile and identify top 3 bottlenecks",
                    goal_id=goal.id,
                    estimated_hours=3,
                    complexity=3,
                    required_skills=["profiling"]
                ),
                Task(
                    id=self._generate_id("task"),
                    description="Implement targeted optimizations",
                    goal_id=goal.id,
                    estimated_hours=6,
                    complexity=4,
                    required_skills=["optimization"]
                ),
                Task(
                    id=self._generate_id("task"),
                    description="Add performance benchmarks",
                    goal_id=goal.id,
                    estimated_hours=2,
                    complexity=2,
                    required_skills=["testing"]
                )
            ])
        
        strategy.tasks = tasks
        strategy.estimated_duration = sum(task.estimated_hours for task in tasks)
        strategy.risk_level = 2
        strategy.success_probability = 0.9
        strategy.trade_offs = {
            "pros": ["Good balance", "Reasonable timeline", "Quality output", "Extensible"],
            "cons": ["Some features deferred", "Not exhaustive testing"]
        }
        
        return strategy
    
    async def _generate_experimental_strategy(self, goal: Goal) -> Optional[Strategy]:
        """Generate a strategy using experimental or cutting-edge approaches"""
        strategy = Strategy(
            id=self._generate_id("strategy"),
            goal_id=goal.id,
            type=StrategyType.EXPERIMENTAL,
            description="Innovative approach using latest techniques and technologies"
        )
        
        tasks = []
        
        if goal.type == GoalType.PERFORMANCE:
            tasks.extend([
                Task(
                    id=self._generate_id("task"),
                    description="Research cutting-edge optimization techniques",
                    goal_id=goal.id,
                    estimated_hours=4,
                    complexity=4,
                    required_skills=["research"]
                ),
                Task(
                    id=self._generate_id("task"),
                    description="Prototype ML-based performance prediction",
                    goal_id=goal.id,
                    estimated_hours=8,
                    complexity=5,
                    required_skills=["machine learning", "programming"]
                ),
                Task(
                    id=self._generate_id("task"),
                    description="Implement adaptive optimization system",
                    goal_id=goal.id,
                    estimated_hours=12,
                    complexity=5,
                    required_skills=["programming", "algorithms"]
                )
            ])
        elif goal.type == GoalType.FEATURE:
            tasks.extend([
                Task(
                    id=self._generate_id("task"),
                    description="Research state-of-the-art implementations",
                    goal_id=goal.id,
                    estimated_hours=3,
                    complexity=3,
                    required_skills=["research"]
                ),
                Task(
                    id=self._generate_id("task"),
                    description="Prototype using emerging technologies",
                    goal_id=goal.id,
                    estimated_hours=6,
                    complexity=4,
                    required_skills=["programming", "innovation"]
                ),
                Task(
                    id=self._generate_id("task"),
                    description="Implement with future-proof architecture",
                    goal_id=goal.id,
                    estimated_hours=10,
                    complexity=4,
                    required_skills=["architecture", "programming"]
                )
            ])
        
        strategy.tasks = tasks
        strategy.estimated_duration = sum(task.estimated_hours for task in tasks)
        strategy.risk_level = 4  # Higher risk
        strategy.success_probability = 0.7
        strategy.trade_offs = {
            "pros": ["Innovative solution", "Future-proof", "Competitive advantage"],
            "cons": ["Higher risk", "Longer timeline", "May need fallback"]
        }
        
        return strategy
    
    def _score_strategy(self, strategy: Strategy, goal: Goal) -> float:
        """Score a strategy based on multiple factors"""
        score = 0.0
        
        # Time efficiency (inverse relationship)
        time_score = 100 / (strategy.estimated_duration + 1)
        score += time_score * 0.3
        
        # Success probability
        score += strategy.success_probability * 100 * 0.3
        
        # Risk assessment (inverse)
        risk_score = 100 / strategy.risk_level
        score += risk_score * 0.2
        
        # Priority alignment
        priority_multiplier = goal.priority.value / 5
        score *= (1 + priority_multiplier * 0.2)
        
        # Type-specific scoring
        if goal.type == GoalType.PERFORMANCE and strategy.type == StrategyType.OPTIMAL:
            score *= 1.1  # Prefer optimal for performance
        elif goal.type == GoalType.BUGFIX and strategy.type == StrategyType.QUICK_WIN:
            score *= 1.2  # Prefer quick fixes for bugs
        
        # Context-based adjustments
        if "urgent" in goal.original_text.lower() and strategy.type == StrategyType.QUICK_WIN:
            score *= 1.3
        
        return round(score, 2)
    
    def select_strategy(self, goal_id: str, strategy_id: str) -> bool:
        """Select a specific strategy for a goal"""
        if goal_id not in self.goals:
            return False
        
        goal = self.goals[goal_id]
        strategy_found = False
        
        for strategy in goal.strategies:
            if strategy.id == strategy_id:
                goal.selected_strategy_id = strategy_id
                strategy_found = True
                break
        
        if strategy_found:
            goal.status = GoalStatus.IN_PROGRESS
            goal.updated_at = datetime.now()
            self._save_goal(goal)
            return True
        
        return False
    
    def get_tasks_for_execution(self, goal_id: str) -> List[Task]:
        """Get ordered tasks for the selected strategy"""
        if goal_id not in self.goals:
            return []
        
        goal = self.goals[goal_id]
        if not goal.selected_strategy_id:
            return []
        
        # Find selected strategy
        selected_strategy = None
        for strategy in goal.strategies:
            if strategy.id == goal.selected_strategy_id:
                selected_strategy = strategy
                break
        
        if not selected_strategy:
            return []
        
        # Order tasks by dependencies
        return self._order_tasks_by_dependencies(selected_strategy.tasks)
    
    def _order_tasks_by_dependencies(self, tasks: List[Task]) -> List[Task]:
        """Order tasks respecting dependencies using topological sort"""
        # Create a graph
        task_graph = nx.DiGraph()
        task_map = {task.id: task for task in tasks}
        
        # Add nodes
        for task in tasks:
            task_graph.add_node(task.id)
        
        # Add edges based on dependencies
        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id in task_map:
                    task_graph.add_edge(dep_id, task.id)
        
        # Topological sort
        try:
            ordered_ids = list(nx.topological_sort(task_graph))
            return [task_map[task_id] for task_id in ordered_ids if task_id in task_map]
        except nx.NetworkXError:
            # Cycle detected, return original order
            logger.warning("Dependency cycle detected, returning original order")
            return tasks
    
    def update_task_progress(self, task_id: str, progress: float, status: str = None):
        """Update progress for a specific task"""
        # Find the task across all goals and strategies
        for goal in self.goals.values():
            for strategy in goal.strategies:
                for task in strategy.tasks:
                    if task.id == task_id:
                        task.progress = progress
                        if status:
                            task.status = status
                        
                        # Update goal progress
                        self._update_goal_progress(goal)
                        self._save_goal(goal)
                        return
    
    def _update_goal_progress(self, goal: Goal):
        """Update overall goal progress based on task completion"""
        if not goal.selected_strategy_id:
            return
        
        # Find selected strategy
        selected_strategy = None
        for strategy in goal.strategies:
            if strategy.id == goal.selected_strategy_id:
                selected_strategy = strategy
                break
        
        if not selected_strategy or not selected_strategy.tasks:
            return
        
        # Calculate average progress
        total_progress = sum(task.progress for task in selected_strategy.tasks)
        goal.progress = total_progress / len(selected_strategy.tasks)
        
        # Update status based on progress
        if goal.progress >= 100:
            goal.status = GoalStatus.COMPLETED
        elif goal.progress > 0:
            goal.status = GoalStatus.IN_PROGRESS
        
        goal.updated_at = datetime.now()
    
    def handle_goal_conflict(self, goal1_id: str, goal2_id: str) -> Dict[str, Any]:
        """Analyze and resolve conflicts between goals"""
        if goal1_id not in self.goals or goal2_id not in self.goals:
            return {"error": "One or both goals not found"}
        
        goal1 = self.goals[goal1_id]
        goal2 = self.goals[goal2_id]
        
        conflicts = []
        resolutions = []
        
        # Check for resource conflicts
        skills1 = set()
        skills2 = set()
        
        for strategy in goal1.strategies:
            if strategy.id == goal1.selected_strategy_id:
                for task in strategy.tasks:
                    skills1.update(task.required_skills)
        
        for strategy in goal2.strategies:
            if strategy.id == goal2.selected_strategy_id:
                for task in strategy.tasks:
                    skills2.update(task.required_skills)
        
        skill_overlap = skills1.intersection(skills2)
        if skill_overlap:
            conflicts.append({
                "type": "resource",
                "description": f"Both goals require: {', '.join(skill_overlap)}"
            })
            resolutions.append({
                "approach": "sequential",
                "description": "Execute goals sequentially based on priority"
            })
        
        # Check for logical conflicts
        if goal1.type == GoalType.PERFORMANCE and goal2.type == GoalType.FEATURE:
            conflicts.append({
                "type": "logical",
                "description": "Performance optimization may conflict with new features"
            })
            resolutions.append({
                "approach": "staged",
                "description": "Implement features first, then optimize"
            })
        
        # Priority-based resolution
        if goal1.priority.value > goal2.priority.value:
            resolutions.append({
                "approach": "priority",
                "description": f"Prioritize '{goal1.parsed_intent}' over '{goal2.parsed_intent}'"
            })
        
        return {
            "conflicts": conflicts,
            "resolutions": resolutions,
            "recommendation": resolutions[0] if resolutions else None
        }
    
    def get_goal_report(self, goal_id: str) -> Dict[str, Any]:
        """Generate a comprehensive report for a goal"""
        if goal_id not in self.goals:
            return {"error": "Goal not found"}
        
        goal = self.goals[goal_id]
        
        # Find selected strategy details
        selected_strategy = None
        for strategy in goal.strategies:
            if strategy.id == goal.selected_strategy_id:
                selected_strategy = strategy
                break
        
        report = {
            "goal": {
                "id": goal.id,
                "original_text": goal.original_text,
                "type": goal.type.value,
                "priority": goal.priority.name,
                "status": goal.status.value,
                "progress": f"{goal.progress:.1f}%",
                "created": goal.created_at.isoformat(),
                "updated": goal.updated_at.isoformat()
            },
            "selected_strategy": None,
            "alternative_strategies": [],
            "tasks": [],
            "dependencies": [],
            "estimated_completion": None
        }
        
        if selected_strategy:
            report["selected_strategy"] = {
                "type": selected_strategy.type.value,
                "description": selected_strategy.description,
                "estimated_hours": selected_strategy.estimated_duration,
                "risk_level": selected_strategy.risk_level,
                "success_probability": f"{selected_strategy.success_probability * 100:.0f}%"
            }
            
            # Task details
            report["tasks"] = [
                {
                    "description": task.description,
                    "status": task.status,
                    "progress": f"{task.progress:.0f}%",
                    "estimated_hours": task.estimated_hours,
                    "complexity": task.complexity
                }
                for task in selected_strategy.tasks
            ]
            
            # Estimate completion
            remaining_hours = sum(
                task.estimated_hours * (1 - task.progress / 100)
                for task in selected_strategy.tasks
            )
            report["estimated_completion"] = f"{remaining_hours:.1f} hours remaining"
        
        # Alternative strategies summary
        for strategy in goal.strategies:
            if strategy.id != goal.selected_strategy_id:
                report["alternative_strategies"].append({
                    "type": strategy.type.value,
                    "score": strategy.score,
                    "estimated_hours": strategy.estimated_duration
                })
        
        # Dependencies
        report["dependencies"] = [
            {
                "goal_id": dep_id,
                "status": self.goals[dep_id].status.value if dep_id in self.goals else "unknown"
            }
            for dep_id in goal.dependencies
        ]
        
        return report
    
    def _update_goal_graph(self, goal: Goal):
        """Update the goal dependency graph"""
        self.goal_graph.add_node(goal.id, goal=goal)
        
        for dep_id in goal.dependencies:
            if dep_id in self.goals:
                self.goal_graph.add_edge(dep_id, goal.id)
    
    def get_execution_order(self) -> List[str]:
        """Get optimal execution order considering all goal dependencies"""
        try:
            return list(nx.topological_sort(self.goal_graph))
        except nx.NetworkXError:
            logger.warning("Cycle in goal dependencies detected")
            # Return goals sorted by priority
            return sorted(
                self.goals.keys(),
                key=lambda g_id: self.goals[g_id].priority.value,
                reverse=True
            )
    
    def _save_goal(self, goal: Goal):
        """Save goal to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Save goal
        cursor.execute('''
            INSERT OR REPLACE INTO goals 
            (id, original_text, parsed_intent, type, priority, status, 
             selected_strategy_id, context, created_at, updated_at, progress)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            goal.id, goal.original_text, goal.parsed_intent,
            goal.type.value, goal.priority.value, goal.status.value,
            goal.selected_strategy_id, json.dumps(goal.context),
            goal.created_at, goal.updated_at, goal.progress
        ))
        
        # Save strategies
        for strategy in goal.strategies:
            cursor.execute('''
                INSERT OR REPLACE INTO strategies
                (id, goal_id, type, description, estimated_duration,
                 risk_level, success_probability, trade_offs, score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                strategy.id, strategy.goal_id, strategy.type.value,
                strategy.description, strategy.estimated_duration,
                strategy.risk_level, strategy.success_probability,
                json.dumps(strategy.trade_offs), strategy.score
            ))
            
            # Save tasks
            for task in strategy.tasks:
                cursor.execute('''
                    INSERT OR REPLACE INTO tasks
                    (id, description, goal_id, strategy_id, dependencies,
                     estimated_hours, complexity, required_skills, status,
                     progress, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task.id, task.description, task.goal_id, strategy.id,
                    json.dumps(task.dependencies), task.estimated_hours,
                    task.complexity, json.dumps(task.required_skills),
                    task.status, task.progress, json.dumps(task.metadata)
                ))
        
        # Save dependencies
        cursor.execute('DELETE FROM goal_dependencies WHERE goal_id = ?', (goal.id,))
        for dep_id in goal.dependencies:
            cursor.execute('''
                INSERT INTO goal_dependencies (goal_id, dependency_id)
                VALUES (?, ?)
            ''', (goal.id, dep_id))
        
        conn.commit()
        conn.close()
    
    def _load_goals_from_db(self):
        """Load all goals from database on startup"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Load goals
        cursor.execute('SELECT * FROM goals')
        goal_rows = cursor.fetchall()
        
        for row in goal_rows:
            goal = Goal(
                id=row[0],
                original_text=row[1],
                parsed_intent=row[2],
                type=GoalType(row[3]),
                priority=GoalPriority(row[4]),
                status=GoalStatus(row[5]),
                selected_strategy_id=row[6],
                context=json.loads(row[7]) if row[7] else {},
                created_at=datetime.fromisoformat(row[8]) if row[8] else datetime.now(),
                updated_at=datetime.fromisoformat(row[9]) if row[9] else datetime.now(),
                progress=row[10] or 0.0
            )
            
            # Load strategies for this goal
            cursor.execute('SELECT * FROM strategies WHERE goal_id = ?', (goal.id,))
            strategy_rows = cursor.fetchall()
            
            for strat_row in strategy_rows:
                strategy = Strategy(
                    id=strat_row[0],
                    goal_id=strat_row[1],
                    type=StrategyType(strat_row[2]),
                    description=strat_row[3],
                    estimated_duration=strat_row[4],
                    risk_level=strat_row[5],
                    success_probability=strat_row[6],
                    trade_offs=json.loads(strat_row[7]) if strat_row[7] else {},
                    score=strat_row[8] or 0.0
                )
                
                # Load tasks for this strategy
                cursor.execute('SELECT * FROM tasks WHERE strategy_id = ?', (strategy.id,))
                task_rows = cursor.fetchall()
                
                for task_row in task_rows:
                    task = Task(
                        id=task_row[0],
                        description=task_row[1],
                        goal_id=task_row[2],
                        dependencies=json.loads(task_row[4]) if task_row[4] else [],
                        estimated_hours=task_row[5],
                        complexity=task_row[6],
                        required_skills=json.loads(task_row[7]) if task_row[7] else [],
                        status=task_row[8],
                        progress=task_row[9] or 0.0,
                        metadata=json.loads(task_row[10]) if task_row[10] else {}
                    )
                    strategy.tasks.append(task)
                
                goal.strategies.append(strategy)
            
            # Load dependencies
            cursor.execute('SELECT dependency_id FROM goal_dependencies WHERE goal_id = ?', (goal.id,))
            dep_rows = cursor.fetchall()
            goal.dependencies = [row[0] for row in dep_rows]
            
            self.goals[goal.id] = goal
            self._update_goal_graph(goal)
        
        conn.close()
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID"""
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
    
    async def export_to_manus_queue(self, goal_id: str) -> Dict[str, Any]:
        """Export goal tasks to MANUS task queue format"""
        if goal_id not in self.goals:
            return {"error": "Goal not found"}
        
        tasks = self.get_tasks_for_execution(goal_id)
        if not tasks:
            return {"error": "No tasks to export"}
        
        manus_tasks = []
        for task in tasks:
            manus_task = {
                "id": task.id,
                "name": task.description,
                "description": f"Task for goal: {self.goals[goal_id].parsed_intent}",
                "priority": self.goals[goal_id].priority.value,
                "dependencies": task.dependencies,
                "metadata": {
                    "goal_id": goal_id,
                    "estimated_hours": task.estimated_hours,
                    "complexity": task.complexity,
                    "required_skills": task.required_skills,
                    "nexus_task_id": task.id
                }
            }
            manus_tasks.append(manus_task)
        
        return {
            "goal_id": goal_id,
            "goal_description": self.goals[goal_id].parsed_intent,
            "tasks": manus_tasks,
            "total_tasks": len(manus_tasks),
            "estimated_total_hours": sum(task.estimated_hours for task in tasks)
        }


# Example usage and testing
async def main():
    """Example usage of the Goal Reasoning System"""
    system = GoalReasoningSystem()
    
    # Example 1: Performance goal
    goal1 = await system.process_goal(
        "Make my application faster by optimizing database queries and reducing load time",
        context={"application": "web_app", "current_load_time": 3.5}
    )
    
    print(f"\nGoal 1: {goal1.parsed_intent}")
    print(f"Type: {goal1.type.value}")
    print(f"Priority: {goal1.priority.name}")
    print(f"Strategies available: {len(goal1.strategies)}")
    
    for strategy in goal1.strategies:
        print(f"\n  Strategy: {strategy.type.value} (Score: {strategy.score})")
        print(f"  Duration: {strategy.estimated_duration} hours")
        print(f"  Tasks: {len(strategy.tasks)}")
    
    # Example 2: Feature goal with dependencies
    goal2 = await system.process_goal(
        "Implement user authentication with JWT tokens after the database optimization is complete"
    )
    
    print(f"\n\nGoal 2: {goal2.parsed_intent}")
    print(f"Dependencies: {goal2.dependencies}")
    
    # Select strategy and get tasks
    system.select_strategy(goal1.id, goal1.strategies[0].id)
    tasks = system.get_tasks_for_execution(goal1.id)
    
    print(f"\n\nTasks for execution:")
    for i, task in enumerate(tasks, 1):
        print(f"{i}. {task.description} ({task.estimated_hours}h)")
    
    # Export to MANUS
    manus_export = await system.export_to_manus_queue(goal1.id)
    print(f"\n\nMANUS Export: {manus_export['total_tasks']} tasks ready")
    
    # Get report
    report = system.get_goal_report(goal1.id)
    print(f"\n\nGoal Report:")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())