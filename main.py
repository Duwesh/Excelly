import os
import shutil
import uuid
import json
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from contextlib import asynccontextmanager
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from my_agent.agent import create_excel_analysis_graph
from my_agent.core.execution_var import set_current_session_id
from my_agent.helpers.sandbox import SESSIONS_DIR
from my_agent.helpers.sandbox_client import preload_file_via_server

# Module-level graph reference (set during app lifespan)
graph = None

# SQLite checkpointer DB path
DB_PATH = Path("data/checkpoints.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the AsyncSqliteSaver lifecycle."""
    global graph
    async with AsyncSqliteSaver.from_conn_string(str(DB_PATH)) as checkpointer:
        graph = create_excel_analysis_graph(checkpointer=checkpointer)
        print(f"✅ Graph initialized with SQLite checkpointer at {DB_PATH}")
        yield
    graph = None

app = FastAPI(title="Excel Analysis Agent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directory exists for uploaded Excel files
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class AnalyzeRequest(BaseModel):
    query: str
    file_path: Optional[str] = None
    thread_id: Optional[str] = None


@app.post("/api/analyze")
async def analyze_excel(request: AnalyzeRequest):
    """One-time response route for complete analysis execution"""
    try:
        thread_id = request.thread_id or str(uuid.uuid4())
        set_current_session_id(thread_id)

        input_state = {
            "messages": [HumanMessage(content=request.query)],
            "excel_file_path": request.file_path,
        }
            
        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 100}
        result = await graph.ainvoke(input_state, config)
        
        return {
            "success": True,
            "final_analysis": result.get("final_analysis"),
            "artifacts": result.get("artifacts", []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/stream")
async def analyze_excel_stream(request: AnalyzeRequest):
    """SSE streaming route — emits graph node updates as server-sent events."""
    thread_id = request.thread_id or str(uuid.uuid4())
    set_current_session_id(thread_id)

    input_state = {
        "messages": [HumanMessage(content=request.query)],
        "excel_file_path": request.file_path,
    }
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 100}

    async def event_generator():
        try:
            # Emit thread_id on first event so the client can persist it
            yield f"data: {json.dumps({'thread_id': thread_id, 'status': 'started'})}\n\n"

            async for chunk in graph.astream(input_state, config, stream_mode="updates", subgraphs=True):
                # chunk is (namespace_tuple, updates_dict) when subgraphs=True
                if isinstance(chunk, tuple):
                    ns, updates = chunk
                    is_subgraph = len(ns) > 0
                    for node_name, node_update in updates.items():
                        payload = {
                            "node": node_name,
                            "is_subgraph": is_subgraph,
                            "update": node_update,
                        }
                        yield f"data: {json.dumps(payload, default=str)}\n\n"
                else:
                    # Flat update dict
                    for node_name, node_update in chunk.items():
                        payload = {"node": node_name, "is_subgraph": False, "update": node_update}
                        yield f"data: {json.dumps(payload, default=str)}\n\n"

            yield f"data: {json.dumps({'status': 'completed'})}\n\n"
        except asyncio.CancelledError:
            pass
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # Disable nginx buffering
        },
    )


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload an Excel or CSV file and return its server-side path."""
    allowed = {".xlsx", ".xls", ".csv"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Use .xlsx, .xls, or .csv."
        )

    unique_name = f"{uuid.uuid4()}{ext}"
    dest = UPLOAD_DIR / unique_name
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    return {
        "success": True,
        "file_path": str(dest),
        "filename": file.filename,
        "size": dest.stat().st_size,
    }


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

