"use client"

import { useEffect, useMemo, useState } from "react"
import { Filter, RefreshCw, Sparkles } from "lucide-react"

import { PredictionCard } from "@/components/prediction-card"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

type LeagueOption = {
  league_code: string
  league_name: string
}

type Prediction = {
  id: number
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

export default function PredictionsPage() {
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedLeague, setSelectedLeague] = useState("all")

  const [leagueOptions, setLeagueOptions] = useState<LeagueOption[]>([])
  const [formLeagueCode, setFormLeagueCode] = useState("")
  const [teams, setTeams] = useState<string[]>([])
  const [homeTeam, setHomeTeam] = useState("")
  const [awayTeam, setAwayTeam] = useState("")
  const [matchDate, setMatchDate] = useState("")
  const [analyzing, setAnalyzing] = useState(false)
  const [analyzeError, setAnalyzeError] = useState("")
  const [customPrediction, setCustomPrediction] = useState<Prediction | null>(null)

  const fetchPredictions = async () => {
    setLoading(true)
    try {
      const res = await fetch("/api/predictions")
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }
      const data = (await res.json()) as Prediction[]
      setPredictions(Array.isArray(data) ? data : [])
    } catch (error) {
      console.error("Error fetching predictions:", error)
      setPredictions([])
    } finally {
      setLoading(false)
    }
  }

  const fetchLeagues = async () => {
    try {
      const res = await fetch("/api/leagues")
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }
      const data = (await res.json()) as LeagueOption[]
      const leagues = Array.isArray(data) ? data : []
      setLeagueOptions(leagues)
      if (leagues.length > 0 && !formLeagueCode) {
        setFormLeagueCode(leagues[0].league_code)
      }
    } catch (error) {
      console.error("Error fetching leagues:", error)
      setLeagueOptions([])
    }
  }

  const fetchTeams = async (leagueCode: string) => {
    if (!leagueCode) {
      setTeams([])
      return
    }
    try {
      const res = await fetch(`/api/teams/${encodeURIComponent(leagueCode)}`)
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }
      const data = (await res.json()) as string[]
      const teamList = Array.isArray(data) ? data : []
      setTeams(teamList)
      setHomeTeam((current) => (teamList.includes(current) ? current : teamList[0] || ""))
      setAwayTeam((current) => {
        if (teamList.includes(current)) return current
        const firstAway = teamList.find((team) => team !== (teamList[0] || ""))
        return firstAway || ""
      })
    } catch (error) {
      console.error("Error fetching teams:", error)
      setTeams([])
      setHomeTeam("")
      setAwayTeam("")
    }
  }

  useEffect(() => {
    void fetchPredictions()
    void fetchLeagues()
  }, [])

  useEffect(() => {
    void fetchTeams(formLeagueCode)
  }, [formLeagueCode])

  const availableAwayTeams = useMemo(
    () => teams.filter((team) => team !== homeTeam),
    [teams, homeTeam],
  )

  useEffect(() => {
    if (awayTeam && awayTeam !== homeTeam) return
    const firstValidAway = availableAwayTeams[0] || ""
    setAwayTeam(firstValidAway)
  }, [homeTeam, awayTeam, availableAwayTeams])

  const leagues = useMemo(
    () => ["all", ...Array.from(new Set(predictions.map((p) => p.match.league)))],
    [predictions],
  )

  const filteredPredictions =
    selectedLeague === "all" ? predictions : predictions.filter((p) => p.match.league === selectedLeague)

  const runCustomPrediction = async () => {
    if (!formLeagueCode || !homeTeam || !awayTeam) {
      setAnalyzeError("Veuillez selectionner la ligue et les deux equipes.")
      return
    }
    if (homeTeam === awayTeam) {
      setAnalyzeError("Les deux equipes doivent etre differentes.")
      return
    }

    setAnalyzeError("")
    setAnalyzing(true)
    try {
      const response = await fetch("/api/predictions/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          league_code: formLeagueCode,
          home_team: homeTeam,
          away_team: awayTeam,
          match_date: matchDate || null,
        }),
      })
      const payload = (await response.json()) as Prediction | { detail?: string }
      if (!response.ok) {
        const detail = "detail" in payload && payload.detail ? payload.detail : "Prediction impossible."
        throw new Error(detail)
      }
      setCustomPrediction(payload as Prediction)
    } catch (error) {
      const message = error instanceof Error ? error.message : "Prediction impossible."
      setAnalyzeError(message)
      setCustomPrediction(null)
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <main className="max-w-7xl mx-auto px-6 py-12">
      <div className="mb-8 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Predictions de Matchs
          </h1>
          <p className="text-slate-400">Analyse probabiliste et explicable des matchs</p>
        </div>
        <Button onClick={fetchPredictions} className="gap-2 bg-blue-600 hover:bg-blue-700">
          <RefreshCw size={18} />
          Actualiser
        </Button>
      </div>

      <Card className="mb-8 border-slate-700 bg-slate-900/70">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-slate-100">
            <Sparkles size={18} className="text-blue-400" />
            Prediction personnalisee (2 equipes)
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-4 gap-3">
            <select
              value={formLeagueCode}
              onChange={(event) => setFormLeagueCode(event.target.value)}
              className="h-10 rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-100"
            >
              {leagueOptions.map((league) => (
                <option key={league.league_code} value={league.league_code}>
                  {league.league_name} ({league.league_code})
                </option>
              ))}
            </select>

            <select
              value={homeTeam}
              onChange={(event) => setHomeTeam(event.target.value)}
              className="h-10 rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-100"
            >
              {teams.map((team) => (
                <option key={team} value={team}>
                  {team}
                </option>
              ))}
            </select>

            <select
              value={awayTeam}
              onChange={(event) => setAwayTeam(event.target.value)}
              className="h-10 rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-100"
            >
              {availableAwayTeams.map((team) => (
                <option key={team} value={team}>
                  {team}
                </option>
              ))}
            </select>

            <input
              type="date"
              value={matchDate}
              onChange={(event) => setMatchDate(event.target.value)}
              className="h-10 rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-100"
            />
          </div>

          <div className="flex items-center gap-3">
            <Button onClick={runCustomPrediction} disabled={analyzing} className="bg-emerald-600 hover:bg-emerald-700">
              {analyzing ? "Prediction en cours..." : "Predire ce match"}
            </Button>
            {analyzeError && <p className="text-sm text-rose-400">{analyzeError}</p>}
          </div>

          {customPrediction && (
            <div className="pt-3">
              <p className="text-sm text-slate-300 mb-3">Resultat de la prediction personnalisee</p>
              <div className="max-w-2xl">
                <PredictionCard {...customPrediction} />
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="mb-8 flex items-center gap-4">
        <Filter size={18} className="text-slate-400" />
        <div className="flex gap-2 flex-wrap">
          {leagues.map((league) => (
            <Button
              key={league}
              variant={selectedLeague === league ? "default" : "outline"}
              onClick={() => setSelectedLeague(league)}
              className={selectedLeague === league ? "bg-blue-600" : "border-slate-700"}
            >
              {league === "all" ? "Toutes les ligues" : league}
            </Button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="grid md:grid-cols-2 gap-6">
          {[1, 2, 3, 4, 5, 6].map((item) => (
            <Skeleton key={item} className="h-80 bg-slate-800" />
          ))}
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          {filteredPredictions.length > 0 ? (
            filteredPredictions.map((prediction) => <PredictionCard key={prediction.id} {...prediction} />)
          ) : (
            <div className="col-span-2 text-center py-12 text-slate-400">
              Aucune prediction disponible pour cette ligue
            </div>
          )}
        </div>
      )}
    </main>
  )
}
