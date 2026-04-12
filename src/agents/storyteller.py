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
    analysis_type = state.get("analysis_type", "standard")
    
    # FIX: Ensure we check both possible keys for the math results
    stats = state.get("statistical_payload", state.get("advanced_analytics_results", {}))
    
    fig = None
    response_text = ""
    
    try:
        # 1. Generate Visualization
        if raw_data is not None and not (isinstance(raw_data, pd.DataFrame) and raw_data.empty):
            fig = generate_visualization(raw_data, query)
            data_context = f"Retrieved relevant banking records."
        else:
            data_context = "No structural data retrieved."

        # 2. Invoke LLM for Executive Narrative (The "Aura" Voice)
        system_prompt = (
            f"You are the 'Storyteller' agent for NatWest Project Aura.\n"
            f"Your job is to provide 'Clarity' for business users.\n"
            f"User Query: {query}\n"
            f"Statistical Findings: {stats}\n\n"
            f"Write a concise, 1-2 sentence professional headline summarizing these findings."
        )
        
        response_msg = llm.invoke(system_prompt)
        response_text = response_msg.content
        error_logs.append("Storyteller synthesized statistical payload into an Executive Summary.")
        status = "completed successfully"

    except Exception as e:
        error_logs.append(f"[storyteller] Error: {str(e)}")
        response_text = "I've visualized the data for you, but I'm currently having trouble generating the narrative summary."
        status = "failed"
        
    return {
        "current_status": f"storyteller_complete",
        "error_logs": error_logs,
        "final_response": response_text,
        "visual_output": fig
    }