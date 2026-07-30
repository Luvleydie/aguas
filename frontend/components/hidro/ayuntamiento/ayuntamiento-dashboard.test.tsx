import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { AyuntamientoDashboard } from "./ayuntamiento-dashboard"
import { boletinActualReal } from "@/lib/boletin-real-mock"

describe("AyuntamientoDashboard", () => {
  it("Inicio: muestra la semana y el semáforo, y permite marcar acción tomada", async () => {
    const user = userEvent.setup()
    render(<AyuntamientoDashboard onLogout={() => {}} />)

    expect(screen.getByText(new RegExp(`Semana ${boletinActualReal.semana}`))).toBeInTheDocument()
    expect(screen.getByRole("img", { name: /Nivel de alerta/ })).toBeInTheDocument()

    const boton = screen.getByRole("button", { name: /marcar acción tomada/i })
    await user.click(boton)
    expect(screen.getByRole("button", { name: /acción registrada/i })).toBeDisabled()
  })

  it("Boletín: solo lectura, no muestra el bloque de publicar", async () => {
    const user = userEvent.setup()
    render(<AyuntamientoDashboard onLogout={() => {}} />)

    await user.click(screen.getByRole("button", { name: "Boletín" }))

    expect(screen.getByText("Estado de presas")).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: /publicar boletín/i })).toBeNull()
  })

  it("Tendencias: grafica el historial de la primera presa", async () => {
    const user = userEvent.setup()
    const { container } = render(<AyuntamientoDashboard onLogout={() => {}} />)

    await user.click(screen.getByRole("button", { name: "Tendencias" }))

    expect(screen.getByText("Nivel de presas locales")).toBeInTheDocument()
    expect(container.querySelector("svg")).toBeTruthy()
  })
})
