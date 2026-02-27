from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from football_bi.pipeline import run_full_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full Football BI pipeline.")
    parser.add_argument("--simulations", type=int, default=1000, help="Number of champion simulations per league.")
    args = parser.parse_args()
    run_full_pipeline(n_simulations=args.simulations)
    print("Full pipeline completed successfully.")


if __name__ == "__main__":
    main()
