import duckdb
import os
import re
import glob
import threading

# Resolve the persistent DB path to the project root
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_DB_PATH = os.path.join(_PROJECT_ROOT, "aura.db")


class DBEngine:
    """
    Strict Singleton DuckDB connection factory.

    Rules:
    - Only ONE duckdb.connect() call ever happens — here, in __new__.
    - All agents and utilities must call DBEngine() to get the shared instance.
    - No other file in the project may call duckdb.connect() directly.
    - Thread safety is achieved via a threading.Lock on the class level.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """
        Thread-safe singleton pattern using double-checked locking to ensure
        strictly one DuckDB connection instance across all agents.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    # Initialize the connection once
                    cls._instance.conn = duckdb.connect(
                        database=_DB_PATH,
                        config={"allow_unsigned_extensions": "true"}
                    )
                    cls._instance._closed = False
                    print(f"[DBEngine] Unified DB Engine initialized: {_DB_PATH}")
                    # cls._instance._load_legacy_assets()
        return cls._instance

    def __init__(self):
        # All initialization happens in __new__
        pass

    def get_connection(self):
        """Returns the shared DuckDB connection object. Re-initializes if closed."""
        if self._closed or self.conn is None:
            with self.__class__._lock:
                # Reset instance to force re-initialization on next call
                self.__class__._instance = None
                return DBEngine().conn
        return self.conn

    def close(self):
        """
        Gracefully closes the connection and resets the Singleton instance.
        Necessary for 'Nuclear' Clear Session to release file locks.
        """
        with self.__class__._lock:
            if hasattr(self, 'conn') and self.conn and not self._closed:
                try:
                    self.conn.close()
                    print("[DBEngine] 🔒 Connection closed gracefully.")
                except Exception as e:
                    print(f"[DBEngine] Error during close: {e}")
                finally:
                    self._closed = True
            
            # Resetting the singleton to allow fresh initialization
            self.__class__._instance = None

    def _load_legacy_assets(self):
        """
        Fallback: loads CSVs from assets/ into the persistent DB
        if the tables do not already exist.
        """
        assets_dir = os.path.join(_PROJECT_ROOT, "assets")
        csv_files = glob.glob(os.path.join(assets_dir, "*.csv"))

        if not csv_files:
            return

        for filepath in csv_files:
            file_name = os.path.splitext(os.path.basename(filepath))[0]
            table_name = "transactions" if file_name == "mock_transactions" else file_name
            try:
                self.conn.execute(
                    f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM read_csv_auto('{filepath}');"
                )
            except Exception as e:
                print(f"[DBEngine] Note: Table '{table_name}' already exists or failed to seed: {e}")

    def list_tables(self) -> list[str]:
        """Returns all table names currently registered in the DuckDB instance."""
        cursor = self.conn.cursor()
        try:
            rows = cursor.execute("SHOW TABLES").fetchall()
            return [row[0] for row in rows]
        finally:
            cursor.close()

    def register_dataframe(self, df, table_name: str):
        """
        Registers a Pandas DataFrame as a DuckDB table (CREATE OR REPLACE).
        Used exclusively by sidebar upload — replaces raw duckdb.connect() calls there.
        """
        self.conn.register("_upload_df", df)
        self.conn.execute(f'CREATE OR REPLACE TABLE "{table_name}" AS SELECT * FROM _upload_df')
        self.conn.unregister("_upload_df")

    def sanitize_query(self, sql_string: str) -> bool:
        """Security Sandbox: ensure the query only retrieves data."""
        clean_sql = re.sub(r'--.*$', '', sql_string, flags=re.MULTILINE)
        clean_sql = clean_sql.strip().upper()

        if not clean_sql.startswith("SELECT") and not clean_sql.startswith("EXPLAIN") and not clean_sql.startswith("PRAGMA"):
            raise ValueError("Security Error: Only SELECT/EXPLAIN/PRAGMA queries are permitted.")

        prohibited = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "GRANT", "REVOKE"]
        tokens = re.split(r'\s+', clean_sql)
        for p in prohibited:
            if p in tokens:
                raise ValueError(f"Security Error: Prohibited operation '{p}' detected.")

        return True

    def execute_query(self, sql_string: str):
        """
        Executes a SQL query after sanitizing it, returning a Pandas DataFrame.
        Uses an explicit cursor to prevent thread-level connection locking.
        """
        self.sanitize_query(sql_string)
        cursor = self.conn.cursor()
        try:
            return cursor.execute(sql_string).df()
        finally:
            cursor.close()


if __name__ == "__main__":
    engine = DBEngine()
    tables = engine.list_tables()
    print(f"\n[DBEngine] Active Tables: {tables}")

    if tables:
        test_table = "transactions" if "transactions" in tables else tables[0]
        print(f"\n--- Sampling '{test_table}' ---")
        df = engine.execute_query(f"SELECT * FROM {test_table} LIMIT 5;")
        print(df)