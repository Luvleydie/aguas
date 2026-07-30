from __future__ import annotations

import math

import pytest

from backend.contracts import Metrica, NivelAlerta, Severidad
from backend.severity import clasificar_severidad, nivel_alerta_global


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


def test_empate_en_extremo_compartido_gana_el_primer_color_del_orden():
    # delta_nivel_mensual_pp se solapa a propósito en los extremos:
    # verde [0, 100], amarillo [-3, 0], naranja [-8, -3], rojo [-100, -8].
    assert clasificar_severidad(Metrica.DELTA_NIVEL_MENSUAL, 0.0) is Severidad.INFO
    assert clasificar_severidad(Metrica.DELTA_NIVEL_MENSUAL, -3.0) is Severidad.WARN
    assert clasificar_severidad(Metrica.DELTA_NIVEL_MENSUAL, -8.0) is Severidad.ALERTA


def test_hueco_entre_rangos_lanza_error_explicito():
    # nivel_presa_pct: rojo termina en 25.0, naranja empieza en 25.01.
    with pytest.raises(ValueError):
        clasificar_severidad(Metrica.NIVEL_PRESA, 25.005)


def test_valor_no_finito_lanza_error_explicito():
    with pytest.raises(ValueError):
        clasificar_severidad(Metrica.NIVEL_PRESA, math.nan)
    with pytest.raises(ValueError):
        clasificar_severidad(Metrica.NIVEL_PRESA, math.inf)


def test_valor_booleano_lanza_error_de_tipo():
    with pytest.raises(TypeError):
        clasificar_severidad(Metrica.NIVEL_PRESA, True)


def test_nivel_alerta_global_es_la_severidad_maxima():
    assert nivel_alerta_global([Severidad.INFO, Severidad.WARN]) is NivelAlerta.AMARILLO
    assert (
        nivel_alerta_global([Severidad.INFO, Severidad.WARN, Severidad.ALERTA, Severidad.CRITICO])
        is NivelAlerta.ROJO
    )
    assert nivel_alerta_global([Severidad.INFO]) is NivelAlerta.VERDE

