"""Tests del adaptador de Ollama."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from backend.ollama_client import _extraer_json, ollama_p


class TestExtraerJson:
    def test_json_puro(self):
        assert _extraer_json('{"a": 1}') == {"a": 1}

    def test_json_envuelto_en_codigo(self):
        texto = '```json\n{"a": 1}\n```'
        assert _extraer_json(texto) == {"a": 1}

    def test_json_con_texto_alrededor(self):
        texto = 'Aquí está el resultado:\n{"a": 1}\nFin.'
        assert _extraer_json(texto) == {"a": 1}

    def test_json_invalido_lanza_error(self):
        with pytest.raises(RuntimeError, match="No se pudo extraer JSON"):
            _extraer_json("esto no es json")

    def test_lista_json(self):
        assert _extraer_json('[{"x": 2}]') == [{"x": 2}]


class TestOllamaP:
    @patch("backend.ollama_client.subprocess.run")
    @patch("backend.ollama_client.shutil.which")
    def test_llama_a_ollama_con_modelo(self, mock_which: MagicMock, mock_run: MagicMock):
        mock_which.return_value = "/usr/bin/ollama"
        mock_run.return_value = MagicMock(
            returncode=0, stdout='respuesta de mistral', stderr=""
        )
        result = ollama_p("hola", model="mistral")
        assert result == "respuesta de mistral"
        call_args = mock_run.call_args[0][0]
        assert "ollama" in call_args[0]
        assert "mistral" in call_args

    @patch("backend.ollama_client.subprocess.run")
    @patch("backend.ollama_client.shutil.which")
    def test_con_schema_devuelve_json(self, mock_which: MagicMock, mock_run: MagicMock):
        mock_which.return_value = "/usr/bin/ollama"
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"tipo": "plan_analisis"}', stderr=""
        )
        result = ollama_p("hola", schema={"type": "object"})
        assert result == {"tipo": "plan_analisis"}

    @patch("backend.ollama_client.shutil.which")
    def test_falla_si_ollama_no_instalado(self, mock_which: MagicMock):
        mock_which.return_value = None
        with pytest.raises(RuntimeError, match="No se encontr"):
            ollama_p("hola")

    @patch("backend.ollama_client.subprocess.run")
    @patch("backend.ollama_client.shutil.which")
    def test_incluye_system_prompt(self, mock_which: MagicMock, mock_run: MagicMock):
        mock_which.return_value = "/usr/bin/ollama"
        mock_run.return_value = MagicMock(returncode=0, stdout="respuesta", stderr="")
        ollama_p("prompt", system="Soy el sistema")
        call_args = mock_run.call_args[0][0]
        assert "--system" in call_args

    @patch("backend.ollama_client.subprocess.run")
    @patch("backend.ollama_client.shutil.which")
    def test_agrega_schema_hint(self, mock_which: MagicMock, mock_run: MagicMock):
        mock_which.return_value = "/usr/bin/ollama"
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"key": "val"}', stderr=""
        )
        schema = {"type": "object", "properties": {"key": {"type": "string"}}}
        result = ollama_p("datos", schema=schema)
        assert result == {"key": "val"}
        call_args = mock_run.call_args[0][0]
        prompt_completo = call_args[-1]
        assert "esquema" in prompt_completo.lower() or "json" in prompt_completo.lower()
