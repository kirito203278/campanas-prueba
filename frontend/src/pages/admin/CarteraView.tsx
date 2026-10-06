import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { ClienteAdminItem } from '../../api/types'
import ClienteAdminDetail from './ClienteAdminDetail'

export default function CarteraView({ cmId }: { cmId: number }) {
  const [clientes, setClientes] = useState<ClienteAdminItem[] | null>(null)
  const [clienteId, setClienteId] = useState<number | null>(null)

  useEffect(() => {
    setClientes(null)
    api.get<ClienteAdminItem[]>(`/admin/cms/${cmId}/clientes`).then((list) => {
      setClientes(list)
      setClienteId(list[0]?.id ?? null)
    })
  }, [cmId])

  if (clientes === null) return <p style={{ color: 'var(--ink-500)' }}>Cargando…</p>

  if (clientes.length === 0) {
    return <p style={{ color: 'var(--ink-500)' }}>Este CM todavía no tiene clientes.</p>
  }

  return (
    <div>
      <div className="field" style={{ maxWidth: 320, marginBottom: 20 }}>
        <label>Cliente</label>
        <select value={clienteId ?? ''} onChange={(e) => setClienteId(Number(e.target.value))}>
          {clientes.map((c) => (
            <option key={c.id} value={c.id}>{c.nombre} ({c.total_campanas} campaña{c.total_campanas !== 1 ? 's' : ''})</option>
          ))}
        </select>
      </div>

      {clienteId && <ClienteAdminDetail clienteId={clienteId} />}
    </div>
  )
}
