"""API FastAPI de HidroAlerta — los 8 endpoints de arquitectura-hidroalerta.md §6.

Autenticación: cada request trae ``Authorization: Bearer <access_token>`` de
Supabase Auth. El token se valida contra Supabase (no se reimplementa
verificación de JWT) y el cliente de datos queda autenticado con ese mismo
token, para que Postgres aplique RLS como el usuario real — el backend nunca
usa la service key para leer/escribir datos de negocio, solo para resolver
qué fila de ``usuarios`` corresponde al token (una operación interna, no una
lectura de datos del dominio).
"""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from postgrest.exceptions import APIError
from pydantic import BaseModel, EmailStr, Field
from supabase import Client, create_client

from backend.pipeline import orquestar
from backend.rag import contexto_historico

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_PUBLISHABLE_KEY = os.environ["SUPABASE_PUBLISHABLE_KEY"]
SUPABASE_SECRET_KEY = os.environ["SUPABASE_SECRET_KEY"]

DATA_DIR = Path(os.environ.get("HIDROALERTA_DATA_DIR", "backend/data"))
OUTPUT_DIR = Path(os.environ.get("HIDROALERTA_OUTPUT_DIR", "boletines"))
LOG_PATH = Path(os.environ.get("HIDROALERTA_LOG_PATH", "log_agentes.jsonl"))

app = FastAPI(title="HidroAlerta API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Modelos de request ──────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


def _rol_desde_email(email: str) -> str:
    dominio = email.rsplit("@", 1)[-1].lower() if "@" in email else ""
    if dominio == "durango.gob.mx":
        return "gobierno"
    if dominio == "ayuntamiento.com":
        return "ayuntamiento"
    if dominio == "prensa.com":
        return "medios"
    return "agricultor"


class GenerarBoletinRequest(BaseModel):
    semana: int = Field(ge=1, le=52)
    anio: int = Field(default_factory=lambda: datetime.now(UTC).year, ge=2000, le=2100)
    forzar: bool = False


class AccionAyuntamientoRequest(BaseModel):
    boletin_id: str = Field(min_length=1)
    accion: str = Field(min_length=1, max_length=500)
    notas: str | None = Field(default=None, max_length=2000)


# ── Identidad y clientes Supabase ───────────────────────────────────────────


class UsuarioActual(BaseModel):
    id: str
    auth_user_id: str
    email: str
    rol: str
    access_token: str


def _anon_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)


def _service_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


def get_client_para(usuario: UsuarioActual | None) -> Client:
    if usuario is None:
        return _anon_client()
    cliente = create_client(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)
    cliente.postgrest.auth(usuario.access_token)
    return cliente


def _validar_token_y_cargar_usuario(access_token: str) -> UsuarioActual:
    try:
        respuesta = httpx.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={"Authorization": f"Bearer {access_token}", "apikey": SUPABASE_PUBLISHABLE_KEY},
            timeout=10,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "No se pudo validar el token") from exc
    if respuesta.status_code != 200:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o expirado")
    auth_user = respuesta.json()

    perfil = (
        _service_client()
        .table("usuarios")
        .select("id, rol")
        .eq("auth_user_id", auth_user["id"])
        .limit(1)
        .execute()
    )
    if not perfil.data:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "El usuario no tiene perfil en HidroAlerta")

    return UsuarioActual(
        id=perfil.data[0]["id"],
        auth_user_id=auth_user["id"],
        email=auth_user.get("email") or "",
        rol=perfil.data[0]["rol"],
        access_token=access_token,
    )


def _token_del_header(authorization: str | None) -> str | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return authorization.split(" ", 1)[1].strip()


def get_current_user(authorization: str | None = Header(default=None)) -> UsuarioActual:
    token = _token_del_header(authorization)
    if token is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Falta encabezado Authorization: Bearer <token>"
        )
    return _validar_token_y_cargar_usuario(token)


def get_current_user_optional(authorization: str | None = Header(default=None)) -> UsuarioActual | None:
    token = _token_del_header(authorization)
    if token is None:
        return None
    return _validar_token_y_cargar_usuario(token)


def require_role(rol_requerido: str):
    def _dependencia(usuario: UsuarioActual = Depends(get_current_user)) -> UsuarioActual:
        if usuario.rol != rol_requerido:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, f"Este endpoint requiere rol '{rol_requerido}'"
            )
        return usuario

    return _dependencia


require_gobierno = require_role("gobierno")
require_ayuntamiento = require_role("ayuntamiento")
require_agricultor = require_role("agricultor")


def get_db_public(usuario: UsuarioActual | None = Depends(get_current_user_optional)) -> Client:
    return get_client_para(usuario)


def get_db_gobierno(usuario: UsuarioActual = Depends(require_gobierno)) -> Client:
    return get_client_para(usuario)


def get_db_ayuntamiento(usuario: UsuarioActual = Depends(require_ayuntamiento)) -> Client:
    return get_client_para(usuario)


def get_db_agricultor(usuario: UsuarioActual = Depends(require_agricultor)) -> Client:
    return get_client_para(usuario)


# ── Helpers de dominio ──────────────────────────────────────────────────────


_CAMPOS_RECOMENDACION = {"cultivo_prioritario", "accion", "razon", "mensaje_whatsapp", "severidad"}


def _ultimo_boletin_de_semana(db: Client, tabla: str, semana: int) -> dict[str, Any] | None:
    respuesta = (
        db.table(tabla)
        .select("*")
        .eq("semana", semana)
        .order("anio", desc=True)
        .limit(1)
        .execute()
    )
    return respuesta.data[0] if respuesta.data else None


def _tabla_boletines_para(usuario: UsuarioActual | None) -> str:
    # RLS es por fila, no por columna (ver backend/db/migrations/0001_init_schema.sql):
    # cualquier rol autenticado que no sea gobierno debe leer la vista pública,
    # nunca la tabla completa, para no exponer hallazgos_json/recomendacion_agricola_json.
    return "boletines" if usuario is not None and usuario.rol == "gobierno" else "boletines_publico"


# ── Endpoints ────────────────────────────────────────────────────────────────


@app.get("/api/auth/seed")
def seed_users():
    users_to_create = [
        {"email": "gobierno@durango.gob.mx", "password": "Password123!", "role": "gobierno", "name": "Gobierno del Estado"},
        {"email": "centro@ayuntamiento.com", "password": "Password123!", "role": "ayuntamiento", "name": "Ayuntamiento Centro"},
        {"email": "noticias@prensa.com", "password": "Password123!", "role": "medios", "name": "Medios de Prensa"},
        {"email": "juan@agricultor.com", "password": "Password123!", "role": "agricultor", "name": "Agricultor Juan"}
    ]
    resultados = []
    
    for u in users_to_create:
        try:
            # Crear clientes frescos para que no se contaminen entre iteraciones
            service = _service_client()
            anon = _anon_client()
            auth_id = None
            
            # 1. Intentar crear en auth.users
            try:
                res = service.auth.admin.create_user({
                    "email": u["email"],
                    "password": u["password"],
                    "email_confirm": True
                })
                auth_id = res.user.id
                resultados.append(f"Auth creado: {u['email']}")
            except Exception as e:
                # Si ya existe, iniciamos sesión para obtener su ID usando el cliente anónimo
                if "already" in str(e).lower() or "rate limit" in str(e).lower():
                    login_res = anon.auth.sign_in_with_password({"email": u["email"], "password": u["password"]})
                    auth_id = login_res.user.id
                    resultados.append(f"Auth recuperado: {u['email']}")
                else:
                    raise e
            
            # 2. Insertar en public.usuarios solo si no existe usando el service_role (brinca RLS)
            if auth_id:
                check = service.table("usuarios").select("id").eq("email", u["email"]).execute()
                if not check.data:
                    service.table("usuarios").insert({
                        "auth_user_id": auth_id,
                        "email": u["email"],
                        "rol": u["role"],
                        "nombre": u["name"]
                    }).execute()
                    resultados.append(f"Perfil público insertado: {u['email']}")
                else:
                    resultados.append(f"Perfil público ya existía: {u['email']}")
                    
        except Exception as e:
            resultados.append(f"Error en {u['email']}: {repr(e)}")
            
    return {"status": "ok", "detalles": resultados}

@app.post("/api/auth/login")
def login(body: LoginRequest) -> dict[str, Any]:
    cliente = _anon_client()
    try:
        sesion = cliente.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
    except Exception as exc:  # supabase-py lanza AuthApiError con credenciales inválidas
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales inválidas") from exc

    return {
        "access_token": sesion.session.access_token,
        "refresh_token": sesion.session.refresh_token,
        "user": {"id": sesion.user.id, "email": sesion.user.email},
    }


@app.get("/api/auth/me")
def auth_me(usuario: UsuarioActual = Depends(get_current_user)) -> dict[str, Any]:
    return {"id": usuario.id, "email": usuario.email, "rol": usuario.rol}


@app.post("/api/auth/register")
def register(body: RegisterRequest) -> dict[str, Any]:
    print(f">>> [REGISTRO] Intentando registrar: {body.email}")
    rol = _rol_desde_email(body.email)
    print(f">>> [REGISTRO] Rol asignado: {rol}")
    cliente = _anon_client()
    try:
        print(">>> [REGISTRO] Llamando a supabase.auth.sign_up...")
        resultado = cliente.auth.sign_up({
            "email": body.email,
            "password": body.password,
        })
        print(f">>> [REGISTRO] Resultado sign_up: {resultado}")
    except Exception as exc:
        print(">>> [REGISTRO ERROR] Excepción en sign_up:", repr(exc))
        if "rate limit" in str(exc).lower():
            print(">>> [REGISTRO] Rate limit detectado. Usando Admin API para crear usuario...")
            try:
                service = _service_client()
                service.auth.admin.create_user({
                    "email": body.email,
                    "password": body.password,
                    "email_confirm": True
                })
                print(">>> [REGISTRO] Usuario creado por Admin API. Iniciando sesión...")
                resultado = cliente.auth.sign_in_with_password({
                    "email": body.email,
                    "password": body.password,
                })
            except Exception as admin_exc:
                print(">>> [REGISTRO ERROR] Fallo en Admin API:", repr(admin_exc))
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se pudo registrar el usuario (Rate limit y Admin fallback fallaron)") from admin_exc
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se pudo registrar el usuario (error en Supabase)") from exc

    if not resultado or not resultado.user:
        print(">>> [REGISTRO ERROR] No devolvió usuario")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se pudo crear el usuario (resultado vacío)")

    service = _service_client()
    fila_usuario = {
        "auth_user_id": resultado.user.id,
        "email": body.email,
        "nombre": body.email.split("@", 1)[0],
        "rol": rol,
    }
    # sign_up confirma antes de que la fila de auth.users sea visible para el
    # chequeo de FK del insert siguiente (visto en producción: 23503
    # "usuarios_auth_user_id_fkey" que desaparece si se reintenta ms después).
    ultimo_error: Exception | None = None
    for intento, espera in enumerate((0, 0.3, 0.8)):
        if espera:
            time.sleep(espera)
        try:
            service.table("usuarios").insert(fila_usuario).execute()
            ultimo_error = None
            break
        except APIError as exc:
            ultimo_error = exc
            print(f">>> [REGISTRO] Insert usuarios intento {intento + 1} falló: {exc}")
            if exc.code != "23503":
                raise
    if ultimo_error is not None:
        raise ultimo_error

    return {
        "id": resultado.user.id,
        "email": resultado.user.email,
        "rol": rol,
    }


@app.post("/api/boletin/generar", status_code=status.HTTP_201_CREATED)
def generar_boletin(
    body: GenerarBoletinRequest,
    usuario: UsuarioActual = Depends(require_gobierno),
    db: Client = Depends(get_db_gobierno),
) -> dict[str, Any]:
    existente = _ultimo_boletin_de_semana(db, "boletines", body.semana)
    sobrescribir = False
    if existente is not None and existente.get("anio") == body.anio:
        if not body.forzar:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Ya existe un boletín para la semana {}/{}. "
                "¿Deseas regenerar y sobrescribir? Envía forzar=true.".format(body.semana, body.anio),
            )
        db.table("agent_logs").delete().eq("boletin_id", existente["id"]).execute()
        sobrescribir = True

    boletin, recomendacion, versiones, evaluacion = orquestar(
        semana=body.semana,
        data_dir=DATA_DIR,
        output_dir=OUTPUT_DIR,
        log_path=LOG_PATH,
        contexto_historico_fn=contexto_historico,
    )

    # orquestar() ya escribió los 5 eventos (uno por agente) al final de
    # LOG_PATH; se reutilizan aquí en vez de volver a serializar cada
    # resultado, y el mensaje del Estadista es la fuente de hallazgos_json.
    eventos = [json.loads(linea) for linea in LOG_PATH.read_text(encoding="utf-8").splitlines()][-5:]
    hallazgos_json = next(
        (evento["mensaje"] for evento in eventos if evento["agente"] == "estadista"), {}
    )

    datos_boletin = {
        "semana": body.semana,
        "anio": body.anio,
        "markdown": boletin.markdown,
        "hallazgos_json": hallazgos_json,
        "recomendacion_agricola_json": recomendacion.model_dump(mode="json"),
        "versiones_json": versiones.model_dump(mode="json") if hasattr(versiones, "model_dump") else versiones,
        "evaluacion_calidad_json": evaluacion,
        "nivel_alerta_global": boletin.nivel_alerta_global.value,
        "recomendacion": boletin.recomendacion,
        "publicado": False,
        "generado_por": usuario.id,
    }

    if sobrescribir:
        fila = (
            db.table("boletines")
            .update(datos_boletin)
            .eq("id", existente["id"])
            .execute()
        )
        boletin_id = existente["id"]
    else:
        fila = db.table("boletines").insert(datos_boletin).execute()
        boletin_id = fila.data[0]["id"]

    db.table("agent_logs").insert(
        [
            {
                "boletin_id": boletin_id,
                "agente": evento["agente"],
                "mensaje": evento["mensaje"],
            }
            for evento in eventos
        ]
    ).execute()

    return {"id": boletin_id, **datos_boletin}


@app.get("/api/boletin/historico")
def historico_boletines(
    usuario: UsuarioActual | None = Depends(get_current_user_optional),
    db: Client = Depends(get_db_public),
) -> list[dict[str, Any]]:
    tabla = _tabla_boletines_para(usuario)
    respuesta = db.table(tabla).select("*").order("anio", desc=True).order("semana", desc=True).execute()
    return respuesta.data


@app.get("/api/boletin/{semana}")
def obtener_boletin(
    semana: int,
    usuario: UsuarioActual | None = Depends(get_current_user_optional),
    db: Client = Depends(get_db_public),
) -> dict[str, Any]:
    tabla = _tabla_boletines_para(usuario)
    fila = _ultimo_boletin_de_semana(db, tabla, semana)
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No hay boletín para la semana {semana}")
    return fila


@app.post("/api/boletin/{boletin_id}/publicar")
def publicar_boletin(
    boletin_id: str,
    usuario: UsuarioActual = Depends(require_gobierno),
    db: Client = Depends(get_db_gobierno),
) -> dict[str, Any]:
    respuesta = (
        db.table("boletines")
        .update({"publicado": True, "published_at": datetime.now(UTC).isoformat()})
        .eq("id", boletin_id)
        .execute()
    )
    if not respuesta.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Boletín no encontrado")
    # Notificaciones (email/push) fuera del alcance del entregable local; el
    # canal whatsapp queda reservado para la fase extra (ver arquitectura §13).
    return respuesta.data[0]


@app.get("/api/logs/{semana}")
def logs_de_semana(
    semana: int,
    usuario: UsuarioActual = Depends(require_gobierno),
    db: Client = Depends(get_db_gobierno),
) -> list[dict[str, Any]]:
    boletin = _ultimo_boletin_de_semana(db, "boletines", semana)
    if boletin is None:
        return []
    respuesta = (
        db.table("agent_logs")
        .select("*")
        .eq("boletin_id", boletin["id"])
        .order("timestamp")
        .execute()
    )
    return respuesta.data


@app.post("/api/acciones/ayuntamiento", status_code=status.HTTP_201_CREATED)
def registrar_accion_ayuntamiento(
    body: AccionAyuntamientoRequest,
    usuario: UsuarioActual = Depends(require_ayuntamiento),
    db: Client = Depends(get_db_ayuntamiento),
) -> dict[str, Any]:
    respuesta = (
        db.table("acciones_ayuntamiento")
        .insert(
            {
                "boletin_id": body.boletin_id,
                "usuario_id": usuario.id,
                "accion": body.accion,
                "notas": body.notas,
            }
        )
        .execute()
    )
    return respuesta.data[0]


@app.get("/api/siembra/{semana}")
def siembra_recomendada(
    semana: int,
    usuario: UsuarioActual = Depends(require_agricultor),
    db: Client = Depends(get_db_agricultor),
) -> dict[str, Any]:
    boletin = _ultimo_boletin_de_semana(db, "boletines", semana)
    if boletin is None or not boletin.get("recomendacion_agricola_json"):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"No hay recomendación de siembra para la semana {semana}"
        )
    # Solo se exponen los campos de la recomendación agrícola — nunca
    # hallazgos_json, aunque la fila completa haya sido legible por RLS.
    recomendacion = boletin["recomendacion_agricola_json"]
    return {"semana": semana, **{k: recomendacion[k] for k in _CAMPOS_RECOMENDACION if k in recomendacion}}


def require_gobierno_o_ayuntamiento(usuario: UsuarioActual = Depends(get_current_user)) -> UsuarioActual:
    if usuario.rol not in ["gobierno", "ayuntamiento"]:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, f"Rol {usuario.rol} no tiene permiso para esta acción"
        )
    return usuario

@app.get("/api/plan-accion/{semana}")
def obtener_plan_accion(
    semana: int,
    usuario: UsuarioActual = Depends(require_gobierno_o_ayuntamiento),
    db: Client = Depends(get_db_public),
) -> list[dict[str, Any]]:
    boletin = _ultimo_boletin_de_semana(db, "boletines", semana)
    if boletin is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No hay boletín para la semana {semana}")
        
    boletin_id = boletin["id"]
    nivel_alerta = boletin.get("nivel_alerta_global", "verde")
    
    respuesta = db.table("planes_accion_generados").select("plan_json").eq("boletin_id", boletin_id).execute()
    if respuesta.data:
        return respuesta.data[0]["plan_json"]
        
    from backend.mcp_tools.plan_accion import generar_plan_accion
    plan = generar_plan_accion(nivel_alerta)
    
    try:
        service_db = _service_client()
        service_db.table("planes_accion_generados").insert(
            {"boletin_id": boletin_id, "plan_json": plan}
        ).execute()
    except Exception:
        pass
    
    return plan

# ── Frontend estático (modo local, un solo puerto — ver run.sh) ────────────


def montar_frontend_estatico(aplicacion: FastAPI, directorio: Path) -> None:
    """Sirve el build estático de Next.js (``frontend/out/``, ``output:
    'export'``) desde el mismo proceso/puerto que la API. Si ``run.sh`` aún
    no corrió el build, el directorio no existe y la API sigue funcionando
    normalmente (solo sin frontend montado en ``/``)."""

    if directorio.is_dir():
        aplicacion.mount("/", StaticFiles(directory=directorio, html=True), name="frontend")


FRONTEND_DIR = Path(os.environ.get("HIDROALERTA_FRONTEND_DIR", "frontend/out"))
montar_frontend_estatico(app, FRONTEND_DIR)
