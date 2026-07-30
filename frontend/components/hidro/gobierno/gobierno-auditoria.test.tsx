import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import { GobiernoAuditoria } from "./gobierno-auditoria"
import { pasosAgentes } from "@/lib/hidro-data"

describe("GobiernoAuditoria", () => {
  it("lista los 4 agentes en orden con su descripción", () => {
    render(<GobiernoAuditoria />)
    const items = screen.getAllByRole("listitem")
    expect(items).toHaveLength(pasosAgentes.length)
    pasosAgentes.forEach((paso, i) => {
      expect(items[i]).toHaveTextContent(paso.agente)
      expect(items[i]).toHaveTextContent(paso.descripcion)
    })
  })
})
