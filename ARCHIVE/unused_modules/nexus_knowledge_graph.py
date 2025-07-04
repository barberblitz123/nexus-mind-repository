#!/usr/bin/env python3
"""
NEXUS Knowledge Graph - Dynamic knowledge management system
Graph construction, entity extraction, and intelligent insights
"""

import os
import json
import pickle
import hashlib
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
import threading
import logging

# Graph databases
import networkx as nx
from neo4j import GraphDatabase, AsyncGraphDatabase
from pyvis.network import Network
import igraph

# NLP and entity extraction
import spacy
from transformers import pipeline, AutoTokenizer, AutoModel
import nltk
from nltk.chunk import ne_chunk
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize

# Knowledge representation
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD
from owlready2 import *

# Machine learning
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import LatentDirichletAllocation
import torch
import torch.nn as nn
from torch_geometric.nn import GCNConv, GAE
from torch_geometric.data import Data

# Embeddings
from sentence_transformers import SentenceTransformer
import faiss

# API and documentation parsing
from sphinx.util.docutils import SphinxDirective
from docutils.parsers.rst import directives
import ast
import inspect

# Monitoring
from prometheus_client import Counter, Histogram, Gauge
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
entities_extracted = Counter('nexus_entities_extracted_total', 'Total entities extracted')
relationships_created = Counter('nexus_relationships_created_total', 'Total relationships created')
queries_processed = Counter('nexus_graph_queries_total', 'Total graph queries processed')
graph_size = Gauge('nexus_graph_size', 'Current graph size', ['metric'])


@dataclass
class KnowledgeConfig:
    """Knowledge graph configuration"""
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # Entity extraction
    spacy_model: str = "en_core_web_lg"
    entity_confidence_threshold: float = 0.7
    
    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384
    similarity_threshold: float = 0.8
    
    # Graph settings
    max_graph_size: int = 1000000
    enable_reasoning: bool = True
    enable_learning: bool = True
    
    # Caching
    cache_embeddings: bool = True
    cache_size: int = 10000
    
    # Auto-documentation
    auto_generate_docs: bool = True
    doc_update_interval: int = 3600  # seconds


@dataclass
class Entity:
    """Knowledge entity"""
    entity_id: str
    entity_type: str
    name: str
    properties: Dict[str, Any]
    embeddings: Optional[np.ndarray] = None
    confidence: float = 1.0
    source: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Relationship:
    """Entity relationship"""
    relationship_id: str
    source_id: str
    target_id: str
    relationship_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class KnowledgeInsight:
    """Derived knowledge insight"""
    insight_id: str
    insight_type: str
    entities: List[str]
    description: str
    confidence: float
    evidence: List[Dict[str, Any]]
    timestamp: datetime = field(default_factory=datetime.now)


class EntityExtractor:
    """Extract entities from various sources"""
    
    def __init__(self, config: KnowledgeConfig):
        self.config = config
        self.nlp = spacy.load(config.spacy_model)
        self.ner_pipeline = pipeline("ner", aggregation_strategy="simple")
        self.entity_cache = {}
        
    def extract_from_text(self, text: str, source: str = "text") -> List[Entity]:
        """Extract entities from text"""
        entities = []
        
        # SpaCy NER
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'PRODUCT', 'TECH', 'LOC']:
                entity = Entity(
                    entity_id=hashlib.md5(f"{ent.text}_{ent.label_}".encode()).hexdigest()[:16],
                    entity_type=ent.label_,
                    name=ent.text,
                    properties={'span': (ent.start_char, ent.end_char)},
                    confidence=0.9,
                    source=source
                )
                entities.append(entity)
                entities_extracted.inc()
        
        # Transformer NER for additional entities
        ner_results = self.ner_pipeline(text)
        for result in ner_results:
            if result['score'] >= self.config.entity_confidence_threshold:
                entity = Entity(
                    entity_id=hashlib.md5(f"{result['word']}_{result['entity_group']}".encode()).hexdigest()[:16],
                    entity_type=result['entity_group'],
                    name=result['word'],
                    properties={'score': result['score']},
                    confidence=result['score'],
                    source=source
                )
                entities.append(entity)
                entities_extracted.inc()
        
        return entities
    
    def extract_from_code(self, code: str, language: str = "python") -> List[Entity]:
        """Extract entities from source code"""
        entities = []
        
        if language == "python":
            try:
                tree = ast.parse(code)
                
                # Extract classes
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        entity = Entity(
                            entity_id=hashlib.md5(f"class_{node.name}".encode()).hexdigest()[:16],
                            entity_type="CLASS",
                            name=node.name,
                            properties={
                                'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                                'docstring': ast.get_docstring(node),
                                'line': node.lineno
                            },
                            source="code"
                        )
                        entities.append(entity)
                        entities_extracted.inc()
                    
                    elif isinstance(node, ast.FunctionDef):
                        entity = Entity(
                            entity_id=hashlib.md5(f"function_{node.name}".encode()).hexdigest()[:16],
                            entity_type="FUNCTION",
                            name=node.name,
                            properties={
                                'args': [arg.arg for arg in node.args.args],
                                'docstring': ast.get_docstring(node),
                                'line': node.lineno
                            },
                            source="code"
                        )
                        entities.append(entity)
                        entities_extracted.inc()
                    
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            entity = Entity(
                                entity_id=hashlib.md5(f"module_{alias.name}".encode()).hexdigest()[:16],
                                entity_type="MODULE",
                                name=alias.name,
                                properties={'alias': alias.asname},
                                source="code"
                            )
                            entities.append(entity)
                            entities_extracted.inc()
                
            except Exception as e:
                logger.error(f"Code parsing error: {e}")
        
        return entities
    
    def extract_from_api_docs(self, module) -> List[Entity]:
        """Extract entities from API documentation"""
        entities = []
        
        try:
            # Inspect module
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj):
                    entity = Entity(
                        entity_id=hashlib.md5(f"api_class_{name}".encode()).hexdigest()[:16],
                        entity_type="API_CLASS",
                        name=name,
                        properties={
                            'module': module.__name__,
                            'docstring': inspect.getdoc(obj),
                            'methods': [m for m, _ in inspect.getmembers(obj, inspect.ismethod)]
                        },
                        source="api"
                    )
                    entities.append(entity)
                    entities_extracted.inc()
                
                elif inspect.isfunction(obj):
                    entity = Entity(
                        entity_id=hashlib.md5(f"api_function_{name}".encode()).hexdigest()[:16],
                        entity_type="API_FUNCTION",
                        name=name,
                        properties={
                            'module': module.__name__,
                            'docstring': inspect.getdoc(obj),
                            'signature': str(inspect.signature(obj))
                        },
                        source="api"
                    )
                    entities.append(entity)
                    entities_extracted.inc()
        
        except Exception as e:
            logger.error(f"API inspection error: {e}")
        
        return entities


class RelationshipExtractor:
    """Extract relationships between entities"""
    
    def __init__(self, config: KnowledgeConfig):
        self.config = config
        self.nlp = spacy.load(config.spacy_model)
        
    def extract_from_text(self, text: str, entities: List[Entity]) -> List[Relationship]:
        """Extract relationships from text"""
        relationships = []
        
        # Create entity lookup
        entity_lookup = {e.name.lower(): e for e in entities}
        
        # Dependency parsing for relationships
        doc = self.nlp(text)
        
        for token in doc:
            if token.dep_ in ["nsubj", "dobj", "pobj"]:
                # Find subject and object entities
                subject = None
                obj = None
                
                for child in token.children:
                    if child.text.lower() in entity_lookup:
                        if token.dep_ == "nsubj":
                            subject = entity_lookup[child.text.lower()]
                        else:
                            obj = entity_lookup[child.text.lower()]
                
                if subject and obj:
                    rel = Relationship(
                        relationship_id=hashlib.md5(f"{subject.entity_id}_{token.lemma_}_{obj.entity_id}".encode()).hexdigest()[:16],
                        source_id=subject.entity_id,
                        target_id=obj.entity_id,
                        relationship_type=token.lemma_,
                        properties={'dependency': token.dep_}
                    )
                    relationships.append(rel)
                    relationships_created.inc()
        
        return relationships
    
    def extract_from_code_structure(self, entities: List[Entity]) -> List[Relationship]:
        """Extract relationships from code structure"""
        relationships = []
        
        # Group entities by type
        classes = [e for e in entities if e.entity_type == "CLASS"]
        functions = [e for e in entities if e.entity_type == "FUNCTION"]
        modules = [e for e in entities if e.entity_type == "MODULE"]
        
        # Class inheritance relationships
        for cls in classes:
            if 'bases' in cls.properties:
                for base in cls.properties['bases']:
                    # Find base class entity
                    base_entity = next((e for e in classes if e.name == base), None)
                    if base_entity:
                        rel = Relationship(
                            relationship_id=hashlib.md5(f"{cls.entity_id}_inherits_{base_entity.entity_id}".encode()).hexdigest()[:16],
                            source_id=cls.entity_id,
                            target_id=base_entity.entity_id,
                            relationship_type="INHERITS"
                        )
                        relationships.append(rel)
                        relationships_created.inc()
        
        # Function-class relationships
        for cls in classes:
            if 'methods' in cls.properties:
                for method_name in cls.properties['methods']:
                    method_entity = next((e for e in functions if e.name == method_name), None)
                    if method_entity:
                        rel = Relationship(
                            relationship_id=hashlib.md5(f"{cls.entity_id}_has_method_{method_entity.entity_id}".encode()).hexdigest()[:16],
                            source_id=cls.entity_id,
                            target_id=method_entity.entity_id,
                            relationship_type="HAS_METHOD"
                        )
                        relationships.append(rel)
                        relationships_created.inc()
        
        return relationships
    
    def infer_relationships(self, entities: List[Entity], embeddings: Dict[str, np.ndarray]) -> List[Relationship]:
        """Infer relationships using embeddings"""
        relationships = []
        
        # Calculate similarity between all entity pairs
        entity_ids = list(embeddings.keys())
        
        for i, id1 in enumerate(entity_ids):
            for j, id2 in enumerate(entity_ids[i+1:], i+1):
                similarity = cosine_similarity(
                    embeddings[id1].reshape(1, -1),
                    embeddings[id2].reshape(1, -1)
                )[0, 0]
                
                if similarity >= self.config.similarity_threshold:
                    rel = Relationship(
                        relationship_id=hashlib.md5(f"{id1}_similar_{id2}".encode()).hexdigest()[:16],
                        source_id=id1,
                        target_id=id2,
                        relationship_type="SIMILAR",
                        properties={'similarity': float(similarity)},
                        confidence=similarity
                    )
                    relationships.append(rel)
                    relationships_created.inc()
        
        return relationships


class GraphNeuralNetwork(nn.Module):
    """Graph neural network for knowledge inference"""
    
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int):
        super().__init__()
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        self.conv3 = GCNConv(hidden_dim, output_dim)
        self.dropout = nn.Dropout(0.2)
        
    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = torch.relu(x)
        x = self.dropout(x)
        
        x = self.conv2(x, edge_index)
        x = torch.relu(x)
        x = self.dropout(x)
        
        x = self.conv3(x, edge_index)
        return x


class KnowledgeReasoner:
    """Reasoning engine for knowledge graph"""
    
    def __init__(self, config: KnowledgeConfig):
        self.config = config
        self.onto = None
        self.reasoner = None
        
        if config.enable_reasoning:
            # Initialize OWL ontology
            self.onto = get_ontology("http://nexus.ai/knowledge.owl")
            
    def create_ontology(self, entities: List[Entity], relationships: List[Relationship]):
        """Create OWL ontology from entities and relationships"""
        if not self.onto:
            return
        
        with self.onto:
            # Create classes
            entity_classes = {}
            for entity in entities:
                if entity.entity_type not in entity_classes:
                    entity_classes[entity.entity_type] = types.new_class(
                        entity.entity_type,
                        (Thing,)
                    )
                
                # Create individual
                individual = entity_classes[entity.entity_type](entity.name)
                
                # Add properties
                for prop_name, prop_value in entity.properties.items():
                    if hasattr(individual, prop_name):
                        setattr(individual, prop_name, prop_value)
            
            # Create relationships
            for rel in relationships:
                # Create object property
                prop = types.new_class(
                    rel.relationship_type,
                    (ObjectProperty,)
                )
        
        # Save ontology
        self.onto.save()
    
    def reason(self) -> List[KnowledgeInsight]:
        """Perform reasoning on knowledge graph"""
        insights = []
        
        if not self.onto:
            return insights
        
        # Run reasoner
        try:
            sync_reasoner(self.onto)
            
            # Extract inferred facts
            for cls in self.onto.classes():
                instances = cls.instances()
                if len(instances) > 1:
                    insight = KnowledgeInsight(
                        insight_id=hashlib.md5(f"{cls.name}_pattern".encode()).hexdigest()[:16],
                        insight_type="CLASS_PATTERN",
                        entities=[str(i) for i in instances],
                        description=f"Found {len(instances)} instances of {cls.name}",
                        confidence=0.8,
                        evidence=[{'class': cls.name, 'instances': len(instances)}]
                    )
                    insights.append(insight)
        
        except Exception as e:
            logger.error(f"Reasoning error: {e}")
        
        return insights
    
    def find_patterns(self, graph: nx.Graph) -> List[KnowledgeInsight]:
        """Find patterns in knowledge graph"""
        insights = []
        
        # Community detection
        try:
            import community
            communities = community.best_partition(graph)
            
            # Group nodes by community
            community_groups = defaultdict(list)
            for node, comm in communities.items():
                community_groups[comm].append(node)
            
            # Create insights for large communities
            for comm_id, nodes in community_groups.items():
                if len(nodes) >= 5:
                    insight = KnowledgeInsight(
                        insight_id=hashlib.md5(f"community_{comm_id}".encode()).hexdigest()[:16],
                        insight_type="COMMUNITY",
                        entities=nodes[:10],  # Sample
                        description=f"Discovered community with {len(nodes)} related entities",
                        confidence=0.7,
                        evidence=[{'community_id': comm_id, 'size': len(nodes)}]
                    )
                    insights.append(insight)
        except:
            pass
        
        # Central nodes
        centrality = nx.betweenness_centrality(graph)
        top_central = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for node, score in top_central:
            if score > 0.1:
                insight = KnowledgeInsight(
                    insight_id=hashlib.md5(f"central_{node}".encode()).hexdigest()[:16],
                    insight_type="CENTRAL_ENTITY",
                    entities=[node],
                    description=f"{node} is a highly connected entity",
                    confidence=score,
                    evidence=[{'centrality_score': score}]
                )
                insights.append(insight)
        
        return insights


class NexusKnowledgeGraph:
    """Main knowledge graph system"""
    
    def __init__(self, config: Optional[KnowledgeConfig] = None):
        self.config = config or KnowledgeConfig()
        
        # Components
        self.entity_extractor = EntityExtractor(self.config)
        self.relationship_extractor = RelationshipExtractor(self.config)
        self.reasoner = KnowledgeReasoner(self.config)
        
        # Graph storage
        self.graph = nx.MultiDiGraph()
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        
        # Embeddings
        self.embedding_model = SentenceTransformer(self.config.embedding_model)
        self.embeddings: Dict[str, np.ndarray] = {}
        self.embedding_index = None
        
        # Neo4j connection (optional)
        self.neo4j_driver = None
        if self.config.neo4j_uri:
            try:
                self.neo4j_driver = GraphDatabase.driver(
                    self.config.neo4j_uri,
                    auth=(self.config.neo4j_user, self.config.neo4j_password)
                )
            except Exception as e:
                logger.warning(f"Neo4j connection failed: {e}")
        
        # Threading
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize embedding index
        self._initialize_embedding_index()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _initialize_embedding_index(self):
        """Initialize FAISS index for embeddings"""
        self.embedding_index = faiss.IndexFlatL2(self.config.embedding_dim)
        
    def _start_background_tasks(self):
        """Start background processing tasks"""
        if self.config.auto_generate_docs:
            threading.Thread(target=self._auto_documentation_loop, daemon=True).start()
    
    def add_knowledge(self, source: str, content: Any, source_type: str = "text") -> Dict[str, int]:
        """Add knowledge from various sources"""
        entities_added = 0
        relationships_added = 0
        
        # Extract entities
        if source_type == "text":
            entities = self.entity_extractor.extract_from_text(content, source)
        elif source_type == "code":
            entities = self.entity_extractor.extract_from_code(content)
        elif source_type == "api":
            entities = self.entity_extractor.extract_from_api_docs(content)
        else:
            entities = []
        
        # Generate embeddings
        for entity in entities:
            if entity.entity_id not in self.embeddings:
                text = f"{entity.entity_type}: {entity.name}"
                if 'docstring' in entity.properties and entity.properties['docstring']:
                    text += f" - {entity.properties['docstring']}"
                
                embedding = self.embedding_model.encode(text)
                self.embeddings[entity.entity_id] = embedding
                entity.embeddings = embedding
                
                # Add to FAISS index
                self.embedding_index.add(np.array([embedding]))
        
        # Extract relationships
        if source_type == "text":
            relationships = self.relationship_extractor.extract_from_text(content, entities)
        elif source_type == "code":
            relationships = self.relationship_extractor.extract_from_code_structure(entities)
        else:
            relationships = []
        
        # Infer additional relationships
        entity_embeddings = {e.entity_id: self.embeddings[e.entity_id] for e in entities}
        inferred_relationships = self.relationship_extractor.infer_relationships(entities, entity_embeddings)
        relationships.extend(inferred_relationships)
        
        # Add to graph
        for entity in entities:
            self.entities[entity.entity_id] = entity
            self.graph.add_node(
                entity.entity_id,
                entity_type=entity.entity_type,
                name=entity.name,
                properties=entity.properties
            )
            entities_added += 1
        
        for rel in relationships:
            self.relationships[rel.relationship_id] = rel
            self.graph.add_edge(
                rel.source_id,
                rel.target_id,
                relationship_type=rel.relationship_type,
                properties=rel.properties
            )
            relationships_added += 1
        
        # Update metrics
        graph_size.labels(metric='nodes').set(self.graph.number_of_nodes())
        graph_size.labels(metric='edges').set(self.graph.number_of_edges())
        
        # Sync to Neo4j if available
        if self.neo4j_driver:
            self._sync_to_neo4j(entities, relationships)
        
        return {
            'entities_added': entities_added,
            'relationships_added': relationships_added
        }
    
    def query(self, query: str, query_type: str = "semantic") -> List[Dict[str, Any]]:
        """Query knowledge graph"""
        queries_processed.inc()
        results = []
        
        if query_type == "semantic":
            results = self._semantic_search(query)
        elif query_type == "cypher" and self.neo4j_driver:
            results = self._cypher_query(query)
        elif query_type == "pattern":
            results = self._pattern_search(query)
        else:
            # NetworkX query
            results = self._graph_query(query)
        
        return results
    
    def _semantic_search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Semantic search using embeddings"""
        # Encode query
        query_embedding = self.embedding_model.encode(query)
        
        # Search in FAISS
        if self.embedding_index.ntotal > 0:
            distances, indices = self.embedding_index.search(
                np.array([query_embedding]), k
            )
            
            results = []
            entity_ids = list(self.embeddings.keys())
            
            for idx, dist in zip(indices[0], distances[0]):
                if idx < len(entity_ids):
                    entity_id = entity_ids[idx]
                    entity = self.entities.get(entity_id)
                    
                    if entity:
                        results.append({
                            'entity': entity,
                            'similarity': 1 / (1 + dist),  # Convert distance to similarity
                            'type': 'semantic_match'
                        })
            
            return results
        
        return []
    
    def _cypher_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute Cypher query on Neo4j"""
        results = []
        
        try:
            with self.neo4j_driver.session() as session:
                result = session.run(query)
                for record in result:
                    results.append(dict(record))
        except Exception as e:
            logger.error(f"Cypher query error: {e}")
        
        return results
    
    def _pattern_search(self, pattern: str) -> List[Dict[str, Any]]:
        """Search for specific patterns in graph"""
        results = []
        
        # Simple pattern matching
        if pattern == "inheritance":
            # Find inheritance relationships
            for edge in self.graph.edges(data=True):
                if edge[2].get('relationship_type') == 'INHERITS':
                    results.append({
                        'source': self.entities.get(edge[0]),
                        'target': self.entities.get(edge[1]),
                        'relationship': 'inheritance'
                    })
        
        elif pattern == "clusters":
            # Find clusters
            if self.graph.number_of_nodes() > 0:
                communities = list(nx.community.greedy_modularity_communities(
                    self.graph.to_undirected()
                ))
                
                for i, community in enumerate(communities):
                    results.append({
                        'cluster_id': i,
                        'entities': [self.entities.get(node) for node in community],
                        'size': len(community)
                    })
        
        return results
    
    def _graph_query(self, query: str) -> List[Dict[str, Any]]:
        """Basic graph queries"""
        results = []
        
        # Parse simple queries
        if query.startswith("neighbors:"):
            node_id = query.split(":", 1)[1].strip()
            if node_id in self.graph:
                neighbors = list(self.graph.neighbors(node_id))
                results = [{'entity': self.entities.get(n)} for n in neighbors]
        
        elif query.startswith("path:"):
            # Find paths between nodes
            parts = query.split(":", 1)[1].strip().split(",")
            if len(parts) == 2:
                source, target = parts[0].strip(), parts[1].strip()
                if source in self.graph and target in self.graph:
                    try:
                        path = nx.shortest_path(self.graph, source, target)
                        results = [{'path': [self.entities.get(n) for n in path]}]
                    except nx.NetworkXNoPath:
                        pass
        
        return results
    
    def get_insights(self) -> List[KnowledgeInsight]:
        """Get insights from knowledge graph"""
        insights = []
        
        # Reasoning insights
        if self.config.enable_reasoning:
            reasoning_insights = self.reasoner.reason()
            insights.extend(reasoning_insights)
        
        # Pattern insights
        pattern_insights = self.reasoner.find_patterns(self.graph)
        insights.extend(pattern_insights)
        
        # Statistical insights
        if self.graph.number_of_nodes() > 0:
            # Density insight
            density = nx.density(self.graph)
            insights.append(KnowledgeInsight(
                insight_id=hashlib.md5("density".encode()).hexdigest()[:16],
                insight_type="GRAPH_STAT",
                entities=[],
                description=f"Knowledge graph density: {density:.3f}",
                confidence=1.0,
                evidence=[{'density': density}]
            ))
            
            # Component insight
            components = list(nx.weakly_connected_components(self.graph))
            insights.append(KnowledgeInsight(
                insight_id=hashlib.md5("components".encode()).hexdigest()[:16],
                insight_type="GRAPH_STAT",
                entities=[],
                description=f"Found {len(components)} connected components",
                confidence=1.0,
                evidence=[{'num_components': len(components)}]
            ))
        
        return insights
    
    def transfer_knowledge(self, target_project: str) -> Dict[str, Any]:
        """Transfer knowledge to another project"""
        # Find relevant knowledge for target project
        relevant_entities = []
        relevant_relationships = []
        
        # Semantic search for project-related entities
        project_results = self._semantic_search(target_project, k=50)
        
        for result in project_results:
            entity = result['entity']
            relevant_entities.append(entity)
            
            # Find related entities
            if entity.entity_id in self.graph:
                neighbors = self.graph.neighbors(entity.entity_id)
                for neighbor in neighbors:
                    if neighbor in self.entities:
                        relevant_entities.append(self.entities[neighbor])
        
        # Find relationships
        entity_ids = {e.entity_id for e in relevant_entities}
        for rel in self.relationships.values():
            if rel.source_id in entity_ids and rel.target_id in entity_ids:
                relevant_relationships.append(rel)
        
        return {
            'entities': relevant_entities,
            'relationships': relevant_relationships,
            'num_entities': len(relevant_entities),
            'num_relationships': len(relevant_relationships)
        }
    
    def generate_documentation(self, entity_id: str) -> str:
        """Generate documentation for entity"""
        if entity_id not in self.entities:
            return ""
        
        entity = self.entities[entity_id]
        doc = f"# {entity.name}\n\n"
        doc += f"**Type**: {entity.entity_type}\n\n"
        
        # Add properties
        if entity.properties:
            doc += "## Properties\n\n"
            for prop, value in entity.properties.items():
                if prop != 'docstring':
                    doc += f"- **{prop}**: {value}\n"
        
        # Add docstring
        if 'docstring' in entity.properties and entity.properties['docstring']:
            doc += f"\n## Description\n\n{entity.properties['docstring']}\n"
        
        # Add relationships
        if entity_id in self.graph:
            edges = list(self.graph.edges(entity_id, data=True))
            if edges:
                doc += "\n## Relationships\n\n"
                for _, target, data in edges:
                    target_entity = self.entities.get(target)
                    if target_entity:
                        doc += f"- **{data['relationship_type']}** -> {target_entity.name}\n"
        
        # Add usage examples (if available)
        similar_entities = self._semantic_search(entity.name, k=5)
        if len(similar_entities) > 1:
            doc += "\n## Related Entities\n\n"
            for result in similar_entities[1:]:  # Skip self
                related = result['entity']
                doc += f"- {related.name} ({related.entity_type})\n"
        
        return doc
    
    def _sync_to_neo4j(self, entities: List[Entity], relationships: List[Relationship]):
        """Sync entities and relationships to Neo4j"""
        if not self.neo4j_driver:
            return
        
        try:
            with self.neo4j_driver.session() as session:
                # Create entities
                for entity in entities:
                    session.run(
                        """
                        MERGE (e:Entity {entity_id: $entity_id})
                        SET e.name = $name,
                            e.entity_type = $entity_type,
                            e.properties = $properties
                        """,
                        entity_id=entity.entity_id,
                        name=entity.name,
                        entity_type=entity.entity_type,
                        properties=json.dumps(entity.properties)
                    )
                
                # Create relationships
                for rel in relationships:
                    session.run(
                        """
                        MATCH (a:Entity {entity_id: $source_id})
                        MATCH (b:Entity {entity_id: $target_id})
                        MERGE (a)-[r:RELATED {relationship_id: $rel_id}]->(b)
                        SET r.relationship_type = $rel_type,
                            r.properties = $properties
                        """,
                        source_id=rel.source_id,
                        target_id=rel.target_id,
                        rel_id=rel.relationship_id,
                        rel_type=rel.relationship_type,
                        properties=json.dumps(rel.properties)
                    )
        
        except Exception as e:
            logger.error(f"Neo4j sync error: {e}")
    
    def _auto_documentation_loop(self):
        """Automatically generate and update documentation"""
        while True:
            try:
                # Generate docs for entities without documentation
                for entity_id, entity in self.entities.items():
                    if 'auto_doc' not in entity.metadata:
                        doc = self.generate_documentation(entity_id)
                        entity.metadata['auto_doc'] = doc
                        entity.metadata['doc_generated'] = datetime.now()
                
                time.sleep(self.config.doc_update_interval)
                
            except Exception as e:
                logger.error(f"Auto documentation error: {e}")
                time.sleep(300)
    
    def visualize(self, output_file: str = "knowledge_graph.html", max_nodes: int = 100):
        """Visualize knowledge graph"""
        net = Network(height='750px', width='100%', directed=True)
        
        # Add nodes
        nodes_added = 0
        for node_id in list(self.graph.nodes())[:max_nodes]:
            entity = self.entities.get(node_id)
            if entity:
                color = {
                    'CLASS': '#FF6B6B',
                    'FUNCTION': '#4ECDC4',
                    'MODULE': '#45B7D1',
                    'API_CLASS': '#96CEB4',
                    'API_FUNCTION': '#FECA57'
                }.get(entity.entity_type, '#DDA0DD')
                
                net.add_node(
                    node_id,
                    label=entity.name,
                    title=f"{entity.entity_type}: {entity.name}",
                    color=color,
                    size=20
                )
                nodes_added += 1
        
        # Add edges
        for edge in self.graph.edges(data=True):
            if edge[0] in net.nodes and edge[1] in net.nodes:
                net.add_edge(
                    edge[0],
                    edge[1],
                    title=edge[2].get('relationship_type', 'related'),
                    color='#888888'
                )
        
        net.save_graph(output_file)
        logger.info(f"Knowledge graph visualization saved to {output_file}")
    
    def export(self, format: str = "json") -> str:
        """Export knowledge graph"""
        if format == "json":
            data = {
                'entities': [
                    {
                        'id': e.entity_id,
                        'type': e.entity_type,
                        'name': e.name,
                        'properties': e.properties
                    }
                    for e in self.entities.values()
                ],
                'relationships': [
                    {
                        'id': r.relationship_id,
                        'source': r.source_id,
                        'target': r.target_id,
                        'type': r.relationship_type
                    }
                    for r in self.relationships.values()
                ]
            }
            return json.dumps(data, indent=2)
        
        elif format == "rdf":
            g = Graph()
            nexus = Namespace("http://nexus.ai/")
            
            for entity in self.entities.values():
                subject = URIRef(f"http://nexus.ai/entity/{entity.entity_id}")
                g.add((subject, RDF.type, nexus[entity.entity_type]))
                g.add((subject, RDFS.label, Literal(entity.name)))
            
            for rel in self.relationships.values():
                subject = URIRef(f"http://nexus.ai/entity/{rel.source_id}")
                predicate = nexus[rel.relationship_type]
                obj = URIRef(f"http://nexus.ai/entity/{rel.target_id}")
                g.add((subject, predicate, obj))
            
            return g.serialize(format='turtle')
        
        return ""
    
    def save(self, file_path: str):
        """Save knowledge graph to file"""
        data = {
            'entities': self.entities,
            'relationships': self.relationships,
            'embeddings': self.embeddings
        }
        
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
    
    def load(self, file_path: str):
        """Load knowledge graph from file"""
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        
        self.entities = data['entities']
        self.relationships = data['relationships']
        self.embeddings = data['embeddings']
        
        # Rebuild graph
        self.graph.clear()
        for entity in self.entities.values():
            self.graph.add_node(
                entity.entity_id,
                entity_type=entity.entity_type,
                name=entity.name,
                properties=entity.properties
            )
        
        for rel in self.relationships.values():
            self.graph.add_edge(
                rel.source_id,
                rel.target_id,
                relationship_type=rel.relationship_type,
                properties=rel.properties
            )
        
        # Rebuild FAISS index
        self._initialize_embedding_index()
        for embedding in self.embeddings.values():
            self.embedding_index.add(np.array([embedding]))


# Example usage
if __name__ == "__main__":
    # Initialize knowledge graph
    config = KnowledgeConfig(
        spacy_model="en_core_web_sm",  # Use smaller model for demo
        enable_reasoning=True,
        auto_generate_docs=True
    )
    
    kg = NexusKnowledgeGraph(config)
    
    # Add knowledge from text
    text = """
    NEXUS is an AI development platform that uses machine learning for code optimization.
    The platform includes components like the Learning Engine and Pattern Detector.
    The Learning Engine uses transformer models like CodeBERT for understanding code.
    """
    
    result = kg.add_knowledge("demo_text", text, "text")
    print(f"Added {result['entities_added']} entities and {result['relationships_added']} relationships")
    
    # Add knowledge from code
    code = """
class NexusCore:
    def __init__(self):
        self.learning_engine = LearningEngine()
        self.pattern_detector = PatternDetector()
    
    def optimize(self, code):
        patterns = self.pattern_detector.detect(code)
        return self.learning_engine.optimize(patterns)
"""
    
    result = kg.add_knowledge("demo_code", code, "code")
    print(f"Added {result['entities_added']} entities from code")
    
    # Query knowledge
    results = kg.query("machine learning", "semantic")
    print(f"\nSemantic search results for 'machine learning':")
    for result in results[:3]:
        print(f"- {result['entity'].name} ({result['entity'].entity_type})")
    
    # Get insights
    insights = kg.get_insights()
    print(f"\nDiscovered {len(insights)} insights:")
    for insight in insights[:3]:
        print(f"- {insight.insight_type}: {insight.description}")
    
    # Generate documentation
    entities = list(kg.entities.values())
    if entities:
        doc = kg.generate_documentation(entities[0].entity_id)
        print(f"\nGenerated documentation for {entities[0].name}:")
        print(doc[:200] + "...")
    
    # Visualize
    kg.visualize("knowledge_graph_demo.html")
    print("\nKnowledge graph visualization saved!")