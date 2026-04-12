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

        st.title("Aura Settings")
        
        with st.container(border=True):
            uploaded_files = st.file_uploader("Data Source", type=["csv", "xlsx"], label_visibility="hidden", accept_multiple_files=True)
        
        st.markdown("---")
        
        if st.button("🧹 Clear Session", use_container_width=True):
            st.session_state.clear()
            st.session_state["retry_count"] = 0
            
            try:
                from src.core.db_engine import DBEngine
                engine = DBEngine()
                if hasattr(engine, 'conn') and engine.conn:
                    engine.conn.close()
                DBEngine._instance = None
            except Exception:
                pass
                
            import shutil
            if os.path.exists(_DB_PATH):
                try: os.remove(_DB_PATH)
                except: pass
            chroma_path = os.path.join(_PROJECT_ROOT, ".chroma_db")
            if os.path.exists(chroma_path):
                try: shutil.rmtree(chroma_path)
                except: pass
            st.rerun()
            
        st.markdown("---")

        if uploaded_files:
            new_uploads = False
            
            # Step 1: Save all new uploads to DuckDB
            for uploaded_file in uploaded_files:
                file_key = f"processed_{uploaded_file.name}_{uploaded_file.size}"
                table_name = os.path.splitext(uploaded_file.name)[0].replace(" ", "_").lower()
                
                if st.session_state.get(file_key):
                    st.success(f"✅ Ready: **{uploaded_file.name}**")
                    st.caption(f"`{table_name}` table is live in AURA's database.")
                else:
                    new_uploads = True
                    with st.status(f"Loading **{uploaded_file.name}**...", expanded=True) as status:
                        try:
                            st.write("📂 Reading file...")
                            if uploaded_file.name.endswith(".xlsx"):
                                df = pd.read_excel(uploaded_file)
                            else:
                                df = pd.read_csv(uploaded_file)

                            st.write(f"🦆 Saving `{table_name}` to AURA database...")
                            _save_to_duckdb(df, table_name)
                            
                            status.update(label=f"✅ {uploaded_file.name} parsed!", state="complete", expanded=False)
                            st.session_state[file_key] = True
                            st.success(f"✅ Ready: **{uploaded_file.name}** → `{table_name}` table")
                            st.caption(f"Rows: {len(df):,} | Columns: {len(df.columns)}")
                        except Exception as e:
                            status.update(label=f"❌ Upload failed for {uploaded_file.name}", state="error", expanded=True)
                            st.error(f"Error processing file: {e}")
            
            # Step 2: If any new files were added, we rebuild the semantic vector index ONE TIME for all of them
            if new_uploads:
                with st.spinner("🧠 Profiling new tables and re-indexing AURA's vector engine..."):
                    try:
                        _run_pipeline()
                        st.info("✅ System synced. Aura is ready to answer questions across all datasets.")
                    except Exception as e:
                        st.error(f"Failed to rebuild index: {e}")
        else:
            st.info("⬆️ Upload CSV or Excel file(s) to begin.")
