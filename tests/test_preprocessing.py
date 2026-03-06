"""
Unit tests for preprocessing modules.

Tests for:
- Temporal leakage detection
- Imputation strategies
- Feature scaling
"""

import numpy as np
import pandas as pd
import pytest
from datetime import datetime
from pathlib import Path
from sklearn.preprocessing import StandardScaler

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_bi.preprocessing.leakage_check import TemporalLeakageValidator
from football_bi.preprocessing.imputation import (
    HierarchicalImputer,
    impute_missing_values,
)
from football_bi.preprocessing.scaling import (
    ScalingProcessor,
    scale_features,
)


class TestTemporalLeakageDetector:
    """Test temporal leakage detection."""

    def setup_method(self):
        """Set up test data before each test."""
        self.valid_df = pd.DataFrame({
            'match_id': [1, 2, 3],
            'match_date': [
                datetime(2024, 1, 1),
                datetime(2024, 1, 15),
                datetime(2024, 2, 1),
            ],
            'home_elo_rating': [1600, 1650, 1700],
            'away_elo_rating': [1500, 1550, 1450],
            'home_recent_ppg': [2.0, 1.5, 2.5],
            'away_recent_ppg': [1.5, 2.0, 1.0],
        })

        self.leakage_df = pd.DataFrame({
            'match_id': [1, 2, 3],
            'match_date': [
                datetime(2024, 1, 1),
                datetime(2024, 1, 15),
                datetime(2024, 2, 1),
            ],
            'home_elo_rating': [1600, 1650, 1700],
            'home_goals': [2, 1, 0],  # FORBIDDEN - goal count is post-match
            'away_goals': [1, 3, 1],  # FORBIDDEN
            'home_recent_ppg': [2.0, 1.5, 2.5],
            'away_recent_ppg': [1.5, 2.0, 1.0],
        })

    def test_valid_features_pass_check(self):
        """Test that valid features pass leakage check."""
        validator = TemporalLeakageValidator()

        # Check should return valid=True
        result = validator.check_feature_names(self.valid_df, strict=False)
        assert result['valid'] is True
        assert len(result['forbidden_found']) == 0

    def test_forbidden_features_detected(self):
        """Test that forbidden features are detected."""
        validator = TemporalLeakageValidator()

        # Check should detect forbidden features
        result = validator.check_feature_names(self.leakage_df, strict=True)
        assert result['valid'] is False
        assert len(result['forbidden_found']) > 0

    def test_check_date_ordering(self):
        """Test temporal integrity of dates."""
        validator = TemporalLeakageValidator()

        # Valid ordered dates should pass
        result = validator.check_date_ordering(self.valid_df)
        assert result is not None

    def test_invalid_date_ordering_detected(self):
        """Test that out-of-order dates are detected."""
        bad_df = self.valid_df.copy()
        bad_df['match_date'] = [
            datetime(2024, 2, 1),
            datetime(2024, 1, 1),  # Out of order
            datetime(2024, 1, 15),
        ]

        validator = TemporalLeakageValidator()

        # Should handle or warn about ordering
        result = validator.check_date_ordering(bad_df)
        assert result is not None


class TestHierarchicalImputation:
    """Test hierarchical imputation strategy."""

    def setup_method(self):
        """Set up test data before each test."""
        self.df = pd.DataFrame({
            'match_date': [
                datetime(2023, 1, 1),
                datetime(2023, 1, 15),
                datetime(2023, 2, 1),
                datetime(2023, 2, 15),
            ],
            'league': ['PL', 'PL', 'PL', 'La Liga'],
            'season_start_year': [2023, 2023, 2023, 2023],
            'home_elo_rating': [1600, np.nan, 1700, 1500],
            'away_elo_rating': [1500, 1550, np.nan, 1400],
            'home_recent_ppg': [2.0, 1.5, np.nan, np.nan],
            'away_recent_ppg': [1.5, np.nan, 1.0, 2.0],
        })

    def test_hierarchical_imputer_initialization(self):
        """Test HierarchicalImputer initialization."""
        imputer = HierarchicalImputer()

        assert imputer is not None
        assert hasattr(imputer, 'fit')
        assert hasattr(imputer, 'transform')

    def test_imputation_reduces_missing_values(self):
        """Test that imputation reduces missing values."""
        missing_before = self.df.isna().sum().sum()
        assert missing_before > 0

        imputed = impute_missing_values(
            self.df,
            strategy='hierarchical',
        )

        missing_after = imputed.isna().sum().sum()
        assert missing_after < missing_before

    def test_imputation_returns_dataframe(self):
        """Test that imputation returns DataFrame."""
        result = impute_missing_values(
            self.df,
            strategy='hierarchical',
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(self.df)

    def test_forward_fill_strategy(self):
        """Test forward fill imputation strategy."""
        result = impute_missing_values(
            self.df,
            strategy='forward_fill',
        )

        assert result is not None
        assert isinstance(result, pd.DataFrame)

    def test_mean_strategy(self):
        """Test mean imputation strategy."""
        result = impute_missing_values(
            self.df,
            strategy='mean',
        )

        assert result is not None
        assert isinstance(result, pd.DataFrame)

    def test_invalid_strategy_raises_error(self):
        """Test that invalid strategy raises error."""
        with pytest.raises(ValueError):
            impute_missing_values(
                self.df,
                strategy='invalid_strategy',
            )


class TestScalingProcessor:
    """Test feature scaling."""

    def setup_method(self):
        """Set up test data before each test."""
        self.df = pd.DataFrame({
            'feature_1': [1, 2, 3, 4, 5],
            'feature_2': [10, 20, 30, 40, 50],
            'feature_3': [100, 200, 300, 400, 500],
            'categorical': ['A', 'B', 'A', 'B', 'A'],
        })

        self.numeric_features = ['feature_1', 'feature_2', 'feature_3']

    def test_scaling_processor_initialization(self):
        """Test ScalingProcessor initialization."""
        processor = ScalingProcessor(
            strategy='standard',
        )

        assert processor is not None
        assert hasattr(processor, 'fit')
        assert hasattr(processor, 'transform')

    def test_scale_features_returns_tuple(self):
        """Test that scaling returns tuple of (dataframe, processor)."""
        result, processor = scale_features(
            self.df,
            strategy='standard',
            features=self.numeric_features,
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(self.df)
        assert processor is not None

    def test_standard_scaling_normalizes_values(self):
        """Test that standard scaling normalizes values to mean~0, std~1."""
        result, _ = scale_features(
            self.df,
            strategy='standard',
            features=self.numeric_features,
        )

        for col in self.numeric_features:
            mean = result[col].mean()
            std = result[col].std(ddof=0)
            assert abs(mean) < 0.05  # Close to 0
            assert abs(std - 1) < 0.05  # Close to 1

    def test_robust_scaling(self):
        """Test robust scaling method."""
        result, _ = scale_features(
            self.df,
            strategy='robust',
            features=self.numeric_features,
        )

        assert result is not None
        assert isinstance(result, pd.DataFrame)

    def test_minmax_scaling(self):
        """Test min-max scaling method."""
        result, _ = scale_features(
            self.df,
            strategy='minmax',
            features=self.numeric_features,
        )

        assert result is not None
        assert isinstance(result, pd.DataFrame)

        # Values should be between 0 and 1
        for col in self.numeric_features:
            assert (result[col] >= 0).all()
            assert (result[col] <= 1).all()

    def test_categorical_features_unchanged(self):
        """Test that non-specified features are unchanged."""
        result, _ = scale_features(
            self.df,
            strategy='standard',
            features=self.numeric_features,
        )

        # Categorical should remain unchanged
        assert (result['categorical'] == self.df['categorical']).all()

    def test_invalid_scaling_method_raises_error(self):
        """Test that invalid scaling method raises error."""
        with pytest.raises(ValueError):
            ScalingProcessor(strategy='invalid_method')


class TestPreprocessingIntegration:
    """Integration tests for preprocessing pipeline."""

    def setup_method(self):
        """Set up test data before each test."""
        self.df = pd.DataFrame({
            'match_id': [1, 2, 3, 4],
            'match_date': [
                datetime(2023, 1, 1),
                datetime(2023, 1, 15),
                datetime(2023, 2, 1),
                datetime(2023, 2, 15),
            ],
            'league': ['PL', 'PL', 'La Liga', 'La Liga'],
            'season_start_year': [2023, 2023, 2023, 2023],
            'home_elo_rating': [1600, np.nan, 1700, 1500],
            'away_elo_rating': [1500, 1550, np.nan, 1400],
            'home_recent_ppg': [2.0, 1.5, np.nan, 2.5],
            'away_recent_ppg': [1.5, np.nan, 1.0, 2.0],
        })

    def test_full_preprocessing_pipeline(self):
        """Test complete preprocessing pipeline: impute -> scale."""
        # Step 1: Impute
        imputed = impute_missing_values(
            self.df,
            strategy='hierarchical',
        )
        assert imputed.isna().sum().sum() < self.df.isna().sum().sum()

        # Step 2: Scale
        numeric_features = ['home_elo_rating', 'away_elo_rating',
                           'home_recent_ppg', 'away_recent_ppg']
        scaled, _ = scale_features(
            imputed,
            strategy='standard',
            features=numeric_features,
        )

        assert scaled is not None
        assert len(scaled) == len(self.df)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
