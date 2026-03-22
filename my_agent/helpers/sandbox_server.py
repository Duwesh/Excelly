import asyncio
import io
import shutil
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from my_agent.helpers.sandbox import (
    SANDBOX_DIR,
    VENV_DIR,
    ensure_sandbox_exists,
    get_pip_executable,
    get_session_plots_dir,
    get_session_tables_dir,
    get_session_dir,
)

if sys.platform == "win32":
    venv_site_packages = VENV_DIR / "Lib" / "site-packages"
else:
    python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    venv_site_packages = VENV_DIR / "lib" / python_version / "site-packages"

if venv_site_packages.exists():
    sys.path.insert(0, str(venv_site_packages))

ensure_sandbox_exists()

SESSION_CONTEXTS: Dict[str, Dict[str, Any]] = {}
SESSION_LAST_ACTIVE: Dict[str, float] = {}
SESSION_TTL_MINUTES: int = 30
CLEANUP_INTERVAL_SECONDS: int = 300
PRELOAD_CACHE: Dict[str, Any] = {}
SHARED_PRELOAD: Dict[str, Any] = {}
_preload_lock = threading.Lock()

app = FastAPI(title="Sandbox Execution Server")

@app.on_event("startup")
async def startup_tasks():
    asyncio.create_task(_session_cleanup_worker())

async def _session_cleanup_worker():
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
        now = time.time()
        ttl_seconds = SESSION_TTL_MINUTES * 60
        expired = [sid for sid, last in list(SESSION_LAST_ACTIVE.items()) if (now - last) > ttl_seconds]
        for sid in expired:
            _cleanup_session(sid)

def _cleanup_session(session_id: str) -> None:
    SESSION_CONTEXTS.pop(session_id, None)
    SESSION_LAST_ACTIVE.pop(session_id, None)
    with _preload_lock:
        keys = [k for k in PRELOAD_CACHE if k.startswith(f"{session_id}::")]
        for k in keys: del PRELOAD_CACHE[k]
    shutil.rmtree(str(get_session_dir(session_id)), ignore_errors=True)

class ExecuteRequest(BaseModel):
    code: str
    session_id: str = "default"

class InstallRequest(BaseModel):
    package_name: str

class ResetRequest(BaseModel):
    session_id: str = "default"

class PreloadRequest(BaseModel):
    file_path: str
    session_id: str = "default"
    shared: bool = False

@app.get("/health")
async def health_check():
    return {"status": "healthy", "active_sessions": len(SESSION_CONTEXTS)}

@app.post("/preload", status_code=202)
async def preload_file(request: PreloadRequest):
    abs_path = str(Path(request.file_path).absolute())
    if request.session_id not in SESSION_CONTEXTS:
        SESSION_CONTEXTS[request.session_id] = {"plots_dir": str(get_session_plots_dir(request.session_id)), "__file_path": abs_path}
    else:
        SESSION_CONTEXTS[request.session_id]["__file_path"] = abs_path
    SESSION_LAST_ACTIVE[request.session_id] = time.time()
    if abs_path in SHARED_PRELOAD: return {"status": "already_cached_shared"}

    def _load():
        try:
            import pandas as pd
            df = pd.read_csv(abs_path) if abs_path.lower().endswith(".csv") else pd.read_excel(abs_path)
            with _preload_lock:
                if request.shared: SHARED_PRELOAD[abs_path] = df
                else: PRELOAD_CACHE[f"{request.session_id}::{abs_path}"] = df
        except Exception: pass
    threading.Thread(target=_load, daemon=True).start()
    return {"status": "loading"}

@app.post("/execute")
async def execute_code(request: ExecuteRequest):
    session_id = request.session_id
    code = request.code
    session_plots_dir = get_session_plots_dir(session_id)
    if session_id not in SESSION_CONTEXTS:
        SESSION_CONTEXTS[session_id] = {"plots_dir": str(session_plots_dir), "__file_path": ""}
    SESSION_LAST_ACTIVE[session_id] = time.time()
    ctx = SESSION_CONTEXTS[session_id]
    ctx["plots_dir"] = str(session_plots_dir)

    # Injected preloaded df logic
    def _inject():
        hint = ctx.get("__file_path", "")
        if hint and hint in SHARED_PRELOAD: ctx["__preloaded_df"] = SHARED_PRELOAD[hint]; return True
        for k, v in list(PRELOAD_CACHE.items()):
            if k.startswith(f"{session_id}::"): ctx["__preloaded_df"] = v; return True
        return False
    _inject()

    session_plots_dir.mkdir(parents=True, exist_ok=True)
    existing_plots = set(session_plots_dir.glob("*.*"))

    try:
        import matplotlib
        matplotlib.use("Agg")
    except ImportError: pass

    output_buffer = io.StringIO()
    try:
        def _exec():
            import contextlib
            with contextlib.redirect_stdout(output_buffer): exec(code, ctx)
        await asyncio.wait_for(asyncio.to_thread(_exec), timeout=120.0)
        
        import matplotlib.pyplot as plt
        if plt.get_fignums():
            for f in plt.get_fignums():
                plt.figure(f).savefig(str(session_plots_dir / f"fig_{f}.png"), dpi=150, bbox_inches="tight")
            plt.close("all")

        new_plots = [str(p) for p in set(session_plots_dir.glob("*.*")) - existing_plots if p.stat().st_size > 2048]
        return {"success": True, "output": output_buffer.getvalue(), "plots": new_plots, "tables": []}
    except Exception as e:
        return {"success": False, "output": output_buffer.getvalue(), "error": str(e), "plots": [], "tables": []}

@app.post("/install")
async def install_package(request: InstallRequest):
    proc = await asyncio.create_subprocess_exec(get_pip_executable(), "install", request.package_name, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    return {"success": proc.returncode == 0, "output": stdout.decode(), "error": stderr.decode()}

@app.post("/reset")
async def reset_session(request: ResetRequest):
    _cleanup_session(request.session_id)
    return {"success": True}
