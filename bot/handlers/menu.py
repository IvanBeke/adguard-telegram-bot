from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.auth import restricted

MAIN_MENU_TEXT = (
    "🏠 *Menú principal — AdGuard Home*\n\n"
    "Selecciona una opción:"
)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Servicios bloqueados", callback_data="blocked_list")],
        [InlineKeyboardButton("🔀 Gestionar bloqueos", callback_data="toggle_menu")],
        [InlineKeyboardButton("📊 Estadísticas", callback_data="stats")],
        [InlineKeyboardButton("🛡️ Protección global", callback_data="protection")],
    ])


@restricted
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        MAIN_MENU_TEXT,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


@restricted
async def main_menu_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        MAIN_MENU_TEXT,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )
