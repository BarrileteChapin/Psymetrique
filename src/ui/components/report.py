"""
Report section - Analysis summary and visualizations
"""

from nicegui import ui
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter
import re
import base64
from io import BytesIO
from ..theme import get_button_class
from ...config import SENTIMENT_COLORS
from ...services.export_service import ExportService
from ...utils.text_processing import extract_meaningful_words

try:
    from wordcloud import WordCloud
    WORDCLOUD_AVAILABLE = True
except ImportError:
    WORDCLOUD_AVAILABLE = False


class ReportSection:
    """Report section for analysis summary and visualizations"""
    
    def __init__(self, app_state):
        self.app_state = app_state
        self.export_service = ExportService(app_state)
        
    def create(self):
        """Create the report section UI"""
        with ui.column().classes('w-full gap-4'):
            self._create_header()
            self._create_visualizations()
            self._create_export_section()
    
    def _create_header(self):
        """Create section header"""
        with ui.column().classes('w-full gap-2'):
            ui.label('Analysis Report').classes('text-h5')
            ui.label(
                'Comprehensive analysis report with word frequency, sentiment distribution, and coding insights'
            ).classes('text-body2 text-grey-6')
    
    def _create_visualizations(self):
        """Create analysis visualizations"""
        with ui.column().classes('w-full gap-4'):
            ui.label('Analysis Visualizations').classes('text-h6')
            
            # Top row - Word frequency and Word cloud
            with ui.row().classes('w-full gap-4'):
                with ui.column().classes('flex-1 gap-4'):
                    self.word_freq_container = ui.column().classes('w-full')
                    self._create_word_frequency_chart()
                with ui.column().classes('flex-1 gap-4'):
                    self.word_cloud_container = ui.column().classes('w-full')
                    self._create_word_cloud()
            
            # Second row - Sentiment and Encoding
            with ui.row().classes('w-full gap-4'):
                with ui.column().classes('flex-1 gap-4'):
                    self.sentiment_container = ui.column().classes('w-full')
                    self._create_enhanced_sentiment_chart()
                with ui.column().classes('flex-1 gap-4'):
                    self.encoding_container = ui.column().classes('w-full')
                    self._create_enhanced_encoding_overview()
    
    def _create_word_frequency_chart(self):
        """Create top word frequency bar chart"""
        with self.word_freq_container:
            ui.label('Top Word Frequency').classes('text-h6 q-mb-md')
            
            if not self.app_state.paragraphs:
                ui.label('No transcript data available').classes('text-body2 text-grey-6 text-center p-4')
                return
            
            # Extract and count words
            all_text = ' '.join([p.text for p in self.app_state.paragraphs])
            words = extract_meaningful_words(all_text)
            word_counts = Counter(words)
            
            # Get top 15 words
            top_words = word_counts.most_common(15)
            
            if top_words:
                words_list, counts_list = zip(*top_words)
                
                fig = go.Figure(data=[go.Bar(
                    x=list(counts_list),
                    y=list(words_list),
                    orientation='h',
                    marker_color='#3674B5',
                    text=list(counts_list),
                    textposition='outside'
                )])
                
                fig.update_layout(
                    title='',
                    xaxis_title='Frequency',
                    yaxis_title='Words',
                    height=400,
                    margin=dict(t=20, b=40, l=100, r=40),
                    yaxis={'categoryorder': 'total ascending'}
                )
                
                ui.plotly(fig).classes('w-full')
            else:
                ui.label('No meaningful words found').classes('text-body2 text-grey-6 text-center p-4')
    
    def _create_word_cloud(self):
        """Create word cloud visualization"""
        with self.word_cloud_container:
            ui.label('Word Cloud').classes('text-h6 q-mb-md')
            
            if not WORDCLOUD_AVAILABLE:
                ui.label('WordCloud library not available. Install with: pip install wordcloud').classes('text-body2 text-orange text-center p-4')
                return
            
            if not self.app_state.paragraphs:
                ui.label('No transcript data available').classes('text-body2 text-grey-6 text-center p-4')
                return
            
            try:
                # Extract meaningful words
                all_text = ' '.join([p.text for p in self.app_state.paragraphs])
                words = extract_meaningful_words(all_text)
                word_text = ' '.join(words)
                
                if not word_text.strip():
                    ui.label('No meaningful words found for word cloud').classes('text-body2 text-grey-6 text-center p-4')
                    return
                
                # Generate word cloud
                wordcloud = WordCloud(
                    width=600, 
                    height=300,
                    background_color='white',
                    colormap='viridis',
                    max_words=100,
                    relative_scaling=0.5,
                    random_state=42
                ).generate(word_text)
                
                # Convert to base64 for display
                img_buffer = BytesIO()
                wordcloud.to_image().save(img_buffer, format='PNG')
                img_str = base64.b64encode(img_buffer.getvalue()).decode()
                
                # Display the word cloud
                with ui.column().classes('w-full items-center'):
                    ui.html(f'<img src="data:image/png;base64,{img_str}" style="max-width: 100%; height: auto;" alt="Word Cloud">')
                
            except Exception as e:
                ui.label(f'Error generating word cloud: {str(e)}').classes('text-body2 text-red text-center p-4')
    
    def _create_enhanced_sentiment_chart(self):
        """Create enhanced sentiment distribution visualization"""
        with self.sentiment_container:
            ui.label('Sentiment Analysis Overview').classes('text-h6 q-mb-md')
            
            # Get sentiment distribution
            distribution = self.app_state.get_sentiment_distribution()
            
            if sum(distribution.values()) > 0:
                # Create donut chart with better styling
                fig = go.Figure(data=[go.Pie(
                    labels=[label.title() for label in distribution.keys()],
                    values=list(distribution.values()),
                    hole=0.4,
                    marker_colors=[SENTIMENT_COLORS[k] for k in distribution.keys()],
                    textinfo='label+percent+value',
                    textposition='auto',
                    hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
                )])
                
                fig.update_layout(
                    title='',
                    showlegend=True,
                    height=350,
                    margin=dict(t=0, b=0, l=0, r=0),
                    annotations=[dict(text='Sentiment<br>Distribution', x=0.5, y=0.5, font_size=14, showarrow=False)]
                )
                
                ui.plotly(fig).classes('w-full')
                
                # Add sentiment statistics
                total = sum(distribution.values())
                with ui.row().classes('w-full gap-2 q-mt-sm'):
                    for sentiment, count in distribution.items():
                        if count > 0:
                            percentage = (count / total * 100) if total > 0 else 0
                            color = SENTIMENT_COLORS[sentiment]
                            with ui.card().classes('flex-1 text-center p-2').style(f'border-left: 4px solid {color}'):
                                ui.label(sentiment.title()).classes('text-caption font-bold')
                                ui.label(f'{count} ({percentage:.1f}%)').classes('text-body2')
            else:
                ui.label('No sentiment data available').classes('text-body2 text-grey-6 text-center p-4')
    
    def _create_enhanced_encoding_overview(self):
        """Create enhanced encoding overview with detailed breakdown"""
        with self.encoding_container:
            ui.label('Encoding Overview').classes('text-h6 q-mb-md')
            
            # Get coding distribution
            distribution = self.app_state.get_coding_distribution()
            
            if distribution:
                # Create horizontal bar chart for better readability
                codes = list(distribution.keys())
                counts = list(distribution.values())
                
                fig = go.Figure(data=[go.Bar(
                    x=counts,
                    y=codes,
                    orientation='h',
                    marker_color='#A1E3F9',
                    text=counts,
                    textposition='outside',
                    hovertemplate='<b>%{y}</b><br>Paragraphs: %{x}<extra></extra>'
                )])
                
                fig.update_layout(
                    title='',
                    xaxis_title='Number of Paragraphs',
                    yaxis_title='Coding Categories',
                    height=max(300, len(codes) * 25 + 100),
                    margin=dict(t=20, b=40, l=150, r=40),
                    yaxis={'categoryorder': 'total ascending'}
                )
                
                ui.plotly(fig).classes('w-full')
                
                # Add encoding statistics
                total_coded = sum(distribution.values())
                total_paragraphs = len(self.app_state.paragraphs)
                coding_coverage = (total_coded / total_paragraphs * 100) if total_paragraphs > 0 else 0
                
                with ui.row().classes('w-full gap-4 q-mt-sm'):
                    with ui.card().classes('flex-1 text-center p-2'):
                        ui.label('Total Codes Applied').classes('text-caption text-grey-6')
                        ui.label(str(total_coded)).classes('text-h6 text-primary')
                    
                    with ui.card().classes('flex-1 text-center p-2'):
                        ui.label('Coding Coverage').classes('text-caption text-grey-6')
                        ui.label(f'{coding_coverage:.1f}%').classes('text-h6 text-secondary')
                    
                    with ui.card().classes('flex-1 text-center p-2'):
                        ui.label('Unique Categories').classes('text-caption text-grey-6')
                        ui.label(str(len(distribution))).classes('text-h6 text-accent')
            else:
                ui.label('No coding data available').classes('text-body2 text-grey-6 text-center p-4')
                
                # Show available coding schemes
                if self.app_state.coding_schemes:
                    ui.label(f'Available coding schemes: {len(self.app_state.coding_schemes)}').classes('text-body2 text-grey-5 text-center')
                    with ui.column().classes('w-full gap-1 q-mt-sm'):
                        for scheme in self.app_state.coding_schemes[:5]:  # Show first 5
                            ui.label(f'• {scheme.title}').classes('text-caption text-grey-5 text-center')
    
    def _create_export_section(self):
        """Create export functionality section"""
        with ui.column().classes('w-full gap-2'):
            ui.label('Export Options').classes('text-h6')
            
            with ui.row().classes('w-full gap-2'):
                ui.button(
                    'Export Report as JSON',
                    on_click=self._export_json,
                    icon='download'
                ).classes(get_button_class('primary'))
                
                ui.button(
                    'Export Charts as Images',
                    on_click=self._export_charts,
                    icon='image'
                ).classes(get_button_class('secondary')).props('outline')
                
                ui.button(
                    'Generate PDF Report',
                    on_click=self._export_pdf,
                    icon='picture_as_pdf'
                ).classes(get_button_class('accent')).props('outline')
    
    def _export_json(self):
        """Export analysis results as JSON"""
        try:
            file_path = self.export_service.export_json()
            ui.notify(f'JSON report exported successfully to: {file_path}', type='positive')
            
        except Exception as e:
            ui.notify(f'Error exporting JSON: {str(e)}', type='negative')
    
    def _export_charts(self):
        """Export charts as images"""
        try:
            exported_files = self.export_service.export_charts_as_images()
            
            if exported_files:
                ui.notify(f'Charts exported successfully! {len(exported_files)} files saved to Downloads folder', type='positive')
                
                # Show list of exported files in a dialog
                with ui.dialog() as dialog, ui.card():
                    ui.label('Exported Chart Files').classes('text-h6 q-mb-md')
                    
                    with ui.column().classes('gap-2'):
                        for file_path in exported_files:
                            file_name = file_path.split('\\')[-1] if '\\' in file_path else file_path.split('/')[-1]
                            ui.label(f'✓ {file_name}').classes('text-body2')
                    
                    with ui.row().classes('w-full justify-end q-mt-md'):
                        ui.button('Close', on_click=dialog.close).classes(get_button_class('primary'))
                
                dialog.open()
            else:
                ui.notify('No charts available to export', type='warning')
                
        except Exception as e:
            ui.notify(f'Error exporting charts: {str(e)}', type='negative')
    
    def _export_pdf(self):
        """Generate PDF report"""
        try:
            file_path = self.export_service.generate_pdf_report()
            ui.notify(f'PDF report generated successfully: {file_path}', type='positive')
            
        except Exception as e:
            ui.notify(f'Error generating PDF: {str(e)}', type='negative')
    
    def refresh(self):
        """Refresh the report section when it becomes active"""
        # This method can be called when the user navigates to the report section
        # to ensure all visualizations are up to date
        if hasattr(self, 'word_freq_container'):
            self.word_freq_container.clear()
            self._create_word_frequency_chart()
        
        if hasattr(self, 'word_cloud_container'):
            self.word_cloud_container.clear()
            self._create_word_cloud()
        
        if hasattr(self, 'sentiment_container'):
            self.sentiment_container.clear()
            self._create_enhanced_sentiment_chart()
        
        if hasattr(self, 'encoding_container'):
            self.encoding_container.clear()
            self._create_enhanced_encoding_overview()
