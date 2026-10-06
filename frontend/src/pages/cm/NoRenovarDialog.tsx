import { useState } from 'react'
import { api, ApiError } from '../../api/client'

type Paso = 'elegir' | 'conservar' | 'borrar'

export default function NoRenovarDialog({
  clienteId, clienteNombre, onClose, onResuelto,
}: {
  clienteId: number
  clienteNombre: string
  onClose: () => void
  onResuelto: () => void
}) {
  const [paso, setPaso] = useState<Paso>('elegir')
  const [motivo, setMotivo] = useState('')
  const [texto, setTexto] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function conservar() {
    setLoading(true)
    setError(null)
    try {
      await api.post(`/cm/clientes/${clienteId}/no-renovar`, { accion: 'conservar', motivo: motivo || null })
      onResuelto()
      onClose()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo guardar')
    } finally {
      setLoading(false)
    }
  }

  async function borrar() {
    setLoading(true)
    setError(null)
    try {
      await api.post(`/cm/clientes/${clienteId}/no-renovar`, { accion: 'borrar', confirmacion_nombre: texto })
      onResuelto()
      onClose()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo eliminar')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-backdrop">
      <div className="modal" style={{ maxWidth: 460 }}>
        {paso === 'elegir' && (
          <>
            <h2 style={{ marginTop: 0, fontSize: 18 }}>{clienteNombre} no renovó</h2>
            <p style={{ color: 'var(--ink-700)', lineHeight: 1.5 }}>
              ¿Borramos todo lo relacionado a este cliente, o lo conservamos en "No renovados" con su historial?
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 16 }}>
              <button className="btn btn-secondary" onClick={() => setPaso('conservar')}>
                Conservar en "No renovados"
              </button>
              <button className="btn btn-danger" onClick={() => setPaso('borrar')}>
                Borrar todo definitivamente
              </button>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
              <button className="btn btn-ghost" onClick={onClose}>Cancelar</button>
            </div>
          </>
        )}

        {paso === 'conservar' && (
          <>
            <h2 style={{ marginTop: 0, fontSize: 18 }}>Conservar en "No renovados"</h2>
            <p style={{ color: 'var(--ink-700)' }}>
              El historial mensual de {clienteNombre} se conserva mientras renueve dentro de los próximos 2 meses.
              Pasado ese plazo, la siguiente campaña empieza de cero; si no vuelve en 1 año, se elimina automáticamente.
            </p>
            <div className="field">
              <label>Motivo (opcional)</label>
              <textarea rows={3} value={motivo} onChange={(e) => setMotivo(e.target.value)} />
            </div>
            {error && <p className="error-text">{error}</p>}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button className="btn btn-ghost" onClick={() => setPaso('elegir')}>Atrás</button>
              <button className="btn btn-primary" onClick={conservar} disabled={loading}>
                {loading ? <span className="spinner" /> : 'Confirmar'}
              </button>
            </div>
          </>
        )}

        {paso === 'borrar' && (
          <>
            <h2 style={{ marginTop: 0, fontSize: 18 }}>Confirma escribiendo el nombre</h2>
            <p style={{ color: 'var(--ink-700)' }}>
              Esta acción eliminará también sus campañas e historial de forma permanente. Escribe exactamente: <strong>{clienteNombre}</strong>
            </p>
            <input type="text" value={texto} onChange={(e) => setTexto(e.target.value)} autoFocus />
            {error && <p className="error-text">{error}</p>}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 16 }}>
              <button className="btn btn-ghost" onClick={() => setPaso('elegir')}>Atrás</button>
              <button className="btn btn-danger" onClick={borrar} disabled={texto !== clienteNombre || loading}>
                {loading ? <span className="spinner" style={{ borderTopColor: 'var(--bad)', borderColor: '#f3c6c1' }} /> : 'Eliminar definitivamente'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
