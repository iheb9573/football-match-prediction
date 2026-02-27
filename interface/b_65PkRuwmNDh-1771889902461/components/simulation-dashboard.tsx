'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface SimulationDashboardProps {
  simulations: any
}

export function SimulationDashboard({ simulations }: SimulationDashboardProps) {
  const championshipData = simulations.championshipWinners.map(team => ({
    team: team.team,
    probability: team.probability * 100,
    simulations: team.simulations
  }))

  return (
    <div className="grid gap-6">
      {/* Championship Winners */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Probabilités de Champion 🏆</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {simulations.championshipWinners.map((team, idx) => (
              <div key={idx} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-medium">{team.team}</span>
                  <Badge variant="outline">{(team.probability * 100).toFixed(1)}%</Badge>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-yellow-400 to-red-500 h-3 rounded-full transition-all"
                    style={{ width: `${team.probability * 100}%` }}
                  />
                </div>
                <div className="text-xs text-gray-500">
                  {team.simulations.toLocaleString()} simulations
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Top 4 Probabilities */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Probabilité Top 4</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={simulations.topFourProbabilities}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="team" fontSize={12} angle={-45} textAnchor="end" height={80} />
              <YAxis domain={[0, 1]} fontSize={12} />
              <Tooltip formatter={(value) => `${(value * 100).toFixed(1)}%`} />
              <Bar dataKey="topFour" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Season Trends */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Évolution de la Probabilité de Champion</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={simulations.seasonTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="week" fontSize={12} />
              <YAxis domain={[0, 0.35]} fontSize={12} />
              <Tooltip 
                formatter={(value) => `${(value * 100).toFixed(1)}%`}
                labelFormatter={(label) => `Semaine ${label}`}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="leadProb" 
                stroke="#3b82f6" 
                strokeWidth={2}
                name="Prob. Champion Leader"
                dot={{ fill: '#3b82f6', r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Monte Carlo Info */}
      <Card className="border-l-4 border-l-blue-500 bg-blue-50">
        <CardHeader>
          <CardTitle className="text-base">À propos des Simulations Monte Carlo</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-gray-700 space-y-2">
          <p>
            Les simulations Monte Carlo réexécutent les matchs restants selon les probabilités prédites par le modèle ML.
          </p>
          <p>
            Chaque simulation génère une saison complète possible, permettant de calculer les probabilités d'arrivée.
          </p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>100,000+ simulations par itération</li>
            <li>Mise à jour après chaque journée</li>
            <li>Intervalle de confiance 95%</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
