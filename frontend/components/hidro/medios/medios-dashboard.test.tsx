import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MediosDashboard } from "./medios-dashboard"
import { boletines, boletinActual, sequiasHistoricas } from "@/lib/hidro-data"

describe("MediosDashboard", () => {
  it("Inicio: lista los boletines publicados", () => {
    render(<MediosDashboard onLogout={() => {}} />)
    for (const b of boletines) {
      expect(screen.getByText(new RegExp(`Semana ${b.semana}`))).toBeInTheDocument()
    }
  })

  it("Boletín narrativo: muestra el texto narrativo de la semana actual", async () => {
    const user = userEvent.setup()
    render(<MediosDashboard onLogout={() => {}} />)

    await user.click(screen.getByRole("button", { name: "Boletín narrativo" }))
    expect(screen.getByText(boletinActual.narrativo)).toBeInTheDocument()
  })

  describe("descargas", () => {
    beforeEach(() => {
      vi.stubGlobal("URL", { createObjectURL: vi.fn(() => "blob:mock"), revokeObjectURL: vi.fn() })
      vi.spyOn(window, "print").mockImplementation(() => {})
      vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {})
    })

    afterEach(() => {
      vi.unstubAllGlobals()
      vi.restoreAllMocks()
    })

    it("'Descargar PDF' llama a window.print", async () => {
      const user = userEvent.setup()
      render(<MediosDashboard onLogout={() => {}} />)
      await user.click(screen.getByRole("button", { name: "Boletín narrativo" }))

      await user.click(screen.getByRole("button", { name: /descargar pdf/i }))
      expect(window.print).toHaveBeenCalledTimes(1)
    })

    it("'Descargar imagen' y 'Descargar Markdown' generan un blob y disparan la descarga", async () => {
      const user = userEvent.setup()
      render(<MediosDashboard onLogout={() => {}} />)
      await user.click(screen.getByRole("button", { name: "Boletín narrativo" }))

      await user.click(screen.getByRole("button", { name: /descargar imagen/i }))
      await user.click(screen.getByRole("button", { name: /descargar markdown/i }))

      expect(URL.createObjectURL).toHaveBeenCalledTimes(2)
      expect(HTMLAnchorElement.prototype.click).toHaveBeenCalledTimes(2)
    })
  })

  it("Comparativa: grafica el historial junto a las sequías históricas", async () => {
    const user = userEvent.setup()
    const { container } = render(<MediosDashboard onLogout={() => {}} />)

    await user.click(screen.getByRole("button", { name: "Comparativa" }))

    expect(container.querySelector("svg")).toBeTruthy()
    for (const s of sequiasHistoricas) {
      expect(screen.getByText(s.anio)).toBeInTheDocument()
    }
  })
})
