import httpx
from typing import Any, Dict

SANDBOX_SERVER_URL = "http://localhost:8765"

class SandboxClient:
    def __init__(self, server_url: str = SANDBOX_SERVER_URL, session_id: str = "default"):
        self.server_url = server_url
        self.session_id = session_id

    async def health_check(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            return (await client.get(f"{self.server_url}/health")).json()

    async def execute_code(self, code: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.post(f"{self.server_url}/execute", json={"code": code, "session_id": self.session_id})
            return res.json()

    async def install_package(self, package_name: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.post(f"{self.server_url}/install", json={"package_name": package_name})
            return res.json()

    async def preload_file(self, file_path: str, shared: bool = False) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.post(f"{self.server_url}/preload", json={"file_path": file_path, "session_id": self.session_id, "shared": shared})
            return res.json()

    async def reset_context(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.post(f"{self.server_url}/reset", json={"session_id": self.session_id})
            return res.json()

async def execute_code_via_server(code: str, session_id: str = "default"):
    return await SandboxClient(session_id=session_id).execute_code(code)

async def install_package_via_server(pkg: str, session_id: str = "default"):
    return await SandboxClient(session_id=session_id).install_package(pkg)

async def preload_file_via_server(path: str, session_id: str = "default", shared: bool = False):
    return await SandboxClient(session_id=session_id).preload_file(path, shared=shared)

async def reset_context_via_server(session_id: str = "default"):
    return await SandboxClient(session_id=session_id).reset_context()

async def check_server_health() -> bool:
    try:
        await SandboxClient().health_check()
        return True
    except: return False
