import { NextRequest, NextResponse } from "next/server"

import { backendGet } from "@/lib/backend-api"

export async function GET(request: NextRequest) {
  try {
    const leagueCode = request.nextUrl.searchParams.get("league_code")
    const limitPerLeague = request.nextUrl.searchParams.get("limit_per_league")
    const params = new URLSearchParams()
    if (leagueCode) params.set("league_code", leagueCode)
    if (limitPerLeague) params.set("limit_per_league", limitPerLeague)

    const endpoint = params.size > 0 ? `/api/predictions?${params.toString()}` : "/api/predictions"
    const predictions = await backendGet(endpoint)
    return NextResponse.json(predictions)
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to load predictions"
    return NextResponse.json({ detail: message }, { status: 502 })
  }
}
