# 📊 Flashscore Scraper + ML Dataset Builder

## Installation

```bash
pip install selenium webdriver-manager pandas requests tqdm scikit-learn
```
> Chrome doit être installé sur votre machine (le driver est téléchargé automatiquement).

---

## Utilisation

### Scraper toutes les ligues + entraîner le modèle
```bash
python flashscore_scraper.py --leagues all --train
```

### Scraper seulement La Liga + Premier League
```bash
python flashscore_scraper.py --leagues la_liga premier_league --train
```

### Ignorer le scraping (recharger les CSV existants) + ML
```bash
python flashscore_scraper.py --skip-scraping --train
```

---

## Fichiers générés dans `flashscore_data/`

| Fichier | Contenu |
|---|---|
| `squads.csv` | Tous les joueurs par équipe + ligue |
| `player_profiles.csv` | Profil complet (poste, âge, taille, nationalité…) |
| `injury_history.csv` | Historique des blessures par joueur |
| `matches_<league>.csv` | Résultats de matchs (datahub.io) |
| `ml_dataset.csv` | Dataset final fusionné prêt pour ML |
| `baseline_rf_model.pkl` | Modèle RandomForest entraîné |
| `scraper.log` | Log complet |

---

## Architecture du pipeline

```
Flashscore
  ├── /team/{slug}/{id}/squad/          → squads.csv
  ├── /player/{slug}/{id}/              → player_profiles.csv
  └── /player/{slug}/{id}/injury-history/ → injury_history.csv

datahub.io
  ├── english-premier-league
  ├── spanish-la-liga
  ├── italian-serie-a
  ├── german-bundesliga
  └── french-ligue-1                    → matches_*.csv

Feature Engineering
  → agrégation par équipe (avg_age, total_injuries, positions…)
  → fusion avec les matchs (home_team / away_team)
  → target : H=1  D=0  A=-1

ML Baseline
  → RandomForestClassifier (200 estimators)
  → classification_report + feature importances
```

---

## Notes importantes

- **Flashscore bloque les bots** : des délais aléatoires (2.5–5s) sont intégrés.
  Pour les grands volumes, utilisez des proxies résidentiels.
- Les **IDs Flashscore** dans `TEAMS` sont des exemples. Récupérez les vrais IDs
  depuis l'URL de chaque équipe : `flashscore.com/team/real-madrid/**W8mj7MDD**/squad/`
- Ajoutez vos propres équipes dans le dictionnaire `TEAMS` du script.
- Le **feature engineering** est facilement extensible (ELO, forme récente, etc.)
