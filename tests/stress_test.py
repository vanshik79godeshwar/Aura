import sys
import os
import pandas as pd
import time

# Ensure project root is in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.agents.orchestrator import app as aura_graph
from src.core.db_engine import DBEngine
from src.core.registry import ContextRegistry

def setup_test_db():
    print("\n[Stress Test] Setting up test database...")
    engine = DBEngine()
    # Reset/Create sales_data table
    csv_path = os.path.join(project_root, "assets", "sales_data.csv")
    df = pd.read_csv(csv_path)
    engine.register_dataframe(df, "sales_data")
    print(f"[Stress Test] Table 'sales_data' registered with {len(df)} rows.")

    # Ingest metadata (Simulate ingest_metadata.py)
    print("[Stress Test] Indexing metadata...")
    from src.core.generate_metadata import auto_generate_metadata
    from src.core.ingest_metadata import ingest
    
    auto_generate_metadata()
    ingest()
    print("[Stress Test] Metadata indexed in ChromaDB.")

def run_15_queries():
    queries = [
        # Descriptive
        "Tell me about the sales_data table.",
        "What columns are available in the sales data?",
        "Describe the schema of the uploaded sales data.",
        
        # Statistical
        "What is the average revenue per region?",
        "Show me the total profit by month.",
        "What is the maximum sales recorded?",
        
        # Visual
        "Plot a bar chart of revenue by region.",
        "Show a line chart of sales over time (months).",
        "Give me a pie chart of profit distribution per region.",
        
        # Complex
        "What is the total revenue if North sales grow by 10% next month?",
        "Compare the total revenue vs total profit for each region.",
        "Which month had the highest revenue-to-profit ratio?",
        
        # Ambiguous
        "Anything interesting in the data?",
        "How is the business performing?",
        "Give me a summary of the sales trends."
    ]

    results = []
    print(f"\n[Stress Test] Starting 15-Query Stress Test...\n")
    
    for i, q in enumerate(queries, 1):
        print(f"Test {i}/15: '{q}'")
        state = {
            "user_query": q,
            "relevant_tables": ["sales_data"],
            "error_logs": [],
            "current_status": "initialized",
            "active_upload": "sales_data"
        }
        
        start_time = time.time()
        try:
            final_state = aura_graph.invoke(state)
            duration = time.time() - start_time
            
            resp = final_state.get("final_response", "")
            plan = final_state.get("supervisor_plan", "No plan.")
            chart = final_state.get("target_chart_type", "None")
            
            # Simple validation: checks for common failure indicators
            passed = True
            if not resp or "X" in resp or "Error" in final_state.get("current_status", ""):
                passed = False
            
            status = "PASS" if passed else "FAIL"
            print(f"  Result: {status} ({duration:.2f}s) | Chart: {chart}")
            if not passed:
                print(f"  Error Logs: {final_state.get('error_logs')}")
            
            results.append({"query": q, "status": status, "duration": duration, "plan": plan})
        except Exception as e:
            print(f"  CRASH: {e}")
            results.append({"query": q, "status": "CRASH", "duration": 0, "plan": str(e)})

    return results

def print_report(results):
    print("\n" + "="*50)
    print("STRESS TEST FINAL REPORT")
    print("="*50)
    passes = sum(1 for r in results if r["status"] == "PASS")
    print(f"Total Success: {passes}/15")
    print("-" * 50)
    for r in results:
        print(f"{r['status']} | {r['query'][:40]:<40} | {r['duration']:.2f}s")
    print("="*50)

if __name__ == "__main__":
    setup_test_db()
    results = run_15_queries()
    print_report(results)
