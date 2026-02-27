from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .config import ProjectPaths


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)


def generate_eda_outputs(df_clean: pd.DataFrame, df_features: pd.DataFrame, paths: ProjectPaths) -> None:
    summary_path = paths.reports_dir / "eda_summary.md"
    league_summary_path = paths.reports_dir / "league_summary.csv"
    season_summary_path = paths.reports_dir / "season_summary.csv"

    league_summary = (
        df_clean.groupby("league_code", as_index=False)
        .agg(
            matches=("league_code", "size"),
            teams=("home_team", "nunique"),
            avg_total_goals=("total_goals", "mean"),
            home_win_rate=("home_win", "mean"),
            draw_rate=("draw", "mean"),
            away_win_rate=("away_win", "mean"),
        )
        .sort_values("matches", ascending=False)
    )
    league_summary["avg_total_goals"] = league_summary["avg_total_goals"].round(3)
    league_summary["home_win_rate"] = league_summary["home_win_rate"].round(3)
    league_summary["draw_rate"] = league_summary["draw_rate"].round(3)
    league_summary["away_win_rate"] = league_summary["away_win_rate"].round(3)
    league_summary.to_csv(league_summary_path, index=False, encoding="utf-8")

    season_summary = (
        df_clean.groupby(["league_code", "season_code"], as_index=False)
        .agg(
            matches=("league_code", "size"),
            start_date=("match_date", "min"),
            end_date=("match_date", "max"),
            avg_total_goals=("total_goals", "mean"),
        )
        .sort_values(["league_code", "season_code"])
    )
    season_summary["avg_total_goals"] = season_summary["avg_total_goals"].round(3)
    season_summary.to_csv(season_summary_path, index=False, encoding="utf-8")

    missing = (df_clean.isna().mean() * 100).sort_values(ascending=False)
    lines = [
        "# EDA Summary",
        "",
        f"- Matches: {len(df_clean)}",
        f"- Date range: {df_clean['match_date'].min().date()} to {df_clean['match_date'].max().date()}",
        f"- Leagues: {', '.join(sorted(df_clean['league_code'].unique().tolist()))}",
        "",
        "## Top Missing Columns (%)",
    ]
    for col, pct in missing.head(12).items():
        lines.append(f"- {col}: {pct:.2f}")
    summary_path.write_text("\n".join(lines), encoding="utf-8")

    sns.set_theme(style="whitegrid")

    fig, ax = plt.subplots(figsize=(10, 5))
    top_missing = missing.head(12)
    ax.bar(top_missing.index, top_missing.values, color="#2563eb")
    ax.set_title("Top Missing Columns (%)")
    ax.set_ylabel("Missing %")
    ax.tick_params(axis="x", rotation=45)
    _save(fig, paths.figures_dir / "01_missingness_top12.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    ftr = df_clean["full_time_result"].value_counts().reindex(["H", "D", "A"], fill_value=0)
    ax.bar(ftr.index, ftr.values, color=["#16a34a", "#f59e0b", "#dc2626"])
    ax.set_title("Match Result Distribution (H / D / A)")
    ax.set_ylabel("Matches")
    _save(fig, paths.figures_dir / "02_result_distribution.png")

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(df_clean["total_goals"], bins=20, color="#7c3aed", alpha=0.85)
    ax.set_title("Total Goals Distribution")
    ax.set_xlabel("Total Goals")
    ax.set_ylabel("Matches")
    _save(fig, paths.figures_dir / "03_total_goals_distribution.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    rows_by_league = df_clean.groupby("league_code").size().sort_values(ascending=False)
    ax.bar(rows_by_league.index, rows_by_league.values, color="#0f766e")
    ax.set_title("Matches by League")
    ax.set_ylabel("Matches")
    _save(fig, paths.figures_dir / "04_matches_by_league.png")

    fig, ax = plt.subplots(figsize=(12, 6))
    goals_trend = df_clean.groupby(["league_code", "season_code"], as_index=False)["total_goals"].mean()
    for league, block in goals_trend.groupby("league_code"):
        block = block.sort_values("season_code")
        ax.plot(block["season_code"], block["total_goals"], marker="o", linewidth=1.5, label=league)
    ax.set_title("Average Total Goals by Season")
    ax.set_xlabel("Season")
    ax.set_ylabel("Avg Goals")
    ax.tick_params(axis="x", rotation=90)
    ax.legend()
    _save(fig, paths.figures_dir / "05_goals_by_season.png")

    fig, ax = plt.subplots(figsize=(12, 6))
    home_trend = df_clean.groupby(["league_code", "season_code"], as_index=False)["home_win"].mean()
    for league, block in home_trend.groupby("league_code"):
        block = block.sort_values("season_code")
        ax.plot(block["season_code"], block["home_win"], marker="o", linewidth=1.5, label=league)
    ax.set_title("Home Win Rate by Season")
    ax.set_xlabel("Season")
    ax.set_ylabel("Home Win Rate")
    ax.tick_params(axis="x", rotation=90)
    ax.legend()
    _save(fig, paths.figures_dir / "06_home_win_rate_by_season.png")

    sample = df_clean.dropna(subset=["home_shots", "home_goals"]).sample(n=min(10000, len(df_clean)), random_state=42)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(sample["home_shots"], sample["home_goals"], s=10, alpha=0.25, color="#0284c7")
    ax.set_title("Home Shots vs Home Goals (sample)")
    ax.set_xlabel("Home Shots")
    ax.set_ylabel("Home Goals")
    _save(fig, paths.figures_dir / "07_home_shots_vs_goals.png")

    corr_cols = [
        "home_elo_pre",
        "away_elo_pre",
        "elo_diff",
        "home_points_per_game_pre",
        "away_points_per_game_pre",
        "ppg_diff",
        "home_rest_days_pre",
        "away_rest_days_pre",
    ]
    corr = df_features[corr_cols].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5, ax=ax)
    ax.set_title("Correlation Heatmap - Pre-match Features")
    _save(fig, paths.figures_dir / "08_feature_correlation_heatmap.png")
