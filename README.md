# AdGuard Home Telegram Bot

Bot de Telegram para gestionar [AdGuard Home](https://github.com/AdguardTeam/AdGuardHome) desde el móvil. Desplegado mediante Docker.

## Funcionalidades

- **Servicios bloqueados** — listado de servicios bloqueados actualmente, clicables para desbloquear
- **Gestión de bloqueos** — toggles rápidos para Twitter, YouTube, Instagram y TikTok; búsqueda y gestión de cualquier servicio disponible; listado completo navegable por grupos
- **Bloqueos temporales** — bloquea un servicio durante 30, 60, 120 o 240 minutos con desbloqueo y notificación automáticos; persisten entre reinicios del contenedor
- **Estadísticas** — total de consultas, porcentaje bloqueado, top dominios y clientes
- **Protección global** — ver estado, pausar temporalmente o indefinidamente y reactivar
- **Autenticación** — solo los usuarios de Telegram autorizados pueden usar el bot

## Requisitos

- Docker y Docker Compose
- Una instancia de AdGuard Home accesible en red
- Un bot de Telegram creado con [@BotFather](https://t.me/BotFather)

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/IvanBeke/adguard-telegram-bot.git
cd adguard-telegram-bot
```

### 2. Configurar las variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con tus datos:

| Variable | Descripción | Requerida |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Token del bot obtenido de @BotFather | ✅ |
| `ALLOWED_USER_IDS` | IDs de Telegram autorizados, separados por coma | ✅ |
| `ADGUARD_URL` | URL base de AdGuard Home, sin `/control` | ✅ |
| `ADGUARD_USER` | Usuario de AdGuard Home | ✅ |
| `ADGUARD_PASSWORD` | Contraseña de AdGuard Home | ✅ |
| `ADGUARD_SYNC_URL` | URL de [adguard-sync](https://github.com/bakito/adguardhome-sync) | ❌ |

> **¿Cómo obtengo mi Telegram User ID?** Escríbele a [@userinfobot](https://t.me/userinfobot).


### 3. Desplegar el contenedor

#### Opción A: Construir localmente

```bash
docker compose up -d --build
```

#### Opción B: Usar imagen preconstruida

Puedes usar una imagen publicada en un registro (por ejemplo, Docker Hub o GitHub Container Registry) sin necesidad de clonar ni construir el código:

1. Crea un archivo `docker-compose.yaml` como este:

```yaml
services:
  adguard-telegram-bot:
    image: ghcr.io/ivanbeke/adguard-telegram-bot:latest
    container_name: adguard-telegram-bot
    restart: unless-stopped
    env_file:
      - .env
    environment:
      - TZ=Europe/Madrid
    volumes:
      - ./data:/app/data
```

2. Descarga o crea el archivo `.env` con tus variables (ver sección anterior).

3. Arranca el bot:

```bash
docker compose up -d
```

Los logs pueden consultarse con:

```bash
docker compose logs -f
```

## Uso

Escribe `/menu` en el chat del bot para abrir el menú principal. El bot también responde a mensajes de texto libres para buscar servicios por nombre.

## Estructura del proyecto

```
adguard-telegram-bot/
├── bot/
│   ├── main.py              # Entry point e inicialización
│   ├── config.py            # Variables de entorno
│   ├── adguard.py           # Cliente de la API de AdGuard Home
│   ├── auth.py              # Middleware de autenticación
│   ├── scheduler.py         # Gestor de bloqueos temporales (persistente)
│   └── handlers/
│       ├── menu.py          # Menú principal
│       ├── blocked_list.py  # Listado de servicios bloqueados
│       ├── toggle.py        # Toggles, búsqueda y gestión de servicios
│       ├── stats.py         # Estadísticas
│       └── protection.py    # Protección global
├── data/                    # Volumen Docker: base de datos de jobs
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

## Notas

- Los bloqueos temporales se almacenan en una base de datos SQLite en `./data/jobs.sqlite` y sobreviven a reinicios del contenedor gracias al volumen de Docker.
- Si se configura `ADGUARD_SYNC_URL`, el bot lanzará una sincronización en segundo plano tras cada cambio de estado, sin bloquear la respuesta al usuario.
- El bot registra automáticamente sus comandos en Telegram al arrancar, por lo que aparecerán en el autocompletado al escribir `/`.