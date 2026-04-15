"""
Message rendering components.
Why it exists: To format chat interactions cleanly, using ELI5 language (Clarity) 
and separating user queries from AI responses. 
"""
import streamlit as st

def render_message(role: str, content: str):
    """
    Platinum Message Card: Focused on pure signal.
    """
    is_dark = st.session_state.get("is_dark", False)
    text_color = "#FFFFFF" if is_dark else "#09090B"
    font_weight = "400"
    
    with st.chat_message(role):
        st.markdown(f"""
            <div style='font-family: "Inter", sans-serif; font-size: 0.92rem; line-height: 1.7; color: {text_color}; font-weight: {font_weight};'>
                {content}
            </div>
        """, unsafe_allow_html=True)

def render_insight_card(content: str):
    """
    Platinum Insight Card: Sharp, grounded intelligence summary.
    """
    is_dark = st.session_state.get("is_dark", False)
    text_color = "#FFFFFF" if is_dark else "#09090B"
    bg_color = "#111111" if is_dark else "#F9F9F9"
    border_color = "#1F1F1F" if is_dark else "#E4E4E7"
    accent = "#3B82F6" if is_dark else "#2563EB"
    
    st.markdown(f"""
        <div style='
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-left: 3px solid {accent};
            padding: 1.25rem 1.5rem;
            border-radius: 6px;
            margin: 1.5rem 0;
        '>
            <div style='font-family: "Instrument Sans", sans-serif; font-weight: 700; font-size: 0.65rem; color: {accent}; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.75rem; opacity: 0.9;'>
                Executive Summary
            </div>
            <div style='font-family: "Inter", sans-serif; font-size: 0.95rem; color: {text_color}; line-height: 1.6; font-weight: 400;'>
                {content}
            </div>
        </div>
    """, unsafe_allow_html=True)
