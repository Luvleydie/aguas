import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import { Semaforo } from "./semaforo"

describe("Semaforo", () => {
  it("renderiza el nivel con su etiqueta accesible", () => {
    render(<Semaforo nivel="amarillo" />)
    expect(screen.getByRole("img", { name: /Nivel de alerta: Precaución/ })).toBeInTheDocument()
  })

  it("size=xl reduce el círculo en viewports angostos para no desbordar (≤380px y ≤340px)", () => {
    render(<Semaforo nivel="verde" size="xl" />)
    const circulo = screen.getByRole("img")
    expect(circulo).toHaveClass("h-64", "w-64", "max-[380px]:h-56", "max-[380px]:w-56", "max-[340px]:h-48", "max-[340px]:w-48")
  })
})
