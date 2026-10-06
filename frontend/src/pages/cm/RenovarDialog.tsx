import { useState } from 'react'
import { api, ApiError } from '../../api/client'
import type { CampanaDetalle } from '../../api/types'

// "Un mes" para efectos de la campaña son 30 días exactos, no el mes de
// calendario (que da 28-31 días según el mes de arranque).
function inUnMesIso() {
  const d = new Date()
  d.setDate(d.getDate() + 30)
  return d.toISOString().slice(0, 10)
}

export default function RenovarDialog({
  campanaId, onClose, onRenovada,
}: {
  campanaId: number
  onClose: () => void
  onRenovada: () => void
}) {
  const [fecha, setFecha] = useState(inUnMesIso())
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function confirmar() {
    setLoading(true)
    setError(null)
    try {
      await api.post<CampanaDetalle>(`/cm/campanas/${campanaId}/renovar`, { fecha_renovacion: fecha })
      onRenovada()
      onClose()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo renovar')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-backdrop">
      <div className="modal" style={{ maxWidth: 420 }}>
        <h2 style={{ marginTop: 0, fontSize: 18 }}>El cliente renovó 🎉</h2>
        <p style={{ color: 'var(--ink-700)' }}>El ciclo reinicia hoy. ¿Cuál es la nueva fecha de renovación?</p>
        <div className="field">
          <label>Nueva fecha de renovación</label>
          <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} />
        </div>
        {error && <p className="error-text">{error}</p>}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
          <button className="btn btn-ghost" onClick={onClose}>Cancelar</button>
          <button className="btn btn-primary" onClick={confirmar} disabled={loading}>
            {loading ? <span className="spinner" /> : 'Confirmar renovación'}
          </button>
        </div>
      </div>
    </div>
  )
}
