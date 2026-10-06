import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { CMConCartera } from '../../api/types'
import AdminSidebar, { type AdminView } from './AdminSidebar'
import CarteraView from './CarteraView'
import EquipoView from './EquipoView'

export default function AdminPanelPage() {
  const [view, setView] = useState<AdminView>('cartera')
  const [cms, setCms] = useState<CMConCartera[]>([])
  const [selectedCmId, setSelectedCmId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<CMConCartera[]>('/admin/cms/cartera').then((list) => {
      const activos = list.filter((c) => c.activo)
      setCms(activos)
      setSelectedCmId(activos[0]?.id ?? null)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center' }}>
        <div className="spinner" style={{ borderTopColor: 'var(--inn-purple-600)', borderColor: 'var(--inn-purple-100)' }} />
      </div>
    )
  }

  return (
    <div className="cm-layout">
      <AdminSidebar cms={cms} selectedCmId={selectedCmId} onSelectCm={setSelectedCmId} view={view} onChangeView={setView} />
      <main className="cm-main">
        {view === 'equipo' ? (
          <EquipoView />
        ) : cms.length === 0 ? (
          <p style={{ color: 'var(--ink-500)' }}>Todavía no hay ningún CM activo.</p>
        ) : selectedCmId ? (
          <CarteraView cmId={selectedCmId} />
        ) : (
          <p style={{ color: 'var(--ink-500)' }}>Selecciona un CM de la lista.</p>
        )}
      </main>
    </div>
  )
}
