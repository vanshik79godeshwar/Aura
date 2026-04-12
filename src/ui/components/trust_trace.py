"""
Trust Trace UI Component.
Why it exists: To fulfill the 'Trust' pillar by visually demonstrating the AI's 
reasoning and the exact data source subset it utilized, without cluttering the main UI.
"""
import streamlit as st
import pandas as pd
from typing import List, Optional

def render_trust_trace(reasoning_steps: List[str], source_data: Optional[pd.DataFrame] = None):
    """
    Renders an expandable section detailing how the AI reached its conclusion.
    Why it exists: Provides an auditable trace for the user while keeping the default view Minimal.
    """
    with st.expander("🔍 Trust Trace: How I got this answer"):
        st.markdown("**Reasoning Steps:**")
        for i, step in enumerate(reasoning_steps, 1):
            st.markdown(f"{i}. {step}")
            
        if source_data is not None and not source_data.empty:
            st.markdown("**Source Data Snippet:**")
            st.dataframe(source_data.head(), use_container_width=True)
            st.caption("Showing the top 5 relevant rows used to generate the answer.")
