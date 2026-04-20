from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from bot.config import ALLOWED_USER_IDS


def restricted(func):
    """Decorador que rechaza cualquier usuario no autorizado."""
    @wraps(func)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if user is None or user.id not in ALLOWED_USER_IDS:
            if update.message:
                await update.message.reply_text("⛔ No tienes permiso para usar este bot.")
            elif update.callback_query:
                await update.callback_query.answer("⛔ Acceso denegado.", show_alert=True)
            return
        return await func(update, ctx, *args, **kwargs)
    return wrapper
