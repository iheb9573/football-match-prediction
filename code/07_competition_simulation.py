from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from football_bi.pipeline import run_step_07_champion_simulation


def main() -> None:
    parser = argparse.ArgumentParser(description="Run probabilistic champion simulation.")
    parser.add_argument("--simulations", type=int, default=1000, help="Number of Monte Carlo simulations per league.")
    args = parser.parse_args()

    output = run_step_07_champion_simulation(n_simulations=args.simulations)
    print(f"Champion simulation completed: {output}")


if __name__ == "__main__":
    main()
