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
    # A small manual verification block (Speed and Clarity check)
    retriever = MetadataRetriever()
    
    test_queries = [
        "How much did the customer spend at Starbucks?",
        "Show me all home loans over 100k",
        "What is my current balance?"
    ]
    
    for query in test_queries:
        print(f"\nUser Query: '{query}'")
        tables = retriever.get_relevant_tables(query)
        print(f"-> Selected Tables: {tables}")
