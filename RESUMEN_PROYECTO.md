# Resumen del proyecto — Sistema de gestión de campañas INNquietus

Documento de referencia de todo lo construido, pensado para arrancar una conversación nueva sin perder contexto.

**Stack:** PostgreSQL · Backend Python (FastAPI + APScheduler) · Frontend React (Vite + TypeScript) · JWT + bcrypt · cifrado AES-GCM · PDF con ReportLab · Docker Compose (Postgres + backend + Adminer).

**Documentos base:** `especificacion_sistema_campanas.md` y `esquema_base_datos.sql`, provistos al inicio del proyecto. El esquema SQL se usó tal cual como fuente de verdad, con migraciones aditivas encima (van en la 006 actualmente, ver abajo).

**Cómo correrlo / comandos:** todo está en **[COMO_EJECUTAR.md](COMO_EJECUTAR.md)** — no repetir aquí, solo remitir a ese archivo.

---

## Las 6 fases del pedido original (todas completas)

### Fase 1 — Base de datos, migraciones y seed
- `001_init.sql`: copia literal de `esquema_base_datos.sql`.
- `002_metricas_config.sql`: tabla `metricas_config` para los umbrales de rendimiento (sección 7), parametrizables sin tocar código. Triggers: `mensuales` inmutable ante `UPDATE`; captura manual de mensual solo si la campaña no tiene ninguno previo.
- `003_semanas_importe_gastado.sql`: columna `semanas.importe_gastado` (costo por resultado e importe gastado son métricas independientes).
- `004_mensuales_permitir_cascada.sql`: corrigió un conflicto real — el bloqueo de `DELETE` en `mensuales` impedía el borrado en cascada que exige la sección 9-c. Se quitó el bloqueo de `DELETE`, se conservó el de `UPDATE`.
- `005_metricas_definitivas.sql`: umbrales **definitivos** de rendimiento que diste (ver sección "Métricas" abajo).
- `006_clientes_datos_pago.sql`: columnas `tipo_cuenta`, `metodo_pago`, `forma_pago` en `clientes`.
- Runner de migraciones propio (`app/migrations/run_migrations.py`), idempotente.
- Seed (`app/seed.py`): CMs Kori, Saray, Uriel, Alondra, Fátima y Luz (cuenta de CM `luz.cm` y de admin `luz.admin` separadas). Solo estructura — sin datos de captura falsos.

### Fase 2 — Autenticación y roles
JWT + bcrypt, aislamiento total por `cm_id`, alta de CM/admin (con opción solo lectura) mostrando credenciales una sola vez, reseteo de contraseñas, bitácora de auditoría.

### Fase 3 — Panel del CM
Lista de clientes, alta múltiple con flujo de vinculación de cuenta (sección 9-a), borrado con doble confirmación, renombrado, dropdown de campañas, pestañas (Datos semanales / Observaciones / Datos de la cuenta), comparación de hasta 2 meses, pantalla "Comenzar" + easter egg del changuito (sección 10, completo: hover, clics, confeti al quinto clic, ola al escribir "innquietus").

### Fase 4 — Jobs programados (APScheduler, `app/jobs/`)
- **Sábado 00:00**: bloquea la semana terminada, crea la nueva.
- **Viernes 14:00**: notifica a CMs con semanas sin capturar.
- **Diario 12:00**: cierra el ciclo de campañas vencidas (archiva mensual, borra semanas/observaciones de esa campaña, bloquea hasta que el CM resuelva renovación/no-renovación).
- Los tres se pueden correr a mano (comandos en `COMO_EJECUTAR.md`) sin esperar al horario real — **importante para pruebas**.

### Fase 5 — Panel admin
CMs → clientes → campañas con fila-resumen y semáforo, tabla de solo lectura, gráficas SVG propias (mensual hasta 3 meses + semanal, sin librerías externas), vista consolidada "Todas", gestión de equipo (alta, reset, baja de CM con migración de cartera completa a otro CM).

### Fase 6 — Reporte mensual en PDF
Botón "Generar reporte": resumen del mes, comparación contra el mes anterior, presupuesto vs. consumido, gráfica, conclusión en español llano. Consolida todas las campañas del cliente.

---

## Cambios pedidos después de las 6 fases (todos completos)

1. **Logo real de INNquietus** integrado en login, ambos sidebars, favicon y encabezado de los PDFs. Paleta de colores tomada del logo (morado/amarillo/naranja) en toda la interfaz.
2. **Umbrales de rendimiento definitivos** (sección 7, ya no provisionales): Local bueno ≤19 / regular 20-29 / bajo ≥30. Nacional bueno ≤14 / regular 15-19 / bajo ≥20. Verificados los 6 casos (3 por tipo) en ambos paneles con datos reales, comparando colores renderizados vía DOM.
3. **"Cuenta publicitaria" → "cuenta"** en todas las etiquetas y mensajes de error visibles (se confundía con otra cosa).
4. **Tipo de cuenta / método de pago / forma de pago**: 3 campos nuevos en el cliente (tabla `clientes`), capturables al dar de alta y editables en "Datos de la cuenta". Implementados como **texto libre** (no se dieron opciones fijas) — convertible a dropdown si luego se da la lista exacta de valores.
5. **Etiquetas de mes duplicadas en la gráfica del admin** ("jun" dos veces): corregido agregando el día ("13 jun", "20 jun", "27 jul").
6. **Fila de semana: guardar → vista + botón Editar**: al guardar, la fila muestra los valores guardados en modo lectura con badge "Guardado" y botón "Editar" (antes se quedaba con los inputs abiertos sin ninguna señal de que había guardado — esto es lo que parecía "no se guarda", pero **sí se guardaba**; era solo falta de retroalimentación visual).
7. **Autocálculo de importe gastado** = mensajes × costo por resultado, mientras se captura; sigue siendo editable a mano si el dato real de la plataforma difiere.
8. **Reportes habilitados también para el CM** (antes solo admin): mismo endpoint reutilizado, con aislamiento por `cm_id`.
9. **Reporte semanal en PDF** (nuevo, además del mensual): mensajes, costo por resultado, importe gastado, comparación contra la semana anterior, gráfica, conclusión en español llano — sin semáforo de color (al consolidar campañas de distinto tipo local/nacional, un semáforo único no tendría sentido). Disponible en ambos paneles.
10. **Modo "un solo comando"**: `app/main.py` monta `StaticFiles` sirviendo `backend/app/static` (ahí cae `npm run build`), así que `docker compose up -d` solo (sin `npm run dev` aparte) sirve todo en `http://localhost:8000`. El modo de dos terminales (con recarga en vivo) sigue disponible para cuando se edite el frontend.
11. **Adminer** agregado como servicio de `docker-compose.yml` — gestor de base de datos visual en `http://localhost:8080`, sin nada que instalar aparte.

**Refactor de soporte:** se creó `backend/app/consolidacion.py` con `mensuales_consolidados_de_cliente()` y `semanas_consolidadas_de_cliente()`, compartido entre el panel admin, el panel CM y los dos generadores de PDF (mensual y semanal) — antes esa lógica estaba duplicada.

**Bug real encontrado y corregido en el camino:** al generar el reporte semanal/mensual en memoria (`io.BytesIO`, para descargar sin guardar un archivo temporal), el código hacía `str(buffer)` por accidente en vez de pasar el objeto — igual al bug que ya se había corregido en el reporte mensual original, pero reapareció al construir el nuevo módulo. Corregido con una guarda genérica (`hasattr(output_path, "write")`).

---

## Cosas descubiertas probando en vivo (no son bugs, son comportamiento esperado)

- **El scheduler puede "perderse" un job programado si el backend se reinicia justo cerca de la hora del disparador** (pasó varias veces hoy porque reinicié el contenedor muchas veces seguidas mientras programaba). En un servidor real que no se reinicia todo el día, esto no pasa. Si hace falta forzar un job sin esperar, están los comandos manuales en `COMO_EJECUTAR.md`.
- **El navegador no se entera solo de cambios que pasan en el servidor** (p. ej. un job corrido a mano desde la terminal): hay que refrescar la página (F5) o volver a entrar al cliente para que el frontend vuelva a pedir los datos actualizados. No hay websockets ni push en tiempo real.

---

## Estado actual de los datos (¡ojo antes de la próxima sesión!)

La base **ya no tiene solo datos de seed** — tiene mezcla de:
- Datos de ejemplo del seed original (Novedades, BTW Amigos, Ferretería El Tornillo, Clínica Vital).
- Datos reales que el usuario capturó probando la app él mismo en su navegador (cliente "Adelene", cliente "luis").
- Datos que yo metí a propósito para verificar el semáforo y los reportes (varios mensuales de prueba en Novedades y Ferretería, 3 notificaciones de vencimiento repetidas en Ferretería por haber corrido el cierre de ciclo 3 veces seguidas para probar verde/amarillo/rojo).

**Por instrucción explícita, no se ha limpiado nada de esto todavía** — se deja así a propósito para que se siga probando. La limpieza total (dejar el sistema vacío, sin ejemplos) es un pendiente explícito, ver abajo.

---

## Métricas de rendimiento (sección 7) — definitivas

Tabla `metricas_config` (editable sin tocar código):

| tipo | umbral_bueno | umbral_regular | bueno | regular | bajo |
|---|---|---|---|---|---|
| local | 19.00 | 29.00 | 0–19 | 20–29 | ≥30 |
| nacional | 14.00 | 19.00 | 0–14 | 15–19 | ≥20 |
| otro | 19.00 | 29.00 | (igual que local, no se usa en la práctica) |

---

## Cambios de la sesión del 27 de julio 2026: botón "Renovar" en No Renovados

1. **Botón "Renovar" en "No renovados"** (antes no existía forma de traer de vuelta a un cliente ya archivado):
   - **Menos de 2 meses desde que se archivó**: al dar "Renovar" se elige entre "Continuar con [la última campaña]" (solo pide nueva fecha, reutiliza `POST /cm/campanas/{id}/renovar` — mismo endpoint de siempre, ahora también reactiva al cliente) o "Crear campaña nueva" (formulario completo, campaña nueva independiente).
   - **2 meses o más**: "borrón y cuenta nueva" — se salta directo a una advertencia y, al continuar, se borran las campañas vencidas del cliente (y su historial de semanas/mensuales) antes de crear la campaña nueva. Nuevo endpoint `POST /cm/clientes/{id}/reactivar`.
   - **1 año sin volver**: se elimina el cliente por completo. Nuevo job diario 12:10 (`backend/app/jobs/purga_no_renovados.py`), registrado en el scheduler junto a los otros tres.
   - Bug real encontrado y corregido en el camino: `archivo_no_renovados.cliente_id` no tiene `ON DELETE CASCADE` en el esquema; el job de purga borra explícitamente esas filas antes de borrar al cliente (si no, `IntegrityError`). El flujo "borrar" existente de `no_renovar_cliente` nunca lo disparó porque solo se usa antes de que exista esa fila.
   - Textos de "No renovados" y del diálogo de no-renovar actualizados para reflejar las reglas de 2 meses / 1 año (ya no dicen "para siempre").
2. **Pagos siempre mensuales**: se quitó el selector "Esquema de presupuesto" (semanal/diario) de los formularios de alta y de campaña nueva — el campo sigue existiendo en la base (por compatibilidad con datos viejos) pero los formularios ya solo mandan `"mensual"`. Se agregó autocompletado: al elegir fecha de inicio, la fecha de renovación se rellena a +1 mes (sigue editable a mano). Se extrajo `frontend/src/pages/cm/CampanaFields.tsx`, compartido entre el alta de clientes y el diálogo de renovar.
3. **Mejor formato en "En resumen" del reporte semanal en PDF**: ahora es una tarjeta con fondo (igual estilo que las tarjetas de estadísticas de arriba) envuelta en `KeepTogether`, en vez de un párrafo suelto — verificado generando un PDF de prueba.

Todo probado en el navegador real con datos de prueba (creados y limpiados vía SQL directo, sin tocar los 6 clientes reales que ya había: Novedades, BTW Amigos, Ferretería El Tornillo, Clínica Vital, Adelene, luis).

---

## Cambios de la sesión del 28 de julio 2026

1. **Bug de datos de prueba en Ferretería El Tornillo**: 3 mensuales de la sesión anterior (creados en segundos, para probar bueno/regular/bajo) tenían periodos traslapados y todos terminaban "hoy" — se veían como "Resultados de junio" repetido dos veces. Se reemplazaron por 3 meses limpios y consecutivos (abril/mayo/junio). De paso, la etiqueta de mes en `frontend/src/pages/cm/tabs/DatosSemanalesTab.tsx` (función `nombreMes`) solo miraba `periodo_inicio`; ahora `etiquetaPeriodo` considera también `periodo_fin` (p. ej. "junio – julio" si el periodo cruza de mes).
2. **Los modales ya no se cierran al hacer clic afuera** — se quitó `onClick={(e) => e.target === e.currentTarget && onClose()}` del backdrop en los 7 diálogos que lo tenían (`AddClientesModal`, `RenovarDialog`, `NoRenovarDialog`, `ReactivarClienteDialog`, `DeleteClientDialog`, `AltaUsuarioModal`, `BajaCmDialog`). Ahora solo se cierran con sus propios botones (Cancelar/✕).
3. **Letras distorsionadas en las gráficas del panel admin** ("1 abr", "S1", etc. se veían como glitcheadas): el `<svg>` de `frontend/src/components/charts/BarChart.tsx` y `LineChart.tsx` usa `preserveAspectRatio="none"` con un `viewBox` de 100 unidades de ancho fijo vs. el ancho real en píxeles (varios cientos) — eso estira X y Y distinto, y estiraba también los glifos del `<text>` SVG. Se sacaron las etiquetas del SVG y se renderizan como `<span>` HTML normal posicionados por porcentaje (mismo patrón que ya usaba el tooltip, que por eso nunca se vio afectado).
4. **Permiso de admin para editar semanas cerradas (2h) + autorrelleno en 0**:
   - Cuando el job `cierre_semana` (sábado 00:00) encuentra una semana nunca capturada, ahora la deja en `mensajes=0, costo_por_resultado=0, importe_gastado=0` en vez de en blanco (`backend/app/jobs/cierre_semana.py`). Se corrió también una corrección única contra las semanas ya cerradas en blanco que hubiera en la base (no había ninguna al momento de aplicarla).
   - Nuevo endpoint `POST /admin/semanas/{id}/habilitar-edicion` (`backend/app/routers/admin_data.py`): le da al CM 2 horas para editar una semana ya cerrada. Solo se puede otorgar entre el **sábado 8:00am y el viernes 3:00pm** siguiente (hora local, `backend/app/dates.py:dentro_de_ventana_habilitacion`) — el cierre normal semanal (sábado 00:00) no cambió. Manda una notificación tipo `"sistema"` al CM dueño (reutiliza el mecanismo de notificaciones existente, sin tocar su esquema).
   - `PUT /cm/semanas/{id}` ahora acepta la edición también si `edicion_habilitada_hasta` sigue vigente, además del caso normal `editable=true`.
   - Nueva columna `semanas.edicion_habilitada_hasta` (migración `007_semanas_edicion_admin.sql`).
   - Frontend: el CM ve un cronómetro corriendo ("Edición habilitada · expira en 01:59:xx") en `DatosSemanalesTab.tsx` mientras el permiso esté activo, y puede editar/guardar como si la semana siguiera abierta; al expirar vuelve a "Cerrada" sola, sin job adicional. El admin otorga el permiso desde `ClienteAdminDetail.tsx` (botón "Habilitar edición 2h" por semana cerrada, oculto para admins de solo lectura).
   - Probado de punta a punta: job de cierre → 0 en vez de blanco → admin habilita → CM edita con cronómetro corriendo → guarda bien → expira → se bloquea de nuevo (confirmado también a nivel backend con `curl`, 403 tras expirar).

5. **"Cerrar sesión" se veía mal al pasar el mouse**: el botón usa `.btn-ghost`, cuyo `:hover` (`background: var(--ink-100)`, gris muy claro) está pensado para fondos claros — dentro de la barra lateral morada oscura se veía como una píldora blanca fuera de lugar. Se agregó `.btn-ghost-dark` (fondo transparente, hover `rgba(255,255,255,0.08)`) en `frontend/src/index.css`, usado en `Sidebar.tsx` y `AdminSidebar.tsx`.
6. **Bug de distorsión en las gráficas, parte 2**: el fix de las letras (sesión anterior del mismo día) no alcanzaba — los círculos de cada punto en `LineChart.tsx` también salían estirados como óvalo, por la misma causa (`viewBox` de "100 unidades" fijas vs. el ancho real en píxeles, con `preserveAspectRatio="none"` forzando escalas X/Y distintas). Se corrigió de raíz en `BarChart.tsx` y `LineChart.tsx`: el `viewBox` ahora usa el ancho real medido con `ResizeObserver` (1 unidad = 1 px en ambos ejes), así que `preserveAspectRatio` ya ni hace falta. Verificado a nivel de píxel: los círculos miden exactamente lo mismo de ancho que de alto.
7. **Limpieza total de datos de ejemplo — ejecutada**: se vació `clientes, campanas, semanas, mensuales, cuentas_publicitarias, observaciones, archivo_no_renovados, notificaciones, bitacora` (los 7 clientes de seed/prueba que había, con todo su historial). Se conservaron las cuentas de usuario (CM/admin, 9 en total) y `metricas_config`. El sistema queda listo para capturar datos reales desde cero.
8. **Git inicializado y primer commit hecho — todavía NO subido a GitHub** (falta que el usuario diga la cuenta/organización; el repo debe ser privado). Antes de comitear se limpiaron dos cosas que no debían quedar en el historial: 3 archivos basura `<_io.BytesIO object at ...>` en `backend/` (residuo físico del bug ya corregido de `str(buffer)` en los reportes) y `.claude/settings.local.json` (tenía una contraseña real en texto plano guardada en un permiso de Bash) — este último se agregó a `.gitignore`.
9. **"Un mes" de campaña ahora son 30 días exactos, no el mes de calendario**: `addMonthIso` (`frontend/src/pages/cm/CampanaFields.tsx`) e `inUnMesIso` (`frontend/src/pages/cm/RenovarDialog.tsx`) usaban `setMonth(getMonth()+1)`, que da entre 28 y 31 días según el mes de arranque (1 feb → 1 mar son solo 28 días). Ahora ambas suman 30 días fijos (`setDate(getDate()+30)`). Afecta el autocompletado de fecha de renovación en alta de cliente, "Crear campaña nueva" y "Continuar con..." al renovar. Verificado: 01/02/2026 + 30 días = 03/03/2026 (no 01/03/2026).
10. **Bug real: dos pestañas de navegador con roles distintos se pisaban entre sí**. El token de sesión se guardaba en `localStorage` (`frontend/src/api/client.ts`), que se comparte entre TODAS las pestañas del mismo navegador — iniciar sesión como admin en una pestaña sobrescribía el token de la pestaña donde ya había una sesión de CM abierta, y esa pestaña pasaba a ser el admin en cuanto volvía a leer el token (p. ej. al refrescar con F5, algo que esta app ya requiere seguido porque no tiene tiempo real). Cambiado a `sessionStorage`, que es independiente por pestaña — verificado abriendo CM en una pestaña y admin en otra, refrescando la del CM y confirmando que se quedó como CM. Trade-off aceptado: cada pestaña nueva pide iniciar sesión de nuevo (ya no persiste entre pestañas), pero sí persiste al refrescar la misma pestaña.

---

## Cambios de la sesión del 29 de julio 2026: despliegue a producción

**Repo en GitHub**: privado, `github.com/kirito203278/sistema-campanas` (cuenta personal del usuario, no la de la empresa — decisión explícita para simplificar). Antes del primer push se limpiaron del repo 3 archivos basura `<_io.BytesIO...>` y se confirmó que `.env`/credenciales no se suben.

**Desplegado en Render** (plan gratis, sin tarjeta) + **Neon** (Postgres gratis, sin tarjeta) — decisión forzada por falta de presupuesto. URL: `https://sistema-campanas.onrender.com`.

1. **Cambios de código para que el Dockerfile sirva tanto local como Render**:
   - `backend/Dockerfile`: pasó a **multi-stage** (etapa `node:20-alpine` compila el frontend, se copia a la imagen final de Python) — Render construye desde git y `backend/app/static` no se versiona, así que la imagen tiene que ser autosuficiente. No afecta el flujo local: `docker-compose.yml` sigue montando `./backend:/app` como bind mount, que tapa lo horneado en la imagen en tiempo de ejecución.
   - `docker-compose.yml`: `build` del servicio `backend` pasó de `./backend` a `{context: ., dockerfile: backend/Dockerfile}` (necesita ver también `frontend/`). Se agregó `RELOAD: "true"` en su `environment` para conservar el auto-reload local.
   - `backend/entrypoint.sh`: puerto ahora lee `${PORT:-8000}` (Render asigna el puerto por variable de entorno) y `--reload` de uvicorn ahora es condicional a `RELOAD=true` (nunca debe ir en producción).
   - `backend/app/main.py`: CORS ya no hardcodeado a `localhost:5173` — nuevo campo `Settings.cors_origins` (coma-separado) en `backend/app/config.py`.
   - Nuevo endpoint `POST /api/jobs/run/{nombre}` (`backend/app/routers/jobs.py`), protegido con secreto compartido (`X-Jobs-Secret`, comparación `hmac.compare_digest`) — dispara cualquiera de los 4 jobs programados desde un cron externo. Necesario porque Render gratis "duerme" el proceso tras inactividad y el scheduler interno (APScheduler) podría no estar despierto a la hora exacta; este endpoint es un respaldo adicional, no reemplaza el scheduler. Nuevo campo `Settings.jobs_secret`.

2. **Zona horaria corregida**: el default de `Settings.tz` (`backend/app/config.py`) y de `.env.example` estaba en `America/Mazatlan` desde el inicio del proyecto — nunca se había confirmado la ubicación real de la agencia. La agencia opera desde **Pachuca, Hidalgo**, que usa `America/Mexico_City` (UTC-6, una hora adelante de Mazatlán). Corregido en ambos lugares y en el `.env` local. Importante: la variable `TZ` la respeta directamente el sistema operativo (glibc), así que corrige no solo el scheduler sino cualquier `datetime.now()`/`date.today()` sin zona explícita en todo el código.

3. **Infraestructura externa configurada** (todo del lado del usuario, en paneles web):
   - **cron-job.org**: 4 tareas (`cierre_semana` sábados 00:05, `recordatorio_captura` viernes 14:00, `cierre_ciclo` diario 12:00, `purga_no_renovados` diario 12:10), zona horaria America/Mexico_City, método POST + header `X-Jobs-Secret`. Los 4 probados con `curl` contra producción, responden 200.
   - **UptimeRobot**: monitor HTTP(s) a `/api/health` cada 5 min, para reducir el "despertar en frío" del plan gratis de Render.
   - Primera cuenta admin real (`cristina`) creada directamente contra la base de Neon (bootstrap — no había forma de crear la primera cuenta vía la app misma, porque el alta de usuarios requiere ya estar logueado como admin). Verificado login real contra producción.

4. **Refuerzos de seguridad** (commit `8874c0b`):
   - Nuevo `backend/app/security/rate_limit.py`: bloquea un `username` tras 5 intentos fallidos de login en 15 minutos (en memoria, un solo proceso — mismo supuesto que ya usa el scheduler). `backend/app/routers/auth.py` lo integra devolviendo 429. Mitiga fuerza bruta (riesgo ya bajo porque las contraseñas se generan aleatorias de 18 caracteres, no las elige la gente).
   - `CORS_ORIGINS` en Render corregido de `*` (cualquier origen, con `allow_credentials=True` — combinación insegura) al dominio real.
   - Documentado en `COMO_EJECUTAR.md` (sección 10) cómo respaldar la base de Neon con `pg_dump` vía Docker desechable (`postgres:18-alpine`, tiene que coincidir la versión mayor con la de Neon — verificado que funciona).

5. **Fix real encontrado dando de alta al equipo real**: `POST /admin/cms/{id}/baja` (dar de baja a un CM) siempre exigía un CM destino para migrar la cartera, **incluso con 0 clientes** — no había nada que migrar, pero si no existía otro CM activo la baja quedaba bloqueada sin motivo. Corregido en `backend/app/routers/admin_data.py` y `backend/app/schemas_admin.py` (`MigrarCMIn.migrar_a_cm_id` ahora opcional): si el CM tiene 0 clientes, se da de baja directo sin pedir destino; si tiene cartera, se sigue exigiendo como antes. `frontend/src/pages/admin/BajaCmDialog.tsx` actualizado para reflejarlo. Verificado también que al migrar SÍ se incluyen los clientes en estado `no_renovado`, no solo los activos (la consulta de migración nunca filtró por estado).

6. **Prueba completa de regresión** de todo el sistema (todas las fases + todos los cambios de las 3 sesiones), hecha contra la base local con datos desechables (creados y borrados con `curl` directo a la API + verificación en navegador real sin errores de consola): auth y rate limiting, alta de clientes, captura semanal y autocálculo, mensual manual, los 3 caminos de vencimiento/renovación completos, panel admin (cartera, semáforo, gráficas, equipo, permisos de solo lectura), los 4 reportes PDF, los 4 jobs programados, el permiso de edición de 2h de punta a punta. Sin errores encontrados.

---

## Pendientes / decisiones abiertas

- **"Habla en plural de listo"** — nunca se resolvió; el usuario no volvió a mencionarlo, sigue sin identificar a qué texto/botón se refería.
- **Notificación por WhatsApp** (capa 3, sección 8) — no implementada; la especificación la marca como opcional a futuro.
- **Conectar el dominio de HostGator** — opcional, puramente estético; el sistema ya funciona 100% en la URL de Render.
- **tipo_cuenta / metodo_pago / forma_pago como texto libre** — si en algún momento se quiere restringir a opciones fijas (dropdown), falta que el usuario dé la lista exacta de valores.
- **Dar de alta al resto del equipo real** — solo existe `cristina` (admin) en producción; falta crear las cuentas de los CMs y demás admins desde el panel.

## Archivos secretos que NO se suben a git (ya en `.gitignore`)

- `.env`
- `backend/seed_credentials.txt`
- `backend/credenciales_entrega.pdf` / `.txt`
