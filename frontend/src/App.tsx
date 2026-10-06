import { useAuth } from './auth/AuthContext'
import LoginPage from './pages/LoginPage'
import CmPanelPage from './pages/cm/CmPanelPage'
import AdminPanelPage from './pages/admin/AdminPanelPage'

export default function App() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center' }}>
        <div className="spinner" style={{ borderTopColor: 'var(--inn-purple-600)', borderColor: 'var(--inn-purple-100)' }} />
      </div>
    )
  }

  if (!user) return <LoginPage />
  if (user.rol === 'cm') return <CmPanelPage />
  return <AdminPanelPage />
}
