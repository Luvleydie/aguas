"""Contratos Pydantic v2 entre los tres agentes de HidroAlerta."""

from __future__ import annotations

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
        secciones = (
            "## Estado de presas",
            "## Precipitación",
            "## Alerta",
            "## Recomendación",
        )
        contenido = value.casefold()
        faltantes = [seccion for seccion in secciones if seccion.casefold() not in contenido]
        if faltantes:
            raise ValueError(f"faltan secciones fijas: {', '.join(faltantes)}")
        return value


AGENT_SCHEMAS: dict[str, dict[str, JsonValue]] = {
    "explorador": PlanAnalisis.model_json_schema(),
    "estadista": ResultadoEstadista.model_json_schema(),
    "narrador": Boletin.model_json_schema(),
}

