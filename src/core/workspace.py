from typing import TypedDict, List, Dict, Any, Optional

class AgentWorkspace(TypedDict, total=False):
    """
    Shared state workspace for the Talk-to-Data orchestrator and all worker agents.
    """
    user_query: str
    identified_metrics: List[str]  # Or a dict representation of the metrics
    analysis_type: str  # e.g., 'standard', 'rca', 'forecast', 'comparison'

    statistical_payload: dict  # To hold Jaideep's variance/growth derivations
    visual_configuration: dict  # To hold Kushal's Plotly heuristic settings

    relevant_tables: List[str] # Retrieved from ChromaDB

    sql_query: str
    raw_data: Optional[Any]  # Can hold dictionary or Pandas DataFrames (including Meet's auto-mocked data)
    advanced_analytics_results: Optional[Dict[str, Any]] # Mathematical output
    error_logs: List[str]
    current_status: str
    retry_count: int  # Helpful for handling retry loops in the orchestrator
    next_action: str  # Routing decision from the orchestrator
    sentry_status: str
    sentry_reason: str
    sentry_correction: str
    final_response: str
