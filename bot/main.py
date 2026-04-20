import logging
from telegram import BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from bot.config import TELEGRAM_BOT_TOKEN
import bot.scheduler as scheduler
from bot.handlers.menu import start, main_menu_callback
from bot.handlers.blocked_list import blocked_list_callback
from bot.handlers.toggle import (
    toggle_menu_callback,
    toggle_service_callback,
    confirm_toggle_callback,
    temp_block_callback,
    cancel_temp_callback,
    search_service_message,
    service_action_callback,
    all_services_callback,
)
from bot.handlers.stats import stats_callback
from bot.handlers.protection import (
    protection_callback,
    protection_pause_menu_callback,
    protection_pause_callback,
    protection_enable_callback,
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s — %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

_bot_instance = None


def get_bot():
    return _bot_instance


async def post_init(application):
    await application.bot.set_my_commands([
        BotCommand("menu", "Abrir el menú principal"),
    ])


def main():
    global _bot_instance

    scheduler.start()
    log.info("Scheduler iniciado.")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    _bot_instance = app.bot


    app.post_init = post_init

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))

    # Navegación principal
    app.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(blocked_list_callback, pattern="^blocked_list$"))

    # Toggles y gestión de servicios
    app.add_handler(CallbackQueryHandler(toggle_menu_callback, pattern="^toggle_menu$"))
    app.add_handler(CallbackQueryHandler(toggle_service_callback, pattern=r"^toggle:.+$"))
    app.add_handler(CallbackQueryHandler(confirm_toggle_callback, pattern=r"^confirm_toggle:.+$"))
    app.add_handler(CallbackQueryHandler(temp_block_callback, pattern=r"^tempblock:.+:.+$"))
    app.add_handler(CallbackQueryHandler(cancel_temp_callback, pattern=r"^cancel_temp:.+$"))
    app.add_handler(CallbackQueryHandler(all_services_callback, pattern=r"^all_services:\d+$"))
    app.add_handler(CallbackQueryHandler(service_action_callback, pattern=r"^service_action:.+$"))

    # Estadísticas
    app.add_handler(CallbackQueryHandler(stats_callback, pattern="^stats$"))

    # Protección global
    app.add_handler(CallbackQueryHandler(protection_callback, pattern="^protection$"))
    app.add_handler(CallbackQueryHandler(protection_pause_menu_callback, pattern="^protection_pause_menu$"))
    app.add_handler(CallbackQueryHandler(protection_pause_callback, pattern=r"^protection_pause:\d+$"))
    app.add_handler(CallbackQueryHandler(protection_enable_callback, pattern="^protection_enable$"))

    # Búsqueda por texto libre
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_service_message))

    log.info("Bot iniciado. Esperando mensajes...")
    app.run_polling(drop_pending_updates=True)

    scheduler.stop()


if __name__ == "__main__":
    main()
