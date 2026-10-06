import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, getToken, setToken } from '../api/client'
import type { LoginResponse, Usuario } from '../api/types'

interface AuthContextValue {
  user: Usuario | null
  loading: boolean
  login: (username: string, password: string) => Promise<Usuario>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Usuario | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    if (!getToken()) {
      setUser(null)
      return
    }
    try {
      const me = await api.get<Usuario>('/auth/me')
      setUser(me)
    } catch {
      setToken(null)
      setUser(null)
    }
  }, [])

  useEffect(() => {
    refreshUser().finally(() => setLoading(false))
  }, [refreshUser])

  const login = useCallback(async (username: string, password: string) => {
    const resp = await api.post<LoginResponse>('/auth/login', { username, password })
    setToken(resp.access_token)
    setUser(resp.user)
    return resp.user
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider')
  return ctx
}
