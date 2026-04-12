"""
Main entry point for the Project Aura UI.
Why it exists: To provide the top-level Streamlit configuration and orchestration 
for the Talk-to-Data interface, prioritizing Clarity, Trust, and Speed for NatWest Hackathon users.
"""

import sys
import os
from dotenv import load_dotenv

# 1. CRITICAL: Load environment variables BEFORE anything else
load_dotenv()

import streamlit as st
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
    
    st.title("Aura Intelligence")
    st.caption("Powered by NatWest")
    
    # Task 3: Modern Layout Custom CSS (Inter font, rounded edges, shadows)
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
        html, body, [class*="st-"] {
            font-family: 'Inter', sans-serif;
        }
        .stChatInputContainer {
            border-radius: 12px;
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05);
            border: 1px solid #30363d !important;
            background-color: #0d1117 !important;
        }
        .stChatMessage {
            border-radius: 10px;
            box-shadow: 0px 2px 6px rgba(0,0,0,0.03);
            margin-bottom: 12px;
            border: 1px solid #30363d !important;
            background-color: #0d1117 !important;
        }
        [data-testid="stMetric"] {
            border: 1px solid #30363d !important;
            background-color: #0d1117 !important;
            border-radius: 10px;
            padding: 10px 20px;
        }
        [data-testid="stMetricValue"] {
            font-size: 3rem !important;
            font-weight: bold;
        }
        [data-testid="stSidebar"] {
            box-shadow: 2px 0px 10px rgba(0,0,0,0.05);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Render the layouts
    render_sidebar()
    render_main_chat()

if __name__ == "__main__":
    main()
