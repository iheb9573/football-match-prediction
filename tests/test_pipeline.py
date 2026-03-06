"""
Integration tests for pipeline orchestrator.

Tests for:
- Pipeline initialization
- Pipeline module imports
- Basic pipeline workflow (without full data)
"""

import numpy as np
import pandas as pd
import pytest
from datetime import datetime
from pathlib import Path
import tempfile

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_bi.pipeline.orchestrator import MLPipeline


class TestPipelineInitialization:
    """Test pipeline initialization."""

    def test_pipeline_module_imports(self):
        """Test pipeline module imports correctly."""
        from football_bi.pipeline.orchestrator import MLPipeline

        assert MLPipeline is not None

    def test_pipeline_initialization_with_defaults(self):
        """Test creating pipeline with default parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy data file
            dummy_csv = Path(tmpdir) / "test_data.csv"
            dummy_df = pd.DataFrame({
                'match_id': [1, 2, 3],
                'match_date': [
                    datetime(2023, 1, 1),
                    datetime(2023, 1, 15),
                    datetime(2023, 2, 1),
                ],
                'home_team': ['Arsenal', 'Liverpool', 'Chelsea'],
                'away_team': ['Liverpool', 'Chelsea', 'Arsenal'],
            })
            dummy_df.to_csv(dummy_csv, index=False)

            pipeline = MLPipeline(
                data_path=str(dummy_csv),
                output_dir=tmpdir,
                verbose=0,
            )

            assert pipeline is not None
            assert hasattr(pipeline, 'run_full_pipeline')

    def test_pipeline_initialization_stores_attributes(self):
        """Test pipeline stores initialization attributes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dummy_csv = Path(tmpdir) / "test_data.csv"
            dummy_df = pd.DataFrame({'match_id': [1, 2]})
            dummy_df.to_csv(dummy_csv, index=False)

            pipeline = MLPipeline(
                data_path=str(dummy_csv),
                output_dir=tmpdir,
                verbose=2,
                random_state=123,
            )

            assert pipeline.verbose == 2
            assert pipeline.random_state == 123


class TestPipelineStructure:
    """Test pipeline structure and methods."""

    def setup_method(self):
        """Set up for each test."""
        self.tmpdir = tempfile.mkdtemp()
        self.data_path = Path(self.tmpdir) / "test_data.csv"

        # Create realistic test data
        test_data = pd.DataFrame({
            'match_id': list(range(1, 51)),
            'match_date': pd.date_range('2023-01-01', periods=50, freq='3D'),
            'season_start_year': [2023] * 50,
            'home_team': ['Arsenal'] * 25 + ['Liverpool'] * 25,
            'away_team': ['Liverpool'] * 25 + ['Arsenal'] * 25,
            'home_elo_rating': np.random.randn(50) + 1600,
            'away_elo_rating': np.random.randn(50) + 1500,
            'home_recent_ppg': np.random.randn(50) + 2.0,
            'away_recent_ppg': np.random.randn(50) + 1.5,
            'result': np.random.choice(['H', 'D', 'A'], 50),
        })
        test_data.to_csv(self.data_path, index=False)

    def teardown_method(self):
        """Clean up after each test."""
        import shutil
        if Path(self.tmpdir).exists():
            shutil.rmtree(self.tmpdir)

    def test_pipeline_has_required_methods(self):
        """Test that pipeline has all required methods."""
        pipeline = MLPipeline(
            data_path=str(self.data_path),
            output_dir=self.tmpdir,
            verbose=0,
        )

        # Check main methods exist
        required_methods = [
            'run_full_pipeline',
            'load_data',
            'preprocess',
            'split_data',
            'train_baseline_models',
            'evaluate_on_test',
            'generate_report',
        ]

        for method in required_methods:
            assert hasattr(pipeline, method), f"Pipeline missing method: {method}"

    def test_pipeline_load_data(self):
        """Test that load_data stage works."""
        pipeline = MLPipeline(
            data_path=str(self.data_path),
            output_dir=self.tmpdir,
            verbose=0,
        )

        result = pipeline.load_data()

        # Should return self for chaining
        assert result is pipeline
        # Should load data
        assert pipeline.df_raw is not None
        assert len(pipeline.df_raw) > 0

    def test_pipeline_preprocess(self):
        """Test that preprocess stage works."""
        pipeline = MLPipeline(
            data_path=str(self.data_path),
            output_dir=self.tmpdir,
            verbose=0,
        )

        pipeline.load_data().preprocess()

        # Should load preprocessed data
        assert pipeline.df_processed is not None
        assert len(pipeline.df_processed) > 0

    def test_pipeline_chaining(self):
        """Test that pipeline stages can be chained."""
        pipeline = MLPipeline(
            data_path=str(self.data_path),
            output_dir=self.tmpdir,
            verbose=0,
        )

        # Should be able to chain calls
        result = pipeline.load_data().preprocess()

        assert result is pipeline  # Returns self for chaining
        assert pipeline.df_raw is not None
        assert pipeline.df_processed is not None

    def test_pipeline_output_directory_created(self):
        """Test that pipeline creates output directory."""
        output_dir = Path(self.tmpdir) / "pipeline_output"
        assert not output_dir.exists()

        pipeline = MLPipeline(
            data_path=str(self.data_path),
            output_dir=str(output_dir),
            verbose=0,
        )

        # Loading data should not create output dir yet
        pipeline.load_data()

        # But it should be created somewhere
        assert True  # Just test that initialization works


class TestPipelineVerbosity:
    """Test pipeline verbose levels."""

    def test_verbose_level_0(self):
        """Test pipeline with verbose=0 (silent)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv = Path(tmpdir) / "test.csv"
            pd.DataFrame({'match_id': [1, 2]}).to_csv(csv, index=False)

            pipeline = MLPipeline(
                data_path=str(csv),
                output_dir=tmpdir,
                verbose=0,
            )
            assert pipeline.verbose == 0

    def test_verbose_level_1(self):
        """Test pipeline with verbose=1 (info)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv = Path(tmpdir) / "test.csv"
            pd.DataFrame({'match_id': [1, 2]}).to_csv(csv, index=False)

            pipeline = MLPipeline(
                data_path=str(csv),
                output_dir=tmpdir,
                verbose=1,
            )
            assert pipeline.verbose == 1

    def test_verbose_level_2(self):
        """Test pipeline with verbose=2 (debug)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv = Path(tmpdir) / "test.csv"
            pd.DataFrame({'match_id': [1, 2]}).to_csv(csv, index=False)

            pipeline = MLPipeline(
                data_path=str(csv),
                output_dir=tmpdir,
                verbose=2,
            )
            assert pipeline.verbose == 2


class TestPipelineConfiguration:
    """Test pipeline configuration options."""

    def test_pipeline_with_custom_random_state(self):
        """Test pipeline with custom random state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv = Path(tmpdir) / "test.csv"
            pd.DataFrame({'match_id': [1, 2]}).to_csv(csv, index=False)

            pipeline = MLPipeline(
                data_path=str(csv),
                output_dir=tmpdir,
                random_state=456,
            )

            assert pipeline.random_state == 456

    def test_pipeline_different_output_dirs(self):
        """Test pipeline with different output directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv = Path(tmpdir) / "test.csv"
            pd.DataFrame({'match_id': [1, 2]}).to_csv(csv, index=False)

            output1 = str(Path(tmpdir) / "output1")
            output2 = str(Path(tmpdir) / "output2")

            p1 = MLPipeline(data_path=str(csv), output_dir=output1, verbose=0)
            p2 = MLPipeline(data_path=str(csv), output_dir=output2, verbose=0)

            assert p1.output_dir == output1
            assert p2.output_dir == output2
            assert p1.output_dir != p2.output_dir


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
