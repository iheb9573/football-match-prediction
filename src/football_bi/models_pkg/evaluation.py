"""
Model evaluation and comparison module.

Provides comprehensive metrics calculation and model comparison utilities.
"""

from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
)


class ExperimentEvaluator:
    """
    Comprehensive model evaluation and comparison.

    Calculates metrics, generates reports, and creates visualizations.
    """

    def __init__(self, classes: list[str] = None):
        """
        Initialize evaluator.

        Parameters
        ----------
        classes : list[str], optional
            Class labels (e.g., ['H', 'D', 'A'])
        """

        self.classes = classes or ["H", "D", "A"]
        self.results = {}

    def calculate_metrics(
        self,
        y_true: pd.Series | np.ndarray,
        y_pred: np.ndarray,
        y_proba: np.ndarray,
        model_name: str = "Model",
    ) -> dict:
        """
        Calculate comprehensive metrics for a model.

        Parameters
        ----------
        y_true : pd.Series or np.ndarray
            True labels
        y_pred : np.ndarray
            Predicted labels
        y_proba : np.ndarray
            Predicted probabilities
        model_name : str
            Name of model for logging

        Returns
        -------
        dict
            Comprehensive metrics dictionary
        """

        metrics = {
            "model": model_name,
            # Overall metrics
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "f1_macro": float(f1_score(y_true, y_pred, average="macro")),
            "f1_weighted": float(f1_score(y_true, y_pred, average="weighted")),
            "log_loss": float(log_loss(y_true, y_proba, labels=list(self.classes))),
            "precision_macro": float(precision_score(y_true, y_pred, average="macro")),
            "recall_macro": float(recall_score(y_true, y_pred, average="macro")),
        }

        # Per-class metrics
        for i, class_label in enumerate(self.classes):
            y_binary = (y_true == class_label).astype(int)
            y_pred_binary = (y_pred == class_label).astype(int)

            metrics[f"precision_{class_label}"] = float(
                precision_score(y_binary, y_pred_binary, zero_division=0)
            )
            metrics[f"recall_{class_label}"] = float(
                recall_score(y_binary, y_pred_binary, zero_division=0)
            )
            metrics[f"f1_{class_label}"] = float(
                f1_score(y_binary, y_pred_binary, zero_division=0)
            )

        # Store for later use
        self.results[model_name] = {
            "y_true": y_true,
            "y_pred": y_pred,
            "y_proba": y_proba,
            "metrics": metrics,
        }

        return metrics

    def create_comparison_table(
        self,
        models_list: list[tuple[str, np.ndarray, np.ndarray, np.ndarray]],
    ) -> pd.DataFrame:
        """
        Create comparison table for multiple models.

        Parameters
        ----------
        models_list : list[tuple[str, np.ndarray, np.ndarray, np.ndarray]]
            List of (y_true, y_pred, y_proba, model_name)

        Returns
        -------
        pd.DataFrame
            Comparison table
        """

        results = []

        for y_true, y_pred, y_proba, model_name in models_list:
            metrics = self.calculate_metrics(y_true, y_pred, y_proba, model_name)
            results.append(metrics)

        df = pd.DataFrame(results)

        # Reorder columns for readability
        main_cols = ["model", "accuracy", "f1_macro", "f1_weighted", "log_loss"]
        other_cols = [col for col in df.columns if col not in main_cols]

        return df[main_cols + other_cols].sort_values("f1_macro", ascending=False)

    def generate_classification_report(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        model_name: str = "Model",
    ) -> str:
        """
        Generate scikit-learn classification report.

        Parameters
        ----------
        y_true : np.ndarray
            True labels
        y_pred : np.ndarray
            Predicted labels
        model_name : str
            Model name for report

        Returns
        -------
        str
            Formatted classification report
        """

        return classification_report(
            y_true,
            y_pred,
            target_names=self.classes,
            digits=4,
        )

    def plot_confusion_matrix(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        model_name: str = "Model",
        figsize: tuple[int, int] = (8, 6),
        save_path: Optional[str] = None,
    ):
        """
        Plot confusion matrix.

        Parameters
        ----------
        y_true : np.ndarray
            True labels
        y_pred : np.ndarray
            Predicted labels
        model_name : str
            Model name
        figsize : tuple[int, int]
            Figure size
        save_path : str, optional
            Path to save figure
        """

        cm = confusion_matrix(y_true, y_pred, labels=self.classes)

        fig, ax = plt.subplots(figsize=figsize)
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax)

        ax.set_title(f"Confusion Matrix - {model_name}")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        ax.set_xticklabels(self.classes)
        ax.set_yticklabels(self.classes)

        fig.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches="tight")

        return fig, ax

    def plot_model_comparison(
        self,
        comparison_df: pd.DataFrame,
        metrics_to_plot: list[str] = None,
        figsize: tuple[int, int] = (12, 6),
        save_path: Optional[str] = None,
    ):
        """
        Plot model comparison.

        Parameters
        ----------
        comparison_df : pd.DataFrame
            Comparison table from create_comparison_table()
        metrics_to_plot : list[str], optional
            Metrics to plot. Default: accuracy, f1_macro, log_loss
        figsize : tuple[int, int]
            Figure size
        save_path : str, optional
            Path to save figure
        """

        if metrics_to_plot is None:
            metrics_to_plot = ["accuracy", "f1_macro", "log_loss"]

        n_metrics = len(metrics_to_plot)
        fig, axes = plt.subplots(1, n_metrics, figsize=figsize)

        if n_metrics == 1:
            axes = [axes]

        for idx, metric in enumerate(metrics_to_plot):
            if metric in comparison_df.columns:
                data = comparison_df[["model", metric]].sort_values(metric, ascending=False)

                axes[idx].barh(data["model"], data[metric])
                axes[idx].set_xlabel(metric.replace("_", " ").title())
                axes[idx].set_title(f"{metric.upper()} Comparison")
                axes[idx].invert_yaxis()

        fig.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches="tight")

        return fig, axes

    def get_summary_stats(self) -> dict:
        """
        Get summary statistics from all evaluated models.

        Returns
        -------
        dict
            Summary statistics
        """

        if not self.results:
            return {}

        metrics_list = [r["metrics"] for r in self.results.values()]
        metrics_df = pd.DataFrame(metrics_list)

        summary = {
            "best_model_accuracy": metrics_df["accuracy"].idxmax(),
            "best_accuracy": metrics_df["accuracy"].max(),
            "best_f1_macro": metrics_df["f1_macro"].max(),
            "worst_accuracy": metrics_df["accuracy"].min(),
            "mean_accuracy": metrics_df["accuracy"].mean(),
            "std_accuracy": metrics_df["accuracy"].std(),
        }

        return summary


def evaluate_model(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray,
    model_name: str = "Model",
    classes: list[str] = None,
) -> dict:
    """
    Quick function to evaluate a single model.

    Parameters
    ----------
    y_true : np.ndarray
        True labels
    y_pred : np.ndarray
        Predicted labels
    y_proba : np.ndarray
        Predicted probabilities
    model_name : str
        Model name
    classes : list[str], optional
        Class labels

    Returns
    -------
    dict
        Evaluation metrics
    """

    evaluator = ExperimentEvaluator(classes=classes)
    return evaluator.calculate_metrics(y_true, y_pred, y_proba, model_name)


def compare_predictions(
    y_true: np.ndarray,
    models_predictions: dict[str, tuple[np.ndarray, np.ndarray]],
    classes: list[str] = None,
) -> pd.DataFrame:
    """
    Compare predictions across multiple models.

    Parameters
    ----------
    y_true : np.ndarray
        True labels
    models_predictions : dict[str, tuple[np.ndarray, np.ndarray]]
        Dictionary mapping model name to (y_pred, y_proba)
    classes : list[str], optional
        Class labels

    Returns
    -------
    pd.DataFrame
        Comparison table
    """

    evaluator = ExperimentEvaluator(classes=classes)

    models_list = [
        (y_true, y_pred, y_proba, model_name)
        for model_name, (y_pred, y_proba) in models_predictions.items()
    ]

    return evaluator.create_comparison_table(models_list)


# Export public API
__all__ = [
    "ExperimentEvaluator",
    "evaluate_model",
    "compare_predictions",
]
