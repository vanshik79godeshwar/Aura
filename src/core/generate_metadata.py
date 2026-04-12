import os
import glob
import pandas as pd
import json

def auto_generate_metadata():
    """
    Acts as the 'Auto-Map' utility. 
    Scans the assets/ folder for newly uploaded CSVs. If it finds one that doesn't 
    exist in the metadata_dictionary, it reads the headers automatically using Pandas 
    and scaffolds the metadata.
    """
    assets_dir = os.path.join(os.path.dirname(__file__), "..", "..", "assets")
    metadata_file = os.path.join(os.path.dirname(__file__), "metadata_dictionary.json")
    
    # We force a completely clean slate, aggressively wiping former ghost dummy tables.
    data = {"tables": {}}
        
    csv_files = glob.glob(os.path.join(assets_dir, "*.csv"))
    
    updated = False
    for filepath in csv_files:
        table_name = os.path.splitext(os.path.basename(filepath))[0]
        
        # Unconditionally process and overwrite since we want perfectly parallel CSV alignment
        print(f"Discovered strict Asset: {table_name}. Profiling headers and sampling data...")
        try:
            # Read 50 rows to securely get headers, infer Data Types, and grab sample values
            df = pd.read_csv(filepath, nrows=50)
            
            columns_meta = {}
            for col in df.columns:
                col_type = str(df[col].dtype)
                desc = f"Auto-detected column '{col}' representing {col_type} data."
                
                # If the data is text/categorical, inject up to 3 unique sample values into the description!
                if col_type == 'object':
                    unique_vals = [str(x) for x in df[col].dropna().unique()[:3]]
                    if unique_vals:
                        desc += f" Example values: {', '.join((unique_vals))}."

                columns_meta[col] = {
                    "description": desc
                }
            
            data["tables"][table_name] = {
                "description": f"Auto-generated schema for dataset {table_name}.",
                "columns": columns_meta
            }
            updated = True
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
                
    if updated:
        with open(metadata_file, "w") as f:
            json.dump(data, f, indent=2)
        print("\n[SUCCESS] metadata_dictionary.json dynamically updated with new CSV structures!")
        print("-> RUN `python src/core/ingest_metadata.py` next to push these to the Vector Engine.")
    else:
        print("[INFO] No unidentified CSV files found. Metadata dictionary is up to date.")

if __name__ == "__main__":
    auto_generate_metadata()
