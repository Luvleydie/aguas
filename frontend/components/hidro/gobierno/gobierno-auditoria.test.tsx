import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { GobiernoAuditoria } from "./gobierno-auditoria"

vi.mock("@/lib/api-client", () => ({
  apiFetch: vi.fn(),
}))

import { apiFetch } from "@/lib/api-client"
const mockApiFetch = vi.mocked(apiFetch)

beforeEach(() => {
  vi.clearAllMocks()
})

describe("GobiernoAuditoria", () => {
  it("lista los 4 agentes en orden", async () => {
    mockApiFetch.mockResolvedValue([
      { id: "1", agente: "explorador", mensaje: "plan", timestamp: "2024-01-01T00:00:00Z" },
      { id: "2", agente: "estadista", mensaje: "hallazgos", timestamp: "2024-01-01T00:00:01Z" },
      { id: "3", agente: "narrador", mensaje: "boletin", timestamp: "2024-01-01T00:00:02Z" },
      { id: "4", agente: "agronomo", mensaje: "recomendacion", timestamp: "2024-01-01T00:00:03Z" },
    ])

    render(<GobiernoAuditoria token="tok" />)
    const items = await screen.findAllByRole("listitem")
    expect(items).toHaveLength(4)
    expect(items[0]).toHaveTextContent("explorador")
    expect(items[3]).toHaveTextContent("agronomo")
  })
})
