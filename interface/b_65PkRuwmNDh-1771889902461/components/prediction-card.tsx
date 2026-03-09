'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from 'recharts'

interface PredictionCardProps {
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
  prediction: string
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

const COLORS = ['#3b82f6', '#8b5cf6', '#ef4444']

export function PredictionCard({
  match,
  probabilities,
  prediction,
  confidence,
  xG_home,
  xG_away,
  features
}: PredictionCardProps) {
  const chartData = [
    { name: 'Home', value: Math.round(probabilities.home * 100) },
    { name: 'Draw', value: Math.round(probabilities.draw * 100) },
    { name: 'Away', value: Math.round(probabilities.away * 100) }
  ]

  const matchDate = new Date(match.date).toLocaleDateString('fr-FR', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })

  const confidencePct = Math.round(confidence * 100)
  const confidenceColor =
    confidence >= 0.85 ? 'bg-green-500/15 text-green-600 dark:text-green-400 border-green-500/30' :
      confidence >= 0.75 ? 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30' :
        'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30'

  return (
    <Card className="overflow-hidden hover:shadow-xl dark:hover:shadow-blue-900/20 transition-all duration-300 bg-card border-border">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <CardTitle className="text-lg text-foreground">{match.homeTeam} vs {match.awayTeam}</CardTitle>
            <CardDescription className="text-xs mt-1 text-muted-foreground">
              {match.league} • {match.stadium}
            </CardDescription>
          </div>
          <Badge className={confidenceColor} variant="outline">
            {confidencePct}%
          </Badge>
        </div>
        <CardDescription className="text-muted-foreground">{matchDate}</CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Probability Chart */}
        <div className="space-y-2">
          <p className="text-sm font-semibold text-foreground">Probabilités de résultat</p>
          <ResponsiveContainer width="100%" height={120}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="name" fontSize={12} tick={{ fill: 'var(--muted-foreground)' }} />
              <YAxis fontSize={12} tick={{ fill: 'var(--muted-foreground)' }} domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--card)',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  color: 'var(--foreground)'
                }}
                formatter={(value) => `${value}%`}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {chartData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* xG */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="bg-blue-500/10 dark:bg-blue-500/15 p-2 rounded border border-blue-500/20">
            <p className="text-xs text-muted-foreground">xG Domicile</p>
            <p className="font-semibold text-blue-600 dark:text-blue-400">{xG_home.toFixed(2)}</p>
          </div>
          <div className="bg-red-500/10 dark:bg-red-500/15 p-2 rounded border border-red-500/20">
            <p className="text-xs text-muted-foreground">xG Extérieur</p>
            <p className="font-semibold text-red-600 dark:text-red-400">{xG_away.toFixed(2)}</p>
          </div>
        </div>

        {/* Team Ratings */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <p className="font-semibold mb-1 text-blue-600 dark:text-blue-400">{match.homeTeam}</p>
            <div className="space-y-1">
              {[
                { label: 'Forme:', value: `${features.homeFormRating.toFixed(1)}/5` },
                { label: 'Attaque:', value: `${features.homeAttack.toFixed(1)}/10` },
                { label: 'Défense:', value: `${features.homeDefense.toFixed(1)}/10` },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between">
                  <span className="text-muted-foreground">{label}</span>
                  <span className="font-medium text-foreground">{value}</span>
                </div>
              ))}
            </div>
          </div>
          <div>
            <p className="font-semibold mb-1 text-red-600 dark:text-red-400">{match.awayTeam}</p>
            <div className="space-y-1">
              {[
                { label: 'Forme:', value: `${features.awayFormRating.toFixed(1)}/5` },
                { label: 'Attaque:', value: `${features.awayAttack.toFixed(1)}/10` },
                { label: 'Défense:', value: `${features.awayDefense.toFixed(1)}/10` },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between">
                  <span className="text-muted-foreground">{label}</span>
                  <span className="font-medium text-foreground">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* H2H */}
        <div className="text-xs bg-purple-500/10 dark:bg-purple-500/15 p-2 rounded border border-purple-500/20">
          <p className="text-muted-foreground">Historique</p>
          <p className="font-semibold text-purple-600 dark:text-purple-400">{features.headToHead}</p>
        </div>

        {/* Prediction Badge */}
        <div className="flex items-center justify-between bg-gradient-to-r from-blue-500/10 to-purple-500/10 dark:from-blue-500/20 dark:to-purple-500/20 p-3 rounded-lg border border-blue-500/20">
          <span className="text-sm font-medium text-foreground">Prédiction ML:</span>
          <Badge className="text-sm px-3 py-1 bg-primary text-primary-foreground">
            {prediction === 'H' ? '🏠 Domicile' : prediction === 'D' ? '🤝 Match Nul' : '✈️ Extérieur'}
          </Badge>
        </div>
      </CardContent>
    </Card>
  )
}
