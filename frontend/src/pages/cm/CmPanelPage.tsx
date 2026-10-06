import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { ClienteListItem, EstadoCM } from '../../api/types'
import WelcomeScreen from './WelcomeScreen'
import Sidebar from './Sidebar'
import EmptyStateMonkey from './EmptyStateMonkey'
import ClienteDetail from './ClienteDetail'
import AddClientesModal from './AddClientesModal'
import NoRenovadosView from './NoRenovadosView'

export default function CmPanelPage() {
  const [estado, setEstado] = useState<EstadoCM | null>(null)
  const [clientes, setClientes] = useState<ClienteListItem[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [showAddModal, setShowAddModal] = useState(false)
  const [pulseAdd, setPulseAdd] = useState(false)
  const [loading, setLoading] = useState(true)
  const [showingNoRenovados, setShowingNoRenovados] = useState(false)

  async function loadEstado() {
    const e = await api.get<EstadoCM>('/cm/estado')
    setEstado(e)
    return e
  }

  async function loadClientes() {
    const list = await api.get<ClienteListItem[]>('/cm/clientes')
    setClientes(list)
    setSelectedId((prev) => (prev && list.some((c) => c.id === prev) ? prev : list[0]?.id ?? null))
  }

  useEffect(() => {
    (async () => {
      const e = await loadEstado()
      if (!e.primer_ingreso) await loadClientes()
      setLoading(false)
    })()
  }, [])

  if (loading || !estado) {
    return (
      <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center' }}>
        <div className="spinner" style={{ borderTopColor: 'var(--inn-purple-600)', borderColor: 'var(--inn-purple-100)' }} />
      </div>
    )
  }

  if (estado.primer_ingreso) {
    return <WelcomeScreen onComenzar={async () => { await loadEstado(); await loadClientes() }} />
  }

  return (
    <div className="cm-layout">
      <Sidebar
        clientes={clientes}
        selectedId={selectedId}
        onSelect={(id) => { setShowingNoRenovados(false); setSelectedId(id) }}
        onAdd={() => setShowAddModal(true)}
        pulseAdd={pulseAdd}
        onShowNoRenovados={() => setShowingNoRenovados(true)}
        showingNoRenovados={showingNoRenovados}
      />
      <main className="cm-main">
        {showingNoRenovados ? (
          <NoRenovadosView />
        ) : clientes.length === 0 ? (
          <EmptyStateMonkey onAddClick={() => setShowAddModal(true)} onFullyAwake={() => setPulseAdd(true)} />
        ) : selectedId ? (
          <ClienteDetail
            clienteId={selectedId}
            onClienteChanged={loadClientes}
            onClienteDeleted={async () => { setSelectedId(null); await loadClientes() }}
          />
        ) : (
          <p style={{ color: 'var(--ink-500)' }}>Selecciona un cliente de la lista.</p>
        )}
      </main>

      {showAddModal && (
        <AddClientesModal
          onClose={() => setShowAddModal(false)}
          onCreated={() => { setPulseAdd(false); loadClientes() }}
        />
      )}
    </div>
  )
}
