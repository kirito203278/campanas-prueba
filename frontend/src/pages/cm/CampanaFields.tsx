export interface CampanaFieldsValue {
  campanaNombre: string
  paquete: string
  tipo: 'local' | 'nacional' | 'otro'
  presupuesto: string
  formato_post: boolean
  formato_3d: boolean
  formato_boton: boolean
  formato_otro: boolean
  lugar: string
  fecha_inicio: string
  fecha_renovacion: string
}

// "Un mes" para efectos de la campaña son 30 días exactos, no el mes de
// calendario (que da 28-31 días según el mes de arranque).
export function addMonthIso(iso: string): string {
  const d = new Date(iso)
  d.setDate(d.getDate() + 30)
  return d.toISOString().slice(0, 10)
}

export function todayIso(): string {
  return new Date().toISOString().slice(0, 10)
}

export function newCampanaFieldsValue(): CampanaFieldsValue {
  const inicio = todayIso()
  return {
    campanaNombre: '', paquete: '', tipo: 'local', presupuesto: '',
    formato_post: true, formato_3d: false, formato_boton: false, formato_otro: false,
    lugar: '', fecha_inicio: inicio, fecha_renovacion: addMonthIso(inicio),
  }
}

export default function CampanaFields({
  value, onChange,
}: {
  value: CampanaFieldsValue
  onChange: (patch: Partial<CampanaFieldsValue>) => void
}) {
  return (
    <>
      <div className="field" style={{ gridColumn: '1 / -1' }}>
        <label>Nombre de la campaña</label>
        <input type="text" value={value.campanaNombre} onChange={(e) => onChange({ campanaNombre: e.target.value })} placeholder="LOCAL ADV - JUL 26" />
      </div>

      <div className="field">
        <label>Paquete</label>
        <input type="text" value={value.paquete} onChange={(e) => onChange({ paquete: e.target.value })} placeholder="Básico / Estándar / VIP" />
      </div>
      <div className="field">
        <label>Tipo</label>
        <select value={value.tipo} onChange={(e) => onChange({ tipo: e.target.value as CampanaFieldsValue['tipo'] })}>
          <option value="local">Local</option>
          <option value="nacional">Nacional</option>
          <option value="otro">Otro</option>
        </select>
      </div>

      <div className="field">
        <label>Presupuesto</label>
        <input type="number" min="0" step="0.01" value={value.presupuesto} onChange={(e) => onChange({ presupuesto: e.target.value })} />
      </div>

      <div className="field">
        <label>Fecha de inicio</label>
        <input type="date" value={value.fecha_inicio}
               onChange={(e) => onChange({ fecha_inicio: e.target.value, fecha_renovacion: addMonthIso(e.target.value) })} />
      </div>
      <div className="field">
        <label>Fecha de renovación</label>
        <input type="date" value={value.fecha_renovacion} onChange={(e) => onChange({ fecha_renovacion: e.target.value })} />
      </div>

      <div className="field" style={{ gridColumn: '1 / -1' }}>
        <label>Lugar</label>
        <input type="text" value={value.lugar} onChange={(e) => onChange({ lugar: e.target.value })} placeholder="Mazatlán, Culiacán" />
      </div>

      <div className="field" style={{ gridColumn: '1 / -1' }}>
        <label>Formato del anuncio</label>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          {([
            ['formato_post', 'Post'],
            ['formato_3d', '3D'],
            ['formato_boton', 'Botón'],
            ['formato_otro', 'Otro'],
          ] as const).map(([key, label]) => (
            <label key={key} style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 400, margin: 0 }}>
              <input type="checkbox" style={{ width: 'auto' }} checked={value[key]}
                     onChange={(e) => onChange({ [key]: e.target.checked } as Partial<CampanaFieldsValue>)} />
              {label}
            </label>
          ))}
        </div>
      </div>
    </>
  )
}
