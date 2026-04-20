from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.auth import restricted
import bot.adguard as adguard
import bot.scheduler as scheduler


def _fmt_remaining(run_at: datetime) -> str:
    remaining = int((run_at - datetime.now(timezone.utc)).total_seconds())
    if remaining <= 0:
        return ""
    h, m = divmod(remaining // 60, 60)
    return f"⏱️ {h}h {m:02d}m" if h else f"⏱️ {m}m"


@restricted
async def blocked_list_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    try:
        all_services = adguard.get_all_services()
        blocked_ids = set(adguard.get_blocked_services())
        scheduled = {sid: run_at for sid, run_at in scheduler.get_all_scheduled()}
    except Exception as e:
        await q.edit_message_text(f"❌ Error al obtener datos de AdGuard: {e}")
        return

    name_map = {s["id"]: s["name"] for s in all_services}
    rows = []

    if not blocked_ids:
        rows.append([InlineKeyboardButton("✅ Ningún servicio bloqueado", callback_data="noop")])
    else:
        for sid in sorted(blocked_ids, key=lambda x: name_map.get(x, x)):
            name = name_map.get(sid, sid)
            run_at = scheduled.get(sid)
            label = f"🔴 {name}"
            if run_at:
                label += f" ({_fmt_remaining(run_at)})"
            rows.append([InlineKeyboardButton(label, callback_data=f"service_action:{sid}")])

    # Sección de desbloqueos programados
    pending = [(sid, run_at) for sid, run_at in scheduled.items() if sid in blocked_ids]
    if pending:
        rows.append([InlineKeyboardButton("── Desbloqueos programados ──", callback_data="noop")])
        for sid, run_at in sorted(pending, key=lambda x: x[1]):
            name = name_map.get(sid, sid)
            rows.append([InlineKeyboardButton(
                f"❌ Cancelar timer: {name} ({_fmt_remaining(run_at)})",
                callback_data=f"cancel_temp:{sid}",
            )])

    rows.append([InlineKeyboardButton("🔄 Actualizar", callback_data="blocked_list")])
    rows.append([InlineKeyboardButton("🏠 Menú principal", callback_data="main_menu")])

    total = len(blocked_ids)
    header = f"🔴 *Servicios bloqueados ({total})*" if total else "✅ *Sin servicios bloqueados*"
    await q.edit_message_text(
        header,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(rows),
    )
