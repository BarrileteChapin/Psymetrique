"""
Main layout and navigation structure
"""

from nicegui import ui
from ..config import STEPS
from .components.home import HomeSection
from .components.entities import EntitiesSection
from .components.speakers import SpeakersSection
from .components.sentiment import SentimentSection
from .components.encoding import EncodingSection
from .components.report import ReportSection
from .theme import get_button_class


class MainLayout:
    """Main application layout with stepper navigation"""
    
    def __init__(self, app_state):
        self.app_state = app_state
        self.stepper = None
        self.sections = {}
        
    def create(self):
        """Create the main layout"""
        # Main container
        with ui.column().classes('main-container w-full'):
            self._create_header()
            self._create_stepper()
            self._create_navigation()
    
    def _create_header(self):
        """Create application header"""
        with ui.row().classes('app-header w-full items-center'):
            ui.label('Therapeutic Transcript Analysis').classes('app-title')
            ui.space()
            # Could add additional header elements here (settings, help, etc.)
    
    def _create_stepper(self):
        """Create the main stepper navigation"""
        with ui.stepper().props('vertical=false header-nav').classes('w-full') as stepper:
            self.stepper = stepper
            
            # Home step
            with ui.step('Home'):
                self.sections['home'] = HomeSection(self.app_state)
                self.sections['home'].create()
            
            # Speakers step
            with ui.step('Speakers'):
                self.sections['speakers'] = SpeakersSection(self.app_state)
                self.sections['speakers'].create()
            
            # Entities step  
            with ui.step('Entities'):
                self.sections['entities'] = EntitiesSection(self.app_state)
                self.sections['entities'].create()
            
            # Sentiment step
            with ui.step('Sentiment'):
                self.sections['sentiment'] = SentimentSection(self.app_state)
                self.sections['sentiment'].create()
            
            # Encoding step
            with ui.step('Encoding'):
                self.sections['encoding'] = EncodingSection(self.app_state)
                self.sections['encoding'].create()
            
            # Report step
            with ui.step('Report'):
                self.sections['report'] = ReportSection(self.app_state)
                self.sections['report'].create()
    
    def _create_navigation(self):
        """Create navigation buttons"""
        with ui.row().classes('nav-buttons w-full'):
            ui.button('Back', on_click=self._go_back).classes(get_button_class('secondary'))
            ui.space()
            ui.button('Next', on_click=self._go_next).classes(get_button_class('primary'))
    
    def _go_back(self):
        """Navigate to previous step"""
        if self.stepper:
            self.stepper.previous()
            if self.app_state.current_step > 0:
                self.app_state.current_step -= 1
                self._refresh_current_section()
    
    def _go_next(self):
        """Navigate to next step"""
        if self.stepper:
            # Validate current step before proceeding
            if self._validate_current_step():
                self.stepper.next()
                if self.app_state.current_step < len(STEPS) - 1:
                    self.app_state.current_step += 1
                self._refresh_current_section()
            else:
                ui.notify('Please complete the current step before proceeding', type='warning')
    
    def _refresh_current_section(self):
        """Refresh the current section's display"""
        current_step = self.app_state.current_step
        
        if current_step == 1 and 'speakers' in self.sections:  # Speakers
            if hasattr(self.sections['speakers'], 'refresh'):
                self.sections['speakers'].refresh()
        elif current_step == 2 and 'entities' in self.sections:  # Entities
            if hasattr(self.sections['entities'], 'refresh'):
                self.sections['entities'].refresh()
        elif current_step == 3 and 'sentiment' in self.sections:  # Sentiment
            if hasattr(self.sections['sentiment'], 'refresh'):
                self.sections['sentiment'].refresh()
        elif current_step == 4 and 'encoding' in self.sections:  # Encoding
            if hasattr(self.sections['encoding'], 'refresh'):
                self.sections['encoding'].refresh()
        elif current_step == 5 and 'report' in self.sections:  # Report
            if hasattr(self.sections['report'], 'refresh'):
                self.sections['report'].refresh()

    def _validate_current_step(self):
        """Validate if current step is complete"""
        current_step = self.app_state.current_step
        
        if current_step == 0:  # Home
            return bool(self.app_state.current_transcript.strip())
        elif current_step == 1:  # Speakers
            return True  # Always allow progression from speakers
        elif current_step == 2:  # Entities
            return True  # Always allow progression from entities
        elif current_step == 3:  # Sentiment
            return True  # Always allow progression from sentiment
        elif current_step == 4:  # Encoding
            return True  # Always allow progression from encoding
        elif current_step == 5:  # Report
            return True  # Final step
        
        return True
