import logging
import os
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from bot.config import DB_PATH

log = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler(
    jobstores={"default": SQLAlchemyJobStore(url=DB_PATH)},
    timezone="Europe/Madrid",
)

# chat_id -> bot, para poder enviar notificaciones tras un reinicio
_notify_targets: dict[str, int] = {}


def start():
    os.makedirs("/app/data", exist_ok=True)
    _scheduler.start()


def stop():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)


# ---------------------------------------------------------------------------
# Función de nivel de módulo: serializable por APScheduler
# ---------------------------------------------------------------------------

async def _do_unblock(service_id: str, chat_id: int):
    import bot.adguard as adguard
    from bot.main import get_bot

    log.info("Desbloqueando automáticamente: %s", service_id)
    try:
        adguard.unblock_service(service_id)
    except Exception as e:
        log.error("Error al desbloquear %s: %s", service_id, e)
        return

    try:
        bot = get_bot()
        if bot and chat_id:
            await bot.send_message(
                chat_id=chat_id,
                text=f"🟢 *{service_id}* ha sido desbloqueado automáticamente.",
                parse_mode="Markdown",
            )
    except Exception as e:
        log.error("Error al enviar notificación de desbloqueo: %s", e)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def schedule_unblock(service_id: str, minutes: int, chat_id: int) -> datetime:
    """
    Programa el desbloqueo de un servicio tras X minutos.
    Cancela cualquier job previo para el mismo servicio.
    Devuelve el datetime en que se ejecutará.
    """
    job_id = f"unblock_{service_id}"
    if _scheduler.get_job(job_id):
        _scheduler.remove_job(job_id)

    run_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)

    _scheduler.add_job(
        _do_unblock,
        trigger="date",
        run_date=run_at,
        id=job_id,
        replace_existing=True,
        args=[service_id, chat_id],
    )
    return run_at


def cancel_scheduled_unblock(service_id: str) -> bool:
    """Cancela un desbloqueo programado. Devuelve True si había uno activo."""
    job_id = f"unblock_{service_id}"
    if _scheduler.get_job(job_id):
        _scheduler.remove_job(job_id)
        return True
    return False


def get_scheduled_unblock(service_id: str) -> datetime | None:
    """Devuelve cuándo se desbloqueará un servicio, o None si no hay job."""
    job = _scheduler.get_job(f"unblock_{service_id}")
    return job.next_run_time if job else None


def get_all_scheduled() -> list[tuple[str, datetime]]:
    """Devuelve todos los desbloqueos programados como lista de (service_id, run_at)."""
    result = []
    for job in _scheduler.get_jobs():
        if job.id.startswith("unblock_"):
            service_id = job.id[len("unblock_"):]
            result.append((service_id, job.next_run_time))
    return sorted(result, key=lambda x: x[1])
