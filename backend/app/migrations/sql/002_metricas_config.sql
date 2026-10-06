-- ============================================================================
-- Métricas de rendimiento PARAMETRIZADAS (especificación, sección 7)
-- Los umbrales de la sección 7 son provisionales; esta tabla permite
-- sustituirlos sin tocar código. Se puede tener una fila por tipo, o una fila
-- por (tipo, paquete) si algún día los umbrales varían por paquete.
-- ============================================================================
CREATE TABLE metricas_config (
    id                      SERIAL PRIMARY KEY,
    tipo                    TEXT NOT NULL CHECK (tipo IN ('local','nacional','otro')),
    paquete                 TEXT,           -- NULL = aplica a todos los paquetes de ese tipo
    umbral_bueno            NUMERIC(10,2) NOT NULL,   -- costo_por_resultado <= este valor => 'bueno'
    umbral_regular          NUMERIC(10,2) NOT NULL,   -- <= este valor => 'regular'; por encima => 'bajo'
    caida_mensajes_alerta_pct NUMERIC(5,2) NOT NULL DEFAULT 30.00,
    activo                  BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en               TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tipo, paquete)
);

-- Umbrales provisionales de la sección 7. 'otro' no está definido en la
-- especificación; se deja igual a 'local' como valor por defecto razonable
-- hasta que se defina la métrica real.
INSERT INTO metricas_config (tipo, paquete, umbral_bueno, umbral_regular, caida_mensajes_alerta_pct)
VALUES
    ('local',    NULL, 20.00, 30.00, 30.00),
    ('nacional', NULL, 15.00, 25.00, 30.00),
    ('otro',     NULL, 20.00, 30.00, 30.00)
ON CONFLICT (tipo, paquete) DO NOTHING;

-- ============================================================================
-- Refuerzo de reglas duras a nivel de base de datos
-- ============================================================================

-- Regla 3 (sección 11): mensuales inmutables. Sin UPDATE ni DELETE desde la
-- aplicación una vez creados.
CREATE OR REPLACE FUNCTION fn_mensuales_inmutable() RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'La tabla mensuales es inmutable: no se permite % sobre registros existentes', TG_OP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_mensuales_no_update
    BEFORE UPDATE ON mensuales
    FOR EACH ROW EXECUTE FUNCTION fn_mensuales_inmutable();

CREATE TRIGGER trg_mensuales_no_delete
    BEFORE DELETE ON mensuales
    FOR EACH ROW EXECUTE FUNCTION fn_mensuales_inmutable();

-- Regla 3: captura manual de mensual solo si la campaña no tiene ninguno.
CREATE OR REPLACE FUNCTION fn_mensuales_manual_solo_primero() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.origen = 'manual' AND EXISTS (
        SELECT 1 FROM mensuales WHERE campana_id = NEW.campana_id
    ) THEN
        RAISE EXCEPTION 'Ya existe un mensual para esta campaña: la captura manual solo se permite si no hay ninguno previo';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_mensuales_manual_solo_primero
    BEFORE INSERT ON mensuales
    FOR EACH ROW EXECUTE FUNCTION fn_mensuales_manual_solo_primero();
