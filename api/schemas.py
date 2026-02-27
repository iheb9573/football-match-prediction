from __future__ import annotations

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    league_code: str = Field(..., examples=["EPL"])
    home_team: str
    away_team: str
    match_date: str | None = Field(default=None, description="Optional YYYY-MM-DD")


class PredictResponse(BaseModel):
    league_code: str
    season_start_year_context: int
    match_date: str
    home_team: str
    away_team: str
    predicted_class: str
    predicted_label: str
    confidence: float
    probabilities: dict[str, float]
    top_explanations: list[dict[str, str | float]]


class DashboardPredictRequest(BaseModel):
    league_code: str = Field(..., examples=["EPL"])
    home_team: str
    away_team: str
    match_date: str | None = Field(default=None, description="Optional YYYY-MM-DD")
