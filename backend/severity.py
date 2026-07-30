"""Clasificación verificable de severidad a partir de ``umbrales.json``."""

from __future__ import annotations

import json
import math
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from backend.contracts import Metrica, NivelAlerta, Severidad

DEFAULT_UMBRALES_PATH = Path(__file__).resolve().parent / "data" / "umbrales.json"

_NIVEL_ALERTA_POR_SEVERIDAD: dict[Severidad, NivelAlerta] = dict(zip(Severidad, NivelAlerta, strict=True))

_SEVERIDAD_POR_COLOR = {
    "verde": Severidad.INFO,
    "amarillo": Severidad.WARN,
    "naranja": Severidad.ALERTA,
    "rojo": Severidad.CRITICO,
}


def _umbrales_path() -> Path:
    return Path(os.environ.get("HIDROALERTA_DATA_DIR", DEFAULT_UMBRALES_PATH.parent)) / "umbrales.json"


@lru_cache(maxsize=8)
def _cargar_umbrales(path: Path) -> dict[str, Any]:
    contenido = json.loads(path.read_text(encoding="utf-8"))
    metricas = contenido["metricas"]
    orden = contenido["alerta_global"]["orden"]
    if not isinstance(metricas, dict) or not isinstance(orden, list) or not orden:
        raise ValueError(f"Configuración de umbrales inválida: {path}")
    return contenido


def clasificar_severidad(metrica: Metrica, valor: float) -> Severidad:
    """Clasifica ``valor`` según ``umbrales.json``, con rangos inclusivos.

    El orden oficial (``alerta_global.orden``) decide el ganador si dos
    rangos comparten un extremo, evitando reglas duplicadas en código.
    """

    metrica_normalizada = Metrica(metrica)

    if isinstance(valor, bool):
        raise TypeError("El valor debe ser numérico, no booleano")
    numero = float(valor)
    if not math.isfinite(numero):
        raise ValueError("El valor debe ser finito")

    configuracion = _cargar_umbrales(_umbrales_path())
    try:
        rangos = configuracion["metricas"][metrica_normalizada.value]
        orden = configuracion["alerta_global"]["orden"]
    except KeyError as exc:
        raise ValueError(f"No hay umbrales para la métrica {metrica_normalizada.value!r}") from exc

    for color in orden:
        severidad = _SEVERIDAD_POR_COLOR[color]
        minimo = float(rangos[color]["min"])
        maximo = float(rangos[color]["max"])
        if minimo <= numero <= maximo:
            return severidad

    raise ValueError(f"Valor {numero} fuera de los rangos de {metrica_normalizada.value!r}")


def nivel_alerta_global(severidades: list[Severidad]) -> NivelAlerta:
    """Alerta global = severidad MÁXIMA entre los hallazgos evaluados (umbrales.json)."""

    orden = list(Severidad)
    maxima = max(severidades, key=orden.index)
    return _NIVEL_ALERTA_POR_SEVERIDAD[maxima]
