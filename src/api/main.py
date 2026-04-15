from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import pandas as pd
import io
import json
import shutil
import asyncio
from src.agents.orchestrator import app as aura_graph
from src.core.registry import ContextRegistry
from src.core.workspace import reset_execution_state, AgentWorkspace

app = FastAPI(title="Aura Platinum API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    active_upload: str = ""

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only CSV or Excel files are supported.")
    
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    registry = ContextRegistry()
    registry.ingest_file(file_path)
    registry.build_registry()
    
    return {"filename": file.filename, "status": "ingested"}

@app.post("/query")
async def execute_query(req: QueryRequest):
    """
    Streaming Endpoint: Emits execution steps before the final payload.
    """
    async def stream_logic():
        registry = ContextRegistry()
        registry.build_registry()
        
        initial_state: AgentWorkspace = {
            "user_query": req.query,
            "identified_metrics": [],
            "relevant_tables": [],
            "metadata_context": registry.get_metadata_context(),
            "logical_plan": {},
            "sql_query": "",
            "error_logs": [],
            "current_status": "initialized",
            "next_action": "",
            "active_upload": req.active_upload
        }
        
        state = reset_execution_state(initial_state)
        
        # Node Map for "Dope Look"
        node_map = {
            "metadata_retriever": "STRATEGIC ROUTING",
            "supervisor": "LOGIC DECOMPOSITION",
            "analyst_and_math": "EXECUTION VALIDATION",
            "visualizer_and_storyteller": "INSIGHT SYNTHESIS"
        }

        # Step 1: Initial Emit
        yield json.dumps({"type": "step", "content": "STRATEGIC ROUTING"}) + "\n"
        
        # Execute Graph via Stream
        for output in aura_graph.stream(state):
            for node_name, state_update in output.items():
                state.update(state_update)
                if node_name in node_map:
                    yield json.dumps({"type": "step", "content": node_map[node_name]}) + "\n"
                await asyncio.sleep(0.1) # Small delay for UI smoothness

        # Prepare Final Payload
        raw_data = state.get("raw_data")
        data = []
        
        if isinstance(raw_data, pd.DataFrame):
            data = raw_data.to_dict(orient="records")
        elif isinstance(raw_data, list):
            data = raw_data
        elif isinstance(raw_data, dict):
            content = raw_data.get("data")
            if isinstance(content, list):
                data = content
            elif isinstance(content, str):
                try:
                    # Parse the JSON string from the Analyst node
                    df_temp = pd.read_json(io.StringIO(content))
                    data = df_temp.to_dict(orient="records")
                except:
                    data = []
        
        visual_output = state.get("visual_output")
        # Fix: parse to dict first to avoid double-serialization.
        # Plotly's .to_json() returns a string; embedding it raw in json.dumps() double-encodes it.
        viz_dict = None
        if visual_output and hasattr(visual_output, "to_json"):
            try:
                viz_dict = json.loads(visual_output.to_json())
            except Exception as e:
                print(f"[API] Viz serialization error: {e}")

        final_payload = {
            "type": "final",
            "response": state.get("final_response"),
            "data": data,
            "viz": viz_dict,  # now a dict, not a string
            "plan": state.get("supervisor_plan")
        }
        yield json.dumps(final_payload) + "\n"

    return StreamingResponse(stream_logic(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
