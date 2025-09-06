"""
Theme and styling configuration for the application
"""

from nicegui import ui
from ..config import COLORS


def apply_theme():
    """Apply global theme and CSS styles"""
    
    # Custom CSS for the application
    css = f"""
    <style>
        /* Global theme variables */
        :root {{
            --primary-color: {COLORS['primary']};
            --secondary-color: {COLORS['secondary']};
            --accent-color: {COLORS['accent']};
            --background-color: {COLORS['background']};
            --white: {COLORS['white']};
            --light-gray: {COLORS['light_gray']};
        }}
        
        /* Main application container */
        .main-container {{
            background-color: var(--white);
            min-height: 100vh;
        }}
        
        /* Header styling */
        .app-header {{
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .app-title {{
            font-size: 1.8rem;
            font-weight: 600;
            margin: 0;
        }}
        
        /* Stepper customization */
        .q-stepper {{
            box-shadow: none;
            background: transparent;
        }}
        
        .q-stepper__header {{
            border-bottom: 1px solid #e0e0e0;
            padding: 1rem 2rem;
        }}
        
        .q-stepper__content {{
            padding: 2rem;
            min-height: 60vh;
        }}
        
        /* Upload area styling */
        .upload-area {{
            border: 2px dashed var(--secondary-color);
            border-radius: 12px;
            padding: 3rem;
            text-align: center;
            background: linear-gradient(45deg, #f8f9fa, #e9ecef);
            transition: all 0.3s ease;
        }}
        
        .upload-area:hover {{
            border-color: var(--primary-color);
            background: linear-gradient(45deg, #e9ecef, #dee2e6);
        }}
        
        /* Paragraph styling */
        .paragraph {{
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 8px;
            border-left: 4px solid transparent;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .paragraph:hover {{
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transform: translateY(-1px);
        }}
        
        .paragraph.client {{
            background-color: {COLORS['client_bg']};
            border-left-color: var(--primary-color);
        }}
        
        .paragraph.therapist {{
            background-color: {COLORS['therapist_bg']};
            border-left-color: var(--secondary-color);
        }}
        
        .paragraph.positive {{
            background-color: rgba(76, 175, 80, 0.1);
            border-left-color: {COLORS['positive']};
        }}
        
        .paragraph.negative {{
            background-color: rgba(244, 67, 54, 0.1);
            border-left-color: {COLORS['negative']};
        }}
        
        .paragraph.neutral {{
            background-color: rgba(158, 158, 158, 0.1);
            border-left-color: {COLORS['neutral']};
        }}
        
        .paragraph.mixed {{
            background-color: rgba(255, 152, 0, 0.1);
            border-left-color: {COLORS['mixed']};
        }}
        
        /* Button styling */
        .primary-btn {{
            background: var(--primary-color) !important;
            color: white !important;
        }}
        
        .secondary-btn {{
            background: var(--secondary-color) !important;
            color: white !important;
        }}
        
        .accent-btn {{
            background: var(--accent-color) !important;
            color: var(--primary-color) !important;
        }}
        
        /* Navigation buttons */
        .nav-buttons {{
            display: flex;
            justify-content: space-between;
            padding: 1rem 2rem;
            border-top: 1px solid #e0e0e0;
            background: var(--light-gray);
        }}
        
        /* Entity table styling */
        .entity-table {{
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        /* Coding scheme table */
        .coding-table {{
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        /* Code badges */
        .code-badge {{
            background: var(--accent-color);
            color: var(--primary-color);
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.8rem;
            margin: 0.1rem;
            display: inline-block;
        }}
        
        /* Charts container */
        .charts-container {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }}
        
        /* Responsive design */
        @media (max-width: 768px) {{
            .app-header {{
                padding: 1rem;
            }}
            
            .q-stepper__content {{
                padding: 1rem;
            }}
            
            .nav-buttons {{
                padding: 1rem;
            }}
        }}
    </style>
    """
    
    ui.add_head_html(css)


def get_paragraph_class(paragraph, mode='speaker'):
    """Get CSS class for paragraph based on mode"""
    base_class = "paragraph"
    
    if mode == 'speaker':
        if paragraph.speaker == 'client':
            return f"{base_class} client"
        elif paragraph.speaker == 'therapist':
            return f"{base_class} therapist"
        else:
            return base_class
    elif mode == 'sentiment':
        return f"{base_class} {paragraph.sentiment}"
    
    return base_class


def get_button_class(button_type='primary'):
    """Get CSS class for buttons"""
    classes = {
        'primary': 'primary-btn',
        'secondary': 'secondary-btn', 
        'accent': 'accent-btn'
    }
    return classes.get(button_type, 'primary-btn')
