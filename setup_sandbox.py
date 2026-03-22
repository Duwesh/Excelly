#!/usr/bin/env python
"""
Setup script to initialize the sandbox environment for the Excel Analysis Agent.
"""

import sys
from pathlib import Path

# Add the project root to the path so we can import from my_agent
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from my_agent.helpers.sandbox import ensure_sandbox_exists, SANDBOX_DIR, VENV_DIR


def main():
    """Initialize the sandbox environment."""
    print("=" * 70)
    print("Excel Analysis Agent - Sandbox Setup")
    print("=" * 70)
    print()
    print(f"Sandbox location: {SANDBOX_DIR}")
    print(f"Virtual environment: {VENV_DIR}")
    print()

    # Create the sandbox
    success = ensure_sandbox_exists()

    print()
    print("-" * 70)
    if success:
        print("[SUCCESS] Sandbox setup completed successfully!")
        return 0
    else:
        print("[FAILED] Sandbox setup failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
