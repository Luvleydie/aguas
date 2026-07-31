import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MediosDashboard } from "./medios-dashboard"
import { sequiasHistoricas } from "@/lib/hidro-data"

vi.mock("@/lib/api-client", () => ({
  apiFetch: vi.fn(),
}))

import { apiFetch } from "@/lib/api-client"
const mockApiFetch = vi.mocked(apiFetch)

const boletinesMock = [
  {
    id: "bol-1",
    semana: 52,
    anio: 2025,
    nivel: "naranja" as const,
    markdown:
      "# Boletín · Semana 52\n\n## Estado de presas\n\nAl 42%.\n\n## Precipitación\n\n1.2 mm.\n\n## Temperatura\n\n17.4 °C.\n\n## Alerta y recomendación\n\nNivel naranja. Restricción parcial del riego agrícola.",
    recomendacion: "Restricción parcial del riego agrícola.",
    publicado: true,
  },
  {
    id: "bol-2",
    semana: 51,
    anio: 2025,
    nivel: "amarillo" as const,
    markdown:
      "# Boletín · Semana 51\n\n## Estado de presas\n\nAl 45%.\n\n## Precipitación\n\n3.4 mm.\n\n## Temperatura\n\n16.1 °C.\n\n## Alerta y recomendación\n\nNivel amarillo. Vigilancia y uso responsable.",
    recomendacion: "Vigilancia y uso responsable del agua.",
    publicado: true,
  },
]

beforeEach(() => {
  vi.clearAllMocks()
  mockApiFetch.mockResolvedValue(boletinesMock)
  vi.stubGlobal("URL", { createObjectURL: vi.fn(() => "blob:mock"), revokeObjectURL: vi.fn() })
  vi.spyOn(window, "print").mockImplementation(() => {})
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {})
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe("MediosDashboard", () => {
  it("Inicio: lista los boletines de GET /api/boletin/historico", async () => {
    render(<MediosDashboard onLogout={() => {}} token="tok" />)
    expect(mockApiFetch).toHaveBeenCalledWith("/api/boletin/historico", { token: "tok" })
    for (const b of boletinesMock) {
      expect(await screen.findByText(new RegExp(`Semana ${b.semana}`))).toBeInTheDocument()
    }
  })

  it("Boletín narrativo: arma el texto a partir de markdown + recomendacion (ya no existe .narrativo)", async () => {
    const user = userEvent.setup()
    render(<MediosDashboard onLogout={() => {}} token="tok" />)
    await screen.findByText(/Semana 52/)

    await user.click(screen.getByRole("button", { name: "Boletín narrativo" }))
    expect(screen.getByText(/Restricción parcial del riego agrícola/)).toBeInTheDocument()
  })

  describe("descargas", () => {
    it("'Descargar PDF' llama a window.print", async () => {
      const user = userEvent.setup()
      render(<MediosDashboard onLogout={() => {}} token="tok" />)
      await screen.findByText(/Semana 52/)
      await user.click(screen.getByRole("button", { name: "Boletín narrativo" }))

      await user.click(screen.getByRole("button", { name: /descargar pdf/i }))
      expect(window.print).toHaveBeenCalledTimes(1)
    })

    it("'Descargar imagen' y 'Descargar Markdown' generan un blob y disparan la descarga", async () => {
      const user = userEvent.setup()
      render(<MediosDashboard onLogout={() => {}} token="tok" />)
      await screen.findByText(/Semana 52/)
      await user.click(screen.getByRole("button", { name: "Boletín narrativo" }))

      await user.click(screen.getByRole("button", { name: /descargar imagen/i }))
      await user.click(screen.getByRole("button", { name: /descargar markdown/i }))

      expect(URL.createObjectURL).toHaveBeenCalledTimes(2)
      expect(HTMLAnchorElement.prototype.click).toHaveBeenCalledTimes(2)
    })
  })

  it("Comparativa: grafica el historial junto a las sequías históricas (sin endpoint, sigue mockeado)", async () => {
    const user = userEvent.setup()
    const { container } = render(<MediosDashboard onLogout={() => {}} token="tok" />)
    await screen.findByText(/Semana 52/)

    await user.click(screen.getByRole("button", { name: "Comparativa" }))

    expect(container.querySelector("svg")).toBeTruthy()
    for (const s of sequiasHistoricas) {
      expect(screen.getByText(s.anio)).toBeInTheDocument()
    }
  })

  it("solo muestra boletines donde publicado=true", async () => {
    const mixBoletines = [
      { ...boletinesMock[0], publicado: true },
      { ...boletinesMock[1], id: "bol-unpub", publicado: false },
    ]
    mockApiFetch.mockResolvedValue(mixBoletines)

    render(<MediosDashboard onLogout={() => {}} token="tok" />)

    expect(await screen.findByText(/Semana 52/)).toBeInTheDocument()
    expect(screen.queryByText(/Semana 51/)).not.toBeInTheDocument()
  })

  it("si no hay boletines publicados, muestra un estado vacío claro", async () => {
    mockApiFetch.mockResolvedValue([])

    render(<MediosDashboard onLogout={() => {}} token="tok" />)

    expect(await screen.findByText(/a[uú]n no hay boletines publicados/i)).toBeInTheDocument()
  })
})
