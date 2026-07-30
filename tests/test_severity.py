from __future__ import annotations

import pytest

from backend.contracts import Metrica, Severidad
from backend.severity import clasificar_severidad


@pytest.mark.red
def test_clasifica_casos_interiores_de_los_cuatro_umbrales():
    casos = [
        (Metrica.NIVEL_PRESA, 65, Severidad.INFO),
        (Metrica.NIVEL_PRESA, 50, Severidad.WARN),
        (Metrica.NIVEL_PRESA, 30, Severidad.ALERTA),
        (Metrica.NIVEL_PRESA, 20, Severidad.CRITICO),
        (Metrica.PRECIPITACION_MENSUAL, 90, Severidad.INFO),
        (Metrica.PRECIPITACION_MENSUAL, 60, Severidad.WARN),
        (Metrica.PRECIPITACION_MENSUAL, 30, Severidad.ALERTA),
        (Metrica.PRECIPITACION_MENSUAL, 10, Severidad.CRITICO),
        (Metrica.DELTA_NIVEL_MENSUAL, 1, Severidad.INFO),
        (Metrica.DELTA_NIVEL_MENSUAL, -1, Severidad.WARN),
        (Metrica.DELTA_NIVEL_MENSUAL, -5, Severidad.ALERTA),
        (Metrica.DELTA_NIVEL_MENSUAL, -10, Severidad.CRITICO),
        (Metrica.TEMPERATURA_MAXIMA, 25, Severidad.INFO),
        (Metrica.TEMPERATURA_MAXIMA, 32, Severidad.WARN),
        (Metrica.TEMPERATURA_MAXIMA, 36, Severidad.ALERTA),
        (Metrica.TEMPERATURA_MAXIMA, 40, Severidad.CRITICO),
    ]

    for metrica, valor, esperado in casos:
        assert clasificar_severidad(metrica, valor) is esperado

