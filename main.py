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

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
