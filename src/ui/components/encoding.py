"""
Encoding section - Custom coding schemes and paragraph categorization
"""

from nicegui import ui, events
from ..theme import get_button_class
from ...app_state import CodingScheme
import csv
import io
import uuid


class EncodingSection:
    """Encoding section for custom coding schemes and categorization"""
    
    def __init__(self, app_state):
        self.app_state = app_state
        self.scheme_table = None
        self.paragraph_container = None
        self.coding_tree_container = None
        
    def create(self):
        """Create the encoding section UI"""
        with ui.column().classes('w-full gap-4'):
            self._create_header()
            self._create_coding_scheme_section()
            self._create_paragraph_coding_section()
            self._create_coding_storage_section()
            
            # Refresh displays when section is created/shown
            self.refresh()
    
    def _create_header(self):
        """Create section header"""
        with ui.column().classes('w-full gap-2'):
            ui.label('Text Encoding & Categorization').classes('text-h5')
            ui.label(
                'Create coding schemes and categorize paragraphs according to your analysis framework'
            ).classes('text-body2 text-grey-6')
    
    def _create_coding_scheme_section(self):
        """Create coding scheme management section"""
        with ui.column().classes('w-full gap-2'):
            ui.label('Coding Scheme').classes('text-h6')
            
            # Manual entry and CSV upload
            with ui.row().classes('w-full gap-2'):
                ui.button(
                    'Add New Code',
                    on_click=self._show_add_code_dialog,
                    icon='add'
                ).classes(get_button_class('primary'))
                
                ui.upload(
                    on_upload=self._handle_csv_upload,
                    label='Upload CSV Scheme'
                ).props('accept=".csv"').classes(get_button_class('secondary'))
            
            # Coding scheme table
            self.scheme_table = ui.table(
                columns=[
                    {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
                    {'name': 'title', 'label': 'Title', 'field': 'title', 'align': 'left'},
                    {'name': 'keywords', 'label': 'Keywords', 'field': 'keywords', 'align': 'left'},
                    {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'},
                ],
                rows=[],
                row_key='id'
            ).classes('coding-table w-full')
            
            self._update_scheme_table()
    
    def _create_paragraph_coding_section(self):
        """Create paragraph coding section"""
        with ui.column().classes('w-full gap-2'):
            ui.label('Paragraph Coding').classes('text-h6')
            ui.label(
                'Click on paragraphs to assign codes from your coding scheme'
            ).classes('text-body2 text-grey-6')
            
            # Container for paragraphs
            self.paragraph_container = ui.column().classes('w-full gap-2')
    
    def _create_coding_storage_section(self):
        """Create coding storage tree view"""
        with ui.column().classes('w-full gap-2'):
            ui.label('Coding Storage').classes('text-h6')
            ui.label(
                'Hierarchical view of coded paragraphs organized by coding scheme'
            ).classes('text-body2 text-grey-6')
            
            # Container for coding tree display
            self.coding_tree_container = ui.column().classes('w-full')
            
            self._update_coding_tree()
    
    def _show_add_code_dialog(self):
        """Show dialog to add new coding scheme"""
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label('Add New Coding Scheme').classes('text-h6 q-mb-md')
            
            # Form inputs
            id_input = ui.input('Code ID', placeholder='e.g., EMOT_POS').classes('w-full')
            title_input = ui.input('Title', placeholder='e.g., Positive Emotion').classes('w-full')
            keywords_input = ui.textarea(
                'Keywords (one per line)', 
                placeholder='happy\\njoyful\\noptimistic'
            ).classes('w-full').props('rows=4')
            
            with ui.row().classes('w-full justify-end gap-2 q-mt-md'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button(
                    'Add Code',
                    on_click=lambda: self._add_coding_scheme(
                        id_input.value, title_input.value, keywords_input.value, dialog
                    )
                ).classes(get_button_class('primary'))
        
        dialog.open()
    
    def _add_coding_scheme(self, code_id, title, keywords_text, dialog):
        """Add new coding scheme"""
        if not code_id or not title:
            ui.notify('Code ID and Title are required', type='warning')
            return
        
        # Check if ID already exists
        if any(scheme.id == code_id for scheme in self.app_state.coding_schemes):
            ui.notify('Code ID already exists', type='warning')
            return
        
        # Parse keywords
        keywords = [k.strip() for k in keywords_text.split('\\n') if k.strip()] if keywords_text else []
        
        # Create and add scheme
        scheme = CodingScheme(id=code_id, title=title, keywords=keywords)
        self.app_state.add_coding_scheme(scheme)
        
        # Update UI
        self._update_scheme_table()
        self._update_coding_tree()
        
        dialog.close()
        ui.notify(f'Added coding scheme: {title}', type='positive')
    
    def _handle_csv_upload(self, event: events.UploadEventArguments):
        """Handle CSV upload for coding schemes"""
        try:
            content = event.content.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(content))
            
            added_count = 0
            for row in csv_reader:
                if 'ID' in row and 'Title' in row:
                    code_id = row['ID'].strip()
                    title = row['Title'].strip()
                    keywords = [k.strip() for k in row.get('Keywords', '').split(',') if k.strip()]
                    
                    # Check if ID already exists
                    if not any(scheme.id == code_id for scheme in self.app_state.coding_schemes):
                        scheme = CodingScheme(id=code_id, title=title, keywords=keywords)
                        self.app_state.add_coding_scheme(scheme)
                        added_count += 1
            
            if added_count > 0:
                self._update_scheme_table()
                self._update_coding_tree()
                ui.notify(f'Added {added_count} coding schemes from CSV', type='positive')
            else:
                ui.notify('No valid coding schemes found in CSV', type='warning')
                
        except Exception as e:
            ui.notify(f'Error processing CSV: {str(e)}', type='negative')
    
    def _update_scheme_table(self):
        """Update the coding scheme table"""
        rows = []
        for scheme in self.app_state.coding_schemes:
            rows.append({
                'id': scheme.id,
                'title': scheme.title,
                'keywords': ', '.join(scheme.keywords[:3]) + ('...' if len(scheme.keywords) > 3 else ''),
                'actions': scheme.id
            })
        
        self.scheme_table.rows = rows
        
        # Add action buttons
        self.scheme_table.add_slot('body-cell-actions', '''
            <q-td :props="props">
                <q-btn size="sm" color="negative" icon="delete" @click="$parent.$emit('delete', props.row.id)" />
            </q-td>
        ''')
        
        # Handle delete action
        self.scheme_table.on('delete', self._delete_coding_scheme)
    
    def _delete_coding_scheme(self, event):
        """Delete a coding scheme"""
        scheme_id = event.args
        self.app_state.remove_coding_scheme(scheme_id)
        self._update_scheme_table()
        self._update_coding_tree()
        ui.notify(f'Deleted coding scheme: {scheme_id}', type='info')
    
    def _update_paragraph_display(self):
        """Update paragraph display for coding"""
        if not self.paragraph_container:
            return
            
        self.paragraph_container.clear()
        
        with self.paragraph_container:
            if not self.app_state.paragraphs:
                ui.label('No transcript loaded. Please upload a transcript in the Home section.').classes('text-body2 text-grey-6 text-center p-4')
                return
            
            for paragraph in self.app_state.paragraphs:
                with ui.card().classes('paragraph cursor-pointer').on('click', 
                    lambda p=paragraph: self._show_coding_menu(p)):
                    
                    with ui.row().classes('w-full items-center gap-2'):
                        ui.label(f'Paragraph {paragraph.id + 1}').classes('text-caption text-grey-6')
                        ui.space()
                        
                        # Show assigned codes as badges
                        for code in paragraph.codes:
                            ui.badge(code).classes('code-badge')
                    
                    ui.label(paragraph.text).classes('text-body2 q-mt-sm')
    
    def _show_coding_menu(self, paragraph):
        """Show coding menu for paragraph"""
        if not self.app_state.coding_schemes:
            ui.notify('No coding schemes available. Please add coding schemes first.', type='warning')
            return
        
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label(f'Code Paragraph {paragraph.id + 1}').classes('text-h6 q-mb-md')
            
            # Paragraph preview
            preview_text = paragraph.text[:150] + '...' if len(paragraph.text) > 150 else paragraph.text
            ui.label(preview_text).classes('text-body2 text-grey-6 q-mb-md bg-grey-1 p-2 rounded')
            
            # Current codes
            if paragraph.codes:
                ui.label('Current codes:').classes('text-body2 font-bold')
                with ui.row().classes('gap-1 q-mb-md'):
                    for code in paragraph.codes:
                        ui.badge(code).classes('code-badge')
            
            # Available codes
            ui.label('Available codes:').classes('text-body2 font-bold')
            with ui.column().classes('gap-1 max-h-64 overflow-auto'):
                for scheme in self.app_state.coding_schemes:
                    is_assigned = scheme.id in paragraph.codes
                    
                    with ui.row().classes('items-center gap-2 w-full'):
                        ui.checkbox(
                            value=is_assigned,
                            on_change=lambda e, s=scheme: self._toggle_paragraph_code(paragraph, s.id, e.value)
                        )
                        with ui.column().classes('flex-1'):
                            ui.label(f'{scheme.id}: {scheme.title}').classes('text-body2')
                            if scheme.keywords:
                                ui.label(f'Keywords: {", ".join(scheme.keywords[:3])}').classes('text-caption text-grey-6')
            
            with ui.row().classes('w-full justify-end q-mt-md'):
                ui.button('Done', on_click=dialog.close).classes(get_button_class('primary'))
        
        dialog.open()
    
    def _toggle_paragraph_code(self, paragraph, code_id, is_checked):
        """Toggle code assignment for paragraph"""
        if is_checked:
            self.app_state.add_paragraph_code(paragraph.id, code_id)
        else:
            self.app_state.remove_paragraph_code(paragraph.id, code_id)
        
        self._update_paragraph_display()
        self._update_coding_tree()
    
    def _update_coding_tree(self):
        """Update the coding storage tree"""
        if not hasattr(self, 'coding_tree_container'):
            return
            
        # Clear existing content
        self.coding_tree_container.clear()
        
        with self.coding_tree_container:
            if not self.app_state.coding_schemes:
                ui.label('No coding schemes available').classes('text-body2 text-grey-6 text-center p-4')
                return
            
            # Create expandable tree structure using cards and nested elements
            for scheme in self.app_state.coding_schemes:
                # Get paragraphs with this code
                coded_paragraphs = [p for p in self.app_state.paragraphs if scheme.id in p.codes]
                
                if coded_paragraphs:
                    with ui.expansion(f'{scheme.id}: {scheme.title} ({len(coded_paragraphs)} paragraphs)').classes('w-full'):
                        with ui.column().classes('gap-1 pl-4'):
                            for paragraph in coded_paragraphs:
                                preview = paragraph.text[:80] + '...' if len(paragraph.text) > 80 else paragraph.text
                                with ui.card().classes('p-2 bg-grey-1'):
                                    ui.label(f'Paragraph {paragraph.id + 1}').classes('text-caption text-primary font-bold')
                                    ui.label(preview).classes('text-body2')
                                    
                                    # Show other codes assigned to this paragraph
                                    other_codes = [code for code in paragraph.codes if code != scheme.id]
                                    if other_codes:
                                        with ui.row().classes('gap-1 mt-1'):
                                            ui.label('Also coded as:').classes('text-caption text-grey-6')
                                            for code in other_codes:
                                                ui.badge(code).classes('text-xs')
                else:
                    # Show scheme even if no paragraphs are coded
                    with ui.expansion(f'{scheme.id}: {scheme.title} (0 paragraphs)').classes('w-full'):
                        ui.label('No paragraphs coded with this scheme yet').classes('text-body2 text-grey-6 p-2')
            
            if not any(p.codes for p in self.app_state.paragraphs):
                ui.label('No coded paragraphs yet. Start coding paragraphs to see them organized here.').classes('text-body2 text-grey-6 text-center p-4')
    
    def refresh(self):
        """Refresh displays when section becomes active"""
        self._update_paragraph_display()
        self._update_coding_tree()
