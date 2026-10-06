# Sistema de gestión de campañas — Especificación funcional v1

Documento de trabajo para construir la aplicación. Acompaña a `esquema_base_datos.sql`.

---

## 1. Arquitectura

Los CM trabajan cada quien en su computadora y la administradora ve todo en tiempo real, por lo que la base de datos debe ser **central**: un servidor con **PostgreSQL** y un backend (API) al que se conecta la aplicación de cada usuario. La app puede ser web servida en la red de la agencia o empaquetada como aplicación de escritorio; en ambos casos el dato vive en el servidor, nunca en la máquina del CM.

Componentes: base de datos PostgreSQL · backend con API y trabajos programados (cron) · frontend con dos paneles (CM y Admin) · generador de reportes PDF.

## 2. Roles y accesos

**CM.** Ve únicamente sus clientes. Captura semanales y observaciones, agrega/borra/renombra clientes, gestiona campañas de sus clientes, ve la comparación de hasta 2 meses. No puede cambiar su propia contraseña.

**Admin (Luz).** Tiene ambos paneles porque además lleva sus propios clientes: entra con su cuenta de CM para operar su cartera y con su cuenta de admin para supervisar. Como admin: ve todos los CM y sus clientes, gráficas de hasta 3 meses, genera el reporte formal del cliente, alta/baja de CM, migración de carteras, reseteo de contraseñas, alta de otros admins (con opción de solo lectura).

**Reglas de cuentas.** El username se deriva del nombre (`luz.hernandez`); la contraseña se genera aleatoria y segura (16+ caracteres, mayúsculas/minúsculas/números/símbolos, generada con CSPRNG) y se muestra a la admin **una sola vez** en una pestaña con botón de copiar, para entregarla por WhatsApp. No hay usernames duplicados. Una persona puede tener cuenta de CM y cuenta de admin, pero son cuentas separadas. Contraseñas de la app: hash bcrypt. Credenciales de la cuenta publicitaria de cada cliente: cifradas en la base (AES-GCM); se muestran solo en el apartado "Datos de la cuenta" del cliente.

## 3. Panel del CM

**Layout.** Columna izquierda: lista de sus clientes + botón "Agregar cliente". Al seleccionar un cliente, a la derecha:

- **Selector de campaña** (dropdown) cuando el cliente tiene más de una.
- **Pestaña Datos semanales:** tabla de la campaña activa con las semanas del ciclo (sábado a viernes), captura de mensajes y costo por resultado. Arriba, los resultados del mes anterior (máximo 2 meses de comparación). La semana en curso se edita las veces que sea; las semanas terminadas aparecen bloqueadas.
- **Pestaña Observaciones:** notas libres de la campaña ("se desactivó un anuncio…").
- **Pestaña Datos de la cuenta:** usuario y contraseña de la cuenta publicitaria del cliente (vienen por default al crear el cliente, editables).
- Datos generales de la campaña: paquete, tipo (local/nacional), formato del anuncio (post / 3D / botón / otro), presupuesto y esquema (mensual/semanal/diario), lugar, fechas de inicio y renovación.

**Altas.** Puede agregar varios clientes a la vez con los campos del Excel. Validación: campos obligatorios completos y credenciales de cliente no repetidas (ver punto 9-a). Si algo no pasa, no se guarda el lote y se marca qué fila falló.

**Bajas.** Borrado permanente con doble confirmación explícita ("Esta acción eliminará también sus campañas e historial. Escribe el nombre del cliente para confirmar"). Queda registro en bitácora.

**Renombrar.** Permitido; el cambio se refleja de inmediato en el panel de la admin.

**Primer ingreso (CM nuevo).** Pantalla de bienvenida con botón **Comenzar**. Al presionarlo se crea su estructura vacía: a la izquierda solo el botón "Agregar clientes" y a la derecha el estado vacío con el easter egg (punto 10).

## 4. Ciclo semanal

- La semana operativa va de **sábado a viernes**.
- Fecha límite de captura: **viernes 3:00 pm**.
- **Viernes 2:00 pm:** a quien tenga semanas sin capturar le llega una notificación (punto 8).
- **Sábado 00:00:** la semana terminada se bloquea (ya no se puede modificar) y se crea la fila de la semana nueva en cada campaña activa.
- El sistema calcula el **rendimiento acumulado** de la campaña de la semana 1 a la última capturada (tendencia de costo y de mensajes).

## 5. Ciclo mensual y renovación

- En el **primer mes de una campaña**, el dato mensual anterior se captura manualmente (una sola vez, solo si no existe ninguno). De ahí en adelante todo mensual se **calcula** a partir de las semanas y es **inmutable**.
- El día de la **fecha de renovación, a las 12:00 pm**, por campaña:
  1. Se calcula el resumen del ciclo (mensajes totales, gasto, costo por mensaje, sobrante vs presupuesto, rendimiento) y se archiva en `mensuales`.
  2. Se **borran** los datos semanales y las observaciones **solo de esa campaña** (sin tocar otras campañas del mismo cliente).
  3. La campaña pasa a estado **vencida** y su interfaz queda **bloqueada**: aparece el aviso de vencimiento y el CM no puede hacer nada más con esa campaña hasta resolver:
     - **"El cliente renovó"** → se confirma, se fija la nueva fecha de renovación y el ciclo reinicia.
     - **"No renovó"** → segunda ventana: **¿borrar todo lo relacionado a este cliente?**
       - **Borrar** → eliminación definitiva (con la misma doble confirmación del punto 3).
       - **Conservar** → el cliente pasa al apartado **"No renovados"**, visible para el CM y la admin; sus mensuales se conservan siempre.

## 6. Panel de la administradora

- Lista de CMs; al elegir uno, dropdown con sus clientes; al elegir cliente, selector de campaña si tiene varias (punto 9-b).
- **Tabla** con los datos capturados por el CM (solo lectura).
- **Dos gráficas:** rendimiento mensual (máximo 3 meses) y rendimiento semanal del ciclo en curso.
- El rendimiento **ya no se consulta por rango de fechas**: el sistema muestra automáticamente el rango de qué tan bien o mal va la campaña, calculado semanal y mensualmente según las métricas del punto 7.
- **Reporte mensual formal** (botón "Generar reporte"): documento PDF con identidad de la agencia, pensado para entregarse al cliente. Contenido: resumen del mes (mensajes, gasto, costo por mensaje), comparación con el mes anterior, presupuesto contratado vs consumido y sobrante, gráfica del mes, y una conclusión en lenguaje no técnico.
- **Gestión de CMs:** alta (genera credenciales, punto 2), baja. Al eliminar un CM, la admin elige a qué CM se migra su cartera completa: clientes, campañas, credenciales de clientes y, si el ciclo sigue abierto, también los datos semanales capturados.
- **Reseteo de contraseñas** de cualquier CM.
- **Alta de otros usuarios admin**, con opción de rol completo o **solo lectura** (ve todo, no edita nada).

## 7. Métricas de rendimiento (PROVISIONALES — se sustituyen cuando pases las reales)

Umbrales de costo por mensaje según tipo de campaña:

| Tipo | Bueno | Regular (vigilar) | Bajo |
|---|---|---|---|
| Local | ≤ $20 | $20.01 – $30 | > $30 |
| Nacional | ≤ $15 | $15.01 – $25 | > $25 |

- **Semanal:** el semáforo de la semana se calcula con su costo por resultado contra la tabla, más una alerta si los mensajes caen ≥ 30 % contra el promedio de las semanas anteriores del ciclo.
- **Mensual:** costo por mensaje del ciclo contra la tabla, ponderado con la tendencia (si las últimas dos semanas empeoran, baja un grado).
- Estos números son inventados a propósito; la estructura ya está lista para recibir los reales por tipo y, si hace falta, por paquete.

## 8. Notificaciones (propuesta técnica)

El requisito: viernes 2:00 pm, recordatorio en la computadora de trabajo a quien no haya capturado. Tres capas, de más simple a más robusta:

1. **Dentro de la app:** campana de notificaciones + banner rojo en el panel. Cero dependencias; funciona siempre que la app esté abierta.
2. **Notificación nativa del sistema operativo:** si la app queda abierta o minimizada en la bandeja, puede lanzar notificaciones de Windows (toast). Es la vía recomendada: la app de escritorio corre en segundo plano y el backend le avisa.
3. **WhatsApp (opcional a futuro):** el backend puede mandar el recordatorio por la API de WhatsApp Business; requiere alta del número y tiene costo por conversación. Lo dejaría para una segunda fase.

Recomendación: implementar 1 y 2 ahora; evaluar 3 después.

## 9. Decisiones propuestas en los puntos abiertos

**a) Credenciales de cliente repetidas — RESUELTO con tabla de cuentas.** Las credenciales no viven en el cliente: existe una tabla de **cuentas publicitarias** y los clientes se **vinculan** a ellas. Cada cuenta es única en el sistema (unicidad por huella, sin descifrar). Al capturar un cliente: si las credenciales no existen, se crea la cuenta y se vincula; si ya existen, el sistema muestra "esta cuenta ya está registrada (cliente X), ¿vincular también a este cliente?". Aceptar cubre el caso legítimo (mismo dueño, dos negocios, como Novedades y BTW Amigos); cancelar corrige el error de dedo. No hace falta autorización de la admin ni excepción alguna.

**b) Varias campañas del mismo cliente en el panel admin.** Propuesta: al seleccionar el cliente, la admin ve primero una **fila-resumen por campaña** (nombre, tipo, semáforo, costo actual) y un selector para entrar al detalle de una campaña; las gráficas mensual y semanal muestran la campaña seleccionada, con opción "Todas" que consolida la suma (útil cuando se cerró una campaña y se abrió otra dentro del mismo ciclo, que para el cliente fue una sola). El reporte formal del cliente **consolida por default** todas sus campañas del ciclo, que es como el cliente lo entiende.

**c) Borrado en cascada vs. historial.** Cuando el cliente "no renueva y se borra", se elimina todo (clientes → campañas → semanas → mensuales, en cascada). Cuando "no renueva pero se conserva", solo cambia de estado y se va al apartado de no renovados con su historial mensual intacto.

## 10. Easter egg del estado vacío (CM nuevo)

Estado vacío a la derecha: la leyenda "Aún no hay clientes ni campañas" acompañada de un **changuito dormido** (mascota INNquietus) en SVG animado. Interacciones escondidas:

- Al pasar el cursor, abre un ojo.
- Al hacer clic, se despierta y estira.
- Al **quinto clic**, confeti morado y la leyenda cambia a: **"¡Ya despertaste al INNquieto! Ahora despierta a tus clientes 🚀"** — y el botón "Agregar clientes" hace un pulso.
- Bonus discreto: si el CM escribe "innquietus" con el panel vacío abierto, todos los elementos de la interfaz hacen una pequeña ola.

## 11. Reglas duras del sistema (resumen para validación en backend)

1. Aislamiento total entre CMs; toda consulta filtra por `cm_id`.
2. Semana = sábado a viernes; semana cerrada = solo lectura.
3. Mensuales inmutables; captura manual solo si la campaña no tiene ninguno.
4. Cierre de ciclo a las 12:00 pm de la fecha de renovación: archiva mensual, borra semanales y observaciones de esa campaña, bloquea la campaña.
5. Campaña vencida: sin acciones posibles salvo confirmar renovación o baja.
6. Comparación: 2 meses (CM) / 3 meses (admin).
7. Bajas permanentes: doble confirmación + bitácora.
8. Migración de CM: mueve clientes, campañas, credenciales y semanales del ciclo abierto.
9. Sin usernames duplicados; contraseñas de app con bcrypt; credenciales de clientes cifradas.
10. Renombrar cliente o agregar uno nuevo se refleja de inmediato en el panel admin.

## 12. Pendientes que dependen de ti

- Las **métricas reales** por tipo de campaña (y si varían por paquete).
- Confirmación de la regla de credenciales duplicadas (punto 9-a).
- Confirmar que el ciclo de renovación es por campaña (fecha de renovación propia de cada campaña, como en el Excel) y no una fecha única por cliente.
- Nombre del sistema (¿seguimos con "Sistema INNterno"?).
