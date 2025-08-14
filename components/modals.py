import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

def create_welcome_modal():
    """Create welcome modal with data source button"""
    return dbc.Modal([
        dbc.ModalBody([
            html.Div([
                html.Div([
                    html.I(className="fas fa-chart-bar fa-5x text-primary mb-4"),
                    html.H2("Welcome to DataCompy Dashboard", className="text-center mb-3"),
                    html.P(
                        "Compare datasets with powerful analytics and detailed insights. "
                        "Upload CSV files or connect to your databases to get started.",
                        className="text-center text-muted mb-4 lead"
                    ),
                    dbc.Button([
                        html.I(className="fas fa-plus me-2"),
                        "Add Your Data Source"
                    ], 
                    id="welcome-add-data", 
                    color="primary", 
                    size="lg",
                    className="shadow-sm")
                ], className="text-center py-4")
            ])
        ])
    ], 
    id="welcome-modal", 
    is_open=True,  # Open by default
    backdrop="static",
    keyboard=False,
    centered=True,
    size="lg")

def create_configuration_modal():
    """Create configuration modal for changing join/compare columns"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H4([
                html.I(className="fas fa-cogs me-2"),
                "Configuration Settings"
            ], className="mb-0")
        ]),
        dbc.ModalBody([
            html.Div(id="config-dataset-info"),
            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                "Tip: You can reconfigure join and compare columns here and run a new comparison with different settings."
            ], color="info", className="mb-3"),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.Label("Join Columns:", className="form-label fw-bold"),
                    html.Div([
                        dbc.InputGroup([
                            dbc.Input(
                                id="config-join-search",
                                placeholder="Search columns...",
                                type="text"
                            ),
                            dbc.Button([
                                html.I(className="fas fa-sort-alpha-down")
                            ], id="config-sort-join", outline=True, color="secondary")
                        ], className="mb-2"),
                        dbc.ButtonGroup([
                            dbc.Button("Select All", id="config-select-all-join", outline=True, color="primary", size="sm"),
                            dbc.Button("Clear All", id="config-clear-all-join", outline=True, color="secondary", size="sm")
                        ], className="mb-3")
                    ]),
                    html.Div(id="config-join-checkboxes")
                ], width=6),
                dbc.Col([
                    html.Label("Compare Columns (optional):", className="form-label fw-bold"),
                    html.Div([
                        dbc.InputGroup([
                            dbc.Input(
                                id="config-compare-search",
                                placeholder="Search columns...",
                                type="text"
                            ),
                            dbc.Button([
                                html.I(className="fas fa-sort-alpha-down")
                            ], id="config-sort-compare", outline=True, color="secondary")
                        ], className="mb-2"),
                        dbc.ButtonGroup([
                            dbc.Button("Select All", id="config-select-all-compare", outline=True, color="primary", size="sm"),
                            dbc.Button("Clear All", id="config-clear-all-compare", outline=True, color="secondary", size="sm")
                        ], className="mb-3")
                    ]),
                    html.Div(id="config-compare-checkboxes")
                ], width=6)
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="config-cancel", color="secondary", className="me-2"),
            dbc.Button([
                html.I(className="fas fa-sync-alt me-2"),
                "Update Comparison"
            ], id="config-update-comparison", color="primary")
        ])
    ], 
    id="configuration-modal", 
    size="xl",
    backdrop="static")

def create_data_source_modal():
    """Create the data source selection modal"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H4([
                html.I(className="fas fa-database me-2"),
                "Select Data Source"
            ], className="mb-0")
        ]),
        dbc.ModalBody([
            # Data source options
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="fas fa-file-csv fa-3x text-primary mb-3"),
                                html.H5("Upload CSV Files", className="card-title"),
                                html.P("Upload both base and compare CSV files", className="card-text text-muted"),
                                dbc.Button([
                                    html.I(className="fas fa-upload me-2"),
                                    "Upload CSV Files"
                                ], id="csv-upload-option", color="primary", outline=True, className="w-100")
                            ], className="text-center")
                        ])
                    ], className="h-100 border-2 hover-card")
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="fas fa-database fa-3x text-success mb-3"),
                                html.H5("SQL Query", className="card-title"),
                                html.P("Connect to database and run queries", className="card-text text-muted"),
                                dbc.Button([
                                    html.I(className="fas fa-plug me-2"),
                                    "Connect to DB"
                                ], id="sql-option", color="success", outline=True, className="w-100")
                            ], className="text-center")
                        ])
                    ], className="h-100 border-2 hover-card")
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="fas fa-code fa-3x text-info mb-3"),
                                html.H5("SQL Queries", className="card-title"),
                                html.P("Write custom SQL queries for comparison", className="card-text text-muted"),
                                dbc.Button([
                                    html.I(className="fas fa-code me-2"),
                                    "Write SQL Queries"
                                ], id="sql-query-option", color="info", outline=True, className="w-100")
                            ], className="text-center")
                        ])
                    ], className="h-100 border-2 hover-card")
                ], width=4)
            ], className="mb-4")
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id="close-data-modal", color="secondary")
        ])
    ], 
    id="data-source-modal", 
    size="xl", 
    backdrop="static",
    is_open=False,  # Don't open by default, will be opened by welcome modal
    className="custom-modal")

def create_sql_credentials_modal():
    """Create the SQL credentials input modal"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H4([
                html.I(className="fas fa-key me-2"),
                "Database Connection"
            ], className="mb-0")
        ]),
        dbc.ModalBody([
            dbc.Form([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Host:", html_for="sql-host", className="fw-bold"),
                        dbc.Input(
                            id="sql-host",
                            type="text",
                            placeholder="localhost",
                            value="localhost"
                        )
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Port:", html_for="sql-port", className="fw-bold"),
                        dbc.Input(
                            id="sql-port",
                            type="number",
                            placeholder="5432",
                            value=5432
                        )
                    ], width=6)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Database:", html_for="sql-database", className="fw-bold"),
                        dbc.Input(
                            id="sql-database",
                            type="text",
                            placeholder="database_name"
                        )
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Username:", html_for="sql-username", className="fw-bold"),
                        dbc.Input(
                            id="sql-username",
                            type="text",
                            placeholder="username"
                        )
                    ], width=6)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Password:", html_for="sql-password", className="fw-bold"),
                        dbc.Input(
                            id="sql-password",
                            type="password",
                            placeholder="password"
                        )
                    ], width=12)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("SQL Query:", html_for="sql-query", className="fw-bold"),
                        dbc.Textarea(
                            id="sql-query",
                            placeholder="SELECT * FROM your_table LIMIT 1000",
                            rows=4,
                            className="font-monospace"
                        )
                    ], width=12)
                ], className="mb-3")
            ]),
            html.Div(id="sql-status")
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="close-sql-modal", color="secondary", className="me-2"),
            dbc.Button([
                html.I(className="fas fa-plug me-2"),
                "Connect"
            ], id="connect-sql", color="success")
        ])
    ], 
    id="sql-credentials-modal", 
    size="lg", 
    backdrop="static",
    className="custom-modal")

def create_csv_upload_modal():
    """Create the CSV upload modal for both files"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H4([
                html.I(className="fas fa-file-csv me-2"),
                "Upload CSV Files"
            ], className="mb-0")
        ]),
        dbc.ModalBody([
            # Base dataset upload
            dbc.Card([
                dbc.CardHeader([
                    html.H6([
                        html.I(className="fas fa-database me-2"),
                        "Base Dataset"
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    dcc.Upload(
                        id='base-csv-upload',
                        children=html.Div([
                            html.I(className="fas fa-cloud-upload-alt fa-2x mb-2"),
                            html.P("Drag and drop or click to select base CSV file", className="mb-0")
                        ], className="text-center py-3"),
                        style={
                            'width': '100%',
                            'height': '80px',
                            'lineHeight': '80px',
                            'borderWidth': '2px',
                            'borderStyle': 'dashed',
                            'borderRadius': '8px',
                            'textAlign': 'center',
                            'backgroundColor': '#f8f9fa'
                        },
                        multiple=False
                    ),
                    html.Div(id="base-upload-status", className="mt-2")
                ])
            ], className="mb-3"),
            
            # Compare dataset upload
            dbc.Card([
                dbc.CardHeader([
                    html.H6([
                        html.I(className="fas fa-copy me-2"),
                        "Compare Dataset"
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    dcc.Upload(
                        id='compare-csv-upload',
                        children=html.Div([
                            html.I(className="fas fa-cloud-upload-alt fa-2x mb-2"),
                            html.P("Drag and drop or click to select compare CSV file", className="mb-0")
                        ], className="text-center py-3"),
                        style={
                            'width': '100%',
                            'height': '80px',
                            'lineHeight': '80px',
                            'borderWidth': '2px',
                            'borderStyle': 'dashed',
                            'borderRadius': '8px',
                            'textAlign': 'center',
                            'backgroundColor': '#f8f9fa'
                        },
                        multiple=False
                    ),
                    html.Div(id="compare-upload-status", className="mt-2")
                ])
            ], className="mb-3"),
            
            # Progress indicator
            html.Div(id="upload-progress", className="mb-3")
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="close-csv-upload-modal", color="secondary", className="me-2"),
            dbc.Button([
                html.I(className="fas fa-arrow-right me-2"),
                "Next: Select Columns"
            ], id="proceed-to-columns", color="primary", disabled=True)
        ])
    ], 
    id="csv-upload-modal", 
    size="lg", 
    backdrop="static",
    className="custom-modal")

def create_column_selection_modal():
    """Create the column selection modal with search and checkboxes"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H4([
                html.I(className="fas fa-columns me-2"),
                "Select Columns for Comparison"
            ], className="mb-0")
        ]),
        dbc.ModalBody([
            # Dataset info
            html.Div(id="dataset-info", className="mb-4"),
            
            # Join columns section
            dbc.Card([
                dbc.CardHeader([
                    html.H6([
                        html.I(className="fas fa-link me-2"),
                        "Join Columns (Required)"
                    ], className="mb-0"),
                    html.Small("Select columns to join/match records between datasets", className="text-muted")
                ]),
                dbc.CardBody([
                    # Search for join columns
                    dbc.InputGroup([
                        dbc.InputGroupText(html.I(className="fas fa-search")),
                        dbc.Input(
                            id="join-column-search",
                            placeholder="Search join columns...",
                            type="text"
                        )
                    ], className="mb-3"),
                    
                    # Join column options
                    html.Div([
                        dbc.Button([
                            html.I(className="fas fa-check-square me-2"),
                            "Select All"
                        ], id="select-all-join", size="sm", color="outline-primary", className="me-2 mb-2"),
                        dbc.Button([
                            html.I(className="fas fa-square me-2"),
                            "Clear All"
                        ], id="clear-all-join", size="sm", color="outline-secondary", className="me-2 mb-2"),
                        dbc.Button([
                            html.I(className="fas fa-sort-alpha-down me-2"),
                            "Sort A-Z"
                        ], id="sort-join-columns", size="sm", color="outline-info", className="mb-2")
                    ], className="mb-3"),
                    
                    html.Div(id="join-column-checkboxes", className="max-height-200 overflow-auto")
                ])
            ], className="mb-4"),
            
            # Compare columns section
            dbc.Card([
                dbc.CardHeader([
                    html.H6([
                        html.I(className="fas fa-balance-scale me-2"),
                        "Compare Columns (Optional)"
                    ], className="mb-0"),
                    html.Small("Select specific columns to compare (leave empty to compare all)", className="text-muted")
                ]),
                dbc.CardBody([
                    # Search for compare columns
                    dbc.InputGroup([
                        dbc.InputGroupText(html.I(className="fas fa-search")),
                        dbc.Input(
                            id="compare-column-search",
                            placeholder="Search compare columns...",
                            type="text"
                        )
                    ], className="mb-3"),
                    
                    # Compare column options
                    html.Div([
                        dbc.Button([
                            html.I(className="fas fa-check-square me-2"),
                            "Select All"
                        ], id="select-all-compare", size="sm", color="outline-primary", className="me-2 mb-2"),
                        dbc.Button([
                            html.I(className="fas fa-square me-2"),
                            "Clear All"
                        ], id="clear-all-compare", size="sm", color="outline-secondary", className="me-2 mb-2"),
                        dbc.Button([
                            html.I(className="fas fa-sort-alpha-down me-2"),
                            "Sort A-Z"
                        ], id="sort-compare-columns", size="sm", color="outline-info", className="mb-2")
                    ], className="mb-3"),
                    
                    html.Div(id="compare-column-checkboxes", className="max-height-200 overflow-auto")
                ])
            ], className="mb-4")
        ]),
        dbc.ModalFooter([
            dbc.Button("Back to Upload", id="back-to-upload", color="secondary", className="me-2"),
            dbc.Button([
                html.I(className="fas fa-play me-2"),
                "Run Comparison"
            ], id="run-comparison-from-modal", color="success", disabled=True)
        ])
    ], 
    id="column-selection-modal", 
    size="xl", 
    backdrop="static",
    className="custom-modal")

def create_sql_query_modal():
    """Create SQL query input modal for base and compare queries"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H4([
                html.I(className="fas fa-code me-2"),
                "SQL Query Input"
            ], className="mb-0")
        ]),
        dbc.ModalBody([
            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                "Write SQL queries to fetch your base and compare datasets. Both queries should return similar column structures for proper comparison."
            ], color="info", className="mb-4"),
            
            # Database connection section
            dbc.Card([
                dbc.CardHeader([
                    html.H5([
                        html.I(className="fas fa-database me-2"),
                        "Database Connection"
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Database Type:", className="fw-bold"),
                            dbc.Select(
                                id="sql-query-db-type",
                                options=[
                                    {"label": "PostgreSQL", "value": "postgresql"},
                                    {"label": "MySQL", "value": "mysql"},
                                    {"label": "SQLite", "value": "sqlite"}
                                ],
                                value="postgresql"
                            )
                        ], width=4),
                        dbc.Col([
                            dbc.Label("Host:", className="fw-bold"),
                            dbc.Input(
                                id="sql-query-host",
                                type="text",
                                placeholder="localhost",
                                value="localhost"
                            )
                        ], width=4),
                        dbc.Col([
                            dbc.Label("Port:", className="fw-bold"),
                            dbc.Input(
                                id="sql-query-port",
                                type="number",
                                placeholder="5432",
                                value=5432
                            )
                        ], width=4)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Database:", className="fw-bold"),
                            dbc.Input(
                                id="sql-query-database",
                                type="text",
                                placeholder="database_name"
                            )
                        ], width=4),
                        dbc.Col([
                            dbc.Label("Username:", className="fw-bold"),
                            dbc.Input(
                                id="sql-query-username",
                                type="text",
                                placeholder="username"
                            )
                        ], width=4),
                        dbc.Col([
                            dbc.Label("Password:", className="fw-bold"),
                            dbc.Input(
                                id="sql-query-password",
                                type="password",
                                placeholder="password"
                            )
                        ], width=4)
                    ])
                ])
            ], className="mb-4"),
            
            # SQL Queries section
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5([
                                html.I(className="fas fa-table me-2 text-primary"),
                                "Base Dataset Query"
                            ], className="mb-0")
                        ]),
                        dbc.CardBody([
                            dbc.Label("SQL Query for Base Dataset:", className="fw-bold mb-2"),
                            dbc.Textarea(
                                id="base-sql-query",
                                placeholder="SELECT * FROM base_table WHERE...",
                                rows=8,
                                className="font-monospace",
                                style={"fontSize": "14px"}
                            ),
                            html.Small("Write your SQL query to fetch the base dataset", className="text-muted")
                        ])
                    ], className="border-primary")
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5([
                                html.I(className="fas fa-table me-2 text-success"),
                                "Compare Dataset Query"
                            ], className="mb-0")
                        ]),
                        dbc.CardBody([
                            dbc.Label("SQL Query for Compare Dataset:", className="fw-bold mb-2"),
                            dbc.Textarea(
                                id="compare-sql-query",
                                placeholder="SELECT * FROM compare_table WHERE...",
                                rows=8,
                                className="font-monospace",
                                style={"fontSize": "14px"}
                            ),
                            html.Small("Write your SQL query to fetch the compare dataset", className="text-muted")
                        ])
                    ], className="border-success")
                ], width=6)
            ], className="mb-3"),
            
            # Test connection and preview
            dbc.Row([
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button([
                            html.I(className="fas fa-plug me-2"),
                            "Test Connection"
                        ], id="test-sql-connection", color="outline-secondary", size="sm"),
                        dbc.Button([
                            html.I(className="fas fa-eye me-2"),
                            "Preview Base"
                        ], id="preview-base-query", color="outline-primary", size="sm"),
                        dbc.Button([
                            html.I(className="fas fa-eye me-2"),
                            "Preview Compare"
                        ], id="preview-compare-query", color="outline-success", size="sm")
                    ], className="w-100")
                ], width=12)
            ]),
            
            # Status/preview area
            html.Div(id="sql-query-status", className="mt-3")
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-sql-query", color="secondary", className="me-2"),
            dbc.Button([
                html.I(className="fas fa-play me-2"),
                "Execute Queries & Compare"
            ], id="execute-sql-queries", color="primary", disabled=True)
        ])
    ], 
    id="sql-query-modal", 
    size="xl",
    backdrop="static",
    is_open=False,
    className="custom-modal")
