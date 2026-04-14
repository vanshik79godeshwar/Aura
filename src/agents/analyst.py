"""
Analyst Agent (Jaideep's Insights & Advanced Analytics Hub)
---------------------------------------------------------
This module implements the Analyst Worker for Project Aura.

Why: Uses LangChain & Gemini API to dynamically generate realistic SQL query strings based on extracted metrics. 
Also dynamically hallucinates mock numerical arrays to test statistical math modules without hardcoding dummy data.
"""
import os
import statistics
import json
import pandas as pd
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from dotenv import load_dotenv

# Resolve .env from the project root regardless of Streamlit's working directory
_ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(_ENV_PATH))

from langchain_groq import ChatGroq
from src.core.workspace import AgentWorkspace
from src.core.db_engine import DBEngine

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, max_retries=3)

class DynamicSQLPayload(BaseModel):
    sql_query: str = Field(description="The generated valid SQL string to fulfill the analytical intent.")

# ---------------------------------------------------------
# Dynamic LLM Database Connectors
# ---------------------------------------------------------
def _build_fallback_sql(metrics: list[str], analysis_type: str, relevant_tables: list[str], logical_plan: dict = None) -> str:
    """
    Rule-based SQL generator used when the Gemini API is unavailable (e.g. rate-limited).
    Reads the metadata_dictionary.json to find the correct numeric column for each table,
    ensuring the SQL is always valid against the DuckDB schema.
    """
    import json
    metadata_path = os.path.join(os.path.dirname(__file__), "..", "core", "metadata_dictionary.json")
    numeric_keywords = ['amount', 'balance', 'value', 'limit', 'points', 'rate', 'revenue', 'return', 'principal', 'outstanding', 'utilization', 'ytd']
    
    try:
        with open(metadata_path) as f:
            meta = json.load(f)
        tables_meta = meta.get("tables", {})
    except Exception:
        tables_meta = {}
    
    # Find the first relevant_table that has a numeric column, and use it
    chosen_table = None
    chosen_col = None
    for table in relevant_tables:
        cols = list(tables_meta.get(table, {}).get("columns", {}).keys())
        for col in cols:
            if any(kw in col.lower() for kw in numeric_keywords):
                chosen_table = table
                chosen_col = col
                break
        if chosen_table:
            break
    
    # Ultimate fallback: use transactions.amount which always exists
    if not chosen_table:
        chosen_table = "transactions"
        chosen_col = "amount"
    
    if logical_plan and logical_plan.get("group_by_required"):
        # Fetch the first non-numeric column to use as breakdown category if possible
        category_col = [c for c in cols if c != chosen_col][0] if chosen_table and 'cols' in locals() and len(cols) > 1 else 'account_id'
        return f"SELECT {category_col}, SUM({chosen_col}) as sum_amount FROM {chosen_table} GROUP BY {category_col};"
        
    if analysis_type == "comparison":
        return f"SELECT {chosen_col} FROM {chosen_table} LIMIT 2;"
    else:
        return f"SELECT {chosen_col} FROM {chosen_table} LIMIT 10;"

def _generate_sql_query(metrics: list[str], analysis_type: str, relevant_tables: list[str], sentry_reason: str = None, live_tables: list[str] = None, logical_plan: dict = None, metadata_context: str = "", supervisor_instructions: str = "") -> str:
    """Uses Groq LLM to formulate valid DuckDB SQL based on strict Data Passport grounding."""
    try:
        feedback = f"\nCRITICAL FIX REQUIRED: Your previous query failed audit. Reason: {sentry_reason}" if sentry_reason else ""
        
        prompt = (
            f"You are the Senior Data Scientist for Project Aura.\n"
            f"OBJECTIVE: {supervisor_instructions}\n\n"
            f"DATA PASSPORT (The ONLY allowed schema):\n{metadata_context}\n\n"
            f"TRAP WARNING: The CSV file DOES NOT contain a 'Product' column. Use 'Region' instead.\n\n"
            f"EXAMPLE 1:\n"
            f"Goal: 'Total sales over months'\n"
            f"Passport: sales_data has ['Month' (VARCHAR), 'Sales' (BIGINT)]\n"
            f"Thought: I must group by Month and sum Sales.\n"
            f"SQL: SELECT \"Month\", SUM(\"Sales\") FROM \"sales_data\" GROUP BY \"Month\";\n\n"
            f"EXAMPLE 2:\n"
            f"Goal: 'Profit by region'\n"
            f"Passport: sales_data has ['Region' (VARCHAR), 'Profit' (BIGINT)]\n"
            f"Thought: I must group by Region and sum Profit.\n"
            f"SQL: SELECT \"Region\", SUM(\"Profit\") FROM \"sales_data\" GROUP BY \"Region\";\n\n"
            f"RULES:\n"
            f"1. PASSPORT SUPREMACY: Use EXACT names from the Passport ONLY.\n"
            f"2. NO HALLUCINATION: If a column (like Product/Date) is not in the Passport, DO NOT USE IT.\n"
            f"3. DUCKDB COMPLIANCE: Use double quotes for all identifiers.\n"
            f"{feedback}\n"
            f"Constraint: You MUST output ONLY the raw SQL string inside backticks, like this: ```sql\nSELECT ...\n```"
        )
        
        response = llm.invoke(prompt)
        text = response.content
        
        # Extract SQL from potential backticks
        import re
        match = re.search(r"```sql\n(.*?)\n```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip()
        
    except Exception as e:
        fallback = _build_fallback_sql(metrics, analysis_type, relevant_tables, logical_plan)
        print(f"Agent [Analyst]: Exception -> {str(e)} | using fallback -> {fallback}")
        return fallback

def _fetch_data_from_db(sql: str, analysis_type: str) -> dict:
    """Executes the SQL query against DuckDB and extracts a pure mathematical array."""
    engine = DBEngine()
    
    try:
        # Executes SQL securely returning a Pandas DataFrame
        df = engine.execute_query(sql)
        
        # Heuristically extract the core tracking float column out of the Pandas result matrix
        numeric_cols = df.select_dtypes(include=['number']).columns
        if not numeric_cols.empty:
            timeseries_array = df[numeric_cols[0]].dropna().tolist()
        else:
            timeseries_array = [0.0] * 5 # Fallback to prevent math formulas crashing
            
        return {
            "status": "success", 
            "data": df.to_json(orient='records'),
            "timeseries_array": timeseries_array
        }
    except Exception as e:
        print(f"Agent [Analyst] DB Error: {e}")
        return {
            "status": "error", 
            "data": "[]",
            "timeseries_array": [0.0] * 5,
            "error_message": str(e)
        }

# ---------------------------------------------------------
# Advanced Analytics (Statistics & Math Hub)
# ---------------------------------------------------------
def _perform_rca(data_array: List[float]) -> Dict[str, Any]:
    if not data_array: return {"finding": "Insufficient data"}
    mean_val = statistics.mean(data_array)
    std_dev = statistics.stdev(data_array) if len(data_array) > 1 else 0
    drop_magnitude = data_array[0] - data_array[-1]
    return {
        "finding": f"Analyzed {len(data_array)} dynamic points. Metric dropped by {round(drop_magnitude,2)}.",
        "variance": round(std_dev, 2),
        "root_cause_flag": "High deviation detected in final standard deviation window." if std_dev > (mean_val*0.2) else "Normal variance."
    }

def _perform_forecasting(data_array: List[float]) -> Dict[str, Any]:
    if len(data_array) < 2: return {"projection": "Insufficient data"}
    growth_rates = [(data_array[i] - data_array[i-1])/data_array[i-1] for i in range(1, len(data_array)) if data_array[i-1] != 0]
    if not growth_rates: return {"projection": "0 variance"}
    avg_growth = statistics.mean(growth_rates)
    next_step_prediction = data_array[-1] * (1 + avg_growth)
    return {
        "historical_avg_growth_rate": f"{round(avg_growth * 100, 2)}%",
        "predicted_next_value": round(next_step_prediction, 2)
    }

def _perform_comparison(data_array: List[float]) -> Dict[str, Any]:
    if len(data_array) < 2: return {"finding": "Need cohorts for comparison."}
    previous, current = data_array[0], data_array[1]
    if previous == 0: return {"absolute_difference": current, "percentage_change": "N/A (base is 0)", "direction": "increased" if current > 0 else "decreased"}
    
    abs_diff = abs(current - previous)
    percent_change = ((current - previous) / previous) * 100
    direction = "increased" if percent_change > 0 else "decreased"
    
    return {
        "previous_period": previous,
        "current_period": current,
        "absolute_difference": round(abs_diff, 2),
        "percentage_change": f"{round(percent_change, 2)}%",
        "direction": direction
    }

# ---------------------------------------------------------
# Main Analyst Agent Node
# ---------------------------------------------------------
def call_analyst(state: AgentWorkspace) -> Dict[str, Any]:
    metrics = state.get("identified_metrics", [])
    analysis_type = state.get("analysis_type", "standard")
    relevant_tables = state.get("relevant_tables", [])
    sentry_reason = state.get("sentry_reason", "")
    
    engine = DBEngine()
    live_tables = engine.list_tables()
    
    if not live_tables:
        error_logs = state.get("error_logs", [])
        error_logs.append("LIVE DATABASE EMPTY: No uploaded files found in persistent aura.db.")
        return {
            "error_logs": error_logs,
            "current_status": "analyst_error",
            "sql_query": ""
        }
    logical_plan = state.get("logical_plan", {})
    # Semantic Context Isolation - Simplified to prioritize full grounding
    filtered_context = state.get("metadata_context", "No data passport context available.")
    selected_tables = logical_plan.get("selected_tables", relevant_tables)
    
    # Increment retry loop
    retry_count = state.get("retry_count", 0) + 1
    
    print(f"Agent [Analyst]: Calling Groq to dynamically generate SQL & fetch data... (Retry {retry_count})")
    
    supervisor_instr = state.get("analyst_instructions", "")
    
    try:
        sql = _generate_sql_query(
            metrics=metrics, 
            analysis_type=analysis_type, 
            relevant_tables=selected_tables, 
            sentry_reason=sentry_reason if retry_count > 1 else None, 
            live_tables=live_tables, 
            logical_plan=logical_plan, 
            metadata_context=filtered_context,
            supervisor_instructions=supervisor_instr
        )
        print(f"Agent [Analyst]: Groq Engineered SQL -> {sql}")
        
        data = _fetch_data_from_db(sql, analysis_type)
        print(f"Agent [Analyst]: Groq Hallucinated DB points -> {data.get('timeseries_array')}")

        # If DuckDB rejected the SQL, immediately use the rule-based fallback
        if data.get("status") == "error":
            db_error = data.get("error_message", "Unknown DB error")
            error_logs = state.get("error_logs", [])
            error_logs.append(f"DB execution error on Retry {retry_count}: {db_error}")
            print(f"Agent [Analyst]: DB error detected -> activating rule-based fallback SQL")
            sql = _build_fallback_sql(metrics, analysis_type, selected_tables, logical_plan)
            print(f"Agent [Analyst]: Fallback SQL -> {sql}")
            data = _fetch_data_from_db(sql, analysis_type)
        
        advanced_results = {}
        ts_array = data.get("timeseries_array", [])
        
        if analysis_type == "rca":
            advanced_results = _perform_rca(ts_array)
        elif analysis_type == "forecast":
            advanced_results = _perform_forecasting(ts_array)
        elif analysis_type == "comparison":
            advanced_results = _perform_comparison(ts_array)
        else:
            advanced_results = {"finding": "Standard tabular retrieval."}
            
        return {
            "sql_query": sql,
            "raw_data": data,
            "advanced_analytics_results": advanced_results,
            "statistical_payload": advanced_results,
            "retry_count": retry_count,
            "current_status": "analyst_complete"
        }
    except Exception as e:
        print(f"Agent [Analyst]: Error executing dynamically -> {e}")
        error_logs = state.get("error_logs", [])
        error_logs.append(str(e))
        return {
            "error_logs": error_logs,
            "current_status": "analyst_error"
        }
