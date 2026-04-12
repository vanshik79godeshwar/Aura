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
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.workspace import AgentWorkspace
from src.agents.metadata_retriever import MetadataRetriever

class OracleExtraction(BaseModel):
    identified_metrics: list[str] = Field(
        description="A list of measurable metrics the user wants to understand, e.g., ['revenue', 'sales', 'region']."
    )
    analysis_type: Literal["standard", "rca", "forecast", "comparison"] = Field(
        description="The type of advanced analysis needed depending on phrasing ('why'->rca, 'compare'->comparison, 'predict/what-if'->forecast, else->standard)."
    )

def analyze_intent(query: str) -> OracleExtraction:
    """Uses a dynamic LLM via LangChain to extract semantic features."""
    # Instantiating the Gemini model wrapper 
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
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
    Semantic Layer Agent (Lexicon): Extracts intention and metrics dynamically via Gemini API,
    and simultaneously pulls Vector Context from ChromaDB Atlas.
    """
    print("Agent [Lexicon]: Asking Gemini to compute intent and fetching verified tables...")
    query = state.get("user_query", "")
    
    # Instantiate the retriever for Atlas schema checks
    retriever = MetadataRetriever()
    relevant_tables = retriever.get_relevant_tables(query)
    print(f"Agent [Lexicon]: ChromaDB identified contextual tables -> {relevant_tables}")
    
    try:
        extraction = analyze_intent(query)
        print(f"Agent [Lexicon]: LLM Parsed Metrics -> {extraction.identified_metrics} | Type -> {extraction.analysis_type}")
        
        return {
            "identified_metrics": extraction.identified_metrics,
            "analysis_type": extraction.analysis_type,
            "relevant_tables": relevant_tables,
            "current_status": "lexicon_complete"
        }
    except Exception as e:
        print(f"Agent [Lexicon]: Warning - LLM parsing failed: {e}")
        # graceful fallback
        return {
            "identified_metrics": ["general"],
            "analysis_type": "standard",
            "relevant_tables": relevant_tables,
            "current_status": "lexicon_error"
        }
