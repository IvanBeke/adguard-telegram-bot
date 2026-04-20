import logging
import threading
import httpx
from bot.config import ADGUARD_URL, ADGUARD_USER, ADGUARD_PASSWORD, ADGUARD_SYNC_URL

log = logging.getLogger(__name__)

_AUTH = (ADGUARD_USER, ADGUARD_PASSWORD)
_BASE = f"{ADGUARD_URL}/control"


def _client() -> httpx.Client:
    return httpx.Client(auth=_AUTH, timeout=10)


def _sync() -> None:
    if not ADGUARD_SYNC_URL:
        return
    def _do():
        try:
            with httpx.Client(timeout=10) as c:
                c.post(f"{ADGUARD_SYNC_URL}/api/v1/sync")
        except Exception as e:
            log.warning("Error al sincronizar AdGuard: %s", e)
    threading.Thread(target=_do, daemon=True).start()


# ---------------------------------------------------------------------------
# Servicios bloqueados
# ---------------------------------------------------------------------------

def get_all_services() -> list[dict]:
    """Devuelve todos los servicios disponibles con id, nombre y group_id."""
    with _client() as c:
        r = c.get(f"{_BASE}/blocked_services/all")
        r.raise_for_status()
        return r.json().get("blocked_services", [])


def get_blocked_services() -> list[str]:
    """Devuelve la lista de IDs de servicios actualmente bloqueados."""
    with _client() as c:
        r = c.get(f"{_BASE}/blocked_services/get")
        r.raise_for_status()
        return r.json().get("ids", [])


def set_blocked_services(ids: list[str]) -> None:
    """Sobreescribe la lista completa de servicios bloqueados."""
    with _client() as c:
        r = c.put(
            f"{_BASE}/blocked_services/update",
            json={"ids": ids},
        )
        r.raise_for_status()
    _sync()


def block_service(service_id: str) -> None:
    current = get_blocked_services()
    if service_id not in current:
        set_blocked_services(current + [service_id])


def unblock_service(service_id: str) -> None:
    current = get_blocked_services()
    if service_id in current:
        set_blocked_services([s for s in current if s != service_id])


def toggle_service(service_id: str) -> bool:
    """Alterna el estado de un servicio. Devuelve True si queda bloqueado."""
    current = get_blocked_services()
    if service_id in current:
        set_blocked_services([s for s in current if s != service_id])
        return False
    else:
        set_blocked_services(current + [service_id])
        return True


# ---------------------------------------------------------------------------
# Protección global
# ---------------------------------------------------------------------------

def get_status() -> dict:
    with _client() as c:
        r = c.get(f"{_BASE}/status")
        r.raise_for_status()
        return r.json()


def set_protection(enabled: bool, duration_ms: int = 0) -> None:
    payload: dict = {"enabled": enabled}
    if not enabled and duration_ms > 0:
        payload["duration"] = duration_ms
    with _client() as c:
        r = c.post(f"{_BASE}/protection", json=payload)
        r.raise_for_status()
    _sync()


# ---------------------------------------------------------------------------
# Estadísticas
# ---------------------------------------------------------------------------

def get_stats() -> dict:
    with _client() as c:
        r = c.get(f"{_BASE}/stats")
        r.raise_for_status()
        return r.json()
