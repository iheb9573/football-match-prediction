"""
Base models module for football match prediction.

Includes:
- Baseline models: LogisticRegression, RandomForest, ExtraTreesClassifier
- New models: XGBoost, LightGBM, CatBoost
- Unified model interface and training pipeline
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Try importing gradient boosting libraries (may not be installed)
try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    XGBClassifier = None

try:
    from lightgbm import LGBMClassifier
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False
    LGBMClassifier = None

try:
    from catboost import CatBoostClassifier
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False
    CatBoostClassifier = None


# Feature lists
NUMERIC_FEATURES = [
    "home_elo_pre",
    "away_elo_pre",
    "elo_diff",
    "home_matches_played_pre",
    "away_matches_played_pre",
    "home_points_per_game_pre",
    "away_points_per_game_pre",
    "ppg_diff",
    "home_goal_diff_per_game_pre",
    "away_goal_diff_per_game_pre",
    "goal_diff_pg_diff",
    "home_recent_points_avg_pre",
    "away_recent_points_avg_pre",
    "recent_points_diff",
    "home_recent_goal_diff_avg_pre",
    "away_recent_goal_diff_avg_pre",
    "recent_goal_diff_diff",
    "home_rest_days_pre",
    "away_rest_days_pre",
    "rest_days_diff",
    "month",
    "weekday",
]

CATEGORICAL_FEATURES = ["league_code", "home_team", "away_team"]


@dataclass
class ModelConfig:
    """Configuration for a model."""

    name: str
    model_type: str
    hyperparams: dict
    is_available: bool = True
    description: str = ""


class ModelRegistry:
    """Registry of all available models."""

    _REGISTRY = {}

    @classmethod
    def register(cls, config: ModelConfig):
        """Register a model configuration."""
        cls._REGISTRY[config.name] = config

    @classmethod
    def get(cls, name: str) -> Optional[ModelConfig]:
        """Get a model configuration by name."""
        return cls._REGISTRY.get(name)

    @classmethod
    def list_available(cls) -> list[str]:
        """List all available models."""
        return [name for name, cfg in cls._REGISTRY.items() if cfg.is_available]

    @classmethod
    def list_all(cls) -> list[str]:
        """List all registered models (including unavailable)."""
        return list(cls._REGISTRY.keys())

    @classmethod
    def get_models_by_type(cls, model_type: str) -> list[str]:
        """Get models by type."""
        return [
            name
            for name, cfg in cls._REGISTRY.items()
            if cfg.model_type == model_type and cfg.is_available
        ]


# Register baseline models
ModelRegistry.register(
    ModelConfig(
        name="logistic_regression",
        model_type="baseline",
        hyperparams={
            "max_iter": 3000,
            "class_weight": "balanced",
            "random_state": 42,
        },
        description="Linear model (baseline)",
    )
)

ModelRegistry.register(
    ModelConfig(
        name="random_forest",
        model_type="tree_ensemble",
        hyperparams={
            "n_estimators": 350,
            "max_depth": 18,
            "min_samples_leaf": 2,
            "class_weight": "balanced_subsample",
            "n_jobs": -1,
            "random_state": 42,
        },
        description="Random Forest classifier",
    )
)

ModelRegistry.register(
    ModelConfig(
        name="extra_trees",
        model_type="tree_ensemble",
        hyperparams={
            "n_estimators": 500,
            "max_depth": 20,
            "min_samples_leaf": 2,
            "class_weight": "balanced_subsample",
            "n_jobs": -1,
            "random_state": 42,
        },
        description="Extra Trees classifier (current best baseline)",
    )
)

# Register gradient boosting models (if available)
if HAS_XGBOOST:
    ModelRegistry.register(
        ModelConfig(
            name="xgboost",
            model_type="gradient_boosting",
            hyperparams={
                "n_estimators": 200,
                "max_depth": 7,
                "learning_rate": 0.05,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "scale_pos_weight": 1,
                "random_state": 42,
                "n_jobs": -1,
                "objective": "multi:softprob",
                "num_class": 3,
            },
            is_available=True,
            description="XGBoost classifier (NEW)",
        )
    )
else:
    ModelRegistry.register(
        ModelConfig(
            name="xgboost",
            model_type="gradient_boosting",
            hyperparams={},
            is_available=False,
            description="XGBoost classifier (not installed)",
        )
    )

if HAS_LIGHTGBM:
    ModelRegistry.register(
        ModelConfig(
            name="lightgbm",
            model_type="gradient_boosting",
            hyperparams={
                "n_estimators": 200,
                "max_depth": 10,
                "num_leaves": 31,
                "learning_rate": 0.05,
                "min_child_samples": 10,
                "feature_fraction": 0.8,
                "bagging_fraction": 0.8,
                "random_state": 42,
                "n_jobs": -1,
                "class_weight": "balanced",
            },
            is_available=True,
            description="LightGBM classifier (NEW)",
        )
    )
else:
    ModelRegistry.register(
        ModelConfig(
            name="lightgbm",
            model_type="gradient_boosting",
            hyperparams={},
            is_available=False,
            description="LightGBM classifier (not installed)",
        )
    )

if HAS_CATBOOST:
    ModelRegistry.register(
        ModelConfig(
            name="catboost",
            model_type="gradient_boosting",
            hyperparams={
                "depth": 8,
                "iterations": 200,
                "learning_rate": 0.05,
                "l2_leaf_reg": 5,
                "verbose": 0,
                "random_state": 42,
            },
            is_available=True,
            description="CatBoost classifier (NEW)",
        )
    )
else:
    ModelRegistry.register(
        ModelConfig(
            name="catboost",
            model_type="gradient_boosting",
            hyperparams={},
            is_available=False,
            description="CatBoost classifier (not installed)",
        )
    )


def _build_preprocessor(
    numeric_features: list[str] = NUMERIC_FEATURES,
    categorical_features: list[str] = CATEGORICAL_FEATURES,
) -> ColumnTransformer:
    """
    Build preprocessing pipeline for features.

    Parameters
    ----------
    numeric_features : list[str]
        Numeric feature names
    categorical_features : list[str]
        Categorical feature names

    Returns
    -------
    ColumnTransformer
        Preprocessing pipeline
    """
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ],
        remainder="drop",
    )


def instantiate_model(
    model_name: str,
    random_state: int = 42,
    custom_params: Optional[dict] = None,
) -> object:
    """
    Instantiate a model by name.

    Parameters
    ----------
    model_name : str
        Model name (from registry)
    random_state : int
        Random state seed
    custom_params : dict, optional
        Override default hyperparameters

    Returns
    -------
    object
        Instantiated model

    Raises
    ------
    ValueError
        If model not found or not available
    """

    config = ModelRegistry.get(model_name)

    if config is None:
        raise ValueError(
            f"Model '{model_name}' not found. Available: {ModelRegistry.list_all()}"
        )

    if not config.is_available:
        raise ValueError(
            f"Model '{model_name}' is not available. Please install required dependencies."
        )

    # Get hyperparameters
    params = config.hyperparams.copy()
    if custom_params:
        params.update(custom_params)

    # Ensure random_state is set
    if "random_state" not in params:
        params["random_state"] = random_state

    # Instantiate appropriate model
    if model_name == "logistic_regression":
        return LogisticRegression(**params)

    elif model_name == "random_forest":
        return RandomForestClassifier(**params)

    elif model_name == "extra_trees":
        return ExtraTreesClassifier(**params)

    elif model_name == "xgboost":
        if not HAS_XGBOOST:
            raise ImportError("XGBoost not installed. Install with: pip install xgboost")
        return XGBClassifier(**params)

    elif model_name == "lightgbm":
        if not HAS_LIGHTGBM:
            raise ImportError("LightGBM not installed. Install with: pip install lightgbm")
        return LGBMClassifier(**params)

    elif model_name == "catboost":
        if not HAS_CATBOOST:
            raise ImportError("CatBoost not installed. Install with: pip install catboost")
        return CatBoostClassifier(**params)

    else:
        raise ValueError(f"Unknown model: {model_name}")


def build_model_pipeline(
    model_name: str,
    numeric_features: list[str] = NUMERIC_FEATURES,
    categorical_features: list[str] = CATEGORICAL_FEATURES,
    random_state: int = 42,
    custom_params: Optional[dict] = None,
) -> Pipeline:
    """
    Build a complete pipeline with preprocessing and model.

    Parameters
    ----------
    model_name : str
        Model name
    numeric_features : list[str]
        Numeric feature names
    categorical_features : list[str]
        Categorical feature names
    random_state : int
        Random state
    custom_params : dict, optional
        Override hyperparameters

    Returns
    -------
    Pipeline
        sklearn Pipeline with preprocessor and model
    """

    preprocessor = _build_preprocessor(numeric_features, categorical_features)
    model = instantiate_model(model_name, random_state, custom_params)

    return Pipeline([("preprocessor", preprocessor), ("model", model)])


def check_model_availability() -> dict[str, bool]:
    """
    Check which models are available (dependencies installed).

    Returns
    -------
    dict[str, bool]
        Model name -> availability mapping
    """

    return {
        "logistic_regression": True,
        "random_forest": True,
        "extra_trees": True,
        "xgboost": HAS_XGBOOST,
        "lightgbm": HAS_LIGHTGBM,
        "catboost": HAS_CATBOOST,
    }


def get_model_suggestions() -> dict[str, str]:
    """
    Get installation suggestions for unavailable models.

    Returns
    -------
    dict[str, str]
        Model name -> installation command
    """

    suggestions = {}

    if not HAS_XGBOOST:
        suggestions["xgboost"] = "pip install xgboost"

    if not HAS_LIGHTGBM:
        suggestions["lightgbm"] = "pip install lightgbm"

    if not HAS_CATBOOST:
        suggestions["catboost"] = "pip install catboost"

    return suggestions


# Export public API
__all__ = [
    "ModelRegistry",
    "ModelConfig",
    "NUMERIC_FEATURES",
    "CATEGORICAL_FEATURES",
    "instantiate_model",
    "build_model_pipeline",
    "check_model_availability",
    "get_model_suggestions",
]
