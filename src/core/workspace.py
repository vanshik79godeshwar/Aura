from typing import TypedDict, List, Dict, Any, Optional

class AgentWorkspace(TypedDict, total=False):
    """
    Shared state workspace for the Talk-to-Data orchestrator and all worker agents.
    """
    user_query: str
    identified_metrics: List[str]  # Or a dict representation of the metrics
    analysis_type: str  # e.g., 'standard', 'rca', 'forecast', 'comparison'
    sql_query: str
    raw_data: Optional[Dict[str, Any]]  # Or Pandas DataFrame
    advanced_analytics_results: Optional[Dict[str, Any]] # Mathematical output
    error_logs: List[str]
    current_status: str
    retry_count: int  # Helpful for handling retry loops in the orchestrator
