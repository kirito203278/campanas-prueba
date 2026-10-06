import { useEffect, useState } from 'react'
import { api } from '../../../api/client'
import type { ObservacionOut } from '../../../api/types'

function formatFechaHora(iso: string) {
  const d = new Date(iso)
  return d.toLocaleString('es-MX', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export default function ObservacionesTab({ campanaId }: { campanaId: number }) {
  const [observaciones, setObservaciones] = useState<ObservacionOut[]>([])
  const [texto, setTexto] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)

  async function load() {
    setLoading(true)
    const obs = await api.get<ObservacionOut[]>(`/cm/campanas/${campanaId}/observaciones`)
    setObservaciones(obs)
    setLoading(false)
  }

  useEffect(() => { load() }, [campanaId]) // eslint-disable-line react-hooks/exhaustive-deps

  async function enviar() {
    if (!texto.trim()) return
    setSending(true)
    try {
      const nueva = await api.post<ObservacionOut>(`/cm/campanas/${campanaId}/observaciones`, { texto })
      setObservaciones((o) => [nueva, ...o])
      setTexto('')
    } finally {
      setSending(false)
    }
  }

  if (loading) return <p style={{ color: 'var(--ink-500)' }}>Cargando…</p>

  return (
    <div className="cm-main-wave-target">
      <div className="field" style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
        <textarea rows={2} placeholder="Ej. Se desactivó un anuncio de bajo rendimiento…" value={texto}
                  onChange={(e) => setTexto(e.target.value)} style={{ flex: 1 }} />
        <button className="btn btn-primary" onClick={enviar} disabled={sending || !texto.trim()}>
          {sending ? <span className="spinner" /> : 'Agregar'}
        </button>
      </div>

      {observaciones.length === 0 ? (
        <p style={{ color: 'var(--ink-500)', fontSize: 13 }}>Sin observaciones todavía.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 8 }}>
          {observaciones.map((o) => (
            <div key={o.id} className="card" style={{ padding: '12px 16px' }}>
              <p style={{ margin: '0 0 6px' }}>{o.texto}</p>
              <span style={{ fontSize: 12, color: 'var(--ink-500)' }}>{formatFechaHora(o.creado_en)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
