from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Now that pipeline/ has been renamed to pipeline_pkg/
# we can safely import from football_bi.pipeline (the .py file)
import football_bi.pipeline as pipeline_module
run_full_pipeline = pipeline_module.run_full_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full Football BI pipeline.")
    parser.add_argument("--simulations", type=int, default=1000, help="Number of champion simulations per league.")
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("🚀 FOOTBALL MATCH PREDICTION - COMPLETE PIPELINE")
    print("="*70)
    print(f"Running pipeline with {args.simulations} simulations...\n")
    
    run_full_pipeline(n_simulations=args.simulations)
    
    print("\n" + "="*70)
    print("✅ Full pipeline completed successfully!")
    print("="*70)
    print("\n📊 Results saved to:")
    print("   • Data: data/processed/football_bi/")
    print("   • Reports: reports/football_bi/")
    print("   • Models: models/football_bi/")


if __name__ == "__main__":
    main()
