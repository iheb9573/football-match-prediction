"""
Feature scaling and normalization module.

Provides multiple scaling strategies for numeric features.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Literal, Optional
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler


class ScalingProcessor:
    """
    Handle feature scaling with multiple strategy options.
    """

    def __init__(self, strategy: Literal['standard', 'robust', 'minmax'] = 'standard'):
        """
        Initialize scaling processor.

        Parameters
        ----------
        strategy : {'standard', 'robust', 'minmax'}
            - 'standard': Zero mean, unit variance (sensitive to outliers)
            - 'robust': IQR-based, resistant to outliers
            - 'minmax': Scales to [0, 1] range
        """
        self.strategy = strategy

        if strategy == 'standard':
            self.scaler = StandardScaler()
        elif strategy == 'robust':
            self.scaler = RobustScaler()
        elif strategy == 'minmax':
            self.scaler = MinMaxScaler()
        else:
            raise ValueError(f"Unknown scaling strategy: {strategy}")

    def fit(self, X: pd.DataFrame | np.ndarray, features: Optional[list[str]] = None):
        """
        Fit scaler on training data.

        Parameters
        ----------
        X : pd.DataFrame or np.ndarray
            Training data
        features : list[str], optional
            Columns to scale. If None, scale all numeric columns.
        """
        if isinstance(X, pd.DataFrame):
            if features is None:
                features = X.select_dtypes(include=[np.number]).columns.tolist()
            X_numeric = X[features]
        else:
            X_numeric = X

        self.scaler.fit(X_numeric)
        self.features = features

    def transform(self, X: pd.DataFrame | np.ndarray) -> pd.DataFrame | np.ndarray:
        """
        Apply scaling transformation.

        Parameters
        ----------
        X : pd.DataFrame or np.ndarray
            Data to scale

        Returns
        -------
        pd.DataFrame or np.ndarray
            Scaled data
        """
        if isinstance(X, pd.DataFrame):
            X_numeric = X[self.features].copy()
            X_scaled = self.scaler.transform(X_numeric)
            X_result = X.copy()
            X_result[self.features] = X_scaled
            return X_result
        else:
            return self.scaler.transform(X)

    def fit_transform(
        self,
        X: pd.DataFrame | np.ndarray,
        features: Optional[list[str]] = None,
    ) -> pd.DataFrame | np.ndarray:
        """Fit and transform in one step."""
        self.fit(X, features)
        return self.transform(X)

    def inverse_transform(self, X_scaled: pd.DataFrame | np.ndarray) -> pd.DataFrame | np.ndarray:
        """
        Reverse the scaling transformation.

        Parameters
        ----------
        X_scaled : pd.DataFrame or np.ndarray
            Scaled data

        Returns
        -------
        pd.DataFrame or np.ndarray
            Original scale data
        """
        if isinstance(X_scaled, pd.DataFrame):
            X_numeric = X_scaled[self.features]
            X_unscaled = self.scaler.inverse_transform(X_numeric)
            X_result = X_scaled.copy()
            X_result[self.features] = X_unscaled
            return X_result
        else:
            return self.scaler.inverse_transform(X_scaled)


def scale_features(
    df: pd.DataFrame,
    strategy: Literal['standard', 'robust', 'minmax'] = 'standard',
    features: Optional[list[str]] = None,
    fit_df: Optional[pd.DataFrame] = None,
) -> tuple[pd.DataFrame, ScalingProcessor]:
    """
    Scale numeric features in dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        Data to scale
    strategy : {'standard', 'robust', 'minmax'}
        Scaling strategy
    features : list[str], optional
        Features to scale. If None, scale all numeric columns.
    fit_df : pd.DataFrame, optional
        Data to fit scaler on (e.g., training set). If None, fit on df.

    Returns
    -------
    tuple[pd.DataFrame, ScalingProcessor]
        - Scaled dataframe
        - Fitted scaler for future use
    """

    processor = ScalingProcessor(strategy=strategy)

    if fit_df is None:
        fit_df = df

    processor.fit(fit_df, features)
    df_scaled = processor.transform(df)

    return df_scaled, processor


def get_scaling_stats(
    df: pd.DataFrame,
    features: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    Get scaling statistics for numeric features.

    Parameters
    ----------
    df : pd.DataFrame
        Data to analyze
    features : list[str], optional
        Features to analyze. If None, analyze all numeric columns.

    Returns
    -------
    pd.DataFrame
        Statistics including mean, std, min, max, median
    """

    if features is None:
        features = df.select_dtypes(include=[np.number]).columns.tolist()

    stats = {
        'feature': [],
        'count': [],
        'mean': [],
        'std': [],
        'min': [],
        'q25': [],
        'median': [],
        'q75': [],
        'max': [],
        'range': [],
    }

    for feature in features:
        if feature in df.columns:
            col = df[feature]
            stats['feature'].append(feature)
            stats['count'].append(col.count())
            stats['mean'].append(col.mean())
            stats['std'].append(col.std())
            stats['min'].append(col.min())
            stats['q25'].append(col.quantile(0.25))
            stats['median'].append(col.median())
            stats['q75'].append(col.quantile(0.75))
            stats['max'].append(col.max())
            stats['range'].append(col.max() - col.min())

    return pd.DataFrame(stats)


def identify_skewed_features(
    df: pd.DataFrame,
    features: Optional[list[str]] = None,
    skew_threshold: float = 1.0,
) -> list[str]:
    """
    Identify highly skewed features (may benefit from log transform).

    Parameters
    ----------
    df : pd.DataFrame
        Data to analyze
    features : list[str], optional
        Features to analyze
    skew_threshold : float
        Absolute skewness threshold above which feature is considered skewed

    Returns
    -------
    list[str]
        Features with skewness above threshold
    """

    if features is None:
        features = df.select_dtypes(include=[np.number]).columns.tolist()

    skewed = []

    for feature in features:
        if feature in df.columns:
            col = df[feature].dropna()
            if len(col) > 0:
                skewness = col.skew()
                if abs(skewness) > skew_threshold:
                    skewed.append(feature)

    return skewed


# Export public API
__all__ = [
    'ScalingProcessor',
    'scale_features',
    'get_scaling_stats',
    'identify_skewed_features',
]
