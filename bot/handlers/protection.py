from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.auth import restricted
import bot.adguard as adguard

PAUSE_OPTIONS = [5, 15, 30, 60]  # minutos


@restricted
async def protection_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    try:
        status = adguard.get_status()
    except Exception as e:
        await q.edit_message_text(f"❌ Error al obtener el estado: {e}")
        return

    enabled = status.get("protection_enabled", False)
    version = status.get("version", "desconocida")
    running = status.get("running", False)

    state_emoji = "🟢" if enabled else "🔴"
    state_text = "activa" if enabled else "pausada"

    rows = []
    if enabled:
        rows.append([InlineKeyboardButton("⏸️ Pausar protección", callback_data="protection_pause_menu")])
    else:
        rows.append([InlineKeyboardButton("▶️ Activar protección", callback_data="protection_enable")])

    rows.append([InlineKeyboardButton("🔄 Actualizar", callback_data="protection")])
    rows.append([InlineKeyboardButton("🏠 Menú principal", callback_data="main_menu")])

    text = (
        f"🛡️ *Protección global*\n\n"
        f"Estado: {state_emoji} *{state_text}*\n"
        f"Servidor DNS: {'✅ en ejecución' if running else '❌ detenido'}\n"
        f"Versión: `{version}`"
    )
    await q.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(rows))


@restricted
async def protection_pause_menu_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    rows = [
        [InlineKeyboardButton(f"⏱️ Pausar {m} min", callback_data=f"protection_pause:{m}")]
        for m in PAUSE_OPTIONS
    ]
    rows.append([InlineKeyboardButton("⏸️ Pausar indefinidamente", callback_data="protection_pause:0")])
    rows.append([InlineKeyboardButton("❌ Cancelar", callback_data="protection")])

    await q.edit_message_text(
        "⏸️ *¿Cuánto tiempo quieres pausar la protección?*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(rows),
    )


@restricted
async def protection_pause_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    minutes = int(q.data.split(":", 1)[1])
    await q.answer()

    try:
        duration_ms = minutes * 60 * 1000 if minutes > 0 else 0
        adguard.set_protection(enabled=False, duration_ms=duration_ms)
    except Exception as e:
        await q.edit_message_text(f"❌ Error al pausar la protección: {e}")
        return

    if minutes > 0:
        msg = f"⏸️ Protección pausada durante *{minutes} minutos*."
    else:
        msg = "⏸️ Protección pausada *indefinidamente*. Recuerda reactivarla."

    await q.edit_message_text(
        msg,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Reactivar ahora", callback_data="protection_enable")],
            [InlineKeyboardButton("🏠 Menú principal", callback_data="main_menu")],
        ]),
    )


@restricted
async def protection_enable_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    try:
        adguard.set_protection(enabled=True)
    except Exception as e:
        await q.edit_message_text(f"❌ Error al activar la protección: {e}")
        return

    await q.edit_message_text(
        "🟢 *Protección reactivada correctamente.*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛡️ Ver estado", callback_data="protection")],
            [InlineKeyboardButton("🏠 Menú principal", callback_data="main_menu")],
        ]),
    )
