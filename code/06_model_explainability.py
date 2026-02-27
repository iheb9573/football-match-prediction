from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from football_bi.pipeline import run_step_06_explainability


if __name__ == "__main__":
    run_step_06_explainability()
    print("Explainability completed. Check reports/football_bi.")
