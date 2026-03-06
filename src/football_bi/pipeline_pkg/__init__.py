"""
Football BI Library - Pipeline Module

End-to-end ML pipeline orchestration for football match prediction.
Manages complete workflow from data loading to model evaluation.
"""

from __future__ import annotations

# Import from orchestrator module
from .orchestrator import MLPipeline

__version__ = "3.0"
__all__ = ["MLPipeline"]
