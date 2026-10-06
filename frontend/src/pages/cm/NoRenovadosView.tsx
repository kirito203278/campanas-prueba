import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { NoRenovadoItem } from '../../api/types'
import ReactivarClienteDialog from './ReactivarClienteDialog'

export default function NoRenovadosView() {
  const [items, setItems] = useState<NoRenovadoItem[] | null>(null)
  const [reactivando, setReactivando] = useState<NoRenovadoItem | null>(null)

  function recargar() {
    api.get<NoRenovadoItem[]>('/cm/no-renovados').then(setItems)
  }

  useEffect(() => {
    recargar()
  }, [])

  if (items === null) return <p style={{ color: 'var(--ink-500)' }}>Cargando…</p>

  return (
    <div>
      <h1 style={{ fontSize: 22, margin: '0 0 6px' }}>No renovados</h1>
      <p style={{ color: 'var(--ink-500)', margin: '0 0 20px' }}>
        Clientes que no renovaron y decidiste conservar. Si vuelve dentro de 2 meses, se conserva su historial;
        si pasa más tiempo, la próxima campaña empieza de cero. Si no vuelve en 1 año, se elimina automáticamente.
      </p>

      {items.length === 0 ? (
        <p style={{ color: 'var(--ink-500)' }}>No tienes clientes en este apartado.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {items.map((c) => (
            <div key={c.id} className="card" style={{ padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
              <div>
                <strong>{c.nombre}</strong>
                <div style={{ marginTop: 6, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {c.campanas.map((camp) => (
                    <span key={camp.id} className="badge badge-neutral">{camp.nombre}</span>
                  ))}
                </div>
              </div>
              <button className="btn btn-secondary btn-sm" onClick={() => setReactivando(c)}>Renovar</button>
            </div>
          ))}
        </div>
      )}

      {reactivando && (
        <ReactivarClienteDialog
          clienteId={reactivando.id}
          clienteNombre={reactivando.nombre}
          puedeContinuar={reactivando.puede_continuar}
          ultimaCampanaId={reactivando.ultima_campana?.id ?? null}
          ultimaCampanaNombre={reactivando.ultima_campana?.nombre ?? null}
          onClose={() => setReactivando(null)}
          onReactivado={recargar}
        />
      )}
    </div>
  )
}
