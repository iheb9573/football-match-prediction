# ✅ CHECKLIST - Football Match Prediction Setup

## 🎯 Avant de Démarrer

- [ ] Vous êtes dans le répertoire du projet
- [ ] `.venv` (environnement virtuel) existe
- [ ] `requirements.txt` est présent
- [ ] ~2 GB libre sur disque (pour données + modèles)

---

## 🚀 ÉTAPE 1 : Exécuter le Pipeline

### Choix 1️⃣ : Auto-Setup (RECOMMANDÉ - Une seule commande)

```bash
.venv\Scripts\python.exe setup_and_run.py
```

**Durée attendue :** 15-30 minutes
**Quoi :** Installe les packages + injecte le pipeline

Attendez la fin (vous verrez "✅ SETUP COMPLETE")

---

### Choix 2️⃣ : Batch Script

```bash
run_pipeline.bat
```

**Durée attendue :** 15-30 minutes

---

### Choix 3️⃣ : Manuellement

```bash
# D'abord : installer les packages
.venv\Scripts\python.exe -m pip install -r requirements.txt

# Puis : exécuter le pipeline
.venv\Scripts\python.exe code/08_run_all.py --simulations 300
```

**Durée pour pip :** 3-10 minutes (une seule fois)
**Durée pipeline :** 15-30 minutes

---

## 📊 ÉTAPE 2 : Vérifier les Résultats

Après exécution, ouvrez :

### Fichier 1 : Accuracy du Modèle
```
reports/football_bi/model_metrics.csv
```
**Quoi :** Accuracy, F1, LogLoss du meilleur modèle
**Ouvrir avec :** Excel, Pandas, ou Notepad

### Fichier 2 : Prédictions Détaillées
```
reports/football_bi/test_predictions.csv
```
**Quoi :** 7000+ prédictions par match avec probabilités

### Dossier 3 : Visualisations
```
reports/football_bi/figures/
```
**Quoi :** Graphiques PNG (confusion matrix, importance des features, etc.)

### Dossier 4 : Modèle Entraîné
```
models/football_bi/match_outcome_model.joblib
```
**Quoi :** Modèle sérialisé prêt pour les prédictions

---

## 🖥️ ÉTAPE 3 : Visualiser le Dashboard (Optionnel)

### Via API FastAPI
```bash
.venv\Scripts\python.exe code/09_run_api.py
```

Puis ouvrez : **http://127.0.0.1:8000**

Les endpoints disponibles :
- `GET /api/leagues` - Lister les ligues
- `GET /api/teams/{league}` - Équipes par ligue  
- `POST /api/predict` - Prédire un match
- `GET /api/dashboard/model-metrics` - Métriques
- `GET /api/dashboard/champion-probabilities` - Probabilités champion

---

## 📚 ÉTAPE 4 : Comprendre les Résultats

### Si accuracy est ~50% (normal)
✅ Cela signifie que le modèle fonctionne!
- Baseline obtenu : 49.5%
- C'est un problème difficile (3 classes sans données en temps réel)
- Les cotes de bookmakers sont nécessaires pour aller >60%

### Si vous voyez F1-Macro ~47%
✅ Normal aussi - F1 non-pondéré sur 3 classes déséquilibrées

### Fichiers clés à consulter
- `reports/football_bi/eda_summary.md` - EDA détaillée
- `reports/football_bi/explainability_summary.md` - Feature importance
- `reports/football_bi/bi/champion_probabilities.md` - Probabilités par ligue

---

## 🔧 Dépannage Rapide

| Problème | Solution |
|----------|----------|
| "No module named X" | `pip install -r requirements.txt` |
| "Cannot find pipeline" | Vérifiez que vous êtes au bon endroit |
| "Execution policy error" | Utilisez `.bat` ou `setup_and_run.py` |
| "Disk full" | Besoin de 2GB pour données + modèles |
| Pipeline très lent | Normal (quelques GB de données) |

---

## 📊 Résumé des Résultats Attendus

```
MODÈLE : Extra Trees (sélectionné après tuning)
DONNÉES : 58,467 matchs (1993-2026)
FEATURES : 40 (Elo, rolling stats, player features, etc.)

PERFORMANCE TEST SET :
├─ Accuracy : ~50%
├─ F1 Macro : ~47%
├─ LogLoss  : ~1.02
└─ Temps exec : 15-30 min

FICHIERS GÉNÉRÉS :
├─ Model : models/football_bi/
├─ Reports : reports/football_bi/
├─ Figures : reports/football_bi/figures/
└─ Logs : logs/
```

---

## ✨ Prochaines Étapes (Après le Pipeline)

1. **Lire les résultats** - Ouvrir `model_metrics.csv`
2. **Voir les visualisations** - `figures/*.png`
3. **Comprendre le modèle** - `docs/ARCHITECTURE.md`
4. **Lancer le dashboard** - `code/09_run_api.py`
5. **Améliorer le modèle** (optionnel)
   - Ajouter des features
   - Tester d'autres modèles
   - Intégrer les données en temps réel

---

## 🎓 Documentation Complète

| Fichier | Durée Lecture | Contenu |
|---------|---------------|---------|
| `EXECUTE_NOW.md` | 2 min | Vue générale (LISEZ CEA D'ABORD!) |
| `QUICK_START.md` | 5 min | Guide d'exécution rapide |
| `SOLUTIONS.md` | 5 min | Explication des corrections |
| `TROUBLESHOOTING.md` | 10 min | FAQ & dépannage avancé |
| `docs/ARCHITECTURE.md` | 30 min | Architecture technique détaillée |
| `tutos/02_PIPELINE_USAGE.md` | 20 min | Guide complet du pipeline |

---

## 🚀 MAINTENANT, ALLEZ-Y!

```bash
.venv\Scripts\python.exe setup_and_run.py
```

**Patience !** ⏳ Cela dure 15-30 minutes mais vous aurez:
- ✅ Un modèle ML entraîné et évalué
- ✅ 50 résultats (accuracy, F1, etc.)
- ✅ Prédictions détaillées pour 7000+ matchs  
- ✅ Visualisations et explainabilité
- ✅ Un API prêt à utiliser
- ✅ Un dashboard interactive

**Aucune autre configuration n'est nécessaire. C'est clé en main! 🎯**
