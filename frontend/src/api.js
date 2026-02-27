const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function callApi(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.json();
}

export async function fetchLeagues() {
  const data = await callApi("/api/leagues");
  return data.items || [];
}

export async function fetchTeams(leagueCode) {
  const data = await callApi(`/api/teams/${leagueCode}`);
  return data.items || [];
}

export async function predictMatch(payload) {
  return callApi("/api/predict", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function fetchModelMetrics() {
  const data = await callApi("/api/dashboard/model-metrics");
  return data.items || [];
}

export async function fetchChampionProbabilities() {
  const data = await callApi("/api/dashboard/champion-probabilities");
  return data.items || [];
}
