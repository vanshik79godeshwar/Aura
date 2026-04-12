import os
from dotenv import load_dotenv

# 1. CRITICAL: Load environment variables FIRST
load_dotenv()


from src.agents.orchestrator import app

def main():
    # Load environment variables (e.g. GEMINI_API_KEY)
    load_dotenv()
    
    initial_state = {
        "user_query": "Why did revenue drop by 11% in the South region last month?",
        "identified_metrics": [],
        "sql_query": "",
        "error_logs": [],
        "current_status": "initialized"
    }

    print("Iterating LangGraph state updates:")
    # Invoke the graph and stream the updates
    for output in app.stream(initial_state):
        for node_name, state_update in output.items():
            print(f"\n--- Update from node: {node_name} ---")
            print(state_update)

if __name__ == "__main__":
    main()
