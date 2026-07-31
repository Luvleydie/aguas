import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { GobiernoInicio } from "./gobierno-inicio"

vi.mock("@/lib/api-client", () => ({
  apiFetch: vi.fn(),
}))

import { apiFetch } from "@/lib/api-client"
const mockApiFetch = vi.mocked(apiFetch)

beforeEach(() => {
  vi.clearAllMocks()
})

describe("GobiernoInicio", () => {
  it("muestra el resumen y la semana del boletín más reciente", async () => {
    mockApiFetch.mockResolvedValue([{
      semana: 42,
      nivel: "amarillo",
      recomendacion: "Activer vigilancia",
      markdown: "# Boletín",
      publicado: false,
      anio: 2024,
      id: "1",
    }])

    render(<GobiernoInicio onNavigate={() => {}} token="tok" />)
    await waitFor(() => {
      expect(screen.getByText(/Semana 42/)).toBeInTheDocument()
    })
  })

  it("'Ver boletín completo' navega a boletin", async () => {
    mockApiFetch.mockResolvedValue([])
    const onNavigate = vi.fn()
    const user = userEvent.setup()
    render(<GobiernoInicio onNavigate={onNavigate} token="tok" />)

    await screen.findByText(/Sin boletines/)
    await user.click(screen.getByRole("button", { name: /ver boletín completo/i }))
    expect(onNavigate).toHaveBeenCalledWith("boletin")
  })

  it("cada acceso rápido navega a su id correspondiente", async () => {
    mockApiFetch.mockResolvedValue([])
    const onNavigate = vi.fn()
    const user = userEvent.setup()
    render(<GobiernoInicio onNavigate={onNavigate} token="tok" />)

    await screen.findByText(/Sin boletines/)
    await user.click(screen.getByRole("button", { name: /generar boletín/i }))
    expect(onNavigate).toHaveBeenCalledWith("generar")

    await user.click(screen.getByRole("button", { name: /tendencias/i }))
    expect(onNavigate).toHaveBeenCalledWith("tendencias")
  })
})
