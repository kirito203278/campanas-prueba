import { useState } from 'react'
import { api, ApiError } from '../../api/client'
import type { CreatedCredentials } from '../../api/types'

export default function AltaUsuarioModal({
  rol, onClose, onCreado,
}: {
  rol: 'cm' | 'admin'
  onClose: () => void
  onCreado: (creds: CreatedCredentials) => void
}) {
  const [nombre, setNombre] = useState('')
  const [apellido, setApellido] = useState('')
  const [soloLectura, setSoloLectura] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function guardar() {
    if (!nombre.trim()) { setError('El nombre es obligatorio'); return }
    setLoading(true)
    setError(null)
    try {
      const path = rol === 'cm' ? '/admin/cms' : '/admin/admins'
      const body: Record<string, unknown> = { nombre: nombre.trim(), apellido: apellido.trim() || null }
      if (rol === 'admin') body.solo_lectura = soloLectura
      const creds = await api.post<CreatedCredentials>(path, body)
      onCreado(creds)
      onClose()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo crear la cuenta')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-backdrop">
      <div className="modal" style={{ maxWidth: 420 }}>
        <h2 style={{ marginTop: 0, fontSize: 18 }}>
          {rol === 'cm' ? 'Agregar Community Manager' : 'Agregar administrador'}
        </h2>

        <div className="field">
          <label>Nombre</label>
          <input type="text" value={nombre} onChange={(e) => setNombre(e.target.value)} autoFocus />
        </div>
        <div className="field">
          <label>Apellido (opcional)</label>
          <input type="text" value={apellido} onChange={(e) => setApellido(e.target.value)} />
        </div>

        {rol === 'admin' && (
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 400, marginBottom: 16 }}>
            <input type="checkbox" style={{ width: 'auto' }} checked={soloLectura} onChange={(e) => setSoloLectura(e.target.checked)} />
            Solo lectura (ve todo, no puede editar nada)
          </label>
        )}

        {error && <p className="error-text">{error}</p>}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
          <button className="btn btn-ghost" onClick={onClose}>Cancelar</button>
          <button className="btn btn-primary" onClick={guardar} disabled={loading}>
            {loading ? <span className="spinner" /> : 'Crear cuenta'}
          </button>
        </div>
      </div>
    </div>
  )
}
