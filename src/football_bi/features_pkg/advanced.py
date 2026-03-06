"""
Advanced feature engineering module.

This module creates higher-order features:
- Interaction terms (form × form, ELO × form, injury impact)
- Advanced temporal features (match quarter, season progression)
- Optional polynomial features
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from datetime import datetime


# Feature definitions
DEFAULT_ADVANCED_FEATURES = {
    "home_form_vs_away_form": "Product of home recent points × away recent points",
    "elo_advantage_with_form": "ELO difference × home recent points average",
    "rest_disparity": "Absolute difference in rest days between teams",
    "injury_impact": "Injury rate difference (home - away)",
    "match_quarter": "Season quarter (1-4, early to late season)",
}


def compute_form_interaction(
    home_recent_points: float,
    away_recent_points: float,
) -> float:
    """
    Compute form interaction feature.

    Product of both teams' recent form:
    - Low (0-1): One team in poor form → likely one-sided match
    - Medium (2-4): Mixed form → competitive match
    - High (6-9): Both teams in excellent form → very competitive

    Parameters
    ----------
    home_recent_points : float
        Home team's recent points average (0-3)
    away_recent_points : float
        Away team's recent points average (0-3)

    Returns
    -------
    float
        Form interaction product (0-9)
    """
    if pd.isna(home_recent_points) or pd.isna(away_recent_points):
        return np.nan

    return home_recent_points * away_recent_points


def compute_elo_form_product(
    elo_diff: float,
    home_recent_points: float,
) -> float:
    """
    Compute ELO advantage amplified by form.

    Captures structural strength (ELO) modulated by current form:
    - Negative: ELO advantage diminished by home team's poor form
    - Positive: ELO advantage amplified by home team's good form

    Parameters
    ----------
    elo_diff : float
        ELO difference including home advantage (-300 to +300)
    home_recent_points : float
        Home team's recent points average (0-3)

    Returns
    -------
    float
        ELO-form interaction product
    """
    if pd.isna(elo_diff) or pd.isna(home_recent_points):
        return np.nan

    return elo_diff * home_recent_points


def compute_rest_disparity(
    home_rest_days: float,
    away_rest_days: float,
) -> float:
    """
    Compute rest disparity between teams.

    Captures advantage of better rest:
    - 0: Both teams rested equally
    - Positive: Home team has rest advantage
    - Negative: Away team has rest advantage

    Parameters
    ----------
    home_rest_days : float
        Days since home team's last match (typically 3-10)
    away_rest_days : float
        Days since away team's last match (typically 3-10)

    Returns
    -------
    float
        Absolute rest disparity (0-15+)
    """
    if pd.isna(home_rest_days) or pd.isna(away_rest_days):
        return np.nan

    return abs(home_rest_days - away_rest_days)


def compute_injury_impact(
    home_injury_rate: float,
    away_injury_rate: float,
) -> float:
    """
    Compute injury impact difference.

    Captures advantage/disadvantage from squad fitness:
    - Positive: Home team less impacted by injuries
    - Negative: Away team healthier

    Parameters
    ----------
    home_injury_rate : float
        Home team's injury rate (% of squad, 0-100)
    away_injury_rate : float
        Away team's injury rate (% of squad, 0-100)

    Returns
    -------
    float
        Injury impact difference (percentage points)
    """
    if pd.isna(home_injury_rate) or pd.isna(away_injury_rate):
        return np.nan

    return home_injury_rate - away_injury_rate


def assign_match_quarter(
    match_date: pd.Timestamp | str,
    season_start_date: pd.Timestamp | str | None = None,
) -> int:
    """
    Assign match quarter based on season progression.

    Divides season into 4 quarters:
    - Q1 (1): Aug-Oct - Early season, teams settling
    - Q2 (2): Nov-Jan - Mid-season, established form
    - Q3 (3): Feb-Apr - Title race, increased intensity
    - Q4 (4): Apr-May - Final stretch, high stakes

    Parameters
    ----------
    match_date : pd.Timestamp or str
        Match date (YYYY-MM-DD format)
    season_start_date : pd.Timestamp or str, optional
        Season start date. If None, infers from match_date year

    Returns
    -------
    int
        Quarter (1, 2, 3, or 4)
    """
    if isinstance(match_date, str):
        match_date = pd.to_datetime(match_date)

    # Infer season start (August of current or previous year)
    if season_start_date is None:
        if match_date.month >= 8:
            season_start = pd.Timestamp(f"{match_date.year}-08-01")
        else:
            season_start = pd.Timestamp(f"{match_date.year - 1}-08-01")
    else:
        if isinstance(season_start_date, str):
            season_start = pd.to_datetime(season_start_date)
        else:
            season_start = season_start_date

    # Days into season (0-365)
    days_into_season = (match_date - season_start).days

    # Assign quarter (0-91 days = Q1, 92-182 = Q2, etc.)
    if days_into_season < 92:
        return 1
    elif days_into_season < 184:
        return 2
    elif days_into_season < 275:
        return 3
    else:
        return 4


def compute_days_since_last_match(
    current_date: pd.Timestamp | str,
    last_match_date: pd.Timestamp | str | None,
) -> float:
    """
    Compute days since team's last match.

    Captures rest/fatigue factor:
    - 3 days: Standard rest (weekend to midweek)
    - 1-2: Short rest (fatigue risk, typically road teams)
    - 7+: Long rest (international break, cold effect)

    Parameters
    ----------
    current_date : pd.Timestamp or str
        Current match date
    last_match_date : pd.Timestamp or str or None
        Previous match date (None = season start)

    Returns
    -------
    float
        Days since last match (typically 3-10)
    """
    if pd.isna(last_match_date) or last_match_date is None:
        # Default for season start or missing data
        return 7.0

    if isinstance(current_date, str):
        current_date = pd.to_datetime(current_date)
    if isinstance(last_match_date, str):
        last_match_date = pd.to_datetime(last_match_date)

    days_diff = (current_date - last_match_date).days
    return float(max(days_diff, 1))  # Ensure at least 1 day


def add_advanced_features_to_matches(
    matches_df: pd.DataFrame,
    include_polynomial: bool = False,
) -> pd.DataFrame:
    """
    Add advanced features to matches dataframe.

    Creates interaction terms and temporal features.

    Parameters
    ----------
    matches_df : pd.DataFrame
        Match data with required columns:
        - home_recent_points_avg_pre, away_recent_points_avg_pre
        - elo_diff
        - home_rest_days_pre, away_rest_days_pre
        - home_injury_rate, away_injury_rate (optional)
        - match_date
    include_polynomial : bool
        If True, also compute polynomial features (increase overfitting risk)

    Returns
    -------
    pd.DataFrame
        matches_df with additional advanced feature columns
    """

    df = matches_df.copy()

    # Interaction features
    df['home_form_vs_away_form'] = df.apply(
        lambda row: compute_form_interaction(
            row.get('home_recent_points_avg_pre', np.nan),
            row.get('away_recent_points_avg_pre', np.nan),
        ),
        axis=1
    )

    df['elo_advantage_with_form'] = df.apply(
        lambda row: compute_elo_form_product(
            row.get('elo_diff', np.nan),
            row.get('home_recent_points_avg_pre', np.nan),
        ),
        axis=1
    )

    df['rest_disparity'] = df.apply(
        lambda row: compute_rest_disparity(
            row.get('home_rest_days_pre', np.nan),
            row.get('away_rest_days_pre', np.nan),
        ),
        axis=1
    )

    # Injury impact (if columns exist)
    if 'home_injury_rate' in df.columns and 'away_injury_rate' in df.columns:
        df['injury_impact'] = df.apply(
            lambda row: compute_injury_impact(
                row.get('home_injury_rate', np.nan),
                row.get('away_injury_rate', np.nan),
            ),
            axis=1
        )
    else:
        df['injury_impact'] = np.nan

    # Temporal features
    if 'match_date' in df.columns:
        df['match_quarter'] = df['match_date'].apply(
            lambda d: assign_match_quarter(d)
        )
    else:
        df['match_quarter'] = 2  # Default to Q2

    # Optional polynomial features
    if include_polynomial:
        if 'elo_diff' in df.columns:
            df['elo_diff_squared'] = df['elo_diff'] ** 2

        if 'ppg_diff' in df.columns:
            df['ppg_diff_squared'] = df['ppg_diff'] ** 2

        if 'rest_disparity' in df.columns:
            df['rest_disparity_squared'] = df['rest_disparity'] ** 2

    return df


def get_advanced_feature_names(include_polynomial: bool = False) -> list[str]:
    """
    Get list of advanced feature names.

    Parameters
    ----------
    include_polynomial : bool
        If True, include polynomial feature names

    Returns
    -------
    list[str]
        Feature names
    """
    features = list(DEFAULT_ADVANCED_FEATURES.keys())

    if include_polynomial:
        features.extend([
            'elo_diff_squared',
            'ppg_diff_squared',
            'rest_disparity_squared',
        ])

    return features


def validate_advanced_features(df: pd.DataFrame, raise_on_error: bool = False) -> dict:
    """
    Validate advanced features for data quality.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe with advanced features
    raise_on_error : bool
        If True, raise exception on errors

    Returns
    -------
    dict
        Validation results
    """
    advanced_features = get_advanced_feature_names()

    # Check for missing columns
    missing_cols = [col for col in advanced_features if col not in df.columns]

    # Count NaN values
    nan_counts = {col: df[col].isna().sum() for col in advanced_features if col in df.columns}

    # Validate value ranges
    issues = []

    # Check rest_disparity ranges
    if 'rest_disparity' in df.columns:
        outliers = df[(df['rest_disparity'] < 0) | (df['rest_disparity'] > 20)]
        if len(outliers) > 0:
            issues.append(f"rest_disparity: {len(outliers)} outlier values (should be 0-20)")

    # Check match_quarter
    if 'match_quarter' in df.columns:
        invalid_quarters = df[(df['match_quarter'] < 1) | (df['match_quarter'] > 4)]
        if len(invalid_quarters) > 0:
            issues.append(f"match_quarter: {len(invalid_quarters)} invalid values (should be 1-4)")

    if missing_cols and raise_on_error:
        issues.append(f"Missing columns: {missing_cols}")

    valid = len(issues) == 0

    if not valid and raise_on_error:
        raise ValueError(f"Advanced feature validation failed: {issues}")

    return {
        'valid': valid,
        'issues': issues,
        'nan_counts': nan_counts,
    }


# Export public API
__all__ = [
    'compute_form_interaction',
    'compute_elo_form_product',
    'compute_rest_disparity',
    'compute_injury_impact',
    'assign_match_quarter',
    'compute_days_since_last_match',
    'add_advanced_features_to_matches',
    'get_advanced_feature_names',
    'validate_advanced_features',
    'DEFAULT_ADVANCED_FEATURES',
]
