-- Agregar columnas para el tier EXTREMO (Supervisor y Juez)

ALTER TABLE boletines
ADD COLUMN versiones_json JSONB,
ADD COLUMN evaluacion_calidad_json JSONB;
