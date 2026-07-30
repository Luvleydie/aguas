import { describe, expect, it } from "vitest"
import { readFileSync } from "node:fs"
import { join } from "node:path"
import { accionLabel, ventanaSiembra } from "./recomendacion-adapter"
import type { AccionAgricola, Cultivo } from "./recomendacion-adapter"

const fixture = JSON.parse(
  readFileSync(join(__dirname, "..", "..", "tests", "fixtures", "recomendacion_agricola.json"), "utf-8"),
) as { cultivo_prioritario: Cultivo; accion: AccionAgricola }

describe("ventanaSiembra", () => {
  it("calcula la ventana de siembra del cultivo priorizado (oráculo: assets/cultivos_valle_guadiana.csv)", () => {
    expect(ventanaSiembra(fixture.cultivo_prioritario)).toBe("Junio – Agosto")
  })

  it("cubre los 3 cultivos de cultivos_valle_guadiana.csv", () => {
    expect(ventanaSiembra("maiz")).toBe("Abril – Junio")
    expect(ventanaSiembra("frijol")).toBe("Junio – Agosto")
    expect(ventanaSiembra("alfalfa")).toBe("Septiembre – Noviembre")
  })
})

describe("accionLabel", () => {
  it("traduce la acción del oráculo a lenguaje simple", () => {
    expect(accionLabel(fixture.accion)).toBe("Retrasar siembra")
  })

  it("cubre las 5 acciones del contrato (AccionAgricola)", () => {
    const acciones: AccionAgricola[] = [
      "sembrar_normal",
      "retrasar_siembra",
      "reducir_riego",
      "cultivo_alternativo",
      "sin_accion_urgente",
    ]
    for (const a of acciones) {
      expect(accionLabel(a)).toEqual(expect.any(String))
      expect(accionLabel(a).length).toBeGreaterThan(0)
    }
  })
})
