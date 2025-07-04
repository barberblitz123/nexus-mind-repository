#!/usr/bin/env python3
"""
NEXUS Learning Pipeline - Production ML Pipeline System
Handles real-time feature extraction, model training, and continuous learning
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
import asyncio
import joblib
import hashlib
from pathlib import Path

# ML Libraries
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
import xgboost as xgb
import lightgbm as lgb

# Deep Learning
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

# MLflow for experiment tracking
import mlflow
import mlflow.sklearn
import mlflow.pytorch

# Feature engineering
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_classif

# Drift detection
from scipy.stats import ks_2samp, chi2_contingency
import warnings
warnings.filterwarnings('ignore')


@dataclass
class FeatureConfig:
    """Configuration for feature extraction"""
    name: str
    type: str  # 'numeric', 'categorical', 'text', 'temporal'
    source: str
    preprocessing: List[str] = field(default_factory=list)
    aggregations: List[str] = field(default_factory=list)


@dataclass
class ModelConfig:
    """Configuration for ML models"""
    name: str
    type: str  # 'classification', 'regression', 'clustering'
    algorithm: str
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    metrics: List[str] = field(default_factory=list)
    threshold: float = 0.5


class FeatureExtractor:
    """Extract features from user actions and system state"""
    
    def __init__(self):
        self.feature_configs = self._load_feature_configs()
        self.feature_cache = {}
        self.aggregation_window = timedelta(minutes=5)
        
    def _load_feature_configs(self) -> List[FeatureConfig]:
        """Load feature configurations"""
        return [
            # User action features
            FeatureConfig(
                name="action_frequency",
                type="numeric",
                source="user_actions",
                preprocessing=["normalize"],
                aggregations=["count", "mean", "std"]
            ),
            FeatureConfig(
                name="action_sequence",
                type="categorical",
                source="user_actions",
                preprocessing=["encode"],
                aggregations=["mode", "unique_count"]
            ),
            FeatureConfig(
                name="typing_speed",
                type="numeric",
                source="keyboard_events",
                preprocessing=["smooth"],
                aggregations=["mean", "max", "percentile_95"]
            ),
            FeatureConfig(
                name="error_rate",
                type="numeric",
                source="system_logs",
                preprocessing=["clip"],
                aggregations=["sum", "mean"]
            ),
            FeatureConfig(
                name="code_complexity",
                type="numeric",
                source="code_analysis",
                preprocessing=["log_transform"],
                aggregations=["mean", "trend"]
            ),
            FeatureConfig(
                name="context_switches",
                type="numeric",
                source="window_events",
                preprocessing=["normalize"],
                aggregations=["count", "duration_mean"]
            ),
            FeatureConfig(
                name="resource_usage",
                type="numeric",
                source="system_metrics",
                preprocessing=["standardize"],
                aggregations=["mean", "max", "variance"]
            ),
            FeatureConfig(
                name="task_completion_time",
                type="numeric",
                source="task_tracking",
                preprocessing=["winsorize"],
                aggregations=["mean", "median", "trend"]
            )
        ]
    
    async def extract_features(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Extract features from raw data"""
        features = {}
        
        for config in self.feature_configs:
            try:
                # Extract raw feature
                raw_value = await self._extract_raw_feature(data, config)
                
                # Apply preprocessing
                processed_value = await self._preprocess_feature(raw_value, config)
                
                # Apply aggregations
                if config.aggregations:
                    for agg in config.aggregations:
                        feature_name = f"{config.name}_{agg}"
                        features[feature_name] = await self._aggregate_feature(
                            processed_value, agg
                        )
                else:
                    features[config.name] = processed_value
                    
            except Exception as e:
                print(f"Error extracting feature {config.name}: {e}")
                features[config.name] = np.nan
        
        return pd.DataFrame([features])
    
    async def _extract_raw_feature(self, data: Dict, config: FeatureConfig) -> Any:
        """Extract raw feature from data source"""
        if config.source not in data:
            return None
            
        source_data = data[config.source]
        
        if config.type == "numeric":
            return float(source_data.get(config.name, 0))
        elif config.type == "categorical":
            return str(source_data.get(config.name, ""))
        elif config.type == "text":
            return source_data.get(config.name, "")
        elif config.type == "temporal":
            return pd.to_datetime(source_data.get(config.name))
        
        return source_data.get(config.name)
    
    async def _preprocess_feature(self, value: Any, config: FeatureConfig) -> Any:
        """Apply preprocessing to feature"""
        if value is None:
            return np.nan
            
        for prep in config.preprocessing:
            if prep == "normalize":
                value = (value - np.mean(value)) / (np.std(value) + 1e-8)
            elif prep == "standardize":
                scaler = StandardScaler()
                value = scaler.fit_transform([[value]])[0][0]
            elif prep == "log_transform":
                value = np.log1p(abs(value))
            elif prep == "clip":
                value = np.clip(value, 0, np.percentile([value], 99))
            elif prep == "winsorize":
                value = stats.mstats.winsorize([value], limits=[0.05, 0.05])[0]
            elif prep == "smooth":
                # Simple moving average
                if isinstance(value, list):
                    value = np.convolve(value, np.ones(3)/3, mode='valid')
            elif prep == "encode":
                # Simple label encoding for categorical
                value = hash(str(value)) % 1000
                
        return value
    
    async def _aggregate_feature(self, values: Any, aggregation: str) -> float:
        """Apply aggregation to feature values"""
        if not isinstance(values, (list, np.ndarray)):
            values = [values]
            
        values = [v for v in values if v is not None and not np.isnan(v)]
        
        if not values:
            return np.nan
            
        if aggregation == "count":
            return len(values)
        elif aggregation == "mean":
            return np.mean(values)
        elif aggregation == "std":
            return np.std(values)
        elif aggregation == "sum":
            return np.sum(values)
        elif aggregation == "max":
            return np.max(values)
        elif aggregation == "min":
            return np.min(values)
        elif aggregation == "median":
            return np.median(values)
        elif aggregation == "mode":
            return stats.mode(values)[0][0]
        elif aggregation == "unique_count":
            return len(set(values))
        elif aggregation == "percentile_95":
            return np.percentile(values, 95)
        elif aggregation == "variance":
            return np.var(values)
        elif aggregation == "trend":
            # Simple linear trend
            if len(values) > 1:
                x = np.arange(len(values))
                return np.polyfit(x, values, 1)[0]
            return 0
        elif aggregation == "duration_mean":
            # For time-based features
            return np.mean(values)
            
        return np.mean(values)


class DataPreprocessor:
    """Handle data preprocessing and normalization"""
    
    def __init__(self):
        self.scalers = {}
        self.encoders = {}
        self.imputers = {}
        
    def fit_transform(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> pd.DataFrame:
        """Fit preprocessors and transform data"""
        X_processed = X.copy()
        
        # Handle missing values
        X_processed = self._impute_missing(X_processed)
        
        # Scale numeric features
        numeric_cols = X_processed.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col not in self.scalers:
                self.scalers[col] = RobustScaler()
            X_processed[col] = self.scalers[col].fit_transform(X_processed[[col]])
        
        # Encode categorical features
        categorical_cols = X_processed.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            X_processed[col] = self._encode_categorical(X_processed[col], col)
        
        # Feature engineering
        X_processed = self._engineer_features(X_processed)
        
        return X_processed
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform data using fitted preprocessors"""
        X_processed = X.copy()
        
        # Handle missing values
        X_processed = self._impute_missing(X_processed)
        
        # Scale numeric features
        numeric_cols = X_processed.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in self.scalers:
                X_processed[col] = self.scalers[col].transform(X_processed[[col]])
        
        # Encode categorical features
        categorical_cols = X_processed.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            X_processed[col] = self._encode_categorical(X_processed[col], col, fit=False)
        
        # Feature engineering
        X_processed = self._engineer_features(X_processed)
        
        return X_processed
    
    def _impute_missing(self, X: pd.DataFrame) -> pd.DataFrame:
        """Impute missing values"""
        # Numeric: median
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col not in self.imputers:
                self.imputers[col] = X[col].median()
            X[col].fillna(self.imputers[col], inplace=True)
        
        # Categorical: mode
        categorical_cols = X.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if col not in self.imputers:
                self.imputers[col] = X[col].mode()[0] if not X[col].mode().empty else "unknown"
            X[col].fillna(self.imputers[col], inplace=True)
        
        return X
    
    def _encode_categorical(self, series: pd.Series, col_name: str, fit: bool = True) -> pd.Series:
        """Encode categorical variables"""
        if fit:
            unique_vals = series.unique()
            self.encoders[col_name] = {val: i for i, val in enumerate(unique_vals)}
        
        return series.map(lambda x: self.encoders[col_name].get(x, -1))
    
    def _engineer_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Engineer additional features"""
        # Interaction features
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) >= 2:
            for i in range(min(3, len(numeric_cols)-1)):
                col1, col2 = numeric_cols[i], numeric_cols[i+1]
                X[f"{col1}_x_{col2}"] = X[col1] * X[col2]
        
        # Polynomial features for key columns
        for col in numeric_cols[:3]:  # Top 3 numeric features
            X[f"{col}_squared"] = X[col] ** 2
        
        # Ratio features
        if 'action_frequency_count' in X.columns and 'error_rate_sum' in X.columns:
            X['success_ratio'] = X['action_frequency_count'] / (X['error_rate_sum'] + 1)
        
        return X


class ModelTrainer:
    """Handle model training with hyperparameter tuning"""
    
    def __init__(self, mlflow_uri: str = "sqlite:///mlflow.db"):
        self.models = {}
        self.best_params = {}
        self.cv_scores = {}
        mlflow.set_tracking_uri(mlflow_uri)
        
    def train_model(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        model_config: ModelConfig,
        cv_folds: int = 5
    ) -> Tuple[Any, Dict[str, float]]:
        """Train model with cross-validation and hyperparameter tuning"""
        
        with mlflow.start_run(run_name=f"{model_config.name}_{datetime.now().isoformat()}"):
            # Log parameters
            mlflow.log_params({
                "model_type": model_config.type,
                "algorithm": model_config.algorithm,
                "cv_folds": cv_folds
            })
            
            # Select model
            model = self._get_model(model_config)
            
            # Hyperparameter tuning
            param_grid = self._get_param_grid(model_config.algorithm)
            
            if param_grid:
                grid_search = GridSearchCV(
                    model,
                    param_grid,
                    cv=cv_folds,
                    scoring=self._get_scoring_metric(model_config.type),
                    n_jobs=-1,
                    verbose=1
                )
                grid_search.fit(X_train, y_train)
                best_model = grid_search.best_estimator_
                self.best_params[model_config.name] = grid_search.best_params_
                
                # Log best parameters
                mlflow.log_params(grid_search.best_params_)
            else:
                best_model = model
                best_model.fit(X_train, y_train)
            
            # Cross-validation scores
            cv_scores = cross_val_score(
                best_model,
                X_train,
                y_train,
                cv=cv_folds,
                scoring=self._get_scoring_metric(model_config.type)
            )
            
            self.cv_scores[model_config.name] = {
                'mean': cv_scores.mean(),
                'std': cv_scores.std(),
                'scores': cv_scores.tolist()
            }
            
            # Log metrics
            mlflow.log_metrics({
                "cv_score_mean": cv_scores.mean(),
                "cv_score_std": cv_scores.std()
            })
            
            # Save model
            self.models[model_config.name] = best_model
            
            # Log model
            if model_config.algorithm in ['random_forest', 'gradient_boosting', 'xgboost', 'lightgbm']:
                mlflow.sklearn.log_model(best_model, f"model_{model_config.name}")
            
            # Feature importance
            if hasattr(best_model, 'feature_importances_'):
                feature_importance = pd.DataFrame({
                    'feature': X_train.columns,
                    'importance': best_model.feature_importances_
                }).sort_values('importance', ascending=False)
                
                # Log feature importance
                for idx, row in feature_importance.iterrows():
                    mlflow.log_metric(f"feature_imp_{row['feature']}", row['importance'])
            
            return best_model, self.cv_scores[model_config.name]
    
    def _get_model(self, config: ModelConfig):
        """Get model instance based on configuration"""
        if config.algorithm == 'random_forest':
            if config.type == 'classification':
                return RandomForestClassifier(random_state=42, n_jobs=-1)
            else:
                return RandomForestRegressor(random_state=42, n_jobs=-1)
        
        elif config.algorithm == 'gradient_boosting':
            if config.type == 'classification':
                return GradientBoostingClassifier(random_state=42)
            else:
                return GradientBoostingRegressor(random_state=42)
        
        elif config.algorithm == 'xgboost':
            if config.type == 'classification':
                return xgb.XGBClassifier(random_state=42, n_jobs=-1)
            else:
                return xgb.XGBRegressor(random_state=42, n_jobs=-1)
        
        elif config.algorithm == 'lightgbm':
            if config.type == 'classification':
                return lgb.LGBMClassifier(random_state=42, n_jobs=-1)
            else:
                return lgb.LGBMRegressor(random_state=42, n_jobs=-1)
        
        else:
            raise ValueError(f"Unknown algorithm: {config.algorithm}")
    
    def _get_param_grid(self, algorithm: str) -> Dict[str, List]:
        """Get hyperparameter grid for algorithm"""
        if algorithm == 'random_forest':
            return {
                'n_estimators': [100, 200, 300],
                'max_depth': [10, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
        
        elif algorithm == 'gradient_boosting':
            return {
                'n_estimators': [100, 200],
                'learning_rate': [0.01, 0.1, 0.3],
                'max_depth': [3, 5, 7],
                'subsample': [0.8, 1.0]
            }
        
        elif algorithm == 'xgboost':
            return {
                'n_estimators': [100, 200],
                'learning_rate': [0.01, 0.1, 0.3],
                'max_depth': [3, 6, 9],
                'subsample': [0.8, 1.0],
                'colsample_bytree': [0.8, 1.0]
            }
        
        elif algorithm == 'lightgbm':
            return {
                'n_estimators': [100, 200],
                'learning_rate': [0.01, 0.1, 0.3],
                'num_leaves': [31, 50, 100],
                'feature_fraction': [0.8, 1.0],
                'bagging_fraction': [0.8, 1.0]
            }
        
        return {}
    
    def _get_scoring_metric(self, model_type: str) -> str:
        """Get scoring metric for model type"""
        if model_type == 'classification':
            return 'f1_weighted'
        else:
            return 'neg_mean_squared_error'


class ABTestingFramework:
    """A/B testing for model comparison"""
    
    def __init__(self):
        self.test_results = {}
        self.active_tests = {}
        
    def create_test(
        self,
        test_name: str,
        model_a: Any,
        model_b: Any,
        test_size: float = 0.2,
        duration_hours: int = 24
    ):
        """Create A/B test"""
        self.active_tests[test_name] = {
            'model_a': model_a,
            'model_b': model_b,
            'test_size': test_size,
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(hours=duration_hours),
            'results_a': [],
            'results_b': []
        }
    
    def route_prediction(self, test_name: str, X: pd.DataFrame) -> Tuple[Any, str]:
        """Route prediction to A or B model"""
        if test_name not in self.active_tests:
            raise ValueError(f"Test {test_name} not found")
        
        test = self.active_tests[test_name]
        
        # Check if test is still active
        if datetime.now() > test['end_time']:
            return self._get_winner(test_name), "winner"
        
        # Random routing based on test size
        if np.random.random() < test['test_size']:
            model = test['model_b']
            group = 'b'
        else:
            model = test['model_a']
            group = 'a'
        
        prediction = model.predict(X)
        
        return prediction, group
    
    def log_result(self, test_name: str, group: str, actual: Any, predicted: Any):
        """Log test result"""
        if test_name not in self.active_tests:
            return
        
        result = {
            'timestamp': datetime.now(),
            'actual': actual,
            'predicted': predicted,
            'correct': actual == predicted
        }
        
        if group == 'a':
            self.active_tests[test_name]['results_a'].append(result)
        else:
            self.active_tests[test_name]['results_b'].append(result)
    
    def _get_winner(self, test_name: str) -> Any:
        """Determine test winner"""
        test = self.active_tests[test_name]
        
        # Calculate accuracies
        acc_a = np.mean([r['correct'] for r in test['results_a']]) if test['results_a'] else 0
        acc_b = np.mean([r['correct'] for r in test['results_b']]) if test['results_b'] else 0
        
        # Statistical significance test
        if len(test['results_a']) > 30 and len(test['results_b']) > 30:
            from scipy.stats import ttest_ind
            correct_a = [r['correct'] for r in test['results_a']]
            correct_b = [r['correct'] for r in test['results_b']]
            _, p_value = ttest_ind(correct_a, correct_b)
            
            if p_value < 0.05:  # Significant difference
                winner = test['model_b'] if acc_b > acc_a else test['model_a']
            else:  # No significant difference, keep current
                winner = test['model_a']
        else:
            winner = test['model_b'] if acc_b > acc_a else test['model_a']
        
        # Store results
        self.test_results[test_name] = {
            'accuracy_a': acc_a,
            'accuracy_b': acc_b,
            'winner': 'b' if winner == test['model_b'] else 'a',
            'samples_a': len(test['results_a']),
            'samples_b': len(test['results_b'])
        }
        
        return winner


class DriftDetector:
    """Detect data and concept drift"""
    
    def __init__(self, window_size: int = 1000, threshold: float = 0.05):
        self.window_size = window_size
        self.threshold = threshold
        self.reference_data = None
        self.drift_history = []
        
    def set_reference(self, X: pd.DataFrame):
        """Set reference distribution"""
        self.reference_data = X.copy()
    
    def detect_drift(self, X_new: pd.DataFrame) -> Dict[str, Any]:
        """Detect drift in new data"""
        if self.reference_data is None:
            self.set_reference(X_new)
            return {'drift_detected': False, 'features': {}}
        
        drift_results = {
            'drift_detected': False,
            'features': {},
            'timestamp': datetime.now()
        }
        
        # Check each feature
        for col in X_new.columns:
            if col not in self.reference_data.columns:
                continue
            
            # Numeric features: KS test
            if pd.api.types.is_numeric_dtype(X_new[col]):
                statistic, p_value = ks_2samp(
                    self.reference_data[col].dropna(),
                    X_new[col].dropna()
                )
                
                if p_value < self.threshold:
                    drift_results['drift_detected'] = True
                    drift_results['features'][col] = {
                        'type': 'numeric',
                        'statistic': statistic,
                        'p_value': p_value
                    }
            
            # Categorical features: Chi-square test
            else:
                ref_counts = self.reference_data[col].value_counts()
                new_counts = X_new[col].value_counts()
                
                # Align categories
                all_categories = set(ref_counts.index) | set(new_counts.index)
                ref_aligned = [ref_counts.get(cat, 0) for cat in all_categories]
                new_aligned = [new_counts.get(cat, 0) for cat in all_categories]
                
                if sum(new_aligned) > 0:
                    chi2, p_value = chi2_contingency([ref_aligned, new_aligned])[:2]
                    
                    if p_value < self.threshold:
                        drift_results['drift_detected'] = True
                        drift_results['features'][col] = {
                            'type': 'categorical',
                            'chi2': chi2,
                            'p_value': p_value
                        }
        
        # Store result
        self.drift_history.append(drift_results)
        
        return drift_results
    
    def get_drift_summary(self) -> Dict[str, Any]:
        """Get drift summary"""
        if not self.drift_history:
            return {'total_checks': 0, 'drift_rate': 0}
        
        drift_count = sum(1 for d in self.drift_history if d['drift_detected'])
        
        return {
            'total_checks': len(self.drift_history),
            'drift_count': drift_count,
            'drift_rate': drift_count / len(self.drift_history),
            'most_drifted_features': self._get_most_drifted_features(),
            'last_drift': self.drift_history[-1] if self.drift_history else None
        }
    
    def _get_most_drifted_features(self) -> List[Tuple[str, int]]:
        """Get features with most drift occurrences"""
        feature_drift_count = {}
        
        for result in self.drift_history:
            for feature in result['features']:
                feature_drift_count[feature] = feature_drift_count.get(feature, 0) + 1
        
        return sorted(feature_drift_count.items(), key=lambda x: x[1], reverse=True)[:5]


class ContinuousLearningPipeline:
    """Continuous learning and model updating"""
    
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.preprocessor = DataPreprocessor()
        self.trainer = ModelTrainer()
        self.ab_tester = ABTestingFramework()
        self.drift_detector = DriftDetector()
        self.model_versions = {}
        self.training_queue = asyncio.Queue()
        self.is_running = False
        
    async def start(self):
        """Start continuous learning pipeline"""
        self.is_running = True
        
        # Start background tasks
        asyncio.create_task(self._training_loop())
        asyncio.create_task(self._drift_monitoring_loop())
        asyncio.create_task(self._performance_monitoring_loop())
        
        print("Continuous learning pipeline started")
    
    async def stop(self):
        """Stop pipeline"""
        self.is_running = False
    
    async def add_training_data(self, data: Dict[str, Any], label: Any):
        """Add new training data"""
        await self.training_queue.put({
            'data': data,
            'label': label,
            'timestamp': datetime.now()
        })
    
    async def predict(self, data: Dict[str, Any], model_name: str) -> Any:
        """Make prediction with continuous learning"""
        # Extract features
        features = await self.feature_extractor.extract_features(data)
        
        # Preprocess
        features_processed = self.preprocessor.transform(features)
        
        # Get model
        if model_name not in self.model_versions:
            return None
        
        model_info = self.model_versions[model_name]
        
        # Check for A/B test
        if f"{model_name}_ab_test" in self.ab_tester.active_tests:
            prediction, group = self.ab_tester.route_prediction(
                f"{model_name}_ab_test",
                features_processed
            )
        else:
            prediction = model_info['model'].predict(features_processed)[0]
            group = 'production'
        
        # Log prediction
        model_info['predictions'].append({
            'features': features_processed.to_dict(orient='records')[0],
            'prediction': prediction,
            'timestamp': datetime.now(),
            'group': group
        })
        
        return prediction
    
    async def _training_loop(self):
        """Background training loop"""
        batch_size = 100
        training_batch = []
        
        while self.is_running:
            try:
                # Collect training data
                while len(training_batch) < batch_size:
                    try:
                        item = await asyncio.wait_for(
                            self.training_queue.get(),
                            timeout=60.0
                        )
                        training_batch.append(item)
                    except asyncio.TimeoutError:
                        break
                
                if len(training_batch) >= batch_size:
                    # Train models
                    await self._retrain_models(training_batch)
                    training_batch = []
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error in training loop: {e}")
                await asyncio.sleep(5)
    
    async def _retrain_models(self, training_data: List[Dict]):
        """Retrain models with new data"""
        # Extract features
        features_list = []
        labels = []
        
        for item in training_data:
            features = await self.feature_extractor.extract_features(item['data'])
            features_list.append(features)
            labels.append(item['label'])
        
        X = pd.concat(features_list, ignore_index=True)
        y = pd.Series(labels)
        
        # Preprocess
        X_processed = self.preprocessor.fit_transform(X, y)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X_processed, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train models
        model_configs = [
            ModelConfig(
                name="user_intent_classifier",
                type="classification",
                algorithm="xgboost",
                metrics=["accuracy", "f1", "precision", "recall"]
            ),
            ModelConfig(
                name="task_time_predictor",
                type="regression",
                algorithm="lightgbm",
                metrics=["mse", "mae", "r2"]
            )
        ]
        
        for config in model_configs:
            # Train new model
            new_model, cv_scores = self.trainer.train_model(
                X_train, y_train, config
            )
            
            # Evaluate on validation set
            if config.type == "classification":
                val_pred = new_model.predict(X_val)
                val_score = accuracy_score(y_val, val_pred)
            else:
                val_pred = new_model.predict(X_val)
                val_score = -mean_squared_error(y_val, val_pred)
            
            # Check if better than current
            if config.name in self.model_versions:
                current_score = self.model_versions[config.name]['val_score']
                if val_score > current_score * 1.05:  # 5% improvement threshold
                    # Create A/B test
                    self.ab_tester.create_test(
                        f"{config.name}_ab_test",
                        self.model_versions[config.name]['model'],
                        new_model,
                        test_size=0.2,
                        duration_hours=12
                    )
                    print(f"Started A/B test for {config.name}")
            else:
                # First model version
                self.model_versions[config.name] = {
                    'model': new_model,
                    'version': 1,
                    'val_score': val_score,
                    'cv_scores': cv_scores,
                    'trained_at': datetime.now(),
                    'predictions': []
                }
    
    async def _drift_monitoring_loop(self):
        """Monitor for data drift"""
        while self.is_running:
            try:
                # Check each model's recent predictions
                for model_name, model_info in self.model_versions.items():
                    recent_predictions = model_info['predictions'][-1000:]
                    
                    if len(recent_predictions) > 100:
                        # Extract features from predictions
                        recent_features = pd.DataFrame([
                            p['features'] for p in recent_predictions
                        ])
                        
                        # Check for drift
                        drift_result = self.drift_detector.detect_drift(recent_features)
                        
                        if drift_result['drift_detected']:
                            print(f"Drift detected for {model_name}: {drift_result['features']}")
                            
                            # Trigger retraining
                            await self._trigger_retraining(model_name)
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                print(f"Error in drift monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _performance_monitoring_loop(self):
        """Monitor model performance"""
        while self.is_running:
            try:
                # Generate performance report
                report = self.generate_performance_report()
                
                # Log to MLflow
                with mlflow.start_run(run_name="performance_monitoring"):
                    for metric_name, metric_value in report['metrics'].items():
                        mlflow.log_metric(metric_name, metric_value)
                
                # Check for degradation
                for model_name, metrics in report['model_metrics'].items():
                    if metrics.get('accuracy', 1.0) < 0.8:  # Threshold
                        print(f"Performance degradation detected for {model_name}")
                        await self._trigger_retraining(model_name)
                
                await asyncio.sleep(600)  # Check every 10 minutes
                
            except Exception as e:
                print(f"Error in performance monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _trigger_retraining(self, model_name: str):
        """Trigger model retraining"""
        print(f"Triggering retraining for {model_name}")
        # Add flag to prioritize this model in next training batch
        # Implementation depends on specific requirements
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'models': list(self.model_versions.keys()),
            'metrics': {},
            'model_metrics': {}
        }
        
        for model_name, model_info in self.model_versions.items():
            recent_predictions = model_info['predictions'][-1000:]
            
            if recent_predictions:
                # Calculate metrics (would need actual labels in production)
                report['model_metrics'][model_name] = {
                    'total_predictions': len(model_info['predictions']),
                    'recent_predictions': len(recent_predictions),
                    'version': model_info['version'],
                    'age_hours': (datetime.now() - model_info['trained_at']).total_seconds() / 3600
                }
        
        # Overall metrics
        report['metrics']['total_models'] = len(self.model_versions)
        report['metrics']['total_predictions'] = sum(
            len(info['predictions']) for info in self.model_versions.values()
        )
        
        # Drift summary
        report['drift_summary'] = self.drift_detector.get_drift_summary()
        
        # A/B test results
        report['ab_tests'] = self.ab_tester.test_results
        
        return report


# Deep Learning Models
class NeuralFeatureExtractor(nn.Module):
    """Neural network for automatic feature extraction"""
    
    def __init__(self, input_size: int, hidden_sizes: List[int], output_size: int):
        super().__init__()
        
        layers = []
        prev_size = input_size
        
        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.BatchNorm1d(hidden_size),
                nn.ReLU(),
                nn.Dropout(0.2)
            ])
            prev_size = hidden_size
        
        layers.append(nn.Linear(prev_size, output_size))
        
        self.model = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.model(x)


class AutoMLPipeline:
    """Automated machine learning pipeline"""
    
    def __init__(self):
        self.best_model = None
        self.best_score = -np.inf
        self.search_history = []
        
    async def auto_train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        task_type: str = "classification",
        time_budget: int = 3600
    ) -> Dict[str, Any]:
        """Automatically find best model and hyperparameters"""
        
        start_time = datetime.now()
        
        # Define search space
        algorithms = ['random_forest', 'xgboost', 'lightgbm']
        
        # Feature selection
        X_selected = await self._auto_feature_selection(X, y, task_type)
        
        # Model search
        for algorithm in algorithms:
            if (datetime.now() - start_time).total_seconds() > time_budget:
                break
            
            config = ModelConfig(
                name=f"auto_{algorithm}",
                type=task_type,
                algorithm=algorithm
            )
            
            trainer = ModelTrainer()
            model, scores = trainer.train_model(X_selected, y, config)
            
            score = scores['mean']
            
            self.search_history.append({
                'algorithm': algorithm,
                'score': score,
                'features': X_selected.columns.tolist(),
                'timestamp': datetime.now()
            })
            
            if score > self.best_score:
                self.best_score = score
                self.best_model = model
        
        return {
            'best_model': self.best_model,
            'best_score': self.best_score,
            'search_history': self.search_history,
            'selected_features': X_selected.columns.tolist()
        }
    
    async def _auto_feature_selection(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        task_type: str
    ) -> pd.DataFrame:
        """Automatic feature selection"""
        
        # Remove highly correlated features
        corr_matrix = X.corr().abs()
        upper = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )
        to_drop = [column for column in upper.columns if any(upper[column] > 0.95)]
        X_filtered = X.drop(columns=to_drop)
        
        # Select K best features
        if task_type == "classification":
            selector = SelectKBest(f_classif, k=min(20, X_filtered.shape[1]))
        else:
            from sklearn.feature_selection import f_regression
            selector = SelectKBest(f_regression, k=min(20, X_filtered.shape[1]))
        
        X_selected = selector.fit_transform(X_filtered, y)
        selected_features = X_filtered.columns[selector.get_support()]
        
        return pd.DataFrame(X_selected, columns=selected_features)


# Main execution
if __name__ == "__main__":
    # Example usage
    async def main():
        # Initialize pipeline
        pipeline = ContinuousLearningPipeline()
        await pipeline.start()
        
        # Simulate data stream
        for i in range(10):
            sample_data = {
                'user_actions': {
                    'action_frequency': np.random.randint(1, 100),
                    'action_sequence': 'click_edit_save'
                },
                'keyboard_events': {
                    'typing_speed': np.random.uniform(50, 150)
                },
                'system_logs': {
                    'error_rate': np.random.uniform(0, 0.1)
                },
                'code_analysis': {
                    'code_complexity': np.random.uniform(1, 10)
                },
                'window_events': {
                    'context_switches': np.random.randint(0, 20)
                },
                'system_metrics': {
                    'resource_usage': np.random.uniform(0, 100)
                },
                'task_tracking': {
                    'task_completion_time': np.random.uniform(60, 3600)
                }
            }
            
            # Make prediction
            prediction = await pipeline.predict(sample_data, 'user_intent_classifier')
            print(f"Prediction {i}: {prediction}")
            
            # Add training data
            label = np.random.choice(['code', 'debug', 'refactor'])
            await pipeline.add_training_data(sample_data, label)
            
            await asyncio.sleep(1)
        
        # Generate report
        report = pipeline.generate_performance_report()
        print(f"Performance Report: {json.dumps(report, indent=2, default=str)}")
        
        # Stop pipeline
        await pipeline.stop()
    
    # Run
    asyncio.run(main())