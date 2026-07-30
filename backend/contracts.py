"""Contratos Pydantic v2 entre los cuatro agentes de HidroAlerta."""

from __future__ import annotations

import re
from datetime import date
from enum import Enum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator


class ContractModel(BaseModel):
    """Base estricta respecto a campos desconocidos."""

    model_config = ConfigDict(extra="forbid")


class ToolName(str, Enum):
    DESCRIBE = "describe"
    FILTER_BY_DATE = "filter_by_date"
    CALC_STATS = "calc_stats"
    COMPARE_PERIODS = "compare_periods"
    PLOT_ASCII = "plot_ascii"


class Severidad(str, Enum):
    INFO = "info"
    WARN = "warn"
    ALERTA = "alerta"
    CRITICO = "critico"


class NivelAlerta(str, Enum):
    VERDE = "verde"
    AMARILLO = "amarillo"
    NARANJA = "naranja"
    ROJO = "rojo"


class Metrica(str, Enum):
    NIVEL_PRESA = "nivel_presa_pct"
    PRECIPITACION_MENSUAL = "precipitacion_mensual_mm"
    DELTA_NIVEL_MENSUAL = "delta_nivel_mensual_pp"
    TEMPERATURA_MAXIMA = "temp_max_promedio_c"


class Cultivo(str, Enum):
    MAIZ = "maiz"
    FRIJOL = "frijol"
    ALFALFA = "alfalfa"


class AccionAgricola(str, Enum):
    SEMBRAR_NORMAL = "sembrar_normal"
    RETRASAR_SIEMBRA = "retrasar_siembra"
    REDUCIR_RIEGO = "reducir_riego"
    CULTIVO_ALTERNATIVO = "cultivo_alternativo"
    SIN_ACCION_URGENTE = "sin_accion_urgente"


class Ventana(ContractModel):
    desde: date
    hasta: date

    @model_validator(mode="after")
    def validar_orden(self) -> Self:
        if self.desde > self.hasta:
            raise ValueError("ventana.desde debe ser anterior o igual a ventana.hasta")
        return self


class PreguntaAnalisis(ContractModel):
    id: str = Field(min_length=1)
    objetivo: str = Field(min_length=1)
    tool: ToolName
    args: dict[str, JsonValue]


class PlanAnalisis(ContractModel):
    """Salida JSON propia del agente Explorador."""

    agente: Literal["explorador"] = "explorador"
    semana: int = Field(ge=1, le=53)
    ventana: Ventana
    preguntas: list[PreguntaAnalisis] = Field(min_length=1)

    @model_validator(mode="after")
    def validar_ids_unicos(self) -> Self:
        ids = [pregunta.id for pregunta in self.preguntas]
        if len(ids) != len(set(ids)):
            raise ValueError("los ids de preguntas deben ser únicos")
        return self


class EvidenciaTool(ContractModel):
    tool: ToolName
    args: dict[str, JsonValue]
    resultado: JsonValue


class Hallazgo(ContractModel):
    id: str = Field(min_length=1)
    pregunta_id: str = Field(min_length=1)
    metrica: Metrica
    valor: float
    unidad: str = Field(min_length=1)
    severidad: Severidad
    contexto: str = Field(min_length=1)
    sparkline: str = Field(min_length=1)
    evidencia: EvidenciaTool


class ResultadoEstadista(ContractModel):
    """Salida JSON propia del agente Estadista."""

    agente: Literal["estadista"] = "estadista"
    semana: int = Field(ge=1, le=53)
    ventana: Ventana
    hallazgos: list[Hallazgo] = Field(min_length=4)
    nivel_alerta_global: NivelAlerta


class Boletin(ContractModel):
    """Salida JSON propia del agente Narrador."""

    agente: Literal["narrador"] = "narrador"
    semana: int = Field(ge=1, le=53)
    nivel_alerta_global: NivelAlerta
    markdown: str = Field(min_length=1)
    recomendacion: str = Field(min_length=1)

    @field_validator("markdown")
    @classmethod
    def exigir_secciones_fijas(cls, value: str) -> str:
        # Oráculo real: assets/boletin_referencia.md. NO existe una sección
        # "Recomendación" separada — va combinada dentro de "Alerta y
        # recomendación". Se permite un prefijo de numeración opcional
        # ("## 1 · Estado de presas") entre "##" y el título.
        secciones = (
            "Estado de presas",
            "Precipitación",
            "Temperatura",
            "Alerta y recomendación",
        )
        faltantes = [
            seccion
            for seccion in secciones
            if not re.search(rf"^##.*{re.escape(seccion)}", value, re.IGNORECASE | re.MULTILINE)
        ]
        if faltantes:
            raise ValueError(f"faltan secciones fijas: {', '.join(faltantes)}")
        return value


class RecomendacionAgricola(ContractModel):
    """Salida JSON propia del agente Agrónomo."""

    agente: Literal["agronomo"] = "agronomo"
    semana: int = Field(ge=1, le=53)
    cultivo_prioritario: Cultivo
    accion: AccionAgricola
    razon: str = Field(min_length=1)
    mensaje_whatsapp: str = Field(min_length=1, max_length=280)
    severidad: Severidad

    @field_validator("mensaje_whatsapp")
    @classmethod
    def sin_tecnicismos(cls, value: str) -> str:
        prohibidos = ("%", " mm", "regresión", "regresion")
        encontrados = [token for token in prohibidos if token.casefold() in value.casefold()]
        if encontrados:
            raise ValueError(
                f"mensaje_whatsapp no debe contener tecnicismos: {', '.join(encontrados)}"
            )
        if value.count("\n") > 1:
            raise ValueError("mensaje_whatsapp debe tener máximo 2 líneas")
        return value


AGENT_SCHEMAS: dict[str, dict[str, JsonValue]] = {
    "explorador": PlanAnalisis.model_json_schema(),
    "estadista": ResultadoEstadista.model_json_schema(),
    "narrador": Boletin.model_json_schema(),
    "agronomo": RecomendacionAgricola.model_json_schema(),
}

