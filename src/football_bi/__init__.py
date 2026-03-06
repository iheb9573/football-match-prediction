"""Football BI project package."""

from .config import LEAGUES, ProjectPaths, get_default_paths

# No need for alias now - pipeline.py can be imported directly
# since pipeline/ has been renamed to pipeline_pkg/

__all__ = ["LEAGUES", "ProjectPaths", "get_default_paths"]
