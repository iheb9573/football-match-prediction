import { NextResponse } from "next/server"

import { backendGet } from "@/lib/backend-api"

type LeagueItem = {
  league_code: string
  league_name: string
}

export async function GET() {
  try {
    const payload = await backendGet<{ items: LeagueItem[] }>("/api/leagues")
    return NextResponse.json(payload.items ?? [])
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to load leagues"
    return NextResponse.json({ detail: message }, { status: 502 })
  }
}
