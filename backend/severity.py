"""Clasificación de umbrales: especificada, aún no implementada."""

from __future__ import annotations

from backend.contracts import Metrica, Severidad


def clasificar_severidad(metrica: Metrica, valor: float) -> Severidad:
    del metrica, valor
    raise NotImplementedError("ROJO esperado: clasificación de severidad pendiente")

