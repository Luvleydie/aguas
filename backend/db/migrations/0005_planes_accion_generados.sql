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
