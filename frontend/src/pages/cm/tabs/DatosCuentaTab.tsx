import { useEffect, useState } from 'react'
import { api, ApiError } from '../../../api/client'
import type { CuentaOut } from '../../../api/types'

export default function DatosCuentaTab({ clienteId }: { clienteId: number }) {
  const [cuenta, setCuenta] = useState<CuentaOut | null>(null)
  const [loading, setLoading] = useState(true)
  const [showPassword, setShowPassword] = useState(false)
  const [editing, setEditing] = useState(false)
  const [usuario, setUsuario] = useState('')
  const [password, setPassword] = useState('')
  const [tipoCuenta, setTipoCuenta] = useState('')
  const [metodoPago, setMetodoPago] = useState('')
  const [formaPago, setFormaPago] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sinCuenta, setSinCuenta] = useState(false)

  function cargarDesde(c: CuentaOut) {
    setCuenta(c)
    setUsuario(c.usuario)
    setPassword(c.password)
    setTipoCuenta(c.tipo_cuenta ?? '')
    setMetodoPago(c.metodo_pago ?? '')
    setFormaPago(c.forma_pago ?? '')
  }

  async function load() {
    setLoading(true)
    setSinCuenta(false)
    try {
      const c = await api.get<CuentaOut>(`/cm/clientes/${clienteId}/cuenta`)
      cargarDesde(c)
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) setSinCuenta(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [clienteId]) // eslint-disable-line react-hooks/exhaustive-deps

  async function guardar() {
    setSaving(true)
    setError(null)
    try {
      const c = await api.put<CuentaOut>(`/cm/clientes/${clienteId}/cuenta`, {
        usuario, password,
        tipo_cuenta: tipoCuenta || null,
        metodo_pago: metodoPago || null,
        forma_pago: formaPago || null,
      })
      cargarDesde(c)
      setEditing(false)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo guardar')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p style={{ color: 'var(--ink-500)' }}>Cargando…</p>
  if (sinCuenta) return <p style={{ color: 'var(--ink-500)' }}>Este cliente no tiene una cuenta vinculada.</p>
  if (!cuenta) return null

  return (
    <div className="card cm-main-wave-target" style={{ padding: 20, maxWidth: 460 }}>
      <div className="field">
        <label>Usuario</label>
        <input type="text" value={usuario} disabled={!editing} onChange={(e) => setUsuario(e.target.value)} />
      </div>
      <div className="field">
        <label>Contraseña</label>
        <div style={{ display: 'flex', gap: 8 }}>
          <input type={showPassword ? 'text' : 'password'} value={password} disabled={!editing}
                 onChange={(e) => setPassword(e.target.value)} />
          <button className="btn btn-ghost btn-sm" onClick={() => setShowPassword((v) => !v)} type="button">
            {showPassword ? 'Ocultar' : 'Ver'}
          </button>
        </div>
      </div>
      <div className="field">
        <label>Tipo de cuenta</label>
        <input type="text" value={tipoCuenta} disabled={!editing} onChange={(e) => setTipoCuenta(e.target.value)}
               placeholder="Ej. Business Manager, personal…" />
      </div>
      <div className="field">
        <label>Método de pago</label>
        <input type="text" value={metodoPago} disabled={!editing} onChange={(e) => setMetodoPago(e.target.value)}
               placeholder="Ej. Tarjeta de crédito, transferencia…" />
      </div>
      <div className="field">
        <label>Forma de pago</label>
        <input type="text" value={formaPago} disabled={!editing} onChange={(e) => setFormaPago(e.target.value)}
               placeholder="Ej. Mensual, quincenal…" />
      </div>

      {error && <p className="error-text">{error}</p>}

      {editing ? (
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-primary" onClick={guardar} disabled={saving}>
            {saving ? <span className="spinner" /> : 'Guardar cambios'}
          </button>
          <button className="btn btn-ghost" onClick={() => { setEditing(false); cargarDesde(cuenta) }}>
            Cancelar
          </button>
        </div>
      ) : (
        <button className="btn btn-secondary" onClick={() => setEditing(true)}>Editar datos de la cuenta</button>
      )}
    </div>
  )
}
