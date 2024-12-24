import os,django
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter,URLRouter
import smerg_chat.routing
from django.core.asgi import get_asgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'smerger.settings')
# chatapp.settings.configure()


class DebugMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        print(f"Incoming connection to: {scope['type']} {scope.get('path', '')}")
        return await self.app(scope, receive, send)

application = DebugMiddleware(ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(smerg_chat.routing.websocket_urlpatterns)
    )
}))

# application = ProtocolTypeRouter({
#     'http':get_asgi_application(),
#     'websocket':AuthMiddlewareStack(
#         URLRouter(smerg_chat.routing.websocket_urlpatterns)
#     )
# })