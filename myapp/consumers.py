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
    if not text:
        return ''
    t = text.casefold()
    t = re.sub(r'[^\w\sа-яёўқғҳʼ\'`]', ' ', t, flags=re.IGNORECASE)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


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
            text = (data.get('text') or '').strip()[:500]
            if not text:
                return
            if await self._contains_banned_word(text):
                await self.send(text_data=json.dumps({
                    'type': 'error',
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
        try:
            from .models import BannedWord
            words = list(
                BannedWord.objects.filter(is_active=True).values_list('word', flat=True)
            )
        except Exception:
            return False
        if not words:
            return False

        norm_text = _normalize(text)
        compact = norm_text.replace(' ', '')

        for raw in words:
            if not raw:
                continue
            w = _normalize(raw)
            if not w:
                continue
            if w in norm_text or w.replace(' ', '') in compact:
                return True
            for token in norm_text.split():
                if w == token or w in token:
                    return True
        return False
