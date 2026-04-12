# 🚀 Progress Report: Meet Modi
- **Role:** Data / AI Engineer
- **Component:** Core Agent Logic & Data Integrity
- **Current Status:** In Progress
- **Project:** Talk-to-Data System (Project Aura for NatWest Hackathon)

---

## Technical Achievements & Completed Tasks

### Step A: Building The Semantic Foundation (The Metadata "Atlas")

Before the AI could intelligently query the database, it needed a strict map of what the data actually represents.
- **What I built:** I created a unified configuration file at `src/core/metadata_dictionary.json`.
- **Details:** I manually architected a mock banking schema representing NatWest data environments, encompassing **10 distinct tables** (e.g., *Transactions, Customers, Mortgages, Credit Cards, Branches*). For each table and column, I laid out clear, human-readable descriptions (like mapping `amt` to "Transaction amount in GBP").
- **Hackathon Pillar Alignment:** This adheres to **Clarity and Trust**. It effectively prevents the LLM from "guessing" or hallucinating what a cryptic column name means, ensuring the AI grounds its logic strictly on documented bank schema instead of assumptions.

### Step B: The Vector Search Engine (Contextual Metadata Retrieval)

Handling a large enterprise schema with 50+ tables means we cannot feed everything into the LLM's context window simultaneously without causing token overflow and degradation in reasoning. 
- **What I built:** I integrated **ChromaDB** and `sentence-transformers` into our local stack to construct a high-performance Vector Database.
- **Details:** 
  1. I wrote `src/core/ingest_metadata.py` which extracts every table string from our "Atlas", converts it into high-dimensional vector embeddings, and stores it persistently in a local `.chroma_db`. 
  2. I developed `src/agents/metadata_retriever.py`, effectively our first Sub-Agent. When a user asks a question (e.g., *"Show me all high-value home loans"*), this retriever converts the prompt into an embedding and calculates the **Cosine Similarity** against our database. It isolates only the top 3-5 most pertinent tables.
- **Hackathon Pillar Alignment:** This is directly built for **Speed and Trust**. By strictly filtering the database context locally *before* giving the data to the LLM, we guarantee lightning-fast response times and eliminate the risk of the LLM fetching the wrong data table for its queries. 
- **The Pitch:** We can confidently tell the judges that we are leveraging *"Contextual Metadata Retrieval"* to bypass the standard limitations of RAG hallucinations.

---
## Upcoming Agenda
- Integration of the retrieved metadata directly into a query-building LLM agent.
- Translating natural language directly to SQL utilizing the verified context.
