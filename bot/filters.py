from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from bot import config


class IsAdmin(BaseFilter):
    """Faqat .env dagi ADMIN_IDS ro'yxatidagi foydalanuvchilar uchun."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        return bool(user) and user.id in config.ADMIN_IDS
