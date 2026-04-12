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
from langchain_groq import ChatGroq
from src.core.workspace import AgentWorkspace
from src.core.db_engine import DBEngine

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, max_retries=3)

class DynamicSQLPayload(BaseModel):
    sql_query: str = Field(description="The generated valid SQL string to fulfill the analytical intent.")

# ---------------------------------------------------------
# Dynamic LLM Database Connectors
# ---------------------------------------------------------
def _build_fallback_sql(metrics: list[str], analysis_type: str, relevant_tables: list[str]) -> str:
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
    
    if analysis_type == "comparison":
        return f"SELECT {chosen_col} FROM {chosen_table} LIMIT 2;"
    else:
        return f"SELECT {chosen_col} FROM {chosen_table} LIMIT 10;"

def _generate_sql_query(metrics: list[str], analysis_type: str, relevant_tables: list[str], sentry_reason: str = None) -> str:
    """Uses Groq LLM to dynamically formulate the database table querying logic using verified context.
    Falls back to a rule-based generator if the API quota is exhausted.
    """
    import json
    metadata_path = os.path.join(os.path.dirname(__file__), "..", "core", "metadata_dictionary.json")
    schema_context = ""
    try:
        with open(metadata_path) as f:
            meta = json.load(f)
        for table in relevant_tables:
            if table in meta.get("tables", {}):
                cols = list(meta["tables"][table].get("columns", {}).keys())
                schema_context += f"Table '{table}' has columns: {cols}\n"
    except Exception:
        schema_context = "(Schema unavailable, use logical assumptions)"

    try:
        structured_llm = llm.with_structured_output(DynamicSQLPayload)
        feedback = f"\nCRITICAL FIX REQUIRED: Your previous query failed audit entirely. Reason: {sentry_reason}\nFix this query immediately based on the reason above!" if sentry_reason else ""
        
        prompt = (
            f"You are a Senior SQL Analyst. A user wants to do a '{analysis_type}' analysis.\n"
            f"The relevant metrics are: {metrics}\n"
            f"The verified database tables you MUST query from are: {relevant_tables}\n"
            f"transactions table columns: tx_id, account_id, amount, tx_date, merchant_name.\n"
            f"Column Reference:\n{schema_context}\n"
            f"Write a standard, logical SQL query to fetch data that supports this. Do not guess table names or column names outside of the verified ones!\n"
            f"You MUST ONLY use the column names listed in the verified schema. If you use table1 or id, the Sentry will block you.\n"
            f"If forecast/comparison, GROUP BY a date-like column. If rca, check for anomalies."
            f"{feedback}"
        )
        result = structured_llm.invoke(prompt)
        return result.sql_query
    except Exception:
        # Quota exhausted or LLM unavailable — fall back to rule-based SQL
        fallback = _build_fallback_sql(metrics, analysis_type, relevant_tables)
        print(f"Agent [Analyst]: LLM unavailable, using rule-based SQL -> {fallback}")
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
            "timeseries_array": [0.0] * 5
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
    
    # Increment retry loop
    retry_count = state.get("retry_count", 0) + 1
    
    print(f"Agent [Analyst]: Calling Groq to dynamically generate SQL & fetch data... (Retry {retry_count})")
    try:
        sql = _generate_sql_query(metrics, analysis_type, relevant_tables, sentry_reason=sentry_reason if retry_count > 1 else None)
        print(f"Agent [Analyst]: Groq Engineered SQL -> {sql}")
        
        data = _fetch_data_from_db(sql, analysis_type)
        print(f"Agent [Analyst]: Groq Hallucinated DB points -> {data.get('timeseries_array')}")
        
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
