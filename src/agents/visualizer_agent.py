"""
Visualizer Agent.
Why it exists: To automatically inspect data and determine the most appropriate
chart type (Plotly/Altair) for beautiful presentation, without user configuration (Minimal Steps).
"""
import pandas as pd
import plotly.express as px
from typing import Any

def generate_visualization(df: pd.DataFrame, chart_type: str = "Bar", chart_goal: str = "") -> Any:
    """
    Pure Executor: Renders the specific chart_type requested by the Supervisor.
    """
    if df is None or df.empty or chart_type == "None":
        return None
        
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()

    if not num_cols:
        return None

    # Determine X and Y based on data availability
    x_col = cat_cols[0] if cat_cols else (num_cols[1] if len(num_cols) > 1 else num_cols[0])
    y_col = num_cols[0]

    fig = None
    
    if chart_type == "Bar":
        fig = px.bar(df, x=x_col, y=y_col, title=chart_goal, color_discrete_sequence=['#00d4ff'])
    elif chart_type == "Line":
        fig = px.line(df, x=x_col, y=y_col, title=chart_goal, markers=True, color_discrete_sequence=['#ff4b4b'])
    elif chart_type == "Scatter":
        if len(num_cols) >= 2:
            fig = px.scatter(df, x=num_cols[0], y=num_cols[1], title=chart_goal, color_discrete_sequence=['#00d4ff'])
        else:
            fig = px.scatter(df, x=x_col, y=y_col, title=chart_goal, color_discrete_sequence=['#00d4ff'])
    elif chart_type == "Pie":
        fig = px.pie(df, names=x_col, values=y_col, title=chart_goal, color_discrete_sequence=px.colors.sequential.RdBu)
    
    if fig:
        _apply_theme(fig)
    
    return fig
        
    return None # Cannot visualize automatically

def _clean_axis_label(label: str) -> str:
    """Converts raw SQL column names / aggregation expressions to human-readable labels."""
    if not label:
        return label
    t = label.lower()
    # Strip common SQL aggregation wrappers
    for agg in ("sum(", "avg(", "count(", "min(", "max("):
        if t.startswith(agg) and t.endswith(")"):
            t = t[len(agg):-1]
    # Replace underscores / SQL AS aliases
    t = t.replace("_", " ").strip()
    # Append currency symbol for monetary columns
    if any(kw in t for kw in ("revenue", "amount", "price", "sales", "cost", "income")):
        return t.title() + " (₹)"
    return t.title()

def _apply_theme(fig):
    """
    Applies a clean, premium dark theme to every Plotly figure,
    and converts any raw SQL column names / aggregation strings into
    human-readable axis labels (e.g. 'sum(revenue)' → 'Revenue (₹)').
    """
    # Read whatever labels Plotly already assigned from the px call
    raw_x = (fig.layout.xaxis.title.text or "") if fig.layout.xaxis.title else ""
    raw_y = (fig.layout.yaxis.title.text or "") if fig.layout.yaxis.title else ""

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font=dict(family="Inter, sans-serif", size=14),
        hoverlabel=dict(bgcolor="rgba(0,0,0,0.8)", font_size=13, font_family="Inter"),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title=_clean_axis_label(raw_x),
        yaxis_title=_clean_axis_label(raw_y),
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(255,255,255,0.1)")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(255,255,255,0.1)")
