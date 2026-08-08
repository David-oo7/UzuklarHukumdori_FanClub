from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_ticket_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    """Yangi ticket haqidagi admin xabari ostidagi tugmalar."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Javob berish", callback_data=f"reply_{ticket_id}"
                ),
                InlineKeyboardButton(
                    text="✅ Ticketni yopish", callback_data=f"close_{ticket_id}"
                ),
            ]
        ]
    )
