"""
ML Model Loader and Manager
Handles downloading, caching, and loading of machine learning models
"""

import os
import json
import hashlib
import requests
import torch
import tensorflow as tf
from pathlib import Path
import logging
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import shutil
import zipfile
import tarfile
from tqdm import tqdm
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Types of ML models"""
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    ONNX = "onnx"
    TFLITE = "tflite"
    OPENCV = "opencv"
    CUSTOM = "custom"


class ModelPriority(Enum):
    """Model priority for loading"""
    HIGH = 1      # Full models with best accuracy
    MEDIUM = 2    # Balanced models
    LOW = 3       # Lightweight models for performance


class ModelLoader:
    """Manages ML model downloading, caching, and loading"""
    
    def __init__(self, cache_dir: str = None, config_path: str = None):
        """Initialize model loader"""
        self.cache_dir = Path(cache_dir or os.path.expanduser("~/.nexus/models"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = self._load_config(config_path)
        self.loaded_models = {}
        self.download_locks = {}
        self.device = self._get_device()
        
        # Model registry
        self.model_registry = self._init_model_registry()
        
        # Performance monitoring
        self.load_times = {}
        self.model_sizes = {}
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration"""
        default_config = {
            "max_cache_size_gb": 10,
            "auto_download": True,
            "prefer_quantized": False,
            "max_concurrent_downloads": 3,
            "download_timeout": 3600,
            "model_sources": {
                "huggingface": "https://huggingface.co",
                "torch_hub": "https://pytorch.org/hub",
                "tf_hub": "https://tfhub.dev"
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config.get('model_loader', {}))
            except Exception as e:
                logger.warning(f"Could not load config: {e}")
        
        return default_config
    
    def _get_device(self) -> torch.device:
        """Determine best available device"""
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif torch.backends.mps.is_available():
            return torch.device("mps")
        else:
            return torch.device("cpu")
    
    def _init_model_registry(self) -> Dict[str, Dict[str, Any]]:
        """Initialize registry of available models"""
        return {
            # Visual models
            "yolov5s": {
                "type": ModelType.PYTORCH,
                "url": "ultralytics/yolov5",
                "model_name": "yolov5s",
                "size_mb": 14,
                "priority": ModelPriority.MEDIUM,
                "description": "YOLOv5 small object detection",
                "fallback": "yolov5n"
            },
            "yolov5n": {
                "type": ModelType.PYTORCH,
                "url": "ultralytics/yolov5",
                "model_name": "yolov5n",
                "size_mb": 4,
                "priority": ModelPriority.LOW,
                "description": "YOLOv5 nano object detection"
            },
            "deepface_emotion": {
                "type": ModelType.TENSORFLOW,
                "url": "https://github.com/serengil/deepface_models/releases/download/v1.0/facial_expression_model_weights.h5",
                "size_mb": 100,
                "priority": ModelPriority.HIGH,
                "description": "Facial emotion recognition",
                "fallback": "fer_light"
            },
            "fer_light": {
                "type": ModelType.TENSORFLOW,
                "url": "https://github.com/justinshenk/fer/releases/download/v1.0.0/fer2013_mini_XCEPTION.102-0.66.hdf5",
                "size_mb": 30,
                "priority": ModelPriority.LOW,
                "description": "Lightweight emotion recognition"
            },
            
            # Audio models
            "wav2vec2_base": {
                "type": ModelType.PYTORCH,
                "url": "facebook/wav2vec2-base-960h",
                "size_mb": 360,
                "priority": ModelPriority.HIGH,
                "description": "Speech recognition and analysis",
                "fallback": "wav2vec2_small"
            },
            "wav2vec2_small": {
                "type": ModelType.PYTORCH,
                "url": "facebook/wav2vec2-base-100h",
                "size_mb": 180,
                "priority": ModelPriority.MEDIUM,
                "description": "Smaller speech model"
            },
            "emotion_recognition": {
                "type": ModelType.PYTORCH,
                "url": "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
                "size_mb": 1200,
                "priority": ModelPriority.HIGH,
                "description": "Audio emotion recognition",
                "fallback": "emotion_recognition_light"
            },
            "emotion_recognition_light": {
                "type": ModelType.PYTORCH,
                "url": "superb/hubert-base-superb-er",
                "size_mb": 360,
                "priority": ModelPriority.MEDIUM,
                "description": "Lightweight audio emotion"
            },
            
            # Additional models
            "mediapipe_face": {
                "type": ModelType.CUSTOM,
                "url": "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite",
                "size_mb": 5,
                "priority": ModelPriority.LOW,
                "description": "MediaPipe face detection"
            },
            "mediapipe_pose": {
                "type": ModelType.CUSTOM,
                "url": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task",
                "size_mb": 30,
                "priority": ModelPriority.MEDIUM,
                "description": "MediaPipe pose detection"
            }
        }
    
    def get_model(self, model_name: str, force_download: bool = False,
                  priority: ModelPriority = None) -> Any:
        """Get a model, downloading if necessary"""
        # Check if already loaded
        if model_name in self.loaded_models and not force_download:
            logger.info(f"Model {model_name} already loaded")
            return self.loaded_models[model_name]
        
        # Get model info
        if model_name not in self.model_registry:
            raise ValueError(f"Unknown model: {model_name}")
        
        model_info = self.model_registry[model_name]
        
        # Check system resources and select appropriate model
        if priority and priority == ModelPriority.LOW and "fallback" in model_info:
            logger.info(f"Using lightweight fallback model: {model_info['fallback']}")
            return self.get_model(model_info["fallback"])
        
        # Check cache
        model_path = self._get_model_cache_path(model_name)
        
        if not model_path.exists() or force_download:
            if self.config["auto_download"]:
                self._download_model(model_name, model_info)
            else:
                raise FileNotFoundError(f"Model {model_name} not in cache and auto_download is disabled")
        
        # Load model
        model = self._load_model(model_name, model_info, model_path)
        self.loaded_models[model_name] = model
        
        return model
    
    def _get_model_cache_path(self, model_name: str) -> Path:
        """Get cache path for a model"""
        return self.cache_dir / f"{model_name}"
    
    def _download_model(self, model_name: str, model_info: Dict[str, Any]):
        """Download a model to cache"""
        # Use lock to prevent multiple downloads
        if model_name not in self.download_locks:
            self.download_locks[model_name] = threading.Lock()
        
        with self.download_locks[model_name]:
            model_path = self._get_model_cache_path(model_name)
            
            # Check again in case another thread downloaded it
            if model_path.exists():
                return
            
            logger.info(f"Downloading model: {model_name}")
            
            if model_info["type"] == ModelType.PYTORCH:
                self._download_pytorch_model(model_name, model_info, model_path)
            elif model_info["type"] == ModelType.TENSORFLOW:
                self._download_tensorflow_model(model_name, model_info, model_path)
            else:
                self._download_generic_model(model_name, model_info, model_path)
    
    def _download_pytorch_model(self, model_name: str, model_info: Dict, model_path: Path):
        """Download PyTorch model"""
        try:
            # For torch hub models
            if model_info["url"].startswith("ultralytics/") or "/" in model_info["url"]:
                # Models from torch.hub are handled differently
                model_path.mkdir(parents=True, exist_ok=True)
                
                # Create a marker file to indicate successful download
                marker_file = model_path / "downloaded.json"
                with open(marker_file, 'w') as f:
                    json.dump({
                        "model_name": model_name,
                        "url": model_info["url"],
                        "downloaded": True
                    }, f)
            else:
                # Direct download for other PyTorch models
                self._download_file(model_info["url"], model_path / "model.pt")
                
        except Exception as e:
            logger.error(f"Failed to download PyTorch model {model_name}: {e}")
            raise
    
    def _download_tensorflow_model(self, model_name: str, model_info: Dict, model_path: Path):
        """Download TensorFlow model"""
        try:
            model_path.mkdir(parents=True, exist_ok=True)
            
            if model_info["url"].endswith('.h5') or model_info["url"].endswith('.hdf5'):
                # Download H5 model file
                self._download_file(model_info["url"], model_path / "model.h5")
            else:
                # TensorFlow Hub models
                marker_file = model_path / "tf_hub_model.json"
                with open(marker_file, 'w') as f:
                    json.dump({
                        "model_name": model_name,
                        "url": model_info["url"],
                        "type": "tf_hub"
                    }, f)
                    
        except Exception as e:
            logger.error(f"Failed to download TensorFlow model {model_name}: {e}")
            raise
    
    def _download_generic_model(self, model_name: str, model_info: Dict, model_path: Path):
        """Download generic model file"""
        try:
            model_path.mkdir(parents=True, exist_ok=True)
            
            # Determine file extension
            url = model_info["url"]
            file_ext = Path(url).suffix or '.model'
            
            # Download file
            output_file = model_path / f"model{file_ext}"
            self._download_file(url, output_file)
            
        except Exception as e:
            logger.error(f"Failed to download model {model_name}: {e}")
            raise
    
    def _download_file(self, url: str, output_path: Path, chunk_size: int = 8192):
        """Download a file with progress bar"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        response = requests.get(url, stream=True, timeout=self.config["download_timeout"])
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f:
            with tqdm(total=total_size, unit='iB', unit_scale=True) as pbar:
                for chunk in response.iter_content(chunk_size):
                    size = f.write(chunk)
                    pbar.update(size)
        
        logger.info(f"Downloaded {output_path}")
    
    def _load_model(self, model_name: str, model_info: Dict, model_path: Path) -> Any:
        """Load a model from cache"""
        import time
        start_time = time.time()
        
        try:
            if model_info["type"] == ModelType.PYTORCH:
                model = self._load_pytorch_model(model_name, model_info, model_path)
            elif model_info["type"] == ModelType.TENSORFLOW:
                model = self._load_tensorflow_model(model_name, model_info, model_path)
            elif model_info["type"] == ModelType.ONNX:
                model = self._load_onnx_model(model_name, model_info, model_path)
            else:
                model = self._load_custom_model(model_name, model_info, model_path)
            
            # Record load time
            self.load_times[model_name] = time.time() - start_time
            logger.info(f"Loaded model {model_name} in {self.load_times[model_name]:.2f}s")
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise
    
    def _load_pytorch_model(self, model_name: str, model_info: Dict, model_path: Path) -> Any:
        """Load PyTorch model"""
        if "/" in model_info["url"]:
            # Torch hub model
            model = torch.hub.load(
                model_info["url"].split("/")[0],
                model_info.get("model_name", model_info["url"].split("/")[1]),
                pretrained=True
            )
        else:
            # Direct model file
            model_file = model_path / "model.pt"
            if model_file.exists():
                model = torch.load(model_file, map_location=self.device)
            else:
                raise FileNotFoundError(f"Model file not found: {model_file}")
        
        model.to(self.device)
        model.eval()
        
        return model
    
    def _load_tensorflow_model(self, model_name: str, model_info: Dict, model_path: Path) -> Any:
        """Load TensorFlow model"""
        model_file = model_path / "model.h5"
        tf_hub_file = model_path / "tf_hub_model.json"
        
        if model_file.exists():
            # Load H5 model
            model = tf.keras.models.load_model(model_file)
        elif tf_hub_file.exists():
            # Load from TensorFlow Hub
            import tensorflow_hub as hub
            with open(tf_hub_file, 'r') as f:
                hub_info = json.load(f)
            model = hub.load(hub_info["url"])
        else:
            raise FileNotFoundError(f"Model not found in {model_path}")
        
        return model
    
    def _load_onnx_model(self, model_name: str, model_info: Dict, model_path: Path) -> Any:
        """Load ONNX model"""
        import onnxruntime as ort
        
        model_file = model_path / "model.onnx"
        if not model_file.exists():
            raise FileNotFoundError(f"ONNX model not found: {model_file}")
        
        # Create inference session
        providers = ['CUDAExecutionProvider'] if torch.cuda.is_available() else ['CPUExecutionProvider']
        session = ort.InferenceSession(str(model_file), providers=providers)
        
        return session
    
    def _load_custom_model(self, model_name: str, model_info: Dict, model_path: Path) -> Any:
        """Load custom model format"""
        # Find model file
        model_files = list(model_path.glob("model.*"))
        
        if not model_files:
            raise FileNotFoundError(f"No model files found in {model_path}")
        
        model_file = model_files[0]
        
        # Return path for custom handling
        return model_file
    
    def preload_models(self, model_names: List[str], max_workers: int = 3):
        """Preload multiple models in parallel"""
        logger.info(f"Preloading {len(model_names)} models...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.get_model, name): name 
                for name in model_names
            }
            
            for future in as_completed(futures):
                model_name = futures[future]
                try:
                    future.result()
                    logger.info(f"Successfully preloaded {model_name}")
                except Exception as e:
                    logger.error(f"Failed to preload {model_name}: {e}")
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a model"""
        if model_name not in self.model_registry:
            return {"error": "Model not found"}
        
        info = self.model_registry[model_name].copy()
        
        # Add cache status
        model_path = self._get_model_cache_path(model_name)
        info["cached"] = model_path.exists()
        
        # Add load status
        info["loaded"] = model_name in self.loaded_models
        
        # Add performance metrics
        if model_name in self.load_times:
            info["load_time"] = self.load_times[model_name]
        
        # Check cache size
        if model_path.exists():
            size_bytes = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
            info["cache_size_mb"] = size_bytes / (1024 * 1024)
        
        return info
    
    def list_models(self, filter_type: Optional[ModelType] = None,
                   filter_priority: Optional[ModelPriority] = None) -> List[Dict[str, Any]]:
        """List available models with optional filtering"""
        models = []
        
        for name, info in self.model_registry.items():
            if filter_type and info["type"] != filter_type:
                continue
            if filter_priority and info.get("priority") != filter_priority:
                continue
            
            model_info = self.get_model_info(name)
            model_info["name"] = name
            models.append(model_info)
        
        return models
    
    def clear_cache(self, model_name: Optional[str] = None):
        """Clear model cache"""
        if model_name:
            # Clear specific model
            model_path = self._get_model_cache_path(model_name)
            if model_path.exists():
                shutil.rmtree(model_path)
                logger.info(f"Cleared cache for {model_name}")
            
            # Remove from loaded models
            if model_name in self.loaded_models:
                del self.loaded_models[model_name]
        else:
            # Clear all cache
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.loaded_models.clear()
            logger.info("Cleared all model cache")
    
    def get_cache_size(self) -> float:
        """Get total cache size in GB"""
        total_size = 0
        for path in self.cache_dir.rglob('*'):
            if path.is_file():
                total_size += path.stat().st_size
        
        return total_size / (1024**3)  # Convert to GB
    
    def optimize_cache(self):
        """Optimize cache by removing least recently used models"""
        cache_size_gb = self.get_cache_size()
        max_size_gb = self.config["max_cache_size_gb"]
        
        if cache_size_gb <= max_size_gb:
            logger.info(f"Cache size ({cache_size_gb:.2f}GB) within limit")
            return
        
        logger.info(f"Cache size ({cache_size_gb:.2f}GB) exceeds limit ({max_size_gb}GB)")
        
        # Get model access times
        model_times = []
        for model_dir in self.cache_dir.iterdir():
            if model_dir.is_dir():
                # Get most recent access time
                access_time = max(f.stat().st_atime for f in model_dir.rglob('*') if f.is_file())
                size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
                model_times.append((model_dir.name, access_time, size))
        
        # Sort by access time (oldest first)
        model_times.sort(key=lambda x: x[1])
        
        # Remove models until under limit
        for model_name, _, size in model_times:
            self.clear_cache(model_name)
            cache_size_gb -= size / (1024**3)
            
            if cache_size_gb <= max_size_gb:
                break
        
        logger.info(f"Cache optimized to {cache_size_gb:.2f}GB")
    
    def export_config(self, output_path: str):
        """Export current configuration and model registry"""
        config_data = {
            "config": self.config,
            "model_registry": self.model_registry,
            "cache_status": {
                name: self.get_model_info(name) 
                for name in self.model_registry
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        logger.info(f"Configuration exported to {output_path}")


# Singleton instance
_model_loader_instance = None


def get_model_loader(cache_dir: str = None, config_path: str = None) -> ModelLoader:
    """Get singleton ModelLoader instance"""
    global _model_loader_instance
    
    if _model_loader_instance is None:
        _model_loader_instance = ModelLoader(cache_dir, config_path)
    
    return _model_loader_instance


# Example usage
if __name__ == "__main__":
    # Create model loader
    loader = get_model_loader()
    
    # List available models
    print("Available models:")
    for model in loader.list_models():
        print(f"  - {model['name']}: {model['description']} "
              f"({'cached' if model['cached'] else 'not cached'})")
    
    # Load a model
    print("\nLoading YOLOv5s...")
    yolo_model = loader.get_model("yolov5s")
    
    # Get model info
    info = loader.get_model_info("yolov5s")
    print(f"\nModel info: {json.dumps(info, indent=2)}")
    
    # Check cache size
    print(f"\nCache size: {loader.get_cache_size():.2f}GB")