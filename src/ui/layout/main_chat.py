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
# REAL-TIME TRUST TRACE CAPTURE (Your original logic)
                    if "current_status" in state_update:
                        trust_steps.append(f"[{node_name}] {state_update['current_status']}")
                    if "error_logs" in state_update and state_update["error_logs"]:
                        # Append only the latest log entry
                        trust_steps.append(f"[{node_name}] Log: {state_update['error_logs'][-1]}")
                    
                    time.sleep(0.3) # Subtle "Thinking" feel for the demo speed pillar

            status.update(label="Analysis Complete", state="complete")
        
        # 1. PERSISTENT SOURCE FEEDBACK: Tell the user what tables we mapped
        if "relevant_tables" in final_state and final_state["relevant_tables"]:
            tables_list = ", ".join([f"**{t}**" for t in final_state["relevant_tables"]])
            retrieval_msg = f"🔍 I have identified the following relevant data sources: {tables_list}"
            st.session_state.messages.append({"role": "assistant", "content": retrieval_msg})
            render_message("assistant", retrieval_msg)

        # 2. RENDER THE COMPLETE TRUST TRACE
        if trust_steps:
            # Fix Dictionary Unpacking Crash cleanly natively
            raw_dict = final_state.get("raw_data")
            raw_df = None
            if isinstance(raw_dict, dict) and raw_dict.get("data") and raw_dict["data"] != "[]":
                import pandas as pd
                import io
                raw_df = pd.read_json(io.StringIO(raw_dict["data"]))
            elif getattr(raw_dict, "__class__", None) and raw_dict.__class__.__name__ == "DataFrame":
                raw_df = raw_dict
                
            render_trust_trace(trust_steps, raw_df)
            
        final_resp = final_state.get("final_response")
        visual_fig = final_state.get("visual_output")
        
        # Regex pull custom metrics logic if single numbers returned
        import re
        metric_match = re.search(r"\[METRIC:\s*([^\]]+)\]", final_resp) if final_resp else None
        
        # Task 1 & 3: Tabs and Metric/Visualization
        if raw_df is not None and not raw_df.empty:
            tab1, tab2 = st.tabs(["📊 Insight", "📂 Source Data"])
            
            with tab1:
                # Task 1: If it’s a single number, use a Big Number Metric Card
                # UI Styling Guardrail: Clean up the "Metric" display. Only show big number card if truly single value.
                if len(raw_df) == 1 and len(raw_df.columns) == 1:
                    col_name = "Metric" if metric_match else raw_df.columns[0].title().replace("_", " ")
                    val = raw_df.iloc[0, 0]
                    try:
                        disp_val = f"{float(val):,.2f}"
                        if any(kw in col_name.lower() for kw in ['price', 'amount', 'revenue', 'cost', '₹', '$']):
                            disp_val = f"₹{disp_val}" 
                        else:
                            disp_val = str(val) # Keep clean if not currency
                    except Exception:
                        disp_val = str(val)
                    
                    st.metric(label=col_name, value=disp_val, delta="Live Data")
                    
                    if final_resp:
                        cleaned_resp = re.sub(r"\[METRIC:\s*([^\]]+)\]", "", final_resp).strip()
                        from src.ui.components.message_cards import render_insight_card
                        render_insight_card(cleaned_resp)
                else:
                    if final_resp:
                        cleaned_resp = re.sub(r"\[METRIC:\s*([^\]]+)\]", "", final_resp).strip()
                        from src.ui.components.message_cards import render_insight_card
                        render_insight_card(cleaned_resp)
                        
                    if visual_fig is not None:
                        st.plotly_chart(visual_fig, width='stretch')
                    elif len(raw_df) > 1:
                        # Task 3: MANDATE a chart generation
                        from src.agents.visualizer_agent import generate_visualization
                        forced_fig = generate_visualization(raw_df, prompt)
                        if forced_fig:
                            st.plotly_chart(forced_fig, width='stretch')
                        else:
                            st.dataframe(raw_df, use_container_width=True)

            with tab2:
                # Task 3: Move "View Source Data" into a secondary tab so it doesn't clutter
                st.dataframe(raw_df, use_container_width=True)
        else:
             if final_resp:
                 from src.ui.components.message_cards import render_insight_card
                 render_insight_card(final_resp)
             if visual_fig is not None:
                 st.plotly_chart(visual_fig, width='stretch')
