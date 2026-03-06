"""
Ensemble methods module for combining multiple models.

Implements:
- Stacking ensemble with meta-learner
- Voting ensemble with weighted averaging
"""

from __future__ import annotations

from typing import Literal, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_predict
from sklearn.pipeline import Pipeline

from .base import CATEGORICAL_FEATURES, NUMERIC_FEATURES, build_model_pipeline


class StackingEnsemble:
    """
    Stacking ensemble that trains a meta-learner on base model predictions.

    Process:
    1. Train base models on training data (or CV folds)
    2. Generate meta-features from base model predictions
    3. Train meta-learner on meta-features
    4. Final prediction: meta-learner(base_predictions)
    """

    def __init__(
        self,
        base_models: list[str],
        meta_model: str = "logistic_regression",
        random_state: int = 42,
    ):
        """
        Initialize stacking ensemble.

        Parameters
        ----------
        base_models : list[str]
            Names of base models (e.g., ['xgboost', 'lightgbm', 'extra_trees'])
        meta_model : str
            Name of meta-learner model
        random_state : int
            Random seed
        """

        self.base_models = base_models
        self.meta_model_name = meta_model
        self.random_state = random_state

        self.base_estimators = {}
        self.meta_estimator = None
        self.classes = None

    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_valid: pd.DataFrame,
        y_valid: pd.Series,
    ) -> StackingEnsemble:
        """
        Fit stacking ensemble.

        Parameters
        ----------
        X_train : pd.DataFrame
            Training features
        y_train : pd.Series
            Training target
        X_valid : pd.DataFrame
            Validation features (used as meta-features training set)
        y_valid : pd.Series
            Validation target

        Returns
        -------
        StackingEnsemble
            Fitted ensemble
        """

        # Step 1: Train base models on training set
        self.base_estimators = {}
        for model_name in self.base_models:
            pipeline = build_model_pipeline(
                model_name,
                numeric_features=NUMERIC_FEATURES,
                categorical_features=CATEGORICAL_FEATURES,
                random_state=self.random_state,
            )

            pipeline.fit(X_train, y_train)
            self.base_estimators[model_name] = pipeline

        # Store classes
        self.classes = self.base_estimators[self.base_models[0]].named_steps[
            "model"
        ].classes_

        # Step 2: Generate meta-features from validation set
        meta_features_valid = self._generate_meta_features(X_valid, skip_fit=True)

        # Step 3: Train meta-learner
        self.meta_estimator = build_model_pipeline(
            self.meta_model_name,
            numeric_features=list(range(len(self.base_models) * len(self.classes))),
            categorical_features=[],
            random_state=self.random_state,
        )

        # Prepare meta-features for meta-learner
        meta_X = self._expand_meta_features(meta_features_valid)
        self.meta_estimator.fit(
            pd.DataFrame(meta_X, columns=[f"base_{i}" for i in range(meta_X.shape[1])]),
            y_valid,
        )

        return self

    def _generate_meta_features(
        self,
        X: pd.DataFrame,
        skip_fit: bool = False,
    ) -> np.ndarray:
        """
        Generate meta-features from base model predictions.

        Parameters
        ----------
        X : pd.DataFrame
            Input features
        skip_fit : bool
            If True, use already fitted base models

        Returns
        -------
        np.ndarray
            Meta-features (n_samples, n_base_models * n_classes)
        """

        meta_features = []

        for model_name in self.base_models:
            pipeline = self.base_estimators[model_name]
            y_proba = pipeline.predict_proba(X)
            meta_features.append(y_proba)

        # Stack horizontally: (n_samples, n_base_models * n_classes)
        return np.hstack(meta_features)

    def _expand_meta_features(self, meta_features: np.ndarray) -> np.ndarray:
        """
        Expand meta-features to DataFrame format.

        Parameters
        ----------
        meta_features : np.ndarray
            Meta-features from _generate_meta_features

        Returns
        -------
        np.ndarray
            Expanded meta-features
        """

        return meta_features

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict class probabilities.

        Parameters
        ----------
        X : pd.DataFrame
            Features

        Returns
        -------
        np.ndarray
            Class probabilities (n_samples, n_classes)
        """

        meta_features = self._generate_meta_features(X, skip_fit=True)
        meta_X = pd.DataFrame(
            meta_features,
            columns=[f"base_{i}" for i in range(meta_features.shape[1])],
        )

        return self.meta_estimator.predict_proba(meta_X)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict class labels.

        Parameters
        ----------
        X : pd.DataFrame
            Features

        Returns
        -------
        np.ndarray
            Predicted class labels
        """

        proba = self.predict_proba(X)
        return self.classes[np.argmax(proba, axis=1)]


class VotingEnsemble:
    """
    Voting ensemble that averages predictions from multiple models.

    Supports soft voting (probability averaging) and hard voting (majority vote).
    """

    def __init__(
        self,
        models: list[str],
        weights: Optional[list[float]] = None,
        voting: Literal["soft", "hard"] = "soft",
        random_state: int = 42,
    ):
        """
        Initialize voting ensemble.

        Parameters
        ----------
        models : list[str]
            Model names to combine
        weights : list[float], optional
            Weights for each model. If None, equal weights.
            (Higher weight = more importance)
        voting : {'soft', 'hard'}
            'soft': Average class probabilities
            'hard': Majority vote on class prediction
        random_state : int
            Random seed
        """

        self.models = models
        self.weights = weights if weights is not None else [1.0] * len(models)
        self.voting = voting
        self.random_state = random_state

        # Normalize weights
        total_weight = sum(self.weights)
        self.weights = [w / total_weight for w in self.weights]

        self.estimators = {}
        self.classes = None

    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
    ) -> VotingEnsemble:
        """
        Fit all base models.

        Parameters
        ----------
        X_train : pd.DataFrame
            Training features
        y_train : pd.Series
            Training target

        Returns
        -------
        VotingEnsemble
            Fitted ensemble
        """

        self.estimators = {}

        for model_name in self.models:
            pipeline = build_model_pipeline(
                model_name,
                numeric_features=NUMERIC_FEATURES,
                categorical_features=CATEGORICAL_FEATURES,
                random_state=self.random_state,
            )

            pipeline.fit(X_train, y_train)
            self.estimators[model_name] = pipeline

        # Store classes
        self.classes = self.estimators[self.models[0]].named_steps["model"].classes_

        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict class probabilities.

        For soft voting: Average probability predictions
        For hard voting: Not applicable (use predict())

        Parameters
        ----------
        X : pd.DataFrame
            Features

        Returns
        -------
        np.ndarray
            Class probabilities
        """

        if self.voting == "hard":
            raise ValueError("predict_proba not available for hard voting")

        # Collect probability predictions
        all_probas = []
        for model_name in self.models:
            pipeline = self.estimators[model_name]
            proba = pipeline.predict_proba(X)
            all_probas.append(proba)

        # Weighted average
        all_probas = np.array(all_probas)  # (n_models, n_samples, n_classes)
        weights = np.array(self.weights).reshape(-1, 1, 1)  # (n_models, 1, 1)

        weighted_proba = (all_probas * weights).sum(axis=0)  # (n_samples, n_classes)

        # Normalize to sum to 1
        return weighted_proba / weighted_proba.sum(axis=1, keepdims=True)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict class labels.

        For soft voting: Use argmax of averaged probabilities
        For hard voting: Majority vote

        Parameters
        ----------
        X : pd.DataFrame
            Features

        Returns
        -------
        np.ndarray
            Predicted class labels
        """

        if self.voting == "soft":
            proba = self.predict_proba(X)
            return self.classes[np.argmax(proba, axis=1)]

        elif self.voting == "hard":
            # Collect predictions
            all_preds = []
            for model_name in self.models:
                pipeline = self.estimators[model_name]
                pred = pipeline.predict(X)
                all_preds.append(pred)

            all_preds = np.array(all_preds)  # (n_models, n_samples)

            # Majority vote with weights
            predictions = np.zeros(all_preds.shape[1], dtype=object)

            for i in range(all_preds.shape[1]):
                vote_counts = {}
                for j, model_name in enumerate(self.models):
                    pred = all_preds[j, i]
                    weight = self.weights[j]

                    if pred not in vote_counts:
                        vote_counts[pred] = 0
                    vote_counts[pred] += weight

                # Select class with highest weighted votes
                predictions[i] = max(vote_counts.items(), key=lambda x: x[1])[0]

            return predictions

        else:
            raise ValueError(f"Unknown voting strategy: {self.voting}")


def create_stacking_ensemble(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_valid: pd.DataFrame,
    y_valid: pd.Series,
    base_models: list[str] = None,
    meta_model: str = "logistic_regression",
    random_state: int = 42,
) -> StackingEnsemble:
    """
    Create and fit a stacking ensemble.

    Parameters
    ----------
    X_train : pd.DataFrame
        Training features
    y_train : pd.Series
        Training target
    X_valid : pd.DataFrame
        Validation features
    y_valid : pd.Series
        Validation target
    base_models : list[str], optional
        Base model names. Default: ['xgboost', 'lightgbm', 'extra_trees', 'catboost']
    meta_model : str
        Meta-learner model name
    random_state : int
        Random seed

    Returns
    -------
    StackingEnsemble
        Fitted stacking ensemble
    """

    if base_models is None:
        base_models = ["xgboost", "lightgbm", "catboost", "extra_trees"]

    ensemble = StackingEnsemble(
        base_models=base_models,
        meta_model=meta_model,
        random_state=random_state,
    )

    ensemble.fit(X_train, y_train, X_valid, y_valid)

    return ensemble


def create_voting_ensemble(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    models: list[str] = None,
    weights: list[float] = None,
    voting: Literal["soft", "hard"] = "soft",
    random_state: int = 42,
) -> VotingEnsemble:
    """
    Create and fit a voting ensemble.

    Parameters
    ----------
    X_train : pd.DataFrame
        Training features
    y_train : pd.Series
        Training target
    models : list[str], optional
        Model names. Default: ['xgboost', 'lightgbm', 'catboost', 'extra_trees']
    weights : list[float], optional
        Model weights. Default: equal weights
    voting : {'soft', 'hard'}
        Voting strategy
    random_state : int
        Random seed

    Returns
    -------
    VotingEnsemble
        Fitted voting ensemble
    """

    if models is None:
        models = ["xgboost", "lightgbm", "catboost", "extra_trees"]

    ensemble = VotingEnsemble(
        models=models,
        weights=weights,
        voting=voting,
        random_state=random_state,
    )

    ensemble.fit(X_train, y_train)

    return ensemble


# Export public API
__all__ = [
    "StackingEnsemble",
    "VotingEnsemble",
    "create_stacking_ensemble",
    "create_voting_ensemble",
]
