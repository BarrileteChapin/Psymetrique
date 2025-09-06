"""
Central application state management
Handles all data persistence and state transitions
"""

from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Entity:
    """Represents a detected entity in the text"""
    text: str
    entity_type: str
    start_pos: int
    end_pos: int
    anonymized: bool = False
    replacement: str = ""


@dataclass
class Paragraph:
    """Represents a paragraph in the transcript"""
    id: int
    text: str
    speaker: str = "unknown"  # "client", "therapist", "unknown"
    sentiment: str = "neutral"  # "positive", "negative", "neutral", "mixed"
    entities: List[Entity] = field(default_factory=list)
    codes: List[str] = field(default_factory=list)


@dataclass
class CodingScheme:
    """Represents a coding scheme entry"""
    id: str
    title: str
    keywords: List[str] = field(default_factory=list)


class AppState:
    """Central state management for the application"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset all state to initial values"""
        self.current_step: int = 0
        self.transcript_file_path: Optional[str] = None
        self.original_transcript: str = ""
        self.current_transcript: str = ""
        self.paragraphs: List[Paragraph] = []
        self.entities: List[Entity] = []
        self.coding_schemes: List[CodingScheme] = []
        self.analysis_results: Dict[str, Any] = {}
        
    def load_transcript(self, content: str, file_path: str = None):
        """Load transcript content and split into paragraphs"""
        self.original_transcript = content
        self.current_transcript = content
        self.transcript_file_path = file_path
        
        # Split into paragraphs with better handling of different line break patterns
        self._split_into_paragraphs(content)
    
    def save_transcript_changes(self, new_content: str):
        """Save changes made to the transcript"""
        self.current_transcript = new_content
        # Re-split into paragraphs
        self._split_into_paragraphs(new_content)
    
    def reload_transcript(self):
        """Reload transcript from original content"""
        self.current_transcript = self.original_transcript
        self._split_into_paragraphs(self.original_transcript)
    
    def _split_into_paragraphs(self, content: str):
        """Split content into paragraphs using multiple strategies"""
        # Try different splitting strategies
        paragraphs_text = []
        
        # Strategy 1: Split by double line breaks
        if '\n\n' in content:
            paragraphs_text = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # Strategy 2: If no double line breaks, split by single line breaks
        elif '\n' in content:
            paragraphs_text = [p.strip() for p in content.split('\n') if p.strip()]
        
        # Strategy 3: If no line breaks, split by sentences (as fallback)
        else:
            import re
            sentences = re.split(r'[.!?]+', content)
            paragraphs_text = [s.strip() for s in sentences if s.strip()]
        
        # If still only one paragraph and it's very long, try to split it further
        if len(paragraphs_text) == 1 and len(paragraphs_text[0]) > 500:
            # Try splitting by periods followed by capital letters
            import re
            sentences = re.split(r'\.(?=\s+[A-Z])', paragraphs_text[0])
            if len(sentences) > 1:
                paragraphs_text = [s.strip() + '.' if not s.endswith('.') else s.strip() for s in sentences if s.strip()]
        
        self.paragraphs = [
            Paragraph(id=i, text=text) 
            for i, text in enumerate(paragraphs_text)
        ]
    
    def update_paragraph_speaker(self, paragraph_id: int, speaker: str):
        """Update speaker assignment for a paragraph"""
        if 0 <= paragraph_id < len(self.paragraphs):
            self.paragraphs[paragraph_id].speaker = speaker
    
    def update_paragraph_sentiment(self, paragraph_id: int, sentiment: str):
        """Update sentiment for a paragraph"""
        if 0 <= paragraph_id < len(self.paragraphs):
            self.paragraphs[paragraph_id].sentiment = sentiment
    
    def add_paragraph_code(self, paragraph_id: int, code: str):
        """Add a code to a paragraph"""
        if 0 <= paragraph_id < len(self.paragraphs):
            if code not in self.paragraphs[paragraph_id].codes:
                self.paragraphs[paragraph_id].codes.append(code)
    
    def remove_paragraph_code(self, paragraph_id: int, code: str):
        """Remove a code from a paragraph"""
        if 0 <= paragraph_id < len(self.paragraphs):
            if code in self.paragraphs[paragraph_id].codes:
                self.paragraphs[paragraph_id].codes.remove(code)
    
    def add_coding_scheme(self, scheme: CodingScheme):
        """Add a new coding scheme"""
        self.coding_schemes.append(scheme)
    
    def remove_coding_scheme(self, scheme_id: str):
        """Remove a coding scheme"""
        self.coding_schemes = [s for s in self.coding_schemes if s.id != scheme_id]
    
    def get_paragraphs_by_speaker(self, speaker: str) -> List[Paragraph]:
        """Get all paragraphs by a specific speaker"""
        return [p for p in self.paragraphs if p.speaker == speaker]
    
    def get_sentiment_distribution(self) -> Dict[str, int]:
        """Get distribution of sentiments across paragraphs"""
        distribution = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
        for paragraph in self.paragraphs:
            if paragraph.sentiment in distribution:
                distribution[paragraph.sentiment] += 1
        return distribution
    
    def get_coding_distribution(self) -> Dict[str, int]:
        """Get distribution of codes across paragraphs"""
        distribution = {}
        for paragraph in self.paragraphs:
            for code in paragraph.codes:
                distribution[code] = distribution.get(code, 0) + 1
        return distribution
    
    def export_state(self) -> Dict[str, Any]:
        """Export current state to dictionary for serialization"""
        return {
            'current_step': self.current_step,
            'transcript_file_path': self.transcript_file_path,
            'original_transcript': self.original_transcript,
            'current_transcript': self.current_transcript,
            'paragraphs': [
                {
                    'id': p.id,
                    'text': p.text,
                    'speaker': p.speaker,
                    'sentiment': p.sentiment,
                    'codes': p.codes,
                    'entities': [
                        {
                            'text': e.text,
                            'entity_type': e.entity_type,
                            'start_pos': e.start_pos,
                            'end_pos': e.end_pos,
                            'anonymized': e.anonymized,
                            'replacement': e.replacement
                        } for e in p.entities
                    ]
                } for p in self.paragraphs
            ],
            'coding_schemes': [
                {
                    'id': s.id,
                    'title': s.title,
                    'keywords': s.keywords
                } for s in self.coding_schemes
            ],
            'analysis_results': self.analysis_results
        }
    
    def save_to_file(self, file_path: str):
        """Save state to JSON file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.export_state(), f, indent=2, ensure_ascii=False)
    
    def load_from_file(self, file_path: str):
        """Load state from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.current_step = data.get('current_step', 0)
        self.transcript_file_path = data.get('transcript_file_path')
        self.original_transcript = data.get('original_transcript', '')
        self.current_transcript = data.get('current_transcript', '')
        
        # Reconstruct paragraphs
        self.paragraphs = []
        for p_data in data.get('paragraphs', []):
            entities = [
                Entity(
                    text=e['text'],
                    entity_type=e['entity_type'],
                    start_pos=e['start_pos'],
                    end_pos=e['end_pos'],
                    anonymized=e.get('anonymized', False),
                    replacement=e.get('replacement', '')
                ) for e in p_data.get('entities', [])
            ]
            
            paragraph = Paragraph(
                id=p_data['id'],
                text=p_data['text'],
                speaker=p_data.get('speaker', 'unknown'),
                sentiment=p_data.get('sentiment', 'neutral'),
                entities=entities,
                codes=p_data.get('codes', [])
            )
            self.paragraphs.append(paragraph)
        
        # Reconstruct coding schemes
        self.coding_schemes = [
            CodingScheme(
                id=s['id'],
                title=s['title'],
                keywords=s.get('keywords', [])
            ) for s in data.get('coding_schemes', [])
        ]
        
        self.analysis_results = data.get('analysis_results', {})
