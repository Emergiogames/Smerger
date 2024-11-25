import json, os, asyncio, base64
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smerger.settings")

import django
django.setup()

from django.contrib.auth.models import User
from .models import *
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async, async_to_sync
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from .utils.enc_utils import *
from .utils.noti_utils import *
from datetime import datetime
from django.utils import timezone
from channels.layers import get_channel_layer
from django.core.files.base import ContentFile
from smerg_app.utils.check_utils import *

class ChatConsumer(AsyncWebsocketConsumer):
    # Connecting WS
    async def connect(self):
        print('Connected')
        token = self.scope['query_string'].decode().split('=')[-1]
        id = self.scope['url_route']['kwargs']['id']
        if not token:
            await self.close()
            return
        exists, self.user = await check_user(token)
        self.chatroom = f'user_chatroom_{id}'
        await self.channel_layer.group_add(self.chatroom, self.channel_name)
        await self.accept()

    # Receive Message from Frontend
    async def receive(self, text_data):
        print('Received', text_data)
        data = json.loads(text_data)
        audio = None
        file_name = None
        recieved, created, room_data, audio = await self.save_message(data.get('roomId'), data.get('token'), data.get('message'), data.get('audio'))
        response = {
            'message': data.get('message'),
            'audio': audio.url if audio else None,
            'roomId': data.get('roomId'),
            'token': data.get('token'),
            'sendedTo': recieved,
            'sendedBy': self.user.id,
            'time': str(created)
        }

        ## Send Message
        room_group_name = f'user_chatroom_{data.get('roomId')}'
        await self.channel_layer.group_send(
            room_group_name,
            {
                'type': 'chat_message',
                'text': json.dumps(response)
            }
        )

        ## Update Room Data
        await self.channel_layer.group_send(
            'room_updates',
            {
                'type': 'room_message',
                'room_data': room_data
            }
        )

    # Sending Message to Frontend
    async def chat_message(self, event):
        print('Chat Message', event)
        await self.send(text_data=event['text'])

    # Disconnecting WS
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.chatroom, self.channel_name)

    async def decode_data(self, audio):
        audio_bytes = base64.b64decode(audio)
        return audio_bytes

    # Saving Message to Db
    @sync_to_async
    def save_message(self, roomId, token, msg, audio):
        room = Room.objects.get(id=roomId)
        recieved = room.second_person if self.user.id == room.first_person.id else room.first_person
        chat = ChatMessage.objects.create(sended_by=self.user, sended_to=recieved, room=room, message=encrypt_message(msg))
        if audio:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'audio_{self.user.username}_{timestamp}.m4a'
            decoded_audio = asyncio.run(self.decode_data(audio))
            chat.audio.save(filename, ContentFile(decoded_audio), save=True)
            if chat.audio and os.path.exists(chat.audio.path):
                print(f"Audio saved successfully at: {chat.audio.path}")
            else:
                print("Audio file was not saved properly")
        print(chat)
        created = chat.timestamp
        room.last_msg = encrypt_message(msg)
        room.updated = datetime.now()
        room.save()
        room_data = {
            'id': room.id,
            'first_person': room.first_person.id,
            'first_name': room.first_person.first_name,
            'first_image': room.first_person.image.url if room.first_person.image else None,
            'second_person': room.second_person.id,
            'second_name': room.second_person.first_name,
            'second_image': room.second_person.image.url if room.second_person.image else None,
            'last_msg': decrypt_message(room.last_msg) if room.last_msg else '',
            'updated': room.updated.strftime('%Y-%m-%d %H:%M:%S'),
            'active': recieved.is_active,
            'last_seen': recieved.inactive_from.strftime('%Y-%m-%d %H:%M:%S') if recieved.inactive_from else None,
            'updated': room.updated.strftime('%Y-%m-%d %H:%M:%S')
        }
        return recieved.id, created, room_data, chat.audio

class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        token = self.scope['query_string'].decode().split('=')[-1]
        exists, user_result = await check_user(token)
        self.user = user_result
        self.user.active_from = timezone.now()
        self.user.is_active = True
        await self.user.asave()
        print('Connected')
        self.room_group_name = 'room_updates'
        await self.channel_layer.group_add(self.room_group_name,self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        self.user.is_active = False
        self.user.inactive_from = timezone.now()
        total_hr_spend = timezone.now() - self.user.active_from
        self.user.total_hr_spend += round(total_hr_spend.total_seconds() / 3600, 2)
        await self.user.asave()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'room_message',
                'room_data': {
                    'active': self.user.is_active,
                    'last_seen': self.user.inactive_from.strftime('%Y-%m-%d %H:%M:%S'),
                }
            })
        await self.channel_layer.group_discard(self.room_group_name,self.channel_name)

    async def room_message(self, event):
        print('Room Data', event)
        room_data = event['room_data']
        await self.send(
            text_data=json.dumps({
                'type': 'room_update',
                'room': room_data,
            })
        )

class NotiConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print('Connected')
        self.room_group_name = 'noti_updates'
        await self.channel_layer.group_add(self.room_group_name,self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name,self.channel_name)

    async def notification(self, event):
        notification = event['noti']
        await self.send(
            text_data=json.dumps({
                'notification': notification
            })
        )