from src.core.workspace import AgentWorkspace
from src.agents.visualizer_agent import generate_visualization
import pandas as pd
from langchain_groq import ChatGroq

# Initialize the Groq LLM for Storyteller Narrative Generation
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.3,
    max_retries=2
)

def run_storyteller(state: AgentWorkspace) -> dict:
    error_logs = list(state.get("error_logs", []))
    raw_data = state.get("raw_data")
    query = state.get("user_query", "")
    
    # Supervisor Instructions
    refined_plan = state.get("supervisor_plan", "Executing standard analysis.")
    visual_instr = state.get("visualizer_instructions", "Viewing retrieved data.")
    chart_type = state.get("target_chart_type", "Bar")

    import io
    if isinstance(raw_data, dict):
        raw_data = pd.read_json(io.StringIO(raw_data.get('data', '[]')))

    stats = state.get("statistical_payload", state.get("advanced_analytics_results", {}))

    fig = None
    response_text = ""

    routing = state.get("routing_decision", "SQL_REQUIRED")

    try:
        # 1. Generate Visualization as Pure Executor
        # RULE: If we have data, we visualize. Regardless of routing flag.
        if raw_data is not None and not (isinstance(raw_data, pd.DataFrame) and raw_data.empty):
            fig = generate_visualization(raw_data, chart_type=chart_type, chart_goal=visual_instr)
            data_context = raw_data.to_string(index=False)
        else:
            # For INTERPRETATION_ONLY or empty data, pull from Registry
            data_context = state.get("metadata_context", "No data passport context available.")

        is_single_value = False
        single_val = ""
        if raw_data is not None and not raw_data.empty and raw_data.shape == (1, 1):
            is_single_value = True
            single_val = str(raw_data.iloc[0, 0])

        system_prompt = (
            f"You are the 'Business Intelligence & Narratives Lead' (Storyteller) for Project Aura.\n"
            f"Your job is to summarize the findings for the user based on the Supervisor's plan.\n\n"
            f"SUPERVISOR PLAN:\n{refined_plan}\n\n"
            f"USER QUERY: {query}\n"
            f"STATISTICAL FINDINGS: {stats}\n\n"
            f"DATA CONTEXT:\n{data_context}\n\n"
            f"Write a professional executive summary. If the routing was 'INTERPRETATION_ONLY', explain the table schema and statistics from the context. "
            f"If SQL was used, report the exact numbers. ABSOLUTE RULE: Never use placeholders like ₹X. Use exact values from the context."
        )

        if is_single_value:
            system_prompt += f"\n\nInclude [METRIC: {single_val}] verbatim for the UI card."

        response_msg = llm.invoke(system_prompt)
        response_text = response_msg.content
        error_logs.append("Storyteller finalized the business narrative.")

    except Exception as e:
        error_logs.append(f"[storyteller] Error: {str(e)}")
        response_text = "Analysis complete. I've visualized the findings based on the supervisor's instructions."

    return {
        "current_status": "storyteller_complete",
        "error_logs": error_logs,
        "final_response": response_text,
        "visual_output": fig,
        "supervisor_plan": refined_plan # Ensure it's returned for the UI
    }