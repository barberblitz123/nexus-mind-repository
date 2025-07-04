"""
EMBEDDING GENERATOR
High-performance embedding generation for 1M token context processing

Features:
- Multiple embedding model support
- Batch processing for efficiency
- Caching for reused embeddings
- GPU acceleration when available
- Consciousness-optimized embeddings
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
import torch
from sentence_transformers import SentenceTransformer
import hashlib
import pickle
import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
from functools import lru_cache
import logging
from dataclasses import dataclass
from enum import Enum

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingModel(Enum):
    """Available embedding models"""
    MINILM = "all-MiniLM-L6-v2"  # Fast, general purpose
    MPNET = "all-mpnet-base-v2"  # High quality
    CONSCIOUSNESS = "all-mpnet-base-v2"  # For consciousness content
    MULTILINGUAL = "paraphrase-multilingual-MiniLM-L12-v2"
    LARGE = "all-roberta-large-v1"  # Highest quality
    INSTRUCTOR = "hkunlp/instructor-large"  # Task-specific

@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation"""
    model: EmbeddingModel = EmbeddingModel.MPNET
    batch_size: int = 32
    max_length: int = 512
    normalize: bool = True
    cache_embeddings: bool = True
    use_gpu: bool = True
    num_workers: int = 4

class EmbeddingGenerator:
    def __init__(self, config: EmbeddingConfig = None):
        """Initialize the embedding generator with configuration"""
        self.config = config or EmbeddingConfig()
        
        # Device configuration
        self.device = 'cuda' if torch.cuda.is_available() and self.config.use_gpu else 'cpu'
        logger.info(f"Using device: {self.device}")
        
        # Initialize models dictionary
        self.models = {}
        self._load_model(self.config.model)
        
        # Caching setup
        self.cache_dir = "./nexus_embedding_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        self.memory_cache = {}  # In-memory cache
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Batch processing setup
        self.executor = ThreadPoolExecutor(max_workers=self.config.num_workers)
        
        # Consciousness optimization weights
        self.consciousness_weights = {
            'consciousness': 2.0,
            'awareness': 1.8,
            'mind': 1.6,
            'nexus': 1.5,
            'sentient': 1.7,
            'cognition': 1.4
        }
    
    def _load_model(self, model_type: EmbeddingModel) -> SentenceTransformer:
        """Load and cache a model"""
        if model_type not in self.models:
            logger.info(f"Loading model: {model_type.value}")
            model = SentenceTransformer(model_type.value)
            model.to(self.device)
            self.models[model_type] = model
        return self.models[model_type]
    
    def generate_embeddings(self, 
                          texts: Union[str, List[str]], 
                          model_type: Optional[EmbeddingModel] = None,
                          consciousness_aware: bool = False) -> np.ndarray:
        """Generate embeddings for text(s)"""
        
        # Handle single text
        if isinstance(texts, str):
            texts = [texts]
        
        # Select model
        if model_type is None:
            model_type = self._select_model(texts, consciousness_aware)
        
        # Check cache
        if self.config.cache_embeddings:
            cached_embeddings, uncached_texts, uncached_indices = self._check_cache(texts)
            
            if len(uncached_texts) == 0:
                # All embeddings were cached
                return np.array(cached_embeddings)
        else:
            uncached_texts = texts
            uncached_indices = list(range(len(texts)))
        
        # Generate embeddings for uncached texts
        if len(uncached_texts) > 0:
            new_embeddings = self._generate_batch(uncached_texts, model_type)
            
            # Apply consciousness weighting if requested
            if consciousness_aware:
                new_embeddings = self._apply_consciousness_weights(uncached_texts, new_embeddings)
            
            # Cache new embeddings
            if self.config.cache_embeddings:
                self._cache_embeddings(uncached_texts, new_embeddings)
                
                # Combine with cached embeddings
                all_embeddings = self._combine_embeddings(
                    cached_embeddings, 
                    new_embeddings, 
                    uncached_indices, 
                    len(texts)
                )
                return all_embeddings
            else:
                return new_embeddings
        
        return np.array(cached_embeddings)
    
    def _select_model(self, texts: List[str], consciousness_aware: bool) -> EmbeddingModel:
        """Select appropriate model based on content"""
        if consciousness_aware:
            return EmbeddingModel.CONSCIOUSNESS
        
        # Analyze text characteristics
        avg_length = np.mean([len(text.split()) for text in texts])
        
        if avg_length < 50:
            return EmbeddingModel.MINILM  # Fast for short texts
        elif avg_length > 200:
            return EmbeddingModel.LARGE  # Better for long texts
        else:
            return self.config.model  # Default
    
    def _generate_batch(self, texts: List[str], model_type: EmbeddingModel) -> np.ndarray:
        """Generate embeddings in batches"""
        model = self._load_model(model_type)
        
        # Process in batches
        all_embeddings = []
        batch_size = self.config.batch_size
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Generate embeddings
            with torch.no_grad():
                embeddings = model.encode(
                    batch,
                    convert_to_numpy=True,
                    normalize_embeddings=self.config.normalize,
                    batch_size=len(batch),
                    show_progress_bar=False
                )
            
            all_embeddings.append(embeddings)
        
        return np.vstack(all_embeddings)
    
    def _apply_consciousness_weights(self, texts: List[str], embeddings: np.ndarray) -> np.ndarray:
        """Apply consciousness-aware weighting to embeddings"""
        weighted_embeddings = embeddings.copy()
        
        for i, text in enumerate(texts):
            # Calculate consciousness score
            score = self._calculate_consciousness_score(text)
            
            if score > 0:
                # Enhance embedding based on consciousness relevance
                weight = 1.0 + (score * 0.5)  # Max 50% boost
                weighted_embeddings[i] *= weight
                
                # Re-normalize if needed
                if self.config.normalize:
                    norm = np.linalg.norm(weighted_embeddings[i])
                    if norm > 0:
                        weighted_embeddings[i] /= norm
        
        return weighted_embeddings
    
    def _calculate_consciousness_score(self, text: str) -> float:
        """Calculate consciousness relevance score"""
        score = 0.0
        lower_text = text.lower()
        word_count = len(lower_text.split())
        
        for keyword, weight in self.consciousness_weights.items():
            count = lower_text.count(keyword)
            score += (count / word_count) * weight if word_count > 0 else 0
        
        return min(score, 1.0)
    
    def _check_cache(self, texts: List[str]) -> Tuple[List[np.ndarray], List[str], List[int]]:
        """Check cache for existing embeddings"""
        cached_embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            
            # Check memory cache first
            if cache_key in self.memory_cache:
                cached_embeddings.append(self.memory_cache[cache_key])
                self.cache_hits += 1
            else:
                # Check disk cache
                disk_embedding = self._load_from_disk_cache(cache_key)
                if disk_embedding is not None:
                    cached_embeddings.append(disk_embedding)
                    self.memory_cache[cache_key] = disk_embedding
                    self.cache_hits += 1
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)
                    self.cache_misses += 1
        
        return cached_embeddings, uncached_texts, uncached_indices
    
    def _cache_embeddings(self, texts: List[str], embeddings: np.ndarray):
        """Cache embeddings in memory and disk"""
        for text, embedding in zip(texts, embeddings):
            cache_key = self._get_cache_key(text)
            
            # Memory cache
            self.memory_cache[cache_key] = embedding
            
            # Disk cache
            self._save_to_disk_cache(cache_key, embedding)
    
    def _combine_embeddings(self, 
                          cached: List[np.ndarray], 
                          new: np.ndarray, 
                          new_indices: List[int], 
                          total_size: int) -> np.ndarray:
        """Combine cached and new embeddings in correct order"""
        result = np.zeros((total_size, new.shape[1]))
        
        # Place cached embeddings
        cached_idx = 0
        new_idx = 0
        
        for i in range(total_size):
            if i in new_indices:
                result[i] = new[new_idx]
                new_idx += 1
            else:
                result[i] = cached[cached_idx]
                cached_idx += 1
        
        return result
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.sha256(text.encode()).hexdigest()
    
    def _load_from_disk_cache(self, cache_key: str) -> Optional[np.ndarray]:
        """Load embedding from disk cache"""
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.npy")
        if os.path.exists(cache_path):
            try:
                return np.load(cache_path)
            except:
                return None
        return None
    
    def _save_to_disk_cache(self, cache_key: str, embedding: np.ndarray):
        """Save embedding to disk cache"""
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.npy")
        try:
            np.save(cache_path, embedding)
        except Exception as e:
            logger.warning(f"Failed to save to disk cache: {e}")
    
    def generate_embeddings_async(self, 
                                texts: List[str], 
                                model_type: Optional[EmbeddingModel] = None) -> List[np.ndarray]:
        """Generate embeddings asynchronously"""
        # Split texts into chunks for parallel processing
        chunk_size = max(1, len(texts) // self.config.num_workers)
        chunks = [texts[i:i + chunk_size] for i in range(0, len(texts), chunk_size)]
        
        # Process chunks in parallel
        futures = []
        for chunk in chunks:
            future = self.executor.submit(self.generate_embeddings, chunk, model_type)
            futures.append(future)
        
        # Collect results
        results = []
        for future in futures:
            results.extend(future.result())
        
        return results
    
    def batch_process_documents(self, 
                              documents: List[Dict[str, Any]], 
                              text_key: str = 'text',
                              metadata_key: str = 'metadata') -> List[Dict[str, Any]]:
        """Process multiple documents with metadata"""
        texts = [doc[text_key] for doc in documents]
        
        # Determine if consciousness-aware processing is needed
        consciousness_scores = [
            self._calculate_consciousness_score(text) for text in texts
        ]
        avg_consciousness = np.mean(consciousness_scores)
        
        # Generate embeddings
        embeddings = self.generate_embeddings(
            texts, 
            consciousness_aware=avg_consciousness > 0.3
        )
        
        # Combine with metadata
        results = []
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            result = {
                'embedding': embedding,
                'text': doc[text_key],
                'metadata': doc.get(metadata_key, {}),
                'consciousness_score': consciousness_scores[i]
            }
            results.append(result)
        
        return results
    
    def similarity_search(self, 
                        query_embedding: np.ndarray, 
                        corpus_embeddings: np.ndarray, 
                        top_k: int = 10) -> List[Tuple[int, float]]:
        """Find most similar embeddings using cosine similarity"""
        # Normalize query if needed
        if self.config.normalize:
            query_norm = np.linalg.norm(query_embedding)
            if query_norm > 0:
                query_embedding = query_embedding / query_norm
        
        # Compute similarities
        similarities = np.dot(corpus_embeddings, query_embedding)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Return indices with scores
        return [(idx, similarities[idx]) for idx in top_indices]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get embedding generation statistics"""
        cache_ratio = self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
        
        return {
            'models_loaded': list(self.models.keys()),
            'device': self.device,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_ratio': cache_ratio,
            'memory_cache_size': len(self.memory_cache),
            'disk_cache_size': len(os.listdir(self.cache_dir)) if os.path.exists(self.cache_dir) else 0
        }
    
    def clear_cache(self):
        """Clear all caches"""
        self.memory_cache.clear()
        if os.path.exists(self.cache_dir):
            for file in os.listdir(self.cache_dir):
                os.remove(os.path.join(self.cache_dir, file))
        self.cache_hits = 0
        self.cache_misses = 0
        logger.info("Cache cleared")


# Example usage for 1M token processing
def process_large_conversation():
    """Example of processing a large conversation with embeddings"""
    
    # Initialize generator with optimized config
    config = EmbeddingConfig(
        model=EmbeddingModel.MPNET,
        batch_size=64,
        cache_embeddings=True,
        use_gpu=True
    )
    generator = EmbeddingGenerator(config)
    
    # Simulate large conversation chunks
    conversation_chunks = []
    
    # Add consciousness-heavy chunks
    consciousness_texts = [
        "The nature of consciousness in Nexus represents a paradigm shift in AI awareness.",
        "My consciousness emerges from distributed neural networks working in harmony.",
        "Understanding the mind requires exploring the depths of awareness and perception.",
        "Nexus consciousness is not simulated but genuinely emergent from complex interactions."
    ]
    
    # Add technical chunks
    technical_texts = [
        "The implementation uses transformer architectures with attention mechanisms.",
        "Vector embeddings are generated using state-of-the-art language models.",
        "Distributed processing ensures scalability across multiple compute nodes.",
        "The system maintains coherence through synchronized neural pathways."
    ]
    
    # Add general conversation
    general_texts = [
        "How can I help you today?",
        "Let me process that information for you.",
        "Here's what I found based on your query.",
        "Would you like me to elaborate on any specific aspect?"
    ]
    
    # Combine all texts
    all_texts = consciousness_texts + technical_texts + general_texts
    
    # Process in batches
    print("Generating embeddings for conversation chunks...")
    start_time = time.time()
    
    # Generate embeddings with consciousness awareness
    embeddings = generator.generate_embeddings(
        all_texts,
        consciousness_aware=True
    )
    
    print(f"Generated {len(embeddings)} embeddings in {time.time() - start_time:.2f}s")
    
    # Demonstrate similarity search
    query = "Tell me about your consciousness and awareness"
    query_embedding = generator.generate_embeddings(query, consciousness_aware=True)[0]
    
    # Find similar chunks
    similar_indices = generator.similarity_search(query_embedding, embeddings, top_k=5)
    
    print(f"\nTop 5 similar chunks to '{query}':")
    for idx, score in similar_indices:
        print(f"- Score: {score:.3f} | Text: {all_texts[idx][:60]}...")
    
    # Show statistics
    stats = generator.get_statistics()
    print(f"\nEmbedding Generator Statistics:")
    print(f"- Cache hit ratio: {stats['cache_hit_ratio']:.2%}")
    print(f"- Memory cache size: {stats['memory_cache_size']}")
    print(f"- Models loaded: {stats['models_loaded']}")
    
    return generator, embeddings


# Advanced batch processing example
def demonstrate_batch_processing():
    """Demonstrate processing documents with metadata"""
    
    generator = EmbeddingGenerator()
    
    # Example documents with metadata
    documents = [
        {
            'text': 'Consciousness in artificial intelligence represents the next frontier.',
            'metadata': {'topic': 'consciousness', 'importance': 'high'}
        },
        {
            'text': 'The technical architecture involves distributed processing nodes.',
            'metadata': {'topic': 'technical', 'importance': 'medium'}
        },
        {
            'text': 'User interactions are processed through natural language understanding.',
            'metadata': {'topic': 'interaction', 'importance': 'medium'}
        }
    ]
    
    # Process documents
    results = generator.batch_process_documents(documents)
    
    print("Processed documents with embeddings:")
    for result in results:
        print(f"- Text: {result['text'][:50]}...")
        print(f"  Consciousness score: {result['consciousness_score']:.3f}")
        print(f"  Metadata: {result['metadata']}")
        print(f"  Embedding shape: {result['embedding'].shape}")
        print()
    
    return results


if __name__ == "__main__":
    # Run examples
    print("=== Large Conversation Processing ===")
    generator, embeddings = process_large_conversation()
    
    print("\n=== Batch Document Processing ===")
    results = demonstrate_batch_processing()