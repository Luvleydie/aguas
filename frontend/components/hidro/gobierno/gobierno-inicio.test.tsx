import { describe, expect, it, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { GobiernoInicio } from "./gobierno-inicio"
import { boletinActual } from "@/lib/hidro-data"

describe("GobiernoInicio", () => {
  it("muestra el resumen y la semana del boletín más reciente", () => {
    render(<GobiernoInicio onNavigate={() => {}} />)
    expect(screen.getByText(new RegExp(`Semana ${boletinActual.semana}`))).toBeInTheDocument()
    expect(screen.getByText(boletinActual.resumen)).toBeInTheDocument()
  })

  it("'Ver boletín completo' navega a boletin", async () => {
    const onNavigate = vi.fn()
    const user = userEvent.setup()
    render(<GobiernoInicio onNavigate={onNavigate} />)

    await user.click(screen.getByRole("button", { name: /ver boletín completo/i }))
    expect(onNavigate).toHaveBeenCalledWith("boletin")
  })

  it("cada acceso rápido navega a su id correspondiente", async () => {
    const onNavigate = vi.fn()
    const user = userEvent.setup()
    render(<GobiernoInicio onNavigate={onNavigate} />)

    await user.click(screen.getByRole("button", { name: /generar boletín/i }))
    expect(onNavigate).toHaveBeenCalledWith("generar")

    await user.click(screen.getByRole("button", { name: /tendencias/i }))
    expect(onNavigate).toHaveBeenCalledWith("tendencias")
  })
})
