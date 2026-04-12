from typing import Literal
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.workspace import AgentWorkspace


# Initialize the Gemini LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

class OrchestratorDecision(BaseModel):
    next_action: Literal["lexicon", "analyst", "storyteller", "END"] = Field(
        description="The next step in the pipeline."
    )

def plan_execution(state: AgentWorkspace) -> dict:
    """The LLM router decides the next immediate step based on execution state."""
    query = state.get("user_query", "")
    metrics = state.get("identified_metrics", [])
    sql = state.get("sql_query", "")

    errors = state.get("error_logs", [])
    
    prompt = (
        f"Look at the user_query and the error_logs.\n"
        f"User Query: {query}\n"
        f"Identified Metrics: {metrics}\n"
        f"SQL Query: {sql}\n"
        f"Error Logs: {errors}\n\n"
        "If we haven't mapped metrics yet, route to 'lexicon'. "
        "If metrics are mapped but no SQL exists, route to 'analyst'. "
        "If analysis is done, route to 'storyteller'."
    )
    
    # Use Pydantic structured output
    structured_llm = llm.with_structured_output(OrchestratorDecision)
    decision = structured_llm.invoke(prompt)
    
    print(f"Agent [plan_execution] routed to: {decision.next_action}")
    return {
        "next_action": decision.next_action,
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

def route(state: AgentWorkspace) -> str:
    """Routing function that reads next_action from state."""
    action = state.get("next_action", "END")
    if action == "END":
        return END
    return action

# Define and compile the state graph
workflow = StateGraph(AgentWorkspace)

# Add strict nodes
workflow.add_node("plan_execution", plan_execution)
workflow.add_node("lexicon", lexicon)
workflow.add_node("analyst", analyst)
workflow.add_node("sentry", sentry)
workflow.add_node("storyteller", storyteller)

# Define conditional edges
workflow.set_entry_point("plan_execution")
workflow.add_conditional_edges("plan_execution", route)

# For graph to compile correctly, other nodes lead to END
workflow.add_edge("lexicon", END)
workflow.add_edge("analyst", END)
workflow.add_edge("sentry", END)
workflow.add_edge("storyteller", END)

# Compile into app variable
app = workflow.compile()
