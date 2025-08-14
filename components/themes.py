import dash_bootstrap_components as dbc
from dash import html

# Define theme configurations
THEMES = {
    'default': {
        'name': 'DataCompy Classic',
        'bootstrap_theme': dbc.themes.BOOTSTRAP,
        'primary_color': '#667eea',
        'secondary_color': '#764ba2',
        'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'card_bg': 'rgba(255, 255, 255, 0.95)',
        'description': 'Classic gradient theme with purple-blue tones'
    },
    'ocean': {
        'name': 'Ocean Blue',
        'bootstrap_theme': dbc.themes.BOOTSTRAP,
        'primary_color': '#0066CC',
        'secondary_color': '#004499',
        'background': 'linear-gradient(135deg, #667db6 0%, #0082c8 100%)',
        'card_bg': 'rgba(255, 255, 255, 0.95)',
        'description': 'Cool ocean-inspired blue theme'
    },
    'sunset': {
        'name': 'Sunset Orange',
        'bootstrap_theme': dbc.themes.BOOTSTRAP,
        'primary_color': '#ff6b35',
        'secondary_color': '#f7931e',
        'background': 'linear-gradient(135deg, #ff6b35 0%, #f7931e 100%)',
        'card_bg': 'rgba(255, 255, 255, 0.95)',
        'description': 'Warm sunset colors with orange gradients'
    },
    'forest': {
        'name': 'Forest Green',
        'bootstrap_theme': dbc.themes.BOOTSTRAP,
        'primary_color': '#2d5016',
        'secondary_color': '#4a7c59',
        'background': 'linear-gradient(135deg, #2d5016 0%, #4a7c59 100%)',
        'card_bg': 'rgba(255, 255, 255, 0.95)',
        'description': 'Natural forest green with earthy tones'
    },
    'night': {
        'name': 'Night Mode',
        'bootstrap_theme': dbc.themes.DARKLY,
        'primary_color': '#1a1a2e',
        'secondary_color': '#16213e',
        'background': 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
        'card_bg': 'rgba(33, 37, 41, 0.95)',
        'description': 'Dark theme for low-light environments'
    },
    'rose': {
        'name': 'Rose Gold',
        'bootstrap_theme': dbc.themes.BOOTSTRAP,
        'primary_color': '#e8b4cb',
        'secondary_color': '#d4a7c9',
        'background': 'linear-gradient(135deg, #e8b4cb 0%, #d4a7c9 100%)',
        'card_bg': 'rgba(255, 255, 255, 0.95)',
        'description': 'Elegant rose gold with soft pink tones'
    },
    'cyber': {
        'name': 'Cyber Purple',
        'bootstrap_theme': dbc.themes.BOOTSTRAP,
        'primary_color': '#9c27b0',
        'secondary_color': '#673ab7',
        'background': 'linear-gradient(135deg, #9c27b0 0%, #673ab7 100%)',
        'card_bg': 'rgba(255, 255, 255, 0.95)',
        'description': 'Futuristic purple theme with neon accents'
    },
    'minimal': {
        'name': 'Minimal Gray',
        'bootstrap_theme': dbc.themes.BOOTSTRAP,
        'primary_color': '#6c757d',
        'secondary_color': '#495057',
        'background': 'linear-gradient(135deg, #6c757d 0%, #495057 100%)',
        'card_bg': 'rgba(255, 255, 255, 0.95)',
        'description': 'Clean minimal design with neutral grays'
    }
}

def create_theme_selector():
    """Create theme selector dropdown component"""
    return html.Div([
        html.Label("Theme:", className="form-label fw-bold text-white me-2"),
        dbc.Select(
            id="theme-selector",
            options=[
                {"label": f"{theme['name']}", "value": theme_id}
                for theme_id, theme in THEMES.items()
            ],
            value="default",
            className="theme-selector",
            style={"width": "200px"}
        )
    ], className="d-flex align-items-center")

def generate_theme_css(theme_id):
    """Generate CSS variables for the selected theme"""
    if theme_id not in THEMES:
        theme_id = 'default'
    
    theme = THEMES[theme_id]
    
    # Return CSS variables that can be applied via external stylesheet
    css_vars = {
        '--theme-primary': theme['primary_color'],
        '--theme-secondary': theme['secondary_color'],
        '--theme-background': theme['background'],
        '--theme-card-bg': theme['card_bg']
    }
    
    return css_vars

def _hex_to_rgb(hex_color):
    """Convert hex color to RGB values"""
    hex_color = hex_color.lstrip('#')
    return ', '.join(str(int(hex_color[i:i+2], 16)) for i in (0, 2, 4))

def get_theme_info(theme_id):
    """Get theme information"""
    return THEMES.get(theme_id, THEMES['default'])