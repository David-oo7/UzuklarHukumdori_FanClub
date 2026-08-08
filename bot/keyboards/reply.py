from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_NEW_TICKET = "📝 Murojaat yuborish"
BTN_MY_TICKETS = "📋 Mening murojaatlarim"
BTN_HELP = "ℹ️ Yordam"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Botning asosiy pastki menyusi."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_NEW_TICKET)],
            [KeyboardButton(text=BTN_MY_TICKETS), KeyboardButton(text=BTN_HELP)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Bo'limni tanlang...",
    )
