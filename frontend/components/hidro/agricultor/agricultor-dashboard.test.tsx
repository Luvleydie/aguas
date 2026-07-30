import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { AgricultorDashboard } from "./agricultor-dashboard"
import { recomendacionActualReal } from "@/lib/recomendacion-real-mock"
import { historialSemanas } from "@/lib/hidro-data"

describe("AgricultorDashboard", () => {
  it("Inicio: muestra el mensaje_whatsapp del Agrónomo (frase simple, ya sin tecnicismos)", () => {
    render(<AgricultorDashboard onLogout={() => {}} />)
    expect(screen.getByText(recomendacionActualReal.mensaje_whatsapp)).toBeInTheDocument()
  })

  it("Siembra: muestra el cultivo priorizado, la acción y la ventana de siembra reales", async () => {
    const user = userEvent.setup()
    render(<AgricultorDashboard onLogout={() => {}} />)

    await user.click(screen.getByRole("button", { name: "Siembra" }))

    expect(screen.getByText("Frijol")).toBeInTheDocument()
    expect(screen.getByText("Retrasar siembra")).toBeInTheDocument()
    expect(screen.getByText(/Junio – Agosto/)).toBeInTheDocument()
    expect(screen.getByText(recomendacionActualReal.razon)).toBeInTheDocument()
  })

  it("Historial: dibuja un punto por cada semana de historialSemanas", async () => {
    const user = userEvent.setup()
    render(<AgricultorDashboard onLogout={() => {}} />)

    await user.click(screen.getByRole("button", { name: "Historial" }))
    expect(screen.getAllByLabelText(/^Semana \d+:/)).toHaveLength(historialSemanas.length)
  })
})
