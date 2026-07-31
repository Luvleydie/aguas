-- Limpieza inicial para permitir ejecuciones múltiples sin errores
DROP TABLE IF EXISTS public.agent_logs CASCADE;
DROP TABLE IF EXISTS public.acciones_ayuntamiento CASCADE;
DROP TABLE IF EXISTS public.alertas_enviadas CASCADE;
DROP TABLE IF EXISTS public.planes_accion_generados CASCADE;
DROP TABLE IF EXISTS public.boletines CASCADE;
DROP TABLE IF EXISTS public.usuarios CASCADE;
DROP TYPE IF EXISTS public.rol_usuario CASCADE;
DROP TYPE IF EXISTS public.nivel_alerta CASCADE;
DROP TYPE IF EXISTS public.canal_alerta CASCADE;
DROP TYPE IF EXISTS public.estado_alerta CASCADE;
DELETE FROM auth.users;

-- HidroAlerta — schema inicial de Supabase (Postgres)
-- Ver arquitectura-hidroalerta.md §7 para el diagrama de relaciones y §8
-- para qué pantalla/rol consume cada tabla.
--
-- Punto de partida para Persona A + expert-bd. Metodología de expert-bd.md
-- sigue aplicando: por cada tabla, escribe primero el test de
-- insert/constraint/RLS que falla, corre esta migración (o la parte que
-- corresponda), confirma que el test pasa. No lo marques "listo" sin esos
-- tests — este archivo es el DDL, no reemplaza la suite.

-- ── Enums fijos (regla expert-bd: no usar tipos libres) ────────────────────
create type rol_usuario as enum ('gobierno', 'ayuntamiento', 'medios', 'agricultor');
create type nivel_alerta as enum ('verde', 'amarillo', 'naranja', 'rojo');
create type canal_alerta as enum ('web', 'whatsapp', 'push');
create type estado_alerta as enum ('pendiente', 'enviado', 'fallido');

-- ── usuarios ────────────────────────────────────────────────────────────
create table usuarios (
    id uuid primary key default gen_random_uuid(),
    auth_user_id uuid unique references auth.users(id) on delete cascade,
    nombre text not null,
    rol rol_usuario not null,
    telefono text,
    email text unique not null,
    municipio text,
    recibir_whatsapp boolean not null default false, -- opt-in, fase extra (§13)
    created_at timestamptz not null default now()
);

-- ── boletines ───────────────────────────────────────────────────────────
create table boletines (
    id uuid primary key default gen_random_uuid(),
    semana integer not null check (semana between 1 and 53),
    anio integer not null default extract(year from now())::integer,
    markdown text not null,               -- 4 secciones reales (boletin_referencia.md)
    hallazgos_json jsonb not null,         -- NO exponer a agricultor/medios, ver vista abajo
    recomendacion_agricola_json jsonb,
    nivel_alerta_global nivel_alerta not null,
    recomendacion text not null,
    publicado boolean not null default false,
    generado_por uuid not null references usuarios(id),
    created_at timestamptz not null default now(),
    published_at timestamptz,
    unique (semana, anio)
);

-- ── agent_logs (auditoría — regla 7 de CLAUDE.md) ──────────────────────
create table agent_logs (
    id uuid primary key default gen_random_uuid(),
    boletin_id uuid not null references boletines(id) on delete cascade,
    agente text not null check (agente in ('explorador', 'estadista', 'narrador', 'agronomo')),
    mensaje jsonb not null,
    tool_llamada text,
    tool_resultado jsonb,
    "timestamp" timestamptz not null default now()
);

-- ── acciones_ayuntamiento ───────────────────────────────────────────────
create table acciones_ayuntamiento (
    id uuid primary key default gen_random_uuid(),
    boletin_id uuid not null references boletines(id) on delete cascade,
    usuario_id uuid not null references usuarios(id),
    accion text not null,
    fecha timestamptz not null default now(),
    notas text
);

-- ── alertas_enviadas ────────────────────────────────────────────────────
create table alertas_enviadas (
    id uuid primary key default gen_random_uuid(),
    boletin_id uuid not null references boletines(id) on delete cascade,
    usuario_id uuid not null references usuarios(id),
    canal canal_alerta not null default 'web',
    fecha_envio timestamptz not null default now(),
    estado estado_alerta not null default 'pendiente'
);

-- Opt-in de WhatsApp (fase extra §13, dejado listo desde ya):
-- nunca debe existir una fila canal='whatsapp' si el usuario no hizo opt-in.
create or replace function chk_whatsapp_opt_in() returns trigger as $$
begin
    if new.canal = 'whatsapp' then
        if not exists (
            select 1 from usuarios
            where id = new.usuario_id and recibir_whatsapp = true
        ) then
            raise exception 'usuario % no tiene opt-in de whatsapp (recibir_whatsapp=false)', new.usuario_id;
        end if;
    end if;
    return new;
end;
$$ language plpgsql;

create trigger trg_whatsapp_opt_in
    before insert or update on alertas_enviadas
    for each row execute function chk_whatsapp_opt_in();

-- ── Índices ─────────────────────────────────────────────────────────────
create index idx_agent_logs_boletin on agent_logs(boletin_id);
create index idx_boletines_semana_anio on boletines(semana, anio);
create index idx_acciones_boletin on acciones_ayuntamiento(boletin_id);
create index idx_alertas_boletin on alertas_enviadas(boletin_id);

-- ── RLS ─────────────────────────────────────────────────────────────────
alter table usuarios enable row level security;
alter table boletines enable row level security;
alter table agent_logs enable row level security;
alter table acciones_ayuntamiento enable row level security;
alter table alertas_enviadas enable row level security;

-- Rol del usuario autenticado actual (helper para las políticas de abajo).
create or replace function rol_actual() returns rol_usuario as $$
    select rol from usuarios where auth_user_id = auth.uid();
$$ language sql stable;

-- usuarios: cada quien ve su propia fila; gobierno ve todas.
create policy usuarios_select_propio on usuarios
    for select using (auth_user_id = auth.uid() or rol_actual() = 'gobierno');

-- boletines: publicados visibles para cualquier rol autenticado; gobierno
-- ve también los no publicados (borradores en progreso).
create policy boletines_select_publicados on boletines
    for select using (publicado = true or rol_actual() = 'gobierno');

-- Solo gobierno genera (insert) y publica (update) boletines.
create policy boletines_insert_gobierno on boletines
    for insert with check (rol_actual() = 'gobierno');

create policy boletines_update_gobierno on boletines
    for update using (rol_actual() = 'gobierno');

-- ⚠️ RLS es por FILA, no por COLUMNA: la política de arriba no basta para
-- esconder hallazgos_json/recomendacion_agricola_json de agricultor/medios
-- (expert-seguridad: "agricultor no accede a hallazgos_json"). Los roles
-- que no son gobierno deben leer esta vista, nunca la tabla directamente:
create view boletines_publico as
    select id, semana, anio, markdown, nivel_alerta_global, recomendacion,
           publicado, generado_por, created_at, published_at
    from boletines
    where publicado = true;

alter view boletines_publico set (security_invoker = true);

-- agent_logs: solo gobierno (auditoría completa). Agricultor NUNCA ve esto.
create policy agent_logs_select_gobierno on agent_logs
    for select using (rol_actual() = 'gobierno');

-- acciones_ayuntamiento: el usuario ve/crea sus propias acciones; gobierno ve todo.
create policy acciones_select on acciones_ayuntamiento
    for select using (
        usuario_id in (select id from usuarios where auth_user_id = auth.uid())
        or rol_actual() = 'gobierno'
    );

create policy acciones_insert_ayuntamiento on acciones_ayuntamiento
    for insert with check (rol_actual() = 'ayuntamiento');

-- alertas_enviadas: cada usuario ve solo las suyas; gobierno ve todas.
create policy alertas_select_propias on alertas_enviadas
    for select using (
        usuario_id in (select id from usuarios where auth_user_id = auth.uid())
        or rol_actual() = 'gobierno'
    );
-- 0001_init_schema.sql solo definió SELECT para agent_logs (gobierno). El
-- backend (backend/main.py::generar_boletin) inserta el rastro de auditoría
-- con el token del propio usuario gobierno que disparó el pipeline, no con
-- la service key, así que necesita también INSERT.
-- Encontrado por TDD: tests/db/test_agent_logs.py::test_rls_gobierno_puede_insertar_agent_log
-- estaba en rojo contra el schema recién aplicado.

create policy agent_logs_insert_gobierno
    on agent_logs
    for insert
    with check (rol_actual() = 'gobierno');
-- La política original de 0001_init_schema.sql solo exigía
-- rol_actual() = 'ayuntamiento' al insertar en acciones_ayuntamiento, sin
-- atar `usuario_id` al auth.uid() de quien hace la petición: cualquier
-- usuario con rol ayuntamiento podía registrar una acción a nombre de otro.
-- Encontrado por TDD: tests/db/test_acciones_ayuntamiento.py::
-- test_rls_ayuntamiento_no_puede_suplantar_a_otro_usuario_al_insertar
-- (ya señalado como riesgo conocido al implementar backend/main.py, que sí
-- fuerza usuario_id = usuario autenticado a nivel API, pero la base de datos
-- debía exigirlo también).

drop policy if exists acciones_insert_ayuntamiento on acciones_ayuntamiento;

create policy acciones_insert_ayuntamiento
    on acciones_ayuntamiento
    for insert
    with check (
        rol_actual() = 'ayuntamiento'
        and usuario_id in (select id from usuarios where auth_user_id = auth.uid())
    );
-- rol_actual() consultaba `usuarios` sin SECURITY DEFINER. Como esa misma
-- tabla tiene RLS que a su vez invoca rol_actual() (usuarios_select_propio:
-- "auth_user_id = auth.uid() or rol_actual() = 'gobierno'"), cualquier
-- evaluación de la rama OR disparaba recursión infinita
-- (Postgres: "statement too complex"). Con SECURITY DEFINER la consulta
-- interna corre como el dueño de la función (que es dueño de la tabla y por
-- tanto no está sujeto a su propio RLS), rompiendo la recursión — mismo
-- patrón que .agents/skills/supabase-postgres-best-practices/references/
-- security-rls-performance.md recomienda para estos helpers.
--
-- Encontrado por TDD: 8 de los tests de RLS en tests/db/ fallaban con
-- psycopg.errors.StatementTooComplex antes de esta migración.

create or replace function rol_actual() returns rol_usuario
language sql
stable
security definer
set search_path = public, pg_temp
as $$
    select rol from usuarios where auth_user_id = auth.uid();
$$;
-- Migración 0005: Tabla para guardar planes de acción generados (auditoría/caché)
CREATE TABLE IF NOT EXISTS public.planes_accion_generados (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    boletin_id UUID NOT NULL REFERENCES public.boletines(id) ON DELETE CASCADE,
    plan_json JSONB NOT NULL,
    fecha_generacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_plan_por_boletin UNIQUE (boletin_id)
);

-- Políticas de RLS
ALTER TABLE public.planes_accion_generados ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Los usuarios de gobierno pueden ver todo" ON public.planes_accion_generados
FOR SELECT
USING (public.rol_actual() = 'gobierno');

CREATE POLICY "Los ayuntamientos pueden ver los planes publicados" ON public.planes_accion_generados
FOR SELECT
USING (public.rol_actual() = 'ayuntamiento');

-- Escritura: En principio, manejada por rol de servicio desde el backend, pero habilitamos insert/update para testing/api si es necesario (el backend usa service_role usualmente).
CREATE POLICY "Escritura planes generados" ON public.planes_accion_generados
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
-- Agregar columnas para el tier EXTREMO (Supervisor y Juez)

ALTER TABLE boletines
ADD COLUMN versiones_json JSONB,
ADD COLUMN evaluacion_calidad_json JSONB;


-- -- Usuarios por defecto ------------------------------------------------
DO $$
DECLARE
  uid_gobierno uuid := gen_random_uuid();
  uid_ayunta uuid := gen_random_uuid();
  uid_prensa uuid := gen_random_uuid();
  uid_agri uuid := gen_random_uuid();
BEGIN
  -- Insertar en auth.users (Supabase Auth)
  INSERT INTO auth.users (id, instance_id, aud, role, email, encrypted_password, email_confirmed_at, raw_app_meta_data, raw_user_meta_data, created_at, updated_at)
  VALUES 
    (uid_gobierno, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 'el_gob@gurango.gob.mx', crypt('D', gen_salt('bf')), now(), '{"provider":"email","providers":["email"]}', '{}', now(), now()),
    (uid_ayunta, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 'ay@ayuntamiento.com', crypt('D', gen_salt('bf')), now(), '{"provider":"email","providers":["email"]}', '{}', now(), now()),
    (uid_prensa, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 'm_p@prensa.com', crypt('D', gen_salt('bf')), now(), '{"provider":"email","providers":["email"]}', '{}', now(), now()),
    (uid_agri, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 'mmrm.miriam@gmail.com', crypt('D', gen_salt('bf')), now(), '{"provider":"email","providers":["email"]}', '{}', now(), now());

  -- Insertar identidades (recomendado por Supabase)
  INSERT INTO auth.identities (id, user_id, provider_id, identity_data, provider, last_sign_in_at, created_at, updated_at)
  VALUES
    (gen_random_uuid(), uid_gobierno, uid_gobierno::text, format('{"sub":"%s","email":"%s"}', uid_gobierno::text, 'el_gob@gurango.gob.mx')::jsonb, 'email', now(), now(), now()),
    (gen_random_uuid(), uid_ayunta, uid_ayunta::text, format('{"sub":"%s","email":"%s"}', uid_ayunta::text, 'ay@ayuntamiento.com')::jsonb, 'email', now(), now(), now()),
    (gen_random_uuid(), uid_prensa, uid_prensa::text, format('{"sub":"%s","email":"%s"}', uid_prensa::text, 'm_p@prensa.com')::jsonb, 'email', now(), now(), now()),
    (gen_random_uuid(), uid_agri, uid_agri::text, format('{"sub":"%s","email":"%s"}', uid_agri::text, 'mmrm.miriam@gmail.com')::jsonb, 'email', now(), now(), now());

  -- Insertar en public.usuarios (Nuestra tabla)
  INSERT INTO public.usuarios (auth_user_id, nombre, rol, email, recibir_whatsapp)
  VALUES
    (uid_gobierno, 'Gobierno del Estado', 'gobierno', 'el_gob@gurango.gob.mx', false),
    (uid_ayunta, 'Ayuntamiento Centro', 'ayuntamiento', 'ay@ayuntamiento.com', false),
    (uid_prensa, 'Medios de Prensa', 'medios', 'm_p@prensa.com', false),
    (uid_agri, 'Agricultor Miriam', 'agricultor', 'mmrm.miriam@gmail.com', false);
END $$;

