import os
import json
from src.core.db_engine import DBEngine


class ContextRegistry:
    """
    Just-In-Time (JIT) Metadata Registry.
    Rebuilds the grounding string for LLM agents based on current DB state.
    Uses the shared DBEngine Singleton — never opens its own DuckDB connection.
    """
    def __init__(self):
        self.registry_path = os.path.join(os.path.dirname(__file__), "metadata_registry.json")

    def ingest_file(self, file_path: str):
        """
        Dynamically loads CSV or Excel files into DuckDB via DBEngine.
        """
        import pandas as pd
        from src.core.db_engine import DBEngine
        engine = DBEngine()
        
        table_name = os.path.splitext(os.path.basename(file_path))[0].replace(" ", "_").replace("-", "_")
        
        try:
            con = engine.get_connection()
            if file_path.endswith('.csv'):
                # Direct DuckDB high-speed load - Bypass execute_query sanitizer for admin task
                con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto('{file_path}');")
            elif file_path.endswith(('.xlsx', '.xls')):
                # Pandas bridge for Excel formatting
                df = pd.read_excel(file_path)
                con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
            
            print(f"[ContextRegistry] Successfully ingested {file_path} into table {table_name}")
            return table_name
        except Exception as e:
            print(f"[ContextRegistry] Ingestion Error: {e}")
            raise e

    def build_registry(self):
        """
        Runs DESCRIBE and SELECT * LIMIT 5 on every table via DBEngine.
        Injects Null counts and Markdown snippets for the Supervisor.
        """
        engine = DBEngine()
        tables = engine.list_tables()

        context_string = "=== JIT METADATA REGISTRY (DATA PASSPORT) ===\n"

        for table in tables:
            context_string += f"\nTable Name: {table}\n"
            try:
                # 1. DESCRIBE table — detailed schema & stats
                describe_df = engine.execute_query(f"DESCRIBE {table};")
                context_string += "Table Schema (DESCRIBE):\n"
                context_string += describe_df.to_markdown(index=False) + "\n"

                # 2. Null Counts
                null_counts = {}
                cols_df = engine.execute_query(f"SELECT * FROM {table} LIMIT 1")
                for col in cols_df.columns:
                    count_df = engine.execute_query(f"SELECT COUNT(*) as total_count, COUNT(\"{col}\") as non_null_count FROM {table}")
                    total = count_df.iloc[0]['total_count']
                    non_null = count_df.iloc[0]['non_null_count']
                    null_counts[col] = int(total - non_null)
                
                context_string += f"Null Counts: {null_counts}\n"

                # 3. Clean Markdown Sample (Max 10 columns, 5 rows)
                sample_df = engine.execute_query(f"SELECT * FROM {table} LIMIT 5;")
                if len(sample_df.columns) > 10:
                    sample_df = sample_df.iloc[:, :10]
                
                context_string += "Sample Data (Markdown - Max 10 cols):\n"
                context_string += sample_df.to_markdown(index=False, tablefmt="github") + "\n"

            except Exception as e:
                context_string += f"Error profiling table: {e}\n"

        # Persist to disk
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump({"metadata_context": context_string}, f)

        print(f"[ContextRegistry] Built Data Passport with {len(tables)} tables.")
        return context_string

    def get_metadata_context(self) -> str:
        """Retrieves the persisted JIT metadata context string."""
        if not os.path.exists(self.registry_path):
            return self.build_registry()
        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("metadata_context", "")
        except Exception:
            return self.build_registry()
