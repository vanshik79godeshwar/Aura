"""
Analyst Agent (Jaideep's Insights & Advanced Analytics Hub)
---------------------------------------------------------
This module implements the Analyst Worker for Project Aura.

Why: The Analyst executes concrete data fetching (SQL) and applies rigorous Math/Statistics
to support advanced queries like Root Cause Analysis, Forecasting, and Comparisons. 
We rely solely on standard Python libraries here for conflict prevention and portability.
"""
import os
import statistics
from typing import Dict, Any, List
from src.core.workspace import AgentWorkspace

# ---------------------------------------------------------
# SQL Generation & Mock Data Fetching
# ---------------------------------------------------------
def _generate_sql_query(metrics: list[str], analysis_type: str) -> str:
    """Generates analytical SQL based on the identified intent."""
    if analysis_type == "forecast" or analysis_type == "comparison":
        return "SELECT date, SUM(revenue) FROM sales GROUP BY date ORDER BY date ASC;"
    elif analysis_type == "rca":
        return "SELECT category, metric_name, value FROM business_metrics WHERE anomaly=true;"
    elif "revenue" in metrics and "region" in metrics:
        return "SELECT region, SUM(revenue) FROM sales GROUP BY region;"
    return "SELECT * FROM sales LIMIT 10;"

def _fetch_mock_timeseries(analysis_type: str) -> List[float]:
    """Returns mock timeseries arrays for math processing."""
    if analysis_type == "forecast":
        return [100, 110, 105, 120, 125, 130, 140] # Trending up
    elif analysis_type == "comparison":
        # Returns [last_week_total, this_week_total]
        return [5000, 4500] 
    elif analysis_type == "rca":
        # Drops over time or related metric drops
        return [200, 190, 150, 90, 80]
    return []

def _fetch_data_from_db(sql: str, analysis_type: str) -> dict:
    """Executes the SQL query against the database to fetch raw data."""
    db_path = os.getenv("DB_PATH")
    if not db_path:
        pass # Ignore for mock mode
        
    return {
        "status": "success", 
        "data": f"Mock tabular data for query: {sql}",
        "timeseries_array": _fetch_mock_timeseries(analysis_type)
    }

# ---------------------------------------------------------
# Advanced Analytics (Statistics & Math Hub)
# ---------------------------------------------------------
def _perform_rca(data_array: List[float]) -> Dict[str, Any]:
    """Calculates statistical deviation to identify root causes."""
    if not data_array: return {"finding": "Insufficient data for RCA"}
    mean_val = statistics.mean(data_array)
    std_dev = statistics.stdev(data_array) if len(data_array) > 1 else 0
    drop_magnitude = data_array[0] - data_array[-1]
    
    return {
        "finding": f"Analyzed {len(data_array)} points. Metric dropped by {drop_magnitude}.",
        "variance": round(std_dev, 2),
        "root_cause_flag": "High deviation detected in final standard deviation window." if std_dev > (mean_val*0.2) else "Normal variance."
    }

def _perform_forecasting(data_array: List[float]) -> Dict[str, Any]:
    """Simple linear projection based on mean historical growth rate."""
    if len(data_array) < 2: return {"projection": "Insufficient data"}
    
    growth_rates = [(data_array[i] - data_array[i-1])/data_array[i-1] for i in range(1, len(data_array))]
    avg_growth = statistics.mean(growth_rates)
    next_step_prediction = data_array[-1] * (1 + avg_growth)
    
    return {
        "historical_avg_growth_rate": f"{round(avg_growth * 100, 2)}%",
        "predicted_next_value": round(next_step_prediction, 2)
    }

def _perform_comparison(data_array: List[float]) -> Dict[str, Any]:
    """Calculates WoW or MoM percentage changes."""
    if len(data_array) != 2: return {"finding": "Need exactly 2 cohorts for comparison."}
    
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
    """
    Analyst Agent: Generates SQL, fetches data, and applies mathematical logic.
    """
    metrics = state.get("identified_metrics", [])
    analysis_type = state.get("analysis_type", "standard")
    
    print(f"Agent [Analyst]: Generating SQL for {analysis_type} analysis...")
    
    try:
        sql = _generate_sql_query(metrics, analysis_type)
        print(f"Agent [Analyst]: Engineered SQL -> {sql}")
        
        data = _fetch_data_from_db(sql, analysis_type)
        print(f"Agent [Analyst]: DB fetch successful.")
        
        # Apply Statistical Logic Map
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
        print(f"Agent [Analyst]: Error executing logic -> {e}")
        error_logs = state.get("error_logs", [])
        error_logs.append(str(e))
        return {
            "error_logs": error_logs,
            "current_status": "analyst_error"
        }
