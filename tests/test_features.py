"""
Unit tests for feature engineering modules.

Tests for:
- Player feature generation
- Advanced feature engineering
- Data leakage validation
"""

import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_bi.features.player import (
    compute_squad_aggregations,
    add_player_features_to_matches,
    validate_player_features,
)

from football_bi.features.advanced import (
    compute_form_interaction,
    compute_elo_form_product,
    assign_match_quarter,
    add_advanced_features_to_matches,
)


class TestPlayerFeatures:
    """Test player feature engineering."""

    def setup_method(self):
        """Set up test data before each test."""
        # Sample player data
        self.player_data = pd.DataFrame({
            'team': ['Arsenal', 'Arsenal', 'Arsenal', 'Liverpool', 'Liverpool'],
            'name': ['Player1', 'Player2', 'Player3', 'Player4', 'Player5'],
            'age': [25, 28, 30, 27, 26],
            'position': ['Defender', 'Midfielder', 'Forward', 'Defender', 'Midfielder'],
            'market_value': [5000000, 8000000, 3000000, 6000000, 7000000],
        })

        # Sample match data
        self.match_data = pd.DataFrame({
            'match_id': [1, 2, 3],
            'match_date': [
                datetime(2024, 1, 1),
                datetime(2024, 1, 15),
                datetime(2024, 2, 1),
            ],
            'home_team': ['Arsenal', 'Arsenal', 'Liverpool'],
            'away_team': ['Liverpool', 'Chelsea', 'Arsenal'],
            'home_goals': [2, 1, 0],
            'away_goals': [1, 3, 1],
            'season_start_year': [2023, 2023, 2023],
        })

    def test_compute_squad_aggregations(self):
        """Test squad aggregation calculation."""
        agg = compute_squad_aggregations(self.player_data, 'Arsenal')

        assert agg is not None
        assert 'squad_avg_age' in agg
        assert 'squad_market_value_sum' in agg
        assert agg['squad_avg_age'] == pytest.approx(27.67, abs=0.1)
        assert agg['squad_market_value_sum'] == 16000000

    def test_compute_squad_aggregations_missing_team(self):
        """Test squad aggregation with team not in data."""
        agg = compute_squad_aggregations(self.player_data, 'NonExistentTeam')

        # Should return defaults for missing team
        assert agg is not None
        assert 'squad_avg_age' in agg

    def test_add_player_features_to_matches(self):
        """Test adding player features to matches."""
        result = add_player_features_to_matches(
            self.match_data,
            self.player_data,
        )

        assert result is not None
        assert 'home_squad_avg_age' in result.columns
        assert 'away_squad_avg_age' in result.columns
        assert len(result) == len(self.match_data)

        # Check that values are numeric
        assert result['home_squad_avg_age'].dtype in [np.float64, np.float32]
        assert result['away_squad_avg_age'].dtype in [np.float64, np.float32]

    def test_validate_player_features(self):
        """Test player features validation."""
        result = add_player_features_to_matches(
            self.match_data,
            self.player_data,
        )

        # Validation should pass without raising
        validation = validate_player_features(result)

        assert validation is not None
        assert len(validation) >= 0  # Returns validation report


class TestAdvancedFeatures:
    """Test advanced feature engineering."""

    def setup_method(self):
        """Set up test data before each test."""
        self.match_data = pd.DataFrame({
            'match_id': [1, 2, 3],
            'match_date': [
                datetime(2023, 8, 1),
                datetime(2023, 8, 15),
                datetime(2023, 8, 28),
            ],
            'home_recent_ppg': [2.0, 1.5, 2.5],
            'away_recent_ppg': [1.5, 2.0, 1.0],
            'home_elo_rating': [1600, 1650, 1700],
            'away_elo_rating': [1500, 1550, 1450],
            'season_start_year': [2023, 2023, 2023],
        })

    def test_compute_form_interaction(self):
        """Test form interaction feature."""
        result = compute_form_interaction(
            self.match_data['home_recent_ppg'].iloc[0],
            self.match_data['away_recent_ppg'].iloc[0],
        )

        expected = 2.0 * 1.5  # Should be product
        assert result == pytest.approx(expected)

    def test_compute_elo_form_product(self):
        """Test Elo and form product."""
        elo_diff = 100
        form_avg = 1.75
        result = compute_elo_form_product(elo_diff, form_avg)

        assert result is not None
        assert isinstance(result, (int, float))

    def test_assign_match_quarter(self):
        """Test match quarter assignment."""
        match_date = datetime(2023, 10, 15)
        season_start = datetime(2023, 8, 1)

        quarter = assign_match_quarter(match_date, season_start)

        assert quarter in [1, 2, 3, 4]
        assert isinstance(quarter, int)

    def test_add_advanced_features_to_matches(self):
        """Test adding advanced features to matches."""
        result = add_advanced_features_to_matches(self.match_data)

        assert result is not None
        # Check for actual feature names from implementation
        assert 'match_quarter' in result.columns
        assert len(result) == len(self.match_data)

        # Check that at least one new feature is numeric
        numeric_cols = [col for col in result.columns
                       if result[col].dtype in [np.float64, np.float32]]
        assert len(numeric_cols) > 0


class TestFeatureLeak:
    """Test that features don't leak future information."""

    def test_no_forbidden_features_in_aggregations(self):
        """Test that squad aggregations don't include forbidden features."""
        # Forbidden features would be things computed AFTER the match
        forbidden = ['home_goals', 'away_goals', 'result', 'match_result']

        player_data = pd.DataFrame({
            'team': ['Arsenal', 'Arsenal'],
            'name': ['Player1', 'Player2'],
            'age': [25, 28],
            'position': ['Defender', 'Midfielder'],
            'market_value': [5000000, 8000000],
        })

        agg = compute_squad_aggregations(player_data, 'Arsenal')

        for key in agg.keys():
            assert key not in forbidden

    def test_match_quarter_uses_season_start(self):
        """Test that match_quarter correctly uses season start date."""
        # Early season match (should be quarter 1)
        early_date = datetime(2023, 8, 15)
        season_start = datetime(2023, 8, 1)

        q1 = assign_match_quarter(early_date, season_start)
        assert q1 == 1

        # Late season match (should be quarter 4)
        late_date = datetime(2024, 5, 15)
        q4 = assign_match_quarter(late_date, season_start)
        assert q4 == 4


class TestFeatureValueRanges:
    """Test that features have reasonable value ranges."""

    def setup_method(self):
        """Set up test data before each test."""
        self.match_data = pd.DataFrame({
            'match_id': [1, 2, 3],
            'match_date': [
                datetime(2023, 8, 1),
                datetime(2023, 8, 15),
                datetime(2023, 8, 28),
            ],
            'home_recent_ppg': [2.0, 1.5, 2.5],
            'away_recent_ppg': [1.5, 2.0, 1.0],
            'home_elo_rating': [1600, 1650, 1700],
            'away_elo_rating': [1500, 1550, 1450],
            'season_start_year': [2023, 2023, 2023],
        })

    def test_form_interaction_reasonable_range(self):
        """Test that form interaction is within reasonable bounds."""
        min_val = compute_form_interaction(0, 0)
        max_val = compute_form_interaction(3, 3)

        assert min_val >= 0
        assert max_val <= 100  # Should be reasonable max

    def test_match_quarter_in_valid_range(self):
        """Test that match quarter is always 1-4."""
        for i in range(1, 366):
            date = datetime(2023, 8, 1) + timedelta(days=i)
            quarter = assign_match_quarter(date, datetime(2023, 8, 1))
            assert 1 <= quarter <= 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
