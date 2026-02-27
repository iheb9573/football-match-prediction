from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import pandas as pd


K_FACTOR = 20
HOME_ELO_ADVANTAGE = 60


@dataclass
class TeamState:
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


def _safe_ppg(points: int, matches: int) -> float:
    return float(points / matches) if matches else 0.0


def _safe_gdpg(goals_for: int, goals_against: int, matches: int) -> float:
    return float((goals_for - goals_against) / matches) if matches else 0.0


def _rest_days(state: TeamState, match_date: pd.Timestamp) -> float:
    if state.last_match_date is None:
        return 7.0
    return float((match_date - state.last_match_date).days)


def _home_expected_score(home_elo: float, away_elo: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((away_elo - (home_elo + HOME_ELO_ADVANTAGE)) / 400.0))


def _result_to_points(result: str) -> tuple[int, int]:
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


def _reset_for_new_season(state: TeamState) -> None:
    state.elo = 0.75 * state.elo + 0.25 * 1500.0
    state.season_matches = 0
    state.season_points = 0
    state.season_goals_for = 0
    state.season_goals_against = 0
    state.recent_points.clear()
    state.recent_goal_diff.clear()
    state.last_match_date = None


def _snapshot(state: TeamState, match_date: pd.Timestamp) -> dict[str, float]:
    return {
        "elo_pre": state.elo,
        "matches_played_pre": float(state.season_matches),
        "points_per_game_pre": _safe_ppg(state.season_points, state.season_matches),
        "goal_diff_per_game_pre": _safe_gdpg(state.season_goals_for, state.season_goals_against, state.season_matches),
        "recent_points_avg_pre": _safe_mean(state.recent_points),
        "recent_goal_diff_avg_pre": _safe_mean(state.recent_goal_diff),
        "rest_days_pre": _rest_days(state, match_date),
    }


def build_match_features(df_clean: pd.DataFrame) -> pd.DataFrame:
    df = df_clean.sort_values(["league_code", "season_start_year", "match_date", "home_team"], kind="stable").copy()
    all_rows: list[dict[str, float | str | int | pd.Timestamp]] = []

    for league_code, league_df in df.groupby("league_code", sort=True):
        league_states: dict[str, TeamState] = {}
        current_season: str | None = None

        for _, row in league_df.iterrows():
            season_code = str(row["season_code"])
            if season_code != current_season:
                for state in league_states.values():
                    _reset_for_new_season(state)
                current_season = season_code

            home_team = str(row["home_team"])
            away_team = str(row["away_team"])
            match_date = row["match_date"]

            home_state = league_states.setdefault(home_team, TeamState())
            away_state = league_states.setdefault(away_team, TeamState())

            home = _snapshot(home_state, match_date)
            away = _snapshot(away_state, match_date)

            out = {
                "league_code": league_code,
                "league_name": row["league_name"],
                "season_code": season_code,
                "season_start_year": int(row["season_start_year"]),
                "match_date": match_date,
                "home_team": home_team,
                "away_team": away_team,
                "target_result": row["full_time_result"],
                "home_goals_actual": float(row["home_goals"]),
                "away_goals_actual": float(row["away_goals"]),
                "total_goals_actual": float(row["total_goals"]),
                "home_elo_pre": home["elo_pre"],
                "away_elo_pre": away["elo_pre"],
                "elo_diff": home["elo_pre"] - away["elo_pre"],
                "home_matches_played_pre": home["matches_played_pre"],
                "away_matches_played_pre": away["matches_played_pre"],
                "home_points_per_game_pre": home["points_per_game_pre"],
                "away_points_per_game_pre": away["points_per_game_pre"],
                "ppg_diff": home["points_per_game_pre"] - away["points_per_game_pre"],
                "home_goal_diff_per_game_pre": home["goal_diff_per_game_pre"],
                "away_goal_diff_per_game_pre": away["goal_diff_per_game_pre"],
                "goal_diff_pg_diff": home["goal_diff_per_game_pre"] - away["goal_diff_per_game_pre"],
                "home_recent_points_avg_pre": home["recent_points_avg_pre"],
                "away_recent_points_avg_pre": away["recent_points_avg_pre"],
                "recent_points_diff": home["recent_points_avg_pre"] - away["recent_points_avg_pre"],
                "home_recent_goal_diff_avg_pre": home["recent_goal_diff_avg_pre"],
                "away_recent_goal_diff_avg_pre": away["recent_goal_diff_avg_pre"],
                "recent_goal_diff_diff": home["recent_goal_diff_avg_pre"] - away["recent_goal_diff_avg_pre"],
                "home_rest_days_pre": home["rest_days_pre"],
                "away_rest_days_pre": away["rest_days_pre"],
                "rest_days_diff": home["rest_days_pre"] - away["rest_days_pre"],
                "month": int(match_date.month),
                "weekday": int(match_date.dayofweek),
            }
            all_rows.append(out)

            home_points, away_points = _result_to_points(str(row["full_time_result"]))
            home_g = int(row["home_goals"])
            away_g = int(row["away_goals"])

            home_state.season_matches += 1
            away_state.season_matches += 1
            home_state.season_points += home_points
            away_state.season_points += away_points
            home_state.season_goals_for += home_g
            home_state.season_goals_against += away_g
            away_state.season_goals_for += away_g
            away_state.season_goals_against += home_g

            home_state.recent_points.append(home_points)
            away_state.recent_points.append(away_points)
            home_state.recent_goal_diff.append(home_g - away_g)
            away_state.recent_goal_diff.append(away_g - home_g)

            home_state.last_match_date = match_date
            away_state.last_match_date = match_date

            expected_home = _home_expected_score(home_state.elo, away_state.elo)
            actual_home = _result_home_score(str(row["full_time_result"]))
            home_state.elo = home_state.elo + K_FACTOR * (actual_home - expected_home)
            away_state.elo = away_state.elo + K_FACTOR * ((1.0 - actual_home) - (1.0 - expected_home))

    features_df = pd.DataFrame(all_rows)
    features_df = features_df.sort_values(["league_code", "season_start_year", "match_date", "home_team"], kind="stable")
    features_df.reset_index(drop=True, inplace=True)
    return features_df
