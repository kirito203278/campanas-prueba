-- ============================================================================
-- Permiso temporal de edición: el admin puede habilitarle al CM la edición
-- de una semana ya cerrada por 2 horas (columna NULL = sin permiso activo).
-- ============================================================================
ALTER TABLE semanas ADD COLUMN edicion_habilitada_hasta TIMESTAMPTZ;
