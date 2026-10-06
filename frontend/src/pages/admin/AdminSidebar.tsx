import type { CMConCartera } from '../../api/types'
import { useAuth } from '../../auth/AuthContext'
import Logo from '../../components/Logo'

export type AdminView = 'cartera' | 'equipo'

export default function AdminSidebar({
  cms, selectedCmId, onSelectCm, view, onChangeView,
}: {
  cms: CMConCartera[]
  selectedCmId: number | null
  onSelectCm: (id: number) => void
  view: AdminView
  onChangeView: (v: AdminView) => void
}) {
  const { user, logout } = useAuth()

  return (
    <aside className="cm-sidebar">
      <div className="cm-sidebar-header">
        <div style={{ flexShrink: 0 }}><Logo size={34} /></div>
        <div style={{ overflow: 'hidden', flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: 14, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {user?.nombre}
          </div>
          <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.55)' }}>
            Panel admin {user?.solo_lectura ? '· solo lectura' : ''}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 4, marginBottom: 14, background: 'rgba(255,255,255,0.08)', borderRadius: 8, padding: 3 }}>
        <button
          onClick={() => onChangeView('cartera')}
          style={{
            flex: 1, border: 'none', borderRadius: 6, padding: '7px 0', fontSize: 13, fontWeight: 600, cursor: 'pointer',
            background: view === 'cartera' ? 'var(--inn-purple-600)' : 'transparent',
            color: view === 'cartera' ? 'white' : 'rgba(255,255,255,0.7)',
          }}
        >Cartera</button>
        <button
          onClick={() => onChangeView('equipo')}
          style={{
            flex: 1, border: 'none', borderRadius: 6, padding: '7px 0', fontSize: 13, fontWeight: 600, cursor: 'pointer',
            background: view === 'equipo' ? 'var(--inn-purple-600)' : 'transparent',
            color: view === 'equipo' ? 'white' : 'rgba(255,255,255,0.7)',
          }}
        >Equipo</button>
      </div>

      {view === 'cartera' && (
        <div className="cm-sidebar-list">
          {cms.map((cm) => (
            <button
              key={cm.id}
              className={`cm-sidebar-item ${cm.id === selectedCmId ? 'active' : ''}`}
              onClick={() => onSelectCm(cm.id)}
            >
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{cm.nombre}</span>
              <span className="badge badge-neutral" style={{ flexShrink: 0 }}>{cm.total_clientes}</span>
            </button>
          ))}
        </div>
      )}

      <div style={{ flex: view === 'cartera' ? undefined : 1 }} />
      <button className="btn btn-ghost-dark" style={{ marginTop: 10 }} onClick={logout}>
        Cerrar sesión
      </button>
    </aside>
  )
}
