"""
Home section - File upload and transcript preview
"""

from nicegui import ui, events
from ...config import APP_CONFIG
from ..theme import get_button_class
import os


class HomeSection:
    """Home section for file upload and transcript editing"""
    
    def __init__(self, app_state):
        self.app_state = app_state
        self.upload_area = None
        self.text_area = None
        self.file_info_label = None
        
    def create(self):
        """Create the home section UI"""
        with ui.column().classes('w-full gap-4'):
            self._create_upload_section()
            self._create_text_preview()
            self._create_controls()
    
    def _create_upload_section(self):
        """Create file upload area"""
        with ui.column().classes('w-full items-center gap-4'):
            ui.label('Upload Transcript File').classes('text-h5 text-center')
            ui.label('Drag and drop a .txt file here or click to browse').classes('text-body2 text-grey-6 text-center')
            
            # File upload component
            self.upload_area = ui.upload(
                on_upload=self._handle_file_upload,
                on_rejected=self._handle_file_rejected,
                max_file_size=APP_CONFIG['max_file_size'],
                max_files=1
            ).props('accept=".txt"').classes('upload-area w-full max-w-2xl')
            
            # File info display
            self.file_info_label = ui.label('No file selected').classes('text-body2 text-grey-6')
    
    def _create_text_preview(self):
        """Create text preview and editing area"""
        with ui.column().classes('w-full gap-2'):
            ui.label('Transcript Preview').classes('text-h6')
            ui.label('You can edit the transcript below before proceeding to analysis').classes('text-body2 text-grey-6')
            
            self.text_area = ui.textarea(
                placeholder='Transcript content will appear here after file upload...',
                value=self.app_state.current_transcript
            ).classes('w-full').props('rows=15 outlined')
            
            # Bind text area changes
            self.text_area.on('input', self._on_text_change)
    
    def _create_controls(self):
        """Create control buttons"""
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button(
                'Reload Original',
                on_click=self._reload_original,
                icon='refresh'
            ).classes(get_button_class('secondary')).props('outline')
            
            ui.button(
                'Save Changes',
                on_click=self._save_changes,
                icon='save'
            ).classes(get_button_class('primary'))
    
    def _handle_file_upload(self, event: events.UploadEventArguments):
        """Handle file upload"""
        try:
            # Validate file extension
            file_name = event.name.lower()
            if not any(file_name.endswith(ext) for ext in APP_CONFIG['allowed_extensions']):
                ui.notify(
                    f"Invalid file type. Only {', '.join(APP_CONFIG['allowed_extensions'])} files are allowed.",
                    type='negative'
                )
                return
            
            # Read file content
            content = event.content.read().decode('utf-8')
            
            # Load into app state
            self.app_state.load_transcript(content, event.name)
            
            # Update UI
            self.text_area.value = content
            self.file_info_label.text = f"File: {event.name} ({len(content)} characters)"
            
            ui.notify(f"Successfully loaded {event.name}", type='positive')
            
        except Exception as e:
            ui.notify(f"Error loading file: {str(e)}", type='negative')
    
    def _handle_file_rejected(self, event):
        """Handle file rejection"""
        ui.notify("File rejected. Please check file size and format.", type='negative')
    
    def _on_text_change(self, event):
        """Handle text area changes"""
        # Update app state with current text (but don't save permanently yet)
        pass
    
    def _save_changes(self):
        """Save changes to transcript"""
        try:
            new_content = self.text_area.value or ""
            self.app_state.save_transcript_changes(new_content)
            
            # Update file info
            char_count = len(new_content)
            file_name = self.app_state.transcript_file_path or "Modified transcript"
            self.file_info_label.text = f"File: {file_name} ({char_count} characters) - Changes saved"
            
            ui.notify("Changes saved successfully", type='positive')
            
        except Exception as e:
            ui.notify(f"Error saving changes: {str(e)}", type='negative')
    
    def _reload_original(self):
        """Reload original transcript content"""
        try:
            self.app_state.reload_transcript()
            self.text_area.value = self.app_state.current_transcript
            
            # Update file info
            char_count = len(self.app_state.current_transcript)
            file_name = self.app_state.transcript_file_path or "Original transcript"
            self.file_info_label.text = f"File: {file_name} ({char_count} characters) - Original restored"
            
            ui.notify("Original transcript restored", type='info')
            
        except Exception as e:
            ui.notify(f"Error reloading original: {str(e)}", type='negative')
