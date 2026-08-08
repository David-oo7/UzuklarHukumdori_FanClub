import logging

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot import config
from bot.keyboards.reply import (
    BTN_HELP,
    BTN_MY_TICKETS,
    BTN_NEW_TICKET,
    main_menu_keyboard,
)
from bot.services import notify_service, ticket_service
from bot.filters import IsAdmin
from bot.states.ticket_states import TicketStates
from support_bot.models import Ticket, TicketMessage

logger = logging.getLogger("support_bot")

router = Router(name="user_handlers")


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()

    user = message.from_user
    await ticket_service.get_or_create_telegram_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    text = (
        f"👋 Salom, {user.first_name or 'foydalanuvchi'}!\n\n"
        "🤖 Support botga xush kelibsiz.\n\n"
        "Siz bu bot orqali sayt bilan bog'liq muammolar haqida "
        "support jamoasiga murojaat qilishingiz mumkin."
    )
    await message.answer(text, reply_markup=main_menu_keyboard())
    logger.info("Foydalanuvchi /start bosdi: %s", user.id)


@router.message(F.text == BTN_HELP)
async def btn_help(message: Message, state: FSMContext) -> None:
    await state.clear()
    text = (
        "ℹ️ Yordam\n\n"
        f"{BTN_NEW_TICKET} — support jamoasiga yangi murojaat yuborish uchun.\n"
        f"{BTN_MY_TICKETS} — yuborgan murojaatlaringiz ro'yxati va statusi.\n\n"
        "Agar sizda ochiq (yopilmagan) murojaating bo'lsa, shunchaki yozgan "
        "har qanday xabaringiz avtomatik ravishda o'sha murojaatga "
        "qo'shiladi va support jamoasiga yetkaziladi."
    )
    await message.answer(text)


@router.message(F.text == BTN_NEW_TICKET)
async def btn_new_ticket(message: Message, state: FSMContext) -> None:
    await state.set_state(TicketStates.waiting_for_message)
    await message.answer(
        "📝 Muammoingizni batafsil yozib yuboring.\n\n"
        "Xabaringizni yuborishingiz bilan support jamoasiga ticket sifatida yetkaziladi."
    )


@router.message(StateFilter(TicketStates.waiting_for_message), F.text)
async def process_new_ticket(message: Message, state: FSMContext) -> None:
    await state.clear()

    user = message.from_user
    telegram_user = await ticket_service.get_or_create_telegram_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    ticket = await ticket_service.create_ticket(telegram_user, message.text)

    await message.answer(
        "✅ Murojaatingiz qabul qilindi!\n\n"
        f"🎫 Ticket: #{ticket.id}\n\n"
        "Support jamoasi tez orada murojaatingizni ko'rib chiqadi.",
        reply_markup=main_menu_keyboard(),
    )

    await notify_service.notify_admins_new_ticket(message.bot, ticket)


@router.message(F.text == BTN_MY_TICKETS)
async def btn_my_tickets(message: Message, state: FSMContext) -> None:
    await state.clear()
    tickets = await ticket_service.get_user_tickets(message.from_user.id, limit=5)

    if not tickets:
        await message.answer(
            "Sizda hali birorta ham murojaat mavjud emas.\n\n"
            f"Yangi murojaat yuborish uchun \"{BTN_NEW_TICKET}\" tugmasini bosing."
        )
        return

    lines = []
    for ticket in tickets:
        created = ticket.created_at.strftime("%d.%m.%Y %H:%M")
        lines.append(
            f"🎫 #{ticket.id}\n📅 {created}\n📌 {ticket.status_display_uz()}"
        )

    text = "📋 Sizning oxirgi murojaatlaringiz:\n\n" + "\n\n".join(lines)
    await message.answer(text)


@router.message(StateFilter(None), ~IsAdmin(), F.text)
async def fallback_text_as_reply(message: Message, state: FSMContext) -> None:
    """
    Foydalanuvchi maxsus tugmalardan foydalanmasdan oddiy xabar yozsa:
    agar uning ochiq (yopilmagan) ticketi bo'lsa, xabar o'sha ticketga
    javob sifatida qo'shiladi va adminlarga yuboriladi.
    Aks holda, "Murojaat yuborish" tugmasidan foydalanish taklif qilinadi.
    """
    ticket = await ticket_service.get_latest_open_ticket(message.from_user.id)

    if ticket is None:
        await message.answer(
            "Sizda hozircha ochiq murojaat yo'q.\n\n"
            f"Yangi murojaat yuborish uchun \"{BTN_NEW_TICKET}\" tugmasini bosing.",
            reply_markup=main_menu_keyboard(),
        )
        return

    if ticket.status == Ticket.STATUS_CLOSED:
        await message.answer(
            f"🎫 #{ticket.id} raqamli murojaatingiz allaqachon yopilgan.\n\n"
            f"Yangi murojaat yuborish uchun \"{BTN_NEW_TICKET}\" tugmasini bosing."
        )
        return

    await ticket_service.add_ticket_message(
        ticket=ticket,
        sender_type=TicketMessage.SENDER_USER,
        sender_telegram_id=message.from_user.id,
        text=message.text,
    )

    await message.answer(f"✅ Xabaringiz #{ticket.id} raqamli murojaatga qo'shildi.")

    forward_text = (
        f"✉️ Foydalanuvchidan yangi xabar (Ticket #{ticket.id})\n\n"
        f"👤 {message.from_user.full_name}\n"
        f"🆔 {message.from_user.id}\n\n"
        f"{message.text}"
    )
    for admin_id in config.ADMIN_IDS:
        await notify_service.safe_send_message(message.bot, admin_id, forward_text)
