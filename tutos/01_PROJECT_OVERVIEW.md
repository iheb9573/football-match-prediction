# Football Match Prediction Project - Overview Guide

Welcome to the Football Match Prediction v3 project! This guide helps you understand the project structure and navigate the codebase.

## 📁 What This Project Is About

This is a comprehensive machine learning system that predicts the outcome of European football matches:
- **Task:** Predict whether Home team wins, Draw, or Away team wins
- **Data:** 58,467 historical matches from 5 major leagues (1993-2026)
- **Current Performance:** 49.5% accuracy with Extra Trees classifier
- **Target:** 55-65% accuracy through enhanced features and better models

## 🎯 Your Journey

### For Beginners: Start Here
1. Read `docs/ARCHITECTURE.md` (10 mins) - Understand the big picture
2. Read `docs/FEATURES.md` (15 mins) - Learn what data we use
3. Read `tutos/02_DATA_EXPLORATION.md` (when available) - Explore the data yourself

### For Developers: Implementation Guide
1. Check `docs/ARCHITECTURE.md` - Module organization
2. Review `src/football_bi/` - Core library structure
3. Check `config/features.yaml` and `config/models.yaml`
4. Start with Phase 1: `Refactor src/football_bi/ into submodules`

### For ML Engineers: Model Deep Dive
1. Review current models in `src/football_bi/modeling.py`
2. Check baseline performance in `reports/football_bi/`
3. Plan new models in `config/models.yaml`
4. Implement hyperparameter tuning (Phase 4)

## 📊 Project Structure

```
football-match-prediction/
├── 📂 code/                    # Complete pipeline execution scripts
│   ├── 00_setup_directories.py
│   ├── 01_data_ingestion.py
│   ├── 02_data_preprocessing.py
│   ├── 03_feature_engineering.py
│   ├── 04_eda_visualization.py
│   ├── 05_model_training.py
│   ├── 06_model_explainability.py
│   ├── 07_competition_simulation.py
│   ├── 08_run_all.py           # Run entire pipeline
│   └── 09_run_api.py           # Start API server

├── 📂 src/football_bi/         # Core ML library (modular)
│   ├── __init__.py
│   ├── config.py               # Configuration management
│   ├── ingestion.py            # Data loading
│   ├── preprocessing.py        # Data cleaning & preprocessing
│   ├── features.py             # Feature engineering (Elo + rolling stats)
│   ├── eda.py                  # Exploratory data analysis
│   ├── modeling.py             # Model training & evaluation
│   ├── explainability.py       # Feature importance, SHAP
│   ├── simulation.py           # Championship simulation
│   ├── prediction_service.py   # API service
│   ├── pipeline.py             # Pipeline orchestration
│   ├── utils.py                # Utilities
│   │
│   ├── 📂 features/            # [NEW] Feature engineering modules
│   │   ├── __init__.py
│   │   ├── base_features.py    # Elo + rolling stats (refactored)
│   │   ├── player.py           # [NEW] Squad aggregations
│   │   ├── advanced.py         # [NEW] Interactions & temporal
│   │   └── engineering.py      # Orchestration
│   │
│   ├── 📂 preprocessing/       # [NEW] Preprocessing submodule
│   │   ├── __init__.py
│   │   ├── cleaning.py         # Data cleaning
│   │   ├── imputation.py       # [NEW] Advanced imputation
│   │   ├── scaling.py          # [NEW] Feature scaling options
│   │   └── leakage_check.py    # [NEW] Temporal validation
│   │
│   ├── 📂 models/              # [NEW] Models submodule
│   │   ├── __init__.py
│   │   ├── base.py             # [NEW] Baseline + new models
│   │   ├── selection.py        # [NEW] Hyperparameter tuning
│   │   ├── ensembles.py        # [NEW] Stacking & voting
│   │   └── evaluation.py       # [NEW] Metrics & comparison
│   │
│   ├── 📂 pipeline/            # [NEW] Pipeline orchestration
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── orchestrator.py     # [NEW] Full ML pipeline manager
│   │
│   └── 📂 utils/               # Utilities
│       ├── logging.py
│       ├── paths.py
│       └── profiling.py        # [NEW] Performance tracking

├── 📂 api/                     # FastAPI backend
│   ├── main.py
│   └── schemas.py

├── 📂 frontend/                # React frontend (Vite)
│   └── ... (separate app)

├── 📂 data/                    # Data storage
│   ├── raw/football_bi/        # Raw data from webscraping
│   ├── processed/football_bi/  # Cleaned & engineered data
│   ├── brute/                  # Alternative sources
│   ├── Scrapping/              # Historical season files
│   └── sources_internet/       # External datasets

├── 📂 models/football_bi/      # Trained ML models
│   ├── match_outcome_model.joblib
│   └── match_outcome_model_metadata.json

├── 📂 config/                  # [NEW] Configuration files
│   ├── features.yaml           # Feature engineering config
│   ├── models.yaml             # Model parameters & search spaces
│   └── experiment.yaml         # Experiment tracking config

├── 📂 docs/                    # [NEW] Comprehensive documentation
│   ├── ARCHITECTURE.md         # Project architecture overview
│   ├── FEATURES.md             # Feature engineering guide
│   └── API.md                  # API documentation

├── 📂 tutos/                   # [NEW] Step-by-step tutorials
│   ├── 01_PROJECT_OVERVIEW.md  # (This file)
│   ├── 02_DATA_EXPLORATION.md  # EDA walkthrough
│   ├── 03_FEATURE_ENGINEERING.md
│   ├── 04_MODEL_SELECTION.md
│   └── 05_DEPLOYMENT.md

├── 📂 tests/                   # [NEW] Unit tests
│   ├── __init__.py
│   ├── test_features.py
│   ├── test_preprocessing.py
│   ├── test_models.py
│   └── test_pipeline.py

├── 📂 notebooks/               # Jupyter notebooks (for experimentation)
├── 📂 reports/                 # Results & visualizations
│   ├── v3/                     # [NEW] Experiment v3 results
│   ├── figures/                # Plots & charts
│   └── experiments.csv         # Experiment tracking spreadsheet

├── README.md                   # Main project README
├── requirements.txt            # Python dependencies
└── .gitignore                  # Git ignore rules
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Explore the Baseline
```bash
# Run complete pipeline with current models
python code/08_run_all.py

# Results in:
# - reports/football_bi/model_metrics.csv
# - reports/football_bi/test_predictions.csv
# - models/football_bi/match_outcome_model.joblib
```

### 3. Check Current Performance
```bash
# View baseline results
cat reports/football_bi/model_metrics.csv

# Output:
# Model: Extra Trees
# Accuracy: 0.4947 (49.47%)
# F1-Macro: 0.4656
# Log Loss: 1.0214
```

## 📈 Implementation Roadmap (6 Phases)

### Phase 1: Project Restructuring (Days 1-3)
- ✓ Create directory structure (scripts/, docs/, config/, tests/)
- ✓ Create configuration files (features.yaml, models.yaml, experiment.yaml)
- ✓ Create documentation (ARCHITECTURE.md, FEATURES.md)
- → Refactor src/football_bi/ into submodules (features/, preprocessing/, models/)

### Phase 2: Player Features (Days 4-7)
- Explore player_profiles.csv, ml_team_features.csv, injury_history.csv
- Create `src/football_bi/features/player.py` with squad aggregations
- Create `src/football_bi/features/advanced.py` with interaction features
- Expected improvement: +2-3% accuracy

### Phase 3: Preprocessing Improvements (Days 8-10)
- Refactor preprocessing.py into preprocessing/ submodule
- Create advanced imputation, scaling, leakage validation
- Expected improvement: +1-2% accuracy

### Phase 4: New Models & Tuning (Days 11-18)
- Create models/base.py with XGBoost, LightGBM, CatBoost
- Create models/selection.py with hyperparameter tuning (RandomSearchCV)
- Create models/ensembles.py with Stacking & Voting
- Expected improvement: +5-7% accuracy

### Phase 5: Pipeline Orchestration (Days 19-21)
- Create pipeline/orchestrator.py with MLPipeline class
- Integrate all components into end-to-end workflow
- Add comprehensive logging and checkpointing

### Phase 6: Testing & Validation (Days 22-24)
- Create unit tests for features, preprocessing, models
- Validate no temporal leakage
- Generate final reports and visualization
- Expected final accuracy: 55-65%

## 📊 Key Metrics

### Baseline Performance (Current)
```
Model: Extra Trees Classifier
Accuracy: 49.5%
F1-Macro: 0.42
Log Loss: 1.08

Per-class metrics:
  Home Win: Precision=0.62, Recall=0.58, F1=0.60
  Draw:     Precision=0.29, Recall=0.27, F1=0.28
  Away Win: Precision=0.48, Recall=0.57, F1=0.52
```

### Target Performance (End of Phase 6)
```
Expected Model: Stacking Ensemble (XGBoost + LightGBM + CatBoost + Extra Trees)
Target Accuracy: 55-65%
Target F1-Macro: 0.50-0.55
Target Log Loss: < 1.0
```

## 🔧 Configuration Guide

### Running Custom Experiments

Edit `config/experiment.yaml` to configure:
```yaml
experiment:
  id: my_experiment_v1
  features:
    base: true        # Enable Elo + rolling stats
    player: true      # Enable player features
    advanced: true    # Enable interaction features

models:
  baseline: true      # Test current models
  gradient_boosting: true  # Test new GB models
  tuning:
    n_iter: 100      # RandomSearch iterations
```

Then run:
```bash
python -c "
from src.football_bi.pipeline.orchestrator import MLPipeline
pipeline = MLPipeline('config/experiment.yaml')
pipeline.run(stages=['all'])
"
```

## 📚 Documentation Map

| Document | Purpose | Read Time |
|----------|---------|-----------|
| README.md | Project overview | 5 min |
| docs/ARCHITECTURE.md | System design | 20 min |
| docs/FEATURES.md | Feature details | 25 min |
| config/features.yaml | Feature config | 5 min |
| config/models.yaml | Model config | 10 min |
| tutos/02_DATA_EXPLORATION.md | EDA walkthrough | 30 min |

## 🤔 FAQ

**Q: Where do I start if I want to improve accuracy?**
A: Start with Phase 2 (Player Features) in the roadmap. Review `docs/FEATURES.md` first.

**Q: How do I run just the baseline models?**
A: `python code/05_model_training.py` (uses existing features and models)

**Q: How do I add a new feature?**
A:
1. Define it in `src/football_bi/features/` (base.py, player.py, or advanced.py)
2. Add to feature list in `src/football_bi/modeling.py`
3. Validate no temporal leakage
4. Test on validation set

**Q: Where are the trained models saved?**
A: `models/football_bi/` directory (joblib format)

**Q: How do I access the API?**
A: Run `python code/09_run_api.py`, then visit `http://localhost:8000/docs`

## 💡 Tips

1. **Before making changes:** Always commit current state to git
2. **Testing features:** Use validation set only (never evaluate on test set)
3. **Temporal integrity:** Always check that features don't use future data
4. **Version control:** Tag major experiments with git tags
5. **Documentation:** Update docs when adding features or models

## 🔗 Related Resources

- [Elo Rating System](https://en.wikipedia.org/wiki/Elo_rating_system)
- [Scikit-learn Ensemble Methods](https://scikit-learn.org/stable/modules/ensemble.html)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [LightGBM Documentation](https://lightgbm.readthedocs.io/)
- [CatBoost Documentation](https://catboost.ai/)

## 📞 Support

For questions, check:
1. Relevant documentation in `docs/`
2. Inline code comments in `src/football_bi/`
3. Tutorial files in `tutos/`
4. Project README.md

---

**Last Updated:** March 6, 2024
**Version:** 3.0
**Author:** Football BI/IA Team
