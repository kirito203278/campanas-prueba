import { useState } from 'react'
import { api, ApiError } from '../../api/client'

export default function DeleteClientDialog({
  clienteId, clienteNombre, onClose, onDeleted,
}: {
  clienteId: number
  clienteNombre: string
  onClose: () => void
  onDeleted: () => void
}) {
  const [step, setStep] = useState<1 | 2>(1)
  const [texto, setTexto] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function confirmar() {
    setLoading(true)
    setError(null)
    try {
      await api.del(`/cm/clientes/${clienteId}`, { confirmacion_nombre: texto })
      onDeleted()
      onClose()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo eliminar el cliente')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-backdrop">
      <div className="modal" style={{ maxWidth: 460 }}>
        {step === 1 ? (
          <>
            <h2 style={{ marginTop: 0, fontSize: 18 }}>¿Eliminar a {clienteNombre}?</h2>
            <p style={{ color: 'var(--ink-700)', lineHeight: 1.5 }}>
              Esta acción eliminará también sus campañas e historial de forma permanente. No se puede deshacer.
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 20 }}>
              <button className="btn btn-ghost" onClick={onClose}>Cancelar</button>
              <button className="btn btn-danger" onClick={() => setStep(2)}>Sí, quiero eliminarlo</button>
            </div>
          </>
        ) : (
          <>
            <h2 style={{ marginTop: 0, fontSize: 18 }}>Confirma escribiendo el nombre</h2>
            <p style={{ color: 'var(--ink-700)', lineHeight: 1.5 }}>
              Para confirmar, escribe exactamente: <strong>{clienteNombre}</strong>
            </p>
            <input type="text" value={texto} onChange={(e) => setTexto(e.target.value)} autoFocus />
            {error && <p className="error-text">{error}</p>}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 20 }}>
              <button className="btn btn-ghost" onClick={onClose}>Cancelar</button>
              <button className="btn btn-danger" onClick={confirmar} disabled={texto !== clienteNombre || loading}>
                {loading ? <span className="spinner" style={{ borderTopColor: 'var(--bad)', borderColor: '#f3c6c1' }} /> : 'Eliminar definitivamente'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
