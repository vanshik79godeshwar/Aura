"""
Main chat interface layout module.
Why it exists: To act as the core interactive 'Talk-to-Data' surface where the user 
asks questions and receives fast, trustworthy insights.
"""
import streamlit as st
from src.ui.components.message_cards import render_message
from src.ui.components.trust_trace import render_trust_trace
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
                "relevant_tables": [],
                "sql_query": "",
                "error_logs": [],
                "current_status": "initialized",
                "next_action": ""
            }

            status = st.status("Processing Request...", expanded=True)
            
            final_state = initial_state.copy()
            trust_steps = ["Orchestrator Routing Logic Initiated"]
            for output in aura_graph.stream(initial_state):
                for node_name, state_update in output.items():
                    status.write(f"✓ Agent **{node_name}** executed.")
                    final_state.update(state_update)
                    
                    if "current_status" in state_update:
                         trust_steps.append(f"[{node_name}] {state_update['current_status']}")
                    if "error_logs" in state_update and state_update["error_logs"]:
                         trust_steps.append(f"[{node_name}] Log: {state_update['error_logs'][-1]}")
            
            status.update(label="Analysis Complete", state="complete")
        
        render_trust_trace(trust_steps)
            
        if final_state.get("final_response"):
            st.markdown(final_state["final_response"])
            
        if final_state.get("visual_output") is not None:
            st.plotly_chart(final_state["visual_output"], use_container_width=True)
            
        if final_state.get("raw_data") is not None:
            with st.expander("View Source Data"):
                st.dataframe(final_state["raw_data"])
