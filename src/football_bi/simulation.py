from __future__ import annotations

import copy
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import ProjectPaths
from .features import HOME_ELO_ADVANTAGE, K_FACTOR


@dataclass
class SimTeamState:
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


def _expected_home(home_elo: float, away_elo: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((away_elo - (home_elo + HOME_ELO_ADVANTAGE)) / 400.0))


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


def _snapshot(state: SimTeamState, match_date: pd.Timestamp) -> dict[str, float]:
    rest_days = 7.0 if state.last_match_date is None else float((match_date - state.last_match_date).days)
    return {
        "elo_pre": state.elo,
        "matches_played_pre": float(state.season_matches),
        "points_per_game_pre": _safe_ppg(state.season_points, state.season_matches),
        "goal_diff_per_game_pre": _safe_gdpg(state.season_goals_for, state.season_goals_against, state.season_matches),
        "recent_points_avg_pre": _safe_mean(state.recent_points),
        "recent_goal_diff_avg_pre": _safe_mean(state.recent_goal_diff),
        "rest_days_pre": rest_days,
    }


def _update_state(state: SimTeamState, match_date: pd.Timestamp, gf: int, ga: int, points: int) -> None:
    state.season_matches += 1
    state.season_points += points
    state.season_goals_for += gf
    state.season_goals_against += ga
    state.recent_points.append(points)
    state.recent_goal_diff.append(gf - ga)
    state.last_match_date = match_date


def _update_elo(home_state: SimTeamState, away_state: SimTeamState, result: str) -> None:
    expected_home = _expected_home(home_state.elo, away_state.elo)
    actual_home = _result_home_score(result)
    home_state.elo = home_state.elo + K_FACTOR * (actual_home - expected_home)
    away_state.elo = away_state.elo + K_FACTOR * ((1.0 - actual_home) - (1.0 - expected_home))


def _init_state_and_table(season_df: pd.DataFrame) -> tuple[dict[str, SimTeamState], dict[str, dict[str, float]]]:
    teams = sorted(set(season_df["home_team"]).union(set(season_df["away_team"])))
    states = {team: SimTeamState() for team in teams}
    table = {team: {"points": 0, "gf": 0, "ga": 0, "gd": 0, "played": 0} for team in teams}

    for _, row in season_df.sort_values("match_date").iterrows():
        home = row["home_team"]
        away = row["away_team"]
        result = row["full_time_result"]
        hg = int(row["home_goals"])
        ag = int(row["away_goals"])
        match_date = row["match_date"]
        hp, ap = _result_points(result)

        _update_state(states[home], match_date, hg, ag, hp)
        _update_state(states[away], match_date, ag, hg, ap)
        _update_elo(states[home], states[away], result)

        table[home]["points"] += hp
        table[away]["points"] += ap
        table[home]["gf"] += hg
        table[home]["ga"] += ag
        table[away]["gf"] += ag
        table[away]["ga"] += hg
        table[home]["gd"] = table[home]["gf"] - table[home]["ga"]
        table[away]["gd"] = table[away]["gf"] - table[away]["ga"]
        table[home]["played"] += 1
        table[away]["played"] += 1

    return states, table


def _build_feature_row(
    league_code: str,
    home_team: str,
    away_team: str,
    match_date: pd.Timestamp,
    states: dict[str, SimTeamState],
) -> dict[str, float | str]:
    home = _snapshot(states[home_team], match_date)
    away = _snapshot(states[away_team], match_date)
    return {
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
        "league_code": league_code,
        "home_team": home_team,
        "away_team": away_team,
    }


def _sample_score(result: str) -> tuple[int, int]:
    # Lightweight score proxy used only for standings tie-break updates.
    if result == "H":
        return 2, 1
    if result == "A":
        return 1, 2
    return 1, 1


def _heuristic_probabilities(home_state: SimTeamState, away_state: SimTeamState) -> dict[str, float]:
    home_ppg = _safe_ppg(home_state.season_points, home_state.season_matches)
    away_ppg = _safe_ppg(away_state.season_points, away_state.season_matches)
    home_form = _safe_mean(home_state.recent_points)
    away_form = _safe_mean(away_state.recent_points)
    home_rest = 7.0 if home_state.last_match_date is None else 5.0
    away_rest = 7.0 if away_state.last_match_date is None else 5.0

    score = (
        0.0028 * (home_state.elo - away_state.elo)
        + 0.85 * (home_ppg - away_ppg)
        + 0.25 * (home_form - away_form)
        + 0.02 * (home_rest - away_rest)
    )
    p_home_raw = 1.0 / (1.0 + np.exp(-score))
    p_draw = max(0.14, 0.26 - 0.08 * abs(score))
    p_home = p_home_raw * (1.0 - p_draw)
    p_away = (1.0 - p_home_raw) * (1.0 - p_draw)

    total = p_home + p_draw + p_away
    return {"H": p_home / total, "D": p_draw / total, "A": p_away / total}


def _league_simulation(
    season_df: pd.DataFrame,
    n_simulations: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    league_code = str(season_df["league_code"].iloc[0])
    teams = sorted(set(season_df["home_team"]).union(set(season_df["away_team"])))

    played = {(str(r["home_team"]), str(r["away_team"])) for _, r in season_df.iterrows()}
    all_fixtures = [(h, a) for h in teams for a in teams if h != a]
    remaining = [fx for fx in all_fixtures if fx not in played]

    base_states, base_table = _init_state_and_table(season_df)
    last_date = season_df["match_date"].max()

    champion_count = {team: 0 for team in teams}
    top3_count = {team: 0 for team in teams}
    points_sum = {team: 0.0 for team in teams}

    for _ in range(n_simulations):
        states = copy.deepcopy(base_states)
        table = copy.deepcopy(base_table)
        fixtures = remaining.copy()
        rng.shuffle(fixtures)
        current_date = last_date + pd.Timedelta(days=2)

        for home, away in fixtures:
            _ = _build_feature_row(league_code=league_code, home_team=home, away_team=away, match_date=current_date, states=states)
            probs = _heuristic_probabilities(states[home], states[away])
            result = rng.choice(["H", "D", "A"], p=[probs["H"], probs["D"], probs["A"]])

            home_points, away_points = _result_points(result)
            hg, ag = _sample_score(result)

            _update_state(states[home], current_date, hg, ag, home_points)
            _update_state(states[away], current_date, ag, hg, away_points)
            _update_elo(states[home], states[away], result)

            table[home]["points"] += home_points
            table[away]["points"] += away_points
            table[home]["gf"] += hg
            table[home]["ga"] += ag
            table[away]["gf"] += ag
            table[away]["ga"] += hg
            table[home]["gd"] = table[home]["gf"] - table[home]["ga"]
            table[away]["gd"] = table[away]["gf"] - table[away]["ga"]
            table[home]["played"] += 1
            table[away]["played"] += 1
            current_date += pd.Timedelta(days=2)

        ranking = sorted(
            teams,
            key=lambda t: (table[t]["points"], table[t]["gd"], table[t]["gf"]),
            reverse=True,
        )
        champion = ranking[0]
        champion_count[champion] += 1
        for team in ranking[:3]:
            top3_count[team] += 1
        for team in teams:
            points_sum[team] += table[team]["points"]

    rows = []
    for team in teams:
        rows.append(
            {
                "league_code": league_code,
                "team": team,
                "champion_probability": champion_count[team] / n_simulations,
                "top3_probability": top3_count[team] / n_simulations,
                "expected_points": points_sum[team] / n_simulations,
            }
        )
    return pd.DataFrame(rows).sort_values("champion_probability", ascending=False)


def run_champion_simulation(df_clean: pd.DataFrame, paths: ProjectPaths, n_simulations: int = 1000, random_state: int = 42) -> pd.DataFrame:
    latest_year = int(df_clean["season_start_year"].max())
    latest_df = df_clean[df_clean["season_start_year"] == latest_year].copy()
    if latest_df.empty:
        raise ValueError("No data for latest season simulation.")

    rng = np.random.default_rng(seed=random_state)
    league_outputs = []

    for league_code, block in latest_df.groupby("league_code", sort=True):
        league_result = _league_simulation(
            season_df=block.sort_values("match_date"),
            n_simulations=n_simulations,
            rng=rng,
        )
        league_outputs.append(league_result)

        fig, ax = plt.subplots(figsize=(9, 5))
        top = league_result.head(10).sort_values("champion_probability")
        ax.barh(top["team"], top["champion_probability"], color="#16a34a")
        ax.set_title(f"{league_code} - Champion Probability (Top 10)")
        ax.set_xlabel("Probability")
        fig.tight_layout()
        out_plot = paths.bi_dir / f"champion_probability_{league_code}.png"
        out_plot.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_plot, dpi=170)
        plt.close(fig)

    final_df = pd.concat(league_outputs, ignore_index=True)
    final_df = final_df.sort_values(["league_code", "champion_probability"], ascending=[True, False])
    paths.bi_dir.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(paths.bi_dir / "champion_probabilities.csv", index=False, encoding="utf-8")

    md_lines = [
        "# Champion Probability Report",
        "",
        f"- Simulations per league: {n_simulations}",
        f"- Season simulated (start year): {latest_year}",
        "- Probability engine: Elo + recent form + points-per-game heuristic (Monte Carlo).",
        "",
    ]
    for league_code, block in final_df.groupby("league_code", sort=True):
        md_lines.append(f"## {league_code}")
        for _, row in block.head(5).iterrows():
            md_lines.append(
                f"- {row['team']}: champion={row['champion_probability']:.3f}, top3={row['top3_probability']:.3f}, expected_points={row['expected_points']:.2f}"
            )
        md_lines.append("")
    (paths.bi_dir / "champion_probabilities.md").write_text("\n".join(md_lines), encoding="utf-8")
    return final_df
