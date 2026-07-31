from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import main
from backend.contracts import Boletin, RecomendacionAgricola
from tests.fakes import FakeSupabase


@pytest.fixture
def api(monkeypatch):
    fake_db = FakeSupabase()
    estado = {"usuario": None}

    def _current_user():
        if estado["usuario"] is None:
            from fastapi import HTTPException, status

            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "no autenticado")
        return estado["usuario"]

    def _current_user_optional():
        return estado["usuario"]

    main.app.dependency_overrides[main.get_current_user] = _current_user
    main.app.dependency_overrides[main.get_current_user_optional] = _current_user_optional
    main.app.dependency_overrides[main.get_db_public] = lambda: fake_db
    main.app.dependency_overrides[main.get_db_gobierno] = lambda: fake_db
    main.app.dependency_overrides[main.get_db_ayuntamiento] = lambda: fake_db
    main.app.dependency_overrides[main.get_db_agricultor] = lambda: fake_db
    monkeypatch.setattr(main, "_service_client", lambda: fake_db)

    def _set_usuario(usuario):
        estado["usuario"] = usuario

    yield TestClient(main.app), fake_db, _set_usuario

    main.app.dependency_overrides.clear()


def _usuario(rol: str, id_: str = "u1") -> main.UsuarioActual:
    return main.UsuarioActual(id=id_, auth_user_id=f"auth-{id_}", email="x@example.com", rol=rol, access_token="tok")


# ── POST /api/auth/login ─────────────────────────────────────────────────


def test_login_exitoso_devuelve_tokens(monkeypatch):
    class SesionFalsa:
        access_token = "acc"
        refresh_token = "ref"

    class ResultadoFalso:
        session = SesionFalsa()

        class user:
            id = "auth-1"
            email = "a@b.com"

    class ClienteFalso:
        class auth:
            @staticmethod
            def sign_in_with_password(_credenciales):
                return ResultadoFalso()

    monkeypatch.setattr(main, "_anon_client", lambda: ClienteFalso())
    cliente = TestClient(main.app)

    respuesta = cliente.post("/api/auth/login", json={"email": "a@b.com", "password": "secreta"})

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "access_token": "acc",
        "refresh_token": "ref",
        "user": {"id": "auth-1", "email": "a@b.com"},
    }


def test_login_credenciales_invalidas_da_401(monkeypatch):
    class ClienteFalso:
        class auth:
            @staticmethod
            def sign_in_with_password(_credenciales):
                raise RuntimeError("invalid_grant")

    monkeypatch.setattr(main, "_anon_client", lambda: ClienteFalso())
    cliente = TestClient(main.app)

    respuesta = cliente.post("/api/auth/login", json={"email": "a@b.com", "password": "mala"})

    assert respuesta.status_code == 401


# ── POST /api/boletin/generar ────────────────────────────────────────────


def test_generar_boletin_requiere_rol_gobierno(api):
    cliente, _fake_db, set_usuario = api
    set_usuario(_usuario("agricultor"))

    respuesta = cliente.post("/api/boletin/generar", json={"semana": 42})

    assert respuesta.status_code == 403


def test_generar_boletin_persiste_boletin_recomendacion_y_logs(api, load_fixture, tmp_path, monkeypatch):
    cliente, fake_db, set_usuario = api
    set_usuario(_usuario("gobierno", id_="admin"))

    boletin = Boletin.model_validate(load_fixture("boletin.json"))
    recomendacion = RecomendacionAgricola.model_validate(load_fixture("recomendacion_agricola.json"))
    log_path = tmp_path / "log_agentes.jsonl"
    eventos = [
        {"agente": "explorador", "semana": 42, "timestamp": "t1", "mensaje": {}},
        {"agente": "estadista", "semana": 42, "timestamp": "t2", "mensaje": {"hallazgos": []}},
        {"agente": "narrador", "semana": 42, "timestamp": "t3", "mensaje": boletin.model_dump(mode="json")},
        {
            "agente": "agronomo",
            "semana": 42,
            "timestamp": "t4",
            "mensaje": recomendacion.model_dump(mode="json"),
        },
    ]
    log_path.write_text("\n".join(json.dumps(e) for e in eventos) + "\n", encoding="utf-8")
    monkeypatch.setattr(main, "LOG_PATH", log_path)
    monkeypatch.setattr(main, "orquestar", lambda **_: (boletin, recomendacion))

    respuesta = cliente.post("/api/boletin/generar", json={"semana": 42, "anio": 2024})

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["semana"] == 42
    assert cuerpo["markdown"] == boletin.markdown
    assert cuerpo["hallazgos_json"] == {"hallazgos": []}
    assert cuerpo["generado_por"] == "admin"
    assert cuerpo["publicado"] is False

    logs = fake_db.store["agent_logs"]
    assert [evento["agente"] for evento in logs] == ["explorador", "estadista", "narrador", "agronomo"]
    assert all(evento["boletin_id"] == cuerpo["id"] for evento in logs)


def test_generar_boletin_duplicado_da_409(api, load_fixture, tmp_path, monkeypatch):
    """POST dos veces la misma semana/año sin forzar debe devolver 409."""
    cliente, fake_db, set_usuario = api
    set_usuario(_usuario("gobierno"))

    boletin = Boletin.model_validate(load_fixture("boletin.json"))
    recomendacion = RecomendacionAgricola.model_validate(load_fixture("recomendacion_agricola.json"))
    log_path = tmp_path / "log_agentes.jsonl"
    eventos = [
        {"agente": "explorador", "semana": 10, "timestamp": "t1", "mensaje": {}},
        {"agente": "estadista", "semana": 10, "timestamp": "t2", "mensaje": {"hallazgos": []}},
        {"agente": "narrador", "semana": 10, "timestamp": "t3", "mensaje": boletin.model_dump(mode="json")},
        {"agente": "agronomo", "semana": 10, "timestamp": "t4", "mensaje": recomendacion.model_dump(mode="json")},
    ]
    log_path.write_text("\n".join(json.dumps(e) for e in eventos) + "\n", encoding="utf-8")
    monkeypatch.setattr(main, "LOG_PATH", log_path)
    monkeypatch.setattr(main, "orquestar", lambda **_: (boletin, recomendacion))

    r1 = cliente.post("/api/boletin/generar", json={"semana": 10, "anio": 2024})
    assert r1.status_code == 201

    r2 = cliente.post("/api/boletin/generar", json={"semana": 10, "anio": 2024})
    assert r2.status_code == 409
    assert "regenerar" in r2.json()["detail"].lower() or "sobrescribir" in r2.json()["detail"].lower()


def test_generar_boletin_duplicado_con_forzar_sobrescribe(api, load_fixture, tmp_path, monkeypatch):
    """POST con forzar=true debe sobrescribir el boletín existente."""
    cliente, fake_db, set_usuario = api
    set_usuario(_usuario("gobierno"))

    boletin = Boletin.model_validate(load_fixture("boletin.json"))
    recomendacion = RecomendacionAgricola.model_validate(load_fixture("recomendacion_agricola.json"))
    log_path = tmp_path / "log_agentes.jsonl"
    eventos = [
        {"agente": "explorador", "semana": 15, "timestamp": "t1", "mensaje": {}},
        {"agente": "estadista", "semana": 15, "timestamp": "t2", "mensaje": {"hallazgos": []}},
        {"agente": "narrador", "semana": 15, "timestamp": "t3", "mensaje": boletin.model_dump(mode="json")},
        {"agente": "agronomo", "semana": 15, "timestamp": "t4", "mensaje": recomendacion.model_dump(mode="json")},
    ]
    log_path.write_text("\n".join(json.dumps(e) for e in eventos) + "\n", encoding="utf-8")
    monkeypatch.setattr(main, "LOG_PATH", log_path)
    monkeypatch.setattr(main, "orquestar", lambda **_: (boletin, recomendacion))

    r1 = cliente.post("/api/boletin/generar", json={"semana": 15, "anio": 2024})
    assert r1.status_code == 201
    id1 = r1.json()["id"]

    r2 = cliente.post("/api/boletin/generar", json={"semana": 15, "anio": 2024, "forzar": True})
    assert r2.status_code == 201
    assert r2.json()["id"] == id1


def test_generar_boletin_duplicado_requiere_gobierno(api, load_fixture, tmp_path, monkeypatch):
    """El endpoint de generar con forzar también requiere rol gobierno."""
    cliente, _fake_db, set_usuario = api
    set_usuario(_usuario("ayuntamiento"))

    respuesta = cliente.post("/api/boletin/generar", json={"semana": 1, "anio": 2024, "forzar": True})
    assert respuesta.status_code == 403


# ── GET /api/boletin/{semana} ────────────────────────────────────────────


def test_obtener_boletin_publicado_visible_sin_autenticacion(api):
    cliente, fake_db, _set_usuario = api
    fake_db.store["boletines"] = [
        {"id": "b1", "semana": 10, "anio": 2024, "publicado": True, "hallazgos_json": {"secreto": True}},
    ]

    respuesta = cliente.get("/api/boletin/10")

    assert respuesta.status_code == 200
    assert "hallazgos_json" not in respuesta.json()


def test_obtener_boletin_no_publicado_da_404_para_anonimo(api):
    cliente, fake_db, _set_usuario = api
    fake_db.store["boletines"] = [{"id": "b1", "semana": 11, "anio": 2024, "publicado": False}]

    respuesta = cliente.get("/api/boletin/11")

    assert respuesta.status_code == 404


def test_obtener_boletin_no_publicado_visible_para_gobierno(api):
    cliente, fake_db, set_usuario = api
    set_usuario(_usuario("gobierno"))
    fake_db.store["boletines"] = [
        {"id": "b1", "semana": 12, "anio": 2024, "publicado": False, "hallazgos_json": {"x": 1}}
    ]

    respuesta = cliente.get("/api/boletin/12")

    assert respuesta.status_code == 200
    assert respuesta.json()["hallazgos_json"] == {"x": 1}


# ── GET /api/boletin/historico ───────────────────────────────────────────


def test_historico_ordena_por_anio_y_semana_descendente(api):
    cliente, fake_db, _set_usuario = api
    fake_db.store["boletines"] = [
        {"id": "b1", "semana": 1, "anio": 2023, "publicado": True},
        {"id": "b2", "semana": 5, "anio": 2024, "publicado": True},
        {"id": "b3", "semana": 3, "anio": 2024, "publicado": True},
    ]

    respuesta = cliente.get("/api/boletin/historico")

    assert [f["id"] for f in respuesta.json()] == ["b2", "b3", "b1"]


# ── POST /api/boletin/{id}/publicar ──────────────────────────────────────


def test_publicar_boletin_marca_publicado_true(api):
    cliente, fake_db, set_usuario = api
    set_usuario(_usuario("gobierno"))
    fake_db.store["boletines"] = [{"id": "b1", "semana": 1, "anio": 2024, "publicado": False}]

    respuesta = cliente.post("/api/boletin/b1/publicar")

    assert respuesta.status_code == 200
    assert respuesta.json()["publicado"] is True
    assert respuesta.json()["published_at"]


def test_publicar_boletin_inexistente_da_404(api):
    cliente, _fake_db, set_usuario = api
    set_usuario(_usuario("gobierno"))

    respuesta = cliente.post("/api/boletin/no-existe/publicar")

    assert respuesta.status_code == 404


def test_publicar_boletin_requiere_gobierno(api):
    cliente, _fake_db, set_usuario = api
    set_usuario(_usuario("ayuntamiento"))

    respuesta = cliente.post("/api/boletin/b1/publicar")

    assert respuesta.status_code == 403


# ── GET /api/logs/{semana} ───────────────────────────────────────────────


def test_logs_de_semana_requiere_gobierno(api):
    cliente, _fake_db, set_usuario = api
    set_usuario(_usuario("medios"))

    respuesta = cliente.get("/api/logs/42")

    assert respuesta.status_code == 403


def test_logs_de_semana_devuelve_eventos_del_boletin(api):
    cliente, fake_db, set_usuario = api
    set_usuario(_usuario("gobierno"))
    fake_db.store["boletines"] = [{"id": "b1", "semana": 42, "anio": 2024}]
    fake_db.store["agent_logs"] = [
        {"id": "l1", "boletin_id": "b1", "agente": "explorador"},
        {"id": "l2", "boletin_id": "otro", "agente": "estadista"},
    ]

    respuesta = cliente.get("/api/logs/42")

    assert [f["id"] for f in respuesta.json()] == ["l1"]


# ── POST /api/acciones/ayuntamiento ──────────────────────────────────────


def test_registrar_accion_requiere_rol_ayuntamiento(api):
    cliente, _fake_db, set_usuario = api
    set_usuario(_usuario("agricultor"))

    respuesta = cliente.post(
        "/api/acciones/ayuntamiento", json={"boletin_id": "b1", "accion": "racionamiento"}
    )

    assert respuesta.status_code == 403


def test_registrar_accion_usa_el_usuario_autenticado_no_uno_del_body(api):
    cliente, fake_db, set_usuario = api
    set_usuario(_usuario("ayuntamiento", id_="u-ayto"))

    respuesta = cliente.post(
        "/api/acciones/ayuntamiento", json={"boletin_id": "b1", "accion": "campaña de ahorro"}
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["usuario_id"] == "u-ayto"
    assert fake_db.store["acciones_ayuntamiento"][0]["accion"] == "campaña de ahorro"


# ── GET /api/siembra/{semana} ────────────────────────────────────────────


def test_siembra_requiere_rol_agricultor(api):
    cliente, _fake_db, set_usuario = api
    set_usuario(_usuario("medios"))

    respuesta = cliente.get("/api/siembra/42")

    assert respuesta.status_code == 403


def test_siembra_devuelve_solo_campos_de_recomendacion_sin_hallazgos(api, load_fixture):
    cliente, fake_db, set_usuario = api
    set_usuario(_usuario("agricultor"))
    recomendacion = load_fixture("recomendacion_agricola.json")
    fake_db.store["boletines"] = [
        {
            "id": "b1",
            "semana": 42,
            "anio": 2024,
            "hallazgos_json": {"secreto": True},
            "recomendacion_agricola_json": recomendacion,
        }
    ]

    respuesta = cliente.get("/api/siembra/42")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert "hallazgos_json" not in cuerpo
    assert cuerpo["cultivo_prioritario"] == recomendacion["cultivo_prioritario"]


# ── run.sh: frontend estático servido en el mismo puerto que la API ─────


def test_montar_frontend_estatico_sirve_index_html(tmp_path):
    (tmp_path / "index.html").write_text("<html>hola</html>", encoding="utf-8")
    app_prueba = FastAPI()

    main.montar_frontend_estatico(app_prueba, tmp_path)

    respuesta = TestClient(app_prueba).get("/")
    assert respuesta.status_code == 200
    assert "hola" in respuesta.text


def test_montar_frontend_estatico_no_monta_si_no_existe_el_directorio(tmp_path):
    app_prueba = FastAPI()

    main.montar_frontend_estatico(app_prueba, tmp_path / "no-existe-todavia")

    respuesta = TestClient(app_prueba).get("/")
    assert respuesta.status_code == 404


def test_siembra_sin_recomendacion_da_404(api):
    cliente, fake_db, set_usuario = api
    set_usuario(_usuario("agricultor"))
    fake_db.store["boletines"] = [{"id": "b1", "semana": 43, "anio": 2024}]

    respuesta = cliente.get("/api/siembra/43")

    assert respuesta.status_code == 404


def test_cors_permite_origen_de_desarrollo_localhost_3000(api):
    cliente, _, _ = api

    respuesta = cliente.get("/api/boletin/historico", headers={"Origin": "http://localhost:3000"})

    assert respuesta.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_responde_preflight_options(api):
    cliente, _, _ = api

    respuesta = cliente.options(
        "/api/boletin/historico",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert respuesta.status_code == 200
    assert respuesta.headers.get("access-control-allow-origin") == "http://localhost:3000"

# ── GET /api/plan-accion/{semana} ────────────────────────────────────────────

@pytest.mark.red
def test_plan_accion_requiere_gobierno_o_ayuntamiento(api):
    cliente, _fake_db, set_usuario = api
    set_usuario(_usuario("agricultor"))
    respuesta = cliente.get("/api/plan-accion/42")
    assert respuesta.status_code == 403

    set_usuario(_usuario("medios"))
    respuesta = cliente.get("/api/plan-accion/42")
    assert respuesta.status_code == 403

@pytest.mark.red
def test_plan_accion_404_si_no_hay_boletin(api):
    cliente, fake_db, set_usuario = api
    set_usuario(_usuario("ayuntamiento"))
    respuesta = cliente.get("/api/plan-accion/99")
    assert respuesta.status_code == 404

@pytest.mark.red
def test_plan_accion_genera_y_guarda(api, monkeypatch):
    cliente, fake_db, set_usuario = api
    set_usuario(_usuario("ayuntamiento"))
    fake_db.store["boletines"] = [{"id": "b1", "semana": 42, "nivel_alerta_global": "rojo"}]
    fake_db.store["planes_accion_generados"] = []

    def mock_generar_plan_accion(nivel):
        return [{"id": 1, "accion": "Test", "nivel_alerta": nivel, "prioridad": 1}]

    from backend.mcp_tools import plan_accion
    monkeypatch.setattr(plan_accion, "generar_plan_accion", mock_generar_plan_accion)

    respuesta = cliente.get("/api/plan-accion/42")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert len(datos) == 1
    assert datos[0]["accion"] == "Test"

    # Verificar auditoría
    assert len(fake_db.store["planes_accion_generados"]) == 1
    assert fake_db.store["planes_accion_generados"][0]["boletin_id"] == "b1"

@pytest.mark.red
def test_plan_accion_retorna_cache(api):
    cliente, fake_db, set_usuario = api
    set_usuario(_usuario("gobierno"))
    fake_db.store["boletines"] = [{"id": "b1", "semana": 42, "nivel_alerta_global": "rojo"}]
    fake_db.store["planes_accion_generados"] = [
        {"id": "p1", "boletin_id": "b1", "plan_json": [{"id": 2, "accion": "Cache", "prioridad": 1}]}
    ]

    respuesta = cliente.get("/api/plan-accion/42")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert len(datos) == 1
    assert datos[0]["accion"] == "Cache"
