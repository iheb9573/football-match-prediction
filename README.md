# Football BI Predictor

Solution complete de **Business Intelligence + Machine Learning** pour predire, de maniere **probabiliste** et **explicable**, l'equipe ayant le plus de chances de remporter la competition.

## Objectif principal
Construire un pipeline professionnel qui couvre:
- ingestion des donnees multi-ligues
- preprocessing robuste
- feature engineering pre-match
- EDA et visualisations BI
- modelisation probabiliste du resultat de match (H / D / A)
- explainability des predictions
- simulation Monte Carlo du vainqueur de championnat

## Ligues couvertes
```python
LEAGUES = {
    "EPL": "english-premier-league",
    "LaLiga": "spanish-la-liga",
    "SerieA": "italian-serie-a",
    "Bundesliga": "german-bundesliga",
    "Ligue1": "french-ligue-1",
}
```

## Demarche suivie (style projet academique)
La demarche suit le meme esprit que les repos de reference (scripts numerotes, pipeline clair, livrables progressifs):

1. Setup des dossiers
2. Ingestion
3. Preprocessing
4. Feature engineering
5. EDA / BI
6. Entrainement modele
7. Explainability
8. Simulation probabiliste champion

## Architecture
```text
football-match-prediction/
  code/
    00_setup_directories.py
    01_data_ingestion.py
    02_data_preprocessing.py
    03_feature_engineering.py
    04_eda_visualization.py
    05_model_training.py
    06_model_explainability.py
    07_competition_simulation.py
    08_run_all.py
    09_run_api.py
  api/
    main.py
    schemas.py
  interface/b_65PkRuwmNDh-1771889902461/
    app/
    components/
    lib/
    package.json
  src/football_bi/
    config.py
    ingestion.py
    preprocessing.py
    features.py
    eda.py
    modeling.py
    explainability.py
    simulation.py
    pipeline.py
  data/
    Scrapping/football-datasets-main/football-datasets-main/datasets/   # source matches
    raw/football_bi/
    processed/football_bi/
  reports/football_bi/
    figures/
    bi/
  models/football_bi/
```

## Installation
```bash
pip install -r requirements.txt
```

## Execution
### Pipeline complet
```bash
python code/08_run_all.py --simulations 300
```

### Execution etape par etape
```bash
python code/00_setup_directories.py
python code/01_data_ingestion.py
python code/02_data_preprocessing.py
python code/03_feature_engineering.py
python code/04_eda_visualization.py
python code/05_model_training.py
python code/06_model_explainability.py
python code/07_competition_simulation.py --simulations 300
```

### Lancer l'API FastAPI
```bash
python code/09_run_api.py
```
API: `http://127.0.0.1:8000`

### Lancer le frontend Next.js (interface professionnelle)
```bash
cd interface/b_65PkRuwmNDh-1771889902461
npm install
# copier .env.example vers .env.local si besoin
npm run dev
```
Frontend: `http://127.0.0.1:3000`

## Sorties generees
### Donnees
- `data/raw/football_bi/matches_raw.csv`
- `data/processed/football_bi/matches_clean.csv`
- `data/processed/football_bi/match_features.csv`

### Rapports EDA / BI
- `reports/football_bi/eda_summary.md`
- `reports/football_bi/league_summary.csv`
- `reports/football_bi/season_summary.csv`
- `reports/football_bi/figures/*.png`

### Modelisation
- `models/football_bi/match_outcome_model.joblib`
- `models/football_bi/match_outcome_model_metadata.json`
- `reports/football_bi/model_metrics.csv`
- `reports/football_bi/test_predictions.csv`
- `reports/football_bi/classification_report_test.txt`

### Explainability
- `reports/football_bi/permutation_importance.csv`
- `reports/football_bi/explainability_summary.md`
- `reports/football_bi/figures/11_permutation_importance_top20.png`

### Probabilites champion
- `reports/football_bi/bi/champion_probabilities.csv`
- `reports/football_bi/bi/champion_probabilities.md`
- `reports/football_bi/bi/champion_probability_<league>.png`

### API + Dashboard
- Prediction de 2 equipes par utilisateur: `POST /api/predict`
- Predictions dashboard: `GET /api/predictions`
- Prediction personnalisee (2 equipes): `POST /api/predictions/analyze`
- Statistiques dashboard: `GET /api/statistics`
- Simulations dashboard: `GET /api/simulations`
- Liste ligues: `GET /api/leagues`
- Liste equipes (ligue): `GET /api/teams/{league_code}`
- Metriques modele: `GET /api/dashboard/model-metrics`
- Dashboard probabilites champion: `GET /api/dashboard/champion-probabilities`

## Resultats obtenus (execution locale)
- Matchs traites: **58,467**
- Fenetre temporelle: **1993-07-23 -> 2026-02-15**
- Modele selectionne: **Extra Trees**
- Validation:
  - Accuracy: **0.5103**
  - F1 Macro: **0.4763**
  - LogLoss: **1.0193**
- Test:
  - Accuracy: **0.4947**
  - F1 Macro: **0.4656**
  - LogLoss: **1.0214**

## A propos de l'objectif 75%
Sur ce probleme **3 classes (H/D/A)** avec uniquement des donnees historiques match-level, atteindre 75% en split temporel strict est tres peu realiste.
Pour se rapprocher de 75%, il faut ajouter des donnees exogenes fortes:
- cotes bookmakers pre-match
- blessures/suspensions et lineups confirms
- forme des joueurs et expected goals (xG)
- contexte calendrier/competitions europeennes en temps reel

## Notes methodologiques
- Preprocessing des valeurs manquantes par imputation hierarchique:
  - mediane `(league, season)` puis `league` puis globale
- Features pre-match sans fuite de donnees:
  - Elo pre-match, forme recente, points/match, repos, differenciels home-away
- Simulation champion:
  - Monte Carlo sur matchs restants de la saison en cours
  - probabilites basees sur un moteur Elo + forme + points/match

## Source de donnees principale
- `football-data.co.uk` via:
  - `data/Scrapping/football-datasets-main/football-datasets-main/datasets/`
