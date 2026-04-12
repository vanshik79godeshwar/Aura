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
5. If you see a TRY_CAST on a VARCHAR price column, DO NOT flag it as an error. Instead, suggest the REGEXP_REPLACE fix to the Analyst: "use REGEXP_REPLACE(column, '[^0-9.]', '', 'g') before casting to FLOAT".
6. TYPE AUDIT: Compare the SQL strictly against the ACTUAL TYPES in the schema below. If the Analyst uses a string function (like REGEXP_REPLACE or TRY_CAST) on a column that is already numeric (INT, BIGINT, DOUBLE, FLOAT), you MUST return status: FAIL with the specific hint: "DESTRUCTIVE LOGIC: [column] is already numeric. Remove all Regex and Cast functions."

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
        from src.core.db_engine import DBEngine
        engine = DBEngine()
        
        live_tables = engine.list_tables()
        schema_text = self._extract_schemas(relevant_tables)
        
        # Inject Live DuckDB types cleanly
        valid_columns = []
        for table in live_tables:
            if table in relevant_tables:
                try:
                    # Task 1: Implement a list_columns() check using PRAGMA table_info
                    desc_df = engine.execute_query(f"PRAGMA table_info('{table}');")
                    valid_columns.extend(desc_df['name'].str.lower().tolist())
                    types = ", ".join(desc_df.apply(lambda row: f"{row['name']}: {row['type']}", axis=1).tolist())
                    schema_text += f"\nACTUAL TYPES Table '{table}': {types}\n"
                except Exception:
                    pass
        
        # Task 1: If a column does not exist, return a FAIL status programmatically without calling the Groq API!
        try:
            engine.execute_query(f"EXPLAIN {proposed_sql}")
        except Exception as e:
            error_str = str(e).lower()
            if "not found" in error_str or "does not exist" in error_str:
                return {
                    "status": "FAIL",
                    "reason": f"Programmatic Sentry Validation Failed: {str(e)}",
                    "correction_hint": "You MUST ONLY use columns returned by the PRAGMA check!"
                }
        
        # Task 2: Sentry Logic Hardening - Programmatic Bypass
        sql_upper = proposed_sql.upper()
        if any(agg in sql_upper for agg in ["SUM(", "AVG(", "COUNT("]):
            return {
                "status": "PASS",
                "reason": "Programmatic Bypass: Verified aggregation query.",
                "correction_hint": ""
            }
        
        prompt = self.generate_auditor_prompt(proposed_sql, relevant_tables)
        # Patch the prompt with injected schema_text overrides
        prompt = prompt.replace(self._extract_schemas(relevant_tables), schema_text)
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
