from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATASETS_DIR = ROOT / "datasets"
COMPREHENSION_DIR = ROOT / "data" / "comprehension"
PLOTS_DIR = COMPREHENSION_DIR / "plots"
PROCESSED_DIR = ROOT / "data" / "processed"

BASE_COLUMNS = [
    "Date",
    "HomeTeam",
    "AwayTeam",
    "FTHG",
    "FTAG",
    "FTR",
    "HTHG",
    "HTAG",
    "HTR",
    "Referee",
    "HS",
    "AS",
    "HST",
    "AST",
    "HF",
    "AF",
    "HC",
    "AC",
    "HY",
    "AY",
    "HR",
    "AR",
]

RENAME_MAP = {
    "Date": "match_date",
    "HomeTeam": "home_team",
    "AwayTeam": "away_team",
    "FTHG": "home_goals",
    "FTAG": "away_goals",
    "FTR": "full_time_result",
    "HTHG": "half_time_home_goals",
    "HTAG": "half_time_away_goals",
    "HTR": "half_time_result",
    "Referee": "referee",
    "HS": "home_shots",
    "AS": "away_shots",
    "HST": "home_shots_on_target",
    "AST": "away_shots_on_target",
    "HF": "home_fouls",
    "AF": "away_fouls",
    "HC": "home_corners",
    "AC": "away_corners",
    "HY": "home_yellows",
    "AY": "away_yellows",
    "HR": "home_reds",
    "AR": "away_reds",
}

NUMERIC_COLUMNS = [
    "home_goals",
    "away_goals",
    "half_time_home_goals",
    "half_time_away_goals",
    "home_shots",
    "away_shots",
    "home_shots_on_target",
    "away_shots_on_target",
    "home_fouls",
    "away_fouls",
    "home_corners",
    "away_corners",
    "home_yellows",
    "away_yellows",
    "home_reds",
    "away_reds",
]


def reset_output_dirs() -> None:
    for directory in [COMPREHENSION_DIR, PROCESSED_DIR]:
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def read_all_datasets() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    csv_files = sorted(DATASETS_DIR.glob("*/*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No dataset CSV found under: {DATASETS_DIR}")

    for csv_path in csv_files:
        league = csv_path.parent.name
        season = csv_path.stem.replace("season-", "")
        df = pd.read_csv(csv_path, encoding="latin-1")
        missing_cols = [c for c in BASE_COLUMNS if c not in df.columns]
        if missing_cols:
            raise ValueError(f"{csv_path} missing columns: {missing_cols}")
        df = df[BASE_COLUMNS].copy()
        df["league"] = league
        df["season"] = season
        frames.append(df)

    return pd.concat(frames, ignore_index=True)


def preprocess_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.rename(columns=RENAME_MAP).copy()

    df["home_team"] = df["home_team"].astype("string").str.strip()
    df["away_team"] = df["away_team"].astype("string").str.strip()
    df["referee"] = df["referee"].astype("string").str.strip()
    df["full_time_result"] = df["full_time_result"].astype("string").str.strip().str.upper()
    df["half_time_result"] = df["half_time_result"].astype("string").str.strip().str.upper()
    df["match_date"] = pd.to_datetime(df["match_date"], format="%d/%m/%y", errors="coerce")

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.drop_duplicates(
        subset=["league", "season", "match_date", "home_team", "away_team"],
        keep="first",
    ).copy()

    df["goal_diff"] = df["home_goals"] - df["away_goals"]
    df["total_goals"] = df["home_goals"] + df["away_goals"]
    df["home_win"] = (df["full_time_result"] == "H").astype("Int64")
    df["draw"] = (df["full_time_result"] == "D").astype("Int64")
    df["away_win"] = (df["full_time_result"] == "A").astype("Int64")
    df["match_year"] = df["match_date"].dt.year
    df["match_month"] = df["match_date"].dt.month

    return df.sort_values(["league", "match_date", "season", "home_team"], kind="stable").reset_index(drop=True)


def write_eda_tables(df: pd.DataFrame) -> None:
    overview_md = COMPREHENSION_DIR / "overview.md"
    season_index_csv = COMPREHENSION_DIR / "season_index.csv"

    missing_pct = (df.isna().mean() * 100).round(2).sort_values(ascending=False)
    rows_by_league = df.groupby("league").size().sort_values(ascending=False)
    seasons_by_league = df.groupby("league")["season"].nunique().sort_values(ascending=False)

    lines = [
        "# Data Comprehension - Professional EDA",
        "",
        f"- Rows: {len(df)}",
        f"- Date range: {df['match_date'].min().date()} to {df['match_date'].max().date()}",
        f"- Leagues: {', '.join(sorted(df['league'].dropna().unique().tolist()))}",
        "",
        "## Rows by League",
    ]
    for league, rows in rows_by_league.items():
        lines.append(f"- {league}: {int(rows)}")
    lines.extend(["", "## Seasons by League"])
    for league, seasons in seasons_by_league.items():
        lines.append(f"- {league}: {int(seasons)}")
    lines.extend(["", "## Top Missing (%)"])
    for col, pct in missing_pct.head(15).items():
        lines.append(f"- {col}: {float(pct)}")

    with overview_md.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    season_index = (
        df.groupby(["league", "season"], as_index=False)
        .agg(
            rows=("league", "size"),
            date_min=("match_date", "min"),
            date_max=("match_date", "max"),
            avg_total_goals=("total_goals", "mean"),
            home_win_rate=("home_win", "mean"),
            draw_rate=("draw", "mean"),
            away_win_rate=("away_win", "mean"),
        )
        .sort_values(["league", "season"])
    )
    season_index["home_win_rate"] = season_index["home_win_rate"].round(4)
    season_index["draw_rate"] = season_index["draw_rate"].round(4)
    season_index["away_win_rate"] = season_index["away_win_rate"].round(4)
    season_index["avg_total_goals"] = season_index["avg_total_goals"].round(3)
    season_index.to_csv(season_index_csv, index=False, encoding="utf-8")


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)


def write_global_plots(df: pd.DataFrame) -> None:
    missing = (df.isna().mean() * 100).sort_values(ascending=False).head(15)
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.bar(missing.index, missing.values, color="#2563eb")
    ax.set_title("Top Missing Columns (%) - Global")
    ax.set_ylabel("Missing %")
    ax.tick_params(axis="x", rotation=45)
    _save(fig, PLOTS_DIR / "01_global_missingness_top15.png")

    result_counts = (
        df.groupby("league")["full_time_result"]
        .value_counts(normalize=True)
        .rename("pct")
        .reset_index()
        .pivot(index="league", columns="full_time_result", values="pct")
        .fillna(0)
        .reindex(columns=["H", "D", "A"], fill_value=0)
    )
    fig, ax = plt.subplots(figsize=(9, 5))
    bottom = np.zeros(len(result_counts))
    colors = {"H": "#16a34a", "D": "#f59e0b", "A": "#dc2626"}
    for col in ["H", "D", "A"]:
        vals = result_counts[col].values
        ax.bar(result_counts.index, vals, bottom=bottom, label=col, color=colors[col])
        bottom += vals
    ax.set_title("Result Mix by League (H/D/A)")
    ax.set_ylabel("Share")
    ax.legend(title="FTR")
    ax.tick_params(axis="x", rotation=20)
    _save(fig, PLOTS_DIR / "02_global_result_mix_by_league.png")

    fig, ax = plt.subplots(figsize=(9, 5))
    bins = np.arange(0, max(10, int(df["total_goals"].max()) + 2)) - 0.5
    ax.hist(df["total_goals"].dropna(), bins=bins, color="#7c3aed", alpha=0.8)
    ax.set_title("Distribution of Total Goals per Match")
    ax.set_xlabel("Total Goals")
    ax.set_ylabel("Matches")
    _save(fig, PLOTS_DIR / "03_global_total_goals_distribution.png")

    goals_trend = (
        df.groupby(["league", "season"], as_index=False)["total_goals"]
        .mean()
        .sort_values(["league", "season"])
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    for league, g in goals_trend.groupby("league"):
        ax.plot(g["season"], g["total_goals"], marker="o", linewidth=1.5, label=league)
    ax.set_title("Average Total Goals by Season and League")
    ax.set_xlabel("Season")
    ax.set_ylabel("Avg Total Goals")
    ax.tick_params(axis="x", rotation=90)
    ax.legend()
    _save(fig, PLOTS_DIR / "04_global_avg_goals_by_season_league.png")

    home_adv = (
        df.groupby(["league", "season"], as_index=False)["home_win"]
        .mean()
        .sort_values(["league", "season"])
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    for league, g in home_adv.groupby("league"):
        ax.plot(g["season"], g["home_win"], marker="o", linewidth=1.5, label=league)
    ax.set_title("Home Win Rate by Season and League")
    ax.set_xlabel("Season")
    ax.set_ylabel("Home Win Rate")
    ax.tick_params(axis="x", rotation=90)
    ax.legend()
    _save(fig, PLOTS_DIR / "05_global_home_win_rate_by_season_league.png")

    sampled = df.dropna(subset=["home_shots", "home_goals"]).sample(n=min(12000, len(df)), random_state=42)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(sampled["home_shots"], sampled["home_goals"], s=10, alpha=0.25, color="#0284c7")
    ax.set_title("Home Shots vs Home Goals (sampled)")
    ax.set_xlabel("Home Shots")
    ax.set_ylabel("Home Goals")
    _save(fig, PLOTS_DIR / "06_global_home_shots_vs_goals.png")

    corr_cols = [
        "home_goals",
        "away_goals",
        "total_goals",
        "home_shots",
        "away_shots",
        "home_shots_on_target",
        "away_shots_on_target",
        "home_fouls",
        "away_fouls",
        "home_corners",
        "away_corners",
    ]
    corr = df[corr_cols].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.index)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticklabels(corr.index)
    ax.set_title("Correlation Heatmap (Core Match Stats)")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    _save(fig, PLOTS_DIR / "07_global_correlation_heatmap.png")

    box_data = [g["total_goals"].dropna().values for _, g in df.groupby("league")]
    labels = [league for league, _ in df.groupby("league")]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.boxplot(box_data, tick_labels=labels, patch_artist=True, boxprops={"facecolor": "#93c5fd"})
    ax.set_title("Total Goals Distribution by League")
    ax.set_ylabel("Total Goals")
    ax.tick_params(axis="x", rotation=20)
    _save(fig, PLOTS_DIR / "08_global_total_goals_boxplot_by_league.png")

    cards = (
        df.groupby("league", as_index=False)[["home_yellows", "away_yellows", "home_reds", "away_reds"]]
        .mean(numeric_only=True)
    )
    cards["avg_yellows"] = cards["home_yellows"] + cards["away_yellows"]
    cards["avg_reds"] = cards["home_reds"] + cards["away_reds"]
    x = np.arange(len(cards))
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x - 0.2, cards["avg_yellows"], width=0.4, label="Avg Yellows", color="#eab308")
    ax.bar(x + 0.2, cards["avg_reds"], width=0.4, label="Avg Reds", color="#ef4444")
    ax.set_xticks(x)
    ax.set_xticklabels(cards["league"], rotation=20, ha="right")
    ax.set_title("Average Cards per Match by League")
    ax.set_ylabel("Cards")
    ax.legend()
    _save(fig, PLOTS_DIR / "09_global_cards_by_league.png")

    by_month = df.groupby("match_month").size().reindex(range(1, 13), fill_value=0)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(by_month.index, by_month.values, color="#0891b2")
    ax.set_title("Matches by Month (All Leagues)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Matches")
    _save(fig, PLOTS_DIR / "10_global_matches_by_month.png")


def write_league_plots(df: pd.DataFrame) -> None:
    for league, g in df.groupby("league", sort=True):
        league_dir = PLOTS_DIR / "by_league" / league
        league_dir.mkdir(parents=True, exist_ok=True)

        ftr = g["full_time_result"].value_counts().reindex(["H", "D", "A"], fill_value=0)
        fig, ax = plt.subplots(figsize=(6.5, 4.5))
        ax.bar(ftr.index, ftr.values, color=["#16a34a", "#f59e0b", "#dc2626"])
        ax.set_title(f"{league} - FTR Distribution")
        ax.set_xlabel("Result")
        ax.set_ylabel("Matches")
        _save(fig, league_dir / "01_ftr_distribution.png")

        trend = g.groupby("season", as_index=False)["total_goals"].mean()
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.plot(trend["season"], trend["total_goals"], marker="o", color="#7c3aed")
        ax.set_title(f"{league} - Avg Total Goals by Season")
        ax.set_xlabel("Season")
        ax.set_ylabel("Avg Total Goals")
        ax.tick_params(axis="x", rotation=90)
        _save(fig, league_dir / "02_avg_total_goals_by_season.png")

        missing = (g.isna().mean() * 100).sort_values(ascending=False).head(12)
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.bar(missing.index, missing.values, color="#2563eb")
        ax.set_title(f"{league} - Top Missing Columns (%)")
        ax.set_ylabel("Missing %")
        ax.tick_params(axis="x", rotation=45)
        _save(fig, league_dir / "03_missingness_top12.png")

        home_adv = g.groupby("season", as_index=False)["home_win"].mean()
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.plot(home_adv["season"], home_adv["home_win"], marker="o", color="#0f766e")
        ax.set_title(f"{league} - Home Win Rate by Season")
        ax.set_xlabel("Season")
        ax.set_ylabel("Home Win Rate")
        ax.tick_params(axis="x", rotation=90)
        _save(fig, league_dir / "04_home_win_rate_by_season.png")


def write_season_plots(df: pd.DataFrame) -> None:
    for (league, season), g in df.groupby(["league", "season"], sort=True):
        season_dir = PLOTS_DIR / "by_league" / league / "by_season"
        season_dir.mkdir(parents=True, exist_ok=True)

        ftr = g["full_time_result"].value_counts().reindex(["H", "D", "A"], fill_value=0)
        means = pd.Series(
            {
                "home_goals": g["home_goals"].mean(),
                "away_goals": g["away_goals"].mean(),
                "total_goals": g["total_goals"].mean(),
            }
        )
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].bar(ftr.index, ftr.values, color=["#16a34a", "#f59e0b", "#dc2626"])
        axes[0].set_title("Result Distribution")
        axes[0].set_xlabel("FTR")
        axes[0].set_ylabel("Matches")
        axes[1].bar(means.index, means.values, color=["#0284c7", "#0891b2", "#7c3aed"])
        axes[1].set_title("Average Goals")
        axes[1].set_ylabel("Goals")
        fig.suptitle(f"{league} - season-{season}")
        _save(fig, season_dir / f"season-{season}.png")


def write_preprocessed_outputs(df_clean: pd.DataFrame) -> None:
    all_dir = PROCESSED_DIR / "all_leagues"
    all_dir.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(all_dir / "matches_clean.csv", index=False, encoding="utf-8")

    by_league_dir = PROCESSED_DIR / "by_league"
    by_league_dir.mkdir(parents=True, exist_ok=True)

    for league, league_df in df_clean.groupby("league", sort=True):
        league_dir = by_league_dir / league
        season_dir = league_dir / "by_season"
        league_dir.mkdir(parents=True, exist_ok=True)
        season_dir.mkdir(parents=True, exist_ok=True)

        league_df = league_df.sort_values(["match_date", "season", "home_team"], kind="stable")
        league_df.to_csv(league_dir / "matches_clean.csv", index=False, encoding="utf-8")
        for season, season_df in league_df.groupby("season", sort=True):
            season_df.to_csv(season_dir / f"season-{season}.csv", index=False, encoding="utf-8")


def main() -> None:
    reset_output_dirs()
    raw = read_all_datasets()
    clean = preprocess_data(raw)

    # Step 1: Professional EDA (tables + plots)
    write_eda_tables(clean)
    write_global_plots(clean)
    write_league_plots(clean)
    write_season_plots(clean)

    # Step 2: Preprocessing outputs
    write_preprocessed_outputs(clean)

    print("Step 1 completed: Professional EDA generated.")
    print(f"EDA outputs: {COMPREHENSION_DIR}")
    print("Step 2 completed: Preprocessing generated.")
    print(f"Processed outputs: {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
