"""
NLP service for text processing and analysis
Placeholder implementations for sentiment analysis, entity recognition, etc.
"""

from typing import List, Dict, Tuple
import re
import random
import stanza
from ..app_state import Entity


class NLPService:
    """Service for natural language processing tasks"""
    
    # Class-level variables for singleton-like behavior
    _shared_pipeline = None
    _shared_initialized = False
    
    def __init__(self):
        # Use shared pipeline if available
        self.nlp_pipeline = NLPService._shared_pipeline
        self._stanza_initialized = NLPService._shared_initialized
        
        # Other models (placeholders for now)
        self.sentiment_model = None
        self.speaker_model = None
    
    def _initialize_stanza(self):
        """Initialize Stanza NLP pipeline with optimized settings"""
        if self._stanza_initialized or NLPService._shared_initialized:
            if NLPService._shared_pipeline:
                self.nlp_pipeline = NLPService._shared_pipeline
                self._stanza_initialized = True
            return
            
        NLPService._shared_initialized = True
        self._stanza_initialized = True
        
        try:
            # Try to initialize with minimal processors and no verbose output
            pipeline = stanza.Pipeline(
                'en', 
                processors='tokenize,ner', 
                download_method=None,
                verbose=False,
                use_gpu=False  # Force CPU to avoid GPU initialization overhead
            )
            NLPService._shared_pipeline = pipeline
            self.nlp_pipeline = pipeline
            print(" Stanza pipeline initialized successfully")
        except Exception:
            try:
                # If model not found, download with minimal output
                print(" Downloading Stanza model (first time only)...")
                stanza.download('en', verbose=False)
                pipeline = stanza.Pipeline(
                    'en', 
                    processors='tokenize,ner',
                    verbose=False,
                    use_gpu=False
                )
                NLPService._shared_pipeline = pipeline
                self.nlp_pipeline = pipeline
                print(" Stanza model downloaded and initialized")
            except Exception as e:
                print(f" Could not initialize Stanza: {e}")
                print(" Falling back to regex-based extraction")
                NLPService._shared_pipeline = None
                self.nlp_pipeline = None

    def analyze_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of text
        Returns: 'positive', 'negative', 'neutral', or 'mixed'
        """
        # Placeholder implementation
        # In practice, this would use a trained sentiment analysis model
        
        # Simple keyword-based approach for demonstration
        positive_words = ['happy', 'joy', 'good', 'great', 'wonderful', 'amazing', 'love', 'excellent']
        negative_words = ['sad', 'angry', 'bad', 'terrible', 'awful', 'hate', 'horrible', 'worst']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        elif positive_count > 0 and negative_count > 0:
            return 'mixed'
        else:
            return 'neutral'
    
    def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract named entities from text using Stanza NER with regex fallback
        Returns list of Entity objects
        """
        entities = []
        
        # Initialize Stanza only when needed
        if not self._stanza_initialized:
            self._initialize_stanza()
        
        if self.nlp_pipeline:
            try:
                # Use Stanza for entity extraction
                doc = self.nlp_pipeline(text)
                
                for sentence in doc.sentences:
                    for entity in sentence.ents:
                        # Map Stanza entity types to our types
                        entity_type = self._map_stanza_entity_type(entity.type)
                        
                        # Calculate character positions
                        start_pos = entity.start_char
                        end_pos = entity.end_char
                        
                        entities.append(Entity(
                            text=entity.text,
                            entity_type=entity_type,
                            start_pos=start_pos,
                            end_pos=end_pos
                        ))
                        
            except Exception as e:
                print(f"Error in Stanza entity extraction: {e}")
                # Fall back to regex-based extraction
                return self._extract_entities_regex(text)
        else:
            # Fall back to regex-based extraction
            return self._extract_entities_regex(text)
        
        return entities
    
    def extract_entities_with_stanza(self, text: str) -> List[Entity]:
        """
        Extract entities using Stanza NER (slower but more accurate)
        Only use this method when high accuracy is required
        """
        entities = []
        
        # Initialize Stanza only when explicitly requested
        if not self._stanza_initialized:
            self._initialize_stanza()
        
        if self.nlp_pipeline:
            try:
                # Use Stanza for entity extraction
                doc = self.nlp_pipeline(text)
                
                for sentence in doc.sentences:
                    for entity in sentence.ents:
                        # Map Stanza entity types to our types
                        entity_type = self._map_stanza_entity_type(entity.type)
                        
                        # Calculate character positions
                        start_pos = entity.start_char
                        end_pos = entity.end_char
                        
                        entities.append(Entity(
                            text=entity.text,
                            entity_type=entity_type,
                            start_pos=start_pos,
                            end_pos=end_pos
                        ))
                        
            except Exception as e:
                print(f"Error in Stanza entity extraction: {e}")
                # Fall back to regex-based extraction
                return self._extract_entities_regex(text)
        else:
            # Fall back to regex-based extraction
            return self._extract_entities_regex(text)
        
        return entities
    
    def _map_stanza_entity_type(self, stanza_type: str) -> str:
        """Map Stanza entity types to our standardized types"""
        mapping = {
            'PERSON': 'PERSON',
            'PER': 'PERSON',
            'ORG': 'ORGANIZATION',
            'ORGANIZATION': 'ORGANIZATION',
            'GPE': 'LOCATION',
            'LOCATION': 'LOCATION',
            'LOC': 'LOCATION',
            'DATE': 'DATE',
            'TIME': 'TIME',
            'MONEY': 'MONEY',
            'PERCENT': 'PERCENT',
            'PHONE': 'PHONE',
            'EMAIL': 'EMAIL',
            'MISC': 'MISC'
        }
        return mapping.get(stanza_type, stanza_type)
    
    def _extract_entities_regex(self, text: str) -> List[Entity]:
        """
        Fallback regex-based entity extraction
        """
        entities = []
        
        # Enhanced patterns for better detection
        patterns = {
            'PERSON': r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
            'DATE': r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b',
            'TIME': r'\b\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?\b',
            'PHONE': r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'MONEY': r'\$\d+(?:,\d{3})*(?:\.\d{2})?',
            'PERCENT': r'\d+(?:\.\d+)?%'
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Skip common words that might match person pattern
                if entity_type == 'PERSON':
                    word = match.group().lower()
                    if word in ['the', 'and', 'but', 'for', 'with', 'this', 'that', 'they', 'them', 'their']:
                        continue
                
                entity = Entity(
                    text=match.group(),
                    entity_type=entity_type,
                    start_pos=match.start(),
                    end_pos=match.end()
                )
                entities.append(entity)
        
        return entities
    
    def identify_speaker(self, text: str, context: List[str] = None) -> str:
        """
        Identify speaker of a text segment
        Returns: 'client', 'therapist', or 'unknown'
        """
        # Placeholder implementation
        # In practice, this would use speaker identification models
        
        text_lower = text.lower()
        
        # Simple heuristics for demonstration
        therapist_indicators = [
            'how does that make you feel',
            'tell me more about',
            'what do you think',
            'can you describe',
            'i understand',
            'that sounds',
            'from my perspective'
        ]
        
        client_indicators = [
            'i feel',
            'i think',
            'i believe',
            'my problem',
            'i\'m struggling',
            'i don\'t know',
            'it\'s hard'
        ]
        
        therapist_score = sum(1 for indicator in therapist_indicators if indicator in text_lower)
        client_score = sum(1 for indicator in client_indicators if indicator in text_lower)
        
        if therapist_score > client_score:
            return 'therapist'
        elif client_score > therapist_score:
            return 'client'
        else:
            return 'unknown'
    
    def suggest_codes(self, text: str, coding_schemes: List) -> List[Tuple[str, float]]:
        """
        Suggest coding schemes for a text based on keywords
        Returns list of (scheme_id, confidence_score) tuples
        """
        suggestions = []
        text_lower = text.lower()
        
        for scheme in coding_schemes:
            score = 0
            for keyword in scheme.keywords:
                if keyword.lower() in text_lower:
                    score += 1
            
            if score > 0:
                # Normalize score by number of keywords
                confidence = score / len(scheme.keywords) if scheme.keywords else 0
                suggestions.append((scheme.id, confidence))
        
        # Sort by confidence score
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions
    
    def anonymize_text(self, text: str, entities: List[Entity]) -> str:
        """
        Anonymize text by replacing entities with placeholders
        """
        anonymized_text = text
        
        # Sort entities by start position in reverse order to avoid offset issues
        sorted_entities = sorted(entities, key=lambda e: e.start_pos, reverse=True)
        
        for entity in sorted_entities:
            if entity.anonymized:
                replacement = entity.replacement or f"[{entity.entity_type}]"
                anonymized_text = (
                    anonymized_text[:entity.start_pos] + 
                    replacement + 
                    anonymized_text[entity.end_pos:]
                )
        
        return anonymized_text
    
    def get_text_statistics(self, text: str) -> Dict[str, int]:
        """
        Get basic text statistics
        """
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        paragraphs = text.split('\n\n')
        
        return {
            'characters': len(text),
            'words': len(words),
            'sentences': len([s for s in sentences if s.strip()]),
            'paragraphs': len([p for p in paragraphs if p.strip()]),
            'avg_words_per_sentence': len(words) / max(len(sentences), 1),
            'avg_sentences_per_paragraph': len(sentences) / max(len(paragraphs), 1)
        }
