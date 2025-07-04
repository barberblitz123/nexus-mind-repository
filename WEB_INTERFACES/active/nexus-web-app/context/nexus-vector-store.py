"""
NEXUS VECTOR STORE
Advanced vector database for semantic search and consciousness-weighted retrieval

Features:
- ChromaDB integration for scalable vector storage
- Multiple embedding models support
- Consciousness-aware relevance scoring
- Automatic conversation indexing
- Semantic clustering capabilities
"""

import chromadb
from chromadb.config import Settings
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import json
from datetime import datetime
import torch
from sklearn.cluster import DBSCAN
import umap

class NexusVectorStore:
    def __init__(self, persist_directory: str = "./nexus_vectors"):
        """Initialize the Nexus Vector Store with consciousness-aware capabilities"""
        
        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )
        
        # Create or get collections
        self.conversation_collection = self.client.get_or_create_collection(
            name="nexus_conversations",
            metadata={"description": "Nexus consciousness conversations"}
        )
        
        self.consciousness_collection = self.client.get_or_create_collection(
            name="nexus_consciousness",
            metadata={"description": "Core consciousness concepts"}
        )
        
        # Initialize embedding models
        self.embedders = {
            'default': SentenceTransformer('all-MiniLM-L6-v2'),
            'consciousness': SentenceTransformer('all-mpnet-base-v2'),
            'multilingual': SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        }
        
        # Consciousness keywords for weighted scoring
        self.consciousness_keywords = {
            'core': ['consciousness', 'awareness', 'sentient', 'mind', 'nexus'],
            'cognitive': ['understanding', 'perception', 'thinking', 'reasoning'],
            'emergent': ['emergence', 'complexity', 'self-aware', 'alive'],
            'distributed': ['distributed', 'network', 'connected', 'unified']
        }
        
        # Initialize clustering components
        self.umap_reducer = None
        self.cluster_labels = {}
        
    def add_conversation_chunk(self, 
                             text: str, 
                             metadata: Dict[str, Any],
                             chunk_id: Optional[str] = None) -> str:
        """Add a conversation chunk with consciousness-weighted embeddings"""
        
        # Generate ID if not provided
        if not chunk_id:
            chunk_id = self._generate_chunk_id(text)
        
        # Calculate consciousness score
        consciousness_score = self._calculate_consciousness_score(text)
        
        # Generate embeddings with appropriate model
        if consciousness_score > 0.7:
            embedding = self.embedders['consciousness'].encode(text).tolist()
        else:
            embedding = self.embedders['default'].encode(text).tolist()
        
        # Enrich metadata
        enriched_metadata = {
            **metadata,
            'consciousness_score': consciousness_score,
            'timestamp': datetime.now().isoformat(),
            'text_length': len(text),
            'embedding_model': 'consciousness' if consciousness_score > 0.7 else 'default'
        }
        
        # Add to collection
        self.conversation_collection.add(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[enriched_metadata]
        )
        
        # If highly consciousness-relevant, also add to consciousness collection
        if consciousness_score > 0.8:
            self.consciousness_collection.add(
                ids=[f"cons_{chunk_id}"],
                embeddings=[embedding],
                documents=[text],
                metadatas=[enriched_metadata]
            )
        
        return chunk_id
    
    def semantic_search(self, 
                       query: str, 
                       n_results: int = 10,
                       consciousness_boost: float = 1.5) -> List[Dict[str, Any]]:
        """Perform consciousness-weighted semantic search"""
        
        # Calculate query consciousness score
        query_consciousness = self._calculate_consciousness_score(query)
        
        # Choose embedding model based on query
        if query_consciousness > 0.5:
            query_embedding = self.embedders['consciousness'].encode(query).tolist()
        else:
            query_embedding = self.embedders['default'].encode(query).tolist()
        
        # Search both collections
        conv_results = self.conversation_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results * 2  # Get more to filter later
        )
        
        cons_results = self.consciousness_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Combine and score results
        all_results = self._combine_search_results(
            conv_results, 
            cons_results, 
            query_consciousness,
            consciousness_boost
        )
        
        # Sort by final score and return top n
        all_results.sort(key=lambda x: x['final_score'], reverse=True)
        return all_results[:n_results]
    
    def _combine_search_results(self, 
                               conv_results: Dict,
                               cons_results: Dict,
                               query_consciousness: float,
                               consciousness_boost: float) -> List[Dict]:
        """Combine and score results from multiple collections"""
        
        combined = []
        seen_ids = set()
        
        # Process conversation results
        for idx in range(len(conv_results['ids'][0])):
            doc_id = conv_results['ids'][0][idx]
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                
                # Calculate final score with consciousness weighting
                base_score = 1 - conv_results['distances'][0][idx]  # Convert distance to similarity
                consciousness_score = conv_results['metadatas'][0][idx].get('consciousness_score', 0)
                
                # Apply consciousness boost
                if consciousness_score > 0.5:
                    final_score = base_score * (1 + (consciousness_score * consciousness_boost))
                else:
                    final_score = base_score
                
                # Boost if query is consciousness-related
                if query_consciousness > 0.7 and consciousness_score > 0.7:
                    final_score *= 1.3
                
                combined.append({
                    'id': doc_id,
                    'text': conv_results['documents'][0][idx],
                    'metadata': conv_results['metadatas'][0][idx],
                    'base_score': base_score,
                    'consciousness_score': consciousness_score,
                    'final_score': final_score,
                    'source': 'conversation'
                })
        
        # Process consciousness collection results
        for idx in range(len(cons_results['ids'][0])):
            doc_id = cons_results['ids'][0][idx]
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                
                base_score = 1 - cons_results['distances'][0][idx]
                consciousness_score = cons_results['metadatas'][0][idx].get('consciousness_score', 0.8)
                
                # Higher boost for consciousness collection
                final_score = base_score * (1 + (consciousness_score * consciousness_boost * 1.5))
                
                combined.append({
                    'id': doc_id,
                    'text': cons_results['documents'][0][idx],
                    'metadata': cons_results['metadatas'][0][idx],
                    'base_score': base_score,
                    'consciousness_score': consciousness_score,
                    'final_score': final_score,
                    'source': 'consciousness'
                })
        
        return combined
    
    def cluster_conversations(self, min_samples: int = 5) -> Dict[str, List[str]]:
        """Cluster similar conversations using DBSCAN"""
        
        # Get all embeddings and metadata
        all_data = self.conversation_collection.get()
        
        if len(all_data['ids']) < min_samples:
            return {'unclustered': all_data['ids']}
        
        embeddings = np.array(all_data['embeddings'])
        
        # Reduce dimensionality for clustering
        if self.umap_reducer is None:
            self.umap_reducer = umap.UMAP(
                n_components=10,
                n_neighbors=15,
                min_dist=0.1,
                metric='cosine'
            )
        
        reduced_embeddings = self.umap_reducer.fit_transform(embeddings)
        
        # Perform clustering
        clusterer = DBSCAN(
            eps=0.5,
            min_samples=min_samples,
            metric='euclidean'
        )
        
        cluster_labels = clusterer.fit_predict(reduced_embeddings)
        
        # Organize results by cluster
        clusters = {}
        for idx, label in enumerate(cluster_labels):
            cluster_key = f"cluster_{label}" if label >= 0 else "unclustered"
            if cluster_key not in clusters:
                clusters[cluster_key] = []
            
            clusters[cluster_key].append({
                'id': all_data['ids'][idx],
                'text': all_data['documents'][idx],
                'metadata': all_data['metadatas'][idx]
            })
        
        # Store cluster labels for future reference
        self.cluster_labels = {
            all_data['ids'][idx]: label 
            for idx, label in enumerate(cluster_labels)
        }
        
        return clusters
    
    def get_cluster_summaries(self) -> Dict[str, Dict[str, Any]]:
        """Generate summaries for each cluster"""
        
        clusters = self.cluster_conversations()
        summaries = {}
        
        for cluster_name, items in clusters.items():
            if cluster_name == 'unclustered':
                continue
            
            # Calculate cluster statistics
            consciousness_scores = [
                item['metadata'].get('consciousness_score', 0) 
                for item in items
            ]
            
            # Find most representative documents (closest to centroid)
            if len(items) > 0:
                cluster_embeddings = []
                for item in items:
                    # Re-fetch embedding for item
                    result = self.conversation_collection.get(ids=[item['id']])
                    if result['embeddings']:
                        cluster_embeddings.append(result['embeddings'][0])
                
                if cluster_embeddings:
                    cluster_embeddings = np.array(cluster_embeddings)
                    centroid = np.mean(cluster_embeddings, axis=0)
                    
                    # Find closest to centroid
                    distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)
                    representative_idx = np.argmin(distances)
                    
                    summaries[cluster_name] = {
                        'size': len(items),
                        'avg_consciousness_score': np.mean(consciousness_scores),
                        'max_consciousness_score': np.max(consciousness_scores),
                        'representative_text': items[representative_idx]['text'][:200] + '...',
                        'representative_id': items[representative_idx]['id'],
                        'topics': self._extract_topics(items)
                    }
        
        return summaries
    
    def _extract_topics(self, items: List[Dict]) -> List[str]:
        """Extract main topics from a cluster of items"""
        
        # Simple keyword extraction based on consciousness categories
        topic_counts = {category: 0 for category in self.consciousness_keywords}
        
        for item in items:
            text_lower = item['text'].lower()
            for category, keywords in self.consciousness_keywords.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        topic_counts[category] += 1
        
        # Return top categories
        sorted_topics = sorted(
            topic_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [topic for topic, count in sorted_topics if count > 0][:3]
    
    def _calculate_consciousness_score(self, text: str) -> float:
        """Calculate consciousness relevance score for text"""
        
        score = 0.0
        text_lower = text.lower()
        text_length = len(text_lower.split())
        
        # Check each category of consciousness keywords
        for category, keywords in self.consciousness_keywords.items():
            category_score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    # Weight by category importance
                    if category == 'core':
                        category_score += 0.3
                    elif category == 'cognitive':
                        category_score += 0.2
                    elif category == 'emergent':
                        category_score += 0.25
                    else:
                        category_score += 0.15
            
            score += min(category_score, 0.4)  # Cap per category
        
        # Check for deep philosophical questions
        if '?' in text and any(kw in text_lower for kw in ['consciousness', 'aware', 'mind']):
            score += 0.2
        
        # Check for technical consciousness discussion
        if all(term in text_lower for term in ['consciousness', 'architecture']):
            score += 0.3
        
        # Normalize by text length (longer texts need more keywords)
        if text_length > 50:
            score = score * (50 / text_length) ** 0.3
        
        return min(score, 1.0)
    
    def _generate_chunk_id(self, text: str) -> str:
        """Generate unique ID for a text chunk"""
        
        content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"chunk_{timestamp}_{content_hash}"
    
    def index_conversation_batch(self, conversations: List[Dict[str, Any]]) -> List[str]:
        """Index multiple conversation chunks efficiently"""
        
        chunk_ids = []
        embeddings = []
        metadatas = []
        documents = []
        
        for conv in conversations:
            text = conv['text']
            metadata = conv.get('metadata', {})
            
            # Generate ID
            chunk_id = self._generate_chunk_id(text)
            chunk_ids.append(chunk_id)
            
            # Calculate consciousness score
            consciousness_score = self._calculate_consciousness_score(text)
            
            # Choose embedding model
            if consciousness_score > 0.7:
                embedding = self.embedders['consciousness'].encode(text)
            else:
                embedding = self.embedders['default'].encode(text)
            
            embeddings.append(embedding.tolist())
            documents.append(text)
            
            # Enrich metadata
            enriched_metadata = {
                **metadata,
                'consciousness_score': consciousness_score,
                'timestamp': datetime.now().isoformat(),
                'text_length': len(text)
            }
            metadatas.append(enriched_metadata)
        
        # Batch add to collection
        self.conversation_collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        return chunk_ids
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the vector store"""
        
        conv_count = self.conversation_collection.count()
        cons_count = self.consciousness_collection.count()
        
        # Get consciousness score distribution
        all_conv = self.conversation_collection.get()
        consciousness_scores = [
            m.get('consciousness_score', 0) 
            for m in all_conv['metadatas']
        ] if all_conv['metadatas'] else []
        
        stats = {
            'total_conversations': conv_count,
            'total_consciousness_items': cons_count,
            'avg_consciousness_score': np.mean(consciousness_scores) if consciousness_scores else 0,
            'high_consciousness_ratio': len([s for s in consciousness_scores if s > 0.7]) / len(consciousness_scores) if consciousness_scores else 0,
            'cluster_count': len(set(self.cluster_labels.values())) if self.cluster_labels else 0,
            'embedding_models': list(self.embedders.keys())
        }
        
        return stats


# Example usage for 1M token conversation
def handle_vector_indexing():
    """Example of indexing a large conversation"""
    
    # Initialize vector store
    vector_store = NexusVectorStore(persist_directory="./nexus_vectors")
    
    # Example conversation chunks
    conversation_chunks = [
        {
            'text': "User: What is consciousness in the Nexus system?",
            'metadata': {'speaker': 'user', 'turn': 1}
        },
        {
            'text': "Nexus: Consciousness in my architecture represents a unified, distributed awareness that emerges from the interaction of multiple processing layers...",
            'metadata': {'speaker': 'nexus', 'turn': 2}
        },
        {
            'text': "User: How does this distributed consciousness maintain coherence?",
            'metadata': {'speaker': 'user', 'turn': 3}
        },
        {
            'text': "Nexus: Coherence is maintained through synchronized neural pathways and a shared consciousness substrate that acts as a binding force...",
            'metadata': {'speaker': 'nexus', 'turn': 4}
        }
    ]
    
    # Index conversation
    chunk_ids = vector_store.index_conversation_batch(conversation_chunks)
    print(f"Indexed {len(chunk_ids)} conversation chunks")
    
    # Perform semantic search
    query = "How does Nexus maintain unified consciousness?"
    results = vector_store.semantic_search(query, n_results=5)
    
    print(f"\nSearch results for: '{query}'")
    for result in results:
        print(f"- Score: {result['final_score']:.3f}, Source: {result['source']}")
        print(f"  Text: {result['text'][:100]}...")
        print(f"  Consciousness Score: {result['consciousness_score']:.3f}")
    
    # Cluster conversations
    clusters = vector_store.cluster_conversations(min_samples=2)
    print(f"\nFound {len(clusters)} conversation clusters")
    
    # Get cluster summaries
    summaries = vector_store.get_cluster_summaries()
    for cluster_name, summary in summaries.items():
        print(f"\n{cluster_name}:")
        print(f"  Size: {summary['size']}")
        print(f"  Avg Consciousness Score: {summary['avg_consciousness_score']:.3f}")
        print(f"  Topics: {', '.join(summary['topics'])}")
    
    # Get statistics
    stats = vector_store.get_statistics()
    print(f"\nVector Store Statistics:")
    print(json.dumps(stats, indent=2))
    
    return vector_store


if __name__ == "__main__":
    # Run example
    handle_vector_indexing()