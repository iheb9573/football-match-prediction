# 🚀 QUICK START - Exécuter le Pipeline

## ✅ Installation & Exécution Rapide

### Option 1 : Batch Script (Windows - Recommandé)
```bash
run_pipeline.bat
```
Cela :
1. ✅ Installe les dépendances (`pip install -r requirements.txt`)
2. ✅ Lance le pipeline complet avec 300 simulations
3. ✅ Génère tous les rapports et modèles

### Option 2 : Exécution Manuelle (Terminal)

```bash
# 1. Résultat des dépendances
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2. Lancer le pipeline
.venv\Scripts\python.exe code/08_run_all.py --simulations 300
```

### Option 3 : Exécution Étape par Étape
```bash
.venv\Scripts\python.exe code/00_setup_directories.py
.venv\Scripts\python.exe code/01_data_ingestion.py
.venv\Scripts\python.exe code/02_data_preprocessing.py
.venv\Scripts\python.exe code/03_feature_engineering.py
.venv\Scripts\python.exe code/04_eda_visualization.py
.venv\Scripts\python.exe code/05_model_training.py
.venv\Scripts\python.exe code/06_model_explainability.py
.venv\Scripts\python.exe code/07_competition_simulation.py --simulations 300
```

---

## 📊 Résultats Générés

Après exécution :

```
reports/football_bi/
├── model_metrics.csv                    # Accuracy, F1, LogLoss
├── test_predictions.csv                 # Prédictions détaillées
├── classification_report_test.txt       # Rapport de classification
├── permutation_importance.csv           # Feature importance
├── champion_probabilities.csv           # Probabilités par ligue
└── figures/
    ├── confusion_matrix_*.png           # Matrices de confusion
    ├── permutation_importance_*.png     # Graphiques importance
    └── champion_probability_*.png       # Probabilités par ligue

models/football_bi/
├── match_outcome_model.joblib           # Modèle entraîné
└── match_outcome_model_metadata.json    # Métadonnées
```

---

## 🖥️ Visualiser le Dashboard

Une fois le pipeline terminé, lancez l'API:

```bash
# Terminal 1 : API FastAPI
.venv\Scripts\python.exe code/09_run_api.py
# → http://127.0.0.1:8000

# Terminal 2 : Frontend (optionnel)
cd interface/b_65PkRuwmNDh-1771889902461
npm install
npm run dev
# → http://127.0.0.1:3000
```

---

## 🔧 Troubleshooting

### Erreur : "No module named 'fastapi'"
```bash
# Réinstallez les dépendances
.venv\Scripts\python.exe -m pip install --upgrade -r requirements.txt
```

### Erreur : "cannot import name 'run_full_pipeline'"
✅ **Déjà corrigé** - Utilisez le script `code/08_run_all.py` mis à jour

### Erreur : "Execution of scripts is disabled"
```bash
# Utilisez le batch script à la place
run_pipeline.bat
```

---

## 📈 Métriques Attendues

Après exécution complète :
- **Accuracy** : ~50% (Extra Trees sur split temporel)
- **F1 Macro** : ~47%
- **LogLoss** : ~1.02
- **Modèles testés** : 6 (LogReg, RF, ET, XGB, LGB, CB)
- **Données traitées** : ~58,467 matchs (1993-2026)

---

## 💡 Notes

- Le pipeline respecte l'**ordre chronologique** (pas de look-ahead bias)
- Les features sont calculées **pré-match** (pas de fuite de données)
- L'imputation est **hiérarchique** : (league, season) → league → global
- Les modèles sont **tuned** via RandomSearchCV avec temporal CV

Pour plus de détails : voir `docs/ARCHITECTURE.md` et `tutos/02_PIPELINE_USAGE.md`
