import sys
from pathlib import Path
import uvicorn

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    from my_agent.helpers.sandbox_server import app
    print("🚀 Starting Sandbox Execution Server on http://localhost:8765")
    uvicorn.run(app, host="localhost", port=8765, log_level="info")
