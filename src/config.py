"""
Application configuration settings
"""
from pathlib import Path

APP_CONFIG = {
    'title': 'Psymerique - Therapeutic Transcript Analysis',
    'port': 8080,
    'max_file_size': 20 * 1024 * 1024,  # 20MB in bytes
    'allowed_extensions': ['.txt'],
    'favicon': str(Path(__file__).parent / "assets" / "images" / "favicon.ico")
}

# Color palette from instructions
COLORS = {
    'primary': '#3674B5',
    'secondary': '#578FCA', 
    'accent': '#A1E3F9',
    'background': '#D1F8EF',
    'white': '#FFFFFF',
    'light_gray': '#F5F5F5',
    'client_bg': '#E3F2FD',  # Light blue for client text
    'therapist_bg': '#F5F5F5',  # Light grey for therapist text
    'positive': '#4CAF50',
    'negative': '#F44336',
    'neutral': '#9E9E9E',
    'mixed': '#FF9800'
}

# Sentiment colors mapping
SENTIMENT_COLORS = {
    'positive': COLORS['positive'],
    'negative': COLORS['negative'],
    'neutral': COLORS['neutral'],
    'mixed': COLORS['mixed']
}

# Step names for the stepper
STEPS = [
    'Home',
    'Speakers',
    'Entities', 
    'Sentiment',
    'Encoding',
    'Report'
]
