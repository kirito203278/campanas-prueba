# Prompt de arranque para Claude Code

Copia y pega esto como primer mensaje en la pestaña Code, con los dos archivos
(especificacion_sistema_campanas.md y esquema_base_datos.sql) dentro de la
carpeta del proyecto.

---

Construye el sistema de gestión de campañas descrito en
`especificacion_sistema_campanas.md`, usando `esquema_base_datos.sql` como
esquema de la base de datos. Léelos completos antes de escribir código; las
reglas duras están en la sección 11 de la especificación y no son negociables.

Stack: PostgreSQL, backend en Python con FastAPI (API REST + jobs programados
con APScheduler), frontend web en React servido por el propio backend,
autenticación con JWT y bcrypt, cifrado AES-GCM para las credenciales de las
cuentas publicitarias (clave en variable de entorno), y generación del reporte
mensual en PDF con identidad de la agencia INNquietus.

Para desarrollo local usa docker-compose (Postgres + backend). Crea datos de
prueba (seed) tomados de la especificación: CMs KORI, SARAY, URIEL, ALONDRA,
FATIMA y LUZ (Luz con cuenta de CM y cuenta de admin), y algunos clientes de
ejemplo con campañas, semanas capturadas y un mensual histórico para poder ver
las gráficas y el reporte desde el primer día.

Trabaja por fases y detente al final de cada una para que yo la pruebe antes
de seguir:

1. Base de datos + migraciones + seed. Verifica que el esquema completo se
   crea sin errores.
2. Autenticación y roles: login, JWT, aislamiento por CM, alta de CM por la
   admin con generación de username y contraseña segura mostrada una sola vez
   con botón de copiar, reseteo de contraseñas, admins de solo lectura.
3. Panel del CM: lista de clientes, alta múltiple con vínculo a cuentas
   publicitarias (flujo de "esta cuenta ya existe, ¿vincular?"), borrado con
   doble confirmación, renombrado, dropdown de campañas, pestañas de datos
   semanales / observaciones / datos de la cuenta, bloqueo de semanas
   cerradas, comparación de hasta 2 meses, y la pantalla "Comenzar" del CM
   nuevo con el estado vacío y el easter egg del changuito (sección 10).
4. Jobs programados: cierre de semana (sábado 00:00), recordatorio de captura
   (viernes 14:00, notificación en la app + notificación nativa del sistema),
   cierre de ciclo a las 12:00 de la fecha de renovación con archivado del
   mensual, borrado de semanales y observaciones de esa campaña, bloqueo de
   campaña vencida y flujo de renovación / no renovación / apartado de no
   renovados.
5. Panel admin: CMs -> clientes -> campañas con fila-resumen y semáforo,
   tabla de solo lectura, gráfica mensual (3 meses) y semanal, vista
   consolidada "Todas" por cliente, migración de cartera al eliminar un CM.
6. Reporte mensual formal en PDF, consolidado por cliente, con comparación
   contra el mes anterior y presupuesto vs consumido, en lenguaje para el
   cliente final.

Las métricas de rendimiento de la sección 7 son provisionales: impleméntalas
parametrizadas (tabla o archivo de configuración) para sustituirlas sin tocar
código.
