# Guide d'Intégration : Connecter Votre Modèle Python ML

Ce guide vous explique comment connecter votre modèle de machine learning Python à l'interface Football BI Predictor.

## 🎯 Architecture de Communication

```
┌─────────────────┐                        ┌─────────────────┐
│  React Frontend │  ←─ fetch JSON ─→     │  Python API     │
│  (localhost:3000)                        │  (localhost:8000)
└─────────────────┘                        └─────────────────┘
                                                     ↓
                                            ┌─────────────────┐
                                            │  Modèle ML      │
                                            │  (XGBoost, etc) │
                                            └─────────────────┘
                                                     ↓
                                            ┌─────────────────┐
                                            │  Base de Données│
                                            │  (Matchs, Stats)│
                                            └─────────────────┘
```

## 📦 Étape 1 : Installer les Dépendances Python

Créez un fichier `requirements.txt` dans votre projet Python :

```
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
pydantic==2.4.2
cors==1.0.1
```

Installez-les :

```bash
pip install -r requirements.txt
```

## 🚀 Étape 2 : Créer Votre API FastAPI

Créez un fichier `main.py` (ou `app.py`) :

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from datetime import datetime, timedelta
from pydantic import BaseModel

app = FastAPI(
    title="Football BI Predictor API",
    description="API ML pour prédictions de football",
    version="1.0.0"
)

# Configurer CORS pour permettre les requêtes du frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Votre frontend React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import de votre modèle ML
# from football_predictor import FootballPredictorModel
# model = FootballPredictorModel()

# ==================== PRÉDICTIONS ====================

class PredictionResponse(BaseModel):
    id: int
    match: dict
    probabilities: dict
    prediction: str
    confidence: float
    xG_home: float
    xG_away: float
    features: dict

@app.get("/api/predictions")
def get_predictions():
    """
    Retourne les prédictions pour les matchs à venir.
    
    Doit appeler votre modèle ML pour générer les prédictions.
    """
    
    # Exemple : faire appel à votre modèle ML
    # predictions = model.predict_upcoming_matches()
    
    # Données mockées pour l'exemple
    predictions = [
        {
            "id": 1,
            "match": {
                "date": (datetime.now() + timedelta(days=1)).isoformat() + "Z",
                "homeTeam": "Paris Saint-Germain",
                "awayTeam": "Lyon",
                "league": "Ligue 1",
                "stadium": "Parc des Princes"
            },
            "probabilities": {
                "home": 0.58,
                "draw": 0.26,
                "away": 0.16
            },
            "prediction": "H",
            "confidence": 0.85,
            "xG_home": 2.1,
            "xG_away": 0.8,
            "features": {
                "homeFormRating": 4.2,
                "awayFormRating": 2.8,
                "homeAttack": 8.5,
                "homeDefense": 7.2,
                "awayAttack": 6.1,
                "awayDefense": 6.8,
                "headToHead": "PSG leads 15-3"
            }
        }
    ]
    
    return predictions


@app.post("/api/predictions/analyze")
def analyze_match(homeTeam: str, awayTeam: str, league: str):
    """
    Analyse un match spécifique et retourne les prédictions détaillées.
    
    Corps de la requête:
    {
        "homeTeam": "Paris Saint-Germain",
        "awayTeam": "Lyon",
        "league": "Ligue 1"
    }
    """
    
    # Appel à votre modèle ML
    # prediction = model.predict_match(homeTeam, awayTeam, league)
    
    return {
        "message": f"Analyse de {homeTeam} vs {awayTeam}",
        "status": "processing"
    }


# ==================== STATISTIQUES ====================

@app.get("/api/statistics")
def get_statistics():
    """
    Retourne les statistiques et performances du modèle.
    """
    
    statistics = {
        "accuracyByLeague": [
            {"league": "Ligue 1", "accuracy": 0.72, "matches": 380},
            {"league": "Premier League", "accuracy": 0.68, "matches": 380},
            {"league": "La Liga", "accuracy": 0.71, "matches": 380},
            {"league": "Serie A", "accuracy": 0.69, "matches": 380},
            {"league": "Bundesliga", "accuracy": 0.74, "matches": 306}
        ],
        "predictionDistribution": [
            {"type": "Home Win", "percentage": 46},
            {"type": "Draw", "percentage": 27},
            {"type": "Away Win", "percentage": 27}
        ],
        "confidenceAnalysis": [
            {"confidenceRange": "90-100%", "count": 45, "accuracy": 0.89},
            {"confidenceRange": "80-89%", "count": 120, "accuracy": 0.82},
            {"confidenceRange": "70-79%", "count": 180, "accuracy": 0.74},
            {"confidenceRange": "60-69%", "count": 150, "accuracy": 0.62},
            {"confidenceRange": "<60%", "count": 105, "accuracy": 0.48}
        ],
        "modelPerformance": {
            "precision": 0.78,
            "recall": 0.72,
            "f1Score": 0.75,
            "auc_roc": 0.81
        },
        "topFeatures": [
            {"feature": "Home Team Form (Last 5)", "importance": 0.18},
            {"feature": "xG Difference", "importance": 0.16},
            {"feature": "Team Strength Rating", "importance": 0.14},
            {"feature": "Head to Head History", "importance": 0.12},
            {"feature": "Recent Injuries", "importance": 0.11},
            {"feature": "Home Advantage", "importance": 0.10},
            {"feature": "Weather Conditions", "importance": 0.08},
            {"feature": "Motivation Factor", "importance": 0.06},
            {"feature": "Player Fatigue Index", "importance": 0.05}
        ],
        "leagueStats": [
            {"league": "Ligue 1", "totalMatches": 380, "avgGoals": 2.78, "avgOdds": 2.15},
            {"league": "Premier League", "totalMatches": 380, "avgGoals": 2.89, "avgOdds": 2.12},
            {"league": "La Liga", "totalMatches": 380, "avgGoals": 2.82, "avgOdds": 2.18},
            {"league": "Serie A", "totalMatches": 380, "avgGoals": 2.61, "avgOdds": 2.22},
            {"league": "Bundesliga", "totalMatches": 306, "avgGoals": 3.12, "avgOdds": 2.08}
        ]
    }
    
    return statistics


@app.get("/api/statistics/model-metrics")
def get_model_metrics():
    """
    Retourne les métriques détaillées du modèle.
    """
    
    # Récupérez ces métriques depuis votre modèle ML
    # from sklearn.metrics import precision_score, recall_score, f1_score
    
    return {
        "precision": 0.78,
        "recall": 0.72,
        "f1_score": 0.75,
        "auc_roc": 0.81,
        "confusion_matrix": {
            "true_positives": 234,
            "false_positives": 45,
            "true_negatives": 198,
            "false_negatives": 56
        }
    }


# ==================== SIMULATIONS ====================

@app.get("/api/simulations")
def get_simulations():
    """
    Retourne les simulations Monte Carlo du championnat.
    """
    
    simulations = {
        "championshipWinners": [
            {"team": "Manchester City", "probability": 0.28, "simulations": 280000},
            {"team": "Real Madrid", "probability": 0.18, "simulations": 180000},
            {"team": "Bayern Munich", "probability": 0.15, "simulations": 150000},
            {"team": "PSG", "probability": 0.12, "simulations": 120000},
            {"team": "Arsenal", "probability": 0.10, "simulations": 100000},
            {"team": "Barcelona", "probability": 0.08, "simulations": 80000},
            {"team": "Others", "probability": 0.09, "simulations": 90000}
        ],
        "topFourProbabilities": [
            {"team": "Manchester City", "topFour": 0.89},
            {"team": "Real Madrid", "topFour": 0.82},
            {"team": "Bayern Munich", "topFour": 0.78},
            {"team": "PSG", "topFour": 0.75},
            {"team": "Arsenal", "topFour": 0.72},
            {"team": "Barcelona", "topFour": 0.68}
        ],
        "seasonTrends": [
            {"week": 1, "leader": "Manchester City", "leadProb": 0.22},
            {"week": 5, "leader": "Manchester City", "leadProb": 0.25},
            {"week": 10, "leader": "Arsenal", "leadProb": 0.24},
            {"week": 15, "leader": "Manchester City", "leadProb": 0.26},
            {"week": 20, "leader": "Manchester City", "leadProb": 0.28},
            {"week": 25, "leader": "Real Madrid", "leadProb": 0.27},
            {"week": 30, "leader": "Manchester City", "leadProb": 0.29},
            {"week": 34, "leader": "Manchester City", "leadProb": 0.30}
        ]
    }
    
    return simulations


@app.post("/api/simulations/run")
def run_simulations(league: str, n_simulations: int = 100000):
    """
    Lance une nouvelle simulation Monte Carlo.
    
    Paramètres:
    - league: La ligue (ex: "Ligue 1")
    - n_simulations: Nombre de simulations à exécuter
    """
    
    # Appelez votre simulateur Monte Carlo
    # results = monte_carlo_simulator.run(league, n_simulations)
    
    return {
        "status": "running",
        "league": league,
        "n_simulations": n_simulations,
        "message": f"Simulation lancée avec {n_simulations} itérations"
    }


# ==================== ENDPOINTS UTILITAIRES ====================

@app.get("/health")
def health_check():
    """Vérification de santé de l'API."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/")
def root():
    """Documentation de l'API."""
    return {
        "message": "Football BI Predictor API",
        "version": "1.0.0",
        "docs": "http://localhost:8000/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
