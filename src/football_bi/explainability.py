from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.inspection import permutation_importance

from .config import ProjectPaths


def _save_plot(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)


def run_explainability(df_features: pd.DataFrame, paths: ProjectPaths) -> None:
    model_path = paths.models_dir / "match_outcome_model.joblib"
    metadata_path = paths.models_dir / "match_outcome_model_metadata.json"
    if not model_path.exists() or not metadata_path.exists():
        raise FileNotFoundError("Model artifacts missing. Run model training first.")

    pipeline = joblib.load(model_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    numeric_features = metadata["numeric_features"]
    categorical_features = metadata["categorical_features"]
    feature_columns = numeric_features + categorical_features
    test_year = int(metadata["test_year"])

    test_df = df_features[df_features["season_start_year"] == test_year].copy()
    X_test = test_df[feature_columns]
    y_test = test_df["target_result"]

    preprocessor = pipeline.named_steps["preprocessor"]
    transformed_feature_names = preprocessor.get_feature_names_out()

    perm = permutation_importance(
        estimator=pipeline,
        X=X_test,
        y=y_test,
        n_repeats=8,
        random_state=42,
        scoring="f1_macro",
        n_jobs=-1,
    )

    perm_df = pd.DataFrame(
        {
            "feature": X_test.columns,
            "importance_mean": perm.importances_mean,
            "importance_std": perm.importances_std,
        }
    ).sort_values("importance_mean", ascending=False)
    perm_df.to_csv(paths.reports_dir / "permutation_importance.csv", index=False, encoding="utf-8")

    top_perm = perm_df.head(20).sort_values("importance_mean", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(top_perm["feature"], top_perm["importance_mean"], color="#2563eb")
    ax.set_title("Top 20 Permutation Importances (F1 Macro)")
    ax.set_xlabel("Importance")
    _save_plot(fig, paths.figures_dir / "11_permutation_importance_top20.png")

    model = pipeline.named_steps["model"]
    coef_summary_path = paths.reports_dir / "logistic_coefficients_top.csv"

    if hasattr(model, "coef_"):
        coef = model.coef_
        class_names = model.classes_
        coef_rows: list[pd.DataFrame] = []
        for idx, cls in enumerate(class_names):
            cls_df = pd.DataFrame(
                {
                    "feature": transformed_feature_names,
                    "coefficient": coef[idx],
                    "abs_coefficient": abs(coef[idx]),
                    "class": cls,
                }
            ).sort_values("abs_coefficient", ascending=False)
            coef_rows.append(cls_df.head(20))
        coef_summary = pd.concat(coef_rows, ignore_index=True)
        coef_summary.to_csv(coef_summary_path, index=False, encoding="utf-8")

        for cls in class_names:
            plot_df = coef_summary[coef_summary["class"] == cls].sort_values("coefficient")
            fig, ax = plt.subplots(figsize=(10, 7))
            colors = ["#dc2626" if x < 0 else "#16a34a" for x in plot_df["coefficient"]]
            ax.barh(plot_df["feature"], plot_df["coefficient"], color=colors)
            ax.set_title(f"Top Logistic Coefficients - Class {cls}")
            ax.set_xlabel("Coefficient")
            _save_plot(fig, paths.figures_dir / f"12_logistic_coefficients_class_{cls}.png")

    explain_lines = [
        "# Explainability Summary",
        "",
        f"- Test season start year: {test_year}",
        f"- Number of test matches: {len(test_df)}",
        "- Main explainability method: permutation importance (global).",
        "- Additional method (if Logistic Regression selected): class-wise coefficients.",
        "",
        "## Top 10 permutation features",
    ]
    for _, row in perm_df.head(10).iterrows():
        explain_lines.append(f"- {row['feature']}: {row['importance_mean']:.6f}")
    (paths.reports_dir / "explainability_summary.md").write_text("\n".join(explain_lines), encoding="utf-8")
