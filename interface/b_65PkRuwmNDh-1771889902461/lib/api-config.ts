// Configuration API - Centralise tous les appels API

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api'

/**
 * Effectue un appel GET à l'API
 * @param endpoint - Le chemin de l'endpoint (ex: '/predictions')
 * @returns Les données JSON retournées
 */
export async function apiGet<T>(endpoint: string): Promise<T> {
  const url = endpoint.startsWith('http') 
    ? endpoint 
    : `${API_BASE_URL}${endpoint}`

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

/**
 * Effectue un appel POST à l'API
 * @param endpoint - Le chemin de l'endpoint
 * @param data - Les données à envoyer
 * @returns Les données JSON retournées
 */
export async function apiPost<T>(endpoint: string, data: any): Promise<T> {
  const url = endpoint.startsWith('http') 
    ? endpoint 
    : `${API_BASE_URL}${endpoint}`

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

// Types pour prédictions
export interface Prediction {
  id: number
  match: {
    date: string
    homeTeam: string
    awayTeam: string
    league: string
    stadium: string
  }
  probabilities: {
    home: number
    draw: number
    away: number
  }
  prediction: 'H' | 'D' | 'A'
  confidence: number
  xG_home: number
  xG_away: number
  features: {
    homeFormRating: number
    awayFormRating: number
    homeAttack: number
    homeDefense: number
    awayAttack: number
    awayDefense: number
    headToHead: string
  }
}

// Types pour statistiques
export interface Statistics {
  accuracyByLeague: Array<{
    league: string
    accuracy: number
    matches: number
  }>
  predictionDistribution: Array<{
    type: string
    percentage: number
  }>
  confidenceAnalysis: Array<{
    confidenceRange: string
    count: number
    accuracy: number
  }>
  modelPerformance: {
    precision: number
    recall: number
    f1Score: number
    auc_roc: number
  }
  topFeatures: Array<{
    feature: string
    importance: number
  }>
  leagueStats: Array<{
    league: string
    totalMatches: number
    avgGoals: number
    avgOdds: number
  }>
}

// Types pour simulations
export interface Simulation {
  championshipWinners: Array<{
    team: string
    probability: number
    simulations: number
  }>
  topFourProbabilities: Array<{
    team: string
    topFour: number
  }>
  seasonTrends: Array<{
    week: number
    leader: string
    leadProb: number
  }>
}
