import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { act, fireEvent, render, screen } from "@testing-library/react"
import { GobiernoGenerar } from "./gobierno-generar"

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe("GobiernoGenerar", () => {
  it("permite elegir semana del 1 al 52 y arranca deshabilitada en 'Generando...'", () => {
    render(<GobiernoGenerar onDone={() => {}} />)

    const select = screen.getByLabelText("Semana del boletín") as HTMLSelectElement
    expect(select.options).toHaveLength(52)

    fireEvent.click(screen.getByRole("button", { name: /generar boletín/i }))
    expect(screen.getByRole("button", { name: /generando/i })).toBeDisabled()
  })

  it("avanza Explorador → Estadista → Narrador → Agrónomo y ofrece 'Ver boletín' al terminar", async () => {
    const onDone = vi.fn()
    render(<GobiernoGenerar onDone={onDone} />)

    fireEvent.click(screen.getByRole("button", { name: /generar boletín/i }))

    for (let i = 0; i < 4; i++) {
      await act(async () => {
        await vi.advanceTimersByTimeAsync(1100)
      })
    }

    expect(screen.getByText(/generado correctamente/i)).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: /ver boletín/i }))
    expect(onDone).toHaveBeenCalledTimes(1)
  })
})
