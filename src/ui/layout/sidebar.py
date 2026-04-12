"""
Sidebar layout module.
Why it exists: To hold tools, settings, and file uploads, keeping the main chat clear
for a focused user experience (Clarity pillar).
"""
import streamlit as st

def render_sidebar():
    """
    Renders the sidebar components.
    Why it exists: To organize system configurations and data inputs in one place.
    """
    with st.sidebar:
        st.title("Aura Settings")
        st.markdown("We keep things simple. Just upload your data and start talking.")
        
        uploaded_file = st.file_uploader("Data Source", type=["csv", "xlsx"], label_visibility="hidden")
        
        st.markdown("---")
        if uploaded_file:
            st.success(f"✅ Ready: {uploaded_file.name}")
        else:
            st.info("Waiting for data source...")
