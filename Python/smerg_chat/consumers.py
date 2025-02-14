import json, os, asyncio, base64, uuid
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
from django.db.models import Q
from django.utils.timezone import localtime

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
        await ChatMessage.objects.filter(sended_to=self.user, seen=False).aupdate(seen=True)
        await Room.objects.filter(id=id, first_person=self.user).aupdate(unread_messages_first=0)
        await Room.objects.filter(id=id, second_person=self.user).aupdate(unread_messages_second=0)

        total_second = await Room.objects.filter(second_person=self.user, unread_messages_second__gt=0).acount()
        total_first = await Room.objects.filter(first_person=self.user, unread_messages_first__gt=0).acount()
        room_data = {
            "total_unread": total_first + total_second,
            "total_noti": await Notification.objects.filter(user=self.user).exclude(read_by=self.user).acount()
        }
        await self.channel_layer.group_send(
            f'user_{self.user.id}',
            {
                'type': 'room_message',
                'room_data': room_data
            }
        )
        await self.channel_layer.group_add(self.chatroom, self.channel_name)
        await self.accept()

    # Receive Message from Frontend
    async def receive(self, text_data):
        print('Received', text_data)
        data = json.loads(text_data)
        recieved, created, room_data, chat = await self.save_message(
            data.get('roomId'),
            data.get('token'),
            data.get('message'), 
            data.get('audio'), 
            datetime.now().strftime('%Y%m%d_%H%M%S'), 
            data.get('duration'), 
            data.get('attachment')
        )
        response = {
            'message': data.get('message'),
            'messageType': 'voice' if chat.audio else 'attachment' if chat.attachment else 'text',
            'audio': chat.audio.url if chat.audio else None,  
            'attachment': {'url' : chat.attachment.url if chat.attachment else None,'size': chat.attachment_size if chat.attachment else None,  'type': chat.attachment_type if chat.attachment else None, },  
            'roomId': data.get('roomId'),
            'token': data.get('token'),
            'sendedTo': recieved,
            'sendedBy': self.user.id,
            'duration': data.get('duration') if data.get('duration') else None,
            'time': str(created),
            'seen':self.chat.seen
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
            f'user_{self.user.id}',
            {
                'type': 'room_message',
                'room_data': room_data
            }
        )

        room_data['total_unread'] = await Room.objects.filter(second_person__id=recieved, unread_messages_second__gt=0).acount() + await Room.objects.filter(first_person__id=recieved, unread_messages_first__gt=0).acount()
        await self.channel_layer.group_send(
            f'user_{recieved}',
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

    # Saving Message to Db
    @sync_to_async
    def save_message(self, roomId, token, msg, audio, time, duration, attachment):
        room = Room.objects.get(id=roomId)
        if self.user == room.first_person:
            recieved = room.second_person
            room.unread_messages_second += 1
        else:
            recieved = room.first_person
            room.unread_messages_first += 1
        seen = True if self.user == recieved else False
        message = "🎙️ Voice message" if audio else "📄 Attachment" if attachment else msg
        self.chat = ChatMessage.objects.create(sended_by=self.user, sended_to=recieved, room=room, message=encrypt_message(message), seen=seen)
        room.last_msg = encrypt_message(msg)
        
        if audio:
            filename = f'audio_{self.user.username}_{time}.m4a'
            decoded_audio = base64.b64decode(audio)
            audio_file = ContentFile(decoded_audio, name=filename)
            self.chat.audio.save(filename, audio_file, save=True)
            self.chat.duration = duration
            room.last_msg = encrypt_message("🎙️ Voice message")
        elif attachment:
            attachment_dict = json.loads(attachment)
            base64_data = attachment_dict['data']
            decoded_attachment = base64.b64decode(base64_data)
            image_type = attachment_dict['fileExtension']
            filename = f'attachment_{self.user.username}_{time}{image_type}'
            attachment_file = ContentFile(decoded_attachment, name=filename)
            self.chat.attachment.save(filename, attachment_file, save=True)
            self.chat.attachment_size = attachment_dict['size']
            self.chat.attachment_type = attachment_dict['type']
            room.last_msg = encrypt_message("📄 Attachment")
        self.chat.save()
        print(self.chat)
        room.updated = datetime.now()
        room.save()
        if room.first_person == self.user:
            unread = room.unread_messages_second
        else:
            unread = room.unread_messages_first
        total_second = Room.objects.filter(second_person=self.user, unread_messages_second__gt=0).count()
        total_first = Room.objects.filter(first_person=self.user, unread_messages_first__gt=0).count()
        room_data = {
            'id': room.id,
            'sender_id': self.user.id,  
            'first_person': room.first_person.id,
            'first_name': room.first_person.first_name,
            'first_image': room.post.image1.url if room.post.image1 else None,
            'second_person': room.second_person.id,
            'second_name': room.second_person.first_name,
            'second_image': room.post.image1.url if room.post.image1 else None,
            'last_msg': decrypt_message(room.last_msg) if room.last_msg else '',
            'updated': localtime(room.updated).strftime('%Y-%m-%d %H:%M:%S'),
            'active': recieved.is_active,
            'last_seen': recieved.inactive_from.strftime('%Y-%m-%d %H:%M:%S') if recieved.inactive_from else None,
            "unread_messages": unread,
            "total_unread": total_second + total_first,
            "total_noti": Notification.objects.filter(user=self.user).exclude(read_by=self.user).count(),
            # "post": room.post if room.post else None
        }
        print(room_data)
        return recieved.id, self.chat.timestamp, room_data, self.chat

class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        token = self.scope['query_string'].decode().split('=')[-1]
        exists, user = await check_user(token)
        self.user_id = user.id
        user.active_from = timezone.now()
        user.is_active = True
        await user.asave()
        self.room_group_name =  f'user_{self.user_id}'
        await self.channel_layer.group_add(self.room_group_name,self.channel_name)
        await self.accept()
        total_second = await Room.objects.filter(second_person=user, unread_messages_second__gt=0).acount()
        total_first = await Room.objects.filter(first_person=user, unread_messages_first__gt=0).acount()
        room_data = {
            "total_unread": total_first + total_second,
            "total_noti": await Notification.objects.filter(user=user).exclude(read_by=user).acount()
        }
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'room_message',
                'room_data': room_data
            }
        )

    async def disconnect(self, close_code):
        user = await UserProfile.objects.aget(id=self.user_id)
        user.is_active = False
        user.inactive_from = timezone.now()
        total_hr_spend = timezone.now() - user.active_from
        user.total_hr_spend += round(total_hr_spend.total_seconds() / 3600, 2)
        await user.asave()
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
        token = self.scope['query_string'].decode().split('=')[-1]
        if not token:
            await self.close()
            return
        exists, self.user = await check_user(token)
        self.user_id = self.user.id
        self.room_group_name = f'noti_updates_{self.user_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print('Connected')

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def notification(self, event):
        notification = event['notification']
        await self.send(
            text_data=json.dumps({
                'type': self.room_group_name,
                'notification': notification
            })
        )