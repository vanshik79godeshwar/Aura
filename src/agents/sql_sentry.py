import json
import os
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq

class SentryDecision(BaseModel):
    status: str = Field(description="PASS or FAIL")
    reason: str = Field(description="If FAIL, explain exactly what is wrong. If PASS, leave empty.")
    correction_hint: str = Field(description="If FAIL, provide the corrected SQL logic. If PASS, leave empty.")

class SQLSentry:
    """
    The Auditor Sub-Agent.
    Responsible for validating AI-generated SQL against the source-of-truth metadata.
    Upholds the Trust and Clarity pillars.
    """
    def __init__(self):
        metadata_file = os.path.join(os.path.dirname(__file__), "..", "core", "metadata_dictionary.json")
        try:
            with open(metadata_file, "r") as f:
                self.metadata = json.load(f).get("tables", {})
        except FileNotFoundError:
            print("Warning: metadata_dictionary.json not found. Sentry operating blind.")
            self.metadata = {}

    def _extract_schemas(self, relevant_tables: list) -> str:
        """Pulls only the required schemas to keep the LLM context tight."""
        schemas = []
        for table in relevant_tables:
            if table in self.metadata:
                info = self.metadata[table]
                desc = info.get("description", "")
                cols = ", ".join([f"{col} ({c_info['description']})" for col, c_info in info.get("columns", {}).items()])
                schemas.append(f"Table: {table}\nDescription: {desc}\nColumns: {cols}")
        return "\n\n".join(schemas)

    def generate_auditor_prompt(self, proposed_sql: str, relevant_tables: list) -> str:
        """Constructs the exact instruction prompt for the LLM API."""
        schema_text = self._extract_schemas(relevant_tables)
        
        prompt = f"""You are 'The Sentry', an expert Database Auditor.
Your job is to relentlessly verify the accuracy of a proposed SQL query against the official database schema.

OFFICIAL SCHEMA:
{schema_text}

PROPOSED SQL:
{proposed_sql}

RULES:
1. Verify every column used in the query actually exists in the schema.
2. Verify the logic makes sense (e.g., do not SUM() a text ID field, do not group by a high-cardinality raw timestamp).
3. Ensure no destructive queries are present.
4. If you find a mistake with a column, you must provide the Exact Correct Column in the correction_hint. For example: "Use tx_date instead of date."

You MUST respond strictly in the following JSON format:
{{
    "status": "PASS" | "FAIL",
    "reason": "If FAIL, explain exactly what is wrong. If PASS, leave empty.",
    "correction_hint": "If FAIL, provide the corrected SQL logic. If PASS, leave empty."
}}
"""
        return prompt

    def analyze_query(self, proposed_sql: str, relevant_tables: list) -> dict:
        """
        Executes the Auditor.
        Leverages Groq to enforce schema exactness over hallucinated queries.
        """
        prompt = self.generate_auditor_prompt(proposed_sql, relevant_tables)
        
        try:
            llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, max_retries=3)
            structured_llm = llm.with_structured_output(SentryDecision)
            decision = structured_llm.invoke(prompt)
            return {"status": decision.status, "reason": decision.reason, "correction_hint": decision.correction_hint}
        except Exception as e:
            return {
                "status": "FAIL",
                "reason": f"Sentry Enforcement Failure: {str(e)}",
                "correction_hint": "Check model availability or skip validation."
            }

if __name__ == "__main__":
    sentry = SQLSentry()
    
    # Test 1: The Sentry catches a hallucinated column / bad math
    print("[Testing Sentry -> Failing Scenario]")
    bad_sql = "SELECT SUM(risk_profile) FROM customers;"
    result = sentry.analyze_query(bad_sql, ["customers"])
    print(f"Sentry Verdict: {result['status']}")
    if result['status'] == "FAIL":
        print(f"Reason: {result['reason']}")
        print(f"Correction: {result['correction_hint']}")
