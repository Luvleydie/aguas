import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { apiFetch, ApiError } from "./api-client"

describe("apiFetch", () => {
  beforeEach(() => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000")
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
  })

  it("antepone NEXT_PUBLIC_API_URL a la ruta y hace GET por default", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200 }))
    vi.stubGlobal("fetch", fetchMock)

    const resultado = await apiFetch<{ ok: boolean }>("/api/boletin/42")

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/boletin/42",
      expect.objectContaining({ method: "GET" }),
    )
    expect(resultado).toEqual({ ok: true })
  })

  it("agrega Authorization: Bearer <token> cuando se pasa token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({}), { status: 200 }))
    vi.stubGlobal("fetch", fetchMock)

    await apiFetch("/api/logs/42", { token: "abc123" })

    const [, init] = fetchMock.mock.calls[0]
    expect(init.headers.Authorization).toBe("Bearer abc123")
  })

  it("serializa el body como JSON y manda Content-Type en POST", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: "1" }), { status: 201 }))
    vi.stubGlobal("fetch", fetchMock)

    await apiFetch("/api/boletin/generar", { method: "POST", body: { semana: 42 } })

    const [, init] = fetchMock.mock.calls[0]
    expect(init.method).toBe("POST")
    expect(init.headers["Content-Type"]).toBe("application/json")
    expect(init.body).toBe(JSON.stringify({ semana: 42 }))
  })

  it("lanza ApiError con status y el detail que manda FastAPI cuando la respuesta no es 2xx", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ detail: "Token inválido o expirado" }), { status: 401 }))
    vi.stubGlobal("fetch", fetchMock)

    await expect(apiFetch("/api/logs/42")).rejects.toMatchObject(
      new ApiError(401, "Token inválido o expirado"),
    )
  })

  it("si la respuesta de error no trae JSON, usa el statusText como detail", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("no-json", { status: 500, statusText: "Server Error" }))
    vi.stubGlobal("fetch", fetchMock)

    await expect(apiFetch("/api/logs/42")).rejects.toMatchObject({ status: 500, detail: "Server Error" })
  })

  it("si fetch lanza un error de red (Failed to fetch), lanza un error descriptivo", async () => {
    const fetchMock = vi.fn().mockRejectedValue(new TypeError("Failed to fetch"))
    vi.stubGlobal("fetch", fetchMock)

    await expect(apiFetch("/api/boletin/generar")).rejects.toMatchObject({
      message: expect.stringContaining("No se pudo conectar"),
    })
  })
})
