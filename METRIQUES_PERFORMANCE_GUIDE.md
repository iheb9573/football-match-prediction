# Guide: Source des Métriques de Performance du Modèle

## 📊 Résumé

Les métriques de performance (Precision, Rappel, F1 Score, AUC-ROC) affichées dans l'interface web à `http://127.0.0.1:3000/` proviennent d'un fichier CSV généré lors de l'entraînement du modèle.

---

## 🔄 Flux de Données

```
test_predictions.csv
        ↓
prediction_service.py (méthode: get_statistics_dashboard)
        ↓
API FastAPI: /api/statistics (port 8000)
        ↓
Interface React (Next.js, port 3000)
        ↓
Affichage dans le Dashboard
```

---

## 📁 Fichiers Clés

### 1. **Source des Données: test_predictions.csv**
- **Chemin**: `reports/football_bi/test_predictions.csv`
- **Créé par**: Script d'entraînement (`code/05_model_training.py`)
- **Contenu**: Prédictions du modèle sur l'ensemble de test
- **Colonnes importantes**:
  - `target_result`: Résultat réel (H/D/A)
  - `predicted_result`: Résultat prédit (H/D/A)
  - `proba_H`, `proba_D`, `proba_A`: Probabilités pour chaque classe

### 2. **Calcul des Métriques: Backend**

#### Fichier: `src/football_bi/prediction_service.py`
**Méthode**: `get_statistics_dashboard()` (ligne 485)

```python
# Les métriques sont calculées ainsi:
precision = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
recall = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
auc_score = float(roc_auc_score(y_bin, proba, average="macro", multi_class="ovr"))
```

**Résultat retourné**:
```json
{
  "modelPerformance": {
    "precision": 0.xx,
    "recall": 0.xx,
    "f1Score": 0.xx,
    "auc_roc": 0.xx
  }
}
```

### 3. **Endpoint API**

#### Fichier: `api/main.py` (ligne 114)
```python
@app.get("/api/statistics")
def dashboard_statistics() -> dict[str, object]:
    return _svc().get_statistics_dashboard()
```

### 4. **Affichage Frontend**

#### Fichier: `interface/b_65PkRuwmNDh-1771889902461/lib/statistics.ts`
- **Type DefautType**: `StatisticsPayload`
- **Normalisation**: `normalizeStatistics()` convertit les données de l'API

#### Fichier: `interface/b_65PkRuwmNDh-1771889902461/components/stats-overview.tsx`
- Affiche les 4 métriques en pourcentage:
  - Precision: `(stats.modelPerformance.precision * 100).toFixed(1)}%`
  - Rappel: `(stats.modelPerformance.recall * 100).toFixed(1)}%`
  - F1 Score: `(stats.modelPerformance.f1Score * 100).toFixed(1)}%`
  - AUC-ROC: `(stats.modelPerformance.auc_roc * 100).toFixed(1)}%`

---

## 🤔 Utilisation de l'Historique des Joueurs

### **NON, l'historique des joueurs n'est PAS utilisé directement**

#### Ce qui EST utilisé (Team-level features):
```python
NUMERIC_FEATURES = [
    "home_elo_pre",          # Rating ELO du domicile
    "away_elo_pre",          # Rating ELO de l'extérieur
    "home_matches_played_pre",  # Matchs joués par l'équipe
    "away_matches_played_pre",
    "home_points_per_game_pre", # Points par match de l'équipe
    "away_points_per_game_pre",
    "home_recent_points_avg_pre", # Moyenne sur les 5 derniers matchs
    "away_recent_points_avg_pre",
    "home_rest_days_pre",    # Jours de repos avant le match
    "away_rest_days_pre",
    # ... autres features d'équipe
]

CATEGORICAL_FEATURES = [
    "league_code",
    "home_team",
    "away_team"
]
```

#### Historique des joueurs:
- **Collecté**: `data/Scrapping/flashScore/flashscore_scraper_v21.py` (profile joueurs, blessures)
- **Stocké dans**: `ml_pipeline_output/profiles_clean.csv`, `injuries_clean.csv`
- **Utilisé pour**: Contexte d'analyse (pas utilisé directement dans le modèle)

---

## ✏️ Comment Modifier les Métriques Affichées

### Option 1: Modifier le fichier CSV source
1. Ouvrir: `reports/football_bi/test_predictions.csv`
2. Les métriques seront recalculées automatiquement au prochain redémarrage de l'API

### Option 2: Modifier directement l'API
1. Fichier: `src/football_bi/prediction_service.py`
2. Modifier la méthode `get_statistics_dashboard()` (ligne 485-490)
3. Exemple:
```python
model_performance = {
    "precision": 0.85,  # Valeur hardcodée pour test
    "recall": 0.82,
    "f1Score": 0.83,
    "auc_roc": 0.88,
}
```

### Option 3: Modifier au niveau du Frontend (NOT RECOMMENDED)
1. Fichier: `interface/b_65PkRuwmNDh-1771889902461/lib/statistics.ts`
2. Modifier `EMPTY_STATISTICS` ou `normalizeStatistics()`

---

## 🔍 Debugging

### Pour vérifier les vraies valeurs:
1. Accès direct à l'API:
```bash
curl http://127.0.0.1:8000/api/statistics
```

2. Vérifier le fichier CSV:
```bash
head -5 reports/football_bi/test_predictions.csv
```

3. Vérifier les logs FastAPI dans le terminal

---

## 📈 Améliorer les Performances Réelles

Pour améliorer les VRAIES métriques (pas seulement les afficher):

1. **Entraîner le modèle avec plus de données**
   ```bash
   python code/08_run_all.py
   ```

2. **Utiliser l'historique des joueurs dans une v2**
   - Ajouter des features basées sur les blessures
   - Intégrer les ratings individuels des joueurs
   - Créer des agrégations au niveau des joueurs

3. **Optimiser les hyperparamètres**
   - Modifier `config/models.yaml`
   - Utiliser GridSearch pour le tuning

---

## 📋 Résumé des Fichiers à Modifier

| Fichier | Ligne | Action |
|---------|-------|--------|
| `test_predictions.csv` | N/A | ✏️ Éditer directement pour tester |
| `src/football_bi/prediction_service.py` | 485-490 | 🔧 Modifier le calcul/sortie |
| `api/main.py` | 114 | 🔧 Modifier l'endpoint |
| `interface/.../statistics.ts` | 102-105 | 🔧 Modifier la normalisation |
| `interface/.../stats-overview.tsx` | 30-33 | 🎨 Modifier l'affichage |

---

## ⚠️ Points Importants

1. **Les métriques sont calculées à chaque démarrage de l'API**
2. **Elles proviennent uniquement du fichier `test_predictions.csv`**
3. **L'historique des joueurs n'est pas encore intégré au modèle principal**
4. **Les modifications au frontend n'affectent que l'affichage, pas les vraies valeurs**

