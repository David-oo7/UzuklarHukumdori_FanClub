import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.filters import IsAdmin
from bot.services import notify_service, ticket_service
from bot.states.ticket_states import AdminReplyStates
from support_bot.models import Ticket, TicketMessage

logger = logging.getLogger("support_bot")

router = Router(name="admin_handlers")


@router.callback_query(F.data.startswith("reply_"), IsAdmin())
async def cb_reply_to_ticket(callback: CallbackQuery, state: FSMContext) -> None:
    ticket_id = int(callback.data.split("_", 1)[1])
    ticket = await ticket_service.get_ticket(ticket_id)

    if ticket is None:
        await callback.answer("❌ Bunday ticket topilmadi.", show_alert=True)
        return

    if ticket.status == Ticket.STATUS_CLOSED:
        await callback.answer("⚠️ Bu ticket allaqachon yopilgan.", show_alert=True)
        return

    await state.set_state(AdminReplyStates.waiting_for_reply)
    await state.update_data(ticket_id=ticket.id)

    await callback.message.answer(
        f"💬 Ticket #{ticket.id} uchun javobingizni yozing:"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("close_"), IsAdmin())
async def cb_close_ticket(callback: CallbackQuery) -> None:
    ticket_id = int(callback.data.split("_", 1)[1])
    ticket = await ticket_service.get_ticket(ticket_id)

    if ticket is None:
        await callback.answer("❌ Bunday ticket topilmadi.", show_alert=True)
        return

    if ticket.status == Ticket.STATUS_CLOSED:
        await callback.answer("⚠️ Bu ticket allaqachon yopilgan.", show_alert=True)
        return

    ticket = await ticket_service.close_ticket(ticket)

    await notify_service.safe_send_message(
        callback.bot,
        ticket.telegram_user.telegram_id,
        f"✅ Ticket #{ticket.id} yopildi.",
    )

    await callback.message.answer(f"✅ Ticket #{ticket.id} muvaffaqiyatli yopildi.")
    await callback.answer()


@router.message(StateFilter(AdminReplyStates.waiting_for_reply), IsAdmin(), F.text)
async def process_admin_reply(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    ticket_id = data.get("ticket_id")
    await state.clear()

    ticket = await ticket_service.get_ticket(ticket_id)
    if ticket is None:
        await message.answer("❌ Bunday ticket topilmadi.")
        return

    if ticket.status == Ticket.STATUS_CLOSED:
        await message.answer(
            f"⚠️ Ticket #{ticket.id} allaqachon yopilgan, javob yuborilmadi."
        )
        return

    await ticket_service.add_ticket_message(
        ticket=ticket,
        sender_type=TicketMessage.SENDER_ADMIN,
        sender_telegram_id=message.from_user.id,
        text=message.text,
    )

    delivered = await notify_service.safe_send_message(
        message.bot,
        ticket.telegram_user.telegram_id,
        "💬 Support javobi\n\n"
        f"🎫 Ticket: #{ticket.id}\n\n"
        f"Admin:\n{message.text}",
    )

    if delivered:
        await message.answer(f"✅ Javobingiz #{ticket.id} ticket egasiga yuborildi.")
    else:
        await message.answer(
            f"⚠️ Javob saqlandi, lekin foydalanuvchiga yetkazib bo'lmadi "
            f"(botni bloklagan bo'lishi mumkin). Ticket: #{ticket.id}"
        )


@router.callback_query(F.data.startswith("reply_") | F.data.startswith("close_"))
async def cb_admin_action_denied(callback: CallbackQuery) -> None:
    """Admin bo'lmagan foydalanuvchi admin tugmasini bossa."""
    logger.warning(
        "Admin bo'lmagan foydalanuvchi admin funksiyasiga urindi: %s",
        callback.from_user.id,
    )
    await callback.answer("⛔ Sizda bu amalni bajarishga ruxsat yo'q.", show_alert=True)
