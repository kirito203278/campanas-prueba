# Sistema de gestión de campañas (INNquietus)

Panel para CMs y administradores: clientes, campañas, captura semanal, resúmenes mensuales, semáforo de rendimiento, renovaciones y reportes en PDF.

## Probarlo en tu computadora

Solo necesitas **Docker**. Sin crear archivos ni configurar nada:

```bash
docker compose -f docker-compose.demo.yml up --build
```

La primera vez tarda unos minutos (compila la interfaz). Cuando veas `Uvicorn running`, abre **http://localhost:8001**
(el puerto es 8001 para que no choque con el sistema de clientes, que usa el 8000).

Se crean solas las tablas y unos datos de ejemplo: 19 clientes ficticios (16 activos y 3 en No renovados) con campañas, semanas capturadas, resúmenes de meses anteriores y observaciones.

| Usuario | Contraseña | Rol |
|---|---|---|
| `luz.admin` | `Admin-Demo-2026` | administrador |
| `lectura.demo` | `Lectura-Demo-2026` | administrador de solo lectura |
| `kori` | `Kori-Demo-2026` | CM (4 clientes, uno con la campaña vencida) |
| `saray` | `Saray-Demo-2026` | CM (3 clientes + 1 no renovado reciente) |
| `uriel` | `Uriel-Demo-2026` | CM |
| `alondra` | `Alondra-Demo-2026` | CM (incluye un no renovado de hace más de un año) |
| `luz.cm` | `Luz-Demo-2026` | CM |
| `fatima` | `Fatima-Demo-2026` | CM nueva, sin clientes (ver la pantalla de bienvenida) |

Qué mirar:

- **Semáforo de rendimiento:** campañas con costo por resultado bueno, regular y bajo, y una con caída de mensajes.
- **Comparar meses:** casi todas traen 1 a 3 meses anteriores (el CM compara hasta 2; el admin, hasta 3).
- **Campañas vencidas:** Gimnasio Fuerza Total y Boutique Aurora llegaron hoy a su fecha de renovación y piden decidir si renovó o no.
- **Clientes con 2 campañas:** Pizzería Don Marco y Joyería Brillante.
- **Cuenta compartida:** Novedades y BTW Amigos usan la misma cuenta publicitaria.
- **No renovados:** tres clientes con distinta antigüedad.
- **Reportes PDF** mensual y semanal, desde la ficha de cada cliente.

Para apagarlo: `Ctrl+C`. Para borrar todo y empezar limpio: `docker compose -f docker-compose.demo.yml down -v`.
Los datos de ejemplo se cargan solo cuando la base está vacía; si ya lo habías levantado antes, usa ese comando para recibir los nuevos.

> Las claves de este modo son de ejemplo y solo valen en tu computadora. No lo uses para producción.

Para desarrollo y despliegue, consulta [COMO_EJECUTAR.md](COMO_EJECUTAR.md).
