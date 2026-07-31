import { describe, expect, it, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { Login } from "./login"

vi.mock("@/lib/api-client", () => ({
  login: vi.fn(),
  register: vi.fn(),
}))

describe("Login", () => {
  it("el campo de contraseña tiene un botón de ojo para mostrar/ocultar", () => {
    render(<Login onLogin={async () => ({ id: "1", email: "a@b.com", rol: "gobierno" })} />)

    const passwordInput = screen.getByLabelText("Contraseña")
    expect(passwordInput).toHaveAttribute("type", "password")

    const toggleBtn = screen.getByRole("button", { name: /mostrar contraseña/i })
    expect(toggleBtn).toBeInTheDocument()
  })

  it("al hacer clic en el ojo, cambia a type=text y el ícono cambia a EyeOff", async () => {
    const user = userEvent.setup()
    render(<Login onLogin={async () => ({ id: "1", email: "a@b.com", rol: "gobierno" })} />)

    const passwordInput = screen.getByLabelText("Contraseña")
    const toggleBtn = screen.getByRole("button", { name: /mostrar contraseña/i })

    await user.click(toggleBtn)

    expect(passwordInput).toHaveAttribute("type", "text")
    expect(screen.getByRole("button", { name: /ocultar contraseña/i })).toBeInTheDocument()
  })

  it("al hacer clic dos veces en el ojo, vuelve a type=password", async () => {
    const user = userEvent.setup()
    render(<Login onLogin={async () => ({ id: "1", email: "a@b.com", rol: "gobierno" })} />)

    const passwordInput = screen.getByLabelText("Contraseña")
    const toggleBtn = screen.getByRole("button", { name: /mostrar contraseña/i })

    await user.click(toggleBtn)
    await user.click(screen.getByRole("button", { name: /ocultar contraseña/i }))

    expect(passwordInput).toHaveAttribute("type", "password")
  })
})
