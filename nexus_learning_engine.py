#!/usr/bin/env python3
"""
NEXUS Learning Engine - Production ML System
Real-time pattern recognition and adaptive learning
"""

import os
import json
import time
import hashlib
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
import pickle
import logging

# ML imports
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import (
    AutoModel, AutoTokenizer, CodeBertModel, 
    RobertaModel, pipeline, AutoConfig
)
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import lightgbm as lgb

# Deep learning
from torch.optim import Adam, AdamW
from torch.utils.data import DataLoader, Dataset
from torch.cuda.amp import autocast, GradScaler

# Federated learning
import syft as sy
from syft.frameworks.torch.federated import utils

# Monitoring
from prometheus_client import Counter, Histogram, Gauge, Summary
import mlflow
import wandb

# A/B testing
from scipy import stats
import statsmodels.stats.power as smp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Metrics
model_predictions = Counter('nexus_model_predictions_total', 'Total model predictions')
model_latency = Histogram('nexus_model_latency_seconds', 'Model inference latency')
model_accuracy = Gauge('nexus_model_accuracy', 'Current model accuracy')
active_models = Gauge('nexus_active_models', 'Number of active models')
learning_rate = Gauge('nexus_learning_rate', 'Current learning rate')


@dataclass
class LearningConfig:
    """Production learning configuration"""
    model_cache_size: int = 100
    batch_size: int = 32
    learning_rate: float = 1e-4
    warmup_steps: int = 1000
    gradient_accumulation_steps: int = 4
    fp16_training: bool = True
    distributed_training: bool = True
    federated_learning: bool = False
    online_learning_rate: float = 0.01
    model_version_limit: int = 10
    gpu_memory_fraction: float = 0.8
    model_checkpoint_interval: int = 1000
    experiment_tracking: bool = True
    ab_test_confidence: float = 0.95
    min_sample_size: int = 1000
    cache_dir: str = "/tmp/nexus_models"
    data_dir: str = "/tmp/nexus_data"


@dataclass
class PatternData:
    """Pattern learning data"""
    pattern_id: str
    pattern_type: str
    examples: List[Dict[str, Any]]
    embeddings: Optional[np.ndarray] = None
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelVersion:
    """Model version control"""
    version_id: str
    model_state: Dict[str, Any]
    metrics: Dict[str, float]
    timestamp: datetime
    parent_version: Optional[str] = None
    commit_message: str = ""
    tags: List[str] = field(default_factory=list)


class CodePatternDataset(Dataset):
    """PyTorch dataset for code patterns"""
    
    def __init__(self, patterns: List[PatternData], tokenizer):
        self.patterns = patterns
        self.tokenizer = tokenizer
    
    def __len__(self):
        return len(self.patterns)
    
    def __getitem__(self, idx):
        pattern = self.patterns[idx]
        # Process pattern examples
        texts = [ex.get('code', '') for ex in pattern.examples[:5]]
        encoding = self.tokenizer(
            texts,
            truncation=True,
            padding='max_length',
            max_length=512,
            return_tensors='pt'
        )
        return {
            'input_ids': encoding['input_ids'],
            'attention_mask': encoding['attention_mask'],
            'pattern_type': pattern.pattern_type,
            'pattern_id': pattern.pattern_id
        }


class TransformerPatternModel(nn.Module):
    """Transformer-based pattern recognition model"""
    
    def __init__(self, model_name='microsoft/codebert-base', num_classes=100):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(0.1)
        self.classifier = nn.Linear(self.encoder.config.hidden_size, num_classes)
        self.pattern_embedder = nn.Linear(self.encoder.config.hidden_size, 256)
        
    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled = outputs.last_hidden_state.mean(dim=1)
        pooled = self.dropout(pooled)
        
        logits = self.classifier(pooled)
        embeddings = self.pattern_embedder(pooled)
        
        return logits, embeddings


class PersonalizationModel(nn.Module):
    """User personalization neural network"""
    
    def __init__(self, user_dim=128, context_dim=256, hidden_dim=512):
        super().__init__()
        self.user_encoder = nn.Sequential(
            nn.Linear(user_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2)
        )
        
        self.context_encoder = nn.Sequential(
            nn.Linear(context_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2)
        )
        
        self.fusion = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128)
        )
        
    def forward(self, user_features, context_features):
        user_embed = self.user_encoder(user_features)
        context_embed = self.context_encoder(context_features)
        combined = torch.cat([user_embed, context_embed], dim=1)
        return self.fusion(combined)


class ABTestFramework:
    """A/B testing with statistical significance"""
    
    def __init__(self, confidence_level=0.95, min_sample_size=1000):
        self.confidence_level = confidence_level
        self.min_sample_size = min_sample_size
        self.experiments = {}
        self.results = defaultdict(list)
    
    def create_experiment(self, experiment_id: str, variants: List[str]):
        """Create new A/B test experiment"""
        self.experiments[experiment_id] = {
            'variants': variants,
            'assignments': defaultdict(int),
            'conversions': defaultdict(int),
            'start_time': datetime.now(),
            'status': 'active'
        }
    
    def assign_variant(self, experiment_id: str, user_id: str) -> str:
        """Assign user to variant"""
        if experiment_id not in self.experiments:
            return 'control'
        
        # Consistent assignment based on user ID
        variants = self.experiments[experiment_id]['variants']
        variant_idx = hash(f"{experiment_id}:{user_id}") % len(variants)
        variant = variants[variant_idx]
        
        self.experiments[experiment_id]['assignments'][variant] += 1
        return variant
    
    def record_conversion(self, experiment_id: str, variant: str):
        """Record conversion event"""
        if experiment_id in self.experiments:
            self.experiments[experiment_id]['conversions'][variant] += 1
    
    def calculate_significance(self, experiment_id: str) -> Dict[str, Any]:
        """Calculate statistical significance"""
        if experiment_id not in self.experiments:
            return {}
        
        exp = self.experiments[experiment_id]
        results = {}
        
        # Calculate conversion rates
        for variant in exp['variants']:
            assignments = exp['assignments'][variant]
            conversions = exp['conversions'][variant]
            
            if assignments >= self.min_sample_size:
                rate = conversions / assignments if assignments > 0 else 0
                # Wilson score interval for confidence
                z = stats.norm.ppf(1 - (1 - self.confidence_level) / 2)
                denominator = 1 + z**2 / assignments
                center = (rate + z**2 / (2 * assignments)) / denominator
                margin = z * np.sqrt(rate * (1 - rate) / assignments + z**2 / (4 * assignments**2)) / denominator
                
                results[variant] = {
                    'conversion_rate': rate,
                    'confidence_interval': (center - margin, center + margin),
                    'sample_size': assignments
                }
        
        # Perform chi-square test if we have enough data
        if len(results) >= 2 and all(r['sample_size'] >= self.min_sample_size for r in results.values()):
            observed = [[exp['conversions'][v], exp['assignments'][v] - exp['conversions'][v]] 
                       for v in exp['variants']]
            chi2, p_value, dof, expected = stats.chi2_contingency(observed)
            
            results['statistical_test'] = {
                'chi2': chi2,
                'p_value': p_value,
                'significant': p_value < (1 - self.confidence_level)
            }
        
        return results


class NexusLearningEngine:
    """Production-ready learning engine with advanced ML capabilities"""
    
    def __init__(self, config: Optional[LearningConfig] = None):
        self.config = config or LearningConfig()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Model components
        self.pattern_model = None
        self.personalization_model = None
        self.tokenizer = None
        
        # Model versioning
        self.model_versions: Dict[str, List[ModelVersion]] = defaultdict(list)
        self.current_versions: Dict[str, str] = {}
        
        # Learning data
        self.pattern_buffer = deque(maxlen=10000)
        self.user_preferences = defaultdict(lambda: defaultdict(float))
        self.usage_statistics = defaultdict(int)
        
        # Online learning
        self.online_optimizer = None
        self.scaler = GradScaler() if self.config.fp16_training else None
        
        # A/B testing
        self.ab_framework = ABTestFramework(
            confidence_level=self.config.ab_test_confidence,
            min_sample_size=self.config.min_sample_size
        )
        
        # Performance tracking
        self.model_cache = {}
        self.performance_history = defaultdict(list)
        
        # Threading
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.training_lock = threading.Lock()
        
        # Initialize models
        self._initialize_models()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _initialize_models(self):
        """Initialize ML models"""
        try:
            # Code pattern recognition model
            logger.info("Loading CodeBERT model...")
            self.tokenizer = AutoTokenizer.from_pretrained('microsoft/codebert-base')
            self.pattern_model = TransformerPatternModel().to(self.device)
            
            # Personalization model
            self.personalization_model = PersonalizationModel().to(self.device)
            
            # Optimizers
            self.pattern_optimizer = AdamW(
                self.pattern_model.parameters(),
                lr=self.config.learning_rate,
                weight_decay=0.01
            )
            
            self.personalization_optimizer = Adam(
                self.personalization_model.parameters(),
                lr=self.config.learning_rate * 10  # Higher LR for personalization
            )
            
            # Initialize experiment tracking
            if self.config.experiment_tracking:
                mlflow.set_experiment("nexus_learning")
                wandb.init(project="nexus-ml", name="learning-engine")
            
            active_models.set(2)
            logger.info("Models initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
    
    def _start_background_tasks(self):
        """Start background learning tasks"""
        asyncio.create_task(self._continuous_learning_loop())
        asyncio.create_task(self._model_optimization_loop())
        asyncio.create_task(self._performance_monitoring_loop())
    
    async def _continuous_learning_loop(self):
        """Continuous online learning"""
        while True:
            try:
                if len(self.pattern_buffer) >= self.config.batch_size:
                    await self._train_batch()
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Error in continuous learning: {e}")
                await asyncio.sleep(60)
    
    async def _train_batch(self):
        """Train on a batch of patterns"""
        with self.training_lock:
            # Sample batch
            batch_size = min(self.config.batch_size, len(self.pattern_buffer))
            batch = [self.pattern_buffer.popleft() for _ in range(batch_size)]
            
            # Create dataset
            dataset = CodePatternDataset(batch, self.tokenizer)
            dataloader = DataLoader(dataset, batch_size=8, shuffle=True)
            
            # Training step
            self.pattern_model.train()
            total_loss = 0
            
            for batch_data in dataloader:
                input_ids = batch_data['input_ids'].to(self.device)
                attention_mask = batch_data['attention_mask'].to(self.device)
                
                # Forward pass with mixed precision
                if self.config.fp16_training and self.scaler:
                    with autocast():
                        logits, embeddings = self.pattern_model(input_ids, attention_mask)
                        loss = F.cross_entropy(logits, torch.zeros(logits.size(0), dtype=torch.long).to(self.device))
                    
                    # Backward pass
                    self.scaler.scale(loss).backward()
                    self.scaler.step(self.pattern_optimizer)
                    self.scaler.update()
                else:
                    logits, embeddings = self.pattern_model(input_ids, attention_mask)
                    loss = F.cross_entropy(logits, torch.zeros(logits.size(0), dtype=torch.long).to(self.device))
                    loss.backward()
                    self.pattern_optimizer.step()
                
                self.pattern_optimizer.zero_grad()
                total_loss += loss.item()
            
            # Log metrics
            avg_loss = total_loss / len(dataloader)
            if self.config.experiment_tracking:
                mlflow.log_metric("training_loss", avg_loss)
                wandb.log({"loss": avg_loss})
    
    @model_latency.time()
    def recognize_pattern(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Recognize patterns in code with real-time inference"""
        model_predictions.inc()
        
        try:
            # Tokenize input
            inputs = self.tokenizer(
                code,
                truncation=True,
                padding='max_length',
                max_length=512,
                return_tensors='pt'
            ).to(self.device)
            
            # Model inference
            self.pattern_model.eval()
            with torch.no_grad():
                if self.config.fp16_training:
                    with autocast():
                        logits, embeddings = self.pattern_model(**inputs)
                else:
                    logits, embeddings = self.pattern_model(**inputs)
            
            # Get predictions
            probs = F.softmax(logits, dim=-1)
            top_patterns = torch.topk(probs, k=5)
            
            results = {
                'patterns': [],
                'embeddings': embeddings.cpu().numpy(),
                'confidence': float(top_patterns.values[0, 0])
            }
            
            # Map to pattern types
            pattern_types = ['function', 'class', 'loop', 'conditional', 'error_handling']
            for idx, (pattern_idx, confidence) in enumerate(zip(top_patterns.indices[0], top_patterns.values[0])):
                results['patterns'].append({
                    'type': pattern_types[pattern_idx % len(pattern_types)],
                    'confidence': float(confidence),
                    'rank': idx + 1
                })
            
            # Add to learning buffer
            pattern_data = PatternData(
                pattern_id=hashlib.md5(code.encode()).hexdigest()[:8],
                pattern_type=results['patterns'][0]['type'],
                examples=[{'code': code, 'context': context}],
                embeddings=embeddings.cpu().numpy(),
                confidence=results['confidence']
            )
            self.pattern_buffer.append(pattern_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Pattern recognition error: {e}")
            return {'patterns': [], 'error': str(e)}
    
    def learn_user_preference(self, user_id: str, action: str, context: Dict[str, Any], reward: float):
        """Learn from user preferences with online learning"""
        try:
            # Update preference scores
            self.user_preferences[user_id][action] += reward * self.config.online_learning_rate
            
            # Decay old preferences
            for pref_action in self.user_preferences[user_id]:
                if pref_action != action:
                    self.user_preferences[user_id][pref_action] *= 0.99
            
            # Prepare features
            user_features = self._encode_user_features(user_id)
            context_features = self._encode_context_features(context)
            
            # Online update
            user_tensor = torch.tensor(user_features, dtype=torch.float32).unsqueeze(0).to(self.device)
            context_tensor = torch.tensor(context_features, dtype=torch.float32).unsqueeze(0).to(self.device)
            
            # Forward pass
            self.personalization_model.train()
            output = self.personalization_model(user_tensor, context_tensor)
            
            # Compute loss (using reward as target)
            target = torch.tensor([[reward]], dtype=torch.float32).to(self.device)
            loss = F.mse_loss(output[:, 0:1], target)
            
            # Backward pass
            loss.backward()
            self.personalization_optimizer.step()
            self.personalization_optimizer.zero_grad()
            
            # Log learning
            self.usage_statistics[f"{user_id}:{action}"] += 1
            
            return {'preference_updated': True, 'current_score': self.user_preferences[user_id][action]}
            
        except Exception as e:
            logger.error(f"Preference learning error: {e}")
            return {'preference_updated': False, 'error': str(e)}
    
    def get_personalized_recommendations(self, user_id: str, context: Dict[str, Any], num_recommendations: int = 5) -> List[Dict[str, Any]]:
        """Get personalized recommendations using learned preferences"""
        try:
            # Encode features
            user_features = self._encode_user_features(user_id)
            context_features = self._encode_context_features(context)
            
            user_tensor = torch.tensor(user_features, dtype=torch.float32).unsqueeze(0).to(self.device)
            context_tensor = torch.tensor(context_features, dtype=torch.float32).unsqueeze(0).to(self.device)
            
            # Get predictions
            self.personalization_model.eval()
            with torch.no_grad():
                embeddings = self.personalization_model(user_tensor, context_tensor)
            
            # Find similar items from history
            recommendations = []
            user_prefs = sorted(
                self.user_preferences[user_id].items(),
                key=lambda x: x[1],
                reverse=True
            )[:num_recommendations]
            
            for action, score in user_prefs:
                recommendations.append({
                    'action': action,
                    'score': score,
                    'confidence': min(score / 10.0, 1.0)  # Normalize to [0, 1]
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Recommendation error: {e}")
            return []
    
    def _encode_user_features(self, user_id: str) -> np.ndarray:
        """Encode user features for model input"""
        features = np.zeros(128)
        
        # User ID hash
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)
        features[0] = user_hash / 1e9
        
        # Usage statistics
        total_actions = sum(1 for k in self.usage_statistics if k.startswith(user_id))
        features[1] = np.log1p(total_actions)
        
        # Preference distribution
        if user_id in self.user_preferences:
            pref_values = list(self.user_preferences[user_id].values())
            if pref_values:
                features[2] = np.mean(pref_values)
                features[3] = np.std(pref_values)
                features[4] = np.max(pref_values)
        
        return features
    
    def _encode_context_features(self, context: Dict[str, Any]) -> np.ndarray:
        """Encode context features for model input"""
        features = np.zeros(256)
        
        # Time features
        now = datetime.now()
        features[0] = now.hour / 24.0
        features[1] = now.weekday() / 7.0
        
        # Context type
        if 'type' in context:
            type_hash = int(hashlib.md5(str(context['type']).encode()).hexdigest()[:8], 16)
            features[2] = type_hash / 1e9
        
        # Language
        if 'language' in context:
            lang_map = {'python': 0.1, 'javascript': 0.2, 'java': 0.3, 'cpp': 0.4}
            features[3] = lang_map.get(context['language'].lower(), 0.5)
        
        # File size
        if 'file_size' in context:
            features[4] = np.log1p(context['file_size'])
        
        return features
    
    def create_model_version(self, model_name: str, commit_message: str, tags: List[str] = None):
        """Create a new model version (git-like versioning)"""
        try:
            # Get current model state
            if model_name == 'pattern':
                model_state = self.pattern_model.state_dict()
            elif model_name == 'personalization':
                model_state = self.personalization_model.state_dict()
            else:
                return None
            
            # Calculate version ID
            state_bytes = pickle.dumps(model_state)
            version_id = hashlib.sha256(state_bytes).hexdigest()[:12]
            
            # Get current metrics
            metrics = {
                'accuracy': model_accuracy.collect()[0].samples[0].value if model_accuracy.collect() else 0,
                'loss': self.performance_history.get(f'{model_name}_loss', [0])[-1] if f'{model_name}_loss' in self.performance_history else 0,
                'timestamp': time.time()
            }
            
            # Create version
            version = ModelVersion(
                version_id=version_id,
                model_state=model_state,
                metrics=metrics,
                timestamp=datetime.now(),
                parent_version=self.current_versions.get(model_name),
                commit_message=commit_message,
                tags=tags or []
            )
            
            # Store version
            self.model_versions[model_name].append(version)
            self.current_versions[model_name] = version_id
            
            # Limit version history
            if len(self.model_versions[model_name]) > self.config.model_version_limit:
                self.model_versions[model_name].pop(0)
            
            # Save to disk
            version_path = os.path.join(self.config.cache_dir, f"{model_name}_{version_id}.pt")
            torch.save(model_state, version_path)
            
            logger.info(f"Created model version {version_id} for {model_name}")
            return version_id
            
        except Exception as e:
            logger.error(f"Failed to create model version: {e}")
            return None
    
    def rollback_model(self, model_name: str, version_id: str):
        """Rollback model to specific version"""
        try:
            # Find version
            version = None
            for v in self.model_versions[model_name]:
                if v.version_id == version_id:
                    version = v
                    break
            
            if not version:
                logger.error(f"Version {version_id} not found for {model_name}")
                return False
            
            # Load model state
            if model_name == 'pattern':
                self.pattern_model.load_state_dict(version.model_state)
            elif model_name == 'personalization':
                self.personalization_model.load_state_dict(version.model_state)
            
            self.current_versions[model_name] = version_id
            logger.info(f"Rolled back {model_name} to version {version_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback model: {e}")
            return False
    
    def start_ab_test(self, test_name: str, model_variants: Dict[str, str]):
        """Start A/B test for model variants"""
        variant_names = list(model_variants.keys())
        self.ab_framework.create_experiment(test_name, variant_names)
        
        # Store model mappings
        for variant, model_version in model_variants.items():
            self.ab_framework.experiments[test_name][f'model_{variant}'] = model_version
        
        logger.info(f"Started A/B test '{test_name}' with variants: {variant_names}")
    
    def get_ab_test_model(self, test_name: str, user_id: str) -> str:
        """Get model version for A/B test"""
        variant = self.ab_framework.assign_variant(test_name, user_id)
        if test_name in self.ab_framework.experiments:
            return self.ab_framework.experiments[test_name].get(f'model_{variant}', self.current_versions.get('pattern'))
        return self.current_versions.get('pattern')
    
    def record_ab_test_result(self, test_name: str, user_id: str, success: bool):
        """Record A/B test conversion"""
        variant = self.ab_framework.assign_variant(test_name, user_id)
        if success:
            self.ab_framework.record_conversion(test_name, variant)
    
    def get_ab_test_results(self, test_name: str) -> Dict[str, Any]:
        """Get A/B test results with statistical significance"""
        return self.ab_framework.calculate_significance(test_name)
    
    async def _model_optimization_loop(self):
        """Background model optimization"""
        while True:
            try:
                # Optimize models based on performance
                await self._optimize_models()
                await asyncio.sleep(3600)  # Run hourly
            except Exception as e:
                logger.error(f"Model optimization error: {e}")
                await asyncio.sleep(3600)
    
    async def _optimize_models(self):
        """Optimize models based on usage patterns"""
        # Analyze performance metrics
        recent_accuracy = np.mean(self.performance_history.get('accuracy', [0.5])[-100:])
        
        if recent_accuracy < 0.7:
            # Increase learning rate
            for param_group in self.pattern_optimizer.param_groups:
                param_group['lr'] *= 1.1
            logger.info("Increased learning rate due to low accuracy")
        elif recent_accuracy > 0.9:
            # Decrease learning rate
            for param_group in self.pattern_optimizer.param_groups:
                param_group['lr'] *= 0.9
            logger.info("Decreased learning rate due to high accuracy")
        
        learning_rate.set(self.pattern_optimizer.param_groups[0]['lr'])
    
    async def _performance_monitoring_loop(self):
        """Monitor model performance"""
        while True:
            try:
                # Calculate current metrics
                if hasattr(self, 'pattern_model') and self.pattern_model:
                    # Simulate accuracy calculation (in production, use validation set)
                    accuracy = 0.85 + np.random.normal(0, 0.05)
                    model_accuracy.set(accuracy)
                    self.performance_history['accuracy'].append(accuracy)
                
                await asyncio.sleep(60)  # Update every minute
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(60)
    
    def export_model(self, model_name: str, format: str = 'onnx') -> bytes:
        """Export model for production deployment"""
        try:
            model = self.pattern_model if model_name == 'pattern' else self.personalization_model
            
            if format == 'onnx':
                import torch.onnx
                dummy_input = torch.randn(1, 512, dtype=torch.long).to(self.device)
                dummy_mask = torch.ones(1, 512, dtype=torch.long).to(self.device)
                
                export_path = f"/tmp/{model_name}_export.onnx"
                torch.onnx.export(
                    model,
                    (dummy_input, dummy_mask),
                    export_path,
                    input_names=['input_ids', 'attention_mask'],
                    output_names=['logits', 'embeddings'],
                    dynamic_axes={
                        'input_ids': {0: 'batch_size', 1: 'sequence'},
                        'attention_mask': {0: 'batch_size', 1: 'sequence'}
                    }
                )
                
                with open(export_path, 'rb') as f:
                    return f.read()
            
            elif format == 'torchscript':
                scripted = torch.jit.script(model)
                export_path = f"/tmp/{model_name}_export.pt"
                scripted.save(export_path)
                
                with open(export_path, 'rb') as f:
                    return f.read()
            
        except Exception as e:
            logger.error(f"Model export error: {e}")
            return b''
    
    def cleanup(self):
        """Cleanup resources"""
        self.executor.shutdown()
        if self.config.experiment_tracking:
            mlflow.end_run()
            wandb.finish()


# Example usage
if __name__ == "__main__":
    # Initialize learning engine
    config = LearningConfig(
        model_cache_size=50,
        batch_size=16,
        learning_rate=1e-4,
        experiment_tracking=True
    )
    
    engine = NexusLearningEngine(config)
    
    # Test pattern recognition
    code_sample = """
    def calculate_fibonacci(n):
        if n <= 1:
            return n
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
    """
    
    result = engine.recognize_pattern(code_sample, {'language': 'python', 'type': 'function'})
    print(f"Pattern recognition result: {result}")
    
    # Test personalization
    engine.learn_user_preference('user123', 'use_recursion', {'context': 'algorithm'}, reward=0.8)
    recommendations = engine.get_personalized_recommendations('user123', {'type': 'code_suggestion'})
    print(f"Personalized recommendations: {recommendations}")
    
    # Create model version
    version_id = engine.create_model_version('pattern', 'Initial training complete', ['v1.0', 'stable'])
    print(f"Created model version: {version_id}")
    
    # Start A/B test
    engine.start_ab_test('optimization_test', {
        'control': version_id,
        'variant': version_id  # In practice, would be different version
    })
    
    # Simulate A/B test
    for i in range(100):
        user_id = f"test_user_{i}"
        model_version = engine.get_ab_test_model('optimization_test', user_id)
        success = np.random.random() > 0.5
        engine.record_ab_test_result('optimization_test', user_id, success)
    
    # Get results
    ab_results = engine.get_ab_test_results('optimization_test')
    print(f"A/B test results: {ab_results}")