import { useEffect, useState } from 'react'
import { api, ApiError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import type { CMConCartera, CreatedCredentials, UsuarioListItem } from '../../api/types'
import AltaUsuarioModal from './AltaUsuarioModal'
import CredentialsRevealModal from './CredentialsRevealModal'
import BajaCmDialog from './BajaCmDialog'

function formatFecha(iso: string) {
  return new Date(iso).toLocaleDateString('es-MX', { day: '2-digit', month: 'short', year: 'numeric' })
}

export default function EquipoView() {
  const { user } = useAuth()
  const puedeEscribir = !user?.solo_lectura

  const [cms, setCms] = useState<UsuarioListItem[]>([])
  const [admins, setAdmins] = useState<UsuarioListItem[]>([])
  const [cartera, setCartera] = useState<CMConCartera[]>([])
  const [loading, setLoading] = useState(true)

  const [altaModal, setAltaModal] = useState<'cm' | 'admin' | null>(null)
  const [credenciales, setCredenciales] = useState<CreatedCredentials | null>(null)
  const [bajaTarget, setBajaTarget] = useState<CMConCartera | null>(null)
  const [resetError, setResetError] = useState<string | null>(null)
  const [resettingId, setResettingId] = useState<number | null>(null)

  async function loadAll() {
    const [cmList, adminList, carteraList] = await Promise.all([
      api.get<UsuarioListItem[]>('/admin/cms'),
      api.get<UsuarioListItem[]>('/admin/admins'),
      api.get<CMConCartera[]>('/admin/cms/cartera'),
    ])
    setCms(cmList)
    setAdmins(adminList)
    setCartera(carteraList)
    setLoading(false)
  }

  useEffect(() => { loadAll() }, [])

  async function resetear(usuarioId: number, nombre: string) {
    setResettingId(usuarioId)
    setResetError(null)
    try {
      const resp = await api.post<{ id: number; username: string; password: string }>(`/admin/usuarios/${usuarioId}/reset-password`)
      setCredenciales({ id: resp.id, nombre, username: resp.username, password: resp.password, rol: '', solo_lectura: false })
    } catch (err) {
      setResetError(err instanceof ApiError ? err.message : 'No se pudo resetear')
    } finally {
      setResettingId(null)
    }
  }

  if (loading) return <p style={{ color: 'var(--ink-500)' }}>Cargando…</p>

  return (
    <div>
      <h1 style={{ fontSize: 22, margin: '0 0 20px' }}>Equipo</h1>

      <section style={{ marginBottom: 32 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <h2 style={{ fontSize: 15, margin: 0 }}>Community Managers</h2>
          {puedeEscribir && <button className="btn btn-primary btn-sm" onClick={() => setAltaModal('cm')}>+ Agregar CM</button>}
        </div>
        <div className="table-scroll">
          <table className="data-table">
            <thead><tr><th>Nombre</th><th>Usuario</th><th>Cartera</th><th>Estado</th><th>Alta</th><th></th></tr></thead>
            <tbody>
              {cms.map((c) => {
                const info = cartera.find((k) => k.id === c.id)
                return (
                  <tr key={c.id}>
                    <td>{c.nombre}</td>
                    <td style={{ fontFamily: 'monospace', fontSize: 13 }}>{c.username}</td>
                    <td>{info?.total_clientes ?? '—'}</td>
                    <td>
                      <span className={`badge ${c.activo ? 'badge-good' : 'badge-neutral'}`}>{c.activo ? 'Activo' : 'Baja'}</span>
                    </td>
                    <td style={{ fontSize: 13, color: 'var(--ink-500)' }}>{formatFecha(c.creado_en)}</td>
                    <td>
                      {puedeEscribir && c.activo && (
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button className="btn btn-secondary btn-sm" disabled={resettingId === c.id}
                                  onClick={() => resetear(c.id, c.nombre)}>
                            {resettingId === c.id ? <span className="spinner" style={{ borderTopColor: 'var(--inn-purple-600)', borderColor: 'var(--inn-purple-100)' }} /> : 'Resetear'}
                          </button>
                          <button className="btn btn-danger btn-sm"
                                  onClick={() => setBajaTarget(cartera.find((k) => k.id === c.id) ?? null)}>
                            Baja
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        {resetError && <p className="error-text">{resetError}</p>}
      </section>

      <section>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <h2 style={{ fontSize: 15, margin: 0 }}>Administradores</h2>
          {puedeEscribir && <button className="btn btn-primary btn-sm" onClick={() => setAltaModal('admin')}>+ Agregar admin</button>}
        </div>
        <div className="table-scroll">
          <table className="data-table">
            <thead><tr><th>Nombre</th><th>Usuario</th><th>Rol</th><th>Alta</th><th></th></tr></thead>
            <tbody>
              {admins.map((a) => (
                <tr key={a.id}>
                  <td>{a.nombre}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: 13 }}>{a.username}</td>
                  <td>
                    <span className={`badge ${a.solo_lectura ? 'badge-neutral' : 'badge-good'}`}>
                      {a.solo_lectura ? 'Solo lectura' : 'Completo'}
                    </span>
                  </td>
                  <td style={{ fontSize: 13, color: 'var(--ink-500)' }}>{formatFecha(a.creado_en)}</td>
                  <td>
                    {puedeEscribir && (
                      <button className="btn btn-secondary btn-sm" disabled={resettingId === a.id}
                              onClick={() => resetear(a.id, a.nombre)}>
                        {resettingId === a.id ? <span className="spinner" style={{ borderTopColor: 'var(--inn-purple-600)', borderColor: 'var(--inn-purple-100)' }} /> : 'Resetear'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {altaModal && (
        <AltaUsuarioModal rol={altaModal} onClose={() => setAltaModal(null)}
                           onCreado={(c) => { setCredenciales(c); loadAll() }} />
      )}
      {credenciales && (
        <CredentialsRevealModal nombre={credenciales.nombre} username={credenciales.username}
                                 password={credenciales.password} onClose={() => setCredenciales(null)} />
      )}
      {bajaTarget && (
        <BajaCmDialog
          cm={bajaTarget}
          otrosCms={cartera.filter((c) => c.id !== bajaTarget.id && c.activo)}
          onClose={() => setBajaTarget(null)}
          onMigrado={loadAll}
        />
      )}
    </div>
  )
}
