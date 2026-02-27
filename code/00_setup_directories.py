from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from football_bi.config import ensure_project_dirs, get_default_paths


def main() -> None:
    paths = get_default_paths()
    ensure_project_dirs(paths)
    print("Project directories are ready.")
    print(f"Raw: {paths.raw_dir}")
    print(f"Processed: {paths.processed_dir}")
    print(f"Reports: {paths.reports_dir}")
    print(f"Models: {paths.models_dir}")


if __name__ == "__main__":
    main()
