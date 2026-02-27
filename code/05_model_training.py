from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from football_bi.pipeline import run_step_05_model_training


if __name__ == "__main__":
    artifacts = run_step_05_model_training()
    print(f"Training completed. Selected model: {artifacts.selected_model_name}")
    print(f"Model saved to: {artifacts.model_path}")
