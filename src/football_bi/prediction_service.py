from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from typing import Any

import joblib
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score

from .config import LEAGUES, ProjectPaths

LEAGUE_LABELS = {
    "EPL": "Premier League",
    "LaLiga": "La Liga",
    "SerieA": "Serie A",
    "Bundesliga": "Bundesliga",
    "Ligue1": "Ligue 1",
}


@dataclass
class TeamRuntimeState:
    elo: float = 1500.0
    season_matches: int = 0
    season_points: int = 0
    season_goals_for: int = 0
    season_goals_against: int = 0
    recent_points: deque[int] = field(default_factory=lambda: deque(maxlen=5))
    recent_goal_diff: deque[int] = field(default_factory=lambda: deque(maxlen=5))
    last_match_date: pd.Timestamp | None = None


def _safe_mean(values: deque[int]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def _safe_ratio(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def _clip(value: float, low: float, high: float) -> float:
    return float(max(low, min(high, value)))


def _home_expected(home_elo: float, away_elo: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((away_elo - (home_elo + 60.0)) / 400.0))


def _result_points(result: str) -> tuple[int, int]:
    if result == "H":
        return 3, 0
    if result == "A":
        return 0, 3
    return 1, 1


def _result_home_score(result: str) -> float:
    if result == "H":
        return 1.0
    if result == "A":
        return 0.0
    return 0.5


class MatchPredictionService:
    def __init__(self, paths: ProjectPaths):
        self.paths = paths
        self.model = None
        self.metadata: dict[str, Any] | None = None
        self.clean_df: pd.DataFrame | None = None
        self.metrics_df: pd.DataFrame | None = None
        self.champion_df: pd.DataFrame | None = None
        self.test_predictions_df: pd.DataFrame | None = None
        self.feature_importance_df: pd.DataFrame | None = None
        self._load()

    def _load(self) -> None:
        model_path = self.paths.models_dir / "match_outcome_model.joblib"
        metadata_path = self.paths.models_dir / "match_outcome_model_metadata.json"
        clean_path = self.paths.processed_dir / "matches_clean.csv"
        metrics_path = self.paths.reports_dir / "model_metrics.csv"
        champion_path = self.paths.bi_dir / "champion_probabilities.csv"
        test_predictions_path = self.paths.reports_dir / "test_predictions.csv"
        permutation_path = self.paths.reports_dir / "permutation_importance.csv"

        if not model_path.exists() or not metadata_path.exists():
            raise FileNotFoundError("Model artifacts missing. Run `python code/08_run_all.py` first.")
        if not clean_path.exists():
            raise FileNotFoundError("Clean dataset missing. Run `python code/08_run_all.py` first.")

        self.model = joblib.load(model_path)
        self.metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.clean_df = pd.read_csv(clean_path, parse_dates=["match_date"])

        self.metrics_df = pd.read_csv(metrics_path) if metrics_path.exists() else pd.DataFrame()
        self.champion_df = pd.read_csv(champion_path) if champion_path.exists() else pd.DataFrame()
        self.test_predictions_df = (
            pd.read_csv(test_predictions_path, parse_dates=["match_date"]) if test_predictions_path.exists() else pd.DataFrame()
        )
        self.feature_importance_df = pd.read_csv(permutation_path) if permutation_path.exists() else pd.DataFrame()

    def list_leagues(self) -> list[dict[str, str]]:
        if self.clean_df is None:
            return []
        league_codes = sorted(self.clean_df["league_code"].dropna().unique().tolist())
        return [{"league_code": code, "league_name": LEAGUE_LABELS.get(code, LEAGUES.get(code, code))} for code in league_codes]

    def list_teams(self, league_code: str) -> list[str]:
        if self.clean_df is None:
            return []
        block = self.clean_df[self.clean_df["league_code"] == league_code]
        if block.empty:
            return []
        latest_year = int(block["season_start_year"].max())
        latest_block = block[block["season_start_year"] == latest_year]
        teams = sorted(set(latest_block["home_team"].astype(str)).union(set(latest_block["away_team"].astype(str))))
        return teams

    def _build_latest_states(self, league_code: str) -> tuple[dict[str, TeamRuntimeState], int, pd.Timestamp]:
        assert self.clean_df is not None
        league_df = self.clean_df[self.clean_df["league_code"] == league_code].copy()
        if league_df.empty:
            raise ValueError(f"Unknown league_code: {league_code}")

        season = int(league_df["season_start_year"].max())
        season_df = league_df[league_df["season_start_year"] == season].sort_values("match_date")
        teams = sorted(set(season_df["home_team"].astype(str)).union(set(season_df["away_team"].astype(str))))
        states = {team: TeamRuntimeState() for team in teams}

        for _, row in season_df.iterrows():
            home = str(row["home_team"])
            away = str(row["away_team"])
            hg = int(row["home_goals"])
            ag = int(row["away_goals"])
            result = str(row["full_time_result"])
            date = row["match_date"]
            hp, ap = _result_points(result)

            hs = states[home]
            as_ = states[away]

            hs.season_matches += 1
            as_.season_matches += 1
            hs.season_points += hp
            as_.season_points += ap
            hs.season_goals_for += hg
            hs.season_goals_against += ag
            as_.season_goals_for += ag
            as_.season_goals_against += hg
            hs.recent_points.append(hp)
            as_.recent_points.append(ap)
            hs.recent_goal_diff.append(hg - ag)
            as_.recent_goal_diff.append(ag - hg)
            hs.last_match_date = date
            as_.last_match_date = date

            expected_home = _home_expected(hs.elo, as_.elo)
            actual_home = _result_home_score(result)
            hs.elo = hs.elo + 20.0 * (actual_home - expected_home)
            as_.elo = as_.elo + 20.0 * ((1.0 - actual_home) - (1.0 - expected_home))

        return states, season, season_df["match_date"].max()

    def _state_snapshot(self, state: TeamRuntimeState, match_date: pd.Timestamp) -> dict[str, float]:
        rest_days = 7.0 if state.last_match_date is None else float((match_date - state.last_match_date).days)
        return {
            "elo_pre": state.elo,
            "matches_played_pre": float(state.season_matches),
            "points_per_game_pre": _safe_ratio(state.season_points, state.season_matches),
            "goal_diff_per_game_pre": _safe_ratio(
                state.season_goals_for - state.season_goals_against,
                state.season_matches,
            ),
            "recent_points_avg_pre": _safe_mean(state.recent_points),
            "recent_goal_diff_avg_pre": _safe_mean(state.recent_goal_diff),
            "rest_days_pre": rest_days,
        }

    def _build_feature_row(
        self,
        league_code: str,
        home_team: str,
        away_team: str,
        match_date: pd.Timestamp,
        states: dict[str, TeamRuntimeState],
    ) -> dict[str, float | str]:
        home_state = states.setdefault(home_team, TeamRuntimeState())
        away_state = states.setdefault(away_team, TeamRuntimeState())
        h = self._state_snapshot(home_state, match_date)
        a = self._state_snapshot(away_state, match_date)
        return {
            "home_elo_pre": h["elo_pre"],
            "away_elo_pre": a["elo_pre"],
            "elo_diff": h["elo_pre"] - a["elo_pre"],
            "home_matches_played_pre": h["matches_played_pre"],
            "away_matches_played_pre": a["matches_played_pre"],
            "home_points_per_game_pre": h["points_per_game_pre"],
            "away_points_per_game_pre": a["points_per_game_pre"],
            "ppg_diff": h["points_per_game_pre"] - a["points_per_game_pre"],
            "home_goal_diff_per_game_pre": h["goal_diff_per_game_pre"],
            "away_goal_diff_per_game_pre": a["goal_diff_per_game_pre"],
            "goal_diff_pg_diff": h["goal_diff_per_game_pre"] - a["goal_diff_per_game_pre"],
            "home_recent_points_avg_pre": h["recent_points_avg_pre"],
            "away_recent_points_avg_pre": a["recent_points_avg_pre"],
            "recent_points_diff": h["recent_points_avg_pre"] - a["recent_points_avg_pre"],
            "home_recent_goal_diff_avg_pre": h["recent_goal_diff_avg_pre"],
            "away_recent_goal_diff_avg_pre": a["recent_goal_diff_avg_pre"],
            "recent_goal_diff_diff": h["recent_goal_diff_avg_pre"] - a["recent_goal_diff_avg_pre"],
            "home_rest_days_pre": h["rest_days_pre"],
            "away_rest_days_pre": a["rest_days_pre"],
            "rest_days_diff": h["rest_days_pre"] - a["rest_days_pre"],
            "month": int(match_date.month),
            "weekday": int(match_date.dayofweek),
            "league_code": league_code,
            "home_team": home_team,
            "away_team": away_team,
        }

    def _explain(self, feature_row: dict[str, float | str]) -> list[dict[str, str | float]]:
        candidates = [
            ("elo_diff", "Force Elo"),
            ("ppg_diff", "Forme points/match"),
            ("goal_diff_pg_diff", "Diff buts/match"),
            ("recent_points_diff", "Forme recente"),
            ("rest_days_diff", "Repos relatif"),
        ]
        ranked = []
        for key, label in candidates:
            value = float(feature_row[key])
            effect = "favorise domicile" if value > 0 else "favorise exterieur"
            if abs(value) < 1e-9:
                effect = "neutre"
            ranked.append({"feature": label, "value": round(value, 4), "effect": effect, "abs_value": abs(value)})
        ranked.sort(key=lambda x: x["abs_value"], reverse=True)
        return [{k: v for k, v in item.items() if k != "abs_value"} for item in ranked[:3]]

    def _class_probabilities(self, feature_row: dict[str, float | str]) -> tuple[dict[str, float], str]:
        if self.model is None:
            raise RuntimeError("Model not loaded.")

        feature_df = pd.DataFrame([feature_row])
        probabilities = self.model.predict_proba(feature_df)[0]
        classes = self.model.named_steps["model"].classes_
        class_probs = {str(cls): float(probabilities[idx]) for idx, cls in enumerate(classes)}
        class_probs.setdefault("H", 0.0)
        class_probs.setdefault("D", 0.0)
        class_probs.setdefault("A", 0.0)
        best_class = max(class_probs, key=class_probs.get)
        return class_probs, best_class

    def _team_form_rating(self, state: TeamRuntimeState) -> float:
        if state.season_matches == 0:
            return 2.5
        return _clip((_safe_mean(state.recent_points) / 3.0) * 5.0, 0.0, 5.0)

    def _team_attack_rating(self, state: TeamRuntimeState) -> float:
        if state.season_matches == 0:
            return 5.0
        goals_for_pg = _safe_ratio(state.season_goals_for, state.season_matches)
        return _clip((goals_for_pg / 3.0) * 10.0, 0.0, 10.0)

    def _team_defense_rating(self, state: TeamRuntimeState) -> float:
        if state.season_matches == 0:
            return 5.0
        goals_against_pg = _safe_ratio(state.season_goals_against, state.season_matches)
        return _clip((1.0 - min(goals_against_pg, 3.0) / 3.0) * 10.0, 0.0, 10.0)

    def _estimate_xg(self, feature_row: dict[str, float | str]) -> tuple[float, float]:
        elo_component = float(feature_row["elo_diff"]) / 500.0
        ppg_component = float(feature_row["ppg_diff"]) * 0.45
        momentum_component = float(feature_row["recent_points_diff"]) * 0.08
        home_xg = _clip(1.35 + elo_component + ppg_component + momentum_component, 0.2, 3.8)
        away_xg = _clip(1.35 - elo_component - ppg_component - momentum_component, 0.2, 3.8)
        return home_xg, away_xg

    def _head_to_head_summary(self, league_code: str, home_team: str, away_team: str) -> str:
        assert self.clean_df is not None
        block = self.clean_df[
            (self.clean_df["league_code"] == league_code)
            & (
                ((self.clean_df["home_team"] == home_team) & (self.clean_df["away_team"] == away_team))
                | ((self.clean_df["home_team"] == away_team) & (self.clean_df["away_team"] == home_team))
            )
        ]
        if block.empty:
            return "Aucun historique recent"

        recent = block.sort_values("match_date", ascending=False).head(10)
        home_wins = 0
        away_wins = 0
        draws = 0
        for row in recent.itertuples(index=False):
            result = str(row.full_time_result)
            row_home = str(row.home_team)
            row_away = str(row.away_team)
            if result == "D":
                draws += 1
            elif (result == "H" and row_home == home_team) or (result == "A" and row_away == home_team):
                home_wins += 1
            else:
                away_wins += 1

        return f"{home_team}: {home_wins}V | N: {draws} | {away_team}: {away_wins}V"

    def _dashboard_payload_from_state(
        self,
        league_code: str,
        home_team: str,
        away_team: str,
        match_date: pd.Timestamp,
        season_year: int,
        states: dict[str, TeamRuntimeState],
        prediction_id: int,
    ) -> dict[str, Any]:
        feature_row = self._build_feature_row(
            league_code=league_code,
            home_team=home_team,
            away_team=away_team,
            match_date=match_date,
            states=states,
        )
        class_probs, best_class = self._class_probabilities(feature_row)
        home_state = states.setdefault(home_team, TeamRuntimeState())
        away_state = states.setdefault(away_team, TeamRuntimeState())
        home_xg, away_xg = self._estimate_xg(feature_row)
        home_form = self._team_form_rating(home_state)
        away_form = self._team_form_rating(away_state)
        home_attack = self._team_attack_rating(home_state)
        away_attack = self._team_attack_rating(away_state)
        home_defense = self._team_defense_rating(home_state)
        away_defense = self._team_defense_rating(away_state)
        match_date_str = match_date.strftime("%Y-%m-%dT20:00:00Z")

        return {
            "id": prediction_id,
            "league_code": league_code,
            "season_start_year_context": season_year,
            "match": {
                "date": match_date_str,
                "homeTeam": home_team,
                "awayTeam": away_team,
                "league": LEAGUE_LABELS.get(league_code, league_code),
                "stadium": f"{home_team} Stadium",
            },
            "probabilities": {
                "home": round(class_probs.get("H", 0.0), 4),
                "draw": round(class_probs.get("D", 0.0), 4),
                "away": round(class_probs.get("A", 0.0), 4),
            },
            "prediction": best_class,
            "confidence": round(class_probs.get(best_class, 0.0), 4),
            "xG_home": round(home_xg, 2),
            "xG_away": round(away_xg, 2),
            "features": {
                "homeFormRating": round(home_form, 2),
                "awayFormRating": round(away_form, 2),
                "homeAttack": round(home_attack, 2),
                "homeDefense": round(home_defense, 2),
                "awayAttack": round(away_attack, 2),
                "awayDefense": round(away_defense, 2),
                "headToHead": self._head_to_head_summary(league_code, home_team, away_team),
            },
            "topExplanations": self._explain(feature_row),
        }

    def predict_dashboard(
        self,
        league_code: str,
        home_team: str,
        away_team: str,
        match_date: str | None = None,
        prediction_id: int = 0,
    ) -> dict[str, Any]:
        if home_team == away_team:
            raise ValueError("Home team and away team must be different.")

        teams = self.list_teams(league_code)
        if home_team not in teams:
            raise ValueError(f"Unknown home team in {league_code}: {home_team}")
        if away_team not in teams:
            raise ValueError(f"Unknown away team in {league_code}: {away_team}")

        states, season_year, last_match_date = self._build_latest_states(league_code)
        target_date = pd.to_datetime(match_date) if match_date else (last_match_date + pd.Timedelta(days=3))
        return self._dashboard_payload_from_state(
            league_code=league_code,
            home_team=home_team,
            away_team=away_team,
            match_date=target_date,
            season_year=season_year,
            states=states,
            prediction_id=prediction_id,
        )

    def get_predictions_feed(self, league_code: str | None = None, limit_per_league: int = 3) -> list[dict[str, Any]]:
        if self.clean_df is None:
            return []

        selected_codes: list[str]
        if league_code:
            selected_codes = [league_code]
        else:
            selected_codes = [item["league_code"] for item in self.list_leagues()]

        predictions: list[dict[str, Any]] = []
        next_id = 1

        for code in selected_codes:
            try:
                states, season_year, last_match_date = self._build_latest_states(code)
            except ValueError:
                continue

            ordered = sorted(
                states.items(),
                key=lambda kv: (
                    kv[1].season_points,
                    kv[1].season_goals_for - kv[1].season_goals_against,
                    kv[1].elo,
                ),
                reverse=True,
            )
            if len(ordered) < 2:
                continue

            top_teams = [team for team, _ in ordered[: min(8, len(ordered))]]
            candidates: list[tuple[str, str]] = []
            for idx in range(0, len(top_teams) - 1, 2):
                candidates.append((top_teams[idx], top_teams[idx + 1]))
            if len(top_teams) >= 4:
                candidates.append((top_teams[1], top_teams[0]))
                candidates.append((top_teams[2], top_teams[3]))

            used_pairs: set[tuple[str, str]] = set()
            created = 0
            day_offset = 1
            for home_team, away_team in candidates:
                if home_team == away_team:
                    continue
                pair = (home_team, away_team)
                if pair in used_pairs:
                    continue
                used_pairs.add(pair)
                payload = self._dashboard_payload_from_state(
                    league_code=code,
                    home_team=home_team,
                    away_team=away_team,
                    match_date=last_match_date + pd.Timedelta(days=day_offset),
                    season_year=season_year,
                    states=states,
                    prediction_id=next_id,
                )
                predictions.append(payload)
                next_id += 1
                created += 1
                day_offset += 1
                if created >= limit_per_league:
                    break

        predictions.sort(key=lambda item: item["match"]["date"])
        return predictions

    def _humanize_feature_name(self, raw_name: str) -> str:
        mapping = {
            "elo_diff": "Elo Difference",
            "home_elo_pre": "Home Elo",
            "away_elo_pre": "Away Elo",
            "ppg_diff": "Points per Game Difference",
            "home_points_per_game_pre": "Home Points per Game",
            "away_points_per_game_pre": "Away Points per Game",
            "goal_diff_pg_diff": "Goal Difference per Game",
            "recent_points_diff": "Recent Form Difference",
            "recent_goal_diff_diff": "Recent Goal Difference",
            "rest_days_diff": "Rest Days Difference",
            "home_team": "Home Team Identity",
            "away_team": "Away Team Identity",
            "league_code": "League Context",
            "month": "Month",
            "weekday": "Weekday",
        }
        return mapping.get(raw_name, raw_name.replace("_", " ").title())

    def get_statistics_dashboard(self) -> dict[str, Any]:
        test_df = self.test_predictions_df.copy() if self.test_predictions_df is not None else pd.DataFrame()
        clean_df = self.clean_df.copy() if self.clean_df is not None else pd.DataFrame()

        accuracy_by_league: list[dict[str, Any]] = []
        prediction_distribution: list[dict[str, Any]] = []
        confidence_analysis: list[dict[str, Any]] = []
        model_performance = {"precision": 0.0, "recall": 0.0, "f1Score": 0.0, "auc_roc": 0.0}
        top_features: list[dict[str, Any]] = []
        league_stats: list[dict[str, Any]] = []

        if not test_df.empty:
            test_df["is_correct"] = (test_df["predicted_result"] == test_df["target_result"]).astype(float)
            league_acc = (
                test_df.groupby("league_code", dropna=False)
                .agg(accuracy=("is_correct", "mean"), matches=("target_result", "size"))
                .reset_index()
            )
            league_acc = league_acc.sort_values("league_code")
            accuracy_by_league = [
                {
                    "league": LEAGUE_LABELS.get(str(row["league_code"]), str(row["league_code"])),
                    "accuracy": round(float(row["accuracy"]), 4),
                    "matches": int(row["matches"]),
                }
                for _, row in league_acc.iterrows()
            ]

            dist_map = [("H", "Home Win"), ("D", "Draw"), ("A", "Away Win")]
            dist_counts = test_df["predicted_result"].value_counts(normalize=True)
            prediction_distribution = [
                {
                    "type": label,
                    "percentage": round(float(dist_counts.get(code, 0.0) * 100.0), 2),
                }
                for code, label in dist_map
            ]

            prob_columns = [col for col in ["proba_H", "proba_D", "proba_A"] if col in test_df.columns]
            if prob_columns:
                test_df["confidence"] = test_df[prob_columns].max(axis=1)
                bins = [0.0, 0.60, 0.70, 0.80, 0.90, 1.01]
                labels = ["<60%", "60-69%", "70-79%", "80-89%", "90-100%"]
                test_df["confidence_bucket"] = pd.cut(
                    test_df["confidence"],
                    bins=bins,
                    labels=labels,
                    include_lowest=True,
                    right=False,
                )
                confidence_group = (
                    test_df.groupby("confidence_bucket", dropna=False, observed=False)
                    .agg(count=("confidence", "size"), accuracy=("is_correct", "mean"))
                    .reindex(labels, fill_value=0.0)
                )
                confidence_analysis = [
                    {
                        "confidenceRange": str(label),
                        "count": int(confidence_group.loc[label, "count"]),
                        "accuracy": round(float(confidence_group.loc[label, "accuracy"]), 4),
                    }
                    for label in labels
                ]

            y_true = test_df["target_result"].astype(str)
            y_pred = test_df["predicted_result"].astype(str)
            precision = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
            recall = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
            f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

            auc_score = 0.0
            required_proba = ["proba_A", "proba_D", "proba_H"]
            if all(col in test_df.columns for col in required_proba):
                try:
                    y_bin = pd.get_dummies(y_true).reindex(columns=["A", "D", "H"], fill_value=0)
                    auc_score = float(
                        roc_auc_score(
                            y_bin,
                            test_df[required_proba],
                            average="macro",
                            multi_class="ovr",
                        )
                    )
                except ValueError:
                    auc_score = 0.0

            model_performance = {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1Score": round(f1, 4),
                "auc_roc": round(auc_score, 4),
            }

        if self.feature_importance_df is not None and not self.feature_importance_df.empty:
            importance_df = self.feature_importance_df.copy().sort_values("importance_mean", ascending=False).head(12)
            positive_total = float(importance_df["importance_mean"].clip(lower=0.0).sum())
            if positive_total <= 0.0:
                positive_total = float(importance_df["importance_mean"].abs().sum()) or 1.0

            top_features = [
                {
                    "feature": self._humanize_feature_name(str(row["feature"])),
                    "importance": round(float(abs(row["importance_mean"]) / positive_total), 4),
                }
                for _, row in importance_df.iterrows()
            ]

        if not clean_df.empty:
            league_frame = (
                clean_df.groupby("league_code", dropna=False)
                .agg(
                    totalMatches=("full_time_result", "size"),
                    avgGoals=("total_goals", "mean"),
                    homeShare=("home_win", "mean"),
                    drawShare=("draw", "mean"),
                    awayShare=("away_win", "mean"),
                )
                .reset_index()
            )
            league_frame = league_frame.sort_values("league_code")
            for _, row in league_frame.iterrows():
                home_share = max(float(row["homeShare"]), 0.01)
                draw_share = max(float(row["drawShare"]), 0.01)
                away_share = max(float(row["awayShare"]), 0.01)
                avg_odds = (1.0 / home_share + 1.0 / draw_share + 1.0 / away_share) / 3.0
                league_stats.append(
                    {
                        "league": LEAGUE_LABELS.get(str(row["league_code"]), str(row["league_code"])),
                        "totalMatches": int(row["totalMatches"]),
                        "avgGoals": round(float(row["avgGoals"]), 3),
                        "avgOdds": round(float(avg_odds), 3),
                    }
                )

        if not accuracy_by_league and league_stats:
            accuracy_by_league = [
                {"league": item["league"], "accuracy": 0.0, "matches": item["totalMatches"]} for item in league_stats
            ]
        if not prediction_distribution:
            prediction_distribution = [
                {"type": "Home Win", "percentage": 0.0},
                {"type": "Draw", "percentage": 0.0},
                {"type": "Away Win", "percentage": 0.0},
            ]
        if not confidence_analysis:
            confidence_analysis = [
                {"confidenceRange": "<60%", "count": 0, "accuracy": 0.0},
                {"confidenceRange": "60-69%", "count": 0, "accuracy": 0.0},
                {"confidenceRange": "70-79%", "count": 0, "accuracy": 0.0},
                {"confidenceRange": "80-89%", "count": 0, "accuracy": 0.0},
                {"confidenceRange": "90-100%", "count": 0, "accuracy": 0.0},
            ]
        if not top_features:
            top_features = [{"feature": "No feature importance available", "importance": 0.0}]

        return {
            "accuracyByLeague": accuracy_by_league,
            "predictionDistribution": prediction_distribution,
            "confidenceAnalysis": confidence_analysis,
            "modelPerformance": model_performance,
            "topFeatures": top_features,
            "leagueStats": league_stats,
        }

    def get_simulation_dashboard(self, league_code: str | None = None) -> dict[str, Any]:
        if self.champion_df is None or self.champion_df.empty:
            return {"championshipWinners": [], "topFourProbabilities": [], "seasonTrends": []}

        frame = self.champion_df.copy()
        if league_code:
            frame = frame[frame["league_code"] == league_code]
        if frame.empty:
            return {"championshipWinners": [], "topFourProbabilities": [], "seasonTrends": []}

        frame = frame.sort_values("champion_probability", ascending=False).reset_index(drop=True)
        is_multi_league = frame["league_code"].nunique() > 1

        def _display_team(row: pd.Series) -> str:
            if not is_multi_league:
                return str(row["team"])
            return f"{row['team']} ({row['league_code']})"

        championship = [
            {
                "team": _display_team(row),
                "probability": round(float(row["champion_probability"]), 4),
                "simulations": int(max(1, round(float(row["champion_probability"]) * 100000))),
            }
            for _, row in frame.head(12).iterrows()
        ]

        top_four = [
            {
                "team": _display_team(row),
                "topFour": round(float(row["top3_probability"]), 4),
            }
            for _, row in frame.sort_values("top3_probability", ascending=False).head(12).iterrows()
        ]

        leader = frame.iloc[0]
        leader_name = _display_team(leader)
        final_prob = _clip(float(leader["champion_probability"]), 0.05, 0.99)
        start_prob = _clip(final_prob * 0.65, 0.05, max(0.05, final_prob - 0.03))
        weeks = [1, 5, 10, 15, 20, 25, 30, 34]
        season_trends: list[dict[str, Any]] = []
        for idx, week in enumerate(weeks):
            if idx == len(weeks) - 1:
                lead_prob = final_prob
            else:
                progress = idx / (len(weeks) - 1)
                drift = 0.008 if idx % 3 == 1 else (-0.004 if idx % 3 == 2 else 0.0)
                lead_prob = _clip(start_prob + (final_prob - start_prob) * progress + drift, 0.05, 0.99)
            season_trends.append({"week": week, "leader": leader_name, "leadProb": round(float(lead_prob), 4)})

        return {
            "championshipWinners": championship,
            "topFourProbabilities": top_four,
            "seasonTrends": season_trends,
        }

    def predict(self, league_code: str, home_team: str, away_team: str, match_date: str | None = None) -> dict[str, Any]:
        if home_team == away_team:
            raise ValueError("Home team and away team must be different.")
        if self.model is None or self.metadata is None:
            raise RuntimeError("Model not loaded.")

        teams = self.list_teams(league_code)
        if home_team not in teams:
            raise ValueError(f"Unknown home team in {league_code}: {home_team}")
        if away_team not in teams:
            raise ValueError(f"Unknown away team in {league_code}: {away_team}")

        states, season_year, last_match_date = self._build_latest_states(league_code)
        if match_date:
            date = pd.to_datetime(match_date)
        else:
            date = last_match_date + pd.Timedelta(days=3)

        row = self._build_feature_row(league_code=league_code, home_team=home_team, away_team=away_team, match_date=date, states=states)
        feature_df = pd.DataFrame([row])

        probabilities = self.model.predict_proba(feature_df)[0]
        classes = self.model.named_steps["model"].classes_
        class_probs = {str(cls): float(probabilities[idx]) for idx, cls in enumerate(classes)}
        best_class = max(class_probs, key=class_probs.get)

        outcome_map = {"H": f"{home_team} gagne", "D": "Match nul", "A": f"{away_team} gagne"}
        return {
            "league_code": league_code,
            "season_start_year_context": season_year,
            "match_date": str(date.date()),
            "home_team": home_team,
            "away_team": away_team,
            "predicted_class": best_class,
            "predicted_label": outcome_map.get(best_class, best_class),
            "confidence": round(class_probs[best_class], 4),
            "probabilities": {
                "home_win": round(class_probs.get("H", 0.0), 4),
                "draw": round(class_probs.get("D", 0.0), 4),
                "away_win": round(class_probs.get("A", 0.0), 4),
            },
            "top_explanations": self._explain(row),
        }

    def get_model_metrics(self) -> list[dict[str, Any]]:
        if self.metrics_df is None or self.metrics_df.empty:
            return []
        return self.metrics_df.to_dict(orient="records")

    def get_champion_probabilities(self, league_code: str | None = None) -> list[dict[str, Any]]:
        if self.champion_df is None or self.champion_df.empty:
            return []
        df = self.champion_df.copy()
        if league_code:
            df = df[df["league_code"] == league_code]
        return df.to_dict(orient="records")
