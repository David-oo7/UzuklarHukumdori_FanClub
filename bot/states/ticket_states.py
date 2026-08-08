from aiogram.fsm.state import State, StatesGroup


class TicketStates(StatesGroup):
    """Foydalanuvchi yangi murojaat (ticket) yozayotgan holat."""

    waiting_for_message = State()


class AdminReplyStates(StatesGroup):
    """Admin muayyan ticketga javob yozayotgan holat."""

    waiting_for_reply = State()
