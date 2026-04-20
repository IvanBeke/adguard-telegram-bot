import logging
from datetime import timezone, datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.auth import restricted
from bot.config import QUICK_ACCESS_SERVICES, EMOJI_BLOCKED, EMOJI_ALLOWED
import bot.adguard as adguard
import bot.scheduler as scheduler

log = logging.getLogger(__name__)

TEMP_BLOCK_OPTIONS = [30, 60, 120, 240]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _service_name(service_id: str, all_services: list[dict]) -> str:
    for s in all_services:
        if s["id"] == service_id:
            return s["name"]
    return service_id.capitalize()


def _build_groups(all_services: list[dict]) -> list[tuple[str, list[dict]]]:
    """Devuelve lista de (group_id, [servicios]) ordenada alfabéticamente."""
    groups: dict[str, list[dict]] = {}
    for s in all_services:
        grp = s.get("group_id", "otros")
        groups.setdefault(grp, []).append(s)
    return sorted(groups.items())


def _toggle_keyboard(blocked_ids: set[str], all_services: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for sid in QUICK_ACCESS_SERVICES:
        name = _service_name(sid, all_services)
        emoji = EMOJI_BLOCKED if sid in blocked_ids else EMOJI_ALLOWED
        rows.append([InlineKeyboardButton(f"{emoji} {name}", callback_data=f"toggle:{sid}")])

    rows.append([InlineKeyboardButton("📄 Ver todos los servicios", callback_data="all_services:0")])
    rows.append([InlineKeyboardButton("🔄 Actualizar", callback_data="toggle_menu")])
    rows.append([InlineKeyboardButton("🏠 Menú principal", callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)


def _toggle_menu_text(blocked_ids: set[str]) -> str:
    return (
        "🔀 *Gestión de bloqueos*\n\n"
        f"{EMOJI_BLOCKED} = bloqueado  |  {EMOJI_ALLOWED} = permitido\n\n"
        "Pulsa un botón para cambiar su estado, o escribe el nombre de cualquier "
        "otro servicio para buscarlo y gestionarlo."
    )


# ---------------------------------------------------------------------------
# Menú de toggles
# ---------------------------------------------------------------------------

@restricted
async def toggle_menu_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        all_services = adguard.get_all_services()
        blocked_ids = set(adguard.get_blocked_services())
    except Exception as e:
        await q.edit_message_text(f"❌ Error al contactar con AdGuard: {e}")
        return

    await q.edit_message_text(
        _toggle_menu_text(blocked_ids),
        parse_mode="Markdown",
        reply_markup=_toggle_keyboard(blocked_ids, all_services),
    )


# ---------------------------------------------------------------------------
# Listado completo de servicios paginado por grupo
# ---------------------------------------------------------------------------

@restricted
async def all_services_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    page = int(q.data.split(":", 1)[1])
    await q.answer()

    try:
        all_services = adguard.get_all_services()
        blocked_ids = set(adguard.get_blocked_services())
    except Exception as e:
        await q.edit_message_text(f"❌ Error al contactar con AdGuard: {e}")
        return

    groups = _build_groups(all_services)
    total = len(groups)
    page = max(0, min(page, total - 1))
    grp_id, services = groups[page]

    rows = []
    for s in sorted(services, key=lambda x: x["name"]):
        emoji = EMOJI_BLOCKED if s["id"] in blocked_ids else EMOJI_ALLOWED
        rows.append([InlineKeyboardButton(
            f"{emoji} {s['name']}",
            callback_data=f"service_action:{s['id']}",
        )])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Anterior", callback_data=f"all_services:{page - 1}"))
    if page < total - 1:
        nav.append(InlineKeyboardButton("Siguiente ▶️", callback_data=f"all_services:{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton("🔙 Volver a bloqueos", callback_data="toggle_menu")])

    await q.edit_message_text(
        f"📄 *{grp_id.capitalize()}* — grupo {page + 1} de {total}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(rows),
    )


# ---------------------------------------------------------------------------
# Toggle de un servicio de acceso rápido
# ---------------------------------------------------------------------------

@restricted
async def toggle_service_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    service_id = q.data.split(":", 1)[1]
    await q.answer()

    try:
        all_services = adguard.get_all_services()
        name = _service_name(service_id, all_services)
    except Exception as e:
        await q.answer(f"❌ Error: {e}", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirmar", callback_data=f"confirm_toggle:{service_id}"),
            InlineKeyboardButton("❌ Cancelar", callback_data="toggle_menu"),
        ]
    ])
    blocked_ids = set(adguard.get_blocked_services())
    action = "desbloquear" if service_id in blocked_ids else "bloquear"
    await q.edit_message_text(
        f"¿Confirmas que quieres *{action}* el servicio *{name}*?",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


@restricted
async def confirm_toggle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    service_id = q.data.split(":", 1)[1]
    await q.answer()

    try:
        all_services = adguard.get_all_services()
        now_blocked = adguard.toggle_service(service_id)
        name = _service_name(service_id, all_services)
    except Exception as e:
        await q.edit_message_text(f"❌ Error al cambiar el estado: {e}")
        return

    if now_blocked:
        scheduled = scheduler.get_scheduled_unblock(service_id)
        rows = [
            [InlineKeyboardButton(
                f"⏱️ Desbloquear en {m} min",
                callback_data=f"tempblock:{service_id}:{m}"
            )]
            for m in TEMP_BLOCK_OPTIONS
        ]
        rows.append([InlineKeyboardButton("🔙 Volver", callback_data="toggle_menu")])
        sched_info = (
            "\n\n🕐 Ya tenía un desbloqueo automático programado: se ha cancelado."
            if scheduled else ""
        )
        scheduler.cancel_scheduled_unblock(service_id)
        await q.edit_message_text(
            f"🔴 *{name}* bloqueado correctamente.{sched_info}\n\n"
            "¿Quieres programar un desbloqueo automático?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(rows),
        )
    else:
        cancelled = scheduler.cancel_scheduled_unblock(service_id)
        extra = "\n⏱️ Desbloqueo automático cancelado." if cancelled else ""
        await q.edit_message_text(
            f"🟢 *{name}* desbloqueado correctamente.{extra}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Volver al menú de bloqueos", callback_data="toggle_menu")],
                [InlineKeyboardButton("🏠 Menú principal", callback_data="main_menu")],
            ]),
        )


# ---------------------------------------------------------------------------
# Bloqueo temporal
# ---------------------------------------------------------------------------

@restricted
async def temp_block_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    _, service_id, minutes_str = q.data.split(":")
    minutes = int(minutes_str)
    await q.answer()

    try:
        all_services = adguard.get_all_services()
        name = _service_name(service_id, all_services)
        run_at = scheduler.schedule_unblock(service_id, minutes, chat_id=q.message.chat_id)
        hora = run_at.astimezone().strftime("%H:%M")
    except Exception as e:
        await q.edit_message_text(f"❌ Error al programar desbloqueo: {e}")
        return

    await q.edit_message_text(
        f"⏱️ *{name}* se desbloqueará automáticamente a las *{hora}* "
        f"({minutes} min).\n\nRecibirás una notificación cuando ocurra.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancelar desbloqueo", callback_data=f"cancel_temp:{service_id}")],
            [InlineKeyboardButton("🔙 Volver", callback_data="toggle_menu")],
        ]),
    )


@restricted
async def cancel_temp_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    service_id = q.data.split(":", 1)[1]
    await q.answer()

    cancelled = scheduler.cancel_scheduled_unblock(service_id)
    try:
        all_services = adguard.get_all_services()
        name = _service_name(service_id, all_services)
    except Exception:
        name = service_id

    msg = (
        f"✅ Desbloqueo automático de *{name}* cancelado."
        if cancelled else
        f"ℹ️ No había ningún desbloqueo programado para *{name}*."
    )
    await q.edit_message_text(
        msg,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Volver", callback_data="toggle_menu")],
        ]),
    )


# ---------------------------------------------------------------------------
# Búsqueda de servicios por texto
# ---------------------------------------------------------------------------

@restricted
async def search_service_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip().lower()

    try:
        all_services = adguard.get_all_services()
        blocked_ids = set(adguard.get_blocked_services())
    except Exception as e:
        await update.message.reply_text(f"❌ Error al contactar con AdGuard: {e}")
        return

    matches = [
        s for s in all_services
        if query in s["id"].lower() or query in s["name"].lower()
    ]

    if not matches:
        await update.message.reply_text(
            f"🔍 No se encontraron servicios para *{query}*.\n\n"
            "Prueba con otro término o usa /menu para volver al menú.",
            parse_mode="Markdown",
        )
        return

    if len(matches) == 1:
        await _show_service_action(update, matches[0], blocked_ids)
        return

    rows = []
    for s in matches[:10]:
        emoji = EMOJI_BLOCKED if s["id"] in blocked_ids else EMOJI_ALLOWED
        rows.append([InlineKeyboardButton(
            f"{emoji} {s['name']}",
            callback_data=f"service_action:{s['id']}",
        )])
    rows.append([InlineKeyboardButton("🏠 Menú principal", callback_data="main_menu")])

    await update.message.reply_text(
        f"🔍 Se encontraron *{len(matches)}* servicios para *{query}*. Elige uno:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def _show_service_action(update: Update, service: dict, blocked_ids: set[str]):
    sid = service["id"]
    name = service["name"]
    is_blocked = sid in blocked_ids
    emoji = EMOJI_BLOCKED if is_blocked else EMOJI_ALLOWED
    action_label = "🟢 Desbloquear" if is_blocked else "🔴 Bloquear"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(action_label, callback_data=f"confirm_toggle:{sid}")],
        [InlineKeyboardButton("🏠 Menú principal", callback_data="main_menu")],
    ])
    text = (
        f"{emoji} *{name}*\n"
        f"Estado actual: {'bloqueado' if is_blocked else 'permitido'}"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)


@restricted
async def service_action_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    service_id = q.data.split(":", 1)[1]
    await q.answer()

    try:
        all_services = adguard.get_all_services()
        blocked_ids = set(adguard.get_blocked_services())
        service = next((s for s in all_services if s["id"] == service_id), None)
    except Exception as e:
        await q.edit_message_text(f"❌ Error: {e}")
        return

    if not service:
        await q.edit_message_text("❌ Servicio no encontrado.")
        return

    await _show_service_action(update, service, blocked_ids)
