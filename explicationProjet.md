# 🎙️ Football Match Prediction — Comment raconter ce projet en 5 minutes

---

## 🏟️ L'histoire du projet (à raconter comme un récit)

### 1. Le problème et l'idée

> "On a voulu répondre à une seule question : **qui va gagner le prochain match de football ?**"

On a construit un pipeline complet de Data Science — de la collecte des données brutes jusqu'à une interface web — qui prédit le résultat d'un match (victoire domicile / nul / victoire extérieur) de façon **probabiliste et explicable**, pour 5 grandes ligues européennes : Premier League, La Liga, Serie A, Bundesliga, Ligue 1.

---

### 2. La collecte des données (`ingestion.py`)

La source est **football-data.co.uk** — des fichiers CSV par saison, par ligue, dans le dossier :
```
data/Scrapping/football-datasets-main/datasets/
```

Le fichier `ingestion.py` lit tous ces CSV (saison après saison) et les concatène en un seul DataFrame. On charge des colonnes très précises : date, équipes, buts mi-temps, buts final, tirs, corners, fautes, cartons. Résultat : **58 467 matchs** de 1993 à 2026.

> "On n'a pas fait de scraping dynamique — les données étaient déjà structurées en CSV, ligue par ligue, saison par saison. On les a chargées, étiquetées avec le code ligue, la saison, et concaténées."

---

### 3. Le prétraitement (`preprocessing.py`)

Après ingestion, on nettoie dans `clean_matches()` :

- **Renommage des colonnes** : `FTHG` → `home_goals`, `FTR` → `full_time_result`, etc.
- **Parsing des dates** : format `dd/mm/yy` → `datetime`
- **Imputation hiérarchique des valeurs manquantes** (tirs, corners, cartons...) :
  1. Médiane par `(league, season)`
  2. Sinon médiane par `league`
  3. Sinon médiane globale
- **Flags de données manquantes** : on garde une colonne `col_was_missing` pour l'explicabilité BI
- **Suppression des doublons** sur la clé naturelle : `(league, season, date, home_team, away_team)`
- **Variables dérivées** : `goal_diff`, `total_goals`, `home_win`, `draw`, `away_win`, `match_month`, `match_weekday`

> "L'idée clé : on ne supprime pas les lignes avec données manquantes — on impute intelligemment en allant du plus précis (même ligue + même saison) au plus général (médiane globale)."

---

### 4. Le Feature Engineering (`features.py`)

C'est le cœur du projet. On ne peut pas utiliser les statistiques du match lui-même pour prédire le résultat (ça serait de la **fuite de données**). Donc on crée des **features pré-match** uniquement.

La fonction `build_match_features()` parcourt tous les matchs **dans l'ordre chronologique** et maintient un état vivant pour chaque équipe, via la classe `TeamState` :

| Feature | Description |
|---|---|
| `elo_pre` | Score ELO avant le match (commence à 1500, K=20) |
| `points_per_game_pre` | Points/match accumulés dans la saison en cours |
| `goal_diff_per_game_pre` | Différence de buts/match |
| `recent_points_avg_pre` | Moyenne des points sur les **5 derniers matchs** |
| `recent_goal_diff_avg_pre` | Différence de buts récente (5 matchs) |
| `rest_days_pre` | Nombre de jours depuis le dernier match |

Pour chaque match, on calcule la **différence** domicile − extérieur pour chaque feature (`elo_diff`, `ppg_diff`, `recent_points_diff`, etc.) → **23 features au total**.

> "Le principe anti-fuite : on prend le **snapshot de l'état de l'équipe AVANT** le match, ensuite seulement on met à jour l'état avec le résultat réel. Ainsi, le modèle ne voit jamais l'avenir."

**ELO** : après chaque match, on met à jour : `elo_nouveau = elo_ancien + 20 × (résultat_réel − résultat_attendu)`. En début de saison, l'ELO est partiellement réinitialisé : `0.75 × elo_precedent + 0.25 × 1500`.

---

### 5. La modélisation (`modeling.py`)

#### Découpage temporel strict (pas de random split !)

```
Train  → toutes les saisons sauf les 2 dernières
Valid  → avant-dernière saison
Test   → dernière saison
```

On ne fait **pas de split aléatoire** — avec des données temporelles, c'est une erreur classique. Un random split laisserait fuiter des matchs futurs dans le train.

#### Les modèles candidats

On compare 3 modèles dans un pipeline `sklearn` (StandardScaler + OneHotEncoder → modèle) :

1. **Logistic Regression** (baseline linéaire)
2. **Random Forest** (350 arbres, max_depth=18)
3. **Extra Trees** ✅ ← sélectionné automatiquement

Chaque modèle est évalué sur la validation, et **Extra Trees est sélectionné** selon le meilleur **F1-macro** + le plus faible **Log Loss**.

> "On n'a pas fait de GridSearch ou RandomSearch complet — les hyperparamètres ont été fixés manuellement après tests. La sélection se fait par comparaison sur la validation (F1-macro)."

#### Résultats finaux

| Métrique | Validation | Test |
|---|---|---|
| Accuracy | 51.0% | 49.5% |
| F1-Macro | 0.476 | 0.466 |
| Log Loss | 1.019 | 1.021 |

> "49-51% sur 3 classes, c'est correct. Une baseline qui prédit toujours 'victoire domicile' (la plus fréquente, 44%) donnerait 44%. Notre modèle fait mieux. Atteindre 75% sans données bookmakers/blessures/lineups est quasi-impossible."

Le modèle est sauvegardé avec `joblib` dans `models/football_bi/match_outcome_model.joblib`.

---

### 6. L'explicabilité (`explainability.py`)

On calcule la **permutation importance** : on mélange une feature et on mesure la baisse de performance. Résultat sauvegardé dans `reports/football_bi/permutation_importance.csv`.

Les features les plus importantes : **elo_diff**, **ppg_diff**, **recent_points_diff**.

---

### 7. La simulation Monte Carlo (`simulation.py`)

Pour savoir **qui a le plus de chances de gagner le championnat**, on simule les matchs restants de la saison en cours avec Monte Carlo :

- On repart de l'état actuel du classement (matchs déjà joués)
- Pour chaque match restant, on calcule les probabilités `P(H)`, `P(D)`, `P(A)` via un moteur heuristique : **ELO + points/match + forme récente**
- On tire un résultat aléatoire selon ces probabilités
- On répète **300 fois** (ou plus) et on compte le nombre de fois où chaque équipe finit première

Résultat → `reports/football_bi/bi/champion_probabilities.csv`

---

### 8. L'API FastAPI (`api/main.py` + `prediction_service.py`)

L'API est construite avec **FastAPI**. Elle démarre avec `python code/09_run_api.py` sur `http://127.0.0.1:8000`.

Au démarrage (`startup`), elle charge :
- Le modèle `.joblib`
- Les métadonnées JSON
- Le CSV des matchs propres
- Les probabilités champion

**Endpoints principaux :**

| Endpoint | Méthode | Rôle |
|---|---|---|
| `GET /api/leagues` | GET | Liste des 5 ligues |
| `GET /api/teams/{league_code}` | GET | Équipes de la dernière saison |
| `POST /api/predict` | POST | Prédiction simple (home/draw/away + probabilités) |
| `POST /api/predictions/analyze` | POST | Prédiction enrichie (xG, forme, H2H, explication) |
| `GET /api/predictions` | GET | Feed de prédictions pour le dashboard |
| `GET /api/simulations` | GET | Probabilités champion (Monte Carlo) |
| `GET /api/statistics` | GET | Stats globales, précision par ligue, top features |

#### Comment fonctionne une prédiction ?

1. L'API reçoit `league_code`, `home_team`, `away_team`
2. Elle reconstruit l'état ELO et les stats de chaque équipe à partir des matchs historiques (`_build_latest_states`)
3. Elle construit la **même feature row** que lors de l'entraînement
4. Elle appelle `model.predict_proba(feature_df)` → `P(H)`, `P(D)`, `P(A)`
5. Elle retourne la classe avec la plus haute probabilité + l'explication des 3 features les plus déterminantes

> "On n'a pas utilisé Swagger manuellement — mais FastAPI génère automatiquement une doc interactive Swagger sur `http://127.0.0.1:8000/docs`. On peut tester tous les endpoints directement depuis le navigateur."

---

### 9. L'interface (`interface/` + `frontend/`)

Il y a **deux interfaces** :

1. **Interface v0 (Next.js avancée)** : `interface/b_65PkRuwmNDh-1771889902461/` → port 3000
2. **Frontend simplifié (Vite)** : `frontend/` → port 5173

L'interface consomme **directement l'API FastAPI** :
- Elle appelle `GET /api/predictions` pour afficher le dashboard de matchs
- Elle appelle `POST /api/predictions/analyze` quand l'utilisateur choisit deux équipes
- Elle appelle `GET /api/simulations` pour les graphiques de probabilités champion
- Elle appelle `GET /api/statistics` pour les métriques du modèle

> "L'interface ne stocke aucune donnée localement — tout vient de l'API. Les chiffres que vous voyez à l'écran sont calculés en temps réel à partir du modèle et des données historiques."

---

### 10. Les tests (`tests/`)

On a 4 fichiers de tests unitaires avec `pytest` :

| Fichier | Ce qu'il teste |
|---|---|
| `test_features.py` | ELO, snapshots, calcul des features pré-match |
| `test_preprocessing.py` | Nettoyage, imputation, parsing des dates |
| `test_models.py` | Pipeline sklearn, prédiction, métriques |
| `test_pipeline.py` | Le pipeline de bout en bout |

Lancement : `pytest tests/` ou `python test_smoke.py` pour un test rapide de fumée.

---

## 📂 Les fichiers les plus importants

| Fichier | Rôle |
|---|---|
| `src/football_bi/ingestion.py` | Charge tous les CSV de matchs |
| `src/football_bi/preprocessing.py` | Nettoie, impute, parse les dates |
| `src/football_bi/features.py` | Crée les features ELO + forme pré-match |
| `src/football_bi/modeling.py` | Compare 3 modèles, sélectionne Extra Trees |
| `src/football_bi/simulation.py` | Monte Carlo → probabilités champion |
| `src/football_bi/prediction_service.py` | Service de prédiction (cœur de l'API) |
| `api/main.py` | Endpoints FastAPI |
| `code/08_run_all.py` | Lance tout le pipeline en une commande |

---

## ❓ Questions possibles et meilleures réponses

**Q : Comment vous avez joiné les données de matchs et les données de joueurs ?**

> "Dans la version de base, on n'a pas de données de joueurs individuels — uniquement les statistiques match-level (buts, tirs, corners...). Les features 'joueurs' (`src/football_bi/features/player.py`) ont été développées mais pas encore intégrées au pipeline principal. La jointure prévue se fait sur `(home_team, season_year)` pour agréger des métriques d'effectif (âge moyen, valeur marchande) à chaque match."

---

**Q : Vous avez fait un GridSearch ou RandomSearch ?**

> "Non. Les hyperparamètres ont été fixés manuellement (Ex: Extra Trees : 500 arbres, max_depth=20, min_samples_leaf=2, class_weight='balanced_subsample'). La sélection du meilleur modèle se fait par comparaison sur le set de validation avec le score F1-macro. On n'a pas fait de recherche automatique d'hyperparamètres — c'est identifié comme prochaine étape dans le PROGRESS.md."

---

**Q : Pourquoi Extra Trees plutôt que Random Forest ou XGBoost ?**

> "Extra Trees a donné le meilleur F1-macro sur la validation. Contrairement au Random Forest, Extra Trees utilise des seuils de split totalement aléatoires (pas optimisés) → moins de variance, meilleure généralisation sur ce type de données tabulaires bruitées. On n'a pas testé XGBoost/LightGBM dans cette version."

---

**Q : Est-ce que vous avez utilisé Swagger pour tester l'API ?**

> "FastAPI génère automatiquement une interface Swagger sur `/docs`. On a utilisé cette interface pour tester chaque endpoint manuellement. On n'a pas configuré de tests d'API automatisés (ex: pytest avec httpx)."

---

**Q : Depuis quel fichier l'interface prend ses données ?**

> "L'interface ne lit pas de fichiers directement. Elle fait des requêtes HTTP vers l'API FastAPI (`http://127.0.0.1:8000`). C'est l'API qui lit les fichiers : le modèle `.joblib`, `matches_clean.csv`, `champion_probabilities.csv`, `model_metrics.csv`. Tout passe par l'API."

---

**Q : Pourquoi 49% d'accuracy et pas 75% ?**

> "C'est un problème difficile à 3 classes (H/D/A) avec seulement des données historiques. Un modèle naïf qui prédit toujours 'victoire domicile' ferait déjà 44%. Pour dépasser 70%, il faudrait des données exogènes : cotes bookmakers, blessures, effectifs confirmés, xG en temps réel. Ces données ne sont pas disponibles gratuitement."

---

**Q : Comment fonctionne le ELO ?**

> "C'est un système de rating emprunté aux échecs. Chaque équipe commence à 1500. Après un match, on calcule le résultat attendu (selon l'écart d'ELO) et on ajuste : `elo_nouveau = elo_ancien + 20 × (résultat_réel − résultat_attendu)`. Une victoire surprise face à une meilleure équipe rapporte plus de points ELO qu'une victoire attendue. On ajoute +60 points d'avantage domicile."

---

**Q : Comment fonctionne la simulation Monte Carlo ?**

> "Pour la saison en cours, on sait quels matchs ont déjà été joués. Pour les matchs restants, on calcule des probabilités avec notre moteur ELO + forme + points/match, et on tire un résultat aléatoire (H/D/A). On répète ça 300 fois. Chaque équipe reçoit comme probabilité de titre : `nombre de fois où elle finit 1ère / 300 simulations`."

---

**Q : Vous avez des tests unitaires ?**

> "Oui — 4 fichiers dans `tests/` : `test_features.py`, `test_preprocessing.py`, `test_models.py`, `test_pipeline.py`. On teste le calcul ELO, l'imputation, le pipeline sklearn complet, et la détection de fuite de données. On lance avec `pytest tests/`."

---

**Q : Comment vous assurez l'absence de fuite de données ?**

> "Deux mécanismes : (1) Dans le feature engineering, on prend le snapshot AVANT le match et on met à jour l'état APRÈS — donc le modèle ne voit jamais le résultat futur. (2) Le split train/validation/test est temporel strict : le test = la dernière saison complète, jamais un split aléatoire. On a même un module `preprocessing/leakage_check.py` qui valide automatiquement ces contraintes."
