import os
import sys

# Ensure project root is in PYTHONPATH
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.agents.orchestrator import app as aura_graph
from src.core.workspace import AgentWorkspace
from src.core.registry import ContextRegistry

def run_verification():
    print("=== AUTOMATED VERIFICATION PROTOCOL ===")
    
    import shutil
    registry = ContextRegistry()
    registry.build_registry()
    
    initial_state: AgentWorkspace = {
        "user_query": "Give me a breakdown of transaction amounts by merchant name",
        "identified_metrics": [],
        "relevant_tables": ["transactions"],
        "metadata_context": registry.get_metadata_context(),
        "logical_plan": {},
        "sql_query": "",
        "error_logs": [],
        "current_status": "test_initialized",
        "next_action": ""
    }

    final_state = initial_state.copy()
    
    print("Executing Graph for Breakdown Query...")
    for output in aura_graph.stream(initial_state):
        for node_name, state_update in output.items():
            final_state.update(state_update)

    sql_query = final_state.get("sql_query", "").upper()
    raw_data = final_state.get("raw_data")

    import pandas as pd
    import io

    df = None
    if isinstance(raw_data, dict) and raw_data.get("data") and raw_data["data"] != "[]":
        try:
            df = pd.read_json(io.StringIO(raw_data["data"]))
        except Exception:
            pass
    elif getattr(raw_data, "__class__", None) and raw_data.__class__.__name__ == "DataFrame":
        df = raw_data

    print(f"\nGenerative SQL Payload: {sql_query}")

    # Check 1: Verify GROUP BY clause
    if "GROUP BY" not in sql_query:
        print("\n[VALIDATION FAILED] Evaluated SQL does not contain 'GROUP BY' despite Breakdown Intent.")
        sys.exit(1)

    # Check 2: Breakdown MUST return >= 2 columns (category col + at least one aggregation)
    if df is None or df.empty:
        print("\n[VALIDATION FAILED] DataFrame output is empty.")
        sys.exit(1)

    if df.shape[1] < 2:
        print(f"\n[VALIDATION FAILED] Breakdown query returned only {df.shape[1]} column(s). "
              f"A Breakdown MUST return at least 2 columns: the GROUP BY column + the aggregation. "
              f"Columns found: {list(df.columns)}")
        sys.exit(1)

    # Check 3: Must have more than 1 row
    if len(df) <= 1:
        print(f"\n[VALIDATION FAILED] DataFrame only has {len(df)} row(s). Breakdown needs > 1 category.")
        sys.exit(1)

    print(f"\n[VALIDATION SUCCESS] Breakdown DataFrame has {df.shape[1]} columns and {len(df)} rows — all checks passed!")
    print(f"  Columns: {list(df.columns)}")

if __name__ == "__main__":
    run_verification()
