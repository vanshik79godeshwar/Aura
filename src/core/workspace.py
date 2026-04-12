from typing import TypedDict, List, Dict, Any, Optional

class AgentWorkspace(TypedDict, total=False):
    """
    Shared state workspace for the Talk-to-Data orchestrator and all worker agents.
    """
    user_query: str
    identified_metrics: List[str]  # Or a dict representation of the metrics
    sql_query: str
    raw_data: Optional[Dict[str, Any]]  # Or Pandas DataFrame
    error_logs: List[str]
    current_status: str
    retry_count: int  # Helpful for handling retry loops in the orchestrator
    next_action: str  # Routing decision from the orchestrator
