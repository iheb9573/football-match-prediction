"""
ML Pipeline Orchestrator - Manages end-to-end football prediction workflow.

Orchestrates all components:
- Data loading
- Preprocessing
- Feature engineering
- Model training
- Hyperparameter tuning
- Ensemble creation
- Evaluation and reporting
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, log_loss

# Import all components
from ..features import advanced, player
from ..models import base, ensembles, evaluation, selection
from ..preprocessing import leakage_check, imputation, scaling


class MLPipeline:
    """
    Complete ML pipeline orchestrator for football match prediction.

    Manages workflow stages:
    1. Ingest data
    2. Preprocess
    3. Engineer features
    4. Split data
    5. Train baseline models
    6. Tune hyperparameters (optional)
    7. Create ensembles (optional)
    8. Evaluate and report
    """

    def __init__(
        self,
        data_path: str | Path,
        output_dir: str | Path = "reports/pipeline",
        random_state: int = 42,
        verbose: int = 1,
    ):
        """
        Initialize pipeline.

        Parameters
        ----------
        data_path : str or Path
            Path to feature-engineered CSV (match_features.csv)
        output_dir : str or Path
            Directory to save results
        random_state : int
            Random seed for reproducibility
        verbose : int
            Verbosity level (0=silent, 1=info, 2=debug)
        """

        self.data_path = Path(data_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.random_state = random_state
        self.verbose = verbose

        # Setup logging
        self.logger = self._setup_logging()

        # Storage for pipeline artifacts
        self.df_raw = None
        self.df_processed = None
        self.X_train = None
        self.y_train = None
        self.X_valid = None
        self.y_valid = None
        self.X_test = None
        self.y_test = None

        self.models_trained = {}
        self.results = {}

        self.logger.info("[INIT] Pipeline initialized")
        self.logger.info(f"[INIT] Data path: {self.data_path}")
        self.logger.info(f"[INIT] Output dir: {self.output_dir}")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""

        logger = logging.getLogger("MLPipeline")
        logger.setLevel(logging.DEBUG if self.verbose >= 2 else logging.INFO)

        # Create handlers
        log_file = self.output_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO if self.verbose > 0 else logging.WARNING)

        # Create formatter
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def load_data(self) -> MLPipeline:
        """
        Load data from CSV.

        Returns
        -------
        MLPipeline
            Self for chaining
        """

        self.logger.info("[01_LOAD] Loading data...")

        try:
            self.df_raw = pd.read_csv(self.data_path)
            self.logger.info(f"[01_LOAD] Loaded {len(self.df_raw)} matches, {len(self.df_raw.columns)} columns")
            self.logger.info(f"[01_LOAD] Columns: {list(self.df_raw.columns[:5])}... (showing first 5)")
            return self

        except FileNotFoundError:
            self.logger.error(f"[01_LOAD] File not found: {self.data_path}")
            raise

    def preprocess(self, imputation_strategy: str = "hierarchical") -> MLPipeline:
        """
        Preprocess data (imputation, scaling, etc).

        Parameters
        ----------
        imputation_strategy : str
            Strategy for missing values: 'hierarchical', 'forward_fill', 'mean'

        Returns
        -------
        MLPipeline
            Self for chaining
        """

        self.logger.info("[02_PREPROCESS] Starting preprocessing...")

        if self.df_raw is None:
            raise ValueError("Load data first with load_data()")

        df = self.df_raw.copy()

        # Identify numeric columns for imputation
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        # Remove target and meta columns
        numeric_cols = [c for c in numeric_cols if c not in ['target_result', 'match_id']]

        # Perform imputation
        self.logger.info(f"[02_PREPROCESS] Imputing {len(numeric_cols)} numeric columns...")
        df = imputation.impute_missing_values(
            df,
            strategy=imputation_strategy,
            features=numeric_cols,
        )

        # Validate leakage
        self.logger.info("[02_PREPROCESS] Validating temporal leakage...")
        validator = leakage_check.TemporalLeakageValidator()
        leakage_check_result = validator.validate_all(df)

        if not leakage_check_result["valid"]:
            self.logger.warning(f"[02_PREPROCESS] Leakage issues: {leakage_check_result['issues']}")
        else:
            self.logger.info("[02_PREPROCESS] Temporal leakage check PASSED")

        self.df_processed = df
        self.logger.info("[02_PREPROCESS] Preprocessing complete")

        return self

    def split_data(
        self,
        test_season_year: int = 2025,
        valid_season_year: int = 2024,
    ) -> MLPipeline:
        """
        Split data into train/valid/test sets using temporal ordering.

        Parameters
        ----------
        test_season_year : int
            Test set season year
        valid_season_year : int
            Validation set season year

        Returns
        -------
        MLPipeline
            Self for chaining
        """

        self.logger.info("[03_SPLIT] Splitting data into train/valid/test...")

        if self.df_processed is None:
            raise ValueError("Preprocess data first with preprocess()")

        df = self.df_processed.copy()

        # Get unique season years
        if 'season_start_year' not in df.columns:
            self.logger.warning("[03_SPLIT] 'season_start_year' not found - creating placeholder")
            # Try to infer from match_date if available
            if 'match_date' in df.columns:
                df['match_date'] = pd.to_datetime(df['match_date'])
                df['season_start_year'] = df['match_date'].dt.year
                df.loc[df['match_date'].dt.month < 8, 'season_start_year'] -= 1

        season_years = sorted(df['season_start_year'].unique().tolist())

        # Split by season
        test_df = df[df['season_start_year'] == test_season_year]
        valid_df = df[df['season_start_year'] == valid_season_year]
        train_df = df[~df['season_start_year'].isin([test_season_year, valid_season_year])]

        self.logger.info(f"[03_SPLIT] Train: {len(train_df)} matches, Valid: {len(valid_df)}, Test: {len(test_df)}")

        # Extract features and target
        feature_cols = base.NUMERIC_FEATURES + base.CATEGORICAL_FEATURES
        feature_cols = [c for c in feature_cols if c in df.columns]

        self.X_train = train_df[feature_cols]
        self.y_train = train_df['target_result']

        self.X_valid = valid_df[feature_cols]
        self.y_valid = valid_df['target_result']

        self.X_test = test_df[feature_cols]
        self.y_test = test_df['target_result']

        self.logger.info("[03_SPLIT] Data split complete")

        return self

    def train_baseline_models(self, models: list[str] | None = None) -> MLPipeline:
        """
        Train baseline models without hyperparameter tuning.

        Parameters
        ----------
        models : list[str], optional
            Models to train. Default: all available

        Returns
        -------
        MLPipeline
            Self for chaining
        """

        self.logger.info("[04_TRAIN] Training baseline models...")

        if self.X_train is None:
            raise ValueError("Split data first with split_data()")

        if models is None:
            models = base.ModelRegistry.list_available()

        # Train and evaluate each model
        baseline_results = []

        for model_name in models:
            try:
                self.logger.info(f"[04_TRAIN] Training {model_name}...")

                # Build and train pipeline
                pipeline = base.build_model_pipeline(
                    model_name,
                    numeric_features=base.NUMERIC_FEATURES,
                    categorical_features=base.CATEGORICAL_FEATURES,
                    random_state=self.random_state,
                )

                pipeline.fit(self.X_train, self.y_train)
                self.models_trained[model_name] = pipeline

                # Evaluate on validation set
                y_pred = pipeline.predict(self.X_valid)
                y_proba = pipeline.predict_proba(self.X_valid)
                classes = pipeline.named_steps["model"].classes_

                metrics = {
                    "model": model_name,
                    "accuracy": accuracy_score(self.y_valid, y_pred),
                    "f1_macro": f1_score(self.y_valid, y_pred, average="macro"),
                    "log_loss": log_loss(self.y_valid, y_proba, labels=list(classes)),
                }

                baseline_results.append(metrics)
                self.logger.info(f"[04_TRAIN] {model_name}: accuracy={metrics['accuracy']:.4f}, f1={metrics['f1_macro']:.4f}")

            except Exception as e:
                self.logger.error(f"[04_TRAIN] Error training {model_name}: {str(e)}")
                continue

        # Save results
        baseline_df = pd.DataFrame(baseline_results).sort_values("f1_macro", ascending=False)
        baseline_df.to_csv(self.output_dir / "01_baseline_results.csv", index=False)

        self.results["baseline"] = baseline_df
        self.logger.info(f"[04_TRAIN] Baseline training complete. Best: {baseline_df.iloc[0]['model']}")

        return self

    def tune_hyperparameters(
        self,
        models: list[str] | None = None,
        strategy: Literal["random", "grid"] = "random",
        n_iter: int = 100,
    ) -> MLPipeline:
        """
        Tune hyperparameters for selected models.

        Parameters
        ----------
        models : list[str], optional
            Models to tune. Default: top performers
        strategy : {'random', 'grid'}
            Tuning strategy
        n_iter : int
            Number of iterations for random search

        Returns
        -------
        MLPipeline
            Self for chaining
        """

        self.logger.info(f"[05_TUNE] Starting hyperparameter tuning ({strategy} search)...")

        if self.X_train is None:
            raise ValueError("Split data first with split_data()")

        if models is None:
            # Default: tune top 3 baseline models
            baseline_df = self.results.get("baseline")
            if baseline_df is not None:
                models = baseline_df.head(3)["model"].tolist()
            else:
                models = ["extra_trees", "random_forest"]

        tuning_results = []

        for model_name in models:
            try:
                self.logger.info(f"[05_TUNE] Tuning {model_name} ({strategy} search, {n_iter} iterations)...")

                optimizer = selection.HyperparameterOptimizer(
                    strategy=strategy,
                    cv_splits=5,
                    n_iter=n_iter,
                    scoring="f1_macro",
                    random_state=self.random_state,
                    verbose=0 if self.verbose < 2 else 1,
                )

                result = optimizer.search(self.X_train, self.y_train, model_name)

                # Evaluate tuned model on validation set
                y_pred = result["best_model"].predict(self.X_valid)
                y_proba = result["best_model"].predict_proba(self.X_valid)
                classes = result["best_model"].named_steps["model"].classes_

                metrics = {
                    "model": f"{model_name}_tuned",
                    "accuracy": accuracy_score(self.y_valid, y_pred),
                    "f1_macro": f1_score(self.y_valid, y_pred, average="macro"),
                    "log_loss": log_loss(self.y_valid, y_proba, labels=list(classes)),
                    "best_cv_score": result["best_score"],
                }

                tuning_results.append(metrics)
                self.models_trained[f"{model_name}_tuned"] = result["best_model"]

                self.logger.info(f"[05_TUNE] {model_name}: accuracy={metrics['accuracy']:.4f}, f1={metrics['f1_macro']:.4f}")

            except Exception as e:
                self.logger.error(f"[05_TUNE] Error tuning {model_name}: {str(e)}")
                continue

        # Save results
        if tuning_results:
            tuning_df = pd.DataFrame(tuning_results).sort_values("f1_macro", ascending=False)
            tuning_df.to_csv(self.output_dir / "02_tuning_results.csv", index=False)
            self.results["tuning"] = tuning_df
            self.logger.info(f"[05_TUNE] Hyperparameter tuning complete")

        return self

    def create_ensembles(self) -> MLPipeline:
        """
        Create ensemble models.

        Returns
        -------
        MLPipeline
            Self for chaining
        """

        self.logger.info("[06_ENSEMBLE] Creating ensemble models...")

        if self.X_train is None:
            raise ValueError("Split data first with split_data()")

        ensemble_results = []

        # Try Stacking
        try:
            self.logger.info("[06_ENSEMBLE] Creating stacking ensemble...")

            stacking = ensembles.create_stacking_ensemble(
                self.X_train,
                self.y_train,
                self.X_valid,
                self.y_valid,
                base_models=["extra_trees", "random_forest"],
                random_state=self.random_state,
            )

            y_pred = stacking.predict(self.X_valid)
            y_proba = stacking.predict_proba(self.X_valid)

            metrics = {
                "model": "stacking_ensemble",
                "accuracy": accuracy_score(self.y_valid, y_pred),
                "f1_macro": f1_score(self.y_valid, y_pred, average="macro"),
                "log_loss": log_loss(self.y_valid, y_proba),
            }

            ensemble_results.append(metrics)
            self.models_trained["stacking_ensemble"] = stacking

            self.logger.info(f"[06_ENSEMBLE] Stacking: accuracy={metrics['accuracy']:.4f}")

        except Exception as e:
            self.logger.warning(f"[06_ENSEMBLE] Stacking failed: {str(e)}")

        # Try Voting
        try:
            self.logger.info("[06_ENSEMBLE] Creating voting ensemble...")

            voting = ensembles.create_voting_ensemble(
                self.X_train,
                self.y_train,
                models=["extra_trees", "random_forest"],
                voting="soft",
                random_state=self.random_state,
            )

            y_pred = voting.predict(self.X_valid)
            y_proba = voting.predict_proba(self.X_valid)

            metrics = {
                "model": "voting_ensemble",
                "accuracy": accuracy_score(self.y_valid, y_pred),
                "f1_macro": f1_score(self.y_valid, y_pred, average="macro"),
                "log_loss": log_loss(self.y_valid, y_proba),
            }

            ensemble_results.append(metrics)
            self.models_trained["voting_ensemble"] = voting

            self.logger.info(f"[06_ENSEMBLE] Voting: accuracy={metrics['accuracy']:.4f}")

        except Exception as e:
            self.logger.warning(f"[06_ENSEMBLE] Voting failed: {str(e)}")

        # Save results
        if ensemble_results:
            ensemble_df = pd.DataFrame(ensemble_results).sort_values("f1_macro", ascending=False)
            ensemble_df.to_csv(self.output_dir / "03_ensemble_results.csv", index=False)
            self.results["ensembles"] = ensemble_df
            self.logger.info(f"[06_ENSEMBLE] Ensemble creation complete")

        return self

    def evaluate_on_test(self) -> MLPipeline:
        """
        Evaluate all trained models on test set.

        Returns
        -------
        MLPipeline
            Self for chaining
        """

        self.logger.info("[07_EVALUATE] Evaluating models on test set...")

        if self.X_test is None:
            raise ValueError("Split data first with split_data()")

        evaluator = evaluation.ExperimentEvaluator(classes=["H", "D", "A"])
        test_results = []

        for model_name, model in self.models_trained.items():
            try:
                y_pred = model.predict(self.X_test)
                y_proba = model.predict_proba(self.X_test)

                metrics = evaluator.calculate_metrics(self.y_test, y_pred, y_proba, model_name)
                test_results.append(metrics)

                self.logger.info(f"[07_EVALUATE] {model_name}: accuracy={metrics['accuracy']:.4f}, f1={metrics['f1_macro']:.4f}")

            except Exception as e:
                self.logger.warning(f"[07_EVALUATE] Error evaluating {model_name}: {str(e)}")
                continue

        # Save results
        if test_results:
            test_df = pd.DataFrame(test_results).sort_values("f1_macro", ascending=False)
            test_df.to_csv(self.output_dir / "04_test_results.csv", index=False)
            self.results["test"] = test_df

            # Identify best model
            best_model = test_df.iloc[0]
            self.logger.info(f"\n[07_EVALUATE] *** BEST MODEL: {best_model['model']} ***")
            self.logger.info(f"[07_EVALUATE]     Accuracy: {best_model['accuracy']:.4f}")
            self.logger.info(f"[07_EVALUATE]     F1-Macro: {best_model['f1_macro']:.4f}")
            self.logger.info(f"[07_EVALUATE]     Log Loss: {best_model['log_loss']:.4f}")

        return self

    def generate_report(self) -> MLPipeline:
        """
        Generate comprehensive pipeline report.

        Returns
        -------
        MLPipeline
            Self for chaining
        """

        self.logger.info("[08_REPORT] Generating pipeline report...")

        report_lines = [
            "=" * 80,
            "FOOTBALL PREDICTION PIPELINE - FINAL REPORT",
            "=" * 80,
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\nData Summary:",
            f"  Train set: {len(self.X_train)} matches" if self.X_train is not None else "  Train: N/A",
            f"  Valid set: {len(self.X_valid)} matches" if self.X_valid is not None else " Valid: N/A",
            f"  Test set:  {len(self.X_test)} matches" if self.X_test is not None else "  Test: N/A",
            f"\nModels Trained: {len(self.models_trained)}",
        ]

        # Add results
        if "baseline" in self.results:
            report_lines.append("\n" + "=" * 80)
            report_lines.append("BASELINE MODELS")
            report_lines.append("=" * 80)
            report_lines.append(str(self.results["baseline"].to_string(index=False)))

        if "tuning" in self.results:
            report_lines.append("\n" + "=" * 80)
            report_lines.append("TUNED MODELS")
            report_lines.append("=" * 80)
            report_lines.append(str(self.results["tuning"].to_string(index=False)))

        if "test" in self.results:
            report_lines.append("\n" + "=" * 80)
            report_lines.append("TEST SET EVALUATION")
            report_lines.append("=" * 80)
            report_lines.append(str(self.results["test"].to_string(index=False)))

            # Improvement analysis
            baseline_accuracy = 0.495  # Current best
            best_accuracy = self.results["test"].iloc[0]["accuracy"]
            improvement = (best_accuracy - baseline_accuracy) * 100

            report_lines.append(f"\n** IMPROVEMENT ANALYSIS **")
            report_lines.append(f"Baseline accuracy: {baseline_accuracy:.4f} (49.5%)")
            report_lines.append(f"Best model accuracy: {best_accuracy:.4f}")
            report_lines.append(f"Improvement: +{improvement:.2f} percentage points")

        report_lines.append("\n" + "=" * 80)

        # Save report
        report_text = "\n".join(report_lines)
        report_file = self.output_dir / "FINAL_REPORT.txt"
        report_file.write_text(report_text)

        self.logger.info(f"[08_REPORT] Report saved to {report_file}")
        print(report_text)  # Print to console

        return self

    def run_full_pipeline(
        self,
        stages: list[str] | str = "all",
        tune_hyperparameters: bool = False,
        create_ensembles: bool = False,
    ) -> dict:
        """
        Run complete pipeline with specified stages.

        Parameters
        ----------
        stages : list[str] or 'all'
            Pipeline stages to run
        tune_hyperparameters : bool
            Whether to tune hyperparameters
        create_ensembles : bool
            Whether to create ensemble models

        Returns
        -------
        dict
            Pipeline results
        """

        self.logger.info("=" * 80)
        self.logger.info("STARTING FULL ML PIPELINE")
        self.logger.info("=" * 80)

        try:
            # Core pipeline stages
            self.load_data()
            self.preprocess()
            self.split_data()
            self.train_baseline_models()

            # Optional stages
            if tune_hyperparameters:
                self.tune_hyperparameters()

            if create_ensembles:
                self.create_ensembles()

            # Evaluation and reporting
            self.evaluate_on_test()
            self.generate_report()

            self.logger.info("\n" + "=" * 80)
            self.logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            self.logger.info("=" * 80)

            return self.results

        except Exception as e:
            self.logger.error(f"\nPIPELINE FAILED: {str(e)}", exc_info=True)
            raise


# Export public API
__all__ = ["MLPipeline"]
