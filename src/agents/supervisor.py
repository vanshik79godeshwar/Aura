import json
import os
from typing import Dict, Any, Literal
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from src.core.workspace import AgentWorkspace
from dotenv import load_dotenv

# Resolve .env from project root
_ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(_ENV_PATH))

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, max_retries=3)

class SupervisorPlan(BaseModel):
    refined_plan: str = Field(description="A multi-step natural language explanation of how you are solving the user's request.")
    routing_decision: Literal["SQL_REQUIRED", "INTERPRETATION_ONLY"] = Field(
        description="Choose SQL_REQUIRED for any chart, breakdown, aggregation, or data fetching request. Use INTERPRETATION_ONLY only for meta-questions about the schema or system."
    )
    analyst_instructions: str = Field(description="Specific instructions for the SQL Analyst (ignored if INTERPRETATION_ONLY).")
    visualizer_instructions: str = Field(description="Instructions for the Visualizer, including the specific chart_type (Bar, Line, Scatter, Pie, or None) and chart_goal.")
    chart_type: Literal["Bar", "Line", "Scatter", "Pie", "None"] = Field(description="The exact chart type to be used.")

def call_supervisor(state: AgentWorkspace) -> Dict[str, Any]:
    """
    Supervisor Node — The Foreman.
    Receives user query and Data Passport. Outputs a detailed execution plan.
    """
    query = state.get("user_query", "")
    metadata_context = state.get("metadata_context", "")
    
    print(f"Agent [Supervisor]: Overseeing query -> '{query}'")

    system_prompt = (
        f"You are the 'Foreman' (Supervisor) of the Aura Data Engine. Your role is orchestrated specialists to answer user data queries.\n"
        f"You have access to the 'Data Passport' which contains table schemas, null counts, and sample markdown data.\n\n"
        f"DATA PASSPORT:\n{metadata_context}\n\n"
        f"USER QUERY: {query}\n\n"
        f"EXAMPLE 1 (Trend):\n"
        f"Query: 'Sales over time'\n"
        f"Passport: table 'sales_data' with columns ['Region', 'Month', 'Sales', 'Revenue', 'Profit', 'Sales_Target']\n"
        f"Plan: 'I will extract Sales totals over Months from the sales_data table.'\n"
        f"Analyst Instructions: 'Query table sales_data. Use columns Month and Sales. SUM(Sales) grouped by Month.'\n"
        f"Visualizer: Line chart of sales trends.\n\n"
        f"EXAMPLE 2 (Complex):\n"
        f"Query: 'Revenue by region'\n"
        f"Passport: table 'sales_data' with columns ['Region', 'Revenue']\n"
        f"Plan: 'I will calculate total revenue per region.'\n"
        f"Analyst Instructions: 'Query table sales_data. Use columns Region and Revenue. SUM(Revenue) grouped by Region order by Revenue DESC.'\n"
        f"Visualizer: Bar chart of revenue distribution.\n\n"
        f"RULES:\n"
        f"1. PASSPORT ONLY: Never mention columns or entities NOT in the Passport. (e.g. don't mention 'Product' if it's not there).\n"
        f"2. EXACT TABLE NAMES: Use 'sales_data' (from Passport) instead of 'sales table'.\n"
        f"3. ANALYST GUIDANCE: List the exact columns to use. Never let the Analyst guess.\n"
    )

    structured_llm = llm.with_structured_output(SupervisorPlan)
    try:
        plan = structured_llm.invoke(system_prompt)
        
        print(f"Agent [Supervisor] Plan: {plan.refined_plan}")
        print(f"Agent [Supervisor] Decision: {plan.routing_decision} | Chart: {plan.chart_type}")
        
        return {
            "logical_plan": plan.dict(), # Keeping the full object for future use
            "supervisor_plan": plan.refined_plan,
            "routing_decision": plan.routing_decision,
            "analyst_instructions": plan.analyst_instructions,
            "visualizer_instructions": plan.visualizer_instructions,
            "target_chart_type": plan.chart_type,
            "current_status": "supervisor_complete"
        }
    except Exception as e:
        print(f"Agent [Supervisor] error: {e}")
        return {
            "routing_decision": "SQL_REQUIRED", # Default fallback
            "supervisor_plan": "Fallback plan: Executing standard SQL analysis.",
            "analyst_instructions": "Analyze the data to answer the user query.",
            "visualizer_instructions": "Generate a suitable visualization.",
            "target_chart_type": "None",
            "current_status": "supervisor_error"
        }
