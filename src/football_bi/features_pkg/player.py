"""
Player-level squad feature engineering module.

This module aggregates player statistics to create squad-level features:
- Squad demographics (average age, squad size)
- Squad market value
- Squad composition by position
- Injury metrics
- Squad balance ratios
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import numpy as np

# Default configurations for player features
DEFAULT_PLAYER_FEATURES = {
    "squad_avg_age": "Average age of squad players",
    "squad_median_age": "Median age of squad players",
    "squad_market_value_sum": "Total transfer market value (million EUR)",
    "squad_market_value_avg": "Average market value per player",
    "squad_size": "Total number of players",
    "num_goalkeepers": "Number of goalkeepers",
    "num_defenders": "Number of defensive players",
    "num_midfielders": "Number of midfield players",
    "num_forwards": "Number of forward players",
    "injury_count": "Number of injured/suspended players",
    "injury_rate": "Percentage of squad injured (%)",
    "def_mid_ratio": "Defenders/Midfielders ratio",
    "mid_fwd_ratio": "Midfielders/Forwards ratio",
}


def load_player_profiles(filepath: str | None = None) -> pd.DataFrame:
    """
    Load player profiles CSV file.

    Expected columns: team, player_name, age, position, market_value, ...

    Parameters
    ----------
    filepath : str, optional
        Path to player profiles CSV. If None, uses default data path.

    Returns
    -------
    pd.DataFrame
        Player profiles with columns: team, age, position, market_value
    """
    if filepath is None:
        # Try common locations
        possible_paths = [
            "data/raw/football_bi/player_profiles.csv",
            "data/processed/football_bi/player_profiles.csv",
        ]
        for path in possible_paths:
            try:
                return pd.read_csv(path)
            except FileNotFoundError:
                continue
        raise FileNotFoundError("player_profiles.csv not found in expected locations")

    return pd.read_csv(filepath)


def load_team_features(filepath: str | None = None) -> pd.DataFrame:
    """
    Load team features CSV file.

    Expected columns: team, season, squad_size, injured_players, ...

    Parameters
    ----------
    filepath : str, optional
        Path to team features CSV. If None, uses default data path.

    Returns
    -------
    pd.DataFrame
        Team features with squad composition and injury information
    """
    if filepath is None:
        possible_paths = [
            "data/raw/football_bi/ml_team_features.csv",
            "data/processed/football_bi/ml_team_features.csv",
        ]
        for path in possible_paths:
            try:
                return pd.read_csv(path)
            except FileNotFoundError:
                continue
        raise FileNotFoundError("ml_team_features.csv not found in expected locations")

    return pd.read_csv(filepath)


def compute_squad_aggregations(
    player_profiles: pd.DataFrame,
    team_name: str,
    match_date: pd.Timestamp | None = None,
) -> dict[str, float]:
    """
    Compute squad-level aggregations for a specific team.

    Parameters
    ----------
    player_profiles : pd.DataFrame
        Player profiles with columns: team, age, position, market_value
    team_name : str
        Team identifier to aggregate
    match_date : pd.Timestamp, optional
        Match date for temporal filtering (not yet implemented)

    Returns
    -------
    dict[str, float]
        Squad aggregation features:
        - squad_avg_age, squad_median_age
        - squad_market_value_sum, squad_market_value_avg
        - squad_size
        - num_goalkeepers, num_defenders, num_midfielders, num_forwards
        - def_mid_ratio, mid_fwd_ratio
    """

    # Filter players for this team
    team_players = player_profiles[player_profiles['team'].str.lower() == team_name.lower()]

    if len(team_players) == 0:
        # Return NaN-filled dictionary for missing teams
        return {
            'squad_avg_age': np.nan,
            'squad_median_age': np.nan,
            'squad_market_value_sum': np.nan,
            'squad_market_value_avg': np.nan,
            'squad_size': 0,
            'num_goalkeepers': 0,
            'num_defenders': 0,
            'num_midfielders': 0,
            'num_forwards': 0,
            'def_mid_ratio': np.nan,
            'mid_fwd_ratio': np.nan,
        }

    # Age statistics
    result = {
        'squad_avg_age': float(team_players['age'].mean()) if 'age' in team_players.columns else np.nan,
        'squad_median_age': float(team_players['age'].median()) if 'age' in team_players.columns else np.nan,
    }

    # Market value statistics
    if 'market_value' in team_players.columns:
        market_values = team_players['market_value'].fillna(0)
        result['squad_market_value_sum'] = float(market_values.sum())
        result['squad_market_value_avg'] = float(market_values.mean())
    else:
        result['squad_market_value_sum'] = np.nan
        result['squad_market_value_avg'] = np.nan

    # Squad size
    result['squad_size'] = float(len(team_players))

    # Position counts
    if 'position' in team_players.columns:
        positions = team_players['position'].str.upper()

        # Count players by position group
        gk_count = (positions == 'GK').sum()
        def_count = positions.isin(['CB', 'LB', 'RB', 'LWB', 'RWB']).sum()
        mid_count = positions.isin(['CM', 'CDM', 'CAM', 'LM', 'RM']).sum()
        fwd_count = positions.isin(['ST', 'CF', 'LW', 'RW']).sum()

        result['num_goalkeepers'] = float(gk_count)
        result['num_defenders'] = float(def_count)
        result['num_midfielders'] = float(mid_count)
        result['num_forwards'] = float(fwd_count)

        # Compute ratios (avoid division by zero)
        result['def_mid_ratio'] = float(def_count / mid_count) if mid_count > 0 else np.nan
        result['mid_fwd_ratio'] = float(mid_count / fwd_count) if fwd_count > 0 else np.nan
    else:
        result['num_goalkeepers'] = np.nan
        result['num_defenders'] = np.nan
        result['num_midfielders'] = np.nan
        result['num_forwards'] = np.nan
        result['def_mid_ratio'] = np.nan
        result['mid_fwd_ratio'] = np.nan

    return result


def add_player_features_to_matches(
    matches_df: pd.DataFrame,
    player_profiles: pd.DataFrame,
    team_features_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Add player-level features to matches dataframe.

    Computes squad aggregations for home and away teams and merges with match data.

    Parameters
    ----------
    matches_df : pd.DataFrame
        Match data with columns: home_team, away_team, match_date (required)
    player_profiles : pd.DataFrame
        Player profiles with columns: team, age, position, market_value
    team_features_df : pd.DataFrame, optional
        Additional team features (injuries, squad size) for temporal snapshots

    Returns
    -------
    pd.DataFrame
        Original matches_df with additional player feature columns
    """

    # Get unique teams
    all_teams = pd.concat([matches_df['home_team'], matches_df['away_team']]).unique()

    # Precompute aggregations for all teams (optimization)
    team_aggregations = {}
    for team in all_teams:
        team_aggregations[team] = compute_squad_aggregations(player_profiles, team)

    # Create feature columns for home team
    df_copy = matches_df.copy()

    home_features = df_copy['home_team'].map(
        lambda team: team_aggregations.get(team, {})
    )
    home_df = pd.DataFrame(home_features.tolist(), index=df_copy.index)
    home_df.columns = [f'home_{col}' for col in home_df.columns]

    # Create feature columns for away team
    away_features = df_copy['away_team'].map(
        lambda team: team_aggregations.get(team, {})
    )
    away_df = pd.DataFrame(away_features.tolist(), index=df_copy.index)
    away_df.columns = [f'away_{col}' for col in away_df.columns]

    # Merge with match data
    df_result = pd.concat([df_copy, home_df, away_df], axis=1)

    return df_result


def get_player_feature_names() -> list[str]:
    """
    Get list of player feature names.

    Returns
    -------
    list[str]
        All player feature names (including home_ and away_ prefixes)
    """

    base_features = list(DEFAULT_PLAYER_FEATURES.keys())
    home_features = [f'home_{f}' for f in base_features]
    away_features = [f'away_{f}' for f in base_features]

    return home_features + away_features


def validate_player_features(df: pd.DataFrame, raise_on_error: bool = False) -> dict[str, any]:
    """
    Validate player features for data quality.

    Checks for missing values, NaN counts, and outliers.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe with player features
    raise_on_error : bool
        If True, raise exception on errors. If False, collect and return issues.

    Returns
    -------
    dict[str, any]
        Validation results: {'valid': bool, 'issues': list, 'nan_counts': dict}
    """

    player_features = get_player_feature_names()

    # Check for missing columns
    missing_cols = [col for col in player_features if col not in df.columns]

    # Count NaN values
    nan_counts = {col: df[col].isna().sum() for col in player_features if col in df.columns}

    # Detect outliers (optional)
    issues = []
    if missing_cols:
        issues.append(f"Missing player feature columns: {missing_cols}")

    # NaN thresholds (warn if > 10% NaN)
    for col, nan_count in nan_counts.items():
        nan_pct = (nan_count / len(df)) * 100
        if nan_pct > 10:
            issues.append(f"Column {col}: {nan_pct:.1f}% NaN values")

    valid = len(issues) == 0

    if not valid and raise_on_error:
        raise ValueError(f"Player feature validation failed: {issues}")

    return {
        'valid': valid,
        'issues': issues,
        'nan_counts': nan_counts,
    }


# Export public API
__all__ = [
    'load_player_profiles',
    'load_team_features',
    'compute_squad_aggregations',
    'add_player_features_to_matches',
    'get_player_feature_names',
    'validate_player_features',
    'DEFAULT_PLAYER_FEATURES',
]
