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
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.workspace import AgentWorkspace

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

class DynamicSQLPayload(BaseModel):
    sql_query: str = Field(description="The generated valid SQL string to fulfill the analytical intent.")
    
class MockDataPayload(BaseModel):
    timeseries_array: List[float] = Field(description="A sequential numerical array representing historical data points over time or categories. Min 2 points.")

# ---------------------------------------------------------
# Dynamic LLM Database Connectors
# ---------------------------------------------------------
def _generate_sql_query(metrics: list[str], analysis_type: str, relevant_tables: list[str]) -> str:
    """Uses Gemini to dynamically formulate the database table querying logic using verified context."""
    structured_llm = llm.with_structured_output(DynamicSQLPayload)
    prompt = (
        f"You are a Senior SQL Analyst. A user wants to do a '{analysis_type}' analysis.\n"
        f"The relevant metrics are: {metrics}\n"
        f"The verified database tables you MUST query from are: {relevant_tables}\n"
        f"Write a standard, logical SQL query to fetch data that supports this. Do not guess table names outside of the verified ones! "
        f"If forecast/comparison, GROUP BY a date-like column. If rca, check for anomalies."
    )
    result = structured_llm.invoke(prompt)
    return result.sql_query

def _fetch_mock_timeseries(analysis_type: str, sql: str) -> List[float]:
    """Uses Gemini to hallucinate a realistic mathematical array so our formulas can run dynamically."""
    structured_llm = llm.with_structured_output(MockDataPayload)
    prompt = (
        f"Our pipeline needs mock data since the DB isn't hooked up. "
        f"We are running analysis type: '{analysis_type}' with SQL: '{sql}'\n"
        f"Generate a realistic float array of at least 5 points representing the data. "
        f"If 'forecast', make it logically trending. If 'rca', create a sudden drop at the end. "
        f"If 'comparison', return exactly 2 points (e.g., this week vs last week)."
    )
    result = structured_llm.invoke(prompt)
    return result.timeseries_array

def _fetch_data_from_db(sql: str, analysis_type: str) -> dict:
    """Executes the SQL query against the database to fetch raw data or falls back to LLM hallucination."""
    db_path = os.getenv("DB_PATH")
    if db_path and db_path != "your_db_path_here":
        # Production execution logic...
        pass 
        
    # Dynamically generate fake datasets via Gemini to prevent static hardcoding
    fake_array = _fetch_mock_timeseries(analysis_type, sql)
    return {
        "status": "success", 
        "data": f"Dynamically hallucinated tabular data for query: {sql}",
        "timeseries_array": fake_array
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
    if previous == 0: return {"delta": "N/A (base is 0)"}
    percent_change = ((current - previous) / previous) * 100
    direction = "increased" if percent_change > 0 else "decreased"
    return {
        "previous_period": previous,
        "current_period": current,
        "delta": f"{abs(round(percent_change, 2))}%",
        "direction": direction
    }

# ---------------------------------------------------------
# Main Analyst Agent Node
# ---------------------------------------------------------
def call_analyst(state: AgentWorkspace) -> Dict[str, Any]:
    metrics = state.get("identified_metrics", [])
    analysis_type = state.get("analysis_type", "standard")
    relevant_tables = state.get("relevant_tables", [])
    
    print(f"Agent [Analyst]: Calling Gemini to dynamically generate SQL & fetch data...")
    try:
        sql = _generate_sql_query(metrics, analysis_type, relevant_tables)
        print(f"Agent [Analyst]: Gemini Engineered SQL -> {sql}")
        
        data = _fetch_data_from_db(sql, analysis_type)
        print(f"Agent [Analyst]: Gemini Hallucinated DB points -> {data.get('timeseries_array')}")
        
        advanced_results = {}
        ts_array = data.get("timeseries_array", [])
        
        if analysis_type == "rca":
            advanced_results = _perform_rca(ts_array)
        elif analysis_type == "forecast":
            advanced_results = _perform_forecasting(ts_array)
        elif analysis_type == "comparison":
            advanced_results = _perform_comparison(ts_array)
            
        return {
            "sql_query": sql,
            "raw_data": data,
            "advanced_analytics_results": advanced_results,
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
