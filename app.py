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

# Callback for opening SQL query modal
@app.callback(
    Output("sql-query-modal", "is_open"),
    [Input("sql-query-option", "n_clicks"),
     Input("cancel-sql-query", "n_clicks")],
    [State("sql-query-modal", "is_open")]
)
def toggle_sql_query_modal(sql_clicks, cancel_clicks, is_open):
    if sql_clicks or cancel_clicks:
        return not is_open
    return is_open

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

# Callback for SQL credentials modal
@app.callback(
    Output("sql-credentials-modal", "is_open"),
    [Input("sql-option", "n_clicks"),
     Input("close-sql-modal", "n_clicks"),
     Input("connect-sql", "n_clicks")],
    [State("sql-credentials-modal", "is_open")]
)
def toggle_sql_modal(sql_clicks, close_clicks, connect_clicks, is_open):
    ctx = callback_context
    if not ctx.triggered:
        return is_open
    
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger == "sql-option":
        return True
    elif trigger in ["close-sql-modal", "connect-sql"]:
        return False
    
    return is_open

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
     Output("column-selection-modal", "is_open")],
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

# Callback for populating join column checkboxes
@app.callback(
    [Output("join-column-checkboxes", "children"),
     Output("run-comparison-from-modal", "disabled")],
    [Input("column-selection-modal", "is_open"),
     Input("join-column-search", "value"),
     Input("select-all-join", "n_clicks"),
     Input("clear-all-join", "n_clicks"),
     Input("sort-join-columns", "n_clicks")],
    [State("base-data-store", "data"),
     State("compare-data-store", "data"),
     State("join-column-checkboxes", "children")]
)
def populate_join_columns(is_open, search_value, select_all, clear_all, sort_cols, base_data, compare_data, current_checkboxes):
    if not is_open or not base_data or not compare_data:
        return html.Div(), True
    
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
        
        # Apply sorting
        ctx = callback_context
        if ctx.triggered and "sort-join-columns" in ctx.triggered[0]['prop_id']:
            common_cols = sorted(common_cols)
        
        # Handle select/clear all and preserve existing selections
        selected_values = []
        if ctx.triggered:
            trigger = ctx.triggered[0]['prop_id'].split('.')[0]
            print(f"DEBUG: Join columns trigger: {trigger}")
            if trigger == "select-all-join":
                selected_values = common_cols
                print(f"DEBUG: Selected all join columns: {selected_values}")
            elif trigger == "clear-all-join":
                selected_values = []
                print(f"DEBUG: Cleared all join columns")
            elif trigger == "column-selection-modal":
                # When modal opens, pre-select the first common column as default
                selected_values = [common_cols[0]] if common_cols else []
                print(f"DEBUG: Modal opened, pre-selected: {selected_values}")
        
        checkboxes = dbc.Checklist(
            id="join-columns-checklist",
            options=[{"label": col, "value": col} for col in common_cols],
            value=selected_values,
            className="checkbox-list"
        )
        
        is_disabled = len(selected_values) == 0
        print(f"DEBUG: Join columns selected: {selected_values}, button disabled: {is_disabled}")
        return checkboxes, is_disabled
        
    except Exception as e:
        return html.Div(f"Error: {str(e)}"), True

# Callback for populating compare column checkboxes
@app.callback(
    Output("compare-column-checkboxes", "children"),
    [Input("column-selection-modal", "is_open"),
     Input("compare-column-search", "value"),
     Input("select-all-compare", "n_clicks"),
     Input("clear-all-compare", "n_clicks"),
     Input("sort-compare-columns", "n_clicks")],
    [State("base-data-store", "data"),
     State("compare-data-store", "data")]
)
def populate_compare_columns(is_open, search_value, select_all, clear_all, sort_cols, base_data, compare_data):
    if not is_open or not base_data or not compare_data:
        return html.Div()
    
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
        
        # Apply sorting
        ctx = callback_context
        if ctx.triggered and "sort-compare-columns" in ctx.triggered[0]['prop_id']:
            common_cols = sorted(common_cols)
        
        # Handle select/clear all
        selected_values = []
        if ctx.triggered:
            trigger = ctx.triggered[0]['prop_id'].split('.')[0]
            if trigger == "select-all-compare":
                selected_values = common_cols
            elif trigger == "clear-all-compare":
                selected_values = []
        
        checkboxes = dbc.Checklist(
            id="compare-columns-checklist",
            options=[{"label": col, "value": col} for col in common_cols],
            value=selected_values,
            className="checkbox-list"
        )
        
        return checkboxes
        
    except Exception as e:
        return html.Div(f"Error: {str(e)}")

# Callback to enable/disable the run button based on join column selection
@app.callback(
    Output("run-comparison-from-modal", "disabled", allow_duplicate=True),
    [Input("join-columns-checklist", "value")],
    prevent_initial_call=True
)
def update_run_button_status(join_cols):
    return not bool(join_cols)  # Disable if no join columns selected

# Callback for running comparison from modal
@app.callback(
    [Output("column-selection-modal", "is_open", allow_duplicate=True),
     Output("comparison-results", "children", allow_duplicate=True)],
    [Input("run-comparison-from-modal", "n_clicks")],
    [State("base-data-store", "data"),
     State("compare-data-store", "data"),
     State("join-columns-checklist", "value"),
     State("compare-columns-checklist", "value")],
    prevent_initial_call=True
)
def run_comparison_from_modal(n_clicks, base_data, compare_data, join_cols, compare_cols):
    if not n_clicks or not base_data or not compare_data:
        return dash.no_update, dash.no_update
    
    try:
        base_df = pd.read_json(io.StringIO(base_data), orient='split')
        compare_df = pd.read_json(io.StringIO(compare_data), orient='split')
        
        if not join_cols:
            return dash.no_update, dbc.Alert("Please select at least one join column", color="warning")
        
        print(f"DEBUG: Running comparison with join_cols: {join_cols}, compare_cols: {compare_cols}")
        
        # Run datacompy comparison
        results = data_handler.run_comparison(base_df, compare_df, join_cols, compare_cols)
        
        # Store results in DuckDB for persistence
        results['session_id'] = duckdb_handler.session_id
        comparison_id = duckdb_handler.store_comparison_results(results)
        results['comparison_id'] = comparison_id
        
        return False, create_comparison_section(results)  # Close modal and show results
        
    except Exception as e:
        print(f"DEBUG: Comparison error: {str(e)}")
        return dash.no_update, dbc.Alert(f"Comparison Error: {str(e)}", color="danger")

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

# Add dynamic CSS container to layout - Fixed approach
main_layout = create_main_layout()
main_layout.children.append(html.Div(id="dynamic-theme-css"))
app.layout = main_layout

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
