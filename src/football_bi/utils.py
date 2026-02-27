from __future__ import annotations

import logging
from pathlib import Path


def season_code_to_start_year(season_code: str) -> int:
    """Convert season code format like 9394, 0001, 2526 to starting year."""
    code = str(season_code).strip()
    if len(code) != 4 or not code.isdigit():
        raise ValueError(f"Invalid season code: {season_code}")

    first_two = int(code[:2])
    if first_two >= 90:
        return 1900 + first_two
    return 2000 + first_two


def season_code_to_label(season_code: str) -> str:
    start_year = season_code_to_start_year(season_code)
    end_year = start_year + 1
    return f"{start_year}/{str(end_year)[-2:]}"


def get_logger(name: str, log_file: Path | None = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger
