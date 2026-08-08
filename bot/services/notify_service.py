import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from bot import config
from bot.keyboards.inline import admin_ticket_keyboard
from support_bot.models import Ticket

logger = logging.getLogger("support_bot")


async def notify_admins_new_ticket(bot: Bot, ticket: Ticket) -> None:
    """Yangi ticket haqida barcha adminlarga xabar yuboradi."""
    user = ticket.telegram_user
    username_line = f"@{user.username}" if user.username else "—"
    full_name = " ".join(filter(None, [user.first_name, user.last_name])) or "—"

    text = (
        "🚨 YANGI SUPPORT MUROJAATI\n\n"
        f"🎫 Ticket: #{ticket.id}\n"
        f"👤 Foydalanuvchi: {full_name}\n"
        f"🔹 Username: {username_line}\n"
        f"🆔 Telegram ID: {user.telegram_id}\n\n"
        f"📝 Muammo:\n{ticket.message}"
    )

    keyboard = admin_ticket_keyboard(ticket.id)

    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, reply_markup=keyboard)
        except TelegramForbiddenError:
            logger.warning(
                "Admin %s botni bloklagan yoki u bilan chat boshlanmagan — xabar yuborilmadi.",
                admin_id,
            )
        except TelegramBadRequest as exc:
            logger.error("Admin %s ga xabar yuborishda xato: %s", admin_id, exc)
        except Exception:
            logger.exception("Admin %s ga xabar yuborishda kutilmagan xato.", admin_id)


async def safe_send_message(bot: Bot, chat_id: int, text: str, **kwargs) -> bool:
    """
    Telegram API xatolarini (masalan, foydalanuvchi botni bloklagan)
    ushlab, botning yiqilib qolishini oldini oladigan xavfsiz yuborish.
    """
    try:
        await bot.send_message(chat_id, text, **kwargs)
        return True
    except TelegramForbiddenError:
        logger.warning("Foydalanuvchi %s botni bloklagan — xabar yuborilmadi.", chat_id)
        return False
    except TelegramBadRequest as exc:
        logger.error("Xabar yuborishda xato (chat_id=%s): %s", chat_id, exc)
        return False
    except Exception:
        logger.exception("Xabar yuborishda kutilmagan xato (chat_id=%s).", chat_id)
        return False
