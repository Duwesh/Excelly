import shutil
import subprocess
import sys
import venv
from pathlib import Path

SANDBOX_DIR = Path(__file__).parent.parent.parent / ".sandbox"
VENV_DIR = SANDBOX_DIR / "venv"
PLOTS_DIR = SANDBOX_DIR / "plots"
TABLES_DIR = SANDBOX_DIR / "tables"
SESSIONS_DIR = SANDBOX_DIR / "sessions"


def get_session_dir(session_id: str) -> Path:
    return SESSIONS_DIR / session_id


def get_session_plots_dir(session_id: str) -> Path:
    d = get_session_dir(session_id) / "plots"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_session_tables_dir(session_id: str) -> Path:
    d = get_session_dir(session_id) / "tables"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_python_executable() -> str:
    if sys.platform == "win32":
        return str(VENV_DIR / "Scripts" / "python.exe")
    else:
        return str(VENV_DIR / "bin" / "python")


def get_pip_executable() -> str:
    if sys.platform == "win32":
        return str(VENV_DIR / "Scripts" / "pip.exe")
    else:
        return str(VENV_DIR / "bin" / "pip")


def ensure_sandbox_exists() -> bool:
    if VENV_DIR.exists() and get_python_executable():
        return True

    print("[SANDBOX] Creating sandbox virtual environment...")
    try:
        SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
        PLOTS_DIR.mkdir(parents=True, exist_ok=True)
        TABLES_DIR.mkdir(parents=True, exist_ok=True)

        venv.create(VENV_DIR, with_pip=True, clear=True)
        subprocess.run([get_pip_executable(), "install", "--upgrade", "pip"], capture_output=True)

        base_packages = [
            "pandas", "numpy", "openpyxl", "matplotlib", "seaborn", 
            "scipy", "statsmodels", "scikit-learn", "tabulate", "python-dateutil"
        ]
        print(f"   Installing base packages...")
        subprocess.run([get_pip_executable(), "install"] + base_packages, capture_output=True)
        print("[SUCCESS] Sandbox environment created successfully!")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create sandbox: {e}")
        return False


def cleanup_sandbox():
    if SANDBOX_DIR.exists():
        shutil.rmtree(SANDBOX_DIR)
        print("🧹 Sandbox cleaned up")
