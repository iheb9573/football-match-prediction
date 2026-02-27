from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from football_bi.config import get_default_paths
from football_bi.prediction_service import MatchPredictionService

from .schemas import DashboardPredictRequest, PredictRequest, PredictResponse


app = FastAPI(
    title="Football BI Predictor API",
    version="1.0.0",
    description="API for probabilistic match prediction and champion BI dashboards.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service: MatchPredictionService | None = None


@app.on_event("startup")
def _startup() -> None:
    global service
    paths = get_default_paths()
    try:
        service = MatchPredictionService(paths)
    except Exception as exc:  # pragma: no cover
        service = None
        app.state.startup_error = str(exc)


def _svc() -> MatchPredictionService:
    global service
    if service is None:
        msg = getattr(app.state, "startup_error", "Service not initialized.")
        raise HTTPException(status_code=503, detail=msg)
    return service


@app.get("/health")
def health() -> dict[str, str]:
    if service is None:
        msg = getattr(app.state, "startup_error", "Service not initialized.")
        return {"status": "error", "detail": msg}
    return {"status": "ok"}


@app.get("/api/leagues")
def list_leagues() -> dict[str, object]:
    return {"items": _svc().list_leagues()}


@app.get("/api/teams/{league_code}")
def list_teams(league_code: str) -> dict[str, object]:
    return {"items": _svc().list_teams(league_code)}


@app.get("/api/predictions")
def dashboard_predictions(
    league_code: str | None = Query(default=None),
    limit_per_league: int = Query(default=3, ge=1, le=10),
) -> list[dict[str, object]]:
    return _svc().get_predictions_feed(league_code=league_code, limit_per_league=limit_per_league)


@app.post("/api/predictions/analyze")
def analyze_prediction(payload: DashboardPredictRequest) -> dict[str, object]:
    try:
        return _svc().predict_dashboard(
            league_code=payload.league_code,
            home_team=payload.home_team,
            away_team=payload.away_team,
            match_date=payload.match_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/predict", response_model=PredictResponse)
def predict_match(payload: PredictRequest) -> PredictResponse:
    try:
        result = _svc().predict(
            league_code=payload.league_code,
            home_team=payload.home_team,
            away_team=payload.away_team,
            match_date=payload.match_date,
        )
        return PredictResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/statistics")
def dashboard_statistics() -> dict[str, object]:
    return _svc().get_statistics_dashboard()


@app.get("/api/simulations")
def dashboard_simulations(league_code: str | None = Query(default=None)) -> dict[str, object]:
    return _svc().get_simulation_dashboard(league_code=league_code)


@app.get("/api/dashboard/model-metrics")
def model_metrics() -> dict[str, object]:
    return {"items": _svc().get_model_metrics()}


@app.get("/api/dashboard/champion-probabilities")
def champion_probabilities(league_code: str | None = Query(default=None)) -> dict[str, object]:
    return {"items": _svc().get_champion_probabilities(league_code)}
