import os
import json
import duckdb
import pandas as pd

# Resolve paths relative to project root
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_DB_PATH = os.path.join(_PROJECT_ROOT, "aura.db")
_METADATA_FILE = os.path.join(os.path.dirname(__file__), "metadata_dictionary.json")


def auto_generate_metadata():
    """
    Reads all tables directly from the persistent DuckDB (aura.db) and regenerates
    metadata_dictionary.json with up-to-date column names, types, and sample values.

    Why: Replaces the old assets/ CSV scan. DuckDB is now the single source of truth,
    so metadata always mirrors what is actually queryable.
    """
    if not os.path.exists(_DB_PATH):
        print(f"[generate_metadata] No database found at {_DB_PATH}.")
        print("  → Upload a CSV from the Streamlit UI first to create aura.db.")
        return

    conn = duckdb.connect(database=_DB_PATH, read_only=True)
    tables = [row[0] for row in conn.execute("SHOW TABLES").fetchall()]

    if not tables:
        print("[generate_metadata] aura.db exists but contains no tables yet.")
        return

    data = {"tables": {}}

    for table_name in tables:
        print(f"Profiling table: '{table_name}'...")
        try:
            df: pd.DataFrame = conn.execute(f"SELECT * FROM \"{table_name}\" LIMIT 50").df()

            columns_meta = {}
            for col in df.columns:
                col_type = str(df[col].dtype)
                desc = f"Auto-detected column '{col}' representing {col_type} data."

                # Enrich categorical columns with up to 3 example values
                if col_type == "object":
                    unique_vals = [str(x) for x in df[col].dropna().unique()[:3]]
                    if unique_vals:
                        desc += f" Example values: {', '.join(unique_vals)}."

                columns_meta[col] = {"description": desc}

            data["tables"][table_name] = {
                "description": f"Auto-generated schema for dataset '{table_name}'.",
                "columns": columns_meta
            }

        except Exception as e:
            print(f"  [WARNING] Could not profile table '{table_name}': {e}")

    conn.close()

    with open(_METADATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n[SUCCESS] metadata_dictionary.json updated with {len(data['tables'])} table(s).")
    print("  -> Run `python src/core/ingest_metadata.py` to push these to the Vector Engine.")


if __name__ == "__main__":
    auto_generate_metadata()
