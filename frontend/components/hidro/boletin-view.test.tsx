import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { BoletinView } from "./boletin-view"
import { boletinActualReal } from "@/lib/boletin-real-mock"
import type { BoletinReal } from "@/lib/boletin-adapter"

describe("BoletinView (contrato real: markdown + hallazgos)", () => {
  it("renderiza las 4 secciones fijas parseadas del markdown del Narrador", () => {
    render(<BoletinView boletin={boletinActualReal} />)

    expect(screen.getByText("Estado de presas")).toBeInTheDocument()
    expect(screen.getByText("Precipitación")).toBeInTheDocument()
    expect(screen.getByText("Temperatura")).toBeInTheDocument()
    expect(screen.getByText("Alerta y recomendación")).toBeInTheDocument()
    expect(screen.getByText(/Promedio ponderado/)).toBeInTheDocument()
    expect(screen.getByText(/53\.7 mm/)).toBeInTheDocument()
  })

  it("muestra la semana, el año (no hay columna fecha en el schema real) y el semáforo", () => {
    render(<BoletinView boletin={boletinActualReal} />)
    expect(screen.getByText(/Semana 42/)).toBeInTheDocument()
    expect(screen.getByText(/2024/)).toBeInTheDocument()
    expect(screen.getByRole("img", { name: /Nivel de alerta: Precaución/ })).toBeInTheDocument()
  })

  it("el panel de hallazgos crudos muestra cada métrica con su sparkline (regla 6)", async () => {
    const user = userEvent.setup()
    render(<BoletinView boletin={boletinActualReal} />)

    await user.click(screen.getByRole("button", { name: /ver datos crudos/i }))

    for (const h of boletinActualReal.hallazgos ?? []) {
      expect(screen.getByText(h.contexto)).toBeInTheDocument()
      expect(screen.getByText(h.sparkline)).toBeInTheDocument()
    }
  })

  it("sin hallazgos (roles distintos de gobierno leen boletines_publico, sin hallazgos_json), no muestra el panel de datos crudos", () => {
    const boletinSinHallazgos: BoletinReal = { ...boletinActualReal, hallazgos: undefined }
    render(<BoletinView boletin={boletinSinHallazgos} />)
    expect(screen.queryByRole("button", { name: /ver datos crudos/i })).toBeNull()
  })

  it("con showPublish, el botón publica y refleja boletin.publicado", async () => {
    const user = userEvent.setup()
    render(<BoletinView boletin={boletinActualReal} showPublish />)

    expect(screen.getByText("Boletín en borrador")).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: /publicar boletín/i }))
    expect(screen.getByText("Boletín publicado")).toBeInTheDocument()
  })

  it("sin showPublish, no se muestra el bloque de publicación", () => {
    render(<BoletinView boletin={boletinActualReal} />)
    expect(screen.queryByText(/Boletín en borrador|Boletín publicado/)).toBeNull()
  })
})
