import datetime as dt

from pydantic import BaseModel

from app.schemas_cm import CampanaDetalle, MensualOut, SemanaOut


class CMConCartera(BaseModel):
    id: int
    nombre: str
    username: str
    activo: bool
    total_clientes: int


class ClienteAdminItem(BaseModel):
    id: int
    nombre: str
    estado: str
    total_campanas: int


class CampanaResumenAdmin(BaseModel):
    id: int
    nombre: str
    tipo: str
    estado: str
    costo_actual: float | None
    semaforo: str | None


class ClienteAdminDetalle(BaseModel):
    id: int
    nombre: str
    estado: str
    cm_id: int
    cm_nombre: str
    campanas: list[CampanaResumenAdmin]


class CampanaDetalleAdmin(CampanaDetalle):
    pass


class SemanaAdmin(SemanaOut):
    pass


class MensualAdmin(MensualOut):
    pass


class SemanaConsolidada(BaseModel):
    inicio: dt.date
    fin: dt.date
    mensajes: int
    costo_por_resultado: float | None
    importe_gastado: float


class MensualConsolidado(BaseModel):
    periodo_inicio: dt.date
    periodo_fin: dt.date
    mensajes_total: int
    gasto_total: float
    costo_por_mensaje: float
    presupuesto: float
    sobrante: float
    rendimiento: str | None


class MigrarCMIn(BaseModel):
    migrar_a_cm_id: int | None = None


class MigrarCMOut(BaseModel):
    clientes_migrados: int
    cm_origen: str
    cm_destino: str
