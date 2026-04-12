from typing import Dict, Any
from langchain_groq import ChatGroq
from src.core.workspace import AgentWorkspace

def run_storyteller(state: AgentWorkspace) -> Dict[str, Any]:
    """
    Storyteller Agent.
    Generates an executive summary based on the statistical payload natively.
    """
    stats_payload = state.get("statistical_payload", state.get("advanced_analytics_results", {}))
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, max_retries=3)
    
    prompt = (
        f"Using the following statistical payload, write a 1-sentence headline for the user.\n"
        f"Example: 'Starbucks represents 27% of your total merchant spend.'\n\n"
        f"Payload:\n{stats_payload}\n\n"
        f"Headline:"
    )
    
    try:
        response = llm.invoke(prompt)
        narrative = response.content.strip()
    except Exception as e:
        narrative = f"Could not generate headline. Error: {e}"
        
    error_logs = state.get("error_logs", [])
    error_logs.append("Storyteller synthesized statistical payload into an Executive Summary.")
    
    return {
        "final_response": narrative,
        "error_logs": error_logs,
        "current_status": "storyteller_complete"
    }
