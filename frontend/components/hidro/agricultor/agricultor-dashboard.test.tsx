import { beforeEach, describe, expect, it, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { AgricultorDashboard } from "./agricultor-dashboard"
import { historialSemanas } from "@/lib/hidro-data"

vi.mock("@/lib/api-client", () => ({
  apiFetch: vi.fn(),
}))

import { apiFetch } from "@/lib/api-client"
const mockApiFetch = vi.mocked(apiFetch)

const recomendacionMock = {
  semana: 42,
  cultivo_prioritario: "frijol" as const,
  accion: "retrasar_siembra" as const,
  razon: "nivel de presa 12% bajo la media, precipitación insuficiente para la etapa crítica",
  mensaje_whatsapp: "🌾 Alerta: nivel bajo en las presas. Se recomienda posponer la siembra 2 semanas.",
  severidad: "alerta" as const,
}

beforeEach(() => {
  vi.clearAllMocks()
  mockApiFetch.mockResolvedValue(recomendacionMock)
})

describe("AgricultorDashboard", () => {
  it("Inicio: muestra el mensaje_whatsapp real de GET /api/siembra/{semana}", async () => {
    render(<AgricultorDashboard onLogout={() => {}} token="tok" />)
    expect(await screen.findByText(recomendacionMock.mensaje_whatsapp)).toBeInTheDocument()
    expect(mockApiFetch).toHaveBeenCalledWith("/api/siembra/52", { token: "tok" })
  })

  it("Siembra: muestra el cultivo priorizado, la acción y la ventana de siembra reales", async () => {
    const user = userEvent.setup()
    render(<AgricultorDashboard onLogout={() => {}} token="tok" />)
    await screen.findByText(recomendacionMock.mensaje_whatsapp)

    await user.click(screen.getByRole("button", { name: "Siembra" }))

    expect(screen.getByText("Frijol")).toBeInTheDocument()
    expect(screen.getByText("Retrasar siembra")).toBeInTheDocument()
    expect(screen.getByText(/Junio – Agosto/)).toBeInTheDocument()
    expect(screen.getByText(recomendacionMock.razon)).toBeInTheDocument()
  })

  it("Historial: dibuja un punto por cada semana de historialSemanas", async () => {
    const user = userEvent.setup()
    render(<AgricultorDashboard onLogout={() => {}} token="tok" />)
    await screen.findByText(recomendacionMock.mensaje_whatsapp)

    await user.click(screen.getByRole("button", { name: "Historial" }))
    expect(screen.getAllByLabelText(/^Semana \d+:/)).toHaveLength(historialSemanas.length)
  })

  it("Historial: la fila de puntos puede envolver en pantallas angostas (sin overflow horizontal)", async () => {
    const user = userEvent.setup()
    render(<AgricultorDashboard onLogout={() => {}} token="tok" />)
    await screen.findByText(recomendacionMock.mensaje_whatsapp)

    await user.click(screen.getByRole("button", { name: "Historial" }))
    const primerPunto = screen.getAllByLabelText(/^Semana \d+:/)[0]
    const fila = primerPunto.parentElement?.parentElement
    expect(fila).toHaveClass("flex-wrap")
  })

  it("si la API falla, no rompe y muestra un estado sin recomendación", async () => {
    mockApiFetch.mockRejectedValue(new Error("network"))
    render(<AgricultorDashboard onLogout={() => {}} token="tok" />)
    expect(await screen.findByText(/sin recomendaci[oó]n/i)).toBeInTheDocument()
  })
})
