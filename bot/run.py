"""
Support botni ishga tushirish uchun asosiy fayl.

Ishga tushirish:
    python -m bot.run

MUHIM: Bu faylni ishga tushirishdan oldin quyidagilarni bajaring:
1. .env faylini to'ldiring (BOT_TOKEN, ADMIN_IDS, DATABASE_URL, DJANGO_SETTINGS_MODULE)
2. Django migratsiyalarini bajaring:
       python manage.py makemigrations support_bot
       python manage.py migrate
"""

import asyncio
import logging

# DIQQAT: django_init eng birinchi import qilinishi shart — u Django'ni
# sozlab beradi, shundan keyingina support_bot.models kabi modullarni
# import qilish mumkin bo'ladi.
from bot import django_init  # noqa: F401
from bot import config
from bot.logging_setup import setup_logging
from bot.loader import create_bot, create_dispatcher

logger = logging.getLogger("support_bot")


async def main() -> None:
    setup_logging()
    logger.info("Support bot ishga tushmoqda...")

    try:
        config.validate_config()
    except RuntimeError as exc:
        logger.error(str(exc))
        raise SystemExit(str(exc))

    bot = create_bot()
    dp = create_dispatcher()

    # Handlerlarni shu yerda import qilamiz — django.setup() chaqirilgandan
    # keyin, chunki ular support_bot.models ni ishlatadi.
    from bot.handlers import admin_handlers, user_handlers

    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)

    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("Bot polling rejimida ishga tushdi. Adminlar: %s", config.ADMIN_IDS)

    try:
        await dp.start_polling(bot)
    except Exception:
        logger.exception("Bot ishlash jarayonida kutilmagan xato yuz berdi.")
        raise
    finally:
        await bot.session.close()
        logger.info("Bot to'xtatildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot foydalanuvchi tomonidan to'xtatildi.")
