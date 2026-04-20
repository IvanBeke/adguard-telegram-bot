from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.auth import restricted
import bot.adguard as adguard


def _top_entries(lst: list[dict], n: int = 5) -> list[tuple[str, int]]:
    """Aplana la lista de TopArrayEntry y devuelve los N primeros."""
    result = []
    for entry in lst:
        for k, v in entry.items():
            result.append((k, int(v)))
    result.sort(key=lambda x: x[1], reverse=True)
    return result[:n]


@restricted
async def stats_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    try:
        data = adguard.get_stats()
    except Exception as e:
        await q.edit_message_text(f"❌ Error al obtener estadísticas: {e}")
        return

    total = data.get("num_dns_queries", 0)
    blocked = data.get("num_blocked_filtering", 0)
    safebrowsing = data.get("num_replaced_safebrowsing", 0)
    parental = data.get("num_replaced_parental", 0)
    safesearch = data.get("num_replaced_safesearch", 0)
    avg_ms = round(data.get("avg_processing_time", 0) * 1000, 2)

    pct = round(blocked / total * 100, 1) if total > 0 else 0

    top_queried = _top_entries(data.get("top_queried_domains", []))
    top_blocked = _top_entries(data.get("top_blocked_domains", []))
    top_clients = _top_entries(data.get("top_clients", []))

    def fmt_top(entries: list[tuple[str, int]]) -> str:
        if not entries:
            return "  _Sin datos_"
        return "\n".join(f"  `{i+1}.` {name} — {count}" for i, (name, count) in enumerate(entries))

    text = (
        "📊 *Estadísticas de AdGuard Home*\n\n"
        f"🔢 Total de consultas: *{total:,}*\n"
        f"🚫 Bloqueadas por filtros: *{blocked:,}* ({pct}%)\n"
        f"🦠 Bloqueadas (safebrowsing): *{safebrowsing:,}*\n"
        f"👨‍👩‍👧 Bloqueadas (parental): *{parental:,}*\n"
        f"🔍 Safe search aplicado: *{safesearch:,}*\n"
        f"⚡ Tiempo medio de respuesta: *{avg_ms} ms*\n\n"
        f"🌐 *Top 5 dominios consultados*\n{fmt_top(top_queried)}\n\n"
        f"🔴 *Top 5 dominios bloqueados*\n{fmt_top(top_blocked)}\n\n"
        f"💻 *Top 5 clientes*\n{fmt_top(top_clients)}"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Actualizar", callback_data="stats")],
        [InlineKeyboardButton("🏠 Menú principal", callback_data="main_menu")],
    ])
    await q.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
