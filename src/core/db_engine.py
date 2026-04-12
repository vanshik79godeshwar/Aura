import json
import duckdb
import os
import re
import random
from datetime import date, timedelta

class DBEngine:
    def __init__(self):
        # In-memory database for extreme OLAP speed (Speed Pillar)
        self.conn = duckdb.connect(database=':memory:')
        self._load_assets()

    def _load_assets(self):
        """
        Dynamically loads uploaded CSV files directly into the ultra-fast DuckDB in-process memory.
        This provides a true queryable sandbox based on real dynamic files.
        """
        import glob
        assets_dir = os.path.join(os.path.dirname(__file__), "..", "..", "assets")
        csv_files = glob.glob(os.path.join(assets_dir, "*.csv"))
        
        if not csv_files:
            print("[DBEngine Warning] No CSV files found in assets/. Database is empty.")
            return

        for filepath in csv_files:
            # Table name is the exact filename of the CSV (e.g. 'sales_data')
            table_name = os.path.splitext(os.path.basename(filepath))[0]
            if table_name == "mock_transactions":
                table_name = "transactions"
            
            # Native DuckDB production CSV mounting bridging the tabular state directly into LLM path
            self.conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{filepath}');")
            
        print("[DBEngine] In-Memory DuckDB Initialized with 10 Mock Tables.")


    def sanitize_query(self, sql_string: str) -> bool:
        """
        Security Sandbox (Trust Pillar): Ensure the query ONLY retrieves data.
        Raises ValueError if Destructive queries are found.
        """
        # Remove comments and whitespace padding for inspection
        clean_sql = re.sub(r'--.*$', '', sql_string, flags=re.MULTILINE)
        clean_sql = clean_sql.strip().upper()
        
        # Must start with SELECT
        if not clean_sql.startswith("SELECT"):
            raise ValueError("Security Error: Only SELECT queries are permitted.")

        # Disallow prohibited keywords anywhere (basic blocklist)
        prohibited = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "GRANT", "REVOKE"]
        
        tokens = re.split(r'\s+', clean_sql)
        for p in prohibited:
            if p in tokens:
                raise ValueError(f"Security Error: Prohibited operation '{p}' detected.")
                
        return True

    def execute_query(self, sql_string: str):
        """
        Executes a SQL query after sanitizing it, returning a Pandas DataFrame.
        """
        self.sanitize_query(sql_string)
        # Returns as pandas dataframe utilizing duckdb's incredibly fast C++ conversion
        return self.conn.execute(sql_string).df()

if __name__ == "__main__":
    engine = DBEngine()
    
    # Test 1: Safe Query Execution ---
    print("\n--- Test 1: Safe Query Execution ---")
    safe_sql = "SELECT * FROM sales_data LIMIT 5;"
    print("Executing:", safe_sql)
    df = engine.execute_query(safe_sql)
    print(df)
    
    # Test 2: Destructive Query
    print("\n--- Test 2: Unsafe Query Rejection ---")
    unsafe_sql = "DROP TABLE sales_data;"
    print("Executing:", unsafe_sql)
    try:
        engine.execute_query(unsafe_sql)
    except Exception as e:
        print("[SUCCESS] Blocked successfully ->", str(e))
