'use client'

import { useEffect, useState } from 'react'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'

import { EMPTY_STATISTICS, normalizeStatistics, type StatisticsPayload } from '@/lib/statistics'

const COLORS = ['#3b82f6', '#8b5cf6', '#ef4444', '#f59e0b', '#10b981']

export default function StatisticsPage() {
  const [statistics, setStatistics] = useState<StatisticsPayload>(EMPTY_STATISTICS)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch('/api/statistics')
        const data = await res.json()

        if (!res.ok) {
          const detail = typeof data?.detail === 'string' ? data.detail : 'Erreur API statistiques'
          throw new Error(detail)
        }

        setStatistics(normalizeStatistics(data))
        setError(null)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Erreur inconnue'
        setError(message)
        setStatistics(EMPTY_STATISTICS)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  return (
    <main className="max-w-7xl mx-auto px-6 py-12">
      <div className="mb-12">
        <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
          Statistiques & EDA
        </h1>
        <p className="text-slate-400 text-lg">Analyse exploratoire des donnees et explainability du modele</p>
      </div>

      {loading ? (
        <div className="space-y-8">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-64 bg-slate-800" />
          ))}
        </div>
      ) : error ? (
        <Card className="bg-rose-950/40 border-rose-800">
          <CardHeader>
            <CardTitle className="text-rose-300">Impossible de charger les statistiques</CardTitle>
          </CardHeader>
          <CardContent className="text-rose-200 text-sm">
            <p>{error}</p>
            <p className="mt-2">Verifier que FastAPI est lance sur `http://127.0.0.1:8000`.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-8">
          <div className="grid md:grid-cols-2 gap-6">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle>Distribution des Resultats</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={statistics.predictionDistribution}
                      cx="50%"
                      cy="50%"
                      nameKey="type"
                      labelLine={false}
                      label={({ type, percentage }) => `${type}: ${percentage}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="percentage"
                    >
                      {statistics.predictionDistribution.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle>Precision par Ligue</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={statistics.accuracyByLeague}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis dataKey="league" fontSize={12} tick={{ fill: '#94a3b8' }} />
                    <YAxis domain={[0, 1]} fontSize={12} tick={{ fill: '#94a3b8' }} />
                    <Tooltip
                      formatter={(value) => `${(Number(value) * 100).toFixed(1)}%`}
                      contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                    />
                    <Bar dataKey="accuracy" fill="#3b82f6" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle>Metriques du Modele</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-4 gap-4">
                {[
                  { label: 'Precision', value: statistics.modelPerformance.precision },
                  { label: 'Rappel', value: statistics.modelPerformance.recall },
                  { label: 'F1 Score', value: statistics.modelPerformance.f1Score },
                  { label: 'AUC-ROC', value: statistics.modelPerformance.auc_roc },
                ].map((metric, idx) => (
                  <div key={idx} className="bg-slate-700/40 p-4 rounded-lg border border-slate-600/50">
                    <p className="text-sm text-slate-300 mb-1">{metric.label}</p>
                    <p className="text-2xl font-bold text-white">{(metric.value * 100).toFixed(1)}%</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle>Importance des Features (SHAP)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {statistics.topFeatures.map((feature, idx) => (
                  <div key={idx} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-300">{feature.feature}</span>
                      <span className="text-blue-400 font-semibold">{(feature.importance * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                        style={{ width: `${feature.importance * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle>Analyse de Confiance</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={statistics.confidenceAnalysis}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="confidenceRange" fontSize={12} tick={{ fill: '#94a3b8' }} />
                  <YAxis fontSize={12} tick={{ fill: '#94a3b8' }} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }} />
                  <Bar dataKey="count" fill="#3b82f6" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}
    </main>
  )
}
