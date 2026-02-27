from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from football_bi.pipeline import run_step_01_ingestion


if __name__ == "__main__":
    output = run_step_01_ingestion()
    print(f"Ingestion completed: {output}")
