import { describe, expect, it } from "vitest"
import { readFileSync } from "node:fs"
import { join } from "node:path"
import { parseSeccionesBoletin } from "./boletin-adapter"

const fixture = JSON.parse(
  readFileSync(join(__dirname, "..", "..", "tests", "fixtures", "boletin.json"), "utf-8"),
) as { markdown: string }

describe("parseSeccionesBoletin", () => {
  it("separa las 4 secciones fijas del markdown del Narrador (oráculo real)", () => {
    const secciones = parseSeccionesBoletin(fixture.markdown)

    expect(secciones.presas).toContain("Promedio ponderado")
    expect(secciones.presas).toContain("**50.8 %**")
    expect(secciones.precipitacion).toContain("53.7 mm")
    expect(secciones.temperatura).toContain("26.3")
    expect(secciones.alerta).toContain("Nivel global")
    expect(secciones.alerta).toContain("AMARILLO")
  })

  it("no incluye el encabezado de la sección siguiente en el contenido de la anterior", () => {
    const secciones = parseSeccionesBoletin(fixture.markdown)

    expect(secciones.presas).not.toContain("Precipitación")
    expect(secciones.precipitacion).not.toContain("Temperatura")
  })

  it("ignora numeración opcional en el encabezado (## 1 · Estado de presas)", () => {
    const markdown = [
      "# Boletín HidroAlerta · Semana 1",
      "",
      "## 1 · Estado de presas",
      "",
      "contenido presas",
      "",
      "## 2 · Precipitación",
      "",
      "contenido lluvia",
      "",
      "## 3 · Temperatura",
      "",
      "contenido temp",
      "",
      "## 4 · Alerta y recomendación",
      "",
      "contenido alerta",
    ].join("\n")

    const secciones = parseSeccionesBoletin(markdown)

    expect(secciones.presas.trim()).toBe("contenido presas")
    expect(secciones.precipitacion.trim()).toBe("contenido lluvia")
    expect(secciones.temperatura.trim()).toBe("contenido temp")
    expect(secciones.alerta.trim()).toBe("contenido alerta")
  })

  it("hace match sin distinguir mayúsculas/minúsculas en el título", () => {
    const markdown = [
      "## ESTADO DE PRESAS",
      "a",
      "## precipitación",
      "b",
      "## Temperatura",
      "c",
      "## alerta y recomendación",
      "d",
    ].join("\n\n")

    const secciones = parseSeccionesBoletin(markdown)

    expect(secciones.presas.trim()).toBe("a")
    expect(secciones.precipitacion.trim()).toBe("b")
    expect(secciones.temperatura.trim()).toBe("c")
    expect(secciones.alerta.trim()).toBe("d")
  })

  it("lanza un error listando las secciones fijas que falten", () => {
    const markdown = "## Estado de presas\n\nsolo esta sección"

    expect(() => parseSeccionesBoletin(markdown)).toThrow(/Precipitación/)
    expect(() => parseSeccionesBoletin(markdown)).toThrow(/Temperatura/)
    expect(() => parseSeccionesBoletin(markdown)).toThrow(/Alerta y recomendación/)
  })
})
