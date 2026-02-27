# Cahier des charges - Football BI Predictor

## 1. Contexte
Projet academique de Data Science / BI pour predire le resultat des matchs et estimer, de maniere probabiliste, les chances de titre par equipe.

## 2. Objectif principal
Fournir une solution complete de Business Intelligence pour predire, de maniere probabiliste et explicable, l'equipe ayant le plus de chances de remporter la competition.

## 3. Perimetre
### Inclus
- Ingestion de donnees historiques (5 ligues europeennes)
- Preprocessing (types, valeurs manquantes, qualite)
- Feature engineering pre-match (sans fuite de donnees)
- EDA avec visualisations BI
- Entrainement d'un modele probabiliste multi-classes (H / D / A)
- Explainability globale du modele
- Simulation Monte Carlo des probabilites champion
- Documentation et scripts d'execution

### Non inclus
- Donnees live minute par minute
- Integration betting odds en temps reel
- MLOps de production cloud (option extension)

## 4. Ligues cibles
```python
LEAGUES = {
    "EPL": "english-premier-league",
    "LaLiga": "spanish-la-liga",
    "SerieA": "italian-serie-a",
    "Bundesliga": "german-bundesliga",
    "Ligue1": "french-ligue-1",
}
```

## 5. Methodologie
1. Setup dossier projet
2. Ingestion
3. Preprocessing
4. Feature engineering
5. EDA/BI
6. Model training
7. Explainability
8. Simulation champion

## 6. Metriques
### Prediction match
- Accuracy
- F1 Macro
- Log Loss
- Matrice de confusion

### Simulation champion
- Probabilite champion par equipe
- Probabilite Top 3
- Points attendus

## 7. Livrables
- Scripts numerotes dans `code/`
- Modules reutilisables dans `src/football_bi/`
- Datasets preprocesses dans `data/processed/football_bi/`
- Rapports BI dans `reports/football_bi/`
- Modele sauvegarde dans `models/football_bi/`
- README projet complet

## 8. Criteres de qualite
- Code propre, modulaire, documente
- Pipeline reproductible de bout en bout
- Sorties explicables et exploitables par metier
