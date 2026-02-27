const BACKEND_API_URL =
  process.env.BACKEND_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000"

function buildBackendUrl(endpoint: string): string {
  const cleanBase = BACKEND_API_URL.endsWith("/") ? BACKEND_API_URL.slice(0, -1) : BACKEND_API_URL
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`
  return `${cleanBase}${cleanEndpoint}`
}

export async function backendGet<T>(endpoint: string): Promise<T> {
  const response = await fetch(buildBackendUrl(endpoint), {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`Backend GET ${endpoint} failed (${response.status}): ${detail}`)
  }

  return response.json()
}

export async function backendPost<T>(endpoint: string, payload: unknown): Promise<T> {
  const response = await fetch(buildBackendUrl(endpoint), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`Backend POST ${endpoint} failed (${response.status}): ${detail}`)
  }

  return response.json()
}
