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

  const confidenceColor =
    confidence >= 0.85 ? 'bg-green-500/20 text-green-700' :
    confidence >= 0.75 ? 'bg-blue-500/20 text-blue-700' :
    'bg-yellow-500/20 text-yellow-700'

  return (
    <Card className="overflow-hidden hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <CardTitle className="text-lg">{match.homeTeam} vs {match.awayTeam}</CardTitle>
            <CardDescription className="text-xs mt-1">
              {match.league} • {match.stadium}
            </CardDescription>
          </div>
          <Badge className={confidenceColor} variant="outline">
            {Math.round(confidence * 100)}%
          </Badge>
        </div>
        <CardDescription>{matchDate}</CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Probability Chart */}
        <div className="space-y-2">
          <p className="text-sm font-semibold">Probabilités de résultat</p>
          <ResponsiveContainer width="100%" height={120}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
              <XAxis dataKey="name" fontSize={12} />
              <YAxis fontSize={12} domain={[0, 100]} />
              <Tooltip formatter={(value) => `${value}%`} />
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
          <div className="bg-blue-50 p-2 rounded">
            <p className="text-xs text-gray-600">xG Domicile</p>
            <p className="font-semibold text-blue-700">{xG_home.toFixed(2)}</p>
          </div>
          <div className="bg-red-50 p-2 rounded">
            <p className="text-xs text-gray-600">xG Extérieur</p>
            <p className="font-semibold text-red-700">{xG_away.toFixed(2)}</p>
          </div>
        </div>

        {/* Team Ratings */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <p className="font-semibold mb-1 text-blue-700">{match.homeTeam}</p>
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-600">Forme:</span>
                <span className="font-medium">{features.homeFormRating.toFixed(1)}/5</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Attaque:</span>
                <span className="font-medium">{features.homeAttack.toFixed(1)}/10</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Défense:</span>
                <span className="font-medium">{features.homeDefense.toFixed(1)}/10</span>
              </div>
            </div>
          </div>
          <div>
            <p className="font-semibold mb-1 text-red-700">{match.awayTeam}</p>
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-600">Forme:</span>
                <span className="font-medium">{features.awayFormRating.toFixed(1)}/5</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Attaque:</span>
                <span className="font-medium">{features.awayAttack.toFixed(1)}/10</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Défense:</span>
                <span className="font-medium">{features.awayDefense.toFixed(1)}/10</span>
              </div>
            </div>
          </div>
        </div>

        {/* H2H */}
        <div className="text-xs bg-purple-50 p-2 rounded border border-purple-200">
          <p className="text-gray-600">Historique</p>
          <p className="font-semibold text-purple-700">{features.headToHead}</p>
        </div>

        {/* Prediction Badge */}
        <div className="flex items-center justify-between bg-gradient-to-r from-blue-50 to-blue-100 p-3 rounded-lg">
          <span className="text-sm font-medium">Prédiction:</span>
          <Badge className="text-lg px-3 py-1">
            {prediction === 'H' ? '🏠 Domicile' : prediction === 'D' ? '🤝 Match Nul' : '✈️ Extérieur'}
          </Badge>
        </div>
      </CardContent>
    </Card>
  )
}
