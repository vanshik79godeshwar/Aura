"""
Data visualization components.
Why it exists: To provide transparent and accurate tabular/graphical views of the source data, 
ensuring the 'Trust' pillar is upheld.
"""
import streamlit as st
import pandas as pd

def show_data_preview(df: pd.DataFrame, title: str = "Data Preview"):
    """
    Renders a clean, readable dataframe preview.
    Why it exists: To let the user verify the data being analyzed without feeling overwhelmed.
    """
    st.subheader(title)
    st.dataframe(df, use_container_width=True)
