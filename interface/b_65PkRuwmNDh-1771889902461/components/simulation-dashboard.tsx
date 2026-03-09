'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface ChampionWinner {
  team: string
  probability: number
  simulations: number
}

interface TopFour {
  team: string
  topFour: number
}

interface SeasonTrend {
  week: number
  leader: string
  leadProb: number
}

interface SimulationData {
  championshipWinners: ChampionWinner[]
  topFourProbabilities: TopFour[]
  seasonTrends: SeasonTrend[]
}

interface SimulationDashboardProps {
  simulations: SimulationData
}

const tooltipStyle = {
  contentStyle: {
    backgroundColor: 'var(--card)',
    border: '1px solid var(--border)',
    borderRadius: '8px',
    color: 'var(--foreground)',
  },
}

export function SimulationDashboard({ simulations }: SimulationDashboardProps) {
  const championshipData = simulations.championshipWinners.map((team) => ({
    team: team.team,
    probability: team.probability * 100,
    simulations: team.simulations,
  }))
  void championshipData

  return (
    <div className="grid gap-6">
      {/* Championship Winners */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-lg text-foreground">Probabilités de Champion 🏆</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {simulations.championshipWinners.map((team, idx) => (
              <div key={idx} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-foreground">{team.team}</span>
                  <Badge variant="outline" className="text-foreground border-border">
                    {(team.probability * 100).toFixed(1)}%
                  </Badge>
                </div>
                <div className="w-full bg-muted rounded-full h-3 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-yellow-400 to-red-500 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${team.probability * 100}%` }}
                  />
                </div>
                <div className="text-xs text-muted-foreground">
                  {team.simulations.toLocaleString()} simulations
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Top 4 Probabilities */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-lg text-foreground">Probabilité Top 4</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={simulations.topFourProbabilities}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="team" fontSize={12} angle={-45} textAnchor="end" height={80}
                tick={{ fill: 'var(--muted-foreground)' }} />
              <YAxis domain={[0, 1]} fontSize={12} tick={{ fill: 'var(--muted-foreground)' }} />
              <Tooltip
                {...tooltipStyle}
                formatter={(value: number) => `${(value * 100).toFixed(1)}%`}
              />
              <Bar dataKey="topFour" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Season Trends */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-lg text-foreground">Évolution de la Probabilité de Champion</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={simulations.seasonTrends}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="week" fontSize={12} tick={{ fill: 'var(--muted-foreground)' }} />
              <YAxis domain={[0, 0.35]} fontSize={12} tick={{ fill: 'var(--muted-foreground)' }} />
              <Tooltip
                {...tooltipStyle}
                formatter={(value: number) => `${(value * 100).toFixed(1)}%`}
                labelFormatter={(label) => `Semaine ${label}`}
              />
              <Legend wrapperStyle={{ color: 'var(--muted-foreground)' }} />
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
      <Card className="border-l-4 border-l-blue-500 bg-blue-500/10 dark:bg-blue-500/15 border-border">
        <CardHeader>
          <CardTitle className="text-base text-foreground">À propos des Simulations Monte Carlo</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>
            Les simulations Monte Carlo réexécutent les matchs restants selon les probabilités prédites par le modèle ML.
          </p>
          <p>
            Chaque simulation génère une saison complète possible, permettant de calculer les probabilités d'arrivée.
          </p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>300+ simulations par ligue</li>
            <li>Basé sur ELO + forme + points/match</li>
            <li>Mis à jour à chaque exécution du pipeline</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
