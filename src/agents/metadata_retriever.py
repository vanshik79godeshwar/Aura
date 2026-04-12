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
        if not self.collection:
            return []

        results = self.collection.query(
            query_texts=[user_query],
            n_results=top_k
        )
        
        # Extract the table names from the results (index 0 because we passed 1 query)
        if results and "metadatas" in results and results["metadatas"]:
            tables = [meta["table_name"] for meta in results["metadatas"][0]]
            return tables
        return []

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
