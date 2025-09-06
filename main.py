"""
Main entry point for Psymerique - Therapeutic Transcript Analysis App
Built with NiceUI for desktop interface
"""

from nicegui import ui, app
from src.app_state import AppState
from src.ui.layout import MainLayout
from src.ui.theme import apply_theme
from src.config import APP_CONFIG

def initialize_nlp_models():
    """Pre-download and initialize NLP models during startup"""
    try:
        print("🔄 Initializing NLP models...")
        
        # Import and initialize Stanza
        import stanza
        from src.services.nlp_service import NLPService
        
        # Download English model if not present
        try:
            # Check if model exists first
            stanza.Pipeline('en', processors='tokenize,ner', download_method=None, verbose=False)
            print("✅ Stanza models already available")
        except:
            print("📥 Downloading Stanza English model (this may take a few minutes)...")
            stanza.download('en', verbose=False)
            print("✅ Stanza model downloaded successfully")
        
        # Pre-initialize the NLP service
        nlp_service = NLPService()
        nlp_service._initialize_stanza()
        print("✅ NLP models ready for offline use")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize NLP models: {e}")
        print("🔄 App will use regex-based fallback for entity detection")

def main():
    """Initialize and run the application"""
    # Initialize NLP models before starting the web server
    initialize_nlp_models()
    
    # Apply global theme
    apply_theme()
    
    # Initialize application state
    app_state = AppState()
    
    # Create main layout
    main_layout = MainLayout(app_state)
    main_layout.create()
    
    # Configure app
    ui.run(
        title=APP_CONFIG['title'],
        favicon=APP_CONFIG.get('favicon'),
        port=APP_CONFIG.get('port', 8080),
        show=True,
        reload=False
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
