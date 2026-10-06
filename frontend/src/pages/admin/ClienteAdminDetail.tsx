import { useEffect, useState } from 'react'
import { api, ApiError, downloadFile } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import type {
  CampanaDetalle, ClienteAdminDetalle, MensualConsolidado, MensualOut,
  SemanaConsolidada, SemanaOut,
} from '../../api/types'
import BarChart, { statusColor } from '../../components/charts/BarChart'
import LineChart from '../../components/charts/LineChart'

const TIPO_LABEL: Record<string, string> = { local: 'Local', nacional: 'Nacional', otro: 'Otro' }
const MESES_CORTO = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

function formatFecha(iso: string) {
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}
function fechaCorta(iso: string) {
  // Incluye el día para no confundir dos periodos que caen en el mismo mes
  // (p. ej. dos ciclos que cerraron ambos en junio).
  const [, m, d] = iso.split('-')
  return `${parseInt(d, 10)} ${MESES_CORTO[parseInt(m, 10) - 1]}`
}
function semaforoBadge(n: string | null) {
  if (n === 'bueno') return <span className="badge badge-good">Bueno</span>
  if (n === 'regular') return <span className="badge badge-warn">Regular</span>
  if (n === 'bajo') return <span className="badge badge-bad">Bajo</span>
  return <span className="badge badge-neutral">Sin datos</span>
}

function esSemanaIndividual(s: SemanaOut | SemanaConsolidada): s is SemanaOut {
  return 'id' in s
}

function formatHora(iso: string) {
  return new Date(iso).toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' })
}

export default function ClienteAdminDetail({ clienteId }: { clienteId: number }) {
  const { user } = useAuth()
  const puedeEscribir = !user?.solo_lectura
  const [cliente, setCliente] = useState<ClienteAdminDetalle | null>(null)
  const [seleccion, setSeleccion] = useState<number | 'todas'>('todas')
  const [campana, setCampana] = useState<CampanaDetalle | null>(null)
  const [semanas, setSemanas] = useState<(SemanaOut | SemanaConsolidada)[]>([])
  const [mensuales, setMensuales] = useState<(MensualOut | MensualConsolidado)[]>([])
  const [loading, setLoading] = useState(true)
  const [generandoReporte, setGenerandoReporte] = useState<'mensual' | 'semanal' | null>(null)
  const [reporteError, setReporteError] = useState<string | null>(null)
  const [habilitandoId, setHabilitandoId] = useState<number | null>(null)
  const [habilitarError, setHabilitarError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    api.get<ClienteAdminDetalle>(`/admin/clientes/${clienteId}`).then((c) => {
      setCliente(c)
      setSeleccion(c.campanas.length === 1 ? c.campanas[0].id : 'todas')
      setLoading(false)
    })
  }, [clienteId])

  useEffect(() => {
    if (!cliente) return
    if (seleccion === 'todas') {
      setCampana(null)
      Promise.all([
        api.get<SemanaConsolidada[]>(`/admin/clientes/${clienteId}/semanas-consolidadas`),
        api.get<MensualConsolidado[]>(`/admin/clientes/${clienteId}/mensuales-consolidados`),
      ]).then(([s, m]) => { setSemanas(s); setMensuales(m) })
    } else {
      Promise.all([
        api.get<CampanaDetalle>(`/admin/campanas/${seleccion}`),
        api.get<SemanaOut[]>(`/admin/campanas/${seleccion}/semanas`),
        api.get<MensualOut[]>(`/admin/campanas/${seleccion}/mensuales`),
      ]).then(([c, s, m]) => { setCampana(c); setSemanas(s); setMensuales(m) })
    }
  }, [seleccion, cliente, clienteId])

  async function habilitarEdicion(semanaId: number) {
    setHabilitandoId(semanaId)
    setHabilitarError(null)
    try {
      await api.post<SemanaOut>(`/admin/semanas/${semanaId}/habilitar-edicion`)
      if (seleccion !== 'todas') {
        const s = await api.get<SemanaOut[]>(`/admin/campanas/${seleccion}/semanas`)
        setSemanas(s)
      }
    } catch (err) {
      setHabilitarError(err instanceof ApiError ? err.message : 'No se pudo habilitar la edición')
    } finally {
      setHabilitandoId(null)
    }
  }

  async function generarReporte(tipo: 'mensual' | 'semanal') {
    if (!cliente) return
    setGenerandoReporte(tipo)
    setReporteError(null)
    try {
      const path = tipo === 'mensual' ? 'reporte-mensual' : 'reporte-semanal'
      await downloadFile(`/admin/clientes/${cliente.id}/${path}`, `reporte-${tipo}-${cliente.nombre}.pdf`)
    } catch (err) {
      setReporteError(err instanceof ApiError ? err.message : 'No se pudo generar el reporte')
    } finally {
      setGenerandoReporte(null)
    }
  }

  if (loading || !cliente) return <p style={{ color: 'var(--ink-500)' }}>Cargando…</p>

  const monthlyBars = [...mensuales].reverse().map((m) => ({
    label: fechaCorta(m.periodo_inicio),
    value: m.mensajes_total,
    color: statusColor(m.rendimiento),
    tooltip: `${m.mensajes_total} mensajes · $${m.costo_por_mensaje.toFixed(2)}/mensaje`,
  }))

  const weeklyMensajes = semanas.map((s, i) => ({
    label: `S${i + 1}`,
    value: s.mensajes ?? 0,
    tooltip: formatFecha(s.inicio),
  }))
  const weeklyCosto = semanas
    .filter((s) => s.costo_por_resultado != null)
    .map((s, i) => ({ label: `S${i + 1}`, value: Number(s.costo_por_resultado), tooltip: formatFecha(s.inicio) }))

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
        <h1 style={{ fontSize: 22, margin: 0 }}>{cliente.nombre}</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <span style={{ fontSize: 13, color: 'var(--ink-500)' }}>CM: {cliente.cm_nombre}</span>
          <button className="btn btn-secondary btn-sm" onClick={() => generarReporte('semanal')} disabled={generandoReporte !== null}>
            {generandoReporte === 'semanal' ? <span className="spinner" style={{ borderTopColor: 'var(--inn-purple-600)', borderColor: 'var(--inn-purple-100)' }} /> : 'Reporte semanal'}
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => generarReporte('mensual')} disabled={generandoReporte !== null}>
            {generandoReporte === 'mensual' ? <span className="spinner" /> : 'Generar reporte'}
          </button>
        </div>
      </div>
      {reporteError && <p className="error-text">{reporteError}</p>}

      <div className="table-scroll" style={{ margin: '16px 0' }}>
        <table className="data-table">
          <thead>
            <tr><th>Campaña</th><th>Tipo</th><th>Estado</th><th>Costo actual</th><th>Semáforo</th></tr>
          </thead>
          <tbody>
            {cliente.campanas.map((c) => (
              <tr key={c.id}>
                <td>{c.nombre}</td>
                <td>{TIPO_LABEL[c.tipo]}</td>
                <td>
                  <span className={`badge ${c.estado === 'activa' ? 'badge-good' : c.estado === 'vencida' ? 'badge-bad' : 'badge-neutral'}`}>
                    {c.estado}
                  </span>
                </td>
                <td>{c.costo_actual != null ? `$${c.costo_actual.toFixed(2)}` : '—'}</td>
                <td>{semaforoBadge(c.semaforo)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {cliente.campanas.length > 1 && (
        <div className="field" style={{ maxWidth: 280 }}>
          <label>Ver</label>
          <select value={seleccion} onChange={(e) => setSeleccion(e.target.value === 'todas' ? 'todas' : Number(e.target.value))}>
            <option value="todas">Todas (consolidado)</option>
            {cliente.campanas.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
          </select>
        </div>
      )}

      {campana && (
        <div className="card" style={{ padding: '14px 18px', margin: '16px 0', display: 'flex', gap: 28, flexWrap: 'wrap', fontSize: 13 }}>
          <div><div style={{ color: 'var(--ink-500)' }}>Paquete</div><strong>{campana.paquete || '—'}</strong></div>
          <div><div style={{ color: 'var(--ink-500)' }}>Presupuesto</div><strong>${campana.presupuesto.toLocaleString('es-MX')} / {campana.presupuesto_esquema}</strong></div>
          <div><div style={{ color: 'var(--ink-500)' }}>Lugar</div><strong>{campana.lugar || '—'}</strong></div>
          <div><div style={{ color: 'var(--ink-500)' }}>Inicio</div><strong>{formatFecha(campana.fecha_inicio)}</strong></div>
          <div><div style={{ color: 'var(--ink-500)' }}>Renovación</div><strong>{formatFecha(campana.fecha_renovacion)}</strong></div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, margin: '20px 0' }}>
        <div className="card" style={{ padding: 16 }}>
          <h3 style={{ margin: '0 0 10px', fontSize: 13, color: 'var(--ink-700)' }}>Rendimiento mensual (hasta 3 meses)</h3>
          <BarChart data={monthlyBars} valueFormat={(v) => `${v} mensajes`} />
        </div>
        <div className="card" style={{ padding: 16 }}>
          <h3 style={{ margin: '0 0 10px', fontSize: 13, color: 'var(--ink-700)' }}>Mensajes por semana (ciclo actual)</h3>
          <BarChart data={weeklyMensajes.map((w) => ({ ...w, color: 'var(--inn-purple-500)' }))} valueFormat={(v) => `${v} mensajes`} />
        </div>
        <div className="card" style={{ padding: 16, gridColumn: '1 / -1' }}>
          <h3 style={{ margin: '0 0 10px', fontSize: 13, color: 'var(--ink-700)' }}>Costo por resultado por semana</h3>
          <LineChart data={weeklyCosto} valueFormat={(v) => `$${v.toFixed(2)}`} />
        </div>
      </div>

      {habilitarError && <p className="error-text">{habilitarError}</p>}
      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr><th>Semana</th><th>Mensajes</th><th>Costo por resultado</th><th>Importe gastado</th><th>Acciones</th></tr>
          </thead>
          <tbody>
            {semanas.map((s, i) => (
              <tr key={i}>
                <td>{formatFecha(s.inicio)} – {formatFecha(s.fin)}</td>
                <td>{s.mensajes ?? '—'}</td>
                <td>{s.costo_por_resultado != null ? `$${s.costo_por_resultado.toFixed(2)}` : '—'}</td>
                <td>{s.importe_gastado != null ? `$${s.importe_gastado.toFixed(2)}` : '—'}</td>
                <td>
                  {esSemanaIndividual(s) && !s.editable && puedeEscribir && (
                    s.edicion_habilitada_hasta && new Date(s.edicion_habilitada_hasta) > new Date() ? (
                      <span className="badge badge-warn">Habilitada hasta {formatHora(s.edicion_habilitada_hasta)}</span>
                    ) : (
                      <button className="btn btn-ghost btn-sm" onClick={() => habilitarEdicion(s.id)} disabled={habilitandoId === s.id}>
                        {habilitandoId === s.id ? <span className="spinner" /> : 'Habilitar edición 2h'}
                      </button>
                    )
                  )}
                </td>
              </tr>
            ))}
            {semanas.length === 0 && (
              <tr><td colSpan={5} style={{ color: 'var(--ink-500)' }}>Sin semanas capturadas todavía.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
