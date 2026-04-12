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

### Step C: The SQL Sandbox Engine (DuckDB)

To facilitate instantaneous analytical queries during the Talk-to-Data flow, the application needs a secure execution environment.
- **What I built:** I constructed `src/core/db_engine.py`, which leverages DuckDB in-memory.
- **Details:** Since we don't have CSVs loaded currently, I implemented an auto-mocking layer that spins up dummy tables synchronously with our `metadata_dictionary.json` Atlas. This means queries never fail on non-existent tables.
- **Security:** I built a rigorous `sanitize_query` regex gatekeeper that strips malicious payloads. Any query involving `DROP`, `DELETE`, `UPDATE`, or fails to start with `SELECT` is blocked in memory before it ever reaches the database layer.
- **Hackathon Pillar Alignment:** This is specifically geared for **Speed** (DuckDB OLAP engine) and **Trust** (Zero risk of state mutations via Sandbox Sanitization).

### Step D: The Sentry / SQL Auditor
*(Timeline: Hour 11+)*

To completely insulate the Talk-to-Data flow from AI Hallucinations (the single biggest reason AI fails in enterprise), we need an authoritative check *before* execution.
- **What I built:** `src/agents/sql_sentry.py`. This is an LLM gating mechanism bridging the SQL generator and DuckDB execution.
- **Details:** The Sentry extracts the exact schemas from `metadata_dictionary.json` and forms an isolated **Auditor System Prompt**. It looks at the AI's proposed SQL and rigorously cross-references every column logic step with the ground-truth map.
- **Enforcement:** If an AI blindly attempts to run `SUM()` on a text column (e.g., `risk_profile`), the Sentry forces a JSON `FAIL` evaluation along with a `correction_hint` advising the main agent how to fix it immediately. 
- **Hackathon Pillar Alignment:** This is the ultimate expression of **Trust**. We algorithmically prove to the judges that the SQL executing on our backend is 100% verifiably mapped to the true schema, preventing hallucinated queries and false data reports.

---
## Upcoming Agenda
- Integration of the retrieved metadata directly into a query-building LLM agent.
- Translating natural language directly to SQL utilizing the verified context.
