from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import ProjectPaths, ensure_project_dirs, get_default_paths
from .eda import generate_eda_outputs
from .explainability import run_explainability
from .features import build_match_features
from .ingestion import ingest_all_matches, save_raw_dataset
from .modeling import TrainingArtifacts, train_models
from .preprocessing import clean_matches
from .simulation import run_champion_simulation
from .utils import get_logger


def _raw_path(paths: ProjectPaths) -> Path:
    return paths.raw_dir / "matches_raw.csv"


def _clean_path(paths: ProjectPaths) -> Path:
    return paths.processed_dir / "matches_clean.csv"


def _features_path(paths: ProjectPaths) -> Path:
    return paths.processed_dir / "match_features.csv"


def run_step_01_ingestion(paths: ProjectPaths | None = None) -> Path:
    paths = paths or get_default_paths()
    ensure_project_dirs(paths)
    logger = get_logger("football_bi.ingestion", paths.logs_dir / "football_bi_pipeline.log")
    logger.info("Step 01 - Ingestion started")
    raw = ingest_all_matches(paths)
    output_path = save_raw_dataset(raw, paths)
    logger.info("Step 01 - Ingestion completed: %s rows saved to %s", len(raw), output_path)
    return output_path


def run_step_02_preprocessing(paths: ProjectPaths | None = None) -> Path:
    paths = paths or get_default_paths()
    ensure_project_dirs(paths)
    logger = get_logger("football_bi.preprocessing", paths.logs_dir / "football_bi_pipeline.log")
    logger.info("Step 02 - Preprocessing started")

    raw_path = _raw_path(paths)
    if not raw_path.exists():
        run_step_01_ingestion(paths)
    raw = pd.read_csv(raw_path)
    clean = clean_matches(raw)

    output_path = _clean_path(paths)
    paths.processed_dir.mkdir(parents=True, exist_ok=True)
    clean.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("Step 02 - Preprocessing completed: %s rows saved to %s", len(clean), output_path)
    return output_path


def run_step_03_feature_engineering(paths: ProjectPaths | None = None) -> Path:
    paths = paths or get_default_paths()
    ensure_project_dirs(paths)
    logger = get_logger("football_bi.features", paths.logs_dir / "football_bi_pipeline.log")
    logger.info("Step 03 - Feature engineering started")

    clean_path = _clean_path(paths)
    if not clean_path.exists():
        run_step_02_preprocessing(paths)
    clean_df = pd.read_csv(clean_path, parse_dates=["match_date"])
    features_df = build_match_features(clean_df)

    output_path = _features_path(paths)
    features_df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("Step 03 - Feature engineering completed: %s rows saved to %s", len(features_df), output_path)
    return output_path


def run_step_04_eda(paths: ProjectPaths | None = None) -> None:
    paths = paths or get_default_paths()
    ensure_project_dirs(paths)
    logger = get_logger("football_bi.eda", paths.logs_dir / "football_bi_pipeline.log")
    logger.info("Step 04 - EDA started")

    clean_path = _clean_path(paths)
    features_path = _features_path(paths)
    if not clean_path.exists():
        run_step_02_preprocessing(paths)
    if not features_path.exists():
        run_step_03_feature_engineering(paths)

    clean_df = pd.read_csv(clean_path, parse_dates=["match_date"])
    features_df = pd.read_csv(features_path, parse_dates=["match_date"])
    generate_eda_outputs(clean_df, features_df, paths)
    logger.info("Step 04 - EDA completed")


def run_step_05_model_training(paths: ProjectPaths | None = None) -> TrainingArtifacts:
    paths = paths or get_default_paths()
    ensure_project_dirs(paths)
    logger = get_logger("football_bi.modeling", paths.logs_dir / "football_bi_pipeline.log")
    logger.info("Step 05 - Model training started")

    features_path = _features_path(paths)
    if not features_path.exists():
        run_step_03_feature_engineering(paths)
    features_df = pd.read_csv(features_path, parse_dates=["match_date"])

    artifacts = train_models(features_df, paths=paths)
    logger.info("Step 05 - Model training completed: selected model = %s", artifacts.selected_model_name)
    return artifacts


def run_step_06_explainability(paths: ProjectPaths | None = None) -> None:
    paths = paths or get_default_paths()
    ensure_project_dirs(paths)
    logger = get_logger("football_bi.explainability", paths.logs_dir / "football_bi_pipeline.log")
    logger.info("Step 06 - Explainability started")

    features_path = _features_path(paths)
    if not features_path.exists():
        run_step_03_feature_engineering(paths)
    features_df = pd.read_csv(features_path, parse_dates=["match_date"])
    run_explainability(features_df, paths)
    logger.info("Step 06 - Explainability completed")


def run_step_07_champion_simulation(paths: ProjectPaths | None = None, n_simulations: int = 1000) -> Path:
    paths = paths or get_default_paths()
    ensure_project_dirs(paths)
    logger = get_logger("football_bi.simulation", paths.logs_dir / "football_bi_pipeline.log")
    logger.info("Step 07 - Champion simulation started")

    clean_path = _clean_path(paths)
    if not clean_path.exists():
        run_step_02_preprocessing(paths)
    clean_df = pd.read_csv(clean_path, parse_dates=["match_date"])
    output_df = run_champion_simulation(clean_df, paths=paths, n_simulations=n_simulations)
    out_path = paths.bi_dir / "champion_probabilities.csv"
    logger.info("Step 07 - Champion simulation completed: %s rows saved to %s", len(output_df), out_path)
    return out_path


def run_full_pipeline(paths: ProjectPaths | None = None, n_simulations: int = 1000) -> None:
    paths = paths or get_default_paths()
    run_step_01_ingestion(paths)
    run_step_02_preprocessing(paths)
    run_step_03_feature_engineering(paths)
    run_step_04_eda(paths)
    run_step_05_model_training(paths)
    run_step_06_explainability(paths)
    run_step_07_champion_simulation(paths, n_simulations=n_simulations)
