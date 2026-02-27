import { useEffect, useMemo, useState } from "react";
import {
  fetchChampionProbabilities,
  fetchLeagues,
  fetchModelMetrics,
  fetchTeams,
  predictMatch
} from "./api";

function ProbBar({ label, value, color }) {
  return (
    <div className="prob-row">
      <div className="prob-label">
        <span>{label}</span>
        <strong>{(value * 100).toFixed(1)}%</strong>
      </div>
      <div className="prob-track">
        <div className="prob-fill" style={{ width: `${value * 100}%`, background: color }} />
      </div>
    </div>
  );
}

export default function App() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [leagues, setLeagues] = useState([]);
  const [teams, setTeams] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [champions, setChampions] = useState([]);
  const [prediction, setPrediction] = useState(null);

  const [form, setForm] = useState({
    league_code: "EPL",
    home_team: "",
    away_team: ""
  });

  useEffect(() => {
    async function bootstrap() {
      try {
        setLoading(true);
        const [leagueData, metricsData, championData] = await Promise.all([
          fetchLeagues(),
          fetchModelMetrics(),
          fetchChampionProbabilities()
        ]);
        setLeagues(leagueData);
        setMetrics(metricsData);
        setChampions(championData);

        const initialLeague = leagueData[0]?.league_code || "EPL";
        const teamData = await fetchTeams(initialLeague);
        setTeams(teamData);
        setForm((old) => ({
          ...old,
          league_code: initialLeague,
          home_team: teamData[0] || "",
          away_team: teamData[1] || teamData[0] || ""
        }));
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }
    bootstrap();
  }, []);

  useEffect(() => {
    async function updateTeams() {
      if (!form.league_code) return;
      try {
        const teamData = await fetchTeams(form.league_code);
        setTeams(teamData);
        setForm((old) => ({
          ...old,
          home_team: teamData.includes(old.home_team) ? old.home_team : (teamData[0] || ""),
          away_team: teamData.includes(old.away_team) ? old.away_team : (teamData[1] || teamData[0] || "")
        }));
      } catch (e) {
        setError(e.message);
      }
    }
    updateTeams();
  }, [form.league_code]);

  const modelSummary = useMemo(() => {
    const testMetrics = metrics.find((row) => row.stage === "test");
    const validation = metrics.filter((row) => row.stage === "validation");
    const bestValidation = [...validation].sort((a, b) => b.f1_macro - a.f1_macro)[0];
    return { testMetrics, bestValidation };
  }, [metrics]);

  const championByLeague = useMemo(() => {
    const map = new Map();
    champions.forEach((row) => {
      if (!map.has(row.league_code)) map.set(row.league_code, []);
      map.get(row.league_code).push(row);
    });
    for (const [key, rows] of map) {
      rows.sort((a, b) => b.champion_probability - a.champion_probability);
      map.set(key, rows.slice(0, 8));
    }
    return map;
  }, [champions]);

  async function onPredict(event) {
    event.preventDefault();
    if (!form.home_team || !form.away_team || form.home_team === form.away_team) {
      setError("Choisis deux equipes differentes.");
      return;
    }
    try {
      setError("");
      const result = await predictMatch(form);
      setPrediction(result);
    } catch (e) {
      setError(e.message);
    }
  }

  if (loading) {
    return <div className="center-message">Loading Football BI Dashboard...</div>;
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <h1>Football BI Predictor</h1>
        <p>Prediction probabiliste + dashboard decisionnel pour le vainqueur de competition.</p>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="grid-top">
        <article className="card">
          <h2>Performance Modele</h2>
          <div className="metric-grid">
            <div>
              <span className="metric-label">Best Validation Model</span>
              <strong>{modelSummary.bestValidation?.model || "N/A"}</strong>
            </div>
            <div>
              <span className="metric-label">Test Accuracy</span>
              <strong>{modelSummary.testMetrics ? `${(modelSummary.testMetrics.accuracy * 100).toFixed(2)}%` : "N/A"}</strong>
            </div>
            <div>
              <span className="metric-label">Test F1 Macro</span>
              <strong>{modelSummary.testMetrics ? modelSummary.testMetrics.f1_macro.toFixed(4) : "N/A"}</strong>
            </div>
            <div>
              <span className="metric-label">Test Log Loss</span>
              <strong>{modelSummary.testMetrics ? modelSummary.testMetrics.log_loss.toFixed(4) : "N/A"}</strong>
            </div>
          </div>
          <p className="hint">
            Objectif 75% en 3 classes: tres difficile sans variables externes (cotes bookmaker, blessures live, lineups).
          </p>
        </article>

        <article className="card form-card">
          <h2>Predire Deux Equipes</h2>
          <form onSubmit={onPredict}>
            <label>
              Ligue
              <select
                value={form.league_code}
                onChange={(e) => setForm((old) => ({ ...old, league_code: e.target.value }))}
              >
                {leagues.map((lg) => (
                  <option key={lg.league_code} value={lg.league_code}>
                    {lg.league_code}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Equipe Domicile
              <select
                value={form.home_team}
                onChange={(e) => setForm((old) => ({ ...old, home_team: e.target.value }))}
              >
                {teams.map((team) => (
                  <option key={team} value={team}>
                    {team}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Equipe Exterieur
              <select
                value={form.away_team}
                onChange={(e) => setForm((old) => ({ ...old, away_team: e.target.value }))}
              >
                {teams.map((team) => (
                  <option key={team} value={team}>
                    {team}
                  </option>
                ))}
              </select>
            </label>
            <button type="submit">Lancer Prediction</button>
          </form>
        </article>
      </section>

      {prediction ? (
        <section className="card prediction-card">
          <h2>
            Prediction: {prediction.home_team} vs {prediction.away_team}
          </h2>
          <p className="prediction-main">
            <strong>{prediction.predicted_label}</strong> (confiance {(prediction.confidence * 100).toFixed(1)}%)
          </p>
          <ProbBar label="Victoire domicile" value={prediction.probabilities.home_win} color="linear-gradient(90deg,#16a34a,#4ade80)" />
          <ProbBar label="Match nul" value={prediction.probabilities.draw} color="linear-gradient(90deg,#f59e0b,#facc15)" />
          <ProbBar label="Victoire exterieur" value={prediction.probabilities.away_win} color="linear-gradient(90deg,#dc2626,#f87171)" />

          <h3>Explications principales</h3>
          <ul className="explain-list">
            {prediction.top_explanations.map((item) => (
              <li key={`${item.feature}-${item.value}`}>
                <span>{item.feature}</span>
                <strong>{item.value}</strong>
                <em>{item.effect}</em>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="card champions-card">
        <h2>Dashboard Probabilites Champion</h2>
        <div className="league-panels">
          {[...championByLeague.entries()].map(([leagueCode, rows]) => (
            <div key={leagueCode} className="league-panel">
              <h3>{leagueCode}</h3>
              {rows.map((row) => (
                <div className="league-row" key={`${leagueCode}-${row.team}`}>
                  <span>{row.team}</span>
                  <div className="league-track">
                    <div
                      className="league-fill"
                      style={{ width: `${row.champion_probability * 100}%` }}
                    />
                  </div>
                  <strong>{(row.champion_probability * 100).toFixed(1)}%</strong>
                </div>
              ))}
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
