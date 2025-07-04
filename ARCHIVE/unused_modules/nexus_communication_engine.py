"""
NEXUS 2.0 Communication Engine
Adaptive, context-aware communication with multi-modal output
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
import networkx as nx
import textwrap

class CommunicationStyle(Enum):
    """Communication styles"""
    CONCISE = "concise"
    DETAILED = "detailed"
    TECHNICAL = "technical"
    CONVERSATIONAL = "conversational"
    TUTORIAL = "tutorial"

class Urgency(Enum):
    """Message urgency levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class UserPattern:
    """User communication patterns"""
    preferred_style: CommunicationStyle
    avg_message_length: float
    technical_level: float  # 0-1
    prefers_visuals: bool
    response_speed: float  # avg seconds between messages
    common_topics: List[str]
    interaction_count: int
    emotion_baseline: Dict[str, float]

@dataclass
class CommunicationContext:
    """Context for adaptive communication"""
    current_topic: str
    conversation_depth: int
    user_expertise: float
    urgency: Urgency
    requires_clarification: bool
    visual_aids_needed: bool
    code_examples_needed: bool

class CommunicationEngine:
    """Advanced communication system for NEXUS 2.0"""
    
    def __init__(self):
        self.user_patterns: Dict[str, UserPattern] = {}
        self.current_user: Optional[str] = None
        self.conversation_history: List[Dict[str, Any]] = []
        self.verbosity_level = 0.5  # 0-1
        self.emotion_weights = {
            'frustration': 0.0,
            'confusion': 0.0,
            'satisfaction': 0.5,
            'urgency': 0.0
        }
        self.topic_models = self._init_topic_models()
        
    def _init_topic_models(self) -> Dict[str, Dict[str, Any]]:
        """Initialize topic understanding models"""
        return {
            'debugging': {
                'keywords': ['error', 'bug', 'issue', 'problem', 'fix', 'debug', 'crash'],
                'response_style': CommunicationStyle.TECHNICAL,
                'needs_details': True
            },
            'implementation': {
                'keywords': ['implement', 'create', 'build', 'develop', 'add', 'feature'],
                'response_style': CommunicationStyle.TUTORIAL,
                'needs_details': True
            },
            'explanation': {
                'keywords': ['explain', 'what', 'how', 'why', 'understand', 'mean'],
                'response_style': CommunicationStyle.CONVERSATIONAL,
                'needs_details': False
            },
            'optimization': {
                'keywords': ['optimize', 'improve', 'faster', 'performance', 'efficient'],
                'response_style': CommunicationStyle.TECHNICAL,
                'needs_details': True
            }
        }
        
    def analyze_message(self, message: str, user_id: str = "default") -> CommunicationContext:
        """Analyze incoming message for context and emotion"""
        self.current_user = user_id
        
        # Get or create user pattern
        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = UserPattern(
                preferred_style=CommunicationStyle.CONVERSATIONAL,
                avg_message_length=len(message),
                technical_level=0.5,
                prefers_visuals=False,
                response_speed=0.0,
                common_topics=[],
                interaction_count=1,
                emotion_baseline={'frustration': 0.0, 'confusion': 0.0, 
                                'satisfaction': 0.5, 'urgency': 0.0}
            )
        else:
            pattern = self.user_patterns[user_id]
            pattern.interaction_count += 1
            pattern.avg_message_length = (
                pattern.avg_message_length * 0.9 + len(message) * 0.1
            )
            
        # Detect topic
        topic = self._detect_topic(message)
        
        # Detect urgency and emotion
        urgency = self._detect_urgency(message)
        emotions = self._detect_emotions(message)
        
        # Update emotion baseline
        for emotion, score in emotions.items():
            self.emotion_weights[emotion] = self.emotion_weights[emotion] * 0.8 + score * 0.2
            
        # Determine technical level
        technical_level = self._assess_technical_level(message)
        
        # Check if clarification needed
        requires_clarification = self._needs_clarification(message)
        
        # Determine if visuals would help
        visual_aids_needed = self._should_use_visuals(message, topic)
        
        # Determine if code examples needed
        code_examples_needed = self._needs_code_examples(message, topic)
        
        # Create context
        context = CommunicationContext(
            current_topic=topic,
            conversation_depth=len(self.conversation_history),
            user_expertise=technical_level,
            urgency=urgency,
            requires_clarification=requires_clarification,
            visual_aids_needed=visual_aids_needed,
            code_examples_needed=code_examples_needed
        )
        
        # Store in history
        self.conversation_history.append({
            'timestamp': datetime.now(),
            'user_id': user_id,
            'message': message,
            'context': context,
            'emotions': emotions
        })
        
        return context
        
    def generate_response(self, content: Dict[str, Any], context: CommunicationContext) -> Dict[str, Any]:
        """Generate adaptive response based on context"""
        response = {
            'text': '',
            'code': [],
            'visualizations': [],
            'metadata': {
                'style': context.current_topic,
                'verbosity': self.verbosity_level,
                'confidence': 0.0
            }
        }
        
        # Adapt style based on user pattern
        if self.current_user in self.user_patterns:
            pattern = self.user_patterns[self.current_user]
            style = pattern.preferred_style
        else:
            style = CommunicationStyle.CONVERSATIONAL
            
        # Generate main text
        response['text'] = self._adapt_text(content.get('message', ''), style, context)
        
        # Add code examples if needed
        if context.code_examples_needed and 'code' in content:
            response['code'] = self._format_code_examples(content['code'], context)
            
        # Generate visualizations if needed
        if context.visual_aids_needed:
            visualizations = self._generate_visualizations(content, context)
            response['visualizations'] = visualizations
            
        # Progressive disclosure
        if context.conversation_depth > 3 and context.user_expertise > 0.7:
            response['text'] = self._add_advanced_details(response['text'], content)
            
        # Add confidence scoring
        response['metadata']['confidence'] = self._calculate_confidence(content, context)
        
        return response
        
    def _detect_topic(self, message: str) -> str:
        """Detect the main topic of the message"""
        message_lower = message.lower()
        
        topic_scores = {}
        for topic, model in self.topic_models.items():
            score = sum(1 for keyword in model['keywords'] if keyword in message_lower)
            topic_scores[topic] = score
            
        # Return topic with highest score
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        return 'general'
        
    def _detect_urgency(self, message: str) -> Urgency:
        """Detect urgency level in message"""
        urgent_indicators = {
            'asap': 3, 'urgent': 3, 'immediately': 3, 'critical': 4,
            'quickly': 2, 'soon': 2, 'help': 2, 'please': 1,
            'crashed': 4, 'down': 3, 'broken': 3
        }
        
        message_lower = message.lower()
        max_urgency = 1
        
        for indicator, level in urgent_indicators.items():
            if indicator in message_lower:
                max_urgency = max(max_urgency, level)
                
        # Check for multiple exclamation marks
        if message.count('!') > 2:
            max_urgency = max(max_urgency, 3)
            
        return Urgency(max_urgency)
        
    def _detect_emotions(self, message: str) -> Dict[str, float]:
        """Detect emotional indicators in message"""
        emotions = {
            'frustration': 0.0,
            'confusion': 0.0,
            'satisfaction': 0.0,
            'urgency': 0.0
        }
        
        # Frustration indicators
        frustration_words = ['frustrated', 'annoying', 'stuck', 'nothing works', 
                           "can't", "doesn't work", 'broken', 'useless']
        emotions['frustration'] = sum(1 for word in frustration_words 
                                    if word in message.lower()) / len(frustration_words)
        
        # Confusion indicators
        confusion_words = ['confused', "don't understand", 'unclear', 'what does',
                          'how does', '?', 'lost', 'no idea']
        emotions['confusion'] = sum(1 for word in confusion_words 
                                  if word in message.lower()) / len(confusion_words)
        
        # Question marks indicate confusion
        emotions['confusion'] += min(message.count('?') * 0.1, 0.3)
        
        # Satisfaction indicators
        satisfaction_words = ['thanks', 'great', 'perfect', 'awesome', 'helpful',
                            'working', 'solved', 'fixed']
        emotions['satisfaction'] = sum(1 for word in satisfaction_words 
                                     if word in message.lower()) / len(satisfaction_words)
        
        # Urgency from exclamation marks and capitals
        capital_ratio = sum(1 for c in message if c.isupper()) / max(len(message), 1)
        emotions['urgency'] = min(capital_ratio + message.count('!') * 0.1, 1.0)
        
        return emotions
        
    def _assess_technical_level(self, message: str) -> float:
        """Assess technical level of user from message"""
        technical_indicators = {
            'high': ['api', 'algorithm', 'implementation', 'architecture', 'optimize',
                    'complexity', 'async', 'thread', 'memory', 'performance'],
            'medium': ['function', 'variable', 'loop', 'class', 'method', 'error',
                      'debug', 'install', 'configure', 'setup'],
            'low': ['help', 'start', 'begin', 'what is', 'how to', 'explain',
                   'simple', 'basic', 'new to', 'beginner']
        }
        
        message_lower = message.lower()
        scores = {'high': 0, 'medium': 0, 'low': 0}
        
        for level, indicators in technical_indicators.items():
            scores[level] = sum(1 for ind in indicators if ind in message_lower)
            
        total = sum(scores.values())
        if total == 0:
            return 0.5
            
        # Weighted average
        technical_level = (scores['high'] * 1.0 + scores['medium'] * 0.5 + 
                          scores['low'] * 0.1) / total
        
        return min(technical_level, 1.0)
        
    def _needs_clarification(self, message: str) -> bool:
        """Check if message needs clarification"""
        # Vague indicators
        vague_words = ['something', 'stuff', 'thing', 'it', 'that', 'this']
        
        # Check for missing context
        if len(message.split()) < 5:
            return True
            
        # Check for pronouns without clear antecedents
        pronouns_without_context = sum(1 for word in vague_words 
                                     if word in message.lower().split())
        
        return pronouns_without_context > 2
        
    def _should_use_visuals(self, message: str, topic: str) -> bool:
        """Determine if visualizations would help"""
        visual_keywords = ['show', 'diagram', 'visualize', 'graph', 'chart',
                          'flow', 'structure', 'architecture', 'relationship']
        
        # Check direct requests
        if any(keyword in message.lower() for keyword in visual_keywords):
            return True
            
        # Topic-based decisions
        if topic in ['implementation', 'optimization']:
            return True
            
        # Complexity-based decisions
        if self.emotion_weights['confusion'] > 0.5:
            return True
            
        return False
        
    def _needs_code_examples(self, message: str, topic: str) -> bool:
        """Determine if code examples are needed"""
        code_keywords = ['example', 'code', 'snippet', 'how to', 'implement',
                        'write', 'syntax', 'usage']
        
        return (any(keyword in message.lower() for keyword in code_keywords) or
                topic in ['implementation', 'debugging'])
                
    def _adapt_text(self, text: str, style: CommunicationStyle, 
                   context: CommunicationContext) -> str:
        """Adapt text based on style and context"""
        if style == CommunicationStyle.CONCISE:
            # Strip unnecessary words, get to the point
            text = self._make_concise(text)
        elif style == CommunicationStyle.TECHNICAL:
            # Add technical details
            text = self._add_technical_details(text, context)
        elif style == CommunicationStyle.TUTORIAL:
            # Step-by-step approach
            text = self._make_tutorial_style(text)
        elif style == CommunicationStyle.CONVERSATIONAL:
            # Natural, friendly tone
            text = self._make_conversational(text)
            
        # Adjust for urgency
        if context.urgency.value >= 3:
            text = f"**Immediate Action Required**\n\n{text}"
            
        # Adjust for confusion
        if self.emotion_weights['confusion'] > 0.6:
            text = f"Let me clarify this step by step:\n\n{text}"
            
        return text
        
    def _make_concise(self, text: str) -> str:
        """Make text more concise"""
        # Remove filler words
        filler_words = ['basically', 'actually', 'really', 'just', 'very',
                       'quite', 'rather', 'somewhat', 'indeed']
        
        words = text.split()
        filtered = [word for word in words if word.lower() not in filler_words]
        
        # Shorten sentences
        sentences = '. '.join(filtered).split('. ')
        short_sentences = []
        
        for sentence in sentences:
            if len(sentence.split()) > 15:
                # Break long sentences
                parts = sentence.split(', ')
                if len(parts) > 1:
                    short_sentences.extend(parts[:2])
                else:
                    short_sentences.append(sentence[:100] + '...')
            else:
                short_sentences.append(sentence)
                
        return '. '.join(short_sentences)
        
    def _add_technical_details(self, text: str, context: CommunicationContext) -> str:
        """Add technical details to text"""
        if context.user_expertise < 0.7:
            return text
            
        # Add complexity analysis
        technical_addendum = "\n\n**Technical Details:**\n"
        technical_addendum += "- Time Complexity: O(n)\n"
        technical_addendum += "- Space Complexity: O(1)\n"
        technical_addendum += "- Thread Safety: Yes\n"
        
        return text + technical_addendum
        
    def _make_tutorial_style(self, text: str) -> str:
        """Convert to tutorial style with steps"""
        lines = text.split('\n')
        tutorial_text = "Let's go through this step by step:\n\n"
        
        step_num = 1
        for line in lines:
            if line.strip():
                tutorial_text += f"**Step {step_num}:** {line}\n"
                step_num += 1
                
        return tutorial_text
        
    def _make_conversational(self, text: str) -> str:
        """Make text more conversational"""
        # Add friendly phrases
        starters = [
            "I'd be happy to help with that!",
            "Great question!",
            "Let me explain this for you.",
            "Here's what I found:"
        ]
        
        import random
        starter = random.choice(starters)
        
        return f"{starter}\n\n{text}"
        
    def _format_code_examples(self, code_snippets: List[str], 
                            context: CommunicationContext) -> List[Dict[str, str]]:
        """Format code examples based on context"""
        formatted = []
        
        for snippet in code_snippets:
            formatted_snippet = {
                'code': snippet,
                'language': 'python',  # Could be detected
                'explanation': ''
            }
            
            # Add explanations for lower expertise
            if context.user_expertise < 0.5:
                lines = snippet.split('\n')
                explained_lines = []
                
                for line in lines:
                    if line.strip() and not line.strip().startswith('#'):
                        explained_lines.append(f"{line}  # {self._explain_line(line)}")
                    else:
                        explained_lines.append(line)
                        
                formatted_snippet['code'] = '\n'.join(explained_lines)
                
            formatted.append(formatted_snippet)
            
        return formatted
        
    def _explain_line(self, line: str) -> str:
        """Generate simple explanation for code line"""
        if 'def ' in line:
            return "Define a function"
        elif 'class ' in line:
            return "Define a class"
        elif 'for ' in line:
            return "Loop through items"
        elif 'if ' in line:
            return "Check condition"
        elif 'return ' in line:
            return "Return result"
        elif '=' in line and '==' not in line:
            return "Assign value"
        else:
            return "Process data"
            
    def _generate_visualizations(self, content: Dict[str, Any], 
                               context: CommunicationContext) -> List[Dict[str, Any]]:
        """Generate appropriate visualizations"""
        visualizations = []
        
        if 'data_flow' in content:
            viz = self._create_flow_diagram(content['data_flow'])
            visualizations.append(viz)
            
        if 'architecture' in content:
            viz = self._create_architecture_diagram(content['architecture'])
            visualizations.append(viz)
            
        if 'metrics' in content:
            viz = self._create_metrics_chart(content['metrics'])
            visualizations.append(viz)
            
        return visualizations
        
    def _create_flow_diagram(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a flow diagram"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create directed graph
        G = nx.DiGraph()
        
        # Add nodes and edges from flow data
        for step in flow_data.get('steps', []):
            G.add_node(step['name'])
            if 'next' in step:
                G.add_edge(step['name'], step['next'])
                
        # Draw graph
        pos = nx.spring_layout(G)
        nx.draw(G, pos, ax=ax, with_labels=True, node_color='lightblue',
                node_size=3000, font_size=10, font_weight='bold',
                arrows=True, arrowsize=20)
        
        plt.title("Process Flow Diagram")
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return {
            'type': 'flow_diagram',
            'data': image_base64,
            'format': 'png',
            'description': 'Process flow visualization'
        }
        
    def _create_architecture_diagram(self, arch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create architecture diagram"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Simple box diagram for components
        components = arch_data.get('components', [])
        
        y_pos = len(components)
        for i, component in enumerate(components):
            # Draw component box
            rect = plt.Rectangle((1, y_pos - i), 3, 0.8, 
                               fill=True, facecolor='lightgreen',
                               edgecolor='black', linewidth=2)
            ax.add_patch(rect)
            ax.text(2.5, y_pos - i + 0.4, component['name'], 
                   ha='center', va='center', fontsize=12, weight='bold')
            
        ax.set_xlim(0, 5)
        ax.set_ylim(0, len(components) + 1)
        ax.set_aspect('equal')
        ax.axis('off')
        plt.title("System Architecture")
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return {
            'type': 'architecture_diagram',
            'data': image_base64,
            'format': 'png',
            'description': 'System architecture visualization'
        }
        
    def _create_metrics_chart(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Create metrics visualization"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create bar chart
        labels = list(metrics.keys())
        values = list(metrics.values())
        
        bars = ax.bar(labels, values, color='skyblue', edgecolor='navy')
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}', ha='center', va='bottom')
                   
        ax.set_ylabel('Value')
        ax.set_title('Performance Metrics')
        plt.xticks(rotation=45, ha='right')
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return {
            'type': 'metrics_chart',
            'data': image_base64,
            'format': 'png',
            'description': 'Performance metrics visualization'
        }
        
    def _add_advanced_details(self, text: str, content: Dict[str, Any]) -> str:
        """Add advanced details for experienced users"""
        if 'advanced' not in content:
            return text
            
        advanced_section = "\n\n**Advanced Considerations:**\n"
        
        for detail in content['advanced']:
            advanced_section += f"- {detail}\n"
            
        return text + advanced_section
        
    def _calculate_confidence(self, content: Dict[str, Any], 
                            context: CommunicationContext) -> float:
        """Calculate confidence score for response"""
        confidence = 0.5
        
        # Increase confidence based on data availability
        if 'verified' in content and content['verified']:
            confidence += 0.3
            
        if 'sources' in content and len(content['sources']) > 0:
            confidence += 0.1 * min(len(content['sources']), 2)
            
        # Decrease confidence for unclear requests
        if context.requires_clarification:
            confidence -= 0.2
            
        # Adjust based on topic match
        if context.current_topic != 'general':
            confidence += 0.1
            
        return max(0.0, min(1.0, confidence))
        
    def update_user_preferences(self, user_id: str, feedback: Dict[str, Any]):
        """Update user preferences based on feedback"""
        if user_id not in self.user_patterns:
            return
            
        pattern = self.user_patterns[user_id]
        
        # Update style preference
        if 'preferred_style' in feedback:
            pattern.preferred_style = CommunicationStyle(feedback['preferred_style'])
            
        # Update technical level
        if 'too_technical' in feedback:
            if feedback['too_technical']:
                pattern.technical_level = max(0, pattern.technical_level - 0.1)
            else:
                pattern.technical_level = min(1, pattern.technical_level + 0.1)
                
        # Update visual preference
        if 'liked_visuals' in feedback:
            pattern.prefers_visuals = feedback['liked_visuals']
            
    def get_communication_stats(self, user_id: str = None) -> Dict[str, Any]:
        """Get communication statistics"""
        if user_id and user_id in self.user_patterns:
            pattern = self.user_patterns[user_id]
            return {
                'user_id': user_id,
                'interactions': pattern.interaction_count,
                'preferred_style': pattern.preferred_style.value,
                'technical_level': pattern.technical_level,
                'avg_message_length': pattern.avg_message_length,
                'prefers_visuals': pattern.prefers_visuals,
                'common_topics': pattern.common_topics[:5]
            }
        else:
            # Global stats
            return {
                'total_users': len(self.user_patterns),
                'total_conversations': len(self.conversation_history),
                'avg_technical_level': np.mean([p.technical_level 
                                               for p in self.user_patterns.values()]),
                'emotion_baseline': self.emotion_weights
            }