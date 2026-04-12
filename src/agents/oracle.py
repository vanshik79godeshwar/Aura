"""
Oracle Agent (Semantic Layer)
-----------------------------
This module implements the Oracle Worker for Project Aura.

Why: The Oracle acts as the semantic layer. Its job is to prioritize Clarity (ELI5 language).
It takes the raw human language and translates it into specific metrics or intent 
so that the downstream agents know exactly what data to fetch.
"""
import os
from typing import Dict, Any
from src.core.workspace import AgentWorkspace

def analyze_intent(query: str) -> tuple[list[str], str]:
    """
    Extracts metrics and the analytical intent from the user query.
    
    Why: By classifying the query into specific analytical buckets (rca, forecast, 
    comparison, standard) we know exactly what mathematical logic to apply downstream.
    
    Args:
        query (str): The raw instruction from the user.
        
    Returns:
        tuple[list[str], str]: A tuple of (metrics, analysis_type).
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY is not set. Continuing with mock extraction.")
    
    query_lower = query.lower()
    metrics = []
    
    if "revenue" in query_lower or "sales" in query_lower:
        metrics.append("revenue")
    if "region" in query_lower or "country" in query_lower:
        metrics.append("region")
    if not metrics:
        metrics.append("general_data")
        
    # Classify Analytical Type
    analysis_type = "standard"
    if "why" in query_lower or "drop" in query_lower or "cause" in query_lower:
        analysis_type = "rca"
    elif "what if" in query_lower or "forecast" in query_lower or "predict" in query_lower:
        analysis_type = "forecast"
    elif "compare" in query_lower or "wow" in query_lower or "mom" in query_lower:
        analysis_type = "comparison"
        
    return metrics, analysis_type

def call_oracle(state: AgentWorkspace) -> Dict[str, Any]:
    """
    Semantic Layer Agent: Extracts intention and metrics from the user query.
    
    Why: To ensure we understand exactly what the user wants to know before 
    we hit the database, fulfilling the 'Clarity' pillar.
    
    Args:
        state (AgentWorkspace): Shared state workspace.
        
    Returns:
        Dict[str, Any]: Updated state values containing extracted metrics.
    """
    print("Agent [Oracle]: Understanding intent and identifying metrics...")
    
    query = state.get("user_query", "")
    metrics, analysis_type = analyze_intent(query)
    
    print(f"Agent [Oracle]: Extracted metrics -> {metrics} | Type -> {analysis_type}")
    
    return {
        "identified_metrics": metrics,
        "analysis_type": analysis_type,
        "current_status": "oracle_complete"
    }
