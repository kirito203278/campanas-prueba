import { useState } from 'react'

export default function CredentialsRevealModal({
  nombre, username, password, onClose,
}: {
  nombre: string
  username: string
  password: string
  onClose: () => void
}) {
  const [copied, setCopied] = useState(false)

  async function copiar() {
    await navigator.clipboard.writeText(`Usuario: ${username}\nContraseña: ${password}`)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="modal-backdrop">
      <div className="modal" style={{ maxWidth: 420 }}>
        <h2 style={{ marginTop: 0, fontSize: 18 }}>Credenciales de {nombre}</h2>
        <p style={{ color: 'var(--warn)', fontSize: 13, fontWeight: 600, margin: '0 0 16px' }}>
          Esta contraseña se muestra una sola vez. Entrégala ahora por un canal seguro (WhatsApp) — el sistema no volverá a mostrarla.
        </p>

        <div className="card" style={{ padding: 16, marginBottom: 16, background: 'var(--inn-purple-50)' }}>
          <div style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 12, color: 'var(--ink-500)' }}>Usuario</div>
            <div style={{ fontFamily: 'monospace', fontSize: 15 }}>{username}</div>
          </div>
          <div>
            <div style={{ fontSize: 12, color: 'var(--ink-500)' }}>Contraseña</div>
            <div style={{ fontFamily: 'monospace', fontSize: 15 }}>{password}</div>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
          <button className="btn btn-secondary" onClick={copiar}>{copied ? '✓ Copiado' : 'Copiar'}</button>
          <button className="btn btn-primary" onClick={onClose}>Listo</button>
        </div>
      </div>
    </div>
  )
}
