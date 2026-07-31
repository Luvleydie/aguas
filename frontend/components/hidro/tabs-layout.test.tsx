import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import { TabsLayout } from "./tabs-layout"

const tabs = [
  { id: "inicio", label: "Inicio" },
  { id: "boletin", label: "Boletín" },
]

describe("TabsLayout", () => {
  it("la franja de color queda de borde a borde, pero el contenido queda en una columna mas angosta (max-w-2xl) para no verse desbalanceado", () => {
    render(
      <TabsLayout tabs={tabs} active="inicio" onSelect={() => {}} roleName="Ayuntamiento de Durango" onLogout={() => {}}>
        <p>contenido</p>
      </TabsLayout>,
    )

    const filaSuperior = screen.getByText("Ayuntamiento de Durango").closest("div.mx-auto")
    expect(filaSuperior).toHaveClass("max-w-2xl")
    expect(filaSuperior).not.toHaveClass("max-w-4xl")

    const nav = screen.getByRole("navigation")
    expect(nav).toHaveClass("max-w-2xl")

    const main = screen.getByText("contenido").closest("main")
    expect(main).toHaveClass("max-w-2xl")
  })
})
