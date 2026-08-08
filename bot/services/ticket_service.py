"""
Django ORM bilan ishlovchi service qatlami.

aiogram asinxron ishlaydi, Django ORM esa (standart holatda) sinxron —
shuning uchun har bir ORM chaqiruvi `sync_to_async` bilan o'raladi.
"""

import logging
from typing import Optional

from asgiref.sync import sync_to_async

from support_bot.models import Ticket, TicketMessage, TelegramUser

logger = logging.getLogger("support_bot")


@sync_to_async
def get_or_create_telegram_user(
    telegram_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
) -> TelegramUser:
    user, created = TelegramUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
        },
    )
    if created:
        logger.info("Yangi foydalanuvchi qo'shildi: %s (%s)", telegram_id, username)
    else:
        # Ism/username o'zgargan bo'lishi mumkin — yangilab qo'yamiz.
        changed = False
        if user.username != username:
            user.username = username
            changed = True
        if user.first_name != first_name:
            user.first_name = first_name
            changed = True
        if user.last_name != last_name:
            user.last_name = last_name
            changed = True
        if changed:
            user.save(update_fields=["username", "first_name", "last_name"])
    return user


@sync_to_async
def create_ticket(telegram_user: TelegramUser, message_text: str) -> Ticket:
    ticket = Ticket.objects.create(
        telegram_user=telegram_user,
        message=message_text,
        status=Ticket.STATUS_OPEN,
    )
    logger.info("Yangi ticket yaratildi: #%s (user=%s)", ticket.id, telegram_user.telegram_id)
    return ticket


@sync_to_async
def get_ticket(ticket_id: int) -> Optional[Ticket]:
    return Ticket.objects.select_related("telegram_user").filter(id=ticket_id).first()


@sync_to_async
def get_latest_open_ticket(telegram_id: int) -> Optional[Ticket]:
    return (
        Ticket.objects.select_related("telegram_user")
        .filter(telegram_user__telegram_id=telegram_id)
        .exclude(status=Ticket.STATUS_CLOSED)
        .order_by("-created_at")
        .first()
    )


@sync_to_async
def get_user_tickets(telegram_id: int, limit: int = 5):
    return list(
        Ticket.objects.filter(telegram_user__telegram_id=telegram_id).order_by(
            "-created_at"
        )[:limit]
    )


@sync_to_async
def add_ticket_message(ticket: Ticket, sender_type: str, sender_telegram_id: int, text: str) -> TicketMessage:
    msg = TicketMessage.objects.create(
        ticket=ticket,
        sender_type=sender_type,
        sender_telegram_id=sender_telegram_id,
        message=text,
    )
    # Admin javob bergan bo'lsa, ticket "jarayonda" statusiga o'tadi.
    if sender_type == TicketMessage.SENDER_ADMIN and ticket.status == Ticket.STATUS_OPEN:
        ticket.status = Ticket.STATUS_IN_PROGRESS
        ticket.save(update_fields=["status", "updated_at"])
    return msg


@sync_to_async
def close_ticket(ticket: Ticket) -> Ticket:
    from django.utils import timezone

    ticket.status = Ticket.STATUS_CLOSED
    ticket.closed_at = timezone.now()
    ticket.save(update_fields=["status", "closed_at", "updated_at"])
    logger.info("Ticket yopildi: #%s", ticket.id)
    return ticket
