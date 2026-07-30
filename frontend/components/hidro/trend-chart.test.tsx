import { describe, expect, it } from "vitest"
import { render } from "@testing-library/react"
import { TrendChart } from "./trend-chart"

const data = [
  { semana: "S41", nivel: 58 },
  { semana: "S42", nivel: 55 },
  { semana: "S43", nivel: 50 },
]

describe("TrendChart", () => {
  it("renderiza un svg con la serie completa (variante default)", () => {
    const { container } = render(<TrendChart data={data} />)
    expect(container.querySelector("svg")).toBeTruthy()
    expect(container.querySelectorAll(".recharts-cartesian-grid").length).toBe(1)
  })

  it("variante simple: oculta la grilla cartesiana", () => {
    const { container } = render(<TrendChart data={data} simple />)
    expect(container.querySelector(".recharts-cartesian-grid")).toBeNull()
  })

  it("variante con anotaciones: dibuja una ReferenceLine por cada referencia", () => {
    const { container } = render(
      <TrendChart data={data} references={[{ y: 25, label: "Nivel crítico" }]} />,
    )
    expect(container.querySelectorAll(".recharts-reference-line").length).toBe(1)
    expect(container.textContent).toContain("Nivel crítico")
  })

  it("sin referencias no dibuja ninguna ReferenceLine", () => {
    const { container } = render(<TrendChart data={data} />)
    expect(container.querySelectorAll(".recharts-reference-line").length).toBe(0)
  })
})
