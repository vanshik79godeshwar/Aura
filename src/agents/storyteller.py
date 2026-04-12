from src.core.workspace import AgentWorkspace
from src.agents.visualizer_agent import generate_visualization
import pandas as pd
from langchain_groq import ChatGroq

# Initialize the Groq LLM for Storyteller Narrative Generation
# Note: Requires GROQ_API_KEY in the environment
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.3, # Slightly creative for better storytelling
    max_retries=2
)

def run_storyteller(state: AgentWorkspace) -> dict:
    """
    Renders the final conversational text using an LLM to evaluate statistical findings
    and triggers the visualizer logic if numerical data requires graphing.
    """
    error_logs = list(state.get("error_logs", []))
    raw_data = state.get("raw_data")
    query = state.get("user_query", "")
    analysis_type = state.get("analysis_type", "standard")
    stats = state.get("statistical_payload", {})
    
    fig = None
    response_text = ""
    
    try:
        # 1. Generate Visualization
        if raw_data is not None and not raw_data.empty:
            fig = generate_visualization(raw_data, query)
            data_context = f"Retrieved table with {len(raw_data)} rows."
        else:
            data_context = "No structural data retrieved."

        # 2. Invoke LLM for ELI5 Narrative Formulation
        system_prompt = (
            f"You are the 'Storyteller' agent for a NatWest Talk-to-Data enterprise system.\n"
            f"Your job is to provide 'Clarity' (Explain Like I'm 5) for business users.\n"
            f"User Query: {query}\n"
            f"Analysis Type Performed: {analysis_type}\n"
            f"Data Context: {data_context}\n"
            f"Raw Mathematical/Statistical Payload from Backend: {stats}\n\n"
            f"Write a concise, professional, yet very easy-to-understand response summarizing the findings "
            f"based on the statistical payload and data context. Do NOT output raw math code, translate it to business logic."
        )
        
        response_msg = llm.invoke(system_prompt)
        response_text = response_msg.content
        
        error_logs.append(f"[storyteller] narrative formed via LLM for {analysis_type} intent")
        status = "completed successfully"

    except Exception as e:
        error_logs.append(f"[storyteller] failed running narrative LLM or visualizer: {str(e)}")
        # Graceful fallback logic so the UI doesn't crash if Groq API rate limits
        if raw_data is not None and not raw_data.empty:     
            fig = generate_visualization(raw_data, query)
            response_text = "I've pulled the relevant records from the database and visualized them for you. (Narrative Engine Offline)"
        else:
            response_text = "I ran into a problem fetching both the data and the narrative formatter."
        status = "failed"
        
    return {
        "current_status": f"[storyteller] {status}",
        "error_logs": error_logs,
        "final_response": response_text,
        "visual_output": fig
    }
