import json
import re
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import ChatMessage

ROOM_GROUP_NAME = 'muhokama_xonasi'

ALLOWED_STICKERS = {
    '💍', '⚔️', '🏹', '🪓', '🌳', '🏔️', '🐴', '🔥',
    '✨', '🛡️', '🌙', '⭐', '👑', '🗡️', '🦅', '🌲',
}


def _normalize(text):
    """Matnni taqqoslash uchun bir xil ko'rinishga keltiradi."""
    if not text:
        return ''
    t = str(text).casefold()
    # Apostrof va o'xshash belgilarni bir xillashtirish
    t = t.replace('ʻ', "'").replace('ʼ', "'").replace('`', "'").replace('´', "'")
    t = t.replace('‘', "'").replace('’', "'")
    # Faqat harf/raqam/bo'shliq/apostrof qoldirish
    t = re.sub(r"[^\w\s']", ' ', t, flags=re.UNICODE)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def _text_matches_banned(text, banned_words):
    """
    Matnda taqiqlangan so'z bor-yo'qligini tekshiradi.
    - Katta-kichik farq qilmaydi
    - Tinish belgilari e'tiborsiz
    - So'z ichida ham topadi (masalan: "yomonsoz" ichida "yomon")
    - Bo'shliq bilan ajratilgan yozuvlar ham (y o m o n)
    """
    if not text or not banned_words:
        return False

    norm_text = _normalize(text)
    if not norm_text:
        return False

    compact = re.sub(r"[\s']+", '', norm_text)
    raw_lower = str(text).casefold()

    for raw in banned_words:
        if not raw:
            continue
        w = _normalize(raw)
        if not w or len(w) < 2:
            # Juda qisqa so'zlarni (1 harf) o'tkazib yuboramiz — false positive ko'p
            continue

        w_compact = re.sub(r"[\s']+", '', w)

        # 1) Normal matnda substring
        if w in norm_text:
            return True
        # 2) Bo'shliqsiz (bypass: "s o z")
        if w_compact and w_compact in compact:
            return True
        # 3) Asl matnda (tinish belgilari bilan)
        if w in raw_lower or raw.casefold() in raw_lower:
            return True
        # 4) Har bir token
        for token in norm_text.split():
            if w == token or (len(w) >= 3 and w in token):
                return True

    return False


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Avval accept — aks holda brauzer faqat "Aloqa uzildi" ko'radi
        await self.accept()

        user = self.scope.get('user')
        if user is None or user.is_anonymous:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'code': 'auth',
                'error': "Chat uchun avval tizimga kiring (Kirish).",
            }))
            await self.close(code=4001)
            return

        try:
            if await self._is_user_banned():
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'code': 'banned',
                    'error': "Sizning hisobingiz bloklangan.",
                }))
                await self.close(code=4003)
                return
        except Exception:
            pass

        await self.channel_layer.group_add(ROOM_GROUP_NAME, self.channel_name)
        await self.send(text_data=json.dumps({
            'type': 'status',
            'status': 'connected',
            'error': '',
        }))

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(ROOM_GROUP_NAME, self.channel_name)
        except Exception:
            pass

    async def receive(self, text_data):
        user = self.scope.get('user')
        if user is None or user.is_anonymous:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'code': 'auth',
                'error': "Chat uchun avval tizimga kiring.",
            }))
            return

        try:
            data = json.loads(text_data)
        except (TypeError, ValueError):
            return

        name = user.username
        msg_type = data.get('type', 'text')

        if msg_type == 'sticker':
            sticker = (data.get('sticker') or '').strip()
            if sticker not in ALLOWED_STICKERS:
                return
            message = await self.save_message(name, message_type=ChatMessage.STICKER, sticker=sticker)
            payload = {
                'type': 'chat_message',
                'name': message.name,
                'message_type': 'sticker',
                'sticker': message.sticker,
                'created_at': message.created_at.strftime('%H:%M'),
            }
        else:
            text = (data.get('text') or data.get('message') or '').strip()[:500]
            if not text:
                return

            # Taqiqlangan so'z tekshiruvi — majburiy
            if await self._contains_banned_word(text):
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'code': 'banned_word',
                    'error': "Xabaringizda taqiqlangan so'z bor. Iltimos, boshqacha yozing.",
                }))
                return

            message = await self.save_message(name, message_type=ChatMessage.TEXT, text=text)
            payload = {
                'type': 'chat_message',
                'name': message.name,
                'message_type': 'text',
                'text': message.text,
                'created_at': message.created_at.strftime('%H:%M'),
            }

        await self.channel_layer.group_send(ROOM_GROUP_NAME, payload)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'name': event.get('name'),
            'message_type': event.get('message_type', 'text'),
            'text': event.get('text', ''),
            'image_url': event.get('image_url', ''),
            'sticker': event.get('sticker', ''),
            'created_at': event.get('created_at'),
        }))

    @database_sync_to_async
    def save_message(self, name, message_type='text', text='', sticker=''):
        return ChatMessage.objects.create(
            name=name or 'Mehmon',
            message_type=message_type,
            text=text,
            sticker=sticker,
        )

    @database_sync_to_async
    def _is_user_banned(self):
        user = self.scope.get('user')
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        try:
            from .models import UserProfile
            return UserProfile.objects.filter(user=user, is_banned=True).exists()
        except Exception:
            return False

    @database_sync_to_async
    def _contains_banned_word(self, text):
        """
        Admin panelidagi faol taqiqlangan so'zlarni tekshiradi.
        Jadval yo'q yoki bo'sh bo'lsa — False (bloklamaydi).
        """
        from .models import BannedWord

        try:
            words = list(
                BannedWord.objects.filter(is_active=True)
                .values_list('word', flat=True)
            )
        except Exception:
            # Jadval hali migrate qilinmagan bo'lishi mumkin
            return False

        # Bo'sh qatorlar va takrorlarni tozalash
        words = [w.strip() for w in words if w and str(w).strip()]
        if not words:
            return False

        return _text_matches_banned(text, words)


class TicketChatConsumer(AsyncWebsocketConsumer):
    """Support ticket ichidagi real-time chat."""

    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.ticket_id = self.scope['url_route']['kwargs']['ticket_id']
        self.group_name = f'ticket_{self.ticket_id}'

        allowed = await self._can_access(user, self.ticket_id)
        if not allowed:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'status',
            'status': 'connected',
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            return
        try:
            data = json.loads(text_data or '{}')
        except (ValueError, TypeError):
            return

        body = (data.get('body') or '').strip()[:3000]
        if not body:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': "Xabar bo'sh bo'lmasligi kerak.",
            }))
            return

        # Closed ticketga yozishni taqiqlash
        ticket = await self._get_ticket(self.ticket_id)
        if not ticket:
            return
        if ticket.status == 'closed':
            from .models import user_can_manage_tickets as _uct
            if not _uct(user):
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'error': "Ticket yopilgan — yangi xabar yuborib bo'lmaydi.",
                }))
                return

        msg = await self._save_message(user, self.ticket_id, body)
        if not msg:
            return

        payload = {
            'type': 'ticket_message',
            'id': msg['id'],
            'body': msg['body'],
            'author': msg['author'],
            'is_staff_reply': msg['is_staff_reply'],
            'created_at': msg['created_at'],
            'attachment_url': msg.get('attachment_url') or '',
        }
        await self.channel_layer.group_send(self.group_name, payload)

    async def ticket_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def _can_access(self, user, ticket_id):
        from .models import SupportTicket, user_can_manage_tickets
        try:
            t = SupportTicket.objects.get(pk=ticket_id)
        except SupportTicket.DoesNotExist:
            return False
        if user_can_manage_tickets(user):
            return True
        return t.user_id == user.id

    @database_sync_to_async
    def _get_ticket(self, ticket_id):
        from .models import SupportTicket
        try:
            return SupportTicket.objects.get(pk=ticket_id)
        except SupportTicket.DoesNotExist:
            return None

    @database_sync_to_async
    def _save_message(self, user, ticket_id, body):
        from .models import SupportTicket, TicketMessage
        from django.utils import timezone
        try:
            ticket = SupportTicket.objects.get(pk=ticket_id)
        except SupportTicket.DoesNotExist:
            return None
        from .models import user_can_manage_tickets
        is_agent = user_can_manage_tickets(user)
        msg = TicketMessage.objects.create(
            ticket=ticket,
            author=user,
            body=body,
            is_staff_reply=is_agent,
        )
        # Agent yozsa — In Progress ga o'tkazish
        if is_agent and ticket.status == SupportTicket.STATUS_OPEN:
            ticket.status = SupportTicket.STATUS_IN_PROGRESS
            ticket.save(update_fields=['status', 'updated_at'])
        else:
            ticket.updated_at = timezone.now()
            ticket.save(update_fields=['updated_at'])
        return {
            'id': msg.id,
            'body': msg.body,
            'author': user.username,
            'is_staff_reply': is_agent,
            'created_at': msg.created_at.strftime('%d.%m.%Y %H:%M'),
            'attachment_url': '',
        }
