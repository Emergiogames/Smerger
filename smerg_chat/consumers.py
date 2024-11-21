import json, os, asyncio
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smerger.settings")

import django
django.setup()

from django.contrib.auth.models import User
from .models import *
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from .utils.enc_utils import *
from .utils.noti_utils import *
from datetime import datetime

class ChatConsumer(AsyncConsumer):

    # Connecting WS
    async def websocket_connect(self,event):
        print('Connected', event)
        token = self.scope['query_string'].decode().split('=')[-1]
        id = self.scope['url_route']['kwargs']['id']
        if not token:
            await self.close()
            return
        user = await self.get_user_from_token(token)
        self.chatroom = f'user_chatroom_{id}'
        await self.channel_layer.group_add(self.chatroom,self.channel_name)
        await self.send({'type':'websocket.accept'})

    # Recieve Message from Frontend
    async def websocket_receive(self,event):
        print('Recieved', event)
        data = json.loads(event['text'])
        recieved, sended, created = await self.save_message(data.get('roomId'),data.get('token'),data.get('message'))
        print(recieved,sended)
        response = {
            'message' : data.get('message'),
            'roomId' : data.get('roomId'),
            'token' : data.get('token'),
            'sendedTo' : recieved,
            'sendedBy' : sended,
            'time' : str(created)
        }
        await self.channel_layer.group_send(
            self.chatroom,
            {
                'type':'chat_message',
                'text': json.dumps(response)
            }
        )
        room_data = await self.get_room_data(data.get('roomId'))
        
        # Send room update to all connected clients
        await self.channel_layer.group_send(
            'room_updates',
            {
                'type': 'room_message',
                'room_data': room_data
            }
        )

    # Sending Message to Frontend
    async def chat_message(self,event):
        print('Chat Message', event)
        await self.send({
            'type':'websocket.send',
            'text': event['text']
        })

    # Disconnecting WS
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.chatroom,self.channel_name)
    # async def websocket_disconnect(self, event):
    #     if getattr(self, '_disconnect_called', False):
    #         print('Previous disconnect in progress, cleaning up...')
    #         while getattr(self, '_disconnect_called', False):
    #             await asyncio.sleep(0.1)
    #         return

    #     self._disconnect_called = True
    #     # print('Disconnected', event)

    #     if hasattr(self, 'channel_layer') and hasattr(self, 'chatroom'):
    #         await self.channel_layer.group_discard(self.chatroom, self.channel_name)

    #     print('Disconnect complete')
    #     self._disconnect_called = False 

    # Getting Username using Token
    @sync_to_async
    def get_user_from_token(self, token):
        if UserProfile.objects.filter(auth_token=token).exists() and not UserProfile.objects.get(auth_token=token).block:
            user = UserProfile.objects.get(auth_token=token)
            return user.username
        return None
    # async def get_user_from_token(self, token):
    #     exist = await UserProfile.objects.filter(auth_token=token).aexists()
    #     if exist:
    #         user = await UserProfile.objects.aget(auth_token=token)
    #         if not user.block:
    #             return user.username
    #     return None

    # Saving Message to Db
    @sync_to_async
    def save_message(self, roomId, token, msg):
        room = Room.objects.get(id = roomId)
        if not UserProfile.objects.filter(auth_token=token).exists() and UserProfile.objects.get(auth_token=token).block:
            return None
        user = UserProfile.objects.get(auth_token=token)
        recieved = room.second_person if user.id == room.first_person.id else room.first_person
        print(f"Message is {msg}")
        # if msg:
        chat = ChatMessage.objects.create(sended_by=user,sended_to=recieved,room=room,message=encrypt_message(msg))
        print(chat)
        created = chat.timestamp
        room.last_msg = encrypt_message(msg)
        room.updated = datetime.now()
        room.save()
        return recieved.id, user.id, created
    
    @sync_to_async
    def get_room_data(self, room_id):
        room = Room.objects.get(id=room_id)
        return {
            'id': room.id,
            'first_person': room.first_person.id,
            'second_person': room.second_person.id,
            'last_msg': decrypt_message(room.last_msg) if room.last_msg else '',
            'updated': str(room.updated)
        }

class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print('Connected')
        self.room_group_name = 'room_updates'
        await self.channel_layer.group_add(self.room_group_name,self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name,self.channel_name)

    async def room_message(self, event):
        room_data = event['room_data']
        await self.send(
            text_data=json.dumps({
                'room': room_data
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



