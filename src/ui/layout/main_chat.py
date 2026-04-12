"""
Main chat interface layout module.
Why it exists: To act as the core interactive 'Talk-to-Data' surface where the user 
asks questions and receives fast, trustworthy insights.
"""
import streamlit as st
from src.ui.components.message_cards import render_message
from src.agents.orchestrator import app as aura_graph
from src.core.workspace import AgentWorkspace

def render_main_chat():
    """
    Renders the primary chat container and input controls.
    Why it exists: To orchestrate the stream of messages between the user and the Aura agents.
    """
    # Initialize chat history if not present
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Welcome to Project Aura! How can I help you analyze your data today?"}
        ]

    # Display chat messages from history
    for msg in st.session_state.messages:
        render_message(msg["role"], msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask me anything about your data..."):
        # Add user message to state
        st.session_state.messages.append({"role": "user", "content": prompt})
        render_message("user", prompt)
        
        with st.chat_message("assistant"):
            initial_state: AgentWorkspace = {
                "user_query": prompt,
                "identified_metrics": [],
                "sql_query": "",
                "error_logs": [],
                "current_status": "initialized",
                "next_action": ""
            }

            status = st.status("Processing Request...", expanded=True)
            
            for output in aura_graph.stream(initial_state):
                for node_name, state_update in output.items():
                    status.write(f"✓ Agent **{node_name}** executed.")
            
            status.update(label="Analysis Complete", state="complete")
