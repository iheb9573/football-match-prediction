"""
Example: Using the ML Pipeline to train and evaluate models.

Run with: python run_pipeline.py
"""

from pathlib import Path

from src.football_bi.pipeline.orchestrator import MLPipeline


def main():
    """Run the complete ML pipeline."""

    # 1. INITIALIZE PIPELINE
    # =====================
    pipeline = MLPipeline(
        data_path="data/processed/football_bi/match_features.csv",
        output_dir="reports/pipeline_run",
        random_state=42,
        verbose=1,  # 0=silent, 1=info, 2=debug
    )

    # 2. RUN FULL PIPELINE
    # ====================
    results = pipeline.run_full_pipeline(
        stages="all",
        tune_hyperparameters=True,  # Enable hyperparameter tuning
        create_ensembles=True,      # Enable ensemble creation
    )

    # 3. ACCESS RESULTS
    # =================
    print("\n" + "=" * 80)
    print("PIPELINE EXECUTION COMPLETE")
    print("=" * 80)

    if "test" in results:
        test_results = results["test"]
        best_model = test_results.iloc[0]

        print(f"\nBest Model: {best_model['model']}")
        print(f"  Accuracy:  {best_model['accuracy']:.4f}")
        print(f"  F1-Macro:  {best_model['f1_macro']:.4f}")
        print(f"  Log Loss:  {best_model['log_loss']:.4f}")

    print(f"\nResults saved to: {pipeline.output_dir}")
    print("\nGenerated files:")
    for file in sorted(pipeline.output_dir.glob("*.csv")):
        print(f"  - {file.name}")
    for file in sorted(pipeline.output_dir.glob("*.txt")):
        print(f"  - {file.name}")


if __name__ == "__main__":
    main()
