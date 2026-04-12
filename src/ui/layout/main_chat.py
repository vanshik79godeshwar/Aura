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

            import time
            from src.ui.components.trust_trace import render_trust_trace

            status = st.status("Thinking...", expanded=True)
            reasoning_steps = []
            
            final_state = initial_state.copy()
            trust_steps = ["Orchestrator Routing Logic Initiated"]
            for output in aura_graph.stream(initial_state):
                for node_name, state_update in output.items():
                    step_desc = f"Agent '{node_name}' executed. Status: {state_update.get('current_status', 'OK')}"
                    reasoning_steps.append(step_desc)
                    status.write(f"✓ {step_desc}")
                    
                    # Highlight relevant tables in the UI for clarity
                    if "relevant_tables" in state_update:
                        tables = state_update["relevant_tables"]
                        if tables:
                            tables_str = ", ".join([f"`{t}`" for t in tables])
                            status.write(f"🔍 **Top Relevant Tables Found:** {tables_str}")
                        else:
                            status.write("⚠️ No relevant tables found.")

                    final_state.update(state_update)
<<<<<<< HEAD
                    
                    if "current_status" in state_update:
                         trust_steps.append(f"[{node_name}] {state_update['current_status']}")
                    if "error_logs" in state_update and state_update["error_logs"]:
                         trust_steps.append(f"[{node_name}] Log: {state_update['error_logs'][-1]}")
            
            status.update(label="Analysis Complete", state="complete")
        
        render_trust_trace(trust_steps)
=======
                    time.sleep(0.5) # Artificial sleep for demo "Thinking" feel
            
            status.update(label="Analysis Complete", state="complete")

            # PERSISTENT CHAT OUTPUT: Show the tables found to the user
            if "relevant_tables" in final_state and final_state["relevant_tables"]:
                tables_list = ", ".join([f"**{t}**" for t in final_state["relevant_tables"]])
                retrieval_msg = f"🔍 I have identified the following relevant data sources for your query: {tables_list}"
                st.session_state.messages.append({"role": "assistant", "content": retrieval_msg})
                render_message("assistant", retrieval_msg)

            # Render the captured Trust Trace!
            if reasoning_steps:
                # Uses final_state raw data as the audit source
                render_trust_trace(reasoning_steps, final_state.get("raw_data"))
>>>>>>> 7a0750b34e85a6adeed8e823cb6955e10db52e5c
            
        if final_state.get("final_response"):
            from src.ui.components.message_cards import render_insight_card
            render_insight_card(final_state["final_response"])
            
        if final_state.get("visual_output") is not None:
            # We explicitly use Plotly here to ensure our theme renders.
            st.plotly_chart(final_state["visual_output"], use_container_width=True)
