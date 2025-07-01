#!/usr/bin/env python3
"""
NEXUS Predictive Engine
======================
ML-powered prediction system for anticipating user needs and system requirements.
"""

import asyncio
import json
import logging
import os
import pickle
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict, Counter, deque
from pathlib import Path
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
import joblib
import hashlib
from enum import Enum
import sqlite3
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PredictionType(Enum):
    """Types of predictions"""
    TASK_SEQUENCE = "task_sequence"
    COMPONENT_NEED = "component_need"
    QUESTION = "question"
    MAINTENANCE = "maintenance"
    REQUIREMENT = "requirement"
    ERROR = "error"
    PERFORMANCE = "performance"


@dataclass
class Prediction:
    """Represents a prediction"""
    prediction_type: PredictionType
    timestamp: datetime
    prediction: Any
    confidence: float
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'type': self.prediction_type.value,
            'timestamp': self.timestamp.isoformat(),
            'prediction': self.prediction,
            'confidence': self.confidence,
            'context': self.context,
            'metadata': self.metadata
        }


@dataclass
class TaskPattern:
    """Pattern of tasks"""
    sequence: List[str]
    frequency: int
    avg_duration: float
    next_likely: List[Tuple[str, float]]  # (task, probability)


@dataclass
class UserContext:
    """User context for predictions"""
    user_id: str
    current_task: Optional[str] = None
    recent_tasks: List[str] = field(default_factory=list)
    current_files: List[str] = field(default_factory=list)
    error_history: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    session_start: datetime = field(default_factory=datetime.now)


class TaskSequencePredictor:
    """Predicts likely task sequences"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "models/task_sequence_model.pkl"
        self.sequence_length = 5
        self.min_pattern_frequency = 3
        
        # Pattern storage
        self.task_sequences: List[List[str]] = []
        self.pattern_index: Dict[str, TaskPattern] = {}
        
        # ML model
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_trained = False
        
        # Load existing model if available
        self._load_model()
        
    def add_task_sequence(self, tasks: List[str]):
        """Add observed task sequence"""
        self.task_sequences.append(tasks)
        
        # Update patterns
        self._update_patterns(tasks)
        
        # Retrain periodically
        if len(self.task_sequences) % 100 == 0:
            self.train()
            
    def predict_next_tasks(self, context: UserContext, n: int = 5) -> List[Tuple[str, float]]:
        """Predict next likely tasks"""
        predictions = []
        
        # Pattern-based prediction
        if context.recent_tasks:
            pattern_key = self._get_pattern_key(context.recent_tasks[-self.sequence_length:])
            
            if pattern_key in self.pattern_index:
                pattern = self.pattern_index[pattern_key]
                predictions.extend(pattern.next_likely[:n])
                
        # ML-based prediction if trained
        if self.is_trained and context.recent_tasks:
            ml_predictions = self._ml_predict(context)
            
            # Merge predictions
            prediction_dict = {}
            for task, conf in predictions:
                prediction_dict[task] = conf
                
            for task, conf in ml_predictions:
                if task in prediction_dict:
                    # Average confidence scores
                    prediction_dict[task] = (prediction_dict[task] + conf) / 2
                else:
                    prediction_dict[task] = conf
                    
            predictions = sorted(prediction_dict.items(), key=lambda x: x[1], reverse=True)[:n]
            
        return predictions
    
    def _update_patterns(self, tasks: List[str]):
        """Update task patterns"""
        for i in range(len(tasks) - self.sequence_length):
            sequence = tasks[i:i + self.sequence_length]
            next_task = tasks[i + self.sequence_length]
            
            pattern_key = self._get_pattern_key(sequence)
            
            if pattern_key not in self.pattern_index:
                self.pattern_index[pattern_key] = TaskPattern(
                    sequence=sequence,
                    frequency=0,
                    avg_duration=0,
                    next_likely=[]
                )
                
            pattern = self.pattern_index[pattern_key]
            pattern.frequency += 1
            
            # Update next likely tasks
            next_counts = defaultdict(int)
            for seq in self.task_sequences:
                for j in range(len(seq) - self.sequence_length):
                    if self._get_pattern_key(seq[j:j + self.sequence_length]) == pattern_key:
                        if j + self.sequence_length < len(seq):
                            next_counts[seq[j + self.sequence_length]] += 1
                            
            # Calculate probabilities
            total = sum(next_counts.values())
            if total > 0:
                pattern.next_likely = [
                    (task, count / total)
                    for task, count in sorted(next_counts.items(), key=lambda x: x[1], reverse=True)
                ]
                
    def _get_pattern_key(self, sequence: List[str]) -> str:
        """Get unique key for sequence pattern"""
        return '->'.join(sequence)
        
    def _ml_predict(self, context: UserContext) -> List[Tuple[str, float]]:
        """ML-based prediction"""
        try:
            # Prepare features
            text_features = ' '.join(context.recent_tasks[-10:])
            
            # Vectorize
            X = self.vectorizer.transform([text_features])
            
            # Predict probabilities
            probs = self.model.predict_proba(X)[0]
            classes = self.model.classes_
            
            # Get top predictions
            predictions = []
            for i, prob in enumerate(probs):
                if prob > 0.1:  # Threshold
                    predictions.append((classes[i], prob))
                    
            return sorted(predictions, key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            logger.error(f"ML prediction error: {e}")
            return []
            
    def train(self):
        """Train ML model on task sequences"""
        if len(self.task_sequences) < 50:
            return
            
        try:
            # Prepare training data
            X_data = []
            y_data = []
            
            for sequence in self.task_sequences:
                for i in range(len(sequence) - self.sequence_length):
                    # Features: previous tasks
                    features = ' '.join(sequence[i:i + self.sequence_length])
                    X_data.append(features)
                    
                    # Target: next task
                    y_data.append(sequence[i + self.sequence_length])
                    
            # Vectorize
            X = self.vectorizer.fit_transform(X_data)
            
            # Train model
            self.model.fit(X, y_data)
            self.is_trained = True
            
            # Save model
            self._save_model()
            
            logger.info("Task sequence model trained successfully")
            
        except Exception as e:
            logger.error(f"Training error: {e}")
            
    def _save_model(self):
        """Save model to disk"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            model_data = {
                'vectorizer': self.vectorizer,
                'model': self.model,
                'sequences': self.task_sequences,
                'patterns': self.pattern_index,
                'is_trained': self.is_trained
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
                
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            
    def _load_model(self):
        """Load model from disk"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    
                self.vectorizer = model_data['vectorizer']
                self.model = model_data['model']
                self.task_sequences = model_data['sequences']
                self.pattern_index = model_data['patterns']
                self.is_trained = model_data['is_trained']
                
                logger.info("Task sequence model loaded successfully")
                
        except Exception as e:
            logger.error(f"Error loading model: {e}")


class ComponentPredictor:
    """Predicts components that will be needed"""
    
    def __init__(self):
        self.component_patterns: Dict[str, List[str]] = {}
        self.file_associations: Dict[str, Set[str]] = defaultdict(set)
        self.import_graph: Dict[str, Set[str]] = defaultdict(set)
        
        # Pre-generation cache
        self.pre_generated: Dict[str, str] = {}
        self.generation_templates: Dict[str, str] = self._load_templates()
        
    def analyze_project(self, project_path: str):
        """Analyze project to learn component patterns"""
        try:
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.endswith(('.py', '.js', '.tsx', '.java')):
                        file_path = os.path.join(root, file)
                        self._analyze_file(file_path)
                        
        except Exception as e:
            logger.error(f"Error analyzing project: {e}")
            
    def predict_components(self, context: UserContext) -> List[Tuple[str, float]]:
        """Predict components that might be needed"""
        predictions = []
        
        # Based on current files
        for file in context.current_files:
            associated = self.file_associations.get(file, set())
            
            for component in associated:
                if component not in context.current_files:
                    # Calculate confidence based on association strength
                    confidence = len(self.import_graph.get(component, set())) / 10.0
                    confidence = min(confidence, 1.0)
                    
                    predictions.append((component, confidence))
                    
        # Based on current task
        if context.current_task:
            task_components = self._predict_from_task(context.current_task)
            predictions.extend(task_components)
            
        # Remove duplicates and sort by confidence
        seen = set()
        unique_predictions = []
        
        for component, conf in sorted(predictions, key=lambda x: x[1], reverse=True):
            if component not in seen:
                seen.add(component)
                unique_predictions.append((component, conf))
                
        return unique_predictions[:10]
        
    def pre_generate_component(self, component_type: str, context: Dict[str, Any]) -> Optional[str]:
        """Pre-generate a component based on prediction"""
        cache_key = self._get_cache_key(component_type, context)
        
        # Check cache
        if cache_key in self.pre_generated:
            return self.pre_generated[cache_key]
            
        # Generate based on template
        if component_type in self.generation_templates:
            template = self.generation_templates[component_type]
            
            try:
                # Simple template substitution
                generated = template
                for key, value in context.items():
                    generated = generated.replace(f"{{{key}}}", str(value))
                    
                # Cache result
                self.pre_generated[cache_key] = generated
                
                return generated
                
            except Exception as e:
                logger.error(f"Error generating component: {e}")
                
        return None
        
    def _analyze_file(self, file_path: str):
        """Analyze file for component patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract imports
            imports = self._extract_imports(content, file_path)
            
            # Build associations
            base_name = os.path.basename(file_path)
            
            for imp in imports:
                self.file_associations[base_name].add(imp)
                self.import_graph[imp].add(base_name)
                
        except Exception as e:
            logger.debug(f"Error analyzing file {file_path}: {e}")
            
    def _extract_imports(self, content: str, file_path: str) -> List[str]:
        """Extract imports from file content"""
        imports = []
        
        if file_path.endswith('.py'):
            # Python imports
            patterns = [
                r'from\s+(\S+)\s+import',
                r'import\s+(\S+)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                imports.extend(matches)
                
        elif file_path.endswith(('.js', '.tsx')):
            # JavaScript imports
            patterns = [
                r"import\s+.*from\s+['\"](.+)['\"]",
                r"require\(['\"](.+)['\"]\)"
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                imports.extend(matches)
                
        return imports
        
    def _predict_from_task(self, task: str) -> List[Tuple[str, float]]:
        """Predict components based on task description"""
        predictions = []
        
        # Keywords to component mapping
        keyword_components = {
            'api': [('api_client.py', 0.8), ('api_routes.py', 0.7)],
            'database': [('db_models.py', 0.9), ('db_connection.py', 0.8)],
            'test': [('test_utils.py', 0.8), ('fixtures.py', 0.7)],
            'ui': [('components.tsx', 0.8), ('styles.css', 0.7)],
            'auth': [('auth_middleware.py', 0.9), ('auth_utils.py', 0.8)],
            'config': [('config.py', 0.9), ('settings.json', 0.7)]
        }
        
        task_lower = task.lower()
        
        for keyword, components in keyword_components.items():
            if keyword in task_lower:
                predictions.extend(components)
                
        return predictions
        
    def _get_cache_key(self, component_type: str, context: Dict[str, Any]) -> str:
        """Generate cache key for pre-generated component"""
        context_str = json.dumps(context, sort_keys=True)
        return hashlib.md5(f"{component_type}:{context_str}".encode()).hexdigest()
        
    def _load_templates(self) -> Dict[str, str]:
        """Load component generation templates"""
        templates = {
            'python_class': '''class {class_name}:
    """
    {description}
    """
    
    def __init__(self):
        pass
        
    def {method_name}(self):
        """TODO: Implement {method_name}"""
        pass
''',
            
            'react_component': '''import React from 'react';

interface {component_name}Props {{
    // TODO: Define props
}}

export const {component_name}: React.FC<{component_name}Props> = (props) => {{
    return (
        <div>
            <h2>{component_name}</h2>
            {{/* TODO: Implement component */}}
        </div>
    );
}};
''',
            
            'test_file': '''import pytest
from {module} import {class_name}

class Test{class_name}:
    """Test cases for {class_name}"""
    
    def test_{method_name}(self):
        """Test {method_name} functionality"""
        # TODO: Implement test
        assert True
'''
        }
        
        return templates


class QuestionPredictor:
    """Predicts questions users might ask"""
    
    def __init__(self):
        self.question_patterns: List[Tuple[str, List[str]]] = []
        self.context_questions: Dict[str, List[str]] = defaultdict(list)
        self.followup_map: Dict[str, List[str]] = {}
        
        # Initialize with common patterns
        self._initialize_patterns()
        
    def predict_questions(self, context: UserContext) -> List[Tuple[str, float]]:
        """Predict likely questions"""
        predictions = []
        
        # Based on current task
        if context.current_task:
            task_questions = self._get_task_questions(context.current_task)
            for q in task_questions:
                predictions.append((q, 0.8))
                
        # Based on recent errors
        if context.error_history:
            error_questions = self._get_error_questions(context.error_history[-1])
            for q in error_questions:
                predictions.append((q, 0.9))
                
        # Based on files
        for file in context.current_files:
            file_questions = self._get_file_questions(file)
            for q in file_questions:
                predictions.append((q, 0.7))
                
        # Remove duplicates
        seen = set()
        unique_predictions = []
        
        for question, conf in sorted(predictions, key=lambda x: x[1], reverse=True):
            if question not in seen:
                seen.add(question)
                unique_predictions.append((question, conf))
                
        return unique_predictions[:5]
        
    def add_question_answer(self, question: str, answer: str, context: UserContext):
        """Learn from question-answer pairs"""
        # Store context-question association
        if context.current_task:
            self.context_questions[context.current_task].append(question)
            
        # Extract potential follow-up questions
        followups = self._extract_followups(answer)
        if followups:
            self.followup_map[question] = followups
            
    def _initialize_patterns(self):
        """Initialize common question patterns"""
        self.question_patterns = [
            ('error', [
                "What does this error mean?",
                "How do I fix this error?",
                "Why am I getting this error?"
            ]),
            ('setup', [
                "How do I set this up?",
                "What are the requirements?",
                "How do I install dependencies?"
            ]),
            ('implementation', [
                "How should I implement this?",
                "What's the best approach?",
                "Can you show me an example?"
            ]),
            ('testing', [
                "How do I test this?",
                "What test cases should I write?",
                "How do I run the tests?"
            ]),
            ('deployment', [
                "How do I deploy this?",
                "What are the deployment steps?",
                "How do I configure for production?"
            ])
        ]
        
    def _get_task_questions(self, task: str) -> List[str]:
        """Get questions related to task"""
        questions = []
        task_lower = task.lower()
        
        for pattern, pattern_questions in self.question_patterns:
            if pattern in task_lower:
                questions.extend(pattern_questions)
                
        # Add learned questions
        if task in self.context_questions:
            questions.extend(self.context_questions[task][:3])
            
        return questions
        
    def _get_error_questions(self, error: str) -> List[str]:
        """Get questions related to error"""
        questions = [
            f"How do I fix: {error[:50]}...?",
            "What causes this error?",
            "Is there a workaround?"
        ]
        
        return questions
        
    def _get_file_questions(self, file: str) -> List[str]:
        """Get questions related to file"""
        questions = []
        
        if file.endswith('.py'):
            questions.extend([
                "How do I run this Python file?",
                "What does this module do?"
            ])
        elif file.endswith(('.js', '.tsx')):
            questions.extend([
                "How do I build this component?",
                "What props does this accept?"
            ])
        elif file.endswith('.md'):
            questions.extend([
                "Can you summarize this documentation?",
                "What are the key points?"
            ])
            
        return questions
        
    def _extract_followups(self, answer: str) -> List[str]:
        """Extract potential follow-up questions from answer"""
        followups = []
        
        # Look for question indicators
        if "you might also want to" in answer.lower():
            followups.append("What else should I consider?")
            
        if "alternatively" in answer.lower():
            followups.append("What are the other alternatives?")
            
        if "make sure" in answer.lower():
            followups.append("What should I verify?")
            
        return followups


class MaintenancePredictor:
    """Predicts maintenance needs"""
    
    def __init__(self):
        self.failure_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self.maintenance_history: List[Dict[str, Any]] = []
        self.mtbf_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        self.is_trained = False
        
    def add_failure(self, component: str, timestamp: datetime, error_type: str):
        """Record a failure event"""
        self.failure_patterns[component].append(timestamp)
        
        self.maintenance_history.append({
            'component': component,
            'timestamp': timestamp,
            'error_type': error_type
        })
        
        # Retrain model periodically
        if len(self.maintenance_history) % 50 == 0:
            self.train()
            
    def predict_maintenance(self, components: List[str]) -> List[Tuple[str, datetime, float]]:
        """Predict maintenance needs for components"""
        predictions = []
        
        for component in components:
            # Pattern-based prediction
            if component in self.failure_patterns:
                pattern_prediction = self._predict_from_pattern(component)
                if pattern_prediction:
                    predictions.append(pattern_prediction)
                    
            # ML-based prediction if trained
            if self.is_trained:
                ml_prediction = self._ml_predict_failure(component)
                if ml_prediction:
                    predictions.append(ml_prediction)
                    
        # Sort by urgency (soonest first)
        predictions.sort(key=lambda x: x[1])
        
        return predictions[:10]
        
    def _predict_from_pattern(self, component: str) -> Optional[Tuple[str, datetime, float]]:
        """Predict based on failure patterns"""
        failures = self.failure_patterns.get(component, [])
        
        if len(failures) < 2:
            return None
            
        # Calculate mean time between failures
        intervals = []
        for i in range(1, len(failures)):
            interval = (failures[i] - failures[i-1]).total_seconds() / 3600  # hours
            intervals.append(interval)
            
        mtbf = np.mean(intervals)
        std_dev = np.std(intervals)
        
        # Predict next failure
        last_failure = failures[-1]
        predicted_time = last_failure + timedelta(hours=mtbf)
        
        # Calculate confidence based on consistency
        confidence = 1.0 - (std_dev / mtbf if mtbf > 0 else 0)
        confidence = max(0.1, min(confidence, 0.95))
        
        return (component, predicted_time, confidence)
        
    def _ml_predict_failure(self, component: str) -> Optional[Tuple[str, datetime, float]]:
        """ML-based failure prediction"""
        try:
            # Prepare features
            features = self._extract_features(component)
            
            if features is None:
                return None
                
            # Predict time to failure (hours)
            X = np.array([features])
            hours_to_failure = self.mtbf_model.predict(X)[0]
            
            # Calculate predicted time
            predicted_time = datetime.now() + timedelta(hours=hours_to_failure)
            
            # Estimate confidence (simplified)
            confidence = 0.7  # Base confidence for ML predictions
            
            return (component, predicted_time, confidence)
            
        except Exception as e:
            logger.error(f"ML prediction error: {e}")
            return None
            
    def _extract_features(self, component: str) -> Optional[List[float]]:
        """Extract features for ML model"""
        features = []
        
        # Component age (days since first failure)
        failures = self.failure_patterns.get(component, [])
        if not failures:
            return None
            
        age = (datetime.now() - failures[0]).days
        features.append(age)
        
        # Failure frequency
        failure_rate = len(failures) / max(age, 1)
        features.append(failure_rate)
        
        # Recent failure count (last 30 days)
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_failures = sum(1 for f in failures if f > recent_cutoff)
        features.append(recent_failures)
        
        # Time since last failure (hours)
        time_since_last = (datetime.now() - failures[-1]).total_seconds() / 3600
        features.append(time_since_last)
        
        # Component type encoding (simplified)
        component_type = 1 if 'service' in component else 0
        features.append(component_type)
        
        return features
        
    def train(self):
        """Train ML model"""
        if len(self.maintenance_history) < 20:
            return
            
        try:
            # Prepare training data
            X_data = []
            y_data = []
            
            # Group by component
            component_failures = defaultdict(list)
            for event in self.maintenance_history:
                component_failures[event['component']].append(event['timestamp'])
                
            # Create training samples
            for component, failures in component_failures.items():
                if len(failures) < 2:
                    continue
                    
                for i in range(1, len(failures)):
                    # Features at time of previous failure
                    features = self._extract_features_at_time(component, failures[i-1])
                    if features:
                        X_data.append(features)
                        
                        # Target: time to next failure (hours)
                        time_to_failure = (failures[i] - failures[i-1]).total_seconds() / 3600
                        y_data.append(time_to_failure)
                        
            if len(X_data) < 10:
                return
                
            # Train model
            X = np.array(X_data)
            y = np.array(y_data)
            
            self.mtbf_model.fit(X, y)
            self.is_trained = True
            
            logger.info("Maintenance prediction model trained successfully")
            
        except Exception as e:
            logger.error(f"Training error: {e}")
            
    def _extract_features_at_time(self, component: str, timestamp: datetime) -> Optional[List[float]]:
        """Extract features at specific time"""
        # Similar to _extract_features but calculated at historical timestamp
        # Simplified for brevity
        return self._extract_features(component)


class RequirementPredictor:
    """Predicts future requirements"""
    
    def __init__(self):
        self.requirement_history: List[Dict[str, Any]] = []
        self.requirement_patterns: Dict[str, List[str]] = defaultdict(list)
        self.technology_trends: Dict[str, float] = {}
        
    def add_requirement(self, requirement: str, context: Dict[str, Any]):
        """Add observed requirement"""
        self.requirement_history.append({
            'requirement': requirement,
            'context': context,
            'timestamp': datetime.now()
        })
        
        # Extract patterns
        self._extract_patterns(requirement, context)
        
    def predict_requirements(self, project_context: Dict[str, Any]) -> List[Tuple[str, float]]:
        """Predict future requirements"""
        predictions = []
        
        # Based on project type
        project_type = project_context.get('type', 'generic')
        type_requirements = self._get_type_requirements(project_type)
        
        for req in type_requirements:
            predictions.append((req, 0.7))
            
        # Based on current technologies
        technologies = project_context.get('technologies', [])
        tech_requirements = self._get_tech_requirements(technologies)
        
        for req in tech_requirements:
            predictions.append((req, 0.8))
            
        # Based on patterns
        pattern_requirements = self._get_pattern_requirements(project_context)
        
        for req in pattern_requirements:
            predictions.append((req, 0.6))
            
        # Remove duplicates and sort
        seen = set()
        unique_predictions = []
        
        for req, conf in sorted(predictions, key=lambda x: x[1], reverse=True):
            if req not in seen:
                seen.add(req)
                unique_predictions.append((req, conf))
                
        return unique_predictions[:10]
        
    def _extract_patterns(self, requirement: str, context: Dict[str, Any]):
        """Extract patterns from requirement"""
        # Extract key concepts
        concepts = self._extract_concepts(requirement)
        
        # Map to context
        for key, value in context.items():
            if isinstance(value, str):
                self.requirement_patterns[value].extend(concepts)
                
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        # Simple keyword extraction
        keywords = []
        
        important_words = [
            'scalability', 'security', 'performance', 'authentication',
            'monitoring', 'logging', 'testing', 'deployment', 'backup',
            'caching', 'api', 'database', 'migration', 'documentation'
        ]
        
        text_lower = text.lower()
        
        for word in important_words:
            if word in text_lower:
                keywords.append(word)
                
        return keywords
        
    def _get_type_requirements(self, project_type: str) -> List[str]:
        """Get requirements based on project type"""
        type_requirements = {
            'web': [
                "Add user authentication system",
                "Implement responsive design",
                "Add API rate limiting",
                "Set up SSL certificates"
            ],
            'mobile': [
                "Add offline support",
                "Implement push notifications",
                "Add biometric authentication",
                "Optimize for battery usage"
            ],
            'api': [
                "Add API versioning",
                "Implement request validation",
                "Add API documentation",
                "Set up rate limiting"
            ],
            'ml': [
                "Add model versioning",
                "Implement data pipeline",
                "Add experiment tracking",
                "Set up model monitoring"
            ]
        }
        
        return type_requirements.get(project_type, [])
        
    def _get_tech_requirements(self, technologies: List[str]) -> List[str]:
        """Get requirements based on technologies"""
        requirements = []
        
        tech_map = {
            'react': ["Add state management", "Implement code splitting"],
            'docker': ["Add container orchestration", "Implement health checks"],
            'kubernetes': ["Add autoscaling", "Implement rolling updates"],
            'postgres': ["Add database backups", "Implement connection pooling"],
            'redis': ["Add cache invalidation", "Implement session management"]
        }
        
        for tech in technologies:
            tech_lower = tech.lower()
            for key, reqs in tech_map.items():
                if key in tech_lower:
                    requirements.extend(reqs)
                    
        return requirements
        
    def _get_pattern_requirements(self, context: Dict[str, Any]) -> List[str]:
        """Get requirements based on patterns"""
        requirements = []
        
        # Analyze patterns
        all_concepts = []
        for concepts in self.requirement_patterns.values():
            all_concepts.extend(concepts)
            
        # Find most common concepts
        concept_counts = Counter(all_concepts)
        
        # Generate requirements for common concepts
        for concept, count in concept_counts.most_common(5):
            if count > 2:
                requirements.append(f"Enhance {concept} capabilities")
                
        return requirements


class ActionPrecomputer:
    """Pre-computes actions based on predictions"""
    
    def __init__(self):
        self.precomputed_actions: Dict[str, Any] = {}
        self.computation_cache: Dict[str, Any] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        self.computation_threads: Dict[str, threading.Thread] = {}
        
    async def precompute_actions(self, predictions: List[Prediction]):
        """Pre-compute actions for predictions"""
        tasks = []
        
        for prediction in predictions:
            if prediction.confidence > 0.7:  # Only high-confidence predictions
                task = asyncio.create_task(
                    self._precompute_single(prediction)
                )
                tasks.append(task)
                
        await asyncio.gather(*tasks, return_exceptions=True)
        
    async def _precompute_single(self, prediction: Prediction):
        """Pre-compute single action"""
        try:
            action_key = self._get_action_key(prediction)
            
            # Check if already computed
            if action_key in self.precomputed_actions:
                if self._is_cache_valid(action_key):
                    return
                    
            # Compute based on prediction type
            if prediction.prediction_type == PredictionType.COMPONENT_NEED:
                result = await self._precompute_component(prediction)
            elif prediction.prediction_type == PredictionType.TASK_SEQUENCE:
                result = await self._precompute_task_setup(prediction)
            elif prediction.prediction_type == PredictionType.MAINTENANCE:
                result = await self._precompute_maintenance(prediction)
            else:
                result = None
                
            if result:
                self.precomputed_actions[action_key] = result
                self.cache_expiry[action_key] = datetime.now() + timedelta(minutes=30)
                
        except Exception as e:
            logger.error(f"Error pre-computing action: {e}")
            
    async def _precompute_component(self, prediction: Prediction) -> Optional[Dict[str, Any]]:
        """Pre-compute component generation"""
        component = prediction.prediction
        
        # Generate component code
        code = self._generate_component_code(component)
        
        # Generate tests
        tests = self._generate_component_tests(component)
        
        # Generate documentation
        docs = self._generate_component_docs(component)
        
        return {
            'component': component,
            'code': code,
            'tests': tests,
            'documentation': docs,
            'timestamp': datetime.now()
        }
        
    async def _precompute_task_setup(self, prediction: Prediction) -> Optional[Dict[str, Any]]:
        """Pre-compute task setup"""
        task = prediction.prediction
        
        # Prepare environment
        env_setup = self._prepare_task_environment(task)
        
        # Load relevant files
        files = self._identify_task_files(task)
        
        # Generate initial code structure
        structure = self._generate_task_structure(task)
        
        return {
            'task': task,
            'environment': env_setup,
            'files': files,
            'structure': structure,
            'timestamp': datetime.now()
        }
        
    async def _precompute_maintenance(self, prediction: Prediction) -> Optional[Dict[str, Any]]:
        """Pre-compute maintenance actions"""
        component, scheduled_time, _ = prediction.prediction
        
        # Generate maintenance script
        script = self._generate_maintenance_script(component)
        
        # Identify backup requirements
        backups = self._identify_backup_needs(component)
        
        # Generate rollback plan
        rollback = self._generate_rollback_plan(component)
        
        return {
            'component': component,
            'scheduled_time': scheduled_time,
            'script': script,
            'backups': backups,
            'rollback': rollback,
            'timestamp': datetime.now()
        }
        
    def get_precomputed_action(self, prediction: Prediction) -> Optional[Any]:
        """Get pre-computed action if available"""
        action_key = self._get_action_key(prediction)
        
        if action_key in self.precomputed_actions:
            if self._is_cache_valid(action_key):
                return self.precomputed_actions[action_key]
                
        return None
        
    def _get_action_key(self, prediction: Prediction) -> str:
        """Generate unique key for action"""
        pred_str = f"{prediction.prediction_type.value}:{prediction.prediction}"
        return hashlib.md5(pred_str.encode()).hexdigest()
        
    def _is_cache_valid(self, action_key: str) -> bool:
        """Check if cached action is still valid"""
        if action_key not in self.cache_expiry:
            return False
            
        return datetime.now() < self.cache_expiry[action_key]
        
    def _generate_component_code(self, component: str) -> str:
        """Generate component code"""
        # Simplified code generation
        if component.endswith('.py'):
            return f'''"""
{component} - Auto-generated component
"""

class {component.replace('.py', '').title()}:
    """TODO: Implement {component}"""
    
    def __init__(self):
        pass
'''
        
        return f"// TODO: Implement {component}"
        
    def _generate_component_tests(self, component: str) -> str:
        """Generate component tests"""
        return f'''"""
Tests for {component}
"""

import pytest

def test_{component.replace('.', '_')}():
    """Test {component} functionality"""
    # TODO: Implement test
    assert True
'''
    
    def _generate_component_docs(self, component: str) -> str:
        """Generate component documentation"""
        return f'''# {component}

## Overview
TODO: Add component overview

## Usage
TODO: Add usage examples

## API Reference
TODO: Add API documentation
'''
    
    def _prepare_task_environment(self, task: str) -> Dict[str, Any]:
        """Prepare task environment"""
        return {
            'task': task,
            'dependencies': [],
            'environment_variables': {},
            'required_services': []
        }
        
    def _identify_task_files(self, task: str) -> List[str]:
        """Identify files relevant to task"""
        # Simplified file identification
        files = []
        
        task_lower = task.lower()
        
        if 'api' in task_lower:
            files.extend(['api.py', 'routes.py', 'models.py'])
        if 'test' in task_lower:
            files.extend(['test_*.py', 'conftest.py'])
        if 'ui' in task_lower:
            files.extend(['App.tsx', 'components/*.tsx'])
            
        return files
        
    def _generate_task_structure(self, task: str) -> Dict[str, Any]:
        """Generate initial task structure"""
        return {
            'directories': ['src', 'tests', 'docs'],
            'files': self._identify_task_files(task),
            'configurations': []
        }
        
    def _generate_maintenance_script(self, component: str) -> str:
        """Generate maintenance script"""
        return f'''#!/bin/bash
# Maintenance script for {component}

echo "Starting maintenance for {component}"

# TODO: Add maintenance steps
# 1. Backup current state
# 2. Apply updates
# 3. Verify functionality
# 4. Clean up

echo "Maintenance completed"
'''
    
    def _identify_backup_needs(self, component: str) -> List[str]:
        """Identify what needs to be backed up"""
        return [
            f"{component}.backup",
            f"{component}.config",
            "database_snapshot"
        ]
        
    def _generate_rollback_plan(self, component: str) -> Dict[str, Any]:
        """Generate rollback plan"""
        return {
            'steps': [
                f"Stop {component} service",
                "Restore from backup",
                "Verify configuration",
                "Restart service",
                "Run health checks"
            ],
            'verification': [
                "Check service status",
                "Verify functionality",
                "Monitor logs"
            ]
        }


class PredictiveEngine:
    """Main predictive engine coordinating all predictors"""
    
    def __init__(self, db_path: str = "predictions.db"):
        self.db_path = db_path
        
        # Initialize predictors
        self.task_predictor = TaskSequencePredictor()
        self.component_predictor = ComponentPredictor()
        self.question_predictor = QuestionPredictor()
        self.maintenance_predictor = MaintenancePredictor()
        self.requirement_predictor = RequirementPredictor()
        self.action_precomputer = ActionPrecomputer()
        
        # User contexts
        self.user_contexts: Dict[str, UserContext] = {}
        
        # Prediction history
        self.prediction_history: List[Prediction] = []
        
        # Initialize database
        self._init_database()
        
        # Background tasks
        self.prediction_task = None
        self.is_running = False
        
    def _init_database(self):
        """Initialize prediction database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                prediction_type TEXT,
                prediction TEXT,
                confidence REAL,
                context TEXT,
                timestamp DATETIME,
                was_correct BOOLEAN
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id INTEGER,
                feedback TEXT,
                rating INTEGER,
                timestamp DATETIME,
                FOREIGN KEY (prediction_id) REFERENCES predictions (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    async def start(self):
        """Start predictive engine"""
        logger.info("Starting NEXUS Predictive Engine")
        self.is_running = True
        
        # Start background prediction task
        self.prediction_task = asyncio.create_task(self._continuous_prediction())
        
        await self.prediction_task
        
    async def stop(self):
        """Stop predictive engine"""
        logger.info("Stopping NEXUS Predictive Engine")
        self.is_running = False
        
        if self.prediction_task:
            self.prediction_task.cancel()
            await asyncio.gather(self.prediction_task, return_exceptions=True)
            
    def get_or_create_context(self, user_id: str) -> UserContext:
        """Get or create user context"""
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = UserContext(user_id=user_id)
            
        return self.user_contexts[user_id]
        
    async def update_context(self, user_id: str, **kwargs):
        """Update user context"""
        context = self.get_or_create_context(user_id)
        
        for key, value in kwargs.items():
            if hasattr(context, key):
                setattr(context, key, value)
                
        # Trigger predictions based on context change
        await self._make_predictions(context)
        
    async def _make_predictions(self, context: UserContext) -> List[Prediction]:
        """Make predictions based on context"""
        predictions = []
        
        # Task sequence predictions
        next_tasks = self.task_predictor.predict_next_tasks(context)
        for task, confidence in next_tasks[:3]:
            pred = Prediction(
                prediction_type=PredictionType.TASK_SEQUENCE,
                timestamp=datetime.now(),
                prediction=task,
                confidence=confidence,
                context={'user_id': context.user_id}
            )
            predictions.append(pred)
            
        # Component predictions
        components = self.component_predictor.predict_components(context)
        for component, confidence in components[:3]:
            pred = Prediction(
                prediction_type=PredictionType.COMPONENT_NEED,
                timestamp=datetime.now(),
                prediction=component,
                confidence=confidence,
                context={'user_id': context.user_id}
            )
            predictions.append(pred)
            
        # Question predictions
        questions = self.question_predictor.predict_questions(context)
        for question, confidence in questions[:2]:
            pred = Prediction(
                prediction_type=PredictionType.QUESTION,
                timestamp=datetime.now(),
                prediction=question,
                confidence=confidence,
                context={'user_id': context.user_id}
            )
            predictions.append(pred)
            
        # Store predictions
        self._store_predictions(predictions)
        
        # Pre-compute actions for high-confidence predictions
        await self.action_precomputer.precompute_actions(predictions)
        
        return predictions
        
    async def _continuous_prediction(self):
        """Continuously make predictions"""
        while self.is_running:
            try:
                # Make predictions for all active contexts
                for user_id, context in self.user_contexts.items():
                    # Skip if no recent activity
                    if datetime.now() - context.session_start > timedelta(hours=1):
                        continue
                        
                    await self._make_predictions(context)
                    
                # Maintenance predictions
                all_components = self._get_all_components()
                maintenance_preds = self.maintenance_predictor.predict_maintenance(all_components)
                
                for component, scheduled_time, confidence in maintenance_preds:
                    pred = Prediction(
                        prediction_type=PredictionType.MAINTENANCE,
                        timestamp=datetime.now(),
                        prediction=(component, scheduled_time, confidence),
                        confidence=confidence,
                        context={'component': component}
                    )
                    self._store_predictions([pred])
                    
            except Exception as e:
                logger.error(f"Error in continuous prediction: {e}")
                
            # Wait before next prediction cycle
            await asyncio.sleep(300)  # 5 minutes
            
    def _get_all_components(self) -> List[str]:
        """Get all system components"""
        # This would be integrated with actual system inventory
        return [
            'api_service',
            'database',
            'cache_service',
            'message_queue',
            'web_server'
        ]
        
    def _store_predictions(self, predictions: List[Prediction]):
        """Store predictions in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for pred in predictions:
            cursor.execute('''
                INSERT INTO predictions (user_id, prediction_type, prediction, 
                                       confidence, context, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                pred.context.get('user_id', 'system'),
                pred.prediction_type.value,
                json.dumps(pred.prediction) if not isinstance(pred.prediction, str) else pred.prediction,
                pred.confidence,
                json.dumps(pred.context),
                pred.timestamp
            ))
            
        conn.commit()
        conn.close()
        
        # Add to history
        self.prediction_history.extend(predictions)
        
    def get_predictions(self, user_id: str = None, 
                       prediction_type: PredictionType = None) -> List[Prediction]:
        """Get predictions with filters"""
        filtered = self.prediction_history
        
        if user_id:
            filtered = [p for p in filtered if p.context.get('user_id') == user_id]
            
        if prediction_type:
            filtered = [p for p in filtered if p.prediction_type == prediction_type]
            
        # Sort by confidence and recency
        filtered.sort(key=lambda p: (p.confidence, p.timestamp), reverse=True)
        
        return filtered[:20]
        
    def record_feedback(self, prediction_id: int, feedback: str, rating: int):
        """Record user feedback on prediction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_feedback (prediction_id, feedback, rating, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (prediction_id, feedback, rating, datetime.now()))
        
        # Update prediction accuracy if applicable
        if rating <= 2:  # Poor rating
            cursor.execute('''
                UPDATE predictions SET was_correct = 0 WHERE id = ?
            ''', (prediction_id,))
        elif rating >= 4:  # Good rating
            cursor.execute('''
                UPDATE predictions SET was_correct = 1 WHERE id = ?
            ''', (prediction_id,))
            
        conn.commit()
        conn.close()
        
    def get_accuracy_metrics(self) -> Dict[str, float]:
        """Get prediction accuracy metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metrics = {}
        
        # Overall accuracy
        cursor.execute('''
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM predictions WHERE was_correct IS NOT NULL
        ''')
        
        result = cursor.fetchone()
        if result and result[0] > 0:
            metrics['overall_accuracy'] = result[1] / result[0]
            
        # Accuracy by type
        for pred_type in PredictionType:
            cursor.execute('''
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct
                FROM predictions 
                WHERE was_correct IS NOT NULL AND prediction_type = ?
            ''', (pred_type.value,))
            
            result = cursor.fetchone()
            if result and result[0] > 0:
                metrics[f'{pred_type.value}_accuracy'] = result[1] / result[0]
                
        conn.close()
        
        return metrics


# Integration with monitoring system
class MonitoringIntegration:
    """Integrates predictive engine with monitoring system"""
    
    def __init__(self, predictive_engine: PredictiveEngine):
        self.engine = predictive_engine
        
    async def handle_monitoring_event(self, event: Dict[str, Any]):
        """Handle events from monitoring system"""
        event_type = event.get('event_type')
        
        # Update context based on event
        if event_type == 'high_cpu':
            # Predict performance issues
            context = self.engine.get_or_create_context('system')
            context.error_history.append('High CPU usage detected')
            await self.engine.update_context('system', error_history=context.error_history)
            
        elif event_type == 'new_issue':
            # Predict related questions
            issue_data = event.get('data', {})
            context = self.engine.get_or_create_context(issue_data.get('author', 'unknown'))
            context.current_task = f"Resolve issue: {issue_data.get('title', '')}"
            await self.engine.update_context(
                context.user_id,
                current_task=context.current_task
            )
            
        elif event_type == 'outdated_package':
            # Record for maintenance prediction
            package = event.get('data', {}).get('package')
            if package:
                self.engine.maintenance_predictor.add_failure(
                    package,
                    datetime.now(),
                    'outdated'
                )


# Example usage
async def main():
    """Example usage of predictive engine"""
    # Create engine
    engine = PredictiveEngine()
    
    # Create monitoring integration
    monitor_integration = MonitoringIntegration(engine)
    
    # Start engine
    await engine.start()
    
    # Simulate user activity
    user_id = "test_user"
    
    # Update context with current task
    await engine.update_context(
        user_id,
        current_task="Implement user authentication",
        current_files=["auth.py", "models.py"],
        recent_tasks=["Setup database", "Create user model"]
    )
    
    # Get predictions
    predictions = engine.get_predictions(user_id)
    
    print("Predictions:")
    for pred in predictions:
        print(f"- {pred.prediction_type.value}: {pred.prediction} (confidence: {pred.confidence:.2f})")
        
    # Check pre-computed actions
    for pred in predictions:
        action = engine.action_precomputer.get_precomputed_action(pred)
        if action:
            print(f"\nPre-computed action for {pred.prediction}:")
            print(action)
            
    # Simulate monitoring event
    await monitor_integration.handle_monitoring_event({
        'event_type': 'new_issue',
        'data': {
            'title': 'Authentication not working',
            'author': user_id
        }
    })
    
    # Get updated predictions
    updated_predictions = engine.get_predictions(user_id)
    
    print("\nUpdated predictions after issue:")
    for pred in updated_predictions[:5]:
        print(f"- {pred.prediction_type.value}: {pred.prediction} (confidence: {pred.confidence:.2f})")
        
    # Stop engine
    await engine.stop()


if __name__ == "__main__":
    asyncio.run(main())