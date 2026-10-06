import { useEffect, useState } from 'react'
import { api, ApiError, downloadFile } from '../../api/client'
import type { CampanaDetalle, ClienteDetalle } from '../../api/types'
import DatosSemanalesTab from './tabs/DatosSemanalesTab'
import ObservacionesTab from './tabs/ObservacionesTab'
import DatosCuentaTab from './tabs/DatosCuentaTab'
import DeleteClientDialog from './DeleteClientDialog'
import RenovarDialog from './RenovarDialog'
import NoRenovarDialog from './NoRenovarDialog'

type TabKey = 'semanales' | 'observaciones' | 'cuenta'

const TIPO_LABEL: Record<string, string> = { local: 'Local', nacional: 'Nacional', otro: 'Otro' }

function formatFecha(iso: string) {
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

export default function ClienteDetail({
  clienteId, onClienteChanged, onClienteDeleted,
}: {
  clienteId: number
  onClienteChanged: () => void
  onClienteDeleted: () => void
}) {
  const [cliente, setCliente] = useState<ClienteDetalle | null>(null)
  const [campanaId, setCampanaId] = useState<number | null>(null)
  const [campana, setCampana] = useState<CampanaDetalle | null>(null)
  const [tab, setTab] = useState<TabKey>('semanales')
  const [renaming, setRenaming] = useState(false)
  const [nombreDraft, setNombreDraft] = useState('')
  const [renameError, setRenameError] = useState<string | null>(null)
  const [showDelete, setShowDelete] = useState(false)
  const [showRenovar, setShowRenovar] = useState(false)
  const [showNoRenovar, setShowNoRenovar] = useState(false)
  const [generandoReporte, setGenerandoReporte] = useState<'mensual' | 'semanal' | null>(null)
  const [reporteError, setReporteError] = useState<string | null>(null)

  async function loadCliente() {
    const c = await api.get<ClienteDetalle>(`/cm/clientes/${clienteId}`)
    setCliente(c)
    setNombreDraft(c.nombre)
    if (c.campanas.length > 0) setCampanaId((prev) => (prev && c.campanas.some((camp) => camp.id === prev) ? prev : c.campanas[0].id))
  }

  async function recargarCampana() {
    if (campanaId != null) setCampana(await api.get<CampanaDetalle>(`/cm/campanas/${campanaId}`))
  }

  useEffect(() => {
    setTab('semanales')
    loadCliente()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clienteId])

  useEffect(() => {
    if (campanaId == null) { setCampana(null); return }
    api.get<CampanaDetalle>(`/cm/campanas/${campanaId}`).then(setCampana)
  }, [campanaId])

  async function guardarNombre() {
    setRenameError(null)
    try {
      const c = await api.patch<ClienteDetalle>(`/cm/clientes/${clienteId}`, { nombre: nombreDraft })
      setCliente(c)
      setRenaming(false)
      onClienteChanged()
    } catch (err) {
      setRenameError(err instanceof ApiError ? err.message : 'No se pudo renombrar')
    }
  }

  async function generarReporte(tipo: 'mensual' | 'semanal') {
    setGenerandoReporte(tipo)
    setReporteError(null)
    try {
      const path = tipo === 'mensual' ? 'reporte-mensual' : 'reporte-semanal'
      await downloadFile(`/cm/clientes/${clienteId}/${path}`, `reporte-${tipo}-${cliente?.nombre}.pdf`)
    } catch (err) {
      setReporteError(err instanceof ApiError ? err.message : 'No se pudo generar el reporte')
    } finally {
      setGenerandoReporte(null)
    }
  }

  if (!cliente) return <p style={{ color: 'var(--ink-500)' }}>Cargando…</p>

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
        <div style={{ flex: 1 }}>
          {renaming ? (
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input type="text" value={nombreDraft} onChange={(e) => setNombreDraft(e.target.value)} autoFocus style={{ maxWidth: 280 }} />
              <button className="btn btn-primary btn-sm" onClick={guardarNombre}>Guardar</button>
              <button className="btn btn-ghost btn-sm" onClick={() => { setRenaming(false); setNombreDraft(cliente.nombre) }}>Cancelar</button>
            </div>
          ) : (
            <h1 style={{ fontSize: 22, margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
              {cliente.nombre}
              <button className="btn btn-ghost btn-sm" onClick={() => setRenaming(true)} title="Renombrar">✏️</button>
            </h1>
          )}
          {renameError && <p className="error-text">{renameError}</p>}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary btn-sm" onClick={() => generarReporte('semanal')} disabled={generandoReporte !== null}>
            {generandoReporte === 'semanal' ? <span className="spinner" style={{ borderTopColor: 'var(--inn-purple-600)', borderColor: 'var(--inn-purple-100)' }} /> : 'Reporte semanal'}
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => generarReporte('mensual')} disabled={generandoReporte !== null}>
            {generandoReporte === 'mensual' ? <span className="spinner" /> : 'Generar reporte'}
          </button>
          <button className="btn btn-danger btn-sm" onClick={() => setShowDelete(true)}>Eliminar cliente</button>
        </div>
      </div>
      {reporteError && <p className="error-text">{reporteError}</p>}

      {cliente.campanas.length > 1 && (
        <div className="field" style={{ maxWidth: 320, marginTop: 14 }}>
          <label>Campaña</label>
          <select value={campanaId ?? ''} onChange={(e) => setCampanaId(Number(e.target.value))}>
            {cliente.campanas.map((c) => (
              <option key={c.id} value={c.id}>{c.nombre} {c.estado === 'vencida' ? '(vencida)' : ''}</option>
            ))}
          </select>
        </div>
      )}

      {campana && (
        <div className="card" style={{ padding: '14px 18px', margin: '16px 0', display: 'flex', gap: 28, flexWrap: 'wrap', fontSize: 13 }}>
          <div><div style={{ color: 'var(--ink-500)' }}>Tipo</div><strong>{TIPO_LABEL[campana.tipo]}</strong></div>
          <div><div style={{ color: 'var(--ink-500)' }}>Paquete</div><strong>{campana.paquete || '—'}</strong></div>
          <div><div style={{ color: 'var(--ink-500)' }}>Presupuesto</div><strong>${campana.presupuesto.toLocaleString('es-MX')} / {campana.presupuesto_esquema}</strong></div>
          <div><div style={{ color: 'var(--ink-500)' }}>Lugar</div><strong>{campana.lugar || '—'}</strong></div>
          <div><div style={{ color: 'var(--ink-500)' }}>Inicio</div><strong>{formatFecha(campana.fecha_inicio)}</strong></div>
          <div><div style={{ color: 'var(--ink-500)' }}>Renovación</div><strong>{formatFecha(campana.fecha_renovacion)}</strong></div>
          <div><div style={{ color: 'var(--ink-500)' }}>Estado</div>
            <span className={`badge ${campana.estado === 'activa' ? 'badge-good' : campana.estado === 'vencida' ? 'badge-bad' : 'badge-neutral'}`}>
              {campana.estado}
            </span>
          </div>
        </div>
      )}

      {campana?.estado === 'vencida' ? (
        <div className="card" style={{ padding: 22, borderColor: 'var(--bad)', background: 'var(--bad-bg)' }}>
          <h3 style={{ margin: '0 0 6px', color: 'var(--bad)' }}>Esta campaña venció</h3>
          <p style={{ margin: '0 0 16px', color: 'var(--ink-700)' }}>
            Llegó la fecha de renovación. El mes se archivó y esta campaña queda bloqueada hasta que confirmes qué pasó.
          </p>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-primary" onClick={() => setShowRenovar(true)}>El cliente renovó</button>
            <button className="btn btn-secondary" onClick={() => setShowNoRenovar(true)}>No renovó</button>
          </div>
        </div>
      ) : (
        <>
          <div className="cm-tabs">
            <button className={`cm-tab ${tab === 'semanales' ? 'active' : ''}`} onClick={() => setTab('semanales')}>Datos semanales</button>
            <button className={`cm-tab ${tab === 'observaciones' ? 'active' : ''}`} onClick={() => setTab('observaciones')}>Observaciones</button>
            <button className={`cm-tab ${tab === 'cuenta' ? 'active' : ''}`} onClick={() => setTab('cuenta')}>Datos de la cuenta</button>
          </div>

          {campanaId && tab === 'semanales' && <DatosSemanalesTab campanaId={campanaId} />}
          {campanaId && tab === 'observaciones' && <ObservacionesTab campanaId={campanaId} />}
          {tab === 'cuenta' && <DatosCuentaTab clienteId={clienteId} />}
        </>
      )}

      {showDelete && (
        <DeleteClientDialog
          clienteId={clienteId}
          clienteNombre={cliente.nombre}
          onClose={() => setShowDelete(false)}
          onDeleted={onClienteDeleted}
        />
      )}
      {showRenovar && campanaId && (
        <RenovarDialog campanaId={campanaId} onClose={() => setShowRenovar(false)}
                       onRenovada={async () => { await recargarCampana(); onClienteChanged() }} />
      )}
      {showNoRenovar && (
        <NoRenovarDialog clienteId={clienteId} clienteNombre={cliente.nombre}
                          onClose={() => setShowNoRenovar(false)} onResuelto={onClienteDeleted} />
      )}
    </div>
  )
}
