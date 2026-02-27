export type StatisticsPayload = {
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

export const EMPTY_STATISTICS: StatisticsPayload = {
  accuracyByLeague: [],
  predictionDistribution: [],
  confidenceAnalysis: [],
  modelPerformance: {
    precision: 0,
    recall: 0,
    f1Score: 0,
    auc_roc: 0,
  },
  topFeatures: [],
  leagueStats: [],
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null
}

function asNumber(value: unknown, fallback = 0): number {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value
  }
  return fallback
}

function asString(value: unknown, fallback = ""): string {
  if (typeof value === "string") {
    return value
  }
  return fallback
}

export function normalizeStatistics(payload: unknown): StatisticsPayload {
  if (!isObject(payload)) {
    return EMPTY_STATISTICS
  }

  const accuracyByLeague = Array.isArray(payload.accuracyByLeague)
    ? payload.accuracyByLeague
        .filter(isObject)
        .map((item) => ({
          league: asString(item.league, "Unknown"),
          accuracy: asNumber(item.accuracy),
          matches: Math.max(0, Math.round(asNumber(item.matches))),
        }))
    : []

  const predictionDistribution = Array.isArray(payload.predictionDistribution)
    ? payload.predictionDistribution
        .filter(isObject)
        .map((item) => ({
          type: asString(item.type, "Unknown"),
          percentage: asNumber(item.percentage),
        }))
    : []

  const confidenceAnalysis = Array.isArray(payload.confidenceAnalysis)
    ? payload.confidenceAnalysis
        .filter(isObject)
        .map((item) => ({
          confidenceRange: asString(item.confidenceRange, "Unknown"),
          count: Math.max(0, Math.round(asNumber(item.count))),
          accuracy: asNumber(item.accuracy),
        }))
    : []

  const modelPerformanceSource = isObject(payload.modelPerformance) ? payload.modelPerformance : {}
  const modelPerformance = {
    precision: asNumber(modelPerformanceSource.precision),
    recall: asNumber(modelPerformanceSource.recall),
    f1Score: asNumber(modelPerformanceSource.f1Score),
    auc_roc: asNumber(modelPerformanceSource.auc_roc),
  }

  const topFeatures = Array.isArray(payload.topFeatures)
    ? payload.topFeatures
        .filter(isObject)
        .map((item) => ({
          feature: asString(item.feature, "Unknown feature"),
          importance: asNumber(item.importance),
        }))
    : []

  const leagueStats = Array.isArray(payload.leagueStats)
    ? payload.leagueStats
        .filter(isObject)
        .map((item) => ({
          league: asString(item.league, "Unknown"),
          totalMatches: Math.max(0, Math.round(asNumber(item.totalMatches))),
          avgGoals: asNumber(item.avgGoals),
          avgOdds: asNumber(item.avgOdds),
        }))
    : []

  return {
    accuracyByLeague,
    predictionDistribution,
    confidenceAnalysis,
    modelPerformance,
    topFeatures,
    leagueStats,
  }
}
