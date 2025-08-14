import dash
from dash import html, dash_table, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def create_comparison_section(results):
    """Create the comprehensive comparison results section with tabs"""
    if not results:
        return html.Div()
    
    return html.Div([
        # Summary metrics cards
        create_summary_metrics(results),
        
        # Main tabs section
        html.Div([
            dbc.Tabs([
                dbc.Tab(
                    label="Overview", 
                    tab_id="overview",
                    children=create_overview_tab(results)
                ),
                dbc.Tab(
                    label="Row Analysis", 
                    tab_id="row-analysis",
                    children=create_row_analysis_tab(results)
                ),
                dbc.Tab(
                    label="Column Analysis", 
                    tab_id="column-analysis",
                    children=create_column_analysis_tab(results)
                ),
                dbc.Tab(
                    label="Mismatch Details", 
                    tab_id="mismatch-details",
                    children=create_mismatch_details_tab(results)
                ),
                dbc.Tab(
                    label="Unique Rows", 
                    tab_id="unique-rows",
                    children=create_unique_rows_tab(results)
                )
            ], 
            id="comparison-tabs", 
            active_tab="overview",
            className="custom-tabs"
            )
        ], className="mt-4")
    ])

def create_summary_metrics(results):
    """Create comprehensive summary metrics cards"""
    
    # Get column counts
    base_cols = results.get('base_shape', [0, 0])[1] if results.get('base_shape') else 0
    compare_cols = results.get('compare_shape', [0, 0])[1] if results.get('compare_shape') else 0
    col_diff = abs(base_cols - compare_cols) if base_cols and compare_cols else 0
    
    # Get columns actually compared
    compared_cols = len(results.get('compared_columns', []))
    
    metrics = [
        # Row 1: Main dataset metrics
        {
            "title": "Base Dataset Rows",
            "value": results.get('base_rows', results.get('total_rows_base', 0)),
            "icon": "fas fa-database",
            "color": "primary"
        },
        {
            "title": "Compare Dataset Rows", 
            "value": results.get('compare_rows', results.get('total_rows_compare', 0)),
            "icon": "fas fa-database",
            "color": "primary"
        },
        {
            "title": "Match Rate",
            "value": f"{results.get('match_rate', 0):.1%}",
            "icon": "fas fa-percentage",
            "color": "success" if results.get('match_rate', 0) > 0.8 else "warning"
        },
        {
            "title": "Total Mismatches",
            "value": results.get('total_mismatches', 0),
            "icon": "fas fa-exclamation-triangle",
            "color": "warning"
        },
        
        # Row 2: Row-level analysis
        {
            "title": "Rows Only in Base",
            "value": results.get('base_only_rows', 0),
            "icon": "fas fa-minus-circle",
            "color": "info"
        },
        {
            "title": "Rows Only in Compare",
            "value": results.get('compare_only_rows', 0),
            "icon": "fas fa-plus-circle",
            "color": "info"
        },
        {
            "title": "Common Rows",
            "value": results.get('intersect_rows', 0),
            "icon": "fas fa-equals",
            "color": "success"
        },
        
        # Row 3: Column metrics
        {
            "title": "Base Columns | Compare Columns | Difference",
            "value": f"{base_cols} | {compare_cols} | {col_diff}",
            "icon": "fas fa-columns",
            "color": "secondary"
        },
        {
            "title": "Columns Compared",
            "value": compared_cols,
            "icon": "fas fa-check-circle",
            "color": "primary"
        },
        {
            "title": "Column Type Mismatches",
            "value": results.get('column_type_mismatches', 0),
            "icon": "fas fa-code",
            "color": "warning"
        }
    ]
    
    # Create rows of cards
    row1_cards = []
    row2_cards = []
    row3_cards = []
    
    # Row 1: 4 cards
    for i in range(4):
        if i < len(metrics):
            metric = metrics[i]
            card = create_metric_card(metric)
            row1_cards.append(dbc.Col(card, width=12, md=6, lg=3, className="mb-3"))
    
    # Row 2: 3 cards  
    for i in range(4, 7):
        if i < len(metrics):
            metric = metrics[i]
            card = create_metric_card(metric)
            row2_cards.append(dbc.Col(card, width=12, md=6, lg=4, className="mb-3"))
    
    # Row 3: 3 cards
    for i in range(7, 10):
        if i < len(metrics):
            metric = metrics[i]
            card = create_metric_card(metric)
            row3_cards.append(dbc.Col(card, width=12, md=6, lg=4, className="mb-3"))
    
    return html.Div([
        dbc.Row(row1_cards, className="mb-3"),
        dbc.Row(row2_cards, className="mb-3"), 
        dbc.Row(row3_cards, className="mb-3")
    ])

def create_metric_card(metric):
    """Create a single metric card"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"{metric['icon']} fa-2x text-{metric['color']} mb-2"),
                html.H6(metric['title'], className="card-title text-muted mb-2"),
                html.H3(
                    str(metric['value']) if not isinstance(metric['value'], int) else f"{metric['value']:,}", 
                    className="mb-0 fw-bold"
                )
            ], className="text-center")
        ])
    ], className="h-100 shadow-sm border-0 metric-card")

def create_overview_tab(results):
    """Create the overview tab content"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📊 Data Overview", className="mb-3"),
                        html.P("Comparison completed successfully!", className="text-success"),
                        html.Hr(),
                        html.H6("Dataset Information:", className="fw-bold mb-3"),
                        html.Ul([
                            html.Li(f"Base dataset: {results.get('base_shape', [0, 0])[0]:,} rows × {results.get('base_shape', [0, 0])[1]} columns"),
                            html.Li(f"Compare dataset: {results.get('compare_shape', [0, 0])[0]:,} rows × {results.get('compare_shape', [0, 0])[1]} columns"),
                            html.Li(f"Join columns: {', '.join(results.get('join_columns', []))}"),
                            html.Li(f"Compared columns: {len(results.get('compared_columns', []))}")
                        ]),
                        
                        html.Hr(),
                        html.H6("Match Statistics:", className="fw-bold mb-3"),
                        html.Ul([
                            html.Li(f"Rows in both datasets: {results.get('intersect_rows', 0):,}"),
                            html.Li(f"Rows only in base: {results.get('base_only_rows', 0):,}"),
                            html.Li(f"Rows only in compare: {results.get('compare_only_rows', 0):,}"),
                            html.Li(f"Overall match rate: {results.get('match_rate', 0):.1%}")
                        ])
                    ])
                ])
            ], width=6),
            dbc.Col([
                create_match_visualization(results)
            ], width=6)
        ])
    ], fluid=True, className="p-3")

def create_row_analysis_tab(results):
    """Create the row analysis tab content"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Row-Level Analysis")),
                    dbc.CardBody([
                        html.H6("Row Comparison Summary:", className="mb-3"),
                        dash_table.DataTable(
                            data=[
                                {"Metric": "Total Rows in Base", "Count": results.get('base_rows', 0)},
                                {"Metric": "Total Rows in Compare", "Count": results.get('compare_rows', 0)},
                                {"Metric": "Rows in Both (Intersection)", "Count": results.get('intersect_rows', 0)},
                                {"Metric": "Rows Only in Base", "Count": results.get('base_only_rows', 0)},
                                {"Metric": "Rows Only in Compare", "Count": results.get('compare_only_rows', 0)},
                                {"Metric": "Matching Rows", "Count": results.get('matching_rows', 0)},
                                {"Metric": "Mismatched Rows", "Count": results.get('mismatched_rows', 0)}
                            ],
                            columns=[
                                {"name": "Metric", "id": "Metric"},
                                {"name": "Count", "id": "Count", "type": "numeric", "format": {"specifier": ","}}
                            ],
                            style_cell={'textAlign': 'left'},
                            style_data_conditional=[
                                {
                                    'if': {'filter_query': '{Count} > 0 and {Metric} contains "Only"'},
                                    'background_color': '#fff3cd',
                                    'color': 'black',
                                },
                                {
                                    'if': {'filter_query': '{Metric} contains "Matching"'},
                                    'background_color': '#d1edff',
                                    'color': 'black',
                                }
                            ]
                        )
                    ])
                ])
            ], width=12)
        ])
    ], fluid=True, className="p-3")

def create_column_analysis_tab(results):
    """Create the column analysis tab with bar chart and connected table"""
    column_stats = results.get('column_stats', {})
    
    if not column_stats:
        return html.Div("No column statistics available", className="p-3")
    
    # Prepare data for table and chart
    table_data = []
    chart_data = []
    
    for col, stats in column_stats.items():
        row = {
            "Column": col,
            "Match Count": stats.get('match_count', 0),
            "Mismatch Count": stats.get('mismatch_count', 0),
            "Match Rate": f"{stats.get('match_rate', 0):.1%}",
            "Base Datatype": stats.get('base_dtype', 'N/A'),
            "Compare Datatype": stats.get('compare_dtype', 'N/A'),
            "Base Nulls": stats.get('base_nulls', 0),
            "Compare Nulls": stats.get('compare_nulls', 0)
        }
        table_data.append(row)
        
        chart_data.append({
            "Column": col,
            "Match": stats.get('match_count', 0),
            "Mismatch": stats.get('mismatch_count', 0)
        })
    
    # Create bar chart
    chart_df = pd.DataFrame(chart_data)
    fig = px.bar(
        chart_df.melt(id_vars=['Column'], value_vars=['Match', 'Mismatch']),
        x='Column', y='value', color='variable',
        title="Match vs Mismatch Count by Column",
        labels={'value': 'Count', 'variable': 'Type'},
        color_discrete_map={'Match': '#28a745', 'Mismatch': '#dc3545'}
    )
    fig.update_layout(height=400)
    
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Column Match/Mismatch Chart")),
                    dbc.CardBody([
                        dcc.Graph(
                            id="column-analysis-chart",
                            figure=fig
                        )
                    ])
                ])
            ], width=12, className="mb-4")
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Column Analysis Details")),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id="column-analysis-table",
                            data=table_data,
                            columns=[
                                {"name": "Column", "id": "Column"},
                                {"name": "Match Count", "id": "Match Count", "type": "numeric"},
                                {"name": "Mismatch Count", "id": "Mismatch Count", "type": "numeric"},
                                {"name": "Match Rate", "id": "Match Rate"},
                                {"name": "Base Datatype", "id": "Base Datatype"},
                                {"name": "Compare Datatype", "id": "Compare Datatype"},
                                {"name": "Base Nulls", "id": "Base Nulls", "type": "numeric"},
                                {"name": "Compare Nulls", "id": "Compare Nulls", "type": "numeric"}
                            ],
                            style_cell={'textAlign': 'left'},
                            style_data_conditional=[
                                {
                                    'if': {'filter_query': '{Mismatch Count} > 0'},
                                    'background_color': '#ffe6e6',
                                    'color': 'black',
                                },
                                {
                                    'if': {'filter_query': '{Base Datatype} != {Compare Datatype}'},
                                    'background_color': '#fff3cd',
                                    'color': 'black',
                                }
                            ],
                            sort_action="native",
                            filter_action="native",
                            page_size=20
                        )
                    ])
                ])
            ], width=12)
        ])
    ], fluid=True, className="p-3")

def create_mismatch_details_tab(results):
    """Create the mismatch details tab with pie chart and connected table"""
    mismatch_details = results.get('mismatch_details', [])
    
    if not mismatch_details:
        return html.Div("No mismatch details available", className="p-3")
    
    # Count mismatches by column for pie chart
    mismatch_counts = {}
    for detail in mismatch_details:
        col = detail.get('column', 'Unknown')
        mismatch_counts[col] = mismatch_counts.get(col, 0) + 1
    
    # Create pie chart
    fig = px.pie(
        values=list(mismatch_counts.values()),
        names=list(mismatch_counts.keys()),
        title="Mismatch Distribution by Column"
    )
    fig.update_layout(height=400)
    
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Mismatch Distribution")),
                    dbc.CardBody([
                        dcc.Graph(
                            id="mismatch-pie-chart",
                            figure=fig
                        )
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Mismatch Summary")),
                    dbc.CardBody([
                        html.H6(f"Total Mismatches: {len(mismatch_details)}", className="text-danger"),
                        html.H6(f"Affected Columns: {len(mismatch_counts)}", className="text-warning"),
                        html.Hr(),
                        html.H6("Top Mismatch Columns:", className="mb-2"),
                        html.Ul([
                            html.Li(f"{col}: {count} mismatches") 
                            for col, count in sorted(mismatch_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                        ])
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Detailed Mismatch Records")),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id="mismatch-details-table",
                            data=mismatch_details[:1000],  # Limit to first 1000 for performance
                            columns=[{"name": i, "id": i} for i in (mismatch_details[0].keys() if mismatch_details else [])],
                            style_cell={'textAlign': 'left'},
                            sort_action="native",
                            filter_action="native",
                            page_size=20
                        )
                    ])
                ])
            ], width=12)
        ])
    ], fluid=True, className="p-3")

def create_unique_rows_tab(results):
    """Create the unique rows tab with separate tables for base and compare"""
    base_only = results.get('base_only_data', [])
    compare_only = results.get('compare_only_data', [])
    
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5(f"Rows Only in Base Dataset ({len(base_only)} rows)")),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id="base-only-table",
                            data=base_only[:500] if base_only else [],  # Limit for performance
                            columns=[{"name": i, "id": i} for i in (base_only[0].keys() if base_only else [])],
                            style_cell={'textAlign': 'left'},
                            sort_action="native",
                            filter_action="native",
                            page_size=10
                        ) if base_only else html.P("No unique rows in base dataset", className="text-muted")
                    ])
                ])
            ], width=12, className="mb-4")
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5(f"Rows Only in Compare Dataset ({len(compare_only)} rows)")),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id="compare-only-table",
                            data=compare_only[:500] if compare_only else [],  # Limit for performance
                            columns=[{"name": i, "id": i} for i in (compare_only[0].keys() if compare_only else [])],
                            style_cell={'textAlign': 'left'},
                            sort_action="native",
                            filter_action="native",
                            page_size=10
                        ) if compare_only else html.P("No unique rows in compare dataset", className="text-muted")
                    ])
                ])
            ], width=12)
        ])
    ], fluid=True, className="p-3")

def create_match_visualization(results):
    """Create a visualization for match statistics"""
    data = [
        {"Category": "Matching Rows", "Count": results.get('matching_rows', 0)},
        {"Category": "Mismatched Rows", "Count": results.get('mismatched_rows', 0)},
        {"Category": "Base Only", "Count": results.get('base_only_rows', 0)},
        {"Category": "Compare Only", "Count": results.get('compare_only_rows', 0)}
    ]
    
    fig = px.bar(
        data, x='Category', y='Count',
        title="Row Comparison Results",
        color='Category',
        color_discrete_map={
            'Matching Rows': '#28a745',
            'Mismatched Rows': '#dc3545', 
            'Base Only': '#17a2b8',
            'Compare Only': '#fd7e14'
        }
    )
    fig.update_layout(height=300, showlegend=False)
    
    return dbc.Card([
        dbc.CardHeader(html.H6("Match Statistics Visualization")),
        dbc.CardBody([
            dcc.Graph(figure=fig)
        ])
    ])