import { NextRequest, NextResponse } from "next/server"

import { backendGet } from "@/lib/backend-api"

export async function GET(request: NextRequest) {
  try {
    const leagueCode = request.nextUrl.searchParams.get("league_code")
    const endpoint = leagueCode ? `/api/simulations?league_code=${encodeURIComponent(leagueCode)}` : "/api/simulations"
    const simulations = await backendGet(endpoint)
    return NextResponse.json(simulations)
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to load simulations"
    return NextResponse.json({ detail: message }, { status: 502 })
  }
}
