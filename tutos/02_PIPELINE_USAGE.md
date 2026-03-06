# Pipeline Orchestrator Guide

## Overview

The ML Pipeline orchestrator manages the complete workflow for football match prediction:
1. Data Loading
2. Preprocessing
3. Feature Engineering
4. Data Splitting (temporal)
5. Baseline Model Training
6. Hyperparameter Tuning (optional)
7. Ensemble Creation (optional)
8. Model Evaluation
9. Report Generation

---

## Quick Start

### Basic Usage

```python
from src.football_bi.pipeline.orchestrator import MLPipeline

# Initialize pipeline
pipeline = MLPipeline(
    data_path="data/processed/football_bi/match_features.csv",
    output_dir="reports/my_experiment",
    verbose=1
)

# Run complete pipeline
results = pipeline.run_full_pipeline(
    tune_hyperparameters=True,
    create_ensembles=True,
)

# Access results
test_results = results["test"]
print(test_results)
```

### Stage-by-Stage Execution

```python
pipeline = MLPipeline(data_path="data/processed/football_bi/match_features.csv")

# Execute individual stages
pipeline.load_data()
pipeline.preprocess(imputation_strategy="hierarchical")
pipeline.split_data(test_season_year=2025, valid_season_year=2024)
pipeline.train_baseline_models(models=["extra_trees", "random_forest"])
pipeline.tune_hyperparameters(strategy="random", n_iter=100)
pipeline.create_ensembles()
pipeline.evaluate_on_test()
pipeline.generate_report()
```

---

## Available Methods

### Initialization
```python
MLPipeline(
    data_path: str | Path,           # Path to features CSV
    output_dir: str | Path = "reports/pipeline",
    random_state: int = 42,
    verbose: int = 1  # 0=silent, 1=info, 2=debug
)
```

### Main Pipeline Methods

#### `load_data()`
Loads data from CSV file.
- **Returns:** `MLPipeline` (self for chaining)
- **Example:** `pipeline.load_data()`

#### `preprocess(imputation_strategy: str = "hierarchical")`
Preprocesses data:
- Imputation (hierarchical → league → global)
- Temporal leakage validation
- Feature cleaning

**Parameters:**
- `imputation_strategy`: "hierarchical", "forward_fill", or "mean"

**Returns:** `MLPipeline`

#### `split_data(test_season_year: int = 2025, valid_season_year: int = 2024)`
Creates temporal train/valid/test splits.

**Parameters:**
- `test_season_year`: Season year for test set
- `valid_season_year`: Season year for validation set

**Returns:** `MLPipeline`

#### `train_baseline_models(models: list[str] | None = None)`
Trains baseline models without tuning.

**Parameters:**
- `models`: List of model names. Default: all available

**Returns:** `MLPipeline`

**Available Models:**
- "logistic_regression"
- "random_forest"
- "extra_trees"
- "xgboost" (if installed)
- "lightgbm" (if installed)
- "catboost" (if installed)

#### `tune_hyperparameters(models: list[str] | None = None, strategy: str = "random", n_iter: int = 100)`
Optimizes hyperparameters for selected models.

**Parameters:**
- `models`: Models to tune. Default: top 3 baseline models
- `strategy`: "random" or "grid"
- `n_iter`: Number of iterations for random search

**Returns:** `MLPipeline`

#### `create_ensembles()`
Creates ensemble models (Stacking and Voting).

**Returns:** `MLPipeline`

#### `evaluate_on_test()`
Evaluates all models on test set.

**Returns:** `MLPipeline`

#### `generate_report()`
Generates comprehensive pipeline report.

**Returns:** `MLPipeline`

#### `run_full_pipeline(stages: list[str] | str = "all", tune_hyperparameters: bool = False, create_ensembles: bool = False)`
Orchestrates complete pipeline execution.

**Parameters:**
- `stages`: "all" or list of stage names
- `tune_hyperparameters`: Whether to tune hyperparams
- `create_ensembles`: Whether to create ensembles

**Returns:** `dict` with results

---

## Output Files

The pipeline generates CSV files with results:

### 1. `01_baseline_results.csv`
Baseline model performance on validation set.

**Columns:**
- model: Model name
- accuracy: Validation accuracy
- f1_macro: Unweighted F1 score
- log_loss: Probabilistic loss

### 2. `02_tuning_results.csv` (if tuning enabled)
Hyperparameter-tuned model performance.

### 3. `03_ensemble_results.csv` (if ensembles enabled)
Ensemble model performance.

### 4. `04_test_results.csv`
Final model evaluation on test set.

**Additional Columns (per-class metrics):**
- precision_{H,D,A}: Precision for each outcome
- recall_{H,D,A}: Recall for each outcome
- f1_{H,D,A}: F1 score for each outcome

### 5. `FINAL_REPORT.txt`
Comprehensive human-readable report.

---

## Logging

The pipeline provides detailed logging:

**Log Levels:**
- INFO (verbose=0): Silent
- INFO (verbose=1): Key milestones
- DEBUG (verbose=2): Detailed debug info

**Log File:** Automatically created in output_dir with timestamp

**Console Output:** Also displayed to terminal

---

## Examples

### Example 1: Baseline Training Only

```python
from src.football_bi.pipeline.orchestrator import MLPipeline

pipeline = MLPipeline(
    data_path="data/processed/football_bi/match_features.csv",
    verbose=1
)

results = pipeline.run_full_pipeline(
    tune_hyperparameters=False,
    create_ensembles=False,
)

# Print best baseline model
best = results["test"].iloc[0]
print(f"Best Model: {best['model']}")
print(f"Accuracy: {best['accuracy']:.4f}")
```

### Example 2: With Hyperparameter Tuning

```python
pipeline = MLPipeline(data_path="data/processed/football_bi/match_features.csv")

results = pipeline.run_full_pipeline(
    tune_hyperparameters=True,
    create_ensembles=False,
)
```

### Example 3: Full Pipeline with Ensembles

```python
pipeline = MLPipeline(data_path="data/processed/football_bi/match_features.csv")

results = pipeline.run_full_pipeline(
    tune_hyperparameters=True,
    create_ensembles=True,
)
```

### Example 4: Manual Stage Execution

```python
pipeline = MLPipeline(
    data_path="data/processed/football_bi/match_features.csv",
    output_dir="reports/custom_run",
    verbose=2  # Debug mode
)

# Load and preprocess
pipeline.load_data()
pipeline.preprocess(imputation_strategy="hierarchical")
pipeline.split_data()

# Train only specific models
pipeline.train_baseline_models(models=["extra_trees", "xgboost"])

# Tune specific models
pipeline.tune_hyperparameters(
    models=["extra_trees"],
    strategy="grid",
    n_iter=50
)

# Evaluate and report
pipeline.evaluate_on_test()
pipeline.generate_report()

# Access results
results = pipeline.results
```

---

## Performance Expectations

### Baseline Models (no tuning)
- Logistic Regression: ~49-50%
- Random Forest: ~50-51%
- Extra Trees: ~49-50%

### After Hyperparameter Tuning
- +2-5% improvement depending on model

### After Ensemble Methods
- +0.5-2% improvement over best individual model

### Overall Expected Range
**55-63% accuracy** (up from 49.5% baseline)

---

## Troubleshooting

### Error: "File not found"
**Solution:** Verify data_path exists and contains match_features.csv
```python
from pathlib import Path
print(Path("data/processed/football_bi/match_features.csv").exists())
```

### Error: "season_start_year not found"
**Solution:** Pipeline will try to infer from match_date column
- Ensure match_date column exists in data
- Or pre-compute season_start_year before loading

### Warning: "Leakage issues detected"
**Solution:** Check feature engineering
- Verify all features computed BEFORE match time
- Use leakage_check module directly to debug

### Error: "Model not found"
**Solution:** Model may not be installed
- Install: `pip install xgboost lightgbm catboost`
- Or use only baseline models (always available)

### Memory Issues on Large Datasets
**Solution:**
- Reduce n_iter in tuning (use default 100 or smaller)
- Use grid search with smaller param grid
- Process data in batches if needed

---

## Best Practices

1. **Always validate preprocessing:**
   ```python
   pipeline.preprocess()
   # Check: pipeline.df_processed for data quality
   ```

2. **Monitor logging:**
   ```python
   pipeline = MLPipeline(..., verbose=2)  # Debug mode
   ```

3. **Save results:**
   ```python
   # Results automatically saved in output_dir
   # Check for CSV files: 01_baseline_results.csv, etc.
   ```

4. **Test small before large:**
   ```python
   # First run without tuning/ensembles
   pipeline.run_full_pipeline(tune_hyperparameters=False)
   # Then add optional stages
   ```

5. **Check temporal integrity:**
   ```python
   # Pipeline validates automatically
   # Check logs for leakage warnings
   ```

---

## Advanced Usage

### Custom Model Selection

```python
# Train only specific models
pipeline.load_data()
pipeline.preprocess()
pipeline.split_data()
pipeline.train_baseline_models(
    models=["extra_trees", "random_forest"]
)
```

### Different Imputation Strategies

```python
# Try hierarchical imputation
pipeline.preprocess(imputation_strategy="hierarchical")

# Or forward-fill for time series
pipeline.preprocess(imputation_strategy="forward_fill")
```

### Grid Search Tuning

```python
# Use exhaustive grid search instead of random
pipeline.tune_hyperparameters(
    strategy="grid",  # Instead of "random"
    n_iter=50
)
```

---

## Performance Monitoring

The pipeline automatically generates:
1. **CSV Results** - Easy to load and analyze
2. **Log Files** - Track execution details
3. **Text Reports** - Human-readable summary

```python
# Load and analyze results
import pandas as pd
baseline_df = pd.read_csv("reports/pipeline/01_baseline_results.csv")
test_df = pd.read_csv("reports/pipeline/04_test_results.csv")

# Find best model
best = test_df.loc[test_df['f1_macro'].idxmax()]
print(best)
```

---

**For more details, see docs/ARCHITECTURE.md and other documentation files.**
