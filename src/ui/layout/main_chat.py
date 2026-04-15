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
    Platinum Chat Interface: Centered, high-fidelity experience.
    """
    # Create a centered column for the chat
    _, center_col, _ = st.columns([1, 4, 1])
    
    with center_col:
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "System online. **AURA Executive Intelligence** is stabilized. Ingest a dataset to begin strategic analysis."}
            ]

        # Display history
        for msg in st.session_state.messages:
            render_message(msg["role"], msg["content"])

        # Input Area (Floating effect is handled via CSS in app.py)
        if prompt := st.chat_input("Input command or query..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            render_message("user", prompt)
            
            with st.chat_message("assistant"):
                from src.core.registry import ContextRegistry
                from src.core.workspace import reset_execution_state
                
                initial_state: AgentWorkspace = {
                    "user_query": prompt,
                    "identified_metrics": [],
                    "relevant_tables": [],
                    "metadata_context": ContextRegistry().get_metadata_context(),
                    "logical_plan": {},
                    "sql_query": "",
                    "error_logs": [],
                    "current_status": "initialized",
                    "next_action": "",
                    "active_upload": st.session_state.get("active_upload", "")
                }
                initial_state = reset_execution_state(initial_state)

                import time
                final_state = initial_state.copy()
                
                # 💠 Platinum Intelligence Progress
                log_placeholder = st.empty()
                executed_steps = []
                
                def update_log(step_name):
                    is_dark = st.session_state.get("is_dark", False)
                    base_color = "#71717A" if not is_dark else "#A1A1AA"
                    sep_color = "#E4E4E7" if not is_dark else "#1F1F1F"
                    executed_steps.append(step_name)
                    breadcrumb_html = f"""
                    <div style='font-family: "Instrument Sans", sans-serif; font-size: 0.75rem; color: {base_color}; margin-bottom: 2.5rem; display: flex; align-items: center; gap: 10px; font-weight: 500;'>
                        {' <span style="color: {sep_color}; font-weight: 400;">/</span> '.join([f'<span>{s}</span>' for s in executed_steps])}
                        <span style='color: #2563EB; animation: pulse 2s infinite;'>●</span>
                    </div>
                    <style>
                    @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: .3; }} }}
                    </style>
                    """
                    log_placeholder.markdown(breadcrumb_html, unsafe_allow_html=True)

                update_log("STRATEGIC ROUTING")
                
                for output in aura_graph.stream(initial_state):
                    for node_name, state_update in output.items():
                        step_map = {
                            "lexicon": "SCHEMA PROFILING",
                            "supervisor": "LOGIC DECOMPOSITION",
                            "analyst_and_math": "EXECUTION VALIDATION",
                            "visualizer_and_storyteller": "INSIGHT SYNTHESIS"
                        }
                        if node_name in step_map:
                            update_log(step_map[node_name])
                        
                        final_state.update(state_update)
                        time.sleep(0.05)

                # Finalize Log with a clean checkmark
                is_dark = st.session_state.get("is_dark", False)
                sep_color = "#E4E4E7" if not is_dark else "#1F1F1F"
                log_placeholder.markdown(f"""
                    <div style='font-family: "Instrument Sans", sans-serif; font-size: 0.75rem; color: #71717A; margin-bottom: 2.5rem; font-weight: 500;'>
                        {' <span style="color: {sep_color}; font-weight: 400;">/</span> '.join([f'<span>{s}</span>' for s in executed_steps])}
                        <span style='color: #10B981; margin-left: 8px;'>✓</span>
                    </div>
                """, unsafe_allow_html=True)
            
            # POST-PROCESSING & RENDERING
            raw_dict = final_state.get("raw_data")
            raw_df = None
            if isinstance(raw_dict, dict) and raw_dict.get("data") and raw_dict["data"] != "[]":
                import pandas as pd
                import io
                raw_df = pd.read_json(io.StringIO(raw_dict["data"]))
            elif getattr(raw_dict, "__class__", None) and raw_dict.__class__.__name__ == "DataFrame":
                raw_df = raw_dict
                    
            final_resp = final_state.get("final_response")
            visual_fig = final_state.get("visual_output")
            supervisor_plan = final_state.get("supervisor_plan")

            import re
            metric_match = re.search(r"\[METRIC:\s*([^\]]+)\]", final_resp) if final_resp else None
            
            if raw_df is not None and not raw_df.empty:
                tab1, tab2 = st.tabs(["ANALYSIS", "SOURCE DATA"])
                
                with tab1:
                    if len(raw_df) == 1 and len(raw_df.columns) == 1:
                        col_name = "METRIC" if metric_match else raw_df.columns[0].upper()
                        val = raw_df.iloc[0, 0]
                        try:
                            disp_val = f"{float(val):,.2f}"
                            if any(kw in col_name.lower() for kw in ['price', 'amount', 'revenue', 'cost', '₹', '$']):
                                disp_val = f"₹{disp_val}" 
                            else:
                                disp_val = str(val)
                        except Exception:
                            disp_val = str(val)
                        
                        st.metric(label=col_name, value=disp_val)
                        
                        if final_resp:
                            cleaned_resp = re.sub(r"\[METRIC:\s*([^\]]+)\]", "", final_resp).strip()
                            render_insight_card(cleaned_resp)
                    else:
                        if final_resp:
                            cleaned_resp = re.sub(r"\[METRIC:\s*([^\]]+)\]", "", final_resp).strip()
                            render_insight_card(cleaned_resp)
                            
                        if visual_fig is not None:
                            st.plotly_chart(visual_fig, use_container_width=True)
                        elif len(raw_df) > 1:
                            from src.agents.visualizer_agent import generate_visualization
                            forced_fig = generate_visualization(raw_df, prompt)
                            if forced_fig:
                                st.plotly_chart(forced_fig, use_container_width=True)
                            else:
                                st.dataframe(raw_df, use_container_width=True, hide_index=True)

                with tab2:
                    st.dataframe(raw_df, use_container_width=True, hide_index=True)
                    if supervisor_plan:
                        st.markdown("### STRATEGIC PLAN")
                        st.caption(supervisor_plan)
            else:
                 if final_resp:
                     render_insight_card(final_resp)
                 if visual_fig is not None:
                     st.plotly_chart(visual_fig, use_container_width=True)
