"""
Sentiment analysis section - Analyze and visualize emotional tone (supports English, Spanish, Portuguese, French)
"""

from nicegui import ui
from ...services.therapeutic_model_service import TherapeuticModelService
from ..theme import get_button_class, get_paragraph_class
from ...config import SENTIMENT_COLORS


class SentimentSection:
    """Sentiment analysis section for emotional tone analysis"""
    
    def __init__(self, app_state):
        self.app_state = app_state
        self.therapeutic_model = TherapeuticModelService()
        self.paragraph_container = None
        self.analysis_started = False
        self.sentiment_summary_container = None
        
    def create(self):
        """Create the sentiment analysis section UI"""
        with ui.column().classes('w-full gap-4'):
            self._create_header()
            self._create_analysis_controls()
            self._create_paragraph_display()
            self._create_sentiment_summary()
            
            # Refresh paragraph display when section is created/shown
            self.refresh()
    
    def _create_header(self):
        """Create section header"""
        with ui.column().classes('w-full gap-2'):
            ui.label('Sentiment Analysis').classes('text-h5')
            ui.label(
                'Analyze emotional tone using AI model (supports English, Spanish, Portuguese, French)'
            ).classes('text-body2 text-grey-6')
    
    def _create_analysis_controls(self):
        """Create analysis control buttons"""
        with ui.row().classes('w-full gap-2'):
            ui.button(
                'Start Sentiment Analysis',
                on_click=self._start_analysis,
                icon='sentiment_satisfied'
            ).classes(get_button_class('primary'))
            
            ui.button(
                'Reset All Sentiments',
                on_click=self._reset_sentiments,
                icon='refresh'
            ).classes(get_button_class('secondary')).props('outline')
    
    def _create_paragraph_display(self):
        """Create paragraph display area"""
        with ui.column().classes('w-full gap-2'):
            ui.label('Transcript Paragraphs').classes('text-h6')
            ui.label(
                'Click on sentiment badges to manually change sentiment classification'
            ).classes('text-body2 text-grey-6')
            
            # Container for paragraphs
            self.paragraph_container = ui.column().classes('w-full gap-2')
    
    def _create_sentiment_summary(self):
        """Create sentiment summary section"""
        with ui.column().classes('w-full gap-2'):
            ui.label('Sentiment Summary').classes('text-h6')
            self.sentiment_summary_container = ui.column().classes('w-full gap-2')
    
    def _start_analysis(self):
        """Start sentiment analysis using the therapeutic BERT model"""
        if not self.app_state.paragraphs:
            ui.notify('No transcript available for analysis', type='warning')
            return
        
        if not self.therapeutic_model.is_available():
            ui.notify('Therapeutic model not available. Please check model files.', type='warning')
            return
        
        total_paragraphs = len(self.app_state.paragraphs)
        ui.notify(f'Starting sentiment analysis on {total_paragraphs} paragraphs...', type='info')
        
        try:
            # Process each paragraph with progress updates
            for i, paragraph in enumerate(self.app_state.paragraphs):
                # Show progress every 5 paragraphs or on last paragraph
                if i % 5 == 0 or i == total_paragraphs - 1:
                    progress = int((i + 1) / total_paragraphs * 100)
                    ui.notify(f'Progress: {progress}% ({i + 1}/{total_paragraphs})', type='info')
                
                # Use therapeutic model for sentiment analysis
                result = self.therapeutic_model.analyze_text(paragraph.text)
                paragraph.sentiment = result['sentiment']
                
                # Store confidence for potential future use
                if not hasattr(paragraph, 'sentiment_confidence'):
                    paragraph.sentiment_confidence = result['sentiment_confidence']
            
            self.analysis_started = True
            
            # Update UI
            self._update_paragraph_display()
            self._update_sentiment_summary()
            
            # Count sentiments
            positive_count = sum(1 for p in self.app_state.paragraphs if p.sentiment == 'positive')
            negative_count = sum(1 for p in self.app_state.paragraphs if p.sentiment == 'negative')
            neutral_count = sum(1 for p in self.app_state.paragraphs if p.sentiment == 'neutral')
            mixed_count = sum(1 for p in self.app_state.paragraphs if p.sentiment == 'mixed')
            
            ui.notify(
                f'✅ Sentiment analysis complete! '
                f'Positive: {positive_count}, Negative: {negative_count}, '
                f'Neutral: {neutral_count}, Mixed: {mixed_count}', 
                type='positive'
            )
            
        except Exception as e:
            ui.notify(f'❌ Error during sentiment analysis: {str(e)}', type='negative')
    
    def _reset_sentiments(self):
        """Reset all sentiment classifications to neutral"""
        if not self.app_state.paragraphs:
            ui.notify('No transcript available', type='warning')
            return
        
        # Reset all paragraphs to neutral sentiment
        for paragraph in self.app_state.paragraphs:
            paragraph.sentiment = 'neutral'
            if hasattr(paragraph, 'sentiment_confidence'):
                delattr(paragraph, 'sentiment_confidence')
        
        self.analysis_started = False
        
        # Update UI
        self._update_paragraph_display()
        self._update_sentiment_summary()
        
        ui.notify('All sentiments reset to neutral', type='info')
    
    def _update_paragraph_display(self):
        """Update the paragraph display with sentiment badges"""
        if not self.paragraph_container:
            return
            
        self.paragraph_container.clear()
        
        with self.paragraph_container:
            if not self.app_state.paragraphs:
                ui.label('No transcript loaded. Please upload a transcript in the Home section.').classes('text-body2 text-grey-6 text-center p-4')
                return
            
            for paragraph in self.app_state.paragraphs:
                with ui.card().classes('paragraph-card p-4'):
                    with ui.row().classes('w-full items-center gap-2'):
                        ui.label(f'Paragraph {paragraph.id + 1}').classes('text-caption text-grey-6')
                        
                        # Sentiment badge with click handler
                        sentiment_color = self._get_sentiment_color(paragraph.sentiment)
                        sentiment_badge = ui.badge(
                            paragraph.sentiment.title(),
                            color=sentiment_color
                        ).classes('cursor-pointer')
                        
                        # Add click handler to toggle sentiment
                        sentiment_badge.on('click', lambda p=paragraph: self._toggle_sentiment(p))
                        
                        # Show confidence if available
                        if hasattr(paragraph, 'sentiment_confidence'):
                            confidence_pct = int(paragraph.sentiment_confidence * 100)
                            ui.label(f'({confidence_pct}%)').classes('text-caption text-grey-5')
                    
                    # Paragraph text with sentiment-based styling
                    text_class = f'text-body2 q-mt-sm sentiment-{paragraph.sentiment}'
                    ui.label(paragraph.text).classes(text_class)
    
    def _get_sentiment_color(self, sentiment):
        """Get color for sentiment badge"""
        colors = {
            'positive': 'positive',
            'negative': 'negative',
            'neutral': 'grey',
            'mixed': 'warning'
        }
        return colors.get(sentiment, 'grey')
    
    def _toggle_sentiment(self, paragraph):
        """Toggle sentiment assignment for a paragraph"""
        sentiments = ['positive', 'negative', 'neutral', 'mixed']
        current_index = sentiments.index(paragraph.sentiment) if paragraph.sentiment in sentiments else 2
        next_index = (current_index + 1) % len(sentiments)
        paragraph.sentiment = sentiments[next_index]
        
        # Update displays
        self._update_paragraph_display()
        self._update_sentiment_summary()
        
        # Safe notification - handle case where UI context is deleted
        try:
            ui.notify(f'Changed paragraph {paragraph.id + 1} sentiment to {paragraph.sentiment.title()}', type='info')
        except RuntimeError as e:
            if "parent element" in str(e) and "deleted" in str(e):
                # UI context was deleted during refresh, ignore the notification
                pass
            else:
                raise e
    
    def _update_sentiment_summary(self):
        """Update sentiment summary statistics"""
        if not self.sentiment_summary_container:
            return
            
        self.sentiment_summary_container.clear()
        
        with self.sentiment_summary_container:
            if not self.app_state.paragraphs:
                ui.label('No data available for summary').classes('text-body2 text-grey-6')
                return
            
            # Calculate sentiment counts
            sentiment_counts = {
                'positive': sum(1 for p in self.app_state.paragraphs if p.sentiment == 'positive'),
                'negative': sum(1 for p in self.app_state.paragraphs if p.sentiment == 'negative'),
                'neutral': sum(1 for p in self.app_state.paragraphs if p.sentiment == 'neutral'),
                'mixed': sum(1 for p in self.app_state.paragraphs if p.sentiment == 'mixed')
            }
            
            total_paragraphs = len(self.app_state.paragraphs)
            
            # Display summary cards
            with ui.row().classes('w-full gap-4'):
                for sentiment, count in sentiment_counts.items():
                    percentage = (count / total_paragraphs * 100) if total_paragraphs > 0 else 0
                    color = self._get_sentiment_color(sentiment)
                    
                    with ui.card().classes('p-4 text-center'):
                        ui.badge(sentiment.title(), color=color).classes('q-mb-sm')
                        ui.label(str(count)).classes('text-h6')
                        ui.label(f'{percentage:.1f}%').classes('text-caption text-grey-6')
    
    def refresh(self):
        """Refresh displays when section becomes active"""
        if self.paragraph_container:
            self._update_paragraph_display()
        if self.sentiment_summary_container:
            self._update_sentiment_summary()
