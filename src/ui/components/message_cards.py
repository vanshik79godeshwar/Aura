"""
Message rendering components.
Why it exists: To format chat interactions cleanly, using ELI5 language (Clarity) 
and separating user queries from AI responses. 
"""
import streamlit as st

def render_message(role: str, content: str):
    """
    Renders a single chat message using Streamlit's native chat UI.
    Why it exists: To maintain a consistent, easy-to-read style for all conversation history.
    """
    with st.chat_message(role):
        st.markdown(content)
