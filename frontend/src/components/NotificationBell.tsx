import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'

interface NotificacionOut {
  id: number
  tipo: string
  mensaje: string
  leida: boolean
  creado_en: string
}

const POLL_MS = 45_000

export default function NotificationBell() {
  const [notificaciones, setNotificaciones] = useState<NotificacionOut[]>([])
  const [open, setOpen] = useState(false)
  const seenIds = useRef<Set<number>>(new Set())
  const permissionAsked = useRef(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [open])

  async function load() {
    const list = await api.get<NotificacionOut[]>('/notificaciones')
    setNotificaciones(list)

    if (!permissionAsked.current && 'Notification' in window && Notification.permission === 'default') {
      permissionAsked.current = true
      Notification.requestPermission()
    }

    for (const n of list) {
      if (!n.leida && !seenIds.current.has(n.id)) {
        seenIds.current.add(n.id)
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification('INNquietus', { body: n.mensaje, tag: `notif-${n.id}` })
        }
      }
    }
  }

  useEffect(() => {
    load()
    const interval = setInterval(load, POLL_MS)
    return () => clearInterval(interval)
  }, [])

  const noLeidas = notificaciones.filter((n) => !n.leida)

  async function marcarLeida(id: number) {
    await api.post(`/notificaciones/${id}/leer`)
    setNotificaciones((ns) => ns.map((n) => (n.id === id ? { ...n, leida: true } : n)))
  }

  async function marcarTodas() {
    await api.post('/notificaciones/leer-todas')
    setNotificaciones((ns) => ns.map((n) => ({ ...n, leida: true })))
  }

  return (
    <div style={{ position: 'relative' }} ref={containerRef}>
      <button className="btn btn-ghost btn-sm" style={{ color: 'rgba(255,255,255,0.85)', position: 'relative' }}
              onClick={() => setOpen((o) => !o)} title="Notificaciones">
        🔔
        {noLeidas.length > 0 && (
          <span style={{
            position: 'absolute', top: -2, right: -2, background: 'var(--inn-orange)', color: 'white',
            borderRadius: 999, fontSize: 10, fontWeight: 700, minWidth: 16, height: 16,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0 3px',
          }}>{noLeidas.length}</span>
        )}
      </button>

      {open && (
        <div className="card" style={{
          position: 'absolute', top: 32, left: 0, width: 320, maxHeight: 360, overflowY: 'auto',
          zIndex: 50, padding: 10, color: 'var(--ink-900)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <strong style={{ fontSize: 13 }}>Notificaciones</strong>
            {noLeidas.length > 0 && (
              <button className="btn btn-ghost btn-sm" onClick={marcarTodas}>Marcar todas leídas</button>
            )}
          </div>
          {notificaciones.length === 0 ? (
            <p style={{ fontSize: 13, color: 'var(--ink-500)', margin: 0 }}>Sin notificaciones.</p>
          ) : (
            notificaciones.map((n) => (
              <div key={n.id} onClick={() => !n.leida && marcarLeida(n.id)}
                   style={{
                     padding: '8px 10px', borderRadius: 8, fontSize: 13, marginBottom: 4, cursor: n.leida ? 'default' : 'pointer',
                     background: n.leida ? 'transparent' : 'var(--inn-purple-50)',
                   }}>
                {n.mensaje}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
