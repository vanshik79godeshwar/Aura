import os
import chromadb

class MetadataRetriever:
    def __init__(self):
        # We link back to the persistent ChromaDB directory at the root level
        db_path = os.path.join(os.path.dirname(__file__), "..", "..", ".chroma_db")
        self.client = chromadb.PersistentClient(path=db_path)
        try:
            self.collection = self.client.get_collection(name="aura_metadata")
        except Exception as e:
            print(f"Error accessing collection. Have you run ingest_metadata.py? ({e})")
            self.collection = None
        
    def get_relevant_tables(self, user_query: str, top_k: int = 3):
        """
        Uses Contextual Metadata Retrieval to find the most conceptually relevant 
        tables for a given user query.
        """
        tables = []
        if self.collection:
            try:
                results = self.collection.query(
                    query_texts=[user_query],
                    n_results=top_k
                )
                
                # Extract the table names from the results (index 0 because we passed 1 query)
                if results and "metadatas" in results and results["metadatas"]:
                    tables = [meta["table_name"] for meta in results["metadatas"][0]]
            except Exception as e:
                print(f"ChromaDB retrieval error: {e}")

        # Enforce live synchronization and keyword fallback matching
        try:
            from src.core.db_engine import DBEngine
            live_tables = DBEngine().list_tables()
            
            # If the user's query mentions a table name explicitly that wasn't retrieved
            for lt in live_tables:
                if lt.lower() in user_query.lower() and lt not in tables:
                    tables.append(lt)
            
            # If there are very few tables, just provide all of them to ensure context is never missed
            if len(live_tables) <= 3:
                for lt in live_tables:
                    if lt not in tables:
                        tables.append(lt)
            
            # Filter non-existent tables to prevent hallucinated references
            tables = [t for t in tables if t in live_tables]

        except Exception as e:
            print(f"Error fetching live tables: {e}")

        # Deduplicate while preserving order
        return list(dict.fromkeys(tables))

def run_retriever(state: dict) -> dict:
    """
    Worker function for the orchestrator.
    Retrieves Top 3 relevant tables and updates the state.
    """
    retriever = MetadataRetriever()
    query = state.get("user_query", "")
    tables = retriever.get_relevant_tables(query, top_k=3)
    
    print(f"Agent [Retriever]: Top 3 tables identified -> {tables}")
    
    return {
        "relevant_tables": tables,
        "current_status": f"Retrieved {len(tables)} relevant tables"
    }

if __name__ == "__main__":
    # Interactive Console for Contextual Metadata Retrieval
    print("\n" + "="*50)
    print("🚀 AURA: CONTEXTUAL METADATA RETRIEVER")
    print("Type a natural language question to see which internal tables")
    print("the Vector Database mathematically matches to your intent.")
    print("Type 'exit' or 'quit' to stop.")
    print("="*50 + "\n")
    
    retriever = MetadataRetriever()
    
    while True:
        try:
            query = input("\n[Aura User] ➤ ")
            if query.strip().lower() in ['exit', 'quit']:
                print("\n[System] Exiting contextual search...")
                break
            
            if not query.strip():
                continue
                
            # Calling the retrieval engine to pull Top 3 relevant files
            tables = retriever.get_relevant_tables(query, top_k=3)
            
            print("\n[Vector Search Engine] -> Top Relevant Tables Found:")
            for idx, table in enumerate(tables, 1):
                print(f"   {idx}. {table}")
                
        except KeyboardInterrupt:
            print("\n[System] Exiting contextual search...")
            break
