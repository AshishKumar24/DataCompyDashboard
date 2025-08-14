import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

def create_comparison_section(results):
    """Create comprehensive comparison dashboard with fixed data tables"""
    
    if not results:
        return html.Div()

    try:
        # Extract basic metrics
        comparison = results.get('comparison_obj')
        base_shape = results.get('base_shape', (0, 0))
        compare_shape = results.get('compare_shape', (0, 0))
        intersect_rows = results.get('intersect_rows', 0)
        base_only_rows = results.get('base_only_rows', 0)
        compare_only_rows = results.get('compare_only_rows', 0)
        match_rate = results.get('match_rate', 0)
        
        # Get DataFrames from comparison object
        unq_base_df = comparison.df1_unq_rows if hasattr(comparison, 'df1_unq_rows') else pd.DataFrame()
        unq_compare_df = comparison.df2_unq_rows if hasattr(comparison, 'df2_unq_rows') else pd.DataFrame()
        all_mismatches_df = comparison.all_mismatch() if hasattr(comparison, 'all_mismatch') else pd.DataFrame()
        
        # Column statistics
        column_stats = []
        for col in comparison.intersect_columns():
            try:
                base_dtype = str(comparison.df1[col].dtype)
                compare_dtype = str(comparison.df2[col].dtype)
                base_nulls = int(comparison.df1[col].isnull().sum())
                compare_nulls = int(comparison.df2[col].isnull().sum())
                
                # Count mismatches for this column
                mismatch_count = 0
                if not all_mismatches_df.empty and col in all_mismatches_df.columns:
                    mismatch_count = len(all_mismatches_df)
                
                column_stats.append({
                    'Column': col,
                    'Base Datatype': base_dtype,
                    'Compare Datatype': compare_dtype,
                    'Base Nulls': base_nulls,
                    'Compare Nulls': compare_nulls,
                    'Mismatch Count': mismatch_count
                })
            except:
                continue
        
        # Calculate comprehensive statistics
        total_mismatches = sum(col.get('Mismatch Count', 0) for col in column_stats)
        common_columns = len(comparison.intersect_columns()) if hasattr(comparison, 'intersect_columns') else 0
        base_only_columns = len(comparison.df1_unq_columns()) if hasattr(comparison, 'df1_unq_columns') else 0
        compare_only_columns = len(comparison.df2_unq_columns()) if hasattr(comparison, 'df2_unq_columns') else 0
        dtype_mismatches = len([col for col in column_stats if col.get('Base Datatype') != col.get('Compare Datatype')])
        
        # Create comprehensive dashboard
        return dbc.Container([
            # Comprehensive statistics cards - Row 1
            dbc.Row([
                dbc.Col([
                    create_metric_card("Base Dataset", f"{base_shape[0]:,} rows", f"{base_shape[1]} columns", "fas fa-database", "primary")
                ], width=3),
                dbc.Col([
                    create_metric_card("Compare Dataset", f"{compare_shape[0]:,} rows", f"{compare_shape[1]} columns", "fas fa-copy", "success")
                ], width=3),
                dbc.Col([
                    create_metric_card("Common Rows", f"{intersect_rows:,}", f"{match_rate:.1%} match rate", "fas fa-check-circle", "info")
                ], width=3),
                dbc.Col([
                    create_metric_card("Total Mismatches", f"{total_mismatches:,}", "field differences", "fas fa-exclamation-triangle", "danger")
                ], width=3)
            ], className="mb-3"),
            
            # Row 2 - Additional statistics
            dbc.Row([
                dbc.Col([
                    create_metric_card("Base Only Rows", f"{base_only_rows:,}", "unique to base", "fas fa-minus-circle", "warning")
                ], width=3),
                dbc.Col([
                    create_metric_card("Compare Only Rows", f"{compare_only_rows:,}", "unique to compare", "fas fa-plus-circle", "warning")
                ], width=3),
                dbc.Col([
                    create_metric_card("Column Analysis", f"Base: {base_shape[1]} | Compare: {compare_shape[1]}", f"Common: {common_columns}, Diff: {base_only_columns + compare_only_columns}", "fas fa-columns", "secondary")
                ], width=3),
                dbc.Col([
                    create_metric_card("Data Type Mismatches", f"{dtype_mismatches}", "columns with different types", "fas fa-code", "dark")
                ], width=3)
            ], className="mb-4"),
            
            # Column Differences Section (if any differences exist)
            (dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5([
                                html.I(className="fas fa-exclamation-triangle me-2", style={"color": "#f39c12"}),
                                "Column Differences Analysis"
                            ], className="card-title text-warning"),
                            html.Hr(),
                            html.Div([
                                dbc.Badge(f"Base Only: {', '.join(comparison.df1_unq_columns())}", color="primary", className="me-2 mb-2") if hasattr(comparison, 'df1_unq_columns') and comparison.df1_unq_columns() else "",
                                dbc.Badge(f"Compare Only: {', '.join(comparison.df2_unq_columns())}", color="success", className="me-2 mb-2") if hasattr(comparison, 'df2_unq_columns') and comparison.df2_unq_columns() else ""
                            ] if (hasattr(comparison, 'df1_unq_columns') and comparison.df1_unq_columns()) or (hasattr(comparison, 'df2_unq_columns') and comparison.df2_unq_columns()) else [
                                dbc.Alert("All columns are present in both datasets.", color="success", className="mb-0")
                            ])
                        ])
                    ], className="mb-3 shadow-sm")
                ], width=12)
            ]) if (hasattr(comparison, 'df1_unq_columns') and comparison.df1_unq_columns()) or (hasattr(comparison, 'df2_unq_columns') and comparison.df2_unq_columns()) else ""),
            
            # Tabbed interface
            dbc.Tabs(id="comparison-tabs", active_tab="overview", children=[
                
                # Overview Tab
                dbc.Tab(label="Overview", tab_id="overview", children=[
                    html.Div([
                        dbc.Row([
                            # Row statistics
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Row Analysis"),
                                    dbc.CardBody([
                                        create_row_stats_table(intersect_rows, base_only_rows, compare_only_rows),
                                        dcc.Graph(
                                            figure=create_row_stats_chart(intersect_rows, base_only_rows, compare_only_rows)
                                        )
                                    ])
                                ])
                            ], width=6),
                            
                            # Column statistics
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Column Analysis"),
                                    dbc.CardBody([
                                        create_column_summary_table(results),
                                        dcc.Graph(
                                            figure=create_column_stats_chart(results)
                                        )
                                    ])
                                ])
                            ], width=6)
                        ], className="mb-4")
                    ], className="p-4")
                ]),
                
                # Row Analysis Tab
                dbc.Tab(label="Row Analysis", tab_id="row-analysis", children=[
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Detailed Row Statistics"),
                                    dbc.CardBody([
                                        create_detailed_row_table(intersect_rows, base_only_rows, compare_only_rows, base_shape[0], compare_shape[0])
                                    ])
                                ])
                            ], width=12)
                        ])
                    ], className="p-4")
                ]),
                
                # Column Analysis Tab with DataTable
                dbc.Tab(label="Column Analysis", tab_id="column-analysis", children=[
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Column-by-Column Analysis"),
                                    dbc.CardBody([
                                        dash_table.DataTable(
                                            data=column_stats,
                                            columns=[
                                                {"name": "Column", "id": "Column"},
                                                {"name": "Base Datatype", "id": "Base Datatype"},
                                                {"name": "Compare Datatype", "id": "Compare Datatype"},
                                                {"name": "Mismatch Count", "id": "Mismatch Count", "type": "numeric"},
                                                {"name": "Base Nulls", "id": "Base Nulls", "type": "numeric"},
                                                {"name": "Compare Nulls", "id": "Compare Nulls", "type": "numeric"}
                                            ],
                                            style_cell={'textAlign': 'left'},
                                            style_data_conditional=[
                                                {
                                                    'if': {'filter_query': '{Mismatch Count} > 0'},
                                                    'backgroundColor': '#ffe6e6',
                                                    'color': 'black',
                                                },
                                                {
                                                    'if': {'filter_query': '{Base Datatype} != {Compare Datatype}'},
                                                    'backgroundColor': '#fff3cd',
                                                    'color': 'black',
                                                }
                                            ],
                                            page_size=10,
                                            sort_action="native",
                                            filter_action="native"
                                        )
                                    ])
                                ])
                            ], width=8),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Column Mismatch Chart"),
                                    dbc.CardBody([
                                        dcc.Graph(
                                            figure=create_column_mismatch_chart(column_stats)
                                        )
                                    ])
                                ])
                            ], width=4)
                        ])
                    ], className="p-4")
                ]),
                
                # Mismatch Details Tab with DataTable
                dbc.Tab(label="Mismatch Details", tab_id="mismatch-details", children=[
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Mismatch Breakdown"),
                                    dbc.CardBody([
                                        create_mismatch_pie_charts(column_stats, all_mismatches_df)
                                    ])
                                ])
                            ], width=6),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Sample Mismatched Records"),
                                    dbc.CardBody([
                                        create_mismatch_data_table(all_mismatches_df)
                                    ])
                                ])
                            ], width=6)
                        ])
                    ], className="p-4")
                ]),
                
                # Unique Rows Tab with DataTable
                dbc.Tab(label="Unique Rows", tab_id="unique-rows", children=[
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Rows Only in Base Dataset"),
                                    dbc.CardBody([
                                        create_unique_rows_data_table(unq_base_df, "base")
                                    ])
                                ])
                            ], width=6),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Rows Only in Compare Dataset"),
                                    dbc.CardBody([
                                        create_unique_rows_data_table(unq_compare_df, "compare")
                                    ])
                                ])
                            ], width=6)
                        ])
                    ], className="p-4")
                ])
            ])
        ], fluid=True)
        
    except Exception as e:
        print(f"Error creating comparison section: {str(e)}")
        return dbc.Alert(f"Error displaying results: {str(e)}", color="danger")

def create_metric_card(title, value, subtitle, icon, color):
    """Create metric card component"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"{icon} fa-2x text-{color} mb-2"),
                html.H4(value, className="card-title mb-1"),
                html.H6(title, className="text-muted mb-0"),
                html.P(subtitle, className="small text-muted mb-0")
            ], className="text-center")
        ])
    ], className="h-100")

def create_row_stats_table(intersect_rows, base_only_rows, compare_only_rows):
    """Create row statistics table"""
    data = [
        {"Metric": "Matching Rows", "Count": intersect_rows},
        {"Metric": "Only in Base", "Count": base_only_rows},
        {"Metric": "Only in Compare", "Count": compare_only_rows}
    ]
    
    return dash_table.DataTable(
        data=data,
        columns=[
            {"name": "Metric", "id": "Metric"},
            {"name": "Count", "id": "Count", "type": "numeric", "format": {"specifier": ","}}
        ],
        style_cell={'textAlign': 'left'},
        style_data_conditional=[
            {
                'if': {'filter_query': '{Count} > 0 and {Metric} contains "Only"'},
                'backgroundColor': '#fff3cd',
                'color': 'black',
            },
            {
                'if': {'filter_query': '{Metric} contains "Matching"'},
                'backgroundColor': '#d1edff',
                'color': 'black',
            }
        ]
    )

def create_detailed_row_table(intersect_rows, base_only_rows, compare_only_rows, total_base, total_compare):
    """Create detailed row analysis table"""
    data = [
        {"Metric": "Total Rows in Base", "Count": total_base, "Percentage": "100%"},
        {"Metric": "Total Rows in Compare", "Count": total_compare, "Percentage": "100%"},
        {"Metric": "Intersecting Rows", "Count": intersect_rows, "Percentage": f"{(intersect_rows/max(total_base, 1))*100:.1f}%"},
        {"Metric": "Base Only Rows", "Count": base_only_rows, "Percentage": f"{(base_only_rows/max(total_base, 1))*100:.1f}%"},
        {"Metric": "Compare Only Rows", "Count": compare_only_rows, "Percentage": f"{(compare_only_rows/max(total_compare, 1))*100:.1f}%"}
    ]
    
    return dash_table.DataTable(
        data=data,
        columns=[
            {"name": "Metric", "id": "Metric"},
            {"name": "Count", "id": "Count", "type": "numeric", "format": {"specifier": ","}},
            {"name": "Percentage", "id": "Percentage"}
        ],
        style_cell={'textAlign': 'left'},
        page_size=10
    )

def create_column_summary_table(results):
    """Create column summary table"""
    base_cols = len(results.get('base_columns', []))
    compare_cols = len(results.get('compare_columns', []))
    common_cols = len(results.get('columns_compared', []))
    
    data = [
        {"Metric": "Base Columns", "Count": base_cols},
        {"Metric": "Compare Columns", "Count": compare_cols},
        {"Metric": "Common Columns", "Count": common_cols}
    ]
    
    return dash_table.DataTable(
        data=data,
        columns=[
            {"name": "Metric", "id": "Metric"},
            {"name": "Count", "id": "Count", "type": "numeric"}
        ],
        style_cell={'textAlign': 'left'}
    )

def create_mismatch_data_table(all_mismatches_df, expanded=False):
    """Create enhanced DataTable for mismatch details with base vs compare rows"""
    if all_mismatches_df.empty:
        return html.Div([
            dbc.Alert("No mismatched records found.", color="info", className="mb-3"),
            dbc.Button([
                html.I(className="fas fa-expand me-2"),
                "Expand Table"
            ], id="expand-mismatch-btn", color="outline-secondary", size="sm", disabled=True)
        ])
    
    # Transform data to show base vs compare values as separate rows
    mismatch_rows = []
    for idx, row in all_mismatches_df.iterrows():
        for col in all_mismatches_df.columns:
            if '_base' in col:
                base_col = col
                compare_col = col.replace('_base', '_compare')
                if compare_col in all_mismatches_df.columns:
                    base_val = row[base_col]
                    compare_val = row[compare_col]
                    if pd.notna(base_val) or pd.notna(compare_val):
                        mismatch_rows.append({
                            'Row Index': idx,
                            'Column Name': base_col.replace('_base', ''),
                            'Base Value': str(base_val) if pd.notna(base_val) else "NULL",
                            'Compare Value': str(compare_val) if pd.notna(compare_val) else "NULL",
                            'Mismatch Type': 'Value Difference' if base_val != compare_val else 'Null Difference'
                        })
    
    if not mismatch_rows:
        # Fallback to original structure if transformation fails
        sample_df = all_mismatches_df.head(300 if expanded else 100).fillna("NULL").infer_objects(copy=False)
        columns = [{"name": col, "id": col} for col in sample_df.columns]
        data = sample_df.to_dict('records')
    else:
        # Use transformed mismatch rows
        sample_data = mismatch_rows[:1000 if expanded else 200]
        columns = [
            {"name": "Row Index", "id": "Row Index", "type": "numeric"},
            {"name": "Column Name", "id": "Column Name"},
            {"name": "Base Value", "id": "Base Value"},
            {"name": "Compare Value", "id": "Compare Value"},
            {"name": "Mismatch Type", "id": "Mismatch Type"}
        ]
        data = sample_data
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Button([
                    html.I(className="fas fa-expand me-2"),
                    f"{'Collapse' if expanded else 'Expand'} Table ({len(data)} rows shown)"
                ], id="expand-mismatch-btn", color="outline-primary", size="sm", className="mb-3")
            ], width=12)
        ]),
        dash_table.DataTable(
            data=data,
            columns=columns,
            style_table={'overflowX': 'auto', 'width': '100%', 'minWidth': '100%'},
            style_cell={
                'textAlign': 'left', 'fontSize': '11px', 'padding': '8px', 
                'maxWidth': '200px', 'overflow': 'hidden', 'textOverflow': 'ellipsis',
                'whiteSpace': 'normal', 'height': 'auto'
            },
            style_header={'backgroundColor': '#e74c3c', 'color': 'white', 'fontWeight': 'bold'},
            style_data={'backgroundColor': '#fdeaea'},
            style_data_conditional=[
                {
                    'if': {'column_id': 'Base Value'},
                    'backgroundColor': '#e3f2fd',
                    'color': '#1976d2'
                },
                {
                    'if': {'column_id': 'Compare Value'},
                    'backgroundColor': '#e8f5e8',
                    'color': '#388e3c'
                }
            ],
            page_size=50 if expanded else 25,
            filter_action="native",
            sort_action="native",
            export_format="csv",
            export_headers="display"
        )
    ])

def create_unique_rows_data_table(unique_df, dataset_type, expanded=False):
    """Create enhanced DataTable for unique rows with expand functionality"""
    if unique_df.empty:
        return html.Div([
            dbc.Alert(f"No unique rows in {dataset_type} dataset.", color="info", className="mb-3"),
            dbc.Button([
                html.I(className="fas fa-expand me-2"),
                "Expand Table"
            ], id=f"expand-{dataset_type.lower()}-btn", color="outline-secondary", size="sm", disabled=True)
        ])
    
    # Sample rows based on expand state
    sample_df = unique_df.head(500 if expanded else 150).fillna("NULL").infer_objects(copy=False)
    
    columns = [{"name": col, "id": col} for col in sample_df.columns]
    
    color_scheme = {
        'base': {'header': '#2c3e50', 'data': '#ecf0f1'},
        'compare': {'header': '#27ae60', 'data': '#d5f4e6'}
    }
    
    colors = color_scheme.get(dataset_type.lower(), {'header': '#6c757d', 'data': '#f8f9fa'})
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Button([
                    html.I(className="fas fa-expand me-2"),
                    f"{'Collapse' if expanded else 'Expand'} {dataset_type} Table ({len(sample_df)} rows shown)"
                ], id=f"expand-{dataset_type.lower()}-btn", color="outline-primary", size="sm", className="mb-3")
            ], width=12)
        ]),
        dash_table.DataTable(
            data=sample_df.to_dict('records'),
            columns=columns,
            style_table={'overflowX': 'auto', 'width': '100%', 'minWidth': '100%'},
            style_cell={
                'textAlign': 'left', 'fontSize': '11px', 'padding': '8px',
                'maxWidth': '150px', 'overflow': 'hidden', 'textOverflow': 'ellipsis',
                'whiteSpace': 'normal', 'height': 'auto'
            },
            style_header={'backgroundColor': colors['header'], 'color': 'white', 'fontWeight': 'bold'},
            style_data={'backgroundColor': colors['data']},
            page_size=50 if expanded else 20,
            sort_action="native",
            filter_action="native",
            export_format="csv",
            export_headers="display"
        )
    ])

def create_row_stats_chart(intersect_rows, base_only_rows, compare_only_rows):
    """Create bar chart for row statistics"""
    categories = ['Matching Rows', 'Only in Base', 'Only in Compare']
    values = [intersect_rows, base_only_rows, compare_only_rows]
    colors = ['#28a745', '#ffc107', '#dc3545']
    
    fig = go.Figure(data=[
        go.Bar(x=categories, y=values, marker_color=colors)
    ])
    
    fig.update_layout(
        title="Row Distribution",
        xaxis_title="Category",
        yaxis_title="Count",
        showlegend=False,
        height=300
    )
    
    return fig

def create_column_stats_chart(results):
    """Create chart for column statistics"""
    base_cols = len(results.get('base_columns', []))
    compare_cols = len(results.get('compare_columns', []))
    common_cols = len(results.get('columns_compared', []))
    
    fig = go.Figure(data=[
        go.Bar(x=['Base Columns', 'Compare Columns', 'Common Columns'], 
               y=[base_cols, compare_cols, common_cols],
               marker_color=['#007bff', '#28a745', '#17a2b8'])
    ])
    
    fig.update_layout(
        title="Column Comparison",
        xaxis_title="Dataset",
        yaxis_title="Column Count",
        showlegend=False,
        height=300
    )
    
    return fig

def create_column_mismatch_chart(column_stats):
    """Create bar chart for column mismatches"""
    if not column_stats:
        return go.Figure()
    
    # Get columns with mismatches
    mismatch_data = [(col['Column'], col['Mismatch Count']) for col in column_stats if col['Mismatch Count'] > 0]
    
    if not mismatch_data:
        return go.Figure().add_annotation(text="No mismatches found", xref="paper", yref="paper", x=0.5, y=0.5)
    
    columns, counts = zip(*mismatch_data)
    
    fig = go.Figure(data=[
        go.Bar(x=list(columns), y=list(counts), marker_color='#dc3545')
    ])
    
    fig.update_layout(
        title="Mismatches by Column",
        xaxis_title="Column",
        yaxis_title="Mismatch Count",
        showlegend=False,
        height=300
    )
    
    return fig

def create_mismatch_pie_charts(column_stats, all_mismatches_df):
    """Create pie charts for mismatch analysis"""
    if not column_stats or all_mismatches_df.empty:
        return html.P("No mismatch data available.", className="text-muted")
    
    # Count mismatches by column
    mismatch_counts = {col['Column']: col['Mismatch Count'] for col in column_stats if col['Mismatch Count'] > 0}
    
    if not mismatch_counts:
        return html.P("No mismatches found in the comparison.", className="text-muted")
    
    # Create pie chart
    fig = go.Figure(data=[
        go.Pie(labels=list(mismatch_counts.keys()), values=list(mismatch_counts.values()))
    ])
    
    fig.update_layout(
        title="Mismatch Distribution by Column",
        height=400
    )
    
    return dcc.Graph(figure=fig)