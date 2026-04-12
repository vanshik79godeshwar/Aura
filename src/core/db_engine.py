import duckdb
import os
import re

# Resolve the persistent DB path to the project root (d:\AURA\aura.db)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_DB_PATH = os.path.join(_PROJECT_ROOT, "aura.db")


class DBEngine:
    def __init__(self):
        # Persistent DuckDB — tables survive across restarts (Speed + Trust Pillar)
        # All user-uploaded data lives here; no more assets/ CSV dependency.
        self.conn = duckdb.connect(database=_DB_PATH)
        print(f"[DBEngine] Connected to persistent store: {_DB_PATH}")

    def list_tables(self) -> list[str]:
        """Returns all table names currently registered in the DuckDB instance."""
        rows = self.conn.execute("SHOW TABLES").fetchall()
        return [row[0] for row in rows]

    def sanitize_query(self, sql_string: str) -> bool:
        """
        Security Sandbox (Trust Pillar): Ensure the query ONLY retrieves data.
        Raises ValueError if destructive queries are found.
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
        # Returns as pandas dataframe utilizing DuckDB's incredibly fast C++ conversion
        return self.conn.execute(sql_string).df()


if __name__ == "__main__":
    engine = DBEngine()

    tables = engine.list_tables()
    print(f"\n[DBEngine] Tables in store: {tables}")

    if tables:
        test_table = tables[0]
        print(f"\n--- Sampling '{test_table}' ---")
        df = engine.execute_query(f"SELECT * FROM {test_table} LIMIT 5;")
        print(df)
    else:
        print("[DBEngine] No tables found. Upload a CSV from the Streamlit UI first.")
