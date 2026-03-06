# Project Architecture - Football Match Prediction v3

## Overview

This document describes the architecture of the Football Match Prediction project v3, a comprehensive ML system for predicting European football match outcomes.

**Current Performance:** 49.5% accuracy (Extra Trees baseline)
**Target Performance:** 55-65% accuracy with enhanced features and models

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA INGESTION LAYER                      │
│  (Raw CSV files from 5 European leagues, 1993-2026)         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  PREPROCESSING LAYER                         │
│  • Data cleaning & validation                               │
│  • Missing value imputation                                 │
│  • Outlier detection (non-destructive)                      │
│  • Leakage validation (temporal integrity)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              FEATURE ENGINEERING LAYER                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ BASE FEATURES (Existing)                            │   │
│  │ • Elo rating system (K-factor=20)                   │   │
│  │ • Rolling statistics (5-match windows)              │   │
│  │ • Temporal features (month, weekday, season)        │   │
│  │ Output: 23 numeric + 3 categorical features         │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ PLAYER FEATURES (NEW - Phase 2)                     │   │
│  │ • Squad aggregations (age, market value)            │   │
│  │ • Squad composition (defenders, midfielders, etc.)  │   │
│  │ • Injury metrics (injury count, rate)               │   │
│  │ Output: 12 additional numeric features              │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ADVANCED FEATURES (NEW - Phase 3)                   │   │
│  │ • Interaction terms (form product, ELO×form)        │   │
│  │ • Advanced temporal (match quarter, days since match)│   │
│  │ • Polynomial features (optional, ELO_diff²)         │   │
│  │ Output: 5 additional derived features               │   │
│  └─────────────────────────────────────────────────────┘   │
│  Total → 40 features (23+12+5) for modeling               │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              DATA SPLITTING (Temporal)                       │
│  Train:      1993-2023 (all seasons before 2024)           │
│  Validation: 2023-2024 season (year -2)                    │
│  Test:       2024-2025 season (year -1 forward)            │
│  → Prevents look-ahead bias, respects time series nature   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                 MODELING LAYER                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ BASELINE MODELS (Phase 1)                           │   │
│  │ • Logistic Regression (simple baseline)             │   │
│  │ • Random Forest (tree ensemble)                     │   │
│  │ • Extra Trees (current best: 49.5% accuracy)        │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ GRADIENT BOOSTING MODELS (NEW - Phase 4)            │   │
│  │ • XGBoost (standard gradient boosting)              │   │
│  │ • LightGBM (fast leaf-wise gradient boosting)       │   │
│  │ • CatBoost (categorical feature handling)           │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ HYPERPARAMETER TUNING (NEW - Phase 4)               │   │
│  │ • RandomSearchCV (n_iter=100, temporal CV=5)        │   │
│  │ • Model-specific search spaces per config/models.yaml
│  │ • Scoring: F1-Macro (handles class imbalance)       │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ENSEMBLE METHODS (NEW - Phase 5)                    │   │
│  │ • Stacking (meta-learner on base model predictions) │   │
│  │ • Voting (weighted average of predictions)          │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│            EVALUATION & REPORTING LAYER                     │
│  • Performance metrics (accuracy, F1, log loss)             │
│  • Per-class metrics (precision, recall, F1 by outcome)     │
│  • Feature importance (SHAP values)                         │
│  • Model comparison & ranking                              │
│  • Experiment tracking & results archiving                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Structure

### Directory Organization

```
src/football_bi/
├── __init__.py                          # Package initialization
├── config.py                            # Path management and config loading
├── features/
│   ├── __init__.py
│   ├── base_features.py                # Elo + rolling stats (existing logic)
│   ├── player.py                       # NEW: Squad aggregations
│   ├── advanced.py                     # NEW: Interaction features
│   └── engineering.py                  # Orchestration
├── preprocessing/
│   ├── __init__.py
│   ├── cleaning.py                     # Data cleaning (existing + validation)
│   ├── imputation.py                   # NEW: Advanced imputation strategies
│   ├── scaling.py                      # NEW: Feature scaling options
│   └── leakage_check.py                # NEW: Temporal leakage validation
├── models/
│   ├── __init__.py
│   ├── base.py                         # Baseline + new models training
│   ├── selection.py                    # NEW: Hyperparameter tuning (RandomSearch)
│   ├── ensembles.py                    # NEW: Stacking & Voting
│   └── evaluation.py                   # NEW: Metrics & comparison
├── pipeline/
│   ├── __init__.py
│   ├── base.py                         # Existing pipeline logic
│   └── orchestrator.py                 # NEW: Full pipeline manager
├── utils/
│   ├── __init__.py
│   ├── logging.py                      # Logging setup
│   ├── paths.py                        # Path utilities
│   └── profiling.py                    # NEW: Performance tracking
├── api/
│   ├── __init__.py
│   ├── main.py                         # FastAPI endpoints
│   └── schemas.py                      # Pydantic models
├── ingestion.py                        # Data loading (existing)
└── simulation.py                       # Championship simulation (existing)

config/
├── features.yaml                       # Feature engineering configuration
├── models.yaml                         # Model parameters and search spaces
└── experiment.yaml                     # Experiment tracking

tests/
├── __init__.py
├── test_features.py                    # Feature engineering tests
├── test_preprocessing.py                # Preprocessing tests
├── test_models.py                      # Model training tests
└── test_pipeline.py                    # End-to-end pipeline tests

docs/
├── ARCHITECTURE.md                     # This file
├── FEATURES.md                         # Feature engineering details
├── MODELS.md                           # Model selection & tuning
└── API.md                              # API documentation

tutos/
├── 01_PROJECT_OVERVIEW.md              # Getting started
├── 02_DATA_EXPLORATION.md              # EDA guide
├── 03_FEATURE_ENGINEERING.md           # Feature creation walkthrough
├── 04_MODEL_SELECTION.md               # Model training & tuning
└── 05_DEPLOYMENT.md                    # Production deployment

reports/
├── v3/
│   ├── predictions/                    # Test set predictions
│   ├── tuning_results/                 # Hyperparameter search results
│   ├── feature_importance/             # Feature importance plots
│   └── final_report.md                 # Comprehensive results report
└── experiments.csv                     # Experiment tracking spreadsheet
```

---

## Data Flow

### 1. Input Data
- **Source:** `data/raw/football_bi/matches_raw.csv`
- **Format:** 58,467 rows (matches) × ~20 columns
- **Coverage:** 5 leagues, 1993-2026, balanced class distribution
- **Classes:** Home Win (H), Draw (D), Away Win (A)

### 2. Preprocessing
```python
matches_raw
  ↓
clean_data()           # Remove incomplete records, normalize types
  ↓
impute_missing()       # Hierarchical: (league,season) → league → global
  ↓
matches_clean          # Output: data/processed/football_bi/matches_clean.csv
```

### 3. Feature Engineering
```python
matches_clean
  ↓
compute_base_features()
  - Elo ratings for each team (update after each match)
  - Rolling 5-match statistics (points, goals)
  - Temporal features (month, weekday, season)
  ↓
compute_player_features()  [NEW]
  - Load player_profiles.csv + ml_team_features.csv
  - Aggregate per squad per match-date
  - Merge with match data
  ↓
compute_advanced_features()  [NEW]
  - Interaction terms (form × form, elo_diff × form)
  - Advanced temporal (quarter of season)
  - Polynomial features (optional)
  ↓
match_features         # Output: data/processed/football_bi/match_features.csv
```

### 4. Data Splitting (Temporal)
```python
match_features
  ↓
train_df (1993-2023)   # 80% of data
valid_df (2023-2024)   # 10% of data
test_df  (2024-2025)   # 10% of data, hold-out
  ↓
X_train, y_train
X_valid, y_valid
X_test,  y_test
```

### 5. Model Training
```
X_train, y_train
  ├→ LogisticRegression        → CV validation
  ├→ RandomForest              → CV validation
  ├→ ExtraTreesClassifier      → CV validation (current best)
  ├→ XGBoost                   → CV validation [NEW]
  ├→ LightGBM                  → CV validation [NEW]
  └→ CatBoost                  → CV validation [NEW]

Best model (by F1-macro on valid_df)
  ↓
Retrain on (X_train + X_valid, y_train + y_valid)
  ↓
Evaluate on test_df
```

### 6. Hyperparameter Tuning [NEW]
```
For each model:
  RandomSearchCV(model, param_grid, cv=5, n_iter=100)
    ↓
  Best parameters
    ↓
  Retrain model with best params
    ↓
  Save tuned model & results
```

### 7. Ensemble Creation [NEW]
```
top_4_models = [model_1, model_2, model_3, model_4]
  ├→ StackingEnsemble(base_models=top_4, meta_model=LogReg)
  └→ VotingEnsemble(models=top_4, weights=[1.0, 1.0, 1.2, 1.1])
  ↓
Evaluate ensembles on test_df
```

### 8. Output
```
Reports generated:
  ✓ Model metrics (accuracy, F1, log loss)
  ✓ Per-class performance (precision, recall, F1 by outcome)
  ✓ Feature importance (SHAP analysis)
  ✓ Confusion matrices
  ✓ Experiment summary
  ✓ Best model artifact (joblib or pkl)
```

---

## Feature Details

### Base Features (23 numeric + 3 categorical)

| Feature | Type | Description |
|---------|------|-------------|
| `home_elo_pre` | numeric | Home team ELO rating before match |
| `away_elo_pre` | numeric | Away team ELO rating before match |
| `elo_diff` | numeric | Home ELO - Away ELO (home advantage built-in) |
| `home_matches_played_pre` | numeric | Matches played in season by home team |
| `home_points_per_game_pre` | numeric | Mean points/match for home team |
| `home_goal_diff_per_game_pre` | numeric | Mean goal difference/match for home |
| `home_recent_points_avg_pre` | numeric | Mean points in last 5 matches |
| `home_recent_goal_diff_avg_pre` | numeric | Mean goal diff in last 5 matches |
| `home_rest_days_pre` | numeric | Days since home team's last match |
| `league_code` | categorical | League identifier (EPL, LaLiga, etc.) |
| `home_team` | categorical | Home team name |
| `away_team` | categorical | Away team name |
| *(same 9 "away" features)* | numeric | Mirrored for away team |
| `month` | numeric | Match month (1-12) |
| `weekday` | numeric | Match day of week (0-6) |

### Player Features [NEW] (12 numeric)

| Feature | Description |
|---------|-------------|
| `home_squad_avg_age_pre` | Average player age in home squad |
| `home_squad_market_value_pre` | Total transfer market value of squad |
| `home_num_defenders` | Count of defensive players |
| `home_num_midfielders` | Count of midfield players |
| `home_num_forwards` | Count of forward players |
| `home_injury_count_pre` | Number of injured/suspended players |
| `home_injury_rate` | Injured % of squad |
| `home_def_mid_ratio` | Defenders / Midfielders ratio |
| *(same 4 "away" features)* | Mirrored for away team |
| *(1 additional derived feature)* | Injury impact difference |

### Advanced Features [NEW] (5 numeric)

| Feature | Description |
|---------|-------------|
| `home_form_vs_away_form` | Home recent points × Away recent points |
| `elo_advantage_with_form` | ELO diff × Home recent points avg |
| `rest_disparity` | abs(Home rest days - Away rest days) |
| `injury_impact` | Injury rate difference (home - away) |
| `match_quarter` | Season quarter (1=early, 4=late) |

---

## Model Comparison Matrix

| Model | Type | Baseline Perf | Expected Tuned | Ensemble Ready |
|-------|------|---------------|----------------|----------------|
| Logistic Regression | Linear | 49.1% | ~50% | ✓ (baseline) |
| Random Forest | Tree Ensemble | 50.9% | 52-54% | ✓ |
| Extra Trees | Tree Ensemble | **49.5%** | 51-53% | ✓ (current best) |
| XGBoost | GB | N/A | **54-56%** | ✓ (expected best) |
| LightGBM | GB | N/A | 53-55% | ✓ |
| CatBoost | GB | N/A | 52-54% | ✓ |

---

## Performance Targets

| Phase | Focus | Target | Timeline |
|-------|-------|--------|----------|
| **1** | Restructuring | N/A | Days 1-3 |
| **2** | Player features | 51-52% | Days 4-7 |
| **3** | Preprocessing | 51-53% | Days 8-10 |
| **4** | Tuning + GB models | 54-57% | Days 11-18 |
| **5** | Ensemble | 55-60% | Days 19-21 |
| **6** | Testing + validation | Final benchmark | Days 22-24 |

**Final Goal:** 55-65% accuracy (minimum 55%, target 60%, stretch 65%)

---

## Configuration Management

All key parameters are externalized in YAML files:

- **`config/features.yaml`** - Feature engineering settings
- **`config/models.yaml`** - Model defaults & search spaces
- **`config/experiment.yaml`** - Experiment tracking & targets

This enables:
- Easy experimentation with different settings
- Reproducibility across runs
- Clear documentation of choices
- Version control of configurations

---

## Quality Assurance

### Data Integrity
- ✓ Temporal leakage validation
- ✓ Train/valid/test splits maintained (no data interaction)
- ✓ Missing value handling documentation
- ✓ Outlier detection (non-destructive)

### Model Validation
- ✓ Cross-validation using temporal splits
- ✓ Evaluation on hold-out test set only
- ✓ Per-class performance monitoring
- ✓ Probability calibration checks

### Testing
- ✓ Unit tests for features, preprocessing, models
- ✓ Integration tests for pipeline
- ✓ Regression tests (model performance benchmarks)

---

## Success Criteria

✓ Accuracy ≥ 55% (beats baseline 49.5%)
✓ F1-Macro ≥ 0.50 (balanced across outcomes)
✓ Log Loss < 1.0 (good probability calibration)
✓ No temporal leakage detected
✓ Code tested and documented
✓ Full reproducibility
