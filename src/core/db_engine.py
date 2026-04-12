import duckdb
import os
import re
import glob

# Resolve the persistent DB path to the project root (d:\AURA\aura.db)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_DB_PATH = os.path.join(_PROJECT_ROOT, "aura.db")

class DBEngine:
    def __init__(self):
        # Persistent DuckDB — tables survive across restarts (Speed + Trust Pillar)
        # This connects to the DB file where your teammates' UI uploads are stored.
        self.conn = duckdb.connect(database=_DB_PATH)
        print(f"[DBEngine] Connected to persistent store: {_DB_PATH}")
        
        # Load legacy assets ONLY if they aren't already in the persistent store
        self._load_legacy_assets()

    def _load_legacy_assets(self):
        """
        Fallback logic: Automatically loads CSVs from assets/ into the persistent DB
        if the tables do not already exist. Standardizes 'mock_transactions' to 'transactions'.
        """
        assets_dir = os.path.join(_PROJECT_ROOT, "assets")
        csv_files = glob.glob(os.path.join(assets_dir, "*.csv"))
        
        if not csv_files:
            return

        for filepath in csv_files:
            file_name = os.path.splitext(os.path.basename(filepath))[0]
            # Standardize naming for the AI agents
            table_name = "transactions" if file_name == "mock_transactions" else file_name
            
            # Use DuckDB native reading; 'IF NOT EXISTS' prevents overwriting UI uploads
            try:
                self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM read_csv_auto('{filepath}');")
            except Exception as e:
                print(f"[DBEngine] Note: Table {table_name} already exists or failed to seed: {e}")

    def list_tables(self) -> list[str]:
        """Returns all table names currently registered in the DuckDB instance."""
        rows = self.conn.execute("SHOW TABLES").fetchall()
        return [row[0] for row in rows]

    def sanitize_query(self, sql_string: str) -> bool:
        """
        Security Sandbox (Trust Pillar): Ensure the query ONLY retrieves data.
        """
        clean_sql = re.sub(r'--.*$', '', sql_string, flags=re.MULTILINE)
        clean_sql = clean_sql.strip().upper()

        if not clean_sql.startswith("SELECT"):
            raise ValueError("Security Error: Only SELECT queries are permitted.")

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
        # Returns as pandas dataframe utilizing DuckDB's fast C++ conversion
        return self.conn.execute(sql_string).df()

if __name__ == "__main__":
    engine = DBEngine()
    tables = engine.list_tables()
    print(f"\n[DBEngine] Active Tables: {tables}")

    if tables:
        test_table = "transactions" if "transactions" in tables else tables[0]
        print(f"\n--- Sampling '{test_table}' ---")
        df = engine.execute_query(f"SELECT * FROM {test_table} LIMIT 5;")
        print(df)