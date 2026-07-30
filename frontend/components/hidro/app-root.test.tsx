import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { AppRoot } from "./app-root"

async function loginComo(rol: "gobierno" | "ayuntamiento" | "medios" | "agricultor") {
  const user = userEvent.setup()
  render(<AppRoot />)
  await user.selectOptions(screen.getByLabelText("Tipo de cuenta"), rol)
  await user.click(screen.getByRole("button", { name: /iniciar sesión/i }))
}

describe("AppRoot", () => {
  it("muestra el login antes de autenticarse", () => {
    render(<AppRoot />)
    expect(screen.getByRole("button", { name: /iniciar sesión/i })).toBeInTheDocument()
  })

  it("redirige a Gobierno si rol=gobierno", async () => {
    await loginComo("gobierno")
    expect(screen.getByText("Gobierno del Estado")).toBeInTheDocument()
    // SidebarLayout duplica los items de navegación entre el aside de
    // escritorio y el nav scroller móvil (ambos montados a la vez en jsdom).
    expect(screen.getAllByText("Auditoría").length).toBeGreaterThan(0)
  })

  it("redirige a Ayuntamiento si rol=ayuntamiento", async () => {
    await loginComo("ayuntamiento")
    expect(screen.getByText("Ayuntamiento de Durango")).toBeInTheDocument()
  })

  it("redirige a Medios si rol=medios", async () => {
    await loginComo("medios")
    expect(screen.getByText("Boletín narrativo")).toBeInTheDocument()
  })

  it("redirige a Agricultor si rol=agricultor", async () => {
    await loginComo("agricultor")
    expect(screen.getByText("Siembra")).toBeInTheDocument()
  })
})
