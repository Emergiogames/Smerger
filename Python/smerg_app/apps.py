from django.apps import AppConfig

class SmergAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'smerg_app'

    def ready(self):
        import smerg_app.signals