from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.workspace import AgentWorkspace

# Initialize the Gemini LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

def plan_execution(state: AgentWorkspace) -> dict:
    """Read user_query, extract entities, update identified_metrics, and decide next step."""
    query = state.get("user_query", "")
    
    # Prompt the LLM to extract metrics
    prompt = f"Extract key metrics or entities from this user query as a comma-separated list: {query}"
    response = llm.invoke(prompt)
    
    metrics_text = response.content if hasattr(response, 'content') else str(response)
    metrics = [m.strip() for m in metrics_text.split(",") if m.strip()]
    
    return {
        "identified_metrics": metrics,
        "current_status": "[plan_execution] executed"
    }

def lexicon(state: AgentWorkspace) -> dict:
    error_logs = list(state.get("error_logs", []))
    error_logs.append("[lexicon] executed")
    return {"current_status": "[lexicon] executed", "error_logs": error_logs}

def analyst(state: AgentWorkspace) -> dict:
    error_logs = list(state.get("error_logs", []))
    error_logs.append("[analyst] executed")
    return {"current_status": "[analyst] executed", "error_logs": error_logs}

def sentry(state: AgentWorkspace) -> dict:
    error_logs = list(state.get("error_logs", []))
    error_logs.append("[sentry] executed")
    return {"current_status": "[sentry] executed", "error_logs": error_logs}

def storyteller(state: AgentWorkspace) -> dict:
    error_logs = list(state.get("error_logs", []))
    error_logs.append("[storyteller] executed")
    return {"current_status": "[storyteller] executed", "error_logs": error_logs}

# Define and compile the state graph
workflow = StateGraph(AgentWorkspace)

# Add strict nodes
workflow.add_node("plan_execution", plan_execution)
workflow.add_node("lexicon", lexicon)
workflow.add_node("analyst", analyst)
workflow.add_node("sentry", sentry)
workflow.add_node("storyteller", storyteller)

# Define edges and conditional routing logic (linear path for now)
workflow.set_entry_point("plan_execution")
workflow.add_edge("plan_execution", "lexicon")
workflow.add_edge("lexicon", "analyst")
workflow.add_edge("analyst", "sentry")
workflow.add_edge("sentry", "storyteller")
workflow.add_edge("storyteller", END)

# Compile into app variable
app = workflow.compile()
