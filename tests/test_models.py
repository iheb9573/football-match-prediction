"""
Unit tests for models module.

Tests for:
- Model instantiation and availability
- Baseline model training
- Hyperparameter optimization
- Ensemble methods
"""

import numpy as np
import pandas as pd
import pytest
from datetime import datetime
from pathlib import Path
from sklearn.datasets import make_classification

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_bi.models.base import (
    ModelRegistry,
    instantiate_model,
    build_model_pipeline,
    check_model_availability,
)
from football_bi.models.selection import (
    HyperparameterOptimizer,
)
from football_bi.models.ensembles import (
    StackingEnsemble,
    VotingEnsemble,
    create_stacking_ensemble,
    create_voting_ensemble,
)
from football_bi.models.evaluation import (
    ExperimentEvaluator,
    evaluate_model,
    compare_predictions,
)


class TestModelRegistry:
    """Test model registry and availability."""

    def test_registry_module_imports(self):
        """Test that model registry imports correctly."""
        from football_bi.models.base import ModelRegistry

        assert ModelRegistry is not None

    def test_instantiate_logistic_regression(self):
        """Test creating logistic regression model."""
        model = instantiate_model('logistic_regression')

        assert model is not None
        assert hasattr(model, 'fit')
        assert hasattr(model, 'predict')

    def test_instantiate_random_forest(self):
        """Test creating random forest model."""
        model = instantiate_model('random_forest')

        assert model is not None
        assert hasattr(model, 'fit')

    def test_instantiate_extra_trees(self):
        """Test creating extra trees model."""
        model = instantiate_model('extra_trees')

        assert model is not None
        assert hasattr(model, 'fit')

    def test_model_availability_check_callable(self):
        """Test that model availability check is callable."""
        # Just test that the function exists and is callable
        assert callable(check_model_availability)


class TestModelInstantiation:
    """Test model creation and instantiation."""

    def test_instantiate_models_without_errors(self):
        """Test creating models doesn't raise import errors."""
        for model_name in ['logistic_regression', 'random_forest', 'extra_trees']:
            model = instantiate_model(model_name)
            assert model is not None
            assert hasattr(model, 'fit')
            assert hasattr(model, 'predict')


class TestPipelineBuilder:
    """Test pipeline building with preprocessing."""

    def setup_method(self):
        """Set up test data before each test."""
        # Create DataFrame with mixed types
        self.X_train = pd.DataFrame({
            'numeric_1': np.random.randn(50),
            'numeric_2': np.random.randn(50),
            'numeric_3': np.random.randn(50),
        })
        self.y_train = np.random.choice([0, 1, 2], 50)

    def test_build_model_pipeline(self):
        """Test building complete model pipeline."""
        pipeline = build_model_pipeline(
            'logistic_regression',
            numeric_features=['numeric_1', 'numeric_2', 'numeric_3'],
            categorical_features=[],
        )

        assert pipeline is not None
        assert hasattr(pipeline, 'fit')
        assert hasattr(pipeline, 'predict')

    def test_pipeline_training(self):
        """Test training a complete pipeline."""
        pipeline = build_model_pipeline(
            'random_forest',
            numeric_features=['numeric_1', 'numeric_2', 'numeric_3'],
            categorical_features=[],
        )

        pipeline.fit(self.X_train, self.y_train)

        # Should have fitted estimator
        assert hasattr(pipeline.named_steps['model'], 'classes_')


class TestHyperparameterOptimization:
    """Test hyperparameter tuning."""

    def test_optimizer_module_imports(self):
        """Test HyperparameterOptimizer module imports."""
        from football_bi.models.selection import HyperparameterOptimizer

        assert HyperparameterOptimizer is not None

    def test_optimizer_initialization(self):
        """Test HyperparameterOptimizer initialization."""
        optimizer = HyperparameterOptimizer(cv_splits=3)

        assert optimizer is not None
        assert hasattr(optimizer, 'search')
        assert optimizer.cv_splits == 3


class TestEnsembleMethods:
    """Test ensemble models."""

    def test_stacking_ensemble_module_imports(self):
        """Test StackingEnsemble module imports."""
        from football_bi.models.ensembles import StackingEnsemble

        assert StackingEnsemble is not None

    def test_stacking_ensemble_initialization(self):
        """Test StackingEnsemble initialization."""
        ensemble = StackingEnsemble(
            base_models=['logistic_regression', 'random_forest'],
            meta_model='logistic_regression',
        )

        assert ensemble is not None
        assert ensemble.base_models == ['logistic_regression', 'random_forest']
        assert ensemble.meta_model_name == 'logistic_regression'

    def test_voting_ensemble_module_imports(self):
        """Test VotingEnsemble module imports."""
        from football_bi.models.ensembles import VotingEnsemble

        assert VotingEnsemble is not None

    def test_voting_ensemble_initialization(self):
        """Test VotingEnsemble initialization."""
        ensemble = VotingEnsemble(
            models=['logistic_regression', 'random_forest'],
            voting='soft',
        )

        assert ensemble is not None
        assert ensemble.voting == 'soft'
        assert len(ensemble.models) == 2

    def test_voting_ensemble_with_weights(self):
        """Test voting ensemble with custom weights."""
        ensemble = VotingEnsemble(
            models=['logistic_regression', 'random_forest'],
            weights=[2.0, 1.0],
            voting='soft',
        )

        assert ensemble is not None
        # Weights should be normalized
        assert abs(sum(ensemble.weights) - 1.0) < 0.01  # Sum to 1

    def test_voting_ensemble_soft_is_default(self):
        """Test that soft voting is default."""
        ensemble = VotingEnsemble(
            models=['logistic_regression', 'random_forest'],
        )

        assert ensemble.voting == 'soft'


class TestEvaluation:
    """Test model evaluation metrics."""

    def setup_method(self):
        """Set up test data before each test."""
        self.y_true = np.array(['H', 'D', 'A', 'H', 'D', 'A', 'H', 'A', 'D', 'H'])
        self.y_pred = np.array(['H', 'D', 'A', 'H', 'H', 'A', 'D', 'A', 'D', 'A'])
        self.y_proba = np.array([
            [0.7, 0.1, 0.2],
            [0.1, 0.8, 0.1],
            [0.1, 0.1, 0.8],
            [0.6, 0.2, 0.2],
            [0.5, 0.3, 0.2],
            [0.1, 0.2, 0.7],
            [0.4, 0.3, 0.3],
            [0.2, 0.1, 0.7],
            [0.2, 0.6, 0.2],
            [0.5, 0.2, 0.3],
        ])

    def test_evaluator_initialization(self):
        """Test ExperimentEvaluator initialization."""
        evaluator = ExperimentEvaluator(classes=['H', 'D', 'A'])

        assert evaluator is not None
        assert evaluator.classes == ['H', 'D', 'A']

    def test_calculate_metrics(self):
        """Test metric calculation."""
        evaluator = ExperimentEvaluator(classes=['H', 'D', 'A'])
        metrics = evaluator.calculate_metrics(
            self.y_true,
            self.y_pred,
            self.y_proba,
            'test_model',
        )

        assert metrics is not None
        assert 'accuracy' in metrics
        assert 'f1_macro' in metrics
        assert 'log_loss' in metrics
        assert 'precision_H' in metrics
        assert 'recall_A' in metrics

    def test_metrics_are_valid_values(self):
        """Test that metrics are valid numbers."""
        evaluator = ExperimentEvaluator()
        metrics = evaluator.calculate_metrics(
            self.y_true,
            self.y_pred,
            self.y_proba,
        )

        assert 0 <= metrics['accuracy'] <= 1
        assert 0 <= metrics['f1_macro'] <= 1
        assert metrics['log_loss'] > 0

    def test_evaluate_model_function(self):
        """Test quick evaluate_model function."""
        metrics = evaluate_model(
            self.y_true,
            self.y_pred,
            self.y_proba,
            'my_model',
        )

        assert metrics is not None
        assert metrics['model'] == 'my_model'

    def test_compare_predictions(self):
        """Test comparing multiple models."""
        models_pred = {
            'model_1': (self.y_pred, self.y_proba),
            'model_2': (self.y_pred, self.y_proba),
        }

        comparison = compare_predictions(
            self.y_true,
            models_pred,
        )

        assert comparison is not None
        assert isinstance(comparison, pd.DataFrame)
        assert len(comparison) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
