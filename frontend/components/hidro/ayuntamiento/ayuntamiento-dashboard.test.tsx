import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { AyuntamientoDashboard } from "./ayuntamiento-dashboard"

vi.mock("@/lib/api-client", () => ({
  apiFetch: vi.fn(),
}))

import { apiFetch } from "@/lib/api-client"
const mockApiFetch = vi.mocked(apiFetch)

const boletinMock = {
  id: "bol-1",
  semana: 42,
  anio: 2024,
  nivel: "amarillo" as const,
  markdown: "# Boletín\n\n## Estado de presas\n\n50%\n\n## Precipitación\n\n53mm\n\n## Temperatura\n\n26°C\n\n## Alerta y recomendación\n\nVigilancia",
  recomendacion: "Restricción parcial del riego",
  publicado: false,
}

beforeEach(() => {
  vi.clearAllMocks()
  mockApiFetch.mockResolvedValue([boletinMock])
})

describe("AyuntamientoDashboard", () => {
  it("Inicio: muestra la semana y el semáforo, y permite marcar acción tomada", async () => {
    const user = userEvent.setup()
    render(<AyuntamientoDashboard onLogout={() => {}} token="tok" />)

    await waitFor(() => {
      expect(screen.getByText(/Semana 42/)).toBeInTheDocument()
    })

    const boton = screen.getByRole("button", { name: /marcar acción tomada/i })
    await user.click(boton)
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /acción registrada/i })).toBeDisabled()
    })
  })

  it("Boletín: solo lectura, no muestra el bloque de publicar", async () => {
    const user = userEvent.setup()
    render(<AyuntamientoDashboard onLogout={() => {}} token="tok" />)

    await screen.findByText(/Semana 42/)
    await user.click(screen.getByRole("button", { name: "Boletín" }))

    expect(screen.getByText("Estado de presas")).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: /publicar boletín/i })).toBeNull()
  })

  it("Tendencias: grafica el historial de la primera presa", async () => {
    const user = userEvent.setup()
    const { container } = render(<AyuntamientoDashboard onLogout={() => {}} token="tok" />)

    await screen.findByText(/Semana 42/)
    await user.click(screen.getByRole("button", { name: "Tendencias" }))

    expect(screen.getByText("Nivel de presas locales")).toBeInTheDocument()
    expect(container.querySelector("svg")).toBeTruthy()
  })
})
