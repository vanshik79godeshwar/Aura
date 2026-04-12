"""
Main entry point for the Project Aura UI.
Why it exists: To provide the top-level Streamlit configuration and orchestration 
for the Talk-to-Data interface, prioritizing Clarity, Trust, and Speed for NatWest Hackathon users.
"""
import streamlit as st
import sys
import os
from dotenv import load_dotenv

# Ensure the root project directory is in the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.ui.layout.sidebar import render_sidebar
from src.ui.layout.main_chat import render_main_chat

def main():
    """
    Initializes and runs the Streamlit application.
    Why it exists: To set up the page layout and combine the sidebar and main chat views.
    """
    # Load environment variables (Security guideline)
    load_dotenv()
    
    # Configure the page for a premium, fast look (Pillars: Speed, Clarity)
    st.set_page_config(
        page_title="Project Aura",
        page_icon="✨",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("✨ Project Aura: Talk-to-Data")
    
    # Render the layouts
    render_sidebar()
    render_main_chat()

if __name__ == "__main__":
    main()
