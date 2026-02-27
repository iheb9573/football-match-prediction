from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import ProjectPaths


@dataclass
class TrainingArtifacts:
    model_path: Path
    metadata_path: Path
    metrics_path: Path
    predictions_path: Path
    selected_model_name: str


NUMERIC_FEATURES = [
    "home_elo_pre",
    "away_elo_pre",
    "elo_diff",
    "home_matches_played_pre",
    "away_matches_played_pre",
    "home_points_per_game_pre",
    "away_points_per_game_pre",
    "ppg_diff",
    "home_goal_diff_per_game_pre",
    "away_goal_diff_per_game_pre",
    "goal_diff_pg_diff",
    "home_recent_points_avg_pre",
    "away_recent_points_avg_pre",
    "recent_points_diff",
    "home_recent_goal_diff_avg_pre",
    "away_recent_goal_diff_avg_pre",
    "recent_goal_diff_diff",
    "home_rest_days_pre",
    "away_rest_days_pre",
    "rest_days_diff",
    "month",
    "weekday",
]

CATEGORICAL_FEATURES = ["league_code", "home_team", "away_team"]


def _temporal_split(df_features: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    season_years = sorted(df_features["season_start_year"].unique().tolist())
    if len(season_years) < 3:
        raise ValueError("Need at least 3 season years for temporal split.")

    train_years = season_years[:-2]
    valid_year = season_years[-2]
    test_year = season_years[-1]

    train_df = df_features[df_features["season_start_year"].isin(train_years)].copy()
    valid_df = df_features[df_features["season_start_year"] == valid_year].copy()
    test_df = df_features[df_features["season_start_year"] == test_year].copy()
    return train_df, valid_df, test_df


def _build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def _candidate_models(random_state: int = 42) -> dict[str, object]:
    return {
        "logistic_regression": LogisticRegression(
            max_iter=3000,
            class_weight="balanced",
            random_state=random_state,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=350,
            max_depth=18,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=random_state,
        ),
        "extra_trees": ExtraTreesClassifier(
            n_estimators=500,
            max_depth=20,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=random_state,
        ),
    }


def _evaluate(y_true: pd.Series, y_pred: np.ndarray, y_proba: np.ndarray, class_order: np.ndarray) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro")),
        "log_loss": float(log_loss(y_true, y_proba, labels=list(class_order))),
    }


def _save_model_comparison_plot(results_df: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(results_df))
    ax.bar(x - 0.15, results_df["accuracy"], width=0.3, label="Accuracy", color="#0ea5e9")
    ax.bar(x + 0.15, results_df["f1_macro"], width=0.3, label="F1 Macro", color="#22c55e")
    ax.set_xticks(x)
    ax.set_xticklabels(results_df["model"])
    ax.set_ylim(0, 1)
    ax.set_title("Validation Metrics by Model")
    ax.legend()
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=170)
    plt.close(fig)


def _save_confusion_matrix(y_true: pd.Series, y_pred: np.ndarray, output_path: Path) -> None:
    cm = confusion_matrix(y_true, y_pred, labels=["H", "D", "A"])
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax)
    ax.set_title("Confusion Matrix (Test)")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_xticklabels(["H", "D", "A"])
    ax.set_yticklabels(["H", "D", "A"])
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=170)
    plt.close(fig)


def train_models(df_features: pd.DataFrame, paths: ProjectPaths, random_state: int = 42) -> TrainingArtifacts:
    train_df, valid_df, test_df = _temporal_split(df_features)

    X_train = train_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_train = train_df["target_result"]
    X_valid = valid_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_valid = valid_df["target_result"]

    preprocessor = _build_preprocessor()
    candidates = _candidate_models(random_state=random_state)

    validation_rows = []
    fitted_candidates: dict[str, Pipeline] = {}

    for model_name, estimator in candidates.items():
        pipeline = Pipeline([("preprocessor", preprocessor), ("model", estimator)])
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_valid)
        y_proba = pipeline.predict_proba(X_valid)
        class_order = pipeline.named_steps["model"].classes_

        metrics = _evaluate(y_valid, y_pred, y_proba, class_order)
        validation_rows.append({"model": model_name, **metrics})
        fitted_candidates[model_name] = pipeline

    validation_df = pd.DataFrame(validation_rows).sort_values(["f1_macro", "log_loss"], ascending=[False, True])
    selected_model_name = str(validation_df.iloc[0]["model"])
    selected_pipeline = fitted_candidates[selected_model_name]

    # Refit best model on train + validation for final test evaluation.
    train_valid_df = pd.concat([train_df, valid_df], ignore_index=True)
    X_train_valid = train_valid_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_train_valid = train_valid_df["target_result"]
    selected_pipeline.fit(X_train_valid, y_train_valid)

    X_test = test_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_test = test_df["target_result"]
    y_test_pred = selected_pipeline.predict(X_test)
    y_test_proba = selected_pipeline.predict_proba(X_test)
    classes = selected_pipeline.named_steps["model"].classes_
    test_metrics = _evaluate(y_test, y_test_pred, y_test_proba, classes)

    # Save artifacts.
    paths.models_dir.mkdir(parents=True, exist_ok=True)
    paths.reports_dir.mkdir(parents=True, exist_ok=True)
    paths.figures_dir.mkdir(parents=True, exist_ok=True)

    model_path = paths.models_dir / "match_outcome_model.joblib"
    metadata_path = paths.models_dir / "match_outcome_model_metadata.json"
    metrics_path = paths.reports_dir / "model_metrics.csv"
    predictions_path = paths.reports_dir / "test_predictions.csv"

    joblib.dump(selected_pipeline, model_path)

    metadata = {
        "selected_model_name": selected_model_name,
        "classes": classes.tolist(),
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "train_years": sorted(train_df["season_start_year"].unique().tolist()),
        "valid_year": int(valid_df["season_start_year"].iloc[0]),
        "test_year": int(test_df["season_start_year"].iloc[0]),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    validation_df["stage"] = "validation"
    test_df_metrics = pd.DataFrame([{"model": selected_model_name, "stage": "test", **test_metrics}])
    all_metrics_df = pd.concat([validation_df, test_df_metrics], ignore_index=True)
    all_metrics_df.to_csv(metrics_path, index=False, encoding="utf-8")

    test_output = test_df[
        ["league_code", "season_code", "match_date", "home_team", "away_team", "target_result", "home_goals_actual", "away_goals_actual"]
    ].copy()
    for idx, cls in enumerate(classes):
        test_output[f"proba_{cls}"] = y_test_proba[:, idx]
    test_output["predicted_result"] = y_test_pred
    test_output.to_csv(predictions_path, index=False, encoding="utf-8")

    _save_model_comparison_plot(validation_df, paths.figures_dir / "09_model_validation_comparison.png")
    _save_confusion_matrix(y_test, y_test_pred, paths.figures_dir / "10_test_confusion_matrix.png")

    report_text = classification_report(y_test, y_test_pred, digits=4)
    (paths.reports_dir / "classification_report_test.txt").write_text(report_text, encoding="utf-8")

    return TrainingArtifacts(
        model_path=model_path,
        metadata_path=metadata_path,
        metrics_path=metrics_path,
        predictions_path=predictions_path,
        selected_model_name=selected_model_name,
    )
