from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


LEAGUES = {
    "EPL": "english-premier-league",
    "LaLiga": "spanish-la-liga",
    "SerieA": "italian-serie-a",
    "Bundesliga": "german-bundesliga",
    "Ligue1": "french-ligue-1",
}

LEAGUE_TO_FOLDER = {
    "EPL": "premier-league",
    "LaLiga": "la-liga",
    "SerieA": "serie-a",
    "Bundesliga": "bundesliga",
    "Ligue1": "ligue-1",
}

FOLDER_TO_LEAGUE = {v: k for k, v in LEAGUE_TO_FOLDER.items()}


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    source_datasets_dir: Path
    raw_dir: Path
    processed_dir: Path
    reports_dir: Path
    figures_dir: Path
    models_dir: Path
    logs_dir: Path
    bi_dir: Path


def get_default_paths() -> ProjectPaths:
    root = Path(__file__).resolve().parents[2]
    source = root / "data" / "Scrapping" / "football-datasets-main" / "football-datasets-main" / "datasets"
    raw_dir = root / "data" / "raw" / "football_bi"
    processed_dir = root / "data" / "processed" / "football_bi"
    reports_dir = root / "reports" / "football_bi"
    figures_dir = reports_dir / "figures"
    models_dir = root / "models" / "football_bi"
    logs_dir = root / "logs"
    bi_dir = reports_dir / "bi"
    return ProjectPaths(
        root=root,
        source_datasets_dir=source,
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        reports_dir=reports_dir,
        figures_dir=figures_dir,
        models_dir=models_dir,
        logs_dir=logs_dir,
        bi_dir=bi_dir,
    )


def ensure_project_dirs(paths: ProjectPaths) -> None:
    for directory in [
        paths.raw_dir,
        paths.processed_dir,
        paths.reports_dir,
        paths.figures_dir,
        paths.models_dir,
        paths.logs_dir,
        paths.bi_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True)
