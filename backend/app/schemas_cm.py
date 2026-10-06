import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field, model_validator

TipoCampana = Literal["local", "nacional", "otro"]
EsquemaPresupuesto = Literal["mensual", "semanal", "diario"]


# ---------------------------------------------------------------- estado CM
class EstadoCMOut(BaseModel):
    primer_ingreso: bool
    total_clientes: int


# -------------------------------------------------------------- clientes
class ClienteListItem(BaseModel):
    id: int
    nombre: str
    estado: str
    campanas_activas: int
    campanas_vencidas: int


class CampanaResumen(BaseModel):
    id: int
    nombre: str
    tipo: str
    estado: str


class ClienteDetalle(BaseModel):
    id: int
    nombre: str
    estado: str
    campanas: list[CampanaResumen]


class RenombrarClienteIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)


class EliminarClienteIn(BaseModel):
    confirmacion_nombre: str


# ------------------------------------------------------- alta múltiple
class ClienteLoteCuentaIn(BaseModel):
    usuario: str = Field(min_length=1)
    password: str = Field(min_length=1)


class ClienteLoteCampanaIn(BaseModel):
    nombre: str = Field(min_length=1)
    paquete: str | None = None
    tipo: TipoCampana
    presupuesto: float = Field(gt=0)
    presupuesto_esquema: EsquemaPresupuesto = "mensual"
    formato_post: bool = False
    formato_3d: bool = False
    formato_boton: bool = False
    formato_otro: bool = False
    lugar: str | None = None
    fecha_inicio: dt.date
    fecha_renovacion: dt.date

    @model_validator(mode="after")
    def _validar_fechas(self):
        if self.fecha_renovacion <= self.fecha_inicio:
            raise ValueError("La fecha de renovación debe ser posterior a la fecha de inicio")
        return self


class ClienteLoteItemIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)
    cuenta: ClienteLoteCuentaIn
    campana: ClienteLoteCampanaIn
    confirmar_vinculo: bool = False
    tipo_cuenta: str | None = None
    metodo_pago: str | None = None
    forma_pago: str | None = None


class ClienteLoteRequest(BaseModel):
    clientes: list[ClienteLoteItemIn] = Field(min_length=1)


class FilaErrorOut(BaseModel):
    index: int
    nombre: str
    errores: list[str]


class FilaConfirmacionOut(BaseModel):
    index: int
    nombre: str
    cliente_existente: str


class ClienteCreadoOut(BaseModel):
    cliente_id: int
    nombre: str
    campana_id: int


class ClienteLoteResultado(BaseModel):
    creados: list[ClienteCreadoOut]


# --------------------------------------------------------- datos de cuenta
class CuentaOut(BaseModel):
    usuario: str
    password: str
    tipo_cuenta: str | None = None
    metodo_pago: str | None = None
    forma_pago: str | None = None


class CuentaIn(BaseModel):
    usuario: str = Field(min_length=1)
    password: str = Field(min_length=1)
    tipo_cuenta: str | None = None
    metodo_pago: str | None = None
    forma_pago: str | None = None


# --------------------------------------------------------------- campañas
class CampanaDetalle(BaseModel):
    id: int
    cliente_id: int
    nombre: str
    paquete: str | None
    tipo: str
    presupuesto: float
    presupuesto_esquema: str
    formato_post: bool
    formato_3d: bool
    formato_boton: bool
    formato_otro: bool
    lugar: str | None
    fecha_inicio: dt.date
    fecha_renovacion: dt.date
    estado: str

    class Config:
        from_attributes = True


# ---------------------------------------------------------------- semanas
class SemanaOut(BaseModel):
    id: int
    inicio: dt.date
    fin: dt.date
    mensajes: int | None
    costo_por_resultado: float | None
    importe_gastado: float | None
    editable: bool
    actualizado_en: dt.datetime | None
    edicion_habilitada_hasta: dt.datetime | None

    class Config:
        from_attributes = True


class SemanaUpdateIn(BaseModel):
    mensajes: int = Field(ge=0)
    costo_por_resultado: float = Field(ge=0)
    importe_gastado: float = Field(ge=0)


# ------------------------------------------------------------ observaciones
class ObservacionOut(BaseModel):
    id: int
    texto: str
    autor_id: int | None
    creado_en: dt.datetime

    class Config:
        from_attributes = True


class ObservacionIn(BaseModel):
    texto: str = Field(min_length=1)


# ----------------------------------------------------------------- mensuales
class MensualOut(BaseModel):
    id: int
    periodo_inicio: dt.date
    periodo_fin: dt.date
    mensajes_total: int
    gasto_total: float
    costo_por_mensaje: float
    presupuesto: float
    sobrante: float | None
    rendimiento: str | None
    origen: str

    class Config:
        from_attributes = True


class MensualManualIn(BaseModel):
    periodo_inicio: dt.date
    periodo_fin: dt.date
    mensajes_total: int = Field(ge=0)
    gasto_total: float = Field(ge=0)

    @model_validator(mode="after")
    def _validar_fechas(self):
        if self.periodo_fin <= self.periodo_inicio:
            raise ValueError("El periodo debe tener una fecha final posterior a la inicial")
        return self


# --------------------------------------------------- renovación / vencimiento
class RenovarCampanaIn(BaseModel):
    fecha_renovacion: dt.date


class NoRenovarClienteIn(BaseModel):
    accion: Literal["borrar", "conservar"]
    confirmacion_nombre: str | None = None
    motivo: str | None = None


class NoRenovadoItem(BaseModel):
    id: int
    nombre: str
    campanas: list[CampanaResumen]
    puede_continuar: bool
    ultima_campana: CampanaResumen | None
