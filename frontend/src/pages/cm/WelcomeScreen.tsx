import { useState } from 'react'
import { api } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import type { EstadoCM } from '../../api/types'
import Logo from '../../components/Logo'

export default function WelcomeScreen({ onComenzar }: { onComenzar: () => void }) {
  const { user } = useAuth()
  const [loading, setLoading] = useState(false)

  async function handleComenzar() {
    setLoading(true)
    try {
      await api.post<EstadoCM>('/cm/comenzar')
      onComenzar()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(160deg, var(--inn-purple-900), var(--inn-purple-700) 55%, var(--inn-purple-500))',
      textAlign: 'center',
      padding: 24,
    }}>
      <div className="card" style={{ maxWidth: 460, padding: 44 }}>
        <div style={{ margin: '0 auto 14px', width: 64 }}><Logo size={64} /></div>
        <h1 style={{ fontSize: 22, margin: '0 0 8px' }}>¡Hola, {user?.nombre}!</h1>
        <p style={{ color: 'var(--ink-500)', margin: '0 0 28px', lineHeight: 1.5 }}>
          Este va a ser tu panel para llevar el control de tus clientes y campañas.
          En cuanto quieras, arrancamos.
        </p>
        <button className="btn btn-primary" onClick={handleComenzar} disabled={loading}
                style={{ padding: '12px 28px', fontSize: 15 }}>
          {loading ? <span className="spinner" /> : 'Comenzar'}
        </button>
      </div>
    </div>
  )
}
