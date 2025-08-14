import dash
from dash import html
import dash_bootstrap_components as dbc

def create_demo_data_info():
    """Create info section about demo data"""
    from utils.demo_data import get_demo_summary
    demo_summary = get_demo_summary()
    
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-database me-2"),
            "Demo Data Loaded"
        ]),
        dbc.CardBody([
            html.H6(demo_summary['description'], className="card-title"),
            html.P(f"Base: {demo_summary['base_dataset']}", className="mb-1"),
            html.P(f"Compare: {demo_summary['compare_dataset']}", className="mb-2"),
            
            html.H6("What this demo shows:", className="mt-3 mb-2"),
            html.Ul([
                html.Li(item) for item in demo_summary['demonstrates'][:5]
            ]),
            
            dbc.Alert([
                html.Strong("Ready to explore! "), 
                f"Join on '{demo_summary['join_column']}' and compare all other columns to see the full dashboard features."
            ], color="success", className="mb-0")
        ])
    ], className="mb-4")

def create_data_source_section():
    """Create the initial data source section when no data is loaded"""
    return html.Div([
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className="fas fa-chart-bar fa-4x text-muted mb-4"),
                    html.H3("Welcome to DataCompy Dashboard", className="text-muted mb-3"),
                    html.P(
                        "Start by adding your base and compare datasets. You can upload CSV files or connect to a SQL database.",
                        className="text-muted mb-4 lead"
                    ),
                    dbc.Button([
                        html.I(className="fas fa-plus me-2"),
                        "Add Your First Dataset"
                    ], 
                    id="initial-add-data", 
                    color="primary", 
                    size="lg",
                    className="shadow")
                ], className="text-center py-5")
            ])
        ], className="shadow-sm border-0")
    ], className="mb-4")

def create_data_status_cards(base_loaded=False, compare_loaded=False, base_rows=0, compare_rows=0):
    """Create status cards showing loaded datasets"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-database fa-2x text-primary mb-2"),
                        html.H5("Base Dataset", className="card-title"),
                        html.P(f"{base_rows:,} rows" if base_loaded else "Not loaded", 
                               className="card-text"),
                        dbc.Badge("✓ Loaded" if base_loaded else "Pending", 
                                 color="success" if base_loaded else "warning",
                                 className="position-absolute top-0 start-100 translate-middle")
                    ], className="text-center position-relative")
                ])
            ], className="h-100 shadow-sm")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-copy fa-2x text-success mb-2"),
                        html.H5("Compare Dataset", className="card-title"),
                        html.P(f"{compare_rows:,} rows" if compare_loaded else "Not loaded", 
                               className="card-text"),
                        dbc.Badge("✓ Loaded" if compare_loaded else "Pending", 
                                 color="success" if compare_loaded else "warning",
                                 className="position-absolute top-0 start-100 translate-middle")
                    ], className="text-center position-relative")
                ])
            ], className="h-100 shadow-sm")
        ], width=6)
    ], className="mb-4")
