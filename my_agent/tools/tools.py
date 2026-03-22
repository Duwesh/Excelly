from typing import Any, Dict
from langchain_core.tools import tool
from my_agent.helpers.sandbox_client import execute_code_via_server, install_package_via_server, reset_context_via_server
from my_agent.core.execution_var import get_current_session_id

async def reset_execution_context():
    await reset_context_via_server(session_id=get_current_session_id())

@tool
def think_tool(reflection: str) -> str:
    """Reflect on progress."""
    return f"Reflection recorded: {reflection}"

@tool
async def python_repl_tool(reasoning: str, code: str) -> Dict[str, Any]:
    """Execute Python code in a sandbox."""
    return await execute_code_via_server(code, session_id=get_current_session_id())

@tool
async def bash_tool(reasoning: str, command: str) -> Dict[str, Any]:
    """Execute bash (pip install) in a sandbox."""
    if not command.strip().startswith("pip install"):
        return {"success": False, "error": "Only pip install supported"}
    pkg = command.replace("pip install", "").strip()
    return await install_package_via_server(pkg, session_id=get_current_session_id())
