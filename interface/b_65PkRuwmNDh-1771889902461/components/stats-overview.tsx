'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

import { EMPTY_STATISTICS, type StatisticsPayload } from '@/lib/statistics'

interface StatsOverviewProps {
  statistics: StatisticsPayload
}

const COLORS = ['#3b82f6', '#8b5cf6', '#ef4444', '#f59e0b', '#10b981']

export function StatsOverview({ statistics }: StatsOverviewProps) {
  const stats = statistics || EMPTY_STATISTICS

  return (
    <div className="grid gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Performance du Modele</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">Precision</p>
              <p className="text-2xl font-bold text-blue-700">{(stats.modelPerformance.precision * 100).toFixed(1)}%</p>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">Rappel</p>
              <p className="text-2xl font-bold text-purple-700">{(stats.modelPerformance.recall * 100).toFixed(1)}%</p>
            </div>
            <div className="bg-gradient-to-br from-pink-50 to-pink-100 p-4 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">F1 Score</p>
              <p className="text-2xl font-bold text-pink-700">{(stats.modelPerformance.f1Score * 100).toFixed(1)}%</p>
            </div>
            <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">AUC-ROC</p>
              <p className="text-2xl font-bold text-green-700">{(stats.modelPerformance.auc_roc * 100).toFixed(1)}%</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Precision par Ligue</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stats.accuracyByLeague}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="league" fontSize={12} />
              <YAxis domain={[0, 1]} fontSize={12} />
              <Tooltip formatter={(value) => `${(Number(value) * 100).toFixed(1)}%`} />
              <Bar dataKey="accuracy" fill="#3b82f6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Distribution des Predictions</CardTitle>
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
                  fill="#8884d8"
                  dataKey="percentage"
                >
                  {stats.predictionDistribution.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Analyse de Confiance</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={stats.confidenceAnalysis}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="confidenceRange" fontSize={10} />
                <YAxis fontSize={12} />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#3b82f6" name="Matchs" />
                <Bar dataKey="accuracy" fill="#10b981" name="Precision" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Importance des Features</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {stats.topFeatures.map((feature, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="font-medium">{feature.feature}</span>
                  <span className="text-gray-600">{(feature.importance * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
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

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Statistiques par Ligue</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b">
                <tr>
                  <th className="text-left py-2 px-2">Ligue</th>
                  <th className="text-right py-2 px-2">Matchs</th>
                  <th className="text-right py-2 px-2">Avg Buts</th>
                  <th className="text-right py-2 px-2">Avg Cotes</th>
                </tr>
              </thead>
              <tbody>
                {stats.leagueStats.map((stat, idx) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-2 font-medium">{stat.league}</td>
                    <td className="text-right py-3 px-2">{stat.totalMatches}</td>
                    <td className="text-right py-3 px-2">{stat.avgGoals.toFixed(2)}</td>
                    <td className="text-right py-3 px-2">{stat.avgOdds.toFixed(2)}</td>
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
