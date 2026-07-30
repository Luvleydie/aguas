import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { GobiernoUsuarios } from "./gobierno-usuarios"
import { usuarios } from "@/lib/hidro-data"

describe("GobiernoUsuarios", () => {
  it("lista nombre y rol de cada usuario", () => {
    render(<GobiernoUsuarios />)
    for (const u of usuarios) {
      expect(screen.getByText(u.nombre)).toBeInTheDocument()
      expect(screen.getByText(u.rol)).toBeInTheDocument()
    }
  })

  it("el toggle de WhatsApp esta deshabilitado (fase extra, no forma parte del entregable local)", async () => {
    const user = userEvent.setup()
    render(<GobiernoUsuarios />)

    const primerToggle = screen.getAllByRole("switch")[0]
    expect(primerToggle).toBeDisabled()

    const estadoInicial = primerToggle.getAttribute("aria-checked")
    await user.click(primerToggle)
    expect(primerToggle.getAttribute("aria-checked")).toBe(estadoInicial)
  })
})
