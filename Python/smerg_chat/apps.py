from django.apps import AppConfig


class SmergChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'smerg_chat'

    def ready(self):
        import smerg_chat.signals