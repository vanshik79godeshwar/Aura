import json
import duckdb
import os
import re

class DBEngine:
    def __init__(self):
        # In-memory database for extreme OLAP speed (Speed Pillar)
        self.conn = duckdb.connect(database=':memory:')
        self._initialize_mock_data()

    def _initialize_mock_data(self):
        """
        Reads metadata_dictionary.json and creates empty/dummy tables.
        This provides a sandbox environment until real CSVs are integrated.
        """
        metadata_file = os.path.join(os.path.dirname(__file__), "metadata_dictionary.json")
        if not os.path.exists(metadata_file):
            print("Warning: metadata_dictionary.json not found. Database is empty.")
            return

        with open(metadata_file, "r") as f:
            data = json.load(f)

        for table_name, table_info in data.get("tables", {}).items():
            columns = list(table_info.get("columns", {}).keys())
            if not columns:
                continue
            
            # Default everything to VARCHAR for the mock setup
            col_defs = ", ".join([f"{col} VARCHAR" for col in columns])
            create_stmt = f"CREATE TABLE {table_name} ({col_defs});"
            self.conn.execute(create_stmt)
            
            # Insert one dummy row per table to ensure queries return something verifiable
            dummy_vals = ", ".join(["'mock_data'" for _ in columns])
            insert_stmt = f"INSERT INTO {table_name} VALUES ({dummy_vals});"
            self.conn.execute(insert_stmt)
            
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
    
    # Test 1: Safe Query
    print("\n--- Test 1: Safe Query Execution ---")
    safe_sql = "SELECT * FROM transactions LIMIT 5;"
    print("Executing:", safe_sql)
    df = engine.execute_query(safe_sql)
    print(df)
    
    # Test 2: Destructive Query
    print("\n--- Test 2: Unsafe Query Rejection ---")
    unsafe_sql = "DROP TABLE transactions;"
    print("Executing:", unsafe_sql)
    try:
        engine.execute_query(unsafe_sql)
    except Exception as e:
        print("[SUCCESS] Blocked successfully ->", str(e))
