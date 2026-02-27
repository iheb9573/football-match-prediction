from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import FOLDER_TO_LEAGUE, LEAGUE_TO_FOLDER, ProjectPaths
from .utils import season_code_to_start_year


RAW_COLUMNS = [
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


def _read_league_files(league_code: str, league_folder: str, source_dir: Path) -> pd.DataFrame:
    folder = source_dir / league_folder
    csv_files = sorted(folder.glob("season-*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No season CSV found in {folder}")

    records: list[pd.DataFrame] = []
    for csv_path in csv_files:
        season_code = csv_path.stem.replace("season-", "")
        df = pd.read_csv(csv_path, encoding="latin-1")
        missing_cols = [c for c in RAW_COLUMNS if c not in df.columns]
        if missing_cols:
            raise ValueError(f"{csv_path} missing columns: {missing_cols}")

        block = df[RAW_COLUMNS].copy()
        block["league_code"] = league_code
        block["league_folder"] = league_folder
        block["league_name"] = FOLDER_TO_LEAGUE.get(league_folder, league_code)
        block["season_code"] = season_code
        block["season_start_year"] = season_code_to_start_year(season_code)
        block["source_file"] = str(csv_path)
        records.append(block)

    return pd.concat(records, ignore_index=True)


def ingest_all_matches(paths: ProjectPaths) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for league_code, folder in LEAGUE_TO_FOLDER.items():
        frames.append(_read_league_files(league_code=league_code, league_folder=folder, source_dir=paths.source_datasets_dir))
    df = pd.concat(frames, ignore_index=True)
    return df


def save_raw_dataset(df_raw: pd.DataFrame, paths: ProjectPaths) -> Path:
    output_path = paths.raw_dir / "matches_raw.csv"
    paths.raw_dir.mkdir(parents=True, exist_ok=True)
    df_raw.to_csv(output_path, index=False, encoding="utf-8")
    return output_path
