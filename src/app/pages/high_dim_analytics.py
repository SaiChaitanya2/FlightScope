from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import duckdb
import pandas as pd
from functools import lru_cache
from src.pipeline.config import DB_PATH

@lru_cache(maxsize=32)
def get_umap_data(month=None, origin_state=None, dest_state=None, origin_airport=None, dest_airport=None):
    """Fetches a sample of flights, filtered by month, state, and airport."""
    conn = duckdb.connect(DB_PATH, read_only=True)
    
    # We select rowid as flight_id so we can track specific points across callbacks
    # We select an analytical row_number window function to use as a flight_id since rowid isn't stable across parquet reads
    base_query = """
        SELECT row_number() OVER () AS flight_id, UMAP_1, UMAP_2, UMAP_3, Origin_Dep_Congestion, 
               Operating_Airline, ArrDelay, Month, TaxiOut, DepDelay, Distance, AirTime
        FROM read_parquet('data/processed/processed_flights_with_umap.parquet')
        WHERE UMAP_1 IS NOT NULL AND UMAP_2 IS NOT NULL AND UMAP_3 IS NOT NULL
    """
    
    if month:
        base_query += f" AND Month = {month}"
    if origin_state:
        base_query += f" AND OriginState = '{origin_state}'"
    if dest_state:
        base_query += f" AND DestState = '{dest_state}'"
    if origin_airport:
        base_query += f" AND Origin = '{origin_airport}'"
    if dest_airport:
        base_query += f" AND Dest = '{dest_airport}'"
        
    final_query = f"SELECT * FROM ({base_query}) USING SAMPLE 5000"
    
    df = conn.execute(final_query).df()
    conn.close()
    return df

def create_layout():
    return dbc.Container([
        dcc.Store(id="hd-selected-flights-store", data=[]),
        dbc.Row([
            dbc.Col([
                html.H1("High-Dimensional Analytics", 
                         style={"color": "#ffffff", "fontWeight": "700", "fontSize": "2.2rem", "letterSpacing": "-0.025em"}, className="mb-1"),
                html.P("Exploring complex delay topologies using UMAP and Parallel Coordinates.", 
                        style={"color": "#64748b", "fontSize": "1rem"}, className="mb-3"),
            ], width=12)
        ], className="mb-3 mt-1"),
        
        # NEW: KPI Cards Row
        # NEW: Compact KPI Bar
        dbc.Row([
            dbc.Col(
                html.Div([
                    html.Span("Flights in View:  ", className="text-muted ms-3"),
                    html.Span(id="hd-kpi-flights", className="text-primary fw-bold me-4 fs-5"),
                    
                    html.Span("Avg Arrival Delay:  ", className="text-muted"),
                    html.Span(id="hd-kpi-arr-delay", className="text-warning fw-bold me-4 fs-5"),
                    
                    html.Span("Avg Taxi-Out:  ", className="text-muted"),
                    html.Span(id="hd-kpi-taxi-out", className="text-info fw-bold me-4 fs-5"),
                    
                    html.Span("Max Delay in Cluster:  ", className="text-muted"),
                    html.Span(id="hd-kpi-max-delay", className="text-danger fw-bold fs-5")
                ], className="d-flex align-items-center py-2 mb-4 shadow-sm rounded", style={"backgroundColor": "#151722"}), 
            width=12)
        ]),
        
        dbc.Row([
            # LEFT COLUMN: Vertical Slider
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Month", className="mb-4 text-center", style={"color": "#ffffff"}),
                        html.Div(
                            dcc.Slider(
                                id='month-slider',
                                min=1, max=12, step=1,
                                marks={
                                    i: {
                                        'label': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][i-1],
                                        'style': {'color': '#94a3b8', 'fontSize': '14px', 'paddingLeft': '15px'}
                                    } for i in range(1, 13)
                                },
                                value=1, 
                                included=False,
                                vertical=True
                            ),
                            style={"height": "60vh", "paddingLeft": "15%"} 
                        )
                    ])
                ], className="shadow-sm border-0 h-100", style={"backgroundColor": "#151722"})
            ], width=1),
            
            # MIDDLE COLUMN: UMAP Graph
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H5("Delay Clusters (3D UMAP)", className="mb-0", style={"color": "#ffffff"}),
                            # NEW: Color By Dropdown for Interactive recoloring
                            html.Div([
                                dbc.Button("Clear Selection", id="clear-umap-selection", size="sm", className="me-2", outline=True, color="secondary"),
                                dcc.Dropdown(
                                    id="color-by-dropdown",
                                    options=[
                                        {"label": "Airport Congestion", "value": "Origin_Dep_Congestion"},
                                        {"label": "Arrival Delay", "value": "ArrDelay"},
                                        {"label": "Distance", "value": "Distance"},
                                        {"label": "Operating Airline", "value": "Operating_Airline"}
                                    ],
                                    value="Origin_Dep_Congestion",
                                    clearable=False,
                                    style={"width": "200px", "color": "#111111"}
                                )
                            ], className="d-flex align-items-center")
                        ], className="d-flex justify-content-between align-items-center mb-3"),
                        dcc.Graph(id="umap-scatter-plot", style={"height": "75vh"})
                    ])
                ], className="shadow-sm border-0 h-100", style={"backgroundColor": "#151722"})
            ], width=6),
            
            # RIGHT COLUMN: Parallel Coordinates Graph
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Multivariate Delay Flow", className="mb-3", style={"color": "#ffffff"}),
                        dcc.Graph(id="parallel-coords-plot", style={"height": "75vh"})
                    ])
                ], className="shadow-sm border-0 h-100", style={"backgroundColor": "#151722"})
            ], width=5)
            
        ], className="mb-4 align-items-stretch") 
        
    ], fluid=True, id="aditi-view-container", style={"backgroundColor": "#0c0d12", "minHeight": "100vh", "padding": "20px"})

layout = create_layout()
@callback(
    [
        Output("umap-scatter-plot", "figure"),
        Output("parallel-coords-plot", "figure"),
        Output("hd-kpi-flights", "children"),
        Output("hd-kpi-arr-delay", "children"),
        Output("hd-kpi-taxi-out", "children"),
        Output("hd-kpi-max-delay", "children")
    ],
    [
        Input("month-slider", "value"),
        Input("global-route-store", "data"),
        Input("color-by-dropdown", "value"),
        Input("hd-selected-flights-store", "data")
    ]
)
def update_graphs(selected_month, route_data, color_by, selected_flight_ids):
    try:
        route_data = route_data or {}
        origin_state = route_data.get("origin_state", "")
        dest_state = route_data.get("dest_state", "")
        origin_airport = route_data.get("origin_airport", "")
        dest_airport = route_data.get("dest_airport", "")
        
        df = get_umap_data(selected_month, origin_state, dest_state, origin_airport, dest_airport).copy()
        
        if df.empty:
            empty_fig = px.scatter_3d(title="No Data Available")
            empty_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"))
            return empty_fig, empty_fig, "0", "0m", "0m", "0m"

        kpi_flights = f"{len(df):,}"
        kpi_arr_delay = f"{df['ArrDelay'].mean():.1f}m"
        kpi_taxi = f"{df['TaxiOut'].mean():.1f}m"
        kpi_max = f"{df['ArrDelay'].max():.0f}m"

        df['marker_size'] = 4
        if selected_flight_ids:
            df.loc[df['flight_id'].isin(selected_flight_ids), 'marker_size'] = 15

        # Cap scales to saturate the colors and avoid outlier washout
        if color_by == "Origin_Dep_Congestion":
            custom_range = [0, 25]
        elif color_by == "ArrDelay":
            df["ArrDelay"] = df["ArrDelay"].fillna(0)
            custom_range = [-15, 90]  # Cap arrival delay between -15m and 90m to reveal structure
        else:
            custom_range = None

        # 1. Update UMAP Figure
        umap_fig = px.scatter_3d(
            df, x='UMAP_1', y='UMAP_2', z='UMAP_3',
            color=color_by,
            size='marker_size',
            size_max=15,
            hover_data=['Operating_Airline', 'ArrDelay'],
            custom_data=['flight_id'], 
            color_continuous_scale="Plasma",
            color_discrete_sequence=px.colors.qualitative.Alphabet,
            range_color=custom_range,
            opacity=1.0,
            labels={'Origin_Dep_Congestion': 'Congestion'},
            template="plotly_dark"
        )
            
        umap_fig.update_layout(
            uirevision="constant",
            margin=dict(l=0, r=0, t=30, b=40), 
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0"),
            scene=dict(
                xaxis=dict(title="UMAP X", gridcolor="#475569", backgroundcolor="rgba(0,0,0,0)"),
                yaxis=dict(title="UMAP Y", gridcolor="#475569", backgroundcolor="rgba(0,0,0,0)"),
                zaxis=dict(title="UMAP Z", gridcolor="#475569", backgroundcolor="rgba(0,0,0,0)")
            ),
            showlegend=(color_by == "Operating_Airline"),
            coloraxis_colorbar=dict(
                thickness=15,
                x=0.95, 
                outlinewidth=0
            )
        )
        
        # Remove the default white borders around the points that obscure colors in dense clusters
        umap_fig.update_traces(marker=dict(line=dict(width=0)))
        
        # 2. Update Parallel Coordinates Figure
        pc_df = df
            
        pc_color = color_by if color_by != "Operating_Airline" else "ArrDelay"
        
        if selected_flight_ids:
            pc_df['is_selected'] = pc_df['flight_id'].isin(selected_flight_ids).astype(float)
            pc_color = 'is_selected'
            pc_custom_range = [0, 1]
        else:
            pc_custom_range = custom_range
            if color_by == "Operating_Airline":
                pc_custom_range = [-15, 90] # Fallback since pc_color is ArrDelay
            
        pc_df = pc_df.sort_values(by=pc_color, ascending=True)
        
        pc_fig = px.parallel_coordinates(
            pc_df, 
            dimensions=['Distance', 'TaxiOut', 'DepDelay', 'AirTime', 'ArrDelay'],
            color=pc_color,
            color_continuous_scale="Plasma",
            range_color=pc_custom_range,
            labels={
                'Origin_Dep_Congestion': 'Congestion',
                'Distance': 'Dist (mi)',
                'TaxiOut': 'Taxi (m)',
                'DepDelay': 'Dep (m)',
                'AirTime': 'Air (m)',
                'ArrDelay': 'Arr (m)'
            },
            template="plotly_dark"
        )

        pc_fig.update_layout(
            margin=dict(l=50, r=5, t=65, b=20), 
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0"),
            coloraxis_colorbar=dict(
                thickness=15,
                x=1.05,
                outlinewidth=0
            )
        )
        
        return umap_fig, pc_fig, kpi_flights, kpi_arr_delay, kpi_taxi, kpi_max
    except Exception as e:
        import traceback
        with open("C:/Users/Chait/FlightScope/callback_error.log", "w") as f:
            f.write(traceback.format_exc())
        raise e

@callback(
    Output("hd-selected-flights-store", "data"),
    [
        Input("umap-scatter-plot", "selectedData"),
        Input("umap-scatter-plot", "clickData"),
        Input("clear-umap-selection", "n_clicks")
    ],
    prevent_initial_call=True
)
def update_store(selectedData, clickData, n_clicks):
    import dash
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
        
    trigger_id = ctx.triggered[0]["prop_id"]
    
    if "clear-umap-selection" in trigger_id:
        return []
        
    if "selectedData" in trigger_id and selectedData and "points" in selectedData:
        if len(selectedData["points"]) > 0:
            return [p["customdata"][0] for p in selectedData["points"] if "customdata" in p]
        return dash.no_update
        
    if "clickData" in trigger_id and clickData and "points" in clickData and len(clickData["points"]) > 0:
        point = clickData["points"][0]
        if "customdata" in point:
            return [point["customdata"][0]]
            
    return dash.no_update