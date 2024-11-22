from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from .utils.enc_utils import *
from smerg_app.utils.async_serial_utils import *
from smerg_app.utils.check_utils import *

# Rooms
class Rooms(APIView):
    async def get(self, request):
        if request.headers.get('token'):
            exists, user = await check_user(request.headers.get('token'))
            if exists:
                rooms = [room async for room in Room.objects.filter(Q(first_person=user) | Q(second_person=user)).order_by('-id')] 
                serialized_data = await serialize_data(rooms, RoomSerial)
                return Response(serialized_data)
            return Response({'status':False,'message': 'User doesnot exist'})
        return Response({'status':False,'message': 'Token is not passed'})

    async def post(self, request):
        if request.headers.get('token'):
            exists, user = await check_user(request.headers.get('token'))
            if exists:
                reciever = await SaleProfiles.objects.aget(id=request.data.get('receiverId')).user
                image = await SaleProfiles.objects.aget(id=request.data.get('receiverId')).user.image.url if SaleProfiles.objects.get(id=request.data.get('receiverId')).user.image and hasattr(SaleProfiles.objects.get(id=request.data.get('receiverId')).user.image, 'url') else None
                room_exist = await Room.objects.filter(Q(first_person=user, second_person=reciever) | Q(second_person=user, first_person=reciever)).aexists()
                if room_exist:
                    room = await Room.objects.aget(Q(first_person=user, second_person=reciever) | Q(second_person=user, first_person=reciever))
                    return Response({'status':True, 'name': reciever.name, 'image':image, 'roomId': room.id})
                room = await Room.objects.acreate(first_person=user, second_person=reciever, last_msg=encrypt_message("Tap to send message"))
                return Response({'status':True,'name': reciever.name, 'image':image, 'roomId':room.id})
            return Response({'status':False,'message': 'User doesnot exist'})
        return Response({'status':False,'message': 'Token is not passed'})

# Chat of 2 users
class Chat(APIView):
    async def get(self, request):
        if request.headers.get('token'):
            exists, user = await check_user(request.headers.get('token'))
            if exists:
                chats = [chat async for chat in ChatMessage.objects.filter(Q(first_person=user) | Q(second_person=user)).order_by('-id')] 
                serialized_data = await serialize_data(chats, ChatSerial)
                return Response(serialized_data)
            return Response({'status':False,'message': 'User doesnot exist'})
        return Response({'status':False,'message': 'Token is not passed'})