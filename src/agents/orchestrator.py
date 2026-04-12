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
    next_action: Literal["metadata_retriever", "analyst_and_math", "sql_sentry", "visualizer_and_storyteller", "END"] = Field(
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
        "If metrics are mapped but no SQL exists, route to 'analyst_and_math'. "
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
    try:
        from src.agents.metadata_retriever import run_retriever
        return run_retriever(state)
    except Exception as e:
        error_logs = list(state.get("error_logs", []))
        error_logs.append(f"[metadata_retriever] fallback or error: {str(e)}")
        return {"current_status": "[metadata_retriever] executed via fallback", "error_logs": error_logs}


def analyst_and_math(state: AgentWorkspace) -> dict:
    try:
        from src.agents.oracle import run_analyst
        return run_analyst(state)
    except Exception as e:
        import pandas as pd
        error_logs = list(state.get("error_logs", []))
        error_logs.append(f"[analyst_and_math] fallback or error: {str(e)}")
        mock_df = pd.DataFrame({"merchant": ["Starbucks", "Tesco", "Uber", "Amazon"], "total_amount": [45.50, 120.00, 15.00, 150.00]})
        return {"current_status": "[analyst_and_math] executed via fallback", "error_logs": error_logs, "raw_data": mock_df}

def sql_sentry(state: AgentWorkspace) -> dict:
    try:
        from src.agents.sql_sentry import run_sentry
        return run_sentry(state)
    except Exception as e:
        error_logs = list(state.get("error_logs", []))
        error_logs.append(f"[sql_sentry] fallback or error: {str(e)}")
        return {"current_status": "[sql_sentry] executed via fallback", "error_logs": error_logs}

def visualizer_and_storyteller(state: AgentWorkspace) -> dict:
    try:
        from src.agents.visualizer_agent import generate_visualization
        from src.agents.storyteller import run_storyteller
        return run_storyteller(state)
    except Exception as e:
        import plotly.express as px
        error_logs = list(state.get("error_logs", []))
        error_logs.append(f"[visualizer_and_storyteller] fallback or error: {str(e)}")
        raw_data = state.get("raw_data")
        fig = None
        if raw_data is not None and not raw_data.empty:
            fig = px.bar(raw_data, x="merchant", y="total_amount")
        return {
            "current_status": "[visualizer_and_storyteller] executed via fallback", 
            "error_logs": error_logs, 
            "final_response": "Here is the comparison breakdown. Starbucks and Amazon represent your highest outflows.", 
            "visual_output": fig
        }

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
workflow.add_node("metadata_retriever", metadata_retriever)
workflow.add_node("analyst_and_math", analyst_and_math)
workflow.add_node("sql_sentry", sql_sentry)
workflow.add_node("visualizer_and_storyteller", visualizer_and_storyteller)

# Define routing
workflow.set_entry_point("plan_execution")

# Conditional jumper based on LLM intent inference
workflow.add_conditional_edges("plan_execution", route)

# Definitive analytical pipeline flow ensuring Sentries evaluate Analysts before visual output
workflow.add_edge("metadata_retriever", "analyst_and_math")
workflow.add_edge("analyst_and_math", "sql_sentry")
workflow.add_edge("sql_sentry", "visualizer_and_storyteller")
workflow.add_edge("visualizer_and_storyteller", END)

# Compile into app variable
app = workflow.compile()
