"""
Trust Trace UI Component.
Why it exists: To fulfill the 'Trust' pillar by visually demonstrating the AI's 
reasoning and the exact data source subset it utilized, without cluttering the main UI.
"""
import streamlit as st
import pandas as pd
from typing import List, Optional

def render_trust_trace(steps, source_data=None):
    # Pure DataFrame constraint: Unwraps safely without AttributeError crashes!
    is_valid_df = isinstance(source_data, pd.DataFrame) and not source_data.empty

    with st.expander("🔍 Trust Trace: How I got this answer", expanded=True):
        for step in steps:
            st.markdown(f"**{step}**")