# Cómo ejecutar el sistema

Ruta del proyecto: `/home/kiri/Documentos/sistema-campanas`

## Índice

1. [Requisitos](#1-requisitos)
2. [Primera vez (después de clonar el repo)](#2-primera-vez-después-de-clonar-el-repo)
3. [Levantar el sistema](#3-levantar-el-sistema) — elige Opción A o B
4. [Sembrar datos de prueba](#4-sembrar-datos-de-prueba)
5. [Ver la base de datos (Adminer)](#5-ver-la-base-de-datos-adminer)
6. [Generar el PDF/TXT de credenciales](#6-generar-el-pdftxt-de-credenciales)
7. [Apagar](#7-apagar)
8. [Otros comandos útiles](#8-otros-comandos-útiles)
9. [Desplegar en Render (gratis)](#9-desplegar-en-render-gratis)
10. [Respaldar la base de producción](#10-respaldar-la-base-de-producción)

---

## 1. Requisitos

- Docker + Docker Compose
- Node.js v20 o superior

---

## 2. Primera vez (después de clonar el repo)

```bash
cd /home/kiri/Documentos/sistema-campanas
cp .env.example .env
```

Genera valores reales para los secretos (los de `.env.example` son placeholders inválidos a propósito). Corre esto y pega cada resultado en el `.env` que acabas de crear:

```bash
# para AES_KEY_B64=
python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"

# para JWT_SECRET= (corre esto DOS veces: una para JWT_SECRET, otra para HUELLA_SECRET — deben ser distintos)
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Instala las dependencias del frontend:

```bash
cd /home/kiri/Documentos/sistema-campanas/frontend
npm install
```

---

## 3. Levantar el sistema

Dos formas de correrlo. Usa **A** si solo vas a usar/presentar la app; usa **B** si vas a editar el frontend.

### Opción A — Un solo comando

El backend sirve el frontend ya compilado, en el mismo proceso y puerto.

```bash
cd /home/kiri/Documentos/sistema-campanas
cd frontend && npm run build && cd ..
docker compose up -d
```

**Abre → http://localhost:8000**

> Solo repites el `npm run build` si vuelves a tocar código del frontend. `docker compose up -d` lo puedes correr las veces que quieras, no hace nada si ya está arriba.

### Opción B — Modo desarrollo (dos terminales)

**Terminal 1:**
```bash
cd /home/kiri/Documentos/sistema-campanas
docker compose up -d
```

**Terminal 2:**
```bash
cd /home/kiri/Documentos/sistema-campanas/frontend
npm run dev
```

**Abre → http://localhost:5173** (recarga sola cada vez que guardas un cambio en el frontend)

---

Con cualquiera de las dos opciones, confirma que no haya errores:

```bash
cd /home/kiri/Documentos/sistema-campanas
docker compose ps
docker compose logs backend --tail 30
```

---

## 4. Sembrar datos de prueba

Solo la primera vez, o después de resetear la base:

```bash
cd /home/kiri/Documentos/sistema-campanas
docker compose exec backend python -m app.seed
```

Genera `backend/seed_credentials.txt` con usuario/contraseña de cada cuenta (CMs + admin). Archivo local, no se sube a git.

Inicia sesión con cualquiera de esas cuentas en la URL que abriste en el paso 3.

---

## 5. Ver la base de datos (Adminer)

**No es un comando aparte.** Adminer ya está incluido en `docker-compose.yml` y arranca solo con el `docker compose up -d` del paso 3 (opción A o B, cualquiera de las dos).

**Abre → http://localhost:8080**

Datos de conexión:

| Campo | Valor |
|---|---|
| Sistema | PostgreSQL |
| Servidor | `db` |
| Usuario | `campanas` |
| Contraseña | `campanas` |
| Base de datos | `campanas` |

### Alternativa por terminal (sin instalar nada)

```bash
cd /home/kiri/Documentos/sistema-campanas
docker compose exec db psql -U campanas -d campanas
```

Dentro de `psql`:
- `\dt` — listar tablas
- `\d nombre_tabla` — ver estructura de una tabla
- `SELECT * FROM usuarios;` — consultar datos
- `\q` — salir

### Alternativa con app de escritorio

DBeaver, TablePlus o pgAdmin, conectando a `localhost:5433` con los mismos datos de la tabla de arriba.

---

## 6. Generar el PDF/TXT de credenciales

Para entregar usuario/contraseña de cada CM y admin:

```bash
cd /home/kiri/Documentos/sistema-campanas
docker compose exec backend python generar_credenciales_entrega.py
```

Genera `backend/credenciales_entrega.pdf` y `.txt`. Tampoco se suben a git — son secretos.

---

## 7. Apagar

```bash
cd /home/kiri/Documentos/sistema-campanas

docker compose down        # apaga backend + base de datos + Adminer, conserva los datos
docker compose down -v     # apaga TODO y BORRA los datos de la base (irreversible)
```

Si usaste la opción B, además presiona `Ctrl+C` en la terminal donde corre `npm run dev`.

---

## 8. Otros comandos útiles

**Aplicar migraciones nuevas a mano** (normalmente se aplican solas al reiniciar el contenedor):

```bash
cd /home/kiri/Documentos/sistema-campanas
docker compose exec backend python -m app.migrations.run_migrations
```

**Correr los jobs programados sin esperar al cron real** (cierre de semana, recordatorio, cierre de ciclo, purga de no renovados):

```bash
cd /home/kiri/Documentos/sistema-campanas
docker compose exec backend python -m app.jobs.cierre_semana
docker compose exec backend python -m app.jobs.recordatorio
docker compose exec backend python -m app.jobs.cierre_ciclo
docker compose exec backend python -m app.jobs.purga_no_renovados
```

---

## 9. Desplegar en Render (gratis)

Ruta elegida por presupuesto cero: **Render** (plan gratis del servicio web, no pide tarjeta) + una base de datos Postgres gratis externa (**Neon** o **Supabase**, tampoco piden tarjeta). El dominio se queda comprado donde ya esté (p. ej. HostGator) y solo se apunta hacia Render.

**Limitación conocida y cómo se resolvió**: el plan gratis de Render "duerme" el servicio tras ~15 min sin tráfico. Si duerme justo a la hora de un job programado (cierre de semana, recordatorio, etc.), ese job no dispara solo. Por eso el backend expone `POST /api/jobs/run/{nombre}` (protegido con un secreto), para que un cron externo gratis lo llame a la hora exacta — la llamada misma despierta el proceso y corre el job en el mismo golpe. El scheduler interno (APScheduler) se queda activo igual, como respaldo para cuando el servicio ya está despierto por otra razón.

### Pasos (todos se hacen en paneles web, no hay comando de Claude Code para esto)

1. **Base de datos** — crea un proyecto Postgres gratis en [Neon](https://neon.tech) o [Supabase](https://supabase.com) (sin tarjeta). Copia el connection string; agrégale `?sslmode=require` al final si no lo trae ya.

2. **Render** — crea cuenta en [render.com](https://render.com) (sin tarjeta para el plan gratis de "Web Service"). "New" → "Web Service" → conecta el repo de GitHub (una vez esté subido). Configuración:
   - **Runtime**: Docker
   - **Dockerfile path**: `backend/Dockerfile`
   - **Docker build context**: `.` (raíz del repo)

3. **Variables de entorno en Render** (sección "Environment"): genera valores nuevos con los comandos de la sección 2 de este documento — **nunca reuses los de desarrollo**.

   | Variable | Valor |
   |---|---|
   | `DATABASE_URL` | el connection string de Neon/Supabase (con `postgresql+psycopg2://` al inicio, no `postgresql://`) |
   | `JWT_SECRET` | nuevo, generado |
   | `AES_KEY_B64` | nuevo, generado |
   | `HUELLA_SECRET` | nuevo, generado |
   | `JOBS_SECRET` | nuevo, generado |
   | `CORS_ORIGINS` | `https://tudominio.com` (el dominio final) |
   | `TZ` | `America/Mazatlan` |

   No pongas `RELOAD` (esa es solo para desarrollo local).

4. **Dominio** — en Render, agrega el dominio propio al servicio; te va a dar un registro (CNAME o A) para configurar en el DNS de HostGator. El HTTPS lo emite Render solo, sin pasos extra.

5. **Cron externo para los jobs** — crea cuenta gratis en [cron-job.org](https://cron-job.org) (sin tarjeta) y configura 4 tareas, todas con método `POST`, header `X-Jobs-Secret: <el valor que pusiste en Render>`, en la zona horaria de México (o convertida a UTC si el sitio no deja elegir zona):

   | URL | Horario |
   |---|---|
   | `https://tudominio.com/api/jobs/run/cierre_semana` | Sábados 00:05 |
   | `https://tudominio.com/api/jobs/run/recordatorio_captura` | Viernes 14:00 |
   | `https://tudominio.com/api/jobs/run/cierre_ciclo` | Diario 12:00 |
   | `https://tudominio.com/api/jobs/run/purga_no_renovados` | Diario 12:10 |

6. **Opcional** — un ping cada 10-14 min con [UptimeRobot](https://uptimerobot.com) (gratis) a la URL pública, para que responda rápido casi siempre en vez de esperar el "despertar en frío".

---

## 10. Respaldar la base de producción

Neon (plan gratis) tiene una ventana de recuperación corta si algo se borra por error — vale la pena hacer un respaldo manual de vez en cuando (una vez al mes es razonable). No hace falta instalar nada: se usa una imagen de Docker desechable con la misma versión de Postgres que Neon (revisa qué versión te muestra Neon en su dashboard si cambia con el tiempo).

```bash
docker run --rm postgres:18-alpine pg_dump "<tu DATABASE_URL de Neon, con postgresql:// normal, no +psycopg2>" > respaldo-$(date +%Y-%m-%d).sql
```

Esto genera un archivo `.sql` con todo (estructura + datos) en tu carpeta actual. Guárdalo en un lugar seguro (no lo subas a git — son datos reales de clientes). Para restaurarlo algún día, sería:

```bash
docker run --rm -i postgres:18-alpine psql "<connection string de la base destino>" < respaldo-2026-07-29.sql
```
