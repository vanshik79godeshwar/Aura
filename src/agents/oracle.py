"""
Oracle Agent (Semantic Layer)
-----------------------------
This module implements the Oracle Worker for Project Aura.

Why: The Oracle acts as the semantic layer. Its job is to prioritize Clarity (ELI5).
It uses a Gemini LLM via LangChain to dynamically extract metrics and understand 
user intent instead of relying on rigid hardcoded rules.
"""
import os
from typing import Dict, Any, Literal
from pydantic import BaseModel, Field

from dotenv import load_dotenv

# Resolve .env from project root regardless of working directory
_ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(_ENV_PATH))

from langchain_groq import ChatGroq
from src.core.workspace import AgentWorkspace
from src.agents.metadata_retriever import MetadataRetriever

class OracleExtraction(BaseModel):
    identified_metrics: list[str] = Field(
        description="A list of measurable metrics the user wants to understand, e.g., ['revenue', 'sales', 'region']."
    )
    analysis_type: Literal["standard", "rca", "forecast", "comparison"] = Field(
        description="The type of advanced analysis needed depending on phrasing ('why'->rca, 'compare'->comparison, 'predict/what-if'->forecast, else->standard)."
    )

def _classify_intent_locally(query: str) -> OracleExtraction:
    """
    Rule-based intent classifier used as a fallback when the Gemini API is unavailable.
    Applies simple keyword detection to map queries to the correct analytical track.
    This ensures Jaideep's math pipeline always routes correctly regardless of API status.
    """
    query_lower = query.lower()
    
    # Detect analysis type from semantic keywords
    if any(kw in query_lower for kw in ["why", "drop", "decline", "fell", "cause", "reason"]):
        analysis_type = "rca"
    elif any(kw in query_lower for kw in ["predict", "forecast", "next", "what if", "future", "project"]):
        analysis_type = "forecast"
    elif any(kw in query_lower for kw in ["compare", "wow", "mom", "week", "month", "versus", "vs"]):
        analysis_type = "comparison"
    else:
        analysis_type = "standard"
    
    # Extract metrics from well-known business keywords
    metrics = []
    for kw in ["revenue", "sales", "balance", "amount", "transactions", "loans", "profit", "spending"]:
        if kw in query_lower:
            metrics.append(kw)
    if not metrics:
        metrics = ["general"]
    
    return OracleExtraction(identified_metrics=metrics, analysis_type=analysis_type)

def analyze_intent(query: str) -> OracleExtraction:

    """Uses Groq LLM to extract semantic features from user query."""

    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, max_retries=3)
    structured_llm = llm.with_structured_output(OracleExtraction)
    
    prompt = (
        f"You are the Oracle agent for a data analytics platform. Read the following user query.\n"
        f"User Query: '{query}'\n\n"
        f"Identify the core business metrics, and strictly categorize the analytical intent."
    )
    result = structured_llm.invoke(prompt)
    return result

def lexicon(state: AgentWorkspace) -> Dict[str, Any]:
    """
    Semantic Layer Agent (Lexicon): Extracts intention and metrics dynamically via Groq API,
    and simultaneously pulls Vector Context from ChromaDB Atlas.
    """
    print("Agent [Lexicon]: Asking Groq to compute intent and fetching verified tables...")
    query = state.get("user_query", "")
    error_logs = state.get("error_logs", [])
    
    # Instantiate the retriever for Atlas schema checks
    retriever = MetadataRetriever()
    relevant_tables = retriever.get_relevant_tables(query)
    print(f"Agent [Lexicon]: ChromaDB identified contextual tables -> {relevant_tables}")
    error_logs.append(f"ChromaDB mapped semantic query to verified structure schemas: {relevant_tables}")
    
    try:
        extraction = analyze_intent(query)
        print(f"Agent [Lexicon]: LLM Parsed Metrics -> {extraction.identified_metrics} | Type -> {extraction.analysis_type}")
        
        return {
            "identified_metrics": extraction.identified_metrics,
            "analysis_type": extraction.analysis_type,
            "relevant_tables": relevant_tables,
            "error_logs": error_logs,
            "current_status": "lexicon_complete"
        }
    except Exception as e:
        print(f"Agent [Lexicon]: LLM unavailable ({type(e).__name__}), falling back to rule-based classification.")
        # Fall back to keyword-based classification — ensures RCA/Forecast/Comparison still route correctly
        extraction = _classify_intent_locally(query)
        print(f"Agent [Lexicon]: Rule-based Metrics -> {extraction.identified_metrics} | Type -> {extraction.analysis_type}")
        return {
            "identified_metrics": extraction.identified_metrics,
            "analysis_type": extraction.analysis_type,
            "relevant_tables": relevant_tables,
            "current_status": "lexicon_fallback"
        }
