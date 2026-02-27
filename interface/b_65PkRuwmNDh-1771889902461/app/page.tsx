'use client'

import { useEffect, useState } from 'react'

import { StatsOverview } from '@/components/stats-overview'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { EMPTY_STATISTICS, normalizeStatistics, type StatisticsPayload } from '@/lib/statistics'

export default function DashboardPage() {
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
          Dashboard Principal
        </h1>
        <p className="text-slate-400 text-lg">Vue d'ensemble de votre modele ML de prediction footballistique</p>
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
        <StatsOverview statistics={statistics} />
      )}
    </main>
  )
}
