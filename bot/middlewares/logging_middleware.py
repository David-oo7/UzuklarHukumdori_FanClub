import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

logger = logging.getLogger("support_bot")


class LoggingMiddleware(BaseMiddleware):
    """Har bir kelayotgan update'ni log qiladi va kutilmagan xatolarni ushlaydi."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Update):
            if event.message:
                logger.info(
                    "Xabar: user=%s text=%r",
                    event.message.from_user.id if event.message.from_user else "?",
                    event.message.text,
                )
            elif event.callback_query:
                logger.info(
                    "Callback: user=%s data=%r",
                    event.callback_query.from_user.id,
                    event.callback_query.data,
                )

        try:
            return await handler(event, data)
        except Exception:
            logger.exception("Handlerda kutilmagan xato yuz berdi.")
            return None
