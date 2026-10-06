-- ============================================================================
-- Datos de pago del cliente, capturados junto con la cuenta al dar de alta
-- (viven en el cliente, no en la cuenta publicitaria compartida: el tipo de
-- cuenta y la forma de pago son propios de la relación con ESE cliente,
-- incluso si dos clientes comparten el mismo login de la cuenta publicitaria).
-- ============================================================================
ALTER TABLE clientes ADD COLUMN tipo_cuenta TEXT;
ALTER TABLE clientes ADD COLUMN metodo_pago TEXT;
ALTER TABLE clientes ADD COLUMN forma_pago TEXT;
