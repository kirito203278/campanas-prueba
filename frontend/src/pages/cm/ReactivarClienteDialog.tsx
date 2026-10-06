import { useState } from 'react'
import { api, ApiError } from '../../api/client'
import type { CampanaDetalle } from '../../api/types'
import CampanaFields, { addMonthIso, newCampanaFieldsValue, todayIso } from './CampanaFields'

type Paso = 'elegir' | 'advertencia' | 'continuar' | 'nueva'

export default function ReactivarClienteDialog({
  clienteId, clienteNombre, puedeContinuar, ultimaCampanaId, ultimaCampanaNombre, onClose, onReactivado,
}: {
  clienteId: number
  clienteNombre: string
  puedeContinuar: boolean
  ultimaCampanaId: number | null
  ultimaCampanaNombre: string | null
  onClose: () => void
  onReactivado: () => void
}) {
  const [paso, setPaso] = useState<Paso>(puedeContinuar && ultimaCampanaId ? 'elegir' : 'advertencia')
  const [fecha, setFecha] = useState(addMonthIso(todayIso()))
  const [campana, setCampana] = useState(newCampanaFieldsValue())
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function continuar() {
    setLoading(true)
    setError(null)
    try {
      await api.post<CampanaDetalle>(`/cm/campanas/${ultimaCampanaId}/renovar`, { fecha_renovacion: fecha })
      onReactivado()
      onClose()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo renovar')
    } finally {
      setLoading(false)
    }
  }

  async function crearNueva() {
    setLoading(true)
    setError(null)
    try {
      await api.post<CampanaDetalle>(`/cm/clientes/${clienteId}/reactivar`, {
        nombre: campana.campanaNombre.trim(),
        paquete: campana.paquete.trim() || null,
        tipo: campana.tipo,
        presupuesto: parseFloat(campana.presupuesto || '0'),
        presupuesto_esquema: 'mensual',
        formato_post: campana.formato_post,
        formato_3d: campana.formato_3d,
        formato_boton: campana.formato_boton,
        formato_otro: campana.formato_otro,
        lugar: campana.lugar.trim() || null,
        fecha_inicio: campana.fecha_inicio,
        fecha_renovacion: campana.fecha_renovacion,
      })
      onReactivado()
      onClose()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo reactivar al cliente')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-backdrop">
      <div className="modal" style={{ maxWidth: paso === 'nueva' ? 780 : 460 }}>
        {paso === 'elegir' && (
          <>
            <h2 style={{ marginTop: 0, fontSize: 18 }}>{clienteNombre} regresa 🎉</h2>
            <p style={{ color: 'var(--ink-700)', lineHeight: 1.5 }}>
              ¿Continúa con la campaña que manejaba antes, o empiezan una campaña nueva?
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 16 }}>
              <button className="btn btn-secondary" onClick={() => setPaso('continuar')}>
                Continuar con "{ultimaCampanaNombre}"
              </button>
              <button className="btn btn-primary" onClick={() => setPaso('nueva')}>
                Crear campaña nueva
              </button>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
              <button className="btn btn-ghost" onClick={onClose}>Cancelar</button>
            </div>
          </>
        )}

        {paso === 'advertencia' && (
          <>
            <h2 style={{ marginTop: 0, fontSize: 18 }}>{clienteNombre} regresa</h2>
            <p style={{ color: 'var(--ink-700)', lineHeight: 1.5 }}>
              Pasaron más de 2 meses desde que este cliente no renovó, así que empezamos desde cero: se
              perderá el historial de sus campañas anteriores y se crea una campaña nueva.
            </p>
            {error && <p className="error-text">{error}</p>}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 16 }}>
              <button className="btn btn-ghost" onClick={onClose}>Cancelar</button>
              <button className="btn btn-primary" onClick={() => setPaso('nueva')}>Entendido, continuar</button>
            </div>
          </>
        )}

        {paso === 'continuar' && (
          <>
            <h2 style={{ marginTop: 0, fontSize: 18 }}>Continuar con "{ultimaCampanaNombre}"</h2>
            <p style={{ color: 'var(--ink-700)' }}>El ciclo reinicia hoy. ¿Cuál es la nueva fecha de renovación?</p>
            <div className="field">
              <label>Nueva fecha de renovación</label>
              <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} />
            </div>
            {error && <p className="error-text">{error}</p>}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button className="btn btn-ghost" onClick={puedeContinuar ? () => setPaso('elegir') : onClose}>
                {puedeContinuar ? 'Atrás' : 'Cancelar'}
              </button>
              <button className="btn btn-primary" onClick={continuar} disabled={loading}>
                {loading ? <span className="spinner" /> : 'Confirmar renovación'}
              </button>
            </div>
          </>
        )}

        {paso === 'nueva' && (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
              <h2 style={{ margin: 0, fontSize: 18 }}>Campaña nueva para {clienteNombre}</h2>
              <button className="btn btn-ghost btn-sm" onClick={onClose}>✕</button>
            </div>
            {error && <p className="error-text" style={{ marginBottom: 14 }}>{error}</p>}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <CampanaFields value={campana} onChange={(patch) => setCampana((c) => ({ ...c, ...patch }))} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 20 }}>
              <button className="btn btn-ghost" onClick={puedeContinuar ? () => setPaso('elegir') : onClose}>
                {puedeContinuar ? 'Atrás' : 'Cancelar'}
              </button>
              <button className="btn btn-primary" onClick={crearNueva} disabled={loading}>
                {loading ? <span className="spinner" /> : 'Reactivar cliente'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
