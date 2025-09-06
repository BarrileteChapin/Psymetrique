"""
Speakers section - Speaker identification and therapist paragraph management
"""

from nicegui import ui
from ...services.therapeutic_model_service import TherapeuticModelService
from ..theme import get_button_class, get_paragraph_class


class SpeakersSection:
    """Speakers section for speaker identification and therapist management"""
    
    def __init__(self, app_state):
        self.app_state = app_state
        self.therapeutic_model = TherapeuticModelService()
        self.paragraph_container = None
        
    def create(self):
        """Create the speakers section UI"""
        with ui.column().classes('w-full gap-4'):
            self._create_header()
            self._create_analysis_controls()
            self._create_paragraph_display()

    def _create_header(self):
        """Create section header"""
        with ui.column().classes('w-full gap-2'):
            ui.label('Speaker Identification').classes('text-h5')
            ui.label(
                'Identify speakers using AI model (supports English, Spanish, Portuguese, French)'
            ).classes('text-body2 text-grey-6')

    def _create_analysis_controls(self):
        """Create analysis control buttons"""
        with ui.row().classes('w-full gap-2'):
            ui.button(
                'Identify Speakers',
                on_click=self._identify_speakers,
                icon='psychology'
            ).classes(get_button_class('primary'))
            
            ui.button(
                'Drop Therapist Paragraphs',
                on_click=self._drop_therapist_paragraphs,
                icon='person_remove'
            ).classes(get_button_class('secondary')).props('outline')

    def _create_paragraph_display(self):
        """Create paragraph display area"""
        with ui.column().classes('w-full gap-2'):
            ui.label('Transcript Paragraphs').classes('text-h6')
            ui.label(
                'Click on speaker badges to toggle between Client/Therapist/Unknown'
            ).classes('text-body2 text-grey-6')
            
            # Container for paragraphs
            self.paragraph_container = ui.column().classes('w-full gap-2')
            
            # Refresh display when created
            self.refresh()

    def _identify_speakers(self):
        """Identify speakers using the therapeutic BERT model"""
        if not self.app_state.paragraphs:
            ui.notify('No transcript available for analysis', type='warning')
            return
        
        if not self.therapeutic_model.is_available():
            ui.notify('Therapeutic model not available. Please check model files.', type='warning')
            return
        
        total_paragraphs = len(self.app_state.paragraphs)
        ui.notify(f'Starting speaker identification on {total_paragraphs} paragraphs...', type='info')
        
        try:
            # Process each paragraph with progress updates
            for i, paragraph in enumerate(self.app_state.paragraphs):
                # Show progress every 5 paragraphs or on last paragraph
                if i % 5 == 0 or i == total_paragraphs - 1:
                    progress = int((i + 1) / total_paragraphs * 100)
                    ui.notify(f'Progress: {progress}% ({i + 1}/{total_paragraphs})', type='info')
                
                # Use therapeutic model for speaker identification
                result = self.therapeutic_model.analyze_text(paragraph.text)
                paragraph.speaker = result['speaker']
                
                # Store confidence for potential future use
                if not hasattr(paragraph, 'speaker_confidence'):
                    paragraph.speaker_confidence = result['speaker_confidence']
            
            # Update UI
            self._update_paragraph_display()
            
            # Count speakers
            client_count = sum(1 for p in self.app_state.paragraphs if p.speaker == 'client')
            therapist_count = sum(1 for p in self.app_state.paragraphs if p.speaker == 'therapist')
            unknown_count = sum(1 for p in self.app_state.paragraphs if p.speaker == 'unknown')
            
            ui.notify(
                f'✅ Speaker identification complete! '
                f'Client: {client_count}, Therapist: {therapist_count}, Unknown: {unknown_count}', 
                type='positive'
            )
            
        except Exception as e:
            ui.notify(f'❌ Error during speaker identification: {str(e)}', type='negative')

    def _drop_therapist_paragraphs(self):
        """Remove therapist paragraphs from the transcript"""
        if not self.app_state.paragraphs:
            ui.notify('No transcript available', type='warning')
            return
        
        # Count therapist paragraphs before removal
        therapist_count = sum(1 for p in self.app_state.paragraphs if p.speaker == 'therapist')
        
        if therapist_count == 0:
            ui.notify('No therapist paragraphs found to remove', type='info')
            return
        
        # Filter out therapist paragraphs
        original_count = len(self.app_state.paragraphs)
        self.app_state.paragraphs = [p for p in self.app_state.paragraphs if p.speaker != 'therapist']
        
        # Reassign paragraph IDs
        for i, paragraph in enumerate(self.app_state.paragraphs):
            paragraph.id = i
        
        # Update current transcript
        remaining_texts = [p.text for p in self.app_state.paragraphs]
        self.app_state.current_transcript = '\n\n'.join(remaining_texts)
        
        # Update UI
        self._update_paragraph_display()
        
        remaining_count = len(self.app_state.paragraphs)
        ui.notify(
            f'✅ Removed {therapist_count} therapist paragraphs. '
            f'{remaining_count} paragraphs remaining.', 
            type='positive'
        )

    def _update_paragraph_display(self):
        """Update the paragraph display with speaker badges"""
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
                        
                        # Speaker badge with click handler
                        speaker_color = self._get_speaker_color(paragraph.speaker)
                        speaker_badge = ui.badge(
                            paragraph.speaker.title(),
                            color=speaker_color
                        ).classes('cursor-pointer')
                        
                        # Add click handler to toggle speaker
                        speaker_badge.on('click', lambda p=paragraph: self._toggle_speaker(p))
                        
                        # Show confidence if available
                        if hasattr(paragraph, 'speaker_confidence'):
                            confidence_pct = int(paragraph.speaker_confidence * 100)
                            ui.label(f'({confidence_pct}%)').classes('text-caption text-grey-5')
                    
                    # Paragraph text
                    ui.label(paragraph.text).classes('text-body2 q-mt-sm')

    def _get_speaker_color(self, speaker):
        """Get color for speaker badge"""
        colors = {
            'client': 'primary',
            'therapist': 'secondary', 
            'unknown': 'grey'
        }
        return colors.get(speaker, 'grey')

    def _toggle_speaker(self, paragraph):
        """Toggle speaker assignment for a paragraph"""
        speakers = ['client', 'therapist', 'unknown']
        current_index = speakers.index(paragraph.speaker) if paragraph.speaker in speakers else 2
        next_index = (current_index + 1) % len(speakers)
        paragraph.speaker = speakers[next_index]
        
        # Update display
        self._update_paragraph_display()
        
        # Safe notification - handle case where UI context is deleted
        try:
            ui.notify(f'Changed paragraph {paragraph.id + 1} speaker to {paragraph.speaker.title()}', type='info')
        except RuntimeError as e:
            if "parent element" in str(e) and "deleted" in str(e):
                # UI context was deleted during refresh, ignore the notification
                pass
            else:
                raise e

    def refresh(self):
        """Refresh displays when section becomes active"""
        if self.paragraph_container:
            self._update_paragraph_display()
