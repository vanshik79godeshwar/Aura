import os
import sys
import shutil
import json
import pandas as pd
from typing import Any

# Ensure project root is on path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Mocking Streamlit for environment where it's not running
from unittest import mock
sys.modules["streamlit"] = mock.MagicMock()

def reset_system():
    print("\n[QA] --- Resetting System ---")
    import time
    
    # Try to close any existing DB connection
    try:
        from src.core.db_engine import DBEngine
        DBEngine().close()
    except: pass
    
    time.sleep(1) # Give OS time to release locks
    
    db_path = os.path.join(PROJECT_ROOT, "aura.db")
    if os.path.exists(db_path):
        try: os.remove(db_path)
        except Exception as e: print(f"  [Warn] Could not remove aura.db: {e}")
    
    chroma_path = os.path.join(PROJECT_ROOT, ".chroma_db")
    if os.path.exists(chroma_path):
        for i in range(3):
            try:
                shutil.rmtree(chroma_path)
                break
            except Exception as e:
                print(f"  [Warn] Attempt {i+1} to remove .chroma_db failed: {e}")
                time.sleep(1)
    
    metadata_file = os.path.join(PROJECT_ROOT, "src", "core", "metadata_dictionary.json")
    if not os.path.exists(os.path.dirname(metadata_file)):
        os.makedirs(os.path.dirname(metadata_file))
    with open(metadata_file, "w") as f:
        json.dump({}, f)

def upload_file(filename: str):
    from src.core.db_engine import DBEngine
    from src.core.generate_metadata import auto_generate_metadata
    from src.core.ingest_metadata import ingest
    from src.core.registry import ContextRegistry
    
    print(f"\n[QA] --- Uploading {filename} ---")
    assets_dir = os.path.join(PROJECT_ROOT, "assets")
    filepath = os.path.join(assets_dir, filename)
    
    # For large files like amazon.csv, we'll take a sample for testing speed
    if filename == "amazon.csv":
        df = pd.read_csv(filepath, nrows=100) # Header + 100 rows is enough for schema profiling
    else:
        df = pd.read_csv(filepath)
    
    table_name = os.path.splitext(filename)[0].replace(" ", "_").lower()
    DBEngine().register_dataframe(df, table_name)
    
    auto_generate_metadata()
    ingest()
    ContextRegistry().build_registry()
    
    return table_name

def run_scenario(query: str, active_upload: str = ""):
    from src.agents.orchestrator import app as aura_graph
    from src.core.registry import ContextRegistry
    
    print(f"\n[QA] --- Scenario Query: '{query}' (Active Upload: {active_upload}) ---")
    
    # Freshly sync metadata context from disk
    metadata_context = ContextRegistry().get_metadata_context()
    
    initial_state = {
        "user_query": query,
        "identified_metrics": [],
        "relevant_tables": [],
        "metadata_context": metadata_context,
        "logical_plan": {},
        "sql_query": "",
        "error_logs": [],
        "current_status": "initialized",
        "next_action": "",
        "active_upload": active_upload,
        "retry_count": 0
    }
    
    final_state = initial_state.copy()
    try:
        # We run the graph
        for output in aura_graph.stream(initial_state):
            for node_name, state_update in output.items():
                final_state.update(state_update)
                print(f"  -> Agent [{node_name}] completed with status: {state_update.get('current_status')}")
    except Exception as e:
        print(f"  [CRITICAL ERROR] Graph execution failed: {e}")
        import traceback
        traceback.print_exc()
        
    return final_state

def test_autonomous_qa():
    reset_system()
    
    # Scenario 1: Single Table - Revenue by Region
    table_name = upload_file("sales_data.csv")
    state1 = run_scenario("Show me Revenue by Region", active_upload=table_name)
    sql1 = state1.get("sql_query", "").upper()
    print(f"[QA Result 1] SQL Produced: {sql1}")
    
    if "GROUP BY" in sql1:
        print("[OK] Scenario 1 Passed: GROUP BY confirmed.")
    else:
        print("[FAIL] Scenario 1 Failed: Missing GROUP BY for breakdown request.")
        sys.exit(1)
    
    # Scenario 2: Context Shift - Missing Data
    # Only sales_data is present. Query is about amazon.
    state2 = run_scenario("What are the top rated amazon products?", active_upload=table_name)
    plan2 = state2.get("logical_plan", {})
    selected_tables = plan2.get("selected_tables", [])
    
    print(f"[QA Result 2] Selected Tables: {selected_tables}")
    # The planner should NOT select sales_data for amazon product queries.
    if table_name in selected_tables:
         print("[FAIL] Scenario 2 Failed: System incorrectly mapped amazon query to sales_data.")
         sys.exit(1)
    else:
         print("[OK] Scenario 2 Passed: System correctly identified lack of relevant data.")

    # Scenario 3: Schema Accuracy - Average Price
    table_name_2 = upload_file("amazon.csv")
    state3 = run_scenario("What is the average actual price?", active_upload=table_name_2)
    sql3 = state3.get("sql_query", "").lower()
    print(f"[QA Result 3] SQL Produced: {sql3}")
    
    # Standard Hallucination would be 'SELECT AVG(price) ...'
    # Correct should be 'SELECT AVG(actual_price) ...' or 'discounted_price'
    if "actual_price" in sql3 or "discounted_price" in sql3:
        if "select price" in sql3 or "avg(price)" in sql3:
             print("[FAIL] Scenario 3 Failed: Hallucinated 'price' column detected.")
             sys.exit(1)
        print("[OK] Scenario 3 Passed: Correct schema mapping used.")
    else:
        print(f"[FAIL] Scenario 3 Failed: SQL did not use expected column. SQL: {sql3}")
        sys.exit(1)

    print("\n" + "="*50)
    print("ALL AUTONOMOUS QA SCENARIOS PASSED")
    print("="*50)

if __name__ == "__main__":
    test_autonomous_qa()
