import { NextResponse } from "next/server"

import { backendGet } from "@/lib/backend-api"

export async function GET(_request: Request, context: { params: Promise<{ leagueCode: string }> }) {
  try {
    const { leagueCode } = await context.params
    const payload = await backendGet<{ items: string[] }>(`/api/teams/${encodeURIComponent(leagueCode)}`)
    return NextResponse.json(payload.items ?? [])
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to load teams"
    return NextResponse.json({ detail: message }, { status: 502 })
  }
}
