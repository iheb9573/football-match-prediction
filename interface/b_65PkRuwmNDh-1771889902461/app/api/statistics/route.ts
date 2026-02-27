import { NextResponse } from "next/server"

import { backendGet } from "@/lib/backend-api"

export async function GET() {
  try {
    const statistics = await backendGet("/api/statistics")
    return NextResponse.json(statistics)
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to load statistics"
    return NextResponse.json({ detail: message }, { status: 502 })
  }
}
