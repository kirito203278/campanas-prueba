export interface Usuario {
  id: number
  nombre: string
  username: string
  rol: 'cm' | 'admin'
  solo_lectura: boolean
  activo: boolean
  primer_ingreso: boolean
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: Usuario
}

export interface EstadoCM {
  primer_ingreso: boolean
  total_clientes: number
}

export interface ClienteListItem {
  id: number
  nombre: string
  estado: string
  campanas_activas: number
  campanas_vencidas: number
}

export interface CampanaResumen {
  id: number
  nombre: string
  tipo: string
  estado: string
}

export interface ClienteDetalle {
  id: number
  nombre: string
  estado: string
  campanas: CampanaResumen[]
}

export interface CampanaDetalle {
  id: number
  cliente_id: number
  nombre: string
  paquete: string | null
  tipo: 'local' | 'nacional' | 'otro'
  presupuesto: number
  presupuesto_esquema: 'mensual' | 'semanal' | 'diario'
  formato_post: boolean
  formato_3d: boolean
  formato_boton: boolean
  formato_otro: boolean
  lugar: string | null
  fecha_inicio: string
  fecha_renovacion: string
  estado: 'activa' | 'vencida' | 'cerrada'
}

export interface SemanaOut {
  id: number
  inicio: string
  fin: string
  mensajes: number | null
  costo_por_resultado: number | null
  importe_gastado: number | null
  editable: boolean
  actualizado_en: string | null
  edicion_habilitada_hasta: string | null
}

export interface ObservacionOut {
  id: number
  texto: string
  autor_id: number | null
  creado_en: string
}

export interface MensualOut {
  id: number
  periodo_inicio: string
  periodo_fin: string
  mensajes_total: number
  gasto_total: number
  costo_por_mensaje: number
  presupuesto: number
  sobrante: number | null
  rendimiento: 'bueno' | 'regular' | 'bajo' | null
  origen: 'manual' | 'calculado'
}

export interface CuentaOut {
  usuario: string
  password: string
  tipo_cuenta: string | null
  metodo_pago: string | null
  forma_pago: string | null
}

export interface ClienteLoteCampanaIn {
  nombre: string
  paquete?: string | null
  tipo: 'local' | 'nacional' | 'otro'
  presupuesto: number
  presupuesto_esquema: 'mensual' | 'semanal' | 'diario'
  formato_post: boolean
  formato_3d: boolean
  formato_boton: boolean
  formato_otro: boolean
  lugar?: string | null
  fecha_inicio: string
  fecha_renovacion: string
}

export interface ClienteLoteItemIn {
  nombre: string
  cuenta: { usuario: string; password: string }
  campana: ClienteLoteCampanaIn
  confirmar_vinculo: boolean
  tipo_cuenta?: string | null
  metodo_pago?: string | null
  forma_pago?: string | null
}

export interface FilaErrorOut {
  index: number
  nombre: string
  errores: string[]
}

export interface FilaConfirmacionOut {
  index: number
  nombre: string
  cliente_existente: string
}

export interface NoRenovadoItem {
  id: number
  nombre: string
  campanas: CampanaResumen[]
  puede_continuar: boolean
  ultima_campana: CampanaResumen | null
}

export interface CreatedCredentials {
  id: number
  nombre: string
  username: string
  password: string
  rol: string
  solo_lectura: boolean
}

export interface UsuarioListItem {
  id: number
  nombre: string
  username: string
  rol: string
  solo_lectura: boolean
  activo: boolean
  creado_en: string
}

// ------------------------------------------------------------- panel admin
export interface CMConCartera {
  id: number
  nombre: string
  username: string
  activo: boolean
  total_clientes: number
}

export interface ClienteAdminItem {
  id: number
  nombre: string
  estado: string
  total_campanas: number
}

export interface CampanaResumenAdmin {
  id: number
  nombre: string
  tipo: string
  estado: string
  costo_actual: number | null
  semaforo: 'bueno' | 'regular' | 'bajo' | null
}

export interface ClienteAdminDetalle {
  id: number
  nombre: string
  estado: string
  cm_id: number
  cm_nombre: string
  campanas: CampanaResumenAdmin[]
}

export interface SemanaConsolidada {
  inicio: string
  fin: string
  mensajes: number
  costo_por_resultado: number | null
  importe_gastado: number
}

export interface MensualConsolidado {
  periodo_inicio: string
  periodo_fin: string
  mensajes_total: number
  gasto_total: number
  costo_por_mensaje: number
  presupuesto: number
  sobrante: number
  rendimiento: 'bueno' | 'regular' | 'bajo' | null
}

export interface MigrarCMOut {
  clientes_migrados: number
  cm_origen: string
  cm_destino: string
}
