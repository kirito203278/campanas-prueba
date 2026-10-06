import { useState } from 'react'
import { api, ApiError } from '../../api/client'
import type { CMConCartera, MigrarCMOut } from '../../api/types'

export default function BajaCmDialog({
  cm, otrosCms, onClose, onMigrado,
}: {
  cm: CMConCartera
  otrosCms: CMConCartera[]
  onClose: () => void
  onMigrado: () => void
}) {
  const sinCartera = cm.total_clientes === 0
  const [destino, setDestino] = useState<number | ''>(otrosCms[0]?.id ?? '')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function confirmar() {
    if (!sinCartera && destino === '') return
    setLoading(true)
    setError(null)
    try {
      await api.post<MigrarCMOut>(`/admin/cms/${cm.id}/baja`, { migrar_a_cm_id: sinCartera ? null : destino })
      onMigrado()
      onClose()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo dar de baja')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-backdrop">
      <div className="modal" style={{ maxWidth: 440 }}>
        <h2 style={{ marginTop: 0, fontSize: 18 }}>Dar de baja a {cm.nombre}</h2>
        {sinCartera ? (
          <p style={{ color: 'var(--ink-700)', lineHeight: 1.5 }}>
            Esta cuenta no tiene clientes en su cartera — se puede dar de baja directamente, sin migrar nada.
          </p>
        ) : (
          <>
            <p style={{ color: 'var(--ink-700)', lineHeight: 1.5 }}>
              Su cartera completa ({cm.total_clientes} cliente{cm.total_clientes !== 1 ? 's' : ''}, con campañas,
              credenciales y datos semanales del ciclo abierto) se migra por completo a otro CM.
            </p>
            {otrosCms.length === 0 ? (
              <p className="error-text">No hay otro CM activo disponible para migrar la cartera.</p>
            ) : (
              <div className="field">
                <label>Migrar cartera a</label>
                <select value={destino} onChange={(e) => setDestino(Number(e.target.value))}>
                  {otrosCms.map((o) => <option key={o.id} value={o.id}>{o.nombre}</option>)}
                </select>
              </div>
            )}
          </>
        )}

        {error && <p className="error-text">{error}</p>}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 10 }}>
          <button className="btn btn-ghost" onClick={onClose}>Cancelar</button>
          <button className="btn btn-danger" onClick={confirmar} disabled={loading || (!sinCartera && otrosCms.length === 0)}>
            {loading ? <span className="spinner" style={{ borderTopColor: 'var(--bad)', borderColor: '#f3c6c1' }} /> : sinCartera ? 'Confirmar baja' : 'Confirmar baja y migración'}
          </button>
        </div>
      </div>
    </div>
  )
}
