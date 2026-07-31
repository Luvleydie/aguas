export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = "ApiError"
    this.status = status
    this.detail = detail
  }
}

export interface ApiFetchOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE"
  token?: string
  body?: unknown
}

export type { BoletinReal, Hallazgo } from "@/lib/boletin-adapter"

export interface LoginResponse {
  access_token: string
  refresh_token: string
  user: { id: string; email: string }
}

export interface UserProfile {
  id: string
  email: string
  rol: "gobierno" | "ayuntamiento" | "medios" | "agricultor"
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  return apiFetch<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: { email, password },
  })
}

export async function register(email: string, password: string): Promise<{ id: string; email: string; rol: string }> {
  return apiFetch("/api/auth/register", {
    method: "POST",
    body: { email, password },
  })
}

export async function getProfile(token: string): Promise<UserProfile> {
  return apiFetch<UserProfile>("/api/auth/me", { token })
}

/**
 * En producción el frontend se sirve desde el mismo proceso/puerto que la
 * API (ver backend/main.py, run.sh), así que NEXT_PUBLIC_API_URL queda
 * vacío y las rutas son relativas. En desarrollo (`next dev`) se apunta a
 * `http://localhost:8000` mientras Persona A no agregue CORS.
 */
export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { method = "GET", token, body } = options
  const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? ""

  const headers: Record<string, string> = {}
  if (body !== undefined) headers["Content-Type"] = "application/json"
  if (token) headers.Authorization = `Bearer ${token}`

  let response: Response
  try {
    response = await fetch(`${baseUrl}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch (err) {
    if (err instanceof TypeError && err.message === "Failed to fetch") {
      throw new ApiError(
        0,
        "No se pudo conectar con el servidor. Verifica que la API esté corriendo en el puerto correcto.",
      )
    }
    throw err
  }

  if (!response.ok) {
    let detail = response.statusText
    try {
      const cuerpo = await response.json()
      if (cuerpo && typeof cuerpo.detail === "string") detail = cuerpo.detail
    } catch {
      // sin cuerpo JSON: se usa statusText
    }
    throw new ApiError(response.status, detail)
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}
