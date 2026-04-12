import json
import os
import chromadb

def ingest():
    db_path = os.path.join(os.path.dirname(__file__), "..", "..", ".chroma_db")
    client = chromadb.PersistentClient(path=db_path)
    
    # Aggressively delete the old collection to destroy NatWest ghost data
    try:
        client.delete_collection(name="aura_metadata")
        print("Purged old ghost matrix.")
    except Exception:
        pass
        
    # The default embedding function is all-MiniLM-L6-v2 which is applied automatically
    collection = client.create_collection(name="aura_metadata")
    
    metadata_file = os.path.join(os.path.dirname(__file__), "metadata_dictionary.json")
    with open(metadata_file, "r") as f:
        data = json.load(f)
        
    documents = []
    metadata = []
    ids = []
    
    for table_name, table_info in data.get("tables", {}).items():
        desc = table_info.get("description", "")
        cols = ", ".join([f"{c} ({c_info['description']})" for c, c_info in table_info.get("columns", {}).items()])
        doc_string = f"Table '{table_name}': {desc} Columns: {cols}"
        
        documents.append(doc_string)
        metadata.append({"table_name": table_name})
        ids.append(table_name)
        
    print(f"Ingesting {len(documents)} tables into ChromaDB...")
    
    # ChromaDB's add method will overwrite entirely or error if IDs exist, so we use upsert
    collection.upsert(
        documents=documents,
        metadatas=metadata,
        ids=ids
    )
    print(f"Ingestion complete! Successfully added {len(documents)} tables to the vector search engine.")

if __name__ == "__main__":
    ingest()
