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
