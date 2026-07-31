from __future__ import annotations

import re

from backend.rag import BoletinHistorico, cargar_boletines_historicos, contexto_historico

_SECCIONES = ("Estado de presas", "Precipitación", "Temperatura", "Alerta y recomendación")


class EmbedderDeJuguete:
    """Bag-of-words determinista sobre un vocabulario fijo — sin descargar
    ningún modelo real, para que estos tests corran rápido y sin red."""

    def __init__(self, vocabulario: list[str]) -> None:
        self.vocabulario = vocabulario

    def encode(self, textos: list[str]) -> list[list[float]]:
        return [[float(texto.count(palabra)) for palabra in self.vocabulario] for texto in textos]


def test_cargar_boletines_historicos_extrae_texto_narrativo_no_vacio():
    """El texto embeddable debe quedarse con las oraciones (interpretación,
    alerta, recomendación), no con las tablas/encabezados markdown — esos son
    casi idénticos entre boletines y diluyen la similitud coseno."""
    for boletin in cargar_boletines_historicos():
        assert boletin.texto_embedding
        assert "|---" not in boletin.texto_embedding
        assert len(boletin.texto_embedding) < len(boletin.texto)


def test_cargar_boletines_historicos_devuelve_los_12_con_las_4_secciones():
    boletines = cargar_boletines_historicos()

    assert len(boletines) == 12
    for boletin in boletines:
        for seccion in _SECCIONES:
            assert re.search(rf"^##.*{re.escape(seccion)}", boletin.texto, re.IGNORECASE | re.MULTILINE), (
                f"{boletin.id} no tiene la sección {seccion!r}"
            )


def test_contexto_historico_ordena_por_similitud_descendente():
    corpus = [
        BoletinHistorico(id="rojo-1", texto="sequia sequia sequia critico critico"),
        BoletinHistorico(id="verde-1", texto="lluvia lluvia normal normal"),
        BoletinHistorico(id="amarillo-1", texto="sequia lluvia moderado"),
    ]
    embedder = EmbedderDeJuguete(["sequia", "lluvia", "critico", "normal", "moderado"])

    resultado = contexto_historico(
        "sequia sequia critico",
        top_k=3,
        boletines=corpus,
        embedder=embedder,
    )

    assert [r["id"] for r in resultado] == ["rojo-1", "amarillo-1", "verde-1"]
    assert resultado[0]["similitud"] > resultado[1]["similitud"] > resultado[2]["similitud"]


def test_contexto_historico_respeta_top_k():
    corpus = [BoletinHistorico(id=f"b{i}", texto="sequia " * i) for i in range(1, 6)]
    embedder = EmbedderDeJuguete(["sequia"])

    resultado = contexto_historico("sequia", top_k=2, boletines=corpus, embedder=embedder)

    assert len(resultado) == 2


def test_contexto_historico_sin_corpus_devuelve_vacio():
    resultado = contexto_historico("sequia", boletines=[], embedder=EmbedderDeJuguete(["sequia"]))

    assert resultado == []


def test_contexto_historico_extracto_no_supera_400_caracteres():
    corpus = [BoletinHistorico(id="largo", texto="x" * 1000)]
    embedder = EmbedderDeJuguete(["x"])

    resultado = contexto_historico("x", boletines=corpus, embedder=embedder)

    assert len(resultado[0]["extracto"]) == 400
