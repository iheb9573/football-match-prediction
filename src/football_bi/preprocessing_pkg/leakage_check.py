"""
Data leakage detection and prevention module.

This module provides utilities to validate temporal integrity:
- Ensures all features are computed from data known BEFORE the match
- Detects look-ahead bias
- Prevents using future information in predictions
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Optional


class TemporalLeakageValidator:
    """
    Validates that features don't contain information from after match start.

    Ensures temporal integrity in time series problem.
    """

    # Features that should NOT be used (contain future information)
    FORBIDDEN_FEATURES = {
        'home_goals',
        'away_goals',
        'target_result',
        'match_result',
        'home_win',
        'away_win',
        'is_draw',
        'full_time_result',
        'goals_home_ft',
        'goals_away_ft',
    }

    # Features that might contain leakage if computed incorrectly
    SUSPICIOUS_FEATURES = {
        'home_elo',  # Should be _pre, not updated post-match
        'away_elo',
        'home_ppg',  # Should be _pre, not include current match
        'away_ppg',
        'home_points',  # Should be _pre, not include current match
        'away_points',
        'home_goals_for',  # Should be season-to-date BEFORE match
        'away_goals_for',
    }

    # Allowed suffixes for safe features
    SAFE_SUFFIXES = {
        '_pre',      # Before match
        '_avg',      # Average computed from past matches
        '_sum',      # Sum from past matches
        '_diff',     # Difference of past features
        '_rate',     # Rate/percentage from past data
        '_ratio',    # Ratio from past data
    }

    @staticmethod
    def check_feature_names(df: pd.DataFrame, strict: bool = False) -> dict:
        """
        Check for forbidden and suspicious feature names.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe to validate
        strict : bool
            If True, consider suspicious features as errors

        Returns
        -------
        dict
            Validation results with keys:
            - 'valid': bool
            - 'forbidden_found': list of forbidden features
            - 'suspicious_found': list of suspicious features
            - 'issues': list of detailed issues
        """
        df_columns = set(df.columns)

        # Check for forbidden features
        forbidden_found = df_columns.intersection(TemporalLeakageValidator.FORBIDDEN_FEATURES)

        # Check for suspicious feature names (without safe suffixes)
        suspicious_found = []
        for col in df_columns:
            col_lower = col.lower()
            # Check if it's in suspicious set and doesn't have safe suffix
            for suspicious in TemporalLeakageValidator.SUSPICIOUS_FEATURES:
                if suspicious in col_lower:
                    has_safe_suffix = any(col_lower.endswith(suffix) for suffix in TemporalLeakageValidator.SAFE_SUFFIXES)
                    if not has_safe_suffix:
                        suspicious_found.append(col)
                    break

        issues = []
        if forbidden_found:
            issues.append(f"FORBIDDEN FEATURES FOUND (will cause leakage): {forbidden_found}")

        if suspicious_found and strict:
            issues.append(f"SUSPICIOUS FEATURES (check carefully): {suspicious_found}")

        valid = len(forbidden_found) == 0 and (not strict or len(suspicious_found) == 0)

        return {
            'valid': valid,
            'forbidden_found': list(forbidden_found),
            'suspicious_found': list(suspicious_found),
            'issues': issues,
        }

    @staticmethod
    def check_date_ordering(
        df: pd.DataFrame,
        date_column: str = 'match_date',
        strict: bool = False,
    ) -> dict:
        """
        Check that all feature dates are before match date.

        Parameters
        ----------
        df : pd.DataFrame
            Match data with feature dates
        date_column : str
            Column name for match dates
        strict : bool
            If True, raise error on violations

        Returns
        -------
        dict
            Validation results
        """
        issues = []

        if date_column not in df.columns:
            issues.append(f"Match date column '{date_column}' not found")
            return {'valid': False, 'issues': issues}

        # Identify date-like columns (should end with _date, _datetime, or _ts)
        date_columns = [col for col in df.columns if any(
            col.endswith(suffix) for suffix in ['_date', '_datetime', '_ts']
        ) if col != date_column]

        if not date_columns:
            # No additional date columns to check
            return {'valid': True, 'issues': [], 'checked_columns': []}

        match_dates = pd.to_datetime(df[date_column], errors='coerce')
        violations = []

        for col in date_columns:
            try:
                col_dates = pd.to_datetime(df[col], errors='coerce')

                # Find where feature date > match date (leakage)
                bad_rows = col_dates > match_dates
                if bad_rows.any():
                    violation_count = bad_rows.sum()
                    violations.append({
                        'column': col,
                        'count': violation_count,
                        'percentage': (violation_count / len(df)) * 100,
                    })

            except Exception as e:
                issues.append(f"Error processing column {col}: {str(e)}")

        if violations:
            for v in violations:
                issues.append(
                    f"Column {v['column']}: {v['count']} rows ({v['percentage']:.1f}%) have dates after match"
                )

        valid = len(violations) == 0

        if not valid and strict:
            raise ValueError(f"Temporal leakage detected: {issues}")

        return {
            'valid': valid,
            'violations': violations,
            'issues': issues,
            'checked_columns': date_columns,
        }

    @staticmethod
    def check_nan_patterns(df: pd.DataFrame) -> dict:
        """
        Analyze NaN patterns to detect potential leakage.

        NaN patterns that appear after match date are suspicious.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe to check

        Returns
        -------
        dict
            Summary of NaN patterns
        """
        nan_stats = {
            'column': [],
            'nan_count': [],
            'nan_percentage': [],
            'suspicious': [],
        }

        for col in df.columns:
            nan_count = df[col].isna().sum()
            if nan_count > 0:
                nan_pct = (nan_count / len(df)) * 100

                # Suspicious if high NaN in what should be pre-computed features
                is_suspicious = (
                    nan_pct > 50 and  # More than half missing
                    col.endswith('_pre') or  # Claims to be pre-match
                    col.endswith('_avg')
                )

                nan_stats['column'].append(col)
                nan_stats['nan_count'].append(nan_count)
                nan_stats['nan_percentage'].append(nan_pct)
                nan_stats['suspicious'].append(is_suspicious)

        return {
            'total_columns_checked': len(df.columns),
            'columns_with_nan': len([c for c in nan_stats['column']]),
            'suspicious_columns': [
                nan_stats['column'][i] for i, sus in enumerate(nan_stats['suspicious']) if sus
            ],
            'details': pd.DataFrame(nan_stats) if nan_stats['column'] else pd.DataFrame(),
        }

    @staticmethod
    def validate_all(
        df: pd.DataFrame,
        date_column: str = 'match_date',
        strict: bool = False,
    ) -> dict:
        """
        Run all temporal leakage validation checks.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe to validate
        date_column : str
            Match date column
        strict : bool
            If True, raise errors on violations

        Returns
        -------
        dict
            Comprehensive validation results
        """
        results = {
            'valid': True,
            'checks': {},
            'issues': [],
        }

        # Check 1: Feature names
        feature_check = TemporalLeakageValidator.check_feature_names(df, strict=strict)
        results['checks']['feature_names'] = feature_check
        if not feature_check['valid']:
            results['valid'] = False
            results['issues'].extend(feature_check['issues'])

        # Check 2: Date ordering
        date_check = TemporalLeakageValidator.check_date_ordering(df, date_column, strict=strict)
        results['checks']['date_ordering'] = date_check
        if not date_check['valid']:
            results['valid'] = False
            results['issues'].extend(date_check.get('issues', []))

        # Check 3: NaN patterns
        nan_check = TemporalLeakageValidator.check_nan_patterns(df)
        results['checks']['nan_patterns'] = nan_check
        if nan_check['suspicious_columns']:
            results['issues'].append(
                f"Found {len(nan_check['suspicious_columns'])} suspicious NaN patterns"
            )

        return results


def validate_no_leakage(
    df: pd.DataFrame,
    date_column: str = 'match_date',
    raise_on_error: bool = False,
) -> bool:
    """
    Quick check for obvious temporal leakage.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe to validate
    date_column : str
        Match date column
    raise_on_error : bool
        If True, raise exception on violations

    Returns
    -------
    bool
        True if no leakage detected, False otherwise
    """
    validator = TemporalLeakageValidator()

    # Check for forbidden columns
    feature_check = validator.check_feature_names(df, strict=False)
    if not feature_check['valid']:
        if raise_on_error:
            raise ValueError(f"Temporal leakage detected: {feature_check['issues']}")
        return False

    # Validate date ordering
    date_check = validator.check_date_ordering(df, date_column, strict=False)
    if not date_check['valid']:
        if raise_on_error:
            raise ValueError(f"Temporal leakage in dates: {date_check['issues']}")
        return False

    return True


# Export public API
__all__ = [
    'TemporalLeakageValidator',
    'validate_no_leakage',
]
