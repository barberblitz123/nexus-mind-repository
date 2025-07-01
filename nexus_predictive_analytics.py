#!/usr/bin/env python3
"""
NEXUS Predictive Analytics
Time series forecasting, anomaly detection, and predictive capabilities
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

# Data handling
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split

# Time series analysis
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller, acf, pacf
import pmdarima as pm
from prophet import Prophet
from tbats import TBATS

# Machine learning
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout, Input, Conv1D, MaxPooling1D
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.svm import OneClassSVM
from sklearn.cluster import DBSCAN
import lightgbm as lgb
import xgboost as xgb

# Anomaly detection
from pyod.models.knn import KNN
from pyod.models.lof import LOF
from pyod.models.iforest import IForest
from pyod.models.auto_encoder import AutoEncoder
from alibi_detect.od import OutlierVAE, IsolationForest as AlibiIF
from alibi_detect.ad import AdversarialAE

# Optimization
from scipy.optimize import minimize
import optuna
from hyperopt import hp, fmin, tpe

# Visualization and monitoring
import matplotlib.pyplot as plt
import seaborn as sns
from prometheus_client import Counter, Histogram, Gauge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
predictions_made = Counter('nexus_predictions_made_total', 'Total predictions made')
anomalies_detected = Counter('nexus_anomalies_detected_total', 'Total anomalies detected')
forecasts_generated = Counter('nexus_forecasts_generated_total', 'Total forecasts generated')
prediction_accuracy = Gauge('nexus_prediction_accuracy', 'Prediction accuracy', ['model'])

@dataclass
class PredictiveConfig:
    """Configuration for predictive analytics"""
    # Time series forecasting
    forecast_horizon: int = 24  # hours
    seasonal_period: int = 24  # hourly seasonality
    confidence_level: float = 0.95
    
    # Anomaly detection
    anomaly_threshold: float = 0.95
    contamination_rate: float = 0.1
    anomaly_window: int = 100
    
    # User behavior prediction
    sequence_length: int = 50
    embedding_dim: int = 128
    behavior_categories: int = 10
    
    # Resource usage prediction
    resource_metrics: List[str] = field(default_factory=lambda: [
        'cpu_usage', 'memory_usage', 'disk_io', 'network_io'
    ])
    prediction_interval: int = 5  # minutes
    
    # Model parameters
    lstm_units: int = 128
    lstm_layers: int = 2
    dropout_rate: float = 0.2
    batch_size: int = 32
    epochs: int = 100
    
    # Optimization
    cost_function: str = "minimize_error"
    optimization_method: str = "bayesian"

@dataclass
class ForecastResult:
    """Time series forecast result"""
    metric: str
    timestamps: List[datetime]
    predictions: np.ndarray
    lower_bound: np.ndarray
    upper_bound: np.ndarray
    model_type: str
    metrics: Dict[str, float]
    
@dataclass
class AnomalyResult:
    """Anomaly detection result"""
    timestamp: datetime
    metric: str
    value: float
    expected_value: float
    anomaly_score: float
    is_anomaly: bool
    anomaly_type: str
    explanation: str
    
@dataclass
class BehaviorPrediction:
    """User behavior prediction"""
    user_id: str
    timestamp: datetime
    predicted_action: str
    confidence: float
    alternative_actions: List[Tuple[str, float]]
    features: Dict[str, Any]

class TimeSeriesForecaster:
    """Advanced time series forecasting"""
    
    def __init__(self, config: PredictiveConfig):
        self.config = config
        self.models = {}
        self.scalers = {}
        
    def forecast(self, data: pd.Series, method: str = "auto") -> ForecastResult:
        """Generate time series forecast"""
        # Prepare data
        data = self._prepare_data(data)
        
        # Select and train model
        if method == "auto":
            method = self._select_best_method(data)
            
        if method == "arima":
            result = self._forecast_arima(data)
        elif method == "prophet":
            result = self._forecast_prophet(data)
        elif method == "lstm":
            result = self._forecast_lstm(data)
        elif method == "ensemble":
            result = self._forecast_ensemble(data)
        else:
            result = self._forecast_exponential_smoothing(data)
            
        forecasts_generated.inc()
        return result
        
    def _prepare_data(self, data: pd.Series) -> pd.Series:
        """Prepare time series data"""
        # Handle missing values
        data = data.interpolate(method='time')
        
        # Remove outliers
        z_scores = np.abs(stats.zscore(data.dropna()))
        data[z_scores > 3] = np.nan
        data = data.interpolate(method='time')
        
        return data
        
    def _select_best_method(self, data: pd.Series) -> str:
        """Automatically select best forecasting method"""
        # Check stationarity
        adf_result = adfuller(data.dropna())
        is_stationary = adf_result[1] < 0.05
        
        # Check seasonality
        if len(data) > 2 * self.config.seasonal_period:
            decomposition = seasonal_decompose(data, period=self.config.seasonal_period)
            seasonal_strength = np.std(decomposition.seasonal) / np.std(data)
            has_seasonality = seasonal_strength > 0.1
        else:
            has_seasonality = False
            
        # Select method based on characteristics
        if len(data) < 100:
            return "exponential_smoothing"
        elif has_seasonality:
            return "prophet"
        elif is_stationary:
            return "arima"
        else:
            return "lstm"
            
    def _forecast_arima(self, data: pd.Series) -> ForecastResult:
        """ARIMA forecasting"""
        try:
            # Auto ARIMA
            model = pm.auto_arima(
                data,
                seasonal=True,
                m=self.config.seasonal_period,
                suppress_warnings=True,
                stepwise=True
            )
            
            # Forecast
            forecast, conf_int = model.predict(
                n_periods=self.config.forecast_horizon,
                return_conf_int=True,
                alpha=1 - self.config.confidence_level
            )
            
            # Generate timestamps
            last_timestamp = data.index[-1]
            timestamps = pd.date_range(
                start=last_timestamp + pd.Timedelta(hours=1),
                periods=self.config.forecast_horizon,
                freq='H'
            )
            
            # Calculate metrics
            in_sample_pred = model.predict_in_sample()
            mape = np.mean(np.abs((data.iloc[-len(in_sample_pred):] - in_sample_pred) / data.iloc[-len(in_sample_pred):])) * 100
            
            return ForecastResult(
                metric=data.name or "value",
                timestamps=timestamps.tolist(),
                predictions=forecast,
                lower_bound=conf_int[:, 0],
                upper_bound=conf_int[:, 1],
                model_type="ARIMA",
                metrics={'mape': mape, 'aic': model.aic()}
            )
            
        except Exception as e:
            logger.error(f"ARIMA forecast failed: {e}")
            return self._fallback_forecast(data)
            
    def _forecast_prophet(self, data: pd.Series) -> ForecastResult:
        """Prophet forecasting"""
        try:
            # Prepare data for Prophet
            df = pd.DataFrame({
                'ds': data.index,
                'y': data.values
            })
            
            # Train model
            model = Prophet(
                interval_width=self.config.confidence_level,
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=True
            )
            model.fit(df)
            
            # Make future dataframe
            future = model.make_future_dataframe(periods=self.config.forecast_horizon, freq='H')
            
            # Predict
            forecast = model.predict(future)
            
            # Extract results
            forecast_data = forecast.iloc[-self.config.forecast_horizon:]
            
            return ForecastResult(
                metric=data.name or "value",
                timestamps=forecast_data['ds'].tolist(),
                predictions=forecast_data['yhat'].values,
                lower_bound=forecast_data['yhat_lower'].values,
                upper_bound=forecast_data['yhat_upper'].values,
                model_type="Prophet",
                metrics={'mape': self._calculate_mape(data, model, df)}
            )
            
        except Exception as e:
            logger.error(f"Prophet forecast failed: {e}")
            return self._fallback_forecast(data)
            
    def _forecast_lstm(self, data: pd.Series) -> ForecastResult:
        """LSTM neural network forecasting"""
        try:
            # Prepare sequences
            X, y = self._create_sequences(data.values)
            
            # Scale data
            scaler = MinMaxScaler()
            X_scaled = scaler.fit_transform(X.reshape(-1, 1)).reshape(X.shape)
            y_scaled = scaler.transform(y.reshape(-1, 1)).flatten()
            
            # Build model
            model = self._build_lstm_model(X.shape[1])
            
            # Train
            model.fit(
                X_scaled, y_scaled,
                epochs=50,  # Reduced for speed
                batch_size=self.config.batch_size,
                verbose=0,
                validation_split=0.2
            )
            
            # Multi-step forecast
            predictions = []
            last_sequence = X_scaled[-1]
            
            for _ in range(self.config.forecast_horizon):
                pred = model.predict(last_sequence.reshape(1, -1, 1), verbose=0)
                predictions.append(pred[0, 0])
                
                # Update sequence
                last_sequence = np.append(last_sequence[1:], pred)
                
            # Inverse transform
            predictions = scaler.inverse_transform(
                np.array(predictions).reshape(-1, 1)
            ).flatten()
            
            # Calculate confidence intervals (using prediction std)
            std = np.std(predictions) * 1.96  # 95% confidence
            
            # Generate timestamps
            last_timestamp = data.index[-1]
            timestamps = pd.date_range(
                start=last_timestamp + pd.Timedelta(hours=1),
                periods=self.config.forecast_horizon,
                freq='H'
            )
            
            return ForecastResult(
                metric=data.name or "value",
                timestamps=timestamps.tolist(),
                predictions=predictions,
                lower_bound=predictions - std,
                upper_bound=predictions + std,
                model_type="LSTM",
                metrics={'mse': model.evaluate(X_scaled, y_scaled, verbose=0)}
            )
            
        except Exception as e:
            logger.error(f"LSTM forecast failed: {e}")
            return self._fallback_forecast(data)
            
    def _forecast_ensemble(self, data: pd.Series) -> ForecastResult:
        """Ensemble forecasting combining multiple methods"""
        methods = ['arima', 'prophet', 'exponential_smoothing']
        forecasts = []
        weights = []
        
        for method in methods:
            try:
                forecast = self.forecast(data, method)
                forecasts.append(forecast)
                # Weight by inverse of error metric
                weight = 1 / (forecast.metrics.get('mape', 10) + 1)
                weights.append(weight)
            except:
                continue
                
        if not forecasts:
            return self._fallback_forecast(data)
            
        # Normalize weights
        weights = np.array(weights) / np.sum(weights)
        
        # Weighted average
        predictions = np.zeros(self.config.forecast_horizon)
        lower_bounds = np.zeros(self.config.forecast_horizon)
        upper_bounds = np.zeros(self.config.forecast_horizon)
        
        for forecast, weight in zip(forecasts, weights):
            predictions += forecast.predictions * weight
            lower_bounds += forecast.lower_bound * weight
            upper_bounds += forecast.upper_bound * weight
            
        return ForecastResult(
            metric=data.name or "value",
            timestamps=forecasts[0].timestamps,
            predictions=predictions,
            lower_bound=lower_bounds,
            upper_bound=upper_bounds,
            model_type="Ensemble",
            metrics={'ensemble_weights': weights.tolist()}
        )
        
    def _forecast_exponential_smoothing(self, data: pd.Series) -> ForecastResult:
        """Exponential smoothing forecast"""
        try:
            # Determine model type
            if len(data) > 2 * self.config.seasonal_period:
                model = ExponentialSmoothing(
                    data,
                    seasonal_periods=self.config.seasonal_period,
                    trend='add',
                    seasonal='add'
                )
            else:
                model = ExponentialSmoothing(data, trend='add')
                
            # Fit model
            fitted_model = model.fit()
            
            # Forecast
            forecast = fitted_model.forecast(self.config.forecast_horizon)
            
            # Calculate confidence intervals
            residuals = data - fitted_model.fittedvalues
            std_error = np.std(residuals)
            z_score = stats.norm.ppf((1 + self.config.confidence_level) / 2)
            margin = z_score * std_error
            
            # Generate timestamps
            last_timestamp = data.index[-1]
            timestamps = pd.date_range(
                start=last_timestamp + pd.Timedelta(hours=1),
                periods=self.config.forecast_horizon,
                freq='H'
            )
            
            return ForecastResult(
                metric=data.name or "value",
                timestamps=timestamps.tolist(),
                predictions=forecast.values,
                lower_bound=forecast.values - margin,
                upper_bound=forecast.values + margin,
                model_type="ExponentialSmoothing",
                metrics={'aic': fitted_model.aic}
            )
            
        except Exception as e:
            logger.error(f"Exponential smoothing failed: {e}")
            return self._fallback_forecast(data)
            
    def _create_sequences(self, data: np.ndarray, seq_length: int = 24) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM"""
        X, y = [], []
        for i in range(len(data) - seq_length):
            X.append(data[i:i+seq_length])
            y.append(data[i+seq_length])
        return np.array(X), np.array(y)
        
    def _build_lstm_model(self, seq_length: int) -> tf.keras.Model:
        """Build LSTM model"""
        model = Sequential([
            LSTM(self.config.lstm_units, return_sequences=True, 
                 input_shape=(seq_length, 1)),
            Dropout(self.config.dropout_rate),
            LSTM(self.config.lstm_units // 2),
            Dropout(self.config.dropout_rate),
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse')
        return model
        
    def _calculate_mape(self, data: pd.Series, model: Prophet, df: pd.DataFrame) -> float:
        """Calculate MAPE for Prophet model"""
        # In-sample predictions
        predictions = model.predict(df)
        actual = data.values
        predicted = predictions['yhat'].values[:len(actual)]
        
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100
        return mape
        
    def _fallback_forecast(self, data: pd.Series) -> ForecastResult:
        """Simple fallback forecast using moving average"""
        # Use last value as forecast
        last_value = data.iloc[-1]
        
        # Generate timestamps
        last_timestamp = data.index[-1]
        timestamps = pd.date_range(
            start=last_timestamp + pd.Timedelta(hours=1),
            periods=self.config.forecast_horizon,
            freq='H'
        )
        
        # Simple linear trend
        if len(data) > 10:
            trend = (data.iloc[-1] - data.iloc[-10]) / 10
        else:
            trend = 0
            
        predictions = np.array([last_value + trend * i for i in range(1, self.config.forecast_horizon + 1)])
        
        # Wide confidence intervals for fallback
        std = np.std(data) * 2
        
        return ForecastResult(
            metric=data.name or "value",
            timestamps=timestamps.tolist(),
            predictions=predictions,
            lower_bound=predictions - std,
            upper_bound=predictions + std,
            model_type="Fallback",
            metrics={'method': 'moving_average'}
        )

class AnomalyDetector:
    """Multi-method anomaly detection"""
    
    def __init__(self, config: PredictiveConfig):
        self.config = config
        self.models = {}
        self.threshold_models = {}
        
    def detect_anomalies(self, data: pd.DataFrame, method: str = "ensemble") -> List[AnomalyResult]:
        """Detect anomalies in data"""
        if method == "ensemble":
            return self._ensemble_detection(data)
        elif method == "isolation_forest":
            return self._isolation_forest_detection(data)
        elif method == "autoencoder":
            return self._autoencoder_detection(data)
        elif method == "statistical":
            return self._statistical_detection(data)
        else:
            return self._lstm_anomaly_detection(data)
            
    def _ensemble_detection(self, data: pd.DataFrame) -> List[AnomalyResult]:
        """Ensemble anomaly detection"""
        methods = ['isolation_forest', 'statistical', 'lof']
        all_results = defaultdict(list)
        
        for method in methods:
            try:
                if method == 'isolation_forest':
                    results = self._isolation_forest_detection(data)
                elif method == 'statistical':
                    results = self._statistical_detection(data)
                elif method == 'lof':
                    results = self._lof_detection(data)
                    
                for result in results:
                    key = (result.timestamp, result.metric)
                    all_results[key].append(result)
            except:
                continue
                
        # Combine results
        final_results = []
        for key, results in all_results.items():
            # Majority voting
            anomaly_votes = sum(1 for r in results if r.is_anomaly)
            is_anomaly = anomaly_votes >= len(methods) // 2 + 1
            
            # Average anomaly score
            avg_score = np.mean([r.anomaly_score for r in results])
            
            if is_anomaly:
                result = results[0]  # Use first result as template
                result.is_anomaly = True
                result.anomaly_score = avg_score
                result.anomaly_type = "ensemble"
                result.explanation = f"Detected by {anomaly_votes}/{len(methods)} methods"
                final_results.append(result)
                
        anomalies_detected.inc(len(final_results))
        return final_results
        
    def _isolation_forest_detection(self, data: pd.DataFrame) -> List[AnomalyResult]:
        """Isolation Forest anomaly detection"""
        results = []
        
        # Prepare data
        X = data.select_dtypes(include=[np.number]).values
        timestamps = data.index
        
        # Train model
        model = IsolationForest(
            contamination=self.config.contamination_rate,
            random_state=42
        )
        
        # Fit and predict
        predictions = model.fit_predict(X)
        scores = model.score_samples(X)
        
        # Normalize scores to [0, 1]
        scores = (scores - scores.min()) / (scores.max() - scores.min())
        
        # Process results
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:  # Anomaly
                for j, col in enumerate(data.columns):
                    if isinstance(data.iloc[i, j], (int, float)):
                        results.append(AnomalyResult(
                            timestamp=timestamps[i],
                            metric=col,
                            value=data.iloc[i, j],
                            expected_value=data[col].median(),
                            anomaly_score=score,
                            is_anomaly=True,
                            anomaly_type="isolation_forest",
                            explanation=f"Isolated from normal patterns (score: {score:.3f})"
                        ))
                        
        return results
        
    def _autoencoder_detection(self, data: pd.DataFrame) -> List[AnomalyResult]:
        """Autoencoder-based anomaly detection"""
        results = []
        
        # Prepare data
        X = data.select_dtypes(include=[np.number]).values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Build autoencoder
        input_dim = X.shape[1]
        encoding_dim = max(2, input_dim // 4)
        
        # Encoder
        input_layer = Input(shape=(input_dim,))
        encoder = Dense(encoding_dim * 2, activation='relu')(input_layer)
        encoder = Dense(encoding_dim, activation='relu')(encoder)
        
        # Decoder
        decoder = Dense(encoding_dim * 2, activation='relu')(encoder)
        decoder = Dense(input_dim, activation='linear')(decoder)
        
        # Model
        autoencoder = Model(inputs=input_layer, outputs=decoder)
        autoencoder.compile(optimizer='adam', loss='mse')
        
        # Train
        autoencoder.fit(
            X_scaled, X_scaled,
            epochs=50,
            batch_size=32,
            verbose=0,
            validation_split=0.1
        )
        
        # Detect anomalies
        reconstructions = autoencoder.predict(X_scaled, verbose=0)
        mse = np.mean(np.power(X_scaled - reconstructions, 2), axis=1)
        
        # Threshold
        threshold = np.percentile(mse, (1 - self.config.contamination_rate) * 100)
        
        # Process results
        for i, error in enumerate(mse):
            if error > threshold:
                for j, col in enumerate(data.columns):
                    if isinstance(data.iloc[i, j], (int, float)):
                        results.append(AnomalyResult(
                            timestamp=data.index[i],
                            metric=col,
                            value=data.iloc[i, j],
                            expected_value=scaler.inverse_transform(reconstructions[i].reshape(1, -1))[0, j],
                            anomaly_score=error / threshold,
                            is_anomaly=True,
                            anomaly_type="autoencoder",
                            explanation=f"High reconstruction error: {error:.3f}"
                        ))
                        
        return results
        
    def _statistical_detection(self, data: pd.DataFrame) -> List[AnomalyResult]:
        """Statistical anomaly detection"""
        results = []
        
        for col in data.select_dtypes(include=[np.number]).columns:
            series = data[col]
            
            # Calculate statistics
            mean = series.mean()
            std = series.std()
            
            # Z-score method
            z_scores = np.abs((series - mean) / std)
            threshold = 3  # 3 standard deviations
            
            # IQR method
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Detect anomalies
            for i, (value, z_score) in enumerate(zip(series, z_scores)):
                is_anomaly = z_score > threshold or value < lower_bound or value > upper_bound
                
                if is_anomaly:
                    results.append(AnomalyResult(
                        timestamp=data.index[i],
                        metric=col,
                        value=value,
                        expected_value=mean,
                        anomaly_score=min(z_score / threshold, 1.0),
                        is_anomaly=True,
                        anomaly_type="statistical",
                        explanation=f"Z-score: {z_score:.2f}, outside bounds: [{lower_bound:.2f}, {upper_bound:.2f}]"
                    ))
                    
        return results
        
    def _lof_detection(self, data: pd.DataFrame) -> List[AnomalyResult]:
        """Local Outlier Factor detection"""
        results = []
        
        # Prepare data
        X = data.select_dtypes(include=[np.number]).values
        
        # Train LOF
        lof = LOF(contamination=self.config.contamination_rate)
        predictions = lof.fit_predict(X)
        scores = lof.negative_outlier_factor_
        
        # Normalize scores
        scores = (scores - scores.min()) / (scores.max() - scores.min())
        
        # Process results
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:  # Anomaly
                for j, col in enumerate(data.columns):
                    if isinstance(data.iloc[i, j], (int, float)):
                        results.append(AnomalyResult(
                            timestamp=data.index[i],
                            metric=col,
                            value=data.iloc[i, j],
                            expected_value=data[col].median(),
                            anomaly_score=score,
                            is_anomaly=True,
                            anomaly_type="lof",
                            explanation=f"Local outlier with score: {score:.3f}"
                        ))
                        
        return results
        
    def _lstm_anomaly_detection(self, data: pd.DataFrame) -> List[AnomalyResult]:
        """LSTM-based anomaly detection"""
        results = []
        
        for col in data.select_dtypes(include=[np.number]).columns:
            series = data[col].values
            
            # Create sequences
            seq_length = min(24, len(series) // 10)
            X, y = [], []
            
            for i in range(len(series) - seq_length):
                X.append(series[i:i+seq_length])
                y.append(series[i+seq_length])
                
            if not X:
                continue
                
            X = np.array(X)
            y = np.array(y)
            
            # Scale data
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X.reshape(-1, 1)).reshape(X.shape)
            y_scaled = scaler.transform(y.reshape(-1, 1)).flatten()
            
            # Build simple LSTM
            model = Sequential([
                LSTM(32, input_shape=(seq_length, 1)),
                Dense(1)
            ])
            model.compile(optimizer='adam', loss='mse')
            
            # Train
            model.fit(
                X_scaled.reshape(-1, seq_length, 1),
                y_scaled,
                epochs=20,
                batch_size=32,
                verbose=0
            )
            
            # Predict and calculate errors
            predictions = model.predict(X_scaled.reshape(-1, seq_length, 1), verbose=0).flatten()
            errors = np.abs(y_scaled - predictions)
            
            # Threshold
            threshold = np.percentile(errors, (1 - self.config.contamination_rate) * 100)
            
            # Detect anomalies
            for i, error in enumerate(errors):
                if error > threshold:
                    results.append(AnomalyResult(
                        timestamp=data.index[i + seq_length],
                        metric=col,
                        value=y[i],
                        expected_value=scaler.inverse_transform(predictions[i].reshape(1, -1))[0, 0],
                        anomaly_score=error / threshold,
                        is_anomaly=True,
                        anomaly_type="lstm",
                        explanation=f"Unexpected pattern, error: {error:.3f}"
                    ))
                    
        return results

class UserBehaviorPredictor:
    """Predict user behavior patterns"""
    
    def __init__(self, config: PredictiveConfig):
        self.config = config
        self.sequence_model = None
        self.action_encoder = {}
        self.user_profiles = {}
        
    def train(self, user_sequences: Dict[str, List[str]]):
        """Train user behavior model"""
        # Encode actions
        all_actions = set()
        for sequences in user_sequences.values():
            all_actions.update(sequences)
            
        self.action_encoder = {action: i for i, action in enumerate(sorted(all_actions))}
        
        # Prepare training data
        X, y = [], []
        for user_id, sequences in user_sequences.items():
            encoded = [self.action_encoder.get(action, 0) for action in sequences]
            
            for i in range(len(encoded) - self.config.sequence_length - 1):
                X.append(encoded[i:i+self.config.sequence_length])
                y.append(encoded[i+self.config.sequence_length])
                
        X = np.array(X)
        y = np.array(y)
        
        # Build transformer model
        self.sequence_model = self._build_transformer_model(len(self.action_encoder))
        
        # Train
        self.sequence_model.fit(
            X, y,
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            validation_split=0.2,
            verbose=0
        )
        
        logger.info(f"Behavior model trained on {len(user_sequences)} users")
        
    def predict_next_action(self, user_id: str, recent_actions: List[str]) -> BehaviorPrediction:
        """Predict next user action"""
        if not self.sequence_model:
            raise ValueError("Model not trained")
            
        # Encode recent actions
        encoded = [self.action_encoder.get(action, 0) for action in recent_actions[-self.config.sequence_length:]]
        
        # Pad if necessary
        if len(encoded) < self.config.sequence_length:
            encoded = [0] * (self.config.sequence_length - len(encoded)) + encoded
            
        # Predict
        X = np.array([encoded])
        predictions = self.sequence_model.predict(X, verbose=0)[0]
        
        # Get top predictions
        top_indices = np.argsort(predictions)[-5:][::-1]
        
        # Decode actions
        action_decoder = {i: action for action, i in self.action_encoder.items()}
        
        predicted_action = action_decoder.get(top_indices[0], "unknown")
        confidence = float(predictions[top_indices[0]])
        
        alternatives = [
            (action_decoder.get(idx, "unknown"), float(predictions[idx]))
            for idx in top_indices[1:]
        ]
        
        # Extract features
        features = self._extract_user_features(user_id, recent_actions)
        
        predictions_made.inc()
        
        return BehaviorPrediction(
            user_id=user_id,
            timestamp=datetime.now(),
            predicted_action=predicted_action,
            confidence=confidence,
            alternative_actions=alternatives,
            features=features
        )
        
    def _build_transformer_model(self, num_actions: int) -> tf.keras.Model:
        """Build transformer model for sequence prediction"""
        # Simplified transformer
        inputs = Input(shape=(self.config.sequence_length,))
        
        # Embedding
        x = tf.keras.layers.Embedding(num_actions, self.config.embedding_dim)(inputs)
        
        # Self-attention
        attention = tf.keras.layers.MultiHeadAttention(
            num_heads=4,
            key_dim=self.config.embedding_dim
        )(x, x)
        
        x = tf.keras.layers.Add()([x, attention])
        x = tf.keras.layers.LayerNormalization()(x)
        
        # Feed forward
        x = tf.keras.layers.GlobalAveragePooling1D()(x)
        x = Dense(self.config.embedding_dim, activation='relu')(x)
        x = Dropout(self.config.dropout_rate)(x)
        
        # Output
        outputs = Dense(num_actions, activation='softmax')(x)
        
        model = Model(inputs=inputs, outputs=outputs)
        model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        
        return model
        
    def _extract_user_features(self, user_id: str, recent_actions: List[str]) -> Dict[str, Any]:
        """Extract user behavior features"""
        features = {
            'action_diversity': len(set(recent_actions)) / max(len(recent_actions), 1),
            'action_frequency': Counter(recent_actions).most_common(5),
            'session_length': len(recent_actions),
            'time_of_day': datetime.now().hour,
            'day_of_week': datetime.now().weekday()
        }
        
        # User profile features
        if user_id in self.user_profiles:
            features.update(self.user_profiles[user_id])
            
        return features

class ResourceUsagePredictor:
    """Predict resource usage and optimize allocation"""
    
    def __init__(self, config: PredictiveConfig):
        self.config = config
        self.models = {}
        self.scalers = {}
        
    def predict_usage(self, historical_data: pd.DataFrame, 
                     resource_type: str,
                     horizon: int = 24) -> Dict[str, Any]:
        """Predict future resource usage"""
        if resource_type not in historical_data.columns:
            raise ValueError(f"Resource {resource_type} not found in data")
            
        # Time series forecasting
        forecaster = TimeSeriesForecaster(self.config)
        forecast = forecaster.forecast(historical_data[resource_type])
        
        # Capacity planning
        capacity_plan = self._plan_capacity(forecast, resource_type)
        
        # Cost optimization
        cost_optimization = self._optimize_costs(forecast, capacity_plan)
        
        predictions_made.inc()
        
        return {
            'resource': resource_type,
            'forecast': {
                'timestamps': forecast.timestamps,
                'values': forecast.predictions.tolist(),
                'confidence_interval': {
                    'lower': forecast.lower_bound.tolist(),
                    'upper': forecast.upper_bound.tolist()
                }
            },
            'capacity_planning': capacity_plan,
            'cost_optimization': cost_optimization,
            'metrics': forecast.metrics
        }
        
    def detect_resource_anomalies(self, current_usage: Dict[str, float]) -> List[Dict[str, Any]]:
        """Detect anomalies in resource usage"""
        anomalies = []
        
        for resource, value in current_usage.items():
            if resource in self.models:
                # Use trained model
                expected = self.models[resource].predict([[value]])[0]
                deviation = abs(value - expected) / expected
                
                if deviation > 0.3:  # 30% deviation
                    anomalies.append({
                        'resource': resource,
                        'current_value': value,
                        'expected_value': expected,
                        'deviation': deviation,
                        'severity': 'high' if deviation > 0.5 else 'medium',
                        'recommendation': self._get_resource_recommendation(resource, value, expected)
                    })
                    
        anomalies_detected.inc(len(anomalies))
        return anomalies
        
    def optimize_allocation(self, current_usage: Dict[str, float],
                          constraints: Dict[str, Any]) -> Dict[str, float]:
        """Optimize resource allocation"""
        # Define optimization problem
        resources = list(current_usage.keys())
        current_values = list(current_usage.values())
        
        # Objective: minimize cost while meeting performance requirements
        def objective(x):
            cost = 0
            for i, resource in enumerate(resources):
                # Simple cost model
                if resource == 'cpu_usage':
                    cost += x[i] * 0.1  # CPU cost per unit
                elif resource == 'memory_usage':
                    cost += x[i] * 0.05  # Memory cost per unit
                elif resource == 'disk_io':
                    cost += x[i] * 0.02  # Disk cost per unit
                    
            # Penalty for deviating from current usage
            deviation_penalty = np.sum((x - current_values) ** 2) * 0.01
            
            return cost + deviation_penalty
            
        # Constraints
        cons = []
        
        # Performance constraint
        cons.append({
            'type': 'ineq',
            'fun': lambda x: np.sum(x) - np.sum(current_values) * 0.8  # At least 80% of current
        })
        
        # Resource limits
        bounds = []
        for i, resource in enumerate(resources):
            max_value = constraints.get(f'{resource}_max', current_values[i] * 1.5)
            bounds.append((0, max_value))
            
        # Optimize
        result = minimize(
            objective,
            current_values,
            method='SLSQP',
            bounds=bounds,
            constraints=cons
        )
        
        optimized = {resource: value for resource, value in zip(resources, result.x)}
        
        return optimized
        
    def _plan_capacity(self, forecast: ForecastResult, resource_type: str) -> Dict[str, Any]:
        """Plan capacity based on forecast"""
        # Peak detection
        peaks = self._find_peaks(forecast.predictions)
        
        # Buffer calculation
        buffer_size = np.percentile(forecast.predictions, 95) * 0.2  # 20% buffer
        
        # Scaling recommendations
        current_capacity = forecast.predictions[0]  # Assume first value is current
        max_predicted = np.max(forecast.upper_bound)
        
        scaling_factor = max_predicted / current_capacity
        
        return {
            'recommended_capacity': float(max_predicted + buffer_size),
            'scaling_factor': float(scaling_factor),
            'peak_times': peaks,
            'buffer_size': float(buffer_size),
            'scaling_strategy': 'auto-scale' if scaling_factor > 1.5 else 'fixed'
        }
        
    def _optimize_costs(self, forecast: ForecastResult, capacity_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize costs based on forecast and capacity plan"""
        # Simple cost model
        fixed_cost_per_unit = 0.1
        variable_cost_per_unit = 0.05
        
        # Current approach cost
        current_cost = np.sum(forecast.predictions) * (fixed_cost_per_unit + variable_cost_per_unit)
        
        # Optimized approach cost
        if capacity_plan['scaling_strategy'] == 'auto-scale':
            # Auto-scaling reduces fixed costs
            optimized_cost = (
                np.sum(forecast.predictions) * variable_cost_per_unit +
                capacity_plan['recommended_capacity'] * fixed_cost_per_unit * 0.3
            )
        else:
            optimized_cost = capacity_plan['recommended_capacity'] * fixed_cost_per_unit * 24
            
        savings = current_cost - optimized_cost
        
        return {
            'current_cost': float(current_cost),
            'optimized_cost': float(optimized_cost),
            'potential_savings': float(max(savings, 0)),
            'savings_percentage': float(max(savings / current_cost * 100, 0)),
            'recommendations': [
                "Enable auto-scaling" if capacity_plan['scaling_strategy'] == 'auto-scale' else "Use reserved instances",
                f"Set maximum capacity to {capacity_plan['recommended_capacity']:.2f}",
                "Consider spot instances for non-critical workloads" if savings > 0 else "Current allocation is optimal"
            ]
        }
        
    def _find_peaks(self, data: np.ndarray) -> List[int]:
        """Find peaks in time series data"""
        peaks = []
        for i in range(1, len(data) - 1):
            if data[i] > data[i-1] and data[i] > data[i+1]:
                peaks.append(i)
        return peaks
        
    def _get_resource_recommendation(self, resource: str, current: float, expected: float) -> str:
        """Get recommendation for resource anomaly"""
        if current > expected:
            if resource == 'cpu_usage':
                return "Check for CPU-intensive processes or infinite loops"
            elif resource == 'memory_usage':
                return "Check for memory leaks or large data structures"
            elif resource == 'disk_io':
                return "Check for excessive logging or database operations"
            else:
                return "Investigate increased resource consumption"
        else:
            return f"Resource usage lower than expected, consider scaling down"

class TrendAnalyzer:
    """Analyze trends and patterns in data"""
    
    def __init__(self, config: PredictiveConfig):
        self.config = config
        
    def analyze_trends(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive trend analysis"""
        results = {}
        
        for column in data.select_dtypes(include=[np.number]).columns:
            series = data[column]
            
            # Trend detection
            trend = self._detect_trend(series)
            
            # Seasonality detection
            seasonality = self._detect_seasonality(series)
            
            # Change points
            change_points = self._detect_change_points(series)
            
            # Forecast trend
            future_trend = self._forecast_trend(series)
            
            results[column] = {
                'current_trend': trend,
                'seasonality': seasonality,
                'change_points': change_points,
                'future_trend': future_trend,
                'statistics': {
                    'mean': float(series.mean()),
                    'std': float(series.std()),
                    'trend_strength': float(self._calculate_trend_strength(series))
                }
            }
            
        return results
        
    def _detect_trend(self, series: pd.Series) -> Dict[str, Any]:
        """Detect trend in time series"""
        # Linear regression
        x = np.arange(len(series))
        y = series.values
        
        # Remove NaN values
        mask = ~np.isnan(y)
        x = x[mask]
        y = y[mask]
        
        if len(x) < 2:
            return {'direction': 'unknown', 'strength': 0}
            
        # Fit linear trend
        z = np.polyfit(x, y, 1)
        slope = z[0]
        
        # Determine trend direction
        if abs(slope) < 0.001:
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'
            
        # Calculate R-squared
        p = np.poly1d(z)
        yhat = p(x)
        ybar = np.mean(y)
        ssreg = np.sum((yhat - ybar) ** 2)
        sstot = np.sum((y - ybar) ** 2)
        r_squared = ssreg / sstot if sstot > 0 else 0
        
        return {
            'direction': direction,
            'slope': float(slope),
            'strength': float(r_squared),
            'percentage_change': float((y[-1] - y[0]) / y[0] * 100) if y[0] != 0 else 0
        }
        
    def _detect_seasonality(self, series: pd.Series) -> Dict[str, Any]:
        """Detect seasonality in time series"""
        if len(series) < 2 * self.config.seasonal_period:
            return {'has_seasonality': False}
            
        try:
            # Seasonal decomposition
            decomposition = seasonal_decompose(
                series,
                period=self.config.seasonal_period,
                extrapolate_trend='freq'
            )
            
            # Calculate seasonal strength
            seasonal_strength = np.std(decomposition.seasonal) / np.std(series)
            
            # Find dominant periods using FFT
            fft = np.fft.fft(series.dropna())
            frequencies = np.fft.fftfreq(len(fft))
            
            # Get top frequencies
            magnitudes = np.abs(fft)
            top_freq_idx = np.argsort(magnitudes)[-5:]
            dominant_periods = [1/abs(frequencies[i]) for i in top_freq_idx if frequencies[i] != 0]
            
            return {
                'has_seasonality': seasonal_strength > 0.1,
                'seasonal_strength': float(seasonal_strength),
                'period': self.config.seasonal_period,
                'dominant_periods': dominant_periods[:3]
            }
            
        except:
            return {'has_seasonality': False}
            
    def _detect_change_points(self, series: pd.Series) -> List[Dict[str, Any]]:
        """Detect change points in time series"""
        change_points = []
        
        if len(series) < 20:
            return change_points
            
        # Simple change point detection using cumulative sum
        y = series.dropna().values
        
        # Calculate CUSUM
        mean = np.mean(y)
        cusum = np.cumsum(y - mean)
        
        # Find change points
        for i in range(10, len(cusum) - 10):
            # Check if there's a significant change in slope
            before_slope = np.polyfit(range(i-10, i), cusum[i-10:i], 1)[0]
            after_slope = np.polyfit(range(i, i+10), cusum[i:i+10], 1)[0]
            
            slope_change = abs(after_slope - before_slope)
            
            if slope_change > np.std(y):
                change_points.append({
                    'index': i,
                    'timestamp': series.index[i].isoformat() if hasattr(series.index[i], 'isoformat') else str(i),
                    'magnitude': float(slope_change),
                    'type': 'increase' if after_slope > before_slope else 'decrease'
                })
                
        return change_points[:5]  # Return top 5 change points
        
    def _forecast_trend(self, series: pd.Series) -> Dict[str, Any]:
        """Forecast future trend"""
        current_trend = self._detect_trend(series)
        
        # Simple trend extrapolation
        if current_trend['direction'] == 'stable':
            forecast_direction = 'stable'
            confidence = 0.8
        elif current_trend['strength'] > 0.7:
            forecast_direction = current_trend['direction']
            confidence = current_trend['strength']
        else:
            forecast_direction = 'uncertain'
            confidence = 0.5
            
        # Estimate future values
        last_value = series.iloc[-1]
        if current_trend['direction'] == 'increasing':
            future_value = last_value * (1 + current_trend['slope'] * 0.1)
        elif current_trend['direction'] == 'decreasing':
            future_value = last_value * (1 - abs(current_trend['slope']) * 0.1)
        else:
            future_value = last_value
            
        return {
            'direction': forecast_direction,
            'confidence': float(confidence),
            'estimated_value': float(future_value),
            'horizon': '24 hours'
        }
        
    def _calculate_trend_strength(self, series: pd.Series) -> float:
        """Calculate overall trend strength"""
        # Multiple methods to assess trend strength
        
        # Method 1: Mann-Kendall test
        n = len(series)
        if n < 10:
            return 0.0
            
        s = 0
        for i in range(n-1):
            for j in range(i+1, n):
                s += np.sign(series.iloc[j] - series.iloc[i])
                
        # Calculate variance
        var_s = n * (n - 1) * (2 * n + 5) / 18
        
        if var_s > 0:
            z = s / np.sqrt(var_s)
            return min(abs(z) / 3, 1.0)  # Normalize to [0, 1]
        else:
            return 0.0

class NexusPredictiveAnalytics:
    """Main predictive analytics system"""
    
    def __init__(self, config: Optional[PredictiveConfig] = None):
        self.config = config or PredictiveConfig()
        
        # Initialize components
        self.forecaster = TimeSeriesForecaster(self.config)
        self.anomaly_detector = AnomalyDetector(self.config)
        self.behavior_predictor = UserBehaviorPredictor(self.config)
        self.resource_predictor = ResourceUsagePredictor(self.config)
        self.trend_analyzer = TrendAnalyzer(self.config)
        
        logger.info("NEXUS Predictive Analytics initialized")
        
    async def forecast_metrics(self, data: pd.DataFrame, 
                             metrics: List[str],
                             horizon: int = 24) -> Dict[str, ForecastResult]:
        """Forecast multiple metrics"""
        results = {}
        
        for metric in metrics:
            if metric in data.columns:
                forecast = self.forecaster.forecast(data[metric])
                results[metric] = forecast
                
                # Update accuracy metric
                if hasattr(forecast, 'metrics') and 'mape' in forecast.metrics:
                    accuracy = 100 - forecast.metrics['mape']
                    prediction_accuracy.labels(model=forecast.model_type).set(accuracy)
                    
        return results
        
    async def detect_anomalies(self, data: pd.DataFrame) -> List[AnomalyResult]:
        """Detect anomalies across all metrics"""
        return self.anomaly_detector.detect_anomalies(data)
        
    async def predict_user_behavior(self, user_id: str, 
                                  recent_actions: List[str]) -> BehaviorPrediction:
        """Predict next user action"""
        return self.behavior_predictor.predict_next_action(user_id, recent_actions)
        
    async def predict_resource_usage(self, historical_data: pd.DataFrame) -> Dict[str, Any]:
        """Predict resource usage for all resource types"""
        results = {}
        
        for resource in self.config.resource_metrics:
            if resource in historical_data.columns:
                prediction = self.resource_predictor.predict_usage(
                    historical_data, resource
                )
                results[resource] = prediction
                
        return results
        
    async def analyze_trends(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends in data"""
        return self.trend_analyzer.analyze_trends(data)
        
    async def get_insights(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Get comprehensive insights from data"""
        insights = {
            'timestamp': datetime.now().isoformat(),
            'data_summary': {
                'rows': len(data),
                'columns': len(data.columns),
                'time_range': {
                    'start': str(data.index[0]),
                    'end': str(data.index[-1])
                }
            }
        }
        
        # Forecast key metrics
        numeric_cols = data.select_dtypes(include=[np.number]).columns[:5]
        forecasts = await self.forecast_metrics(data, numeric_cols.tolist())
        
        insights['forecasts'] = {
            metric: {
                'next_value': float(forecast.predictions[0]),
                'trend': 'up' if forecast.predictions[-1] > forecast.predictions[0] else 'down',
                'confidence': float(forecast.metrics.get('confidence', 0.8))
            }
            for metric, forecast in forecasts.items()
        }
        
        # Detect anomalies
        anomalies = await self.detect_anomalies(data)
        insights['anomalies'] = {
            'count': len(anomalies),
            'metrics_affected': list(set(a.metric for a in anomalies)),
            'recent': [
                {
                    'metric': a.metric,
                    'value': a.value,
                    'score': a.anomaly_score,
                    'type': a.anomaly_type
                }
                for a in anomalies[-5:]
            ]
        }
        
        # Analyze trends
        trends = await self.analyze_trends(data)
        insights['trends'] = {
            metric: {
                'direction': info['current_trend']['direction'],
                'strength': info['current_trend']['strength'],
                'seasonality': info['seasonality']['has_seasonality']
            }
            for metric, info in trends.items()
        }
        
        return insights

# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize predictive analytics
        analytics = NexusPredictiveAnalytics()
        
        # Generate sample data
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='H')
        data = pd.DataFrame({
            'timestamp': dates,
            'cpu_usage': np.random.normal(50, 10, len(dates)) + 10 * np.sin(np.arange(len(dates)) * 2 * np.pi / 24),
            'memory_usage': np.random.normal(60, 15, len(dates)),
            'requests': np.random.poisson(100, len(dates))
        })
        data.set_index('timestamp', inplace=True)
        
        # Add some anomalies
        data.loc[data.index[100], 'cpu_usage'] = 95
        data.loc[data.index[200], 'memory_usage'] = 95
        
        # Get insights
        insights = await analytics.get_insights(data)
        
        print("Predictive Analytics Insights:")
        print(f"Data summary: {insights['data_summary']}")
        print(f"\nForecasts:")
        for metric, forecast in insights['forecasts'].items():
            print(f"  {metric}: {forecast['next_value']:.2f} ({forecast['trend']})")
            
        print(f"\nAnomalies detected: {insights['anomalies']['count']}")
        print(f"Metrics affected: {insights['anomalies']['metrics_affected']}")
        
        print(f"\nTrends:")
        for metric, trend in insights['trends'].items():
            print(f"  {metric}: {trend['direction']} (strength: {trend['strength']:.2f})")
            
        # Forecast specific metric
        cpu_forecast = await analytics.forecast_metrics(data, ['cpu_usage'], horizon=24)
        print(f"\nCPU usage forecast for next 24 hours:")
        print(f"  Model: {cpu_forecast['cpu_usage'].model_type}")
        print(f"  First prediction: {cpu_forecast['cpu_usage'].predictions[0]:.2f}")
        print(f"  Last prediction: {cpu_forecast['cpu_usage'].predictions[-1]:.2f}")
        
    asyncio.run(main())