'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts'
import { EMPTY_STATISTICS, type StatisticsPayload } from '@/lib/statistics'

interface StatsOverviewProps {
  statistics: StatisticsPayload
}

const COLORS = ['#3b82f6', '#8b5cf6', '#ef4444', '#f59e0b', '#10b981']

const tooltipStyle = {
  contentStyle: {
    backgroundColor: 'var(--card)',
    border: '1px solid var(--border)',
    borderRadius: '8px',
    color: 'var(--foreground)',
  },
}

export function StatsOverview({ statistics }: StatsOverviewProps) {
  const stats = statistics || EMPTY_STATISTICS

  return (
    <div className="grid gap-6">
      {/* Model Performance */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-lg text-foreground">Performance du Modèle (Extra Trees)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Précision', value: stats.modelPerformance.precision, color: 'blue' },
              { label: 'Rappel', value: stats.modelPerformance.recall, color: 'purple' },
              { label: 'F1 Score', value: stats.modelPerformance.f1Score, color: 'pink' },
              { label: 'AUC-ROC', value: stats.modelPerformance.auc_roc, color: 'green' },
            ].map(({ label, value, color }) => (
              <div
                key={label}
                className={`bg-${color}-500/10 dark:bg-${color}-500/15 p-4 rounded-lg border border-${color}-500/20`}
              >
                <p className="text-sm text-muted-foreground mb-1">{label}</p>
                <p className={`text-2xl font-bold text-${color}-600 dark:text-${color}-400`}>
                  {(value * 100).toFixed(1)}%
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Accuracy by League */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-lg text-foreground">Précision par Ligue</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stats.accuracyByLeague}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="league" fontSize={12} tick={{ fill: 'var(--muted-foreground)' }} />
              <YAxis domain={[0, 1]} fontSize={12} tick={{ fill: 'var(--muted-foreground)' }} />
              <Tooltip {...tooltipStyle} formatter={(value) => `${(Number(value) * 100).toFixed(1)}%`} />
              <Bar dataKey="accuracy" fill="#3b82f6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Prediction Distribution */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-lg text-foreground">Distribution des Prédictions</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={stats.predictionDistribution}
                  cx="50%"
                  cy="50%"
                  nameKey="type"
                  labelLine={false}
                  label={({ type, percentage }) => `${type}: ${percentage}%`}
                  outerRadius={80}
                  dataKey="percentage"
                >
                  {stats.predictionDistribution.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip {...tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Confidence Analysis */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-lg text-foreground">Analyse de Confiance</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={stats.confidenceAnalysis}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="confidenceRange" fontSize={10} tick={{ fill: 'var(--muted-foreground)' }} />
                <YAxis fontSize={12} tick={{ fill: 'var(--muted-foreground)' }} />
                <Tooltip {...tooltipStyle} />
                <Legend wrapperStyle={{ color: 'var(--muted-foreground)' }} />
                <Bar dataKey="count" fill="#3b82f6" name="Matchs" />
                <Bar dataKey="accuracy" fill="#10b981" name="Précision" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Feature Importance */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-lg text-foreground">Importance des Features (Permutation)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {stats.topFeatures.map((feature, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="font-medium text-foreground">{feature.feature}</span>
                  <span className="text-muted-foreground">{(feature.importance * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${feature.importance * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* League Stats Table */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-lg text-foreground">Statistiques par Ligue</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-border">
                <tr>
                  <th className="text-left py-2 px-2 text-muted-foreground">Ligue</th>
                  <th className="text-right py-2 px-2 text-muted-foreground">Matchs</th>
                  <th className="text-right py-2 px-2 text-muted-foreground">Avg Buts</th>
                  <th className="text-right py-2 px-2 text-muted-foreground">Avg Cotes</th>
                </tr>
              </thead>
              <tbody>
                {stats.leagueStats.map((stat, idx) => (
                  <tr key={idx} className="border-b border-border/50 hover:bg-muted/40 transition-colors">
                    <td className="py-3 px-2 font-medium text-foreground">{stat.league}</td>
                    <td className="text-right py-3 px-2 text-muted-foreground">{stat.totalMatches}</td>
                    <td className="text-right py-3 px-2 text-muted-foreground">{stat.avgGoals.toFixed(2)}</td>
                    <td className="text-right py-3 px-2 text-muted-foreground">{stat.avgOdds.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
