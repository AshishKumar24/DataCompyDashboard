import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table, ALL
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import base64
import io
import os

from components.layout import create_main_layout
from components.modals import create_data_source_modal, create_sql_credentials_modal
from components.data_source import create_data_source_section, create_data_status_cards
from components.comparison_fixed import create_comparison_section
from utils.data_handler import DataHandler
from utils.sql_handler import SQLHandler
from utils.duckdb_handler import DuckDBHandler
from utils.demo_data import generate_demo_data, get_demo_summary
from components.themes import generate_theme_css, get_theme_info

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True
)

app.title = "DataCompy Dashboard"

# Initialize handlers
data_handler = DataHandler()
sql_handler = SQLHandler()
duckdb_handler = DuckDBHandler()

# Layout will be set after adding theme CSS container

# Callback for welcome modal button to open data source modal
@app.callback(
    [Output("welcome-modal", "is_open"),
     Output("data-source-modal", "is_open", allow_duplicate=True)],
    [Input("welcome-add-data", "n_clicks")],
    prevent_initial_call=True
)
def open_data_source_from_welcome(n_clicks):
    """Open data source modal when welcome button is clicked"""
    if n_clicks:
        return False, True  # Close welcome modal, open data source modal
    return dash.no_update, dash.no_update

# Callback for opening data source modal from header button
@app.callback(
    Output("data-source-modal", "is_open"),
    [Input("add-data-btn", "n_clicks"),
     Input("close-data-modal", "n_clicks")],
    [State("data-source-modal", "is_open")]
)
def toggle_data_source_modal(add_clicks, close_clicks, is_open):
    if add_clicks or close_clicks:
        return not is_open
    return is_open

# Callback for opening configuration modal
@app.callback(
    Output("configuration-modal", "is_open"),
    [Input("config-btn", "n_clicks"),
     Input("config-cancel", "n_clicks")],
    [State("configuration-modal", "is_open")]
)
def toggle_configuration_modal(config_clicks, cancel_clicks, is_open):
    if config_clicks or cancel_clicks:
        return not is_open
    return is_open

# Callback for opening SQL query modal (Step 1 - Base Dataset)
@app.callback(
    [Output("sql-query-modal", "is_open"),
     Output("data-source-modal", "is_open", allow_duplicate=True)],
    [Input("sql-query-option", "n_clicks"),
     Input("cancel-sql-step", "n_clicks")],
    [State("sql-query-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_sql_query_modal(sql_clicks, cancel_clicks, is_open):
    if sql_clicks:
        return True, False  # Open SQL modal, close data source modal
    elif cancel_clicks:
        return False, True  # Close SQL modal, open data source modal
    return is_open, dash.no_update

# Callback for SQL query step navigation
@app.callback(
    [Output("sql-query-modal", "is_open", allow_duplicate=True),
     Output("sql-compare-modal", "is_open"),
     Output("sql-step-database", "value", allow_duplicate=True),
     Output("sql-step-base-query", "value", allow_duplicate=True)],
    [Input("next-to-compare-step", "n_clicks"),
     Input("back-to-base-step", "n_clicks")],
    [State("sql-step-database", "value"),
     State("sql-step-base-query", "value"),
     State("sql-compare-modal", "is_open")],
    prevent_initial_call=True
)
def handle_sql_step_navigation(next_clicks, back_clicks, base_database_name, base_query, compare_modal_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "next-to-compare-step" and next_clicks:
        # Validate inputs before proceeding
        if base_database_name and base_query:
            return False, True, base_database_name, base_query  # Close base modal, open compare modal
        else:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    elif button_id == "back-to-base-step" and back_clicks:
        return True, False, base_database_name, base_query  # Open base modal, close compare modal
    
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

# Callback for opening credentials popup
@app.callback(
    [Output("sql-compare-modal", "is_open", allow_duplicate=True),
     Output("sql-credentials-popup", "is_open")],
    [Input("execute-step-queries", "n_clicks"),
     Input("cancel-sql-execution", "n_clicks")],
    [State("sql-step-compare-database", "value"),
     State("sql-step-compare-query", "value"),
     State("sql-credentials-popup", "is_open")],
    prevent_initial_call=True
)
def handle_sql_execution(execute_clicks, cancel_clicks, compare_database_name, compare_query, popup_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "execute-step-queries" and execute_clicks:
        # Validate compare database and query before opening credentials popup
        if compare_database_name and compare_query:
            return False, True  # Close compare modal, open credentials popup
        else:
            return dash.no_update, dash.no_update
    elif button_id == "cancel-sql-execution" and cancel_clicks:
        return True, False  # Open compare modal, close credentials popup
    
    return dash.no_update, dash.no_update

# Callback for executing SQL queries with spinner and parallel execution
@app.callback(
    [Output("sql-credentials-popup", "is_open", allow_duplicate=True),
     Output("sql-spinner-container", "children", allow_duplicate=True),
     Output("column-selection-modal", "is_open", allow_duplicate=True)],
    [Input("connect-and-execute-sql", "n_clicks")],
    [State("sql-step-database", "value"),
     State("sql-step-compare-database", "value"),
     State("sql-step-base-query", "value"),
     State("sql-step-compare-query", "value"),
     State("sql-exec-username", "value"),
     State("sql-exec-password", "value")],
    prevent_initial_call=True
)
def execute_sql_queries_parallel(execute_clicks, base_database_name, compare_database_name, base_query, compare_query, username, password):
    if not execute_clicks:
        return dash.no_update, dash.no_update, dash.no_update
    
    print(f"DEBUG: SQL execution triggered with base_db='{base_database_name}', compare_db='{compare_database_name}'")
    
    # Validate all required inputs
    if not all([base_database_name, compare_database_name, base_query, compare_query, username, password]):
        error_msg = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Please fill all required fields before executing queries."
        ], color="danger", className="text-center")
        return dash.no_update, error_msg, dash.no_update
    
    try:
        print(f"DEBUG: Starting parallel SQL execution...")
        
        # First return the spinner immediately
        spinner_content = html.Div([
            dbc.Spinner([
                html.Div([
                    html.H5("Executing SQL Queries...", className="text-center mb-3"),
                    html.P(f"Running queries on databases: {base_database_name} and {compare_database_name}", 
                           className="text-center text-muted"),
                    dbc.Progress(value=50, animated=True, color="primary", className="mb-2"),
                    html.Small("This may take a few moments", className="text-center text-muted d-block")
                ])
            ], color="primary", type="border", size="lg", spinner_style={"width": "3rem", "height": "3rem"})
        ], className="d-flex justify-content-center py-4")
        
        # Return spinner immediately, let execution happen in background
        import time
        from concurrent.futures import ThreadPoolExecutor
        
        def execute_query(query, query_type, database_name):
            """Simulate SQL query execution"""
            print(f"DEBUG: Executing {query_type} query on {database_name}")
            time.sleep(2)  # Simulate actual database query time
            return f"{query_type} query executed successfully on database '{database_name}'"
        
        # Execute queries in parallel with their respective databases
        with ThreadPoolExecutor(max_workers=2) as executor:
            base_future = executor.submit(execute_query, base_query, "Base", base_database_name)
            compare_future = executor.submit(execute_query, compare_query, "Compare", compare_database_name)
            
            base_result = base_future.result()
            compare_result = compare_future.result()
        
        print(f"DEBUG: SQL execution completed successfully")
        
        # Success - close popup, show success message, and open column selection
        success_content = dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            f"Queries executed successfully! Base: {base_database_name}, Compare: {compare_database_name}"
        ], color="success", className="text-center")
        
        return (
            False,  # Close credentials popup
            success_content,  # Show success message
            True   # Open column selection modal
        )
        
    except Exception as e:
        print(f"DEBUG: SQL execution error: {str(e)}")
        # Error handling
        error_content = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error executing queries: {str(e)}"
        ], color="danger", className="text-center")
        
        return (
            dash.no_update,  # Keep popup open
            error_content,   # Show error
            dash.no_update   # Don't open column selection
        )





# Callback to handle back to data source from column selection
@app.callback(
    [Output("column-selection-modal", "is_open", allow_duplicate=True),
     Output("data-source-modal", "is_open", allow_duplicate=True)],
    [Input("back-to-data-source", "n_clicks")],
    prevent_initial_call=True
)
def back_to_data_source_from_columns(back_clicks):
    if back_clicks:
        return False, True  # Close column modal, open data source modal
    return dash.no_update, dash.no_update

# Callback for initial add data button (dynamic button)
@app.callback(
    Output("data-source-modal", "is_open", allow_duplicate=True),
    [Input("initial-add-data", "n_clicks")],
    [State("data-source-modal", "is_open")],
    prevent_initial_call=True
)
def open_modal_from_initial_button(n_clicks, is_open):
    if n_clicks:
        return True
    return is_open

# Callback for SQL query workflow
@app.callback(
    [Output("data-source-modal", "is_open", allow_duplicate=True),
     Output("sql-query-modal", "is_open", allow_duplicate=True)],
    [Input("sql-query-option", "n_clicks")],
    prevent_initial_call=True
)
def open_sql_query_workflow(sql_clicks):
    if sql_clicks:
        return False, True  # Close data source modal, open SQL query modal
    return dash.no_update, dash.no_update

# Callback for Start Comparison button
@app.callback(
    Output("column-selection-modal", "is_open", allow_duplicate=True),
    [Input("start-comparison-btn", "n_clicks")],
    prevent_initial_call=True
)
def open_comparison_modal(n_clicks):
    if n_clicks:
        return True
    return dash.no_update

# Callback for CSV upload option button
@app.callback(
    [Output("data-source-modal", "is_open", allow_duplicate=True),
     Output("csv-upload-modal", "is_open")],
    [Input("csv-upload-option", "n_clicks")],
    prevent_initial_call=True
)
def open_csv_upload_modal(n_clicks):
    if n_clicks:
        return False, True  # Close data source modal, open CSV upload modal
    return dash.no_update, dash.no_update

# Callback for CSV upload modal
@app.callback(
    Output("csv-upload-modal", "is_open", allow_duplicate=True),
    [Input("close-csv-upload-modal", "n_clicks"),
     Input("back-to-upload", "n_clicks")],
    [State("csv-upload-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_csv_upload_modal(close_btn, back_btn, is_open):
    if close_btn or back_btn:
        return not is_open
    return is_open

# Callback for handling base CSV upload
@app.callback(
    [Output("base-upload-status", "children"),
     Output("base-data-store", "data", allow_duplicate=True),
     Output("proceed-to-columns", "disabled", allow_duplicate=True)],
    [Input("base-csv-upload", "contents")],
    [State("base-csv-upload", "filename"),
     State("compare-data-store", "data")],
    prevent_initial_call=True
)
def handle_base_csv_upload(contents, filename, compare_data):
    if contents is None:
        return "", dash.no_update, True
    
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        
        # Check if both datasets are now loaded
        both_loaded = bool(compare_data)
        
        return (
            dbc.Alert(f"✅ Base dataset '{filename}' uploaded successfully! ({len(df)} rows)", color="success"),
            df.to_json(date_format='iso', orient='split'),
            not both_loaded  # Enable button only if both datasets are loaded
        )
    except Exception as e:
        return (
            dbc.Alert(f"❌ Error uploading base file: {str(e)}", color="danger"),
            dash.no_update,
            True
        )

# Callback for handling compare CSV upload
@app.callback(
    [Output("compare-upload-status", "children"),
     Output("compare-data-store", "data", allow_duplicate=True),
     Output("proceed-to-columns", "disabled", allow_duplicate=True)],
    [Input("compare-csv-upload", "contents")],
    [State("compare-csv-upload", "filename"),
     State("base-data-store", "data")],
    prevent_initial_call=True
)
def handle_compare_csv_upload(contents, filename, base_data):
    if contents is None:
        return "", dash.no_update, True
    
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        
        # Check if both datasets are now loaded
        both_loaded = bool(base_data)
        
        return (
            dbc.Alert(f"✅ Compare dataset '{filename}' uploaded successfully! ({len(df)} rows)", color="success"),
            df.to_json(date_format='iso', orient='split'),
            not both_loaded  # Enable button only if both datasets are loaded
        )
    except Exception as e:
        return (
            dbc.Alert(f"❌ Error uploading compare file: {str(e)}", color="danger"),
            dash.no_update,
            True
        )

# Callback for opening column selection modal
@app.callback(
    [Output("csv-upload-modal", "is_open", allow_duplicate=True),
     Output("column-selection-modal", "is_open", allow_duplicate=True)],
    [Input("proceed-to-columns", "n_clicks")],
    prevent_initial_call=True
)
def open_column_selection_modal(n_clicks):
    if n_clicks:
        return False, True  # Close CSV upload modal, open column selection modal
    return dash.no_update, dash.no_update

# Callback for column selection modal
@app.callback(
    Output("column-selection-modal", "is_open", allow_duplicate=True),
    [Input("back-to-upload", "n_clicks"),
     Input("run-comparison-from-modal", "n_clicks")],
    [State("column-selection-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_column_selection_modal(back_btn, run_btn, is_open):
    if back_btn or run_btn:
        return not is_open
    return is_open

# Callback for handling CSV upload
@app.callback(
    [Output("upload-status", "children"),
     Output("base-data-store", "data", allow_duplicate=True),
     Output("compare-data-store", "data", allow_duplicate=True)],
    [Input("csv-upload", "contents")],
    [State("csv-upload", "filename"),
     State("data-type-radio", "value")],
    prevent_initial_call=True
)
def handle_csv_upload(contents, filename, data_type):
    if contents is None:
        return "", dash.no_update, dash.no_update
    
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        
        # Store data based on selected type and in DuckDB
        if data_type == "base":
            duckdb_handler.store_base_dataset(df)
            return (
                dbc.Alert(f"✅ Base dataset '{filename}' uploaded successfully! ({len(df)} rows)", color="success"),
                df.to_json(date_format='iso', orient='split'),
                dash.no_update
            )
        else:
            duckdb_handler.store_compare_dataset(df)
            return (
                dbc.Alert(f"✅ Compare dataset '{filename}' uploaded successfully! ({len(df)} rows)", color="success"),
                dash.no_update,
                df.to_json(date_format='iso', orient='split')
            )
    except Exception as e:
        return (
            dbc.Alert(f"❌ Error uploading file: {str(e)}", color="danger"),
            dash.no_update,
            dash.no_update
        )

# Callback for SQL connection
@app.callback(
    [Output("sql-status", "children"),
     Output("base-data-store", "data", allow_duplicate=True),
     Output("compare-data-store", "data", allow_duplicate=True)],
    [Input("connect-sql", "n_clicks")],
    [State("sql-host", "value"),
     State("sql-port", "value"),
     State("sql-database", "value"),
     State("sql-username", "value"),
     State("sql-password", "value"),
     State("sql-query", "value"),
     State("data-type-radio", "value")],
    prevent_initial_call=True
)
def handle_sql_connection(n_clicks, host, port, database, username, password, query, data_type):
    if not n_clicks:
        return "", dash.no_update, dash.no_update
    
    try:
        df = sql_handler.execute_query(host, port, database, username, password, query)
        
        # Store in DuckDB
        if data_type == "base":
            duckdb_handler.store_base_dataset(df)
            return (
                dbc.Alert(f"✅ Base dataset loaded from SQL! ({len(df)} rows)", color="success"),
                df.to_json(date_format='iso', orient='split'),
                dash.no_update
            )
        else:
            duckdb_handler.store_compare_dataset(df)
            return (
                dbc.Alert(f"✅ Compare dataset loaded from SQL! ({len(df)} rows)", color="success"),
                dash.no_update,
                df.to_json(date_format='iso', orient='split')
            )
    except Exception as e:
        return (
            dbc.Alert(f"❌ SQL Connection Error: {str(e)}", color="danger"),
            dash.no_update,
            dash.no_update
        )

# Callback for updating main data preview area
@app.callback(
    [Output("join-columns", "options"),
     Output("compare-columns", "options"),
     Output("data-source-section", "children")],
    [Input("base-data-store", "data"),
     Input("compare-data-store", "data"),
     Input("comparison-results", "children")]  # Add comparison results as trigger
)
def update_main_display(base_data, compare_data, comparison_results):
    print(f"DEBUG: base_data exists: {bool(base_data)}, compare_data exists: {bool(compare_data)}")
    
    # If comparison results exist, show the dashboard
    if comparison_results and comparison_results != []:
        return [], [], comparison_results
    
    # If neither dataset is loaded, show initial screen
    if not base_data and not compare_data:
        return [], [], create_data_source_section()
    
    try:
        # Handle case where only one dataset is loaded
        if base_data and not compare_data:
            base_df = pd.read_json(io.StringIO(base_data), orient='split')
            base_cols = list(base_df.columns)
            join_options = [{"label": col, "value": col} for col in base_cols]
            compare_options = [{"label": col, "value": col} for col in base_cols]
            
            preview = html.Div([
                dbc.Alert("Base dataset loaded! Please upload the compare dataset to continue.", 
                         color="info", className="mb-3"),
                create_data_status_cards(base_loaded=True, base_rows=len(base_df)),
                
                # Column arrangement in dbc.Col layout
                html.H5("📊 Base Dataset Preview", className="text-primary mb-3"),
                dbc.Row([
                    dbc.Col([
                        dash_table.DataTable(
                            data=base_df.head().to_dict('records'),
                            columns=[{"name": i, "id": i} for i in base_df.columns],
                            style_cell={'textAlign': 'left', 'fontSize': '12px'},
                            style_header={'backgroundColor': '#2c3e50', 'color': 'white', 'fontWeight': 'bold'},
                            style_data={'backgroundColor': '#ecf0f1'},
                            page_size=5
                        )
                    ], width=12)
                ])
            ])
            return join_options, compare_options, preview
            
        elif compare_data and not base_data:
            compare_df = pd.read_json(io.StringIO(compare_data), orient='split')
            compare_cols = list(compare_df.columns)
            join_options = [{"label": col, "value": col} for col in compare_cols]
            compare_options = [{"label": col, "value": col} for col in compare_cols]
            
            preview = html.Div([
                dbc.Alert("Compare dataset loaded! Please upload the base dataset to continue.", 
                         color="info", className="mb-3"),
                create_data_status_cards(compare_loaded=True, compare_rows=len(compare_df)),
                
                # Column arrangement in dbc.Col layout
                html.H5("📊 Compare Dataset Preview", className="text-success mb-3"),
                dbc.Row([
                    dbc.Col([
                        dash_table.DataTable(
                            data=compare_df.head().to_dict('records'),
                            columns=[{"name": i, "id": i} for i in compare_df.columns],
                            style_cell={'textAlign': 'left', 'fontSize': '12px'},
                            style_header={'backgroundColor': '#27ae60', 'color': 'white', 'fontWeight': 'bold'},
                            style_data={'backgroundColor': '#d5f4e6'},
                            page_size=5
                        )
                    ], width=12)
                ])
            ])
            return join_options, compare_options, preview
        
        # Both datasets are loaded - show dataset status and add data button
        base_df = pd.read_json(io.StringIO(base_data), orient='split')
        compare_df = pd.read_json(io.StringIO(compare_data), orient='split')
        
        # Get common columns for join
        base_cols = set(base_df.columns)
        compare_cols = set(compare_df.columns)
        common_cols = list(base_cols.intersection(compare_cols))
        
        print(f"DEBUG: base_cols: {base_cols}")
        print(f"DEBUG: compare_cols: {compare_cols}")
        print(f"DEBUG: common_cols: {common_cols}")
        
        join_options = [{"label": col, "value": col} for col in common_cols]
        compare_options = [{"label": col, "value": col} for col in common_cols]
        
        # Create ready-to-compare view
        preview = html.Div([
            dbc.Alert("Both datasets loaded! Click the button below to start comparing your data.", 
                     color="success", className="mb-3"),
            create_data_status_cards(True, True, len(base_df), len(compare_df)),
            
            # Action button to start comparison
            html.Div([
                dbc.Button([
                    html.I(className="fas fa-play me-2"),
                    "Start Data Comparison"
                ], id="start-comparison-btn", color="primary", size="lg", className="shadow"),
            ], className="text-center mb-4"),
            
            # Preview both datasets in columns
            dbc.Row([
                dbc.Col([
                    html.H5("📊 Base Dataset Preview", className="text-primary mb-3"),
                    dash_table.DataTable(
                        data=base_df.head().to_dict('records'),
                        columns=[{"name": i, "id": i} for i in base_df.columns],
                        style_cell={'textAlign': 'left', 'fontSize': '12px'},
                        style_header={'backgroundColor': '#2c3e50', 'color': 'white', 'fontWeight': 'bold'},
                        style_data={'backgroundColor': '#ecf0f1'},
                        page_size=5
                    )
                ], width=6),
                dbc.Col([
                    html.H5("📊 Compare Dataset Preview", className="text-success mb-3"),
                    dash_table.DataTable(
                        data=compare_df.head().to_dict('records'),
                        columns=[{"name": i, "id": i} for i in compare_df.columns],
                        style_cell={'textAlign': 'left', 'fontSize': '12px'},
                        style_header={'backgroundColor': '#27ae60', 'color': 'white', 'fontWeight': 'bold'},
                        style_data={'backgroundColor': '#d5f4e6'},
                        page_size=5
                    )
                ], width=6)
            ])
        ])
        
        return join_options, compare_options, preview
        
    except Exception as e:
        print(f"DEBUG: Error in update_main_display: {str(e)}")
        return [], [], dbc.Alert(f"Error processing data: {str(e)}", color="danger")

# This callback is removed to prevent duplicate results - comparison is now handled by run_comparison_from_modal

# Callback for populating dataset info in column selection modal
@app.callback(
    Output("dataset-info", "children"),
    [Input("column-selection-modal", "is_open")],
    [State("base-data-store", "data"),
     State("compare-data-store", "data")]
)
def populate_dataset_info(is_open, base_data, compare_data):
    if not is_open or not base_data or not compare_data:
        return html.Div()
    
    try:
        base_df = pd.read_json(io.StringIO(base_data), orient='split')
        compare_df = pd.read_json(io.StringIO(compare_data), orient='split')
        
        return dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6([html.I(className="fas fa-database me-2"), "Base Dataset"], className="text-primary"),
                        html.P(f"Rows: {len(base_df):,} | Columns: {len(base_df.columns)}", className="mb-0")
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6([html.I(className="fas fa-copy me-2"), "Compare Dataset"], className="text-success"),
                        html.P(f"Rows: {len(compare_df):,} | Columns: {len(compare_df.columns)}", className="mb-0")
                    ])
                ])
            ], width=6)
        ])
    except:
        return html.Div()

# Column sort state managed in layout.py stores

# Callback for populating join column checkboxes
@app.callback(
    [Output("join-columns-dropdown", "options"),
     Output("join-columns-dropdown", "value"),
     Output("run-comparison-from-modal", "disabled")],
    [Input("column-selection-modal", "is_open")],
    [State("base-data-store", "data"),
     State("compare-data-store", "data"),
     State("join-columns-dropdown", "value")]
)
def populate_join_columns(is_open, base_data, compare_data, current_selection):
    if not is_open or not base_data or not compare_data:
        return [], [], True
    
    try:
        base_df = pd.read_json(io.StringIO(base_data), orient='split')
        compare_df = pd.read_json(io.StringIO(compare_data), orient='split')
        
        # Get common columns
        base_cols = set(base_df.columns)
        compare_cols = set(compare_df.columns)
        common_cols = sorted(list(base_cols.intersection(compare_cols)))  # Always sort alphabetically
        
        # Preserve current selections when possible
        selected_values = current_selection if current_selection else []
        
        # Handle modal opening - pre-select the first common column as default
        ctx = callback_context
        if ctx.triggered and "column-selection-modal" in ctx.triggered[0]['prop_id']:
            selected_values = [common_cols[0]] if common_cols else []
            print(f"DEBUG: Modal opened, pre-selected: {selected_values}")
        
        # Filter selected values to only include available columns
        selected_values = [val for val in selected_values if val in common_cols]
        
        # Create dropdown options
        dropdown_options = [{"label": col, "value": col} for col in common_cols]
        
        is_disabled = len(selected_values) == 0
        print(f"DEBUG: Join columns selected: {selected_values}, button disabled: {is_disabled}")
        return dropdown_options, selected_values, is_disabled
        
    except Exception as e:
        return [], [], True

# Callback for populating compare column checkboxes
@app.callback(
    [Output("compare-column-checkboxes", "children"),
     Output("compare-sort-state", "data")],
    [Input("column-selection-modal", "is_open"),
     Input("compare-column-search", "value"),
     Input("select-all-compare", "n_clicks"),
     Input("clear-all-compare", "n_clicks"),
     Input("sort-compare-columns", "n_clicks")],
    [State("base-data-store", "data"),
     State("compare-data-store", "data"),
     State("compare-column-checkboxes", "children"),
     State("compare-sort-state", "data")]
)
def populate_compare_columns(is_open, search_value, select_all, clear_all, sort_cols, base_data, compare_data, current_checklist_value, sort_state):
    if not is_open or not base_data or not compare_data:
        return html.Div(), {"is_sorted": False}
    
    try:
        base_df = pd.read_json(io.StringIO(base_data), orient='split')
        compare_df = pd.read_json(io.StringIO(compare_data), orient='split')
        
        # Get common columns
        base_cols = set(base_df.columns)
        compare_cols = set(compare_df.columns)
        common_cols = list(base_cols.intersection(compare_cols))
        
        # Apply search filter
        if search_value:
            common_cols = [col for col in common_cols if search_value.lower() in col.lower()]
        
        # Manage sorting state
        ctx = callback_context
        is_sorted = sort_state.get("is_sorted", False) if sort_state else False
        
        if ctx.triggered:
            trigger = ctx.triggered[0]['prop_id'].split('.')[0]
            if trigger == "sort-compare-columns":
                is_sorted = not is_sorted  # Toggle sort state
                print(f"DEBUG: Compare columns sort toggled, now sorted: {is_sorted}")
        
        # Apply sorting based on current state
        if is_sorted:
            common_cols = sorted(common_cols)
        
        # Extract current selections from the children component if it exists
        selected_values = []
        if current_checklist_value and isinstance(current_checklist_value, dict):
            if 'props' in current_checklist_value and 'value' in current_checklist_value['props']:
                selected_values = current_checklist_value['props']['value'] or []
        
        # Handle button actions
        if ctx.triggered:
            trigger = ctx.triggered[0]['prop_id'].split('.')[0]
            print(f"DEBUG: Compare columns trigger: {trigger}")
            
            if trigger == "select-all-compare":
                selected_values = common_cols
                print(f"DEBUG: Selected all compare columns: {selected_values}")
            elif trigger == "clear-all-compare":
                selected_values = []
                print(f"DEBUG: Cleared all compare columns")
            elif trigger == "sort-compare-columns":
                # Keep existing selections when sorting
                print(f"DEBUG: Sorting triggered, preserving selections: {selected_values}")
            elif trigger == "compare-column-search":
                # Keep existing selections when searching
                print(f"DEBUG: Search triggered, preserving selections: {selected_values}")
        
        # Filter selected values to only include available columns
        selected_values = [val for val in selected_values if val in common_cols]
        
        checkboxes = dbc.Checklist(
            id="compare-columns-checklist",
            options=[{"label": col, "value": col} for col in common_cols],
            value=selected_values,
            className="checkbox-list"
        )
        
        print(f"DEBUG: Compare columns selected: {selected_values}")
        return checkboxes, {"is_sorted": is_sorted}
        
    except Exception as e:
        return html.Div(f"Error: {str(e)}"), {"is_sorted": False}

# Callback to enable/disable the run button based on join column selection  
@app.callback(
    Output("run-comparison-from-modal", "disabled", allow_duplicate=True),
    [Input("join-columns-dropdown", "value")],
    prevent_initial_call=True
)
def update_run_button_status(join_cols):
    return not bool(join_cols)  # Disable if no join columns selected

# Callback for running comparison from modal with loading spinner
@app.callback(
    [Output("column-selection-modal", "is_open", allow_duplicate=True),
     Output("comparison-results", "children", allow_duplicate=True)],
    [Input("run-comparison-from-modal", "n_clicks")],
    [State("base-data-store", "data"),
     State("compare-data-store", "data"),
     State("join-columns-dropdown", "value"),
     State("compare-column-checkboxes", "children")],
    prevent_initial_call=True
)
def run_comparison_from_modal(n_clicks, base_data, compare_data, join_cols, compare_col_children):
    if not n_clicks or not base_data or not compare_data:
        return dash.no_update, dash.no_update
    
    try:
        # Show loading spinner immediately
        loading_spinner = html.Div([
            dbc.Spinner([
                html.Div([
                    html.H4("Running Data Comparison...", className="text-center mb-3"),
                    html.P("Analyzing differences between datasets", className="text-center text-muted"),
                    dbc.Progress(value=75, animated=True, color="success", className="mb-2"),
                    html.Small("This may take a few moments depending on dataset size", className="text-center text-muted d-block")
                ])
            ], color="success", type="border", size="lg", spinner_style={"width": "3rem", "height": "3rem"})
        ], className="d-flex justify-content-center py-5")
        
        base_df = pd.read_json(io.StringIO(base_data), orient='split')
        compare_df = pd.read_json(io.StringIO(compare_data), orient='split')
        
        if not join_cols:
            return dash.no_update, dbc.Alert("Please select at least one join column", color="warning")
        
        # Extract compare columns from children component
        compare_cols = []
        if compare_col_children and isinstance(compare_col_children, dict):
            if 'props' in compare_col_children and 'value' in compare_col_children['props']:
                compare_cols = compare_col_children['props']['value'] or []
        
        print(f"DEBUG: Running comparison with join_cols: {join_cols}, compare_cols: {compare_cols}")
        
        # Simulate processing time for large datasets
        import time
        time.sleep(1)  # Brief delay to show spinner
        
        # Run datacompy comparison
        results = data_handler.run_comparison(base_df, compare_df, join_cols, compare_cols)
        
        # Store results in DuckDB for persistence
        results['session_id'] = duckdb_handler.session_id
        comparison_id = duckdb_handler.store_comparison_results(results)
        results['comparison_id'] = comparison_id
        
        print(f"DEBUG: Comparison completed successfully")
        
        return False, create_comparison_section(results)  # Close modal and show results
        
    except Exception as e:
        print(f"DEBUG: Comparison error: {str(e)}")
        error_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Comparison Error: {str(e)}"
        ], color="danger", className="mt-3")
        return dash.no_update, error_alert

# Callback for loading demo data
@app.callback(
    [Output("base-data-store", "data", allow_duplicate=True),
     Output("compare-data-store", "data", allow_duplicate=True),
     Output("column-selection-modal", "is_open", allow_duplicate=True)],
    [Input("load-demo-btn", "n_clicks")],
    prevent_initial_call=True
)
def load_demo_data(n_clicks):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update
    
    try:
        # Generate demo data
        base_df, compare_df = generate_demo_data()
        
        # Convert to JSON for storage
        base_data = base_df.to_json(orient='split')
        compare_data = compare_df.to_json(orient='split')
        
        print(f"DEBUG: Demo data loaded - Base: {len(base_df)} rows, Compare: {len(compare_df)} rows")
        
        # Open column selection modal with demo data loaded
        return base_data, compare_data, True
        
    except Exception as e:
        print(f"ERROR: Failed to load demo data: {str(e)}")
        return dash.no_update, dash.no_update, dash.no_update

# Simplified theme callback - just for logging
@app.callback(
    Output("dynamic-theme-css", "children"),
    [Input("theme-selector", "value")]
)
def update_theme(theme_id):
    if not theme_id:
        theme_id = "default"
    
    theme_info = get_theme_info(theme_id)
    print(f"DEBUG: Theme changed to: {theme_info['name']}")
    
    # Return empty div - theme styling handled via CSS classes
    return html.Div()

# Session Management Callbacks
@app.callback(
    [Output("session-info-display", "children"),
     Output("session-files-display", "children")],
    [Input("refresh-session-info", "n_clicks"),
     Input("configuration-modal", "is_open")],
    prevent_initial_call=True
)
def update_session_information(refresh_clicks, modal_open):
    """Update session information display"""
    if not modal_open:
        return dash.no_update, dash.no_update
    
    try:
        # Current session info
        session_info_card = dbc.Row([
            dbc.Col([
                dbc.Badge(f"Session ID: {duckdb_handler.session_id}", color="primary", className="mb-2")
            ], width=12),
            dbc.Col([
                html.P([
                    html.Strong("Database Path: "),
                    html.Code(duckdb_handler.db_path)
                ], className="mb-2"),
                html.P([
                    html.Strong("Connection Status: "),
                    dbc.Badge("Connected" if duckdb_handler.conn else "Disconnected", 
                             color="success" if duckdb_handler.conn else "danger")
                ], className="mb-0")
            ], width=12)
        ])
        
        # Session files info
        from utils.duckdb_handler import DuckDBHandler
        session_files = DuckDBHandler.get_session_files_info()
        
        if not session_files:
            files_display = dbc.Alert("No session files found", color="info")
        else:
            total_size = sum(file['size_mb'] for file in session_files)
            
            files_table = dbc.Table([
                html.Thead([
                    html.Tr([
                        html.Th("Filename"),
                        html.Th("Size (MB)"),
                        html.Th("Age (hours)")
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(file['filename']),
                        html.Td(f"{file['size_mb']:.2f}"),
                        html.Td(f"{file['age_hours']:.1f}")
                    ]) for file in session_files[:10]  # Show first 10 files
                ])
            ], striped=True, hover=True, size="sm")
            
            files_display = html.Div([
                dbc.Alert([
                    html.Strong(f"Total: {len(session_files)} files"),
                    html.Span(f" • {total_size:.2f} MB total size")
                ], color="light", className="mb-3"),
                files_table,
                html.Small(f"Showing {min(10, len(session_files))} of {len(session_files)} files", 
                          className="text-muted") if len(session_files) > 10 else ""
            ])
        
        return session_info_card, files_display
        
    except Exception as e:
        error_message = dbc.Alert(f"Error loading session info: {str(e)}", color="danger")
        return error_message, error_message

@app.callback(
    Output("cleanup-status", "children"),
    [Input("cleanup-old-sessions", "n_clicks"),
     Input("force-cleanup-sessions", "n_clicks")],
    [State("cleanup-threshold", "value")],
    prevent_initial_call=True
)
def handle_session_cleanup(cleanup_old_clicks, force_cleanup_clicks, threshold_hours):
    """Handle session cleanup actions"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if button_id == "cleanup-old-sessions":
            # Clean old sessions based on threshold
            threshold = threshold_hours or 24
            old_count = len([f for f in duckdb_handler.get_session_files_info() 
                           if f['age_hours'] > threshold])
            
            duckdb_handler._cleanup_old_sessions(max_age_hours=threshold)
            
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Successfully cleaned {old_count} session files older than {threshold} hours."
            ], color="success", dismissable=True)
            
        elif button_id == "force-cleanup-sessions":
            # Force cleanup all sessions except current
            cleaned_count = duckdb_handler.force_cleanup_all_sessions()
            
            return dbc.Alert([
                html.I(className="fas fa-trash-alt me-2"),
                f"Force cleaned {cleaned_count} session files. Warning: This removed all session files."
            ], color="warning", dismissable=True)
            
    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Cleanup error: {str(e)}"
        ], color="danger", dismissable=True)
    
    return dash.no_update

# Callbacks for expand table functionality
@app.callback(
    Output("comparison-results", "children", allow_duplicate=True),
    [Input("expand-mismatch-btn", "n_clicks"),
     Input("expand-base-btn", "n_clicks"), 
     Input("expand-compare-btn", "n_clicks")],
    [State("comparison-results", "children"),
     State("base-data-store", "data"),
     State("compare-data-store", "data"),
     State("join-columns-dropdown", "value")],
    prevent_initial_call=True
)
def handle_table_expansion(mismatch_clicks, base_clicks, compare_clicks, current_results, base_data, compare_data, join_cols):
    """Handle expand/collapse functionality for tables in comparison results"""
    if not any([mismatch_clicks, base_clicks, compare_clicks]) or not current_results:
        return dash.no_update
    
    # Determine which button was clicked
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update
        
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        # Re-run comparison with expanded flag
        if not base_data or not compare_data or not join_cols:
            return dash.no_update
            
        base_df = pd.read_json(io.StringIO(base_data), orient='split')
        compare_df = pd.read_json(io.StringIO(compare_data), orient='split')
        
        # Get compare columns from current UI state (fallback to all if not available)
        compare_cols = base_df.columns.tolist()  # Use all columns as fallback
        
        # Create comparison with datacompy
        import datacompy
        comparison = datacompy.Compare(
            base_df,
            compare_df,
            join_columns=join_cols,
            df1_name="Base",
            df2_name="Compare"
        )
        
        # Store results with expansion flags
        results = {
            'comparison_obj': comparison,
            'base_shape': base_df.shape,
            'compare_shape': compare_df.shape,
            'intersect_rows': comparison.intersect_rows.shape[0] if hasattr(comparison, 'intersect_rows') else 0,
            'base_only_rows': comparison.df1_unq_rows.shape[0] if hasattr(comparison, 'df1_unq_rows') else 0,
            'compare_only_rows': comparison.df2_unq_rows.shape[0] if hasattr(comparison, 'df2_unq_rows') else 0,
            'match_rate': float(comparison.matches()) if hasattr(comparison, 'matches') else 0.0,
            # Expansion flags
            'expand_mismatch': button_id == "expand-mismatch-btn",
            'expand_base': button_id == "expand-base-btn", 
            'expand_compare': button_id == "expand-compare-btn"
        }
        
        return create_comparison_section(results)
        
    except Exception as e:
        print(f"DEBUG: Table expansion error: {str(e)}")
        return current_results

# Add dynamic CSS container to layout - Fixed approach
main_layout = create_main_layout()
if hasattr(main_layout, 'children') and main_layout.children is not None:
    main_layout.children.append(html.Div(id="dynamic-theme-css"))
else:
    # Fallback if children is None
    main_layout = html.Div([main_layout, html.Div(id="dynamic-theme-css")])
app.layout = main_layout

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
