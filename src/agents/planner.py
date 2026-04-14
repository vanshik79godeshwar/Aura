import json
from typing import Dict, Any, List
from langchain_groq import ChatGroq

from src.core.workspace import AgentWorkspace

_FALLBACK_PLAN = {
    "intent_type": "Aggregation",
    "target_columns": [],
    "selected_tables": [],
    "group_by_required": False,
    "visualization_suggestion": "Bar"
}

def call_planner(state: AgentWorkspace) -> Dict[str, Any]:
    """
    Strategic Planner Node — JSON Mode.
    Determines the logic structure strictly based on User Query and Grounding String without writing unverified SQL.
    Uses plain .invoke() + json.loads() instead of structured output / function calling,
    which is more stable for Llama-3 on Groq when handling multiple tables.
    """
    query = state.get("user_query", "")
    metadata_context = state.get("metadata_context", "")
    active_upload = state.get("active_upload", "")
    priority_instruction = ""
    if active_upload:
        priority_instruction = f"\nIMPORTANT: The user just uploaded '{active_upload}'. Prioritize this table for any 'describe' or 'statistics' requests. Ignore other tables unless the user explicitly names them.\n"

    print("Agent [Planner]: Analyzing Request & System Metadata...")

    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, max_retries=3)

    prompt = f"""You are the core Logic Engine for a Talk-to-Data Architecture.
Your objective is to read the JIT Metadata Context and produce a declarative logical plan for data retrieval, WITHOUT writing actual SQL code.
{priority_instruction}
USER REQUEST: {query}

JIT METADATA REGISTRY CONTEXT:
{metadata_context}

RULES:
1. Identify the 'intent_type'. Choose one of: Scalar, Aggregation, Breakdown, Forecasting.
   If the user asks for a "Breakdown", "Split", or "By X", choose "Breakdown" and set 'group_by_required' to true.
2. Select 'target_columns' using ONLY the exact column names present in the JIT METADATA REGISTRY CONTEXT above.
   Do NOT invent names like 'transaction_amount' if the context says 'amount'.
3. Select 'selected_tables' by picking ONLY the table names from the context that actually host these columns.
4. Set 'visualization_suggestion' to one of: Metric, Bar, Line, Table. Single total values map to 'Metric'.
5. Respond ONLY with a raw JSON object. Do not include markdown code fences, backticks, or any extra text.
6. DATA VALIDATION: If the user request relates to entities, concepts, or tables that are NOT explicitly defined in the JIT METADATA REGISTRY CONTEXT (e.g., asking for 'amazon' OR 'products' when you only have 'sales_data' with 'revenue'), you MUST set 'intent_type': "Error" and leave all other fields empty/false. DO NOT try to fulfill the request using unrelated tables like 'sales_data' just because it's available.

Return exactly this JSON shape:
{{
  "intent_type": "...",
  "target_columns": [...],
  "selected_tables": [...],
  "group_by_required": true | false,
  "visualization_suggestion": "..."
}}
"""
    for attempt in range(3):
        try:
            msg = llm.invoke(prompt)
            raw = msg.content.strip()

            # Strip accidental markdown fences
            if raw.startswith("```json"):
                raw = raw[7:]
            elif raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

            plan = json.loads(raw)
            print(f"Agent [Planner] Logged Intent: {plan.get('intent_type')} | Group By: {plan.get('group_by_required')} | Tables: {plan.get('selected_tables')}")
            return {
                "logical_plan": plan,
                "current_status": "planner_complete"
            }
        except Exception as e:
            print(f"Agent [Planner] Attempt {attempt + 1} failed: {e}")

    # Hard fallback — pass an empty plan so downstream nodes can still attempt a query
    print("Agent [Planner] All retries exhausted. Using fallback plan.")
    error_logs = state.get("error_logs", [])
    error_logs.append("Strategic Planner: JSON parsing failed after 3 attempts. Using fallback plan.")
    return {
        "logical_plan": _FALLBACK_PLAN,
        "error_logs": error_logs,
        "current_status": "planner_error"
    }
