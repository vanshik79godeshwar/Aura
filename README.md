# Project Aura: Self-Service Intelligence Mesh

## Overview
Aura is an intelligent "Talk-to-Data" interface designed to solve the friction of data analysis for non-technical users. It empowers everyday users to ask natural language questions and receive fast, trustworthy, and verified insights without complex workflows or unclear terminology. 

## Features
* **Agentic Semantic Layer:** Translates vague business queries into strict, consistent schema metrics using Contextual Metadata Retrieval (ChromaDB).
* **Automated Data Visualizer:** Heuristically determines the best chart type (Plotly) based on raw data inputs without requiring user configuration.
* **The "Trust Trace":** A transparent UI expander that explicitly shows the AI's reasoning steps and the exact source data rows used to formulate the answer.
* **Self-Correcting Execution:** Uses LangGraph to route errors back to the analytical agent for code correction before presenting failure to the user.

## Tech Stack
* **Orchestration:** LangGraph, Python 3.10+
* **LLM:** Google Gemini 2.5 Flash (`langchain-google-genai`)
* **Databases:** DuckDB (In-memory analytical SQL), ChromaDB (Vector store for semantic schema)
* **Frontend:** Streamlit, Plotly

## Install and Run Instructions
1. Clone the repository and navigate to the project root.
2. Install dependencies: `pip install -r requirements.txt`
3. Initialize the Vector Database: `python src/core/ingest_metadata.py`
4. Copy `.env.example` to `.env` and add your `GEMINI_API_KEY`.
5. Launch the application: `streamlit run src/ui/app.py`

## Architecture Notes
Aura utilizes a **Modular Intelligent Mesh**. Instead of a single prone-to-hallucination prompt, tasks are decomposed. The Master Orchestrator routes the user query to a Lexicon Agent (for schema mapping), then an Analyst Agent (for strict SQL execution via DuckDB), and finally a Storyteller Agent (for jargon-free synthesis).