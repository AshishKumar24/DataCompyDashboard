import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from components.modals import create_welcome_modal, create_data_source_modal, create_sql_credentials_modal, create_csv_upload_modal, create_column_selection_modal, create_configuration_modal, create_sql_query_modal, create_sql_compare_modal, create_sql_credentials_popup
from components.themes import create_theme_selector

def create_main_layout():
    """Create the main layout for the dashboard"""
    return html.Div([
        # URL location for page load detection
        dcc.Location(id="url", refresh=False),
        
        # Data stores
        dcc.Store(id="base-data-store"),
        dcc.Store(id="compare-data-store"),
        
        # Overlay div for background greying
        html.Div(id="overlay", className="overlay"),
        
        # Main container
        dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H1([
                            html.I(className="fas fa-chart-line me-3"),
                            "DataCompy Dashboard"
                        ], className="text-white mb-0"),
                        html.P("Compare datasets with powerful analytics", 
                               className="text-white-50 mb-0")
                    ])
                ], width=6),
                dbc.Col([
                    html.Div([
                        create_theme_selector(),
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-cogs me-2"),
                                "Settings"
                            ], 
                            id="config-btn", 
                            color="secondary", 
                            size="lg",
                            outline=True),
                            dbc.Button([
                                html.I(className="fas fa-plus me-2"),
                                "Add Data Source"
                            ], 
                            id="add-data-btn", 
                            color="light", 
                            size="lg"),
                            dbc.Button([
                                html.I(className="fas fa-database me-2"),
                                "Load Demo Data"
                            ], 
                            id="load-demo-btn", 
                            color="success", 
                            size="lg")
                        ], className="ms-3")
                    ], className="d-flex align-items-center float-end")
                ], width=6)
            ], className="mb-4 py-4"),
            
            # Main content area - Single container to prevent duplicates
            html.Div(id="main-dashboard-content", children=[
                # Data source section (visible when no data loaded)
                html.Div(id="data-source-section"),
                
                # Comparison results section (hidden initially)  
                html.Div(id="comparison-results"),
                
                # Hidden dropdowns for callbacks (not displayed but needed for functionality)
                html.Div([
                    dcc.Dropdown(id="join-columns", multi=True, style={"display": "none"}),
                    dcc.Dropdown(id="compare-columns", multi=True, style={"display": "none"}),
                    dbc.Button(id="run-comparison", style={"display": "none"})
                ], style={"display": "none"})
            ])
        ], fluid=True, className="main-content"),
        
        # Modals
        html.Div(id="modals-container", children=[
            create_welcome_modal(),
            create_data_source_modal(),
            create_sql_credentials_modal(),
            create_csv_upload_modal(),
            create_column_selection_modal(),
            create_configuration_modal(),
            create_sql_query_modal(),
            create_sql_compare_modal(),
            create_sql_credentials_popup()
        ])
    ], className="dashboard-container")


