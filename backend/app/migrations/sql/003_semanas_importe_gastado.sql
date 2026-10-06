-- ============================================================================
-- Se agrega el importe gastado por semana como dato capturado independiente
-- del costo por resultado (igual que en la plataforma publicitaria, "costo
-- por resultado" e "importe gastado" son dos métricas separadas, no una
-- calculada de la otra).
-- ============================================================================
ALTER TABLE semanas ADD COLUMN importe_gastado NUMERIC(10,2);
