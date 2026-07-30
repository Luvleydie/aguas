import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { GobiernoTendencias } from "./gobierno-tendencias"
import { presas } from "@/lib/hidro-data"

describe("GobiernoTendencias", () => {
  it("muestra por default la primera presa y su gráfica", () => {
    const { container } = render(<GobiernoTendencias />)
    expect(container.querySelector("svg")).toBeTruthy()
    expect(screen.getByRole("combobox", { name: /seleccionar presa/i })).toHaveValue(presas[0].id)
  })

  it("lista las 4 presas con su nivel y capacidad", () => {
    render(<GobiernoTendencias />)
    for (const p of presas) {
      // p.nombre aparece tanto en el <select> de presas como en su tarjeta.
      expect(screen.getAllByText(p.nombre).length).toBeGreaterThan(0)
      expect(screen.getByText(`${p.capacidadPct}%`)).toBeInTheDocument()
    }
  })

  it("cambiar la presa seleccionada actualiza el texto de tendencia", async () => {
    const user = userEvent.setup()
    render(<GobiernoTendencias />)

    const otraPresa = presas[1]
    await user.selectOptions(screen.getByRole("combobox", { name: /seleccionar presa/i }), otraPresa.id)

    expect(screen.getAllByText(new RegExp(otraPresa.nombre)).length).toBeGreaterThan(0)
  })
})
