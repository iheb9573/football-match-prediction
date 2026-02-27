from __future__ import annotations

import sys
from pathlib import Path

import uvicorn


if __name__ == "__main__":
    # Ensure the project root is importable for "api.main:app".
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
