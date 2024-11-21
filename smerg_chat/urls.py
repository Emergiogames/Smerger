from django.urls import path
from .views import *

urlpatterns = [
    path('rooms',Rooms.as_view()), # Rooms
    path('chats',Chat.as_view()), # Chats
]