'use client'

import { useEffect, useState } from 'react'
import { Skeleton } from '@/components/ui/skeleton'
import { SimulationDashboard } from '@/components/simulation-dashboard'

export default function SimulationsPage() {
  const [simulations, setSimulations] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch('/api/simulations')
        const data = await res.json()
        setSimulations(data)
      } catch (error) {
        console.error('Error fetching simulations:', error)
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
          Simulations Monte Carlo
        </h1>
        <p className="text-slate-400 text-lg">
          Projection probabiliste de l'issue du championnat basée sur 100k+ simulations
        </p>
      </div>

      {loading ? (
        <div className="space-y-8">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-64 bg-slate-800" />
          ))}
        </div>
      ) : (
        simulations && <SimulationDashboard simulations={simulations} />
      )}
    </main>
  )
}
