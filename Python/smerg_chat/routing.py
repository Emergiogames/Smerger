from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('<int:id>', consumers.ChatConsumer.as_asgi()),
    path('rooms', consumers.RoomConsumer.as_asgi()),
    path('notifications/', consumers.NotiConsumer.as_asgi()),
]