import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import { TabsLayout } from "./tabs-layout"

const tabs = [
  { id: "inicio", label: "Inicio" },
  { id: "boletin", label: "Boletín" },
]

describe("TabsLayout", () => {
  it("el header es una tarjeta redondeada y centrada, no una franja de borde a borde", () => {
    render(
      <TabsLayout tabs={tabs} active="inicio" onSelect={() => {}} roleName="Ayuntamiento de Durango" onLogout={() => {}}>
        <p>contenido</p>
      </TabsLayout>,
    )

    const header = screen.getByText("Ayuntamiento de Durango").closest("header")
    expect(header).toHaveClass("rounded-3xl")

    const wrapper = header?.parentElement
    expect(wrapper).toHaveClass("mx-auto", "max-w-2xl")

    const main = screen.getByText("contenido").closest("main")
    expect(main).toHaveClass("max-w-2xl")
  })
})
