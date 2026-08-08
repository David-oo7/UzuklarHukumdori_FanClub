"""
Support botning konfiguratsiyasi.

Barcha maxfiy ma'lumotlar (.env) fayldan o'qiladi.
Mavjud Django loyihasining nomiga qarab DJANGO_SETTINGS_MODULE ni
o'zgartirishni unutmang (pastga qarang).
"""

import os

from dotenv import load_dotenv

load_dotenv()

# --- Telegram ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

_admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = {
    int(admin_id.strip())
    for admin_id in _admin_ids_raw.split(",")
    if admin_id.strip().isdigit()
}

# --- Database (Django uchun ishlatiladi, PostgreSQL) ---
DATABASE_URL = os.getenv("DATABASE_URL", "")

# --- Django integratsiyasi ---
# MUHIM: Bu qiymatni o'zingizning mavjud Django loyihangizning
# settings moduliga moslang. Masalan, agar loyihangiz "myproject2"
# deb nomlangan bo'lsa (manage.py bilan bir joyda joylashgan),
# quyidagicha bo'ladi:
DJANGO_SETTINGS_MODULE = os.getenv("DJANGO_SETTINGS_MODULE", "myproject2.settings")

# --- Ticketlar ro'yxatida ko'rsatiladigan oxirgi nechta ticket ---
MY_TICKETS_LIMIT = int(os.getenv("MY_TICKETS_LIMIT", "5"))

# --- Loglar ---
LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_FILE = os.path.join(LOG_DIR, "bot.log")


def validate_config() -> None:
    """Botni ishga tushirishdan oldin konfiguratsiyani tekshiradi."""
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not ADMIN_IDS:
        missing.append("ADMIN_IDS")
    if not DATABASE_URL:
        missing.append("DATABASE_URL")

    if missing:
        raise RuntimeError(
            ".env faylida quyidagi majburiy o'zgaruvchilar to'ldirilmagan: "
            + ", ".join(missing)
        )
