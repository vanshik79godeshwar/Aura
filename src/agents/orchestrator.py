from typing import Literal
from src.core.workspace import AgentWorkspace

from src.agents.oracle import call_oracle as call_semantic_layer
from src.agents.analyst import call_analyst

# ---------------------------------------------------------
# Worker Agent Dummy Nodes (Sentry & Storyteller)
# ---------------------------------------------------------

def call_sentry(state: AgentWorkspace) -> dict:
    """Validates data and queries for correctness and security."""
    print("Agent [Sentry]: Validating execution...")
    return {"current_status": "sentry_complete"}

def call_storyteller(state: AgentWorkspace) -> dict:
    """Crafts the final natural language response based on data."""
    print("Agent [Storyteller]: Crafting response...")
    return {"current_status": "storyteller_complete"}

# ---------------------------------------------------------
# Conditional Routing Logic
# ---------------------------------------------------------

MAX_RETRIES = 3

def route_after_analyst(state: AgentWorkspace) -> Literal["call_analyst", "call_storyteller"]:
    """
    If call_analyst populates error_logs, route back to call_analyst 
    for self-correction up to MAX_RETRIES.
    Otherwise, route to call_storyteller.
    """
    errors = state.get("error_logs", [])
    retries = state.get("retry_count", 0)

    if errors and retries < MAX_RETRIES:
        print(f"Orchestrator: Error detected. Routing to Analyst for self-correction. (Retry {retries + 1}/{MAX_RETRIES})")
        return "call_analyst"
    
    print("Orchestrator: Query successful or max retries hit. Routing to Storyteller.")
    return "call_storyteller"

# ---------------------------------------------------------
# Sample State Graph Configuration (e.g. for LangGraph)
# ---------------------------------------------------------
"""
from langgraph.graph import StateGraph, END

# Initialize the Master Agent routing logic
workflow = StateGraph(AgentWorkspace)

# Add nodes
workflow.add_node("semantic_layer", call_semantic_layer)
workflow.add_node("analyst", call_analyst)
workflow.add_node("sentry", call_sentry)
workflow.add_node("storyteller", call_storyteller)

# Define routing
workflow.set_entry_point("semantic_layer")
workflow.add_edge("semantic_layer", "analyst")

workflow.add_conditional_edges(
    "analyst",
    route_after_analyst,
    {
        "call_analyst": "analyst",
        "call_storyteller": "storyteller" 
        # Alternatively, route to sentry first before storyteller
    }
)

workflow.add_edge("storyteller", END)

# compile to create the master orchestrator application
app = workflow.compile()
"""
