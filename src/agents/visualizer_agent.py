"""
Visualizer Agent.
Why it exists: To automatically inspect data and determine the most appropriate
chart type (Plotly/Altair) for beautiful presentation, without user configuration (Minimal Steps).
"""
import pandas as pd
import plotly.express as px
from typing import Any

def generate_visualization(df: pd.DataFrame, context_query: str = "") -> Any:
    """
    Heuristically determines and returns a Plotly figure based on the dataframe structure.
    Why it exists: Takes the ownership of output styling so the core data agents just return DataFrames.
    """
    # Defensive programming: handle empty or invalid data
    if df is None or df.empty:
        return None
        
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
    date_cols = df.select_dtypes(include=['datetime']).columns.tolist()

    # Rule 1: Time series data -> Line chart
    if date_cols and num_cols:
        x_col = date_cols[0]
        y_col = num_cols[0]
        color_col = cat_cols[0] if cat_cols else None
        
        # NatWest theme approximation (Purple/Red core, subtle backgrounds)
        fig = px.line(df, x=x_col, y=y_col, color=color_col, 
                      title=f"{y_col} over Time",
                      color_discrete_sequence=px.colors.qualitative.Prism)
        _apply_theme(fig)
        return fig
        
    # Rule 2: Categorical + Numeric -> Bar chart
    if cat_cols and num_cols:
        x_col = cat_cols[0]
        y_col = num_cols[0]
        
        # Check cardinality: if too many categories, maybe a horizontal bar
        if df[x_col].nunique() > 10:
            fig = px.bar(df, x=y_col, y=x_col, orientation='h', 
                         title=f"{y_col} by {x_col}",
                         color_discrete_sequence=['#42145F']) # NatWest Purple
        else:
            fig = px.bar(df, x=x_col, y=y_col, 
                         title=f"{y_col} by {x_col}",
                         color_discrete_sequence=['#42145F']) 
        _apply_theme(fig)
        return fig
        
    # Rule 3: Only Numerics -> Scatter plot
    if len(num_cols) >= 2:
        fig = px.scatter(df, x=num_cols[0], y=num_cols[1], 
                         title=f"Correlation: {num_cols[0]} vs {num_cols[1]}",
                         color_discrete_sequence=['#42145F', '#8A1B61']) # Purple & Magenta
        _apply_theme(fig)
        return fig
        
    return None # Cannot visualize automatically

def _apply_theme(fig):
    """
    Applies a clean, premium visual theme to Plotly figures.
    Why it exists: To ensure consistent, "Pretty" outputs across the application.
    """
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=14),
        hoverlabel=dict(bgcolor="white", font_size=13, font_family="Inter"),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.2)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.2)')
