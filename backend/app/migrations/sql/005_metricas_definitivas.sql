-- ============================================================================
-- Umbrales DEFINITIVOS de rendimiento (sustituyen a los provisionales de la
-- migración 002), confirmados por la agencia. El rendimiento se mide por
-- costo por mensaje: entre más bajo, mejor.
--
--   Local:    bueno 0-19   | regular 20-29  | bajo 30 o más
--   Nacional: bueno 0-14   | regular 15-19  | bajo 20 o más
--   Otro:     igual que Local (no se usa en la práctica; se deja el mismo
--             valor por defecto razonable hasta que se defina uno propio).
--
-- Solo datos, sin cambios de lógica: si esta migración ya se aplicó a mano
-- vía UPDATE directo, este UPDATE es idempotente (deja los mismos valores).
-- ============================================================================
UPDATE metricas_config SET umbral_bueno = 19.00, umbral_regular = 29.00, actualizado_en = now()
    WHERE tipo = 'local' AND paquete IS NULL;

UPDATE metricas_config SET umbral_bueno = 14.00, umbral_regular = 19.00, actualizado_en = now()
    WHERE tipo = 'nacional' AND paquete IS NULL;

UPDATE metricas_config SET umbral_bueno = 19.00, umbral_regular = 29.00, actualizado_en = now()
    WHERE tipo = 'otro' AND paquete IS NULL;
