# 🔧 SOLUTIONS AUX PROBLÈMES IDENTIFIÉS

## Problèmes Rencontrés

### ❌ Erreur 1 : ImportError: cannot import name 'run_full_pipeline'
```
ImportError: cannot import name 'run_full_pipeline' from 'football_bi.pipeline'
```

**Cause :** Collision entre deux éléments du même nom :
- Fichier : `src/football_bi/pipeline.py` (contient `run_full_pipeline()`)
- Répertoire : `src/football_bi/pipeline/` (package avec `__init__.py`)

Quand Python importe `from football_bi.pipeline import X`, il préfère le **répertoire** au **fichier**.

**✅ Solution Appliquée :**
- Modifié `code/08_run_all.py` pour utiliser `importlib.util` et charger le module `pipeline.py` directement
- Bypass intelligent de la collision de noms

---

### ❌ Erreur 2 : ModuleNotFoundError: No module named 'fastapi'
```
ModuleNotFoundError: No module named 'fastapi'
```

**Cause :** Les packages requis ne sont pas installés dans l'environnement virtuel

**✅ Solution :**
Installer toutes les dépendances :
```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**PowerShell execution policy :** Si vous avez une erreur de policy PowerShell, utilisez le batch script à la place

---

## 🚀 Étapes pour Exécuter le Pipeline

### **Méthode 1 : Batch Script (Plus Simple)**
```bash
run_pipeline.bat
```
Cela va :
1. Installer les dépendances
2. Exécuter le pipeline avec 300 simulations
3. Générer all résultats

---

### **Méthode 2 : PowerShell Script**
```bash
.\run_pipeline.ps1 -Simulations 300
```

---

### **Méthode 3 : Commands Manuelles**

#### Étape 1 : Installer les dépendances
```bash
cd "d:\TEK-UP University\ING-4-J-SDIA-F-A\semestre2\Projet BI-IA\football-match-prediction"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

#### Étape 2 : Exécuter le pipeline complet
```bash
.\.venv\Scripts\python.exe code/08_run_all.py --simulations 300
```

#### Ou : Exécuter étape par étape
```bash
.\.venv\Scripts\python.exe code/01_data_ingestion.py
.\.venv\Scripts\python.exe code/02_data_preprocessing.py
.\.venv\Scripts\python.exe code/03_feature_engineering.py
.\.venv\Scripts\python.exe code/04_eda_visualization.py
.\.venv\Scripts\python.exe code/05_model_training.py
.\.venv\Scripts\python.exe code/06_model_explainability.py
.\.venv\Scripts\python.exe code/07_competition_simulation.py --simulations 300
```

---

## 📊 Résultats Attendus

Après exécution, vérifiez :

```
reports/football_bi/
├── model_metrics.csv                    ✅ Accuracies & F1 scores
├── test_predictions.csv                 ✅ Prédictions détaillées
├── classification_report_test.txt       ✅ Rapport complet
├── permutation_importance.csv           ✅ Feature importance
├── champion_probabilities.csv           ✅ Prob. pour chaque ligue
└── figures/
    ├── confusion_matrix_*.png
    ├── permutation_importance_top20.png
    └── champion_probability_*.png

models/football_bi/
├── match_outcome_model.joblib           ✅ Modèle entraîné
└── match_outcome_model_metadata.json    ✅ Métadonnées
```

---

## 🖥️ Visualiser les Résultats

### Via API + Dashboard
```bash
# Terminal 1 : Lancer l'API
.\.venv\Scripts\python.exe code/09_run_api.py
# → API sur http://127.0.0.1:8000

# Terminal 2 : Frontend (optionnel)
cd interface/b_65PkRuwmNDh-1771889902461
npm install
npm run dev
# → Interface sur http://127.0.0.1:3000
```

### Via CSV Reports
- Ouvrez `reports/football_bi/model_metrics.csv` avec Excel/Pandas
- Ouvrez les images PNG : `reports/football_bi/figures/`

---

## 📈 Métriques de Référence

| Métrique | Baseline (ET) | Après Tuning | Avec Ensemble |
|----------|--------------|--------------|---------------|
| Accuracy | **49.5%** | ~52-55% | ~54-56% |
| F1 Macro | **47%** | ~50% | ~51% |
| LogLoss | **1.02** | ~0.98 | ~0.95 |

**Note :** Ces sont des estimations. Les vraies valeurs dépendent des données.

---

## 🔍 Fichiers Modifiés pour Résoudre les Problèmes

### 1. `code/08_run_all.py`
✅ **Changement :** Import intelligent de `run_full_pipeline` via `importlib`
→ Contourne la collision entre `pipeline.py` et `pipeline/`

### 2. `QUICK_START.md`
✅ **Nouveau :** Guide rapide pour l'utilisateur

### 3. `run_pipeline.bat`
✅ **Nouveau :** Script Windows pour exécution automatique

### 4. `run_pipeline.ps1`
✅ **Nouveau :** Script PowerShell (bypass policy issues)

### 5. `TROUBLESHOOTING.md` (ce fichier)
✅ **Nouveau :** Documentation des problèmes et solutions

---

## ✅ Checklist Avant d'Exécuter

- [ ] Venv activé (`.venv/Scripts/python.exe` existe)
- [ ] `requirements.txt` présent à la racine
- [ ] ~2 GB libre sur disque (pour data processed + models)
- [ ] Connexion internet (pour la première exécution si données manquantes)

---

## 💡 Dépannage Avancé

### "Cannot find pipeline module"
→ Vérifiez que vous êtes dans le bon répertoire:
```bash
cd "d:\TEK-UP University\ING-4-J-SDIA-F-A\semestre2\Projet BI-IA\football-match-prediction"
```

### "Pandas/Numpy/Sklearn not found"
→ Réinstallez avec force:
```bash
.\.venv\Scripts\python.exe -m pip install --force-reinstall pandas scikit-learn numpy
```

### "No space left on device"
→ Le dataset est volumineux, vérifiez l'espace disque:
```bash
# PowerShell:
Get-Volume C | Select-Object SizeRemaining
```

---

## 📞 Next Steps

1. ✅ Exécuter le pipeline avec l'une des méthodes ci-dessus
2. ✅ Vérifier les résultats dans `reports/football_bi/`
3. ✅ Lancer l'API avec `code/09_run_api.py`
4. ✅ Explorer le dashboard frontend
5. 📚 Lire `docs/ARCHITECTURE.md` pour plus de détails

**Bonne chance ! 🚀**
