import { useEffect, useState } from 'react'
import { api, ApiError } from '../../../api/client'
import type { MensualOut, SemanaOut } from '../../../api/types'

function rendimientoBadge(r: string | null) {
  if (r === 'bueno') return <span className="badge badge-good">Bueno</span>
  if (r === 'regular') return <span className="badge badge-warn">Regular</span>
  if (r === 'bajo') return <span className="badge badge-bad">Bajo</span>
  return <span className="badge badge-neutral">Sin calcular</span>
}

function formatFecha(iso: string) {
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

function nombreMes(iso: string) {
  const [, m] = iso.split('-')
  return MESES[parseInt(m, 10) - 1]
}

// Dos mensuales de la misma campaña pueden compartir el mes calendario de
// periodo_inicio (uno manual, otro archivado por el cierre de ciclo) sin ser
// el mismo periodo; por eso la etiqueta considera también periodo_fin en vez
// de mostrar siempre el mismo nombre de mes.
function etiquetaPeriodo(inicio: string, fin: string) {
  const [anioInicio, mesInicio] = inicio.split('-')
  const [anioFin, mesFin] = fin.split('-')
  if (anioInicio === anioFin && mesInicio === mesFin) return nombreMes(inicio)
  if (anioInicio === anioFin) return `${nombreMes(inicio)} – ${nombreMes(fin)}`
  return `${nombreMes(inicio)} ${anioInicio} – ${nombreMes(fin)} ${anioFin}`
}

type Draft = { mensajes: string; costo: string; importe: string }

// El admin puede habilitarle al CM la edición de una semana ya cerrada por
// 2 horas; mientras esté activa se muestra un cronómetro con el tiempo
// restante para que lo tenga en cuenta.
function puedeEditar(s: SemanaOut, now: Date) {
  return s.editable || (s.edicion_habilitada_hasta != null && new Date(s.edicion_habilitada_hasta) > now)
}

function tiempoRestante(hasta: string, now: Date) {
  const ms = new Date(hasta).getTime() - now.getTime()
  if (ms <= 0) return null
  const totalSeg = Math.floor(ms / 1000)
  const h = Math.floor(totalSeg / 3600)
  const m = Math.floor((totalSeg % 3600) / 60)
  const s = totalSeg % 60
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

export default function DatosSemanalesTab({ campanaId }: { campanaId: number }) {
  const [semanas, setSemanas] = useState<SemanaOut[]>([])
  const [mensuales, setMensuales] = useState<MensualOut[]>([])
  const [loading, setLoading] = useState(true)
  const [drafts, setDrafts] = useState<Record<number, Draft>>({})
  const [editingIds, setEditingIds] = useState<Set<number>>(new Set())
  const [savingId, setSavingId] = useState<number | null>(null)
  const [rowError, setRowError] = useState<Record<number, string>>({})
  const [showManual, setShowManual] = useState(false)
  const [manualForm, setManualForm] = useState({ periodo_inicio: '', periodo_fin: '', mensajes_total: '', gasto_total: '' })
  const [manualError, setManualError] = useState<string | null>(null)
  const [manualSaving, setManualSaving] = useState(false)
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const hayCronometro = semanas.some((s) => !s.editable && s.edicion_habilitada_hasta != null)
    if (!hayCronometro) return
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [semanas])

  async function load() {
    setLoading(true)
    const [s, m] = await Promise.all([
      api.get<SemanaOut[]>(`/cm/campanas/${campanaId}/semanas`),
      api.get<MensualOut[]>(`/cm/campanas/${campanaId}/mensuales`),
    ])
    setSemanas(s)
    setMensuales(m)
    setDrafts(Object.fromEntries(s.map((sem) => [sem.id, {
      mensajes: sem.mensajes?.toString() ?? '',
      costo: sem.costo_por_resultado?.toString() ?? '',
      importe: sem.importe_gastado?.toString() ?? '',
    }])))
    // Semanas en curso que nunca se han capturado arrancan en modo edición;
    // las que ya tienen datos guardados arrancan en modo vista (con botón Editar).
    setEditingIds(new Set(s.filter((sem) => sem.editable && sem.mensajes == null).map((sem) => sem.id)))
    setLoading(false)
  }

  useEffect(() => { load() }, [campanaId]) // eslint-disable-line react-hooks/exhaustive-deps

  function updateDraft(id: number, patch: Partial<Draft>) {
    setDrafts((d) => {
      const actual = d[id] ?? { mensajes: '', costo: '', importe: '' }
      const siguiente = { ...actual, ...patch }
      // Autocalcula el importe gastado = mensajes x costo por resultado;
      // el CM puede seguir ajustándolo a mano después si el dato real difiere.
      if ('mensajes' in patch || 'costo' in patch) {
        const mensajes = parseFloat(siguiente.mensajes)
        const costo = parseFloat(siguiente.costo)
        if (!isNaN(mensajes) && !isNaN(costo)) {
          siguiente.importe = (mensajes * costo).toFixed(2)
        }
      }
      return { ...d, [id]: siguiente }
    })
  }

  async function guardarSemana(id: number) {
    setSavingId(id)
    setRowError((e) => ({ ...e, [id]: '' }))
    try {
      const draft = drafts[id]
      const updated = await api.put<SemanaOut>(`/cm/semanas/${id}`, {
        mensajes: parseInt(draft.mensajes || '0', 10),
        costo_por_resultado: parseFloat(draft.costo || '0'),
        importe_gastado: parseFloat(draft.importe || '0'),
      })
      setSemanas((s) => s.map((sem) => (sem.id === id ? updated : sem)))
      setEditingIds((ids) => {
        const next = new Set(ids)
        next.delete(id)
        return next
      })
    } catch (err) {
      setRowError((e) => ({ ...e, [id]: err instanceof ApiError ? err.message : 'No se pudo guardar' }))
    } finally {
      setSavingId(null)
    }
  }

  function editarSemana(id: number) {
    setEditingIds((ids) => new Set(ids).add(id))
  }

  async function guardarManual() {
    setManualSaving(true)
    setManualError(null)
    try {
      await api.post(`/cm/campanas/${campanaId}/mensuales/manual`, {
        periodo_inicio: manualForm.periodo_inicio,
        periodo_fin: manualForm.periodo_fin,
        mensajes_total: parseInt(manualForm.mensajes_total || '0', 10),
        gasto_total: parseFloat(manualForm.gasto_total || '0'),
      })
      setShowManual(false)
      await load()
    } catch (err) {
      setManualError(err instanceof ApiError ? err.message : 'No se pudo guardar')
    } finally {
      setManualSaving(false)
    }
  }

  if (loading) return <p style={{ color: 'var(--ink-500)' }}>Cargando…</p>

  return (
    <div className="cm-main-wave-target">
      <div className="card" style={{ padding: 18, marginBottom: 22 }}>
        <h3 style={{ margin: '0 0 12px', fontSize: 14, color: 'var(--ink-700)' }}>
          Resultados de meses anteriores (máx. 2, para comparar)
        </h3>
        {mensuales.length === 0 ? (
          <div>
            <p style={{ color: 'var(--ink-500)', fontSize: 13, margin: '0 0 10px' }}>
              Todavía no hay ningún mensual archivado para esta campaña.
            </p>
            {!showManual ? (
              <button className="btn btn-secondary btn-sm" onClick={() => setShowManual(true)}>
                ¿Ya tienes datos del mes anterior a que entrara al sistema? Captúralos aquí
              </button>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, maxWidth: 520 }}>
                <div className="field">
                  <label>Periodo inicio</label>
                  <input type="date" value={manualForm.periodo_inicio}
                         onChange={(e) => setManualForm((f) => ({ ...f, periodo_inicio: e.target.value }))} />
                </div>
                <div className="field">
                  <label>Periodo fin</label>
                  <input type="date" value={manualForm.periodo_fin}
                         onChange={(e) => setManualForm((f) => ({ ...f, periodo_fin: e.target.value }))} />
                </div>
                <div className="field">
                  <label>Mensajes totales</label>
                  <input type="number" min="0" value={manualForm.mensajes_total}
                         onChange={(e) => setManualForm((f) => ({ ...f, mensajes_total: e.target.value }))} />
                </div>
                <div className="field">
                  <label>Gasto total</label>
                  <input type="number" min="0" step="0.01" value={manualForm.gasto_total}
                         onChange={(e) => setManualForm((f) => ({ ...f, gasto_total: e.target.value }))} />
                </div>
                {manualError && <p className="error-text" style={{ gridColumn: '1 / -1' }}>{manualError}</p>}
                <div style={{ gridColumn: '1 / -1', display: 'flex', gap: 8 }}>
                  <button className="btn btn-primary btn-sm" onClick={guardarManual} disabled={manualSaving}>
                    {manualSaving ? <span className="spinner" /> : 'Guardar mes anterior'}
                  </button>
                  <button className="btn btn-ghost btn-sm" onClick={() => setShowManual(false)}>Cancelar</button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Mes</th>
                  <th>Mensajes</th>
                  <th>Costo por mensaje</th>
                  <th>Gasto total</th>
                  <th>Presupuesto</th>
                  <th>Sobrante</th>
                  <th>Rendimiento</th>
                </tr>
              </thead>
              <tbody>
                {mensuales.map((m) => (
                  <tr key={m.id}>
                    <td>Resultados de {etiquetaPeriodo(m.periodo_inicio, m.periodo_fin)} <span style={{ color: 'var(--ink-500)' }}>({formatFecha(m.periodo_inicio)} – {formatFecha(m.periodo_fin)})</span></td>
                    <td>{m.mensajes_total}</td>
                    <td>${m.costo_por_mensaje.toFixed(2)}</td>
                    <td>${m.gasto_total.toLocaleString('es-MX', { minimumFractionDigits: 2 })}</td>
                    <td>${m.presupuesto.toLocaleString('es-MX', { minimumFractionDigits: 2 })}</td>
                    <td>{m.sobrante != null ? `$${m.sobrante.toLocaleString('es-MX', { minimumFractionDigits: 2 })}` : '—'}</td>
                    <td>{rendimientoBadge(m.rendimiento)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            <th>Semana</th>
            <th>Mensajes</th>
            <th>Costo por resultado</th>
            <th>Importe gastado</th>
            <th>Estado</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {semanas.map((s, idx) => {
            const draft = drafts[s.id] ?? { mensajes: '', costo: '', importe: '' }
            const habilitada = puedeEditar(s, now)
            const editando = habilitada && editingIds.has(s.id)
            const restante = !s.editable && s.edicion_habilitada_hasta ? tiempoRestante(s.edicion_habilitada_hasta, now) : null
            return (
              <tr key={s.id}>
                <td>
                  <strong>Semana {idx + 1}</strong>
                  <div style={{ color: 'var(--ink-500)', fontSize: 12 }}>{formatFecha(s.inicio)} – {formatFecha(s.fin)}</div>
                </td>
                <td style={{ width: 120 }}>
                  {editando ? (
                    <input type="number" min="0" value={draft.mensajes}
                           onChange={(e) => updateDraft(s.id, { mensajes: e.target.value })} />
                  ) : (s.mensajes ?? '—')}
                </td>
                <td style={{ width: 140 }}>
                  {editando ? (
                    <input type="number" min="0" step="0.01" value={draft.costo}
                           onChange={(e) => updateDraft(s.id, { costo: e.target.value })} />
                  ) : (s.costo_por_resultado != null ? `$${s.costo_por_resultado.toFixed(2)}` : '—')}
                </td>
                <td style={{ width: 140 }}>
                  {editando ? (
                    <input type="number" min="0" step="0.01" value={draft.importe}
                           onChange={(e) => updateDraft(s.id, { importe: e.target.value })} />
                  ) : (s.importe_gastado != null ? `$${s.importe_gastado.toFixed(2)}` : '—')}
                </td>
                <td>
                  {s.editable ? (
                    <span className="badge badge-good">{editando ? 'En curso' : 'Guardado'}</span>
                  ) : restante ? (
                    <span className="badge badge-warn">Edición habilitada · expira en {restante}</span>
                  ) : (
                    <span className="badge badge-neutral">Cerrada</span>
                  )}
                </td>
                <td>
                  {habilitada && (
                    <>
                      {editando ? (
                        <button className="btn btn-secondary btn-sm" onClick={() => guardarSemana(s.id)} disabled={savingId === s.id}>
                          {savingId === s.id ? <span className="spinner" style={{ borderTopColor: 'var(--inn-purple-600)', borderColor: 'var(--inn-purple-100)' }} /> : 'Guardar'}
                        </button>
                      ) : (
                        <button className="btn btn-ghost btn-sm" onClick={() => editarSemana(s.id)}>Editar</button>
                      )}
                      {rowError[s.id] && <div className="error-text">{rowError[s.id]}</div>}
                    </>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
      </div>
    </div>
  )
}
