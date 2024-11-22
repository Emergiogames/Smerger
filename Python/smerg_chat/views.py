from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from .utils.enc_utils import *
from smerg_app.utils.async_serial_utils import *
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Rooms
class Rooms(APIView):
    @swagger_auto_schema(operation_description="Get a list of all chat rooms for the authenticated user.",
        responses={200: "List of chat rooms retrieved successfully.",404: "User does not exist.",400: "Token is not passed."})
    async def get(self, request):
        if request.headers.get('token'):
            exist = await UserProfile.objects.filter(auth_token=request.headers.get('token')).aexists()
            user = await UserProfile.objects.aget(auth_token=request.headers.get('token'))
            if exist and not user.block:
                rooms = [room async for room in Room.objects.filter(Q(first_person=user) | Q(second_person=user)).order_by('-id')] 
                serialized_data = await serialize_data(rooms, RoomSerial)
                return Response(serialized_data)
            return Response({'status':False,'message': 'User doesnot exist'})
        return Response({'status':False,'message': 'Token is not passed'})
    @swagger_auto_schema(operation_description="Create a new chat room or retrieve an existing one between two users.",request_body=openapi.Schema(type=openapi.TYPE_OBJECT,
        properties={'receiverId': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the receiver's SaleProfile."),},required=['receiverId'],),
        responses={200: "Chat room created or retrieved successfully.",404: "User does not exist.",400: "Token is not passed."})
    async def post(self, request):
        if request.headers.get('token'):
            exist = await UserProfile.objects.filter(auth_token=request.headers.get('token')).aexists()
            user = await UserProfile.objects.aget(auth_token=request.headers.get('token'))
            if exist and not user.block:
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
    @swagger_auto_schema(operation_description="Fetch chat messages for a specific room.",
        manual_parameters=[openapi.Parameter('roomId', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,description="ID of the chat room.")],
        responses={200: "Chat messages retrieved successfully.",404: "User does not exist.",400: "Token is not passed."})
    
    async def get(self, request):
        if request.headers.get('token'):
            exist = await UserProfile.objects.filter(auth_token=request.headers.get('token')).aexists()
            user = await UserProfile.objects.aget(auth_token=request.headers.get('token'))
            if exist and not user.block:
                chats = [chat async for chat in ChatMessage.objects.filter(Q(first_person=user) | Q(second_person=user)).order_by('-id')] 
                serialized_data = await serialize_data(chats, ChatSerial)
                return Response(serialized_data)
            return Response({'status':False,'message': 'User doesnot exist'})
        return Response({'status':False,'message': 'Token is not passed'})