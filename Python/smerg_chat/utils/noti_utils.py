#################################  P U S H  N O T I F I C A T I O N  #################################
from onesignal_sdk.client import Client
from onesignal_sdk.client import AsyncClient
from django.conf import settings
from .enc_utils import *
from asgiref.sync import sync_to_async

def send_notifications(message, title, onesignal_id):
    client = Client(app_id=settings.ONESIGNAL_APP_ID, rest_api_key=settings.ONESIGNAL_API_KEY)
    print(f"working : {client}")
    notification_body = {
        "headings": {"en": title},
        "contents": {"en": decrypt_message(message)},
        "include_player_ids": [onesignal_id]
    }
    response = client.send_notification(notification_body)
    print(f"Notification sent successfully. SID: {response}")