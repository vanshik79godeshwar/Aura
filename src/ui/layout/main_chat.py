"""
Main chat interface layout module.
Why it exists: To act as the core interactive 'Talk-to-Data' surface where the user 
asks questions and receives fast, trustworthy insights.
"""
import streamlit as st
from src.ui.components.message_cards import render_message

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
        
        # Placeholder for agent response with mockup
        with st.chat_message("assistant"):
            if "plot" in prompt.lower() or "chart" in prompt.lower() or "data" in prompt.lower():
                import pandas as pd
                from src.agents.visualizer_agent import generate_visualization
                from src.ui.components.trust_trace import render_trust_trace

                st.markdown("Here is how I visualize your data using our brand theme:")
                
                # 1. Provide Mock Data
                df_mock = pd.DataFrame({
                    "Month": pd.date_range(start="2024-01-01", periods=6, freq="ME"),
                    "Revenue (M)": [12.4, 15.1, 14.8, 18.2, 21.0, 24.5]
                })

                # 2. Render Trust Trace Expander
                reasoning = [
                    "Identified intent: 'Visualize revenue trends'.",
                    "Extracted 'Revenue (M)' alongside datetime column 'Month'.",
                    "Time-series structure detected. Invoking VisualizerAgent with Line Chartheuristics."
                ]
                render_trust_trace(reasoning, df_mock)

                # 3. Generate Visualization
                fig = generate_visualization(df_mock)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Visualization generation failed for mock data.")

            else:
                st.markdown("I am running in UI-stub mode! Try asking me to **'show a plot'** or **'visualize data'** to see the new components in action.")
