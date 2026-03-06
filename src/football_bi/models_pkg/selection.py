"""
Hyperparameter tuning and model selection module.

Implements RandomSearchCV and GridSearchCV with temporal cross-validation
for systematic hyperparameter optimization.
"""

from __future__ import annotations

import warnings
from typing import Literal, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, TimeSeriesSplit
from sklearn.pipeline import Pipeline

from .base import CATEGORICAL_FEATURES, NUMERIC_FEATURES, build_model_pipeline

# Suppress sklearn warnings
warnings.filterwarnings("ignore", category=UserWarning)


class TemporalTimeSeriesSplit(TimeSeriesSplit):
    """
    Time series split that respects temporal order of matches.

    Ensures train set is always before validation set (no look-ahead bias).
    """

    def __init__(self, n_splits: int = 5):
        """
        Initialize temporal split.

        Parameters
        ----------
        n_splits : int
            Number of splits
        """
        super().__init__(n_splits=n_splits)

    def split(self, X: pd.DataFrame | np.ndarray, y=None, groups=None):
        """
        Generate temporal train/test indices.

        Parameters
        ----------
        X : pd.DataFrame or np.ndarray
            Data to split
        y : ignored
        groups : ignored

        Yields
        ------
        tuple[np.ndarray, np.ndarray]
            Train indices, test indices
        """
        if isinstance(X, pd.DataFrame):
            n_samples = len(X)
        else:
            n_samples = X.shape[0]

        indices = np.arange(n_samples)

        # Standard time series split (cumulative training)
        for train, test in super().split(X, y, groups):
            yield train, test


class HyperparameterOptimizer:
    """
    Hyperparameter optimization using random or grid search.

    Supports multiple models with model-specific search spaces.
    """

    # Predefined search spaces for each model
    SEARCH_SPACES = {
        "logistic_regression": {
            "model__max_iter": [1000, 2000, 3000, 5000],
            "model__C": [0.001, 0.01, 0.1, 1.0, 10.0],
            "model__penalty": ["l2"],
        },
        "random_forest": {
            "model__n_estimators": [100, 200, 350, 500],
            "model__max_depth": [10, 15, 18, 20, 25, None],
            "model__min_samples_leaf": [1, 2, 4],
            "model__min_samples_split": [2, 5, 10],
            "model__max_features": ["sqrt", "log2"],
        },
        "extra_trees": {
            "model__n_estimators": [200, 350, 500, 700],
            "model__max_depth": [15, 18, 20, 25, None],
            "model__min_samples_leaf": [1, 2, 4],
            "model__max_features": ["sqrt", "log2"],
        },
        "xgboost": {
            "model__n_estimators": [50, 100, 200, 300],
            "model__max_depth": [3, 5, 7, 10],
            "model__learning_rate": [0.01, 0.05, 0.1],
            "model__subsample": [0.6, 0.8, 1.0],
            "model__colsample_bytree": [0.6, 0.8, 1.0],
            "model__min_child_weight": [1, 3, 5],
        },
        "lightgbm": {
            "model__n_estimators": [50, 100, 200, 300],
            "model__max_depth": [5, 7, 10, 15, -1],
            "model__num_leaves": [15, 31, 63, 127],
            "model__learning_rate": [0.01, 0.05, 0.1],
            "model__min_child_samples": [5, 10, 20],
        },
        "catboost": {
            "model__depth": [4, 6, 8],
            "model__learning_rate": [0.01, 0.05, 0.1],
            "model__iterations": [100, 200, 300],
            "model__l2_leaf_reg": [1, 3, 5, 10],
        },
    }

    def __init__(
        self,
        strategy: Literal["random", "grid"] = "random",
        cv_splits: int = 5,
        n_iter: int = 100,
        scoring: str = "f1_macro",
        random_state: int = 42,
        verbose: int = 1,
        n_jobs: int = -1,
    ):
        """
        Initialize hyperparameter optimizer.

        Parameters
        ----------
        strategy : {'random', 'grid'}
            Search strategy
        cv_splits : int
            Number of CV splits
        n_iter : int
            Number of iterations for random search
        scoring : str
            Scoring metric
        random_state : int
            Random seed
        verbose : int
            Verbosity level
        n_jobs : int
            Number of parallel jobs
        """

        self.strategy = strategy
        self.cv_splits = cv_splits
        self.n_iter = n_iter
        self.scoring = scoring
        self.random_state = random_state
        self.verbose = verbose
        self.n_jobs = n_jobs

        # Use temporal CV instead of random k-fold
        self.cv = TemporalTimeSeriesSplit(n_splits=cv_splits)

        self.best_model = None
        self.best_params = None
        self.cv_results = None

    def search(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        model_name: str,
        param_grid: Optional[dict] = None,
    ) -> dict:
        """
        Run hyperparameter search.

        Parameters
        ----------
        X_train : pd.DataFrame
            Training features
        y_train : pd.Series
            Training target
        model_name : str
            Model name (from registry)
        param_grid : dict, optional
            Custom parameter grid. If None, use default for model_name

        Returns
        -------
        dict
            Results containing best_params, best_score, cv_results
        """

        # Get parameter grid
        if param_grid is None:
            if model_name not in self.SEARCH_SPACES:
                raise ValueError(
                    f"No default search space for '{model_name}'. Provide param_grid."
                )
            param_grid = self.SEARCH_SPACES[model_name]

        # Build base pipeline
        pipeline = build_model_pipeline(
            model_name,
            numeric_features=NUMERIC_FEATURES,
            categorical_features=CATEGORICAL_FEATURES,
            random_state=self.random_state,
        )

        # Run search
        if self.strategy == "random":
            search = RandomizedSearchCV(
                pipeline,
                param_distributions=param_grid,
                n_iter=self.n_iter,
                cv=self.cv,
                scoring=self.scoring,
                random_state=self.random_state,
                verbose=self.verbose,
                n_jobs=self.n_jobs,
            )

        elif self.strategy == "grid":
            search = GridSearchCV(
                pipeline,
                param_grid=param_grid,
                cv=self.cv,
                scoring=self.scoring,
                verbose=self.verbose,
                n_jobs=self.n_jobs,
            )

        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

        # Fit search
        search.fit(X_train, y_train)

        # Store results
        self.best_model = search.best_estimator_
        self.best_params = search.best_params_
        self.cv_results = search.cv_results_

        return {
            "best_model": self.best_model,
            "best_params": self.best_params,
            "best_score": search.best_score_,
            "cv_results": pd.DataFrame(search.cv_results_),
        }

    def get_cv_results_df(self) -> pd.DataFrame:
        """
        Get cross-validation results as DataFrame.

        Returns
        -------
        pd.DataFrame
            CV results with rank, score, and hyperparameters
        """

        if self.cv_results is None:
            raise ValueError("No CV results available. Run search() first.")

        results_df = pd.DataFrame(self.cv_results)

        # Select key columns
        key_cols = ["rank_test_score", "mean_test_score", "std_test_score"]
        param_cols = [col for col in results_df.columns if col.startswith("param_")]

        return results_df[key_cols + param_cols].sort_values("rank_test_score")

    def get_top_results(self, n: int = 10) -> pd.DataFrame:
        """
        Get top N results from CV search.

        Parameters
        ----------
        n : int
            Number of top results to return

        Returns
        -------
        pd.DataFrame
            Top N results
        """

        results_df = self.get_cv_results_df()
        return results_df.head(n)


def tune_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    model_name: str,
    strategy: Literal["random", "grid"] = "random",
    n_iter: int = 100,
    cv_splits: int = 5,
    scoring: str = "f1_macro",
    random_state: int = 42,
    param_grid: Optional[dict] = None,
) -> dict:
    """
    Convenience function to tune a single model.

    Parameters
    ----------
    X_train : pd.DataFrame
        Training features
    y_train : pd.Series
        Training target
    model_name : str
        Model name
    strategy : {'random', 'grid'}
        Search strategy
    n_iter : int
        Number of iterations (for random search)
    cv_splits : int
        Number of CV splits
    scoring : str
        Scoring metric
    random_state : int
        Random seed
    param_grid : dict, optional
        Custom parameter grid

    Returns
    -------
    dict
        Results with best_model, best_params, best_score
    """

    optimizer = HyperparameterOptimizer(
        strategy=strategy,
        cv_splits=cv_splits,
        n_iter=n_iter,
        scoring=scoring,
        random_state=random_state,
    )

    return optimizer.search(X_train, y_train, model_name, param_grid)


def compare_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    model_names: list[str],
    X_valid: pd.DataFrame,
    y_valid: pd.Series,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Train and compare multiple models on validation set.

    Parameters
    ----------
    X_train : pd.DataFrame
        Training features
    y_train : pd.Series
        Training target
    model_names : list[str]
        Models to compare
    X_valid : pd.DataFrame
        Validation features
    y_valid : pd.Series
        Validation target
    random_state : int
        Random seed

    Returns
    -------
    pd.DataFrame
        Comparison results with accuracy, f1, log_loss for each model
    """

    from sklearn.metrics import accuracy_score, f1_score, log_loss

    results = []

    for model_name in model_names:
        try:
            # Build and train pipeline
            pipeline = build_model_pipeline(
                model_name,
                numeric_features=NUMERIC_FEATURES,
                categorical_features=CATEGORICAL_FEATURES,
                random_state=random_state,
            )

            pipeline.fit(X_train, y_train)

            # Evaluate
            y_pred = pipeline.predict(X_valid)
            y_proba = pipeline.predict_proba(X_valid)
            classes = pipeline.named_steps["model"].classes_

            metric_result = {
                "model": model_name,
                "accuracy": accuracy_score(y_valid, y_pred),
                "f1_macro": f1_score(y_valid, y_pred, average="macro"),
                "log_loss": log_loss(y_valid, y_proba, labels=list(classes)),
            }

            results.append(metric_result)

        except Exception as e:
            print(f"Error training {model_name}: {str(e)}")
            continue

    return pd.DataFrame(results).sort_values("f1_macro", ascending=False)


# Export public API
__all__ = [
    "HyperparameterOptimizer",
    "TemporalTimeSeriesSplit",
    "tune_model",
    "compare_models",
]
