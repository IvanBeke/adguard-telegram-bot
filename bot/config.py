import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]

ALLOWED_USER_IDS: set[int] = {
    int(uid.strip())
    for uid in os.environ["ALLOWED_USER_IDS"].split(",")
    if uid.strip()
}

ADGUARD_URL: str = os.environ["ADGUARD_URL"].rstrip("/")
ADGUARD_USER: str = os.environ["ADGUARD_USER"]
ADGUARD_PASSWORD: str = os.environ["ADGUARD_PASSWORD"]
ADGUARD_SYNC_URL: str = os.environ.get("ADGUARD_SYNC_URL", "").rstrip("/")

DB_PATH: str = "sqlite:////app/data/jobs.sqlite"

# Servicios de acceso rápido en el menú de toggles
QUICK_ACCESS_SERVICES: list[str] = ["twitter", "youtube", "instagram", "tiktok"]

# Emojis de estado
EMOJI_BLOCKED = "🔴"
EMOJI_ALLOWED = "🟢"
