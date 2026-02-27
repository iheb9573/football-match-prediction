import { NextResponse } from "next/server"

import { backendPost } from "@/lib/backend-api"

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const prediction = await backendPost("/api/predictions/analyze", body)
    return NextResponse.json(prediction)
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to analyze prediction"
    return NextResponse.json({ detail: message }, { status: 502 })
  }
}
