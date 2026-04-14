from typing import Literal
import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Resolve .env from project root regardless of working directory
_ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(_ENV_PATH))

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.workspace import AgentWorkspace
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    max_retries=3
)
from src.agents.oracle import lexicon
from src.agents.analyst import call_analyst as analyst


class OrchestratorDecision(BaseModel):
    next_action: Literal["metadata_retriever", "planner", "analyst_and_math", "sql_sentry", "visualizer_and_storyteller", "END"] = Field(
        description="The next step in the pipeline."
    )
    analysis_type: Literal['standard', 'rca', 'forecast', 'comparison'] = Field(
        description="The semantic classification intent based on user query."
    )

def plan_execution(state: AgentWorkspace) -> dict:
    """The LLM router acts as an Oracle. It classifies the intent and dictates insertion point."""
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
        "Determine the 'analysis_type' ('standard', 'rca', 'forecast', or 'comparison') based on the query intent.\n"
        "If we haven't mapped metrics yet, route to 'metadata_retriever'. "
        "If metrics are mapped but no SQL exists, route to 'planner'. "
        "If analysis is working but hasn't been audited, route to 'sql_sentry'. "
        "If data and auditing are completed, route to 'visualizer_and_storyteller'."
    )
    
    structured_llm = llm.with_structured_output(OrchestratorDecision)
    decision = structured_llm.invoke(prompt)
    
    print(f"Agent [plan_execution] classed {decision.analysis_type} and routed to: {decision.next_action}")
    return {
        "next_action": decision.next_action,
        "analysis_type": decision.analysis_type,
        "current_status": f"[plan_execution] routed to {decision.next_action}"
    }

# ----------------- Worker Wrapper Functions -----------------
# Implementing the Grand Merge logic by calling team files gracefully.
# NOTE: LangGraph state TypedDict allows holding pandas DataFrames directly, seamlessly
# accepting Meet's auto-mocked data without breaking transition definitions.

def metadata_retriever(state: AgentWorkspace) -> dict:
    from src.agents.oracle import lexicon
    return lexicon(state)

def analyst_and_math(state: AgentWorkspace) -> dict:
    from src.agents.analyst import call_analyst
    return call_analyst(state)

def sql_sentry(state: AgentWorkspace) -> dict:
    if state.get("current_status") == "analyst_error":
        # Pass immediately to prevent infinite correction loops on empty DB
        return {"sentry_status": "PASS", "current_status": "sql_sentry skipped"}

    from src.agents.sql_sentry import SQLSentry
    auditor = SQLSentry()
    res = auditor.analyze_query(state.get("sql_query", ""), state.get("relevant_tables", []), state.get("metadata_context", ""))
    
    error_logs = state.get("error_logs", [])
    if res.get("status") == "PASS":
        error_logs.append("Audit Approval: SQL Execution authorized by Sentry.")
    else:
        reason = res.get('reason')
        previous_reasons = [log for log in error_logs if reason in log]
        error_logs.append(f"Correction Reason: {reason} (Hint: {res.get('correction_hint')})")
        
    # Orchestrator Logic Guardrail: Self-Correction Loop for Breakdown vs Single Value
    query = state.get("user_query", "").lower()
    needs_breakdown = any(w in query for w in ["breakdown", "by", "distribution", "split", "per"])
    sql_text = state.get("sql_query", "").upper()
    if needs_breakdown and "GROUP BY" not in sql_text:
        error_logs.append("Correction Reason: The user requested a breakdown, but a single scalar was returned instead of grouped data.")
        return {
            "current_status": "sql_sentry complete",
            "sentry_status": "FAIL",
            "sentry_reason": "You must include a GROUP BY clause and a categorical column because the user asked for a breakdown.",
            "error_logs": error_logs
        }
        
    if res.get("status") != "PASS":
        # Loop Breaker Task: Intercept duplicate failures and re-sync natively!
        if len(previous_reasons) > 0:
            return {
                "current_status": "sentry_loop_detected",
                "sentry_status": "FAIL",
                "sentry_reason": reason,
                "error_logs": error_logs,
                "next_action": "metadata_retriever"
            }
        
    return {
        "current_status": "sql_sentry complete",
        "sentry_status": res.get("status", "FAIL"),
        "sentry_reason": res.get("reason", ""),
        "sentry_correction": res.get("correction_hint", ""),
        "error_logs": error_logs
    }

def visualizer_and_storyteller(state: AgentWorkspace) -> dict:
    from src.agents.storyteller import run_storyteller
    
    # Intercept missing data graceful exit
    if any("LIVE DATABASE EMPTY" in err for err in state.get("error_logs", [])):
        return {
            "current_status": "error_resolved",
            "final_response": "Please upload your data first.",
            "visual_output": None
        }

    # Otherwise let the united storyteller & visualizer handle it natively
    return run_storyteller(state)

def route(state: AgentWorkspace) -> str:
    """Routing function that reads next_action from state."""
    action = state.get("next_action", "END")
    
    # Task 1: Ban the transition back to metadata_retriever once a SQL query has been successfully executed.
    if action == "metadata_retriever" and state.get("sql_query", "") != "":
        return "visualizer_and_storyteller"
        
    if action == "planner" and state.get("sql_query", "") != "":
        return "visualizer_and_storyteller"
        
    if state.get("current_status") == "analyst_complete":
        return "visualizer_and_storyteller"
        
    if action == "END":
        return END
    return action

def route_sentry(state: AgentWorkspace) -> str:
    """Conditional self-healing loop: Route back to analyst if Sentry catches hallucinated syntax."""
    status = state.get("sentry_status", "PASS")
    current_status = state.get("current_status", "")
    retries = state.get("retry_count", 0)
    
    if current_status == "sentry_loop_detected":
        return "metadata_retriever"
    
    # Send it to Visualizer if Audit clears. 
    # BUT explicitly force it if we are stuck in an infinite query glitch! (Max 3 retries).
    if status == "PASS" or retries >= 3:
        return "visualizer_and_storyteller"
        
    return "analyst_and_math"

from src.agents.supervisor import call_supervisor

def route_supervisor(state: AgentWorkspace) -> str:
    """Routes based on the Supervisor's decision."""
    decision = state.get("routing_decision", "SQL_REQUIRED")
    if decision == "INTERPRETATION_ONLY":
        return "visualizer_and_storyteller"
    return "analyst_and_math"

def supervisor(state: AgentWorkspace) -> dict:
    # Build Data Passport if not exists or if we want fresh context
    from src.core.registry import ContextRegistry
    registry = ContextRegistry()
    registry.build_registry()
    state["metadata_context"] = registry.get_metadata_context()
    
    return call_supervisor(state)

# Define and compile the state graph
workflow = StateGraph(AgentWorkspace)

# Add nodes
workflow.add_node("metadata_retriever", metadata_retriever)
workflow.add_node("supervisor", supervisor)
workflow.add_node("analyst_and_math", analyst_and_math)
workflow.add_node("sql_sentry", sql_sentry)
workflow.add_node("visualizer_and_storyteller", visualizer_and_storyteller)

# Define routing
workflow.set_entry_point("metadata_retriever")

# Flow: Retriever -> Supervisor -> (Analyst -> Sentry -> Storyteller) OR (Storyteller)
workflow.add_edge("metadata_retriever", "supervisor")

workflow.add_conditional_edges("supervisor", route_supervisor, {
    "visualizer_and_storyteller": "visualizer_and_storyteller",
    "analyst_and_math": "analyst_and_math"
})

workflow.add_edge("analyst_and_math", "sql_sentry")
workflow.add_conditional_edges("sql_sentry", route_sentry, {
    "metadata_retriever": "metadata_retriever",
    "visualizer_and_storyteller": "visualizer_and_storyteller",
    "analyst_and_math": "analyst_and_math"
})

workflow.add_edge("visualizer_and_storyteller", END)

# Compile into app variable
app = workflow.compile()
