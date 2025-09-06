"""
Entities section - Entity detection and anonymization
"""

from nicegui import ui
from ...services.nlp_service import NLPService
from ..theme import get_button_class, get_paragraph_class
from ...app_state import Entity
import asyncio

class EntitiesSection:
    """Entities section for entity detection and anonymization"""
    
    def __init__(self, app_state):
        self.app_state = app_state
        self.nlp_service = NLPService()
        self.paragraph_container = None
        self.entity_table = None
        self.highlighted_entity_id = None  # Track currently highlighted entity
        # Progress UI elements
        self._progress_dialog = None
        self._progress_label = None
        self._progress_bar = None
        
    def create(self):
        """Create the entities section UI"""
        with ui.column().classes('w-full gap-4'):
            self._create_header()
            self._create_paragraph_display()
            self._create_entity_section()
            self._add_entity_styles()

    def _create_header(self):
        """Create section header"""
        with ui.column().classes('w-full gap-2'):
            ui.label('Entity Detection & Anonymization').classes('text-h5')
            ui.label(
                'Detect and anonymize personal information in the transcript'
            ).classes('text-body2 text-grey-6')

    def _create_paragraph_display(self):
        """Create paragraph display area"""
        with ui.column().classes('w-full gap-2'):
            ui.label('Transcript Paragraphs').classes('text-h6')
            ui.label(
                'Paragraphs with detected entities highlighted by type'
            ).classes('text-body2 text-grey-6')
            
            # Container for paragraphs
            self.paragraph_container = ui.column().classes('w-full gap-2')
            
            # Refresh display when created
            self.refresh()

    def _create_entity_section(self):
        """Create entity detection and anonymization section"""
        with ui.column().classes('w-full gap-2'):
            ui.label('Detected Entities').classes('text-h6')
            ui.label(
                'Personal information detected in the transcript. Configure anonymization for each entity.'
            ).classes('text-body2 text-grey-6')
            
            # Entity detection and anonymization controls
            with ui.row().classes('w-full gap-2 q-mb-md'):
                ui.button(
                    'Detect Entities',
                    on_click=self._show_detection_warning,
                    icon='search'
                ).classes(get_button_class('primary'))
                
                ui.button(
                    'Apply Anonymization',
                    on_click=self._apply_anonymization,
                    icon='security'
                ).classes(get_button_class('accent'))
                
                ui.space()
                
                ui.button(
                    'Anonymize All',
                    on_click=self._anonymize_all_entities,
                    icon='visibility_off'
                ).classes(get_button_class('secondary')).props('size=sm')
                
                ui.button(
                    'Clear All',
                    on_click=self._clear_all_entities,
                    icon='clear'
                ).classes(get_button_class('secondary')).props('size=sm outline')
                
                ui.button(
                    'Add Manual Entity',
                    on_click=self._show_manual_entity_dialog,
                    icon='add'
                ).classes(get_button_class('secondary')).props('size=sm')
            
            # Entity table
            self.entity_table = ui.table(
                columns=[
                    {'name': 'text', 'label': 'Text', 'field': 'text', 'align': 'left'},
                    {'name': 'type', 'label': 'Type', 'field': 'entity_type', 'align': 'left'},
                    {'name': 'replacement', 'label': 'Replacement', 'field': 'replacement', 'align': 'left'},
                    {'name': 'anonymized', 'label': 'Anonymized', 'field': 'anonymized', 'align': 'center'},
                    {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'},
                ],
                rows=[],
                row_key='id'
            ).classes('entity-table w-full')

    async def _detect_entities(self, client):
        """Detect entities using Stanza NER with progress updates"""
        if not self.app_state.paragraphs:
            with client:
                ui.notify('No transcript available for analysis', type='warning')
            return
        
        total_paragraphs = len(self.app_state.paragraphs)
        # Open progress dialog (non-blocking overlay)
        with client:
            self._open_progress_dialog(total_paragraphs)
        
        # Briefly yield so the dialog actually appears before heavy work
        await asyncio.sleep(0)
        
        # Give the UI a chance to close dialogs/update before heavy work
        await asyncio.sleep(0)
        
        # Clear existing entities
        self.app_state.entities = []
        
        # Update UI to show empty state
        with client:
            self._update_entity_table()
            self._update_paragraph_display()
        
        try:
            # Process each paragraph with progress updates and UI refreshes
            for i, paragraph in enumerate(self.app_state.paragraphs):
                # Update progress UI every few paragraphs
                if i % 3 == 0 or i == total_paragraphs - 1:
                    with client:
                        self._update_progress(i + 1, total_paragraphs)
                
                # Use Stanza-based extraction with regex fallback (run in thread to avoid blocking UI)
                entities = await asyncio.to_thread(self.nlp_service.extract_entities, paragraph.text)
                
                # Store paragraph reference for context
                for entity in entities:
                    entity.paragraph_id = paragraph.id
                    self.app_state.entities.append(entity)
                
                # Update UI every 5 paragraphs to show progress
                if i % 5 == 0 or i == total_paragraphs - 1:
                    with client:
                        self._update_entity_table()
                        self._update_paragraph_display()
                    # Allow UI to update
                    await asyncio.sleep(0.01)
            
            # Final UI update
            with client:
                self._update_entity_table()
                self._update_paragraph_display()
            
            entity_count = len(self.app_state.entities)
            with client:
                ui.notify(f'✅ Detection complete! Found {entity_count} entities', type='positive')
            
        except Exception as e:
            with client:
                ui.notify(f'❌ Error during entity detection: {str(e)}', type='negative')
        finally:
            # Close progress dialog
            with client:
                self._close_progress_dialog()

    def _apply_anonymization(self):
        """Apply anonymization to the transcript"""
        if not self.app_state.entities:
            ui.notify('No entities detected. Run entity detection first.', type='warning')
            return
        
        anonymized_entities = [e for e in self.app_state.entities if e.anonymized]
        if not anonymized_entities:
            ui.notify('No entities marked for anonymization', type='warning')
            return
        
        try:
            total_entities = len(anonymized_entities)
            ui.notify(f'Applying anonymization to {total_entities} entities...', type='info')
            
            processed_paragraphs = 0
            for paragraph in self.app_state.paragraphs:
                # Get entities for this paragraph
                paragraph_entities = [e for e in anonymized_entities if hasattr(e, 'paragraph_id') and e.paragraph_id == paragraph.id]
                
                if paragraph_entities:
                    processed_paragraphs += 1
                    # Only show progress for every 3rd paragraph to reduce notification spam
                    if processed_paragraphs % 3 == 0:
                        ui.notify(f'Anonymizing paragraph {processed_paragraphs}...', type='info')
                    paragraph.text = self.nlp_service.anonymize_text(paragraph.text, paragraph_entities)
            
            # Update current transcript
            anonymized_paragraphs = [p.text for p in self.app_state.paragraphs]
            self.app_state.current_transcript = '\n\n'.join(anonymized_paragraphs)
            
            # Clear entities after anonymization
            self.app_state.entities = []
            
            # Update displays
            self._update_paragraph_display()
            self._update_entity_table()
            
            ui.notify(f'✅ Anonymization complete! Applied to {total_entities} entities', type='positive')
            
        except Exception as e:
            ui.notify(f'❌ Error applying anonymization: {str(e)}', type='negative')

    def _update_paragraph_display(self):
        """Update the paragraph display with entity highlighting"""
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
                    
                    # Render paragraph text with entity highlighting
                    highlighted_text = self._render_paragraph_with_entities(paragraph)
                    ui.html(highlighted_text).classes('text-body2 q-mt-sm')

    def _render_paragraph_with_entities(self, paragraph):
        """Render paragraph text with entity highlighting"""
        text = paragraph.text
        
        # Get entities for this paragraph
        paragraph_entities = [e for e in self.app_state.entities 
                            if hasattr(e, 'paragraph_id') and e.paragraph_id == paragraph.id]
        
        if not paragraph_entities:
            return text
        
        # Sort entities by start position in reverse order to avoid offset issues
        paragraph_entities.sort(key=lambda e: e.start_pos, reverse=True)
        
        # Wrap entities in highlight spans
        for i, entity in enumerate(paragraph_entities):
            entity_type_class = f"entity-{entity.entity_type.lower()}"
            selected_class = "selected" if i == self.highlighted_entity_id else ""
            
            entity_html = (
                f'<span class="entity-highlight {entity_type_class} {selected_class}" '
                f'data-entity-id="{i}" '
                f'title="{entity.entity_type}: {entity.text}">'
                f'{entity.text}'
                f'</span>'
            )
            
            text = text[:entity.start_pos] + entity_html + text[entity.end_pos:]
        
        return text

    def _add_entity_styles(self):
        """Add CSS styles for entity highlighting"""
        ui.add_head_html('''
        <style>
        .entity-highlight {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 3px;
            padding: 1px 3px;
            margin: 0 1px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .entity-highlight:hover {
            background-color: #ffeaa7;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }
        .entity-highlight.selected {
            background-color: #74b9ff;
            border-color: #0984e3;
            color: white;
            font-weight: bold;
        }
        .entity-person { background-color: #e8f4fd; border-color: #74b9ff; }
        .entity-date { background-color: #e8f5e8; border-color: #00b894; }
        .entity-time { background-color: #ffeaa7; border-color: #fdcb6e; }
        .entity-phone { background-color: #fd79a8; border-color: #e84393; color: white; }
        .entity-email { background-color: #a29bfe; border-color: #6c5ce7; color: white; }
        .entity-money { background-color: #00b894; border-color: #00a085; color: white; }
        .entity-percent { background-color: #fd79a8; border-color: #e84393; color: white; }
        </style>
        ''')

    def _update_entity_table(self):
        """Update the entity table"""
        if not self.entity_table:
            return
            
        rows = []
        for i, entity in enumerate(self.app_state.entities):
            rows.append({
                'id': i,
                'text': entity.text,
                'entity_type': entity.entity_type,
                'replacement': entity.replacement or f'[{entity.entity_type}]',
                'anonymized': '✓' if entity.anonymized else '✗',
                'actions': i
            })
        
        self.entity_table.rows = rows
        
        # Add action buttons to table
        self.entity_table.add_slot('body-cell-actions', '''
            <q-td :props="props">
                <q-btn size="sm" color="primary" icon="edit" @click="$parent.$emit('edit', props.row)" dense />
                <q-btn size="sm" color="accent" icon="visibility_off" @click="$parent.$emit('toggle', props.row)" class="q-ml-xs" dense />
                <q-btn size="sm" color="negative" icon="delete" @click="$parent.$emit('remove', props.row)" class="q-ml-xs" dense />
                <q-btn size="sm" color="info" icon="highlight" @click="$parent.$emit('highlight', props.row)" class="q-ml-xs" dense />
            </q-td>
        ''')
        
        # Remove existing event handlers to prevent duplicates
        try:
            self.entity_table._event_listeners.clear()
        except:
            pass
        
        # Add event handlers
        self.entity_table.on('edit', self._edit_entity)
        self.entity_table.on('toggle', self._toggle_entity_anonymization)
        self.entity_table.on('remove', self._remove_entity)
        self.entity_table.on('highlight', self._highlight_entity)

    def _edit_entity(self, event):
        """Edit entity replacement text"""
        entity_index = event.args['id']
        entity = self.app_state.entities[entity_index]
        
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label(f'Edit Entity: {entity.text}').classes('text-h6 q-mb-md')
            
            # Entity info
            ui.label(f'Type: {entity.entity_type}').classes('text-body2 text-grey-6')
            ui.label(f'Original: "{entity.text}"').classes('text-body2 q-mb-md')
            
            # Replacement input
            replacement_input = ui.input(
                'Replacement Text',
                value=entity.replacement or f'[{entity.entity_type}]'
            ).classes('w-full')
            
            with ui.row().classes('w-full justify-end gap-2 q-mt-md'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button(
                    'Save',
                    on_click=lambda: self._save_entity_edit(entity, replacement_input.value, dialog)
                ).classes(get_button_class('primary'))
        
        dialog.open()

    def _save_entity_edit(self, entity, replacement, dialog):
        """Save entity replacement text"""
        entity.replacement = replacement
        self._update_entity_table()
        dialog.close()
        ui.notify(f'Updated replacement for "{entity.text}"', type='positive')

    def _toggle_entity_anonymization(self, event):
        """Toggle entity anonymization status"""
        entity_index = event.args['id']
        entity = self.app_state.entities[entity_index]
        
        entity.anonymized = not entity.anonymized
        self._update_entity_table()
        
        status = 'enabled' if entity.anonymized else 'disabled'
        ui.notify(f'Anonymization {status} for "{entity.text}"', type='info')

    def _remove_entity(self, event):
        """Remove entity from list"""
        entity_index = event.args['id']
        entity = self.app_state.entities[entity_index]
        
        self.app_state.entities.pop(entity_index)
        self._update_entity_table()
        
        ui.notify(f'Removed entity "{entity.text}"', type='info')

    def _anonymize_all_entities(self):
        """Mark all entities for anonymization"""
        for entity in self.app_state.entities:
            entity.anonymized = True
            if not entity.replacement:
                entity.replacement = f'[{entity.entity_type}]'
        
        self._update_entity_table()
        ui.notify(f'Marked {len(self.app_state.entities)} entities for anonymization', type='positive')

    def _clear_all_entities(self):
        """Clear all entity anonymization"""
        for entity in self.app_state.entities:
            entity.anonymized = False
        
        self._update_entity_table()
        ui.notify('Cleared all entity anonymization', type='info')

    def _highlight_entity(self, event):
        """Highlight entity in the transcript"""
        entity_index = event.args['id']
        
        # Toggle highlight - if same entity is clicked, remove highlight
        if self.highlighted_entity_id == entity_index:
            self.highlighted_entity_id = None
        else:
            self.highlighted_entity_id = entity_index
        
        # Refresh paragraph display to show highlighting
        self._update_paragraph_display()
        
        if self.highlighted_entity_id is not None:
            entity = self.app_state.entities[entity_index]
            ui.notify(f'Highlighted "{entity.text}" in transcript', type='info')
        else:
            ui.notify('Removed highlighting', type='info')

    def refresh(self):
        """Refresh displays when section becomes active"""
        if self.paragraph_container:
            self._update_paragraph_display()
        if self.entity_table:
            self._update_entity_table()

    def _show_detection_warning(self):
        """Show warning dialog before entity detection"""
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label('Entity Detection Warning').classes('text-h6 q-mb-md')
            ui.label('Entity detection may take a few minutes to complete, depending on the size of the transcript.').classes('text-body2 text-grey-6 q-mb-md')
            ui.label('Please be patient and do not close this window until the detection is complete.').classes('text-body2 text-grey-6')
            
            # Define async click handler to preserve UI context
            async def _proceed(e):
                # capture the current client from the event to preserve UI context in background task
                client = e.client
                # Close the dialog and yield to the event loop so it actually disappears
                dialog.close()
                await asyncio.sleep(0)
                # Run detection in background while keeping the client context for UI updates
                asyncio.create_task(self._detect_entities(client))
            
            with ui.row().classes('w-full justify-end gap-2 q-mt-md'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button(
                    'Proceed',
                    on_click=_proceed,
                ).classes(get_button_class('primary'))
        
        dialog.open()

    def _show_manual_entity_dialog(self):
        """Show dialog to add manual entity"""
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label('Add Manual Entity').classes('text-h6 q-mb-md')
            ui.label('Enter text to search for in the transcript and mark as an entity').classes('text-body2 text-grey-6 q-mb-md')
            
            # Entity text input with search
            entity_text_input = ui.input(
                'Search Text',
                placeholder='Enter text to find and mark as entity'
            ).classes('w-full')
            
            # Search results container
            search_results_container = ui.column().classes('w-full q-mt-md')
            
            # Entity type select
            entity_type_select = ui.select(
                ['PERSON', 'DATE', 'TIME', 'PHONE', 'EMAIL', 'MONEY', 'PERCENT', 'ORGANIZATION', 'LOCATION'],
                value='PERSON',
                label='Entity Type'
            ).classes('w-full q-mt-md')
            
            # Replacement input
            replacement_input = ui.input(
                'Replacement Text (optional)',
                placeholder='Leave empty to use default replacement'
            ).classes('w-full q-mt-md')
            
            # Search function
            def search_text():
                search_term = entity_text_input.value.strip()
                search_results_container.clear()
                
                if not search_term:
                    return
                
                matches = []
                for i, paragraph in enumerate(self.app_state.paragraphs):
                    if search_term.lower() in paragraph.text.lower():
                        start_pos = paragraph.text.lower().find(search_term.lower())
                        context_start = max(0, start_pos - 30)
                        context_end = min(len(paragraph.text), start_pos + len(search_term) + 30)
                        context = paragraph.text[context_start:context_end]
                        matches.append({
                            'paragraph_id': i,
                            'context': context,
                            'start_pos': start_pos
                        })
                
                with search_results_container:
                    if matches:
                        ui.label(f'Found {len(matches)} matches:').classes('text-body2 font-bold')
                        for match in matches:
                            with ui.card().classes('w-full q-pa-sm q-mb-xs'):
                                ui.label(f'Paragraph {match["paragraph_id"] + 1}').classes('text-caption text-grey-6')
                                ui.label(f'...{match["context"]}...').classes('text-body2')
                                ui.button(
                                    'Select This Match',
                                    on_click=lambda m=match: self._create_entity_from_match(
                                        search_term, entity_type_select.value, replacement_input.value, m, dialog
                                    )
                                ).classes('q-mt-xs').props('size=sm color=primary')
                    else:
                        ui.label('No matches found').classes('text-body2 text-grey-6')
            
            # Auto-search on text change
            entity_text_input.on('input', search_text)
            
            with ui.row().classes('w-full justify-end gap-2 q-mt-md'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button(
                    'Add Entity Manually',
                    on_click=lambda: self._add_entity_without_search(
                        entity_text_input.value,
                        entity_type_select.value,
                        replacement_input.value,
                        dialog
                    )
                ).classes(get_button_class('primary'))
        
        dialog.open()

    def _add_entity_without_search(self, entity_text, entity_type, replacement, dialog):
        """Add entity manually and automatically find it in paragraphs for highlighting"""
        if not entity_text or not entity_text.strip():
            ui.notify('Entity text cannot be empty', type='warning')
            return
        
        entity_text_clean = entity_text.strip()
        
        # Check for duplicate entities
        existing_entity = next(
            (e for e in self.app_state.entities if e.text.lower() == entity_text_clean.lower()),
            None
        )
        
        if existing_entity:
            ui.notify(f'Entity "{entity_text_clean}" already exists', type='warning')
            return
        
        # Find all occurrences of the text in paragraphs
        entities_created = 0
        for i, paragraph in enumerate(self.app_state.paragraphs):
            # Search for all occurrences in this paragraph
            text_lower = paragraph.text.lower()
            search_term_lower = entity_text_clean.lower()
            start_pos = 0
            
            while True:
                pos = text_lower.find(search_term_lower, start_pos)
                if pos == -1:
                    break
                
                # Get the actual text with original casing
                actual_text = paragraph.text[pos:pos + len(entity_text_clean)]
                end_pos = pos + len(actual_text)
                
                # Check if this specific occurrence already exists
                existing_occurrence = next(
                    (e for e in self.app_state.entities 
                     if hasattr(e, 'paragraph_id') 
                     and e.paragraph_id == i 
                     and e.start_pos == pos),
                    None
                )
                
                if not existing_occurrence:
                    # Create new entity for this occurrence
                    entity = Entity(
                        text=actual_text,
                        entity_type=entity_type,
                        start_pos=pos,
                        end_pos=end_pos,
                        anonymized=False,
                        replacement=replacement.strip() if replacement else f'[{entity_type}]'
                    )
                    entity.auto_detected = False  # Mark as manual entity
                    entity.paragraph_id = i
                    
                    self.app_state.entities.append(entity)
                    entities_created += 1
                
                # Move to next potential occurrence
                start_pos = pos + 1
        
        if entities_created == 0:
            # If not found in any paragraph, create a general entity
            entity = Entity(
                text=entity_text_clean,
                entity_type=entity_type,
                start_pos=0,
                end_pos=len(entity_text_clean),
                anonymized=False,
                replacement=replacement.strip() if replacement else f'[{entity_type}]'
            )
            entity.auto_detected = False  # Mark as manual entity
            self.app_state.entities.append(entity)
            ui.notify(f'Added general {entity_type} entity: "{entity_text_clean}" (not found in transcript)', type='info')
        else:
            ui.notify(f'Added {entities_created} {entity_type} entities for "{entity_text_clean}" found in transcript', type='positive')
        
        # Update displays
        self._update_entity_table()
        self._update_paragraph_display()
        
        dialog.close()

    def _create_entity_from_match(self, entity_text, entity_type, replacement, match, dialog):
        """Create entity from search match"""
        paragraph_id = match['paragraph_id']
        paragraph = self.app_state.paragraphs[paragraph_id]
        
        # Find exact position of the search term
        start_pos = paragraph.text.lower().find(entity_text.lower())
        if start_pos == -1:
            ui.notify('Text not found in paragraph', type='warning')
            return
        
        # Get the actual text with original casing
        actual_text = paragraph.text[start_pos:start_pos + len(entity_text)]
        end_pos = start_pos + len(actual_text)
        
        # Check for duplicates
        existing_entity = next(
            (e for e in self.app_state.entities 
             if hasattr(e, 'paragraph_id') 
             and e.paragraph_id == paragraph_id),
            None
        )
        
        if existing_entity:
            ui.notify(f'Entity "{actual_text}" already exists in paragraph {paragraph_id + 1}', type='warning')
            return
        
        # Create new entity
        entity = Entity(
            text=actual_text,
            entity_type=entity_type,
            start_pos=start_pos,
            end_pos=end_pos,
            anonymized=False,
            replacement=replacement.strip() if replacement else f'[{entity_type}]'
        )
        entity.auto_detected = False  # Mark as manual entity
        entity.paragraph_id = paragraph_id
        
        # Add to entities list
        self.app_state.entities.append(entity)
        
        # Update displays
        self._update_entity_table()
        self._update_paragraph_display()
        
        dialog.close()
        ui.notify(f'Added {entity_type} entity: "{actual_text}" in paragraph {paragraph_id + 1}', type='positive')

    def _open_progress_dialog(self, total_paragraphs: int):
        """Open a small progress dialog overlay."""
        with ui.dialog() as d, ui.card().classes('w-96 items-start'):
            ui.label('Detecting Entities...').classes('text-h6 q-mb-sm')
            self._progress_label = ui.label(f'Scanning 0/{total_paragraphs} paragraphs (0%)').classes('text-body2 text-grey-7')
            self._progress_bar = ui.linear_progress(value=0.0).classes('w-full q-mt-sm')
        self._progress_dialog = d
        d.open()

    def _update_progress(self, current: int, total: int):
        """Update the progress label and bar."""
        if not self._progress_dialog:
            return
        pct = current / max(total, 1)
        if self._progress_label:
            self._progress_label.text = f'Scanning {current}/{total} paragraphs ({int(pct*100)}%)'
        if self._progress_bar:
            self._progress_bar.value = pct

    def _close_progress_dialog(self):
        """Close and reset progress dialog."""
        if self._progress_dialog:
            self._progress_dialog.close()
        self._progress_dialog = None
        self._progress_label = None
        self._progress_bar = None
