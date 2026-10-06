import { useState, type FormEvent } from 'react'
import { useAuth } from '../auth/AuthContext'
import { ApiError } from '../api/client'
import Logo from '../components/Logo'

export default function LoginPage() {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(username, password)
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
      else setError('No se pudo iniciar sesión')
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
    }}>
      <form onSubmit={onSubmit} className="card" style={{ width: 380, padding: 36 }}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ margin: '0 auto 14px', width: 60, filter: 'drop-shadow(var(--shadow-md))' }}>
            <Logo size={60} />
          </div>
          <h1 style={{ fontSize: 20, margin: '0 0 4px', color: 'var(--ink-900)' }}>INNquietus</h1>
          <p style={{ margin: 0, color: 'var(--ink-500)', fontSize: 13 }}>Sistema de gestión de campañas</p>
        </div>

        <div className="field">
          <label htmlFor="username">Usuario</label>
          <input id="username" type="text" autoFocus value={username}
                 onChange={(e) => setUsername(e.target.value)} required />
        </div>
        <div className="field">
          <label htmlFor="password">Contraseña</label>
          <input id="password" type="password" value={password}
                 onChange={(e) => setPassword(e.target.value)} required />
        </div>

        {error && <p className="error-text" style={{ marginBottom: 14 }}>{error}</p>}

        <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} disabled={loading}>
          {loading ? <span className="spinner" /> : 'Entrar'}
        </button>
      </form>
    </div>
  )
}
