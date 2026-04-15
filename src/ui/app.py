import sys
import os
from dotenv import load_dotenv
import streamlit as st

# 1. CRITICAL: Load environment variables BEFORE anything else
load_dotenv()

# Ensure the root project directory is in the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.ui.layout.sidebar import render_sidebar
from src.ui.layout.main_chat import render_main_chat

def inject_custom_css(is_dark=False):
    """
    Platinum Executive Design System (v2.0)
    A high-end, SaaS-inspired UI engine.
    """
    # Palette Definition
    if is_dark:
        bg = "#000000"
        surface = "#111111"
        border = "#1F1F1F"
        text = "#FFFFFF"
        subtext = "#A1A1AA"
        accent = "#3B82F6"
        shadow = "rgba(0,0,0,0.5)"
    else:
        bg = "#FFFFFF"
        surface = "#F9F9F9"
        border = "#E4E4E7"
        text = "#09090B"
        subtext = "#71717A"
        accent = "#2563EB"
        shadow = "rgba(0,0,0,0.03)"

    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');
        
        /* Reset & Base */
        .stApp {{
            background-color: {bg} !important;
            color: {text} !important;
        }}
        
        html, body, [class*="st-"] {{
            font-family: 'Inter', sans-serif;
            color: {text};
        }}

        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Instrument Sans', sans-serif !important;
            letter-spacing: -0.03em !important;
            font-weight: 600 !important;
            color: {text} !important;
        }}

        /* HIDE DEFAULT CLUTTER */
        [data-testid="stHeader"], [data-testid="stToolbar"] {{
            display: none !important;
        }}
        
        [data-testid="stSidebar"] {{
            background-color: {surface} !important;
            border-right: 1px solid {border} !important;
            padding-top: 2rem !important;
            width: 250px !important;
        }}
        
        [data-testid="stSidebarNav"] {{
            display: none !important;
        }}

        /* CUSTOM SIDEBAR BRANDING */
        .sidebar-title {{
            font-family: 'Instrument Sans', sans-serif;
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 2rem;
            padding: 0 1rem;
            text-align: left;
            letter-spacing: -2px;
        }}

        /* PLATINUM COMPONENTS */
        .stChatMessage {{
            background-color: {bg} !important;
            border: 1px solid {border} !important;
            border-radius: 8px !important;
            padding: 1.25rem !important;
            box-shadow: 0 4px 12px {shadow} !important;
            margin-bottom: 1.5rem !important;
        }}

        .stChatInputContainer {{
            background-color: {surface} !important;
            border: 1px solid {border} !important;
            border-radius: 99px !important;
            padding: 4px 12px !important;
            bottom: 20px !important;
            box-shadow: 0 10px 30px {shadow} !important;
            max-width: 800px !important;
            margin: 0 auto !important;
        }}
        
        .stChatInputContainer textarea {{
            color: {text} !important;
            font-size: 0.95rem !important;
            background-color: transparent !important;
        }}

        /* PREMIUM FILE UPLOADER */
        [data-testid="stFileUploadDropzone"] {{
            background-color: {surface} !important;
            border: 1px solid {border} !important;
            border-radius: 8px !important;
            transition: all 0.2s ease;
        }}
        
        [data-testid="stFileUploadDropzone"]:hover {{
            border-color: {accent} !important;
            background-color: {accent}05 !important;
        }}
        
        [data-testid="stFileUploadDropzone"] * {{
            color: {text} !important;
            font-size: 0.8rem !important;
        }}

        /* PLATINUM METRICS */
        [data-testid="stMetric"] {{
            background-color: {surface} !important;
            border: 1px solid {border} !important;
            padding: 1.5rem !important;
            border-radius: 12px !important;
        }}
        
        [data-testid="stMetricLabel"] {{
            color: {subtext} !important;
            font-size: 0.75rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            font-weight: 600 !important;
        }}
        
        [data-testid="stMetricValue"] {{
            font-family: 'Instrument Sans', sans-serif !important;
            color: {text} !important;
            font-weight: 700 !important;
            font-size: 2.5rem !important;
        }}

        /* BUTTONS */
        .stButton button {{
            background-color: {text} !important;
            color: {bg} !important;
            border: none !important;
            border-radius: 6px !important;
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            padding: 0.5rem 1rem !important;
            transition: opacity 0.2s;
        }}
        
        .stButton button:hover {{
            opacity: 0.9;
        }}

        /* TABS */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: transparent !important;
            gap: 2rem !important;
            border-bottom: 1px solid {border} !important;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            font-family: 'Instrument Sans', sans-serif !important;
            font-size: 0.9rem !important;
            color: {subtext} !important;
            font-weight: 500 !important;
            padding: 1rem 0 !important;
        }}
        
        .stTabs [aria-selected="true"] {{
            color: {text} !important;
            border-bottom-color: {text} !important;
        }}

        /* BADGES */
        .aura-badge {{
            background-color: {accent}10;
            color: {accent};
            border: 1px solid {accent}30;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
        }}

        </style>
    """, unsafe_allow_html=True)

def render_architect_profile():
    st.markdown("<h1 style='margin-top: 0;'>The Architect</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #71717A; border-left: 2px solid #E4E4E7; padding-left: 1rem; margin-bottom: 3rem;'>Pioneering high-precision data engines and multi-agent orchestration.</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2], gap="large")
    
    with col1:
        st.markdown(f"""
            <div style='padding: 2rem; background: #F9F9F9; border: 1px solid #E4E4E7; border-radius: 12px;'>
                <h2 style='margin: 0; font-size: 1.5rem;'>Vanshik Godeshwar</h2>
                <p style='font-size: 0.85rem; color: #71717A;'>AI Solutions Architect</p>
                <div style='margin-top: 1.5rem; display: flex; flex-wrap: wrap; gap: 8px;'>
                    <span class='aura-badge'>SVNIT SURAT</span>
                    <span class='aura-badge'>CANDIDATE MASTER</span>
                    <span class='aura-badge'>ICPC QUALIFIER</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        ### Strategic Profile
        Specialized in the convergence of **Competitive Algorithmic Design** and **Enterprise AI Systems**.
        - **B.Tech CSE**: SVNIT Surat (NIT Surat).
        - **Competitive Programming**: Rated 2100+ (Candidate Master) on Codeforces.
        - **Achievements**: Qualified for ICPC Regionals twice, ranking in the top percentiles globally.

        ### Execution Philosophy
        Aura is the culmination of years of algorithmic rigor and a deep-seated belief that data accessibility is the ultimate competitive advantage for the modern executive.
        """)

def render_product_docs():
    st.markdown("<h1 style='margin-top: 0;'>Technical Reference</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            readme_content = f.read()
            # Cleanly render with a custom container for better readability
            st.markdown(f"<div style='max-width: 800px;'>{readme_content}</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Documentation offline: {e}")

def main():
    st.set_page_config(
        page_title="Aura Executive",
        page_icon="💠",
        layout="wide"
    )
    
    # Theme Management
    if "is_dark" not in st.session_state:
        st.session_state.is_dark = False
        
    inject_custom_css(st.session_state.is_dark)
    
    with st.sidebar:
        st.markdown("<div class='sidebar-title'>AURA</div>", unsafe_allow_html=True)
        
        selection = st.radio(
            "Hub Select",
            ["Analytics Hub", "Tech Reference", "Architect Profile"],
            label_visibility="collapsed"
        )
        
        st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
        
        if selection == "Analytics Hub":
            render_sidebar()
            
        st.markdown("---")
        
        # Toggle with refined label
        theme_label = "Switch to Onyx" if not st.session_state.is_dark else "Switch to Platinum"
        if st.button(theme_label, use_container_width=True):
            st.session_state.is_dark = not st.session_state.is_dark
            st.rerun()

    # Main Rendering Container
    if selection == "Analytics Hub":
        render_main_chat()
    elif selection == "Tech Reference":
        render_product_docs()
    elif selection == "Architect Profile":
        render_architect_profile()

if __name__ == "__main__":
    main()
