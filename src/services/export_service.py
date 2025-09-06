"""
Export service for generating reports in various formats
"""

import json
import os
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import Counter
import tempfile

from fpdf import FPDF
from nicegui import ui
from ..utils.text_processing import extract_meaningful_words

# Matplotlib for PNG export without browser dependency (so we avoided kaleido)
import matplotlib
matplotlib.use('Agg')  # non-GUI backend 
import matplotlib.pyplot as plt

try:
    from wordcloud import WordCloud
    WORDCLOUD_AVAILABLE = True
except ImportError:
    WORDCLOUD_AVAILABLE = False


class ExportService:
    """Service for exporting analysis results in various formats"""
    
    def __init__(self, app_state):
        self.app_state = app_state
        self._pdf_font_family = 'Arial'
        
    def export_json(self, filename: Optional[str] = None) -> str:
        """Export comprehensive analysis results as JSON"""
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"Psymerique_analysis_{timestamp}.json"
            
            # Extract meaningful words for analysis
            all_text = ' '.join([p.text for p in self.app_state.paragraphs])
            words = extract_meaningful_words(all_text)
            word_counts = Counter(words)
            
            # Create comprehensive report data
            report_data = {
                'metadata': {
                    'export_timestamp': datetime.now().isoformat(),
                    'application': 'Psymerique - Therapeutic Transcript Analysis',
                    'version': '1.0.0'
                },
                'summary': {
                    'total_paragraphs': len(self.app_state.paragraphs),
                    'coded_paragraphs': len([p for p in self.app_state.paragraphs if p.codes]),
                    'coding_schemes': len(self.app_state.coding_schemes),
                    'unique_words': len(word_counts),
                    'total_words': sum(word_counts.values())
                },
                'analysis_results': {
                    'word_frequency': dict(word_counts.most_common(100)),
                    'sentiment_distribution': self.app_state.get_sentiment_distribution(),
                    'coding_distribution': self.app_state.get_coding_distribution(),
                    'speaker_distribution': {
                        'client': len(self.app_state.get_paragraphs_by_speaker('client')),
                        'therapist': len(self.app_state.get_paragraphs_by_speaker('therapist')),
                        'unknown': len(self.app_state.get_paragraphs_by_speaker('unknown'))
                    }
                },
                'transcript_data': {
                    'paragraphs': [
                        {
                            'id': p.id,
                            'text': p.text,
                            'speaker': p.speaker,
                            'sentiment': p.sentiment,
                            'sentiment_confidence': getattr(p, 'sentiment_confidence', None),
                            'codes': p.codes,
                            'order': idx
                        } for idx, p in enumerate(self.app_state.paragraphs)
                    ]
                },
                'configuration': {
                    'coding_schemes': [
                        {
                            'id': s.id,
                            'title': s.title,
                            'keywords': s.keywords,
                            'description': getattr(s, 'description', '')
                        } for s in self.app_state.coding_schemes
                    ]
                }
            }
            
            # Create downloads directory if it doesn't exist
            downloads_dir = Path.home() / "Downloads"
            downloads_dir.mkdir(exist_ok=True)
            
            # Save JSON file
            file_path = downloads_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            return str(file_path)
            
        except Exception as e:
            raise Exception(f"Error exporting JSON: {str(e)}")
    
    def export_charts_as_images(self, filename_prefix: Optional[str] = None) -> List[str]:
        """Export all charts as PNG images using matplotlib"""
        try:
            if not filename_prefix:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename_prefix = f"Psymerique_charts_{timestamp}"
            
            downloads_dir = Path.home() / "Downloads"
            downloads_dir.mkdir(exist_ok=True)
            exported_files: List[str] = []
            
            # Prepare data once
            wf_data = self._get_word_frequency_data(top_n=15)
            sd_data = self.app_state.get_sentiment_distribution()
            enc_data = self.app_state.get_coding_distribution()
            spk_data = {
                'Client': len(self.app_state.get_paragraphs_by_speaker('client')),
                'Therapist': len(self.app_state.get_paragraphs_by_speaker('therapist')),
                'Unknown': len(self.app_state.get_paragraphs_by_speaker('unknown')),
            }
            spk_data = {k: v for k, v in spk_data.items() if v > 0}
            
            # 1) Word Frequency Chart
            if wf_data:
                path = downloads_dir / f"{filename_prefix}_word_frequency.png"
                labels = [w for w, c in wf_data]
                values = [c for w, c in wf_data]
                plt.figure(figsize=(10, 6), dpi=150)
                plt.barh(labels, values, color="#3674B5")
                for i, v in enumerate(values):
                    plt.text(v + max(values)*0.01 if values else 0.1, i, str(v), va='center', fontsize=9)
                plt.xlabel('Frequency')
                plt.ylabel('Words')
                plt.title('Top Word Frequency')
                plt.tight_layout()
                plt.savefig(path, bbox_inches='tight')
                plt.close()
                exported_files.append(str(path))
            
            # 2) Word Cloud
            if WORDCLOUD_AVAILABLE:
                wc_path = self._create_wordcloud_image(downloads_dir, filename_prefix)
                if wc_path:
                    exported_files.append(wc_path)
            
            # 3) Sentiment Distribution
            if sum(sd_data.values()) > 0:
                path = downloads_dir / f"{filename_prefix}_sentiment_distribution.png"
                labels = [k.title() for k, v in sd_data.items() if v > 0]
                sizes = [v for v in sd_data.values() if v > 0]
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA726']
                plt.figure(figsize=(8, 8), dpi=150)
                plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors[:len(sizes)])
                plt.title('Sentiment Distribution')
                plt.tight_layout()
                plt.savefig(path, bbox_inches='tight')
                plt.close()
                exported_files.append(str(path))
            
            # 4) Encoding Overview
            if enc_data:
                path = downloads_dir / f"{filename_prefix}_encoding_overview.png"
                labels = list(enc_data.keys())
                values = list(enc_data.values())
                plt.figure(figsize=(10, max(6, 0.4*len(labels))), dpi=150)
                plt.barh(labels, values, color="#A1E3F9")
                for i, v in enumerate(values):
                    plt.text(v + (max(values)*0.01 if values else 0.1), i, str(v), va='center', fontsize=9)
                plt.xlabel('Number of Paragraphs')
                plt.ylabel('Coding Categories')
                plt.title('Encoding Overview')
                plt.tight_layout()
                plt.savefig(path, bbox_inches='tight')
                plt.close()
                exported_files.append(str(path))
            
            
            return exported_files
        except Exception as e:
            raise Exception(f"Error exporting charts: {str(e)}")
    
    def generate_pdf_report(self, filename: Optional[str] = None) -> str:
        """Generate comprehensive PDF report with embedded charts"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"Psymerique_report_{timestamp}.pdf"
            downloads_dir = Path.home() / "Downloads"
            downloads_dir.mkdir(exist_ok=True)
            file_path = downloads_dir / filename
            
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            self._add_pdf_header(pdf)
            self._add_executive_summary(pdf)
            self._add_analysis_results(pdf)
            
            # Generate chart PNGs and embed them
            tmp_dir = Path(tempfile.mkdtemp(prefix="Psymerique_pdf_"))
            chart_files: List[Path] = []
            
            # Word Frequency Chart
            wf = self._get_word_frequency_data(top_n=15)
            if wf:
                p = tmp_dir / "word_frequency.png"
                labels = [w for w, c in wf]
                values = [c for w, c in wf]
                plt.figure(figsize=(8, 6), dpi=150)
                plt.barh(labels, values, color="#3674B5")
                for i, v in enumerate(values):
                    plt.text(v + (max(values)*0.01 if values else 0.1), i, str(v), va='center', fontsize=8)
                plt.xlabel('Frequency')
                plt.ylabel('Words')
                plt.title('Top Word Frequency')
                plt.tight_layout()
                plt.savefig(p, bbox_inches='tight')
                plt.close()
                chart_files.append(p)
            
            # Word Cloud
            if WORDCLOUD_AVAILABLE:
                all_text = ' '.join([p.text for p in self.app_state.paragraphs])
                words = extract_meaningful_words(all_text)
                word_text = ' '.join(words)
                if word_text.strip():
                    p = tmp_dir / "wordcloud.png"
                    wordcloud = WordCloud(
                        width=800, 
                        height=400,
                        background_color='white',
                        colormap='viridis',
                        max_words=100,
                        relative_scaling=0.5,
                        random_state=42
                    ).generate(word_text)
                    wordcloud.to_file(str(p))
                    chart_files.append(p)
            
            # Sentiment Distribution
            sd = self.app_state.get_sentiment_distribution()
            if sum(sd.values()) > 0:
                p = tmp_dir / "sentiment_distribution.png"
                labels = [k.title() for k, v in sd.items() if v > 0]
                sizes = [v for v in sd.values() if v > 0]
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA726']
                plt.figure(figsize=(8, 6), dpi=150)
                plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors[:len(sizes)])
                plt.title('Sentiment Distribution')
                plt.tight_layout()
                plt.savefig(p, bbox_inches='tight')
                plt.close()
                chart_files.append(p)
            
            # Encoding Overview
            enc = self.app_state.get_coding_distribution()
            if enc:
                p = tmp_dir / "encoding_overview.png"
                labels = list(enc.keys())
                values = list(enc.values())
                plt.figure(figsize=(8, max(6, 0.4*len(labels))), dpi=150)
                plt.barh(labels, values, color="#A1E3F9")
                for i, v in enumerate(values):
                    plt.text(v + (max(values)*0.01 if values else 0.1), i, str(v), va='center', fontsize=8)
                plt.xlabel('Number of Paragraphs')
                plt.ylabel('Coding Categories')
                plt.title('Encoding Overview')
                plt.tight_layout()
                plt.savefig(p, bbox_inches='tight')
                plt.close()
                chart_files.append(p)
            
            # Embed images in PDF - each chart on its own page
            for img in chart_files:
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 8, img.stem.replace('_', ' ').title(), 0, 1, 'L')
                pdf.ln(5)
                # Calculate image dimensions to fit page
                page_w = pdf.w - 20
                max_h = pdf.h - 60  # Leave space for title and margins
                pdf.image(str(img), x=10, y=pdf.get_y(), w=page_w, h=min(max_h, page_w * 0.6))
            
            # Add transcript sample on new page
            pdf.add_page()
            self._add_transcript_sample(pdf)
            self._add_pdf_footer(pdf)
            pdf.output(str(file_path))
            return str(file_path)
        except Exception as e:
            raise Exception(f"Error generating PDF: {str(e)}")
    
    def _get_word_frequency_data(self, top_n: int = 15):
        """Helper to compute top-N word frequency list [(word, count), ...]"""
        if not self.app_state.paragraphs:
            return []
        all_text = ' '.join([p.text for p in self.app_state.paragraphs])
        words = extract_meaningful_words(all_text)
        word_counts = Counter(words)
        return word_counts.most_common(top_n)
    
    def _create_wordcloud_image(self, downloads_dir: Path, filename_prefix: str) -> Optional[str]:
        """Create and save word cloud image"""
        if not self.app_state.paragraphs:
            return None
        
        all_text = ' '.join([p.text for p in self.app_state.paragraphs])
        words = extract_meaningful_words(all_text)
        word_text = ' '.join(words)
        
        if not word_text.strip():
            return None
        
        wordcloud = WordCloud(
            width=800, 
            height=400,
            background_color='white',
            colormap='viridis',
            max_words=100,
            relative_scaling=0.5,
            random_state=42
        ).generate(word_text)
        
        wordcloud_path = downloads_dir / f"{filename_prefix}_wordcloud.png"
        wordcloud.to_file(str(wordcloud_path))
        
        return str(wordcloud_path)
    
    def _add_pdf_header(self, pdf: FPDF):
        """Add header with logo and title to PDF"""
        # Add logo if available
        logo_path = Path(__file__).parent.parent / "assets" / "images" / "logo.png"
        if logo_path.exists():
            # Add logo on the left side
            pdf.image(str(logo_path), x=10, y=10, w=30)
            # Adjust title position to account for logo
            title_y = 15
        else:
            title_y = 10
        
        # Title
        pdf.set_font(self._pdf_font_family, 'B', 24)
        pdf.set_text_color(54, 116, 181)  # Blue color
        pdf.cell(0, 15, self._sanitize_text('Psymerique Analysis Report'), 0, 1, 'C')
        
        # Subtitle
        pdf.set_font(self._pdf_font_family, '', 12)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 10, self._sanitize_text('Therapeutic Transcript Analysis'), 0, 1, 'C')
        
        # Date
        pdf.set_font(self._pdf_font_family, '', 10)
        pdf.cell(0, 10, self._sanitize_text(f'Generated on: {datetime.now().strftime("%B %d, %Y at %H:%M")}'), 0, 1, 'C')
        
        pdf.ln(10)
    
    def _add_executive_summary(self, pdf: FPDF):
        """Add executive summary to PDF"""
        pdf.set_font(self._pdf_font_family, 'B', 16)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, self._sanitize_text('Executive Summary'), 0, 1, 'L')
        pdf.ln(5)
        
        # Summary statistics
        total_paragraphs = len(self.app_state.paragraphs)
        client_paragraphs = len(self.app_state.get_paragraphs_by_speaker('client'))
        therapist_paragraphs = len(self.app_state.get_paragraphs_by_speaker('therapist'))
        coded_paragraphs = len([p for p in self.app_state.paragraphs if p.codes])
        
        pdf.set_font(self._pdf_font_family, '', 11)
        
        summary_text = f"""
This report presents a comprehensive analysis of a therapeutic transcript containing {total_paragraphs} paragraphs.

Key Statistics:
- Total Paragraphs: {total_paragraphs}
- Client Contributions: {client_paragraphs} paragraphs ({client_paragraphs/total_paragraphs*100:.1f}%)
- Therapist Contributions: {therapist_paragraphs} paragraphs ({therapist_paragraphs/total_paragraphs*100:.1f}%)
- Coded Paragraphs: {coded_paragraphs} paragraphs ({coded_paragraphs/total_paragraphs*100:.1f}% coverage)
- Coding Schemes Available: {len(self.app_state.coding_schemes)}

The analysis includes word frequency analysis, sentiment distribution, speaker identification, 
and thematic coding to provide insights into the therapeutic conversation dynamics.
        """.strip()
        
        # Split text into lines and add to PDF
        for line in summary_text.split('\n'):
            if line.strip():
                pdf.cell(0, 6, self._sanitize_text(line.strip()), 0, 1, 'L')
            else:
                pdf.ln(3)
        
        pdf.ln(10)
    
    def _add_analysis_results(self, pdf: FPDF):
        """Add analysis results section to PDF"""
        pdf.set_font(self._pdf_font_family, 'B', 16)
        pdf.cell(0, 10, self._sanitize_text('Analysis Results'), 0, 1, 'L')
        pdf.ln(5)
        
        # Word Frequency Analysis
        pdf.set_font(self._pdf_font_family, 'B', 12)
        pdf.cell(0, 8, self._sanitize_text('Word Frequency Analysis'), 0, 1, 'L')
        pdf.set_font(self._pdf_font_family, '', 10)
        
        all_text = ' '.join([p.text for p in self.app_state.paragraphs])
        words = extract_meaningful_words(all_text)
        word_counts = Counter(words)
        top_words = word_counts.most_common(10)
        
        if top_words:
            pdf.cell(0, 6, self._sanitize_text('Top 10 Most Frequent Words:'), 0, 1, 'L')
            for i, (word, count) in enumerate(top_words, 1):
                pdf.cell(0, 5, self._sanitize_text(f'{i}. {word}: {count} occurrences'), 0, 1, 'L')
        
        pdf.ln(5)
        
        # Sentiment Analysis
        pdf.set_font(self._pdf_font_family, 'B', 12)
        pdf.cell(0, 8, self._sanitize_text('Sentiment Analysis'), 0, 1, 'L')
        pdf.set_font(self._pdf_font_family, '', 10)
        
        sentiment_dist = self.app_state.get_sentiment_distribution()
        total_sentiment = sum(sentiment_dist.values())
        
        if total_sentiment > 0:
            for sentiment, count in sentiment_dist.items():
                if count > 0:
                    percentage = (count / total_sentiment) * 100
                    pdf.cell(0, 5, self._sanitize_text(f'{sentiment.title()}: {count} paragraphs ({percentage:.1f}%)'), 0, 1, 'L')
        
        pdf.ln(5)
        
        # Coding Analysis
        pdf.set_font(self._pdf_font_family, 'B', 12)
        pdf.cell(0, 8, self._sanitize_text('Thematic Coding'), 0, 1, 'L')
        pdf.set_font(self._pdf_font_family, '', 10)
        
        coding_dist = self.app_state.get_coding_distribution()
        if coding_dist:
            pdf.cell(0, 6, self._sanitize_text('Coding Distribution:'), 0, 1, 'L')
            for code, count in list(coding_dist.items())[:10]:  # Top 10 codes
                pdf.cell(0, 5, self._sanitize_text(f'- {code}: {count} paragraphs'), 0, 1, 'L')
        else:
            pdf.cell(0, 6, self._sanitize_text('No thematic coding applied to the transcript.'), 0, 1, 'L')
        
        pdf.ln(10)
    
    def _add_transcript_sample(self, pdf: FPDF):
        """Add sample transcript data to PDF"""
        pdf.set_font(self._pdf_font_family, 'B', 16)
        pdf.cell(0, 10, self._sanitize_text('Transcript'), 0, 1, 'L')
        pdf.ln(5)
        
        pdf.set_font(self._pdf_font_family, '', 10)
        pdf.cell(0, 6, self._sanitize_text('Analyzed transcript:'), 0, 1, 'L')
        pdf.ln(3)
        
        # Show first 5 paragraphs as sample
        sample_paragraphs = self.app_state.paragraphs[:5]
        
        for i, paragraph in enumerate(sample_paragraphs, 1):
            # Check if we need a new page
            if pdf.get_y() > 250:
                pdf.add_page()
            
            pdf.set_font(self._pdf_font_family, 'B', 9)
            speaker_label = f"[{paragraph.speaker.upper()}]" if paragraph.speaker else "[UNKNOWN]"
            pdf.cell(0, 5, self._sanitize_text(f'{i}. {speaker_label}'), 0, 1, 'L')
            
            pdf.set_font(self._pdf_font_family, '', 9)
            # Truncate long paragraphs
            raw_text = paragraph.text[:200] + "..." if len(paragraph.text) > 200 else paragraph.text
            
            # Split text into multiple lines if needed
            words = raw_text.split()
            current_line = ""
            for word in words:
                if len(current_line + " " + word) < 80:
                    current_line += " " + word if current_line else word
                else:
                    if current_line:
                        pdf.cell(0, 4, self._sanitize_text(current_line), 0, 1, 'L')
                    current_line = word
            
            if current_line:
                pdf.cell(0, 4, self._sanitize_text(current_line), 0, 1, 'L')
            
            pdf.ln(2)
        
        if len(self.app_state.paragraphs) > 5:
            pdf.set_font(self._pdf_font_family, 'I', 9)
            pdf.cell(0, 5, self._sanitize_text(f'... and {len(self.app_state.paragraphs) - 5} more paragraphs'), 0, 1, 'L')
    
    def _add_pdf_footer(self, pdf: FPDF):
        """Add footer to PDF"""
        pdf.ln(10)
        pdf.set_font(self._pdf_font_family, 'I', 8)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 5, self._sanitize_text('Generated by Psymerique - Therapeutic Transcript Analysis Tool'), 0, 1, 'C')
        pdf.cell(0, 5, self._sanitize_text('For research and clinical analysis purposes'), 0, 1, 'C')
    
    def _sanitize_text(self, text: str) -> str:
        """Replace or strip characters not supported by core fonts (Arial/Helvetica).
        
        Performs best-effort ASCII fallbacks for common punctuation and removes
        unsupported characters to avoid FPDF range errors.
        """
        if text is None:
            return ''
        # Normalize newlines
        text = text.replace('\r', ' ').replace('\n', ' ')
        # Common Unicode to ASCII replacements
        replacements = {
            '\u2013': '-',   # en dash
            '\u2014': '-',   # em dash
            '\u2026': '...', # ellipsis
            '\u2018': "'",   # left single quote
            '\u2019': "'",   # right single quote
            '\u201C': '"',   # left double quote
            '\u201D': '"',   # right double quote
            '\u00A0': ' ',   # non-breaking space
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        # Remove/replace any remaining unsupported characters
        try:
            text = text.encode('latin-1', 'ignore').decode('latin-1')
        except Exception:
            # As a last resort, strip non-ASCII
            text = ''.join(ch for ch in text if ord(ch) < 128)
        return text
