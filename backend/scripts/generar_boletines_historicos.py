"""Genera los 12 boletines históricos sintéticos que alimentan el RAG (§5 de
arquitectura-hidroalerta.md). No son datos reales: sirven para que la
similitud coseno del punto 7 tenga contra qué comparar hallazgos nuevos.

Mismo formato que assets/boletin_referencia.md (4 secciones fijas). Semanas,
años y severidades variadas a propósito, incluyendo las sequías mencionadas
en el reto (2011, 2020, 2023) y años de comparación con niveles normales.

Uso: python -m backend.scripts.generar_boletines_historicos
Escribe en backend/data/boletines_historicos/BOLETIN_{anio}_S{semana}.md
"""

from __future__ import annotations

from pathlib import Path

SALIDA = Path(__file__).resolve().parents[2] / "backend" / "data" / "boletines_historicos"

_EMOJI = {"verde": "🟢", "amarillo": "🟡", "naranja": "🟠", "rojo": "🔴"}

_NARRATIVA = {
    "verde": (
        "Temporada de lluvias favorable. Los embalses del Valle del Guadiana se mantienen "
        "en niveles adecuados y no hay restricciones de consumo."
    ),
    "amarillo": (
        "Se observa un descenso moderado respecto al histórico. Se recomienda vigilancia y "
        "uso responsable del agua, sin restricciones obligatorias todavía."
    ),
    "naranja": (
        "Sequía moderada en desarrollo. Se recomienda restricción parcial del riego agrícola "
        "y campañas activas de ahorro en zonas urbanas."
    ),
    "rojo": (
        "Sequía severa. Los embalses operan en niveles críticos; se activa racionamiento y "
        "prioridad absoluta al consumo humano sobre el riego."
    ),
}

_RECOMENDACION = {
    "verde": "Sin acciones adicionales. Mantener monitoreo semanal de rutina.",
    "amarillo": "Ayuntamiento: campaña de ahorro voluntario nivel 1 en colonias de mayor consumo.",
    "naranja": "Ayuntamiento: restricción parcial de riego agrícola y campaña de ahorro obligatoria.",
    "rojo": "Gobierno estatal: racionamiento por horario y prioridad de consumo humano.",
}

# id, semana, anio, rango_fechas, color, nivel_promedio, precip_mm, delta_pp, temp_c, nota_contexto
_ENTRADAS: list[tuple[str, int, int, str, str, float, float, float, float, str]] = [
    ("2011-S30", 30, 2011, "25–31 jul 2011", "rojo", 16.4, 6.1, -11.2, 39.8,
     "Una de las sequías más severas registradas en el Valle del Guadiana."),
    ("2011-S45", 45, 2011, "7–13 nov 2011", "rojo", 14.1, 4.3, -9.5, 33.5,
     "El déficit acumulado del año agrava el panorama hacia el cierre de 2011."),
    ("2018-S42", 42, 2018, "15–21 oct 2018", "verde", 73.2, 98.4, 1.8, 22.9,
     "Año de referencia con precipitación por encima del promedio histórico."),
    ("2019-S10", 10, 2019, "4–10 mar 2019", "verde", 68.5, 91.7, 0.6, 25.1,
     "Cierre de temporada invernal con embalses en niveles saludables."),
    ("2020-S15", 15, 2020, "6–12 abr 2020", "verde", 65.9, 87.3, 0.4, 27.4,
     "Antes del inicio del declive que marcaría el resto del año."),
    ("2020-S40", 40, 2020, "28 sep–4 oct 2020", "amarillo", 48.3, 52.6, -1.9, 31.2,
     "Primeras señales de la sequía 2020 tras un verano de lluvias irregulares."),
    ("2020-S48", 48, 2020, "23–29 nov 2020", "naranja", 33.7, 21.8, -5.4, 35.0,
     "La sequía 2020 se profundiza; La Tinaja se acerca al umbral rojo."),
    ("2021-S25", 25, 2021, "14–20 jun 2021", "amarillo", 51.6, 58.9, -1.1, 30.8,
     "Recuperación parcial tras la sequía del año anterior."),
    ("2022-S18", 18, 2022, "2–8 may 2022", "amarillo", 49.4, 47.5, -2.3, 32.6,
     "Nivel estable pero por debajo del promedio histórico para la fecha."),
    ("2023-S20", 20, 2023, "15–21 may 2023", "naranja", 30.8, 24.2, -4.7, 36.3,
     "Inicio de la sequía 2023, con déficit de precipitación en la sierra."),
    ("2023-S35", 35, 2023, "28 ago–3 sep 2023", "rojo", 19.2, 9.4, -8.9, 38.9,
     "Punto más crítico de la sequía 2023: las 3 presas por debajo del 25%."),
    ("2024-S30", 30, 2024, "22–28 jul 2024", "naranja", 34.9, 26.7, -3.8, 35.4,
     "Comparable en magnitud al inicio de la sequía 2023 un año antes."),
]

_PLANTILLA = """# Boletín HidroAlerta · Semana {semana} ({rango_fechas})

**Nivel de alerta global:** {emoji} **{color_upper}**
**Estado:** Boletín histórico sintético · generado para el motor de RAG

---

## Estado de presas

| Presa | Nivel actual (%) | Δ vs. mes anterior | Tendencia |
|---|---:|---:|:---:|
| La Tinaja | {nivel_tinaja:.1f} | {delta_pp:+.1f} pp | {tendencia} |
| Peña del Águila | {nivel_penia:.1f} | {delta_pp:+.1f} pp | {tendencia} |
| Guadalupe Victoria | {nivel_guadalupe:.1f} | {delta_pp:+.1f} pp | {tendencia} |
| **Promedio ponderado** | **{nivel_promedio:.1f}** | **{delta_pp:+.1f} pp** | — |

**Interpretación:** el promedio ponderado ({nivel_promedio:.1f}%) se ubica en rango **{color_upper}**.

---

## Precipitación

| Estación | Acumulado mes (mm) |
|---|---:|
| Media estatal | {precip_mm:.1f} |

**Interpretación:** precipitación acumulada de {precip_mm:.1f} mm, rango **{color_upper}** según umbrales.json.

---

## Temperatura

**Región Valle del Guadiana** — semana {semana}:
- Tmax promedio: **{temp_c:.1f} °C**

---

## Alerta y recomendación

**Nivel global: {emoji} {color_upper}** — {narrativa}

**Recomendación operativa:** {recomendacion}

*Nota de contexto histórico: {nota_contexto}*

---

*Boletín histórico sintético · HidroAlerta · usado únicamente como corpus del motor de RAG (arquitectura-hidroalerta.md §5), no representa una medición real.*
"""


def _tendencia(delta_pp: float) -> str:
    if delta_pp > 0.3:
        return "↑"
    if delta_pp < -0.3:
        return "↓"
    return "→"


def generar() -> list[Path]:
    SALIDA.mkdir(parents=True, exist_ok=True)
    escritos = []
    for (
        _id,
        semana,
        anio,
        rango_fechas,
        color,
        nivel_promedio,
        precip_mm,
        delta_pp,
        temp_c,
        nota_contexto,
    ) in _ENTRADAS:
        contenido = _PLANTILLA.format(
            semana=semana,
            rango_fechas=rango_fechas,
            emoji=_EMOJI[color],
            color_upper=color.upper(),
            nivel_tinaja=max(0.0, nivel_promedio - 6.0),
            nivel_penia=min(100.0, nivel_promedio + 8.0),
            nivel_guadalupe=max(0.0, nivel_promedio - 2.0),
            nivel_promedio=nivel_promedio,
            delta_pp=delta_pp,
            tendencia=_tendencia(delta_pp),
            precip_mm=precip_mm,
            temp_c=temp_c,
            narrativa=_NARRATIVA[color],
            recomendacion=_RECOMENDACION[color],
            nota_contexto=nota_contexto,
        )
        ruta = SALIDA / f"BOLETIN_{anio}_S{semana:02d}.md"
        ruta.write_text(contenido, encoding="utf-8")
        escritos.append(ruta)
    return escritos


if __name__ == "__main__":
    for ruta in generar():
        print(f"[+] {ruta.relative_to(SALIDA.parents[2])}")
