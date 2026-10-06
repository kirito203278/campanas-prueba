import type { ClienteListItem } from '../../api/types'
import { useAuth } from '../../auth/AuthContext'
import Logo from '../../components/Logo'
import NotificationBell from '../../components/NotificationBell'

export default function Sidebar({
  clientes, selectedId, onSelect, onAdd, pulseAdd, onShowNoRenovados, showingNoRenovados,
}: {
  clientes: ClienteListItem[]
  selectedId: number | null
  onSelect: (id: number) => void
  onAdd: () => void
  pulseAdd: boolean
  onShowNoRenovados: () => void
  showingNoRenovados: boolean
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
          <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.55)' }}>Panel CM</div>
        </div>
        <NotificationBell />
      </div>

      <button className={`btn btn-primary ${pulseAdd ? 'pulse-attention' : ''}`} onClick={onAdd} style={{ marginBottom: 14, justifyContent: 'center' }}>
        + Agregar clientes
      </button>

      <div className="cm-sidebar-list">
        {clientes.map((c) => (
          <button
            key={c.id}
            className={`cm-sidebar-item ${!showingNoRenovados && c.id === selectedId ? 'active' : ''}`}
            onClick={() => onSelect(c.id)}
          >
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.nombre}</span>
            {c.campanas_vencidas > 0 && (
              <span className="badge badge-bad" style={{ flexShrink: 0 }}>vencida</span>
            )}
          </button>
        ))}
      </div>

      <button className={`cm-sidebar-item ${showingNoRenovados ? 'active' : ''}`} onClick={onShowNoRenovados} style={{ marginTop: 8 }}>
        No renovados
      </button>
      <button className="btn btn-ghost-dark" style={{ marginTop: 10 }} onClick={logout}>
        Cerrar sesión
      </button>
    </aside>
  )
}
