"""Modelos SQLAlchemy que reflejan esquema_base_datos.sql tal cual. El SQL de
las migraciones es la fuente de verdad del DDL; estas clases son la
proyección ORM usada por la API."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    rol: Mapped[str] = mapped_column(Text, nullable=False)
    solo_lectura: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    primer_ingreso: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[dt.datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (CheckConstraint("rol IN ('cm','admin')", name="usuarios_rol_check"),)


class CuentaPublicitaria(Base):
    __tablename__ = "cuentas_publicitarias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_enc: Mapped[str] = mapped_column(Text, nullable=False)
    password_enc: Mapped[str] = mapped_column(Text, nullable=False)
    huella: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    creado_en: Mapped[dt.datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    clientes: Mapped[list["Cliente"]] = relationship(back_populates="cuenta")


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cm_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    cuenta_id: Mapped[int | None] = mapped_column(ForeignKey("cuentas_publicitarias.id"))
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[str] = mapped_column(Text, nullable=False, default="activo")
    tipo_cuenta: Mapped[str | None] = mapped_column(Text)
    metodo_pago: Mapped[str | None] = mapped_column(Text)
    forma_pago: Mapped[str | None] = mapped_column(Text)
    creado_en: Mapped[dt.datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    cuenta: Mapped[CuentaPublicitaria | None] = relationship(back_populates="clientes")
    campanas: Mapped[list["Campana"]] = relationship(back_populates="cliente", cascade="all, delete-orphan")
    cm: Mapped["Usuario"] = relationship(foreign_keys=[cm_id])

    __table_args__ = (
        CheckConstraint("estado IN ('activo','no_renovado')", name="clientes_estado_check"),
        UniqueConstraint("cm_id", "nombre", name="clientes_cm_id_nombre_key"),
    )


class Campana(Base):
    __tablename__ = "campanas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    paquete: Mapped[str | None] = mapped_column(Text)
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    presupuesto: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    presupuesto_esquema: Mapped[str] = mapped_column(Text, nullable=False, default="mensual")
    formato_post: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    formato_3d: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    formato_boton: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    formato_otro: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    lugar: Mapped[str | None] = mapped_column(Text)
    fecha_inicio: Mapped[dt.date] = mapped_column(Date, nullable=False)
    fecha_renovacion: Mapped[dt.date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(Text, nullable=False, default="activa")
    creado_en: Mapped[dt.datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    cliente: Mapped[Cliente] = relationship(back_populates="campanas")
    semanas: Mapped[list["Semana"]] = relationship(back_populates="campana", cascade="all, delete-orphan")
    observaciones: Mapped[list["Observacion"]] = relationship(back_populates="campana", cascade="all, delete-orphan")
    mensuales: Mapped[list["Mensual"]] = relationship(back_populates="campana", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("tipo IN ('local','nacional','otro')", name="campanas_tipo_check"),
        CheckConstraint(
            "presupuesto_esquema IN ('mensual','semanal','diario')", name="campanas_presupuesto_esquema_check"
        ),
        CheckConstraint("estado IN ('activa','vencida','cerrada')", name="campanas_estado_check"),
    )


class Semana(Base):
    __tablename__ = "semanas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campana_id: Mapped[int] = mapped_column(ForeignKey("campanas.id", ondelete="CASCADE"), nullable=False)
    inicio: Mapped[dt.date] = mapped_column(Date, nullable=False)
    fin: Mapped[dt.date] = mapped_column(Date, nullable=False)
    mensajes: Mapped[int | None] = mapped_column(Integer)
    costo_por_resultado: Mapped[float | None] = mapped_column(Numeric(10, 2))
    importe_gastado: Mapped[float | None] = mapped_column(Numeric(10, 2))
    editable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    capturado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    actualizado_en: Mapped[dt.datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    edicion_habilitada_hasta: Mapped[dt.datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    campana: Mapped[Campana] = relationship(back_populates="semanas")

    __table_args__ = (UniqueConstraint("campana_id", "inicio", name="semanas_campana_id_inicio_key"),)


class Observacion(Base):
    __tablename__ = "observaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campana_id: Mapped[int] = mapped_column(ForeignKey("campanas.id", ondelete="CASCADE"), nullable=False)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    autor_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    creado_en: Mapped[dt.datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    campana: Mapped[Campana] = relationship(back_populates="observaciones")


class Mensual(Base):
    __tablename__ = "mensuales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campana_id: Mapped[int] = mapped_column(ForeignKey("campanas.id", ondelete="CASCADE"), nullable=False)
    periodo_inicio: Mapped[dt.date] = mapped_column(Date, nullable=False)
    periodo_fin: Mapped[dt.date] = mapped_column(Date, nullable=False)
    mensajes_total: Mapped[int] = mapped_column(Integer, nullable=False)
    gasto_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    costo_por_mensaje: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    presupuesto: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    sobrante: Mapped[float | None] = mapped_column(Numeric(12, 2))
    rendimiento: Mapped[str | None] = mapped_column(Text)
    origen: Mapped[str] = mapped_column(Text, nullable=False, default="calculado")
    creado_en: Mapped[dt.datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    campana: Mapped[Campana] = relationship(back_populates="mensuales")

    __table_args__ = (
        CheckConstraint("rendimiento IN ('bueno','regular','bajo')", name="mensuales_rendimiento_check"),
        CheckConstraint("origen IN ('manual','calculado')", name="mensuales_origen_check"),
        UniqueConstraint("campana_id", "periodo_inicio", name="mensuales_campana_id_periodo_inicio_key"),
    )


class ArchivoNoRenovado(Base):
    __tablename__ = "archivo_no_renovados"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    cm_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    motivo: Mapped[str | None] = mapped_column(Text)
    archivado_en: Mapped[dt.datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    leida: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    creado_en: Mapped[dt.datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "tipo IN ('recordatorio_captura','vencimiento','sistema')", name="notificaciones_tipo_check"
        ),
    )


class Bitacora(Base):
    __tablename__ = "bitacora"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    accion: Mapped[str] = mapped_column(Text, nullable=False)
    detalle: Mapped[dict | None] = mapped_column(JSONB)
    creado_en: Mapped[dt.datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class MetricaConfig(Base):
    __tablename__ = "metricas_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    paquete: Mapped[str | None] = mapped_column(Text)
    umbral_bueno: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    umbral_regular: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    caida_mensajes_alerta_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=30)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[dt.datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    actualizado_en: Mapped[dt.datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("tipo IN ('local','nacional','otro')", name="metricas_config_tipo_check"),
        UniqueConstraint("tipo", "paquete", name="metricas_config_tipo_paquete_key"),
    )
