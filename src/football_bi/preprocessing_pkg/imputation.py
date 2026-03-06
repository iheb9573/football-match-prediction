"""
Advanced imputation strategies for handling missing values.

Provides hierarchical imputation, KNN-based approaches, and temporal forward filling.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Literal, Optional


class HierarchicalImputer:
    """
    Impute missing values using hierarchical strategy.

    For football data, values missing at team/league level:
    1. Impute with (league, season) median
    2. Fall back to league median
    3. Fall back to global median
    """

    def __init__(self):
        self.league_season_stats = {}
        self.league_stats = {}
        self.global_stats = {}

    def fit(
        self,
        df: pd.DataFrame,
        features_to_impute: list[str],
        league_col: str = 'league_code',
        season_col: str = 'season_start_year',
    ):
        """
        Learn imputation values from training data.

        Parameters
        ----------
        df : pd.DataFrame
            Training data
        features_to_impute : list[str]
            Columns to impute
        league_col : str
            League identifier column
        season_col : str
            Season identifier column
        """

        for feature in features_to_impute:
            if feature not in df.columns:
                continue

            # (league, season) level
            self.league_season_stats[feature] = df.groupby(
                [league_col, season_col]
            )[feature].median().to_dict()

            # league level
            self.league_stats[feature] = df.groupby(league_col)[feature].median().to_dict()

            # global level
            self.global_stats[feature] = df[feature].median()

    def transform(
        self,
        df: pd.DataFrame,
        features_to_impute: list[str],
        league_col: str = 'league_code',
        season_col: str = 'season_start_year',
    ) -> pd.DataFrame:
        """
        Apply imputation to dataframe.

        Parameters
        ----------
        df : pd.DataFrame
            Data to impute
        features_to_impute : list[str]
            Columns to impute
        league_col : str
            League column
        season_col : str
            Season column

        Returns
        -------
        pd.DataFrame
            Data with missing values imputed
        """

        df_copy = df.copy()

        for feature in features_to_impute:
            if feature not in df_copy.columns:
                continue

            for idx in df_copy[df_copy[feature].isna()].index:
                league = df_copy.loc[idx, league_col]
                season = df_copy.loc[idx, season_col]

                # Try (league, season) level
                key = (league, season)
                if key in self.league_season_stats.get(feature, {}):
                    df_copy.loc[idx, feature] = self.league_season_stats[feature][key]
                # Fall back to league level
                elif league in self.league_stats.get(feature, {}):
                    df_copy.loc[idx, feature] = self.league_stats[feature][league]
                # Fall back to global
                else:
                    df_copy.loc[idx, feature] = self.global_stats.get(feature, 0)

        return df_copy

    def fit_transform(
        self,
        df: pd.DataFrame,
        features_to_impute: list[str],
        league_col: str = 'league_code',
        season_col: str = 'season_start_year',
    ) -> pd.DataFrame:
        """Fit imputer and apply in one step."""
        self.fit(df, features_to_impute, league_col, season_col)
        return self.transform(df, features_to_impute, league_col, season_col)


class TemporalForwardFiller:
    """
    Fill missing values using temporal forward fill.

    For time series data, forward fill preserves temporal continuity.
    """

    @staticmethod
    def fill_forward(
        df: pd.DataFrame,
        features: list[str],
        group_col: str = 'team',
        date_col: str = 'match_date',
        max_gap: int = 10,
    ) -> pd.DataFrame:
        """
        Forward fill missing values within groups.

        Parameters
        ----------
        df : pd.DataFrame
            Data to fill
        features : list[str]
            Columns to forward fill
        group_col : str
            Column to group by (e.g., team)
        date_col : str
            Date column for ordering
        max_gap : int
            Maximum days to forward fill (prevents stale data)

        Returns
        -------
        pd.DataFrame
            Data with forward fills applied
        """

        df_copy = df.copy()

        if date_col not in df_copy.columns:
            # If no date column, use index-based filling
            for group in df_copy[group_col].unique():
                mask = df_copy[group_col] == group
                for feature in features:
                    if feature in df_copy.columns:
                        df_copy.loc[mask, feature] = df_copy.loc[mask, feature].fillna(method='ffill')
            return df_copy

        # Date-based forward filling
        df_copy[date_col] = pd.to_datetime(df_copy[date_col])

        for group in df_copy[group_col].unique():
            group_mask = df_copy[group_col] == group
            group_df = df_copy[group_mask].copy()

            for feature in features:
                if feature not in group_df.columns:
                    continue

                # Find NaN positions
                nan_mask = group_df[feature].isna()

                for nan_idx in group_df[nan_mask].index:
                    # Find last non-null value
                    before = group_df.loc[:nan_idx, feature].dropna()

                    if len(before) == 0:
                        continue

                    last_value = before.iloc[-1]
                    last_date = group_df.loc[before.index[-1], date_col]
                    current_date = group_df.loc[nan_idx, date_col]

                    # Check gap
                    gap_days = (current_date - last_date).days
                    if gap_days <= max_gap:
                        df_copy.loc[nan_idx, feature] = last_value

        return df_copy


def impute_missing_values(
    df: pd.DataFrame,
    strategy: Literal['hierarchical', 'forward_fill', 'mean'] = 'hierarchical',
    features: Optional[list[str]] = None,
    **kwargs,
) -> pd.DataFrame:
    """
    Impute missing values using specified strategy.

    Parameters
    ----------
    df : pd.DataFrame
        Data with missing values
    strategy : {'hierarchical', 'forward_fill', 'mean'}
        Imputation strategy
    features : list[str], optional
        Features to impute. If None, impute all numeric columns
    **kwargs
        Additional arguments passed to imputer

    Returns
    -------
    pd.DataFrame
        Data with imputations applied
    """

    df_copy = df.copy()

    if features is None:
        features = df_copy.select_dtypes(include=[np.number]).columns.tolist()

    if strategy == 'hierarchical':
        imputer = HierarchicalImputer()
        league_col = kwargs.get('league_col', 'league_code')
        season_col = kwargs.get('season_col', 'season_start_year')

        if league_col in df_copy.columns and season_col in df_copy.columns:
            return imputer.fit_transform(df_copy, features, league_col, season_col)
        else:
            # Fall back to simple median
            return df_copy.fillna(df_copy[features].median())

    elif strategy == 'forward_fill':
        group_col = kwargs.get('group_col', 'team')
        date_col = kwargs.get('date_col', 'match_date')
        max_gap = kwargs.get('max_gap', 10)

        if group_col in df_copy.columns:
            return TemporalForwardFiller.fill_forward(
                df_copy, features, group_col, date_col, max_gap
            )
        else:
            return df_copy.fillna(method='ffill').fillna(df_copy[features].median())

    elif strategy == 'mean':
        return df_copy.fillna(df_copy[features].mean())

    else:
        raise ValueError(f"Unknown strategy: {strategy}")


# Export public API
__all__ = [
    'HierarchicalImputer',
    'TemporalForwardFiller',
    'impute_missing_values',
]
