"""
Sidebar layout module.
Why it exists: To hold tools, settings, and file uploads, keeping the main chat clear
for a focused user experience (Clarity pillar).

Upload Pipeline (DuckDB-Centric):
  User uploads CSV/XLSX
    → DataFrame saved as table in aura.db (persistent DuckDB)
    → generate_metadata() re-profiles all tables → metadata_dictionary.json
    → ingest() re-indexes into ChromaDB vector engine
    → All downstream agents (retriever, analyst, sentry) work on aura.db automatically
"""
import os
import sys
import duckdb
import pandas as pd
import streamlit as st

# Ensure project root is on path so src.core imports resolve correctly
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_DB_PATH = os.path.join(_PROJECT_ROOT, "aura.db")


def _save_to_duckdb(df: pd.DataFrame, table_name: str):
    """Persist a DataFrame as a DuckDB table in aura.db. Replaces same-named table."""
    conn = duckdb.connect(database=_DB_PATH)
    # Register the DataFrame so DuckDB SQL can reference it
    conn.register("_upload_df", df)
    conn.execute(f'CREATE OR REPLACE TABLE "{table_name}" AS SELECT * FROM _upload_df')
    conn.close()


def _run_pipeline():
    """Regenerate metadata and re-index ChromaDB after a new upload."""
    from src.core.generate_metadata import auto_generate_metadata
    from src.core.ingest_metadata import ingest

    auto_generate_metadata()
    ingest()


def render_sidebar():
    """
    Renders the sidebar components.
    Why it exists: To organize system configurations and data inputs in one place.
    """
    with st.sidebar:
        st.title("✨ Aura Settings")
        st.markdown("Upload your data and start talking — Aura handles the rest.")

        uploaded_file = st.file_uploader(
            "Data Source",
            type=["csv", "xlsx"],
            label_visibility="hidden",
            key="data_uploader"
        )

        st.markdown("---")

        if uploaded_file:
            # Guard: only process once per unique uploaded file (avoid re-run loops)
            file_key = f"processed_{uploaded_file.name}_{uploaded_file.size}"
            if st.session_state.get(file_key):
                st.success(f"✅ Ready: **{uploaded_file.name}**")
                st.caption("Data is live in AURA's query engine.")
            else:
                table_name = os.path.splitext(uploaded_file.name)[0].replace(" ", "_").lower()

                with st.status(f"Loading **{uploaded_file.name}**...", expanded=True) as status:
                    try:
                        # Step 1: Read file into DataFrame
                        st.write("📂 Reading file...")
                        if uploaded_file.name.endswith(".xlsx"):
                            df = pd.read_excel(uploaded_file)
                        else:
                            df = pd.read_csv(uploaded_file)

                        # Step 2: Persist to DuckDB
                        st.write(f"🦆 Saving `{table_name}` to AURA database...")
                        _save_to_duckdb(df, table_name)

                        # Step 3: Regenerate metadata + re-index vectors
                        st.write("🧠 Profiling schema and re-indexing vector engine...")
                        _run_pipeline()

                        status.update(label="✅ Upload complete!", state="complete", expanded=False)
                        st.session_state[file_key] = True
                        st.success(f"✅ Ready: **{uploaded_file.name}** → `{table_name}` table")
                        st.caption(f"Rows: {len(df):,} | Columns: {len(df.columns)}")

                    except Exception as e:
                        status.update(label="❌ Upload failed", state="error", expanded=True)
                        st.error(f"Error processing file: {e}")
        else:
            st.info("⬆️ Upload a CSV or Excel file to begin.")
