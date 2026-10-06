import { useState } from 'react'
import { api, ApiError } from '../../api/client'
import type { ClienteLoteItemIn, FilaConfirmacionOut, FilaErrorOut } from '../../api/types'
import CampanaFields, { newCampanaFieldsValue, type CampanaFieldsValue } from './CampanaFields'

interface RowState extends CampanaFieldsValue {
  nombre: string
  usuario: string
  password: string
  tipoCuenta: string
  metodoPago: string
  formaPago: string
  confirmar_vinculo: boolean
  confirmacionPendiente?: string
  rowErrors: string[]
}

function newRow(): RowState {
  return {
    nombre: '', usuario: '', password: '',
    tipoCuenta: '', metodoPago: '', formaPago: '',
    ...newCampanaFieldsValue(),
    confirmar_vinculo: false, rowErrors: [],
  }
}

export default function AddClientesModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [rows, setRows] = useState<RowState[]>([newRow()])
  const [submitting, setSubmitting] = useState(false)
  const [generalError, setGeneralError] = useState<string | null>(null)

  function updateRow(idx: number, patch: Partial<RowState>) {
    setRows((rs) => rs.map((r, i) => (i === idx ? { ...r, ...patch, rowErrors: [], confirmacionPendiente: undefined } : r)))
  }

  function addRow() {
    setRows((rs) => [...rs, newRow()])
  }

  function removeRow(idx: number) {
    setRows((rs) => rs.filter((_, i) => i !== idx))
  }

  function buildPayload(): ClienteLoteItemIn[] {
    return rows.map((r) => ({
      nombre: r.nombre.trim(),
      cuenta: { usuario: r.usuario.trim(), password: r.password },
      campana: {
        nombre: r.campanaNombre.trim(),
        paquete: r.paquete.trim() || null,
        tipo: r.tipo,
        presupuesto: parseFloat(r.presupuesto || '0'),
        presupuesto_esquema: 'mensual',
        formato_post: r.formato_post,
        formato_3d: r.formato_3d,
        formato_boton: r.formato_boton,
        formato_otro: r.formato_otro,
        lugar: r.lugar.trim() || null,
        fecha_inicio: r.fecha_inicio,
        fecha_renovacion: r.fecha_renovacion,
      },
      confirmar_vinculo: r.confirmar_vinculo,
      tipo_cuenta: r.tipoCuenta.trim() || null,
      metodo_pago: r.metodoPago.trim() || null,
      forma_pago: r.formaPago.trim() || null,
    }))
  }

  async function handleSubmit() {
    setSubmitting(true)
    setGeneralError(null)
    try {
      await api.post('/cm/clientes/lote', { clientes: buildPayload() })
      onCreated()
      onClose()
    } catch (err) {
      if (err instanceof ApiError && err.status === 422) {
        const detail = (err.body as { detail?: unknown })?.detail as { errores?: FilaErrorOut[] } | undefined
        if (detail?.errores) {
          setRows((rs) => rs.map((r, i) => {
            const fila = detail.errores!.find((e) => e.index === i)
            return fila ? { ...r, rowErrors: fila.errores } : r
          }))
        } else {
          setGeneralError('Revisa los campos: hay datos incompletos o inválidos.')
        }
      } else if (err instanceof ApiError && err.status === 409) {
        const detail = (err.body as { detail?: unknown })?.detail as { confirmaciones_requeridas?: FilaConfirmacionOut[] } | undefined
        if (detail?.confirmaciones_requeridas) {
          setRows((rs) => rs.map((r, i) => {
            const fila = detail.confirmaciones_requeridas!.find((c) => c.index === i)
            return fila ? { ...r, confirmacionPendiente: fila.cliente_existente } : r
          }))
        }
      } else if (err instanceof ApiError) {
        setGeneralError(err.message)
      } else {
        setGeneralError('No se pudo guardar el lote.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-backdrop">
      <div className="modal" style={{ maxWidth: 780 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
          <h2 style={{ margin: 0, fontSize: 18 }}>Agregar clientes</h2>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>✕</button>
        </div>

        {generalError && <p className="error-text" style={{ marginBottom: 14 }}>{generalError}</p>}

        {rows.map((row, idx) => (
          <div key={idx} className="card" style={{ padding: 18, marginBottom: 16, borderColor: row.rowErrors.length ? 'var(--bad)' : row.confirmacionPendiente ? 'var(--warn)' : undefined }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <strong style={{ fontSize: 13, color: 'var(--ink-500)' }}>Cliente {idx + 1}</strong>
              {rows.length > 1 && (
                <button className="btn btn-ghost btn-sm" onClick={() => removeRow(idx)}>Quitar</button>
              )}
            </div>

            {row.rowErrors.length > 0 && (
              <ul style={{ margin: '0 0 10px', paddingLeft: 18, color: 'var(--bad)', fontSize: 13 }}>
                {row.rowErrors.map((e, i) => <li key={i}>{e}</li>)}
              </ul>
            )}

            {row.confirmacionPendiente && (
              <div style={{ background: 'var(--warn-bg)', border: '1px solid #eddca3', borderRadius: 8, padding: '10px 12px', marginBottom: 12, fontSize: 13 }}>
                Esta cuenta ya está registrada (cliente <strong>{row.confirmacionPendiente}</strong>).
                ¿Vincular también a este cliente?
                <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                  <button className="btn btn-secondary btn-sm" onClick={() => updateRow(idx, { confirmar_vinculo: true, confirmacionPendiente: undefined })}>
                    Sí, vincular
                  </button>
                  <button className="btn btn-ghost btn-sm" onClick={() => updateRow(idx, { confirmacionPendiente: undefined })}>
                    Cancelar / corregir datos
                  </button>
                </div>
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div className="field" style={{ gridColumn: '1 / -1' }}>
                <label>Nombre del cliente</label>
                <input type="text" value={row.nombre} onChange={(e) => updateRow(idx, { nombre: e.target.value })} placeholder="Novedades" />
              </div>

              <div className="field">
                <label>Usuario de la cuenta</label>
                <input type="text" value={row.usuario} onChange={(e) => updateRow(idx, { usuario: e.target.value })} />
              </div>
              <div className="field">
                <label>Contraseña de la cuenta</label>
                <input type="text" value={row.password} onChange={(e) => updateRow(idx, { password: e.target.value })} />
              </div>
              <div className="field">
                <label>Tipo de cuenta</label>
                <input type="text" value={row.tipoCuenta} onChange={(e) => updateRow(idx, { tipoCuenta: e.target.value })}
                       placeholder="Ej. Business Manager, personal…" />
              </div>
              <div className="field">
                <label>Método de pago</label>
                <input type="text" value={row.metodoPago} onChange={(e) => updateRow(idx, { metodoPago: e.target.value })}
                       placeholder="Ej. Tarjeta de crédito, transferencia…" />
              </div>
              <div className="field">
                <label>Forma de pago</label>
                <input type="text" value={row.formaPago} onChange={(e) => updateRow(idx, { formaPago: e.target.value })}
                       placeholder="Ej. Mensual, quincenal…" />
              </div>

              <CampanaFields value={row} onChange={(patch) => updateRow(idx, patch)} />
            </div>
          </div>
        ))}

        <button className="btn btn-secondary" onClick={addRow} style={{ marginBottom: 20 }}>+ Agregar otra fila</button>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
          <button className="btn btn-ghost" onClick={onClose}>Cancelar</button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting}>
            {submitting ? <span className="spinner" /> : 'Guardar clientes'}
          </button>
        </div>
      </div>
    </div>
  )
}
