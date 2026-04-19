# 🌟 Project Aura: Self-Service Intelligence Mesh

**Official Hackathon Submission (v1.0)**: The core functional version submitted for the NatWest challenge can be found at this historical snapshot:  
    [🔗 View v1.0 Submission Archive](https://github.com/vanshik79godeshwar/Aura/tree/303998801ab7d70949a012ff9cdd839cb711cbea)

**Current Version (v2.0 - Active)**: Features the **Supervisor-Specialist Hub** refactor, enhanced **JIT Data Passports**, and a self-correcting autonomous reasoning engine.

## 📚 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Install and Run Instructions](#install-and-run-instructions)
- [Tech Stack](#tech-stack)
  - [Frontend & User Interface](#frontend--user-interface)
  - [AI & Agent Orchestration (Intelligent Mesh)](#ai--agent-orchestration-intelligent-mesh)
  - [Databases & Data Processing](#databases--data-processing)
  - [Embeddings & Modeling](#embeddings--modeling)
  - [Environment & Configuration](#environment--configuration)
- [Usage Examples](#usage-examples)
- [Architecture Notes](#architecture-notes)

## Overview
**Aura: The Self-Service Intelligence Mesh** is a multi-agent, AI-driven data intelligence system that enables users to interact with structured datasets through natural language. It transforms raw data into actionable insights by combining semantic understanding, deterministic query execution, and automated reasoning within a modular agent architecture.

The system addresses the challenge of extracting reliable and understandable insights from complex data without requiring technical expertise. It is designed for non-technical stakeholders such as business analysts, decision-makers, and domain experts who need fast, trustworthy, and explainable answers from their data.

## Features

- **Natural Language Query Interface**  
  Users can query structured data using plain language, which is translated into executable analytical tasks.

- **Semantic Mapping Layer**  
  Maps user intent to relevant tables, columns, and metrics using a defined schema and metadata-driven matching.

- **Deterministic SQL Execution (DuckDB)**  
  Executes generated queries on structured datasets with fast, in-memory processing to ensure accurate results.

- **Multi-Agent Workflow Orchestration**  
  Uses a modular agent pipeline to handle task decomposition, query generation, validation, and response synthesis.

- **Query Validation and Safety Checks**  
  Validates generated queries to prevent invalid column references and ensures logical consistency of results.

- **Automated Data Visualization**  
  Converts query outputs into appropriate charts (e.g., bar, line) for easier interpretation.

- **Explainable Output Generation**  
  Produces concise, human-readable summaries of results, translating raw outputs into meaningful insights.

- **Transparent Execution Trace**  
  Displays the generated query and data source used, enabling users to verify how results were derived.

## Install and Run Instructions
1. Clone the repository and navigate to the project root.
2. Install dependencies: 
   ```bash
   pip install -r requirements.txt
   cd frontend
   npm install
   ```
3. Copy `.env.example` to `.env` and add your `GROQ_API_KEY`.
4. Launch the application: 
   ```bash
   python -m uvicorn src.api.main:app --reload
   cd frontend 
   npm run dev
   ```

## Tech Stack

### Frontend & User Interface
- **Vite**: Web application framework for building the primary user interface.
- **React**: Library for building user interfaces.
- **Plotly**: Interactive graphing library for automated data visualization.
- **TailwindCSS**: Utility-first CSS framework for styling.

### AI & Agent Orchestration (Intelligent Mesh)
- **LangGraph**: Multi-agent workflow orchestration and state management.
- **LangChain**: Core framework for building LLM-powered applications.
- **Google GenAI (langchain-google-genai)**: Integration for accessing Gemini models.
- **Groq (langchain-groq)**: High-speed LLM inference engine API integration.

### Databases & Data Processing
- **DuckDB**: In-memory analytical SQL database for deterministic query execution.
- **ChromaDB**: Vector database for semantic mapping and metadata retrieval.
- **Pandas**: Data manipulation and analysis library.
- **openpyxl**: Library for reading and writing Excel (.xlsx) files.

### Embeddings & Modeling
- **Sentence-Transformers**: Used for generating semantic text embeddings for vector search.
- **Pydantic**: Data validation and schema enforcement using type hints.

### Environment & Configuration
- **python-dotenv**: Manages environment variables (e.g., API keys) using `.env` files.

## Usage Examples

1. **Running the Application**  
   running the server and web interface:
   ```bash
   python -m uvicorn src.api.main:app --reload
   cd frontend 
   npm run dev
   ```
   This launches the web interface where users can upload data and interact with the system.
   

3. **Uploading Data**  
   Upload a structured dataset (CSV or Excel file) through the UI. The system automatically:
   - Parses the data using Pandas.
   - Registers schema metadata.
   - Stores embeddings in ChromaDB for semantic mapping.
  ![WhatsApp Image 2026-04-12 at 20 39 54](https://github.com/user-attachments/assets/5575a0f5-d0fe-42ad-83c3-a9e6c6c287ce)



4. **Example Queries**  
   Users can interact using natural language:

   - **Input:** What was the total revenue last month?  
     **Output:** 
     - Aggregated revenue value
     - Corresponding SQL query
     - Visualization (e.g., bar/line chart)

   - **Input:** Compare sales between North and South regions.  
     **Output:** 
     - Comparative breakdown table
     - Visualization (grouped bar chart)
     - Summary explanation

   - **Input:** Why did revenue drop in February?  
     **Output:** 
     - Identified contributing factors
     - Supporting data breakdown
     - Explanation generated from analysis
![WhatsApp Image 2026-04-12 at 20 41 42](https://github.com/user-attachments/assets/3cf85730-8c94-4594-a521-70e615b94fff)

5. **Query Transparency (Trust Trace)**  
   For every query, the system provides:
   - Generated SQL query
   - Tables and columns used
   - Intermediate data (if applicable)

   This ensures full transparency and allows users to verify results.

6. **API Usage (Optional Backend)**  
   If running the backend API separately:
   ```bash
   python -m uvicorn src.api.main:app --reload
   ```
   Example API request:
   ```bash
   curl -X POST "http://localhost:8000/query" \
   -H "Content-Type: application/json" \
   -d '{"query": "Show total sales by region"}'
   ```
   Response:
   ```json
   {
     "summary": "Sales are highest in the North region",
     "data": [...],
     "sql_query": "SELECT region, SUM(sales) FROM table GROUP BY region"
   }
   ```

7. **Visualization Output**  
   Charts are generated automatically based on query type. Supported visualizations include:
   - Line charts (time series)
   - Bar charts (comparisons)
   - Tables (aggregated results)
![WhatsApp Image 2026-04-12 at 20 42 02](https://github.com/user-attachments/assets/6c73f7bd-d1ae-4a99-ae59-4337a5f46f42)

8. **Notes**
   - Ensure the dataset is clean and properly formatted.
   - Column names should be meaningful for better semantic mapping.
   - Large datasets may increase processing time depending on complexity.
![WhatsApp Image 2026-04-12 at 20 45 38](https://github.com/user-attachments/assets/9631da0b-d47f-4ef3-b2fa-76fba6134b34)
![WhatsApp Image 2026-04-12 at 20 47 10](https://github.com/user-attachments/assets/d79f7132-ffff-4a6a-93a8-8b5508dce62d)
