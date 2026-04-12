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

            import time
            import pandas as pd
            from src.agents.visualizer_agent import generate_visualization
            from src.ui.components.trust_trace import render_trust_trace

            status = st.status("Thinking...", expanded=True)
            reasoning_steps = []
            
            # Execute LangGraph and capture the trace
            for output in aura_graph.stream(initial_state):
                for node_name, state_update in output.items():
                    step_desc = f"Agent '{node_name}' executed. Status: {state_update.get('current_status', 'OK')}"
                    reasoning_steps.append(step_desc)
                    status.write(f"✓ {step_desc}")
                    time.sleep(0.5) # Artificial sleep for demo "Thinking" feel
            
            status.update(label="Analysis Complete", state="complete")

            # Render the captured Trust Trace!
            if reasoning_steps:
                # Provide mock data since we don't have DuckDB payload yet
                df_mock = pd.DataFrame({
                    "Month": pd.date_range(start="2024-01-01", periods=6, freq="ME"),
                    "Revenue (M)": [12.4, 15.1, 14.8, 18.2, 21.0, 24.5]
                })
                # Add our final Storyteller conclusion to the top
                st.markdown("Here is the requested insight along with the core execution path.")
                render_trust_trace(reasoning_steps, df_mock)

                # Render our mockup visualization
                if "plot" in prompt.lower() or "chart" in prompt.lower() or "data" in prompt.lower():
                    fig = generate_visualization(df_mock)
                    if fig:
                        # Use Streamlit's native width property to avoid deprecation warnings
                        st.plotly_chart(fig)
