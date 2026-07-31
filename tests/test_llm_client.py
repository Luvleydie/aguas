"""Tests del router unificado de LLM (llm_client)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.llm_client import llm_p


class TestLlmP:
    @patch("backend.llm_client.claude_p")
    def test_auto_usa_claude_cuando_disponible(self, mock_claude: MagicMock):
        mock_claude.return_value = {"ok": True}
        result = llm_p("hola")
        assert result == {"ok": True}
        mock_claude.assert_called_once()

    @patch("backend.llm_client.claude_p")
    def test_fallback_a_ollama_cuando_claude_falla(self, mock_claude: MagicMock):
        mock_claude.side_effect = RuntimeError("No se encontró Claude CLI")
        with patch("backend.llm_client._resolve_backend", return_value="auto"):
            with patch("backend.llm_client._get_ollama_p") as mock_get_ollama:
                mock_ollama = MagicMock(return_value={"fuente": "ollama"})
                mock_get_ollama.return_value = mock_ollama
                result = llm_p("hola")
                assert result == {"fuente": "ollama"}
                mock_ollama.assert_called_once()

    @patch("backend.llm_client._resolve_backend", return_value="ollama")
    def test_backend_ollama_fuerza_ollama(self, _mock_backend: MagicMock):
        with patch("backend.llm_client._get_ollama_p") as mock_get_ollama:
            mock_ollama = MagicMock(return_value={"fuente": "ollama"})
            mock_get_ollama.return_value = mock_ollama
            result = llm_p("hola", system="sys", schema={"type": "object"})
            assert result == {"fuente": "ollama"}

    @patch("backend.llm_client._resolve_backend", return_value="claude")
    def test_backend_claude_fuerza_claude(self, _mock_backend: MagicMock):
        with patch("backend.llm_client.claude_p") as mock_claude:
            mock_claude.return_value = {"fuente": "claude"}
            result = llm_p("hola")
            assert result == {"fuente": "claude"}

    @patch("backend.llm_client._resolve_backend", return_value="claude")
    def test_backend_claude_falla_si_no_disponible(self, _mock_backend: MagicMock):
        with patch("backend.llm_client.claude_p") as mock_claude:
            mock_claude.side_effect = RuntimeError("claude not found")
            with pytest.raises(RuntimeError, match="claude not found"):
                llm_p("hola")
