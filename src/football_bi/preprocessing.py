from __future__ import annotations

import pandas as pd


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

NUMERIC_STAT_COLS = [
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

IMPUTE_STAT_COLS = [
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


def clean_matches(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.rename(columns=RENAME_MAP).copy()

    for col in ["home_team", "away_team", "referee", "league_code", "league_name", "season_code"]:
        df[col] = df[col].astype("string").str.strip()

    df["full_time_result"] = df["full_time_result"].astype("string").str.strip().str.upper()
    df["half_time_result"] = df["half_time_result"].astype("string").str.strip().str.upper()

    df["match_date"] = pd.to_datetime(df["match_date"], format="%d/%m/%y", errors="coerce")
    for col in NUMERIC_STAT_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Keep a missing flag for BI/explainability.
    for col in IMPUTE_STAT_COLS:
        df[f"{col}_was_missing"] = df[col].isna().astype("Int64")

    # Hierarchical imputation: (league, season) -> league -> global median.
    for col in IMPUTE_STAT_COLS:
        df[col] = df[col].fillna(df.groupby(["league_code", "season_code"])[col].transform("median"))
        df[col] = df[col].fillna(df.groupby("league_code")[col].transform("median"))
        df[col] = df[col].fillna(df[col].median())

    # Referee has very high missingness: explicit token.
    df["referee"] = df["referee"].fillna("Unknown")
    df["referee"] = df["referee"].replace("", "Unknown")

    # Remove records without valid match date and core target info.
    df = df.dropna(subset=["match_date", "home_team", "away_team", "home_goals", "away_goals", "full_time_result"]).copy()
    df = df[df["full_time_result"].isin(["H", "D", "A"])].copy()

    # Drop duplicates on natural match key.
    df = df.drop_duplicates(
        subset=["league_code", "season_code", "match_date", "home_team", "away_team"],
        keep="first",
    ).copy()

    df["goal_diff"] = df["home_goals"] - df["away_goals"]
    df["total_goals"] = df["home_goals"] + df["away_goals"]
    df["home_win"] = (df["full_time_result"] == "H").astype("Int64")
    df["draw"] = (df["full_time_result"] == "D").astype("Int64")
    df["away_win"] = (df["full_time_result"] == "A").astype("Int64")
    df["match_year"] = df["match_date"].dt.year
    df["match_month"] = df["match_date"].dt.month
    df["match_weekday"] = df["match_date"].dt.dayofweek

    df = df.sort_values(["league_code", "season_start_year", "match_date", "home_team"], kind="stable").reset_index(drop=True)
    return df


def save_clean_matches(df_clean: pd.DataFrame, output_path: str) -> None:
    df_clean.to_csv(output_path, index=False, encoding="utf-8")
