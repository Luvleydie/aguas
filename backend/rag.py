"""RAG (arquitectura-hidroalerta.md §5): similitud coseno entre los hallazgos
de la semana y 12 boletines históricos sintéticos (``backend/scripts/
generar_boletines_historicos.py``). Local, en memoria, sin API key.

Es tier Pro y opcional a propósito: ``backend/pipeline.py`` solo la usa si el
llamador inyecta ``contexto_historico_fn`` explícitamente (ver
``backend/main.py``); si el modelo de embeddings no está disponible, el
Narrador simplemente no recibe contexto histórico — no rompe el resto del
pipeline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Protocol

HISTORICOS_DIR = Path(__file__).resolve().parent / "data" / "boletines_historicos"
MODELO_NOMBRE = "paraphrase-multilingual-MiniLM-L12-v2"

_PREFIJOS_NARRATIVOS = (
    "**Interpretación:**",
    "**Nivel global:",
    "**Recomendación operativa:**",
)


class Embedder(Protocol):
    def encode(self, textos: list[str]) -> list[list[float]]: ...


@dataclass(frozen=True)
class BoletinHistorico:
    id: str
    texto: str
    texto_embedding: str | None = None

    @property
    def texto_para_similitud(self) -> str:
        return self.texto_embedding or self.texto


def _texto_narrativo(texto_completo: str) -> str:
    """Solo las oraciones con contenido semántico (interpretaciones, alerta,
    recomendación, nota de contexto) — las tablas y encabezados markdown son
    casi idénticos entre boletines y diluyen la señal de similitud coseno."""

    lineas: list[str] = []
    for cruda in texto_completo.splitlines():
        linea = cruda.strip()
        for prefijo in _PREFIJOS_NARRATIVOS:
            if linea.startswith(prefijo):
                lineas.append(linea.removeprefix(prefijo).strip())
                break
        else:
            if linea.startswith("*Nota de contexto histórico:"):
                lineas.append(re.sub(r"^\*|\*$", "", linea).removeprefix("Nota de contexto histórico:").strip())
    return " ".join(lineas)


def cargar_boletines_historicos(directorio: Path = HISTORICOS_DIR) -> list[BoletinHistorico]:
    boletines = []
    for ruta in sorted(directorio.glob("*.md")):
        texto = ruta.read_text(encoding="utf-8")
        boletines.append(
            BoletinHistorico(id=ruta.stem, texto=texto, texto_embedding=_texto_narrativo(texto))
        )
    return boletines


@lru_cache(maxsize=1)
def _modelo_por_defecto() -> Embedder:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODELO_NOMBRE)


def _coseno(a: list[float], b: list[float]) -> float:
    producto = sum(x * y for x, y in zip(a, b, strict=True))
    norma_a = sum(x * x for x in a) ** 0.5
    norma_b = sum(y * y for y in b) ** 0.5
    if norma_a == 0 or norma_b == 0:
        return 0.0
    return producto / (norma_a * norma_b)


def contexto_historico(
    texto_consulta: str,
    *,
    top_k: int = 3,
    boletines: list[BoletinHistorico] | None = None,
    embedder: Embedder | None = None,
) -> list[dict[str, object]]:
    """``top_k`` boletines históricos más parecidos a ``texto_consulta``."""

    corpus = boletines if boletines is not None else cargar_boletines_historicos()
    if not corpus:
        return []

    modelo = embedder if embedder is not None else _modelo_por_defecto()
    vectores = modelo.encode([texto_consulta, *[b.texto_para_similitud for b in corpus]])
    vector_consulta, *vectores_corpus = (list(v) for v in vectores)

    similitudes = sorted(
        (
            (boletin, _coseno(vector_consulta, vector))
            for boletin, vector in zip(corpus, vectores_corpus, strict=True)
        ),
        key=lambda par: par[1],
        reverse=True,
    )

    return [
        {"id": boletin.id, "similitud": round(similitud, 4), "extracto": boletin.texto[:400]}
        for boletin, similitud in similitudes[:top_k]
    ]
